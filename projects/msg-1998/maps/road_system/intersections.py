"""
MSG-1998 Intersection Detection and Building

Detects intersections from non-contiguous road segments and
generates proper intersection geometry.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple
from enum import Enum
import math
from collections import defaultdict


class IntersectionType(Enum):
    """Types of road intersections."""
    FOUR_WAY = "4way"           # Standard 4-way intersection
    THREE_WAY_T = "3way_t"      # T-junction
    THREE_WAY_Y = "3way_y"      # Y-junction (angled)
    FIVE_WAY = "5way"           # 5-way intersection
    ROUNDABOUT = "roundabout"   # Roundabout/circle
    OVERLAP = "overlap"         # Roads overlapping without proper intersection
    MERGE = "merge"             # Lane merge point


@dataclass
class RoadEndpoint:
    """Represents an endpoint of a road segment."""
    road_id: str
    position: Tuple[float, float, float]
    is_start: bool  # True if start of road, False if end
    direction: float  # Angle in radians
    width: float

    def distance_to(self, other: Tuple[float, float, float]) -> float:
        """Calculate distance to another point."""
        dx = other[0] - self.position[0]
        dy = other[1] - self.position[1]
        return math.sqrt(dx * dx + dy * dy)


@dataclass
class IntersectionCluster:
    """
    A cluster of road endpoints that form an intersection.

    Groups endpoints that are within proximity threshold and
    calculates the intersection center and type.
    """
    cluster_id: str
    endpoints: List[RoadEndpoint] = field(default_factory=list)
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    intersection_type: IntersectionType = IntersectionType.FOUR_WAY
    max_width: float = 10.0
    road_ids: Set[str] = field(default_factory=set)

    @property
    def road_count(self) -> int:
        """Number of unique roads in this intersection."""
        return len(self.road_ids)

    @property
    def angles(self) -> List[float]:
        """Get sorted list of road approach angles."""
        return sorted([ep.direction for ep in self.endpoints])

    def calculate_center(self) -> Tuple[float, float, float]:
        """Calculate center point of intersection."""
        if not self.endpoints:
            return (0.0, 0.0, 0.0)

        x = sum(ep.position[0] for ep in self.endpoints) / len(self.endpoints)
        y = sum(ep.position[1] for ep in self.endpoints) / len(self.endpoints)
        z = sum(ep.position[2] for ep in self.endpoints) / len(self.endpoints)

        self.center = (x, y, z)
        return self.center

    def determine_type(self) -> IntersectionType:
        """Determine intersection type from endpoint configuration."""
        n = self.road_count

        if n == 2:
            # Check if roads are crossing or merging
            angles = self.angles
            angle_diff = abs(angles[1] - angles[0])
            # Normalize to 0-pi range
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            if abs(angle_diff - math.pi) < 0.3:  # ~17 degrees tolerance
                # Roads are parallel/opposite - it's a merge
                self.intersection_type = IntersectionType.MERGE
            else:
                # Roads crossing at angle
                self.intersection_type = IntersectionType.OVERLAP

        elif n == 3:
            # T or Y junction
            angles = self.angles
            # Check angle distribution
            diffs = []
            for i in range(len(angles)):
                diff = angles[(i + 1) % len(angles)] - angles[i]
                if diff < 0:
                    diff += 2 * math.pi
                diffs.append(diff)

            # T-junction has one ~180 degree angle
            if any(abs(d - math.pi) < 0.4 for d in diffs):
                self.intersection_type = IntersectionType.THREE_WAY_T
            else:
                self.intersection_type = IntersectionType.THREE_WAY_Y

        elif n == 4:
            self.intersection_type = IntersectionType.FOUR_WAY

        elif n >= 5:
            self.intersection_type = IntersectionType.FIVE_WAY

        return self.intersection_type


@dataclass
class IntersectionGeometry:
    """Generated geometry for an intersection."""
    cluster: IntersectionCluster
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    faces: List[Tuple[int, ...]] = field(default_factory=list)
    material_index: int = 0
    has_crosswalks: bool = True
    has_traffic_signals: bool = False


class IntersectionDetector:
    """
    Detects intersections from non-contiguous road segments.

    Uses endpoint clustering to find where roads meet, handling:
    - Roads that don't share vertices but are nearby
    - Overlapping road endpoints
    - Multi-way intersections (3, 4, 5+ roads)
    """

    def __init__(
        self,
        proximity_threshold: float = 2.0,  # meters
        min_intersection_roads: int = 2,
    ):
        """
        Initialize detector.

        Args:
            proximity_threshold: Distance in meters to consider endpoints as same intersection
            min_intersection_roads: Minimum roads to form an intersection
        """
        self.proximity_threshold = proximity_threshold
        self.min_intersection_roads = min_intersection_roads

        # Results
        self.clusters: List[IntersectionCluster] = []
        self.endpoint_to_cluster: Dict[str, str] = {}  # endpoint_id -> cluster_id

    def detect(
        self,
        road_segments: List[Dict[str, Any]],
    ) -> List[IntersectionCluster]:
        """
        Detect intersections from road segments.

        Args:
            road_segments: List of road segment dicts with:
                - id: unique identifier
                - vertices: list of (x, y, z) points
                - width: road width in meters

        Returns:
            List of IntersectionCluster objects
        """
        self.clusters = []
        self.endpoint_to_cluster = {}

        # Extract all endpoints
        endpoints = self._extract_endpoints(road_segments)

        # Cluster endpoints by proximity
        self._cluster_endpoints(endpoints)

        # Post-process clusters
        self._postprocess_clusters()

        return self.clusters

    def _extract_endpoints(
        self,
        road_segments: List[Dict[str, Any]],
    ) -> List[RoadEndpoint]:
        """Extract road endpoints with direction information."""
        endpoints = []

        for segment in road_segments:
            road_id = segment.get("id", segment.get("name", "unknown"))
            vertices = segment.get("vertices", [])
            width = segment.get("width") or 10.0  # Default width if None

            if len(vertices) < 2:
                continue

            # Start endpoint
            start_pos = vertices[0]
            start_dir = self._calculate_direction(vertices[0], vertices[1])
            endpoints.append(RoadEndpoint(
                road_id=road_id,
                position=tuple(start_pos),
                is_start=True,
                direction=start_dir,
                width=width,
            ))

            # End endpoint
            end_pos = vertices[-1]
            end_dir = self._calculate_direction(vertices[-2], vertices[-1])
            endpoints.append(RoadEndpoint(
                road_id=road_id,
                position=tuple(end_pos),
                is_start=False,
                direction=end_dir,
                width=width,
            ))

        return endpoints

    def _calculate_direction(
        self,
        p1: Tuple[float, ...],
        p2: Tuple[float, ...],
    ) -> float:
        """Calculate direction angle between two points."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.atan2(dy, dx)

    def _cluster_endpoints(self, endpoints: List[RoadEndpoint]) -> None:
        """Cluster endpoints by proximity using union-find approach."""
        cluster_id = 0

        for endpoint in endpoints:
            # Check if this endpoint is close to any existing cluster
            found_cluster = None

            for cluster in self.clusters:
                if cluster.endpoints:
                    # Check distance to cluster center
                    dist = endpoint.distance_to(cluster.center)
                    if dist < self.proximity_threshold:
                        found_cluster = cluster
                        break

            if found_cluster:
                # Add to existing cluster
                found_cluster.endpoints.append(endpoint)
                found_cluster.road_ids.add(endpoint.road_id)
                # Handle None values in max calculation
                ep_width = endpoint.width or 10.0
                cluster_width = found_cluster.max_width or 10.0
                found_cluster.max_width = max(cluster_width, ep_width)
                found_cluster.calculate_center()
            else:
                # Create new cluster
                new_cluster = IntersectionCluster(
                    cluster_id=f"intersection_{cluster_id}",
                    endpoints=[endpoint],
                    road_ids={endpoint.road_id},
                    max_width=endpoint.width or 10.0,
                )
                new_cluster.calculate_center()
                self.clusters.append(new_cluster)
                cluster_id += 1

    def _postprocess_clusters(self) -> None:
        """Post-process clusters to determine types and filter."""
        # Determine intersection types
        for cluster in self.clusters:
            cluster.determine_type()
            cluster.calculate_center()

        # Filter out clusters with too few roads
        self.clusters = [
            c for c in self.clusters
            if c.road_count >= self.min_intersection_roads
        ]

    def get_cluster_for_road(self, road_id: str) -> List[IntersectionCluster]:
        """Get all clusters that a road participates in."""
        return [c for c in self.clusters if road_id in c.road_ids]


