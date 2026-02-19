"""
Cinematic Rendering System Package

A comprehensive system for cinematic camera, lighting, and rendering.

Modules:
- types: Core data structures (ShotState, CameraConfig, etc.)
- enums: Type-safe enumerations
- state_manager: State persistence
- preset_loader: Camera and lighting preset loading utilities
- camera: Camera creation and management
- plumb_bob: Orbit/focus targeting system
- lenses: Lens imperfections via compositor
- rigs: Camera rig systems and multi-camera layouts
- lighting: Light creation and management
- gel: Gel/color filter system
- hdri: HDRI environment lighting
- backdrops: Infinite curve backdrops, gradients, and shadow catchers
- color: Color management, LUT validation, and exposure lock
- animation: Camera moves, motion paths, and turntable rotations
- motion_path: Procedural motion path generation
- render: Quality tiers, render passes, EXR output, denoising

Quick Start:
    from lib.cinematic import (
        ShotState, CameraConfig, Transform3D,
        StateManager, FrameStore,
        PlumbBobConfig, RigConfig,
        get_lens_preset, get_sensor_preset,
        create_camera, configure_dof,
        apply_plumb_bob_to_rig,
        setup_camera_rig,
        # Lighting
        LightConfig, GelConfig, HDRIConfig, LightRigConfig,
        create_light, create_area_light, create_spot_light,
        setup_light_linking, apply_lighting_rig,
        apply_gel, create_gel_from_preset, kelvin_to_rgb,
        setup_hdri, load_hdri_preset, find_hdri_path,
        # Color management
        ColorConfig, LUTConfig, ExposureLockConfig,
        set_view_transform, apply_color_preset, apply_lut,
    )

    # Create camera config
    camera = CameraConfig(
        name="hero_camera",
        focal_length=85.0,
        f_stop=4.0
    )

    # Create shot state
    state = ShotState(
        shot_name="hero_knob_01",
        camera=camera
    )

    # Save state
    manager = StateManager()
    manager.save(state, Path(".gsd-state/cinematic/sessions/hero.yaml"))

    # Load lens preset
    lens = get_lens_preset("85mm_portrait")

    # Create camera in Blender
    cam_obj = create_camera(camera, set_active=True)

    # Set up plumb bob targeting
    plumb_config = PlumbBobConfig(mode="auto", offset=(0, 0, 0.5))
    apply_plumb_bob_to_rig("hero_camera", "my_subject", plumb_config)

    # Set up camera rig
    rig_config = RigConfig(rig_type="tripod")
    setup_camera_rig("hero_camera", rig_config, "plumb_bob_target")

    # Apply lighting rig preset
    apply_lighting_rig("three_point_soft", target_position=(0, 0, 0.5))

    # Set up HDRI environment
    load_hdri_preset("studio_bright")

    # Apply color preset
    apply_color_preset("agx_default")
"""

