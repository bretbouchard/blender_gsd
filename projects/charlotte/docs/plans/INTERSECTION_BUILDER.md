# Charlotte - Intersection Builder Plan

## Goal
Detect and build intersections from the road network, handling both at-grade intersections and grade-separated highway interchanges (bridges).

## Requirements
- Detect where roads meet (shared vertices or endpoint proximity)
- Distinguish at-grade from grade-separated intersections
- Build intersection geometry with proper materials
- Place crosswalks where appropriate
- Handle complex highway interchanges

## Key Differences from MSG-1998

| Aspect | MSG-1998 | Charlotte |
|--------|----------|-----------|
| Grade Separation | Minimal | Critical (265 bridges) |
| Highway Interchanges | None | I-77/I-85/I-277 complex |
| Intersection Types | Grid-based 4-way | Organic + interchanges |

## Implementation

### File: `scripts/lib/intersection_detector.py`

```python
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
    GRADE_SEPARATED = "grade_separated"  # Highway interchange
    OVERPASS = "overpass"  # Roads cross at different elevations

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
            diff = abs(angles[1] - angles[0])
            if diff > math.pi:
                diff = 2 * math.pi - diff

            if abs(diff - math.pi) < 0.3:
                # Roads are opposite - it's a merge
                pass  # Not really an intersection
            else:
                self.intersection_type = IntersectionType.OVERPASS

        elif n == 3:
            angles = sorted([ep.direction for ep in self.endpoints])
            diffs = []
            for i in range(3):
                diff = angles[(i + 1) % 3] - angles[i]
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

    def detect(self, road_segments: List[dict]) -> List[IntersectionCluster]:
        """
        Detect intersections from road segments.

        Args:
            road_segments: List of road data with vertices and properties

        Returns:
            List of detected intersection clusters
        """
        self.clusters = []

        # Extract all endpoints
        endpoints = self._extract_endpoints(road_segments)
        print(f"Extracted {len(endpoints)} road endpoints")

        # Cluster endpoints by proximity
        self._cluster_endpoints(endpoints)
        print(f"Found {len(self.clusters)} potential intersections")

        # Post-process
        self._postprocess_clusters()

        return self.clusters

    def _extract_endpoints(self, road_segments: List[dict]) -> List[RoadEndpoint]:
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

    def _postprocess_clusters(self) -> None:
        """Process clusters to determine types and filter."""
        # Check grade separation and determine types
        for cluster in self.clusters:
            cluster.check_grade_separation(self.elevation_threshold)
            cluster.determine_type()

        # Filter out single-road clusters (not real intersections)
        self.clusters = [c for c in self.clusters if c.road_count >= 2]

        # Separate at-grade from grade-separated
        at_grade = [c for c in self.clusters if not c.is_grade_separated]
        grade_separated = [c for c in self.clusters if c.is_grade_separated]

        print(f"At-grade intersections: {len(at_grade)}")
        print(f"Grade-separated intersections: {len(grade_separated)}")

    def get_at_grade(self) -> List[IntersectionCluster]:
        """Get at-grade intersections."""
        return [c for c in self.clusters if not c.is_grade_separated]

    def get_grade_separated(self) -> List[IntersectionCluster]:
        """Get grade-separated intersections."""
        return [c for c in self.clusters if c.is_grade_separated]
```

### File: `scripts/lib/intersection_builder.py`

