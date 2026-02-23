"""
Interior Layout Types

Data structures for floor plans, rooms, connections, and interior elements.
Designed for JSON serialization for Geometry Nodes consumption.

Implements REQ-IL-01: Floor Plan Generator types.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import json


class RoomType(Enum):
    """Room type classification."""
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    MASTER_BEDROOM = "master_bedroom"
    KITCHEN = "kitchen"
    DINING_ROOM = "dining_room"
    BATHROOM = "bathroom"
    MASTER_BATHROOM = "master_bathroom"
    HALF_BATH = "half_bath"
    OFFICE = "office"
    STUDY = "study"
    CLOSET = "closet"
    WALK_IN_CLOSET = "walk_in_closet"
    LAUNDRY = "laundry"
    UTILITY = "utility"
    HALLWAY = "hallway"
    FOYER = "foyer"
    GARAGE = "garage"
    STORAGE = "storage"
    BALCONY = "balcony"
    SUNROOM = "sunroom"
    DINING_AREA = "dining_area"  # Open plan dining
    FAMILY_ROOM = "family_room"
    DEN = "den"
    LIBRARY = "library"
    GYM = "gym"
    MEDIA_ROOM = "media_room"
    WINE_CELLAR = "wine_cellar"
    PANTRY = "pantry"
    MUDROOM = "mudroom"


class InteriorStyle(Enum):
    """Interior style presets."""
    MODERN = "modern"
    CONTEMPORARY = "contemporary"
    MINIMALIST = "minimalist"
    SCANDINAVIAN = "scandinavian"
    INDUSTRIAL = "industrial"
    MID_CENTURY = "mid_century"
    TRADITIONAL = "traditional"
    VICTORIAN = "victorian"
    ART_DECO = "art_deco"
    RUSTIC = "rustic"
    FARMHOUSE = "farmhouse"
    COASTAL = "coastal"
    BOHEMIAN = "bohemian"
    JAPANESE = "japanese"
    MEDITERRANEAN = "mediterranean"


class DoorType(Enum):
    """Door type classification."""
    STANDARD = "standard"
    POCKET = "pocket"
    SLIDING = "sliding"
    FRENCH = "french"
    BARN = "barn"
    DUTCH = "dutch"
    SALOON = "saloon"
    BI_FOLD = "bi_fold"
    ARCH = "arch"
    DOUBLE = "double"


class WindowType(Enum):
    """Window type classification."""
    SINGLE_HUNG = "single_hung"
    DOUBLE_HUNG = "double_hung"
    CASEMENT = "casement"
    AWNING = "awning"
    PICTURE = "picture"
    SLIDER = "slider"
    BAY = "bay"
    BOW = "bow"
    GARDEN = "garden"
    SKYLIGHT = "skylight"
    TRANSOM = "transom"


@dataclass
class DoorSpec:
    """
    Door specification for floor plan.

    Attributes:
        wall_index: Index of wall in room polygon (0-based)
        position: Position along wall (0-1 normalized)
        width: Door width in meters
        height: Door height in meters
        door_type: Type of door
        swing_direction: Direction door swings
    """
    wall_index: int = 0
    position: float = 0.5
    width: float = 0.9
    height: float = 2.1
    door_type: str = "standard"
    swing_direction: str = "in_right"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "wall_index": self.wall_index,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "door_type": self.door_type,
            "swing_direction": self.swing_direction,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DoorSpec":
        """Create from dictionary."""
        return cls(
            wall_index=data.get("wall_index", 0),
            position=data.get("position", 0.5),
            width=data.get("width", 0.9),
            height=data.get("height", 2.1),
            door_type=data.get("door_type", "standard"),
            swing_direction=data.get("swing_direction", "in_right"),
        )


@dataclass
class WindowSpec:
    """
    Window specification for floor plan.

    Attributes:
        wall_index: Index of wall in room polygon (0-based)
        position: Position along wall (0-1 normalized)
        width: Window width in meters
        height: Window height in meters
        sill_height: Height from floor to sill in meters
        window_type: Type of window
    """
    wall_index: int = 0
    position: float = 0.5
    width: float = 1.2
    height: float = 1.4
    sill_height: float = 0.9
    window_type: str = "double_hung"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "wall_index": self.wall_index,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "sill_height": self.sill_height,
            "window_type": self.window_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowSpec":
        """Create from dictionary."""
        return cls(
            wall_index=data.get("wall_index", 0),
            position=data.get("position", 0.5),
            width=data.get("width", 1.2),
            height=data.get("height", 1.4),
            sill_height=data.get("sill_height", 0.9),
            window_type=data.get("window_type", "double_hung"),
        )


@dataclass
class Room:
    """
    Room definition in a floor plan.

    Attributes:
        id: Unique room identifier
        room_type: Type of room
        polygon: List of (x, y) vertices defining room shape
        height: Room height in meters
        doors: List of door specifications
        windows: List of window specifications
        floor_material: Floor material preset
        wall_material: Wall material preset
        has_crown_molding: Whether room has crown molding
        has_baseboard: Whether room has baseboard
        name: Human-readable room name
    """
    id: str = "room_0"
    room_type: str = "living_room"
    polygon: List[Tuple[float, float]] = field(default_factory=list)
    height: float = 2.8
    doors: List[DoorSpec] = field(default_factory=list)
    windows: List[WindowSpec] = field(default_factory=list)
    floor_material: str = "hardwood_oak"
    wall_material: str = "drywall_white"
    has_crown_molding: bool = False
    has_baseboard: bool = True
    name: str = ""

    def __post_init__(self):
        """Set default name if not provided."""
        if not self.name:
            self.name = self.room_type.replace("_", " ").title()

    @property
    def center(self) -> Tuple[float, float]:
        """Calculate room center point."""
        if not self.polygon:
            return (0.0, 0.0)
        x_sum = sum(p[0] for p in self.polygon)
        y_sum = sum(p[1] for p in self.polygon)
        n = len(self.polygon)
        return (x_sum / n, y_sum / n)

    @property
    def area(self) -> float:
        """Calculate room area using shoelace formula."""
        if len(self.polygon) < 3:
            return 0.0

        n = len(self.polygon)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.polygon[i][0] * self.polygon[j][1]
            area -= self.polygon[j][0] * self.polygon[i][1]
        return abs(area) / 2.0

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get room bounding box (min_x, min_y, max_x, max_y)."""
        if not self.polygon:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p[0] for p in self.polygon]
        ys = [p[1] for p in self.polygon]
        return (min(xs), min(ys), max(xs), max(ys))

    def get_wall_length(self, wall_index: int) -> float:
        """Get length of a specific wall."""
        if not self.polygon or wall_index >= len(self.polygon):
            return 0.0
        p1 = self.polygon[wall_index]
        p2 = self.polygon[(wall_index + 1) % len(self.polygon)]
        return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "room_type": self.room_type,
            "polygon": [list(p) for p in self.polygon],
            "height": self.height,
            "center": list(self.center),
            "area": self.area,
            "doors": [d.to_dict() for d in self.doors],
            "windows": [w.to_dict() for w in self.windows],
            "floor_material": self.floor_material,
            "wall_material": self.wall_material,
            "has_crown_molding": self.has_crown_molding,
            "has_baseboard": self.has_baseboard,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        """Create from dictionary."""
        polygon = [tuple(p) for p in data.get("polygon", [])]
        doors = [DoorSpec.from_dict(d) for d in data.get("doors", [])]
        windows = [WindowSpec.from_dict(w) for w in data.get("windows", [])]

        return cls(
            id=data.get("id", "room_0"),
            room_type=data.get("room_type", "living_room"),
            polygon=polygon,
            height=data.get("height", 2.8),
            doors=doors,
            windows=windows,
            floor_material=data.get("floor_material", "hardwood_oak"),
            wall_material=data.get("wall_material", "drywall_white"),
            has_crown_molding=data.get("has_crown_molding", False),
            has_baseboard=data.get("has_baseboard", True),
            name=data.get("name", ""),
        )


