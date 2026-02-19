"""
Camera Animation Module

Provides camera animation functions for cinematic shots including:
- Orbit animation around a target point
- Dolly/truck movements (forward/backward, left/right)
- Crane shots (vertical + forward movement)
- Pan/tilt rotations
- Rack focus (depth of field animation)
- Push-in (dolly + zoom combined)
- Turntable rotation for product showcase

All keyframe operations use direct API calls (obj.keyframe_insert)
to avoid context dependencies from bpy.ops.

Easing functions provide smooth acceleration/deceleration curves.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import math

from .types import AnimationConfig, TurntableConfig
from .preset_loader import get_camera_move_preset, get_easing_preset, get_turntable_preset

# Guarded imports for Blender API
try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    BLENDER_AVAILABLE = False


# =============================================================================
# EASING FUNCTIONS
# =============================================================================

def apply_easing(t: float, easing: str) -> float:
    """
    Apply easing function to normalized time value.

    Args:
        t: Normalized time value (0.0 to 1.0)
        easing: Easing function name

    Returns:
        Eased time value (0.0 to 1.0)

    Supported easing types:
    - linear: Constant speed
    - ease_in: Quadratic acceleration
    - ease_out: Quadratic deceleration
    - ease_in_out: Quadratic smooth start and end
    - ease_in_quad: Quadratic acceleration
    - ease_out_quad: Quadratic deceleration
    - ease_in_out_quad: Quadratic smooth
    - ease_in_cubic: Cubic acceleration
    - ease_out_cubic: Cubic deceleration
    - ease_in_out_cubic: Cubic smooth
    - ease_in_expo: Exponential acceleration
    - ease_out_expo: Exponential deceleration
    - ease_in_out_expo: Exponential smooth
    - ease_out_bounce: Bouncing deceleration
    - ease_out_elastic: Elastic bounce at end
    - ease_in_back: Overshoot backward first
    - ease_out_back: Overshoot then settle
    - ease_in_out_back: Back easing both ends
    """
    # Clamp t to valid range
    t = max(0.0, min(1.0, t))

    if easing == "linear":
        return t

    elif easing == "ease_in":
        return t * t

    elif easing == "ease_out":
        return t * (2.0 - t)

    elif easing == "ease_in_out":
        if t < 0.5:
            return 2.0 * t * t
        else:
            return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)

    elif easing == "ease_in_quad":
        return t * t

    elif easing == "ease_out_quad":
        return t * (2.0 - t)

    elif easing == "ease_in_out_quad":
        if t < 0.5:
            return 2.0 * t * t
        else:
            return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)

    elif easing == "ease_in_cubic":
        return t * t * t

    elif easing == "ease_out_cubic":
        t1 = t - 1.0
        return t1 * t1 * t1 + 1.0

    elif easing == "ease_in_out_cubic":
        if t < 0.5:
            return 4.0 * t * t * t
        else:
            t1 = 2.0 * t - 2.0
            return 1.0 + 0.5 * t1 * t1 * t1

    elif easing == "ease_in_expo":
        if t == 0:
            return 0.0
        return math.pow(2.0, 10.0 * (t - 1.0))

    elif easing == "ease_out_expo":
        if t == 1:
            return 1.0
        return 1.0 - math.pow(2.0, -10.0 * t)

    elif easing == "ease_in_out_expo":
        if t == 0:
            return 0.0
        if t == 1:
            return 1.0
        if t < 0.5:
            return 0.5 * math.pow(2.0, 20.0 * t - 10.0)
        else:
            return 1.0 - 0.5 * math.pow(2.0, -20.0 * t + 10.0)

    elif easing == "ease_out_bounce":
        n1 = 7.5625
        d1 = 2.75
        if t < 1.0 / d1:
            return n1 * t * t
        elif t < 2.0 / d1:
            t1 = t - 1.5 / d1
            return n1 * t1 * t1 + 0.75
        elif t < 2.5 / d1:
            t1 = t - 2.25 / d1
            return n1 * t1 * t1 + 0.9375
        else:
            t1 = t - 2.625 / d1
            return n1 * t1 * t1 + 0.984375

    elif easing == "ease_out_elastic":
        if t == 0:
            return 0.0
        if t == 1:
            return 1.0
        p = 0.3
        return math.pow(2.0, -10.0 * t) * math.sin((t - p / 4.0) * 2.0 * math.pi / p) + 1.0

    elif easing == "ease_in_back":
        c1 = 1.70158
        c3 = c1 + 1.0
        return c3 * t * t * t - c1 * t * t

    elif easing == "ease_out_back":
        c1 = 1.70158
        c3 = c1 + 1.0
        t1 = t - 1.0
        return 1.0 + c3 * t1 * t1 * t1 + c1 * t1 * t1

    elif easing == "ease_in_out_back":
        c1 = 1.70158
        c2 = c1 * 1.525
        if t < 0.5:
            t1 = 2.0 * t
            return 0.5 * (t1 * t1 * ((c2 + 1.0) * t1 - c2))
        else:
            t1 = 2.0 * t - 2.0
            return 0.5 * (t1 * t1 * ((c2 + 1.0) * t1 + c2) + 2.0)

    # Default to linear if easing type not recognized
    return t


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_animation(object_name: str) -> bool:
    """
    Clear all animation data from an object.

    Args:
        object_name: Name of the Blender object

    Returns:
        True if animation was cleared, False if object not found
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return False

    obj.animation_data_clear()
    return True


