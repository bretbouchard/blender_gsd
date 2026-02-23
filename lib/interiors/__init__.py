"""
Interior Layout System

Procedural interior generation using BSP (Binary Space Partitioning) for floor plans.
Python pre-processing generates JSON that Geometry Nodes consumes for geometry creation.

Architecture:
    BSPSolver (Python) → JSON Floor Plan → GN Wall Builder → Blender Geometry

Key Components:
    - BSPSolver: Recursive subdivision algorithm for floor plan generation
    - FloorPlan: Room and connection data structures
    - WallBuilder: JSON-driven wall geometry generation
    - FurniturePlacer: Ergonomic furniture placement

Implements REQ-IL-01 through REQ-IL-08.
"""

from .types import (
    RoomType,
    Room,
    Connection,
    DoorSpec,
    WindowSpec,
    FloorPlan,
    InteriorStyle,
    FurniturePlacement,
)

from .bsp_solver import (
    BSPSolver,
    BSPNode,
    BSPSplitDirection,
)

from .floor_plan import (
    FloorPlanGenerator,
    generate_apartment_floor_plan,
    generate_office_floor_plan,
    generate_house_floor_plan,
    list_floor_plan_presets,
)

from .walls import (
    WallBuilder,
    WallSegment,
    WallOpening,
    create_wall_geometry_from_plan,
)

from .flooring import (
    FlooringGenerator,
    FlooringPattern,
    FlooringConfig,
    create_flooring_from_plan,
)

from .furniture import (
    FurniturePlacer,
    FurnitureCategory,
    FurnitureItem,
    FurnitureLayout,
    place_furniture_in_room,
)

from .details import (
    InteriorDetails,
    MoldingType,
    MoldingConfig,
    FixtureType,
    FixtureConfig,
    add_interior_details,
)

from .room_types import (
    RoomTypeConfig,
    RoomRequirements,
    get_room_requirements,
    get_room_config,
    list_room_types,
)


# =============================================================================
# MODULE INFO
# =============================================================================

__version__ = "1.0.0"
__author__ = "Bret Bouchard"
__description__ = "Procedural interior layout generation with BSP floor plans"

# Module-level convenience
__all__ = [
    # Types
    "RoomType",
    "Room",
    "Connection",
    "DoorSpec",
    "WindowSpec",
    "FloorPlan",
    "InteriorStyle",
    "FurniturePlacement",
    # BSP
    "BSPSolver",
    "BSPNode",
    "BSPSplitDirection",
    # Floor Plan
    "FloorPlanGenerator",
    "generate_apartment_floor_plan",
    "generate_office_floor_plan",
    "generate_house_floor_plan",
    "list_floor_plan_presets",
    # Walls
    "WallBuilder",
    "WallSegment",
    "WallOpening",
    "create_wall_geometry_from_plan",
    # Flooring
    "FlooringGenerator",
    "FlooringPattern",
    "FlooringConfig",
    "create_flooring_from_plan",
    # Furniture
    "FurniturePlacer",
    "FurnitureCategory",
    "FurnitureItem",
    "FurnitureLayout",
    "place_furniture_in_room",
    # Details
    "InteriorDetails",
    "MoldingType",
    "MoldingConfig",
    "FixtureType",
    "FixtureConfig",
    "add_interior_details",
    # Room Types
    "RoomTypeConfig",
    "RoomRequirements",
    "get_room_requirements",
    "get_room_config",
    "list_room_types",
]
