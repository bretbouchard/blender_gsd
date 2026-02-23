"""
Room Builder Node Group

Consumes JSON floor plans from BSP solver and generates room geometry.
Creates walls, floors, ceilings with openings for doors/windows.

Implements REQ-GN-01: Room Builder Node Group.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import json


class WallType(Enum):
    """Wall type classification."""
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    PARTITION = "partition"
    LOAD_BEARING = "load_bearing"


class OpeningType(Enum):
    """Opening type classification."""
    DOOR = "door"
    WINDOW = "window"
    ARCHWAY = "archway"
    PASSAGE = "passage"


@dataclass
class WallSpec:
    """
    Wall specification for geometry generation.

    Attributes:
        wall_id: Unique wall identifier
        start: Start point (x, y)
        end: End point (x, y)
        height: Wall height
        thickness: Wall thickness
        wall_type: Wall type classification
        openings: List of openings (doors, windows)
        material: Material assignment
    """
    wall_id: str = ""
    start: Tuple[float, float] = (0.0, 0.0)
    end: Tuple[float, float] = (1.0, 0.0)
    height: float = 3.0
    thickness: float = 0.15
    wall_type: str = "interior"
    openings: List[Dict[str, Any]] = field(default_factory=list)
    material: str = "drywall"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "wall_id": self.wall_id,
            "start": list(self.start),
            "end": list(self.end),
            "height": self.height,
            "thickness": self.thickness,
            "wall_type": self.wall_type,
            "openings": self.openings,
            "material": self.material,
        }

    @property
    def length(self) -> float:
        """Calculate wall length."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return (dx**2 + dy**2) ** 0.5

    @property
    def angle(self) -> float:
        """Calculate wall angle in radians."""
        import math
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.atan2(dy, dx)


@dataclass
class OpeningSpec:
    """
    Opening specification for walls.

    Attributes:
        opening_type: Type of opening
        position: Position along wall (0-1)
        width: Opening width
        height: Opening height
        sill_height: Height of sill (for windows)
        frame_width: Frame thickness
        frame_depth: Frame depth into wall
    """
    opening_type: str = "door"
    position: float = 0.5
    width: float = 0.9
    height: float = 2.1
    sill_height: float = 0.0
    frame_width: float = 0.05
    frame_depth: float = 0.02

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "opening_type": self.opening_type,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "sill_height": self.sill_height,
            "frame_width": self.frame_width,
            "frame_depth": self.frame_depth,
        }


@dataclass
class RoomGeometry:
    """
    Generated room geometry data.

    Attributes:
        room_id: Room identifier
        walls: Generated wall specs
        floor: Floor polygon
        ceiling: Ceiling polygon
        bounds: Bounding box (min_x, min_y, max_x, max_y)
    """
    room_id: str = ""
    walls: List[WallSpec] = field(default_factory=list)
    floor: List[Tuple[float, float]] = field(default_factory=list)
    ceiling: List[Tuple[float, float]] = field(default_factory=list)
    bounds: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "room_id": self.room_id,
            "walls": [w.to_dict() for w in self.walls],
            "floor": [list(f) for f in self.floor],
            "ceiling": [list(c) for c in self.ceiling],
            "bounds": list(self.bounds),
        }


# =============================================================================
# STANDARD OPENING DIMENSIONS
# =============================================================================

STANDARD_DOORS: Dict[str, OpeningSpec] = {
    "standard": OpeningSpec(
        opening_type="door",
        width=0.9,
        height=2.1,
        sill_height=0.0,
    ),
    "wide": OpeningSpec(
        opening_type="door",
        width=1.2,
        height=2.1,
        sill_height=0.0,
    ),
    "double": OpeningSpec(
        opening_type="door",
        width=1.8,
        height=2.1,
        sill_height=0.0,
    ),
    "sliding": OpeningSpec(
        opening_type="door",
        width=2.0,
        height=2.1,
        sill_height=0.0,
    ),
}

STANDARD_WINDOWS: Dict[str, OpeningSpec] = {
    "standard": OpeningSpec(
        opening_type="window",
        width=1.2,
        height=1.2,
        sill_height=0.9,
    ),
    "picture": OpeningSpec(
        opening_type="window",
        width=1.8,
        height=1.4,
        sill_height=0.8,
    ),
    "tall": OpeningSpec(
        opening_type="window",
        width=0.9,
        height=1.8,
        sill_height=0.3,
    ),
    "skylight": OpeningSpec(
        opening_type="window",
        width=0.8,
        height=0.8,
        sill_height=0.0,  # In ceiling
    ),
}