def set_scene_frame_range(start_frame: int, end_frame: int) -> None:
    """
    Set scene frame range for playback and rendering.

    Args:
        start_frame: First frame number
        end_frame: Last frame number
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame


def _set_keyframe_interpolation(obj: Any, data_path: str, frame: int, interpolation: str = "LINEAR") -> None:
    """
    Set interpolation mode for a specific keyframe.

    Args:
        obj: Blender object with animation data
        data_path: Animation data path
        frame: Frame number of keyframe
        interpolation: Interpolation type (LINEAR, BEZIER, etc.)
    """
    if not obj.animation_data or not obj.animation_data.action:
        return

    # Find the fcurve for this data path
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == data_path:
            for keyframe in fcurve.keyframe_points:
                if keyframe.co.x == frame:
                    keyframe.interpolation = interpolation


# =============================================================================
# ORBIT ANIMATION
# =============================================================================

def create_orbit_animation(
    camera_name: str,
    target_position: Tuple[float, float, float],
    radius: float,
    angle_range: Tuple[float, float] = (0.0, 360.0),
    duration: int = 120,
    easing: str = "linear",
    start_frame: int = 1,
    axis: str = "Z"
) -> bool:
    """
    Create orbit animation around a target point.

    Camera moves in a circular path around the target, always facing it.

    Args:
        camera_name: Name of the camera object
        target_position: World position to orbit around (x, y, z)
        radius: Orbit radius in meters
        angle_range: Start and end angles in degrees (default full 360)
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation
        axis: Rotation axis (X, Y, or Z)

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj:
        return False

    # Clear existing animation
    cam_obj.animation_data_clear()

    # Convert angles to radians
    start_angle = math.radians(angle_range[0])
    end_angle = math.radians(angle_range[1])

    # Create keyframes
    end_frame = start_frame + duration

    # Store keyframe positions for Track To constraint
    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate angle
        angle = start_angle + (end_angle - start_angle) * eased_t

        # Calculate position based on axis
        if axis.upper() == "Z":
            # Horizontal orbit (around Z axis)
            x = target_position[0] + radius * math.sin(angle)
            y = target_position[1] - radius * math.cos(angle)
            z = target_position[2]
        elif axis.upper() == "Y":
            # Orbit around Y axis (front-back)
            x = target_position[0] + radius * math.sin(angle)
            y = target_position[1]
            z = target_position[2] - radius * math.cos(angle)
        else:  # X axis
            # Orbit around X axis (vertical)
            x = target_position[0]
            y = target_position[1] + radius * math.sin(angle)
            z = target_position[2] - radius * math.cos(angle)

        cam_obj.location = (x, y, z)
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Set LINEAR interpolation for constant speed
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "LINEAR"

    # Add Track To constraint to look at target
    constraint = cam_obj.constraints.new(type="TRACK_TO")

    # Create target empty if needed
    target_name = f"{camera_name}_orbit_target"
    target_empty = bpy.data.objects.get(target_name)
    if not target_empty:
        target_empty = bpy.data.objects.new(target_name, None)
        bpy.context.collection.objects.link(target_empty)

    target_empty.location = target_position
    constraint.target = target_empty
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    return True


# =============================================================================
# DOLLY ANIMATION
# =============================================================================

