"""
Furniture Scatter System

Procedural furniture and prop placement within rooms.
Uses constraint-based positioning with collision avoidance.

Implements REQ-GN-03: Furniture Scatter System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set
from enum import Enum
import random
import math


class PlacementStrategy(Enum):
    """Furniture placement strategy."""
    GRID = "grid"
    RANDOM = "random"
    WALL_ALIGNED = "wall_aligned"
    CENTERED = "centered"
    CORNER = "corner"
    ERGONOMIC = "ergonomic"


class FurnitureCategory(Enum):
    """Furniture category classification."""
    SEATING = "seating"
    TABLE = "table"
    STORAGE = "storage"
    BED = "bed"
    DESK = "desk"
    LIGHTING = "lighting"
    DECORATION = "decoration"
    APPLIANCE = "appliance"


@dataclass
class FurnitureBounds:
    """
    Furniture bounding box.

    Attributes:
        width: X dimension
        depth: Y dimension
        height: Z dimension
    """
    width: float = 0.5
    depth: float = 0.5
    height: float = 0.5

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
        }

    @property
    def footprint(self) -> float:
        """Calculate footprint area."""
        return self.width * self.depth


@dataclass
class PlacementConstraint:
    """
    Constraint for furniture placement.

    Attributes:
        constraint_type: Type of constraint
        target: Target object or zone
        distance: Required distance
        weight: Constraint weight for optimization
    """
    constraint_type: str = "avoid_wall"
    target: str = ""
    distance: float = 0.5
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "constraint_type": self.constraint_type,
            "target": self.target,
            "distance": self.distance,
            "weight": self.weight,
        }


@dataclass
class FurnitureItem:
    """
    Furniture item specification.

    Attributes:
        item_id: Unique item identifier
        name: Display name
        category: Furniture category
        bounds: Bounding box dimensions
        model_path: Path to 3D model
        placement_strategy: Preferred placement strategy
        constraints: Placement constraints
        required_clearance: Required clearance space
        can_stack: Whether items can stack
        tags: Search tags
    """
    item_id: str = ""
    name: str = ""
    category: str = "prop"
    bounds: FurnitureBounds = field(default_factory=FurnitureBounds)
    model_path: str = ""
    placement_strategy: str = "random"
    constraints: List[PlacementConstraint] = field(default_factory=list)
    required_clearance: float = 0.1
    can_stack: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category,
            "bounds": self.bounds.to_dict(),
            "model_path": self.model_path,
            "placement_strategy": self.placement_strategy,
            "constraints": [c.to_dict() for c in self.constraints],
            "required_clearance": self.required_clearance,
            "can_stack": self.can_stack,
            "tags": self.tags,
        }


@dataclass
class PlacedItem:
    """
    Placed furniture instance.

    Attributes:
        instance_id: Unique instance identifier
        item_id: Source furniture item ID
        position: World position (x, y, z)
        rotation: Rotation in degrees (x, y, z)
        scale: Scale factor
        variant: Material variant index
    """
    instance_id: str = ""
    item_id: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    variant: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "item_id": self.item_id,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": self.scale,
            "variant": self.variant,
        }


@dataclass
class ScatterResult:
    """
    Result of scatter operation.

    Attributes:
        success: Whether scatter succeeded
        placed_items: Successfully placed items
        rejected_items: Items that couldn't be placed
        coverage: Room coverage percentage
        collision_count: Number of collision checks
    """
    success: bool = True
    placed_items: List[PlacedItem] = field(default_factory=list)
    rejected_items: List[str] = field(default_factory=list)
    coverage: float = 0.0
    collision_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "placed_items": [p.to_dict() for p in self.placed_items],
            "rejected_items": self.rejected_items,
            "coverage": self.coverage,
            "collision_count": self.collision_count,
        }


# =============================================================================
# FURNITURE CATALOG
# =============================================================================

FURNITURE_CATALOG: Dict[str, FurnitureItem] = {
    # Seating
    "sofa_2seat": FurnitureItem(
        item_id="sofa_2seat",
        name="2-Seat Sofa",
        category="seating",
        bounds=FurnitureBounds(width=1.6, depth=0.9, height=0.85),
        placement_strategy="wall_aligned",
        constraints=[
            PlacementConstraint(constraint_type="avoid_wall", distance=0.1),
            PlacementConstraint(constraint_type="face_center", target="room", weight=0.8),
        ],
        required_clearance=0.5,
        tags=["living_room", "seating", "modern"],
    ),
    "armchair": FurnitureItem(
        item_id="armchair",
        name="Armchair",
        category="seating",
        bounds=FurnitureBounds(width=0.8, depth=0.8, height=0.9),
        placement_strategy="wall_aligned",
        required_clearance=0.4,
        tags=["living_room", "seating"],
    ),
    "dining_chair": FurnitureItem(
        item_id="dining_chair",
        name="Dining Chair",
        category="seating",
        bounds=FurnitureBounds(width=0.45, depth=0.5, height=0.9),
        placement_strategy="grid",
        required_clearance=0.3,
        can_stack=True,
        tags=["dining", "seating"],
    ),
    "office_chair": FurnitureItem(
        item_id="office_chair",
        name="Office Chair",
        category="seating",
        bounds=FurnitureBounds(width=0.6, depth=0.6, height=1.1),
        placement_strategy="centered",
        required_clearance=0.4,
        tags=["office", "seating"],
    ),

    # Tables
    "coffee_table": FurnitureItem(
        item_id="coffee_table",
        name="Coffee Table",
        category="table",
        bounds=FurnitureBounds(width=1.2, depth=0.6, height=0.45),
        placement_strategy="centered",
        constraints=[
            PlacementConstraint(constraint_type="distance_from", target="sofa_2seat", distance=0.4),
        ],
        required_clearance=0.3,
        tags=["living_room", "table"],
    ),
    "dining_table": FurnitureItem(
        item_id="dining_table",
        name="Dining Table",
        category="table",
        bounds=FurnitureBounds(width=1.8, depth=1.0, height=0.75),
        placement_strategy="centered",
        required_clearance=0.8,
        tags=["dining", "table"],
    ),
    "desk": FurnitureItem(
        item_id="desk",
        name="Office Desk",
        category="desk",
        bounds=FurnitureBounds(width=1.4, depth=0.7, height=0.75),
        placement_strategy="wall_aligned",
        required_clearance=0.6,
        tags=["office", "desk"],
    ),
    "nightstand": FurnitureItem(
        item_id="nightstand",
        name="Nightstand",
        category="storage",
        bounds=FurnitureBounds(width=0.5, depth=0.4, height=0.55),
        placement_strategy="corner",
        required_clearance=0.1,
        tags=["bedroom", "storage"],
    ),

    # Storage
    "bookshelf": FurnitureItem(
        item_id="bookshelf",
        name="Bookshelf",
        category="storage",
        bounds=FurnitureBounds(width=0.8, depth=0.3, height=1.8),
        placement_strategy="wall_aligned",
        constraints=[
            PlacementConstraint(constraint_type="against_wall", distance=0.0),
        ],
        required_clearance=0.2,
        tags=["storage", "living_room", "office"],
    ),
    "wardrobe": FurnitureItem(
        item_id="wardrobe",
        name="Wardrobe",
        category="storage",
        bounds=FurnitureBounds(width=1.5, depth=0.6, height=2.1),
        placement_strategy="wall_aligned",
        required_clearance=0.5,
        tags=["bedroom", "storage"],
    ),
    "tv_stand": FurnitureItem(
        item_id="tv_stand",
        name="TV Stand",
        category="storage",
        bounds=FurnitureBounds(width=1.4, depth=0.4, height=0.5),
        placement_strategy="wall_aligned",
        required_clearance=0.2,
        tags=["living_room", "storage", "entertainment"],
    ),

    # Beds
    "bed_single": FurnitureItem(
        item_id="bed_single",
        name="Single Bed",
        category="bed",
        bounds=FurnitureBounds(width=0.9, depth=2.0, height=0.5),
        placement_strategy="wall_aligned",
        required_clearance=0.5,
        tags=["bedroom", "bed"],
    ),
    "bed_double": FurnitureItem(
        item_id="bed_double",
        name="Double Bed",
        category="bed",
        bounds=FurnitureBounds(width=1.6, depth=2.0, height=0.5),
        placement_strategy="wall_aligned",
        required_clearance=0.6,
        tags=["bedroom", "bed"],
    ),

    # Lighting
    "floor_lamp": FurnitureItem(
        item_id="floor_lamp",
        name="Floor Lamp",
        category="lighting",
        bounds=FurnitureBounds(width=0.4, depth=0.4, height=1.6),
        placement_strategy="corner",
        required_clearance=0.2,
        tags=["lighting", "living_room", "bedroom"],
    ),
    "table_lamp": FurnitureItem(
        item_id="table_lamp",
        name="Table Lamp",
        category="lighting",
        bounds=FurnitureBounds(width=0.25, depth=0.25, height=0.45),
        placement_strategy="random",
        required_clearance=0.1,
        tags=["lighting", "decor"],
    ),

    # Decoration
    "plant_small": FurnitureItem(
        item_id="plant_small",
        name="Small Plant",
        category="decoration",
        bounds=FurnitureBounds(width=0.3, depth=0.3, height=0.6),
        placement_strategy="random",
        required_clearance=0.1,
        tags=["decoration", "nature"],
    ),
    "plant_large": FurnitureItem(
        item_id="plant_large",
        name="Large Plant",
        category="decoration",
        bounds=FurnitureBounds(width=0.5, depth=0.5, height=1.5),
        placement_strategy="corner",
        required_clearance=0.2,
        tags=["decoration", "nature"],
    ),
    "rug_medium": FurnitureItem(
        item_id="rug_medium",
        name="Medium Rug",
        category="decoration",
        bounds=FurnitureBounds(width=2.0, depth=1.5, height=0.02),
        placement_strategy="centered",
        required_clearance=0.0,
        tags=["decoration", "floor"],
    ),

    # Appliances
    "refrigerator": FurnitureItem(
        item_id="refrigerator",
        name="Refrigerator",
        category="appliance",
        bounds=FurnitureBounds(width=0.7, depth=0.7, height=1.8),
        placement_strategy="corner",
        required_clearance=0.3,
        tags=["kitchen", "appliance"],
    ),
    "tv_flat": FurnitureItem(
        item_id="tv_flat",
        name="Flat Screen TV",
        category="appliance",
        bounds=FurnitureBounds(width=1.2, depth=0.1, height=0.7),
        placement_strategy="wall_aligned",
        required_clearance=0.1,
        tags=["entertainment", "living_room"],
    ),
}


# =============================================================================
# ROOM TYPE FURNITURE SETS
# =============================================================================

ROOM_FURNITURE_SETS: Dict[str, List[str]] = {
    "living_room": [
        "sofa_2seat",
        "armchair",
        "coffee_table",
        "tv_stand",
        "tv_flat",
        "floor_lamp",
        "plant_small",
        "rug_medium",
    ],
    "bedroom": [
        "bed_double",
        "nightstand",
        "nightstand",
        "wardrobe",
        "table_lamp",
        "plant_small",
    ],
    "office": [
        "desk",
        "office_chair",
        "bookshelf",
        "table_lamp",
        "plant_small",
    ],
    "dining_room": [
        "dining_table",
        "dining_chair",
        "dining_chair",
        "dining_chair",
        "dining_chair",
        "plant_large",
        "rug_medium",
    ],
    "kitchen": [
        "refrigerator",
        "plant_small",
    ],
}


class FurnitureScatterer:
    """
    Procedural furniture placement system.

    Places furniture in rooms using constraint-based positioning
    with collision avoidance.

    Usage:
        scatterer = FurnitureScatterer()
        result = scatterer.scatter(
            room_bounds=(0, 0, 5, 4),
            furniture_set="living_room",
            seed=42,
        )
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize scatterer.

        Args:
            seed: Random seed for reproducibility
        """
        self.rng = random.Random(seed)
        self.catalog = FURNITURE_CATALOG
        self._instance_counter = 0

    def scatter(
        self,
        room_bounds: Tuple[float, float, float, float],
        furniture_set: str,
        density: float = 1.0,
        avoid_zones: Optional[List[Tuple[float, float, float, float]]] = None,
        existing_items: Optional[List[PlacedItem]] = None,
    ) -> ScatterResult:
        """
        Scatter furniture in room.

        Args:
            room_bounds: Room bounding box (min_x, min_y, max_x, max_y)
            furniture_set: Room type for furniture selection
            density: Placement density (0-1)
            avoid_zones: Zones to avoid (bounding boxes)
            existing_items: Already placed items

        Returns:
            ScatterResult with placed items
        """
        result = ScatterResult()
        avoid_zones = avoid_zones or []
        existing_items = existing_items or []

        # Get furniture list for room type
        furniture_ids = ROOM_FURNITURE_SETS.get(furniture_set, [])
        if not furniture_ids:
            result.success = False
            result.rejected_items.append(f"No furniture set: {furniture_set}")
            return result

        # Apply density
        num_items = int(len(furniture_ids) * density)
        furniture_ids = furniture_ids[:num_items]

        # Track placed bounds for collision
        placed_bounds: List[Tuple[float, float, float, float]] = []
        for item in existing_items:
            catalog_item = self.catalog.get(item.item_id)
            if catalog_item:
                bx = item.position[0] - catalog_item.bounds.width / 2
                by = item.position[1] - catalog_item.bounds.depth / 2
                ex = item.position[0] + catalog_item.bounds.width / 2
                ey = item.position[1] + catalog_item.bounds.depth / 2
                placed_bounds.append((bx, by, ex, ey))

        # Place each item
        for furniture_id in furniture_ids:
            item = self.catalog.get(furniture_id)
            if not item:
                result.rejected_items.append(furniture_id)
                continue

            position = self._find_position(
                item,
                room_bounds,
                placed_bounds + avoid_zones,
            )

            if position:
                rotation = self._calculate_rotation(item, position, room_bounds)

                placed = PlacedItem(
                    instance_id=self._generate_instance_id(),
                    item_id=furniture_id,
                    position=position,
                    rotation=rotation,
                    scale=1.0,
                    variant=self.rng.randint(0, 3),
                )
                result.placed_items.append(placed)

                # Add to placed bounds
                bx = position[0] - item.bounds.width / 2 - item.required_clearance
                by = position[1] - item.bounds.depth / 2 - item.required_clearance
                ex = position[0] + item.bounds.width / 2 + item.required_clearance
                ey = position[1] + item.bounds.depth / 2 + item.required_clearance
                placed_bounds.append((bx, by, ex, ey))
            else:
                result.rejected_items.append(furniture_id)

        # Calculate coverage
        room_area = (room_bounds[2] - room_bounds[0]) * (room_bounds[3] - room_bounds[1])
        covered_area = sum(
            self.catalog[p.item_id].bounds.footprint
            for p in result.placed_items
            if p.item_id in self.catalog
        )
        result.coverage = covered_area / room_area if room_area > 0 else 0
        result.success = len(result.placed_items) > 0

        return result

    def _find_position(
        self,
        item: FurnitureItem,
        room_bounds: Tuple[float, float, float, float],
        avoid_zones: List[Tuple[float, float, float, float]],
        max_attempts: int = 50,
    ) -> Optional[Tuple[float, float, float]]:
        """Find valid position for item."""
        min_x, min_y, max_x, max_y = room_bounds

        # Shrink bounds by item size + clearance
        padding = max(item.bounds.width, item.bounds.depth) / 2 + item.required_clearance
        min_x += padding
        min_y += padding
        max_x -= padding
        max_y -= padding

        if min_x >= max_x or min_y >= max_y:
            return None

        strategy = item.placement_strategy

        for _ in range(max_attempts):
            if strategy == "wall_aligned":
                # Place near wall
                wall = self.rng.choice(["left", "right", "top", "bottom"])
                if wall == "left":
                    x = min_x
                    y = self.rng.uniform(min_y + padding, max_y - padding)
                elif wall == "right":
                    x = max_x
                    y = self.rng.uniform(min_y + padding, max_y - padding)
                elif wall == "top":
                    x = self.rng.uniform(min_x + padding, max_x - padding)
                    y = max_y
                else:
                    x = self.rng.uniform(min_x + padding, max_x - padding)
                    y = min_y

            elif strategy == "corner":
                # Place in corner
                corner = self.rng.choice(["tl", "tr", "bl", "br"])
                if corner == "tl":
                    x, y = min_x, max_y
                elif corner == "tr":
                    x, y = max_x, max_y
                elif corner == "bl":
                    x, y = min_x, min_y
                else:
                    x, y = max_x, min_y

            elif strategy == "centered":
                # Place near center
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                x = center_x + self.rng.uniform(-0.5, 0.5)
                y = center_y + self.rng.uniform(-0.5, 0.5)

            else:  # random or grid
                x = self.rng.uniform(min_x, max_x)
                y = self.rng.uniform(min_y, max_y)

            # Check collision
            item_bounds = (
                x - item.bounds.width / 2 - item.required_clearance,
                y - item.bounds.depth / 2 - item.required_clearance,
                x + item.bounds.width / 2 + item.required_clearance,
                y + item.bounds.depth / 2 + item.required_clearance,
            )

            if not self._check_collision(item_bounds, avoid_zones):
                return (x, y, 0.0)

        return None

    def _calculate_rotation(
        self,
        item: FurnitureItem,
        position: Tuple[float, float, float],
        room_bounds: Tuple[float, float, float, float],
    ) -> Tuple[float, float, float]:
        """Calculate rotation for item."""
        if item.placement_strategy == "wall_aligned":
            # Face toward center of room
            center_x = (room_bounds[0] + room_bounds[2]) / 2
            center_y = (room_bounds[1] + room_bounds[3]) / 2

            dx = center_x - position[0]
            dy = center_y - position[1]
            angle = math.degrees(math.atan2(dy, dx))

            return (0.0, 0.0, angle)

        elif item.placement_strategy == "corner":
            # Face away from corner
            angle = self.rng.choice([45, 135, 225, 315])
            return (0.0, 0.0, angle)

        else:
            # Random rotation
            return (0.0, 0.0, self.rng.uniform(0, 360))

    def _check_collision(
        self,
        bounds: Tuple[float, float, float, float],
        avoid_zones: List[Tuple[float, float, float, float]],
    ) -> bool:
        """Check if bounds collide with avoid zones."""
        for zone in avoid_zones:
            if self._bounds_overlap(bounds, zone):
                return True
        return False

    def _bounds_overlap(
        self,
        a: Tuple[float, float, float, float],
        b: Tuple[float, float, float, float],
    ) -> bool:
        """Check if two bounds overlap."""
        return not (
            a[2] < b[0] or  # a is left of b
            a[0] > b[2] or  # a is right of b
            a[3] < b[1] or  # a is below b
            a[1] > b[3]     # a is above b
        )

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID."""
        self._instance_counter += 1
        return f"furniture_{self._instance_counter:04d}"


def scatter_furniture(
    room_bounds: Tuple[float, float, float, float],
    room_type: str,
    **kwargs,
) -> ScatterResult:
    """
    Convenience function to scatter furniture.

    Args:
        room_bounds: Room bounding box
        room_type: Type of room
        **kwargs: FurnitureScatterer options

    Returns:
        ScatterResult
    """
    scatterer = FurnitureScatterer(**kwargs)
    return scatterer.scatter(room_bounds, room_type)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PlacementStrategy",
    "FurnitureCategory",
    # Data classes
    "FurnitureBounds",
    "PlacementConstraint",
    "FurnitureItem",
    "PlacedItem",
    "ScatterResult",
    # Constants
    "FURNITURE_CATALOG",
    "ROOM_FURNITURE_SETS",
    # Classes
    "FurnitureScatterer",
    # Functions
    "scatter_furniture",
]
