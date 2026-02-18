"""
Lighting System Module

Provides light creation, configuration, and management functions for
cinematic product visualization. Supports area, spot, point, and sun lights
with color temperature control and light linking.

All bpy access is guarded for testing outside Blender.

Usage:
    from lib.cinematic.lighting import create_light, create_area_light
    from lib.cinematic.types import LightConfig, Transform3D

    # Create light from config
    config = LightConfig(
        name="key_light",
        light_type="area",
        intensity=1000.0,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.0
    )
    light = create_light(config)

    # Apply lighting rig preset
    from lib.cinematic.lighting import apply_lighting_rig
    result = apply_lighting_rig("three_point_soft")
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import math

from .types import LightConfig, Transform3D, LightRigConfig
from .preset_loader import get_lighting_rig_preset

# Guarded bpy import
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


# Area light shape constants
AREA_SHAPES = ["SQUARE", "RECTANGLE", "DISK", "ELLIPSE"]

# Minimum Blender version for light linking
BLENDER_40_MIN = (4, 0, 0)


def _validate_area_shape(shape: str) -> bool:
    """
    Validate area light shape is valid Blender value.

    Args:
        shape: Shape name to validate

    Returns:
        True if valid

    Raises:
        ValueError: If shape is not valid
    """
    shape_upper = shape.upper()
    if shape_upper not in AREA_SHAPES:
        raise ValueError(
            f"Invalid area light shape '{shape}'. "
            f"Must be one of: {AREA_SHAPES}"
        )
    return True


def create_light(
    config: LightConfig,
    collection: Optional[Any] = None,
    link_to_scene: bool = True
) -> Optional[Any]:
    """
    Create a light object from LightConfig.

    Handles all four light types: area, spot, point, sun.
    Configures type-specific properties and applies transform.

    Args:
        config: LightConfig with all settings
        collection: Optional collection to link to (defaults to scene collection)
        link_to_scene: If True, link to scene collection when no collection specified

    Returns:
        Created light object, or None if Blender not available

    Raises:
        ValueError: If area shape is invalid
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check context
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return None

        scene = bpy.context.scene
        light_type = config.light_type.upper()

        # Create light data
        light_data = bpy.data.lights.new(name=config.name, type=light_type)

        # Common properties
        light_data.color = list(config.color)
        light_data.energy = config.intensity
        light_data.shadow_soft_size = config.shadow_soft_size
        light_data.use_shadow = config.use_shadow

        # Area-specific properties
        if light_type == "AREA":
            _validate_area_shape(config.shape)
            light_data.shape = config.shape.upper()
            light_data.size = config.size
            if config.shape.upper() in ["RECTANGLE", "ELLIPSE"]:
                light_data.size_y = config.size_y
            if hasattr(light_data, "spread"):
                light_data.spread = config.spread

        # Spot-specific properties
        elif light_type == "SPOT":
            light_data.spot_size = config.spot_size
            light_data.spot_blend = config.spot_blend

        # Color temperature (Blender 4.0+)
        if hasattr(light_data, "use_temperature"):
            light_data.use_temperature = config.use_temperature
            if config.use_temperature:
                light_data.temperature = config.temperature

        # Create light object
        light_obj = bpy.data.objects.new(config.name, light_data)

        # Apply transform
        transform_blender = config.transform.to_blender()
        light_obj.location = transform_blender["location"]
        light_obj.rotation_euler = transform_blender["rotation_euler"]
        light_obj.scale = transform_blender["scale"]

        # Link to collection
        if collection is None and link_to_scene:
            collection = scene.collection
        if collection is not None:
            collection.objects.link(light_obj)

        return light_obj

    except Exception:
        # Any Blender access error, return None
        return None