```python
import bpy
import bmesh
from typing import List, Tuple
import math

from .intersection_detector import IntersectionCluster, IntersectionType

class IntersectionBuilder:
    """Builds Blender geometry for intersections."""

    def __init__(self, material_name: str = "asphalt_intersection"):
        self.material_name = material_name

    def build_all(self, clusters: List[IntersectionCluster]):
        """Build geometry for all intersections."""
        at_grade = [c for c in clusters if not c.is_grade_separated]

        print(f"Building {len(at_grade)} at-grade intersections")

        for cluster in at_grade:
            self.build(cluster)

    def build(self, cluster: IntersectionCluster) -> bpy.types.Object:
        """Build geometry for a single intersection."""
        if cluster.is_grade_separated:
            return None  # Skip grade-separated for now

        # Calculate intersection polygon
        vertices, faces = self._build_polygon(cluster)

        # Create mesh
        mesh = bpy.data.meshes.new(f"Intersection_{cluster.cluster_id}")

        bm = bmesh.new()
        bm_verts = [bm.verts.new(v) for v in vertices]
        bm.verts.ensure_lookup_table()

        for face in faces:
            try:
                bm.faces.new([bm_verts[i] for i in face])
            except:
                pass

        bm.to_mesh(mesh)
        bm.free()

        # Create object
        obj = bpy.data.objects.new(f"Intersection_{cluster.cluster_id}", mesh)
        bpy.context.scene.collection.objects.link(obj)

        # Add properties
        obj['cluster_id'] = cluster.cluster_id
        obj['intersection_type'] = cluster.intersection_type.value
        obj['road_count'] = cluster.road_count
        obj['roads'] = ','.join(str(rid) for rid in cluster.road_ids)

        return obj

    def _build_polygon(
        self,
        cluster: IntersectionCluster
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Build intersection polygon based on type."""
        cx, cy, cz = cluster.center

        # Get max road width for sizing
        max_width = max(ep.width for ep in cluster.endpoints)
        radius = max_width / 2 + 1.5

        if cluster.intersection_type == IntersectionType.FOUR_WAY:
            return self._build_four_way(cx, cy, cz, radius)
        elif cluster.intersection_type in (IntersectionType.THREE_WAY_T, IntersectionType.THREE_WAY_Y):
            return self._build_three_way(cx, cy, cz, radius)
        else:
            return self._build_circular(cx, cy, cz, radius)

    def _build_four_way(self, cx, cy, cz, radius):
        """Build 4-way intersection (octagonal)."""
        vertices = []
        for i in range(8):
            angle = i * math.pi / 4 + math.pi / 8
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        faces = [(0, i, i + 1) for i in range(1, 7)]
        faces.append((0, 7, 1))

        return vertices, faces

    def _build_three_way(self, cx, cy, cz, radius):
        """Build 3-way intersection."""
        vertices = []
        for i in range(6):
            angle = i * math.pi / 3
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5)]

        return vertices, faces

    def _build_circular(self, cx, cy, cz, radius):
        """Build circular intersection (12-sided)."""
        vertices = []
        n_sides = 12

        for i in range(n_sides):
            angle = i * 2 * math.pi / n_sides
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        # Fan triangulation from center
        center_idx = n_sides
        vertices.append((cx, cy, cz + 0.01))

        faces = [(center_idx, i, (i + 1) % n_sides) for i in range(n_sides)]

        return vertices, faces

class CrosswalkBuilder:
    """Builds crosswalks at intersections."""

    STRIPE_WIDTH = 0.4  # meters
    STRIPE_LENGTH = 3.0  # meters
    STRIPE_GAP = 0.6  # meters

    def build_crosswalks(self, cluster: IntersectionCluster) -> List[bpy.types.Object]:
        """Build crosswalks for an intersection."""
        if cluster.is_grade_separated:
            return []

        crosswalks = []
        cx, cy, cz = cluster.center

        for endpoint in cluster.endpoints:
            # Direction from intersection center to endpoint
            dx = endpoint.position[0] - cx
            dy = endpoint.position[1] - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 0.1:
                continue

            # Offset crosswalk from center
            offset = endpoint.width / 2 + 2.0
            px = cx + (dx / dist) * offset
            py = cy + (dy / dist) * offset

            # Crosswalk direction (perpendicular to road)
            direction = math.atan2(dy, dx) + math.pi / 2

            crosswalk = self._build_crosswalk(
                (px, py, cz + 0.02),
                direction,
                endpoint.width
            )

            if crosswalk:
                crosswalk['road_id'] = endpoint.road_id
                crosswalk['road_name'] = endpoint.road_name
                crosswalks.append(crosswalk)

        return crosswalks

    def _build_crosswalk(self, center, direction, road_width):
        """Build a single crosswalk."""
        # Create stripe geometry
        # ... (implementation details)
        pass
```