# =============================================================================
# WALL MATERIALS
# =============================================================================

WALL_MATERIALS: Dict[str, Dict[str, Any]] = {
    "drywall": {
        "color": "#F5F5F5",
        "roughness": 0.7,
        "specular": 0.1,
    },
    "concrete": {
        "color": "#808080",
        "roughness": 0.9,
        "specular": 0.05,
    },
    "brick": {
        "color": "#8B4513",
        "roughness": 0.85,
        "specular": 0.1,
        "pattern": "brick_bond",
    },
    "wood_panel": {
        "color": "#DEB887",
        "roughness": 0.6,
        "specular": 0.2,
        "pattern": "wood_grain",
    },
    "glass": {
        "color": "#E0FFFF",
        "roughness": 0.1,
        "specular": 0.9,
        "transmission": 0.9,
    },
}


class RoomBuilder:
    """
    Builds room geometry from BSP-generated floor plans.

    Consumes JSON output from BSPSolver and generates geometry
    for Blender's Geometry Nodes system.

    Usage:
        builder = RoomBuilder()
        geometry = builder.build_from_json(floor_plan_json)
        # Pass geometry to GN Room Builder node group
    """

    def __init__(
        self,
        wall_height: float = 3.0,
        wall_thickness: float = 0.15,
        floor_thickness: float = 0.02,
    ):
        """
        Initialize room builder.

        Args:
            wall_height: Default wall height
            wall_thickness: Default wall thickness
            floor_thickness: Floor slab thickness
        """
        self.wall_height = wall_height
        self.wall_thickness = wall_thickness
        self.floor_thickness = floor_thickness

    def build_from_json(self, floor_plan_json: str) -> List[RoomGeometry]:
        """
        Build room geometry from JSON floor plan.

        Args:
            floor_plan_json: JSON string from BSPSolver

        Returns:
            List of RoomGeometry for each room
        """
        data = json.loads(floor_plan_json)
        return self.build_from_dict(data)

    def build_from_dict(self, floor_plan: Dict[str, Any]) -> List[RoomGeometry]:
        """
        Build room geometry from dictionary floor plan.

        Args:
            floor_plan: Floor plan dictionary from BSPSolver

        Returns:
            List of RoomGeometry for each room
        """
        rooms = []

        for room_data in floor_plan.get("rooms", []):
            room = self._build_room(room_data)
            rooms.append(room)

        return rooms

    def _build_room(self, room_data: Dict[str, Any]) -> RoomGeometry:
        """Build single room from data."""
        room_id = room_data.get("id", "room_0")
        polygon = room_data.get("polygon", [])
        room_type = room_data.get("type", "generic")

        # Create walls from polygon
        walls = []
        for i in range(len(polygon)):
            start = tuple(polygon[i])
            end = tuple(polygon[(i + 1) % len(polygon)])

            wall = WallSpec(
                wall_id=f"{room_id}_wall_{i}",
                start=start,
                end=end,
                height=self.wall_height,
                thickness=self.wall_thickness,
                wall_type="interior",
            )

            # Add openings from room data
            for opening in room_data.get("doors", []):
                if opening.get("wall") == i:
                    wall.openings.append(self._create_door_opening(opening))

            for opening in room_data.get("windows", []):
                if opening.get("wall") == i:
                    wall.openings.append(self._create_window_opening(opening))

            walls.append(wall)

        # Calculate bounds
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        bounds = (min(xs), min(ys), max(xs), max(ys))

        return RoomGeometry(
            room_id=room_id,
            walls=walls,
            floor=[tuple(p) for p in polygon],
            ceiling=[tuple(p) for p in polygon],
            bounds=bounds,
        )

    def _create_door_opening(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create door opening specification."""
        door_type = data.get("type", "standard")
        spec = STANDARD_DOORS.get(door_type, STANDARD_DOORS["standard"])

        return {
            "opening_type": "door",
            "position": data.get("position", 0.5),
            "width": spec.width,
            "height": spec.height,
            "sill_height": 0.0,
        }

    def _create_window_opening(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create window opening specification."""
        window_type = data.get("type", "standard")
        spec = STANDARD_WINDOWS.get(window_type, STANDARD_WINDOWS["standard"])

        return {
            "opening_type": "window",
            "position": data.get("position", 0.5),
            "width": spec.width,
            "height": spec.height,
            "sill_height": spec.sill_height,
        }

    def to_gn_input(self, rooms: List[RoomGeometry]) -> Dict[str, Any]:
        """
        Convert rooms to Geometry Nodes input format.

        This creates the data structure that GN Room Builder
        node group expects as input.

        Args:
            rooms: List of room geometries

        Returns:
            GN-compatible input dictionary
        """
        return {
            "version": "1.0",
            "rooms": [r.to_dict() for r in rooms],
            "global_settings": {
                "wall_height": self.wall_height,
                "wall_thickness": self.wall_thickness,
                "floor_thickness": self.floor_thickness,
            },
            "materials": WALL_MATERIALS,
        }


class RoomBuilderGN:
    """
    Geometry Nodes interface for room building.

    Creates node group structure for Blender that consumes
    room geometry data and generates 3D geometry.

    Note: This creates the Python structure that describes
    the node group. Actual node creation happens in Blender.
    """

    @staticmethod
    def create_node_group_spec() -> Dict[str, Any]:
        """
        Create specification for Room Builder node group.

        Returns:
            Node group specification
        """
        return {
            "name": "Room_Builder",
            "inputs": {
                "Room_Data": {
                    "type": "STRING",
                    "subtype": "JSON",
                    "description": "JSON room data from BSP solver",
                },
                "Wall_Height": {
                    "type": "VALUE",
                    "default": 3.0,
                    "min": 1.0,
                    "max": 10.0,
                },
                "Wall_Thickness": {
                    "type": "VALUE",
                    "default": 0.15,
                    "min": 0.05,
                    "max": 0.5,
                },
                "Generate_Floor": {
                    "type": "BOOLEAN",
                    "default": True,
                },
                "Generate_Ceiling": {
                    "type": "BOOLEAN",
                    "default": True,
                },
            },
            "outputs": {
                "Geometry": {
                    "type": "GEOMETRY",
                    "description": "Combined room geometry",
                },
                "Wall_Mesh": {
                    "type": "GEOMETRY",
                    "description": "Wall geometry only",
                },
                "Floor_Mesh": {
                    "type": "GEOMETRY",
                    "description": "Floor geometry only",
                },
                "Opening_Mesh": {
                    "type": "GEOMETRY",
                    "description": "Door/window frame geometry",
                },
            },
            "node_tree": {
                "type": "geometry",
                "nodes": [
                    {"type": "Input", "name": "Room Data Input"},
                    {"type": "JSON_Parse", "name": "Parse Room Data"},
                    {"type": "Mesh_Primitive", "name": "Create Wall Mesh"},
                    {"type": "Mesh_Boolean", "name": "Cut Openings"},
                    {"type": "Join_Geometry", "name": "Combine Geometry"},
                    {"type": "Output", "name": "Geometry Output"},
                ],
            },
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def build_rooms(floor_plan: Dict[str, Any], **kwargs) -> List[RoomGeometry]:
    """
    Build room geometry from floor plan.

    Args:
        floor_plan: Floor plan dictionary
        **kwargs: RoomBuilder options

    Returns:
        List of room geometries
    """
    builder = RoomBuilder(**kwargs)
    return builder.build_from_dict(floor_plan)


def rooms_to_gn_format(rooms: List[RoomGeometry], **kwargs) -> Dict[str, Any]:
    """
    Convert rooms to GN input format.

    Args:
        rooms: Room geometries
        **kwargs: RoomBuilder options

    Returns:
        GN-compatible input
    """
    builder = RoomBuilder(**kwargs)
    return builder.to_gn_input(rooms)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "WallType",
    "OpeningType",
    # Data classes
    "WallSpec",
    "OpeningSpec",
    "RoomGeometry",
    # Constants
    "STANDARD_DOORS",
    "STANDARD_WINDOWS",
    "WALL_MATERIALS",
    # Classes
    "RoomBuilder",
    "RoomBuilderGN",
    # Functions
    "build_rooms",
    "rooms_to_gn_format",
]
