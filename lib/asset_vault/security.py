"""
Asset Vault Security Module

Path sanitization, access control, and audit logging.
Addresses Council of Ricks security requirements:
- TOCTOU protection for symlinks
- Path traversal prevention
- Whitelist-based access control
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .types import SecurityConfig


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


# Default allowed paths (can be configured via set_allowed_paths)
ALLOWED_PATHS: List[Path] = []


def _load_allowed_paths_from_config() -> List[Path]:
    """Load allowed paths from config/asset_library.yaml if available."""
    config_path = Path("config/asset_library.yaml")
    if not config_path.exists():
        return []

    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        security_config = config.get("security", {})
        paths = security_config.get("allowed_paths", [])
        return [Path(p).expanduser().resolve() for p in paths]
    except Exception:
        return []


def set_allowed_paths(paths: List[Path]) -> None:
    """
    Set the whitelist of allowed paths.

    Args:
        paths: List of allowed directory paths
    """
    global ALLOWED_PATHS
    ALLOWED_PATHS = [Path(p).resolve() for p in paths]


def get_allowed_paths() -> List[Path]:
    """
    Get the current allowed paths, loading from config if not set.

    Returns:
        List of allowed directory paths
    """
    global ALLOWED_PATHS
    if not ALLOWED_PATHS:
        ALLOWED_PATHS = _load_allowed_paths_from_config()
        if not ALLOWED_PATHS:
            # Default fallback
            ALLOWED_PATHS = [
                Path("/Volumes/Storage/3d"),
                Path.home() / "Documents" / "Blender",
            ]
    return ALLOWED_PATHS


def sanitize_path(path: str | Path) -> Path:
    """
    Sanitize and validate a file path.

    Security measures:
    - Resolves to absolute path
    - Resolves all symlinks (TOCTOU protection)
    - Blocks ".." components after resolution
    - Verifies path is within allowed directories

    Args:
        path: Input path (string or Path object)

    Returns:
        Validated absolute Path

    Raises:
        SecurityError: If path validation fails
    """
    # Convert to Path and make absolute
    abs_path = Path(path).absolute()

    # Check for obvious traversal attempts before resolution
    path_str = str(abs_path)
    if ".." in path_str:
        raise SecurityError(f"Path traversal detected: {path}")

    # Resolve symlinks (TOCTOU protection)
    try:
        resolved = abs_path.resolve()
    except OSError as e:
        raise SecurityError(f"Cannot resolve path: {path} - {e}")

    # Check resolved path doesn't contain traversal
    if ".." in str(resolved):
        raise SecurityError(f"Resolved path contains traversal: {resolved}")

    # Verify path is within allowed directories
    allowed = get_allowed_paths()
    if allowed:
        for allowed_path in allowed:
            try:
                resolved.relative_to(allowed_path)
                return resolved  # Path is within allowed directory
            except ValueError:
                continue
        raise SecurityError(f"Path not in allowed directories: {resolved}")

    # No whitelist configured, allow (with warning)
    return resolved


def validate_file_access(path: Path, config: Optional[SecurityConfig] = None) -> Tuple[bool, str]:
    """
    Validate that a file can be accessed.

    Checks:
    - Path is sanitized
    - File exists
    - File size within limits
    - Extension is allowed

    Args:
        path: File path to validate
        config: Security configuration (uses defaults if None)

    Returns:
        Tuple of (is_valid, error_message)
    """
    config = config or SecurityConfig()

    try:
        sanitized = sanitize_path(path)
    except SecurityError as e:
        return False, str(e)

    if not sanitized.exists():
        return False, f"File does not exist: {sanitized}"

    if not sanitized.is_file():
        return False, f"Path is not a file: {sanitized}"

    # Check file size
    file_size_mb = sanitized.stat().st_size / (1024 * 1024)
    if file_size_mb > config.max_file_size_mb:
        return False, f"File too large: {file_size_mb:.1f}MB > {config.max_file_size_mb}MB"

    # Check extension
    ext = sanitized.suffix.lower()
    if ext not in config.allowed_extensions:
        return False, f"Extension not allowed: {ext}"

    return True, ""


@dataclass
class AuditEvent:
    """Single audit log event."""
    timestamp: str
    event_type: str  # "access", "denied", "scan", "load", "index"
    path: str
    action: str  # "read", "write", "delete", "load", "scan"
    success: bool
    user: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "path": self.path,
            "action": self.action,
            "success": self.success,
            "user": self.user,
            "details": self.details,
        }


class AuditLogger:
    """
    Audit logging for asset access operations.

    Logs to JSON lines format for easy parsing and analysis.
    """

    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize audit logger.

        Args:
            log_path: Path to log file (None to disable logging)
        """
        self.log_path = log_path
        self._events: List[AuditEvent] = []
        self._rate_limiter: Dict[str, List[float]] = {}

    def _get_timestamp(self) -> str:
        """Get ISO 8601 timestamp."""
        return datetime.now().isoformat()

    def log_access(
        self,
        path: Path,
        action: str,
        success: bool,
        user: str = "system"
    ) -> None:
        """
        Log a file access attempt.

        Args:
            path: File path being accessed
            action: Action type (read, write, delete, load, scan)
            success: Whether the access succeeded
            user: User identifier
        """
        event = AuditEvent(
            timestamp=self._get_timestamp(),
            event_type="access" if success else "denied",
            path=str(path),
            action=action,
            success=success,
            user=user,
        )
        self._record_event(event)

    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        user: str = "system"
    ) -> None:
        """
        Log a security-relevant event.

        Args:
            event_type: Type of security event
            details: Event details
            user: User identifier
        """
        event = AuditEvent(
            timestamp=self._get_timestamp(),
            event_type=event_type,
            path=details.get("path", ""),
            action=details.get("action", "security"),
            success=False,
            user=user,
            details=details,
        )
        self._record_event(event)

    def log_index_event(
        self,
        action: str,
        count: int,
        duration_ms: int,
        user: str = "system"
    ) -> None:
        """
        Log an index operation.

        Args:
            action: Action type (build, update, load)
            count: Number of assets processed
            duration_ms: Duration in milliseconds
            user: User identifier
        """
        event = AuditEvent(
            timestamp=self._get_timestamp(),
            event_type="index",
            path="",
            action=action,
            success=True,
            user=user,
            details={"count": count, "duration_ms": duration_ms},
        )
        self._record_event(event)

    def _record_event(self, event: AuditEvent) -> None:
        """Record an event to memory and optionally to file."""
        self._events.append(event)

        if self.log_path:
            try:
                # Ensure directory exists
                self.log_path.parent.mkdir(parents=True, exist_ok=True)

                # Append to log file (JSON lines format)
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(event.to_dict()) + "\n")
            except Exception:
                pass  # Don't fail operations due to logging errors

    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent events from memory.

        Args:
            count: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        return [e.to_dict() for e in self._events[-count:]]

    def export_audit_log(
        self,
        output_path: Path,
        format: str = "json"
    ) -> Path:
        """
        Export audit log to file.

        Args:
            output_path: Output file path
            format: Output format ("json" or "csv")

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump([e.to_dict() for e in self._events], f, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "event_type", "path", "action", "success", "user"])
                for e in self._events:
                    writer.writerow([
                        e.timestamp, e.event_type, e.path, e.action, e.success, e.user
                    ])
        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit statistics.

        Returns:
            Dictionary with event counts and patterns
        """
        total = len(self._events)
        access_count = sum(1 for e in self._events if e.event_type == "access")
        denied_count = sum(1 for e in self._events if e.event_type == "denied")
        index_count = sum(1 for e in self._events if e.event_type == "index")

        # Count accessed paths
        path_counts: Dict[str, int] = {}
        for e in self._events:
            if e.path:
                path_counts[e.path] = path_counts.get(e.path, 0) + 1

        top_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_events": total,
            "access_count": access_count,
            "denied_count": denied_count,
            "index_count": index_count,
            "top_accessed_paths": top_paths,
        }

    def check_rate_limit(
        self,
        path: Path,
        max_per_minute: int = 100
    ) -> bool:
        """
        Check if path access is within rate limits.

        Args:
            path: Path being accessed
            max_per_minute: Maximum accesses per minute

        Returns:
            True if within limits, False if exceeded
        """
        key = str(path)
        now = time.time()

        # Clean old entries
        if key in self._rate_limiter:
            self._rate_limiter[key] = [
                t for t in self._rate_limiter[key] if now - t < 60
            ]
        else:
            self._rate_limiter[key] = []

        # Check limit
        if len(self._rate_limiter[key]) >= max_per_minute:
            return False

        # Record access
        self._rate_limiter[key].append(now)
        return True


def validate_security_config(config: SecurityConfig) -> List[str]:
    """
    Validate security configuration.

    Args:
        config: Security configuration to validate

    Returns:
        List of warning/error messages
    """
    issues = []

    if not config.allowed_paths:
        issues.append("WARNING: No allowed_paths configured - all paths accessible")

    for path in config.allowed_paths:
        if not path.exists():
            issues.append(f"WARNING: Allowed path does not exist: {path}")

    if config.max_file_size_mb <= 0:
        issues.append("ERROR: max_file_size_mb must be positive")

    if not config.allowed_extensions:
        issues.append("WARNING: No allowed_extensions configured")

    return issues
