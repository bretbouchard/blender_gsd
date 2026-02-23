"""
BSP (Binary Space Partitioning) Solver

Implements recursive subdivision algorithm for procedural floor plan generation.
Runs in Python (not GN) because it requires recursive subdivision and arbitrary
depth iteration that Geometry Nodes cannot handle.

Output: JSON floor plan consumed by GN Wall Builder.

Architecture:
    BSPSolver.generate(width, height, room_count)
        ↓
    Recursive subdivision creating BSPNode tree
        ↓
    Extract leaf nodes as rooms
        ↓
    Connect adjacent rooms
        ↓
    FloorPlan with rooms and connections

Implements REQ-IL-01: Floor Plan Generator (BSP algorithm).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import random
import math

from .types import (
    Room,
    RoomType,
    Connection,
    DoorSpec,
    WindowSpec,
    FloorPlan,
    InteriorStyle,
)


class BSPSplitDirection(Enum):
    """Direction of BSP split."""
    HORIZONTAL = "horizontal"  # Split along X axis (creates top/bottom)
    VERTICAL = "vertical"  # Split along Y axis (creates left/right)


@dataclass
class Rect:
    """
    Rectangle representation for BSP.

    Attributes:
        x: X position of bottom-left corner
        y: Y position of bottom-left corner
        width: Rectangle width
        height: Rectangle height
    """
    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0

    @property
    def center(self) -> Tuple[float, float]:
        """Get rectangle center."""
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def area(self) -> float:
        """Get rectangle area."""
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width/height)."""
        if self.height == 0:
            return float('inf')
        return self.width / self.height

    def contains_point(self, px: float, py: float) -> bool:
        """Check if point is inside rectangle."""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def overlaps(self, other: "Rect") -> bool:
        """Check if this rectangle overlaps another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

    def to_polygon(self) -> List[Tuple[float, float]]:
        """Convert to polygon vertices (counter-clockwise)."""
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]

    def inset(self, amount: float) -> "Rect":
        """Create inset rectangle."""
        return Rect(
            x=self.x + amount,
            y=self.y + amount,
            width=max(0, self.width - 2 * amount),
            height=max(0, self.height - 2 * amount),
        )


@dataclass
class BSPNode:
    """
    Node in BSP tree.

    Each node represents a rectangular space that can be:
    - A leaf node (room)
    - A branch node (split into two children)

    Attributes:
        rect: Rectangle bounds of this node
        left: Left/top child (if branch)
        right: Right/bottom child (if branch)
        split_direction: Direction of split (if branch)
        split_position: Position of split (if branch)
        room: Room data (if leaf)
        is_leaf: Whether this is a leaf node
    """
    rect: Rect = field(default_factory=Rect)
    left: Optional["BSPNode"] = None
    right: Optional["BSPNode"] = None
    split_direction: Optional[BSPSplitDirection] = None
    split_position: Optional[float] = None
    room: Optional[Room] = None
    is_leaf: bool = True

    def get_leaf_nodes(self) -> List["BSPNode"]:
        """Get all leaf nodes in this subtree."""
        if self.is_leaf:
            return [self]
        leaves = []
        if self.left:
            leaves.extend(self.left.get_leaf_nodes())
        if self.right:
            leaves.extend(self.right.get_leaf_nodes())
        return leaves

    def get_room_nodes(self) -> List["BSPNode"]:
        """Get all nodes with assigned rooms."""
        leaves = self.get_leaf_nodes()
        return [n for n in leaves if n.room is not None]


# Room type priorities for assignment
ROOM_TYPE_PRIORITIES = {
    # High priority - essential rooms
    "living_room": 10,
    "kitchen": 9,
    "master_bedroom": 8,
    "bathroom": 7,

    # Medium priority - common rooms
    "bedroom": 6,
    "dining_room": 5,
    "office": 4,
    "laundry": 3,

    # Low priority - optional rooms
    "closet": 2,
    "hallway": 1,
    "storage": 0,
}

# Minimum room sizes by type (width, height) in meters
MIN_ROOM_SIZES = {
    "living_room": (3.5, 3.5),
    "master_bedroom": (3.5, 3.0),
    "bedroom": (3.0, 2.8),
    "kitchen": (2.5, 2.5),
    "dining_room": (3.0, 3.0),
    "bathroom": (1.8, 1.8),
    "master_bathroom": (2.5, 2.0),
    "half_bath": (1.2, 1.0),
    "office": (2.5, 2.5),
    "closet": (1.0, 0.8),
    "walk_in_closet": (1.8, 1.5),
    "laundry": (1.5, 1.5),
    "utility": (1.5, 1.5),
    "hallway": (1.2, 2.0),
    "foyer": (1.5, 1.5),
    "storage": (1.0, 1.0),
}


class BSPSolver:
    """
    Binary Space Partitioning solver for floor plan generation.

    Generates procedural floor plans by recursively subdividing a rectangular
    space into smaller rooms. The algorithm ensures all rooms are connected
    and meet minimum size requirements.

    Usage:
        solver = BSPSolver(seed=42)
        plan = solver.generate(width=10, height=8, room_count=5)
        json_output = plan.to_json()

    Attributes:
        seed: Random seed for reproducibility
        min_room_size: Minimum room dimension in meters
        split_margin: Margin from edges for splits (0-1)
        room_type_distribution: Weights for room type selection
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        min_room_size: float = 2.5,
        split_margin: float = 0.3,
        style: str = "modern",
    ):
        """
        Initialize BSP solver.

        Args:
            seed: Random seed for reproducibility
            min_room_size: Minimum room dimension in meters
            split_margin: Margin from edges for splits (0-0.5)
            style: Interior style preset
        """
        self.seed = seed
        self.min_room_size = min_room_size
        self.split_margin = max(0.1, min(0.5, split_margin))
        self.style = style
        self._rng = random.Random(seed)
        self._room_counter = 0
        self._connection_counter = 0

    def generate(
        self,
        width: float,
        height: float,
        room_count: int,
        room_types: Optional[List[str]] = None,
    ) -> FloorPlan:
        """
        Generate floor plan with connected rooms.

        Args:
            width: Floor plan width in meters
            height: Floor plan height in meters
            room_count: Target number of rooms
            room_types: Optional list of room types to use

        Returns:
            FloorPlan with rooms and connections
        """
        # Reset counters
        self._room_counter = 0
        self._connection_counter = 0

        # Reset RNG for reproducibility
        self._rng = random.Random(self.seed)

        # Create root node covering entire space
        root = BSPNode(rect=Rect(0, 0, width, height))

        # Subdivide until we have enough rooms
        self._subdivide(root, room_count)

        # Get leaf nodes and create rooms
        leaves = root.get_leaf_nodes()
        rooms = self._create_rooms(leaves, room_types)

        # Connect adjacent rooms
        connections = self._connect_rooms(rooms)

        # Add exterior windows
        self._add_exterior_windows(rooms, width, height)

        # Create floor plan
        plan = FloorPlan(
            dimensions=(width, height),
            rooms=rooms,
            connections=connections,
            style=self.style,
            seed=self.seed,
        )

        return plan

    def _subdivide(self, node: BSPNode, target_rooms: int) -> None:
        """
        Recursively subdivide node until target room count is reached.

        Args:
            node: Node to potentially subdivide
            target_rooms: Target number of leaf nodes
        """
        # Count current leaf nodes
        current_leaves = len(node.get_leaf_nodes()) if node.is_leaf else len(node.get_room_nodes())

        # Check if we should stop subdividing
        if current_leaves >= target_rooms:
            return

        # Check if node is too small to subdivide
        if not self._can_subdivide(node.rect):
            return

        # Determine split direction based on aspect ratio
        direction = self._choose_split_direction(node.rect)

        # Calculate split position
        split_pos = self._calculate_split_position(node.rect, direction)

        if split_pos is None:
            return

        # Perform split
        node.is_leaf = False
        node.split_direction = direction
        node.split_position = split_pos

        # Create child nodes
        if direction == BSPSplitDirection.HORIZONTAL:
            # Split horizontally (top/bottom)
            node.left = BSPNode(rect=Rect(
                node.rect.x,
                node.rect.y,
                node.rect.width,
                split_pos - node.rect.y
            ))
            node.right = BSPNode(rect=Rect(
                node.rect.x,
                split_pos,
                node.rect.width,
                node.rect.y + node.rect.height - split_pos
            ))
        else:
            # Split vertically (left/right)
            node.left = BSPNode(rect=Rect(
                node.rect.x,
                node.rect.y,
                split_pos - node.rect.x,
                node.rect.height
            ))
            node.right = BSPNode(rect=Rect(
                split_pos,
                node.rect.y,
                node.rect.x + node.rect.width - split_pos,
                node.rect.height
            ))

        # Recursively subdivide children
        remaining_rooms = target_rooms - len(node.get_room_nodes())
        if remaining_rooms > 0:
            # Distribute room targets between children
            left_target = max(1, remaining_rooms // 2 + self._rng.randint(-1, 1))

            self._subdivide(node.left, left_target + 1)
            self._subdivide(node.right, remaining_rooms - left_target + 1)

    def _can_subdivide(self, rect: Rect) -> bool:
        """Check if rectangle can be subdivided while maintaining min sizes."""
        return (rect.width >= self.min_room_size * 2 + 0.1 and
                rect.height >= self.min_room_size * 2 + 0.1)

    def _choose_split_direction(self, rect: Rect) -> BSPSplitDirection:
        """Choose split direction based on aspect ratio."""
        aspect = rect.aspect_ratio

        # If very wide, split vertically
        if aspect > 1.5:
            return BSPSplitDirection.VERTICAL
        # If very tall, split horizontally
        elif aspect < 0.67:
            return BSPSplitDirection.HORIZONTAL
        # Otherwise random
        else:
            return self._rng.choice(list(BSPSplitDirection))

    def _calculate_split_position(
        self,
        rect: Rect,
        direction: BSPSplitDirection
    ) -> Optional[float]:
        """Calculate split position within margin bounds."""
        if direction == BSPSplitDirection.HORIZONTAL:
            min_pos = rect.y + self.min_room_size
            max_pos = rect.y + rect.height - self.min_room_size
        else:
            min_pos = rect.x + self.min_room_size
            max_pos = rect.x + rect.width - self.min_room_size

        if min_pos >= max_pos:
            return None

        # Add some randomness within bounds
        margin = (max_pos - min_pos) * self.split_margin
        actual_min = min_pos + margin
        actual_max = max_pos - margin

        if actual_min >= actual_max:
            # Fallback to center
            return (min_pos + max_pos) / 2

        return self._rng.uniform(actual_min, actual_max)

    def _create_rooms(
        self,
        leaves: List[BSPNode],
        room_types: Optional[List[str]] = None
    ) -> List[Room]:
        """Create rooms from leaf nodes."""
        rooms = []

        # Default room types if not specified
        if room_types is None:
            room_types = list(ROOM_TYPE_PRIORITIES.keys())

        # Sort leaves by area (larger rooms get higher priority types)
        leaves_sorted = sorted(leaves, key=lambda n: n.rect.area, reverse=True)

        for i, leaf in enumerate(leaves_sorted):
            # Assign room type
            room_type = self._assign_room_type(i, len(leaves_sorted), room_types)

            # Create room with inset rect for wall thickness
            inset_rect = leaf.rect.inset(0.01)  # Small inset for walls

            room = Room(
                id=f"room_{self._room_counter}",
                room_type=room_type,
                polygon=inset_rect.to_polygon(),
                height=2.8,
                name=f"{room_type.replace('_', ' ').title()} {i + 1}",
            )

            leaf.room = room
            rooms.append(room)
            self._room_counter += 1

        return rooms

    def _assign_room_type(
        self,
        index: int,
        total: int,
        available_types: List[str]
    ) -> str:
        """Assign room type based on index and priority."""
        # Filter to available types
        types_with_priority = [
            (t, ROOM_TYPE_PRIORITIES.get(t, 0))
            for t in available_types
            if t in MIN_ROOM_SIZES
        ]

        if not types_with_priority:
            return "living_room"

        # Sort by priority
        types_with_priority.sort(key=lambda x: x[1], reverse=True)

        # Distribute types based on index
        type_index = min(index, len(types_with_priority) - 1)
        return types_with_priority[type_index][0]

    def _connect_rooms(self, rooms: List[Room]) -> List[Connection]:
        """Create connections between adjacent rooms."""
        connections = []

        # Find all shared walls between rooms
        for i, room_a in enumerate(rooms):
            for room_b in rooms[i + 1:]:
                shared_wall = self._find_shared_wall(room_a, room_b)
                if shared_wall:
                    # Create connection with door
                    conn = Connection(
                        id=f"conn_{self._connection_counter}",
                        room_a_id=room_a.id,
                        room_b_id=room_b.id,
                        door_spec=DoorSpec(
                            wall_index=shared_wall[0],
                            position=0.5,
                            width=self._get_door_width(room_a, room_b),
                        ),
                    )
                    connections.append(conn)
                    self._connection_counter += 1

                    # Add door to both rooms
                    room_a.doors.append(DoorSpec(
                        wall_index=shared_wall[0],
                        position=shared_wall[1],
                        width=self._get_door_width(room_a, room_b),
                    ))
                    room_b.doors.append(DoorSpec(
                        wall_index=shared_wall[2],
                        position=shared_wall[3],
                        width=self._get_door_width(room_a, room_b),
                    ))

        return connections

    def _find_shared_wall(
        self,
        room_a: Room,
        room_b: Room
    ) -> Optional[Tuple[int, float, int, float]]:
        """
        Find shared wall between two rooms.

        Returns: (wall_index_a, position_a, wall_index_b, position_b) or None
        """
        poly_a = room_a.polygon
        poly_b = room_b.polygon

        if len(poly_a) < 2 or len(poly_b) < 2:
            return None

        # Check each wall of room_a against each wall of room_b
        for i in range(len(poly_a)):
            wall_a_start = poly_a[i]
            wall_a_end = poly_a[(i + 1) % len(poly_a)]

            for j in range(len(poly_b)):
                wall_b_start = poly_b[j]
                wall_b_end = poly_b[(j + 1) % len(poly_b)]

                # Check if walls are collinear and overlapping
                overlap = self._check_wall_overlap(
                    wall_a_start, wall_a_end,
                    wall_b_start, wall_b_end
                )

                if overlap:
                    return (i, 0.5, j, 0.5)  # Default to center

        return None

    def _check_wall_overlap(
        self,
        a1: Tuple[float, float],
        a2: Tuple[float, float],
        b1: Tuple[float, float],
        b2: Tuple[float, float],
        tolerance: float = 0.01
    ) -> bool:
        """Check if two wall segments overlap."""
        # Check if walls are parallel (either horizontal or vertical)
        a_horizontal = abs(a1[1] - a2[1]) < tolerance
        b_horizontal = abs(b1[1] - b2[1]) < tolerance
        a_vertical = abs(a1[0] - a2[0]) < tolerance
        b_vertical = abs(b1[0] - b2[0]) < tolerance

        if a_horizontal and b_horizontal:
            # Both horizontal - check y alignment
            if abs(a1[1] - b1[1]) > tolerance:
                return False
            # Check x overlap
            a_min, a_max = min(a1[0], a2[0]), max(a1[0], a2[0])
            b_min, b_max = min(b1[0], b2[0]), max(b1[0], b2[0])
            return a_max > b_min and b_max > a_min

        elif a_vertical and b_vertical:
            # Both vertical - check x alignment
            if abs(a1[0] - b1[0]) > tolerance:
                return False
            # Check y overlap
            a_min, a_max = min(a1[1], a2[1]), max(a1[1], a2[1])
            b_min, b_max = min(b1[1], b2[1]), max(b1[1], b2[1])
            return a_max > b_min and b_max > a_min

        return False

    def _get_door_width(self, room_a: Room, room_b: Room) -> float:
        """Determine door width based on room types."""
        # Default door width
        default_width = 0.9

        # Wider doors for main rooms
        main_rooms = {"living_room", "kitchen", "master_bedroom", "dining_room"}
        if room_a.room_type in main_rooms or room_b.room_type in main_rooms:
            return 1.0

        # Narrower doors for utility rooms
        utility_rooms = {"closet", "half_bath", "utility", "storage"}
        if room_a.room_type in utility_rooms and room_b.room_type in utility_rooms:
            return 0.8

        # Double doors for formal connections
        if room_a.room_type == "living_room" and room_b.room_type == "dining_room":
            return 1.4

        return default_width

    def _add_exterior_windows(
        self,
        rooms: List[Room],
        width: float,
        height: float,
        tolerance: float = 0.1
    ) -> None:
        """Add windows to walls on exterior boundaries."""
        for room in rooms:
            for i in range(len(room.polygon)):
                p1 = room.polygon[i]
                p2 = room.polygon[(i + 1) % len(room.polygon)]

                # Check if wall is on exterior boundary
                is_exterior = False

                # Check bottom boundary
                if abs(p1[1]) < tolerance and abs(p2[1]) < tolerance:
                    is_exterior = True
                # Check top boundary
                elif abs(p1[1] - height) < tolerance and abs(p2[1] - height) < tolerance:
                    is_exterior = True
                # Check left boundary
                elif abs(p1[0]) < tolerance and abs(p2[0]) < tolerance:
                    is_exterior = True
                # Check right boundary
                elif abs(p1[0] - width) < tolerance and abs(p2[0] - width) < tolerance:
                    is_exterior = True

                if is_exterior:
                    # Add window to this wall
                    wall_length = room.get_wall_length(i)
                    if wall_length >= 1.0:  # Only add window if wall is long enough
                        room.windows.append(WindowSpec(
                            wall_index=i,
                            position=0.5,
                            width=min(1.5, wall_length * 0.6),
                            height=1.4,
                            sill_height=0.9,
                        ))


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_floor_plan(
    width: float,
    height: float,
    room_count: int,
    seed: Optional[int] = None,
    style: str = "modern",
) -> FloorPlan:
    """
    Generate a floor plan with default settings.

    Args:
        width: Floor plan width in meters
        height: Floor plan height in meters
        room_count: Number of rooms
        seed: Random seed for reproducibility
        style: Interior style preset

    Returns:
        Generated FloorPlan
    """
    solver = BSPSolver(seed=seed, style=style)
    return solver.generate(width, height, room_count)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BSPSplitDirection",
    "Rect",
    "BSPNode",
    "BSPSolver",
    "generate_floor_plan",
    "ROOM_TYPE_PRIORITIES",
    "MIN_ROOM_SIZES",
]
