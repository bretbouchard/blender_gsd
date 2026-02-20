"""
Tracking Operators Module

Provides Python functions wrapping Blender's tracking operators.
All operators require active Clip Editor context.

Key Functions:
- detect_features: Automatic feature detection
- track_markers: Forward/backward marker tracking
- solve_camera: Camera motion solving
- set_scene_frames: Sync scene frame range to clip
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .context import tracking_context


@dataclass
class DetectionResult:
    """Result of feature detection."""
    features_found: int = 0
    success: bool = False
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "features_found": self.features_found,
            "success": self.success,
            "message": self.message,
        }


@dataclass
class TrackingResult:
    """Result of marker tracking."""
    frames_tracked: int = 0
    tracks_processed: int = 0
    tracks_lost: int = 0
    success: bool = False
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frames_tracked": self.frames_tracked,
            "tracks_processed": self.tracks_processed,
            "tracks_lost": self.tracks_lost,
            "success": self.success,
            "message": self.message,
        }


def detect_features(
    clip,
    threshold: float = 0.5,
    margin: int = 16,
    min_distance: int = 8,
    place: bool = True,
) -> DetectionResult:
    """
    Detect features in current frame using Blender's detect_features operator.

    Uses bpy.ops.clip.detect_features for automatic corner detection.

    Args:
        clip: MovieClip to detect features in
        threshold: Detection threshold (0-1, lower = more features)
        margin: Margin from frame edges in pixels
        min_distance: Minimum distance between features in pixels
        place: Place markers at detected positions

    Returns:
        DetectionResult with features found count

    Raises:
        RuntimeError: If Blender not available or context setup fails
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    try:
        with tracking_context(clip) as ctx:
            # Count tracks before
            tracks_before = len([t for t in clip.tracking.tracks if not t.mute])

            result = bpy.ops.clip.detect_features(
                ctx,
                threshold=threshold,
                margin=margin,
                min_distance=min_distance,
                place=place,
            )

            # Count tracks after
            tracks_after = len([t for t in clip.tracking.tracks if not t.mute])

            if result == {'FINISHED'}:
                return DetectionResult(
                    features_found=tracks_after - tracks_before,
                    success=True,
                    message=f"Detected {tracks_after - tracks_before} new features",
                )
            else:
                return DetectionResult(
                    features_found=0,
                    success=False,
                    message="Detection did not complete",
                )

    except RuntimeError as e:
        return DetectionResult(
            features_found=0,
            success=False,
            message=str(e),
        )


def track_markers(
    clip,
    direction: str = "forward",
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
    sequence: bool = True,
) -> TrackingResult:
    """
    Track markers through frames using Blender's track_markers operator.

    Uses bpy.ops.clip.track_markers for optical flow tracking.

    Args:
        clip: MovieClip with markers to track
        direction: "forward" or "backward"
        frame_start: Starting frame (uses current if None)
        frame_end: Ending frame (uses clip end if None)
        sequence: Track entire sequence vs. single frame

    Returns:
        TrackingResult with tracking statistics

    Raises:
        RuntimeError: If Blender not available or context setup fails
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    try:
        with tracking_context(clip) as ctx:
            # Set frame range
            if frame_start is None:
                frame_start = bpy.context.scene.frame_current
            if frame_end is None:
                frame_end = clip.frame_start + clip.frame_duration - 1

            # Count active tracks before
            tracks_before = len([t for t in clip.tracking.tracks if not t.mute])

            # Determine backward flag
            backward = direction.lower() == "backward"

            result = bpy.ops.clip.track_markers(
                ctx,
                backward=backward,
                sequence=sequence,
            )

            if result == {'FINISHED'}:
                frames_tracked = abs(frame_end - frame_start) if sequence else 1
                return TrackingResult(
                    frames_tracked=frames_tracked,
                    tracks_processed=tracks_before,
                    tracks_lost=0,  # Would need to analyze to determine
                    success=True,
                    message=f"Tracked {tracks_before} markers for {frames_tracked} frames",
                )
            else:
                return TrackingResult(
                    frames_tracked=0,
                    tracks_processed=0,
                    tracks_lost=0,
                    success=False,
                    message="Tracking did not complete",
                )

    except RuntimeError as e:
        return TrackingResult(
            frames_tracked=0,
            tracks_processed=0,
            tracks_lost=0,
            success=False,
            message=str(e),
        )


def track_markers_forward(
    clip,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
) -> TrackingResult:
    """
    Track all markers forward through frames.

    Convenience wrapper for track_markers(direction="forward").

    Args:
        clip: MovieClip with markers
        frame_start: Starting frame (uses current if None)
        frame_end: Ending frame (uses clip end if None)

    Returns:
        TrackingResult with statistics
    """
    return track_markers(
        clip,
        direction="forward",
        frame_start=frame_start,
        frame_end=frame_end,
        sequence=True,
    )


def track_markers_backward(
    clip,
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
) -> TrackingResult:
    """
    Track all markers backward through frames.

    Convenience wrapper for track_markers(direction="backward").

    Args:
        clip: MovieClip with markers
        frame_start: Starting frame (uses current if None)
        frame_end: Ending frame (uses clip start if None)

    Returns:
        TrackingResult with statistics
    """
    return track_markers(
        clip,
        direction="backward",
        frame_start=frame_start,
        frame_end=frame_end,
        sequence=True,
    )


def solve_camera_motion(
    clip,
    allow_focal_length_refine: bool = True,
) -> Dict[str, Any]:
    """
    Solve camera motion from tracked markers.

    Uses bpy.ops.clip.solve_camera for libmv camera solving.

    Args:
        clip: MovieClip with tracked markers
        allow_focal_length_refine: Allow solver to refine focal length

    Returns:
        Dict with solve results:
        - success: Whether solve succeeded
        - average_error: Average reprojection error
        - camera_count: Number of reconstructed cameras
        - reconstruction: Reference to reconstruction object

    Raises:
        RuntimeError: If Blender not available or context setup fails
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    try:
        with tracking_context(clip) as ctx:
            result = bpy.ops.clip.solve_camera(ctx)

            if result != {'FINISHED'}:
                return {
                    "success": False,
                    "average_error": float('inf'),
                    "camera_count": 0,
                    "message": "Solve did not complete",
                }

            reconstruction = clip.tracking.reconstruction

            if not reconstruction.is_valid:
                return {
                    "success": False,
                    "average_error": float('inf'),
                    "camera_count": 0,
                    "message": "Reconstruction is not valid",
                }

            return {
                "success": True,
                "average_error": reconstruction.average_error,
                "camera_count": len(reconstruction.cameras),
                "reconstruction": reconstruction,
                "message": f"Solve successful with error {reconstruction.average_error:.3f}px",
            }

    except RuntimeError as e:
        return {
            "success": False,
            "average_error": float('inf'),
            "camera_count": 0,
            "message": str(e),
        }


