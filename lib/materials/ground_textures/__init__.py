"""
Ground Texture Painting System

Layered texture system for ground materials with procedural and painted masks.
Based on Polygon Runway texture painting workflow.

Features:
- Multi-layer texture blending (asphalt + dirt + markings)
- Painted mask workflow with grunge brushes
- Procedural mask generation (noise, voronoi, edge wear)
- Node Wrangler-compatible texture import
- Sanctus material system integration
- Urban road system integration

Usage:
    from lib.materials.ground_textures import (
        # Texture Layers
        TextureLayerType,
        BlendMode,
        MaskType,
        TextureLayer,
        LayeredTextureConfig,
        LayeredTextureManager,
        create_asphalt_with_dirt,
        create_road_material,

        # Painted Masks
        GrungeBrush,
        MaskTexture,
        PaintedMaskWorkflow,
        create_grunge_brush,
        generate_road_dirt_mask,

        # Sanctus Integration
        RoadWeatheringLevel,
        RoadEnvironment,
        WeatheredGroundConfig,
        SanctusGroundIntegration,
        create_weathered_road_material,

        # Urban Integration
        RoadSurfaceType,
        RoadZoneType,
        RoadMaterialConfig,
        UrbanRoadMaterialManager,
        create_road_surface_material,
        apply_materials_to_road_network,
    )

    # Create layered asphalt with dirt
    config = create_asphalt_with_dirt(dirt_amount=0.4)
    manager = LayeredTextureManager()
    material = manager.apply_to_material(config)

    # Create weathered road material
    weathered = create_weathered_road_material(
        base_type="asphalt",
        wear_level="heavy",
        wetness=0.2
    )
    integration = SanctusGroundIntegration()
    road_material = integration.create_material(weathered)

    # Generate road dirt mask
    mask = generate_road_dirt_mask(
        resolution=2048,
        dirt_amount=0.5,
        seed=42
    )
"""

from typing import Dict, Any

__version__ = "1.0.0"
__author__ = "Bret Bouchard"

# Texture Layers
from .texture_layers import (
    # Enums
    TextureLayerType,
    BlendMode,
    MaskType,
    # Dataclasses
    TextureMaps,
    TextureLayer,
    PaintedMask,
    LayeredTextureConfig,
    # Manager
    LayeredTextureManager,
    # Presets
    GROUND_TEXTURE_PRESETS,
    # Functions
    create_asphalt_with_dirt,
    create_road_material,
    create_painted_marking_material,
)

# Painted Masks
from .painted_masks import (
    # Enums
    BrushType,
    BrushBlendMode,
    MaskEdgeMode,
    # Dataclasses
    GrungeBrush,
    MaskTexture,
    PaintStroke,
    # Manager
    PaintedMaskWorkflow,
    # Presets
    GRUNGE_BRUSH_PRESETS,
    # Functions
    create_grunge_brush,
    generate_road_dirt_mask,
    create_wear_mask,
)

# Sanctus Integration
from .sanctus_integration import (
    # Enums
    RoadWeatheringLevel,
    RoadEnvironment,
    # Dataclasses
    WeatheredGroundConfig,
    # Manager
    SanctusGroundIntegration,
    # Presets
    ENVIRONMENT_PRESETS,
    WEATHERING_LEVEL_MULTIPLIERS,
    # Functions
    create_weathered_road_material,
    apply_road_weathering,
    get_environment_preset,
)

# Urban Integration
from .urban_integration import (
    # Enums
    RoadSurfaceType,
    RoadZoneType,
    # Dataclasses
    RoadMaterialConfig,
    # Manager
    UrbanRoadMaterialManager,
    # Presets
    ROAD_SURFACE_PRESETS,
    ZONE_CONFIGS,
    # Functions
    create_road_surface_material,
    apply_materials_to_road_network,
)

