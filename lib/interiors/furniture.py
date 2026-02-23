"""
Furniture Placer

Intelligent furniture placement based on room type and ergonomic rules.
Generates furniture layout suggestions for rooms.

Implements REQ-IL-07: Furniture Placement Engine.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math

from .types import FloorPlan, Room, FurniturePlacement


class FurnitureCategory(Enum):
    """Furniture category classification."""
    SEATING = "seating"
    TABLE = "table"
    STORAGE = "storage"
    BED = "bed"
    DESK = "desk"
    APPLIANCE = "appliance"
    DECOR = "decor"
    LIGHTING = "lighting"
    RUG = "rug"
    PLANT = "plant"


@dataclass
class FurnitureItem:
    """
    Furniture item definition.

    Attributes:
        name: Item name
        category: Furniture category
        dimensions: (width, depth, height) in meters
        tags: Search tags
        wall_required: Whether item needs to be against wall
        clearance: Required clearance space in meters
        centered: Whether item should be centered in room
        corner: Whether item is a corner piece
    """
    name: str = ""
    category: str = "decor"
    dimensions: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    tags: List[str] = field(default_factory=list)
    wall_required: bool = False
    clearance: float = 0.5
    centered: bool = False
    corner: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "dimensions": list(self.dimensions),
            "tags": self.tags,
            "wall_required": self.wall_required,
            "clearance": self.clearance,
            "centered": self.centered,
            "corner": self.corner,
        }


# Furniture catalogs by room type
FURNITURE_CATALOGS: Dict[str, List[FurnitureItem]] = {
    "living_room": [
        # Seating
        FurnitureItem(name="sofa_3seat", category="seating",
                     dimensions=(2.2, 0.9, 0.85), wall_required=True, clearance=0.8),
        FurnitureItem(name="sofa_2seat", category="seating",
                     dimensions=(1.8, 0.9, 0.85), wall_required=True, clearance=0.8),
        FurnitureItem(name="armchair", category="seating",
                     dimensions=(0.85, 0.85, 0.9), clearance=0.6),
        FurnitureItem(name="loveseat", category="seating",
                     dimensions=(1.5, 0.85, 0.85), wall_required=True, clearance=0.7),
        FurnitureItem(name="ottoman", category="seating",
                     dimensions=(0.6, 0.6, 0.45), clearance=0.3),
        # Tables
        FurnitureItem(name="coffee_table", category="table",
                     dimensions=(1.2, 0.6, 0.45), clearance=0.4),
        FurnitureItem(name="side_table", category="table",
                     dimensions=(0.5, 0.5, 0.55), clearance=0.2),
        FurnitureItem(name="console_table", category="table",
                     dimensions=(1.2, 0.4, 0.8), wall_required=True, clearance=0.5),
        # Storage
        FurnitureItem(name="tv_stand", category="storage",
                     dimensions=(1.8, 0.5, 0.5), wall_required=True, clearance=0.3),
        FurnitureItem(name="bookshelf", category="storage",
                     dimensions=(0.9, 0.35, 1.8), wall_required=True, clearance=0.4),
        # Decor
        FurnitureItem(name="area_rug", category="rug",
                     dimensions=(2.5, 2.0, 0.02), centered=True, clearance=0.0),
        FurnitureItem(name="floor_lamp", category="lighting",
                     dimensions=(0.4, 0.4, 1.6), clearance=0.3),
        FurnitureItem(name="plant_large", category="plant",
                     dimensions=(0.5, 0.5, 1.2), clearance=0.2),
    ],

    "bedroom": [
        FurnitureItem(name="bed_single", category="bed",
                     dimensions=(1.0, 2.0, 0.5), wall_required=True, clearance=0.6),
        FurnitureItem(name="bed_double", category="bed",
                     dimensions=(1.4, 2.0, 0.5), wall_required=True, clearance=0.6),
        FurnitureItem(name="bed_queen", category="bed",
                     dimensions=(1.6, 2.0, 0.5), wall_required=True, clearance=0.7),
        FurnitureItem(name="bed_king", category="bed",
                     dimensions=(1.9, 2.0, 0.5), wall_required=True, clearance=0.8),
        FurnitureItem(name="nightstand", category="storage",
                     dimensions=(0.5, 0.45, 0.55), wall_required=True, clearance=0.2),
        FurnitureItem(name="dresser", category="storage",
                     dimensions=(1.2, 0.5, 0.9), wall_required=True, clearance=0.5),
        FurnitureItem(name="wardrobe", category="storage",
                     dimensions=(1.8, 0.6, 2.1), wall_required=True, clearance=0.5),
        FurnitureItem(name="desk_small", category="desk",
                     dimensions=(1.0, 0.6, 0.75), wall_required=True, clearance=0.6),
        FurnitureItem(name="chair_desk", category="seating",
                     dimensions=(0.5, 0.5, 0.9), clearance=0.4),
        FurnitureItem(name="area_rug", category="rug",
                     dimensions=(2.0, 1.5, 0.02), centered=True),
    ],

    "master_bedroom": [
        FurnitureItem(name="bed_king", category="bed",
                     dimensions=(1.9, 2.0, 0.5), wall_required=True, clearance=0.8),
        FurnitureItem(name="nightstand", category="storage",
                     dimensions=(0.55, 0.5, 0.6), wall_required=True, clearance=0.3),
        FurnitureItem(name="dresser_large", category="storage",
                     dimensions=(1.8, 0.55, 0.95), wall_required=True, clearance=0.6),
        FurnitureItem(name="armoire", category="storage",
                     dimensions=(2.0, 0.65, 2.2), wall_required=True, clearance=0.5),
        FurnitureItem(name="bench_bed", category="seating",
                     dimensions=(1.5, 0.45, 0.45), wall_required=True, clearance=0.3),
        FurnitureItem(name="vanity", category="desk",
                     dimensions=(1.0, 0.5, 0.75), wall_required=True, clearance=0.6),
        FurnitureItem(name="chair_vanity", category="seating",
                     dimensions=(0.45, 0.45, 0.85), clearance=0.3),
        FurnitureItem(name="area_rug_large", category="rug",
                     dimensions=(3.0, 2.5, 0.02), centered=True),
        FurnitureItem(name="floor_lamp", category="lighting",
                     dimensions=(0.4, 0.4, 1.6), clearance=0.3),
    ],

    "kitchen": [
        FurnitureItem(name="dining_table_4", category="table",
                     dimensions=(1.2, 0.9, 0.75), clearance=0.8),
        FurnitureItem(name="dining_table_6", category="table",
                     dimensions=(1.8, 1.0, 0.75), clearance=0.8),
        FurnitureItem(name="chair_dining", category="seating",
                     dimensions=(0.45, 0.5, 0.85), clearance=0.5),
        FurnitureItem(name="bar_stool", category="seating",
                     dimensions=(0.4, 0.4, 0.75), clearance=0.3),
        FurnitureItem(name="kitchen_island", category="storage",
                     dimensions=(1.8, 0.9, 0.9), clearance=0.9),
        FurnitureItem(name="pantry_cabinet", category="storage",
                     dimensions=(0.6, 0.6, 2.1), wall_required=True, clearance=0.5),
    ],

    "dining_room": [
        FurnitureItem(name="dining_table_6", category="table",
                     dimensions=(1.8, 1.1, 0.75), centered=True, clearance=1.0),
        FurnitureItem(name="dining_table_8", category="table",
                     dimensions=(2.2, 1.2, 0.75), centered=True, clearance=1.0),
        FurnitureItem(name="chair_dining", category="seating",
                     dimensions=(0.45, 0.5, 0.85), clearance=0.6),
        FurnitureItem(name="buffet", category="storage",
                     dimensions=(1.8, 0.5, 0.85), wall_required=True, clearance=0.5),
        FurnitureItem(name="china_cabinet", category="storage",
                     dimensions=(1.5, 0.45, 1.8), wall_required=True, clearance=0.4),
        FurnitureItem(name="chandelier", category="lighting",
                     dimensions=(0.8, 0.8, 0.5), centered=True),
        FurnitureItem(name="area_rug", category="rug",
                     dimensions=(3.0, 2.5, 0.02), centered=True),
    ],

    "bathroom": [
        FurnitureItem(name="vanity_single", category="storage",
                     dimensions=(0.8, 0.5, 0.85), wall_required=True, clearance=0.5),
        FurnitureItem(name="vanity_double", category="storage",
                     dimensions=(1.5, 0.55, 0.85), wall_required=True, clearance=0.5),
        FurnitureItem(name="toilet", category="appliance",
                     dimensions=(0.4, 0.65, 0.8), wall_required=True, clearance=0.3),
        FurnitureItem(name="shower", category="appliance",
                     dimensions=(1.0, 1.0, 2.2), corner=True, clearance=0.1),
        FurnitureItem(name="bathtub", category="appliance",
                     dimensions=(1.7, 0.75, 0.55), wall_required=True, clearance=0.3),
        FurnitureItem(name="towel_rack", category="storage",
                     dimensions=(0.6, 0.1, 0.1), wall_required=True, clearance=0.1),
        FurnitureItem(name="medicine_cabinet", category="storage",
                     dimensions=(0.5, 0.15, 0.6), wall_required=True, clearance=0.1),
    ],

    "office": [
        FurnitureItem(name="desk_executive", category="desk",
                     dimensions=(1.8, 0.9, 0.75), wall_required=True, clearance=0.8),
        FurnitureItem(name="desk_standard", category="desk",
                     dimensions=(1.4, 0.7, 0.75), wall_required=True, clearance=0.7),
        FurnitureItem(name="chair_office", category="seating",
                     dimensions=(0.6, 0.6, 1.0), clearance=0.5),
        FurnitureItem(name="bookcase", category="storage",
                     dimensions=(0.9, 0.35, 1.8), wall_required=True, clearance=0.4),
        FurnitureItem(name="filing_cabinet", category="storage",
                     dimensions=(0.45, 0.6, 1.3), wall_required=True, clearance=0.4),
        FurnitureItem(name="desk_lamp", category="lighting",
                     dimensions=(0.3, 0.3, 0.5), clearance=0.2),
        FurnitureItem(name="chair_guest", category="seating",
                     dimensions=(0.5, 0.5, 0.85), clearance=0.4),
    ],

    "laundry": [
        FurnitureItem(name="washer", category="appliance",
                     dimensions=(0.6, 0.65, 0.9), wall_required=True, clearance=0.3),
        FurnitureItem(name="dryer", category="appliance",
                     dimensions=(0.6, 0.65, 0.9), wall_required=True, clearance=0.3),
        FurnitureItem(name="utility_sink", category="appliance",
                     dimensions=(0.6, 0.5, 0.85), wall_required=True, clearance=0.3),
        FurnitureItem(name="folding_table", category="table",
                     dimensions=(1.2, 0.6, 0.9), wall_required=True, clearance=0.5),
        FurnitureItem(name="storage_shelf", category="storage",
                     dimensions=(0.9, 0.4, 1.8), wall_required=True, clearance=0.3),
    ],

    "hallway": [
        FurnitureItem(name="console_table", category="table",
                     dimensions=(1.0, 0.35, 0.8), wall_required=True, clearance=0.3),
        FurnitureItem(name="bench_entry", category="seating",
                     dimensions=(1.0, 0.4, 0.45), wall_required=True, clearance=0.5),
        FurnitureItem(name="coat_rack", category="storage",
                     dimensions=(0.4, 0.4, 1.8), clearance=0.3),
        FurnitureItem(name="mirror", category="decor",
                     dimensions=(0.6, 0.05, 1.0), wall_required=True, clearance=0.1),
        FurnitureItem(name="runner_rug", category="rug",
                     dimensions=(0.7, 2.5, 0.02), clearance=0.0),
    ],

    "foyer": [
        FurnitureItem(name="console_table", category="table",
                     dimensions=(1.2, 0.4, 0.8), wall_required=True, clearance=0.5),
        FurnitureItem(name="bench_entry", category="seating",
                     dimensions=(1.2, 0.45, 0.45), wall_required=True, clearance=0.6),
        FurnitureItem(name="coat_closet", category="storage",
                     dimensions=(1.0, 0.6, 2.1), wall_required=True, clearance=0.0),
        FurnitureItem(name="mirror_large", category="decor",
                     dimensions=(0.8, 0.05, 1.5), wall_required=True, clearance=0.1),
        FurnitureItem(name="chandelier", category="lighting",
                     dimensions=(0.6, 0.6, 0.5), centered=True),
        FurnitureItem(name="area_rug", category="rug",
                     dimensions=(1.5, 1.0, 0.02), centered=True),
    ],

    "closet": [
        FurnitureItem(name="closet_rod", category="storage",
                     dimensions=(1.5, 0.05, 0.05), wall_required=True, clearance=0.5),
        FurnitureItem(name="shelf_closet", category="storage",
                     dimensions=(1.0, 0.35, 0.03), wall_required=True, clearance=0.3),
        FurnitureItem(name="shoe_rack", category="storage",
                     dimensions=(0.8, 0.35, 0.6), wall_required=True, clearance=0.3),
        FurnitureItem(name="drawer_unit", category="storage",
                     dimensions=(0.5, 0.45, 1.0), wall_required=True, clearance=0.3),
    ],
}


@dataclass
class FurnitureLayout:
    """
    Complete furniture layout for a room.

    Attributes:
        room_id: ID of room
        items: List of placed furniture items
        total_items: Total number of items
        coverage: Floor coverage percentage
    """
    room_id: str = ""
    items: List[FurniturePlacement] = field(default_factory=list)
    total_items: int = 0
    coverage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "room_id": self.room_id,
            "items": [i.to_dict() for i in self.items],
            "total_items": self.total_items,
            "coverage": self.coverage,
        }


class FurniturePlacer:
    """
    Intelligent furniture placement system.

    Places furniture based on room type, dimensions, and ergonomic rules.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize furniture placer.

        Args:
            seed: Random seed for variation
        """
        self.seed = seed

    def place_furniture(
        self,
        room: Room,
        max_items: int = 15
    ) -> FurnitureLayout:
        """
        Place furniture in a room.

        Args:
            room: Room to place furniture in
            max_items: Maximum number of items to place

        Returns:
            FurnitureLayout with placed items
        """
        items = []

        # Get furniture catalog for room type
        catalog = FURNITURE_CATALOGS.get(room.room_type, [])
        if not catalog:
            # Default to living room catalog
            catalog = FURNITURE_CATALOGS.get("living_room", [])

        # Get room center and bounds
        center = room.center
        bounds = room.bounds
        room_width = bounds[2] - bounds[0]
        room_depth = bounds[3] - bounds[1]

        # Place essential items first
        placed_categories = set()
        item_count = 0

        for furniture in catalog:
            if item_count >= max_items:
                break

            # Check if item fits in room
            if not self._item_fits(furniture, room_width, room_depth):
                continue

            # Calculate placement position
            position = self._calculate_placement(
                furniture, center, bounds, room_width, room_depth
            )

            if position:
                items.append(FurniturePlacement(
                    furniture_type=furniture.name,
                    position=(position[0], position[1], 0.0),
                    rotation=position[2],
                    scale=1.0,
                    variant=0,
                ))
                placed_categories.add(furniture.category)
                item_count += 1

        # Calculate coverage
        total_area = 0.0
        for item in items:
            furniture_def = next(
                (f for f in catalog if f.name == item.furniture_type),
                None
            )
            if furniture_def:
                dims = furniture_def.dimensions
                total_area += dims[0] * dims[1]

        coverage = total_area / room.area if room.area > 0 else 0.0

        return FurnitureLayout(
            room_id=room.id,
            items=items,
            total_items=len(items),
            coverage=min(coverage, 1.0),
        )

    def _item_fits(
        self,
        furniture: FurnitureItem,
        room_width: float,
        room_depth: float
    ) -> bool:
        """Check if furniture item fits in room."""
        dims = furniture.dimensions

        # Check minimum clearance
        required_width = dims[0] + furniture.clearance * 2
        required_depth = dims[1] + furniture.clearance * 2

        return required_width <= room_width and required_depth <= room_depth

    def _calculate_placement(
        self,
        furniture: FurnitureItem,
        center: Tuple[float, float],
        bounds: Tuple[float, float, float, float],
        room_width: float,
        room_depth: float
    ) -> Optional[Tuple[float, float, float]]:
        """Calculate placement position for furniture."""
        dims = furniture.dimensions

        if furniture.centered:
            # Place at room center
            return (center[0], center[1], 0.0)

        if furniture.wall_required:
            # Place against a wall
            # Choose wall based on furniture dimensions
            if dims[0] > dims[1]:
                # Long furniture against long wall
                if room_width >= room_depth:
                    # Against top or bottom wall
                    return (
                        center[0],
                        bounds[1] + dims[1] / 2 + furniture.clearance,
                        0.0
                    )
                else:
                    # Against left or right wall
                    return (
                        bounds[0] + dims[0] / 2 + furniture.clearance,
                        center[1],
                        math.pi / 2
                    )
            else:
                # Against side wall
                return (
                    bounds[0] + dims[0] / 2 + furniture.clearance,
                    bounds[1] + dims[1] / 2 + furniture.clearance,
                    0.0
                )

        if furniture.corner:
            # Place in corner
            return (
                bounds[0] + dims[0] / 2 + furniture.clearance,
                bounds[1] + dims[1] / 2 + furniture.clearance,
                0.0
            )

        # Default placement near center with offset
        offset_x = (dims[0] / 2) if room_width > room_depth else 0
        offset_y = (dims[1] / 2) if room_depth > room_width else 0

        return (
            center[0] + offset_x * 0.3,
            center[1] + offset_y * 0.3,
            0.0
        )


def place_furniture_in_room(
    room: Room,
    max_items: int = 15,
    seed: Optional[int] = None
) -> FurnitureLayout:
    """
    Convenience function to place furniture in a room.

    Args:
        room: Room to place furniture in
        max_items: Maximum number of items
        seed: Random seed

    Returns:
        FurnitureLayout with placed items
    """
    placer = FurniturePlacer(seed=seed)
    return placer.place_furniture(room, max_items)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FurnitureCategory",
    "FurnitureItem",
    "FurnitureLayout",
    "FurniturePlacer",
    "FURNITURE_CATALOGS",
    "place_furniture_in_room",
]
