"""
MSG-1998 Road System

Complete NYC 1998 road system with:
- Road classification (arterial, collector, local, hero)
- Intersection detection and geometry
- Sidewalks, curbs, and pavement
- Lane markings and crosswalks
- Street furniture distribution
- LOD system for city-wide vs hero blocks
"""

from .classification import (
    RoadClass,
    RoadClassifier,
    NYCRoadSpecs,
    classify_road,
    get_road_spec,
)
from .intersections import (
    IntersectionDetector,
    IntersectionBuilder,
    IntersectionCluster,
)
from .geometry import (
    RoadGeometryBuilder,
    PavementBuilder,
    CurbBuilder,
    SidewalkBuilder,
)
from .markings import (
    MarkingBuilder,
    MarkingType,
    CrosswalkBuilder,
)
from .furniture import (
    FurnitureDistributor,
    ManholePlacer,
    StreetFurniture,
)
from .processor import MSGRoadProcessor

__all__ = [
    # Classification
    "RoadClass",
    "RoadClassifier",
    "NYCRoadSpecs",
    "classify_road",
    "get_road_spec",
    # Intersections
    "IntersectionDetector",
    "IntersectionBuilder",
    "IntersectionCluster",
    # Geometry
    "RoadGeometryBuilder",
    "PavementBuilder",
    "CurbBuilder",
    "SidewalkBuilder",
    # Markings
    "MarkingBuilder",
    "MarkingType",
    "CrosswalkBuilder",
    # Furniture
    "FurnitureDistributor",
    "ManholePlacer",
    "StreetFurniture",
    # Main processor
    "MSGRoadProcessor",
]

__version__ = "0.1.0"