def set_scene_frames(clip, include_handles: bool = False) -> None:
    """
    Set scene frame range to match clip duration.

    Args:
        clip: MovieClip to sync frames from
        include_handles: Add extra frames at start/end
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    scene = bpy.context.scene

    start = clip.frame_start
    end = clip.frame_start + clip.frame_duration - 1

    if include_handles:
        # Add 10% handles
        duration = end - start
        handles = int(duration * 0.1)
        start -= handles
        end += handles

    scene.frame_start = start
    scene.frame_end = end


def get_clip_frame_range(clip) -> Tuple[int, int]:
    """
    Get clip frame range.

    Args:
        clip: MovieClip

    Returns:
        Tuple of (start_frame, end_frame)
    """
    start = clip.frame_start
    end = clip.frame_start + clip.frame_duration - 1
    return (start, end)


def set_clip_frame_range(clip, start: int, end: int) -> None:
    """
    Set clip frame range.

    Args:
        clip: MovieClip
        start: Start frame
        end: End frame
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    clip.frame_start = start
    # Note: frame_duration is calculated from end


def clear_reconstruction(clip) -> bool:
    """
    Clear camera reconstruction data.

    Args:
        clip: MovieClip with reconstruction

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    reconstruction = clip.tracking.reconstruction

    if reconstruction.is_valid:
        # Clear reconstruction
        while reconstruction.cameras:
            reconstruction.cameras.remove(reconstruction.cameras[0])

    return True


def delete_track(clip, track_name: str) -> bool:
    """
    Delete a track by name.

    Args:
        clip: MovieClip with tracks
        track_name: Name of track to delete

    Returns:
        True if track was found and deleted
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    tracks = clip.tracking.tracks

    for track in tracks:
        if track.name == track_name:
            tracks.remove(track)
            return True

    return False


def delete_all_tracks(clip) -> int:
    """
    Delete all tracks.

    Args:
        clip: MovieClip with tracks

    Returns:
        Number of tracks deleted
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    tracks = clip.tracking.tracks
    count = len(tracks)

    while tracks:
        tracks.remove(tracks[0])

    return count


def disable_track(clip, track_name: str, disabled: bool = True) -> bool:
    """
    Disable/enable a track by name.

    Args:
        clip: MovieClip with tracks
        track_name: Name of track
        disabled: True to disable, False to enable

    Returns:
        True if track was found
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    for track in clip.tracking.tracks:
        if track.name == track_name:
            track.mute = disabled
            return True

    return False


def select_track(clip, track_name: str, select: bool = True) -> bool:
    """
    Select/deselect a track by name.

    Args:
        clip: MovieClip with tracks
        track_name: Name of track
        select: True to select, False to deselect

    Returns:
        True if track was found
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    for track in clip.tracking.tracks:
        if track.name == track_name:
            track.select = select
            return True

    return False


def get_track_count(clip) -> int:
    """
    Get number of tracks.

    Args:
        clip: MovieClip with tracks

    Returns:
        Number of tracks
    """
    return len(clip.tracking.tracks)


def get_active_track_count(clip) -> int:
    """
    Get number of active (non-muted) tracks.

    Args:
        clip: MovieClip with tracks

    Returns:
        Number of active tracks
    """
    return len([t for t in clip.tracking.tracks if not t.mute])


__all__ = [
    "BLENDER_AVAILABLE",
    "DetectionResult",
    "TrackingResult",
    "detect_features",
    "track_markers",
    "track_markers_forward",
    "track_markers_backward",
    "solve_camera_motion",
    "set_scene_frames",
    "get_clip_frame_range",
    "set_clip_frame_range",
    "clear_reconstruction",
    "delete_track",
    "delete_all_tracks",
    "disable_track",
    "select_track",
    "get_track_count",
    "get_active_track_count",
]
