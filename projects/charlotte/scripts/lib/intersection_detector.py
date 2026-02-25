"""
Charlotte Digital Twin - Intersection Detector

Detects intersections from the road network, handling both
at-grade intersections and grade-separated highway interchanges.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
import math


class IntersectionType(Enum):
    """Types of intersections."""
    FOUR_WAY = "4way"
    THREE_WAY_T = "3way_t"
    THREE_WAY_Y = "3way_y"
    FIVE_WAY = "5way"
    ROUNDABOUT = "roundabout"
    GRADE_SEPARATED = "grade_separated"
    OVERPASS = "overpass"


@dataclass
class RoadEndpoint:
    """Endpoint of a road segment."""
    road_id: int
    road_name: str
    position: Tuple[float, float, float]
    is_start: bool
    direction: float  # Heading in radians
    width: float
    road_class: str

    def distance_to(self, other_pos: Tuple[float, float, float]) -> float:
        """Calculate 2D distance to another point."""
        dx = other_pos[0] - self.position[0]
        dy = other_pos[1] - self.position[1]
        return math.sqrt(dx * dx + dy * dy)

    def elevation_diff(self, other_pos: Tuple[float, float, float]) -> float:
        """Calculate elevation difference."""
        return abs(self.position[2] - other_pos[2])


@dataclass
class IntersectionCluster:
    """Cluster of road endpoints forming an intersection."""
    cluster_id: str
    endpoints: List[RoadEndpoint] = field(default_factory=list)
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    intersection_type: IntersectionType = IntersectionType.FOUR_WAY
    is_grade_separated: bool = False

    @property
    def road_ids(self) -> Set[int]:
        return {ep.road_id for ep in self.endpoints}

    @property
    def road_count(self) -> int:
        return len(self.road_ids)

    def calculate_center(self) -> Tuple[float, float, float]:
        """Calculate geometric center of intersection."""
        if not self.endpoints:
            return (0.0, 0.0, 0.0)

        x = sum(ep.position[0] for ep in self.endpoints) / len(self.endpoints)
        y = sum(ep.position[1] for ep in self.endpoints) / len(self.endpoints)
        z = sum(ep.position[2] for ep in self.endpoints) / len(self.endpoints)

        self.center = (x, y, z)
        return self.center

    def check_grade_separation(self, threshold: float = 3.0) -> bool:
        """
        Check if this is a grade-separated intersection.

        Args:
            threshold: Elevation difference (meters) to consider grade-separated
        """
        if len(self.endpoints) < 2:
            return False

        elevations = [ep.position[2] for ep in self.endpoints]
        max_diff = max(elevations) - min(elevations)

        self.is_grade_separated = max_diff > threshold
        return self.is_grade_separated

    def determine_type(self) -> IntersectionType:
        """Determine intersection type from configuration."""
        if self.is_grade_separated:
            self.intersection_type = IntersectionType.GRADE_SEPARATED
            return self.intersection_type

        n = self.road_count

        if n == 2:
            # Check if crossing or merging
            angles = sorted([ep.direction for ep in self.endpoints])
            if len(angles) >= 2:
                diff = abs(angles[1] - angles[0])
                if diff > math.pi:
                    diff = 2 * math.pi - diff

                if abs(diff - math.pi) < 0.3:
                    pass  # Roads are opposite - merge, not intersection
                else:
                    self.intersection_type = IntersectionType.OVERPASS

        elif n == 3:
            angles = sorted([ep.direction for ep in self.endpoints])
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


class IntersectionDetector:
    """Detects intersections from road network."""

    def __init__(
        self,
        proximity_threshold: float = 2.0,
        elevation_threshold: float = 3.0,
    ):
        """
        Args:
            proximity_threshold: Distance (meters) to consider endpoints as same intersection
            elevation_threshold: Elevation difference to consider grade-separated
        """
        self.proximity_threshold = proximity_threshold
        self.elevation_threshold = elevation_threshold
        self.clusters: List[IntersectionCluster] = []

    def detect(
        self,
        road_segments: List[Dict],
        min_roads: int = 2
    ) -> List[IntersectionCluster]:
        """
        Detect intersections from road segments.

        Args:
            road_segments: List of road data with vertices and properties
            min_roads: Minimum roads to form an intersection

        Returns:
            List of detected intersection clusters
        """
        self.clusters = []

        # Extract all endpoints
        endpoints = self._extract_endpoints(road_segments)
        print(f"  Extracted {len(endpoints)} road endpoints")

        # Cluster endpoints by proximity
        self._cluster_endpoints(endpoints)
        print(f"  Found {len(self.clusters)} potential intersections")

        # Post-process
        self._postprocess_clusters(min_roads)

        return self.clusters

    def _extract_endpoints(self, road_segments: List[Dict]) -> List[RoadEndpoint]:
        """Extract road endpoints with metadata."""
        endpoints = []

        for road in road_segments:
            vertices = road.get('vertices', [])
            if len(vertices) < 2:
                continue

            road_id = road['osm_id']
            road_name = road.get('name', f"Road_{road_id}")
            width = road.get('width', 10.0)
            road_class = road.get('road_class', 'local')

            # Start endpoint
            start_dir = self._calculate_direction(vertices[0], vertices[1])
            endpoints.append(RoadEndpoint(
                road_id=road_id,
                road_name=road_name,
                position=tuple(vertices[0]),
                is_start=True,
                direction=start_dir,
                width=width,
                road_class=road_class,
            ))

            # End endpoint
            end_dir = self._calculate_direction(vertices[-2], vertices[-1])
            endpoints.append(RoadEndpoint(
                road_id=road_id,
                road_name=road_name,
                position=tuple(vertices[-1]),
                is_start=False,
                direction=end_dir,
                width=width,
                road_class=road_class,
            ))

        return endpoints

    def _calculate_direction(self, p1: Tuple, p2: Tuple) -> float:
        """Calculate heading from p1 to p2."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.atan2(dy, dx)

    def _cluster_endpoints(self, endpoints: List[RoadEndpoint]) -> None:
        """Cluster endpoints by proximity."""
        cluster_id = 0

        for endpoint in endpoints:
            found_cluster = None

            for cluster in self.clusters:
                if cluster.endpoints:
                    # Check 2D proximity
                    dist = endpoint.distance_to(cluster.center)
                    if dist < self.proximity_threshold:
                        found_cluster = cluster
                        break

            if found_cluster:
                found_cluster.endpoints.append(endpoint)
                found_cluster.calculate_center()
            else:
                new_cluster = IntersectionCluster(
                    cluster_id=f"intersection_{cluster_id}",
                    endpoints=[endpoint],
                )
                new_cluster.calculate_center()
                self.clusters.append(new_cluster)
                cluster_id += 1

    def _postprocess_clusters(self, min_roads: int) -> None:
        """Process clusters to determine types and filter."""
        # Check grade separation and determine types
        for cluster in self.clusters:
            cluster.check_grade_separation(self.elevation_threshold)
            cluster.determine_type()

        # Filter out clusters with too few roads
        self.clusters = [c for c in self.clusters if c.road_count >= min_roads]

        # Separate at-grade from grade-separated
        at_grade = [c for c in self.clusters if not c.is_grade_separated]
        grade_separated = [c for c in self.clusters if c.is_grade_separated]

        print(f"  At-grade intersections: {len(at_grade)}")
        print(f"  Grade-separated intersections: {len(grade_separated)}")

    def get_at_grade(self) -> List[IntersectionCluster]:
        """Get at-grade intersections."""
        return [c for c in self.clusters if not c.is_grade_separated]

    def get_grade_separated(self) -> List[IntersectionCluster]:
        """Get grade-separated intersections."""
        return [c for c in self.clusters if c.is_grade_separated]
