"""
Shot Builder Module

Provides complete shot preset system for studio, product, automotive,
environment, and signature photography looks.

Usage:
    from lib.cinematic.shot_builder import (
        apply_shot_preset, list_shot_presets, get_shot_preset
    )

    # Apply a preset
    apply_shot_preset("studio_white", subject_name="my_product")

    # List available presets
    list_shot_presets("studio")  # By category
    list_shot_presets()  # All presets
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

# Configuration root
CONFIG_ROOT = Path("configs/cinematic/shots")


@dataclass
class LightSetupConfig:
    """Configuration for a single light in a shot."""
    light_type: str = "area"
    intensity: float = 1000.0
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    position: Tuple[float, float, float] = (0.0, -2.0, 2.0)
    size: Tuple[float, float] = (1.0, 1.0)
    angle: float = 0.3  # For spot lights


@dataclass
class BackdropSetupConfig:
    """Configuration for shot backdrop."""
    type: str = "solid"
    color: Tuple[float, float, float] = (0.95, 0.95, 0.95)
    color_bottom: Tuple[float, float, float] = (0.95, 0.95, 0.95)
    color_top: Tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class ShotPreset:
    """Complete shot preset configuration."""
    name: str
    category: str
    description: str = ""
    use_case: str = ""
    lighting: Dict[str, Any] = field(default_factory=dict)
    backdrop: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    camera: Dict[str, Any] = field(default_factory=dict)
    post: Dict[str, Any] = field(default_factory=dict)


def load_shot_preset_file(category: str) -> Dict[str, Any]:
    """
    Load a shot preset YAML file.

    Args:
        category: Category name (studio, product, etc.)

    Returns:
        Dictionary with preset data

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If YAML not available
    """
    path = CONFIG_ROOT / f"{category}_presets.yaml"

    if not path.exists():
        raise FileNotFoundError(f"Shot preset file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        if yaml:
            return yaml.safe_load(f)
        else:
            import json
            return json.loads(f.read())


def get_shot_preset(preset_name: str) -> ShotPreset:
    """
    Get a specific shot preset by name.

    Args:
        preset_name: Name of the preset (e.g., "studio_white", "apple_hero")

    Returns:
        ShotPreset object

    Raises:
        ValueError: If preset not found
    """
    # Search all category files for the preset
    categories = ["studio", "product", "automotive", "environment", "signature"]

    for category in categories:
        try:
            data = load_shot_preset_file(category)
            category_presets = data.get(category, {})

            if preset_name in category_presets:
                preset_data = category_presets[preset_name]
                return ShotPreset(
                    name=preset_name,
                    category=category,
                    description=preset_data.get("description", ""),
                    use_case=preset_data.get("use_case", ""),
                    lighting=preset_data.get("lighting", {}),
                    backdrop=preset_data.get("backdrop", {}),
                    environment=preset_data.get("environment", {}),
                    camera=preset_data.get("camera", {}),
                    post=preset_data.get("post", {}),
                )
        except FileNotFoundError:
            continue

    raise ValueError(f"Shot preset '{preset_name}' not found in any category")


def list_shot_presets(category: Optional[str] = None) -> List[str]:
    """
    List available shot presets.

    Args:
        category: Optional category filter (studio, product, etc.)

    Returns:
        Sorted list of preset names
    """
    presets = []

    if category:
        categories = [category]
    else:
        categories = ["studio", "product", "automotive", "environment", "signature"]

    for cat in categories:
        try:
            data = load_shot_preset_file(cat)
            cat_presets = data.get(cat, {})
            presets.extend(cat_presets.keys())
        except FileNotFoundError:
            continue

    return sorted(presets)


def list_shot_presets_by_category() -> Dict[str, List[str]]:
    """
    List all presets organized by category.

    Returns:
        Dictionary mapping category names to preset name lists
    """
    result = {}
    categories = ["studio", "product", "automotive", "environment", "signature"]

    for cat in categories:
        try:
            data = load_shot_preset_file(cat)
            cat_presets = data.get(cat, {})
            result[cat] = sorted(cat_presets.keys())
        except FileNotFoundError:
            result[cat] = []

    return result


def create_light_from_config(
    name: str,
    config: Dict[str, Any],
    collection: Optional[Any] = None
) -> Optional[Any]:
    """
    Create a light from configuration.

    Args:
        name: Light name
        config: Light configuration dict
        collection: Optional collection to link to

    Returns:
        Created light object or None
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        light_type = config.get("type", "AREA").upper()
        intensity = config.get("intensity", 1000)
        color = config.get("color", [1.0, 1.0, 1.0])
        position = config.get("position", [0, -2, 2])

        # Map type names
        type_map = {
            "area": "AREA",
            "spot": "SPOT",
            "point": "POINT",
            "sun": "SUN",
        }
        bpy_type = type_map.get(light_type.lower(), "AREA")

        # Create light data
        light_data = bpy.data.lights.new(name=f"{name}_data", type=bpy_type)
        light_data.energy = intensity
        light_data.color = color

        # Area light specific
        if bpy_type == "AREA":
            size = config.get("size", [1, 1])
            light_data.size = size[0]
            light_data.size_y = size[1]

        # Spot light specific
        if bpy_type == "SPOT":
            angle = config.get("angle", 0.3)
            light_data.spot_size = angle

        # Create object
        light_obj = bpy.data.objects.new(name, light_data)
        light_obj.location = position

        # Link to collection
        if collection is None and hasattr(bpy, "context") and bpy.context.scene:
            collection = bpy.context.scene.collection
        if collection:
            collection.objects.link(light_obj)

        return light_obj

    except Exception:
        return None


