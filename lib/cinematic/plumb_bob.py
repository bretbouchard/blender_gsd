"""
Plumb Bob Targeting System

Provides orbit/focus targeting for cameras.
Supports auto (bounding box), manual (explicit), and object modes.
Handles focus_mode (auto/manual) for focus distance control.
Connects to camera rig setup workflow.

Usage:
    from lib.cinematic.plumb_bob import (
        calculate_plumb_bob, apply_plumb_bob_to_rig
    )
    from lib.cinematic.types import PlumbBobConfig

    # Calculate target from subject bounding box
    config = PlumbBobConfig(mode="auto", offset=(0, 0, 0.5))
    target = calculate_plumb_bob("my_subject", config)

    # Apply to camera rig
    apply_plumb_bob_to_rig("camera", "my_subject", config)
"""

from __future__ import annotations
from typing import Optional, Tuple, Any
from pathlib import Path
import math

from .types import PlumbBobConfig

# Guarded imports
try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    BLENDER_AVAILABLE = False


def calculate_plumb_bob(
    subject_name: str,
    config: PlumbBobConfig
) -> Optional[Tuple[float, float, float]]:
    """
    Calculate plumb bob target position based on config mode.

    Args:
        subject_name: Name of subject object in scene
        config: PlumbBobConfig with mode and parameters

    Returns:
        World position tuple (x, y, z) or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Handle manual mode - use explicit position
        if config.mode == "manual":
            return (
                config.manual_position[0] + config.offset[0],
                config.manual_position[1] + config.offset[1],
                config.manual_position[2] + config.offset[2],
            )

        # Handle object mode - get target object position
        if config.mode == "object":
            if config.target_object not in bpy.data.objects:
                return None
            target_obj = bpy.data.objects[config.target_object]
            world_pos = target_obj.matrix_world.translation
            return (
                world_pos[0] + config.offset[0],
                world_pos[1] + config.offset[1],
                world_pos[2] + config.offset[2],
            )

        # Auto mode - calculate from subject bounding box
        if config.mode == "auto":
            if subject_name not in bpy.data.objects:
                return None

            subject = bpy.data.objects[subject_name]

            # Get bounding box corners (8 corners in local space)
            bbox = subject.bound_box

            # Calculate center of bounding box
            center = Vector((
                sum(v[0] for v in bbox) / 8,
                sum(v[1] for v in bbox) / 8,
                sum(v[2] for v in bbox) / 8
            ))

            # Convert to world space
            world_center = subject.matrix_world @ center

            # Add offset
            return (
                world_center[0] + config.offset[0],
                world_center[1] + config.offset[1],
                world_center[2] + config.offset[2],
            )

        # Unknown mode
        return None

    except Exception:
        return None


def create_target_empty(
    position: Tuple[float, float, float],
    name: str = "plumb_bob_target"
) -> Optional[Any]:
    """
    Create an empty object at the target position.

    Args:
        position: World position (x, y, z)
        name: Name for the empty object

    Returns:
        Created empty object or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check if already exists
        if name in bpy.data.objects:
            empty = bpy.data.objects[name]
            empty.location = position
            return empty

        # Create new empty
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.location = position

        # Link to scene collection
        if hasattr(bpy, "context") and bpy.context.scene is not None:
            bpy.context.scene.collection.objects.link(empty)

        return empty

    except Exception:
        return None


def calculate_focus_distance(
    camera_name: str,
    target: Tuple[float, float, float]
) -> float:
    """
    Calculate distance from camera to target.

    Args:
        camera_name: Name of camera object
        target: Target position (x, y, z)

    Returns:
        Distance in meters, or 0.0 if failed
    """
    if not BLENDER_AVAILABLE:
        return 0.0

    try:
        if camera_name not in bpy.data.objects:
            return 0.0

        camera = bpy.data.objects[camera_name]
        cam_pos = camera.matrix_world.translation

        # Calculate 3D distance
        dx = target[0] - cam_pos[0]
        dy = target[1] - cam_pos[1]
        dz = target[2] - cam_pos[2]

        return math.sqrt(dx*dx + dy*dy + dz*dz)

    except Exception:
        return 0.0


def set_camera_focus_target(
    camera_name: str,
    target_position: Tuple[float, float, float],
    config: PlumbBobConfig
) -> float:
    """
    Set camera focus distance based on target and focus mode.

    Args:
        camera_name: Name of camera object
        target_position: Target world position (x, y, z)
        config: PlumbBobConfig with focus_mode setting

    Returns:
        Focus distance that was set, or 0.0 if failed
    """
    if not BLENDER_AVAILABLE:
        return 0.0

    try:
        if camera_name not in bpy.data.objects:
            return 0.0

        camera = bpy.data.objects[camera_name]
        if camera.data is None or not hasattr(camera.data, "dof"):
            return 0.0

        cam_data = camera.data

        # Handle focus mode
        if config.focus_mode == "manual":
            # Use explicit focus distance from config
            focus_dist = config.focus_distance
        elif config.focus_mode == "auto":
            # Calculate from camera position to target
            cam_pos = camera.matrix_world.translation
            target_vec = Vector(target_position)
            focus_dist = (target_vec - cam_pos).length
        else:
            # Unknown mode, default to auto
            cam_pos = camera.matrix_world.translation
            target_vec = Vector(target_position)
            focus_dist = (target_vec - cam_pos).length

        # Set focus distance
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = focus_dist

        return focus_dist

    except Exception:
        return 0.0


def remove_target_empty(name: str = "plumb_bob_target") -> bool:
    """
    Remove the target empty object.

    Args:
        name: Name of the empty to remove

    Returns:
        True if removed, False if not found or failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if name not in bpy.data.objects:
            return False

        empty = bpy.data.objects[name]

        # Unlink from all collections
        for collection in bpy.data.collections:
            if empty.name in collection.objects:
                collection.objects.unlink(empty)

        # Check scene collection
        if hasattr(bpy, "context") and bpy.context.scene is not None:
            scene_collection = bpy.context.scene.collection
            if empty.name in scene_collection.objects:
                scene_collection.objects.unlink(empty)

        # Remove object
        bpy.data.objects.remove(empty)
        return True

    except Exception:
        return False


def get_or_create_target(
    subject_name: str,
    config: PlumbBobConfig
) -> Optional[Any]:
    """
    Calculate plumb bob position and create/update target empty.

    Args:
        subject_name: Name of subject object
        config: PlumbBobConfig with targeting parameters

    Returns:
        Target empty object or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Calculate position
        position = calculate_plumb_bob(subject_name, config)
        if position is None:
            return None

        # Create or update empty
        empty = create_target_empty(position, "plumb_bob_target")
        return empty

    except Exception:
        return None


def apply_plumb_bob_to_rig(
    camera_name: str,
    subject_name: str,
    config: PlumbBobConfig
) -> Optional[Any]:
    """
    Complete workflow for connecting plumb bob to camera rig.

    This is the primary entry point for the plumb bob -> rig workflow.

    Args:
        camera_name: Name of camera to configure
        subject_name: Name of subject to target
        config: PlumbBobConfig with all targeting parameters

    Returns:
        Target empty object or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # 1. Calculate plumb bob position
        position = calculate_plumb_bob(subject_name, config)
        if position is None:
            return None

        # 2. Create/update target empty
        target_empty = get_or_create_target(subject_name, config)
        if target_empty is None:
            return None

        # 3. Set camera focus target
        set_camera_focus_target(camera_name, position, config)

        return target_empty

    except Exception:
        return None
