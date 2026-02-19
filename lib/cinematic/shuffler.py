"""
Shot Variation Generator (Shuffler) Module

Generates multiple shot variations with randomized camera,
lighting, and lens parameters for batch rendering workflows.

Usage:
    from lib.cinematic.shuffler import generate_variations, apply_variation, create_shuffle_set
    from lib.cinematic.types import ShuffleConfig, CameraConfig

    # Generate 5 camera variations
    config = ShuffleConfig(num_variations=5, seed=42)
    variations = generate_variations(config, base_camera)

    # Create a full shuffle set with multiple cameras
    camera_names = create_shuffle_set("hero_shot", config)

    # Apply shuffle preset
    variations = apply_shuffle_preset("dramatic", base_camera)
"""

from __future__ import annotations
import random
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .types import CameraConfig, ShuffleConfig, Transform3D

# Blender availability check
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


def generate_variations(
    config: ShuffleConfig,
    base_camera: CameraConfig
) -> List[CameraConfig]:
    """
    Generate N variations based on config parameters.

    Creates variations with randomized camera position, rotation,
    and lens settings within the defined ranges.

    Args:
        config: ShuffleConfig with randomization ranges
        base_camera: Base camera configuration to vary from

    Returns:
        List of CameraConfig variations
    """
    # Set random seed for reproducibility
    if config.seed is not None and config.seed != 0:
        random.seed(config.seed)

    variations = []
    for i in range(config.num_variations):
        # Generate randomized values within ranges
        angle_offset = random.uniform(*config.camera_angle_range)
        height_offset = random.uniform(*config.camera_height_range)
        focal_length = random.uniform(*config.focal_length_range)

        # Calculate new position with angle offset (orbit around origin)
        base_x = base_camera.transform.position[0]
        base_y = base_camera.transform.position[1]
        base_z = base_camera.transform.position[2]

        # Apply angle offset (around Z axis - horizontal orbit)
        angle_rad = math.radians(angle_offset)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        new_x = base_x * cos_a - base_y * sin_a
        new_y = base_x * sin_a + base_y * cos_a
        new_z = base_z + height_offset

        # Create variation with new transform
        variation = CameraConfig(
            name=f"{base_camera.name}_var_{i:03d}",
            focal_length=focal_length,
            focus_distance=base_camera.focus_distance,
            sensor_width=base_camera.sensor_width,
            sensor_height=base_camera.sensor_height,
            f_stop=base_camera.f_stop,
            aperture_blades=base_camera.aperture_blades,
            transform=Transform3D(
                position=(new_x, new_y, new_z),
                rotation=(
                    base_camera.transform.rotation[0],
                    base_camera.transform.rotation[1] + angle_offset,
                    base_camera.transform.rotation[2]
                ),
                scale=base_camera.transform.scale
            )
        )
        variations.append(variation)

    return variations


def apply_variation(camera_name: str, variation: CameraConfig) -> bool:
    """
    Apply a variation to an existing camera in Blender.

    Updates the camera's position, rotation, and lens settings
    to match the variation configuration.

    Args:
        camera_name: Name of the camera to modify
        variation: CameraConfig with new settings

    Returns:
        True if successful, False if camera not found or Blender unavailable
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if camera_name not in bpy.data.objects:
            return False

        obj = bpy.data.objects[camera_name]
        if obj.type != 'CAMERA':
            return False

        cam = obj.data

        # Apply transform
        obj.location = variation.transform.position
        obj.rotation_euler = tuple(
            r * 0.017453292519943295 for r in variation.transform.rotation
        )
        obj.scale = variation.transform.scale

        # Apply lens settings
        cam.lens = variation.focal_length
        cam.sensor_width = variation.sensor_width
        cam.sensor_height = variation.sensor_height

        # Apply DOF if available
        if hasattr(cam, 'dof') and cam.dof is not None:
            cam.dof.focus_distance = variation.focus_distance

        return True

    except Exception:
        return False


def create_shuffle_set(
    shot_name: str,
    config: ShuffleConfig,
    base_camera: Optional[CameraConfig] = None
) -> List[str]:
    """
    Create multiple camera objects with variations.

    Generates variations and creates actual Blender camera objects
    for each variation. Cameras are named with the shot prefix.

    Args:
        shot_name: Prefix for camera names
        config: ShuffleConfig with variation parameters
        base_camera: Optional base camera to vary from (uses defaults if None)

    Returns:
        List of created camera names
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return []

        scene = bpy.context.scene

        # Use provided base or create default
        if base_camera is None:
            base_camera = CameraConfig(name=f"{shot_name}_base")

        # Generate variations
        variations = generate_variations(config, base_camera)

        created_cameras = []
        for i, variation in enumerate(variations):
            # Create camera data
            cam_name = f"{shot_name}_shuffle_{i:03d}"
            cam_data = bpy.data.cameras.new(name=cam_name)
            cam_data.lens = variation.focal_length
            cam_data.sensor_width = variation.sensor_width
            cam_data.sensor_height = variation.sensor_height

            # Create camera object
            cam_obj = bpy.data.objects.new(cam_name, cam_data)

            # Apply transform
            cam_obj.location = variation.transform.position
            cam_obj.rotation_euler = tuple(
                r * 0.017453292519943295 for r in variation.transform.rotation
            )
            cam_obj.scale = variation.transform.scale

            # Link to scene collection
            scene.collection.objects.link(cam_obj)

            created_cameras.append(cam_name)

        return created_cameras

    except Exception:
        return []


