"""
Control System Package

A comprehensive system for generating procedural control surface elements.

Modules:
- parameters: Hierarchical parameter resolution
- colors: Color system with LAB interpolation
- profiles: Knob geometry profile definitions
- surface_features: Surface feature configurations (knurling, ribbing, etc.)
- surface_geo: Geometry Nodes builders for surface features
- faders: Fader configuration and presets
- fader_geo: Geometry Nodes builders for faders

Quick Start:
    from lib.control_system import ParameterHierarchy, get_profile, SurfaceFeatures, FaderConfig

    # Get a knob profile
    profile = get_profile("chicken_head")
    params = profile.to_params()

    # Get surface features preset
    features = SurfaceFeatures.from_preset("neve_1073")
    params.update(features.to_params())

    # Get a fader preset
    fader = get_fader_preset("ssl_4000_channel")

    # Resolve parameters with hierarchy
    hierarchy = ParameterHierarchy()
    params = hierarchy.resolve(
        category_preset="consoles/neve_1073",
        instance_params={"base_color": [1, 0, 0]}
    )
"""

from .parameters import (
    ParameterGroup,
    ParameterHierarchy,
    resolve_task_parameters,
)

from .colors import (
    ColorToken,
    ColorSystem,
    create_default_color_system,
)

from .profiles import (
    KnobProfile,
    KnobProfileType,
    get_profile,
    list_profiles,
    create_custom_profile,
    PROFILES,
)

from .surface_features import (
    # Enums
    KnurlPattern,
    IndicatorType,
    GroovePattern,
    # Config classes
    KnurlingConfig,
    RibbingConfig,
    GrooveConfig,
    IndicatorConfig,
    ColletConfig,
    CapConfig,
    BacklightConfig,
    SurfaceFeatures,
    # Presets
    SURFACE_PRESETS,
    list_presets,
    get_preset,
)

from .faders import (
    # Enums
    FaderType,
    FaderKnobStyle,
    TrackStyle,
    ScaleType,
    LEDResponse,
    ScalePosition,
    # Config classes
    FaderKnobConfig,
    TrackConfig,
    ScaleConfig,
    LEDMeterConfig,
    FaderConfig,
    # Presets
    FADER_PRESETS,
    list_fader_presets,
    get_fader_preset,
)

__all__ = [
    # Parameters
    "ParameterGroup",
    "ParameterHierarchy",
    "resolve_task_parameters",

    # Colors
    "ColorToken",
    "ColorSystem",
    "create_default_color_system",

    # Profiles
    "KnobProfile",
    "KnobProfileType",
    "get_profile",
    "list_profiles",
    "create_custom_profile",
    "PROFILES",

    # Surface Features - Enums
    "KnurlPattern",
    "IndicatorType",
    "GroovePattern",

    # Surface Features - Configs
    "KnurlingConfig",
    "RibbingConfig",
    "GrooveConfig",
    "IndicatorConfig",
    "ColletConfig",
    "CapConfig",
    "BacklightConfig",
    "SurfaceFeatures",

    # Surface Features - Presets
    "SURFACE_PRESETS",
    "list_presets",
    "get_preset",

    # Faders - Enums
    "FaderType",
    "FaderKnobStyle",
    "TrackStyle",
    "ScaleType",
    "LEDResponse",
    "ScalePosition",

    # Faders - Configs
    "FaderKnobConfig",
    "TrackConfig",
    "ScaleConfig",
    "LEDMeterConfig",
    "FaderConfig",

    # Faders - Presets
    "FADER_PRESETS",
    "list_fader_presets",
    "get_fader_preset",
]

__version__ = "0.3.0"
