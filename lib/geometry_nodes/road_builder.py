"""
Road Builder Node Group

Consumes JSON road networks from L-System generator and creates road geometry.
Handles lanes, markings, curbs, and intersections.

Implements REQ-GN-02: Road Builder Node Group.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import json
import math


class RoadType(Enum):
    """Road type classification."""
    HIGHWAY = "highway"
    ARTERIAL = "arterial"
    COLLECTOR = "collector"
    LOCAL = "local"
    RESIDENTIAL = "residential"
    ALLEY = "alley"


class LaneType(Enum):
    """Lane type classification."""
    TRAVEL = "travel"
    TURN = "turn"
    BIKE = "bike"
    BUS = "bus"
    PARKING = "parking"
    EMERGENCY = "emergency"


class IntersectionType(Enum):
    """Intersection type classification."""
    FOUR_WAY = "4way"
    THREE_WAY_T = "3way_t"
    THREE_WAY_Y = "3way_y"
    ROUNDABOUT = "roundabout"
    OVERPASS = "overpass"


@dataclass
class LaneSpec:
    """
    Lane specification.

    Attributes:
        lane_id: Unique lane identifier
        lane_type: Type of lane
        width: Lane width in meters
        direction: Travel direction (1, -1, or 0 for bidirectional)
        marking: Lane marking type
    """
    lane_id: str = ""
    lane_type: str = "travel"
    width: float = 3.5
    direction: int = 1
    marking: str = "solid_white"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lane_id": self.lane_id,
            "lane_type": self.lane_type,
            "width": self.width,
            "direction": self.direction,
            "marking": self.marking,
        }


@dataclass
class RoadSegment:
    """
    Road segment specification.

    Attributes:
        segment_id: Unique segment identifier
        start_node: Starting node ID
        end_node: Ending node ID
        control_points: Bezier curve control points
        road_type: Road type classification
        lanes: Lane specifications
        speed_limit: Speed limit in km/h
        has_sidewalk: Whether road has sidewalks
        has_median: Whether road has median
        surface: Road surface type
    """
    segment_id: str = ""
    start_node: str = ""
    end_node: str = ""
    control_points: List[Tuple[float, float]] = field(default_factory=list)
    road_type: str = "local"
    lanes: List[LaneSpec] = field(default_factory=list)
    speed_limit: float = 50.0
    has_sidewalk: bool = True
    has_median: bool = False
    surface: str = "asphalt"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segment_id": self.segment_id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "control_points": [list(p) for p in self.control_points],
            "road_type": self.road_type,
            "lanes": [l.to_dict() for l in self.lanes],
            "speed_limit": self.speed_limit,
            "has_sidewalk": self.has_sidewalk,
            "has_median": self.has_median,
            "surface": self.surface,
        }

    @property
    def total_width(self) -> float:
        """Calculate total road width including lanes."""
        return sum(lane.width for lane in self.lanes)

    @property
    def lane_count(self) -> int:
        """Get number of lanes."""
        return len(self.lanes)


@dataclass
class IntersectionGeometry:
    """
    Intersection geometry specification.

    Attributes:
        intersection_id: Unique intersection identifier
        position: Center position (x, y)
        intersection_type: Type of intersection
        radius: Radius for roundabout
        legs: Connected road segment IDs
        signalized: Whether traffic signals present
        crosswalks: Crosswalk specifications
    """
    intersection_id: str = ""
    position: Tuple[float, float] = (0.0, 0.0)
    intersection_type: str = "4way"
    radius: float = 10.0
    legs: List[str] = field(default_factory=list)
    signalized: bool = False
    crosswalks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intersection_id": self.intersection_id,
            "position": list(self.position),
            "intersection_type": self.intersection_type,
            "radius": self.radius,
            "legs": self.legs,
            "signalized": self.signalized,
            "crosswalks": self.crosswalks,
        }


@dataclass
class RoadNetwork:
    """
    Complete road network specification.

    Attributes:
        network_id: Network identifier
        segments: Road segments
        intersections: Intersection geometries
        bounds: Network bounding box
    """
    network_id: str = ""
    segments: List[RoadSegment] = field(default_factory=list)
    intersections: List[IntersectionGeometry] = field(default_factory=list)
    bounds: Tuple[float, float, float, float] = (0.0, 0.0, 100.0, 100.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "network_id": self.network_id,
            "segments": [s.to_dict() for s in self.segments],
            "intersections": [i.to_dict() for i in self.intersections],
            "bounds": list(self.bounds),
        }


# =============================================================================
# ROAD TYPE TEMPLATES
# =============================================================================

ROAD_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "highway": {
        "lanes": [
            {"type": "travel", "width": 3.75, "direction": 1},
            {"type": "travel", "width": 3.75, "direction": 1},
            {"type": "emergency", "width": 3.0, "direction": 1},
        ],
        "speed_limit": 120,
        "has_sidewalk": False,
        "has_median": True,
        "surface": "asphalt",
    },
    "arterial": {
        "lanes": [
            {"type": "travel", "width": 3.5, "direction": 1},
            {"type": "travel", "width": 3.5, "direction": 1},
            {"type": "turn", "width": 3.0, "direction": 0},
        ],
        "speed_limit": 60,
        "has_sidewalk": True,
        "has_median": True,
        "surface": "asphalt",
    },
    "collector": {
        "lanes": [
            {"type": "travel", "width": 3.5, "direction": 1},
            {"type": "parking", "width": 2.5, "direction": 0},
        ],
        "speed_limit": 50,
        "has_sidewalk": True,
        "has_median": False,
        "surface": "asphalt",
    },
    "local": {
        "lanes": [
            {"type": "travel", "width": 3.0, "direction": 0},
            {"type": "parking", "width": 2.0, "direction": 0},
        ],
        "speed_limit": 40,
        "has_sidewalk": True,
        "has_median": False,
        "surface": "asphalt",
    },
    "residential": {
        "lanes": [
            {"type": "travel", "width": 3.0, "direction": 0},
        ],
        "speed_limit": 30,
        "has_sidewalk": True,
        "has_median": False,
        "surface": "asphalt",
    },
}


# =============================================================================
# SURFACE MATERIALS
# =============================================================================

SURFACE_MATERIALS: Dict[str, Dict[str, Any]] = {
    "asphalt": {
        "color": "#2F2F2F",
        "roughness": 0.85,
        "bump_strength": 0.3,
    },
    "concrete": {
        "color": "#808080",
        "roughness": 0.7,
        "bump_strength": 0.2,
    },
    "brick": {
        "color": "#8B4513",
        "roughness": 0.8,
        "bump_strength": 0.4,
        "pattern": "herringbone",
    },
    "cobblestone": {
        "color": "#696969",
        "roughness": 0.75,
        "bump_strength": 0.5,
        "pattern": "cobble",
    },
    "gravel": {
        "color": "#A0522D",
        "roughness": 0.95,
        "bump_strength": 0.6,
    },
}


class RoadBuilder:
    """
    Builds road geometry from L-System generated networks.

    Consumes JSON output from LSystemRoads and generates geometry
    for Blender's Geometry Nodes system.

    Usage:
        builder = RoadBuilder()
        network = builder.build_from_json(road_network_json)
        # Pass network to GN Road Builder node group
    """

    def __init__(
        self,
        default_lane_width: float = 3.5,
        curb_height: float = 0.15,
        sidewalk_width: float = 1.5,
    ):
        """
        Initialize road builder.

        Args:
            default_lane_width: Default lane width
            curb_height: Curb height in meters
            sidewalk_width: Default sidewalk width
        """
        self.default_lane_width = default_lane_width
        self.curb_height = curb_height
        self.sidewalk_width = sidewalk_width

    def build_from_json(self, network_json: str) -> RoadNetwork:
        """
        Build road network from JSON.

        Args:
            network_json: JSON string from LSystemRoads

        Returns:
            RoadNetwork specification
        """
        data = json.loads(network_json)
        return self.build_from_dict(data)

    def build_from_dict(self, network_data: Dict[str, Any]) -> RoadNetwork:
        """
        Build road network from dictionary.

        Args:
            network_data: Network dictionary from LSystemRoads

        Returns:
            RoadNetwork specification
        """
        network_id = network_data.get("network_id", "network_0")

        # Build segments
        segments = []
        for edge_data in network_data.get("edges", []):
            segment = self._build_segment(edge_data)
            segments.append(segment)

        # Build intersections
        intersections = []
        for node_data in network_data.get("nodes", []):
            if node_data.get("type") in ["intersection_4way", "intersection_3way", "roundabout"]:
                intersection = self._build_intersection(node_data)
                intersections.append(intersection)

        # Calculate bounds
        all_points = []
        for seg in segments:
            all_points.extend(seg.control_points)
        for inter in intersections:
            all_points.append(inter.position)

        if all_points:
            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            bounds = (min(xs), min(ys), max(xs), max(ys))
        else:
            bounds = (0.0, 0.0, 100.0, 100.0)

        return RoadNetwork(
            network_id=network_id,
            segments=segments,
            intersections=intersections,
            bounds=bounds,
        )

    def _build_segment(self, edge_data: Dict[str, Any]) -> RoadSegment:
        """Build road segment from edge data."""
        segment_id = edge_data.get("id", "segment_0")
        road_type = edge_data.get("road_type", "local")

        # Get template for road type
        template = ROAD_TEMPLATES.get(road_type, ROAD_TEMPLATES["local"])

        # Create lanes from template
        lanes = []
        for i, lane_data in enumerate(template.get("lanes", [])):
            lane = LaneSpec(
                lane_id=f"{segment_id}_lane_{i}",
                lane_type=lane_data.get("type", "travel"),
                width=lane_data.get("width", self.default_lane_width),
                direction=lane_data.get("direction", 1),
            )
            lanes.append(lane)

        # Override with custom lanes if provided
        if "lanes" in edge_data:
            lanes = []
            for i, lane_data in enumerate(edge_data["lanes"]):
                lane = LaneSpec(
                    lane_id=f"{segment_id}_lane_{i}",
                    lane_type=lane_data.get("type", "travel"),
                    width=lane_data.get("width", self.default_lane_width),
                    direction=lane_data.get("direction", 1),
                )
                lanes.append(lane)

        # Parse control points
        control_points = []
        for point in edge_data.get("curve", []):
            control_points.append(tuple(point))

        return RoadSegment(
            segment_id=segment_id,
            start_node=edge_data.get("from", ""),
            end_node=edge_data.get("to", ""),
            control_points=control_points,
            road_type=road_type,
            lanes=lanes,
            speed_limit=edge_data.get("speed_limit", template.get("speed_limit", 50)),
            has_sidewalk=edge_data.get("has_sidewalk", template.get("has_sidewalk", True)),
            has_median=edge_data.get("has_median", template.get("has_median", False)),
            surface=edge_data.get("surface", template.get("surface", "asphalt")),
        )

    def _build_intersection(self, node_data: Dict[str, Any]) -> IntersectionGeometry:
        """Build intersection from node data."""
        node_type = node_data.get("type", "intersection_4way")

        # Map node type to intersection type
        type_map = {
            "intersection_4way": "4way",
            "intersection_3way": "3way_t",
            "roundabout": "roundabout",
        }

        return IntersectionGeometry(
            intersection_id=node_data.get("id", "intersection_0"),
            position=tuple(node_data.get("position", [0.0, 0.0])),
            intersection_type=type_map.get(node_type, "4way"),
            radius=node_data.get("radius", 10.0),
            legs=node_data.get("connections", []),
            signalized=node_data.get("signalized", False),
            crosswalks=node_data.get("crosswalks", []),
        )

    def to_gn_input(self, network: RoadNetwork) -> Dict[str, Any]:
        """
        Convert network to Geometry Nodes input format.

        Args:
            network: Road network specification

        Returns:
            GN-compatible input dictionary
        """
        return {
            "version": "1.0",
            "network": network.to_dict(),
            "global_settings": {
                "default_lane_width": self.default_lane_width,
                "curb_height": self.curb_height,
                "sidewalk_width": self.sidewalk_width,
            },
            "materials": SURFACE_MATERIALS,
        }

    def calculate_curve_length(self, segment: RoadSegment) -> float:
        """
        Calculate approximate curve length.

        Args:
            segment: Road segment

        Returns:
            Approximate length in meters
        """
        points = segment.control_points
        if len(points) < 2:
            return 0.0

        length = 0.0
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            length += math.sqrt(dx * dx + dy * dy)

        return length


class RoadBuilderGN:
    """
    Geometry Nodes interface for road building.

    Creates node group structure for Blender that consumes
    road network data and generates 3D geometry.
    """

    @staticmethod
    def create_node_group_spec() -> Dict[str, Any]:
        """
        Create specification for Road Builder node group.

        Returns:
            Node group specification
        """
        return {
            "name": "Road_Builder",
            "inputs": {
                "Network_Data": {
                    "type": "STRING",
                    "subtype": "JSON",
                    "description": "JSON road network from L-system",
                },
                "Default_Lane_Width": {
                    "type": "VALUE",
                    "default": 3.5,
                    "min": 2.0,
                    "max": 5.0,
                },
                "Curb_Height": {
                    "type": "VALUE",
                    "default": 0.15,
                    "min": 0.0,
                    "max": 0.3,
                },
                "Generate_Markings": {
                    "type": "BOOLEAN",
                    "default": True,
                },
                "Generate_Curbs": {
                    "type": "BOOLEAN",
                    "default": True,
                },
            },
            "outputs": {
                "Geometry": {
                    "type": "GEOMETRY",
                    "description": "Combined road geometry",
                },
                "Road_Surface": {
                    "type": "GEOMETRY",
                    "description": "Road surface mesh",
                },
                "Markings": {
                    "type": "GEOMETRY",
                    "description": "Lane markings",
                },
                "Curbs": {
                    "type": "GEOMETRY",
                    "description": "Curb geometry",
                },
                "Intersections": {
                    "type": "GEOMETRY",
                    "description": "Intersection meshes",
                },
            },
            "node_tree": {
                "type": "geometry",
                "nodes": [
                    {"type": "Input", "name": "Network Data Input"},
                    {"type": "JSON_Parse", "name": "Parse Network Data"},
                    {"type": "Curve_Primitive", "name": "Create Road Curves"},
                    {"type": "Mesh_Extrude", "name": "Create Road Surface"},
                    {"type": "Mesh_Boolean", "name": "Create Intersections"},
                    {"type": "Join_Geometry", "name": "Combine Geometry"},
                    {"type": "Output", "name": "Geometry Output"},
                ],
            },
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def build_road_network(network_data: Dict[str, Any], **kwargs) -> RoadNetwork:
    """
    Build road network from data.

    Args:
        network_data: Network dictionary
        **kwargs: RoadBuilder options

    Returns:
        RoadNetwork specification
    """
    builder = RoadBuilder(**kwargs)
    return builder.build_from_dict(network_data)


def network_to_gn_format(network: RoadNetwork, **kwargs) -> Dict[str, Any]:
    """
    Convert network to GN input format.

    Args:
        network: Road network
        **kwargs: RoadBuilder options

    Returns:
        GN-compatible input
    """
    builder = RoadBuilder(**kwargs)
    return builder.to_gn_input(network)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RoadType",
    "LaneType",
    "IntersectionType",
    # Data classes
    "LaneSpec",
    "RoadSegment",
    "IntersectionGeometry",
    "RoadNetwork",
    # Constants
    "ROAD_TEMPLATES",
    "SURFACE_MATERIALS",
    # Classes
    "RoadBuilder",
    "RoadBuilderGN",
    # Functions
    "build_road_network",
    "network_to_gn_format",
]
