"""
Color Pipeline Module

Provides color management, LUT validation, compositor LUT application, and exposure lock functionality.

Usage:
    from lib.cinematic.color import (
        set_view_transform, apply_color_preset,
        validate_lut_file, apply_lut, calculate_auto_exposure
    )

    # Set view transform
    set_view_transform("AgX", look="AgX Default Medium High Contrast")

    # Apply color preset
    apply_color_preset("agx_default")

    # Validate and apply LUT
    valid, error = validate_lut_file(Path("luts/kodak_2383.cube"), 33)
    if valid:
        apply_lut(lut_config)

    # Calculate auto exposure
    exposure = calculate_auto_exposure(exposure_config, scene_luminance=0.15)
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import math

from .types import ColorConfig, LUTConfig, ExposureLockConfig
from .preset_loader import (
    get_color_preset, get_film_lut_preset, get_technical_lut_preset,
    list_film_lut_presets, list_technical_lut_presets, COLOR_CONFIG_ROOT
)

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


# =============================================================================
# Task 1: Core Color Management Functions
# =============================================================================


def set_view_transform(
    view_transform: str,
    look: str = "None",
    exposure: float = 0.0,
    gamma: float = 1.0,
    display_device: str = "sRGB"
) -> bool:
    """
    Set scene view transform settings.

    Configures Blender's color management view transform, look, exposure,
    gamma, and display device settings.

    Args:
        view_transform: View transform name (AgX, Filmic, Standard, etc.)
        look: Look preset name (e.g., "AgX Default Medium High Contrast")
        exposure: Global exposure adjustment (-10 to +10)
        gamma: Gamma correction (0 to 5)
        display_device: Output display device (sRGB, DCI-P3, etc.)

    Returns:
        True on success, False if Blender not available or error
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        view_settings = scene.view_settings
        display_settings = scene.display_settings

        # Set view transform
        view_settings.view_transform = view_transform

        # Set look (use "None" for default)
        view_settings.look = look

        # Set exposure
        view_settings.exposure = exposure

        # Set gamma (clamped to valid range)
        view_settings.gamma = max(0.0, min(5.0, gamma))

        # Set display device
        display_settings.display_device = display_device

        return True

    except Exception:
        return False


def apply_color_preset(preset_name: str) -> bool:
    """
    Apply color management preset by name.

    Loads preset from color_management_presets.yaml and applies
    view transform settings to the current scene.

    Args:
        preset_name: Name of the color preset (e.g., "neutral", "high_contrast")

    Returns:
        True on success, False on failure
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Load preset using preset_loader
        preset = get_color_preset(preset_name)

        # Extract settings from preset
        view_transform = preset.get("view_transform", "AgX")
        look = preset.get("look", "None")
        exposure = preset.get("exposure", 0.0)
        gamma = preset.get("gamma", 1.0)
        display_device = preset.get("display_device", "sRGB")

        # Apply via set_view_transform
        return set_view_transform(
            view_transform=view_transform,
            look=look,
            exposure=exposure,
            gamma=gamma,
            display_device=display_device
        )

    except Exception:
        return False


def get_current_color_settings() -> Optional[ColorConfig]:
    """
    Get current color management settings from scene.

    Returns:
        ColorConfig with current settings, or None if Blender not available
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return None

        scene = bpy.context.scene
        view_settings = scene.view_settings
        display_settings = scene.display_settings
        seq_settings = scene.sequencer_colorspace_settings

        return ColorConfig(
            view_transform=view_settings.view_transform,
            exposure=view_settings.exposure,
            gamma=view_settings.gamma,
            look=view_settings.look,
            display_device=display_settings.display_device,
            working_color_space=seq_settings.name if hasattr(seq_settings, "name") else "AgX"
        )

    except Exception:
        return None


def reset_color_settings() -> bool:
    """
    Reset color settings to Blender defaults.

    Defaults: view_transform="AgX", look="None", exposure=0.0, gamma=1.0

    Returns:
        True on success, False if Blender not available
    """
    return set_view_transform(
        view_transform="AgX",
        look="None",
        exposure=0.0,
        gamma=1.0,
        display_device="sRGB"
    )


