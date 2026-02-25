"""
MSG-1998 Road Processor

Main orchestrator that processes existing road data from Streets_Roads
and generates complete road geometry with:
- Classification
- Intersections
- Pavement, curbs, sidewalks
- Lane markings
- Street furniture distribution
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set
import math

# Support both relative imports (package) and absolute imports (script)
try:
    from .classification import (
        RoadClass,
        RoadClassifier,
        NYCRoadSpec,
        ClassifiedRoad,
        MSG_HERO_ROADS,
        get_road_spec,
    )
    from .intersections import (
        IntersectionDetector,
        IntersectionBuilder,
        IntersectionCluster,
        IntersectionGeometry,
    )
    from .geometry import (
        RoadGeometryBuilder,
        PavementBuilder,
        CurbBuilder,
        SidewalkBuilder,
        GeometryResult,
    )
    from .markings import (
        RoadMarkingGenerator,
        MarkingBuilder,
        CrosswalkBuilder,
        MarkingGeometry,
    )
    from .furniture import (
        FurnitureDistributor,
        ManholePlacer,
        StreetFurniture,
        FurnitureType,
    )
except ImportError:
    from classification import (
        RoadClass,
        RoadClassifier,
        NYCRoadSpec,
        ClassifiedRoad,
        MSG_HERO_ROADS,
        get_road_spec,
    )
    from intersections import (
        IntersectionDetector,
        IntersectionBuilder,
        IntersectionCluster,
        IntersectionGeometry,
    )
    from geometry import (
        RoadGeometryBuilder,
        PavementBuilder,
        CurbBuilder,
        SidewalkBuilder,
        GeometryResult,
    )
    from markings import (
        RoadMarkingGenerator,
        MarkingBuilder,
        CrosswalkBuilder,
        MarkingGeometry,
    )
    from furniture import (
        FurnitureDistributor,
        ManholePlacer,
        StreetFurniture,
        FurnitureType,
    )


@dataclass
class RoadSegmentData:
    """Processed data for a road segment."""
    id: str
    name: str
    vertices: List[Tuple[float, float, float]]
    classified: ClassifiedRoad
    pavement: Optional[GeometryResult] = None
    curb: Optional[GeometryResult] = None
    sidewalk: Optional[GeometryResult] = None
    markings: List[MarkingGeometry] = field(default_factory=list)


@dataclass
class ProcessedRoadSystem:
    """Complete processed road system data."""
    segments: List[RoadSegmentData] = field(default_factory=list)
    intersections: List[IntersectionGeometry] = field(default_factory=list)
    furniture: List[StreetFurniture] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class MSGRoadProcessor:
    """
    Main processor for MSG-1998 road system.

    Reads existing road data from Streets_Roads collection,
    processes it through classification, intersection detection,
    geometry generation, and furniture distribution.

    Usage:
        processor = MSGRoadProcessor()
        result = processor.process_from_blender()

        # Or from raw data
        result = processor.process(road_data)
    """

    def __init__(
        self,
        hero_roads: Optional[Set[str]] = None,
        lod_mode: str = "hero",  # "hero" or "city"
        seed: Optional[int] = None,
    ):
        """
        Initialize processor.

        Args:
            hero_roads: Set of road names to treat as hero roads
            lod_mode: "hero" for high detail, "city" for optimized
            seed: Random seed for reproducibility
        """
        self.hero_roads = hero_roads or MSG_HERO_ROADS
        self.lod_mode = lod_mode
        self.seed = seed

        # Initialize components
        self.classifier = RoadClassifier(hero_roads=self.hero_roads)
        self.intersection_detector = IntersectionDetector(
            proximity_threshold=2.0,
            min_intersection_roads=2,
        )
        self.intersection_builder = IntersectionBuilder()
        self.geometry_builder = RoadGeometryBuilder(
            pavement_builder=PavementBuilder(),
            curb_builder=CurbBuilder(),
            sidewalk_builder=SidewalkBuilder(),
        )
        self.marking_generator = RoadMarkingGenerator()
        self.furniture_distributor = FurnitureDistributor(seed=seed)

    def process(
        self,
        road_segments: List[Dict[str, Any]],
    ) -> ProcessedRoadSystem:
        """
        Process road segments into complete road system.

        Args:
            road_segments: List of road segment dicts with:
                - id: unique identifier
                - name: road name
                - vertices: list of (x, y, z) points
                - width: optional width override
                - tags: optional OSM tags

        Returns:
            ProcessedRoadSystem with all geometry and furniture
        """
        result = ProcessedRoadSystem()

        # Step 1: Classify all roads
        classified_roads = self._classify_roads(road_segments)

        # Step 2: Detect intersections
        clusters = self.intersection_detector.detect(road_segments)
        result.intersections = [
            self.intersection_builder.build(cluster)
            for cluster in clusters
        ]

        # Step 3: Generate geometry for each road
        for i, segment in enumerate(road_segments):
            segment_id = segment.get("id", segment.get("name", f"road_{i}"))
            segment_name = segment.get("name", segment_id)
            vertices = segment.get("vertices", [])

            if len(vertices) < 2:
                continue

            classified = classified_roads.get(segment_id)
            if not classified:
                continue

            # Get road spec
            spec = classified.spec

            # Generate geometry
            geometry = self.geometry_builder.build_all(
                road_vertices=vertices,
                road_width=classified.effective_width,
                sidewalk_width=spec.sidewalk_width,
                has_curb=spec.has_curb,
                has_sidewalk=spec.has_sidewalk,
                road_name=segment_name,
            )

            # Generate markings
            markings = self.marking_generator.generate_markings(
                road_vertices=vertices,
                road_width=classified.effective_width,
                lanes=spec.lanes,
                is_oneway=spec.is_oneway,
                marking_detail=spec.marking_detail,
                road_name=segment_name,
            )

            segment_data = RoadSegmentData(
                id=segment_id,
                name=segment_name,
                vertices=vertices,
                classified=classified,
                pavement=geometry.get("pavement"),
                curb=geometry.get("curb"),
                sidewalk=geometry.get("sidewalk"),
                markings=markings,
            )
            result.segments.append(segment_data)

        # Step 4: Distribute street furniture
        intersection_positions = [
            ig.cluster.center for ig in result.intersections
        ]
        result.furniture = self.furniture_distributor.distribute(
            road_segments=road_segments,
            intersections=intersection_positions,
            lod_mode=self.lod_mode,
        )

        # Step 5: Calculate statistics
        result.statistics = self._calculate_statistics(result)

        return result

    def _classify_roads(
        self,
        road_segments: List[Dict[str, Any]],
    ) -> Dict[str, ClassifiedRoad]:
        """Classify all road segments."""
        classified = {}

        for i, segment in enumerate(road_segments):
            segment_id = segment.get("id", segment.get("name", f"road_{i}"))
            name = segment.get("name", "")
            tags = segment.get("tags", {})

            road_class = self.classifier.classify(
                name=name,
                osm_highway=tags.get("highway"),
                width=segment.get("width"),
                lanes=tags.get("lanes"),
                is_oneway=tags.get("oneway") == "yes",
                tags=tags,
            )
            spec = self.classifier.get_spec(road_class)

            classified[segment_id] = ClassifiedRoad(
                name=name,
                road_class=road_class,
                spec=spec,
                width_override=segment.get("width"),
                is_hero=road_class == RoadClass.HERO,
                lod_level=spec.lod_default,
                tags=tags,
            )

        return classified

    def _calculate_statistics(
        self,
        result: ProcessedRoadSystem,
    ) -> Dict[str, Any]:
        """Calculate statistics about processed roads."""
        stats = {
            "total_segments": len(result.segments),
            "total_intersections": len(result.intersections),
            "total_furniture": len(result.furniture),
            "by_class": {},
            "total_length_m": 0.0,
            "hero_roads": 0,
            "furniture_by_type": {},
        }

        # Count by class
        for segment in result.segments:
            cls = segment.classified.road_class.value
            stats["by_class"][cls] = stats["by_class"].get(cls, 0) + 1

            if segment.classified.is_hero:
                stats["hero_roads"] += 1

            # Calculate length
            verts = segment.vertices
            for i in range(1, len(verts)):
                dx = verts[i][0] - verts[i - 1][0]
                dy = verts[i][1] - verts[i - 1][1]
                stats["total_length_m"] += math.sqrt(dx * dx + dy * dy)

        # Count furniture by type
        for item in result.furniture:
            ft = item.furniture_type.value
            stats["furniture_by_type"][ft] = stats["furniture_by_type"].get(ft, 0) + 1

        return stats

    def process_from_blender(
        self,
        collection_name: str = "Streets_Roads",
    ) -> ProcessedRoadSystem:
        """
        Process roads directly from Blender collection.

        Args:
            collection_name: Name of collection containing road meshes

        Returns:
            ProcessedRoadSystem with all geometry and furniture
        """
        try:
            import bpy
        except ImportError:
            raise ImportError("Blender required for process_from_blender")

        # Extract road data from collection
        road_segments = []

        collection = bpy.data.collections.get(collection_name)
        if not collection:
            raise ValueError(f"Collection '{collection_name}' not found")

        for obj in collection.objects:
            if obj.type != 'MESH':
                continue

            # Extract vertices in world space
            vertices = []
            mesh = obj.data

            # Get world matrix for proper coordinates
            world_matrix = obj.matrix_world

            for vertex in mesh.vertices:
                world_pos = world_matrix @ vertex.co
                vertices.append((world_pos.x, world_pos.y, world_pos.z))

            # Sort vertices along the road (approximate)
            vertices = self._sort_vertices_along_road(vertices)

            road_segments.append({
                "id": obj.name,
                "name": obj.name,
                "vertices": vertices,
                "width": obj.get("road_width", None),
                "tags": {
                    k.replace("tag_", ""): v
                    for k, v in obj.items()
                    if k.startswith("tag_")
                },
            })

        return self.process(road_segments)

    def _sort_vertices_along_road(
        self,
        vertices: List[Tuple[float, float, float]],
    ) -> List[Tuple[float, float, float]]:
        """
        Sort vertices to form a continuous path along the road.

        Uses nearest-neighbor approach to order vertices.
        """
        if len(vertices) <= 2:
            return vertices

        # Start with first vertex
        sorted_verts = [vertices[0]]
        remaining = list(vertices[1:])

        while remaining:
            last = sorted_verts[-1]

            # Find nearest neighbor
            min_dist = float('inf')
            nearest_idx = 0

            for i, v in enumerate(remaining):
                dist = math.sqrt(
                    (v[0] - last[0]) ** 2 +
                    (v[1] - last[1]) ** 2
                )
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = i

            sorted_verts.append(remaining.pop(nearest_idx))

        return sorted_verts

    def create_blender_objects(
        self,
        result: ProcessedRoadSystem,
        target_collection: Optional[str] = None,
    ) -> Dict[str, List[Any]]:
        """
        Create Blender objects from processed road system.

        Args:
            result: ProcessedRoadSystem from process()
            target_collection: Collection to add objects to

        Returns:
            Dict mapping object types to created Blender objects
        """
        try:
            import bpy
            import bmesh
        except ImportError:
            raise ImportError("Blender required for create_blender_objects")

        created = {
            "pavements": [],
            "curbs": [],
            "sidewalks": [],
            "markings": [],
            "intersections": [],
        }

        # Get or create target collection
        if target_collection:
            collection = bpy.data.collections.get(target_collection)
            if not collection:
                collection = bpy.data.collections.new(target_collection)
                bpy.context.scene.collection.children.link(collection)
        else:
            collection = bpy.context.collection

        # Create objects for each segment
        for segment in result.segments:
            # Pavement
            if segment.pavement and segment.pavement.vertices:
                obj = self._create_mesh_object(
                    segment.pavement,
                    f"{segment.name}_pavement",
                )
                collection.objects.link(obj)
                created["pavements"].append(obj)

            # Curb
            if segment.curb and segment.curb.vertices:
                obj = self._create_mesh_object(
                    segment.curb,
                    f"{segment.name}_curb",
                )
                collection.objects.link(obj)
                created["curbs"].append(obj)

            # Sidewalk
            if segment.sidewalk and segment.sidewalk.vertices:
                obj = self._create_mesh_object(
                    segment.sidewalk,
                    f"{segment.name}_sidewalk",
                )
                collection.objects.link(obj)
                created["sidewalks"].append(obj)

            # Markings
            for i, marking in enumerate(segment.markings):
                if marking.vertices:
                    obj = self._create_mesh_object(
                        marking,
                        f"{segment.name}_marking_{i}",
                    )
                    collection.objects.link(obj)
                    created["markings"].append(obj)

        # Create intersection objects
        for i, intersection in enumerate(result.intersections):
            if intersection.vertices:
                obj = self._create_mesh_object(
                    intersection,
                    f"intersection_{i}",
                )
                collection.objects.link(obj)
                created["intersections"].append(obj)

        return created

    def _create_mesh_object(
        self,
        geometry: Any,
        name: str,
    ) -> Any:
        """Create a Blender mesh object from geometry data."""
        import bpy
        import bmesh

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Add vertices
        vert_map = {}
        for v in geometry.vertices:
            bm_vert = bm.verts.new(v)
            vert_map[v] = bm_vert

        bm.verts.ensure_lookup_table()

        # Add faces
        for face in geometry.faces:
            try:
                bm_face_verts = [bm.verts[i] for i in face]
                bm.faces.new(bm_face_verts)
            except ValueError:
                pass  # Skip invalid faces

        bm.to_mesh(mesh)
        bm.free()

        return obj


def process_msg_roads(
    collection_name: str = "Streets_Roads",
    hero_roads: Optional[Set[str]] = None,
    lod_mode: str = "hero",
    create_objects: bool = True,
    target_collection: str = "Roads_Processed",
) -> ProcessedRoadSystem:
    """
    Convenience function to process MSG roads in Blender.

    Args:
        collection_name: Source collection with road meshes
        hero_roads: Set of hero road names
        lod_mode: "hero" for high detail, "city" for optimized
        create_objects: Whether to create Blender objects
        target_collection: Collection for created objects

    Returns:
        ProcessedRoadSystem with all data
    """
    processor = MSGRoadProcessor(
        hero_roads=hero_roads,
        lod_mode=lod_mode,
    )

    result = processor.process_from_blender(collection_name)

    if create_objects:
        processor.create_blender_objects(result, target_collection)

    return result


__all__ = [
    "RoadSegmentData",
    "ProcessedRoadSystem",
    "MSGRoadProcessor",
    "process_msg_roads",
]