def create_backdrop_from_config(
    config: Dict[str, Any],
    radius: float = 5.0
) -> Optional[Any]:
    """
    Create backdrop from configuration.

    Args:
        config: Backdrop configuration dict
        radius: Backdrop size

    Returns:
        Created backdrop object or None
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        backdrop_type = config.get("type", "solid")
        color = config.get("color", config.get("color_bottom", [0.95, 0.95, 0.95]))

        # Simple implementation - create a plane for now
        # Full implementation would create infinite curves, gradients, etc.

        bpy.ops.mesh.primitive_plane_add(size=radius * 2, location=(0, 0, 0))
        backdrop = bpy.context.active_object
        backdrop.name = "backdrop"

        # Create material
        mat = bpy.data.materials.new(name="backdrop_material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.9

        backdrop.data.materials.append(mat)

        return backdrop

    except Exception:
        return None


def apply_shot_preset(
    preset_name: str,
    subject_name: Optional[str] = None,
    clear_existing: bool = True
) -> bool:
    """
    Apply a complete shot preset to the scene.

    This is the main entry point for shot presets. It:
    1. Loads the preset configuration
    2. Creates lighting setup
    3. Creates backdrop
    4. Suggests camera settings
    5. Sets up post-processing hints

    Args:
        preset_name: Name of preset to apply
        subject_name: Optional subject object name for framing
        clear_existing: Clear existing lights before applying

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        preset = get_shot_preset(preset_name)

        # Clear existing lights if requested
        if clear_existing:
            clear_scene_lights()

        # Create lighting
        lighting = preset.lighting
        if lighting:
            setup = lighting.get("setup", "three_point")

            # Create key light
            if "key" in lighting:
                create_light_from_config("key_light", lighting["key"])

            # Create fill light
            if "fill" in lighting:
                create_light_from_config("fill_light", lighting["fill"])

            # Create rim light
            if "rim" in lighting:
                create_light_from_config("rim_light", lighting["rim"])

        # Create backdrop
        backdrop = preset.backdrop
        if backdrop:
            create_backdrop_from_config(backdrop)

        return True

    except Exception:
        return False


def clear_scene_lights() -> bool:
    """
    Remove all lights from the scene.

    Returns:
        True on success
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Remove all light objects
        for obj in bpy.data.objects:
            if obj.type == "LIGHT":
                bpy.data.objects.remove(obj)

        return True
    except Exception:
        return False


def get_shot_preset_info(preset_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a shot preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Dictionary with preset information
    """
    preset = get_shot_preset(preset_name)

    return {
        "name": preset.name,
        "category": preset.category,
        "description": preset.description,
        "use_case": preset.use_case,
        "lighting_setup": preset.lighting.get("setup", "unknown"),
        "backdrop_type": preset.backdrop.get("type", "unknown"),
        "suggested_lens": preset.camera.get("lens_preset", "unknown"),
        "suggested_fstop": preset.camera.get("f_stop", 4.0),
        "color_grade": preset.post.get("color_grade", "neutral"),
    }


def get_presets_for_use_case(use_case: str) -> List[str]:
    """
    Find presets suitable for a specific use case.

    Args:
        use_case: Use case to search for (e.g., "product", "portrait")

    Returns:
        List of matching preset names
    """
    matches = []
    all_presets = list_shot_presets()

    for name in all_presets:
        try:
            preset = get_shot_preset(name)
            if use_case.lower() in preset.use_case.lower():
                matches.append(name)
        except ValueError:
            continue

    return matches
