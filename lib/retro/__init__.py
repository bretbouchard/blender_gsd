"""
Retro Pixel Art Conversion System

Transforms photorealistic renders into stylized pixel art
across multiple retro console styles. Also includes CRT display
effects for authentic retro monitor simulation.

Modules:
- pixel_types: Data structures and type definitions
- pixelator: Core pixelation engine
- quantizer: Color quantization algorithms
- preset_loader: YAML profile loading
- pixel_compositor: Blender compositor integration
- dither_types: Dithering data structures
- dither_ordered: Bayer and ordered dithering
- dither_error: Error diffusion algorithms
- dither_patterns: Pattern-based dithering
- dither: Main dithering interface
- isometric_types: Isometric and side-scroller data structures
- isometric: Isometric camera system
- side_scroller: Side-scroller camera system
- sprites: Sprite sheet generator
- tiles: Tile system
- view_preset_loader: View preset loader
- crt_types: CRT display effect types and presets
- scanlines: Scanline effect generation
- phosphor: Phosphor mask effects
- curvature: Screen curvature and vignette
- crt_effects: Additional CRT effects (bloom, aberration, noise)
- crt_compositor: Blender compositor integration for CRT
- crt_preset_loader: CRT preset loading from YAML

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

    # Dithering
    from lib.retro import dither, DitherConfig
    dither_config = DitherConfig(mode="atkinson", strength=1.0)
    dithered = dither(image, dither_config)

    # Isometric rendering
    from lib.retro import IsometricConfig, create_isometric_camera_config
    config = IsometricConfig.for_game_style("classic_pixel")
    cam_config = create_isometric_camera_config(config)

    # Sprite sheet generation
    from lib.retro import SpriteSheetConfig, generate_sprite_sheet
    config = SpriteSheetConfig.for_character(frame_width=32, frame_height=32)
    result = generate_sprite_sheet(images, config)

    # CRT display effects
    from lib.retro import load_crt_preset, apply_all_effects
    config = load_crt_preset("arcade_80s")
    result = apply_all_effects(image, config)

    # Custom CRT configuration
    from lib.retro import CRTConfig, ScanlineConfig
    config = CRTConfig(
        name="custom",
        scanlines=ScanlineConfig(enabled=True, intensity=0.3),
        bloom=0.15,
        chromatic_aberration=0.003
    )
    result = apply_all_effects(image, config)
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
# Dithering Module Imports
# =============================================================================

from lib.retro.dither_types import (
    # Enums
    DitherMode as DitherModeEnum,
    DitherColorSpace,
    # Dataclasses
    DitherConfig,
    DitherMatrix,
    # Built-in matrices
    BAYER_2X2,
    BAYER_4X4,
    BAYER_8X8,
    CHECKERBOARD,
    BUILTIN_MATRICES,
    # Functions
    get_matrix,
    list_matrices,
)

from lib.retro.dither_ordered import (
    # Main functions
    ordered_dither,
    bayer_dither,
    checkerboard_dither,
    halftone_dither,
    diagonal_dither,
    blue_noise_dither,
    # Matrix functions
    generate_bayer_matrix,
    normalize_matrix,
    get_bayer_threshold,
    # Constants
    BAYER_2X2_INT,
    BAYER_4X4_INT,
    BAYER_8X8_INT,
)

from lib.retro.dither_error import (
    # Main functions
    error_diffusion_dither,
    floyd_steinberg_dither,
    atkinson_dither,
    sierra_dither,
    jarvis_judice_ninke_dither,
    stucki_dither,
    burkes_dither,
    # Utility functions
    find_nearest_color,
    quantize_to_level,
    rgb_distance,
    lab_distance,
    get_kernel,
    get_kernel_names,
    # Constants
    FLOYD_STEINBERG,
    ATKINSON,
    SIERRA_LITE,
    SIERRA_3,
    JARVIS_JUDICE_NINKE,
    STUCKI,
    BURKES,
    ERROR_DIFFUSION_KERNELS,
)

from lib.retro.dither_patterns import (
    # Main functions
    pattern_dither,
    custom_pattern_dither,
    custom_matrix_dither,
    stipple_dither,
    newsprint_dither,
    woodcut_dither,
    # Pattern generation
    generate_diagonal_pattern,
    generate_dot_pattern,
    generate_circle_pattern,
    generate_crosshatch_pattern,
    tile_pattern,
    # Utility
    list_patterns,
    get_pattern,
    # Constants
    DIAGONAL_LINES,
    HORIZONTAL_LINES,
    VERTICAL_LINES,
    CROSSHATCH,
    DIAMOND,
    DOTS_2X2,
    DOTS_3X3,
    CIRCLES_4X4,
    HERRINGBONE,
    BRICK,
    WEAVE,
    PATTERNS,
)

from lib.retro.dither import (
    # Main function
    dither,
    # Convenience functions
    dither_1bit,
    dither_gameboy,
    dither_macplus,
    dither_newspaper,
    # Utility functions
    get_available_modes,
    list_all_modes,
    is_valid_mode,
    get_mode_description,
)


# =============================================================================
# Isometric & Side-Scroller Module Imports
# =============================================================================

from lib.retro.isometric_types import (
    # Enums
    IsometricAngle,
    ViewDirection,
    SpriteFormat,
    TileFormat,
    # Dataclasses
    IsometricConfig,
    SideScrollerConfig,
    SpriteSheetConfig,
    TileConfig,
    IsometricRenderResult,
    SpriteSheetResult,
    TileSetResult,
    # Angle presets
    ISOMETRIC_ANGLES,
    get_isometric_angle,
    list_isometric_angles,
    # Tile sizes
    TILE_SIZES,
    get_tile_size,
    list_tile_sizes,
)

from lib.retro.isometric import (
    # Camera config
    CameraConfig,
    # Main functions
    create_isometric_camera_config,
    set_isometric_angle,
    calculate_isometric_rotation,
    calculate_camera_position,
    # Projection functions
    project_to_isometric,
    project_to_screen,
    # Depth sorting
    depth_sort_objects,
    get_isometric_depth,
    # Grid functions
    create_isometric_grid_data,
    snap_to_isometric_grid,
    # Rendering
    render_isometric_tile,
    render_isometric_tile_set,
    # Utility
    get_tile_bounds,
    world_to_tile,
    tile_to_world,
    calculate_tile_neighbors,
)

from lib.retro.side_scroller import (
    # Dataclasses
    ParallaxLayer,
    SideScrollerCameraConfig,
    # Camera functions
    create_side_scroller_camera_config,
    get_camera_rotation_for_view,
    # Parallax functions
    separate_parallax_layers,
    calculate_parallax_offset,
    calculate_layer_scroll_speed,
    get_parallax_positions,
    # Rendering
    render_parallax_layer,
    render_all_parallax_layers,
    # Animation
    create_parallax_animation,
    animate_parallax_layers,
    # Depth assignment
    assign_depth_by_z,
    assign_depth_by_collection,
    assign_depth_by_name_pattern,
    # Utility
    get_layer_visibility_at_depth,
    calculate_optimal_layer_count,
    generate_layer_depths,
    merge_parallax_layers,
)

from lib.retro.sprites import (
    # Dataclasses
    SpriteFrame,
    # Main functions
    generate_sprite_sheet,
    trim_sprite,
    calculate_pivot,
    calculate_pivot_world,
    # Metadata generation
    generate_sprite_metadata,
    export_phaser_json,
    export_unity_json,
    export_godot_json,
    export_generic_json,
    # Animation helpers
    extract_animation_frames,
    generate_walk_cycle_sheet,
    generate_animation_sheet,
    # Utility
    get_frame_position,
    get_frame_bounds,
    calculate_frame_count,
    optimize_sheet_layout,
)

from lib.retro.tiles import (
    # Dataclasses
    Tile,
    TileSet,
    # Tile set generation
    render_tile_set,
    create_tile_set_from_images,
    # Tile map generation
    generate_tile_map,
    generate_tile_map_from_positions,
    # Tile map export
    export_tile_map,
    export_tile_map_csv,
    export_tile_map_json,
    export_tile_map_tmx,
    # Autotile
    AUTOTILE_MASKS,
    calculate_autotile_index,
    get_autotile_neighbors,
    create_autotile_template,
    apply_autotile,
    # Collision map
    generate_collision_map,
    export_collision_map,
    # Utility
    get_tile_at_position,
    world_to_tile as tile_world_to_tile,
    tile_to_world as tile_tile_to_world,
    resize_tile_map,
    flip_tile_map_horizontal,
    flip_tile_map_vertical,
    rotate_tile_map_90,
)

from lib.retro.view_preset_loader import (
    # Isometric presets
    load_isometric_preset,
    list_isometric_presets,
    get_isometric_preset,
    # Side-scroller presets
    load_side_scroller_preset,
    list_side_scroller_presets,
    get_side_scroller_preset,
    # Sprite sheet presets
    load_sprite_sheet_preset,
    list_sprite_sheet_presets,
    get_sprite_sheet_preset,
    # Tile presets
    load_tile_preset,
    list_tile_presets,
    get_tile_preset,
    # Generic
    load_view_preset,
    list_view_presets,
    # Cache management
    clear_preset_cache,
    reload_presets,
)


# =============================================================================
# CRT Display Effects Module Imports
# =============================================================================

from lib.retro.crt_types import (
    # Enums
    ScanlineMode,
    PhosphorPattern,
    DisplayType,
    # Dataclasses
    ScanlineConfig,
    PhosphorConfig,
    CurvatureConfig,
    CRTConfig,
    # Built-in presets
    CRT_PRESETS,
    # Functions
    get_preset as get_crt_preset_builtin,
    list_presets as list_crt_presets_builtin,
    get_preset_description,
    create_custom_preset,
    validate_config as validate_crt_config,
)

from lib.retro.scanlines import (
    # Pattern generators
    alternate_scanlines,
    every_line_scanlines,
    random_scanlines,
    # Overlay creation
    create_scanline_overlay,
    create_scanline_texture,
    # Main functions
    apply_scanlines,
    apply_scanlines_fast,
    apply_scanlines_gpu,
    get_scanline_shader_code,
    # Utility functions
    calculate_brightness_loss,
    recommend_brightness_compensation,
    estimate_scanline_visibility,
)

from lib.retro.phosphor import (
    # Pattern generators
    create_rgb_stripe_mask,
    create_aperture_grille_mask,
    create_slot_mask,
    create_shadow_mask,
    create_phosphor_mask,
    # Application functions
    apply_phosphor_mask,
    apply_phosphor_mask_fast,
    # Utility functions
    get_phosphor_brightness_factor,
    list_phosphor_patterns,
    get_pattern_description as get_phosphor_pattern_description,
    estimate_mask_visibility,
    # Constants
    PHOSPHOR_PATTERNS,
)

from lib.retro.curvature import (
    # UV transformation
    calculate_curved_uv,
    calculate_barrel_distortion_grid,
    # Vignette
    create_vignette_mask,
    create_corner_mask,
    apply_vignette,
    # Main functions
    apply_curvature,
    bilinear_sample,
    apply_border,
    combine_curvature_vignette,
    # Utility functions
    calculate_edge_stretch,
    estimate_content_loss,
    recommend_border_size,
)

from lib.retro.crt_effects import (
    # Individual effects
    apply_bloom,
    apply_chromatic_aberration,
    apply_flicker,
    apply_interlace,
    apply_pixel_jitter,
    apply_noise,
    apply_ghosting,
    apply_color_adjustments,
    # Pipeline
    apply_all_effects,
    apply_effects_fast,
)

from lib.retro.crt_compositor import (
    # Node creation
    create_crt_node_group,
    create_scanline_node_config,
    create_phosphor_node_config,
    # Setup
    setup_crt_compositing,
    create_curvature_node,
    create_scanline_node,
    # Utilities
    get_crt_node_group_name,
    list_crt_node_templates,
    get_node_template_description,
    create_preset_nodes,
    export_node_setup_python,
    # Constants
    CRT_NODE_GROUP_NAME,
    CRT_NODE_TEMPLATES,
)

from lib.retro.crt_preset_loader import (
    # Preset loading
    load_crt_preset,
    list_crt_presets,
    get_crt_preset,
    get_crt_preset_description,
    # Cache management
    clear_preset_cache as clear_crt_preset_cache,
    reload_presets as reload_crt_presets,
    # Convenience functions
    get_arcade_80s,
    get_crt_tv,
    get_pvm,
    get_gameboy,
)


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
    "DitherModeEnum",
    "DitherColorSpace",
    "IsometricAngle",
    "ViewDirection",
    "SpriteFormat",
    "TileFormat",

    # Dataclasses
    "PixelStyle",
    "PixelationConfig",
    "PixelationResult",
    "ColorPalette",
    "DitherConfig",
    "DitherMatrix",
    "IsometricConfig",
    "SideScrollerConfig",
    "SpriteSheetConfig",
    "TileConfig",
    "IsometricRenderResult",
    "SpriteSheetResult",
    "TileSetResult",
    "CameraConfig",
    "ParallaxLayer",
    "SideScrollerCameraConfig",
    "SpriteFrame",
    "Tile",
    "TileSet",

    # Core pixelation functions
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

    # ==========================================================================
    # Dithering API
    # ==========================================================================

    # Main dithering
    "dither",
    "DitherConfig",
    "DitherMatrix",
    "DitherModeEnum",
    "DitherColorSpace",

    # Ordered dithering
    "ordered_dither",
    "bayer_dither",
    "checkerboard_dither",
    "halftone_dither",
    "diagonal_dither",
    "blue_noise_dither",

    # Error diffusion
    "error_diffusion_dither",
    "floyd_steinberg_dither",
    "atkinson_dither",
    "sierra_dither",
    "jarvis_judice_ninke_dither",
    "stucki_dither",
    "burkes_dither",

    # Pattern dithering
    "pattern_dither",
    "custom_pattern_dither",
    "custom_matrix_dither",
    "stipple_dither",
    "newsprint_dither",
    "woodcut_dither",

    # Convenience functions
    "dither_1bit",
    "dither_gameboy",
    "dither_macplus",
    "dither_newspaper",

    # Matrix functions
    "generate_bayer_matrix",
    "normalize_matrix",
    "get_bayer_threshold",
    "get_matrix",
    "list_matrices",

    # Color functions
    "find_nearest_color",
    "quantize_to_level",
    "rgb_distance",
    "lab_distance",

    # Pattern functions
    "generate_diagonal_pattern",
    "generate_dot_pattern",
    "generate_circle_pattern",
    "generate_crosshatch_pattern",
    "tile_pattern",
    "list_patterns",
    "get_pattern",

    # Dither utility
    "get_available_modes",
    "list_all_modes",
    "is_valid_mode",
    "get_mode_description",
    "get_kernel",
    "get_kernel_names",

    # Dither constants
    "BAYER_2X2",
    "BAYER_4X4",
    "BAYER_8X8",
    "CHECKERBOARD",
    "BUILTIN_MATRICES",
    "BAYER_2X2_INT",
    "BAYER_4X4_INT",
    "BAYER_8X8_INT",
    "FLOYD_STEINBERG",
    "ATKINSON",
    "SIERRA_LITE",
    "SIERRA_3",
    "JARVIS_JUDICE_NINKE",
    "STUCKI",
    "BURKES",
    "ERROR_DIFFUSION_KERNELS",
    "DIAGONAL_LINES",
    "HORIZONTAL_LINES",
    "VERTICAL_LINES",
    "CROSSHATCH",
    "DIAMOND",
    "DOTS_2X2",
    "DOTS_3X3",
    "CIRCLES_4X4",
    "HERRINGBONE",
    "BRICK",
    "WEAVE",
    "PATTERNS",

    # ==========================================================================
    # Isometric API
    # ==========================================================================

    # Angle presets
    "ISOMETRIC_ANGLES",
    "get_isometric_angle",
    "list_isometric_angles",
    "TILE_SIZES",
    "get_tile_size",
    "list_tile_sizes",

    # Camera functions
    "create_isometric_camera_config",
    "set_isometric_angle",
    "calculate_isometric_rotation",
    "calculate_camera_position",

    # Projection
    "project_to_isometric",
    "project_to_screen",

    # Depth sorting
    "depth_sort_objects",
    "get_isometric_depth",

    # Grid
    "create_isometric_grid_data",
    "snap_to_isometric_grid",

    # Rendering
    "render_isometric_tile",
    "render_isometric_tile_set",

    # Utility
    "get_tile_bounds",
    "world_to_tile",
    "tile_to_world",
    "calculate_tile_neighbors",

    # ==========================================================================
    # Side-Scroller API
    # ==========================================================================

    # Camera
    "create_side_scroller_camera_config",
    "get_camera_rotation_for_view",

    # Parallax
    "separate_parallax_layers",
    "calculate_parallax_offset",
    "calculate_layer_scroll_speed",
    "get_parallax_positions",

    # Rendering
    "render_parallax_layer",
    "render_all_parallax_layers",

    # Animation
    "create_parallax_animation",
    "animate_parallax_layers",

    # Depth assignment
    "assign_depth_by_z",
    "assign_depth_by_collection",
    "assign_depth_by_name_pattern",

    # Utility
    "get_layer_visibility_at_depth",
    "calculate_optimal_layer_count",
    "generate_layer_depths",
    "merge_parallax_layers",

    # ==========================================================================
    # Sprite Sheet API
    # ==========================================================================

    # Main functions
    "generate_sprite_sheet",
    "trim_sprite",
    "calculate_pivot",
    "calculate_pivot_world",

    # Metadata
    "generate_sprite_metadata",
    "export_phaser_json",
    "export_unity_json",
    "export_godot_json",
    "export_generic_json",

    # Animation
    "extract_animation_frames",
    "generate_walk_cycle_sheet",
    "generate_animation_sheet",

    # Utility
    "get_frame_position",
    "get_frame_bounds",
    "calculate_frame_count",
    "optimize_sheet_layout",

    # ==========================================================================
    # Tile System API
    # ==========================================================================

    # Tile set generation
    "render_tile_set",
    "create_tile_set_from_images",

    # Tile map
    "generate_tile_map",
    "generate_tile_map_from_positions",

    # Export
    "export_tile_map",
    "export_tile_map_csv",
    "export_tile_map_json",
    "export_tile_map_tmx",

    # Autotile
    "AUTOTILE_MASKS",
    "calculate_autotile_index",
    "get_autotile_neighbors",
    "create_autotile_template",
    "apply_autotile",

    # Collision
    "generate_collision_map",
    "export_collision_map",

    # Tile utility
    "get_tile_at_position",
    "tile_world_to_tile",
    "tile_tile_to_world",
    "resize_tile_map",
    "flip_tile_map_horizontal",
    "flip_tile_map_vertical",
    "rotate_tile_map_90",

    # ==========================================================================
    # View Preset API
    # ==========================================================================

    # Isometric presets
    "load_isometric_preset",
    "list_isometric_presets",
    "get_isometric_preset",

    # Side-scroller presets
    "load_side_scroller_preset",
    "list_side_scroller_presets",
    "get_side_scroller_preset",

    # Sprite sheet presets
    "load_sprite_sheet_preset",
    "list_sprite_sheet_presets",
    "get_sprite_sheet_preset",

    # Tile presets
    "load_tile_preset",
    "list_tile_presets",
    "get_tile_preset",

    # Generic
    "load_view_preset",
    "list_view_presets",

    # Cache
    "clear_preset_cache",
    "reload_presets",

    # ==========================================================================
    # CRT Display Effects API
    # ==========================================================================

    # CRT Enums
    "ScanlineMode",
    "PhosphorPattern",
    "DisplayType",

    # CRT Dataclasses
    "ScanlineConfig",
    "PhosphorConfig",
    "CurvatureConfig",
    "CRTConfig",

    # CRT Presets
    "CRT_PRESETS",
    "get_crt_preset_builtin",
    "list_crt_presets_builtin",
    "get_preset_description",
    "create_custom_preset",
    "validate_crt_config",

    # Scanline Effects
    "alternate_scanlines",
    "every_line_scanlines",
    "random_scanlines",
    "create_scanline_overlay",
    "create_scanline_texture",
    "apply_scanlines",
    "apply_scanlines_fast",
    "apply_scanlines_gpu",
    "get_scanline_shader_code",
    "calculate_brightness_loss",
    "recommend_brightness_compensation",
    "estimate_scanline_visibility",

    # Phosphor Effects
    "create_rgb_stripe_mask",
    "create_aperture_grille_mask",
    "create_slot_mask",
    "create_shadow_mask",
    "create_phosphor_mask",
    "apply_phosphor_mask",
    "apply_phosphor_mask_fast",
    "get_phosphor_brightness_factor",
    "list_phosphor_patterns",
    "get_phosphor_pattern_description",
    "estimate_mask_visibility",
    "PHOSPHOR_PATTERNS",

    # Curvature Effects
    "calculate_curved_uv",
    "calculate_barrel_distortion_grid",
    "create_vignette_mask",
    "create_corner_mask",
    "apply_vignette",
    "apply_curvature",
    "bilinear_sample",
    "apply_border",
    "combine_curvature_vignette",
    "calculate_edge_stretch",
    "estimate_content_loss",
    "recommend_border_size",

    # Additional CRT Effects
    "apply_bloom",
    "apply_chromatic_aberration",
    "apply_flicker",
    "apply_interlace",
    "apply_pixel_jitter",
    "apply_noise",
    "apply_ghosting",
    "apply_color_adjustments",
    "apply_all_effects",
    "apply_effects_fast",

    # CRT Compositor
    "create_crt_node_group",
    "create_scanline_node_config",
    "create_phosphor_node_config",
    "setup_crt_compositing",
    "create_curvature_node",
    "create_scanline_node",
    "get_crt_node_group_name",
    "list_crt_node_templates",
    "get_node_template_description",
    "create_preset_nodes",
    "export_node_setup_python",
    "CRT_NODE_GROUP_NAME",
    "CRT_NODE_TEMPLATES",

    # CRT Preset Loader
    "load_crt_preset",
    "list_crt_presets",
    "get_crt_preset",
    "get_crt_preset_description",
    "clear_crt_preset_cache",
    "reload_crt_presets",
    "get_arcade_80s",
    "get_crt_tv",
    "get_pvm",
    "get_gameboy",
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

__version__ = "0.3.0"
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
        "isometric_presets": list_isometric_presets(),
        "side_scroller_presets": list_side_scroller_presets(),
        "sprite_sheet_presets": list_sprite_sheet_presets(),
        "tile_presets": list_tile_presets(),
        "crt_presets": list_crt_presets(),
    }
