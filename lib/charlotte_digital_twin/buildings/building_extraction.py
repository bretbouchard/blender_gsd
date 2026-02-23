"""
Building Extraction System

Extracts and generates buildings from OSM data:
- Building footprint parsing
- Height estimation from OSM tags
- Procedural building generation
- LOD system for distant buildings

Integrates with OpenStreetMap data for Charlotte urban areas.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random
import xml.etree.ElementTree as ET

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any


class BuildingType(Enum):
    """Types of buildings."""
    OFFICE = "office"
    RESIDENTIAL = "residential"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    PARKING = "parking"
    HOTEL = "hotel"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    APARTMENTS = "apartments"
    CHURCH = "church"
    UNKNOWN = "unknown"


@dataclass
class BuildingFootprint:
    """A building footprint from OSM data."""
    id: str
    name: str = ""
    building_type: BuildingType = BuildingType.UNKNOWN
    height: float = 10.0  # Meters
    levels: int = 3
    footprint: List[Tuple[float, float]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    # Position offset
    origin: Tuple[float, float] = (0.0, 0.0)


@dataclass
class BuildingConfig:
    """Configuration for building generation."""
    # Default dimensions
    default_height: float = 10.0
    default_levels: int = 3
    level_height: float = 3.5  # Meters per floor

    # Extrusion
    extrude_height: bool = True

    # Details
    add_windows: bool = True
    window_width: float = 1.5
    window_height: float = 1.8
    window_spacing: float = 2.5

    # Roof
    roof_type: str = "flat"  # flat, gabled, hipped
    roof_height: float = 2.0

    # Materials
    wall_color: Tuple[float, float, float] = (0.7, 0.7, 0.7)
    window_color: Tuple[float, float, float] = (0.3, 0.5, 0.7)
    roof_color: Tuple[float, float, float] = (0.4, 0.35, 0.3)


# Building type color mapping
BUILDING_TYPE_COLORS = {
    BuildingType.OFFICE: (0.6, 0.65, 0.7),       # Blue-gray
    BuildingType.RESIDENTIAL: (0.75, 0.7, 0.6),  # Tan
    BuildingType.RETAIL: (0.8, 0.75, 0.7),       # Light pink/gray
    BuildingType.INDUSTRIAL: (0.5, 0.5, 0.5),    # Gray
    BuildingType.PARKING: (0.55, 0.55, 0.55),    # Dark gray
    BuildingType.HOTEL: (0.7, 0.65, 0.6),        # Warm gray
    BuildingType.HOSPITAL: (0.9, 0.9, 0.9),      # White
    BuildingType.SCHOOL: (0.8, 0.75, 0.65),      # Cream
    BuildingType.APARTMENTS: (0.72, 0.68, 0.62), # Brown-gray
    BuildingType.CHURCH: (0.85, 0.8, 0.75),      # Stone
    BuildingType.UNKNOWN: (0.65, 0.65, 0.65),    # Neutral gray
}


class BuildingExtractor:
    """
    Extracts building data from OSM XML files.

    Parses OpenStreetMap data to get building footprints,
    heights, and types for 3D generation.
    """

    def __init__(self):
        """Initialize the building extractor."""
        self._nodes: Dict[str, Tuple[float, float]] = {}
        self._ways: Dict[str, List[str]] = {}
        self._buildings: List[BuildingFootprint] = []

    def parse_osm_file(
        self,
        osm_path: str,
        origin: Optional[Tuple[float, float]] = None,
    ) -> List[BuildingFootprint]:
        """
        Parse buildings from OSM XML file.

        Args:
            osm_path: Path to .osm file
            origin: Optional origin offset (lat, lon)

        Returns:
            List of building footprints
        """
        try:
            tree = ET.parse(osm_path)
            root = tree.getroot()

            # Clear previous data
            self._nodes.clear()
            self._ways.clear()
            self._buildings.clear()

            # Parse nodes first
            for node in root.findall('node'):
                node_id = node.get('id')
                lat = float(node.get('lat', 0))
                lon = float(node.get('lon', 0))
                self._nodes[node_id] = (lat, lon)

            # Parse ways
            for way in root.findall('way'):
                way_id = way.get('id')
                node_refs = [nd.get('ref') for nd in way.findall('nd')]
                self._ways[way_id] = node_refs

                # Check if it's a building
                tags = {tag.get('k'): tag.get('v') for tag in way.findall('tag')}

                if tags.get('building') == 'yes' or 'building' in tags:
                    building = self._create_building_footprint(
                        way_id, node_refs, tags, origin
                    )
                    if building:
                        self._buildings.append(building)

            return self._buildings

        except Exception as e:
            print(f"Error parsing OSM file: {e}")
            return []

    def _create_building_footprint(
        self,
        way_id: str,
        node_refs: List[str],
        tags: Dict[str, str],
        origin: Optional[Tuple[float, float]],
    ) -> Optional[BuildingFootprint]:
        """Create building footprint from OSM way."""
        # Get coordinates for each node
        footprint = []
        for ref in node_refs:
            if ref in self._nodes:
                lat, lon = self._nodes[ref]
                footprint.append((lat, lon))

        if len(footprint) < 3:
            return None

        # Remove duplicate last point (OSM ways are closed)
        if footprint[0] == footprint[-1]:
            footprint = footprint[:-1]

        # Get building properties
        name = tags.get('name', '')

        # Building type
        building_type = BuildingType.UNKNOWN
        type_str = tags.get('building', tags.get('amenity', ''))
        type_map = {
            'office': BuildingType.OFFICE,
            'residential': BuildingType.RESIDENTIAL,
            'retail': BuildingType.RETAIL,
            'commercial': BuildingType.RETAIL,
            'industrial': BuildingType.INDUSTRIAL,
            'parking': BuildingType.PARKING,
            'hotel': BuildingType.HOTEL,
            'hospital': BuildingType.HOSPITAL,
            'school': BuildingType.SCHOOL,
            'apartments': BuildingType.APARTMENTS,
            'church': BuildingType.CHURCH,
            'yes': BuildingType.UNKNOWN,
        }
        building_type = type_map.get(type_str.lower(), BuildingType.UNKNOWN)

        # Height estimation
        height = 10.0
        levels = 3

        if 'height' in tags:
            try:
                height_str = tags['height'].replace('m', '').strip()
                height = float(height_str)
            except ValueError:
                pass

        if 'building:levels' in tags:
            try:
                levels = int(tags['building:levels'])
                if height == 10.0:  # Use levels if no explicit height
                    height = levels * 3.5
            except ValueError:
                pass

        return BuildingFootprint(
            id=way_id,
            name=name,
            building_type=building_type,
            height=height,
            levels=levels,
            footprint=footprint,
            tags=tags,
            origin=origin or (0.0, 0.0),
        )

    def get_buildings_in_bounds(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
    ) -> List[BuildingFootprint]:
        """Get buildings within geographic bounds."""
        result = []

        for building in self._buildings:
            # Check if any footprint point is in bounds
            for lat, lon in building.footprint:
                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    result.append(building)
                    break

        return result


class BuildingGenerator:
    """
    Generates 3D building geometry from footprints.

    Creates procedural buildings with configurable detail levels.
    """

    def __init__(self):
        """Initialize building generator."""
        self._material_cache: Dict[str, Any] = {}

    def create_building(
        self,
        footprint: BuildingFootprint,
        config: Optional[BuildingConfig] = None,
        name: str = "Building",
    ) -> Optional[Object]:
        """
        Create 3D building from footprint.

        Args:
            footprint: Building footprint data
            config: Generation configuration
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE or len(footprint.footprint) < 3:
            return None

        config = config or BuildingConfig()

        # Create parent
        building_obj = bpy.data.objects.new(name, None)
        building_obj.empty_display_type = "PLAIN_AXES"

        # Create main building body
        body = self._create_building_body(footprint, config, f"{name}_Body")
        if body:
            body.parent = building_obj

        # Create roof
        roof = self._create_roof(footprint, config, f"{name}_Roof")
        if roof:
            roof.location = (0, 0, footprint.height)
            roof.parent = building_obj

        return building_obj

    def _create_building_body(
        self,
        footprint: BuildingFootprint,
        config: BuildingConfig,
        name: str,
    ) -> Optional[Object]:
        """Create extruded building body."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        # Convert geographic coords to local meters (approximate)
        points = self._convert_footprint_to_local(footprint)

        # Create bottom face
        bottom_verts = []
        for x, y in points:
            vert = bm.verts.new((x, y, 0))
            bottom_verts.append(vert)

        bm.verts.ensure_lookup_table()
        bottom_face = bm.faces.new(bottom_verts)

        # Extrude to height
        top_verts = bmesh.ops.extrude_face_region(
            bm,
            geom=[bottom_face],
        )['geom']

        # Move top vertices up
        for geom in top_verts:
            if isinstance(geom, bmesh.types.BMVert):
                geom.co.z += footprint.height

        bm.to_mesh(mesh)
        bm.free()

        # Apply material
        color = BUILDING_TYPE_COLORS.get(footprint.building_type, config.wall_color)
        mat = self._get_wall_material(color)
        if mat:
            obj.data.materials.append(mat)

        # Smooth shade
        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    def _create_roof(
        self,
        footprint: BuildingFootprint,
        config: BuildingConfig,
        name: str,
    ) -> Optional[Object]:
        """Create building roof."""
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        points = self._convert_footprint_to_local(footprint)

        if config.roof_type == "flat":
            # Simple flat roof
            verts = []
            for x, y in points:
                vert = bm.verts.new((x, y, 0))
                verts.append(vert)

            bm.verts.ensure_lookup_table()
            bm.faces.new(verts)

        elif config.roof_type == "gabled":
            # Gabled roof
            # Find the longest edge for ridge direction
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)

            # Simple gable along X axis
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            # Create ridge point
            ridge_z = config.roof_height
            ridge_y = center_y

            # Create roof vertices
            bm.verts.new((min_x, min_y, 0))
            bm.verts.new((max_x, min_y, 0))
            bm.verts.new((max_x, max_y, 0))
            bm.verts.new((min_x, max_y, 0))
            bm.verts.new((center_x, ridge_y, ridge_z))

            bm.verts.ensure_lookup_table()

            # Create faces
            bm.faces.new([bm.verts[0], bm.verts[1], bm.verts[4]])
            bm.faces.new([bm.verts[1], bm.verts[2], bm.verts[4]])
            bm.faces.new([bm.verts[2], bm.verts[3], bm.verts[4]])
            bm.faces.new([bm.verts[3], bm.verts[0], bm.verts[4]])

        bm.to_mesh(mesh)
        bm.free()

        mat = self._get_roof_material(config.roof_color)
        if mat:
            obj.data.materials.append(mat)

        return obj

    def _convert_footprint_to_local(
        self,
        footprint: BuildingFootprint,
    ) -> List[Tuple[float, float]]:
        """Convert geographic coordinates to local meters."""
        # Simple approximation: 1 degree ~ 111km
        # For Charlotte area
        origin_lat, origin_lon = footprint.origin

        points = []
        for lat, lon in footprint.footprint:
            # Convert to meters relative to origin
            x = (lon - origin_lon) * 111000 * math.cos(math.radians(lat))
            y = (lat - origin_lat) * 111000
            points.append((x, y))

        return points

    def _get_wall_material(self, color: Tuple[float, float, float]) -> Optional[Any]:
        """Get or create wall material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"wall_{color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        mat = bpy.data.materials.new("Building_Wall")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.7
            bsdf.inputs["Metallic"].default_value = 0.0

        self._material_cache[cache_key] = mat
        return mat

    def _get_roof_material(self, color: Tuple[float, float, float]) -> Optional[Any]:
        """Get or create roof material."""
        if not BLENDER_AVAILABLE:
            return None

        if "roof" in self._material_cache:
            return self._material_cache["roof"]

        mat = bpy.data.materials.new("Building_Roof")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
            bsdf.inputs["Metallic"].default_value = 0.0

        self._material_cache["roof"] = mat
        return mat


