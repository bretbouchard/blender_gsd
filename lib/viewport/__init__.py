"""
Viewport Control System

Provides interactive 3D viewport gizmos and HUD controls for real-time
manipulation of scene objects without navigating menus.

IMPORTANT: All HUDs are DISABLED by default. You must explicitly enable them.

Modules:
- hud_settings: Centralized enable/disable control for all HUDs
- viewport_widgets: Base widget classes and HUD framework
- tool_huds: Pre-built HUD configurations for cameras, lights, materials
- animation_huds: Animation and rigging HUD controls
- vfx_huds: VFX/compositor HUD controls
- editorial_huds: Timeline and editing HUD controls

Quick Start:
    from lib.viewport import (
        HUDSettings,
        enable_hud,
        disable_hud,
        apply_hud_preset,
    )

    # HUDs are disabled by default - enable what you need:
    enable_hud("camera_hud")
    enable_hud("playback_hud")

    # Or use presets:
    apply_hud_preset("minimal")  # camera + playback
    apply_hud_preset("animation")  # rig, shape keys, bones, playback
    apply_hud_preset("vfx")  # color correction, compositor, glare
    apply_hud_preset("none")  # disable all

    # Check if enabled before showing:
    settings = HUDSettings.get_instance()
    if settings.is_enabled("camera_hud"):
        cam_hud = CameraHUD("MainCamera")
        cam_hud.setup()
        cam_hud.show()

    # Available HUD names:
    # - camera_hud, light_hud, hdri_hud, material_hud, render_hud
    # - rig_hud, shape_key_hud, bone_hud, animation_layer_hud
    # - color_correction_hud, compositor_layer_hud, glare_hud,
    #   lens_distortion_hud, motion_blur_hud, cryptomatte_hud
    # - playback_hud, track_control_hud, clip_edit_hud,
    #   transition_hud, marker_hud
    # - gn_modifier_hud, simulation_hud, procedural_params_hud
"""

from .viewport_widgets import (
    # Core
    HUDManager,
    HUDWidget,
    HUDSlider,
    HUDToggle,
    HUDDial,
    # Config
    WidgetTheme,
    GizmoConfig,
    HUDControlConfig,
    HUDPanelConfig,
    GizmoType,
    HUDWidgetType,
    # 3D Gizmos
    CameraGizmoGroup,
    # Registration
    register_camera_widgets,
    unregister_camera_widgets,
    # Presets
    CAMERA_GIZMOS,
    CAMERA_HUD_PANEL,
    # Functions
    create_camera_hud as create_camera_widgets,
    setup_camera_hud,
)

from .tool_huds import (
    # Tool HUDs
    CameraHUD,
    LightHUD,
    MultiLightHUD,
    HDRIHUD,
    MaterialHUD,
    RenderHUD,
    # Auto-HUD
    AutoHUDManager,
    get_auto_hud,
    setup_active_tool_hud,
    # Convenience
    create_lighting_rig_hud,
    create_camera_hud,
    create_light_hud,
    # Themes
    CAMERA_THEME,
    LIGHT_THEME,
    HDRI_THEME,
    MATERIAL_THEME,
    RENDER_THEME,
)

from .animation_huds import (
    # Animation HUDs
    BoneHUD,
    IKFKBlendHUD,
    ConstraintHUD,
    ShapeKeyHUD,
    RigHUD,
    TimelineHUD,
    AnimationLayerHUD,
    # Convenience
    create_rig_hud,
    create_shape_key_hud,
    create_ikfk_hud,
    # Themes
    RIG_THEME,
    BONE_THEME,
    IK_THEME,
    FK_THEME,
    SHAPE_KEY_THEME,
    TIMELINE_THEME,
)

from .vfx_huds import (
    # VFX HUDs
    ColorCorrectionHUD,
    CompositorLayerHUD,
    GlareHUD,
    LensDistortionHUD,
    MotionBlurHUD,
    CryptomatteHUD,
    VFXMasterHUD,
    # Convenience
    create_color_correction_hud,
    create_compositor_layer_hud,
    create_vfx_master_hud,
    create_glare_hud,
    create_lens_distortion_hud,
    create_cryptomatte_hud,
    # Theme
    VFX_THEME,
)

from .editorial_huds import (
    # Editorial HUDs
    PlaybackHUD,
    TrackControlHUD,
    ClipEditHUD,
    TransitionHUD,
    MarkerHUD,
    EditorialMasterHUD,
    # Convenience
    create_playback_hud,
    create_track_control_hud,
    create_clip_edit_hud,
    create_transition_hud,
    create_marker_hud,
    create_editorial_master_hud,
    # Themes
    EDITORIAL_THEME,
    VIDEO_TRACK_THEME,
    AUDIO_TRACK_THEME,
)

