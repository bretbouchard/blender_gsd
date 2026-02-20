"""
Tracking Context Module

Provides context management for Blender tracking operators.
Most bpy.ops.clip.* operators require an active Movie Clip Editor area
with a loaded clip.

Key Functions:
- tracking_context: Context manager for tracking operations
- get_clip_editor_area: Find Clip Editor area
- ensure_clip_loaded: Load or retrieve existing clip
- get_active_clip: Get currently active clip
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
import os

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


@contextmanager
def tracking_context(clip) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager for tracking operations requiring Clip Editor.

    Sets up proper Blender context for bpy.ops.clip.* operators.
    Most tracking operators require an active Movie Clip Editor area
    with a loaded clip.

    Args:
        clip: bpy.types.MovieClip to set as active

    Yields:
        Context override dict for use with operators

    Usage:
        with tracking_context(clip) as ctx:
            bpy.ops.clip.detect_features(ctx, threshold=0.5)

    Raises:
        RuntimeError: If Blender not available or no Clip Editor found
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available - tracking requires Blender")

    # Check for screen availability (headless mode)
    if not bpy.context.screen:
        raise RuntimeError("No screen available - tracking requires GUI context")

    # Find Clip Editor area
    clip_area = None
    for area in bpy.context.screen.areas:
        if area.type == 'CLIP_EDITOR':
            clip_area = area
            break

    if clip_area is None:
        raise RuntimeError(
            "No Clip Editor area found. Open a Clip Editor window "
            "or change an area to Clip Editor type."
        )

    # Store original state
    original_clip = clip_area.spaces.active.clip
    original_space_type = clip_area.type

    try:
        # Set active clip
        clip_area.spaces.active.clip = clip

        # Create context override
        override = bpy.context.copy()
        override['area'] = clip_area
        override['space_data'] = clip_area.spaces.active
        override['region'] = clip_area.regions[-1]  # Use last region (usually window)

        yield override

    finally:
        # Restore original state
        if clip_area:
            clip_area.spaces.active.clip = original_clip


def get_clip_editor_area():
    """
    Get the active Clip Editor area, or None if not found.

    Returns:
        bpy.types.Area or None
    """
    if not BLENDER_AVAILABLE:
        return None

    if not bpy.context.screen:
        return None

    for area in bpy.context.screen.areas:
        if area.type == 'CLIP_EDITOR':
            return area

    return None


def ensure_clip_loaded(clip_path: str) -> 'bpy.types.MovieClip':
    """
    Ensure a movie clip is loaded and return it.

    Checks if the clip is already loaded before creating a new one.
    Uses absolute path for consistent matching.

    Args:
        clip_path: Path to video file or image sequence

    Returns:
        Loaded MovieClip

    Raises:
        RuntimeError: If Blender not available
        FileNotFoundError: If clip file doesn't exist
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    path = os.path.abspath(clip_path)

    # Check if file exists
    if not os.path.exists(path):
        # Try with Blender's path conversion
        if not os.path.exists(path):
            raise FileNotFoundError(f"Clip not found: {clip_path}")

    # Check if already loaded
    for clip in bpy.data.movieclips:
        if os.path.abspath(clip.filepath) == path:
            return clip

    # Load new clip
    return bpy.data.movieclips.load(path)


def get_active_clip() -> Optional['bpy.types.MovieClip']:
    """
    Get the currently active clip from the Clip Editor.

    Returns:
        Active MovieClip or None if no Clip Editor or no clip loaded
    """
    if not BLENDER_AVAILABLE:
        return None

    clip_area = get_clip_editor_area()
    if clip_area is None:
        return None

    return clip_area.spaces.active.clip


def get_tracking_object(clip, name: str = "Camera") -> Optional[Any]:
    """
    Get a tracking object by name.

    Args:
        clip: MovieClip with tracking data
        name: Tracking object name (default: "Camera")

    Returns:
        MovieTrackingObject or None
    """
    if not BLENDER_AVAILABLE:
        return None

    tracking = clip.tracking
    for obj in tracking.objects:
        if obj.name == name:
            return obj

    # Return default camera object if not found
    if name == "Camera" and tracking.objects:
        return tracking.objects[0]

    return None


def set_active_tracking_object(clip, name: str) -> bool:
    """
    Set the active tracking object by name.

    Args:
        clip: MovieClip with tracking data
        name: Tracking object name to activate

    Returns:
        True if successful, False if object not found
    """
    if not BLENDER_AVAILABLE:
        return False

    tracking = clip.tracking
    for obj in tracking.objects:
        if obj.name == name:
            tracking.objects.active = obj
            return True

    return False


def get_track_by_name(clip, track_name: str) -> Optional[Any]:
    """
    Get a track by name from the active tracking object.

    Args:
        clip: MovieClip with tracking data
        track_name: Name of track to find

    Returns:
        MovieTrackingTrack or None
    """
    if not BLENDER_AVAILABLE:
        return None

    tracking = clip.tracking
    tracks = tracking.tracks

    return tracks.get(track_name)


def get_frame_range(clip) -> tuple:
    """
    Get the frame range for a clip.

    Args:
        clip: MovieClip

    Returns:
        Tuple of (start_frame, end_frame)
    """
    if not BLENDER_AVAILABLE:
        return (1, 100)

    start = clip.frame_start
    end = clip.frame_start + clip.frame_duration - 1

    return (start, end)


def is_tracking_available() -> bool:
    """
    Check if tracking functionality is available.

    Returns:
        True if Blender is available with tracking context
    """
    return BLENDER_AVAILABLE and get_clip_editor_area() is not None


def create_tracking_object(clip, name: str, object_type: str = "CAMERA") -> Optional[Any]:
    """
    Create a new tracking object.

    Args:
        clip: MovieClip to add tracking object to
        name: Name for the new tracking object
        object_type: Type of tracking object ("CAMERA" or "OBJECT")

    Returns:
        Created MovieTrackingObject or None
    """
    if not BLENDER_AVAILABLE:
        return None

    tracking = clip.tracking

    # Check if object already exists
    for obj in tracking.objects:
        if obj.name == name:
            return obj

    # Create new object
    new_obj = tracking.objects.new(name)

    return new_obj


def get_scene_frame_range() -> tuple:
    """
    Get the current scene frame range.

    Returns:
        Tuple of (start_frame, end_frame)
    """
    if not BLENDER_AVAILABLE:
        return (1, 100)

    scene = bpy.context.scene
    return (scene.frame_start, scene.frame_end)


def set_scene_frame(frame: int) -> None:
    """
    Set the current scene frame.

    Args:
        frame: Frame number to set
    """
    if BLENDER_AVAILABLE:
        bpy.context.scene.frame_set(frame)


def get_current_frame() -> int:
    """
    Get the current scene frame.

    Returns:
        Current frame number
    """
    if not BLENDER_AVAILABLE:
        return 1

    return bpy.context.scene.frame_current


__all__ = [
    "BLENDER_AVAILABLE",
    "tracking_context",
    "get_clip_editor_area",
    "ensure_clip_loaded",
    "get_active_clip",
    "get_tracking_object",
    "set_active_tracking_object",
    "get_track_by_name",
    "get_frame_range",
    "is_tracking_available",
    "create_tracking_object",
    "get_scene_frame_range",
    "set_scene_frame",
    "get_current_frame",
]
