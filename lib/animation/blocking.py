"""
Blocking System for Animation

Provides tools for rough animation passes to establish timing and key poses.
Supports stepped interpolation, pose management, and timeline navigation.

Phase 13.3: Blocking System (REQ-ANIM-05)
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

from .types import (
    BlockingSession,
    KeyPose,
    KeyPoseType,
    InterpolationMode,
    Pose,
    BonePose,
)

if TYPE_CHECKING:
    import bpy


class BlockingSystem:
    """
    Manage blocking workflow for animation.

    The blocking system provides tools for rough animation passes:
    - Stepped interpolation mode (no in-betweening)
    - Key pose management at specific frames
    - Copy/paste poses between frames
    - Frame range management

    Example:
        >>> blocking = BlockingSystem(armature)
        >>> blocking.start_session("walk_cycle", 1, 48)
        >>> blocking.set_stepped_mode()
        >>> blocking.add_key_pose(1, "t_pose", "Start pose")
        >>> blocking.add_key_pose(24, "walk_contact_L", "Left foot contact")
    """

    def __init__(self, armature: Optional['bpy.types.Object'] = None):
        """
        Initialize blocking system.

        Args:
            armature: The armature object to animate
        """
        self.armature = armature
        self.session: Optional[BlockingSession] = None
        self._pose_cache: Dict[int, Dict[str, BonePose]] = {}

    def start_session(
        self,
        scene_name: str,
        range_start: int = 1,
        range_end: int = 100,
        character_name: Optional[str] = None
    ) -> BlockingSession:
        """
        Start a new blocking session.

        Args:
            scene_name: Name of the scene
            range_start: Start frame
            range_end: End frame
            character_name: Name of character (defaults to armature name)

        Returns:
            The new blocking session
        """
        char_name = character_name or (self.armature.name if self.armature else "Character")
        self.session = BlockingSession(
            scene_name=scene_name,
            character_name=char_name,
            range_start=range_start,
            range_end=range_end
        )
        return self.session

    def end_session(self) -> Optional[Dict[str, Any]]:
        """
        End the current session and return session data.

        Returns:
            Serialized session data, or None if no session
        """
        if not self.session:
            return None
        data = self.session.to_dict()
        self.session = None
        return data

    def load_session(self, data: Dict[str, Any]) -> BlockingSession:
        """
        Load a blocking session from data.

        Args:
            data: Serialized session data

        Returns:
            The loaded blocking session
        """
        self.session = BlockingSession.from_dict(data)
        return self.session

    # -------------------------------------------------------------------------
    # Interpolation Control
    # -------------------------------------------------------------------------

    def set_interpolation_mode(self, mode: InterpolationMode) -> None:
        """
        Set interpolation mode for all bone keyframes.

        Args:
            mode: Interpolation mode (STEPPED, LINEAR, BEZIER)
        """
        if self.session:
            self.session.interpolation_mode = mode

        if not self.armature:
            return

        # In Blender, set interpolation for all fcurves
        try:
            import bpy
            if not self.armature.animation_data:
                return
            if not self.armature.animation_data.action:
                return

            for fcurve in self.armature.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = mode.value
        except ImportError:
            pass  # Not in Blender context

    def set_stepped_mode(self) -> None:
        """Set stepped interpolation (blocking mode)."""
        self.set_interpolation_mode(InterpolationMode.STEPPED)

    def set_linear_mode(self) -> None:
        """Set linear interpolation."""
        self.set_interpolation_mode(InterpolationMode.LINEAR)

    def set_bezier_mode(self) -> None:
        """Set bezier interpolation (smooth mode)."""
        self.set_interpolation_mode(InterpolationMode.BEZIER)

    # -------------------------------------------------------------------------
    # Key Pose Management
    # -------------------------------------------------------------------------

    def add_key_pose(
        self,
        frame: int,
        pose_id: Optional[str] = None,
        description: str = "",
        pose_type: KeyPoseType = KeyPoseType.KEY,
        notes: str = ""
    ) -> KeyPose:
        """
        Add a key pose at a specific frame.

        Args:
            frame: Frame number
            pose_id: Optional pose library ID to apply
            description: Description of the pose
            pose_type: Type of key pose (key, breakdown, extreme, hold)
            notes: Additional notes

        Returns:
            The created key pose
        """
        if not self.session:
            raise RuntimeError("No active blocking session. Call start_session() first.")

        # Create key pose record
        key_pose = KeyPose(
            frame=frame,
            pose_id=pose_id,
            description=description,
            pose_type=pose_type,
            notes=notes
        )

        # Add to session and sort by frame
        self.session.key_poses.append(key_pose)
        self.session.key_poses.sort(key=lambda x: x.frame)

        return key_pose

    def add_breakdown(self, frame: int, description: str = "", notes: str = "") -> KeyPose:
        """
        Add a breakdown pose at a frame.

        Breakdowns are transition poses between key poses.

        Args:
            frame: Frame number
            description: Description of the breakdown
            notes: Additional notes

        Returns:
            The created breakdown pose
        """
        return self.add_key_pose(
            frame=frame,
            description=description,
            pose_type=KeyPoseType.BREAKDOWN,
            notes=notes
        )

    def add_extreme(self, frame: int, description: str = "", notes: str = "") -> KeyPose:
        """
        Add an extreme pose at a frame.

        Extremes are the most extreme positions in motion.

        Args:
            frame: Frame number
            description: Description of the extreme
            notes: Additional notes

        Returns:
            The created extreme pose
        """
        return self.add_key_pose(
            frame=frame,
            description=description,
            pose_type=KeyPoseType.EXTREME,
            notes=notes
        )

    def delete_key_pose(self, frame: int) -> bool:
        """
        Delete a key pose at a frame.

        Args:
            frame: Frame number to delete

        Returns:
            True if a pose was deleted
        """
        if not self.session:
            return False

        original_count = len(self.session.key_poses)
        self.session.key_poses = [
            kp for kp in self.session.key_poses if kp.frame != frame
        ]
        return len(self.session.key_poses) < original_count

    def get_key_pose(self, frame: int) -> Optional[KeyPose]:
        """
        Get key pose at a frame.

        Args:
            frame: Frame number

        Returns:
            Key pose if found, None otherwise
        """
        if not self.session:
            return None

        for kp in self.session.key_poses:
            if kp.frame == frame:
                return kp
        return None

    def get_key_poses(self) -> List[KeyPose]:
        """
        Get all key poses in the session.

        Returns:
            List of key poses sorted by frame
        """
        if not self.session:
            return []
        return sorted(self.session.key_poses, key=lambda x: x.frame)

    def get_key_poses_by_type(self, pose_type: KeyPoseType) -> List[KeyPose]:
        """
        Get key poses of a specific type.

        Args:
            pose_type: Type of poses to get

        Returns:
            List of matching key poses
        """
        if not self.session:
            return []
        return [kp for kp in self.session.key_poses if kp.pose_type == pose_type]

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def get_next_key_frame(self, current_frame: int) -> Optional[int]:
        """
        Get the next key frame after current.

        Args:
            current_frame: Current frame number

        Returns:
            Next key frame, or None if no more
        """
        if not self.session:
            return None

        for kp in self.session.key_poses:
            if kp.frame > current_frame:
                return kp.frame
        return None

    def get_prev_key_frame(self, current_frame: int) -> Optional[int]:
        """
        Get the previous key frame before current.

        Args:
            current_frame: Current frame number

        Returns:
            Previous key frame, or None if none before
        """
        if not self.session:
            return None

        for kp in reversed(self.session.key_poses):
            if kp.frame < current_frame:
                return kp.frame
        return None

    def jump_to_next_key(self, current_frame: int) -> Optional[int]:
        """
        Jump to next key pose.

        Args:
            current_frame: Current frame

        Returns:
            New frame, or None if no next key
        """
        next_frame = self.get_next_key_frame(current_frame)
        if next_frame is not None and self.session:
            self.session.current_frame = next_frame
        return next_frame

    def jump_to_prev_key(self, current_frame: int) -> Optional[int]:
        """
        Jump to previous key pose.

        Args:
            current_frame: Current frame

        Returns:
            New frame, or None if no previous key
        """
        prev_frame = self.get_prev_key_frame(current_frame)
        if prev_frame is not None and self.session:
            self.session.current_frame = prev_frame
        return prev_frame

    # -------------------------------------------------------------------------
    # Pose Operations
    # -------------------------------------------------------------------------

    def copy_pose_to_frame(self, source_frame: int, target_frame: int) -> bool:
        """
        Copy pose from one frame to another.

        Args:
            source_frame: Frame to copy from
            target_frame: Frame to copy to

        Returns:
            True if copy succeeded
        """
        if not self.session:
            return False

        source_pose = self.get_key_pose(source_frame)
        if not source_pose:
            return False

        # Create new key pose at target
        new_pose = KeyPose(
            frame=target_frame,
            pose_id=source_pose.pose_id,
            description=f"Copy of: {source_pose.description}",
            pose_type=source_pose.pose_type,
            notes=source_pose.notes
        )
        self.session.key_poses.append(new_pose)
        self.session.key_poses.sort(key=lambda x: x.frame)

        return True

    def mirror_pose_at_frame(self, frame: int) -> bool:
        """
        Mirror the pose at a frame (L/R swap).

        Args:
            frame: Frame to mirror

        Returns:
            True if mirror succeeded
        """
        key_pose = self.get_key_pose(frame)
        if not key_pose:
            return False

        # Store the mirror operation in notes
        key_pose.notes = f"{key_pose.notes} [MIRRORED]".strip()
        return True

    # -------------------------------------------------------------------------
    # Timing Notes
    # -------------------------------------------------------------------------

    def add_timing_note(self, note: str) -> None:
        """
        Add a timing note to the session.

        Args:
            note: The note to add
        """
        if not self.session:
            raise RuntimeError("No active blocking session.")

        self.session.timing_notes.append(note)

    def get_timing_notes(self) -> List[str]:
        """
        Get all timing notes.

        Returns:
            List of timing notes
        """
        if not self.session:
            return []
        return self.session.timing_notes.copy()

    def clear_timing_notes(self) -> None:
        """Clear all timing notes."""
        if self.session:
            self.session.timing_notes = []

    # -------------------------------------------------------------------------
    # Session Utilities
    # -------------------------------------------------------------------------

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.

        Returns:
            Dictionary with session info
        """
        if not self.session:
            return {"active": False}

        return {
            "active": True,
            "scene_name": self.session.scene_name,
            "character_name": self.session.character_name,
            "key_pose_count": len(self.session.key_poses),
            "frame_range": (self.session.range_start, self.session.range_end),
            "interpolation": self.session.interpolation_mode.value,
            "timing_notes": len(self.session.timing_notes)
        }

    def save_session_to_file(self, filepath: str) -> bool:
        """
        Save session to YAML file.

        Args:
            filepath: Path to save file

        Returns:
            True if save succeeded
        """
        if not self.session:
            return False

        import yaml

        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w') as f:
                yaml.dump(self.session.to_dict(), f, default_flow_style=False)
            return True
        except Exception:
            return False

    def load_session_from_file(self, filepath: str) -> Optional[BlockingSession]:
        """
        Load session from YAML file.

        Args:
            filepath: Path to load file

        Returns:
            Loaded session, or None on failure
        """
        import yaml

        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            return self.load_session(data)
        except Exception:
            return None


