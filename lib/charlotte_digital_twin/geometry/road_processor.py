"""
Road Network Processor for Charlotte Digital Twin

Processes OSM road data into connected road networks and generates
Blender geometry (curves and meshes).

Usage:
    from lib.charlotte_digital_twin.geometry import RoadNetworkProcessor
    from lib.charlotte_digital_twin import OSMDownloader

    # Download OSM data
    downloader = OSMDownloader()
    osm_data = downloader.download_charlotte_extract()

    # Process roads
    processor = RoadNetworkProcessor()
    segments = processor.process(osm_data)

    # Generate Blender curves
    curves = processor.create_blender_curves(segments)
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .types import (
    GeometryConfig,
    RoadType,
    RoadSegment,
    WorldCoordinate,
    ROAD_WIDTHS,
    ROAD_LANES,
)
from .coordinates import CoordinateTransformer


@dataclass
class RoadNode:
    """Represents a node in the road network graph."""
    node_id: int
    lat: float
    lon: float
    world_coord: Optional[WorldCoordinate] = None
    connections: List[int] = field(default_factory=list)  # Connected node IDs


@dataclass
class Intersection:
    """Represents a road intersection."""
    node_id: int
    position: WorldCoordinate
    roads: List[int] = field(default_factory=list)  # Road segment IDs
    road_types: Set[RoadType] = field(default_factory=set)


class RoadNetworkProcessor:
    """
    Processes raw OSM data into a road network.

    Features:
    - Extracts roads from OSM ways
    - Builds connectivity graph
    - Detects intersections
    - Creates RoadSegment objects
    - Generates Blender curves
    """

    def __init__(
        self,
        config: Optional[GeometryConfig] = None,
        transformer: Optional[CoordinateTransformer] = None,
    ):
        """
        Initialize road processor.

        Args:
            config: Geometry configuration
            transformer: Coordinate transformer
        """
        self.config = config or GeometryConfig()
        self.transformer = transformer or CoordinateTransformer(self.config)

        # Internal data structures
        self._nodes: Dict[int, RoadNode] = {}
        self._segments: List[RoadSegment] = []
        self._intersections: Dict[int, Intersection] = {}

    def process(self, osm_data: Any) -> List[RoadSegment]:
        """
        Process OSM data and extract road segments.

        Args:
            osm_data: OSMData object from OSMDownloader

        Returns:
            List of RoadSegment objects
        """
        # Reset state
        self._nodes = {}
        self._segments = []
        self._intersections = {}

        # Build node lookup with world coordinates
        for node_id, node in osm_data.nodes.items():
            world = self.transformer.latlon_to_world(node.lat, node.lon)
            self._nodes[node_id] = RoadNode(
                node_id=node_id,
                lat=node.lat,
                lon=node.lon,
                world_coord=world,
            )

        # Process ways to extract roads
        for way_id, way in osm_data.ways.items():
            highway = way.tags.get("highway")
            if not highway:
                continue

            # Try to parse road type
            try:
                road_type = RoadType(highway)
            except ValueError:
                # Unknown road type, skip or use unclassified
                road_type = RoadType.UNCLASSIFIED

            # Create road segment
            segment = self._create_segment(way_id, way, road_type)
            if segment:
                self._segments.append(segment)

        # Detect intersections
        self._detect_intersections()

        return self._segments

    def _create_segment(
        self,
        way_id: int,
        way: Any,
        road_type: RoadType,
    ) -> Optional[RoadSegment]:
        """Create a RoadSegment from an OSM way."""
        if not way.node_ids:
            return None

        # Get world coordinates for all nodes
        coords = []
        for node_id in way.node_ids:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                if node.world_coord:
                    coords.append(node.world_coord)

        if len(coords) < 2:
            return None

        # Get road properties from tags
        tags = way.tags

        # Width
        width = ROAD_WIDTHS.get(road_type, self.config.default_road_width)
        width_str = tags.get("width")
        if width_str:
            try:
                width = float(width_str.replace("m", "").strip())
            except ValueError:
                pass

        # Lanes
        lanes = ROAD_LANES.get(road_type, 2)
        lanes_str = tags.get("lanes")
        if lanes_str:
            try:
                lanes = int(lanes_str)
            except ValueError:
                pass

        # Other properties
        surface = tags.get("surface", "asphalt")
        is_bridge = tags.get("bridge") == "yes"
        is_tunnel = tags.get("tunnel") == "yes"
        is_oneway = tags.get("oneway") == "yes"

        return RoadSegment(
            osm_id=way_id,
            name=tags.get("name", ""),
            road_type=road_type,
            coordinates=coords,
            width=width,
            lanes=lanes,
            surface=surface,
            is_bridge=is_bridge,
            is_tunnel=is_tunnel,
            is_oneway=is_oneway,
            tags=tags,
        )

    def _detect_intersections(self) -> None:
        """Detect road intersections from shared nodes."""
        # Count how many roads use each node
        node_usage: Dict[int, List[int]] = defaultdict(list)

        for segment in self._segments:
            for coord_idx, coord in enumerate(segment.coordinates):
                # Find node ID for this coordinate
                for node_id, node in self._nodes.items():
                    if node.world_coord:
                        if (abs(node.world_coord.x - coord.x) < 0.01 and
                            abs(node.world_coord.y - coord.y) < 0.01):
                            node_usage[node_id].append(segment.osm_id)
                            node.connections.append(segment.osm_id)
                            break

        # Nodes used by multiple roads are intersections
        for node_id, road_ids in node_usage.items():
            if len(set(road_ids)) > 1:
                node = self._nodes[node_id]
                if node.world_coord:
                    # Get unique road types
                    road_types = set()
                    for segment in self._segments:
                        if segment.osm_id in road_ids:
                            road_types.add(segment.road_type)

                    self._intersections[node_id] = Intersection(
                        node_id=node_id,
                        position=node.world_coord,
                        roads=list(set(road_ids)),
                        road_types=road_types,
                    )

    def get_intersections(self) -> List[Intersection]:
        """Get all detected intersections."""
        return list(self._intersections.values())

    def filter_by_type(
        self,
        road_types: Optional[Set[RoadType]] = None,
    ) -> List[RoadSegment]:
        """
        Filter road segments by type.

        Args:
            road_types: Set of road types to include (None = all)

        Returns:
            Filtered list of road segments
        """
        if road_types is None:
            return self._segments

        return [s for s in self._segments if s.road_type in road_types]

    def filter_by_bounds(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
    ) -> List[RoadSegment]:
        """
        Filter road segments by bounding box.

        Args:
            min_x, min_y, max_x, max_y: Bounding box in world coordinates

        Returns:
            Road segments that intersect the bounds
        """
        filtered = []
        for segment in self._segments:
            for coord in segment.coordinates:
                if (min_x <= coord.x <= max_x and
                    min_y <= coord.y <= max_y):
                    filtered.append(segment)
                    break
        return filtered

    def get_by_name(self, name: str) -> List[RoadSegment]:
        """Get road segments by name (partial match)."""
        name_lower = name.lower()
        return [
            s for s in self._segments
            if name_lower in s.name.lower()
        ]

    def get_highways(self) -> List[RoadSegment]:
        """Get all highway segments (motorways and trunks)."""
        highway_types = {
            RoadType.MOTORWAY,
            RoadType.MOTORWAY_LINK,
            RoadType.TRUNK,
            RoadType.TRUNK_LINK,
        }
        return self.filter_by_type(highway_types)

    def get_major_roads(self) -> List[RoadSegment]:
        """Get all major roads (primary and secondary)."""
        major_types = {
            RoadType.PRIMARY,
            RoadType.PRIMARY_LINK,
            RoadType.SECONDARY,
            RoadType.SECONDARY_LINK,
        }
        return self.filter_by_type(major_types)

    def get_local_roads(self) -> List[RoadSegment]:
        """Get all local roads (residential, service, etc.)."""
        local_types = {
            RoadType.TERTIARY,
            RoadType.TERTIARY_LINK,
            RoadType.RESIDENTIAL,
            RoadType.SERVICE,
            RoadType.UNCLASSIFIED,
        }
        return self.filter_by_type(local_types)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the road network."""
        stats = {
            "total_segments": len(self._segments),
            "total_intersections": len(self._intersections),
            "by_type": defaultdict(int),
            "total_length_m": 0.0,
            "bridges": 0,
            "tunnels": 0,
            "oneway": 0,
            "named_roads": 0,
        }

        for segment in self._segments:
            stats["by_type"][segment.road_type.value] += 1
            stats["total_length_m"] += segment.get_length()
            if segment.is_bridge:
                stats["bridges"] += 1
            if segment.is_tunnel:
                stats["tunnels"] += 1
            if segment.is_oneway:
                stats["oneway"] += 1
            if segment.name:
                stats["named_roads"] += 1

        stats["by_type"] = dict(stats["by_type"])
        return stats


__all__ = [
    "RoadNode",
    "Intersection",
    "RoadNetworkProcessor",
]
