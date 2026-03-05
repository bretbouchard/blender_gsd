"""
GP Modifier system for Grease Pencil.

IMPORTANT: GP has its own modifier stack, separate from Geometry Nodes.
This module uses GP_BUILD, GP_NOISE, GP_SMOOTH, etc.

DO NOT use Geometry Nodes for GP effects - they cannot process GP data.

Phase 21.0: Core GP Module (REQ-GP-05)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from bpy.types import GreasePencilModifier, Object as BlenderObject

from .types import GPMaskConfig


# =============================================================================
# MODIFIER TYPE ENUM (for type hints)
# =============================================================================

GP_MODIFIER_BUILD = "GP_BUILD"
GP_MODIFIER_NOISE = "GP_NOISE"
GP_MODIFIER_SMOOTH = "GP_SMOOTH"
GP_MODIFIER_OPACITY = "GP_OPACITY"
GP_MODIFIER_COLOR = "GP_COLOR"
GP_MODIFIER_TINT = "GP_TINT"
GP_MODIFIER_THICKNESS = "GP_THICKNESS"
GP_MODIFIER_ARRAY = "GP_ARRAY"
GP_MODIFIER_MIRROR = "GP_MIRROR"
GP_MODIFIER_SIMPLIFY = "GP_SIMPLIFY"
GP_MODIFIER_OFFSET = "GP_OFFSET"
GP_MODIFIER_ARMATURE = "GP_ARMATURE"
GP_MODIFIER_HOOK = "GP_HOOK"
GP_MODIFIER_LATTICE = "GP_LATTICE"
GP_MODIFIER_LENGTH = "GP_LENGTH"
GP_MODIFIER_TIME = "GP_TIME"
GP_MODIFIER_ENVELOPE = "GP_ENVELOPE"
GP_MODIFIER_OUTLINE = "GP_OUTLINE"
GP_MODIFIER_SHRINKWRAP = "GP_SHRINKWRAP"

GPModifierType = Union[
    "GP_BUILD",
    "GP_NOISE",
    "GP_SMOOTH",
    "GP_OPACITY",
    "GP_COLOR",
    "GP_TINT",
    "GP_THICKNESS",
    "GP_ARRAY",
    "GP_MIRROR",
    "GP_SIMPLIFY",
    "GP_OFFSET",
    "GP_ARMATURE",
    "GP_HOOK",
    "GP_LATTICE",
    "GP_LENGTH",
    "GP_TIME",
    "GP_ENVELOPE",
    "GP_OUTLINE",
    "GP_SHRINKWRAP",
]


# =============================================================================
# MASK APPLICATION
# =============================================================================

def apply_effect_with_mask(
    modifier: "GreasePencilModifier",
    mask_config: Optional[GPMaskConfig],
) -> None:
    """
    Apply mask configuration to a GP modifier.

    All GP effects support masking per SLC requirement.

    Args:
        modifier: The GP modifier to configure
        mask_config: Mask configuration (None = no mask)

    Example:
        >>> mask = GPMaskConfig(enabled=True, mask_layer="Layer_001")
        >>> apply_effect_with_mask(modifier, mask)
    """
    if mask_config is None or not mask_config.enabled:
        return

    # Apply mask layer
    if mask_config.mask_layer and hasattr(modifier, "layer"):
        modifier.layer = mask_config.mask_layer

    # Apply invert
    if hasattr(modifier, "invert_layer"):
        modifier.invert_layer = mask_config.invert

    # Apply feather (if supported by modifier)
    if hasattr(modifier, "feather"):
        modifier.feather = mask_config.feather


    # Apply influence (if supported)
    if hasattr(modifier, "influence"):
        modifier.influence = mask_config.influence


# =============================================================================
# BUILD MODIFIER
# =============================================================================

def apply_build_modifier(
    gp_obj: "BlenderObject",
    name: str = "Build",
    mode: str = "SEQUENTIAL",
    transition: str = "GROW",
    frame_start: int = 1,
    frame_duration: int = 50,
    seed: Optional[int] = None,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Build modifier for stroke reveal animation.

    Uses GP_BUILD modifier (NOT Geometry Nodes).

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        mode: Build mode (SEQUENTIAL, CONCURRENT, ADDITIVE)
        transition: Transition type (GROW, SHRINK, FADE)
        frame_start: Start frame
        frame_duration: Duration in frames
        seed: Random seed for determinism
        mask_config: Optional mask configuration
        **kwargs: Additional modifier properties

    Returns:
        The created modifier

    Example:
        >>> mod = apply_build_modifier(
        ...     gp_obj,
        ...     mode="SEQUENTIAL",
        ...     frame_start=1,
        ...     frame_duration=24,
        ... )
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_build_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_BUILD")
    modifier.mode = mode
    modifier.transition = transition
    modifier.start_delay = frame_start - 1
    modifier.length = frame_duration

    if seed is not None and hasattr(modifier, "seed"):
        modifier.seed = seed

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    # Apply mask if provided
    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# NOISE MODIFIER
# =============================================================================

def apply_noise_modifier(
    gp_obj: "BlenderObject",
    name: str = "Noise",
    factor: float = 0.5,
    scale: float = 1.0,
    seed: Optional[int] = None,
    affect_position: bool = True,
    affect_strength: bool = False,
    affect_thickness: bool = False,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Noise modifier for procedural jitter.

    Uses GP_NOISE modifier (NOT Geometry Nodes).

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        factor: Noise intensity
        scale: Noise scale
        seed: Random seed
        affect_position: Apply noise to stroke points
        affect_strength: Apply noise to stroke strength
        affect_thickness: Apply noise to stroke thickness
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_noise_modifier(gp_obj, factor=0.3, seed=42)
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_noise_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_NOISE")
    modifier.factor = factor
    modifier.noise_scale = scale

    if seed is not None and hasattr(modifier, "seed"):
        modifier.seed = seed

    # Apply affect settings
    if hasattr(modifier, "use_noise_position"):
        modifier.use_noise_position = affect_position
    if hasattr(modifier, "use_noise_strength"):
        modifier.use_noise_strength = affect_strength
    if hasattr(modifier, "use_noise_thickness"):
        modifier.use_noise_thickness = affect_thickness

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# SMOOTH MODIFIER
# =============================================================================

def apply_smooth_modifier(
    gp_obj: "BlenderObject",
    name: str = "Smooth",
    factor: float = 0.5,
    steps: int = 1,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Smooth modifier for stroke smoothing.

    Uses GP_SMOOTH modifier (NOT Geometry Nodes).

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        factor: Smooth intensity
        steps: Number of smooth iterations
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_smooth_modifier(gp_obj, factor=0.8, steps=2)
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_smooth_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_SMOOTH")
    modifier.factor = factor

    if hasattr(modifier, "step"):
        modifier.step = steps

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# OPACITY MODIFIER
# =============================================================================

def apply_opacity_modifier(
    gp_obj: "BlenderObject",
    name: str = "Opacity",
    factor: float = 1.0,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Opacity modifier for transparency effects.

    Uses GP_OPACITY modifier (NOT Geometry Nodes).

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        factor: Opacity factor (0.0 = fully opaque)
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_opacity_modifier(gp_obj, factor=0.5)  # 50% opacity
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_opacity_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_OPACITY")
    modifier.factor = factor

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# COLOR MODIFIER
# =============================================================================

def apply_color_modifier(
    gp_obj: "BlenderObject",
    name: str = "Color",
    hue: float = 0.0,
    saturation: float = 1.0,
    value: float = 1.0,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Color modifier for HSV color adjustments.

    Uses GP_COLOR modifier (NOT Geometry Nodes).

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        hue: Hue shift (-0.5 to 0.0)
        saturation: Saturation multiplier
        value: Value/brightness multiplier
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_color_modifier(gp_obj, hue=0.1, saturation=1.2)
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_color_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_COLOR")

    if hasattr(modifier, "hue"):
        modifier.hue = hue
    if hasattr(modifier, "saturation"):
        modifier.saturation = saturation
    if hasattr(modifier, "value"):
        modifier.value = value

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# TINT MODIFIER
# =============================================================================

def apply_tint_modifier(
    gp_obj: "BlenderObject",
    name: str = "Tint",
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    factor: float = 1.0,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Tint modifier for color tinting.

    Uses GP_TINT modifier.

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        color: Tint color (RGBA)
        factor: Tint intensity
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_tint_modifier(gp_obj, color=(1.0, 0.5, 0.0, 1.0))
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_tint_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_TINT")

    if hasattr(modifier, "tint_color"):
        modifier.tint_color = color
    if hasattr(modifier, "tint_factor"):
        modifier.tint_factor = factor

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# THICKNESS MODIFIER
# =============================================================================

def apply_thickness_modifier(
    gp_obj: "BlenderObject",
    name: str = "Thickness",
    factor: float = 1.0,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Thickness modifier for stroke width adjustment.

    Uses GP_THICKNESS modifier.

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        factor: Thickness multiplier
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_thickness_modifier(gp_obj, factor=2.0)  # Double thickness
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_thickness_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_THICKNESS")
    modifier.factor = factor

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# ARRAY MODIFIER
# =============================================================================

def apply_array_modifier(
    gp_obj: "BlenderObject",
    name: str = "Array",
    count: int = 2,
    offset: float = 0.1,
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Array modifier for stroke duplication.

    Uses GP_ARRAY modifier.

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        count: Number of copies
        offset: Offset between copies
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_array_modifier(gp_obj, count=5, offset=0.5)
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_array_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_ARRAY")

    if hasattr(modifier, "count"):
        modifier.count = count
    if hasattr(modifier, "offset"):
        modifier.offset = offset

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# MIRROR MODIFIER
# =============================================================================

def apply_mirror_modifier(
    gp_obj: "BlenderObject",
    name: str = "Mirror",
    mirror_axis: str = "X",
    mask_config: Optional[GPMaskConfig] = None,
    **kwargs: Any,
) -> "GreasePencilModifier":
    """
    Apply GP Mirror modifier for stroke mirroring.

    Uses GP_MIRROR modifier.

    Args:
        gp_obj: GP object to modify
        name: Modifier name
        mirror_axis: Axis to mirror (X, Y, Z)
        mask_config: Optional mask configuration

    Returns:
        The created modifier

    Example:
        >>> mod = apply_mirror_modifier(gp_obj, mirror_axis="X")
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_mirror_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.new(name, type="GP_MIRROR")

    # Map axis string to enum value
    axis_map = {
        "X": "X",
        "Y": "Y",
        "Z": "Z",
    }
    if hasattr(modifier, "mirror_axis"):
        modifier.mirror_axis = axis_map.get(mirror_axis, "X")

    # Apply kwargs
    for key, value in kwargs.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    apply_effect_with_mask(modifier, mask_config)

    return modifier


