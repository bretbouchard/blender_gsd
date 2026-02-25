"""
SD Projection Mapping System

Stable Diffusion texture projection onto 3D geometry with
drifting/slipping animation effects (Arcane-style painted look).

Modules:
    sd_projection: Core projection mapping with ControlNet
    style_blender: Multi-style blending and drift animation
    building_projection: Building-specific projection with LOD

Quick Start:
    from lib.sd_projection import (
        SDProjectionMapper,
        StyleConfig,
        BuildingProjector,
        project_onto_buildings,
    )

    # Simple usage
    results = project_onto_buildings(
        camera=scene.camera,
        buildings=city_buildings,
        style="cyberpunk_night",
        prompt="neon lit cyberpunk city, rain",
        drift_speed=0.1,
    )

    # Advanced usage with full control
    config = StyleConfig(
        prompt="surreal dreamscape",
        drift_enabled=True,
        drift_speed=0.15,
        drift_direction=(1.0, 0.5),
    )
    mapper = SDProjectionMapper(config)
    result = mapper.project_onto_objects(
        camera=scene.camera,
        objects=buildings,
    )

Style Presets:
    - cyberpunk_night: Neon-lit cyberpunk with rain
    - arcane_painted: Arcane-style hand-painted look
    - trippy_drift: Psychedelic with heavy drift
    - noir_gritty: Film noir with rain streaks
    - anime_cel: Clean cel-shaded anime style
"""

from .sd_projection import (
    # Main classes
    SDProjectionMapper,
    SDClient,
    PassGenerator,

    # Configuration
    StyleConfig,
    StyleModel,
    ControlNetConfig,

    # Enums
    ControlNetType,
    ProjectionMode,
    SDBackend,

    # Results
    ProjectionResult,

    # Convenience
    create_projection_mapper,
)

from .style_blender import (
    # Main classes
    StyleBlender,
    StyleAnimator,

    # Configuration
    DriftConfig,
    StyleBlendConfig,
    StyleLayer,

    # Enums
    BlendMode,
    DriftPattern,

    # Patterns
    DriftPatternGenerator,

    # Convenience
    create_drift_material,
    create_style_crossfade,
)

from .building_projection import (
    # Main class
    BuildingProjector,

    # Configuration
    BuildingProjectionConfig,
    BuildingInfo,

    # Enums
    BuildingVisibility,
    BuildingLOD,

    # Presets
    STYLE_PRESETS,
    get_style_preset,
    list_style_presets,

    # Convenience
    project_onto_buildings,
)


__all__ = [
    # Core projection
    "SDProjectionMapper",
    "SDClient",
    "PassGenerator",
    "StyleConfig",
    "StyleModel",
    "ControlNetConfig",
    "ControlNetType",
    "ProjectionMode",
    "SDBackend",
    "ProjectionResult",
    "create_projection_mapper",

    # Style blending
    "StyleBlender",
    "StyleAnimator",
    "DriftConfig",
    "StyleBlendConfig",
    "StyleLayer",
    "BlendMode",
    "DriftPattern",
    "DriftPatternGenerator",
    "create_drift_material",
    "create_style_crossfade",

    # Building projection
    "BuildingProjector",
    "BuildingProjectionConfig",
    "BuildingInfo",
    "BuildingVisibility",
    "BuildingLOD",
    "STYLE_PRESETS",
    "get_style_preset",
    "list_style_presets",
    "project_onto_buildings",
]
