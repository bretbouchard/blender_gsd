"""
Camera System Module

Provides camera creation, configuration, and management functions.
All bpy access is guarded for testing outside Blender.

Usage:
    from lib.cinematic.camera import create_camera, configure_dof
    from lib.cinematic.types import CameraConfig, Transform3D

    # Create camera from config
    config = CameraConfig(
        name="hero_camera",
        focal_length=85.0,
        f_stop=2.8,
        focus_distance=5.0
    )
    camera = create_camera(config, set_active=True)
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import math

from .types import CameraConfig, Transform3D, PlumbBobConfig
from .preset_loader import get_lens_preset, get_sensor_preset, get_aperture_preset

# Guarded bpy import
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


# Aperture range constants (REQ-CINE-CAM)
APERTURE_MIN = 0.95  # f/0.95 - fastest practical lens
APERTURE_MAX = 22.0  # f/22 - smallest practical aperture


def validate_aperture(f_stop: float) -> bool:
    """
    Validate aperture f-stop is within valid range.

    Args:
        f_stop: F-stop value to validate

    Returns:
        True if valid

    Raises:
        ValueError: If f_stop is outside f/0.95 to f/22 range
    """
    if not (APERTURE_MIN <= f_stop <= APERTURE_MAX):
        raise ValueError(
            f"Invalid aperture f/{f_stop}. Must be between f/{APERTURE_MIN} and f/{APERTURE_MAX}"
        )
    return True


def create_camera(
    config: CameraConfig,
    collection: Optional[Any] = None,
    set_active: bool = False,
    plumb_bob_config: Optional[PlumbBobConfig] = None
) -> Optional[Any]:
    """
    Create a camera object from CameraConfig.

    Args:
        config: CameraConfig with all settings
        collection: Optional collection to link to (defaults to scene collection)
        set_active: If True, set as scene camera
        plumb_bob_config: Optional plumb bob config for focus mode handling

    Returns:
        Created camera object, or None if Blender not available

    Raises:
        ValueError: If aperture f_stop is outside valid range
    """
    # Validate aperture
    validate_aperture(config.f_stop)

    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check context
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return None

        scene = bpy.context.scene

        # Create camera data
        cam_data = bpy.data.cameras.new(name=config.name)
        cam_data.lens = config.focal_length
        cam_data.sensor_width = config.sensor_width
        cam_data.sensor_height = config.sensor_height

        # Create camera object
        cam_obj = bpy.data.objects.new(config.name, cam_data)

        # Apply transform
        transform_blender = config.transform.to_blender()
        cam_obj.location = transform_blender["location"]
        cam_obj.rotation_euler = transform_blender["rotation_euler"]
        cam_obj.scale = transform_blender["scale"]

        # Link to collection
        if collection is None:
            collection = scene.collection
        collection.objects.link(cam_obj)

        # Configure DoF if focus_distance > 0
        if config.focus_distance > 0:
            configure_dof(
                cam_data,
                config.f_stop,
                config.focus_distance,
                config.aperture_blades
            )

        # Set as active camera if requested
        if set_active:
            scene.camera = cam_obj

        return cam_obj

    except Exception:
        # Any Blender access error, return None
        return None


def configure_dof(
    camera: Any,
    f_stop: float,
    focus_distance: float,
    blades: int = 9
) -> bool:
    """
    Configure depth of field for a camera.

    Args:
        camera: Blender camera data object
        f_stop: Aperture f-stop value
        focus_distance: Focus distance in meters
        blades: Number of aperture blades (default 9)

    Returns:
        True if successful, False if failed

    Raises:
        ValueError: If aperture f_stop is outside valid range
    """
    # Validate aperture
    validate_aperture(f_stop)

    if not BLENDER_AVAILABLE:
        return False

    try:
        camera.dof.use_dof = True
        camera.dof.aperture_fstop = f_stop
        camera.dof.focus_distance = focus_distance
        camera.dof.aperture_blades = blades
        return True
    except Exception:
        return False


def set_focus_mode(
    camera_name: str,
    plumb_bob_config: PlumbBobConfig,
    target_position: Optional[Tuple[float, float, float]] = None
) -> float:
    """
    Set focus mode (auto/manual) and calculate focus distance.

    Args:
        camera_name: Name of the camera object
        plumb_bob_config: PlumbBobConfig with focus_mode and focus_distance
        target_position: Target position for auto focus mode (world coordinates)

    Returns:
        Focus distance that was set, or 0.0 if failed
    """
    if not BLENDER_AVAILABLE:
        return 0.0

    try:
        # Get camera object
        if camera_name not in bpy.data.objects:
            return 0.0

        cam_obj = bpy.data.objects[camera_name]
        if cam_obj.data is None or not hasattr(cam_obj.data, "dof"):
            return 0.0

        cam_data = cam_obj.data

        # Calculate focus distance based on mode
        if plumb_bob_config.focus_mode == "manual":
            # Use explicit focus distance from config
            focus_distance = plumb_bob_config.focus_distance
        else:
            # Auto mode: calculate from camera to target position
            if target_position is None:
                return 0.0

            # Calculate distance from camera to target
            cam_pos = cam_obj.location
            dx = target_position[0] - cam_pos[0]
            dy = target_position[1] - cam_pos[1]
            dz = target_position[2] - cam_pos[2]
            focus_distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        # Set focus distance
        if cam_data.dof.use_dof:
            cam_data.dof.focus_distance = focus_distance

        return focus_distance

    except Exception:
        return 0.0


def apply_lens_preset(camera: Any, preset_name: str) -> Optional[Dict[str, Any]]:
    """
    Apply lens preset to camera.

    Args:
        camera: Blender camera data object
        preset_name: Name of lens preset (e.g., "85mm_portrait")

    Returns:
        Preset dictionary, or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        preset = get_lens_preset(preset_name)
        camera.lens = preset.get("focal_length", 50.0)
        return preset
    except Exception:
        return None