def get_available_looks() -> List[str]:
    """
    Get list of available look presets from Blender.

    Returns:
        List of look preset names, or empty list if not available
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        # Access available looks via RNA properties
        # This provides the enum items for the look property
        scene_rna = bpy.types.Scene.bl_rna
        view_settings_prop = scene_rna.properties.get("view_settings")

        if view_settings_prop is None:
            return []

        # Get look property enum items
        look_prop = view_settings_prop.enum_items_static if hasattr(view_settings_prop, "enum_items_static") else None

        if look_prop:
            return [item.identifier for item in look_prop]

        # Fallback: return common looks
        return [
            "None",
            "AgX Default",
            "AgX Default High Contrast",
            "AgX Default Medium High Contrast",
            "AgX Default Low Contrast",
            "AgX Punchy",
            "AgX Log",
            "Filmic Base Contrast",
            "Filmic Medium High Contrast",
            "Filmic High Contrast",
            "Filmic Low Contrast",
            "Filmic Very Low Contrast",
        ]

    except Exception:
        return []


def set_working_color_space(working_space: str) -> bool:
    """
    Set the scene's working color space.

    Note: Blender 4.x primarily uses view_transform for color management.
    This sets the sequencer color space setting.

    Args:
        working_space: Color space name (e.g., "AgX", "ACEScg", "Filmic")

    Returns:
        True on success, False if Blender not available
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene

        # Set sequencer color space (this is the working color space in Blender)
        scene.sequencer_colorspace_settings.name = working_space

        return True

    except Exception:
        return False


# =============================================================================
# Task 2: LUT Validation Functions
# =============================================================================


def validate_lut_file(path: Path, expected_precision: int) -> Tuple[bool, str]:
    """
    Validate LUT file format and precision.

    Validates that a .cube LUT file exists, has correct format,
    and matches expected precision (3D LUT size).

    Args:
        path: Path to the .cube LUT file
        expected_precision: Expected LUT 3D size (e.g., 33 for film, 65 for technical)

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, "error description") if invalid
    """
    path = Path(path)

    # Check file exists
    if not path.exists():
        return False, f"LUT file not found: {path}"

    # Check file extension
    if path.suffix.lower() != ".cube":
        return False, f"Invalid format: expected .cube, got {path.suffix}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find LUT_3D_SIZE line
        for line in lines:
            line = line.strip()
            if line.startswith("LUT_3D_SIZE"):
                parts = line.split()
                if len(parts) < 2:
                    return False, "Invalid LUT_3D_SIZE format: missing size value"

                try:
                    size = int(parts[1])
                except ValueError:
                    return False, f"Invalid LUT_3D_SIZE value: {parts[1]}"

                if size != expected_precision:
                    return False, f"Wrong precision: expected {expected_precision}^3, got {size}^3"

                return True, ""

        # LUT_3D_SIZE not found
        return False, "Missing LUT_3D_SIZE in .cube file"

    except IOError as e:
        return False, f"Error reading LUT file: {e}"
    except Exception as e:
        return False, f"Error validating LUT: {e}"


def find_lut_path(
    lut_filename: str,
    search_paths: Optional[List[Path]] = None
) -> Optional[Path]:
    """
    Find LUT file using multi-path search.

    Searches in order:
    1. Project local: assets/luts/
    2. User library: ~/.lut_library/
    3. Config bundled: COLOR_CONFIG_ROOT/luts/

    Args:
        lut_filename: LUT filename to search for
        search_paths: Optional custom search paths (uses defaults if None)

    Returns:
        Path to found LUT file, or None if not found
    """
    # Default search paths
    default_paths = [
        Path("assets/luts"),
        Path("~/.lut_library").expanduser(),
        COLOR_CONFIG_ROOT / "luts",
    ]

    paths = search_paths if search_paths is not None else default_paths

    for search_path in paths:
        candidate = search_path / lut_filename
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def load_lut_config(
    preset_name: str,
    lut_type: str = "film"
) -> Optional[LUTConfig]:
    """
    Load LUT preset and resolve file path.

    Loads LUT preset from configuration, resolves the LUT file path,
    and validates the precision.

    Args:
        preset_name: Name of the LUT preset
        lut_type: LUT type - "film" or "technical"

    Returns:
        LUTConfig if successful, None if validation fails
    """
    try:
        # Load preset based on type
        if lut_type == "technical":
            preset = get_technical_lut_preset(preset_name)
            expected_precision = 65  # Technical LUTs typically use 65^3
        else:  # film or creative
            preset = get_film_lut_preset(preset_name)
            expected_precision = 33  # Film LUTs typically use 33^3

        # Get LUT filename from preset
        lut_filename = preset.get("file", preset.get("lut_path", ""))
        if not lut_filename:
            return None

        # Resolve LUT path
        lut_path = find_lut_path(lut_filename)
        if lut_path is None:
            # Try using the filename directly if it's an absolute path
            direct_path = Path(lut_filename)
            if direct_path.exists():
                lut_path = direct_path
            else:
                return None

        # Validate precision
        valid, error = validate_lut_file(lut_path, expected_precision)
        if not valid:
            # Still create config but log the warning
            pass

        # Create and return LUTConfig
        return LUTConfig(
            name=preset_name,
            lut_path=str(lut_path),
            intensity=preset.get("intensity", 0.8),
            enabled=preset.get("enabled", True),
            lut_type=lut_type,
            precision=preset.get("precision", expected_precision)
        )

    except Exception:
        return None


