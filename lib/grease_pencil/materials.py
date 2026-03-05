"""
GP Material system for Grease Pencil.

Provides material creation and configuration for GP strokes
and fills using MaterialGPencilStyle and shader node groups.

Phase 21.0: Core GP Module (REQ-GP-04)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from bpy.types import Material, Object

from .types import (
    GPMaterialConfig,
    StrokeStyle,
    FillStyle,
    StrokeMode,
)


# =============================================================================
# MATERIAL CREATION
# =============================================================================

def create_gp_material(
    name: str,
    config: Optional[GPMaterialConfig] = None,
    **kwargs: Any,
) -> "Material":
    """
    Create a Grease Pencil material.

    Args:
        name: Material name
        config: Optional GPMaterialConfig for configuration
        **kwargs: Override any config values

    Returns:
        The created material with GP settings

    Raises:
        ImportError: If bpy not available

    Example:
        >>> mat = create_gp_material(
        ...     "outline_material",
        ...     stroke_style=StrokeStyle.SOLID,
        ...     show_stroke=True,
        ...     show_fill=False,
        ... )
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "create_gp_material requires Blender (bpy module). "
            "Use create_gp_material_config() for Blender-independent configuration."
        ) from exc

    # Create material
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    # Get GP material settings
    gp_mat = mat.grease_pencil

    # Apply config if provided
    if config:
        gp_mat.show_stroke = config.show_stroke
        gp_mat.show_fill = config.show_fill

        # Set colors (convert tuple to list for Blender)
        gp_mat.color = list(config.color)
        gp_mat.fill_color = list(config.fill_color)

        # Set modes
        gp_mat.mode = config.stroke_mode.value
        gp_mat.stroke_style = config.stroke_style.value
        gp_mat.fill_style = config.fill_style.value

        # Set holdout
        gp_mat.use_stroke_holdout = config.use_stroke_holdout
        gp_mat.use_fill_holdout = config.use_fill_holdout

        # Set hardness and stroke width if available
        if hasattr(gp_mat, 'hardness'):
            gp_mat.hardness = config.hardness
        if hasattr(gp_mat, 'stroke_width'):
            gp_mat.stroke_width = config.stroke_width

    # Apply kwargs overrides
    for key, value in kwargs.items():
        if hasattr(gp_mat, key):
            setattr(gp_mat, key, value)

    return mat


def apply_material_to_gp(
    gp_obj: "Object",
    material: "Material",
    slot_index: Optional[int] = None,
) -> int:
    """
    Apply a material to a Grease Pencil object.

    Args:
        gp_obj: Grease Pencil object
        material: Material to apply
        slot_index: Optional slot index (appends if None)

    Returns:
        Material slot index

    Raises:
        ImportError: If bpy not available

    Example:
        >>> mat = create_gp_material("outline")
        >>> slot = apply_material_to_gp(gp_obj, mat)
    """
    try:
        import bpy
    except ImportError as exc:
        raise ImportError(
            "apply_material_to_gp requires Blender (bpy module)."
        ) from exc

    # Add material slot
    if slot_index is None:
        slot_index = len(gp_obj.material_slots)

    # Ensure material slot exists
    while len(gp_obj.material_slots) <= slot_index:
        gp_obj.material_slots.add()

    # Assign material
    gp_obj.material_slots[slot_index].material = material

    return slot_index


# =============================================================================
# MATERIAL NODE GROUPS (NPR Styles)
# =============================================================================

