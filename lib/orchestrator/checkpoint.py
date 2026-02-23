"""
Checkpoint System

Provides save/resume functionality for scene generation.
Enables fault tolerance and long-running generation recovery.

Implements REQ-SO-12: Checkpoint/Resume.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import uuid
import shutil


class CheckpointError(Exception):
    """Checkpoint-related error."""
    pass


@dataclass
class Checkpoint:
    """
    Generation checkpoint.

    Attributes:
        checkpoint_id: Unique checkpoint identifier
        session_id: Session this checkpoint belongs to
        stage: Current generation stage
        status: Checkpoint status
        timestamp: When checkpoint was created
        scene_outline: Scene outline at checkpoint
        asset_selections: Asset selections made so far
        generation_state: Generator-specific state
        progress: Progress information
        errors: Errors encountered
        metadata: Additional metadata
    """
    checkpoint_id: str = ""
    session_id: str = ""
    stage: str = "initialized"
    status: str = "active"
    timestamp: str = ""
    scene_outline: Optional[Dict[str, Any]] = None
    asset_selections: List[Dict[str, Any]] = field(default_factory=list)
    generation_state: Dict[str, Any] = field(default_factory=dict)
    progress: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "stage": self.stage,
            "status": self.status,
            "timestamp": self.timestamp,
            "scene_outline": self.scene_outline,
            "asset_selections": self.asset_selections,
            "generation_state": self.generation_state,
            "progress": self.progress,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data.get("checkpoint_id", ""),
            session_id=data.get("session_id", ""),
            stage=data.get("stage", "initialized"),
            status=data.get("status", "active"),
            timestamp=data.get("timestamp", ""),
            scene_outline=data.get("scene_outline"),
            asset_selections=data.get("asset_selections", []),
            generation_state=data.get("generation_state", {}),
            progress=data.get("progress", {}),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
        )


class GenerationStage:
    """Generation stage constants."""
    INITIALIZED = "initialized"
    PARSING = "parsing"
    REQUIREMENT_RESOLUTION = "requirement_resolution"
    ASSET_SELECTION = "asset_selection"
    PLACEMENT = "placement"
    GEOMETRY_GENERATION = "geometry_generation"
    MATERIAL_APPLICATION = "material_application"
    LIGHTING_SETUP = "lighting_setup"
    CAMERA_SETUP = "camera_setup"
    POST_PROCESSING = "post_processing"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"


class CheckpointManager:
    """
    Manages generation checkpoints.

    Provides save, load, list, and delete operations.
    Supports automatic checkpointing at stage transitions.

    Usage:
        manager = CheckpointManager(".checkpoints")
        checkpoint = manager.create_checkpoint(outline, stage="asset_selection")
        # ... generation continues ...
        manager.update_checkpoint(checkpoint.checkpoint_id, stage="placement")
        # Resume later
        checkpoint = manager.load_checkpoint(checkpoint_id)
    """

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._current_session = self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _generate_checkpoint_id(self) -> str:
        """Generate unique checkpoint ID."""
        return f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}"

    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        """Get path to checkpoint file."""
        return self.checkpoint_dir / f"{checkpoint_id}.json"

    def _get_session_path(self, session_id: str) -> Path:
        """Get path to session directory."""
        return self.checkpoint_dir / session_id

    def create_checkpoint(
        self,
        scene_outline: Optional[Any] = None,
        stage: str = GenerationStage.INITIALIZED,
        generation_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        """
        Create new checkpoint.

        Args:
            scene_outline: Scene outline at checkpoint
            stage: Current generation stage
            generation_state: Generator-specific state
            metadata: Additional metadata

        Returns:
            Created checkpoint
        """
        checkpoint = Checkpoint(
            checkpoint_id=self._generate_checkpoint_id(),
            session_id=self._current_session,
            stage=stage,
            status="active",
            timestamp=datetime.now().isoformat(),
            generation_state=generation_state or {},
            metadata=metadata or {},
        )

        # Convert scene outline to dict if needed
        if scene_outline is not None:
            if hasattr(scene_outline, "to_dict"):
                checkpoint.scene_outline = scene_outline.to_dict()
            else:
                checkpoint.scene_outline = scene_outline

        # Save checkpoint
        self._save_checkpoint(checkpoint)

        return checkpoint

    def update_checkpoint(
        self,
        checkpoint_id: str,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        asset_selections: Optional[List[Dict[str, Any]]] = None,
        generation_state: Optional[Dict[str, Any]] = None,
        progress: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        append_errors: bool = False,
    ) -> Optional[Checkpoint]:
        """
        Update existing checkpoint.

        Args:
            checkpoint_id: Checkpoint to update
            stage: New stage (optional)
            status: New status (optional)
            asset_selections: Asset selections (optional)
            generation_state: Generator state (optional)
            progress: Progress info (optional)
            errors: Errors (optional)
            append_errors: Append to existing errors instead of replacing

        Returns:
            Updated checkpoint or None if not found
        """
        checkpoint = self.load_checkpoint(checkpoint_id)
        if not checkpoint:
            return None

        # Update fields
        if stage is not None:
            checkpoint.stage = stage
        if status is not None:
            checkpoint.status = status
        if asset_selections is not None:
            checkpoint.asset_selections = asset_selections
        if generation_state is not None:
            checkpoint.generation_state.update(generation_state)
        if progress is not None:
            checkpoint.progress.update(progress)
        if errors is not None:
            if append_errors:
                checkpoint.errors.extend(errors)
            else:
                checkpoint.errors = errors

        # Update timestamp
        checkpoint.timestamp = datetime.now().isoformat()

        # Save updated checkpoint
        self._save_checkpoint(checkpoint)

        return checkpoint

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Load checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Checkpoint or None if not found
        """
        path = self._get_checkpoint_path(checkpoint_id)
        if not path.exists():
            return None

        try:
            with open(path, "r") as f:
                data = json.load(f)
            return Checkpoint.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}")

    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to disk."""
        path = self._get_checkpoint_path(checkpoint.checkpoint_id)
        with open(path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

    def list_checkpoints(
        self,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List checkpoints.

        Args:
            session_id: Filter by session
            status: Filter by status
            stage: Filter by stage
            limit: Maximum number to return

        Returns:
            List of checkpoint summaries
        """
        checkpoints = []

        for path in self.checkpoint_dir.glob("cp_*.json"):
            try:
                with open(path, "r") as f:
                    data = json.load(f)

                # Apply filters
                if session_id and data.get("session_id") != session_id:
                    continue
                if status and data.get("status") != status:
                    continue
                if stage and data.get("stage") != stage:
                    continue

                checkpoints.append({
                    "checkpoint_id": data.get("checkpoint_id"),
                    "session_id": data.get("session_id"),
                    "stage": data.get("stage"),
                    "status": data.get("status"),
                    "timestamp": data.get("timestamp"),
                })

            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by timestamp descending
        checkpoints.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return checkpoints[:limit]

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete checkpoint.

        Args:
            checkpoint_id: Checkpoint to delete

        Returns:
            True if deleted
        """
        path = self._get_checkpoint_path(checkpoint_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def delete_session(self, session_id: str) -> int:
        """
        Delete all checkpoints for a session.

        Args:
            session_id: Session to delete

        Returns:
            Number of checkpoints deleted
        """
        count = 0
        for cp in self.list_checkpoints(session_id=session_id, limit=1000):
            if self.delete_checkpoint(cp["checkpoint_id"]):
                count += 1
        return count

    def clean_old_checkpoints(self, max_age_days: int = 7) -> int:
        """
        Remove checkpoints older than specified age.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of checkpoints removed
        """
        count = 0
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)

        for path in self.checkpoint_dir.glob("cp_*.json"):
            try:
                with open(path, "r") as f:
                    data = json.load(f)

                timestamp_str = data.get("timestamp", "")
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str).timestamp()
                    if timestamp < cutoff:
                        path.unlink()
                        count += 1

            except (json.JSONDecodeError, ValueError):
                # Remove corrupted checkpoints
                path.unlink()
                count += 1

        return count

    def get_latest_checkpoint(self, session_id: Optional[str] = None) -> Optional[Checkpoint]:
        """
        Get most recent checkpoint.

        Args:
            session_id: Optional session filter

        Returns:
            Latest checkpoint or None
        """
        checkpoints = self.list_checkpoints(session_id=session_id, limit=1)
        if not checkpoints:
            return None
        return self.load_checkpoint(checkpoints[0]["checkpoint_id"])

    def get_session_checkpoints(self, session_id: str) -> List[Checkpoint]:
        """
        Get all checkpoints for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of checkpoints
        """
        summaries = self.list_checkpoints(session_id=session_id, limit=1000)
        return [self.load_checkpoint(s["checkpoint_id"]) for s in summaries if self.load_checkpoint(s["checkpoint_id"])]


class CheckpointContext:
    """
    Context manager for automatic checkpointing.

    Usage:
        with CheckpointContext(manager, outline, "asset_selection") as cp:
            # Do work
            selections = select_assets(outline)
            cp.update(asset_selections=selections)
    """

    def __init__(
        self,
        manager: CheckpointManager,
        scene_outline: Optional[Any] = None,
        stage: str = GenerationStage.INITIALIZED,
        auto_update_stage: bool = True,
    ):
        """
        Initialize checkpoint context.

        Args:
            manager: Checkpoint manager
            scene_outline: Scene outline
            stage: Initial stage
            auto_update_stage: Automatically update stage on exit
        """
        self.manager = manager
        self.scene_outline = scene_outline
        self.stage = stage
        self.auto_update_stage = auto_update_stage
        self.checkpoint: Optional[Checkpoint] = None

    def __enter__(self) -> "CheckpointContext":
        """Enter context and create checkpoint."""
        self.checkpoint = self.manager.create_checkpoint(
            scene_outline=self.scene_outline,
            stage=self.stage,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and update checkpoint."""
        if self.checkpoint:
            if exc_type is not None:
                # Record error
                self.manager.update_checkpoint(
                    self.checkpoint.checkpoint_id,
                    stage=GenerationStage.FAILED,
                    status="failed",
                    errors=[str(exc_val)],
                    append_errors=True,
                )
            elif self.auto_update_stage:
                # Mark complete
                self.manager.update_checkpoint(
                    self.checkpoint.checkpoint_id,
                    status="completed",
                )

    def update(self, **kwargs) -> None:
        """Update checkpoint with current state."""
        if self.checkpoint:
            self.manager.update_checkpoint(self.checkpoint.checkpoint_id, **kwargs)


def resume_from_checkpoint(
    checkpoint_id: str,
    checkpoint_dir: str = ".checkpoints",
) -> Optional[Checkpoint]:
    """
    Resume generation from checkpoint.

    Args:
        checkpoint_id: Checkpoint to resume from
        checkpoint_dir: Checkpoint directory

    Returns:
        Loaded checkpoint or None
    """
    manager = CheckpointManager(checkpoint_dir)
    return manager.load_checkpoint(checkpoint_id)


def auto_checkpoint(
    manager: CheckpointManager,
    stage: str,
    scene_outline: Any,
    state: Dict[str, Any],
) -> Checkpoint:
    """
    Create automatic checkpoint at stage transition.

    Args:
        manager: Checkpoint manager
        stage: Current stage
        scene_outline: Scene outline
        state: Generation state

    Returns:
        Created checkpoint
    """
    return manager.create_checkpoint(
        scene_outline=scene_outline,
        stage=stage,
        generation_state=state,
        metadata={"auto": True},
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CheckpointError",
    "Checkpoint",
    "GenerationStage",
    "CheckpointManager",
    "CheckpointContext",
    "resume_from_checkpoint",
    "auto_checkpoint",
]
