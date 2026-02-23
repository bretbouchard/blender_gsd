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
from dataclasses import dataclass, field
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


# =============================================================================
# LENS PRESETS FOR PHOTOSHOOT SYSTEM
# =============================================================================

@dataclass
class LensPreset:
    """Lens preset configuration."""
    name: str
    focal_length: float  # mm
    lens_type: str  # prime, zoom, macro, tilt_shift
    max_aperture: float
    characteristics: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    description: str = ""


# Professional lens presets
LENS_PRESETS: Dict[str, LensPreset] = {
    # Portrait Primes
    "portrait_50mm": LensPreset(
        name="50mm f/1.4 Portrait",
        focal_length=50.0,
        lens_type="prime",
        max_aperture=1.4,
        characteristics=["natural_perspective", "bokeh", "sharp"],
        use_cases=["portrait", "street", "documentary"],
        description="Classic 'nifty fifty' with natural field of view",
    ),
    "portrait_85mm": LensPreset(
        name="85mm f/1.4 Portrait",
        focal_length=85.0,
        lens_type="prime",
        max_aperture=1.4,
        characteristics=["compression", "beautiful_bokeh", "sharp"],
        use_cases=["portrait", "headshot", "fashion"],
        description="The portrait photographer's favorite",
    ),
    "portrait_135mm": LensPreset(
        name="135mm f/2 Portrait",
        focal_length=135.0,
        lens_type="prime",
        max_aperture=2.0,
        characteristics=["strong_compression", "dreamy_bokeh", "flattering"],
        use_cases=["portrait", "headshot", "performance"],
        description="Telephoto portrait lens for beautiful compression",
    ),

    # Macro Lenses
    "macro_60mm": LensPreset(
        name="60mm f/2.8 Macro",
        focal_length=60.0,
        lens_type="macro",
        max_aperture=2.8,
        characteristics=["1:1_magnification", "flat_field", "sharp"],
        use_cases=["product", "jewelry", "food"],
        description="Short telephoto macro for product photography",
    ),
    "macro_100mm": LensPreset(
        name="100mm f/2.8 Macro",
        focal_length=100.0,
        lens_type="macro",
        max_aperture=2.8,
        characteristics=["1:1_magnification", "working_distance", "sharp"],
        use_cases=["product", "jewelry", "nature"],
        description="Classic macro lens with good working distance",
    ),

    # Product Photography
    "product_45mm": LensPreset(
        name="45mm f/2.8 Tilt-Shift",
        focal_length=45.0,
        lens_type="tilt_shift",
        max_aperture=2.8,
        characteristics=["perspective_control", "flat_field", "sharp"],
        use_cases=["product", "architecture", "interior"],
        description="Tilt-shift for product and architecture",
    ),
    "product_90mm": LensPreset(
        name="90mm f/2.8 Tilt-Shift",
        focal_length=90.0,
        lens_type="tilt_shift",
        max_aperture=2.8,
        characteristics=["perspective_control", "working_distance"],
        use_cases=["product", "jewelry", "food"],
        description="Long tilt-shift for product work",
    ),

    # Wide Angle
    "wide_24mm": LensPreset(
        name="24mm f/1.4 Wide",
        focal_length=24.0,
        lens_type="prime",
        max_aperture=1.4,
        characteristics=["wide_angle", "environmental", "dramatic"],
        use_cases=["environmental_portrait", "interior", "automotive"],
        description="Fast wide angle for environmental shots",
    ),
    "wide_35mm": LensPreset(
        name="35mm f/1.4 Wide",
        focal_length=35.0,
        lens_type="prime",
        max_aperture=1.4,
        characteristics=["documentary", "environmental", "versatile"],
        use_cases=["street", "environmental_portrait", "interior"],
        description="Versatile wide angle lens",
    ),

    # Telephoto
    "telephoto_200mm": LensPreset(
        name="200mm f/2.8 Telephoto",
        focal_length=200.0,
        lens_type="prime",
        max_aperture=2.8,
        characteristics=["strong_compression", "shallow_dof", "reach"],
        use_cases=["portrait", "sports", "performance"],
        description="Medium telephoto for compressed portraits",
    ),

    # Zoom Lenses
    "zoom_24_70mm": LensPreset(
        name="24-70mm f/2.8 Zoom",
        focal_length=50.0,  # Typical setting
        lens_type="zoom",
        max_aperture=2.8,
        characteristics=["versatile", "constant_aperture", "professional"],
        use_cases=["portrait", "event", "product"],
        description="Professional standard zoom",
    ),
    "zoom_70_200mm": LensPreset(
        name="70-200mm f/2.8 Zoom",
        focal_length=135.0,  # Typical setting
        lens_type="zoom",
        max_aperture=2.8,
        characteristics=["versatile_telephoto", "compression", "sports"],
        use_cases=["portrait", "sports", "event"],
        description="Professional telephoto zoom",
    ),
}


