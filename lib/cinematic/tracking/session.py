"""
Session Management Module (Phase 7.4)

Provides session persistence and resume capability for tracking workflows.
Enables tracking sessions to be saved, interrupted, and resumed without
losing progress - essential for long tracking jobs and batch processing.

Core Classes:
    TrackingSessionManager: Main session manager with checkpoint/resume
    SessionStatus: Enum for session lifecycle states

Factory Functions:
    create_session: Create new tracking session
    resume_tracking: Resume from checkpoint
    load_session: Load without resume logic
    list_sessions: Find all session files

Utility Functions:
    get_session_status: Analyze session state
    export_session_report: Generate human-readable report
    merge_sessions: Combine multiple sessions
    cleanup_old_sessions: Remove old session files

Session File Location:
    .gsd-state/tracking/
    ├── sessions/
    │   └── {session_id}.yaml
    └── solves/
        └── {solve_name}/

Usage:
    from lib.cinematic.tracking.session import (
        TrackingSessionManager,
        create_session,
        resume_tracking,
        SessionStatus,
    )

    # Create new session
    manager = create_session("footage/shot.mp4", "hero_shot")

    # Save checkpoint
    manager.save_checkpoint(frame=50, operation="track_forward")

    # Resume later
    manager = resume_tracking(".gsd-state/tracking/sessions/hero_shot.yaml")
    next_frame = manager.get_resume_point()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import uuid

try:
    import yaml
except ImportError:
    yaml = None

from .types import (
    TrackingSession,
    TrackData,
    SolveData,
    FootageMetadata,
)


# =============================================================================
# SESSION STATUS ENUM
# =============================================================================

class SessionStatus(Enum):
    """
    Tracking session lifecycle states.

    States:
        NOT_STARTED: Session created but no tracking done
        TRACKING: Actively tracking frames
        TRACKING_COMPLETE: All frames tracked, ready for solve
        SOLVING: Running camera solve
        COMPLETE: Tracking and solve complete
        FAILED: Error during tracking or solve
    """
    NOT_STARTED = "not_started"
    TRACKING = "tracking"
    TRACKING_COMPLETE = "tracking_complete"
    SOLVING = "solving"
    COMPLETE = "complete"
    FAILED = "failed"


# =============================================================================
# TRACKING SESSION MANAGER
# =============================================================================

class TrackingSessionManager:
    """
    Manager for tracking session persistence and resume.

    Handles saving/loading tracking sessions, checkpoints for resume,
    and progress tracking across tracking and solving workflows.

    Attributes:
        session_path: Path to session file
        session: TrackingSession data object
        state: Raw state dict for checkpoint data
    """

    def __init__(self, session_path: Path):
        """
        Initialize session manager.

        Args:
            session_path: Path to session file (.yaml or .json)
        """
        self.session_path = Path(session_path)
        self.state = self._load_or_create_state()

        # Create TrackingSession from state
        session_data = self.state.get('session', {})
        self._session = TrackingSession.from_dict(session_data) if session_data else TrackingSession()

    def _load_or_create_state(self) -> Dict[str, Any]:
        """Load existing session state or create new empty state."""
        if self.session_path.exists():
            return self._load_yaml(self.session_path)

        # Create new state with defaults
        return {
            "id": str(uuid.uuid4())[:8],
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "session": {},
            "footage": {},
            "tracking": {
                "status": "not_started",
                "tracked_frames": [],
                "remaining_frames": [],
            },
            "solve": {
                "status": "pending",
                "solve_id": None,
            },
            "checkpoint": None,
        }

    @property
    def session(self) -> TrackingSession:
        """Access underlying TrackingSession."""
        return self._session

    @session.setter
    def session(self, value: TrackingSession):
        self._session = value
        self.state['session'] = value.to_dict()

    # -------------------------------------------------------------------------
    # CHECKPOINT AND RESUME
    # -------------------------------------------------------------------------

    def save_checkpoint(self, frame: int, operation: str) -> None:
        """
        Save current progress for resume.

        Updates tracked frames list and saves session state.

        Args:
            frame: Current frame number
            operation: Current operation description
        """
        # Update checkpoint
        self.state['checkpoint'] = {
            "frame": frame,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
        }

        # Add frame to tracked if not already
        tracked = set(self.state['tracking'].get('tracked_frames', []))
        tracked.add(frame)
        self.state['tracking']['tracked_frames'] = sorted(list(tracked))

        # Update status
        if self.state['tracking']['status'] == 'not_started':
            self.state['tracking']['status'] = 'tracking'

        # Update timestamps
        self.state['modified'] = datetime.now().isoformat()
        if self._session:
            self._session.updated_at = self.state['modified']

        # Persist
        self._save()

    def get_resume_point(self) -> Optional[int]:
        """
        Get frame to resume from (max tracked + 1).

        Returns:
            Frame number to resume from, or None if tracking complete
        """
        tracked = self.state['tracking'].get('tracked_frames', [])
        if not tracked:
            return self._session.frame_start if self._session else 1

        max_tracked = max(tracked)
        frame_end = self._session.frame_end if self._session else 100

        if max_tracked >= frame_end:
            return None  # Tracking complete

        return max_tracked + 1

    def get_progress(self) -> Dict[str, Any]:
        """
        Get tracking progress summary.

        Returns:
            Dict with:
                - total_frames: int
                - tracked_frames: int
                - percent_complete: float
                - status: str
                - remaining_frames: List[int]
        """
        tracked = self.state['tracking'].get('tracked_frames', [])
        frame_start = self._session.frame_start if self._session else 1
        frame_end = self._session.frame_end if self._session else 100

        total = frame_end - frame_start + 1
        tracked_count = len(tracked)
        percent = (tracked_count / total * 100) if total > 0 else 0.0

        # Calculate remaining frames
        tracked_set = set(tracked)
        remaining = [f for f in range(frame_start, frame_end + 1) if f not in tracked_set]

        return {
            "total_frames": total,
            "tracked_frames": tracked_count,
            "percent_complete": round(percent, 1),
            "status": self.state['tracking'].get('status', 'not_started'),
            "remaining_frames": remaining,
        }

    def mark_tracking_complete(self) -> None:
        """Mark tracking phase as complete."""
        self.state['tracking']['status'] = 'complete'
        self.state['modified'] = datetime.now().isoformat()
        self._save()

    def mark_solve_complete(self, solve_id: str) -> None:
        """
        Mark solve phase as complete.

        Args:
            solve_id: Identifier for completed solve
        """
        self.state['solve']['status'] = 'complete'
        self.state['solve']['solve_id'] = solve_id
        self.state['tracking']['status'] = 'complete'
        self.state['modified'] = datetime.now().isoformat()
        self._save()

    # -------------------------------------------------------------------------
    # PERSISTENCE
    # -------------------------------------------------------------------------

    def _save(self) -> None:
        """Save state to session file."""
        # Ensure parent directory exists
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self._save_yaml(self.session_path, self.state)

    def _save_yaml(self, path: Path, data: Dict) -> None:
        """Save data to YAML with atomic write."""
        temp_path = path.with_suffix('.tmp')

        try:
            if yaml:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)

            # Atomic rename
            temp_path.replace(path)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load data from YAML with error handling."""
        if not path.exists():
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                if yaml:
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception:
            return {}


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_session(
    footage_path: Path,
    name: str,
    base_path: Optional[Path] = None
) -> TrackingSessionManager:
    """
    Create new tracking session with footage info.

    Args:
        footage_path: Path to footage file
        name: Session name
        base_path: Base path for sessions (default: .gsd-state/tracking/sessions/)

    Returns:
        TrackingSessionManager instance
    """
    if base_path is None:
        base_path = Path(".gsd-state/tracking/sessions")

    session_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_path = base_path / f"{session_id}.yaml"

    manager = TrackingSessionManager(session_path)

    # Initialize session
    session = TrackingSession(
        session_id=session_id,
        footage_path=str(footage_path),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        status="not_started",
    )

    manager.session = session
    manager.state['footage']['source_path'] = str(footage_path)
    manager._save()

    return manager