def create_area_light(
    name: str,
    position: Tuple[float, float, float],
    size: float,
    shape: str = "RECTANGLE",
    intensity: float = 1000.0,
    size_y: Optional[float] = None,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    **kwargs
) -> Optional[Any]:
    """
    Convenience function for creating area lights.

    Args:
        name: Light name
        position: World position (x, y, z)
        size: Width or radius of light
        shape: Area shape (SQUARE, RECTANGLE, DISK, ELLIPSE)
        intensity: Light intensity in watts
        size_y: Height for RECTANGLE/ELLIPSE (defaults to size)
        color: RGB color (0-1 range)
        rotation: Euler rotation in degrees (x, y, z)
        **kwargs: Additional LightConfig properties

    Returns:
        Created light object, or None if Blender not available
    """
    # Default size_y to size for non-rectangular shapes
    if size_y is None:
        size_y = size

    config = LightConfig(
        name=name,
        light_type="area",
        intensity=intensity,
        color=color,
        transform=Transform3D(
            position=position,
            rotation=rotation
        ),
        shape=shape,
        size=size,
        size_y=size_y,
        shadow_soft_size=kwargs.get("shadow_soft_size", 0.1),
        use_shadow=kwargs.get("use_shadow", True),
        spread=kwargs.get("spread", 1.047),
        use_temperature=kwargs.get("use_temperature", False),
        temperature=kwargs.get("temperature", 6500.0)
    )

    return create_light(config)


def create_spot_light(
    name: str,
    position: Tuple[float, float, float],
    spot_size: float = 45.0,
    spot_blend: float = 0.5,
    intensity: float = 1000.0,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    **kwargs
) -> Optional[Any]:
    """
    Convenience function for creating spot lights.

    Converts spot_size from degrees to radians internally.

    Args:
        name: Light name
        position: World position (x, y, z)
        spot_size: Cone angle in degrees (converted to radians)
        spot_blend: Edge softness 0-1
        intensity: Light intensity in watts
        color: RGB color (0-1 range)
        rotation: Euler rotation in degrees (x, y, z)
        **kwargs: Additional LightConfig properties

    Returns:
        Created light object, or None if Blender not available
    """
    # Convert degrees to radians
    spot_size_rad = math.radians(spot_size)

    config = LightConfig(
        name=name,
        light_type="spot",
        intensity=intensity,
        color=color,
        transform=Transform3D(
            position=position,
            rotation=rotation
        ),
        spot_size=spot_size_rad,
        spot_blend=spot_blend,
        shadow_soft_size=kwargs.get("shadow_soft_size", 0.1),
        use_shadow=kwargs.get("use_shadow", True),
        use_temperature=kwargs.get("use_temperature", False),
        temperature=kwargs.get("temperature", 6500.0)
    )

    return create_light(config)


def create_point_light(
    name: str,
    position: Tuple[float, float, float],
    intensity: float = 1000.0,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    **kwargs
) -> Optional[Any]:
    """
    Convenience function for creating point lights.

    Args:
        name: Light name
        position: World position (x, y, z)
        intensity: Light intensity in watts
        color: RGB color (0-1 range)
        **kwargs: Additional LightConfig properties

    Returns:
        Created light object, or None if Blender not available
    """
    config = LightConfig(
        name=name,
        light_type="point",
        intensity=intensity,
        color=color,
        transform=Transform3D(
            position=position,
            rotation=kwargs.get("rotation", (0.0, 0.0, 0.0))
        ),
        shadow_soft_size=kwargs.get("shadow_soft_size", 0.1),
        use_shadow=kwargs.get("use_shadow", True),
        use_temperature=kwargs.get("use_temperature", False),
        temperature=kwargs.get("temperature", 6500.0)
    )

    return create_light(config)


