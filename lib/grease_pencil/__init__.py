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