def resume_tracking(session_path: Path) -> TrackingSessionManager:
    """
    Load existing session and return manager ready to continue.

    Prints resume status information.

    Args:
        session_path: Path to session file

    Returns:
        TrackingSessionManager instance
    """
    manager = TrackingSessionManager(session_path)

    # Print resume info
    progress = manager.get_progress()
    resume_frame = manager.get_resume_point()

    print(f"Session: {manager.session.session_id}")
    print(f"Progress: {progress['tracked_frames']}/{progress['total_frames']} frames ({progress['percent_complete']}%)")
    print(f"Status: {progress['status']}")

    if resume_frame:
        print(f"Resume from frame: {resume_frame}")
    else:
        print("Tracking complete - ready for solve")

    return manager


def load_session(session_path: Path) -> TrackingSessionManager:
    """
    Load session without resume logic.

    Args:
        session_path: Path to session file

    Returns:
        TrackingSessionManager instance
    """
    return TrackingSessionManager(session_path)


def list_sessions(base_path: Optional[Path] = None) -> List[Path]:
    """
    Find all session files in sessions directory.

    Args:
        base_path: Base path for sessions (default: .gsd-state/tracking/sessions/)

    Returns:
        List of session file paths
    """
    if base_path is None:
        base_path = Path(".gsd-state/tracking/sessions")

    if not base_path.exists():
        return []

    return sorted(base_path.glob("*.yaml"))