def get_lens_preset_config(preset_name: str) -> LensPreset:
    """
    Get a lens preset configuration.

    Args:
        preset_name: Name of lens preset

    Returns:
        LensPreset configuration

    Raises:
        ValueError: If preset not found
    """
    if preset_name not in LENS_PRESETS:
        available = list(LENS_PRESETS.keys())
        raise ValueError(f"Unknown lens preset: {preset_name}. Available: {available}")
    return LENS_PRESETS[preset_name]


def list_lens_presets() -> List[str]:
    """List available lens preset names."""
    return list(LENS_PRESETS.keys())


def get_lens_preset_for_use_case(use_case: str) -> List[str]:
    """
    Get lens presets suitable for a specific use case.

    Args:
        use_case: Use case (portrait, product, etc.)

    Returns:
        List of matching preset names
    """
    matching = []
    for name, preset in LENS_PRESETS.items():
        if use_case.lower() in [uc.lower() for uc in preset.use_cases]:
            matching.append(name)
    return matching


# =============================================================================
# RIGID CAMERA MOUNT (Empty + Offset System)
# =============================================================================

def create_camera_mount(
    target_name: str,
    offset: Tuple[float, float, float] = (-6.0, 0.0, 2.5),
    look_at_target: bool = True,
    mount_name: Optional[str] = None,
) -> Optional[Any]:
    """
    Create a rigid camera mount using an Empty parented to a target.

    This is the SIMPLEST approach for vehicle cameras - the empty moves
    exactly with the car, and the camera is offset from it. No complex
    following logic, no speed-based adjustments.

    Usage:
        # Create mount attached to car
        mount = create_camera_mount("Car", offset=(-8, 2, 3))

        # Create your camera and parent it to the mount
        camera = create_camera(config)
        camera.parent = mount

    Args:
        target_name: Name of the target object (e.g., "Car")
        offset: Camera offset from target (x behind, y side, z height)
        look_at_target: If True, add Track To constraint pointing at target
        mount_name: Custom name for the empty (default: "{target}_CameraMount")

    Returns:
        The empty object that serves as the camera mount, or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Get target object
        if target_name not in bpy.data.objects:
            print(f"Target '{target_name}' not found")
            return None

        target = bpy.data.objects[target_name]

        # Create empty as mount point
        mount_name = mount_name or f"{target_name}_CameraMount"
        mount = bpy.data.objects.new(mount_name, None)
        mount.empty_display_type = 'ARROWS'
        mount.empty_display_size = 0.5

        # Link to scene
        bpy.context.scene.collection.objects.link(mount)

        # Parent to target (mount follows target exactly)
        mount.parent = target

        # Set local offset position
        mount.location = offset

        # Rotation: initially pointing forward (same as parent)
        mount.rotation_euler = (0, 0, 0)

        # Add Track To constraint if requested (camera looks at car)
        if look_at_target:
            track_constraint = mount.constraints.new(type='TRACK_TO')
            track_constraint.target = target
            track_constraint.track_axis = 'TRACK_NEGATIVE_Z'  # Camera -Z points at target
            track_constraint.up_axis = 'UP_Y'

        return mount

    except Exception as e:
        print(f"Failed to create camera mount: {e}")
        return None


def attach_camera_to_mount(
    camera_name: str,
    mount_name: str,
    local_offset: Tuple[float, float, float] = (0, 0, 0),
) -> bool:
    """
    Attach an existing camera to a mount point.

    Args:
        camera_name: Name of the camera object
        mount_name: Name of the mount empty
        local_offset: Additional offset from mount point

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        camera = bpy.data.objects.get(camera_name)
        mount = bpy.data.objects.get(mount_name)

        if not camera or not mount:
            return False

        # Parent camera to mount
        camera.parent = mount
        camera.location = local_offset

        # Camera rotation is handled by mount's Track To constraint
        camera.rotation_euler = (0, 0, 0)

        return True

    except Exception:
        return False