def create_dolly_animation(
    camera_name: str,
    distance: float,
    direction: str = "forward",
    duration: int = 60,
    easing: str = "ease_out",
    start_frame: int = 1
) -> bool:
    """
    Create dolly animation moving camera forward or backward.

    Args:
        camera_name: Name of the camera object
        distance: Travel distance in meters
        direction: "forward" or "backward"
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj:
        return False

    # Clear existing animation on location
    if cam_obj.animation_data:
        # Only clear location animation, keep other properties
        action = cam_obj.animation_data.action
        if action:
            for fcurve in action.fcurves[:]:
                if fcurve.data_path == "location":
                    action.fcurves.remove(fcurve)

    # Get camera's forward direction (-Z in camera space)
    forward = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))
    forward.normalize()

    # Reverse direction if backward
    if direction == "backward":
        forward = -forward

    # Get start position
    start_pos = cam_obj.location.copy() if hasattr(cam_obj.location, 'copy') else Vector(cam_obj.location)

    # Create keyframes
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate position
        offset = forward * distance * eased_t
        new_pos = start_pos + offset

        cam_obj.location = new_pos
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Set interpolation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"

    return True


# =============================================================================
# TRUCK ANIMATION
# =============================================================================

def create_truck_animation(
    camera_name: str,
    distance: float,
    direction: str = "right",
    duration: int = 60,
    easing: str = "ease_in_out",
    start_frame: int = 1
) -> bool:
    """
    Create truck animation moving camera laterally (left/right).

    Args:
        camera_name: Name of the camera object
        distance: Travel distance in meters
        direction: "left" or "right"
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj:
        return False

    # Clear existing location animation
    if cam_obj.animation_data:
        action = cam_obj.animation_data.action
        if action:
            for fcurve in action.fcurves[:]:
                if fcurve.data_path == "location":
                    action.fcurves.remove(fcurve)

    # Get camera's right direction (+X in camera space)
    right = cam_obj.matrix_world.to_3x3() @ Vector((1, 0, 0))
    right.normalize()

    # Reverse direction if left
    if direction == "left":
        right = -right

    # Get start position
    start_pos = cam_obj.location.copy() if hasattr(cam_obj.location, 'copy') else Vector(cam_obj.location)

    # Create keyframes
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate position
        offset = right * distance * eased_t
        new_pos = start_pos + offset

        cam_obj.location = new_pos
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Set interpolation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"

    return True


# =============================================================================
# CRANE ANIMATION
# =============================================================================

def create_crane_animation(
    camera_name: str,
    elevation_range: Tuple[float, float] = (0.0, 45.0),
    distance: float = 2.0,
    duration: int = 90,
    easing: str = "ease_in_out",
    start_frame: int = 1
) -> bool:
    """
    Create crane animation with combined vertical and forward movement.

    Args:
        camera_name: Name of the camera object
        elevation_range: Start and end elevation angles in degrees
        distance: Forward travel distance in meters
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj:
        return False

    # Clear existing location animation
    if cam_obj.animation_data:
        action = cam_obj.animation_data.action
        if action:
            for fcurve in action.fcurves[:]:
                if fcurve.data_path == "location":
                    action.fcurves.remove(fcurve)

    # Get camera's forward direction
    forward = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))
    up = Vector((0, 0, 1))

    # Get start position
    start_pos = cam_obj.location.copy() if hasattr(cam_obj.location, 'copy') else Vector(cam_obj.location)

    # Convert elevation angles to radians
    start_elev = math.radians(elevation_range[0])
    end_elev = math.radians(elevation_range[1])

    # Create keyframes
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate elevation at this point
        current_elev = start_elev + (end_elev - start_elev) * eased_t

        # Calculate forward distance traveled
        current_distance = distance * eased_t

        # Calculate position change
        forward_offset = forward * current_distance * math.cos(current_elev)
        up_offset = up * current_distance * math.sin(current_elev)

        new_pos = start_pos + forward_offset + up_offset
        cam_obj.location = new_pos
        cam_obj.keyframe_insert(data_path="location", frame=frame)

    # Set interpolation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"

    return True


# =============================================================================
# PAN ANIMATION
# =============================================================================

def create_pan_animation(
    camera_name: str,
    angle: float,
    direction: str = "right",
    duration: int = 60,
    easing: str = "ease_in_out",
    start_frame: int = 1
) -> bool:
    """
    Create pan animation rotating camera around its local Z axis.

    Args:
        camera_name: Name of the camera object
        angle: Rotation angle in degrees
        direction: "left" or "right"
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj:
        return False

    # Clear existing rotation animation
    if cam_obj.animation_data:
        action = cam_obj.animation_data.action
        if action:
            for fcurve in action.fcurves[:]:
                if fcurve.data_path == "rotation_euler":
                    action.fcurves.remove(fcurve)

    # Convert angle and handle direction
    angle_rad = math.radians(angle)
    if direction == "left":
        angle_rad = -angle_rad

    # Get start rotation
    start_rot = cam_obj.rotation_euler.copy() if hasattr(cam_obj.rotation_euler, 'copy') else list(cam_obj.rotation_euler)

    # Create keyframes (rotation around Z axis is index 2)
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate rotation
        current_angle = angle_rad * eased_t
        cam_obj.rotation_euler = (start_rot[0], start_rot[1], start_rot[2] + current_angle)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Set interpolation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "rotation_euler":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"

    return True


