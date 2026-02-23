"""
Scene Assembly Orchestrator for Charlotte Digital Twin

Assembles complete scenes from geographic data.

Usage:
    from lib.charlotte_digital_twin.geometry import SceneAssembler

    assembler = SceneAssembler()

    # Build complete scene from OSM data
    scene = assembler.build_scene(osm_data)

    # Or build individual layers
    assembler.build_road_layer(road_segments)
    assembler.build_building_layer(building_footprints)
    assembler.build_poi_layer(poi_markers)
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from .types import (
    GeometryConfig,
    RoadSegment,
    BuildingFootprint,
    POIMarker,
    RoadType,
    BuildingType,
    POICategory,
    DetailLevel,
    SceneBounds,
)
from .coordinates import CoordinateTransformer, CHARLOTTE_ORIGINS
from .scale import ScaleManager, ScalePreset
from .road_processor import RoadNetworkProcessor
from .road_geometry import RoadGeometryGenerator
from .road_materials import RoadMaterialMapper
from .building_geometry import BuildingGeometryGenerator
from .building_materials import BuildingMaterialMapper
from .poi_geometry import POIGeometryGenerator


@dataclass
class SceneLayer:
    """Represents a layer in the scene."""
    name: str
    objects: List[Any] = field(default_factory=list)
    visible: bool = True
    selectable: bool = True


@dataclass
class SceneStats:
    """Statistics about the assembled scene."""
    total_objects: int = 0
    road_segments: int = 0
    road_vertices: int = 0
    buildings: int = 0
    building_vertices: int = 0
    pois: int = 0
    intersections: int = 0
    bounds: Optional[SceneBounds] = None


class SceneAssembler:
    """
    Orchestrates the assembly of complete Charlotte Digital Twin scenes.

    Features:
    - Builds all geometry layers
    - Applies materials
    - Creates organized collections
    - Handles LOD
    - Generates ground plane
    """

    def __init__(
        self,
        config: Optional[GeometryConfig] = None,
        origin_name: str = "downtown",
    ):
        """
        Initialize scene assembler.

        Args:
            config: Geometry configuration
            origin_name: Name of Charlotte origin preset
        """
        self.config = config or GeometryConfig()

        # Set origin from preset if not specified
        if origin_name in CHARLOTTE_ORIGINS:
            self.config.origin = CHARLOTTE_ORIGINS[origin_name]

        self.transformer = CoordinateTransformer(self.config)
        self.scale_manager = ScaleManager()

        # Initialize generators
        self.road_processor = RoadNetworkProcessor(self.config, self.transformer)
        self.road_geometry = RoadGeometryGenerator(self.config, self.transformer)
        self.road_materials = RoadMaterialMapper()
        self.building_geometry = BuildingGeometryGenerator(self.config, self.transformer)
        self.building_materials = BuildingMaterialMapper()
        self.poi_geometry = POIGeometryGenerator(self.config, self.transformer)

        # Scene layers
        self.layers: Dict[str, SceneLayer] = {}

        # Stats
        self.stats = SceneStats()

        # Check Blender availability
        self._blender_available = False
        self._bpy = None
        try:
            import bpy
            self._bpy = bpy
            self._blender_available = True
        except ImportError:
            pass

    def build_scene(
        self,
        osm_data: Any,
        include_roads: bool = True,
        include_buildings: bool = True,
        include_pois: bool = True,
        include_ground: bool = True,
    ) -> Dict[str, Any]:
        """
        Build complete scene from OSM data.

        Args:
            osm_data: OSMData object from OSMDownloader
            include_roads: Whether to build road layer
            include_buildings: Whether to build building layer
            include_pois: Whether to build POI layer
            include_ground: Whether to create ground plane

        Returns:
            Dictionary with scene information
        """
        result = {
            "roads": None,
            "buildings": None,
            "pois": None,
            "ground": None,
            "stats": None,
        }

        # Process roads
        if include_roads:
            result["roads"] = self.build_road_layer_from_osm(osm_data)

        # Process buildings
        if include_buildings:
            result["buildings"] = self.build_building_layer_from_osm(osm_data)

        # Process POIs
        if include_pois:
            result["pois"] = self.build_poi_layer_from_osm(osm_data)

        # Create ground plane
        if include_ground:
            result["ground"] = self.create_ground_plane()

        # Update stats
        result["stats"] = self.get_scene_stats()

        return result

    def build_road_layer_from_osm(
        self,
        osm_data: Any,
        collection_name: str = "Roads",
        create_meshes: bool = True,
    ) -> Optional[SceneLayer]:
        """
        Build road layer from OSM data.

        Args:
            osm_data: OSMData object
            collection_name: Name for collection
            create_meshes: Whether to create meshes (vs curves)

        Returns:
            SceneLayer object
        """
        if not self._blender_available:
            return None

        # Process roads from OSM
        segments = self.road_processor.process(osm_data)

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        objects = []

        # Create meshes for each segment
        for segment in segments:
            if create_meshes:
                obj = self.road_geometry.create_road_mesh(segment)
            else:
                obj = self.road_geometry.create_curve(segment)

            if obj:
                # Apply material
                self.road_materials.apply_material_to_segment(obj, segment)

                # Move to collection
                self._bpy.context.collection.objects.unlink(obj)
                collection.objects.link(obj)
                objects.append(obj)

        # Create layer
        layer = SceneLayer(name=collection_name, objects=objects)
        self.layers[collection_name] = layer

        # Update stats
        self.stats.road_segments = len(objects)
        self.stats.intersections = len(self.road_processor.get_intersections())

        return layer

    def build_road_layer(
        self,
        segments: List[RoadSegment],
        collection_name: str = "Roads",
        create_meshes: bool = True,
    ) -> Optional[SceneLayer]:
        """
        Build road layer from RoadSegment objects.

        Args:
            segments: List of RoadSegment objects
            collection_name: Name for collection
            create_meshes: Whether to create meshes (vs curves)

        Returns:
            SceneLayer object
        """
        if not self._blender_available:
            return None

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        objects = []

        for segment in segments:
            if create_meshes:
                obj = self.road_geometry.create_road_mesh(segment)
            else:
                obj = self.road_geometry.create_curve(segment)

            if obj:
                self.road_materials.apply_material_to_segment(obj, segment)
                self._bpy.context.collection.objects.unlink(obj)
                collection.objects.link(obj)
                objects.append(obj)

        layer = SceneLayer(name=collection_name, objects=objects)
        self.layers[collection_name] = layer
        self.stats.road_segments = len(objects)

        return layer

    def build_building_layer_from_osm(
        self,
        osm_data: Any,
        collection_name: str = "Buildings",
    ) -> Optional[SceneLayer]:
        """
        Build building layer from OSM data.

        Args:
            osm_data: OSMData object
            collection_name: Name for collection

        Returns:
            SceneLayer object
        """
        if not self._blender_available:
            return None

        # Extract building footprints from OSM ways
        footprints = []
        for way_id, way in osm_data.ways.items():
            if way.tags.get("building"):
                footprint = self._create_footprint_from_way(way_id, way, osm_data)
                if footprint:
                    footprints.append(footprint)

        return self.build_building_layer(footprints, collection_name)

    def build_building_layer(
        self,
        footprints: List[BuildingFootprint],
        collection_name: str = "Buildings",
    ) -> Optional[SceneLayer]:
        """
        Build building layer from BuildingFootprint objects.

        Args:
            footprints: List of BuildingFootprint objects
            collection_name: Name for collection

        Returns:
            SceneLayer object
        """
        if not self._blender_available:
            return None

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        objects = []

        for footprint in footprints:
            obj = self.building_geometry.create_building(footprint)
            if obj:
                self.building_materials.apply_material_to_building(obj, footprint)
                self._bpy.context.collection.objects.unlink(obj)
                collection.objects.link(obj)
                objects.append(obj)

        layer = SceneLayer(name=collection_name, objects=objects)
        self.layers[collection_name] = layer
        self.stats.buildings = len(objects)

        return layer

    def build_poi_layer_from_osm(
        self,
        osm_data: Any,
        collection_name: str = "POIs",
        categories: Optional[Set[POICategory]] = None,
    ) -> Optional[SceneLayer]:
        """
        Build POI layer from OSM data.

        Args:
            osm_data: OSMData object
            collection_name: Name for collection
            categories: Filter by categories

        Returns:
            SceneLayer object
        """
        if not self._blender_available:
            return None

        # Extract POIs from OSM nodes
        pois = []
        for node_id, node in osm_data.nodes.items():
            poi = self._create_poi_from_node(node_id, node)
            if poi:
                if categories is None or poi.category in categories:
                    pois.append(poi)

        return self.build_poi_layer(pois, collection_name)

    def build_poi_layer(
        self,
        pois: List[POIMarker],
        collection_name: str = "POIs",
    ) -> Optional[SceneLayer]:
        """
        Build POI layer from POIMarker objects.

        Args:
            pois: List of POIMarker objects
            collection_name: Name for collection

        Returns:
            SceneLayer object
        """
        if not self._blender_available:
            return None

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        objects = []

        for poi in pois:
            obj = self.poi_geometry.create_poi_marker(poi)
            if obj:
                self._bpy.context.collection.objects.unlink(obj)
                collection.objects.link(obj)
                objects.append(obj)

        layer = SceneLayer(name=collection_name, objects=objects)
        self.layers[collection_name] = layer
        self.stats.pois = len(objects)

        return layer

    def create_ground_plane(
        self,
        size: float = 1000.0,
        collection_name: str = "Ground",
    ) -> Optional[Any]:
        """
        Create a ground plane.

        Args:
            size: Size of ground plane in meters
            collection_name: Name for collection

        Returns:
            Ground plane object
        """
        if not self._blender_available:
            return None

        # Create collection
        collection = self._bpy.data.collections.new(collection_name)
        self._bpy.context.collection.children.link(collection)

        # Create plane
        bpy = self._bpy
        mesh = bpy.data.meshes.new("Ground_mesh")

        half = size / 2
        vertices = [
            (-half, -half, 0),
            (half, -half, 0),
            (half, half, 0),
            (-half, half, 0),
        ]
        faces = [(0, 1, 2, 3)]

        mesh.from_pydata(vertices, [], faces)

        obj = bpy.data.objects.new("Ground", mesh)
        collection.objects.link(obj)

        return obj

    def _create_footprint_from_way(
        self,
        way_id: int,
        way: Any,
        osm_data: Any,
    ) -> Optional[BuildingFootprint]:
        """Create BuildingFootprint from OSM way."""
        if not way.node_ids:
            return None

        # Get coordinates
        coords = []
        for node_id in way.node_ids:
            if node_id in osm_data.nodes:
                node = osm_data.nodes[node_id]
                world = self.transformer.latlon_to_world(node.lat, node.lon)
                coords.append(world)

        if len(coords) < 3:
            return None

        # Parse building type
        building_value = way.tags.get("building", "yes")
        try:
            building_type = BuildingType(building_value)
        except ValueError:
            building_type = BuildingType.YES

        # Parse height
        height = None
        height_str = way.tags.get("height") or way.tags.get("building:height")
        if height_str:
            try:
                height = float(height_str.replace("m", "").strip())
            except ValueError:
                pass

        # Parse levels
        levels = None
        levels_str = way.tags.get("building:levels")
        if levels_str:
            try:
                levels = int(levels_str)
            except ValueError:
                pass

        return BuildingFootprint(
            osm_id=way_id,
            name=way.tags.get("name", ""),
            building_type=building_type,
            coordinates=coords,
            height=height,
            levels=levels,
            tags=way.tags,
        )

    def _create_poi_from_node(
        self,
        node_id: int,
        node: Any,
    ) -> Optional[POIMarker]:
        """Create POIMarker from OSM node."""
        # Determine category from tags
        category = None
        for key in node.tags:
            if key in ["amenity", "tourism", "shop", "leisure", "office", "public_transport"]:
                value = node.tags[key]
                try:
                    category = POICategory(value.upper())
                except ValueError:
                    category = POICategory.OTHER
                break

        if category is None:
            return None

        # Get world position
        world = self.transformer.latlon_to_world(node.lat, node.lon)

        return POIMarker(
            osm_id=node_id,
            name=node.tags.get("name", ""),
            category=category,
            position=world,
            tags=node.tags,
        )

    def get_scene_stats(self) -> SceneStats:
        """Get statistics about the assembled scene."""
        self.stats.total_objects = (
            self.stats.road_segments +
            self.stats.buildings +
            self.stats.pois
        )
        return self.stats

    def clear_scene(self) -> None:
        """Clear all generated objects from scene."""
        if not self._blender_available:
            return

        for layer_name, layer in self.layers.items():
            for obj in layer.objects:
                if obj.name in self._bpy.data.objects:
                    self._bpy.data.objects.remove(obj, do_unlink=True)

            # Remove collection
            if layer_name in self._bpy.data.collections:
                self._bpy.data.collections.remove(
                    self._bpy.data.collections[layer_name],
                    do_unlink=True
                )

        self.layers.clear()
        self.stats = SceneStats()


__all__ = [
    "SceneAssembler",
    "SceneLayer",
    "SceneStats",
]