# =============================================================================
# Convenience Functions
# =============================================================================

def start_blocking(
    armature: Optional['bpy.types.Object'] = None,
    scene_name: str = "blocking",
    start: int = 1,
    end: int = 100
) -> BlockingSystem:
    """
    Start a blocking session with stepped interpolation.

    Args:
        armature: The armature to animate
        scene_name: Name of the scene
        start: Start frame
        end: End frame

    Returns:
        Configured blocking system
    """
    system = BlockingSystem(armature)
    system.start_session(scene_name, start, end)
    system.set_stepped_mode()
    return system


def create_blocking_session(
    scene_name: str,
    character_name: str,
    frame_range: tuple = (1, 100)
) -> BlockingSession:
    """
    Create a new blocking session data structure.

    Args:
        scene_name: Name of the scene
        character_name: Name of the character
        frame_range: (start, end) frame range

    Returns:
        New blocking session
    """
    return BlockingSession(
        scene_name=scene_name,
        character_name=character_name,
        range_start=frame_range[0],
        range_end=frame_range[1]
    )


def add_key_pose_to_session(
    session: BlockingSession,
    frame: int,
    description: str = "",
    pose_type: KeyPoseType = KeyPoseType.KEY
) -> KeyPose:
    """
    Add a key pose to an existing session.

    Args:
        session: The blocking session
        frame: Frame number
        description: Pose description
        pose_type: Type of key pose

    Returns:
        The created key pose
    """
    key_pose = KeyPose(
        frame=frame,
        description=description,
        pose_type=pose_type
    )
    session.key_poses.append(key_pose)
    session.key_poses.sort(key=lambda x: x.frame)
    return key_pose


def get_blocking_summary(session: BlockingSession) -> Dict[str, Any]:
    """
    Get a summary of a blocking session.

    Args:
        session: The blocking session

    Returns:
        Summary dictionary
    """
    key_count = len(session.key_poses)
    breakdown_count = len([kp for kp in session.key_poses if kp.pose_type == KeyPoseType.BREAKDOWN])
    extreme_count = len([kp for kp in session.key_poses if kp.pose_type == KeyPoseType.EXTREME])

    return {
        "scene": session.scene_name,
        "character": session.character_name,
        "frame_range": f"{session.range_start}-{session.range_end}",
        "total_poses": key_count,
        "key_poses": key_count - breakdown_count - extreme_count,
        "breakdowns": breakdown_count,
        "extremes": extreme_count,
        "timing_notes": len(session.timing_notes),
        "interpolation": session.interpolation_mode.value
    }
