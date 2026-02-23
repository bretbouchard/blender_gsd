"""
Wall Builder

Converts floor plan JSON to wall geometry for Blender.
Consumes FloorPlan JSON output and generates wall meshes.

Implements REQ-IL-02: Wall System with openings.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math

from .types import (
    FloorPlan,
    Room,
    DoorSpec,
    WindowSpec,
)


class WallType(Enum):
    """Wall type classification."""
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    PARTITION = "partition"
    LOAD_BEARING = "load_bearing"


@dataclass
class WallOpening:
    """
    Opening in a wall (door or window).

    Attributes:
        opening_type: Type of opening ("door" or "window")
        position: Position along wall (0-1 normalized)
        width: Opening width in meters
        height: Opening height in meters
        sill_height: Height from floor to sill (windows only)
        header_height: Height from floor to top of opening
    """
    opening_type: str = "door"
    position: float = 0.5
    width: float = 0.9
    height: float = 2.1
    sill_height: float = 0.0
    header_height: float = 2.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "opening_type": self.opening_type,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "sill_height": self.sill_height,
            "header_height": self.header_height,
        }


@dataclass
class WallSegment:
    """
    Single wall segment with openings.

    Attributes:
        start: Start point (x, y)
        end: End point (x, y)
        height: Wall height
        thickness: Wall thickness
        wall_type: Type of wall
        openings: List of openings in this wall
        material: Material preset
        room_id: ID of room this wall belongs to
    """
    start: Tuple[float, float] = (0.0, 0.0)
    end: Tuple[float, float] = (1.0, 0.0)
    height: float = 2.8
    thickness: float = 0.15
    wall_type: str = "interior"
    openings: List[WallOpening] = field(default_factory=list)
    material: str = "drywall_white"
    room_id: str = ""

    @property
    def length(self) -> float:
        """Calculate wall length."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.sqrt(dx * dx + dy * dy)

    @property
    def angle(self) -> float:
        """Calculate wall angle in radians."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.atan2(dy, dx)

    @property
    def center(self) -> Tuple[float, float]:
        """Calculate wall center point."""
        return (
            (self.start[0] + self.end[0]) / 2,
            (self.start[1] + self.end[1]) / 2,
        )

    def get_point_at_position(self, position: float) -> Tuple[float, float]:
        """Get point along wall at normalized position (0-1)."""
        return (
            self.start[0] + (self.end[0] - self.start[0]) * position,
            self.start[1] + (self.end[1] - self.start[1]) * position,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": list(self.start),
            "end": list(self.end),
            "length": self.length,
            "angle": self.angle,
            "center": list(self.center),
            "height": self.height,
            "thickness": self.thickness,
            "wall_type": self.wall_type,
            "openings": [o.to_dict() for o in self.openings],
            "material": self.material,
            "room_id": self.room_id,
        }


@dataclass
class WallGeometry:
    """
    Generated wall geometry data.

    Contains all data needed to create wall meshes in Blender.
    """
    segments: List[WallSegment] = field(default_factory=list)
    total_length: float = 0.0
    exterior_length: float = 0.0
    interior_length: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segments": [s.to_dict() for s in self.segments],
            "total_length": self.total_length,
            "exterior_length": self.exterior_length,
            "interior_length": self.interior_length,
            "segment_count": len(self.segments),
        }


class WallBuilder:
    """
    Converts floor plans to wall geometry.

    Processes floor plan JSON and generates wall segments with proper
    openings for doors and windows.

    Usage:
        builder = WallBuilder()
        geometry = builder.build_from_plan(floor_plan)
        # Use geometry to create Blender meshes
    """

    def __init__(
        self,
        default_height: float = 2.8,
        default_thickness: float = 0.15,
        exterior_thickness: float = 0.25,
    ):
        """
        Initialize wall builder.

        Args:
            default_height: Default wall height
            default_thickness: Default interior wall thickness
            exterior_thickness: Exterior wall thickness
        """
        self.default_height = default_height
        self.default_thickness = default_thickness
        self.exterior_thickness = exterior_thickness

    def build_from_plan(self, plan: FloorPlan) -> WallGeometry:
        """
        Build wall geometry from floor plan.

        Args:
            plan: FloorPlan to process

        Returns:
            WallGeometry with all wall segments
        """
        geometry = WallGeometry()
        processed_edges = set()  # Track processed edges to avoid duplicates

        for room in plan.rooms:
            segments = self._process_room(room, plan, processed_edges)
            geometry.segments.extend(segments)

        # Calculate totals
        for segment in geometry.segments:
            geometry.total_length += segment.length
            if segment.wall_type == "exterior":
                geometry.exterior_length += segment.length
            else:
                geometry.interior_length += segment.length

        return geometry

    def _process_room(
        self,
        room: Room,
        plan: FloorPlan,
        processed_edges: set,
    ) -> List[WallSegment]:
        """Process room walls into segments."""
        segments = []
        polygon = room.polygon

        if len(polygon) < 3:
            return segments

        # Check if room is on exterior boundary
        bounds = room.bounds
        is_on_exterior = (
            abs(bounds[0]) < 0.1 or  # Left
            abs(bounds[1]) < 0.1 or  # Bottom
            abs(bounds[2] - plan.dimensions[0]) < 0.1 or  # Right
            abs(bounds[3] - plan.dimensions[1]) < 0.1  # Top
        )

        for i in range(len(polygon)):
            start = polygon[i]
            end = polygon[(i + 1) % len(polygon)]

            # Create edge key for deduplication
            edge_key = self._make_edge_key(start, end)
            if edge_key in processed_edges:
                continue
            processed_edges.add(edge_key)

            # Check if this wall is on exterior
            is_exterior = self._is_exterior_wall(start, end, plan.dimensions)

            # Create segment
            segment = WallSegment(
                start=start,
                end=end,
                height=room.height,
                thickness=self.exterior_thickness if is_exterior else self.default_thickness,
                wall_type="exterior" if is_exterior else "interior",
                material=room.wall_material,
                room_id=room.id,
            )

            # Add openings
            self._add_openings_to_segment(segment, room, i)

            segments.append(segment)

        return segments

    def _make_edge_key(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        tolerance: float = 0.01
    ) -> str:
        """Create unique key for edge regardless of direction."""
        # Sort points to ensure consistent key
        if (p1[0], p1[1]) < (p2[0], p2[1]):
            return f"{p1[0]:.2f},{p1[1]:.2f}-{p2[0]:.2f},{p2[1]:.2f}"
        else:
            return f"{p2[0]:.2f},{p2[1]:.2f}-{p1[0]:.2f},{p1[1]:.2f}"

    def _is_exterior_wall(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        dimensions: Tuple[float, float],
        tolerance: float = 0.1
    ) -> bool:
        """Check if wall is on exterior boundary."""
        # Check if both points are on the same boundary edge
        on_left = abs(start[0]) < tolerance and abs(end[0]) < tolerance
        on_right = abs(start[0] - dimensions[0]) < tolerance and abs(end[0] - dimensions[0]) < tolerance
        on_bottom = abs(start[1]) < tolerance and abs(end[1]) < tolerance
        on_top = abs(start[1] - dimensions[1]) < tolerance and abs(end[1] - dimensions[1]) < tolerance

        return on_left or on_right or on_bottom or on_top

    def _add_openings_to_segment(
        self,
        segment: WallSegment,
        room: Room,
        wall_index: int
    ) -> None:
        """Add door and window openings to segment."""
        # Add doors
        for door in room.doors:
            if door.wall_index == wall_index:
                segment.openings.append(WallOpening(
                    opening_type="door",
                    position=door.position,
                    width=door.width,
                    height=door.height,
                    sill_height=0.0,
                    header_height=door.height,
                ))

        # Add windows
        for window in room.windows:
            if window.wall_index == wall_index:
                segment.openings.append(WallOpening(
                    opening_type="window",
                    position=window.position,
                    width=window.width,
                    height=window.height,
                    sill_height=window.sill_height,
                    header_height=window.sill_height + window.height,
                ))


def create_wall_geometry_from_plan(plan: FloorPlan) -> WallGeometry:
    """
    Convenience function to create wall geometry from floor plan.

    Args:
        plan: FloorPlan to process

    Returns:
        WallGeometry with all wall segments
    """
    builder = WallBuilder()
    return builder.build_from_plan(plan)


# =============================================================================
# BLENDER INTEGRATION (Optional - only when bpy is available)
# =============================================================================

def create_blender_walls(geometry: WallGeometry, collection: Any = None) -> List[Any]:
    """
    Create Blender wall meshes from geometry.

    Args:
        geometry: WallGeometry to convert
        collection: Optional Blender collection

    Returns:
        List of created mesh objects
    """
    try:
        import bpy
        import bmesh
        from mathutils import Matrix
    except ImportError:
        raise ImportError("Blender required for wall mesh creation")

    objects = []

    for i, segment in enumerate(geometry.segments):
        mesh = bpy.data.meshes.new(f"wall_{i}")
        obj = bpy.data.objects.new(f"wall_{i}", mesh)

        bm = bmesh.new()

        # Create wall geometry
        length = segment.length
        height = segment.height
        thickness = segment.thickness

        half_length = length / 2
        half_thickness = thickness / 2

        # Create vertices for wall box
        # Front face
        v1 = bm.verts.new((-half_length, -half_thickness, 0))
        v2 = bm.verts.new((half_length, -half_thickness, 0))
        v3 = bm.verts.new((half_length, -half_thickness, height))
        v4 = bm.verts.new((-half_length, -half_thickness, height))

        # Back face
        v5 = bm.verts.new((-half_length, half_thickness, 0))
        v6 = bm.verts.new((half_length, half_thickness, 0))
        v7 = bm.verts.new((half_length, half_thickness, height))
        v8 = bm.verts.new((-half_length, half_thickness, height))

        bm.verts.ensure_lookup_table()

        # Create faces
        bm.faces.new([v1, v2, v3, v4])  # Front
        bm.faces.new([v6, v5, v8, v7])  # Back
        bm.faces.new([v5, v1, v4, v8])  # Left
        bm.faces.new([v2, v6, v7, v3])  # Right
        bm.faces.new([v4, v3, v7, v8])  # Top
        bm.faces.new([v1, v5, v6, v2])  # Bottom

        # TODO: Add opening cutouts using boolean operations

        bm.to_mesh(mesh)
        bm.free()

        # Position and rotate wall
        center = segment.center
        angle = segment.angle
        obj.location = (center[0], center[1], 0)
        obj.rotation_euler = (0, 0, angle)

        # Add to collection
        if collection:
            collection.objects.link(obj)
        else:
            bpy.context.collection.objects.link(obj)

        objects.append(obj)

    return objects


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "WallType",
    "WallOpening",
    "WallSegment",
    "WallGeometry",
    "WallBuilder",
    "create_wall_geometry_from_plan",
    "create_blender_walls",
]