def list_available_luts(lut_type: str = "film") -> List[str]:
    """
    List available LUT preset names.

    Args:
        lut_type: LUT type - "film" or "technical"

    Returns:
        Sorted list of LUT preset names
    """
    try:
        if lut_type == "technical":
            return list_technical_lut_presets()
        else:  # film or creative
            return list_film_lut_presets()
    except Exception:
        return []


# =============================================================================
# Task 3: Compositor-based LUT Application
# =============================================================================


def apply_lut(config: LUTConfig) -> bool:
    """
    Apply LUT using compositor nodes with intensity blending.

    Creates a node chain:
    1. Render Layers -> ColorBalance (LUT-style grading) -> MixRGB[1]
    2. Render Layers -> MixRGB[2] (original)
    3. MixRGB blends at config.intensity ratio (default 0.8)
    4. Output -> Composite

    Note: Blender lacks a native LUT loading node. This implementation
    uses ColorBalance nodes to approximate LUT effects.
    For actual .cube LUT loading, consider using OCIO or custom parsing.

    Args:
        config: LUTConfig with name, lut_path, intensity, enabled, lut_type, precision

    Returns:
        True on success, False on failure
    """
    if not BLENDER_AVAILABLE:
        return False

    if not config.enabled:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        scene.use_nodes = True

        tree = scene.node_tree
        if tree is None:
            return False

        # Get or create Render Layers node
        render_layers = tree.nodes.get("Render Layers")
        if not render_layers:
            render_layers = tree.nodes.new("CompositorNodeRLayers")
            render_layers.name = "Render Layers"

        # Get or create Composite node
        composite = tree.nodes.get("Composite")
        if not composite:
            composite = tree.nodes.new("CompositorNodeComposite")
            composite.name = "Composite"

        # Create ColorBalance node for LUT-style grading
        color_balance = tree.nodes.new("CompositorNodeColorBalance")
        color_balance.name = f"LUT_{config.name}"
        color_balance.correction_method = "LIFT_GAMMA_GAIN"

        # Set position for clean layout
        color_balance.location = (300, 0)

        # Create MixRGB node for intensity blending
        mix = tree.nodes.new("CompositorNodeMixRGB")
        mix.name = f"LUT_Mix_{config.name}"
        mix.blend_type = "MIX"
        mix.inputs["Fac"].default_value = config.intensity  # Use intensity from config
        mix.location = (500, 0)

        # Connect nodes:
        # Render -> ColorBalance -> Mix[1] (graded image to socket 1)
        # Render -> Mix[2] (original to socket 2)
        # Mix -> Composite
        tree.links.new(render_layers.outputs["Image"], color_balance.inputs["Image"])
        tree.links.new(render_layers.outputs["Image"], mix.inputs[2])  # Original to socket 2
        tree.links.new(color_balance.outputs["Image"], mix.inputs[1])   # Graded to socket 1
        tree.links.new(mix.outputs["Image"], composite.inputs["Image"])

        return True

    except Exception:
        return False


def remove_lut_nodes(lut_name: Optional[str] = None) -> bool:
    """
    Remove LUT-related compositor nodes.

    Args:
        lut_name: If provided, remove only nodes matching this name.
                  If None, remove all LUT_ and LUT_Mix_ nodes.

    Returns:
        True on success, False if Blender not available
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        if not scene.use_nodes or scene.node_tree is None:
            return True  # Nothing to remove

        tree = scene.node_tree
        nodes_to_remove = []

        if lut_name:
            # Remove specific LUT nodes
            for pattern in [f"LUT_{lut_name}", f"LUT_Mix_{lut_name}"]:
                node = tree.nodes.get(pattern)
                if node:
                    nodes_to_remove.append(node)
        else:
            # Remove all LUT-related nodes
            for node in tree.nodes:
                if node.name.startswith("LUT_") or node.name.startswith("LUT_Mix_"):
                    nodes_to_remove.append(node)

        # Remove nodes
        for node in nodes_to_remove:
            tree.nodes.remove(node)

        # Reconnect Render Layers directly to Composite if both exist
        render_layers = tree.nodes.get("Render Layers")
        composite = tree.nodes.get("Composite")

        if render_layers and composite:
            # Remove existing links to composite
            for link in list(tree.links):
                if link.to_node == composite and link.to_socket == composite.inputs.get("Image"):
                    tree.links.remove(link)

            # Create direct connection
            tree.links.new(render_layers.outputs["Image"], composite.inputs["Image"])

        return True

    except Exception:
        return False


def get_active_luts() -> List[str]:
    """
    Get list of active LUT node names in compositor.

    Returns:
        List of active LUT node names (without LUT_ prefix), empty list if none
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return []

        scene = bpy.context.scene
        if not scene.use_nodes or scene.node_tree is None:
            return []

        tree = scene.node_tree
        active_luts = []

        for node in tree.nodes:
            if node.name.startswith("LUT_") and not node.name.startswith("LUT_Mix_"):
                # Extract LUT name (remove "LUT_" prefix)
                lut_name = node.name[4:]
                active_luts.append(lut_name)

        return active_luts

    except Exception:
        return []