# =============================================================================
# MODIFIER MANAGEMENT
# =============================================================================

def remove_modifier(
    gp_obj: "BlenderObject",
    modifier_name: str,
) -> None:
    """
    Remove a modifier from a GP object.

    Args:
        gp_obj: GP object
        modifier_name: Name of modifier to remove

    Example:
        >>> remove_modifier(gp_obj, "Noise")
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "remove_modifier requires Blender (bpy module)."
        ) from exc

    modifier = gp_obj.grease_pencil_modifiers.get(modifier_name)
    if modifier:
        gp_obj.grease_pencil_modifiers.remove(modifier)


def get_modifier_stack(
    gp_obj: "BlenderObject",
) -> List[str]:
    """
    Get list of modifiers applied to a GP object.

    Args:
        gp_obj: GP object

    Returns:
        List of modifier names

    Example:
        >>> mods = get_modifier_stack(gp_obj)
        >>> print(mods)  # ['Build', 'Smooth', 'Opacity']
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "get_modifier_stack requires Blender (bpy module)."
        ) from exc

    return [mod.name for mod in gp_obj.grease_pencil_modifiers]


# =============================================================================
# PRESET LOADER
# =============================================================================

def load_modifier_preset(
    preset_name: str,
) -> Dict[str, Any]:
    """
    Load a modifier preset configuration.

    Args:
        preset_name: Name of preset to load

    Returns:
        Dict with modifier configurations

    Raises:
        ValueError: If preset not found

    Example:
        >>> config = load_modifier_preset("build_reveal")
        >>> # Apply to object using apply_build_modifier
    """
    import yaml
    from pathlib import Path

    # Find presets file
    presets_path = Path(__file__).parent.parent.parent / "configs" / "grease_pencil" / "modifier_presets.yaml"

    if not presets_path.exists():
        raise ValueError(f"Modifier presets file not found: {presets_path}")

    with open(presets_path) as f:
        presets = yaml.safe_load(f)

    if preset_name not in presets:
        raise ValueError(f"Modifier preset '{preset_name}' not found")

    return presets[preset_name]