# =============================================================================
# TILT ANIMATION
# =============================================================================

def create_tilt_animation(
    camera_name: str,
    angle: float,
    direction: str = "up",
    duration: int = 60,
    easing: str = "ease_in_out",
    start_frame: int = 1
) -> bool:
    """
    Create tilt animation rotating camera around its local X axis.

    Args:
        camera_name: Name of the camera object
        angle: Rotation angle in degrees
        direction: "up" or "down"
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj:
        return False

    # Clear existing rotation animation
    if cam_obj.animation_data:
        action = cam_obj.animation_data.action
        if action:
            for fcurve in action.fcurves[:]:
                if fcurve.data_path == "rotation_euler":
                    action.fcurves.remove(fcurve)

    # Convert angle and handle direction
    angle_rad = math.radians(angle)
    if direction == "down":
        angle_rad = -angle_rad

    # Get start rotation
    start_rot = cam_obj.rotation_euler.copy() if hasattr(cam_obj.rotation_euler, 'copy') else list(cam_obj.rotation_euler)

    # Create keyframes (rotation around X axis is index 0)
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate rotation
        current_angle = angle_rad * eased_t
        cam_obj.rotation_euler = (start_rot[0] + current_angle, start_rot[1], start_rot[2])
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Set interpolation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "rotation_euler":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"

    return True


# =============================================================================
# RACK FOCUS ANIMATION
# =============================================================================

def create_rack_focus_animation(
    camera_name: str,
    from_distance: float,
    to_distance: float,
    duration: int = 30,
    easing: str = "ease_in_out",
    start_frame: int = 1
) -> bool:
    """
    Create rack focus animation changing DoF focus distance.

    Args:
        camera_name: Name of the camera object
        from_distance: Starting focus distance in meters
        to_distance: Ending focus distance in meters
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj or cam_obj.type != "CAMERA":
        return False

    camera = cam_obj.data

    # Enable DoF
    camera.dof.use_dof = True

    # Clear existing focus distance animation
    if cam_obj.animation_data:
        action = cam_obj.animation_data.action
        if action:
            for fcurve in action.fcurves[:]:
                if fcurve.data_path == "dof.focus_distance":
                    action.fcurves.remove(fcurve)

    # Create keyframes
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate focus distance
        current_distance = from_distance + (to_distance - from_distance) * eased_t
        camera.dof.focus_distance = current_distance
        cam_obj.keyframe_insert(data_path="dof.focus_distance", frame=frame)

    # Set interpolation
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "dof.focus_distance":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "BEZIER"

    return True


# =============================================================================
# PUSH IN ANIMATION
# =============================================================================

