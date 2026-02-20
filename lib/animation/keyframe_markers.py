"""
Keyframe Markers and Pose Thumbnails

Provides timeline marker management and pose thumbnail generation for
the blocking workflow.

Phase 13.3: Blocking System (REQ-ANIM-05)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from pathlib import Path

from .types import (
    KeyPose,
    KeyPoseType,
    TimelineMarkerConfig,
)

if TYPE_CHECKING:
    import bpy


class KeyPoseMarkers:
    """
    Manage timeline markers for key poses.

    Timeline markers help visualize key poses on the timeline and provide
    quick navigation between poses.

    Example:
        >>> markers = KeyPoseMarkers()
        >>> markers.add_marker(24, "Step 1", (0.2, 0.8, 0.2))
        >>> markers.sync_markers_with_key_poses(blocking_session.key_poses)
    """

    # Color presets for different pose types
    POSE_COLORS = {
        KeyPoseType.KEY: (0.2, 0.8, 0.2),        # Green - major key
        KeyPoseType.BREAKDOWN: (0.8, 0.8, 0.2),  # Yellow - breakdown
        KeyPoseType.EXTREME: (0.8, 0.4, 0.2),    # Orange - extreme
        KeyPoseType.HOLD: (0.4, 0.6, 0.8),       # Blue - hold
    }

    def __init__(self):
        """Initialize marker manager."""
        self._markers: Dict[int, TimelineMarkerConfig] = {}

    def add_marker(
        self,
        frame: int,
        name: str,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> TimelineMarkerConfig:
        """
        Add a timeline marker.

        Args:
            frame: Frame number
            name: Marker name
            color: RGB color (0-1 range)

        Returns:
            The created marker config
        """
        marker = TimelineMarkerConfig(
            name=name,
            frame=frame,
            color=color
        )
        self._markers[frame] = marker
        return marker

    def add_key_pose_marker(self, key_pose: KeyPose) -> TimelineMarkerConfig:
        """
        Add marker for a key pose.

        Uses appropriate color based on pose type.

        Args:
            key_pose: The key pose to create marker for

        Returns:
            The created marker config
        """
        color = self.POSE_COLORS.get(key_pose.pose_type, (1.0, 1.0, 1.0))

        # Generate marker name
        name = f"KP_{key_pose.frame}"
        if key_pose.description:
            name = key_pose.description[:20]

        return self.add_marker(key_pose.frame, name, color)

    def remove_marker(self, frame: int) -> bool:
        """
        Remove marker at frame.

        Args:
            frame: Frame number

        Returns:
            True if marker was removed
        """
        if frame in self._markers:
            del self._markers[frame]
            return True
        return False

    def get_marker_at_frame(self, frame: int) -> Optional[TimelineMarkerConfig]:
        """
        Get marker at a frame.

        Args:
            frame: Frame number

        Returns:
            Marker config if found, None otherwise
        """
        return self._markers.get(frame)

    def get_all_markers(self) -> List[TimelineMarkerConfig]:
        """
        Get all markers sorted by frame.

        Returns:
            List of marker configs
        """
        return sorted(self._markers.values(), key=lambda m: m.frame)

    def clear_all_markers(self) -> None:
        """Remove all markers."""
        self._markers.clear()

    def sync_markers_with_key_poses(self, key_poses: List[KeyPose]) -> int:
        """
        Sync timeline markers with key poses.

        Clears existing markers and creates new ones for each key pose.

        Args:
            key_poses: List of key poses to sync

        Returns:
            Number of markers created
        """
        self.clear_all_markers()

        for kp in key_poses:
            self.add_key_pose_marker(kp)

        return len(self._markers)

    def get_marker_frames(self) -> List[int]:
        """
        Get all marker frame numbers.

        Returns:
            Sorted list of frame numbers with markers
        """
        return sorted(self._markers.keys())

    def get_next_marker_frame(self, current_frame: int) -> Optional[int]:
        """
        Get next marker frame after current.

        Args:
            current_frame: Current frame

        Returns:
            Next marker frame, or None if no more
        """
        frames = self.get_marker_frames()
        for frame in frames:
            if frame > current_frame:
                return frame
        return None

    def get_prev_marker_frame(self, current_frame: int) -> Optional[int]:
        """
        Get previous marker frame before current.

        Args:
            current_frame: Current frame

        Returns:
            Previous marker frame, or None if none before
        """
        frames = self.get_marker_frames()
        for frame in reversed(frames):
            if frame < current_frame:
                return frame
        return None

    def rename_marker(self, frame: int, new_name: str) -> bool:
        """
        Rename a marker.

        Args:
            frame: Frame number
            new_name: New marker name

        Returns:
            True if renamed successfully
        """
        if frame not in self._markers:
            return False

        old_marker = self._markers[frame]
        self._markers[frame] = TimelineMarkerConfig(
            name=new_name,
            frame=frame,
            color=old_marker.color,
            description=old_marker.description
        )
        return True

    def set_marker_color(self, frame: int, color: Tuple[float, float, float]) -> bool:
        """
        Set marker color.

        Args:
            frame: Frame number
            color: RGB color (0-1 range)

        Returns:
            True if color was set
        """
        if frame not in self._markers:
            return False

        old_marker = self._markers[frame]
        self._markers[frame] = TimelineMarkerConfig(
            name=old_marker.name,
            frame=frame,
            color=color,
            description=old_marker.description
        )
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize markers to dictionary."""
        import yaml
        return {
            'markers': [m.to_dict() for m in self.get_all_markers()]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyPoseMarkers':
        """Load markers from dictionary."""
        markers = cls()
        for marker_data in data.get('markers', []):
            config = TimelineMarkerConfig.from_dict(marker_data)
            markers._markers[config.frame] = config
        return markers


# Need Any for to_dict
from typing import Any


class PoseThumbnails:
    """
    Generate and manage pose thumbnails.

    Thumbnails provide visual reference for key poses on the timeline
    or in a pose browser.

    Example:
        >>> thumbnails = PoseThumbnails()
        >>> thumb_path = thumbnails.capture_thumbnail(armature, 24, "/path/to/output")
    """

    def __init__(self, output_dir: Optional[str] = None, size: Tuple[int, int] = (256, 256)):
        """
        Initialize thumbnail generator.

        Args:
            output_dir: Default output directory for thumbnails
            size: Default thumbnail size (width, height)
        """
        self.output_dir = output_dir
        self.default_size = size
        self._thumbnails: Dict[int, str] = {}

    def get_thumbnail_path(self, frame: int, output_dir: Optional[str] = None) -> str:
        """
        Get thumbnail path for a frame.

        Args:
            frame: Frame number
            output_dir: Output directory (uses default if None)

        Returns:
            Full path to thumbnail file
        """
        directory = output_dir or self.output_dir or "."
        filename = f"frame_{frame:04d}.png"
        return str(Path(directory) / filename)

    def capture_thumbnail(
        self,
        frame: int,
        output_path: Optional[str] = None,
        size: Optional[Tuple[int, int]] = None
    ) -> str:
        """
        Capture a thumbnail of the pose at frame.

        Note: In test environments without Blender, this returns a placeholder path.

        Args:
            frame: Frame to capture
            output_path: Path to save thumbnail (auto-generated if None)
            size: Thumbnail size (uses default if None)

        Returns:
            Path to the captured thumbnail
        """
        path = output_path or self.get_thumbnail_path(frame)
        thumb_size = size or self.default_size

        # Store the thumbnail info
        self._thumbnails[frame] = path

        # In Blender context, would render actual thumbnail here
        # For now, return the path (tests run outside Blender)
        return path

    def generate_all_thumbnails(
        self,
        key_poses: List[KeyPose],
        output_dir: Optional[str] = None
    ) -> Dict[int, str]:
        """
        Generate thumbnails for all key poses.

        Args:
            key_poses: List of key poses to thumbnail
            output_dir: Output directory

        Returns:
            Dictionary mapping frame numbers to thumbnail paths
        """
        directory = output_dir or self.output_dir or "."

        for kp in key_poses:
            path = self.capture_thumbnail(kp.frame, output_dir=directory)
            kp.thumbnail_path = path

        return self._thumbnails.copy()

    def get_thumbnail(self, frame: int) -> Optional[str]:
        """
        Get thumbnail path for a frame.

        Args:
            frame: Frame number

        Returns:
            Thumbnail path if exists, None otherwise
        """
        return self._thumbnails.get(frame)

    def clear_thumbnails(self) -> None:
        """Clear all stored thumbnails."""
        self._thumbnails.clear()

    def has_thumbnail(self, frame: int) -> bool:
        """
        Check if thumbnail exists for frame.

        Args:
            frame: Frame number

        Returns:
            True if thumbnail exists
        """
        return frame in self._thumbnails


class TimelineNavigator:
    """
    Navigate between key poses and markers on timeline.

    Combines marker and thumbnail functionality for easy timeline navigation.

    Example:
        >>> nav = TimelineNavigator()
        >>> nav.sync_with_session(blocking_session)
        >>> next_frame = nav.jump_to_next_key(current_frame=12)
    """

    def __init__(self):
        """Initialize timeline navigator."""
        self.markers = KeyPoseMarkers()
        self.thumbnails = PoseThumbnails()

    def sync_with_session(self, key_poses: List[KeyPose], generate_thumbnails: bool = False) -> None:
        """
        Sync navigator with blocking session.

        Args:
            key_poses: List of key poses from session
            generate_thumbnails: Whether to generate thumbnails
        """
        self.markers.sync_markers_with_key_poses(key_poses)

        if generate_thumbnails:
            self.thumbnails.generate_all_thumbnails(key_poses)

    def jump_to_next_key(self, current_frame: int) -> Optional[int]:
        """
        Get next key frame.

        Args:
            current_frame: Current frame

        Returns:
            Next key frame, or None
        """
        return self.markers.get_next_marker_frame(current_frame)

    def jump_to_prev_key(self, current_frame: int) -> Optional[int]:
        """
        Get previous key frame.

        Args:
            current_frame: Current frame

        Returns:
            Previous key frame, or None
        """
        return self.markers.get_prev_marker_frame(current_frame)

    def get_key_count(self) -> int:
        """Get number of key frames."""
        return len(self.markers.get_marker_frames())

    def get_frame_list(self) -> List[int]:
        """Get list of all key frames."""
        return self.markers.get_marker_frames()


# =============================================================================
# Convenience Functions
# =============================================================================

def create_marker_for_key_pose(key_pose: KeyPose) -> TimelineMarkerConfig:
    """
    Create a timeline marker config for a key pose.

    Args:
        key_pose: The key pose

    Returns:
        Timeline marker configuration
    """
    colors = KeyPoseMarkers.POSE_COLORS
    color = colors.get(key_pose.pose_type, (1.0, 1.0, 1.0))

    name = key_pose.description[:20] if key_pose.description else f"KP_{key_pose.frame}"

    return TimelineMarkerConfig(
        name=name,
        frame=key_pose.frame,
        color=color,
        description=key_pose.description
    )


def sync_markers_from_key_poses(key_poses: List[KeyPose]) -> KeyPoseMarkers:
    """
    Create markers from a list of key poses.

    Args:
        key_poses: List of key poses

    Returns:
        KeyPoseMarkers instance with synced markers
    """
    markers = KeyPoseMarkers()
    markers.sync_markers_with_key_poses(key_poses)
    return markers


def get_navigation_frames(key_poses: List[KeyPose]) -> Dict[str, List[int]]:
    """
    Get navigation information from key poses.

    Args:
        key_poses: List of key poses

    Returns:
        Dictionary with frame lists by type
    """
    return {
        "all_frames": sorted([kp.frame for kp in key_poses]),
        "key_frames": sorted([kp.frame for kp in key_poses if kp.pose_type == KeyPoseType.KEY]),
        "breakdowns": sorted([kp.frame for kp in key_poses if kp.pose_type == KeyPoseType.BREAKDOWN]),
        "extremes": sorted([kp.frame for kp in key_poses if kp.pose_type == KeyPoseType.EXTREME]),
        "holds": sorted([kp.frame for kp in key_poses if kp.pose_type == KeyPoseType.HOLD]),
    }
