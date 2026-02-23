"""
Urban Infrastructure System

Procedural road network generation using L-Systems for city layouts.
Python pre-processing generates JSON that Geometry Nodes consumes for geometry creation.

Architecture:
    LSystemRoads (Python) → JSON Road Network → GN Road Builder → Blender Geometry

Key Components:
    - LSystemRoads: L-system string rewriting for road network generation
    - RoadNetwork: Node and edge data structures
    - RoadGeometry: JSON-driven road mesh generation
    - StreetElements: Signs, lights, furniture placement

Implements REQ-UR-01 through REQ-UR-08.
"""

from .types import (
    NodeType,
    EdgeType,
    RoadType,
    RoadNode,
    RoadEdge,
    RoadNetwork,
    IntersectionType,
    UrbanStyle,
)

from .l_system import (
    LSystemRoads,
    LSystemRule,
    LSystemConfig,
    generate_road_network,
)

from .road_network import (
    RoadNetworkGenerator,
    generate_grid_network,
    generate_organic_network,
    generate_suburban_network,
    list_network_presets,
)

from .road_geometry import (
    RoadGeometryBuilder,
    RoadSegment,
    LaneConfig,
    create_road_geometry_from_network,
)

from .intersections import (
    IntersectionBuilder,
    IntersectionConfig,
    IntersectionGeometry,
    IntersectionShape,
    create_intersection_geometry,
)

from .signage import (
    SignCategory,
    SignShape,
    SignPurpose,
    SignSpec,
    SignInstance,
    SignLibrary,
    SignPlacer,
    REGULATORY_SIGNS,
    WARNING_SIGNS,
    GUIDE_SIGNS,
    create_sign_library,
)

from .lighting import (
    LuminaireType,
    LightSource,
    PoleMaterial,
    LightDistribution,
    PhotometricSpec,
    LuminaireSpec,
    PoleSpec,
    StreetLightInstance,
    LUMINAIRE_CATALOG,
    POLE_CATALOG,
    LightingPlacer,
    create_lighting_placer,
)

from .furniture import (
    FurnitureCategory,
    FurnitureMaterial,
    MountingType,
    FurnitureSpec,
    FurnitureInstance,
    BENCH_CATALOG,
    BOLLARD_CATALOG,
    PLANTER_CATALOG,
    TRASH_RECEPTACLE_CATALOG,
    BIKE_RACK_CATALOG,
    BUS_SHELTER_CATALOG,
    UTILITY_CATALOG,
    FURNITURE_CATALOG,
    FurniturePlacer,
    create_furniture_placer,
)

from .markings import (
    MarkingColor,
    MarkingType,
    MarkingMaterial,
    MarkingSpec,
    MarkingInstance,
    CrosswalkGeometry,
    LANE_LINE_MARKINGS,
    CROSSWALK_MARKINGS,
    SYMBOL_MARKINGS,
    SPECIAL_MARKINGS,
    MARKING_CATALOG,
    MarkingPlacer,
    create_marking_placer,
)


# =============================================================================
# MODULE INFO
# =============================================================================

__version__ = "1.0.0"
__author__ = "Bret Bouchard"
__description__ = "Procedural urban infrastructure with L-System road networks"

__all__ = [
    # Types
    "NodeType",
    "EdgeType",
    "RoadType",
    "RoadNode",
    "RoadEdge",
    "RoadNetwork",
    "IntersectionType",
    "UrbanStyle",
    # L-System
    "LSystemRoads",
    "LSystemRule",
    "LSystemConfig",
    "generate_road_network",
    # Road Network
    "RoadNetworkGenerator",
    "generate_grid_network",
    "generate_organic_network",
    "generate_suburban_network",
    "list_network_presets",
    # Road Geometry
    "RoadGeometryBuilder",
    "RoadSegment",
    "LaneConfig",
    "create_road_geometry_from_network",
    # Intersections
    "IntersectionBuilder",
    "IntersectionConfig",
    "IntersectionGeometry",
    "IntersectionShape",
    "create_intersection_geometry",
    # Signage
    "SignCategory",
    "SignShape",
    "SignPurpose",
    "SignSpec",
    "SignInstance",
    "SignLibrary",
    "SignPlacer",
    "REGULATORY_SIGNS",
    "WARNING_SIGNS",
    "GUIDE_SIGNS",
    "create_sign_library",
    # Lighting
    "LuminaireType",
    "LightSource",
    "PoleMaterial",
    "LightDistribution",
    "PhotometricSpec",
    "LuminaireSpec",
    "PoleSpec",
    "StreetLightInstance",
    "LUMINAIRE_CATALOG",
    "POLE_CATALOG",
    "LightingPlacer",
    "create_lighting_placer",
    # Furniture
    "FurnitureCategory",
    "FurnitureMaterial",
    "MountingType",
    "FurnitureSpec",
    "FurnitureInstance",
    "BENCH_CATALOG",
    "BOLLARD_CATALOG",
    "PLANTER_CATALOG",
    "TRASH_RECEPTACLE_CATALOG",
    "BIKE_RACK_CATALOG",
    "BUS_SHELTER_CATALOG",
    "UTILITY_CATALOG",
    "FURNITURE_CATALOG",
    "FurniturePlacer",
    "create_furniture_placer",
    # Markings
    "MarkingColor",
    "MarkingType",
    "MarkingMaterial",
    "MarkingSpec",
    "MarkingInstance",
    "CrosswalkGeometry",
    "LANE_LINE_MARKINGS",
    "CROSSWALK_MARKINGS",
    "SYMBOL_MARKINGS",
    "SPECIAL_MARKINGS",
    "MARKING_CATALOG",
    "MarkingPlacer",
    "create_marking_placer",
]
