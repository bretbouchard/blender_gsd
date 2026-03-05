"""
Grease Pencil Stage Pipeline Functions

Universal Stage Order for GP generation:
    Normalize -> Primary -> Secondary -> Detail -> OutputPrep

Phase 21.0: Core GP Module (REQ-GP-02)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List

from .types import (
    GPStrokeConfig,
    GPMaterialConfig,
    GPLayerConfig,
    GPMaskConfig,
    GPAnimationConfig,
    DisplayMode,
    StrokeStyle,
    FillStyle,
    StrokeMode,
    BlendMode,
)
from .utils import generate_seed_from_params, validate_gp_params





# =============================================================================
# STAGE 1: NORMALIZE
# =============================================================================

def stage_normalize_gp(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and validate GP parameters.

    Produces canonical parameter dict with:
    - All required fields present
    - Default values applied
    - Seed generated if not provided
    - Types validated

    Args:
        params: Raw input parameters

    Returns:
        Normalized parameter dictionary

    Example:
        >>> normalized = stage_normalize_gp({'stroke_count': 10})
        >>> assert 'seed' in normalized
        >>> assert normalized['stroke_count'] == 10
    """
    validated = validate_gp_params(params)

    # Generate deterministic seed
    if 'seed' not in validated or validated['seed'] is None:
        validated['seed'] = generate_seed_from_params(validated)

    return {
        'params': validated,
        'stage': 'normalize',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    }


# =============================================================================
# STAGE 2: PRIMARY
# =============================================================================