@dataclass
class Connection:
    """
    Connection between two rooms (door/passageway).

    Attributes:
        id: Unique connection identifier
        room_a_id: First room ID
        room_b_id: Second room ID
        door_spec: Door specification (None for open passageway)
        is_open: Whether this is an open passageway (no door)
    """
    id: str = "conn_0"
    room_a_id: str = ""
    room_b_id: str = ""
    door_spec: Optional[DoorSpec] = None
    is_open: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "room_a_id": self.room_a_id,
            "room_b_id": self.room_b_id,
            "door_spec": self.door_spec.to_dict() if self.door_spec else None,
            "is_open": self.is_open,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Connection":
        """Create from dictionary."""
        door_data = data.get("door_spec")
        door_spec = DoorSpec.from_dict(door_data) if door_data else None

        return cls(
            id=data.get("id", "conn_0"),
            room_a_id=data.get("room_a_id", ""),
            room_b_id=data.get("room_b_id", ""),
            door_spec=door_spec,
            is_open=data.get("is_open", False),
        )


@dataclass
class FurniturePlacement:
    """
    Furniture placement specification.

    Attributes:
        furniture_type: Type of furniture
        position: Position in room (x, y, z)
        rotation: Rotation in degrees
        scale: Scale factor
        variant: Variant index
    """
    furniture_type: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0
    scale: float = 1.0
    variant: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "furniture_type": self.furniture_type,
            "position": list(self.position),
            "rotation": self.rotation,
            "scale": self.scale,
            "variant": self.variant,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FurniturePlacement":
        """Create from dictionary."""
        return cls(
            furniture_type=data.get("furniture_type", ""),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation=data.get("rotation", 0.0),
            scale=data.get("scale", 1.0),
            variant=data.get("variant", 0),
        )