def create_material_node_group(
    name: str,
    node_group_type: str = "NPR_AnimeCel",
) -> Dict[str, Any]:
    """
    Create a shader node group for GP material.

    This returns a node group configuration for NPR-style rendering.
    The actual node group must be created in Blender's shader editor.

    Args:
        name: Node group name
        node_group_type: Type of NPR node group

    Returns:
        Node group configuration dict

    Node Group Types:
        - NPR_AnimeCel: Anime cel-shading style
        - NPR_Ghibli: Ghibli watercolor style
        - NPR_90sAnime: 90s anime aesthetic
        - NPR_Neon: Neon glow effect
        - NPR_Sketch: Pencil sketch style

    Example:
        >>> config = create_material_node_group("my_anime", "NPR_AnimeCel")
        >>> # Use config to create actual node group in Blender
    """
    node_group_configs = {
        "NPR_AnimeCel": {
            "description": "Anime cel-shading with sharp shadows",
            "inputs": {
                "BaseColor": (0.9, 0.9, 0.95, 1.0),
                "ShadowColor": (0.6, 0.65, 0.75, 1.0),
                "ShadowThreshold": 0.5,
                "OutlineWidth": 2.0,
            },
            "nodes": [
                {"type": "MIX_SHADER", "name": "ColorMix"},
                {"type": "MATH", "name": "Threshold", "operation": "LESS_THAN"},
            ],
        },
        "NPR_Ghibli": {
            "description": "Ghibli watercolor style with soft gradients",
            "inputs": {
                "BaseColor": (0.95, 0.9, 0.85, 1.0),
                "GradientColor": (0.8, 0.75, 0.7, 1.0),
                "Softness": 0.7,
                "TextureStrength": 0.3,
            },
            "nodes": [
                {"type": "MIX_SHADER", "name": "GradientMix"},
                {"type": "TEX_COORD", "name": "UV"},
            ],
        },
        "NPR_90sAnime": {
            "description": "90s anime aesthetic with limited palette",
            "inputs": {
                "SkinColor": (1.0, 0.85, 0.8, 1.0),
                "HairColor": (0.8, 0.6, 0.4, 1.0),
                "ShadowStrength": 0.8,
                "DitherAmount": 0.1,
            },
            "nodes": [
                {"type": "MIX_SHADER", "name": "ColorMix"},
                {"type": "MATH", "name": "Dither"},
            ],
        },
        "NPR_Neon": {
            "description": "Neon glow effect with bloom",
            "inputs": {
                "NeonColor": (1.0, 0.2, 0.8, 1.0),
                "GlowIntensity": 2.0,
                "BloomRadius": 10.0,
            },
            "nodes": [
                {"type": "EMISSION", "name": "Glow"},
                {"type": "MIX_SHADER", "name": "Blend"},
            ],
        },
        "NPR_Sketch": {
            "description": "Pencil sketch style with hatching",
            "inputs": {
                "PaperColor": (0.98, 0.96, 0.94, 1.0),
                "InkColor": (0.1, 0.1, 0.1, 1.0),
                "HatchingDensity": 0.5,
                "LineWeight": 1.0,
            },
            "nodes": [
                {"type": "MIX_SHADER", "name": "InkBlend"},
                {"type": "TEX_NOISE", "name": "Hatching"},
            ],
        },
    }

    config = node_group_configs.get(node_group_type, node_group_configs["NPR_AnimeCel"])
    config["name"] = name
    config["type"] = node_group_type

    return config


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_outline_material(
    name: str = "GP_Outline",
    color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    stroke_width: float = 3.0,
) -> "Material":
    """
    Create a simple outline-only GP material.

    Args:
        name: Material name
        color: Stroke color (RGBA)
        stroke_width: Stroke width in pixels

    Returns:
        Created material

    Example:
        >>> outline = create_outline_material("character_outline")
    """
    config = GPMaterialConfig(
        id=f"outline_{name}",
        name=name,
        stroke_style=StrokeStyle.SOLID,
        fill_style=FillStyle.SOLID,
        color=color,
        fill_color=(0.0, 0.0, 0.0, 0.0),  # Transparent fill
        show_stroke=True,
        show_fill=False,
        stroke_width=stroke_width,
        stroke_mode=StrokeMode_LINE,
    )
    return create_gp_material(name, config)


