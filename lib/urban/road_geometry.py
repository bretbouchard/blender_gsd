"""
Road Geometry Builder

Converts road network JSON to road geometry for Blender.
Consumes RoadNetwork JSON output and generates road mesh data.

Implements REQ-UR-02: Road Geometry (lanes, markings, curbs - GN from JSON).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math

from .types import RoadNetwork, RoadEdge, RoadNode, LaneConfig


class RoadSurfaceType(Enum):
    """Road surface materials."""
    ASPHALT = "asphalt"
    CONCRETE = "concrete"
    COBBLESTONE = "cobblestone"
    GRAVEL = "gravel"
    DIRT = "dirt"
    BRICK = "brick"


@dataclass
class LaneConfig:
    """Lane configuration for geometry."""
    count: int = 2
    width: float = 3.5
    has_center_line: bool = True
    has_edge_lines: bool = True
    has_lane_markings: bool = True
    marking_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class RoadSegment:
    """
    Road segment geometry data.

    Attributes:
        edge_id: Source edge ID
        start_pos: Start position (x, y, z)
        end_pos: End position (x, y, z)
        control_points: Bezier control points
        width: Total road width
        lane_config: Lane configuration
        has_curb: Whether road has curbs
        curb_height: Curb height in meters
        surface_type: Surface material type
    """
    edge_id: str = ""
    start_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    end_pos: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    control_points: List[Tuple[float, float, float]] = field(default_factory=list)
    width: float = 10.0
    lane_config: Optional[LaneConfig] = None
    has_curb: bool = True
    curb_height: float = 0.15
    surface_type: str = "asphalt"

    @property
    def length(self) -> float:
        """Calculate segment length."""
        if self.control_points:
            # Approximate bezier length
            total = 0.0
            points = [self.start_pos] + self.control_points + [self.end_pos]
            for i in range(len(points) - 1):
                dx = points[i + 1][0] - points[i][0]
                dy = points[i + 1][1] - points[i][1]
                dz = points[i + 1][2] - points[i][2]
                total += math.sqrt(dx*dx + dy*dy + dz*dz)
            return total
        else:
            dx = self.end_pos[0] - self.start_pos[0]
            dy = self.end_pos[1] - self.start_pos[1]
            return math.sqrt(dx*dx + dy*dy)

    @property
    def direction(self) -> float:
        """Calculate direction angle in radians."""
        dx = self.end_pos[0] - self.start_pos[0]
        dy = self.end_pos[1] - self.start_pos[1]
        return math.atan2(dy, dx)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "edge_id": self.edge_id,
            "start_pos": list(self.start_pos),
            "end_pos": list(self.end_pos),
            "control_points": [list(p) for p in self.control_points],
            "length": self.length,
            "direction": self.direction,
            "width": self.width,
            "has_curb": self.has_curb,
            "curb_height": self.curb_height,
            "surface_type": self.surface_type,
        }


@dataclass
class RoadGeometry:
    """
    Complete road geometry for a network.

    Attributes:
        segments: List of road segments
        total_length: Total road length
        total_area: Total road surface area
    """
    segments: List[RoadSegment] = field(default_factory=list)
    total_length: float = 0.0
    total_area: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segments": [s.to_dict() for s in self.segments],
            "total_length": self.total_length,
            "total_area": self.total_area,
            "segment_count": len(self.segments),
        }


class RoadGeometryBuilder:
    """
    Converts road networks to geometry data.

    Processes road network JSON and generates geometry for roads,
    curbs, sidewalks, and lane markings.

    Usage:
        builder = RoadGeometryBuilder()
        geometry = builder.build_from_network(network)
    """

    def __init__(
        self,
        default_width: float = 10.0,
        default_curb_height: float = 0.15,
        default_sidewalk_width: float = 1.5,
    ):
        """
        Initialize geometry builder.

        Args:
            default_width: Default road width
            default_curb_height: Default curb height
            default_sidewalk_width: Default sidewalk width
        """
        self.default_width = default_width
        self.default_curb_height = default_curb_height
        self.default_sidewalk_width = default_sidewalk_width

    def build_from_network(self, network: RoadNetwork) -> RoadGeometry:
        """
        Build road geometry from network.

        Args:
            network: RoadNetwork to process

        Returns:
            RoadGeometry with all segments
        """
        geometry = RoadGeometry()

        # Create lookup for nodes
        node_lookup = {n.id: n for n in network.nodes}

        for edge in network.edges:
            segment = self._create_segment(edge, node_lookup)
            if segment:
                geometry.segments.append(segment)
                geometry.total_length += segment.length
                geometry.total_area += segment.length * segment.width

        return geometry

    def _create_segment(
        self,
        edge: RoadEdge,
        node_lookup: Dict[str, RoadNode]
    ) -> Optional[RoadSegment]:
        """Create road segment from edge."""
        start_node = node_lookup.get(edge.from_node)
        end_node = node_lookup.get(edge.to_node)

        if not start_node or not end_node:
            return None

        # Calculate width from lane config
        width = edge.lanes.total_width if edge.lanes else self.default_width

        # Create segment
        segment = RoadSegment(
            edge_id=edge.id,
            start_pos=(start_node.position[0], start_node.position[1], start_node.elevation),
            end_pos=(end_node.position[0], end_node.position[1], end_node.elevation),
            width=width,
            has_curb=True,
            curb_height=self.default_curb_height,
            surface_type=edge.surface,
        )

        # Add curve points
        if edge.curve_points:
            segment.control_points = [
                (p[0], p[1], 0.0) for p in edge.curve_points
            ]

        return segment


def create_road_geometry_from_network(network: RoadNetwork) -> RoadGeometry:
    """
    Convenience function to create road geometry.

    Args:
        network: RoadNetwork to process

    Returns:
        RoadGeometry with all segments
    """
    builder = RoadGeometryBuilder()
    return builder.build_from_network(network)


# =============================================================================
# BLENDER INTEGRATION
# =============================================================================

def create_blender_roads(geometry: RoadGeometry, collection: Any = None) -> List[Any]:
    """
    Create Blender road meshes from geometry.

    Args:
        geometry: RoadGeometry to convert
        collection: Optional Blender collection

    Returns:
        List of created mesh objects
    """
    try:
        import bpy
        import bmesh
        from mathutils import Vector, Matrix
    except ImportError:
        raise ImportError("Blender required for road mesh creation")

    objects = []

    for i, segment in enumerate(geometry.segments):
        mesh = bpy.data.meshes.new(f"road_{i}")
        obj = bpy.data.objects.new(f"road_{i}", mesh)

        bm = bmesh.new()

        # Create road as extruded curve
        width = segment.width
        length = segment.length
        half_width = width / 2

        # Create road surface (simplified rectangle)
        direction = segment.direction
        cos_d = math.cos(direction)
        sin_d = math.sin(direction)

        # Perpendicular vector
        perp_x = -sin_d * half_width
        perp_y = cos_d * half_width

        # Forward vector
        fwd_x = cos_d * length
        fwd_y = sin_d * length

        # Create vertices
        sx, sy, sz = segment.start_pos
        v1 = bm.verts.new((sx - perp_x, sy - perp_y, sz + 0.01))
        v2 = bm.verts.new((sx + perp_x, sy + perp_y, sz + 0.01))
        v3 = bm.verts.new((sx + fwd_x + perp_x, sy + fwd_y + perp_y, sz + 0.01))
        v4 = bm.verts.new((sx + fwd_x - perp_x, sy + fwd_y - perp_y, sz + 0.01))

        bm.verts.ensure_lookup_table()
        bm.faces.new([v1, v2, v3, v4])

        # Add curb if enabled
        if segment.has_curb:
            curb_h = segment.curb_height
            v5 = bm.verts.new((sx - perp_x - 0.15, sy - perp_y - 0.15, sz + curb_h))
            v6 = bm.verts.new((sx - perp_x, sy - perp_y, sz))
            v7 = bm.verts.new((sx + fwd_x - perp_x, sy + fwd_y - perp_y, sz))
            v8 = bm.verts.new((sx + fwd_x - perp_x - 0.15, sy + fwd_y - perp_y - 0.15, sz + curb_h))

            bm.faces.new([v5, v6, v7, v8])

        bm.to_mesh(mesh)
        bm.free()

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
    "RoadSurfaceType",
    "LaneConfig",
    "RoadSegment",
    "RoadGeometry",
    "RoadGeometryBuilder",
    "create_road_geometry_from_network",
    "create_blender_roads",
]