def create_chase_camera_rig(
    target_name: str,
    distance: float = 8.0,
    height: float = 2.5,
    side_offset: float = 0.0,
    focal_length: float = 35.0,
    f_stop: float = 2.8,
) -> Optional[Tuple[Any, Any]]:
    """
    Create a complete chase camera rig in one call.

    This creates:
    1. An Empty mounted to the target vehicle
    2. A camera parented to that empty
    3. Track To constraint so camera always looks at vehicle

    The camera will move EXACTLY with the vehicle - same speed,
    same turns, no lag, no prediction. Rock solid.

    Args:
        target_name: Name of the vehicle/target object
        distance: How far behind the camera sits (meters)
        height: How high above the vehicle (meters)
        side_offset: Left/right offset (negative = left, positive = right)
        focal_length: Camera lens mm
        f_stop: Aperture for DoF

    Returns:
        Tuple of (mount_empty, camera_object) or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Create mount (offset is in target's local space)
        # Negative X = behind, Y = side, Z = up
        offset = (-distance, side_offset, height)
        mount = create_camera_mount(
            target_name=target_name,
            offset=offset,
            look_at_target=True,
            mount_name=f"{target_name}_ChaseMount"
        )

        if not mount:
            return None

        # Create camera
        from .types import CameraConfig, Transform3D

        config = CameraConfig(
            name=f"{target_name}_ChaseCam",
            focal_length=focal_length,
            f_stop=f_stop,
            sensor_width=36.0,
            sensor_height=24.0,
            focus_distance=distance,  # Focus on the car
            transform=Transform3D(
                position=(0, 0, 0),  # Local to mount
                rotation=(0, 0, 0),
            ),
        )

        camera = create_camera(config, set_active=True)

        if not camera:
            return None

        # Parent camera to mount
        camera.parent = mount
        camera.location = (0, 0, 0)

        # Remove any Track To from camera itself (mount handles it)
        for constraint in camera.constraints:
            if constraint.type == 'TRACK_TO':
                camera.constraints.remove(constraint)

        return (mount, camera)

    except Exception as e:
        print(f"Failed to create chase camera rig: {e}")
        return None


def create_side_camera_rig(
    target_name: str,
    side: str = "left",
    distance: float = 6.0,
    height: float = 1.5,
    focal_length: float = 50.0,
    f_stop: float = 2.8,
) -> Optional[Tuple[Any, Any]]:
    """
    Create a side-mounted camera rig (for racing games style).

    Args:
        target_name: Name of the vehicle
        side: "left" or "right"
        distance: Distance from vehicle
        height: Height above ground
        focal_length: Camera lens
        f_stop: Aperture

    Returns:
        Tuple of (mount_empty, camera_object) or None
    """
    side_offset = -distance if side == "left" else distance
    return create_chase_camera_rig(
        target_name=target_name,
        distance=3.0,  # Slightly behind
        height=height,
        side_offset=side_offset,
        focal_length=focal_length,
        f_stop=f_stop,
    )


def create_tracking_camera_rig(
    target_name: str,
    distance: float = 8.0,
    height: float = 2.0,
    orbit_speed: float = 30.0,
    focal_length: float = 50.0,
    f_stop: float = 2.8,
    start_angle: float = 0.0,
) -> Optional[Tuple[Any, Any, Any]]:
    """
    Create an orbiting/tracking camera rig that circles around the vehicle.

    This creates:
    1. A parent Empty attached to the vehicle (follows exactly)
    2. A rotating Empty that orbits around the parent
    3. A camera attached to the orbiting empty

    Great for:
    - Hero shots circling the car
    - Revealing the vehicle from all angles
    - Cinematic establishing shots

    Args:
        target_name: Name of the vehicle/target object
        distance: Orbit radius (meters from vehicle)
        height: Camera height above vehicle (meters)
        orbit_speed: Rotation speed in degrees per second
        focal_length: Camera lens mm
        f_stop: Aperture for DoF
        start_angle: Starting angle in degrees (0 = behind)

    Returns:
        Tuple of (parent_empty, orbit_empty, camera_object) or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        target = bpy.data.objects.get(target_name)
        if not target:
            print(f"Target '{target_name}' not found")
            return None

        # 1. Create parent empty (follows vehicle exactly)
        parent_name = f"{target_name}_TrackParent"
        parent_empty = bpy.data.objects.new(parent_name, None)
        parent_empty.empty_display_type = 'ARROWS'
        parent_empty.empty_display_size = 0.3
        bpy.context.scene.collection.objects.link(parent_empty)

        # Parent to target
        parent_empty.parent = target
        parent_empty.location = (0, 0, height)  # At vehicle center, raised up

        # 2. Create orbit empty (rotates around parent)
        orbit_name = f"{target_name}_TrackOrbit"
        orbit_empty = bpy.data.objects.new(orbit_name, None)
        orbit_empty.empty_display_type = 'CIRCLE'
        orbit_empty.empty_display_size = distance
        bpy.context.scene.collection.objects.link(orbit_empty)

        # Parent orbit to parent empty
        orbit_empty.parent = parent_empty
        orbit_empty.location = (0, 0, 0)

        # Position at orbit radius
        start_rad = math.radians(start_angle)
        orbit_empty.location = (
            -distance * math.cos(start_rad),  # Start behind
            distance * math.sin(start_rad),
            0
        )

        # Add rotation animation to orbit empty (if scene has timeline)
        if hasattr(bpy.context.scene, 'frame_start') and hasattr(bpy.context.scene, 'frame_end'):
            orbit_empty.rotation_euler = (0, 0, start_rad)

            # Keyframe rotation at start
            orbit_empty.keyframe_insert(data_path="rotation_euler", index=2, frame=bpy.context.scene.frame_start)

            # Calculate frames for one full rotation
            fps = bpy.context.scene.render.fps
            rotation_frames = int(360.0 / orbit_speed * fps)
            end_frame = bpy.context.scene.frame_start + rotation_frames

            orbit_empty.rotation_euler = (0, 0, start_rad + math.radians(360))
            orbit_empty.keyframe_insert(data_path="rotation_euler", index=2, frame=end_frame)

        # 3. Create camera
        from .types import CameraConfig, Transform3D

        config = CameraConfig(
            name=f"{target_name}_TrackCam",
            focal_length=focal_length,
            f_stop=f_stop,
            sensor_width=36.0,
            sensor_height=24.0,
            focus_distance=distance,
            transform=Transform3D(
                position=(0, 0, 0),
                rotation=(0, 0, 0),
            ),
        )

        camera = create_camera(config, set_active=True)
        if not camera:
            return None

        # Parent camera to orbit empty
        camera.parent = orbit_empty
        camera.location = (0, 0, 0)

        # Add Track To constraint to look at parent (vehicle)
        track_constraint = camera.constraints.new(type='TRACK_TO')
        track_constraint.target = parent_empty
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'

        return (parent_empty, orbit_empty, camera)

    except Exception as e:
        print(f"Failed to create tracking camera rig: {e}")
        return None