def create_push_in_animation(
    camera_name: str,
    dolly_distance: float = 0.3,
    focal_from: float = 35.0,
    focal_to: float = 50.0,
    duration: int = 120,
    easing: str = "ease_in_out",
    start_frame: int = 1
) -> bool:
    """
    Create push-in animation combining dolly movement with focal length change.

    Creates the classic "dolly zoom" or "vertigo" effect.

    Args:
        camera_name: Name of the camera object
        dolly_distance: Forward travel distance in meters
        focal_from: Starting focal length in mm
        focal_to: Ending focal length in mm
        duration: Animation duration in frames
        easing: Easing function name
        start_frame: First frame of animation

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    if not cam_obj or cam_obj.type != "CAMERA":
        return False

    camera = cam_obj.data

    # Clear existing animation
    cam_obj.animation_data_clear()

    # Get camera's forward direction
    forward = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))
    forward.normalize()

    # Get start position
    start_pos = cam_obj.location.copy() if hasattr(cam_obj.location, 'copy') else Vector(cam_obj.location)

    # Create keyframes
    end_frame = start_frame + duration

    for frame_offset in range(duration + 1):
        frame = start_frame + frame_offset
        t = frame_offset / duration if duration > 0 else 0
        eased_t = apply_easing(t, easing)

        # Calculate position
        offset = forward * dolly_distance * eased_t
        new_pos = start_pos + offset
        cam_obj.location = new_pos
        cam_obj.keyframe_insert(data_path="location", frame=frame)

        # Calculate focal length
        current_focal = focal_from + (focal_to - focal_from) * eased_t
        camera.lens = current_focal
        cam_obj.keyframe_insert(data_path="data.lens", frame=frame)

    # Set interpolation for both
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = "BEZIER"

    return True


# =============================================================================
# TURNTABLE ANIMATION
# =============================================================================

def create_turntable_animation(
    subject_name: str,
    config: Optional[TurntableConfig] = None,
    **kwargs
) -> bool:
    """
    Create turntable rotation animation for product showcase.

    Rotates the subject object around a specified axis with linear
    interpolation for smooth, constant-speed motion.

    Args:
        subject_name: Name of the subject object to rotate
        config: TurntableConfig with rotation settings
        **kwargs: Override config values (axis, angle_range, duration, etc.)

    Returns:
        True if animation was created successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    # Get subject object
    subject = bpy.data.objects.get(subject_name)
    if not subject:
        return False

    # Create config from kwargs or use provided config
    if config is None:
        config = TurntableConfig()

    # Override with kwargs
    if "axis" in kwargs:
        config.axis = kwargs["axis"]
    if "angle_range" in kwargs:
        config.angle_range = tuple(kwargs["angle_range"])
    if "duration" in kwargs:
        config.duration = kwargs["duration"]
    if "start_frame" in kwargs:
        config.start_frame = kwargs["start_frame"]
    if "easing" in kwargs:
        config.easing = kwargs["easing"]
    if "loop" in kwargs:
        config.loop = kwargs["loop"]
    if "direction" in kwargs:
        config.direction = kwargs["direction"]

    if not config.enabled:
        return False

    # Clear existing animation
    subject.animation_data_clear()

    # Set rotation mode to Euler for keyframing
    subject.rotation_mode = "XYZ"

    # Convert angle range to radians
    start_angle = math.radians(config.angle_range[0])
    end_angle = math.radians(config.angle_range[1])

    # Handle direction
    if config.direction == "counterclockwise":
        angle_diff = start_angle - end_angle
    else:
        angle_diff = end_angle - start_angle

    # Determine rotation axis index
    axis_map = {"X": 0, "Y": 1, "Z": 2}
    axis_idx = axis_map.get(config.axis.upper(), 2)

    # Get start rotation
    start_rot = list(subject.rotation_euler)

    # Create keyframes
    end_frame = config.start_frame + config.duration

    # Start keyframe
    subject.rotation_euler[axis_idx] = start_rot[axis_idx] + start_angle
    subject.keyframe_insert(data_path="rotation_euler", frame=config.start_frame)

    # End keyframe
    subject.rotation_euler[axis_idx] = start_rot[axis_idx] + start_angle + angle_diff
    subject.keyframe_insert(data_path="rotation_euler", frame=end_frame)

    # Set LINEAR interpolation for constant speed
    if subject.animation_data and subject.animation_data.action:
        for fcurve in subject.animation_data.action.fcurves:
            if fcurve.data_path == "rotation_euler":
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "LINEAR"

    return True


# =============================================================================
# PRESET APPLICATION
# =============================================================================

