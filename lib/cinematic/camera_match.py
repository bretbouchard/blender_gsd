"""
Camera Matching Module (REQ-CINE-MATCH)

Camera matching from reference images and tracking data import.
Supports focal length estimation, horizon matching, and external
tracking data from Nuke, After Effects, FBX, etc.

Usage:
    from lib.cinematic.camera_match import (
        match_camera_to_reference, import_tracking_data, estimate_focal_length
    )

    # Match camera to reference image
    camera = match_camera_to_reference("reference.jpg", subject_bounds=(100, 100, 500, 400))

    # Import tracking data
    camera = import_tracking_data("tracking.fbx", format="fbx")
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import math

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import CameraMatchConfig, TrackingImportConfig, CameraProfile, CameraConfig


def estimate_focal_length(
    image_width: int,
    vanishing_points: List[Tuple[float, float]],
    sensor_width: float = 36.0
) -> float:
    """
    Estimate focal length from vanishing points.

    Uses the perspective projection relationship between vanishing
    points and focal length.

    Args:
        image_width: Image width in pixels
        vanishing_points: List of vanishing point (x, y) coordinates
        sensor_width: Camera sensor width in mm

    Returns:
        Estimated focal length in mm
    """
    if len(vanishing_points) < 2:
        # Not enough data - return default
        return 50.0

    # Calculate distance from image center to vanishing point
    center_x = image_width / 2

    # Use average distance for estimation
    distances = [abs(vp[0] - center_x) for vp in vanishing_points[:2]]
    avg_distance = sum(distances) / len(distances)

    # Focal length estimation from perspective geometry
    # f = (sensor_width * image_width) / (2 * vp_distance)
    if avg_distance > 0:
        # This is a simplified estimation
        focal_length = (sensor_width * image_width) / (2 * avg_distance * 2)
        # Clamp to reasonable range
        focal_length = max(14.0, min(200.0, focal_length))
    else:
        focal_length = 50.0

    return focal_length


def detect_horizon_line(
    image_path: str
) -> float:
    """
    Detect horizon line position in image.

    This is a placeholder - full implementation would use edge detection
    and vanishing point analysis.

    Args:
        image_path: Path to reference image

    Returns:
        Horizon line position (0-1 normalized)
    """
    # Placeholder - return default (middle of image)
    # Full implementation would analyze image for horizon
    return 0.5


def match_camera_to_reference(
    config: CameraMatchConfig,
    camera_name: str = "matched_camera",
    scene: Optional[Any] = None
) -> Optional[Any]:
    """
    Match a camera to a reference image.

    Creates a camera positioned and configured to match the perspective
    of the reference image.

    Args:
        config: Camera match configuration
        camera_name: Name for created camera
        scene: Optional scene (uses context if None)

    Returns:
        Created/modified camera object or None
    """
    if not BLENDER_AVAILABLE:
        return None

    if scene is None:
        scene = bpy.context.scene

    try:
        # Create or get camera
        if camera_name in bpy.data.objects:
            camera_obj = bpy.data.objects[camera_name]
        else:
            cam_data = bpy.data.cameras.new(name=f"{camera_name}_data")
            camera_obj = bpy.data.objects.new(camera_name, cam_data)
            scene.collection.objects.link(camera_obj)

        camera = camera_obj.data

        # Set background image for reference
        if config.reference_image and Path(config.reference_image).exists():
            # Add background image
            if not hasattr(camera, "background_images"):
                return camera_obj

            bg = camera.background_images.new()
            bg.image = bpy.data.images.load(config.reference_image)
            bg.display_depth = 'BACK'

        # Estimate focal length
        if config.auto_detect_focal and config.focal_length_estimate == 0:
            # Use vanishing points if available
            if config.vanishing_points:
                focal = estimate_focal_length(
                    1920,  # Assume 1080p
                    config.vanishing_points,
                    camera.sensor_width
                )
            else:
                focal = 50.0  # Default
        else:
            focal = config.focal_length_estimate if config.focal_length_estimate > 0 else 50.0

        camera.lens = focal

        # Set horizon line (affects camera pitch)
        if config.auto_detect_horizon:
            horizon = detect_horizon_line(config.reference_image)
        else:
            horizon = config.horizon_line

        # Adjust camera pitch based on horizon
        # Horizon at 0.5 = level camera, above = tilted up, below = tilted down
        pitch_offset = (horizon - 0.5) * 0.5  # Max 0.25 radians

        # Position camera at appropriate distance
        camera_obj.location = (0, -3, 1.7)  # Typical viewing position
        camera_obj.rotation_euler = (pitch_offset, 0, 0)

        return camera_obj

    except Exception:
        return None


def import_tracking_data(
    config: TrackingImportConfig,
    camera_name: str = "tracked_camera",
    scene: Optional[Any] = None
) -> Optional[Any]:
    """
    Import tracking data from external file.

    Supports FBX, Alembic, BVH, and custom JSON formats.

    Args:
        config: Tracking import configuration
        camera_name: Name for imported camera
        scene: Optional scene

    Returns:
        Imported camera object or None
    """
    if not BLENDER_AVAILABLE:
        return None

    if scene is None:
        scene = bpy.context.scene

    file_path = Path(config.file_path)
    if not file_path.exists():
        return None

    try:
        if config.format == "fbx":
            return _import_fbx_camera(file_path, camera_name, config, scene)
        elif config.format == "alembic":
            return _import_alembic_camera(file_path, camera_name, config, scene)
        elif config.format == "bvh":
            return _import_bvh_camera(file_path, camera_name, config, scene)
        elif config.format == "json":
            return _import_json_camera(file_path, camera_name, config, scene)
        elif config.format == "nuke_chan":
            return _import_nuke_chan(file_path, camera_name, config, scene)
        else:
            return None
    except Exception:
        return None


def _import_fbx_camera(
    file_path: Path,
    camera_name: str,
    config: TrackingImportConfig,
    scene: Any
) -> Optional[Any]:
    """Import camera from FBX file."""
    # Use Blender's FBX importer
    bpy.ops.import_scene.fbx(filepath=str(file_path))

    # Find imported camera
    for obj in scene.objects:
        if obj.type == "CAMERA":
            obj.name = camera_name
            # Apply coordinate conversion if needed
            if config.coordinate_system == "y_up":
                # Convert Y-up to Z-up (Blender default)
                pass  # Blender handles this in import
            return obj

    return None


def _import_alembic_camera(
    file_path: Path,
    camera_name: str,
    config: TrackingImportConfig,
    scene: Any
) -> Optional[Any]:
    """Import camera from Alembic file."""
    if not hasattr(bpy.ops, "wm"):
        return None

    bpy.ops.wm.alembic_import(filepath=str(file_path))

    for obj in scene.objects:
        if obj.type == "CAMERA":
            obj.name = camera_name
            return obj

    return None


def _import_bvh_camera(
    file_path: Path,
    camera_name: str,
    config: TrackingImportConfig,
    scene: Any
) -> Optional[Any]:
    """Import camera from BVH motion capture file."""
    if not hasattr(bpy.ops, "import_anim"):
        return None

    bpy.ops.import_anim.bvh(filepath=str(file_path))

    # BVH creates armature, need to extract camera from it
    # This is simplified - full implementation would create camera
    # that follows armature motion
    for obj in scene.objects:
        if obj.type == "ARMATURE":
            # Create camera parented to armature
            cam_data = bpy.data.cameras.new(name=f"{camera_name}_data")
            cam_obj = bpy.data.objects.new(camera_name, cam_data)
            scene.collection.objects.link(cam_obj)
            cam_obj.parent = obj
            return cam_obj

    return None


def _import_json_camera(
    file_path: Path,
    camera_name: str,
    config: TrackingImportConfig,
    scene: Any
) -> Optional[Any]:
    """Import camera from custom JSON format."""
    import json

    with open(file_path, "r") as f:
        data = json.load(f)

    # Create camera
    cam_data = bpy.data.cameras.new(name=f"{camera_name}_data")
    cam_obj = bpy.data.objects.new(camera_name, cam_data)
    scene.collection.objects.link(cam_obj)

    # Apply frame data
    frames = data.get("frames", [])
    for frame_data in frames:
        frame = frame_data.get("frame", 1) + config.frame_offset
        position = frame_data.get("position", [0, -3, 0])
        rotation = frame_data.get("rotation", [0, 0, 0])

        cam_obj.location = position
        cam_obj.rotation_euler = [math.radians(r) for r in rotation]

        cam_obj.keyframe_insert(data_path="location", frame=frame)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Set lens
    if "focal_length" in data:
        cam_data.lens = data["focal_length"]

    return cam_obj


def _import_nuke_chan(
    file_path: Path,
    camera_name: str,
    config: TrackingImportConfig,
    scene: Any
) -> Optional[Any]:
    """Import camera from Nuke .chan file."""
    # Create camera
    cam_data = bpy.data.cameras.new(name=f"{camera_name}_data")
    cam_obj = bpy.data.objects.new(camera_name, cam_data)
    scene.collection.objects.link(cam_obj)

    # Parse .chan file (tab-separated: frame tx ty tz rx ry rz fov)
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue

            parts = line.strip().split()
            if len(parts) >= 7:
                frame = int(float(parts[0])) + config.frame_offset
                tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
                rx, ry, rz = float(parts[4]), float(parts[5]), float(parts[6])

                # Nuke Y-up to Blender Z-up conversion
                if config.coordinate_system == "y_up":
                    ty, tz = tz, -ty

                cam_obj.location = (tx * config.scale_factor, ty * config.scale_factor, tz * config.scale_factor)
                cam_obj.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))

                cam_obj.keyframe_insert(data_path="location", frame=frame)
                cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

                if len(parts) >= 8:
                    fov = float(parts[7])
                    # Convert FOV to focal length (simplified)
                    cam_data.lens = 36.0 / (2 * math.tan(math.radians(fov / 2)))

    return cam_obj


def apply_camera_profile(
    camera_obj: Any,
    profile: CameraProfile
) -> None:
    """
    Apply camera device profile to camera.

    Sets sensor size, distortion parameters, and other device-specific settings.

    Args:
        camera_obj: Blender camera object
        profile: Camera profile to apply
    """
    if not BLENDER_AVAILABLE or camera_obj is None:
        return

    camera = camera_obj.data

    # Set sensor dimensions
    camera.sensor_width = profile.sensor_width
    camera.sensor_height = profile.sensor_height
    camera.lens = profile.focal_length

    # Note: Full distortion implementation would require compositor nodes
    # or lens distortion modifier (not available in base Blender)
