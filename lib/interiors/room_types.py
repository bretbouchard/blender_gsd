"""
Room Types

Room type definitions with requirements and default configurations.
Provides room-specific settings and constraints.

Implements REQ-IL-01: Room type configuration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

from .types import RoomType


@dataclass
class RoomRequirements:
    """
    Room requirements and constraints.

    Attributes:
        min_width: Minimum room width in meters
        min_depth: Minimum room depth in meters
        min_height: Minimum ceiling height in meters
        min_area: Minimum room area in square meters
        requires_window: Whether room requires exterior window
        requires_closet: Whether room requires closet access
        max_doors: Maximum number of doors
        typical_doors: Typical number of doors
    """
    min_width: float = 2.5
    min_depth: float = 2.5
    min_height: float = 2.4
    min_area: float = 6.0
    requires_window: bool = False
    requires_closet: bool = False
    max_doors: int = 3
    typical_doors: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_width": self.min_width,
            "min_depth": self.min_depth,
            "min_height": self.min_height,
            "min_area": self.min_area,
            "requires_window": self.requires_window,
            "requires_closet": self.requires_closet,
            "max_doors": self.max_doors,
            "typical_doors": self.typical_doors,
        }


@dataclass
class RoomTypeConfig:
    """
    Complete room type configuration.

    Attributes:
        room_type: Room type identifier
        name: Human-readable name
        description: Description of room purpose
        requirements: Room size and feature requirements
        default_materials: Default material assignments
        typical_placement: Where room is typically placed
        adjacency_requirements: Required adjacent rooms
    """
    room_type: str = "living_room"
    name: str = "Living Room"
    description: str = "Main living space"
    requirements: RoomRequirements = field(default_factory=RoomRequirements)
    default_materials: Dict[str, str] = field(default_factory=dict)
    typical_placement: str = "front"
    adjacency_requirements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "room_type": self.room_type,
            "name": self.name,
            "description": self.description,
            "requirements": self.requirements.to_dict(),
            "default_materials": self.default_materials,
            "typical_placement": self.typical_placement,
            "adjacency_requirements": self.adjacency_requirements,
        }


# Room type configurations
ROOM_TYPE_CONFIGS: Dict[str, RoomTypeConfig] = {
    "living_room": RoomTypeConfig(
        room_type="living_room",
        name="Living Room",
        description="Main living and entertainment space",
        requirements=RoomRequirements(
            min_width=3.5,
            min_depth=4.0,
            min_height=2.6,
            min_area=14.0,
            requires_window=True,
            max_doors=4,
            typical_doors=2,
        ),
        default_materials={
            "floor": "hardwood_oak",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="front",
        adjacency_requirements=["kitchen", "dining_room", "hallway"],
    ),

    "master_bedroom": RoomTypeConfig(
        room_type="master_bedroom",
        name="Master Bedroom",
        description="Primary bedroom with en-suite potential",
        requirements=RoomRequirements(
            min_width=3.5,
            min_depth=3.5,
            min_height=2.6,
            min_area=12.0,
            requires_window=True,
            requires_closet=True,
            max_doors=3,
            typical_doors=2,
        ),
        default_materials={
            "floor": "carpet_neutral",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="rear",
        adjacency_requirements=["master_bathroom", "closet"],
    ),

    "bedroom": RoomTypeConfig(
        room_type="bedroom",
        name="Bedroom",
        description="Secondary bedroom",
        requirements=RoomRequirements(
            min_width=3.0,
            min_depth=3.0,
            min_height=2.4,
            min_area=9.0,
            requires_window=True,
            requires_closet=True,
            max_doors=2,
            typical_doors=1,
        ),
        default_materials={
            "floor": "carpet_neutral",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="side",
        adjacency_requirements=["hallway", "bathroom"],
    ),

    "kitchen": RoomTypeConfig(
        room_type="kitchen",
        name="Kitchen",
        description="Food preparation space",
        requirements=RoomRequirements(
            min_width=2.5,
            min_depth=2.5,
            min_height=2.4,
            min_area=7.0,
            requires_window=True,
            max_doors=3,
            typical_doors=2,
        ),
        default_materials={
            "floor": "tile_ceramic",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="rear",
        adjacency_requirements=["dining_room", "living_room", "pantry"],
    ),

    "dining_room": RoomTypeConfig(
        room_type="dining_room",
        name="Dining Room",
        description="Formal dining space",
        requirements=RoomRequirements(
            min_width=3.0,
            min_depth=3.5,
            min_height=2.6,
            min_area=10.0,
            requires_window=False,
            max_doors=3,
            typical_doors=2,
        ),
        default_materials={
            "floor": "hardwood_oak",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="front",
        adjacency_requirements=["kitchen", "living_room"],
    ),

    "bathroom": RoomTypeConfig(
        room_type="bathroom",
        name="Bathroom",
        description="Full bathroom with tub/shower",
        requirements=RoomRequirements(
            min_width=1.8,
            min_depth=2.0,
            min_height=2.4,
            min_area=4.0,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "tile_ceramic",
            "wall": "tile_ceramic",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=["hallway", "bedroom"],
    ),

    "master_bathroom": RoomTypeConfig(
        room_type="master_bathroom",
        name="Master Bathroom",
        description="En-suite bathroom for master bedroom",
        requirements=RoomRequirements(
            min_width=2.5,
            min_depth=2.5,
            min_height=2.4,
            min_area=6.0,
            requires_window=False,
            max_doors=2,
            typical_doors=1,
        ),
        default_materials={
            "floor": "tile_marble",
            "wall": "tile_marble",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=["master_bedroom"],
    ),

    "half_bath": RoomTypeConfig(
        room_type="half_bath",
        name="Half Bath",
        description="Powder room with toilet and sink only",
        requirements=RoomRequirements(
            min_width=1.2,
            min_depth=1.5,
            min_height=2.4,
            min_area=2.0,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "tile_ceramic",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=["hallway", "foyer"],
    ),

    "office": RoomTypeConfig(
        room_type="office",
        name="Office",
        description="Home office or study",
        requirements=RoomRequirements(
            min_width=2.5,
            min_depth=2.5,
            min_height=2.4,
            min_area=7.0,
            requires_window=True,
            max_doors=2,
            typical_doors=1,
        ),
        default_materials={
            "floor": "hardwood_oak",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="front",
        adjacency_requirements=["hallway"],
    ),

    "laundry": RoomTypeConfig(
        room_type="laundry",
        name="Laundry Room",
        description="Washer and dryer space",
        requirements=RoomRequirements(
            min_width=1.5,
            min_depth=1.5,
            min_height=2.4,
            min_area=2.5,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "tile_ceramic",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="rear",
        adjacency_requirements=["hallway", "garage"],
    ),

    "closet": RoomTypeConfig(
        room_type="closet",
        name="Closet",
        description="Standard closet",
        requirements=RoomRequirements(
            min_width=1.0,
            min_depth=0.8,
            min_height=2.4,
            min_area=1.0,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "carpet_neutral",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=["bedroom"],
    ),

    "walk_in_closet": RoomTypeConfig(
        room_type="walk_in_closet",
        name="Walk-in Closet",
        description="Walk-in closet space",
        requirements=RoomRequirements(
            min_width=1.8,
            min_depth=1.5,
            min_height=2.4,
            min_area=3.0,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "carpet_neutral",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=["master_bedroom"],
    ),

    "hallway": RoomTypeConfig(
        room_type="hallway",
        name="Hallway",
        description="Connecting passage",
        requirements=RoomRequirements(
            min_width=1.0,
            min_depth=2.0,
            min_height=2.4,
            min_area=2.0,
            requires_window=False,
            max_doors=10,
            typical_doors=4,
        ),
        default_materials={
            "floor": "hardwood_oak",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="center",
        adjacency_requirements=[],
    ),

    "foyer": RoomTypeConfig(
        room_type="foyer",
        name="Foyer",
        description="Entryway",
        requirements=RoomRequirements(
            min_width=1.5,
            min_depth=2.0,
            min_height=2.4,
            min_area=3.0,
            requires_window=False,
            max_doors=4,
            typical_doors=2,
        ),
        default_materials={
            "floor": "tile_marble",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="front",
        adjacency_requirements=["living_room", "hallway"],
    ),

    "storage": RoomTypeConfig(
        room_type="storage",
        name="Storage",
        description="General storage space",
        requirements=RoomRequirements(
            min_width=1.0,
            min_depth=1.0,
            min_height=2.4,
            min_area=1.5,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "concrete",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=[],
    ),

    "pantry": RoomTypeConfig(
        room_type="pantry",
        name="Pantry",
        description="Food storage",
        requirements=RoomRequirements(
            min_width=1.0,
            min_depth=1.0,
            min_height=2.4,
            min_area=1.5,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "tile_ceramic",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=["kitchen"],
    ),

    "mudroom": RoomTypeConfig(
        room_type="mudroom",
        name="Mudroom",
        description="Entry from garage/outside",
        requirements=RoomRequirements(
            min_width=1.5,
            min_depth=2.0,
            min_height=2.4,
            min_area=3.0,
            requires_window=False,
            max_doors=3,
            typical_doors=2,
        ),
        default_materials={
            "floor": "tile_ceramic",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="rear",
        adjacency_requirements=["garage", "laundry", "kitchen"],
    ),

    "family_room": RoomTypeConfig(
        room_type="family_room",
        name="Family Room",
        description="Casual gathering space",
        requirements=RoomRequirements(
            min_width=3.5,
            min_depth=4.0,
            min_height=2.6,
            min_area=14.0,
            requires_window=True,
            max_doors=4,
            typical_doors=2,
        ),
        default_materials={
            "floor": "hardwood_oak",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="rear",
        adjacency_requirements=["kitchen", "living_room"],
    ),

    "utility": RoomTypeConfig(
        room_type="utility",
        name="Utility Room",
        description="Mechanical/utility space",
        requirements=RoomRequirements(
            min_width=1.2,
            min_depth=1.2,
            min_height=2.4,
            min_area=2.0,
            requires_window=False,
            max_doors=1,
            typical_doors=1,
        ),
        default_materials={
            "floor": "concrete",
            "wall": "drywall_white",
            "ceiling": "drywall_white",
        },
        typical_placement="interior",
        adjacency_requirements=[],
    ),
}


def get_room_requirements(room_type: str) -> RoomRequirements:
    """
    Get requirements for a room type.

    Args:
        room_type: Room type identifier

    Returns:
        RoomRequirements for the room type
    """
    config = ROOM_TYPE_CONFIGS.get(room_type)
    if config:
        return config.requirements
    return RoomRequirements()


def get_room_config(room_type: str) -> Optional[RoomTypeConfig]:
    """
    Get full configuration for a room type.

    Args:
        room_type: Room type identifier

    Returns:
        RoomTypeConfig or None if not found
    """
    return ROOM_TYPE_CONFIGS.get(room_type)


def list_room_types() -> List[str]:
    """Get list of all available room types."""
    return list(ROOM_TYPE_CONFIGS.keys())


def get_adjacent_room_types(room_type: str) -> List[str]:
    """
    Get recommended adjacent room types.

    Args:
        room_type: Room type identifier

    Returns:
        List of recommended adjacent room types
    """
    config = ROOM_TYPE_CONFIGS.get(room_type)
    if config:
        return config.adjacency_requirements
    return []


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RoomRequirements",
    "RoomTypeConfig",
    "ROOM_TYPE_CONFIGS",
    "get_room_requirements",
    "get_room_config",
    "list_room_types",
    "get_adjacent_room_types",
]