from .types import (
    Transform3D,
    CameraConfig,
    LightConfig,
    BackdropConfig,
    RenderSettings,
    ShotState,
    PlumbBobConfig,
    RigConfig,
    ImperfectionConfig,
    MultiCameraLayout,
    # Lighting types
    GelConfig,
    HDRIConfig,
    LightRigConfig,
    # Color types
    ColorConfig,
    LUTConfig,
    ExposureLockConfig,
    # Animation types
    AnimationConfig,
    MotionPathConfig,
    TurntableConfig,
    # Composition types
    CompositionConfig,
    CompleteShotConfig,
    # Composition constants
    SHOT_SIZES,
    LENS_BY_SHOT_SIZE,
    FSTOP_BY_SHOT_SIZE,
    CAMERA_ANGLES,
    CAMERA_POSITIONS,
    LIGHTING_RATIOS,
    # Render types
    CinematicRenderSettings,
)
from .enums import (
    LensType,
    LightType,
    QualityTier,
    ColorSpace,
    EasingType,
    # Lighting enum
    AreaLightShape,
    # Color enums
    ViewTransform,
    WorkingColorSpace,
    # Render enums
    RenderEngine,
    DenoiserType,
)
from .state_manager import (
    StateManager,
    FrameStore,
)
from .preset_loader import (
    load_preset,
    get_lens_preset,
    get_sensor_preset,
    get_rig_preset,
    get_imperfection_preset,
    list_lens_presets,
    list_sensor_presets,
    list_rig_presets,
    list_imperfection_presets,
    get_aperture_preset,
    # Lighting preset loaders
    get_lighting_rig_preset,
    get_gel_preset,
    get_hdri_preset,
    list_lighting_rig_presets,
    list_gel_presets,
    list_hdri_presets,
    # Backdrop preset loaders
    get_infinite_curve_preset,
    get_gradient_preset,
    get_environment_preset,
    list_infinite_curve_presets,
    list_gradient_presets,
    list_environment_presets,
    # Color preset loaders
    get_color_preset,
    get_technical_lut_preset,
    get_film_lut_preset,
    list_color_presets,
    list_technical_lut_presets,
    list_film_lut_presets,
    # Animation preset loaders
    get_camera_move_preset,
    get_easing_preset,
    get_turntable_preset,
    list_camera_move_presets,
    list_easing_presets,
    list_turntable_presets,
    # Render preset loaders
    get_quality_profile,
    get_pass_preset,
    get_exr_settings,
    list_quality_profiles,
    list_pass_presets,
    list_exr_presets,
)
from .camera import (
    create_camera,
    configure_dof,
    apply_lens_preset,
    apply_sensor_preset,
    get_active_camera,
    set_active_camera,
    delete_camera,
    list_cameras,
    validate_aperture,
    set_focus_mode,
    APERTURE_MIN,
    APERTURE_MAX,
    BLENDER_AVAILABLE,
)
from .plumb_bob import (
    calculate_plumb_bob,
    create_target_empty,
    calculate_focus_distance,
    set_camera_focus_target,
    remove_target_empty,
    get_or_create_target,
    apply_plumb_bob_to_rig,
)
from .lenses import (
    setup_compositor_for_lens,
    apply_lens_imperfections,
    get_bokeh_blade_count,
    clear_lens_effects,
    apply_imperfection_preset,
    apply_bokeh_to_camera,
)
from .rigs import (
    setup_camera_rig,
    create_rig_controller,
    clear_rig_constraints,
    get_rig_type,
    apply_rig_preset,
    create_multi_camera_layout,
    setup_multi_camera_composite,
    render_multi_camera_composite,
    clear_multi_camera_composite,
)
from .lighting import (
    create_light,
    create_area_light,
    create_spot_light,
    create_point_light,
    create_sun_light,
    setup_light_linking,
    apply_lighting_rig,
    delete_light,
    list_lights,
    get_light,
    set_light_intensity,
    set_light_color,
    set_light_temperature,
)
from .gel import (
    apply_gel,
    create_gel_from_preset,
    kelvin_to_rgb,
    combine_gels,
    list_gel_presets as list_gel_preset_names,
)
from .hdri import (
    setup_hdri,
    load_hdri_preset,
    find_hdri_path,
    clear_hdri,
    get_hdri_info,
    list_available_hdris,
)
from .backdrops import (
    create_infinite_curve,
    create_gradient_material,
    apply_gradient_material,
    setup_shadow_catcher,
    configure_render_for_shadow_catcher,
    create_backdrop,
    create_backdrop_from_preset,
    delete_backdrop,
    get_backdrop,
)
from .color import (
    set_view_transform,
    apply_color_preset,
    get_current_color_settings,
    reset_color_settings,
    get_available_looks,
    set_working_color_space,
    validate_lut_file,
    find_lut_path,
    load_lut_config,
    list_available_luts,
    apply_lut,
    remove_lut_nodes,
    get_active_luts,
    calculate_auto_exposure,
    apply_exposure_lock,
    set_exposure,
    set_gamma,
    get_exposure_range,
    get_gamma_range,
)
from .shot_builder import (
    apply_shot_preset,
    get_shot_preset,
    list_shot_presets,
    list_shot_presets_by_category,
    get_shot_preset_info,
    get_presets_for_use_case,
    ShotPreset,
)
from .animation import (
    create_orbit_animation,
    create_dolly_animation,
    create_truck_animation,
    create_crane_animation,
    create_pan_animation,
    create_tilt_animation,
    create_rack_focus_animation,
    create_push_in_animation,
    create_turntable_animation,
    create_animation_from_preset,
    apply_camera_move_preset,
    apply_turntable_preset,
    clear_animation,
    set_scene_frame_range,
    apply_easing,
)
from .motion_path import (
    generate_bezier_path,
    generate_arc_path,
    generate_orbit_path,
    interpolate_catmull_rom,
    create_motion_path_curve,
    setup_camera_follow_path,
    create_motion_path_from_config,
    create_motion_path_from_preset,
    calculate_path_length,
    get_point_at_distance,
    sample_path_uniformly,
    remove_motion_path,
)
from .render import (
    apply_quality_profile,
    apply_render_settings,
    configure_render_passes,
    setup_cryptomatte,
    setup_exr_output,
    detect_optimal_denoiser,
    enable_denoising,
    set_render_engine,
    set_resolution,
    set_frame_range,
    render_frame,
    render_animation,
    get_render_settings,
    apply_pass_preset,
)

