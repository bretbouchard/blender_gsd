"""
Road Builder Node Group - Codified from Urban System

Consumes JSON road networks from L-System generator and creates road geometry.
Handles lanes, markings, curbs, and intersections using NodeKit pattern.

Based on: Urban Road System (REQ-GN-02, REQ-UR-01)

Usage:
    from lib.geometry_nodes.road_builder import RoadBuilder, RoadNetworkGN

    # Create road from curve
    road = RoadBuilder.create("MainRoad")
    road.set_lanes(4).set_width(3.5).add_sidewalks().build()

    # Create from network data
    network_gn = RoadNetworkGN.create("CityGrid")
    network_gn.load_from_dict(network_data).build()

    # Display HUD
    from lib.geometry_nodes.road_builder import RoadHUD
    print(RoadHUD.display_road_types())
    print(RoadHUD.display_lane_config(4))
"""

from __future__ import annotations
import bpy
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
from enum import Enum
import json
import math

# Import NodeKit for node building
try:
    from ..nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

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


# =============================================================================
# DATA CLASSES
# =============================================================================

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


# =============================================================================
# ROAD BUILDER - NODEKIT PATTERN
# =============================================================================

class RoadBuilder:
    """
    Builds road geometry from curves using Geometry Nodes.

    Creates node group that generates road surface, markings, curbs.

    Cross-references:
    - KB Section 5: Scattering on roads
    - KB Section 15: Procedural patterns for markings
    - REQ-GN-02: Road Builder Node Group

    Usage:
        road = RoadBuilder.create("MainStreet")
        road.set_lanes(4).set_width(3.5).add_sidewalks().build()
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._created_nodes: dict = {}

        # Road configuration
        self._lane_count = 2
        self._lane_width = 3.5
        self._curb_height = 0.15
        self._sidewalk_width = 1.5
        self._has_sidewalk = True
        self._has_markings = True
        self._has_median = False
        self._surface_type = "asphalt"

    @classmethod
    def create(cls, name: str = "Road") -> "RoadBuilder":
        """
        Create road builder node tree.

        Args:
            name: Node tree name

        Returns:
            Configured RoadBuilder instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "Road"
    ) -> "RoadBuilder":
        """
        Create and attach to curve object via modifier.

        Args:
            obj: Curve object to use as road path
            name: Node tree name

        Returns:
            Configured RoadBuilder instance
        """
        mod = obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_road_type(cls, road_type: str, name: str = None) -> "RoadBuilder":
        """
        Create road from preset type.

        Args:
            road_type: Type from ROAD_TEMPLATES (highway, arterial, etc.)
            name: Optional node tree name

        Returns:
            Configured RoadBuilder with preset values
        """
        template = ROAD_TEMPLATES.get(road_type, ROAD_TEMPLATES["local"])
        instance = cls.create(name or f"Road_{road_type}")

        # Apply template
        instance._lane_count = len(template["lanes"])
        instance._has_sidewalk = template.get("has_sidewalk", True)
        instance._has_median = template.get("has_median", False)
        instance._surface_type = template.get("surface", "asphalt")

        return instance

    def _setup_interface(self) -> None:
        """Set up node group interface."""
        # Inputs
        self.node_tree.interface.new_socket(
            name="Curve", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Lane Count", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._lane_count, min_value=1, max_value=12
        )
        self.node_tree.interface.new_socket(
            name="Lane Width", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._lane_width, min_value=2.0, max_value=5.0
        )
        self.node_tree.interface.new_socket(
            name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._curb_height, min_value=0.0, max_value=0.5
        )
        self.node_tree.interface.new_socket(
            name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._sidewalk_width, min_value=0.0, max_value=5.0
        )
        self.node_tree.interface.new_socket(
            name="Resolution", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=12, min_value=3, max_value=64
        )

        # Boolean inputs
        self.node_tree.interface.new_socket(
            name="Generate Markings", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=True
        )
        self.node_tree.interface.new_socket(
            name="Generate Curbs", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=True
        )
        self.node_tree.interface.new_socket(
            name="Generate Sidewalks", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=True
        )

        # Outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Road Surface", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Markings", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Curbs", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_lanes(self, count: int) -> "RoadBuilder":
        """Set number of lanes."""
        self._lane_count = count
        return self

    def set_width(self, width: float) -> "RoadBuilder":
        """Set lane width in meters."""
        self._lane_width = width
        return self

    def set_curb_height(self, height: float) -> "RoadBuilder":
        """Set curb height in meters."""
        self._curb_height = height
        return self

    def add_sidewalks(self, width: float = 1.5) -> "RoadBuilder":
        """Enable sidewalks with given width."""
        self._has_sidewalk = True
        self._sidewalk_width = width
        return self

    def add_median(self) -> "RoadBuilder":
        """Enable road median."""
        self._has_median = True
        return self

    def set_surface(self, surface_type: str) -> "RoadBuilder":
        """Set road surface type."""
        self._surface_type = surface_type
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the road node tree.

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() or from_object() first")

        nk = self.nk
        x = 0

        # === INPUT ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === CALCULATE ROAD WIDTH ===
        # Multiply: Lane Count × Lane Width = Total Width
        mult_width = nk.n("ShaderNodeMath", "Calc Width", x=x, y=200)
        mult_width.operation = 'MULTIPLY'
        nk.link(group_in.outputs["Lane Count"], mult_width.inputs[0])
        nk.link(group_in.outputs["Lane Width"], mult_width.inputs[1])
        self._created_nodes['calc_width'] = mult_width
        x += 200

        # === CURVE TO MESH - ROAD SURFACE ===
        # Create curve from input and convert to mesh
        curve_to_mesh = nk.n(
            "GeometryNodeCurveToMesh",
            "Road Surface",
            x=x, y=0
        )
        nk.link(group_in.outputs["Curve"], curve_to_mesh.inputs["Curve"])

        # Create profile curve (rectangle for road)
        profile = nk.n("GeometryNodeCurvePrimitiveQuadrilateral", "Profile", x=x-100, y=-200)
        profile.mode = 'RECTANGLE'
        nk.link(mult_width.outputs[0], profile.inputs["Width"])
        nk.set(profile.inputs["Height"], 0.01)  # Thin road surface

        nk.link(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
        self._created_nodes['road_surface'] = curve_to_mesh
        self._created_nodes['profile'] = profile
        x += 300

        # Store road surface for output
        road_geo = curve_to_mesh

        # === LANE MARKINGS (if enabled) ===
        markings_geo = None
        if self._has_markings:
            # Create center line marking
            marking_profile = nk.n(
                "GeometryNodeCurvePrimitiveQuadrilateral",
                "Marking Profile",
                x=x-100, y=-400
            )
            marking_profile.mode = 'RECTANGLE'
            nk.set(marking_profile.inputs["Width"], 0.15)  # 15cm line
            nk.set(marking_profile.inputs["Height"], 0.02)  # Slight raised

            marking_mesh = nk.n(
                "GeometryNodeCurveToMesh",
                "Center Marking",
                x=x, y=-300
            )
            nk.link(group_in.outputs["Curve"], marking_mesh.inputs["Curve"])
            nk.link(marking_profile.outputs["Curve"], marking_mesh.inputs["Profile Curve"])

            self._created_nodes['marking_profile'] = marking_profile
            self._created_nodes['markings'] = marking_mesh
            markings_geo = marking_mesh
        x += 300

        # === CURBS (if enabled) ===
        curbs_geo = None
        curb_left = None
        curb_right = None

        # Create curb profiles and meshes
        curb_profile = nk.n(
            "GeometryNodeCurvePrimitiveQuadrilateral",
            "Curb Profile",
            x=x-100, y=-500
        )
        curb_profile.mode = 'RECTANGLE'
        nk.set(curb_profile.inputs["Width"], 0.3)  # 30cm curb
        nk.link(group_in.outputs["Curb Height"], curb_profile.inputs["Height"])

        # Left curb
        curb_left_mesh = nk.n("GeometryNodeCurveToMesh", "Left Curb", x=x, y=-400)
        nk.link(group_in.outputs["Curve"], curb_left_mesh.inputs["Curve"])
        nk.link(curb_profile.outputs["Curve"], curb_left_mesh.inputs["Profile Curve"])

        # Right curb (same curve, offset later)
        curb_right_mesh = nk.n("GeometryNodeCurveToMesh", "Right Curb", x=x, y=-550)
        nk.link(group_in.outputs["Curve"], curb_right_mesh.inputs["Curve"])
        nk.link(curb_profile.outputs["Curve"], curb_right_mesh.inputs["Profile Curve"])

        self._created_nodes['curb_profile'] = curb_profile
        self._created_nodes['curb_left'] = curb_left_mesh
        self._created_nodes['curb_right'] = curb_right_mesh

        # Join curbs
        join_curbs = nk.n("GeometryNodeJoinGeometry", "Join Curbs", x=x+200, y=-450)
        nk.link(curb_left_mesh.outputs["Mesh"], join_curbs.inputs["Geometry"])
        nk.link(curb_right_mesh.outputs["Mesh"], join_curbs.inputs["Geometry"])
        curbs_geo = join_curbs
        self._created_nodes['join_curbs'] = join_curbs
        x += 300

        # === JOIN ALL GEOMETRY ===
        join_all = nk.n("GeometryNodeJoinGeometry", "Join All", x=x, y=0)
        nk.link(road_geo.outputs["Mesh"], join_all.inputs["Geometry"])
        if markings_geo:
            nk.link(markings_geo.outputs["Mesh"], join_all.inputs["Geometry"])
        if curbs_geo:
            nk.link(curbs_geo.outputs["Geometry"], join_all.inputs["Geometry"])
        self._created_nodes['join_all'] = join_all
        x += 200

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=0)
        nk.link(join_all.outputs["Geometry"], group_out.inputs["Geometry"])
        nk.link(road_geo.outputs["Mesh"], group_out.inputs["Road Surface"])
        if markings_geo:
            nk.link(markings_geo.outputs["Mesh"], group_out.inputs["Markings"])
        if curbs_geo:
            nk.link(curbs_geo.outputs["Geometry"], group_out.inputs["Curbs"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class RoadNetworkGN:
    """
    Geometry Nodes interface for complete road networks.

    Takes L-System generated network data and creates full city layout.

    Cross-references:
    - KB Section 5: Network-based scattering
    - REQ-GN-02: Road Builder Node Group
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._network_data: Optional[Dict[str, Any]] = None
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "RoadNetwork") -> "RoadNetworkGN":
        """
        Create road network node tree.

        Args:
            name: Node tree name

        Returns:
            Configured RoadNetworkGN instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    def _setup_interface(self) -> None:
        """Set up node group interface."""
        # Inputs
        self.node_tree.interface.new_socket(
            name="Network Data", in_out='INPUT', socket_type='NodeSocketString'
        )
        self.node_tree.interface.new_socket(
            name="Default Lane Width", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=3.5, min_value=2.0, max_value=5.0
        )
        self.node_tree.interface.new_socket(
            name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=0.15, min_value=0.0, max_value=0.3
        )
        self.node_tree.interface.new_socket(
            name="Generate Markings", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=True
        )
        self.node_tree.interface.new_socket(
            name="Generate Curbs", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=True
        )

        # Outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Road Surfaces", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Intersections", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Markings", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def load_from_json(self, json_str: str) -> "RoadNetworkGN":
        """Load network from JSON string."""
        self._network_data = json.loads(json_str)
        return self

    def load_from_dict(self, data: Dict[str, Any]) -> "RoadNetworkGN":
        """Load network from dictionary."""
        self._network_data = data
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the network node tree.

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() first")

        nk = self.nk
        x = 0

        # === INPUT ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === PLACEHOLDER - Network parsing would go here ===
        # In practice, this would iterate over segments and create
        # curve primitives, then join them

        # Create a simple grid as placeholder
        grid = nk.n("GeometryNodeCurvePrimitiveGrid", "Grid", x=x, y=0)
        nk.set(grid.inputs["Vertices X"], 10)
        nk.set(grid.inputs["Vertices Y"], 10)
        nk.set(grid.inputs["Size X"], 100)
        nk.set(grid.inputs["Size Y"], 100)
        self._created_nodes['grid'] = grid
        x += 300

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=0)
        nk.link(grid.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class IntersectionBuilder:
    """
    Builds intersection geometry.

    Cross-references:
    - KB Section 15: Procedural intersection patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._created_nodes: dict = {}
        self._intersection_type = "4way"
        self._radius = 10.0

    @classmethod
    def create(cls, name: str = "Intersection") -> "IntersectionBuilder":
        """Create intersection builder node tree."""
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    def _setup_interface(self) -> None:
        """Set up node group interface."""
        # Inputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Radius", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=10.0, min_value=5.0, max_value=50.0
        )
        self.node_tree.interface.new_socket(
            name="Type", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=0, min_value=0, max_value=3
        )

        # Outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_type(self, intersection_type: str) -> "IntersectionBuilder":
        """Set intersection type (4way, 3way_t, roundabout)."""
        self._intersection_type = intersection_type
        return self

    def set_radius(self, radius: float) -> "IntersectionBuilder":
        """Set intersection radius."""
        self._radius = radius
        return self

    def build(self) -> bpy.types.NodeTree:
        """Build intersection geometry."""
        if not self.nk:
            raise RuntimeError("Call create() first")

        nk = self.nk
        x = 0

        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # Create circular intersection surface
        circle = nk.n("GeometryNodeMeshCircle", "Intersection Circle", x=x, y=0)
        nk.link(group_in.outputs["Radius"], circle.inputs["Radius"])
        nk.set(circle.inputs["Vertices"], 32)
        self._created_nodes['circle'] = circle
        x += 200

        # Fill the circle
        fill = nk.n("GeometryNodeMeshFill", "Fill", x=x, y=0)
        nk.link(circle.outputs["Mesh"], fill.inputs["Mesh"])
        self._created_nodes['fill'] = fill
        x += 200

        group_out = nk.group_output(x=x, y=0)
        nk.link(fill.outputs["Mesh"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree


# =============================================================================
# ROAD HUD - VISUALIZATION SYSTEM
# =============================================================================

class RoadHUD:
    """
    Heads-Up Display for road system visualization.

    Provides formatted console output for road configuration,
    lane setups, and network statistics.

    Cross-references:
    - KB Section 5: Road visualization
    - KB Section 15: Pattern reference
    """

    @staticmethod
    def display_road_types() -> str:
        """Display road type reference table."""
        lines = [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║                    ROAD TYPE REFERENCE                        ║",
            "╠═══════════════╦═════════╦══════════╦═══════════╦════════════╣",
            "║ Type          ║ Lanes   ║ Width    ║ Speed     ║ Sidewalk   ║",
            "╠═══════════════╬═════════╬══════════╬═══════════╬════════════╣",
        ]

        type_info = [
            ("highway", "3", "10.5m", "120 km/h", "No"),
            ("arterial", "3", "10.0m", "60 km/h", "Yes"),
            ("collector", "2", "6.0m", "50 km/h", "Yes"),
            ("local", "2", "5.0m", "40 km/h", "Yes"),
            ("residential", "1", "3.0m", "30 km/h", "Yes"),
        ]

        for name, lanes, width, speed, sidewalk in type_info:
            lines.append(f"║ {name:13} ║ {lanes:7} ║ {width:8} ║ {speed:9} ║ {sidewalk:10} ║")

        lines.append("╚═══════════════╩═════════╩══════════╩═══════════╩════════════╝")

        return "\n".join(lines)

    @staticmethod
    def display_lane_config(lane_count: int) -> str:
        """Display lane configuration diagram."""
        lines = [
            f"\n{'='*60}",
            f"  LANE CONFIGURATION: {lane_count} LANES",
            f"{'='*60}",
            "",
        ]

        # Draw cross-section
        total_width = lane_count * 3.5
        lane_width = 3.5

        # Top view
        lines.append("  Cross-Section View (not to scale):")
        lines.append("")

        # Draw curb
        lines.append("  ┌" + "─" * 56 + "┐")

        # Draw sidewalk
        lines.append("  │ ████████ │" + " " * 36 + "│ ████████ │")
        lines.append("  │ SIDEWALK │" + " " * 36 + "│ SIDEWALK │")
        lines.append("  │          │" + " " * 36 + "│          │")

        # Draw lanes
        lane_section = ""
        for i in range(lane_count):
            if i == lane_count // 2 and lane_count >= 4:
                lane_section += "│ ═══ "
            elif i < lane_count // 2:
                lane_section += "│ >>> "
            else:
                lane_section += "│ <<< "
        lane_section += "│"

        padding = 36 - len(lane_section) + 12
        lines.append("  ├──────────┼" + "─" * 34 + "┼──────────┤")
        lines.append("  │          │" + lane_section.center(34) + "│          │")
        lines.append("  │          │" + f"  {lane_count} LANES ({total_width}m total)".center(34) + "│          │")

        # Draw curb
        lines.append("  │          │" + " " * 36 + "│          │")
        lines.append("  └──────────┴" + "─" * 34 + "┴──────────┘")

        lines.append("")
        lines.append("  Legend:")
        lines.append("    >>>   Traffic direction (forward)")
        lines.append("    <<<   Traffic direction (reverse)")
        lines.append("    ═══   Center median/divider")

        return "\n".join(lines)

    @staticmethod
    def display_intersection_types() -> str:
        """Display intersection type reference."""
        return """
╔═══════════════════════════════════════════════════════════════╗
║                    INTERSECTION TYPES                         ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  4-WAY INTERSECTION          T-INTERSECTION                  ║
║       │                           │                          ║
║   ────┼────                    ────┼────                      ║
║       │                           │                          ║
║       │                       ───────                        ║
║                                                               ║
║  ROUNDABOUT                  Y-INTERSECTION                  ║
║      ╭───╮                        /\                         ║
║     /     \                      /  \                        ║
║     │  ●  │                     /    \                       ║
║     \     /                                                   ║
║      ╰───╯                                                    ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║  Types: 4way, 3way_t, 3way_y, roundabout, overpass            ║
╚═══════════════════════════════════════════════════════════════╝
"""

    @staticmethod
    def display_network_stats(network: RoadNetwork) -> str:
        """Display network statistics."""
        total_length = 0
        for seg in network.segments:
            # Approximate length from control points
            for i in range(len(seg.control_points) - 1):
                dx = seg.control_points[i+1][0] - seg.control_points[i][0]
                dy = seg.control_points[i+1][1] - seg.control_points[i][1]
                total_length += math.sqrt(dx*dx + dy*dy)

        total_lanes = sum(seg.lane_count for seg in network.segments)

        lines = [
            f"\n{'='*50}",
            f"  ROAD NETWORK STATISTICS",
            f"{'='*50}",
            f"",
            f"  Network ID:    {network.network_id or 'Unnamed'}",
            f"  Segments:      {len(network.segments)}",
            f"  Intersections: {len(network.intersections)}",
            f"  Total Length:  {total_length:.1f}m ({total_length/1000:.2f}km)",
            f"  Total Lanes:   {total_lanes}",
            f"",
            f"  Bounds:        ({network.bounds[0]:.0f}, {network.bounds[1]:.0f}) to",
            f"                 ({network.bounds[2]:.0f}, {network.bounds[3]:.0f})",
            f"{'='*50}",
        ]

        return "\n".join(lines)

    @staticmethod
    def display_surface_materials() -> str:
        """Display surface material options."""
        lines = [
            "\n╔═════════════════════════════════════════════════╗",
            "║           SURFACE MATERIAL OPTIONS               ║",
            "╠══════════════════╦════════════╦══════════════════╣",
            "║ Material         ║ Roughness  ║ Color            ║",
            "╠══════════════════╬════════════╬══════════════════╣",
        ]

        for name, props in SURFACE_MATERIALS.items():
            lines.append(f"║ {name:16} ║ {props['roughness']:10.2f} ║ {props['color']:16} ║")

        lines.append("╚══════════════════╩════════════╩══════════════════╝")

        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display road building checklist."""
        return """
╔═══════════════════════════════════════════════════════════════╗
║                  ROAD BUILDING CHECKLIST                      ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  1. CURVE PREPARATION                                         ║
║     □ Create curve path for road centerline                   ║
║     □ Set curve to 2D (if needed)                             ║
║     □ Adjust spline resolution                                ║
║                                                               ║
║  2. ROAD PARAMETERS                                           ║
║     □ Set lane count (1-12)                                   ║
║     □ Set lane width (2.0-5.0m)                               ║
║     □ Set curb height (0.0-0.5m)                              ║
║     □ Enable/disable sidewalks                                ║
║                                                               ║
║  3. MARKINGS                                                  ║
║     □ Center line (yellow, dashed)                            ║
║     □ Edge lines (white, solid)                               ║
║     □ Crosswalks at intersections                             ║
║                                                               ║
║  4. INTERSECTIONS                                             ║
║     □ Define intersection type                                ║
║     □ Set radius for roundabouts                              ║
║     □ Add traffic signals (if signalized)                     ║
║                                                               ║
║  5. MATERIALS                                                 ║
║     □ Apply asphalt material                                  ║
║     □ Set UV scale for texture                                ║
║     □ Add wear/damage details                                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

    @staticmethod
    def display_node_flow() -> str:
        """Display road builder node flow."""
        return """
  ROAD BUILDER NODE FLOW
  ═══════════════════════

  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ Group Input │────▶│ Calc Width  │────▶│  Profile    │
  │  (Curve)    │     │ (Lane×Width)│     │ (Rectangle) │
  └─────────────┘     └─────────────┘     └──────┬──────┘
                                                 │
                                                 ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   Curb      │     │ Curve to    │────▶│ Road Mesh   │
  │  Profile    │────▶│    Mesh     │     │  (Output)   │
  └─────────────┘     └─────────────┘     └─────────────┘

         │                                    │
         ▼                                    ▼
  ┌─────────────┐                     ┌─────────────┐
  │   Markings  │                     │    Join     │
  │   (Dashed)  │                     │  Geometry   │
  └──────┬──────┘                     └──────┬──────┘
         │                                   │
         └───────────────┬───────────────────┘
                         ▼
                  ┌─────────────┐
                  │Group Output │
                  └─────────────┘
"""


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def build_road_network(network_data: Dict[str, Any], **kwargs) -> RoadNetwork:
    """
    Build road network from data.

    Args:
        network_data: Network dictionary
        **kwargs: Additional options

    Returns:
        RoadNetwork specification
    """
    network_id = network_data.get("network_id", "network_0")

    # Build segments
    segments = []
    for edge_data in network_data.get("edges", []):
        segment = _build_segment(edge_data)
        segments.append(segment)

    # Build intersections
    intersections = []
    for node_data in network_data.get("nodes", []):
        if node_data.get("type") in ["intersection_4way", "intersection_3way", "roundabout"]:
            intersection = _build_intersection(node_data)
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


def _build_segment(edge_data: Dict[str, Any]) -> RoadSegment:
    """Build road segment from edge data."""
    segment_id = edge_data.get("id", "segment_0")
    road_type = edge_data.get("road_type", "local")
    template = ROAD_TEMPLATES.get(road_type, ROAD_TEMPLATES["local"])

    # Create lanes from template
    lanes = []
    for i, lane_data in enumerate(template.get("lanes", [])):
        lane = LaneSpec(
            lane_id=f"{segment_id}_lane_{i}",
            lane_type=lane_data.get("type", "travel"),
            width=lane_data.get("width", 3.5),
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


def _build_intersection(node_data: Dict[str, Any]) -> IntersectionGeometry:
    """Build intersection from node data."""
    node_type = node_data.get("type", "intersection_4way")

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


def network_to_gn_format(network: RoadNetwork, **kwargs) -> Dict[str, Any]:
    """
    Convert network to GN input format.

    Args:
        network: Road network
        **kwargs: Additional options

    Returns:
        GN-compatible input
    """
    return {
        "version": "1.0",
        "network": network.to_dict(),
        "global_settings": {
            "default_lane_width": 3.5,
            "curb_height": 0.15,
            "sidewalk_width": 1.5,
        },
        "materials": SURFACE_MATERIALS,
    }


def quick_road(lanes: int = 2, width: float = 3.5) -> RoadBuilder:
    """Quick road setup with common defaults."""
    road = RoadBuilder.create("QuickRoad")
    road.set_lanes(lanes).set_width(width).add_sidewalks()
    return road


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
    "RoadNetworkGN",
    "IntersectionBuilder",
    "RoadHUD",
    # Functions
    "build_road_network",
    "network_to_gn_format",
    "quick_road",
]
