"""
Charlotte Digital Twin - Elevation Manager

Manages elevation data for all scene elements including:
- Node elevation from OSM 'ele' tags
- Interpolation for nodes without explicit elevation
- Bridge clearance calculations
- Elevation validation and conflict detection
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
import xml.etree.ElementTree as ET
import math
import json


@dataclass
class ElevationReport:
    """Report of elevation analysis."""
    total_nodes: int = 0
    nodes_with_elevation: int = 0
    nodes_interpolated: int = 0
    bridges_processed: int = 0
    elevation_conflicts: List[Dict] = field(default_factory=list)
    road_grade_issues: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'total_nodes': self.total_nodes,
            'nodes_with_elevation': self.nodes_with_elevation,
            'nodes_interpolated': self.nodes_interpolated,
            'bridges_processed': self.bridges_processed,
            'elevation_conflicts': self.elevation_conflicts,
            'road_grade_issues': self.road_grade_issues,
        }


class ElevationManager:
    """
    Manages elevation data for all scene elements.

    Uses OSM 'ele' tags when available, otherwise interpolates
    from nearby known elevations using inverse distance weighting.
    """

    # Reference point for Charlotte (center of data)
    REF_LAT = 35.226
    REF_LON = -80.843

    def __init__(self):
        # Node data: osm_id -> {lat, lon, ele, tags}
        self.nodes: Dict[int, Dict] = {}

        # Elevation cache: osm_id -> elevation (explicit or interpolated)
        self.elevations: Dict[int, float] = {}

        # Known elevation points for interpolation
        self.known_points: List[Tuple[float, float, float]] = []

        # Default elevation for Charlotte area (meters above sea level)
        self.default_elevation = 220.0

        # Analysis report
        self.report = ElevationReport()

    def load_from_osm(self, osm_path: str) -> None:
        """
        Load elevation data from OSM file.

        Extracts all nodes with their positions and elevation tags.
        """
        print(f"Loading elevation data from {osm_path}...")

        tree = ET.parse(osm_path)
        root = tree.getroot()

        for node in root.findall('node'):
            node_id = int(node.get('id'))
            lat = float(node.get('lat'))
            lon = float(node.get('lon'))

            # Extract tags
            tags = {}
            ele = None

            for tag in node.findall('tag'):
                k = tag.get('k')
                v = tag.get('v')
                tags[k] = v

                if k == 'ele':
                    try:
                        ele = float(v)
                    except ValueError:
                        pass

            self.nodes[node_id] = {
                'lat': lat,
                'lon': lon,
                'ele': ele,
                'tags': tags,
            }

            if ele is not None:
                self.elevations[node_id] = ele
                self.known_points.append((lat, lon, ele))

        self.report.total_nodes = len(self.nodes)
        self.report.nodes_with_elevation = len(self.elevations)

        print(f"  Loaded {len(self.nodes)} nodes")
        print(f"  {len(self.elevations)} nodes with explicit elevation")

    def get_elevation(self, node_id: int) -> float:
        """
        Get elevation for a node.

        Returns cached elevation if available, otherwise interpolates.
        """
        if node_id in self.elevations:
            return self.elevations[node_id]

        node = self.nodes.get(node_id)
        if not node:
            return self.default_elevation

        # Interpolate from known points
        elevation = self.interpolate_elevation(node['lat'], node['lon'])
        self.elevations[node_id] = elevation
        self.report.nodes_interpolated += 1

        return elevation

    def interpolate_elevation(
        self,
        lat: float,
        lon: float,
        max_distance: float = 500.0,
        power: int = 2
    ) -> float:
        """
        Interpolate elevation using inverse distance weighting.

        Args:
            lat: Latitude of point
            lon: Longitude of point
            max_distance: Maximum distance (meters) to consider
            power: Exponent for distance weighting

        Returns:
            Interpolated elevation in meters
        """
        if not self.known_points:
            return self.default_elevation

        weighted_sum = 0.0
        weight_sum = 0.0

        for kp_lat, kp_lon, kp_ele in self.known_points:
            dist = self._haversine_distance(lat, lon, kp_lat, kp_lon)

            if dist > max_distance or dist < 0.1:
                continue

            weight = 1.0 / (dist ** power)
            weighted_sum += weight * kp_ele
            weight_sum += weight

        if weight_sum > 0:
            return weighted_sum / weight_sum

        return self.default_elevation

    def get_road_profile(self, node_ids: List[int]) -> List[float]:
        """
        Get elevation at each vertex of a road.

        Args:
            node_ids: List of OSM node IDs along road

        Returns:
            List of elevations corresponding to each node
        """
        return [self.get_elevation(nid) for nid in node_ids]

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two points in meters.

        Uses Haversine formula for spherical Earth.
        """
        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def latlon_to_local(self, lat: float, lon: float) -> Tuple[float, float]:
        """
        Convert lat/lon to local scene coordinates (meters from reference).

        Returns:
            (x, y) tuple in meters
        """
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(self.REF_LAT))

        x = (lon - self.REF_LON) * meters_per_deg_lon
        y = (lat - self.REF_LAT) * meters_per_deg_lat

        return (x, y)

    def save_report(self, output_path: str) -> None:
        """Save elevation analysis report to JSON."""
        with open(output_path, 'w') as f:
            json.dump(self.report.to_dict(), f, indent=2)
        print(f"Elevation report saved to {output_path}")


