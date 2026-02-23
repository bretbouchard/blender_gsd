"""
Materials Module

Comprehensive material system with:
- Sanctus: Procedural materials with damage, weathering, and pattern generation
- Ground Textures: Layered ground materials with painted masks

Usage:
    # Sanctus materials
    from lib.materials.sanctus import (
        SanctusShaderTools,
        SanctusMaterials,
        WeatheringTools,
        DamageTools,
        PatternGenerator,
    )

    # Ground texture system
    from lib.materials.ground_textures import (
        LayeredTextureManager,
        PaintedMaskWorkflow,
        SanctusGroundIntegration,
        UrbanRoadMaterialManager,
        create_weathered_road_material,
    )
"""

# Sanctus is the main procedural materials library
from .sanctus import (
    SanctusShaderTools,
    SanctusMaterials,
    SanctusBaker,
    SanctusGNGenerator,
    DamageGenerator,
    WeatheringGenerator,
    PatternGenerator,
    DamageTools,
    WeatheringTools,
    ShaderToolRegistry,
    ToolCategory,
    PerformanceRating,
    MaterialCategory,
    MaterialPreset,
    MATERIAL_PRESETS,
    DamageType,
    DamageParameters,
    WeatheringType,
    WeatheringParameters,
    PatternType,
    PatternParameters,
    BakeChannel,
    BakeSettings,
    ExportEngine,
    GNDamageType,
    GNWearType,
)

# Ground textures is the layered texture system
from .ground_textures import (
    # Texture Layers
    TextureLayerType,
    BlendMode,
    MaskType,
    TextureMaps,
    TextureLayer,
    PaintedMask,
    LayeredTextureConfig,
    LayeredTextureManager,
    GROUND_TEXTURE_PRESETS,
    create_asphalt_with_dirt,
    create_road_material,
    create_painted_marking_material,

    # Painted Masks
    BrushType,
    BrushBlendMode,
    MaskEdgeMode,
    GrungeBrush,
    MaskTexture,
    PaintStroke,
    PaintedMaskWorkflow,
    GRUNGE_BRUSH_PRESETS,
    create_grunge_brush,
    generate_road_dirt_mask,
    create_wear_mask,

    # Sanctus Integration
    RoadWeatheringLevel,
    RoadEnvironment,
    WeatheredGroundConfig,
    SanctusGroundIntegration,
    ENVIRONMENT_PRESETS,
    WEATHERING_LEVEL_MULTIPLIERS,
    create_weathered_road_material,
    apply_road_weathering,
    get_environment_preset,

    # Urban Integration
    RoadSurfaceType,
    RoadZoneType,
    RoadMaterialConfig,
    UrbanRoadMaterialManager,
    ROAD_SURFACE_PRESETS,
    ZONE_CONFIGS,
    create_road_surface_material,
    apply_materials_to_road_network,
)


__all__ = [
    # Sanctus - Main API
    "SanctusShaderTools",
    "SanctusMaterials",
    "SanctusBaker",
    "SanctusGNGenerator",
    # Sanctus - Generators
    "DamageGenerator",
    "WeatheringGenerator",
    "PatternGenerator",
    # Sanctus - Tools
    "DamageTools",
    "WeatheringTools",
    "ShaderToolRegistry",
    # Sanctus - Enums
    "ToolCategory",
    "PerformanceRating",
    "MaterialCategory",
    "MaterialPreset",
    "DamageType",
    "WeatheringType",
    "PatternType",
    "BakeChannel",
    "GNDamageType",
    "GNWearType",
    # Sanctus - Data
    "MATERIAL_PRESETS",
    "DamageParameters",
    "WeatheringParameters",
    "PatternParameters",
    "BakeSettings",
    "ExportEngine",

    # Ground Textures - Enums
    "TextureLayerType",
    "BlendMode",
    "MaskType",
    "BrushType",
    "BrushBlendMode",
    "MaskEdgeMode",
    "RoadWeatheringLevel",
    "RoadEnvironment",
    "RoadSurfaceType",
    "RoadZoneType",

    # Ground Textures - Dataclasses
    "TextureMaps",
    "TextureLayer",
    "PaintedMask",
    "LayeredTextureConfig",
    "GrungeBrush",
    "MaskTexture",
    "PaintStroke",
    "WeatheredGroundConfig",
    "RoadMaterialConfig",

    # Ground Textures - Managers
    "LayeredTextureManager",
    "PaintedMaskWorkflow",
    "SanctusGroundIntegration",
    "UrbanRoadMaterialManager",

    # Ground Textures - Presets
    "GROUND_TEXTURE_PRESETS",
    "GRUNGE_BRUSH_PRESETS",
    "ENVIRONMENT_PRESETS",
    "WEATHERING_LEVEL_MULTIPLIERS",
    "ROAD_SURFACE_PRESETS",
    "ZONE_CONFIGS",

    # Ground Textures - Functions
    "create_asphalt_with_dirt",
    "create_road_material",
    "create_painted_marking_material",
    "create_grunge_brush",
    "generate_road_dirt_mask",
    "create_wear_mask",
    "create_weathered_road_material",
    "apply_road_weathering",
    "get_environment_preset",
    "create_road_surface_material",
    "apply_materials_to_road_network",
]

__version__ = "1.0.0"