def apply_sensor_preset(camera: Any, preset_name: str) -> Optional[Dict[str, Any]]:
    """
    Apply sensor preset to camera.

    Args:
        camera: Blender camera data object
        preset_name: Name of sensor preset (e.g., "full_frame")

    Returns:
        Preset dictionary, or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        preset = get_sensor_preset(preset_name)
        camera.sensor_width = preset.get("width", 36.0)
        camera.sensor_height = preset.get("height", 24.0)
        return preset
    except Exception:
        return None


def get_active_camera() -> Optional[Any]:
    """
    Get the active scene camera.

    Returns:
        Active camera object, or None if not available
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return None
        return bpy.context.scene.camera
    except Exception:
        return None


def set_active_camera(camera: Any) -> bool:
    """
    Set the active scene camera.

    Args:
        camera: Camera object to set as active

    Returns:
        True if successful, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False
        bpy.context.scene.camera = camera
        return True
    except Exception:
        return False


def delete_camera(name: str) -> bool:
    """
    Delete a camera object and its data.

    Args:
        name: Name of the camera to delete

    Returns:
        True if deleted, False if not found or failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Find camera object
        if name not in bpy.data.objects:
            return False

        cam_obj = bpy.data.objects[name]
        cam_data = cam_obj.data

        # Unlink from all collections
        for collection in bpy.data.collections:
            if cam_obj.name in collection.objects:
                collection.objects.unlink(cam_obj)

        # Also check scene collection
        if hasattr(bpy.context, "scene") and bpy.context.scene is not None:
            scene_collection = bpy.context.scene.collection
            if cam_obj.name in scene_collection.objects:
                scene_collection.objects.unlink(cam_obj)

        # Delete object and data
        bpy.data.objects.remove(cam_obj)
        if cam_data and cam_data.name in bpy.data.cameras:
            bpy.data.cameras.remove(cam_data)

        return True

    except Exception:
        return False


def list_cameras() -> List[str]:
    """
    List all camera object names in the current scene.

    Returns:
        List of camera names
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        cameras = []
        for obj in bpy.data.objects:
            if obj.type == "CAMERA":
                cameras.append(obj.name)
        return sorted(cameras)
    except Exception:
        return []
