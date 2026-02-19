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
)
from .enums import (
    LensType,
    LightType,
    QualityTier,
    ColorSpace,
    EasingType,
    # Lighting enum
    AreaLightShape,
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

    # Enums
    "LensType",
    "LightType",
    "QualityTier",
    "ColorSpace",
    "EasingType",
    "AreaLightShape",

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

    # Constants
    "APERTURE_MIN",
    "APERTURE_MAX",
    "BLENDER_AVAILABLE",
]

__version__ = "0.1.3"