def get_session_status(manager: TrackingSessionManager) -> SessionStatus:
    """
    Analyze session state and return status.

    Args:
        manager: TrackingSessionManager instance

    Returns:
        SessionStatus enum value
    """
    tracking_status = manager.state.get('tracking', {}).get('status', 'not_started')
    solve_status = manager.state.get('solve', {}).get('status', 'pending')

    # Map to SessionStatus
    if tracking_status == 'not_started':
        return SessionStatus.NOT_STARTED
    elif tracking_status == 'tracking':
        return SessionStatus.TRACKING
    elif tracking_status == 'complete':
        if solve_status == 'complete':
            return SessionStatus.COMPLETE
        elif solve_status == 'solving':
            return SessionStatus.SOLVING
        else:
            return SessionStatus.TRACKING_COMPLETE
    elif tracking_status == 'failed' or solve_status == 'failed':
        return SessionStatus.FAILED

    return SessionStatus.NOT_STARTED


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def export_session_report(session_path: Path, output_path: Path) -> None:
    """
    Generate human-readable session report.

    Args:
        session_path: Path to session file
        output_path: Output path for report
    """
    manager = TrackingSessionManager(session_path)
    progress = manager.get_progress()
    status = get_session_status(manager)

    report_lines = [
        f"# Tracking Session Report",
        f"",
        f"**Session ID:** {manager.session.session_id}",
        f"**Status:** {status.value}",
        f"**Created:** {manager.state.get('created', 'N/A')}",
        f"**Modified:** {manager.state.get('modified', 'N/A')}",
        f"",
        f"## Footage",
        f"- Path: {manager.session.footage_path}",
        f"- Frame Range: {manager.session.frame_start} - {manager.session.frame_end}",
        f"",
        f"## Progress",
        f"- Total Frames: {progress['total_frames']}",
        f"- Tracked Frames: {progress['tracked_frames']}",
        f"- Percent Complete: {progress['percent_complete']}%",
        f"",
        f"## Tracks",
        f"- Track Count: {len(manager.session.tracks)}",
        f"",
        f"## Checkpoint",
    ]

    checkpoint = manager.state.get('checkpoint')
    if checkpoint:
        report_lines.extend([
            f"- Frame: {checkpoint.get('frame', 'N/A')}",
            f"- Operation: {checkpoint.get('operation', 'N/A')}",
            f"- Timestamp: {checkpoint.get('timestamp', 'N/A')}",
        ])
    else:
        report_lines.append("No checkpoint recorded")

    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def merge_sessions(
    session_paths: List[Path],
    output_path: Path,
    name: Optional[str] = None
) -> TrackingSessionManager:
    """
    Combine multiple sessions into one.

    Merges tracks from multiple sessions, keeps best solve.
    Useful for multi-shot tracking.

    Args:
        session_paths: List of session file paths
        output_path: Output path for merged session
        name: Optional name for merged session

    Returns:
        TrackingSessionManager for merged session
    """
    if not session_paths:
        raise ValueError("No sessions to merge")

    # Load all sessions
    managers = [TrackingSessionManager(p) for p in session_paths]

    # Use first session as base
    base = managers[0]

    # Create new merged session
    merged = TrackingSessionManager(output_path)

    # Merge tracks
    all_tracks = []
    for mgr in managers:
        all_tracks.extend(mgr.session.tracks)

    # Remove duplicates by name
    seen_names = set()
    unique_tracks = []
    for track in all_tracks:
        if track.name not in seen_names:
            seen_names.add(track.name)
            unique_tracks.append(track)

    # Create merged session
    merged_session = TrackingSession(
        session_id=name or f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        footage_path=base.session.footage_path,
        frame_start=min(m.session.frame_start for m in managers),
        frame_end=max(m.session.frame_end for m in managers),
        tracks=unique_tracks,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        status="complete" if all(m.state['tracking'].get('status') == 'complete' for m in managers) else "tracking",
    )

    merged.session = merged_session
    merged._save()

    return merged


def cleanup_old_sessions(base_path: Path, days_old: int = 30) -> int:
    """
    Remove sessions older than N days.

    Args:
        base_path: Base path for sessions
        days_old: Age threshold in days

    Returns:
        Number of removed sessions
    """
    if base_path is None:
        base_path = Path(".gsd-state/tracking/sessions")

    if not base_path.exists():
        return 0

    removed = 0
    threshold = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

    for session_file in base_path.glob("*.yaml"):
        try:
            manager = TrackingSessionManager(session_file)
            modified_str = manager.state.get('modified', '')
            if modified_str:
                modified = datetime.fromisoformat(modified_str).timestamp()
                if modified < threshold:
                    session_file.unlink()
                    removed += 1
        except Exception:
            pass

    return removed


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "TrackingSessionManager",
    "SessionStatus",

    # Factory functions
    "create_session",
    "resume_tracking",
    "load_session",
    "list_sessions",

    # Utility functions
    "get_session_status",
    "export_session_report",
    "merge_sessions",
    "cleanup_old_sessions",
]