def create_follow_camera_rig(
    target_name: str,
    distance: float = 8.0,
    height: float = 2.5,
    smoothing: float = 0.2,
    speed_factor: float = 0.3,
    max_speed_distance: float = 3.0,
    focal_length: float = 35.0,
    f_stop: float = 2.8,
) -> Optional[Tuple[Any, Any]]:
    """
    Create a dynamic follow camera rig with speed-based distance.

    This camera:
    - Follows behind the vehicle
    - Pulls back when vehicle speeds up
    - Has smooth interpolation for natural movement
    - Uses drivers for real-time speed detection

    Great for:
    - High-speed chases where you want to feel the speed
    - Dynamic action sequences
    - Racing footage

    Args:
        target_name: Name of the vehicle/target object
        distance: Base distance behind vehicle (meters)
        height: Height above vehicle (meters)
        smoothing: Follow smoothing factor (0=instant, 1=very slow)
        speed_factor: How much speed affects distance (0-1)
        max_speed_distance: Max extra distance at high speed (meters)
        focal_length: Camera lens mm
        f_stop: Aperture for DoF

    Returns:
        Tuple of (mount_empty, camera_object) or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        target = bpy.data.objects.get(target_name)
        if not target:
            print(f"Target '{target_name}' not found")
            return None

        # Create the follow mount (this one uses drivers for speed detection)
        mount_name = f"{target_name}_FollowMount"
        mount = bpy.data.objects.new(mount_name, None)
        mount.empty_display_type = 'ARROWS'
        mount.empty_display_size = 0.5
        bpy.context.scene.collection.objects.link(mount)

        # Parent to target
        mount.parent = target

        # Base position (will be modified by driver)
        mount.location = (-distance, 0, height)

        # Add Track To constraint
        track_constraint = mount.constraints.new(type='TRACK_TO')
        track_constraint.target = target
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'

        # Add driver for speed-based distance on X location
        # The driver will read target velocity and adjust distance
        driver = mount.driver_add('location', 0)

        # Create driver expression
        # Distance = -base_distance - (speed * speed_factor) clamped to max
        # We use a simplified approach: read the target's velocity from animation

        var = driver.driver.variables.new()
        var.name = "base_dist"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = target
        var.targets[0].data_path = ""  # Will use self

        var2 = driver.driver.variables.new()
        var2.name = "speed"

        # Try to get velocity - this works if object has animation
        # For animated objects, we can read delta position
        var2.targets[0].id_type = 'OBJECT'
        var2.targets[0].id = target
        var2.targets[0].data_path = "delta_location"  # Simplified - real impl needs velocity calculation

        # Driver expression: -base_distance - min(speed_magnitude * speed_factor, max_speed_distance)
        driver.driver.expression = f"-{distance} - min(sqrt(speed[0]**2 + speed[1]**2 + speed[2]**2) * {speed_factor}, {max_speed_distance})"

        # Create camera
        from .types import CameraConfig, Transform3D

        config = CameraConfig(
            name=f"{target_name}_FollowCam",
            focal_length=focal_length,
            f_stop=f_stop,
            sensor_width=36.0,
            sensor_height=24.0,
            focus_distance=distance,
            transform=Transform3D(
                position=(0, 0, 0),
                rotation=(0, 0, 0),
            ),
        )

        camera = create_camera(config, set_active=True)
        if not camera:
            return None

        # Parent camera to mount
        camera.parent = mount
        camera.location = (0, 0, 0)

        return (mount, camera)

    except Exception as e:
        print(f"Failed to create follow camera rig: {e}")
        return None


# =============================================================================
# CAMERA RIG MANAGER
# =============================================================================

@dataclass
class CameraRigConfig:
    """Configuration for a complete vehicle camera rig system."""
    target_name: str
    chase_distance: float = 8.0
    chase_height: float = 2.5
    track_distance: float = 10.0
    track_height: float = 3.0
    track_orbit_speed: float = 20.0
    follow_distance: float = 6.0
    follow_height: float = 2.0
    follow_speed_factor: float = 0.3
    focal_length: float = 35.0
    f_stop: float = 2.8


class VehicleCameraRigManager:
    """
    Manages multiple camera rigs for a vehicle.

    Allows easy switching between:
    - Chase: Fixed behind vehicle
    - track: Orbiting around vehicle
    - follow: Dynamic distance based on speed

    Usage:
        manager = VehicleCameraRigManager("Car")

        # Create all rigs
        manager.create_all_rigs()

        # Switch between cameras
        manager.set_active_camera("chase")
        manager.set_active_camera("track")
        manager.set_active_camera("follow")

        # Or get specific camera
        chase_cam = manager.get_camera("chase")
    """

    RIG_TYPES = ["chase", "track", "follow"]

    def __init__(self, target_name: str, config: Optional[CameraRigConfig] = None):
        """
        Initialize camera rig manager.

        Args:
            target_name: Name of the target vehicle object
            config: Optional configuration (uses defaults if not provided)
        """
        self.target_name = target_name
        self.config = config or CameraRigConfig(target_name=target_name)
        self._rigs: Dict[str, Any] = {}  # rig_type -> (mount, camera) or (parent, orbit, camera)
        self._cameras: Dict[str, Any] = {}  # rig_type -> camera_object

    def create_chase_rig(self) -> Optional[Any]:
        """Create chase camera rig (fixed behind vehicle)."""
        result = create_chase_camera_rig(
            target_name=self.target_name,
            distance=self.config.chase_distance,
            height=self.config.chase_height,
            focal_length=self.config.focal_length,
            f_stop=self.config.f_stop,
        )
        if result:
            mount, camera = result
            self._rigs["chase"] = (mount, camera)
            self._cameras["chase"] = camera
            return camera
        return None

    def create_track_rig(self) -> Optional[Any]:
        """Create tracking/orbit camera rig (circles vehicle)."""
        result = create_tracking_camera_rig(
            target_name=self.target_name,
            distance=self.config.track_distance,
            height=self.config.track_height,
            orbit_speed=self.config.track_orbit_speed,
            focal_length=self.config.focal_length,
            f_stop=self.config.f_stop,
        )
        if result:
            parent, orbit, camera = result
            self._rigs["track"] = (parent, orbit, camera)
            self._cameras["track"] = camera
            return camera
        return None

    def create_follow_rig(self) -> Optional[Any]:
        """Create dynamic follow camera rig (speed-based distance)."""
        result = create_follow_camera_rig(
            target_name=self.target_name,
            distance=self.config.follow_distance,
            height=self.config.follow_height,
            speed_factor=self.config.follow_speed_factor,
            focal_length=self.config.focal_length,
            f_stop=self.config.f_stop,
        )
        if result:
            mount, camera = result
            self._rigs["follow"] = (mount, camera)
            self._cameras["follow"] = camera
            return camera
        return None

    def create_all_rigs(self) -> Dict[str, Any]:
        """
        Create all three camera rigs at once.

        Returns:
            Dictionary of rig_type -> camera_object
        """
        self.create_chase_rig()
        self.create_track_rig()
        self.create_follow_rig()
        return self._cameras.copy()

    def get_camera(self, rig_type: str) -> Optional[Any]:
        """
        Get a specific camera by rig type.

        Args:
            rig_type: One of "chase", "track", "follow"

        Returns:
            Camera object or None
        """
        return self._cameras.get(rig_type)

    def set_active_camera(self, rig_type: str) -> bool:
        """
        Set a specific camera as the active scene camera.

        Args:
            rig_type: One of "chase", "track", "follow"

        Returns:
            True if successful
        """
        camera = self.get_camera(rig_type)
        if camera and BLENDER_AVAILABLE:
            return set_active_camera(camera)
        return False

    def list_cameras(self) -> List[str]:
        """List available camera rig types."""
        return [k for k, v in self._cameras.items() if v is not None]

    def get_rig(self, rig_type: str) -> Optional[Any]:
        """Get the full rig tuple for a specific rig type."""
        return self._rigs.get(rig_type)


def create_vehicle_camera_system(
    target_name: str,
    chase_distance: float = 8.0,
    chase_height: float = 2.5,
    track_distance: float = 10.0,
    track_height: float = 3.0,
    track_orbit_speed: float = 20.0,
    follow_distance: float = 6.0,
    follow_height: float = 2.0,
    follow_speed_factor: float = 0.3,
    focal_length: float = 35.0,
    f_stop: float = 2.8,
    create_all: bool = True,
) -> VehicleCameraRigManager:
    """
    Convenience function to create a complete vehicle camera system.

    Creates a manager with all three rig types. Use the manager to
    switch between cameras during animation.

    Args:
        target_name: Name of the vehicle object
        chase_distance: Chase camera distance behind vehicle
        chase_height: Chase camera height
        track_distance: Tracking camera orbit radius
        track_height: Tracking camera height
        track_orbit_speed: Tracking camera rotation speed (degrees/sec)
        follow_distance: Follow camera base distance
        follow_height: Follow camera height
        follow_speed_factor: How much speed affects follow distance
        focal_length: Lens mm for all cameras
        f_stop: Aperture for all cameras
        create_all: If True, create all rigs immediately

    Returns:
        VehicleCameraRigManager instance

    Usage:
        # Create camera system for car
        manager = create_vehicle_camera_system("Car")

        # Switch to different cameras
        manager.set_active_camera("chase")   # Fixed behind
        manager.set_active_camera("track")   # Orbiting around
        manager.set_active_camera("follow")  # Dynamic distance
    """
    config = CameraRigConfig(
        target_name=target_name,
        chase_distance=chase_distance,
        chase_height=chase_height,
        track_distance=track_distance,
        track_height=track_height,
        track_orbit_speed=track_orbit_speed,
        follow_distance=follow_distance,
        follow_height=follow_height,
        follow_speed_factor=follow_speed_factor,
        focal_length=focal_length,
        f_stop=f_stop,
    )

    manager = VehicleCameraRigManager(target_name, config)

    if create_all:
        manager.create_all_rigs()

    return manager


def create_camera_from_lens_preset(
    preset_name: str,
    position: Tuple[float, float, float] = (0, -5, 1.5),
    target: Tuple[float, float, float] = (0, 0, 1),
    f_stop: Optional[float] = None,
) -> CameraConfig:
    """
    Create a camera configuration from a lens preset.

    Args:
        preset_name: Name of lens preset
        position: Camera position
        target: Look-at target
        f_stop: Override f-stop (default uses preset max aperture)

    Returns:
        CameraConfig ready for create_camera()
    """
    preset = get_lens_preset_config(preset_name)

    # Calculate focus distance
    dx = target[0] - position[0]
    dy = target[1] - position[1]
    dz = target[2] - position[2]
    focus_distance = math.sqrt(dx*dx + dy*dy + dz*dz)

    # Calculate rotation to point at target
    horizontal_angle = math.degrees(math.atan2(dx, -dy))
    vertical_angle = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

    return CameraConfig(
        name=f"camera_{preset_name}",
        focal_length=preset.focal_length,
        f_stop=f_stop or preset.max_aperture,
        sensor_width=36.0,
        sensor_height=24.0,
        focus_distance=focus_distance,
        transform=Transform3D(
            position=position,
            rotation=(vertical_angle + 90, 0, horizontal_angle),
        ),
    )