# Geometry Nodes Integration
from .gn_integration import (
    # Enums
    GNSamplingStrategy,
    GNMaterialAssignment,
    # Dataclasses
    GNMaskNodeGroup,
    GNLayerConfig,
    MaterialSlotConfig,
    GNOutputFormat,
    # Functions
    convert_to_gn_format,
    create_road_gn_config,
    # Classes
    GNTextureIntegrator,
    # Presets
    ROAD_ZONE_PRESETS,
)


__all__ = [
    # Version
    "__version__",
    "__author__",

    # Texture Layers - Enums
    "TextureLayerType",
    "BlendMode",
    "MaskType",

    # Texture Layers - Dataclasses
    "TextureMaps",
    "TextureLayer",
    "PaintedMask",
    "LayeredTextureConfig",

    # Texture Layers - Manager
    "LayeredTextureManager",

    # Texture Layers - Presets
    "GROUND_TEXTURE_PRESETS",

    # Texture Layers - Functions
    "create_asphalt_with_dirt",
    "create_road_material",
    "create_painted_marking_material",

    # Painted Masks - Enums
    "BrushType",
    "BrushBlendMode",
    "MaskEdgeMode",

    # Painted Masks - Dataclasses
    "GrungeBrush",
    "MaskTexture",
    "PaintStroke",

    # Painted Masks - Manager
    "PaintedMaskWorkflow",

    # Painted Masks - Presets
    "GRUNGE_BRUSH_PRESETS",

    # Painted Masks - Functions
    "create_grunge_brush",
    "generate_road_dirt_mask",
    "create_wear_mask",

    # Sanctus Integration - Enums
    "RoadWeatheringLevel",
    "RoadEnvironment",

    # Sanctus Integration - Dataclasses
    "WeatheredGroundConfig",

    # Sanctus Integration - Manager
    "SanctusGroundIntegration",

    # Sanctus Integration - Presets
    "ENVIRONMENT_PRESETS",
    "WEATHERING_LEVEL_MULTIPLIERS",

    # Sanctus Integration - Functions
    "create_weathered_road_material",
    "apply_road_weathering",
    "get_environment_preset",

    # Urban Integration - Enums
    "RoadSurfaceType",
    "RoadZoneType",

    # Urban Integration - Dataclasses
    "RoadMaterialConfig",

    # Urban Integration - Manager
    "UrbanRoadMaterialManager",

    # Urban Integration - Presets
    "ROAD_SURFACE_PRESETS",
    "ZONE_CONFIGS",

    # Urban Integration - Functions
    "create_road_surface_material",
    "apply_materials_to_road_network",

    # GN Integration - Enums
    "GNSamplingStrategy",
    "GNMaterialAssignment",

    # GN Integration - Dataclasses
    "GNMaskNodeGroup",
    "GNLayerConfig",
    "MaterialSlotConfig",
    "GNOutputFormat",

    # GN Integration - Functions
    "convert_to_gn_format",
    "create_road_gn_config",

    # GN Integration - Classes
    "GNTextureIntegrator",
]


def get_version() -> str:
    """Get the current version of the Ground Texture System."""
    return __version__


def get_module_info() -> Dict[str, Any]:
    """Get information about available components."""
    return {
        "version": __version__,
        "texture_layer_types": list(TextureLayerType),
        "blend_modes": list(BlendMode),
        "mask_types": list(MaskType),
        "brush_types": list(BrushType),
        "road_weathering_levels": list(RoadWeatheringLevel),
        "road_environments": list(RoadEnvironment),
        "road_surface_types": list(RoadSurfaceType),
        "road_zone_types": list(RoadZoneType),
        "preset_count": {
            "ground_textures": len(GROUND_TEXTURE_PRESETS),
            "grunge_brushes": len(GRUNGE_BRUSH_PRESETS),
            "environments": len(ENVIRONMENT_PRESETS),
            "road_surfaces": len(ROAD_SURFACE_PRESETS),
            "road_zones": len(ZONE_CONFIGS),
        },
    }