def create_sun_light(
    name: str,
    rotation: Tuple[float, float, float],
    intensity: float = 1.0,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    **kwargs
) -> Optional[Any]:
    """
    Convenience function for creating sun lights.

    Sun lights are directional and position-independent.
    Only rotation affects the lighting direction.

    Args:
        name: Light name
        rotation: Euler rotation in degrees (x, y, z)
        intensity: Light intensity
        color: RGB color (0-1 range)
        **kwargs: Additional LightConfig properties

    Returns:
        Created light object, or None if Blender not available
    """
    config = LightConfig(
        name=name,
        light_type="sun",
        intensity=intensity,
        color=color,
        transform=Transform3D(
            position=kwargs.get("position", (0.0, 0.0, 0.0)),
            rotation=rotation
        ),
        shadow_soft_size=kwargs.get("shadow_soft_size", 0.1),
        use_shadow=kwargs.get("use_shadow", True),
        use_temperature=kwargs.get("use_temperature", False),
        temperature=kwargs.get("temperature", 6500.0)
    )

    return create_light(config)


def setup_light_linking(
    light_name: str,
    receiver_objects: List[str],
    blocker_objects: Optional[List[str]] = None
) -> bool:
    """
    Configure light to only illuminate specific objects.

    Light linking is a Blender 4.0+ feature for selective illumination.
    Only specified receiver objects will be lit by this light.

    Args:
        light_name: Name of the light object
        receiver_objects: List of object names that should receive light
        blocker_objects: Optional list of objects that block light (not yet used)

    Returns:
        True if successful, False if failed or Blender < 4.0

    Note:
        Blocker collection is configured but light linking shadow blockers
        requires additional setup in Blender's shader nodes.
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Version check for Blender 4.0+
        if bpy.app.version < BLENDER_40_MIN:
            return False

        # Check context
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene

        # Get light object
        if light_name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[light_name]
        if light_obj.data is None or not hasattr(light_obj.data, "type"):
            return False

        # Check light linking is available
        if not hasattr(light_obj, "light_linking"):
            return False

        # Create receiver collection if not exists
        receiver_coll_name = f"{light_name}_receivers"
        if receiver_coll_name not in bpy.data.collections:
            receiver_coll = bpy.data.collections.new(receiver_coll_name)
            scene.collection.children.link(receiver_coll)
        else:
            receiver_coll = bpy.data.collections[receiver_coll_name]

        # Link receiver objects to collection
        for obj_name in receiver_objects:
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                # Link to receiver collection if not already
                if obj_name not in receiver_coll.objects:
                    receiver_coll.objects.link(obj)

        # Set receiver collection on light
        light_obj.light_linking.receiver_collection = receiver_coll

        # Handle blockers if specified
        if blocker_objects:
            blocker_coll_name = f"{light_name}_blockers"
            if blocker_coll_name not in bpy.data.collections:
                blocker_coll = bpy.data.collections.new(blocker_coll_name)
                scene.collection.children.link(blocker_coll)
            else:
                blocker_coll = bpy.data.collections[blocker_coll_name]

            for obj_name in blocker_objects:
                if obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    if obj_name not in blocker_coll.objects:
                        blocker_coll.objects.link(obj)

            # Set blocker collection
            if hasattr(light_obj.light_linking, "blocker_collection"):
                light_obj.light_linking.blocker_collection = blocker_coll

        return True

    except Exception:
        return False


def apply_lighting_rig(
    preset_name: str,
    target_position: Tuple[float, float, float] = (0, 0, 0),
    intensity_scale: float = 1.0,
    collection: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Apply a lighting rig preset from YAML configuration.

    Loads preset from configs/cinematic/lighting/rig_presets.yaml.
    Handles preset inheritance via the 'extends' field.
    Converts angle_distance positioning to world coordinates.

    Args:
        preset_name: Name of the lighting rig preset
        target_position: Center position for the rig (default origin)
        intensity_scale: Multiplier for all light intensities
        collection: Optional collection to link lights to

    Returns:
        Dictionary containing:
        - preset_name: Name of applied preset
        - lights_created: List of created light names
        - light_objects: Dictionary of light name -> object
        - total_lights: Number of lights created

    Raises:
        ValueError: If preset not found or invalid
        FileNotFoundError: If preset file doesn't exist
    """
    if not BLENDER_AVAILABLE:
        return {
            "preset_name": preset_name,
            "lights_created": [],
            "light_objects": {},
            "total_lights": 0
        }

    try:
        # Load preset (handles inheritance internally)
        preset = _load_preset_with_inheritance(preset_name)

        lights_created = []
        light_objects = {}

        # Get lights from preset
        lights_data = preset.get("lights", {})

        for light_name, light_data in lights_data.items():
            # Build LightConfig from preset data
            config = _build_light_config(
                light_name,
                light_data,
                target_position,
                intensity_scale
            )

            # Create the light
            light_obj = create_light(config, collection)

            if light_obj is not None:
                lights_created.append(light_name)
                light_objects[light_name] = light_obj

        return {
            "preset_name": preset_name,
            "lights_created": lights_created,
            "light_objects": light_objects,
            "total_lights": len(lights_created)
        }

    except Exception as e:
        raise ValueError(f"Failed to apply lighting rig '{preset_name}': {e}")