def stage_primary_gp(normalized_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create GP object with layers from normalized parameters.

    Produces GP object configuration with:
    - Object structure
    - Layer configurations
    - Material slot allocation

    Args:
        normalized_params: Normalized parameters from stage_normalize_gp

    Returns:
        Primary GP configuration dict

    Example:
        >>> params = stage_normalize_gp({'stroke_count': 10})
        >>> primary = stage_primary_gp(params)
        >>> assert 'layers' in primary
        >>> assert len(primary['layers']) > 0
    """
    params = normalized_params['params']
    stroke_count = params.get('stroke_count', 10)
    layer_count = params.get('layer_count', 3)
    layer_names = params.get('layer_names', [])

    # Build layer configurations
    layers = []
    for i in range(layer_count):
        layer_name = layer_names[i] if i < len(layer_names) else f"Layer_{i:03d}"
        layer_config = GPLayerConfig(
            id=f"layer_{i:03d}",
            name=layer_name,
            opacity=1.0,
            blend_mode=BlendMode.REGULAR,
            use_lights=False,
            use_mask_layer=False,
            stroke_configs=[],
        )
        layers.append(layer_config)

    return {
        'stage': 'primary',
        'layer_count': layer_count,
        'layers': [layer.to_dict() for layer in layers],
        'default_stroke_width': params.get('stroke_width', 5.0),
        'default_material_index': 0,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    }


# =============================================================================
# STAGE 3: SECONDARY
# =============================================================================

def stage_secondary_gp(primary_result: Dict[str, Any], normalized_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply secondary modifications to GP data.

    Processes:
    - Stroke generation
    - Material assignments
    - Layer relationships

    Args:
        primary_result: Result from stage_primary_gp
        normalized_params: Original normalized parameters

    Returns:
        Secondary GP configuration dict with stroke and material data
    """
    params = normalized_params['params']
    stroke_count = params.get('stroke_count', 10)
    seed = normalized_params['seed']

    # Generate stroke configurations
    strokes = []
    materials = []

    import random
    random.seed(seed)

    for i in range(stroke_count):
        # Generate random stroke points
        point_count = random.randint(3, 10)
        points = []
        for j in range(point_count):
            x = random.uniform(-5, 5)
            y = random.uniform(-5, 5)
            z = random.uniform(0, 2)
            pressure = random.uniform(0.5, 1.0)
            strength = random.uniform(0.7, 1.0)
            points.append((x, y, z, pressure, strength))

        stroke_config = GPStrokeConfig(
            id=f"stroke_{i:04d}",
            points=points,
            stroke_width=params.get('stroke_width', 5.0),
            hardness=random.uniform(0.8, 1.0),
            seed=seed + i,
        )
        strokes.append(stroke_config)

        # Create material for each stroke
        material_config = GPMaterialConfig(
            id=f"material_{i:04d}",
            name=f"Material {i}",
            stroke_style=StrokeStyle.SOLID,
            fill_style=FillStyle.SOLID,
            color=(random.random(), random.random(), random.random(), 1.0),
            fill_color=(random.random(), random.random(), random.random(), 1.0),
        )
        materials.append(material_config)

    return {
        'stage': 'secondary',
        'strokes': [s.to_dict() for s in strokes],
        'materials': [m.to_dict() for m in materials],
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    }


# =============================================================================
# STAGE 4: DETAIL
# =============================================================================

def stage_detail_gp(secondary_result: Dict[str, Any], normalized_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply GP modifiers with masks for detail pass.

    Processes:
    - GP modifier stack configuration
    - Mask application
    - Effect blending

    Args:
        secondary_result: Result from stage_secondary_gp
        normalized_params: Original normalized parameters

    Returns:
        Detail GP configuration dict with modifier and mask data
    """
    params = normalized_params['params']
    apply_modifiers = params.get('apply_modifiers', True)
    mask_config = params.get('mask_config', {})

    # Build modifier stack
    modifiers = []
    if apply_modifiers:
        # Default GP modifier presets
        modifier_presets = [
            {'type': 'GP_NOISE', 'strength': 0.5},
            {'type': 'GP_SMOOTH', 'iterations': 2},
        ]
        for preset in modifier_presets:
            modifiers.append({
                'type': preset['type'],
                'properties': {k: v for k, v in preset.items() if k != 'type'},
            })

    # Build mask configuration
    mask = None
    if mask_config:
        mask = GPMaskConfig(
            enabled=mask_config.get('enabled', False),
            mask_layer=mask_config.get('mask_layer', ''),
            invert=mask_config.get('invert', False),
            feather=mask_config.get('feather', 0.0),
            type=mask_config.get('type', 'procedural'),
        )

    return {
        'stage': 'detail',
        'modifiers': modifiers,
        'mask': mask.to_dict() if mask else None,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    }


# =============================================================================
# STAGE 5: OUTPUT
# =============================================================================

def stage_output_gp(detail_result: Dict[str, Any], normalized_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare GP for final render output.

    Processes:
    - Animation setup
    - Render layer configuration
    - Output format preparation

    Args:
        detail_result: Result from stage_detail_gp
        normalized_params: Original normalized parameters

    Returns:
        Output configuration dict ready for render
    """
    params = normalized_params['params']

    # Build animation configuration
    animation_config = GPAnimationConfig(
        id="main_animation",
        frame_start=params.get('frame_start', 1),
        frame_end=params.get('frame_end', 100),
        frame_rate=params.get('frame_rate', 24.0),
        onion_skin_enabled=params.get('onion_skin_enabled', False),
    )

    return {
        'stage': 'output',
        'animation': animation_config.to_dict(),
        'render_settings': {
            'engine': 'CYCLES',
            'samples': 128,
            'resolution': (1920, 1080),
        },
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    }


# =============================================================================
# FULL PIPELINE
# =============================================================================

def run_gp_pipeline(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run complete GP generation pipeline.

    Stages:
    1. Normalize - Validate and seed
    2. Primary - Create object structure
    3. Secondary - Generate strokes and materials
    4. Detail - Apply modifiers and masks
    5. Output - Prepare for render

    Args:
        params: Raw generation parameters

    Returns:
        Complete GP configuration dict
    """
    # Stage 1: Normalize
    normalized = stage_normalize_gp(params)
    print(f"[Stage 1/5] Normalize complete - seed: {normalized['seed']}")

    # Stage 2: Primary
    primary = stage_primary_gp(normalized)
    print(f"[Stage 2/5] Primary complete - {primary['layer_count']} layers")

    # Stage 3: Secondary
    secondary = stage_secondary_gp(primary, normalized)
    print(f"[Stage 3/5] Secondary complete - {len(secondary['strokes'])} strokes")

    # Stage 4: Detail
    detail = stage_detail_gp(secondary, normalized)
    print(f"[Stage 4/5] Detail complete - {len(detail['modifiers'])} modifiers")

    # Stage 5: Output
    output = stage_output_gp(detail, normalized)
    print(f"[Stage 5/5] Output complete - ready for render")

    return {
        'normalized': normalized,
        'primary': primary,
        'secondary': secondary,
        'detail': detail,
        'output': output,
        'complete': True,
    }
