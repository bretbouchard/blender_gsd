"""
Charlotte Digital Twin - Intersection Builder

Builds intersection geometry from detected clusters.
"""

import bpy
import bmesh
import sys
import math
from pathlib import Path
from typing import List, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.intersection_detector import IntersectionDetector, IntersectionType, IntersectionCluster


class IntersectionBuilder:
    """Builds Blender geometry for intersections."""

    def __init__(self, material_name: str = "asphalt_intersection"):
        self.material_name = material_name

    def build_all(self, clusters: List[IntersectionCluster]):
        """Build geometry for all intersections."""
        at_grade = [c for c in clusters if not c.is_grade_separated]

        print(f"  Building {len(at_grade)} at-grade intersections")

        for cluster in at_grade:
            self.build(cluster)

    def build(self, cluster: IntersectionCluster) -> bpy.types.Object:
        """Build geometry for a single intersection."""
        if cluster.is_grade_separated:
            return None

        # Calculate intersection polygon
        vertices, faces = self._build_polygon(cluster)

        if not vertices or not faces:
            return None

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
        max_width = max((ep.width for ep in cluster.endpoints), default=10.0)
        radius = max_width / 2 + 1.5

        if cluster.intersection_type == IntersectionType.FOUR_WAY:
            return self._build_four_way(cx, cy, cz, radius)
        elif cluster.intersection_type in (IntersectionType.THREE_WAY_T, IntersectionType.THREE_WAY_Y):
            return self._build_three_way(cx, cy, cz, radius)
        else:
            return self._build_circular(cx, cy, cz, radius)

    def _build_four_way(
        self,
        cx: float,
        cy: float,
        cz: float,
        radius: float
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
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

    def _build_three_way(
        self,
        cx: float,
        cy: float,
        cz: float,
        radius: float
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
        """Build 3-way intersection."""
        vertices = []
        for i in range(6):
            angle = i * math.pi / 3
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            vertices.append((x, y, cz + 0.01))

        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5)]

        return vertices, faces

    def _build_circular(
        self,
        cx: float,
        cy: float,
        cz: float,
        radius: float
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
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


def main():
    """Build intersections from imported roads."""
    print("\n=== Building Intersections ===")

    # Get all road objects from scene
    road_objects = []
    for obj in bpy.context.scene.objects:
        if obj.get('road_class'):
            # Get vertices in world coordinates
            vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]

            # Group vertices by connected faces to get road segments
            # For simplicity, we'll use all vertices as a single segment
            road_objects.append({
                'osm_id': obj.get('osm_id', 0),
                'name': obj.get('road_name', ''),
                'road_class': obj.get('road_class', 'local'),
                'width': obj.get('width', 10.0),
                'vertices': [(v.x, v.y, v.z) for v in vertices],
            })

    print(f"  Found {len(road_objects)} road objects")

    # Detect intersections
    detector = IntersectionDetector(
        proximity_threshold=2.0,
        elevation_threshold=3.0
    )
    clusters = detector.detect(road_objects)

    # Create collections
    intersections_coll = bpy.data.collections.get("Intersections")
    if not intersections_coll:
        intersections_coll = bpy.data.collections.new("Intersections")
        bpy.context.scene.collection.children.link(intersections_coll)

    at_grade_coll = bpy.data.collections.get("At_Grade")
    if not at_grade_coll:
        at_grade_coll = bpy.data.collections.new("At_Grade")
        intersections_coll.children.link(at_grade_coll)

    grade_sep_coll = bpy.data.collections.get("Grade_Separated")
    if not grade_sep_coll:
        grade_sep_coll = bpy.data.collections.new("Grade_Separated")
        intersections_coll.children.link(grade_sep_coll)

    # Build at-grade intersections
    builder = IntersectionBuilder()

    for cluster in detector.get_at_grade():
        obj = builder.build(cluster)
        if obj:
            at_grade_coll.objects.link(obj)

    # Mark grade-separated intersections (for reference)
    for cluster in detector.get_grade_separated():
        # Create empty marker
        empty = bpy.data.objects.new(f"GradeSep_{cluster.cluster_id}", None)
        empty.empty_type = 'SPHERE'
        empty.empty_size = 5.0
        empty.location = cluster.center
        empty['cluster_id'] = cluster.cluster_id
        empty['intersection_type'] = 'grade_separated'
        empty['road_count'] = cluster.road_count
        bpy.context.scene.collection.objects.link(empty)
        grade_sep_coll.objects.link(empty)

    print("Intersection building complete!")


if __name__ == '__main__':
    main()