def _load_preset_with_inheritance(preset_name: str) -> Dict[str, Any]:
    """
    Load preset and resolve inheritance chain.

    Args:
        preset_name: Name of the preset to load

    Returns:
        Fully resolved preset dictionary with all inherited properties
    """
    # Load base preset
    preset = get_lighting_rig_preset(preset_name)

    # Handle inheritance
    extends = preset.get("extends", "")
    if extends:
        try:
            parent = _load_preset_with_inheritance(extends)

            # Merge lights: parent lights as base, child lights override
            merged_lights = parent.get("lights", {}).copy()
            merged_lights.update(preset.get("lights", {}))

            # Merge other properties
            result = parent.copy()
            result.update(preset)
            result["lights"] = merged_lights

            return result
        except Exception:
            # If parent not found, use current preset
            pass

    return preset


def _build_light_config(
    light_name: str,
    light_data: Dict[str, Any],
    target_position: Tuple[float, float, float],
    intensity_scale: float
) -> LightConfig:
    """
    Build LightConfig from preset data.

    Handles angle_distance positioning and converts to world coordinates.

    Args:
        light_name: Name for the light
        light_data: Light configuration dictionary from preset
        target_position: Target center position for positioning
        intensity_scale: Intensity multiplier

    Returns:
        Configured LightConfig instance
    """
    # Get positioning data
    position_data = light_data.get("position", {})
    position_type = position_data.get("type", "absolute")

    if position_type == "angle_distance":
        # Convert angle/distance to world coordinates
        angle_deg = position_data.get("angle", 0.0)
        distance = position_data.get("distance", 5.0)
        height = position_data.get("height", 2.0)

        # Convert angle to radians
        angle_rad = math.radians(angle_deg)

        # Calculate world position
        x = target_position[0] + distance * math.sin(angle_rad)
        y = target_position[1] - distance * math.cos(angle_rad)
        z = target_position[2] + height

        position = (x, y, z)

        # Calculate rotation to point at target
        # Point light at target (simple look-at rotation)
        dx = target_position[0] - x
        dy = target_position[1] - y
        dz = target_position[2] - z

        # Calculate rotation angles
        horizontal_angle = math.degrees(math.atan2(dx, -dy))
        vertical_angle = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

        rotation = (vertical_angle + 90, 0.0, horizontal_angle)
    else:
        # Absolute positioning
        pos_list = position_data.get("coordinates", [0, 0, 0])
        position = tuple(pos_list) if isinstance(pos_list, list) else (0, 0, 0)
        rotation = tuple(light_data.get("rotation", [0, 0, 0]))

    # Build transform
    transform = Transform3D(
        position=position,
        rotation=rotation,
        scale=tuple(light_data.get("scale", [1, 1, 1]))
    )

    # Get color
    color_data = light_data.get("color", [1.0, 1.0, 1.0])
    color = tuple(color_data) if isinstance(color_data, list) else (1.0, 1.0, 1.0)

    # Calculate scaled intensity
    intensity = light_data.get("intensity", 1000.0) * intensity_scale

    # Build config
    return LightConfig(
        name=light_name,
        light_type=light_data.get("light_type", "area"),
        intensity=intensity,
        color=color,
        transform=transform,
        shape=light_data.get("shape", "RECTANGLE"),
        size=light_data.get("size", 1.0),
        size_y=light_data.get("size_y", 1.0),
        spread=light_data.get("spread", 1.047),
        spot_size=light_data.get("spot_size", 0.785),
        spot_blend=light_data.get("spot_blend", 0.5),
        shadow_soft_size=light_data.get("shadow_soft_size", 0.1),
        use_shadow=light_data.get("use_shadow", True),
        use_temperature=light_data.get("use_temperature", False),
        temperature=light_data.get("temperature", 6500.0)
    )


