"""
Tracking Session Persistence

Provides TrackingSessionManager for save/load/resume of tracking sessions.
Follows pattern from lib/cinematic/state_manager.py.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional, List

try:
    import yaml
except ImportError:
    yaml = None

from .types import TrackingSession


class TrackingSessionManager:
    """
    Manager for tracking session persistence.

    Handles saving and loading TrackingSession to/from YAML files.
    Provides resume capability for interrupted tracking operations.

    Usage:
        manager = TrackingSessionManager()

        # Save session
        session = TrackingSession(session_id="shot_001", footage_path="/path/to/footage.mp4")
        manager.save(session)

        # Load session
        loaded = manager.load("shot_001")

        # List sessions
        sessions = manager.list_sessions()
    """

    def __init__(self, state_root: Optional[Path] = None):
        """
        Initialize TrackingSessionManager.

        Args:
            state_root: Root directory for state files.
                       Defaults to .gsd-state/tracking
        """
        if state_root is None:
            state_root = Path(".gsd-state/tracking")
        self.state_root = Path(state_root)
        self.sessions_dir = self.state_root / "sessions"
        self.solves_dir = self.state_root / "solves"
        self.footage_dir = self.state_root / "footage"

    def save(self, session: TrackingSession, path: Optional[Path] = None) -> None:
        """
        Save tracking session to YAML file.

        Sets timestamp before saving. Creates parent directories
        if needed. Falls back to JSON if PyYAML not available.

        Args:
            session: TrackingSession to save
            path: Optional output path. Defaults to sessions/{session_id}.yaml
        """
        if path is None:
            path = self.sessions_dir / f"{session.session_id}.yaml"

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict with timestamp
        data = session.to_dict()
        data["saved_at"] = datetime.utcnow().isoformat()

        # Write YAML or JSON
        if yaml:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load(self, session_id: str) -> TrackingSession:
        """
        Load tracking session by ID.

        Args:
            session_id: Session identifier

        Returns:
            TrackingSession loaded from file

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        path = self.sessions_dir / f"{session_id}.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        with open(path, "r", encoding="utf-8") as f:
            data_raw = f.read()

        if yaml:
            data = yaml.safe_load(data_raw)
        else:
            import json
            data = json.loads(data_raw)

        return TrackingSession.from_dict(data)

    def list_sessions(self) -> List[str]:
        """
        List all available session IDs.

        Returns:
            Sorted list of session IDs
        """
        if not self.sessions_dir.exists():
            return []

        sessions = []
        for item in self.sessions_dir.iterdir():
            if item.is_file() and item.suffix.lower() in [".yaml", ".yml", ".json"]:
                sessions.append(item.stem)

        return sorted(sessions)

    def delete(self, session_id: str) -> bool:
        """
        Delete a tracking session.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if deleted, False if not found
        """
        for ext in [".yaml", ".yml", ".json"]:
            path = self.sessions_dir / f"{session_id}{ext}"
            if path.exists():
                path.unlink()
                return True
        return False

    def get_latest_session(self) -> Optional[TrackingSession]:
        """
        Get the most recently saved session.

        Returns:
            Latest TrackingSession or None if no sessions exist
        """
        sessions = self.list_sessions()
        if not sessions:
            return None

        # Find latest by file modification time
        latest_session = None
        latest_time = None

        for session_id in sessions:
            for ext in [".yaml", ".yml", ".json"]:
                path = self.sessions_dir / f"{session_id}{ext}"
                if path.exists():
                    mtime = path.stat().st_mtime
                    if latest_time is None or mtime > latest_time:
                        try:
                            latest_time = mtime
                            latest_session = self.load(session_id)
                        except Exception:
                            continue
                    break

        return latest_session