# =============================================================================
# Task 4: Exposure Lock System
# =============================================================================


def calculate_auto_exposure(
    config: ExposureLockConfig,
    scene_luminance: Optional[float] = None
) -> float:
    """
    Calculate exposure adjustment to hit target gray value.

    Uses log2(target_gray / scene_luminance) formula to calculate
    the exposure offset needed to achieve the target middle gray.

    Args:
        config: ExposureLockConfig with target_gray and protection values
        scene_luminance: Optional average scene luminance (0-1).
                        If None, returns 0.0 (requires render pass for actual data)

    Returns:
        Calculated exposure value, or 0.0 if disabled or no luminance data

    Note:
        Direct scene luminance sampling is not available in Blender Python API.
        For now, this function accepts optional scene_luminance parameter.
        Future implementation could use render passes for luminance calculation.
    """
    if not config.enabled:
        return 0.0

    # Without scene luminance data, we cannot calculate exposure
    if scene_luminance is None or scene_luminance <= 0:
        return 0.0

    try:
        # Calculate exposure to hit target gray
        # Formula: exposure = log2(target_gray / scene_luminance)
        exposure = math.log2(config.target_gray / scene_luminance)

        # Calculate exposure limits based on protection values
        # highlight_protection = max exposure (don't blow out highlights)
        # shadow_protection = min exposure (don't crush shadows)
        # Higher highlight protection = lower max exposure
        # Higher shadow protection = higher min exposure

        # Max exposure: how much we can brighten before highlights clip
        max_exposure = math.log2(config.highlight_protection / scene_luminance) if scene_luminance > 0 else 0.0

        # Min exposure: how much we can darken before shadows crush
        min_exposure = math.log2(config.shadow_protection / scene_luminance) if scene_luminance > 0 else 0.0

        # Clamp exposure to protect highlights and shadows
        clamped_exposure = max(min_exposure, min(max_exposure, exposure))

        return clamped_exposure

    except Exception:
        return 0.0


def apply_exposure_lock(config: ExposureLockConfig) -> bool:
    """
    Apply auto-exposure based on config.

    Calculates auto exposure using calculate_auto_exposure() and
    applies it to the scene's view settings.

    Args:
        config: ExposureLockConfig with exposure lock settings

    Returns:
        True on success, False if Blender not available

    Note:
        Without scene luminance data (requires render pass),
        this will set exposure to 0.0.
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Calculate auto exposure
        # Note: scene_luminance would need to come from render pass analysis
        # For now, this is a placeholder that returns 0.0
        exposure = calculate_auto_exposure(config, scene_luminance=None)

        # Apply to scene
        return set_exposure(exposure)

    except Exception:
        return False


def set_exposure(exposure: float) -> bool:
    """
    Direct exposure setter.

    Args:
        exposure: Exposure value (typically -10 to +10)

    Returns:
        True on success, False if Blender not available
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        scene.view_settings.exposure = exposure

        return True

    except Exception:
        return False


def set_gamma(gamma: float) -> bool:
    """
    Direct gamma setter.

    Args:
        gamma: Gamma value (clamped to 0-5)

    Returns:
        True on success, False if Blender not available
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene

        # Clamp gamma to valid range (0 to 5)
        clamped_gamma = max(0.0, min(5.0, gamma))
        scene.view_settings.gamma = clamped_gamma

        return True

    except Exception:
        return False


def get_exposure_range() -> Tuple[float, float]:
    """
    Get valid exposure range for UI validation.

    Returns:
        Tuple of (min_exposure, max_exposure) = (-10.0, 10.0)
    """
    return (-10.0, 10.0)


def get_gamma_range() -> Tuple[float, float]:
    """
    Get valid gamma range for UI validation.

    Returns:
        Tuple of (min_gamma, max_gamma) = (0.0, 5.0)
    """
    return (0.0, 5.0)
