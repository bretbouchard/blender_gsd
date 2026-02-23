"""
Urban Infrastructure Types

Data structures for road networks, intersections, and urban elements.
Designed for JSON serialization for Geometry Nodes consumption.

Implements REQ-UR-01: Road Network Generator types.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import json


class NodeType(Enum):
    """Road network node types."""
    INTERSECTION_4WAY = "intersection_4way"
    INTERSECTION_3WAY = "intersection_3way"  # T-junction
    INTERSECTION_5WAY = "intersection_5way"
    ROUNDABOUT = "roundabout"
    DEAD_END = "dead_end"
    CURVE_POINT = "curve_point"
    BRIDGE_START = "bridge_start"
    BRIDGE_END = "bridge_end"
    TUNNEL_START = "tunnel_start"
    TUNNEL_END = "tunnel_end"
    HIGHWAY_EXIT = "highway_exit"
    HIGHWAY_ENTRY = "highway_entry"


class EdgeType(Enum):
    """Road edge types."""
    ROAD = "road"
    HIGHWAY = "highway"
    RESIDENTIAL = "residential"
    SERVICE_ROAD = "service_road"
    ALLEY = "alley"
    PEDESTRIAN = "pedestrian"
    BIKE_LANE = "bike_lane"
    BRIDGE = "bridge"
    TUNNEL = "tunnel"


class RoadType(Enum):
    """Road classification."""
    HIGHWAY = "highway"
    ARTERIAL = "arterial"
    COLLECTOR = "collector"
    LOCAL = "local"
    RESIDENTIAL = "residential"
    SERVICE = "service"
    ALLEY = "alley"
    PRIVATE = "private"
    PEDESTRIAN = "pedestrian"


class IntersectionType(Enum):
    """Intersection types."""
    FOUR_WAY = "four_way"
    THREE_WAY_T = "three_way_t"
    THREE_WAY_Y = "three_way_y"
    FIVE_WAY = "five_way"
    ROUNDABOUT = "roundabout"
    TRAFFIC_CIRCLE = "traffic_circle"
    STAGGERED = "staggered"
    GRADE_SEPARATED = "grade_separated"


class UrbanStyle(Enum):
    """Urban environment style presets."""
    MODERN_URBAN = "modern_urban"
    DOWNTOWN = "downtown"
    SUBURBAN = "suburban"
    INDUSTRIAL = "industrial"
    HISTORIC = "historic"
    EUROPEAN = "european"
    AMERICAN_GRID = "american_grid"
    ASIAN_MEGA = "asian_mega"
    VILLAGE = "village"
    CAMPUS = "campus"


@dataclass
class RoadNode:
    """
    Node in road network (intersection or endpoint).

    Attributes:
        id: Unique node identifier
        position: Position (x, y) in meters
        node_type: Type of node
        elevation: Height above ground level
        connections: List of connected edge IDs
        has_traffic_light: Whether intersection has traffic light
        has_crosswalk: Whether intersection has crosswalk
    """
    id: str = "node_0"
    position: Tuple[float, float] = (0.0, 0.0)
    node_type: str = "intersection_4way"
    elevation: float = 0.0
    connections: List[str] = field(default_factory=list)
    has_traffic_light: bool = False
    has_crosswalk: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "position": list(self.position),
            "node_type": self.node_type,
            "elevation": self.elevation,
            "connections": self.connections,
            "has_traffic_light": self.has_traffic_light,
            "has_crosswalk": self.has_crosswalk,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoadNode":
        """Create from dictionary."""
        return cls(
            id=data.get("id", "node_0"),
            position=tuple(data.get("position", (0.0, 0.0))),
            node_type=data.get("node_type", "intersection_4way"),
            elevation=data.get("elevation", 0.0),
            connections=data.get("connections", []),
            has_traffic_light=data.get("has_traffic_light", False),
            has_crosswalk=data.get("has_crosswalk", True),
        )


@dataclass
class LaneConfig:
    """
    Lane configuration for a road.

    Attributes:
        count: Number of lanes
        width: Lane width in meters
        direction: Traffic direction ("both", "forward", "backward")
        has_center_turn: Whether road has center turn lane
        has_bike_lane: Whether road has bike lane
        has_parking: Whether road has parking lanes
        has_sidewalk: Whether road has sidewalks
        sidewalk_width: Sidewalk width in meters
    """
    count: int = 2
    width: float = 3.5
    direction: str = "both"
    has_center_turn: bool = False
    has_bike_lane: bool = False
    has_parking: bool = False
    has_sidewalk: bool = True
    sidewalk_width: float = 1.5

    @property
    def total_width(self) -> float:
        """Calculate total road width."""
        total = self.count * self.width
        if self.has_center_turn:
            total += self.width
        if self.has_bike_lane:
            total += 1.5 * 2  # Bike lanes on both sides
        if self.has_parking:
            total += 2.5 * 2  # Parking on both sides
        if self.has_sidewalk:
            total += self.sidewalk_width * 2
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "width": self.width,
            "direction": self.direction,
            "has_center_turn": self.has_center_turn,
            "has_bike_lane": self.has_bike_lane,
            "has_parking": self.has_parking,
            "has_sidewalk": self.has_sidewalk,
            "sidewalk_width": self.sidewalk_width,
            "total_width": self.total_width,
        }


@dataclass
class RoadEdge:
    """
    Edge in road network (road segment between nodes).

    Attributes:
        id: Unique edge identifier
        from_node: Starting node ID
        to_node: Ending node ID
        road_type: Type of road
        name: Road name
        lanes: Lane configuration
        curve_points: Intermediate curve points (for curved roads)
        speed_limit: Speed limit in km/h
        has_median: Whether road has center median
        median_width: Median width in meters
        surface: Road surface type
    """
    id: str = "edge_0"
    from_node: str = ""
    to_node: str = ""
    road_type: str = "local"
    name: str = ""
    lanes: LaneConfig = field(default_factory=LaneConfig)
    curve_points: List[Tuple[float, float]] = field(default_factory=list)
    speed_limit: int = 50
    has_median: bool = False
    median_width: float = 2.0
    surface: str = "asphalt"

    @property
    def length(self) -> float:
        """Calculate approximate edge length."""
        if not self.curve_points:
            return 0.0

        total = 0.0
        points = self.curve_points
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            total += (dx * dx + dy * dy) ** 0.5
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "road_type": self.road_type,
            "name": self.name,
            "lanes": self.lanes.to_dict(),
            "curve_points": [list(p) for p in self.curve_points],
            "length": self.length,
            "speed_limit": self.speed_limit,
            "has_median": self.has_median,
            "median_width": self.median_width,
            "surface": self.surface,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoadEdge":
        """Create from dictionary."""
        lanes_data = data.get("lanes", {})
        lanes = LaneConfig(**lanes_data) if lanes_data else LaneConfig()

        return cls(
            id=data.get("id", "edge_0"),
            from_node=data.get("from_node", ""),
            to_node=data.get("to_node", ""),
            road_type=data.get("road_type", "local"),
            name=data.get("name", ""),
            lanes=lanes,
            curve_points=[tuple(p) for p in data.get("curve_points", [])],
            speed_limit=data.get("speed_limit", 50),
            has_median=data.get("has_median", False),
            median_width=data.get("median_width", 2.0),
            surface=data.get("surface", "asphalt"),
        )


@dataclass
class RoadNetwork:
    """
    Complete road network with nodes and edges.

    This is the main output of the L-System generator and input to Geometry Nodes.

    Attributes:
        version: JSON format version
        dimensions: Network dimensions (width, height)
        nodes: List of road nodes (intersections)
        edges: List of road edges (road segments)
        style: Urban style preset
        seed: Random seed used for generation
    """
    version: str = "1.0"
    dimensions: Tuple[float, float] = (100.0, 100.0)
    nodes: List[RoadNode] = field(default_factory=list)
    edges: List[RoadEdge] = field(default_factory=list)
    style: str = "modern_urban"
    seed: Optional[int] = None

    def get_node_by_id(self, node_id: str) -> Optional[RoadNode]:
        """Get node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edge_by_id(self, edge_id: str) -> Optional[RoadEdge]:
        """Get edge by ID."""
        for edge in self.edges:
            if edge.id == edge_id:
                return edge
        return None

    def get_edges_from_node(self, node_id: str) -> List[RoadEdge]:
        """Get all edges connected to a node."""
        return [e for e in self.edges if e.from_node == node_id or e.to_node == node_id]

    def get_connected_nodes(self, node_id: str) -> List[str]:
        """Get IDs of all nodes connected to the given node."""
        connected = set()
        for edge in self.edges:
            if edge.from_node == node_id:
                connected.add(edge.to_node)
            elif edge.to_node == node_id:
                connected.add(edge.from_node)
        return list(connected)

    def is_connected(self) -> bool:
        """Check if all nodes are connected (no isolated segments)."""
        if not self.nodes:
            return True

        visited = set()
        queue = [self.nodes[0].id]
        visited.add(self.nodes[0].id)

        while queue:
            current = queue.pop(0)
            for neighbor in self.get_connected_nodes(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(self.nodes)

    @property
    def total_road_length(self) -> float:
        """Calculate total road length."""
        return sum(edge.length for edge in self.edges)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "dimensions": list(self.dimensions),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "style": self.style,
            "seed": self.seed,
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "total_road_length": self.total_road_length,
                "is_connected": self.is_connected(),
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoadNetwork":
        """Create from dictionary."""
        nodes = [RoadNode.from_dict(n) for n in data.get("nodes", [])]
        edges = [RoadEdge.from_dict(e) for e in data.get("edges", [])]

        return cls(
            version=data.get("version", "1.0"),
            dimensions=tuple(data.get("dimensions", (100.0, 100.0))),
            nodes=nodes,
            edges=edges,
            style=data.get("style", "modern_urban"),
            seed=data.get("seed"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string for GN consumption."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "RoadNetwork":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, filepath: str) -> None:
        """Save network to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "RoadNetwork":
        """Load network from JSON file."""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())


# =============================================================================
# VALIDATION
# =============================================================================

def validate_node(node: RoadNode) -> List[str]:
    """Validate node configuration, return list of errors."""
    errors = []

    if not node.id:
        errors.append("Node ID is required")

    if len(node.connections) == 1 and node.node_type not in ["dead_end", "bridge_end", "tunnel_end"]:
        errors.append(f"Node {node.id}: single connection should be dead_end")

    return errors


def validate_edge(edge: RoadEdge) -> List[str]:
    """Validate edge configuration, return list of errors."""
    errors = []

    if not edge.id:
        errors.append("Edge ID is required")

    if not edge.from_node:
        errors.append(f"Edge {edge.id}: from_node is required")

    if not edge.to_node:
        errors.append(f"Edge {edge.id}: to_node is required")

    if edge.lanes.count < 1:
        errors.append(f"Edge {edge.id}: lane count must be positive")

    return errors


def validate_network(network: RoadNetwork) -> List[str]:
    """Validate road network, return list of errors."""
    errors = []

    if network.dimensions[0] <= 0 or network.dimensions[1] <= 0:
        errors.append("Network dimensions must be positive")

    if not network.nodes:
        errors.append("Network must have at least one node")

    # Validate nodes
    node_ids = set()
    for node in network.nodes:
        errors.extend(validate_node(node))
        if node.id in node_ids:
            errors.append(f"Duplicate node ID: {node.id}")
        node_ids.add(node.id)

    # Validate edges reference valid nodes
    for edge in network.edges:
        errors.extend(validate_edge(edge))
        if edge.from_node and edge.from_node not in node_ids:
            errors.append(f"Edge {edge.id}: from_node '{edge.from_node}' not found")
        if edge.to_node and edge.to_node not in node_ids:
            errors.append(f"Edge {edge.id}: to_node '{edge.to_node}' not found")

    return errors


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "NodeType",
    "EdgeType",
    "RoadType",
    "IntersectionType",
    "UrbanStyle",
    # Dataclasses
    "RoadNode",
    "LaneConfig",
    "RoadEdge",
    "RoadNetwork",
    # Validation
    "validate_node",
    "validate_edge",
    "validate_network",
]
