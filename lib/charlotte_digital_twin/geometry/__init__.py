"""
Charlotte Digital Twin Geometry Module

Converts geographic data to Blender geometry for Charlotte NC scenes.

Modules:
- types: Core data types (GeometryConfig, SceneOrigin, etc.)
- coordinates: WGS84 to world coordinate transformation
- scale: Scene scale management
- road_processor: OSM road data processing
- road_geometry: Road mesh generation
- road_materials: Road material mapping
- road_uv: Road UV coordinate generation
- building_geometry: Building mesh generation
- building_materials: Building material mapping
- poi_geometry: POI marker generation
- scene_assembly: Scene orchestration

Usage:
    from lib.charlotte_digital_twin.geometry import (
        # Types
        GeometryConfig,
        SceneOrigin,
        SceneBounds,
        WorldCoordinate,
        RoadSegment,
        BuildingFootprint,
        POIMarker,
        DetailLevel,
        RoadType,
        BuildingType,
        POICategory,

        # Coordinates
        CoordinateTransformer,
        CHARLOTTE_ORIGINS,

        # Scale
        ScaleManager,
        ScalePreset,

        # Generators
        RoadGeometryGenerator,
        BuildingGeometryGenerator,
        POIGeometryGenerator,
        SceneAssembler,

        # Constants
        ROAD_WIDTHS,
        ROAD_LANES,
    )

    # Create configuration
    config = GeometryConfig(
        origin=SceneOrigin(lat=35.2271, lon=-80.8431),
        detail_level=DetailLevel.STANDARD,
    )

    # Transform coordinates
    transformer = CoordinateTransformer(config)
    world = transformer.latlon_to_world(35.2280, -80.8420)

    # Build complete scene
    assembler = SceneAssembler(config)
    scene = assembler.build_scene(osm_data)
"""

__version__ = "0.1.0"

# Core types
from .types import (
    DetailLevel,
    RoadType,
    BuildingType,
    POICategory,
    SceneOrigin,
    GeometryConfig,
    WorldCoordinate,
    GeoCoordinate,
    UTMCoordinate,
    RoadSegment,
    BuildingFootprint,
    POIMarker,
    SceneBounds,
    ROAD_WIDTHS,
    ROAD_LANES,
)

# Coordinate system
from .coordinates import (
    CoordinateTransformer,
    CHARLOTTE_ORIGINS,
)

# Scale management
from .scale import (
    ScalePreset,
    ScaleConfig,
    ScaleManager,
    ROAD_WIDTHS_METERS,
    BUILDING_HEIGHTS_METERS,
    CHARLOTTE_BUILDING_HEIGHTS,
)

# Road processing
from .road_processor import (
    RoadNode,
    Intersection,
    RoadNetworkProcessor,
)

# Road geometry
from .road_geometry import RoadGeometryGenerator

# Road materials
from .road_materials import (
    RoadMaterialMapper,
    MaterialProperties,
    SURFACE_MATERIALS,
    ROAD_TYPE_ADJUSTMENTS,
)

# Road UV
from .road_uv import (
    RoadUVGenerator,
    UVConfig,
)

# Building geometry
from .building_geometry import BuildingGeometryGenerator

# Building materials
from .building_materials import (
    BuildingMaterialMapper,
    BuildingMaterialProperties,
    BUILDING_MATERIALS,
    BUILDING_TYPE_MATERIALS,
)

# POI geometry
from .poi_geometry import POIGeometryGenerator

# Scene assembly
from .scene_assembly import (
    SceneAssembler,
    SceneLayer,
    SceneStats,
)


__all__ = [
    # Version
    "__version__",

    # Enums
    "DetailLevel",
    "RoadType",
    "BuildingType",
    "POICategory",
    "ScalePreset",

    # Data classes
    "SceneOrigin",
    "GeometryConfig",
    "WorldCoordinate",
    "GeoCoordinate",
    "UTMCoordinate",
    "RoadSegment",
    "BuildingFootprint",
    "POIMarker",
    "SceneBounds",
    "ScaleConfig",
    "MaterialProperties",
    "BuildingMaterialProperties",
    "UVConfig",
    "SceneLayer",
    "SceneStats",

    # Classes
    "CoordinateTransformer",
    "ScaleManager",
    "RoadNetworkProcessor",
    "RoadGeometryGenerator",
    "RoadMaterialMapper",
    "RoadUVGenerator",
    "BuildingGeometryGenerator",
    "BuildingMaterialMapper",
    "POIGeometryGenerator",
    "SceneAssembler",

    # Data classes (road network)
    "RoadNode",
    "Intersection",

    # Constants
    "ROAD_WIDTHS",
    "ROAD_LANES",
    "ROAD_WIDTHS_METERS",
    "BUILDING_HEIGHTS_METERS",
    "CHARLOTTE_BUILDING_HEIGHTS",
    "CHARLOTTE_ORIGINS",
    "SURFACE_MATERIALS",
    "ROAD_TYPE_ADJUSTMENTS",
    "BUILDING_MATERIALS",
    "BUILDING_TYPE_MATERIALS",
]
