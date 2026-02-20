"""
Retro Pixel Art Conversion System

Transforms photorealistic renders into stylized pixel art
across multiple retro console styles.

Modules:
- pixel_types: Data structures and type definitions
- pixelator: Core pixelation engine
- quantizer: Color quantization algorithms
- preset_loader: YAML profile loading
- pixel_compositor: Blender compositor integration

Example Usage:
    from lib.retro import pixelate, PixelationConfig

    # Using console preset
    config = PixelationConfig.for_console("snes")
    result = pixelate(image, config)

    # Custom configuration
    from lib.retro import PixelStyle
    config = PixelationConfig(
        style=PixelStyle(mode="8bit", pixel_size=4, color_limit=16),
        target_resolution=(128, 128)
    )
    result = pixelate(image, config)

    # Load from YAML preset
    from lib.retro import load_pixel_profile
    config = load_pixel_profile("gameboy")
    result = pixelate(image, config)
"""

from lib.retro.pixel_types import (
    # Enums
    PixelMode,
    AspectRatioMode,
    ScalingFilter,
    DitherMode,
    SubPixelLayout,
    # Dataclasses
    PixelStyle,
    PixelationConfig,
    PixelationResult,
    ColorPalette,
    # Built-in palettes
    GAMEBOY_PALETTE,
    NES_PALETTE,
    PICO8_PALETTE,
    CGA_PALETTE,
    MACPLUS_PALETTE,
    EGA_PALETTE,
    BUILTIN_PALETTES,
    # Functions
    get_palette,
    list_palettes as list_builtin_palettes,
)

from lib.retro.pixelator import (
    # Main functions
    pixelate,
    downscale_image,
    pixelate_block,
    enhance_edges,
    posterize,
    quantize_colors as pixelator_quantize_colors,
    quantize_to_palette,
    extract_palette,
    # Mode-specific
    pixelate_32bit,
    pixelate_16bit,
    pixelate_8bit,
    pixelate_4bit,
    pixelate_2bit,
    pixelate_1bit,
)

from lib.retro.quantizer import (
    quantize_colors,
    quantize_to_palette as quantizer_quantize_to_palette,
    extract_palette as quantizer_extract_palette,
    median_cut_quantize,
    kmeans_quantize,
    octree_quantize,
    nearest_color_match,
    build_weighted_palette,
    count_colors,
    get_color_histogram,
    OctreeNode,
)

from lib.retro.preset_loader import (
    load_pixel_profile,
    list_profiles,
    load_palette,
    list_palettes,
    load_resolution,
    list_resolutions,
    get_snes_config,
    get_nes_config,
    get_gameboy_config,
    get_pico8_config,
)

# Blender compositor integration (optional)
try:
    from lib.retro.pixel_compositor import (
        create_pixelator_nodes,
        setup_pixelator_pass,
        bake_pixelation,
        create_scale_node,
        create_posterize_node,
        create_color_ramp_quantize,
        setup_pixel_preview,
        apply_pixel_style_to_scene,
        get_pixel_node_group,
    )
    HAS_COMPOSITOR = True
except ImportError:
    HAS_COMPOSITOR = False


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Enums
    "PixelMode",
    "AspectRatioMode",
    "ScalingFilter",
    "DitherMode",
    "SubPixelLayout",

    # Dataclasses
    "PixelStyle",
    "PixelationConfig",
    "PixelationResult",
    "ColorPalette",

    # Core functions
    "pixelate",
    "downscale_image",
    "pixelate_block",
    "enhance_edges",
    "posterize",
    "quantize_colors",
    "quantize_to_palette",
    "extract_palette",

    # Quantization methods
    "median_cut_quantize",
    "kmeans_quantize",
    "octree_quantize",
    "nearest_color_match",
    "build_weighted_palette",

    # Mode-specific functions
    "pixelate_32bit",
    "pixelate_16bit",
    "pixelate_8bit",
    "pixelate_4bit",
    "pixelate_2bit",
    "pixelate_1bit",

    # Presets
    "load_pixel_profile",
    "list_profiles",
    "load_palette",
    "list_palettes",
    "load_resolution",
    "list_resolutions",
    "get_snes_config",
    "get_nes_config",
    "get_gameboy_config",
    "get_pico8_config",

    # Built-in palettes
    "GAMEBOY_PALETTE",
    "NES_PALETTE",
    "PICO8_PALETTE",
    "CGA_PALETTE",
    "MACPLUS_PALETTE",
    "EGA_PALETTE",
    "BUILTIN_PALETTES",
    "get_palette",
    "list_builtin_palettes",

    # Utility
    "count_colors",
    "get_color_histogram",
    "OctreeNode",

    # Compositor (optional)
    "HAS_COMPOSITOR",
]

# Add compositor functions to exports if available
if HAS_COMPOSITOR:
    __all__.extend([
        "create_pixelator_nodes",
        "setup_pixelator_pass",
        "bake_pixelation",
        "create_scale_node",
        "create_posterize_node",
        "create_color_ramp_quantize",
        "setup_pixel_preview",
        "apply_pixel_style_to_scene",
        "get_pixel_node_group",
    ])


# =============================================================================
# Module info
# =============================================================================

__version__ = "0.1.0"
__author__ = "GSD"
__description__ = "Retro pixel art conversion for cinematic rendering"


def get_version() -> str:
    """Get module version."""
    return __version__


def info() -> dict:
    """Get module information."""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "has_compositor": HAS_COMPOSITOR,
        "builtin_palettes": list_builtin_palettes(),
        "profiles_available": list_profiles() if list_profiles() else [],
    }