def generate_buildings_from_osm(
    osm_path: str,
    origin: Tuple[float, float],
    config: Optional[BuildingConfig] = None,
    collection: Optional[Collection] = None,
    max_buildings: int = 100,
) -> List[Object]:
    """
    Generate 3D buildings from OSM file.

    Args:
        osm_path: Path to .osm file
        origin: Origin offset (lat, lon)
        config: Building configuration
        collection: Collection to add to
        max_buildings: Maximum buildings to generate

    Returns:
        List of created building objects
    """
    extractor = BuildingExtractor()
    footprints = extractor.parse_osm_file(osm_path, origin)

    generator = BuildingGenerator()
    objects = []

    for i, footprint in enumerate(footprints[:max_buildings]):
        building = generator.create_building(
            footprint,
            config,
            name=f"Building_{footprint.name or i}",
        )

        if building:
            if collection:
                collection.objects.link(building)
            objects.append(building)

    return objects


def create_placeholder_building(
    center: Tuple[float, float, float],
    width: float,
    depth: float,
    height: float,
    building_type: BuildingType = BuildingType.OFFICE,
    name: str = "Building",
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Create a simple placeholder building.

    Args:
        center: Building center position
        width: Building width
        depth: Building depth
        height: Building height
        building_type: Type of building
        name: Object name
        collection: Collection to add to

    Returns:
        Blender mesh object
    """
    if not BLENDER_AVAILABLE:
        return None

    footprint = BuildingFootprint(
        id="placeholder",
        building_type=building_type,
        height=height,
        footprint=[
            (-width/2, -depth/2),
            (width/2, -depth/2),
            (width/2, depth/2),
            (-width/2, depth/2),
        ],
    )

    generator = BuildingGenerator()
    building = generator.create_building(footprint, name=name)

    if building:
        building.location = center

        if collection:
            collection.objects.link(building)

    return building


__all__ = [
    "BuildingType",
    "BuildingFootprint",
    "BuildingConfig",
    "BUILDING_TYPE_COLORS",
    "BuildingExtractor",
    "BuildingGenerator",
    "generate_buildings_from_osm",
    "create_placeholder_building",
]
