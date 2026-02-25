"""
Charlotte Digital Twin - Library Package
"""

from .elevation import (
    ElevationManager,
    BridgeElevationCalculator,
    ElevationValidator,
    ElevationReport,
)

from .building_processor import (
    BuildingClassifier,
    NeighborhoodDetector,
    BlockDetector,
    BuildingData,
)

from .road_classification import (
    RoadClass,
    CharlotteRoadSpec,
    RoadClassifier,
    CHARLOTTE_ROAD_SPECS,
)

from .intersection_detector import (
    IntersectionType,
    RoadEndpoint,
    IntersectionCluster,
    IntersectionDetector,
)

from .lod_system import (
    LODLevel,
    LODSpec,
    LODAssigner,
    LODOrganizer,
    LOD_SPECS,
)

__all__ = [
    # Elevation
    'ElevationManager',
    'BridgeElevationCalculator',
    'ElevationValidator',
    'ElevationReport',

    # Buildings
    'BuildingClassifier',
    'NeighborhoodDetector',
    'BlockDetector',
    'BuildingData',

    # Roads
    'RoadClass',
    'CharlotteRoadSpec',
    'RoadClassifier',
    'CHARLOTTE_ROAD_SPECS',

    # Intersections
    'IntersectionType',
    'RoadEndpoint',
    'IntersectionCluster',
    'IntersectionDetector',

    # LOD
    'LODLevel',
    'LODSpec',
    'LODAssigner',
    'LODOrganizer',
    'LOD_SPECS',
]