def randomize_parameter(
    value: float,
    range_tuple: Tuple[float, float],
    seed: Optional[int] = None
) -> float:
    """
    Generate a random value within a range.

    Args:
        value: Base value (unused, kept for API compatibility)
        range_tuple: (min, max) tuple
        seed: Optional random seed

    Returns:
        Random float within range
    """
    if seed is not None:
        random.seed(seed)

    return random.uniform(*range_tuple)


def generate_light_variations(
    config: ShuffleConfig,
    base_lights: Optional[List[Dict[str, Any]]] = None
) -> List[List[Dict[str, Any]]]:
    """
    Generate lighting variations based on shuffle configuration.

    Creates N variations of lighting setups with randomized
    intensity and angle within the defined ranges.

    Args:
        config: ShuffleConfig with variation parameters
        base_lights: Optional list of base light configurations

    Returns:
        List of light variation sets
    """
    if config.seed is not None and config.seed != 0:
        random.seed(config.seed)

    if base_lights is None:
        base_lights = []

    variations = []
    for i in range(config.num_variations):
        light_set = []
        for base_light in base_lights:
            # Randomize intensity
            intensity_mult = random.uniform(*config.light_intensity_range)

            # Randomize angle
            angle_offset = random.uniform(*config.light_angle_range)

            # Create variation
            light_var = dict(base_light)
            light_var["intensity"] = base_light.get("intensity", 1000) * intensity_mult
            light_var["angle_offset"] = angle_offset
            light_var["name"] = f"{base_light.get('name', 'light')}_var_{i:03d}"

            light_set.append(light_var)

        variations.append(light_set)

    return variations


def clear_shuffle_set(shot_name: str) -> int:
    """
    Remove all shuffle cameras for a shot.

    Args:
        shot_name: Prefix of cameras to remove

    Returns:
        Number of cameras removed
    """
    if not BLENDER_AVAILABLE:
        return 0

    try:
        removed = 0
        to_remove = []

        for obj in bpy.data.objects:
            if obj.type == "CAMERA" and obj.name.startswith(f"{shot_name}_shuffle_"):
                to_remove.append(obj.name)

        for name in to_remove:
            obj = bpy.data.objects[name]
            cam_data = obj.data

            # Unlink from all collections
            for collection in bpy.data.collections:
                if obj.name in collection.objects:
                    collection.objects.unlink(obj)

            # Check scene collection
            if hasattr(bpy.context, "scene") and bpy.context.scene is not None:
                if obj.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(obj)

            # Remove object and data
            bpy.data.objects.remove(obj)
            if cam_data and cam_data.name in bpy.data.cameras:
                bpy.data.cameras.remove(cam_data)

            removed += 1

        return removed

    except Exception:
        return 0


def apply_shuffle_preset(
    preset_name: str,
    base_camera: Optional[CameraConfig] = None
) -> List[CameraConfig]:
    """
    Apply a shuffle preset by name.

    Args:
        preset_name: Name of preset from shuffle_presets.yaml
        base_camera: Optional base camera to vary from

    Returns:
        List of camera variations
    """
    from .preset_loader import get_shuffle_preset

    preset = get_shuffle_preset(preset_name)

    config = ShuffleConfig(
        enabled=preset.get("enabled", True),
        camera_angle_range=tuple(preset.get("camera_angle_range", (-15.0, 15.0))),
        camera_height_range=tuple(preset.get("camera_height_range", (-0.2, 0.2))),
        focal_length_range=tuple(preset.get("focal_length_range", (45.0, 85.0))),
        light_intensity_range=tuple(preset.get("light_intensity_range", (0.8, 1.2))),
        light_angle_range=tuple(preset.get("light_angle_range", (-30.0, 30.0))),
        exposure_range=tuple(preset.get("exposure_range", (-0.5, 0.5))),
        num_variations=preset.get("num_variations", preset.get("count", 5)),
        seed=preset.get("seed", None)
    )

    return generate_variations(config, base_camera)