def apply_camera_move_preset(
    camera_name: str,
    preset_name: str,
    target_position: Optional[Tuple[float, float, float]] = None,
    start_frame: int = 1
) -> bool:
    """
    Apply a camera move preset to a camera.

    Args:
        camera_name: Name of the camera object
        preset_name: Name of the preset (e.g., "orbit_360", "dolly_in")
        target_position: Target position for orbit/pivot moves
        start_frame: First frame of animation

    Returns:
        True if preset was applied successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    # Load preset
    try:
        preset = get_camera_move_preset(preset_name)
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to load preset '{preset_name}': {e}")
        return False

    move_type = preset.get("type", "static")
    duration = preset.get("duration", 120)
    easing = preset.get("easing", "linear")

    if move_type == "orbit":
        radius = preset.get("radius", 1.0)
        angle_range = tuple(preset.get("angle_range", [0, 360]))
        axis = preset.get("axis", "Z")
        if target_position is None:
            target_position = (0, 0, 0)
        return create_orbit_animation(
            camera_name, target_position, radius, angle_range,
            duration, easing, start_frame, axis
        )

    elif move_type == "dolly":
        distance = preset.get("distance", 0.5)
        direction = preset.get("direction", "forward")
        return create_dolly_animation(
            camera_name, distance, direction, duration, easing, start_frame
        )

    elif move_type == "truck":
        distance = preset.get("distance", 0.5)
        direction = preset.get("direction", "right")
        return create_truck_animation(
            camera_name, distance, direction, duration, easing, start_frame
        )

    elif move_type == "crane":
        elevation_range = tuple(preset.get("elevation_range", [0, 45]))
        distance = preset.get("distance", 2.0)
        return create_crane_animation(
            camera_name, elevation_range, distance, duration, easing, start_frame
        )

    elif move_type == "pan":
        angle = preset.get("angle", 45)
        direction = preset.get("direction", "right")
        return create_pan_animation(
            camera_name, angle, direction, duration, easing, start_frame
        )

    elif move_type == "tilt":
        angle = preset.get("angle", 30)
        direction = preset.get("direction", "up")
        return create_tilt_animation(
            camera_name, angle, direction, duration, easing, start_frame
        )

    elif move_type == "focus":
        from_distance = preset.get("from", 0.5)
        to_distance = preset.get("to", 2.0)
        return create_rack_focus_animation(
            camera_name, from_distance, to_distance, duration, easing, start_frame
        )

    elif move_type == "combined":
        # Handle combined moves like push_in
        dolly_distance = preset.get("dolly_distance", 0.3)
        focal_from = preset.get("focal_from", 35)
        focal_to = preset.get("focal_to", 50)
        return create_push_in_animation(
            camera_name, dolly_distance, focal_from, focal_to,
            duration, easing, start_frame
        )

    return False


def apply_turntable_preset(
    subject_name: str,
    preset_name: str,
    start_frame: int = 1
) -> bool:
    """
    Apply a turntable preset to a subject object.

    Args:
        subject_name: Name of the object to rotate
        preset_name: Name of the turntable preset
        start_frame: First frame of animation

    Returns:
        True if preset was applied successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    # Load preset
    try:
        preset = get_turntable_preset(preset_name)
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to load turntable preset '{preset_name}': {e}")
        return False

    # Create config from preset
    config = TurntableConfig(
        enabled=preset.get("enabled", True),
        axis=preset.get("axis", "Z"),
        angle_range=tuple(preset.get("angle_range", [0.0, 360.0])),
        duration=preset.get("duration", 120),
        start_frame=start_frame,
        easing=preset.get("easing", "linear"),
        loop=preset.get("loop", True),
        direction=preset.get("direction", "clockwise"),
        rotation_speed=preset.get("rotation_speed", 1.0)
    )

    return create_turntable_animation(subject_name, config)


# =============================================================================
# CREATE ANIMATION FROM CONFIG
# =============================================================================

def create_animation_from_preset(
    camera_name: str,
    config: AnimationConfig,
    target_position: Optional[Tuple[float, float, float]] = None
) -> bool:
    """
    Create animation from AnimationConfig.

    Args:
        camera_name: Name of the camera object
        config: AnimationConfig with animation settings
        target_position: Target position for orbit moves

    Returns:
        True if animation was created successfully
    """
    if not config.enabled:
        return False

    anim_type = config.type

    if anim_type == "orbit":
        if target_position is None:
            target_position = (0, 0, 0)
        return create_orbit_animation(
            camera_name, target_position, config.radius,
            config.angle_range, config.duration, config.easing,
            config.start_frame
        )

    elif anim_type == "dolly":
        return create_dolly_animation(
            camera_name, config.distance, config.direction,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "truck":
        return create_truck_animation(
            camera_name, config.distance, config.direction,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "crane":
        return create_crane_animation(
            camera_name, config.elevation_range, config.distance,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "pan":
        angle = config.angle_range[1] - config.angle_range[0]
        return create_pan_animation(
            camera_name, angle, config.direction,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "tilt":
        angle = config.elevation_range[1] - config.elevation_range[0]
        return create_tilt_animation(
            camera_name, angle, config.direction,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "rack_focus":
        return create_rack_focus_animation(
            camera_name, config.from_value, config.to_value,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "push_in":
        return create_push_in_animation(
            camera_name, config.distance, config.from_value, config.to_value,
            config.duration, config.easing, config.start_frame
        )

    elif anim_type == "turntable":
        # Turntable rotates the subject, not the camera
        # This would need a subject_name parameter
        return False

    return False