class BridgeElevationCalculator:
    """
    Calculates proper elevations for bridges.

    Handles:
    - Clearance calculation over crossing roads
    - Approach slope generation
    - Validation of bridge heights
    """

    # Standard clearances (meters)
    CLEARANCES = {
        'road': 4.5,       # Minimum clearance over road
        'highway': 5.5,    # Highway overpass
        'rail': 6.5,       # Railway overpass
        'pedestrian': 3.0, # Pedestrian bridge
    }

    # Maximum allowed grade for approaches
    MAX_GRADE = 0.05  # 5%

    def __init__(self, elevation_manager: ElevationManager):
        self.elevation = elevation_manager

    def calculate_bridge_elevation(
        self,
        bridge_node_ids: List[int],
        crossing_road_elevation: float,
        clearance_type: str = 'highway'
    ) -> List[float]:
        """
        Calculate bridge deck elevations.

        Args:
            bridge_node_ids: Node IDs along bridge
            crossing_road_elevation: Elevation of road under bridge
            clearance_type: Type of clearance to apply

        Returns:
            List of elevations for each bridge node
        """
        clearance = self.CLEARANCES.get(clearance_type, 5.5)
        min_deck_elevation = crossing_road_elevation + clearance

        # Get base elevations for bridge nodes
        base_elevations = [
            self.elevation.get_elevation(nid)
            for nid in bridge_node_ids
        ]

        # Bridge must be at least min_deck_elevation
        bridge_elevations = [
            max(base, min_deck_elevation)
            for base in base_elevations
        ]

        return bridge_elevations

    def generate_approach_slopes(
        self,
        bridge_start: Tuple[float, float, float],
        bridge_end: Tuple[float, float, float],
        ground_start: float,
        ground_end: float
    ) -> List[Tuple[float, float, float]]:
        """
        Generate approach ramp points if bridge is elevated.

        Args:
            bridge_start: (x, y, z) of bridge start
            bridge_end: (x, y, z) of bridge end
            ground_start: Ground elevation at start
            ground_end: Ground elevation at end

        Returns:
            List of approach points (x, y, z) for both ends
        """
        approach_points = []

        # Calculate if approaches are needed
        start_rise = bridge_start[2] - ground_start
        end_rise = bridge_end[2] - ground_end

        # Calculate approach length needed (at max grade)
        start_approach_length = start_rise / self.MAX_GRADE if start_rise > 0 else 0
        end_approach_length = end_rise / self.MAX_GRADE if end_rise > 0 else 0

        # Generate approach points for start
        if start_approach_length > 0:
            # Direction from bridge to approach
            dx = bridge_start[0] - bridge_end[0]
            dy = bridge_start[1] - bridge_end[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx /= length
                dy /= length

            # Add approach point
            approach_x = bridge_start[0] + dx * start_approach_length
            approach_y = bridge_start[1] + dy * start_approach_length
            approach_points.append((approach_x, approach_y, ground_start))

        # Generate approach points for end
        if end_approach_length > 0:
            dx = bridge_end[0] - bridge_start[0]
            dy = bridge_end[1] - bridge_start[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx /= length
                dy /= length

            approach_x = bridge_end[0] + dx * end_approach_length
            approach_y = bridge_end[1] + dy * end_approach_length
            approach_points.append((approach_x, approach_y, ground_end))

        return approach_points

    def validate_clearance(
        self,
        bridge_elevation: float,
        under_road_elevation: float,
        clearance_type: str = 'highway'
    ) -> Tuple[bool, float]:
        """
        Validate bridge provides adequate clearance.

        Returns:
            (is_valid, actual_clearance)
        """
        required = self.CLEARANCES.get(clearance_type, 5.5)
        actual = bridge_elevation - under_road_elevation

        return (actual >= required, actual)


class ElevationValidator:
    """
    Validates elevation consistency across the scene.
    """

    # Maximum allowed road grade
    MAX_ROAD_GRADE = 0.15  # 15%

    def __init__(self, elevation_manager: ElevationManager):
        self.elevation = elevation_manager

    def check_road_continuity(
        self,
        way_data: Dict
    ) -> List[Dict]:
        """
        Check for problematic elevation jumps in roads.

        Returns list of issues found.
        """
        issues = []
        node_ids = way_data.get('node_ids', [])

        if len(node_ids) < 2:
            return issues

        # Get local coordinates for distance calculation
        prev_node = self.elevation.nodes.get(node_ids[0])
        if not prev_node:
            return issues

        prev_x, prev_y = self.elevation.latlon_to_local(
            prev_node['lat'], prev_node['lon']
        )
        prev_z = self.elevation.get_elevation(node_ids[0])

        for i, nid in enumerate(node_ids[1:], 1):
            node = self.elevation.nodes.get(nid)
            if not node:
                continue

            x, y = self.elevation.latlon_to_local(node['lat'], node['lon'])
            z = self.elevation.get_elevation(nid)

            # Calculate grade
            dx = x - prev_x
            dy = y - prev_y
            horizontal_dist = math.sqrt(dx*dx + dy*dy)

            if horizontal_dist > 0.1:  # Avoid division by zero
                grade = abs(z - prev_z) / horizontal_dist

                if grade > self.MAX_ROAD_GRADE:
                    issues.append({
                        'way_id': way_data.get('osm_id'),
                        'segment': (i-1, i),
                        'grade': grade,
                        'elevation_change': abs(z - prev_z),
                        'distance': horizontal_dist,
                    })

            prev_x, prev_y, prev_z = x, y, z

        return issues

    def check_intersection_conflicts(
        self,
        intersections: List[Dict]
    ) -> List[Dict]:
        """
        Find intersections where roads at different layers meet incorrectly.

        Returns list of conflicts found.
        """
        conflicts = []

        for intersection in intersections:
            elevations = intersection.get('elevations', [])
            if not elevations:
                continue

            # Check for significant elevation differences
            min_ele = min(elevations)
            max_ele = max(elevations)
            diff = max_ele - min_ele

            # If more than 3 meters difference, it might be grade-separated
            if diff > 3.0 and not intersection.get('is_bridge'):
                conflicts.append({
                    'intersection_id': intersection.get('id'),
                    'elevation_diff': diff,
                    'min_elevation': min_ele,
                    'max_elevation': max_ele,
                    'roads': intersection.get('road_ids', []),
                })

        return conflicts


# Convenience function
def create_elevation_manager(osm_path: str) -> ElevationManager:
    """Create and initialize an elevation manager from OSM data."""
    manager = ElevationManager()
    manager.load_from_osm(osm_path)
    return manager


if __name__ == '__main__':
    # Test with Charlotte data
    import sys

    osm_path = sys.argv[1] if len(sys.argv) > 1 else 'maps/charlotte-merged.osm'

    manager = create_elevation_manager(osm_path)

    # Sample some elevations
    print("\nSample elevations:")
    for node_id in list(manager.nodes.keys())[:5]:
        ele = manager.get_elevation(node_id)
        print(f"  Node {node_id}: {ele:.1f}m")

    # Save report
    manager.save_report('output/elevation_report.json')