### File: `scripts/5_build_intersections.py`

```python
import bpy
from lib.intersection_detector import IntersectionDetector
from lib.intersection_builder import IntersectionBuilder, CrosswalkBuilder

def main():
    """Build intersections from imported roads."""
    # Get all road objects from scene
    road_objects = []
    for obj in bpy.context.scene.objects:
        if obj.get('road_class'):
            road_objects.append({
                'osm_id': obj['osm_id'],
                'name': obj.get('road_name', ''),
                'road_class': obj['road_class'],
                'width': obj.get('width', 10.0),
                'vertices': [v.co[:] for v in obj.data.vertices],
            })

    print(f"Found {len(road_objects)} roads")

    # Detect intersections
    detector = IntersectionDetector()
    clusters = detector.detect(road_objects)

    # Create collections
    intersections_coll = bpy.data.collections.get("Intersections")
    if not intersections_coll:
        intersections_coll = bpy.data.collections.new("Intersections")
        bpy.context.scene.collection.children.link(intersections_coll)

    at_grade_coll = bpy.data.collections.new("At_Grade")
    grade_sep_coll = bpy.data.collections.new("Grade_Separated")
    intersections_coll.children.link(at_grade_coll)
    intersections_coll.children.link(grade_sep_coll)

    # Build at-grade intersections
    builder = IntersectionBuilder()
    crosswalk_builder = CrosswalkBuilder()

    for cluster in detector.get_at_grade():
        obj = builder.build(cluster)
        if obj:
            at_grade_coll.objects.link(obj)

            # Build crosswalks
            crosswalks = crosswalk_builder.build_crosswalks(cluster)
            for cw in crosswalks:
                at_grade_coll.objects.link(cw)

    # Mark grade-separated intersections (for reference)
    for cluster in detector.get_grade_separated():
        # Create empty marker
        empty = bpy.data.objects.new(f"GradeSep_{cluster.cluster_id}", None)
        empty.empty_type = 'SPHERE'
        empty.location = cluster.center
        empty['cluster_id'] = cluster.cluster_id
        empty['intersection_type'] = 'grade_separated'
        empty['road_count'] = cluster.road_count
        grade_sep_coll.objects.link(empty)

    print("Intersection building complete!")

if __name__ == '__main__':
    main()
```

## Collection Structure

```
Intersections/
├── At_Grade/
│   ├── Intersection_intersection_0
│   ├── Intersection_intersection_1
│   ├── Crosswalk_Road_123456789
│   └── ...
└── Grade_Separated/
    ├── GradeSep_intersection_42  # Empty marker
    └── ...
```

## Custom Properties

### Intersection Object
```python
obj['cluster_id'] = "intersection_0"
obj['intersection_type'] = "4way"  # or "3way_t", "grade_separated"
obj['road_count'] = 4
obj['roads'] = "12345,67890,11111,22222"  # OSM IDs of participating roads
```

### Crosswalk Object
```python
obj['road_id'] = 123456789
obj['road_name'] = "N Tryon St"
```

## Grade Separation Logic

```
For each intersection cluster:
1. Collect all endpoint elevations
2. Calculate max - min elevation
3. If difference > 3 meters:
   - Mark as grade-separated
   - Create marker instead of geometry
   - These are highway interchanges
4. Else:
   - Build at-grade intersection geometry
```

## Success Criteria
- [ ] All at-grade intersections detected
- [ ] Grade-separated interchanges identified
- [ ] Intersection geometry built
- [ ] Crosswalks placed at appropriate intersections
- [ ] All organized into collections

## Estimated Effort
- Intersection detector: 2 hours (adapt from msg-1998)
- Grade separation logic: 1 hour
- Geometry builder: 2 hours
- Crosswalks: 1 hour