def delete_light(name: str) -> bool:
    """
    Delete a light object and its data.

    Args:
        name: Name of the light to delete

    Returns:
        True if deleted, False if not found or failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Find light object
        if name not in bpy.data.objects:
            return False

        light_obj = bpy.data.objects[name]
        light_data = light_obj.data

        # Unlink from all collections
        for collection in bpy.data.collections:
            if light_obj.name in collection.objects:
                collection.objects.unlink(light_obj)

        # Also check scene collection
        if hasattr(bpy.context, "scene") and bpy.context.scene is not None:
            scene_collection = bpy.context.scene.collection
            if light_obj.name in scene_collection.objects:
                scene_collection.objects.unlink(light_obj)

        # Delete object and data
        bpy.data.objects.remove(light_obj)
        if light_data and light_data.name in bpy.data.lights:
            bpy.data.lights.remove(light_data)

        return True

    except Exception:
        return False


def list_lights() -> List[str]:
    """
    List all light object names in the current scene.

    Returns:
        List of light names
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        lights = []
        for obj in bpy.data.objects:
            if obj.type == "LIGHT":
                lights.append(obj.name)
        return sorted(lights)
    except Exception:
        return []


def get_light(name: str) -> Optional[Any]:
    """
    Get a light object by name.

    Args:
        name: Name of the light

    Returns:
        Light object, or None if not found
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        if name not in bpy.data.objects:
            return None

        obj = bpy.data.objects[name]
        if obj.type == "LIGHT":
            return obj
        return None
    except Exception:
        return None


def set_light_intensity(name: str, intensity: float) -> bool:
    """
    Set the intensity of a light.

    Args:
        name: Name of the light
        intensity: New intensity value in watts

    Returns:
        True if successful, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        light_obj = get_light(name)
        if light_obj is None:
            return False

        light_obj.data.energy = intensity
        return True
    except Exception:
        return False


def set_light_color(name: str, color: Tuple[float, float, float]) -> bool:
    """
    Set the color of a light.

    Args:
        name: Name of the light
        color: RGB color tuple (0-1 range)

    Returns:
        True if successful, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        light_obj = get_light(name)
        if light_obj is None:
            return False

        light_obj.data.color = list(color)
        return True
    except Exception:
        return False


def set_light_temperature(name: str, temperature: float) -> bool:
    """
    Set the color temperature of a light (Blender 4.0+).

    Args:
        name: Name of the light
        temperature: Color temperature in Kelvin

    Returns:
        True if successful, False if failed or Blender < 4.0
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if bpy.app.version < BLENDER_40_MIN:
            return False

        light_obj = get_light(name)
        if light_obj is None:
            return False

        if hasattr(light_obj.data, "use_temperature"):
            light_obj.data.use_temperature = True
            light_obj.data.temperature = temperature
            return True
        return False
    except Exception:
        return False