__all__ = [
    # Core types
    "Transform3D",
    "CameraConfig",
    "LightConfig",
    "BackdropConfig",
    "RenderSettings",
    "ShotState",

    # Camera system types
    "PlumbBobConfig",
    "RigConfig",
    "ImperfectionConfig",
    "MultiCameraLayout",

    # Lighting types
    "GelConfig",
    "HDRIConfig",
    "LightRigConfig",

    # Color types
    "ColorConfig",
    "LUTConfig",
    "ExposureLockConfig",

    # Animation types
    "AnimationConfig",
    "MotionPathConfig",
    "TurntableConfig",

    # Composition types
    "CompositionConfig",
    "CompleteShotConfig",

    # Composition constants
    "SHOT_SIZES",
    "LENS_BY_SHOT_SIZE",
    "FSTOP_BY_SHOT_SIZE",
    "CAMERA_ANGLES",
    "CAMERA_POSITIONS",
    "LIGHTING_RATIOS",

    # Enums
    "LensType",
    "LightType",
    "QualityTier",
    "ColorSpace",
    "EasingType",
    "AreaLightShape",
    # Color enums
    "ViewTransform",
    "WorkingColorSpace",

    # State management
    "StateManager",
    "FrameStore",

    # Preset loading
    "load_preset",
    "get_lens_preset",
    "get_sensor_preset",
    "get_rig_preset",
    "get_imperfection_preset",
    "list_lens_presets",
    "list_sensor_presets",
    "list_rig_presets",
    "list_imperfection_presets",
    "get_aperture_preset",
    # Lighting preset loaders
    "get_lighting_rig_preset",
    "get_gel_preset",
    "get_hdri_preset",
    "list_lighting_rig_presets",
    "list_gel_presets",
    "list_hdri_presets",
    # Backdrop preset loaders
    "get_infinite_curve_preset",
    "get_gradient_preset",
    "get_environment_preset",
    "list_infinite_curve_presets",
    "list_gradient_presets",
    "list_environment_presets",
    # Color preset loaders
    "get_color_preset",
    "get_technical_lut_preset",
    "get_film_lut_preset",
    "list_color_presets",
    "list_technical_lut_presets",
    "list_film_lut_presets",
    # Animation preset loaders
    "get_camera_move_preset",
    "get_easing_preset",
    "get_turntable_preset",
    "list_camera_move_presets",
    "list_easing_presets",
    "list_turntable_presets",

    # Camera functions
    "create_camera",
    "configure_dof",
    "apply_lens_preset",
    "apply_sensor_preset",
    "get_active_camera",
    "set_active_camera",
    "delete_camera",
    "list_cameras",
    "validate_aperture",
    "set_focus_mode",

    # Plumb bob functions
    "calculate_plumb_bob",
    "create_target_empty",
    "calculate_focus_distance",
    "set_camera_focus_target",
    "remove_target_empty",
    "get_or_create_target",
    "apply_plumb_bob_to_rig",

    # Lens functions
    "setup_compositor_for_lens",
    "apply_lens_imperfections",
    "get_bokeh_blade_count",
    "clear_lens_effects",
    "apply_imperfection_preset",
    "apply_bokeh_to_camera",

    # Rig functions
    "setup_camera_rig",
    "create_rig_controller",
    "clear_rig_constraints",
    "get_rig_type",
    "apply_rig_preset",
    "create_multi_camera_layout",
    "setup_multi_camera_composite",
    "render_multi_camera_composite",
    "clear_multi_camera_composite",

    # Lighting functions
    "create_light",
    "create_area_light",
    "create_spot_light",
    "create_point_light",
    "create_sun_light",
    "setup_light_linking",
    "apply_lighting_rig",
    "delete_light",
    "list_lights",
    "get_light",
    "set_light_intensity",
    "set_light_color",
    "set_light_temperature",

    # Gel functions
    "apply_gel",
    "create_gel_from_preset",
    "kelvin_to_rgb",
    "combine_gels",
    "list_gel_preset_names",

    # HDRI functions
    "setup_hdri",
    "load_hdri_preset",
    "find_hdri_path",
    "clear_hdri",
    "get_hdri_info",
    "list_available_hdris",

    # Backdrop functions
    "create_infinite_curve",
    "create_gradient_material",
    "apply_gradient_material",
    "setup_shadow_catcher",
    "configure_render_for_shadow_catcher",
    "create_backdrop",
    "create_backdrop_from_preset",
    "delete_backdrop",
    "get_backdrop",

    # Color functions
    "set_view_transform",
    "apply_color_preset",
    "get_current_color_settings",
    "reset_color_settings",
    "get_available_looks",
    "set_working_color_space",
    "validate_lut_file",
    "find_lut_path",
    "load_lut_config",
    "list_available_luts",
    "apply_lut",
    "remove_lut_nodes",
    "get_active_luts",
    "calculate_auto_exposure",
    "apply_exposure_lock",
    "set_exposure",
    "set_gamma",
    "get_exposure_range",
    "get_gamma_range",

    # Shot preset functions
    "apply_shot_preset",
    "get_shot_preset",
    "list_shot_presets",
    "list_shot_presets_by_category",
    "get_shot_preset_info",
    "get_presets_for_use_case",
    "ShotPreset",

    # Animation functions
    "create_orbit_animation",
    "create_dolly_animation",
    "create_truck_animation",
    "create_crane_animation",
    "create_pan_animation",
    "create_tilt_animation",
    "create_rack_focus_animation",
    "create_push_in_animation",
    "create_turntable_animation",
    "create_animation_from_preset",
    "apply_camera_move_preset",
    "apply_turntable_preset",
    "clear_animation",
    "set_scene_frame_range",
    "apply_easing",

    # Motion path functions
    "generate_bezier_path",
    "generate_arc_path",
    "generate_orbit_path",
    "interpolate_catmull_rom",
    "create_motion_path_curve",
    "setup_camera_follow_path",
    "create_motion_path_from_config",
    "create_motion_path_from_preset",
    "calculate_path_length",
    "get_point_at_distance",
    "sample_path_uniformly",
    "remove_motion_path",

    # Render types
    "CinematicRenderSettings",
    # Render enums
    "RenderEngine",
    "DenoiserType",
    # Render preset loaders
    "get_quality_profile",
    "get_pass_preset",
    "get_exr_settings",
    "list_quality_profiles",
    "list_pass_presets",
    "list_exr_presets",
    # Render functions
    "apply_quality_profile",
    "apply_render_settings",
    "configure_render_passes",
    "setup_cryptomatte",
    "setup_exr_output",
    "detect_optimal_denoiser",
    "enable_denoising",
    "set_render_engine",
    "set_resolution",
    "set_frame_range",
    "render_frame",
    "render_animation",
    "get_render_settings",
    "apply_pass_preset",

    # Constants
    "APERTURE_MIN",
    "APERTURE_MAX",
    "BLENDER_AVAILABLE",
]

__version__ = "0.2.2"