@dataclass
class FloorPlan:
    """
    Complete floor plan with rooms, connections, and metadata.

    This is the main output of the BSP solver and input to Geometry Nodes.

    Attributes:
        version: JSON format version
        dimensions: Total floor plan dimensions (width, height)
        rooms: List of rooms
        connections: List of connections between rooms
        style: Interior style preset
        wall_height: Default wall height
        wall_thickness: Default wall thickness
        seed: Random seed used for generation
    """
    version: str = "1.0"
    dimensions: Tuple[float, float] = (10.0, 8.0)
    rooms: List[Room] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)
    style: str = "modern"
    wall_height: float = 2.8
    wall_thickness: float = 0.15
    seed: Optional[int] = None

    @property
    def total_area(self) -> float:
        """Calculate total floor area."""
        return sum(room.area for room in self.rooms)

    def get_room_by_id(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None

    def get_connected_rooms(self, room_id: str) -> List[str]:
        """Get IDs of all rooms connected to the given room."""
        connected = []
        for conn in self.connections:
            if conn.room_a_id == room_id:
                connected.append(conn.room_b_id)
            elif conn.room_b_id == room_id:
                connected.append(conn.room_a_id)
        return connected

    def is_connected(self) -> bool:
        """Check if all rooms are connected (no isolated rooms)."""
        if not self.rooms:
            return True

        # BFS to check connectivity
        visited = set()
        queue = [self.rooms[0].id]
        visited.add(self.rooms[0].id)

        while queue:
            current = queue.pop(0)
            for neighbor in self.get_connected_rooms(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(self.rooms)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "dimensions": list(self.dimensions),
            "rooms": [r.to_dict() for r in self.rooms],
            "connections": [c.to_dict() for c in self.connections],
            "style": self.style,
            "wall_height": self.wall_height,
            "wall_thickness": self.wall_thickness,
            "seed": self.seed,
            "total_area": self.total_area,
            "is_connected": self.is_connected(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FloorPlan":
        """Create from dictionary."""
        rooms = [Room.from_dict(r) for r in data.get("rooms", [])]
        connections = [Connection.from_dict(c) for c in data.get("connections", [])]

        return cls(
            version=data.get("version", "1.0"),
            dimensions=tuple(data.get("dimensions", (10.0, 8.0))),
            rooms=rooms,
            connections=connections,
            style=data.get("style", "modern"),
            wall_height=data.get("wall_height", 2.8),
            wall_thickness=data.get("wall_thickness", 0.15),
            seed=data.get("seed"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string for GN consumption."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "FloorPlan":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, filepath: str) -> None:
        """Save floor plan to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "FloorPlan":
        """Load floor plan from JSON file."""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())


# =============================================================================
# VALIDATION
# =============================================================================

def validate_room(room: Room) -> List[str]:
    """Validate room configuration, return list of errors."""
    errors = []

    if len(room.polygon) < 3:
        errors.append(f"Room {room.id}: polygon must have at least 3 vertices")

    if room.height <= 0:
        errors.append(f"Room {room.id}: height must be positive")

    for i, door in enumerate(room.doors):
        if door.width <= 0:
            errors.append(f"Room {room.id}, door {i}: width must be positive")
        if door.position < 0 or door.position > 1:
            errors.append(f"Room {room.id}, door {i}: position must be 0-1")

    for i, window in enumerate(room.windows):
        if window.width <= 0:
            errors.append(f"Room {room.id}, window {i}: width must be positive")
        if window.position < 0 or window.position > 1:
            errors.append(f"Room {room.id}, window {i}: position must be 0-1")

    return errors


def validate_floor_plan(plan: FloorPlan) -> List[str]:
    """Validate floor plan, return list of errors."""
    errors = []

    if plan.dimensions[0] <= 0 or plan.dimensions[1] <= 0:
        errors.append("Floor plan dimensions must be positive")

    if not plan.rooms:
        errors.append("Floor plan must have at least one room")

    # Validate individual rooms
    for room in plan.rooms:
        errors.extend(validate_room(room))

    # Validate connections reference valid rooms
    room_ids = {r.id for r in plan.rooms}
    for conn in plan.connections:
        if conn.room_a_id not in room_ids:
            errors.append(f"Connection {conn.id}: room_a_id '{conn.room_a_id}' not found")
        if conn.room_b_id not in room_ids:
            errors.append(f"Connection {conn.id}: room_b_id '{conn.room_b_id}' not found")

    # Check connectivity
    if not plan.is_connected():
        errors.append("Floor plan has isolated rooms (not all rooms connected)")

    return errors


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RoomType",
    "InteriorStyle",
    "DoorType",
    "WindowType",
    # Dataclasses
    "DoorSpec",
    "WindowSpec",
    "Room",
    "Connection",
    "FurniturePlacement",
    "FloorPlan",
    # Validation
    "validate_room",
    "validate_floor_plan",
]
