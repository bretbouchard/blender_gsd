"""
VFX Compositor Package

Multi-layer compositing system for VFX integration and final output assembly.

Phase 12.1: Compositor
Requirements: REQ-COMP-01 through REQ-COMP-05

Modules:
- compositor_types: Data structures for compositing
- layer_compositor: Layer management and compositing
- blend_modes: Blend mode implementations
- color_correction: Color correction functions
- cryptomatte: Cryptomatte matte extraction
- compositor_blender: Blender integration
"""

from .compositor_types import (
    # Enums
    BlendMode,
    LayerSource,
    OutputFormat,
    # Dataclasses
    Transform2D,
    ColorCorrection,
    GradientStop,
    LayerMask,
    CompLayer,
    CryptomatteLayer,
    CompositeConfig,
)

from .layer_compositor import (
    LayerCompositor,
    CompositeResult,
    create_compositor,
    load_compositor,
)

from .blend_modes import (
    # Basic blend functions
    blend_normal,
    blend_multiply,
    blend_screen,
    blend_add,
    blend_subtract,
    blend_difference,
    # Contrast blends
    blend_overlay,
    blend_soft_light,
    blend_hard_light,
    # Dodge/Burn
    blend_color_dodge,
    blend_color_burn,
    blend_linear_dodge,
    blend_linear_burn,
    # Comparative
    blend_darken,
    blend_lighten,
    blend_exclusion,
    blend_pin_light,
    blend_hard_mix,
    # Component
    blend_hue,
    blend_saturation,
    blend_color,
    blend_luminosity,
    # Color space
    rgb_to_hsl,
    hsl_to_rgb,
    # Registry
    BLEND_MODES,
    BLEND_MODES_RGB,
    get_blend_function,
    apply_blend,
)

from .color_correction import (
    # Basic
    apply_exposure,
    apply_gamma,
    apply_contrast,
    apply_saturation,
    # LGG
    apply_lift_gamma_gain,
    apply_lgg_rgb,
    # CDL
    apply_cdl,
    apply_cdl_rgb,
    # Curves
    apply_curve,
    apply_rgb_curves,
    # Levels
    apply_levels,
    # HSV
    rgb_to_hsv,
    hsv_to_rgb,
    apply_hsv_adjustment,
    # White balance
    apply_white_balance,
    # Highlights/Shadows
    apply_highlights_shadows,
    # Combined
    apply_color_correction,
    # Presets
    COLOR_PRESETS,
    get_color_preset,
    apply_preset,
)

from .cryptomatte import (
    # Dataclasses
    CryptomatteManifestEntry,
    CryptomatteManifest,
    MatteResult,
    # Hash functions
    hash_object_name,
    hash_to_float,
    float_to_hash,
    # Manifest
    load_manifest_from_json,
    load_manifest_from_exr_sidecar,
    parse_manifest_from_exr_header,
    create_cryptomatte_manifest,
    save_manifest,
    # Extraction
    extract_matte_for_object,
    extract_matte_for_objects,
    # Utilities
    get_cryptomatte_layer_names,
    get_cryptomatte_info,
    rank_to_channels,
    estimate_cryptomatte_ranks,
    merge_manifests,
)

from .compositor_blender import (
    create_composite_nodes,
    create_layer_node,
    create_transform_node,
    create_color_correction_node,
    create_blend_node,
    setup_render_passes,
    create_basic_composite,
    add_color_correction_to_composite,
)


__all__ = [
    # Types
    "BlendMode",
    "LayerSource",
    "OutputFormat",
    "Transform2D",
    "ColorCorrection",
    "GradientStop",
    "LayerMask",
    "CompLayer",
    "CryptomatteLayer",
    "CompositeConfig",
    # Compositor
    "LayerCompositor",
    "CompositeResult",
    "create_compositor",
    "load_compositor",
    # Blend Modes
    "blend_normal",
    "blend_multiply",
    "blend_screen",
    "blend_add",
    "blend_subtract",
    "blend_difference",
    "blend_overlay",
    "blend_soft_light",
    "blend_hard_light",
    "blend_color_dodge",
    "blend_color_burn",
    "blend_linear_dodge",
    "blend_linear_burn",
    "blend_darken",
    "blend_lighten",
    "blend_exclusion",
    "blend_pin_light",
    "blend_hard_mix",
    "blend_hue",
    "blend_saturation",
    "blend_color",
    "blend_luminosity",
    "rgb_to_hsl",
    "hsl_to_rgb",
    "BLEND_MODES",
    "BLEND_MODES_RGB",
    "get_blend_function",
    "apply_blend",
    # Color Correction
    "apply_exposure",
    "apply_gamma",
    "apply_contrast",
    "apply_saturation",
    "apply_lift_gamma_gain",
    "apply_lgg_rgb",
    "apply_cdl",
    "apply_cdl_rgb",
    "apply_curve",
    "apply_rgb_curves",
    "apply_levels",
    "rgb_to_hsv",
    "hsv_to_rgb",
    "apply_hsv_adjustment",
    "apply_white_balance",
    "apply_highlights_shadows",
    "apply_color_correction",
    "COLOR_PRESETS",
    "get_color_preset",
    "apply_preset",
    # Cryptomatte
    "CryptomatteManifestEntry",
    "CryptomatteManifest",
    "MatteResult",
    "hash_object_name",
    "hash_to_float",
    "float_to_hash",
    "load_manifest_from_json",
    "load_manifest_from_exr_sidecar",
    "parse_manifest_from_exr_header",
    "create_cryptomatte_manifest",
    "save_manifest",
    "extract_matte_for_object",
    "extract_matte_for_objects",
    "get_cryptomatte_layer_names",
    "get_cryptomatte_info",
    "rank_to_channels",
    "estimate_cryptomatte_ranks",
    "merge_manifests",
    # Blender
    "create_composite_nodes",
    "create_layer_node",
    "create_transform_node",
    "create_color_correction_node",
    "create_blend_node",
    "setup_render_passes",
    "create_basic_composite",
    "add_color_correction_to_composite",
]

__version__ = "0.1.0"