def apply_modifier_preset(
    gp_obj: "BlenderObject",
    preset_name: str,
    modifier_name: Optional[str] = None,
) -> "GreasePencilModifier":
    """
    Apply a modifier preset to a GP object.

    Args:
        gp_obj: GP object
        preset_name: Name of preset
        modifier_name: Optional custom name for modifier

    Returns:
        The created modifier

    Example:
        >>> mod = apply_modifier_preset(gp_obj, "build_reveal")
    """
    config = load_modifier_preset(preset_name)

    modifier_type = config.get("type", "GP_BUILD")
    name = modifier_name or config.get("name", preset_name)

    # Map type to function
    type_to_func = {
        "GP_BUILD": apply_build_modifier,
        "GP_NOISE": apply_noise_modifier,
        "GP_SMOOTH": apply_smooth_modifier,
        "GP_OPACITY": apply_opacity_modifier,
        "GP_COLOR": apply_color_modifier,
        "GP_TINT": apply_tint_modifier,
        "GP_THICKNESS": apply_thickness_modifier,
        "GP_ARRAY": apply_array_modifier,
        "GP_MIRROR": apply_mirror_modifier,
    }

    func = type_to_func.get(modifier_type)
    if not func:
        raise ValueError(f"Unknown modifier type: {modifier_type}")

    # Extract modifier-specific kwargs
    kwargs = {k: v for k, v in config.items() if k not in ["type", "name"]}

    return func(gp_obj, name=name, **kwargs)