def create_fill_material(
    name: str = "GP_Fill",
    fill_color: Tuple[float, float, float, float] = (0.9, 0.9, 0.9, 1.0),
    show_stroke: bool = False,
) -> "Material":
    """
    Create a fill-only GP material.

    Args:
        name: Material name
        fill_color: Fill color (RGBA)
        show_stroke: Whether to show stroke

    Returns:
        Created material

    Example:
        >>> fill = create_fill_material("skin_fill", (1.0, 0.85, 0.8, 1.0))
    """
    config = GPMaterialConfig(
        id=f"fill_{name}",
        name=name,
        stroke_style=StrokeStyle.SOLID,
        fill_style=FillStyle.SOLID,
        color=(0.0, 0.0, 0.0, 1.0),
        fill_color=fill_color,
        show_stroke=show_stroke,
        show_fill=True,
        stroke_mode=StrokeMode_LINE,
    )
    return create_gp_material(name, config)


def create_gradient_material(
    name: str = "GP_Gradient",
    color_start: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    color_end: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0),
    gradient_type: str = "LINEAR",
    mix_factor: float = 0.5,
) -> "Material":
    """
    Create a gradient fill GP material.

    Args:
        name: Material name
        color_start: Start color (RGBA)
        color_end: End color (RGBA)
        gradient_type: Type of gradient (LINEAR, RADIAL, DIAGONAL)
        mix_factor: Mix factor between colors

    Returns:
        Created material

    Example:
        >>> gradient = create_gradient_material(
        ...     "sunset_gradient",
        ...     (1.0, 0.5, 0.0, 1.0),
        ...     (0.5, 0.0, 0.5, 1.0),
        ... )
    """
    config = GPMaterialConfig(
        id=f"gradient_{name}",
        name=name,
        stroke_style=StrokeStyle.SOLID,
        fill_style=FillStyle.GRADIENT,
        color=(0.0, 0.0, 0.0, 1.0),
        fill_color=color_start,
        mix_factor=mix_factor,
        show_stroke=True,
        show_fill=True,
        stroke_mode=StrokeMode_LINE,
    )
    return create_gp_material(name, config)


# =============================================================================
# PRESET LOADER
# =============================================================================

def load_material_preset(preset_name: str) -> GPMaterialConfig:
    """
    Load a material preset by name.

    Args:
        preset_name: Name of preset to load

    Returns:
        GPMaterialConfig from preset

    Raises:
        ValueError: If preset not found

    Example:
        >>> config = load_material_preset("anime_cel")
        >>> mat = create_gp_material("my_cel", config)
    """
    import yaml
    from pathlib import Path

    # Find presets file
    presets_path = Path(__file__).parent.parent.parent / "configs" / "grease_pencil" / "material_presets.yaml"

    if not presets_path.exists():
        raise ValueError(f"Material presets file not found: {presets_path}")

    with open(presets_path) as f:
        presets = yaml.safe_load(f)

    if preset_name not in presets:
        raise ValueError(f"Material preset '{preset_name}' not found")

    preset_data = presets[preset_name]

    # Convert preset to GPMaterialConfig
    return GPMaterialConfig(
        id=f"preset_{preset_name}",
        name=preset_data.get("name", preset_name),
        stroke_style=StrokeStyle(preset_data.get("stroke_style", "SOLID")),
        fill_style=FillStyle(preset_data.get("fill_style", "SOLID")),
        color=tuple(preset_data.get("color", (0.0, 0.0, 0.0, 1.0))),
        fill_color=tuple(preset_data.get("fill_color", (1.0, 1.0, 1.0, 1.0))),
        mix_factor=preset_data.get("mix_factor", 1.0),
        hardness=preset_data.get("hardness", 1.0),
        stroke_width=preset_data.get("stroke_width", 1.0),
        use_stroke_holdout=preset_data.get("use_stroke_holdout", True),
        use_fill_holdout=preset_data.get("use_fill_holdout", True),
        show_stroke=preset_data.get("show_stroke", True),
        show_fill=preset_data.get("show_fill", True),
        stroke_mode=StrokeMode(preset_data.get("stroke_mode", "LINE")),
    )
