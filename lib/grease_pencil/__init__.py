"""
Grease Pencil System - Node-centric 2D animation in Blender.

This module provides procedural GP generation following GSD's
Universal Stage Order with deterministic output.

Phase 21.0: Core GP Module (REQ-GP-01)
"""

from .types import (
    # Enums
    StrokeStyle,
    FillStyle,
    StrokeMode,
    DisplayMode,
    BlendMode,
    # Configs
    GPStrokeConfig,
    GPMaterialConfig,
    GPLayerConfig,
    GPMaskConfig,
    GPAnimationConfig,
)
from .stages import (
    stage_normalize_gp,
    stage_primary_gp,
    stage_secondary_gp,
    stage_detail_gp,
    stage_output_gp,
    run_gp_pipeline,
)
from .utils import (
    generate_seed_from_params,
    validate_gp_params,
)
from .objects import (
    GPObjectResult,
    create_gp_object_config,
    create_layer_config,
    create_stroke_config,
    create_material_config,
    create_mask_config,
    generate_line_stroke,
    generate_circle_stroke,
    generate_rect_stroke,
    generate_arc_stroke,
    create_simple_gp_object,
)
from .materials import (
    create_gp_material,
    apply_material_to_gp,
    create_material_node_group,
    create_outline_material,
    create_fill_material,
    create_gradient_material,
    load_material_preset,
)
from .modifiers import (
    apply_build_modifier,
    apply_noise_modifier,
    apply_smooth_modifier,
    apply_opacity_modifier,
    apply_color_modifier,
    apply_tint_modifier,
    apply_thickness_modifier,
    apply_array_modifier,
    apply_mirror_modifier,
    apply_effect_with_mask,
    remove_modifier,
    get_modifier_stack,
    load_modifier_preset,
    apply_modifier_preset,
)


__all__ = [
    # Enums
    'StrokeStyle',
    'FillStyle',
    'StrokeMode',
    'DisplayMode',
    'BlendMode',
    # Configs
    'GPStrokeConfig',
    'GPMaterialConfig',
    'GPLayerConfig',
    'GPMaskConfig',
    'GPAnimationConfig',
    # Stages
    'stage_normalize_gp',
    'stage_primary_gp',
    'stage_secondary_gp',
    'stage_detail_gp',
    'stage_output_gp',
    'run_gp_pipeline',
    # Utils
    'generate_seed_from_params',
    'validate_gp_params',
    # Objects
    'GPObjectResult',
    'create_gp_object_config',
    'create_layer_config',
    'create_stroke_config',
    'create_material_config',
    'create_mask_config',
    'generate_line_stroke',
    'generate_circle_stroke',
    'generate_rect_stroke',
    'generate_arc_stroke',
    'create_simple_gp_object',
]

__version__ = '0.1.0'
