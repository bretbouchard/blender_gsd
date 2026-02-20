"""
Road Network System - Procedural Roads and Intersections

Creates procedural road networks with lanes, intersections, and bridges.
Supports both OSM-imported data and procedural generation.

Usage:
    from lib.animation.city.road_network import RoadNetwork, create_road_network

    # Create road network from scratch
    network = RoadNetwork(name="City_Roads")
    network.add_road_segment(
        start=(0, 0, 0),
        end=(100, 0, 0),
        lanes=4,
        style="highway"
    )
    network.add_intersection(
        position=(100, 0, 0),
        type="traffic_light"
    )

    # Or create from OSM data
    from lib.animation.city.geo_data import import_osm_data
    osm_data = import_osm_data(bbox)
    network = RoadNetwork.from_osm(osm_data)

    # Generate Blender curves
    network.generate_blender_curves()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from pathlib import Path
import math
import random

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Matrix = None
    BLENDER_AVAILABLE = False


@dataclass
class LaneConfig:
    """Configuration for a single lane."""
    index: int
    direction: int  # 1 = forward, -1 = backward
    width: float = 3.5  # meters
    type: str = "travel"  # travel, turn_left, turn_right, parking, bike, bus
    marking: str = "solid"  # solid, dashed, double_yellow, none

    @property
    def offset(self) -> float:
        """Get lateral offset from road center."""
        return self.index * self.width * self.direction


@dataclass
class RoadStyle:
    """Visual style configuration for roads."""
    name: str
    surface_color: Tuple[float, float, float] = (0.2, 0.2, 0.2)
    surface_roughness: float = 0.8
    marking_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    curb_color: Tuple[float, float, float] = (0.4, 0.4, 0.4)
    curb_height: float = 0.15  # meters
    has_sidewalk: bool = True
    sidewalk_width: float = 2.0  # meters


# Road style presets
ROAD_PRESETS = {
    "highway": RoadStyle(
        name="Highway",
        surface_color=(0.15, 0.15, 0.15),
        has_sidewalk=False,
    ),
    "arterial": RoadStyle(
        name="Arterial",
        surface_color=(0.18, 0.18, 0.18),
        sidewalk_width=2.5,
    ),
    "urban": RoadStyle(
        name="Urban",
        surface_color=(0.2, 0.2, 0.2),
        sidewalk_width=3.0,
    ),
    "residential": RoadStyle(
        name="Residential",
        surface_color=(0.25, 0.25, 0.25),
        sidewalk_width=2.0,
    ),
    "industrial": RoadStyle(
        name="Industrial",
        surface_color=(0.17, 0.17, 0.17),
        sidewalk_width=1.5,
    ),
    "downtown": RoadStyle(
        name="Downtown",
        surface_color=(0.2, 0.2, 0.2),
        sidewalk_width=4.0,
    ),
}


class RoadSegment:
    """
    A single road segment with lanes.

    Supports:
    - Multiple lanes in each direction
    - Turn lanes at intersections
    - Road markings
    - Curves and elevation changes
    """

    def __init__(
        self,
        id: str,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        lanes_forward: int = 2,
        lanes_backward: int = 2,
        style: str = "urban",
        name: str = "",
        max_speed: float = 50.0,  # km/h
        control_points: Optional[List[Tuple[float, float, float]]] = None
    ):
        self.id = id
        self.start = Vector(start) if Vector else start
        self.end = Vector(end) if Vector else end
        self.lanes_forward = lanes_forward
        self.lanes_backward = lanes_backward
        self.style_name = style
        self.style = ROAD_PRESETS.get(style, ROAD_PRESETS["urban"])
        self.name = name
        self.max_speed = max_speed
        self.control_points = control_points or []

        # Build lane configurations
        self.lanes: List[LaneConfig] = []
        self._build_lanes()

    def _build_lanes(self) -> None:
        """Build lane configuration list."""
        self.lanes.clear()

        # Forward lanes (positive direction)
        for i in range(self.lanes_forward):
            lane_type = "travel"
            marking = "dashed" if i < self.lanes_forward - 1 else "solid"

            if i == 0 and self.lanes_forward > 1:
                lane_type = "travel"
            elif i == self.lanes_forward - 1:
                marking = "double_yellow" if self.lanes_backward > 0 else "solid"

            self.lanes.append(LaneConfig(
                index=i,
                direction=1,
                type=lane_type,
                marking=marking
            ))

        # Backward lanes (negative direction)
        for i in range(self.lanes_backward):
            lane_type = "travel"
            marking = "dashed" if i < self.lanes_backward - 1 else "solid"

            self.lanes.append(LaneConfig(
                index=i,
                direction=-1,
                type=lane_type,
                marking=marking
            ))

    @property
    def total_width(self) -> float:
        """Total road width in meters."""
        lane_width = sum(lane.width for lane in self.lanes)
        sidewalk = self.style.sidewalk_width * 2 if self.style.has_sidewalk else 0
        return lane_width + sidewalk

    @property
    def length(self) -> float:
        """Road segment length in meters."""
        if Vector:
            return (self.end - self.start).length
        else:
            dx = self.end[0] - self.start[0]
            dy = self.end[1] - self.start[1]
            dz = self.end[2] - self.start[2]
            return math.sqrt(dx*dx + dy*dy + dz*dz)

    @property
    def direction(self) -> Tuple[float, float, float]:
        """Normalized direction vector."""
        if Vector:
            return (self.end - self.start).normalized()
        else:
            dx = self.end[0] - self.start[0]
            dy = self.end[1] - self.start[1]
            dz = self.end[2] - self.start[2]
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length > 0:
                return (dx/length, dy/length, dz/length)
            return (1, 0, 0)

    def get_lane_center(self, lane_index: int, direction: int = 1) -> float:
        """Get lateral offset for lane center from road centerline."""
        if direction == 1:
            # Forward lanes
            half_width = sum(l.width for l in self.lanes if l.direction == 1) / 2
            lane_offset = sum(
                self.lanes[i].width
                for i in range(lane_index)
                if self.lanes[i].direction == 1
            )
            return lane_offset - half_width + self.lanes[lane_index].width / 2
        else:
            # Backward lanes
            backward_lanes = [l for l in self.lanes if l.direction == -1]
            half_width = sum(l.width for l in backward_lanes) / 2
            lane_offset = sum(
                backward_lanes[i].width
                for i in range(min(lane_index, len(backward_lanes)))
            )
            return -(lane_offset - half_width + 1.75)

    def to_blender_curve(self) -> Optional[Any]:
        """Convert road segment to Blender curve object."""
        if not BLENDER_AVAILABLE:
            return None

        # Create curve
        curve = bpy.data.curves.new(f"Road_{self.id}", type='CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = self.total_width / 2
        curve.fill_mode = 'FULL'

        # Create spline
        spline = curve.splines.new('POLY')

        # Add control points if curved
        points = [self.start]
        if self.control_points:
            points.extend(self.control_points)
        points.append(self.end)

        spline.points.add(len(points) - 1)
        for i, point in enumerate(points):
            if Vector:
                spline.points[i].co = (*point, 1.0)
            else:
                spline.points[i].co = (point[0], point[1], point[2], 1.0)

        # Create object
        obj = bpy.data.objects.new(curve.name, curve)

        # Apply road material
        self._apply_road_material(obj)

        return obj

    def _apply_road_material(self, obj: Any) -> None:
        """Apply road surface material."""
        if not BLENDER_AVAILABLE:
            return

        mat = bpy.data.materials.new(f"RoadMat_{self.id}")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*self.style.surface_color, 1.0)
            bsdf.inputs["Roughness"].default_value = self.style.surface_roughness

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)


@dataclass
class Intersection:
    """Road intersection with traffic control."""
    id: str
    position: Tuple[float, float, float]
    type: str = "cross"  # cross, t_junction, roundabout, traffic_light
    connected_roads: List[str] = field(default_factory=list)
    traffic_light_phase: float = 30.0  # seconds
    has_crosswalk: bool = True
    has_traffic_light: bool = True

    def to_blender_object(self) -> Optional[Any]:
        """Create intersection geometry in Blender."""
        if not BLENDER_AVAILABLE:
            return None

        # Create intersection pad
        bpy.ops.mesh.primitive_plane_add(
            size=20.0,  # Typical intersection size
            location=self.position
        )
        obj = bpy.context.active_object
        obj.name = f"Intersection_{self.id}"

        # Apply intersection material
        mat = bpy.data.materials.new(f"IntersectionMat_{self.id}")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.18, 0.18, 0.18, 1.0)

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        # Add traffic light if needed
        if self.has_traffic_light and self.type == "traffic_light":
            self._add_traffic_lights(obj)

        return obj

    def _add_traffic_lights(self, parent: Any) -> None:
        """Add traffic light poles to intersection."""
        if not BLENDER_AVAILABLE:
            return

        # Create simple traffic light poles at each corner
        positions = [
            (10, 10, 0),
            (-10, 10, 0),
            (-10, -10, 0),
            (10, -10, 0),
        ]

        for i, offset in enumerate(positions):
            # Pole
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.15,
                depth=5.0,
                location=(
                    self.position[0] + offset[0],
                    self.position[1] + offset[1],
                    self.position[2] + offset[2] + 2.5
                )
            )
            pole = bpy.context.active_object
            pole.name = f"TrafficLight_{self.id}_{i}"
            pole.parent = parent

            # Light housing
            bpy.ops.mesh.primitive_cube_add(
                size=0.5,
                location=(
                    self.position[0] + offset[0],
                    self.position[1] + offset[1],
                    self.position[2] + offset[2] + 4.5
                )
            )
            light = bpy.context.active_object
            light.name = f"LightHousing_{self.id}_{i}"
            light.parent = pole


class BridgeType:
    """Bridge type enumeration."""
    OVERPASS = "overpass"
    UNDERPASS = "underpass"
    BRIDGE = "bridge"
    TUNNEL = "tunnel"


class RoadNetwork:
    """
    Complete road network with segments, intersections, and bridges.

    Manages:
    - Road segments with lanes
    - Intersections with traffic control
    - Bridges and overpasses
    - Path finding for navigation
    """

    def __init__(self, name: str = "RoadNetwork"):
        self.name = name
        self.segments: Dict[str, RoadSegment] = {}
        self.intersections: Dict[str, Intersection] = {}
        self.bridges: List[Dict[str, Any]] = []

        # Navigation graph
        self._graph: Dict[str, List[str]] = {}  # node -> connected nodes

    @classmethod
    def from_osm(cls, osm_data: Any, scale: float = 1000.0) -> 'RoadNetwork':
        """Create road network from imported OSM data."""
        network = cls(name="OSM_Roads")

        for road in osm_data.roads:
            coords = road.get("coordinates", [])
            if len(coords) < 2:
                continue

            # Convert coordinates
            start = coords[0]
            end = coords[-1]

            # Determine lanes from road type
            road_type = road.get("type", "road")
            lanes = road.get("lanes", 2)

            if road_type in ["motorway", "trunk"]:
                style = "highway"
                lanes_forward = lanes // 2 or 2
                lanes_backward = lanes // 2 or 2
            elif road_type in ["primary", "secondary"]:
                style = "arterial"
                lanes_forward = lanes // 2 or 1
                lanes_backward = lanes // 2 or 1
            elif road_type in ["tertiary"]:
                style = "urban"
                lanes_forward = 1
                lanes_backward = 1
            else:
                style = "residential"
                lanes_forward = 1
                lanes_backward = 1

            # Add segment
            segment = RoadSegment(
                id=str(road["id"]),
                start=(start[1] * scale, start[0] * scale, 0),  # lon, lat -> x, y
                end=(end[1] * scale, end[0] * scale, 0),
                lanes_forward=lanes_forward,
                lanes_backward=lanes_backward,
                style=style,
                name=road.get("name", ""),
                max_speed=float(road.get("max_speed", "50").replace(" km/h", ""))
            )
            network.add_segment(segment)

        return network

    def add_segment(self, segment: RoadSegment) -> None:
        """Add a road segment to the network."""
        self.segments[segment.id] = segment

        # Update navigation graph
        start_key = f"{segment.start[0]:.1f}_{segment.start[1]:.1f}"
        end_key = f"{segment.end[0]:.1f}_{segment.end[1]:.1f}"

        if start_key not in self._graph:
            self._graph[start_key] = []
        if end_key not in self._graph:
            self._graph[end_key] = []

        self._graph[start_key].append(end_key)
        self._graph[end_key].append(start_key)

    def add_road_segment(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        lanes_forward: int = 2,
        lanes_backward: int = 2,
        style: str = "urban",
        name: str = "",
        **kwargs
    ) -> RoadSegment:
        """Add a new road segment by parameters."""
        segment_id = f"road_{len(self.segments)}"
        segment = RoadSegment(
            id=segment_id,
            start=start,
            end=end,
            lanes_forward=lanes_forward,
            lanes_backward=lanes_backward,
            style=style,
            name=name,
            **kwargs
        )
        self.add_segment(segment)
        return segment

    def add_intersection(
        self,
        position: Tuple[float, float, float],
        type: str = "cross",
        connected_roads: Optional[List[str]] = None,
        **kwargs
    ) -> Intersection:
        """Add an intersection to the network."""
        intersection_id = f"int_{len(self.intersections)}"
        intersection = Intersection(
            id=intersection_id,
            position=position,
            type=type,
            connected_roads=connected_roads or [],
            **kwargs
        )
        self.intersections[intersection_id] = intersection
        return intersection

    def add_bridge(
        self,
        segment_id: str,
        bridge_type: str,
        height: float,
        length: float
    ) -> None:
        """Add a bridge or overpass to a segment."""
        self.bridges.append({
            "segment_id": segment_id,
            "type": bridge_type,
            "height": height,
            "length": length,
        })

    def find_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> List[RoadSegment]:
        """
        Find a route through the road network.

        Uses A* pathfinding for optimal route.
        """
        # Simple implementation - would use full A* in production
        route = []

        # Find nearest segments to start and end
        start_seg = min(
            self.segments.values(),
            key=lambda s: min(
                math.sqrt((s.start[0]-start[0])**2 + (s.start[1]-start[1])**2),
                math.sqrt((s.end[0]-start[0])**2 + (s.end[1]-start[1])**2)
            )
        )

        end_seg = min(
            self.segments.values(),
            key=lambda s: min(
                math.sqrt((s.start[0]-end[0])**2 + (s.start[1]-end[1])**2),
                math.sqrt((s.end[0]-end[0])**2 + (s.end[1]-end[1])**2)
            )
        )

        # BFS to find path
        visited = set()
        queue = [(start_seg.id, [start_seg])]

        while queue:
            current_id, path = queue.pop(0)

            if current_id == end_seg.id:
                return path

            if current_id in visited:
                continue

            visited.add(current_id)

            # Find connected segments
            current = self.segments[current_id]
            for seg_id, seg in self.segments.items():
                if seg_id not in visited:
                    # Check if segments connect
                    if (abs(seg.start[0] - current.end[0]) < 1.0 and
                        abs(seg.start[1] - current.end[1]) < 1.0):
                        queue.append((seg_id, path + [seg]))
                    elif (abs(seg.end[0] - current.start[0]) < 1.0 and
                          abs(seg.end[1] - current.start[1]) < 1.0):
                        queue.append((seg_id, path + [seg]))

        return route

    def get_route(
        self,
        start: str,
        end: str
    ) -> List[Tuple[float, float, float]]:
        """
        Get a route by named locations.

        Args:
            start: Starting location name
            end: Ending location name

        Returns:
            List of waypoints
        """
        # Would look up named locations and call find_route
        # For now, return direct path
        return [(0, 0, 0), (100, 0, 0), (100, 100, 0)]

    def generate_blender_curves(self) -> Dict[str, Any]:
        """Generate all road curves as Blender objects."""
        if not BLENDER_AVAILABLE:
            return {}

        result = {
            "segments": [],
            "intersections": [],
            "bridges": [],
        }

        # Create collection
        collection = bpy.data.collections.new(self.name)
        bpy.context.collection.children.link(collection)

        # Generate segments
        for segment in self.segments.values():
            obj = segment.to_blender_curve()
            if obj:
                collection.objects.link(obj)
                result["segments"].append(obj)

        # Generate intersections
        for intersection in self.intersections.values():
            obj = intersection.to_blender_object()
            if obj:
                collection.objects.link(obj)
                result["intersections"].append(obj)

        return result

    def get_random_route(self, min_length: float = 500.0) -> List[Tuple[float, float, float]]:
        """Get a random route through the network."""
        if not self.segments:
            return [(0, 0, 0), (100, 0, 0), (100, 100, 0)]

        # Pick random start segment
        import random
        start_seg = random.choice(list(self.segments.values()))

        route = [tuple(start_seg.start)]
        current = start_seg
        total_length = 0

        while total_length < min_length:
            route.append(tuple(current.end))
            total_length += current.length

            # Find next connected segment
            connected = [
                seg for seg in self.segments.values()
                if (abs(seg.start[0] - current.end[0]) < 1.0 and
                    abs(seg.start[1] - current.end[1]) < 1.0 and
                    seg.id != current.id)
            ]

            if not connected:
                break

            current = random.choice(connected)

        return route


def create_road_segment(
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    **kwargs
) -> RoadSegment:
    """Convenience function to create a road segment."""
    return RoadSegment(
        id=f"seg_{hash(start) ^ hash(end)}",
        start=start,
        end=end,
        **kwargs
    )


def create_road_network(
    style: str = "urban",
    grid_size: Tuple[int, int] = (5, 5),
    block_size: float = 100.0,
    lanes: int = 2
) -> RoadNetwork:
    """
    Create a procedural grid-based road network.

    Args:
        style: Road style preset
        grid_size: Number of blocks in x and y
        block_size: Size of each block in meters
        lanes: Number of lanes per direction

    Returns:
        Complete road network
    """
    network = RoadNetwork(name="Procedural_Roads")

    # Create grid of roads
    for i in range(grid_size[0] + 1):
        # Horizontal roads
        network.add_road_segment(
            start=(0, i * block_size, 0),
            end=(grid_size[1] * block_size, i * block_size, 0),
            lanes_forward=lanes,
            lanes_backward=lanes,
            style=style,
            name=f"E{i}"
        )

    for j in range(grid_size[1] + 1):
        # Vertical roads
        network.add_road_segment(
            start=(j * block_size, 0, 0),
            end=(j * block_size, grid_size[0] * block_size, 0),
            lanes_forward=lanes,
            lanes_backward=lanes,
            style=style,
            name=f"N{j}"
        )

    # Add intersections at grid points
    for i in range(grid_size[0] + 1):
        for j in range(grid_size[1] + 1):
            network.add_intersection(
                position=(j * block_size, i * block_size, 0),
                type="traffic_light" if (i + j) % 3 == 0 else "cross"
            )

    return network