class IntersectionBuilder:
    """
    Builds intersection geometry from detected clusters.

    Generates:
    - Intersection surface mesh
    - Crosswalk positions
    - Traffic signal positions (for signalized intersections)
    """

    def __init__(
        self,
        default_material: str = "asphalt_intersection",
        crosswalk_width: float = 3.0,
    ):
        """
        Initialize builder.

        Args:
            default_material: Material name for intersection surfaces
            crosswalk_width: Width of crosswalk markings in meters
        """
        self.default_material = default_material
        self.crosswalk_width = crosswalk_width

    def build(
        self,
        cluster: IntersectionCluster,
    ) -> IntersectionGeometry:
        """
        Build intersection geometry for a cluster.

        Args:
            cluster: IntersectionCluster to build geometry for

        Returns:
            IntersectionGeometry with mesh data
        """
        geometry = IntersectionGeometry(
            cluster=cluster,
            has_crosswalks=cluster.road_count >= 3,
            has_traffic_signals=cluster.intersection_type == IntersectionType.FOUR_WAY,
        )

        # Calculate intersection polygon based on type
        if cluster.intersection_type == IntersectionType.FOUR_WAY:
            vertices, faces = self._build_four_way(cluster)
        elif cluster.intersection_type in (IntersectionType.THREE_WAY_T, IntersectionType.THREE_WAY_Y):
            vertices, faces = self._build_three_way(cluster)
        elif cluster.intersection_type == IntersectionType.FIVE_WAY:
            vertices, faces = self._build_five_way(cluster)
        else:
            # Default: simple circular intersection
            vertices, faces = self._build_circular(cluster)

        geometry.vertices = vertices
        geometry.faces = faces

        return geometry

    def _build_four_way(
        self,
        cluster: IntersectionCluster,
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Build 4-way intersection geometry."""
        cx, cy, cz = cluster.center
        radius = cluster.max_width / 2 + 1.0  # Extra margin

        # Create octagonal intersection shape
        vertices = []
        for i in range(8):
            angle = i * math.pi / 4 + math.pi / 8  # Offset for better road alignment
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))  # Slightly above road surface

        # Simple fan triangulation
        faces = [(0, i, i + 1) for i in range(1, 7)]
        faces.append((0, 7, 0))

        return vertices, faces

    def _build_three_way(
        self,
        cluster: IntersectionCluster,
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Build 3-way (T or Y) intersection geometry."""
        cx, cy, cz = cluster.center
        radius = cluster.max_width / 2 + 1.0

        # Create 6-sided shape for T/Y junction
        vertices = []
        for i in range(6):
            angle = i * math.pi / 3
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5)]

        return vertices, faces

    def _build_five_way(
        self,
        cluster: IntersectionCluster,
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Build 5-way intersection geometry."""
        cx, cy, cz = cluster.center
        radius = cluster.max_width / 2 + 1.5

        # Create decagon (10-sided) for 5-way
        vertices = []
        for i in range(10):
            angle = i * math.pi / 5
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        # Fan triangulation from center
        center_idx = len(vertices)
        vertices.append((cx, cy, cz + 0.01))
        faces = [(center_idx, i, (i + 1) % 10) for i in range(10)]

        return vertices, faces

    def _build_circular(
        self,
        cluster: IntersectionCluster,
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Build circular intersection geometry (default)."""
        cx, cy, cz = cluster.center
        radius = cluster.max_width / 2

        # Create 12-sided circle
        vertices = []
        n_sides = 12
        for i in range(n_sides):
            angle = i * 2 * math.pi / n_sides
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        # Fan triangulation from center
        center_idx = len(vertices)
        vertices.append((cx, cy, cz + 0.01))
        faces = [(center_idx, i, (i + 1) % n_sides) for i in range(n_sides)]

        return vertices, faces

    def get_crosswalk_positions(
        self,
        geometry: IntersectionGeometry,
    ) -> List[Dict[str, Any]]:
        """
        Calculate crosswalk positions for an intersection.

        Returns list of crosswalk specs with:
        - position: center of crosswalk
        - direction: angle perpendicular to road
        - width: crosswalk width
        - length: crosswalk length
        """
        if not geometry.has_crosswalks:
            return []

        crosswalks = []
        cluster = geometry.cluster
        cx, cy, cz = cluster.center

        # Place crosswalks for each road approach
        for endpoint in cluster.endpoints:
            # Direction from intersection to endpoint
            dx = endpoint.position[0] - cx
            dy = endpoint.position[1] - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 0.1:
                continue

            # Normalize and offset from center
            offset = cluster.max_width / 2 + 1.0
            px = cx + (dx / dist) * offset
            py = cy + (dy / dist) * offset

            # Crosswalk direction is perpendicular to approach
            direction = math.atan2(dy, dx) + math.pi / 2

            crosswalks.append({
                "position": (px, py, cz + 0.02),
                "direction": direction,
                "width": self.crosswalk_width,
                "length": endpoint.width * 0.8,
                "road_id": endpoint.road_id,
            })

        return crosswalks


__all__ = [
    "IntersectionType",
    "RoadEndpoint",
    "IntersectionCluster",
    "IntersectionGeometry",
    "IntersectionDetector",
    "IntersectionBuilder",
]
