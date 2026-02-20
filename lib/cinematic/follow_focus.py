"""
Follow Focus System Module

Implements automated follow-focus for cameras tracking moving subjects.
Provides focus distance calculation, focus rig creation, and animation.

Key features:
- Distance calculation from camera to tracked target
- Follow-focus rig creation with constraints
- Automatic focus distance keyframing
- Support for multiple focus modes (auto, manual, tracked)
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import math

from .tracking_types import TrackingMarker, TrackingData, FollowFocusRig
from .tracking_solver import interpolate_position, predict_position

# Check if Blender is available
try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Vector = None


def calculate_focus_distance(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float]
) -> float:
    """
    Calculate focus distance from camera to target.

    Uses Euclidean distance formula for 3D points.

    Args:
        camera_pos: Camera world position (x, y, z)
        target_pos: Target world position (x, y, z)

    Returns:
        Focus distance in meters
    """
    dx = target_pos[0] - camera_pos[0]
    dy = target_pos[1] - camera_pos[1]
    dz = target_pos[2] - camera_pos[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def create_follow_focus_rig(
    camera_name: str,
    target: TrackingMarker,
    rig_name: str = ""
) -> Optional[FollowFocusRig]:
    """
    Create automated follow-focus setup.

    Creates a FollowFocusRig configuration that can be applied
    to have a camera automatically track a target marker.

    Args:
        camera_name: Name of camera object in Blender
        target: Tracking marker to follow
        rig_name: Optional rig name (defaults to "{camera}_follow_focus")

    Returns:
        FollowFocusRig configuration or None if setup fails
    """
    if not rig_name:
        rig_name = f"{camera_name}_follow_focus"

    rig = FollowFocusRig(
        name=rig_name,
        camera_name=camera_name,
        target_marker=target.name,
        follow_position=False,  # Camera position typically not auto-moved
        follow_focus=True,
        position_smoothing=0.5,
        focus_smoothing=0.3,
        offset=(0.0, 0.0, 0.0),
    )

    return rig


def animate_focus_distance(
    rig: FollowFocusRig,
    tracking_data: Dict[str, TrackingData],
    frame_start: int,
    frame_end: int,
    smoothing: float = 0.3
) -> bool:
    """
    Keyframe focus distance based on tracking data.

    Animates the camera's focus distance to follow the tracked
    target through the frame range.

    Args:
        rig: Follow-focus rig configuration
        tracking_data: Dictionary of marker_name -> TrackingData
        frame_start: First frame to keyframe
        frame_end: Last frame to keyframe
        smoothing: Smoothing factor for focus changes (0-1)

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        return False

    # Get camera
    camera = bpy.data.objects.get(rig.camera_name)
    if camera is None or camera.type != 'CAMERA':
        return False

    # Get tracking data for target
    target_data = tracking_data.get(rig.target_marker)
    if target_data is None:
        return False

    # Previous focus distance for smoothing
    prev_focus = None

    # Keyframe focus distance for each frame
    for frame in range(frame_start, frame_end + 1):
        # Get target position at frame
        target_pos = interpolate_position(target_data, frame)
        if target_pos is None:
            continue

        # Set scene frame
        bpy.context.scene.frame_set(frame)

        # Get camera position
        camera_pos = camera.matrix_world.translation
        camera_pos_tuple = (camera_pos.x, camera_pos.y, camera_pos.z)

        # Calculate focus distance
        focus_distance = calculate_focus_distance(camera_pos_tuple, target_pos)

        # Apply rig offset to target
        if rig.offset != (0.0, 0.0, 0.0):
            offset_dist = math.sqrt(
                rig.offset[0] ** 2 + rig.offset[1] ** 2 + rig.offset[2] ** 2
            )
            focus_distance += offset_dist

        # Apply smoothing
        if prev_focus is not None and smoothing > 0:
            alpha = 1.0 - smoothing
            focus_distance = alpha * focus_distance + smoothing * prev_focus

        # Set focus distance
        camera.data.dof.focus_distance = focus_distance

        # Keyframe
        camera.data.dof.keyframe_insert(data_path="focus_distance", frame=frame)

        prev_focus = focus_distance

    return True