from .geometry_huds import (
    # Geometry HUDs
    GNModifierHUD,
    SimulationHUD,
    ProceduralParamsHUD,
    GNMasterHUD,
    # Convenience
    create_gn_modifier_hud,
    create_simulation_hud,
    create_procedural_params_hud,
    create_gn_master_hud,
    # Themes
    GEOMETRY_THEME,
    SIMULATION_THEME,
)

from .hud_settings import (
    # Settings manager
    HUDSettings,
    HUDSetting,
    HUDCategory,
    # Convenience functions
    get_hud_settings,
    enable_hud,
    disable_hud,
    toggle_hud,
    is_hud_enabled,
    apply_hud_preset,
    get_enabled_huds,
    hide_all_huds,
)

__all__ = [
    # Core HUD framework
    "HUDManager",
    "HUDWidget",
    "HUDSlider",
    "HUDToggle",
    "HUDDial",
    # Configuration
    "WidgetTheme",
    "GizmoConfig",
    "HUDControlConfig",
    "HUDPanelConfig",
    "GizmoType",
    "HUDWidgetType",
    # 3D Gizmos
    "CameraGizmoGroup",
    "register_camera_widgets",
    "unregister_camera_widgets",
    # Tool HUDs
    "CameraHUD",
    "LightHUD",
    "MultiLightHUD",
    "HDRIHUD",
    "MaterialHUD",
    "RenderHUD",
    # Auto-HUD
    "AutoHUDManager",
    "get_auto_hud",
    "setup_active_tool_hud",
    # Convenience functions
    "create_camera_widgets",
    "create_camera_hud",
    "create_light_hud",
    "create_lighting_rig_hud",
    "setup_camera_hud",
    # Themes
    "CAMERA_THEME",
    "LIGHT_THEME",
    "HDRI_THEME",
    "MATERIAL_THEME",
    "RENDER_THEME",
    # Presets
    "CAMERA_GIZMOS",
    "CAMERA_HUD_PANEL",
    # Animation HUDs
    "BoneHUD",
    "IKFKBlendHUD",
    "ConstraintHUD",
    "ShapeKeyHUD",
    "RigHUD",
    "TimelineHUD",
    "AnimationLayerHUD",
    # Animation convenience
    "create_rig_hud",
    "create_shape_key_hud",
    "create_ikfk_hud",
    # Animation themes
    "RIG_THEME",
    "BONE_THEME",
    "IK_THEME",
    "FK_THEME",
    "SHAPE_KEY_THEME",
    "TIMELINE_THEME",
    # VFX HUDs
    "ColorCorrectionHUD",
    "CompositorLayerHUD",
    "GlareHUD",
    "LensDistortionHUD",
    "MotionBlurHUD",
    "CryptomatteHUD",
    "VFXMasterHUD",
    # VFX convenience
    "create_color_correction_hud",
    "create_compositor_layer_hud",
    "create_vfx_master_hud",
    "create_glare_hud",
    "create_lens_distortion_hud",
    "create_cryptomatte_hud",
    # VFX theme
    "VFX_THEME",
    # Editorial HUDs
    "PlaybackHUD",
    "TrackControlHUD",
    "ClipEditHUD",
    "TransitionHUD",
    "MarkerHUD",
    "EditorialMasterHUD",
    # Editorial convenience
    "create_playback_hud",
    "create_track_control_hud",
    "create_clip_edit_hud",
    "create_transition_hud",
    "create_marker_hud",
    "create_editorial_master_hud",
    # Editorial themes
    "EDITORIAL_THEME",
    "VIDEO_TRACK_THEME",
    "AUDIO_TRACK_THEME",
    # Geometry HUDs
    "GNModifierHUD",
    "SimulationHUD",
    "ProceduralParamsHUD",
    "GNMasterHUD",
    # Geometry convenience
    "create_gn_modifier_hud",
    "create_simulation_hud",
    "create_procedural_params_hud",
    "create_gn_master_hud",
    # Geometry themes
    "GEOMETRY_THEME",
    "SIMULATION_THEME",
    # HUD Settings
    "HUDSettings",
    "HUDSetting",
    "HUDCategory",
    # HUD Settings convenience
    "get_hud_settings",
    "enable_hud",
    "disable_hud",
    "toggle_hud",
    "is_hud_enabled",
    "apply_hud_preset",
    "get_enabled_huds",
    "hide_all_huds",
]

__version__ = "1.1.0"