def set_focus_mode(camera_name: str, mode: str) -> bool:
    """
    Set focus mode for a camera.

    Args:
        camera_name: Name of camera object
        mode: Focus mode (auto, manual, tracked)

    Returns:
        True if mode was set successfully
    """
    if not BLENDER_AVAILABLE:
        return False

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        return False

    if mode == "auto":
        # Enable auto focus
        camera.data.dof.use_dof = True
        camera.data.dof.focus_object = None
    elif mode == "manual":
        # Manual focus - no auto-focus target
        camera.data.dof.use_dof = True
        camera.data.dof.focus_object = None
    elif mode == "tracked":
        # Tracked mode - focus will be animated
        camera.data.dof.use_dof = True
        camera.data.dof.focus_object = None
    else:
        return False

    return True


def create_focus_target_empty(
    name: str,
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> Optional[str]:
    """
    Create an empty object to serve as a focus target.

    Args:
        name: Name for the empty object
        position: World position for the empty

    Returns:
        Name of created empty or None if creation failed
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create empty
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = 0.1
    empty.location = position

    # Link to scene
    bpy.context.collection.objects.link(empty)

    return empty.name


def link_camera_to_focus_target(
    camera_name: str,
    target_name: str
) -> bool:
    """
    Link camera to focus on a target object.

    Sets the camera's focus object to track the target empty,
    enabling automatic focus distance calculation.

    Args:
        camera_name: Name of camera object
        target_name: Name of target empty/object

    Returns:
        True if linking was successful
    """
    if not BLENDER_AVAILABLE:
        return False

    camera = bpy.data.objects.get(camera_name)
    target = bpy.data.objects.get(target_name)

    if camera is None or camera.type != 'CAMERA':
        return False
    if target is None:
        return False

    # Enable DOF and set focus object
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target

    return True


def animate_focus_target(
    target_name: str,
    tracking_data: TrackingData,
    frame_start: int,
    frame_end: int
) -> bool:
    """
    Animate a focus target empty to follow tracking data.

    Moves the target empty through each frame based on tracked positions,
    which the camera will then focus on automatically.

    Args:
        target_name: Name of target empty object
        tracking_data: Tracking data to follow
        frame_start: First frame to animate
        frame_end: Last frame to animate

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        return False

    target = bpy.data.objects.get(target_name)
    if target is None:
        return False

    for frame in range(frame_start, frame_end + 1):
        pos = interpolate_position(tracking_data, frame)
        if pos is None:
            continue

        target.location = pos
        target.keyframe_insert(data_path="location", frame=frame)

    return True


def get_camera_focus_info(camera_name: str) -> Optional[Dict[str, Any]]:
    """
    Get focus information for a camera.

    Args:
        camera_name: Name of camera object

    Returns:
        Dictionary with focus info or None if camera not found
    """
    if not BLENDER_AVAILABLE:
        return None

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        return None

    dof = camera.data.dof

    return {
        "name": camera_name,
        "dof_enabled": dof.use_dof,
        "focus_distance": dof.focus_distance,
        "focus_object": dof.focus_object.name if dof.focus_object else None,
        "f_stop": dof.aperture_fstop,
        "aperture_blades": dof.aperture_blades,
    }


def remove_follow_focus_animation(camera_name: str) -> bool:
    """
    Remove all focus distance keyframes from a camera.

    Args:
        camera_name: Name of camera object

    Returns:
        True if animation was removed successfully
    """
    if not BLENDER_AVAILABLE:
        return False

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        return False

    # Remove focus distance animation data
    if camera.data.dof.animation_data:
        # Remove FCurves for focus_distance
        action = camera.data.dof.animation_data.action
        if action:
            for fcurve in action.fcurves:
                if "focus_distance" in fcurve.data_path:
                    action.fcurves.remove(fcurve)

    return True
