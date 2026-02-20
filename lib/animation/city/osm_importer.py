"""
OSM City Importer - Real World City Generation

Imports real OpenStreetMap data and creates complete city scenes.

Usage:
    from lib.animation.city.osm_importer import OSMCityImporter

    # Import Charlotte, NC
    importer = OSMCityImporter()
    city = importer.import_city("Charlotte, NC", radius_km=2)

    # Or use preset bounding box
    city = importer.import_preset("charlotte_uptown")

    # Or custom bounding box
    city = importer.import_bbox(
        south=35.220, west=-80.850,
        north=35.235, east=-80.835
    )
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
import math
import json
import urllib.request
import urllib.parse
import random

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector
    import bmesh
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    bmesh = None
    BLENDER_AVAILABLE = False


# Charlotte NC preset locations
CHARLOTTE_PRESETS = {
    "uptown": {
        "center": (35.227, -80.843),
        "radius_km": 1.5,
        "name": "Charlotte Uptown"
    },
    "downtown_full": {
        "center": (35.227, -80.843),
        "radius_km": 3.0,
        "name": "Charlotte Downtown"
    },
    "south_end": {
        "center": (35.210, -80.855),
        "radius_km": 1.0,
        "name": "Charlotte South End"
    },
    "noDa": {
        "center": (35.245, -80.815),
        "radius_km": 0.8,
        "name": "NoDa Arts District"
    },
    "plaza_midwood": {
        "center": (35.235, -80.800),
        "radius_km": 0.8,
        "name": "Plaza Midwood"
    },
    "myers_park": {
        "center": (35.200, -80.830),
        "radius_km": 1.5,
        "name": "Myers Park"
    },
    "dilworth": {
        "center": (35.205, -80.850),
        "radius_km": 1.0,
        "name": "Dilworth"
    },
    "airport": {
        "center": (35.215, -80.945),
        "radius_km": 2.0,
        "name": "Charlotte Douglas Airport"
    },
    "university": {
        "center": (35.310, -80.730),
        "radius_km": 2.0,
        "name": "UNC Charlotte"
    },
}


@dataclass
class OSMNode:
    """OSM node (point)."""
    id: int
    lat: float
    lon: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OSMWay:
    """OSM way (line/polygon)."""
    id: int
    node_ids: List[int]
    tags: Dict[str, str] = field(default_factory=dict)
    nodes: List[OSMNode] = field(default_factory=list)

    @property
    def is_closed(self) -> bool:
        return len(self.node_ids) > 2 and self.node_ids[0] == self.node_ids[-1]

    @property
    def is_building(self) -> bool:
        return "building" in self.tags

    @property
    def is_road(self) -> bool:
        return "highway" in self.tags

    @property
    def height(self) -> float:
        """Get building height in meters."""
        if "height" in self.tags:
            try:
                h = self.tags["height"].lower().replace("m", "").strip()
                return float(h)
            except:
                pass

        if "building:levels" in self.tags:
            try:
                levels = int(self.tags["building:levels"])
                return levels * 4.0  # ~4m per floor
            except:
                pass

        # Default heights by building type
        building_type = self.tags.get("building", "yes")
        defaults = {
            "house": 8.0,
            "residential": 12.0,
            "apartments": 20.0,
            "commercial": 15.0,
            "office": 30.0,
            "retail": 10.0,
            "warehouse": 12.0,
            "industrial": 15.0,
            "church": 15.0,
            "school": 10.0,
            "hospital": 25.0,
            "hotel": 40.0,
            "skyscraper": 100.0,
        }
        return defaults.get(building_type, 12.0)


@dataclass
class ImportedCity:
    """Result of OSM import."""
    name: str
    center_lat: float
    center_lon: float
    buildings: List[OSMWay] = field(default_factory=list)
    roads: List[OSMWay] = field(default_factory=list)
    water: List[OSMWay] = field(default_factory=list)
    parks: List[OSMWay] = field(default_factory=list)

    # Blender objects after generation
    building_objects: List[Any] = field(default_factory=list)
    road_objects: List[Any] = field(default_factory=list)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box (min_lat, min_lon, max_lat, max_lon)."""
        all_nodes = []
        for way in self.buildings + self.roads:
            all_nodes.extend(way.nodes)

        if not all_nodes:
            return (0, 0, 0, 0)

        lats = [n.lat for n in all_nodes]
        lons = [n.lon for n in all_nodes]
        return (min(lats), min(lons), max(lats), max(lons))


class OSMCityImporter:
    """
    Import real-world city data from OpenStreetMap.

    Features:
    - Building import with heights
    - Road network import
    - Water/park areas
    - Coordinate transformation
    - Blender mesh generation
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    NOMINATIM_URL = "https://nominatim.openstreetmap.org"

    def __init__(self, scale: float = 1000.0):
        """
        Initialize importer.

        Args:
            scale: 1 Blender unit = scale meters
        """
        self.scale = scale
        self._nodes_cache: Dict[int, OSMNode] = {}

    def geocode(self, query: str) -> Optional[Tuple[float, float]]:
        """
        Geocode location name to lat/lon.

        Args:
            query: Location name (e.g., "Charlotte, NC")

        Returns:
            (lat, lon) or None if not found
        """
        try:
            params = urllib.parse.urlencode({
                "q": query,
                "format": "json",
                "limit": 1
            })

            req = urllib.request.Request(
                f"{self.NOMINATIM_URL}/search?{params}",
                headers={"User-Agent": "BlenderGSD/1.0"}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                results = json.loads(response.read().decode('utf-8'))

                if results:
                    return (
                        float(results[0]["lat"]),
                        float(results[0]["lon"])
                    )
        except Exception as e:
            print(f"Geocoding error: {e}")

        return None

    def import_city(
        self,
        location: str,
        radius_km: float = 2.0
    ) -> ImportedCity:
        """
        Import city by location name.

        Args:
            location: Location name (e.g., "Charlotte, NC")
            radius_km: Radius around center to import

        Returns:
            ImportedCity with all data
        """
        # Geocode location
        coords = self.geocode(location)
        if not coords:
            raise ValueError(f"Could not find location: {location}")

        lat, lon = coords

        # Calculate bounding box
        # 1 degree latitude ~111km
        delta_lat = radius_km / 111.0
        # 1 degree longitude varies by latitude
        delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))

        return self.import_bbox(
            south=lat - delta_lat,
            west=lon - delta_lon,
            north=lat + delta_lat,
            east=lon + delta_lon,
            name=location
        )

    def import_preset(self, preset_name: str) -> ImportedCity:
        """
        Import from Charlotte preset.

        Args:
            preset_name: Preset name (e.g., "uptown")

        Returns:
            ImportedCity
        """
        if preset_name not in CHARLOTTE_PRESETS:
            available = list(CHARLOTTE_PRESETS.keys())
            raise ValueError(f"Unknown preset: {preset_name}. Available: {available}")

        preset = CHARLOTTE_PRESETS[preset_name]
        lat, lon = preset["center"]
        radius_km = preset["radius_km"]

        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))

        return self.import_bbox(
            south=lat - delta_lat,
            west=lon - delta_lon,
            north=lat + delta_lat,
            east=lon + delta_lon,
            name=preset["name"]
        )

    def import_bbox(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        name: str = "City"
    ) -> ImportedCity:
        """
        Import by bounding box.

        Args:
            south, west, north, east: Bounding box coordinates
            name: City name

        Returns:
            ImportedCity with all data
        """
        city = ImportedCity(
            name=name,
            center_lat=(south + north) / 2,
            center_lon=(west + east) / 2
        )

        # Query Overpass API
        print(f"Querying OSM data for {name}...")

        # Buildings query
        building_data = self._query_overpass(f"""
            [out:json][timeout:60];
            (
                way["building"]({south},{west},{north},{east});
                relation["building"]({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
        """)
        self._parse_ways(building_data, city.buildings, is_buildings=True)
        print(f"  Found {len(city.buildings)} buildings")

        # Roads query
        road_data = self._query_overpass(f"""
            [out:json][timeout:60];
            (
                way["highway"]({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
        """)
        self._parse_ways(road_data, city.roads, is_roads=True)
        print(f"  Found {len(city.roads)} roads")

        # Water query
        water_data = self._query_overpass(f"""
            [out:json][timeout:60];
            (
                way["natural"="water"]({south},{west},{north},{east});
                way["waterway"]({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
        """)
        self._parse_ways(water_data, city.water)
        print(f"  Found {len(city.water)} water features")

        # Parks query
        parks_data = self._query_overpass(f"""
            [out:json][timeout:60];
            (
                way["leisure"="park"]({south},{west},{north},{east});
                way["landuse"="recreation_ground"]({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
        """)
        self._parse_ways(parks_data, city.parks)
        print(f"  Found {len(city.parks)} parks")

        return city

    def _query_overpass(self, query: str) -> Dict:
        """Execute Overpass API query."""
        try:
            data = urllib.parse.urlencode({"data": query}).encode('utf-8')
            req = urllib.request.Request(self.OVERPASS_URL, data=data)

            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Overpass API error: {e}")
            return {"elements": []}

    def _parse_ways(
        self,
        data: Dict,
        ways_list: List[OSMWay],
        is_buildings: bool = False,
        is_roads: bool = False
    ) -> None:
        """Parse OSM ways from API response."""
        # First pass: collect nodes
        nodes = {}
        for element in data.get("elements", []):
            if element["type"] == "node":
                nodes[element["id"]] = OSMNode(
                    id=element["id"],
                    lat=element["lat"],
                    lon=element["lon"]
                )

        # Second pass: collect ways
        for element in data.get("elements", []):
            if element["type"] == "way":
                way = OSMWay(
                    id=element["id"],
                    node_ids=element.get("nodes", []),
                    tags=element.get("tags", {})
                )

                # Attach nodes
                way.nodes = [
                    nodes[nid] for nid in way.node_ids
                    if nid in nodes
                ]

                if len(way.nodes) >= 2:
                    ways_list.append(way)

    def coords_to_local(
        self,
        lat: float,
        lon: float,
        center_lat: float,
        center_lon: float
    ) -> Tuple[float, float]:
        """Convert lat/lon to local coordinates."""
        meters_per_deg_lat = 111320.0
        meters_per_deg_lon = 111320.0 * math.cos(math.radians(lat))

        x = (lon - center_lon) * meters_per_deg_lon / self.scale
        y = (lat - center_lat) * meters_per_deg_lat / self.scale

        return (x, y)

    def create_blender_scene(
        self,
        city: ImportedCity,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create Blender scene from imported city.

        Args:
            city: ImportedCity data
            detail_level: "low", "medium", "high"

        Returns:
            Dictionary of created objects
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender not available")

        print(f"\nCreating Blender scene: {city.name}")

        result = {
            "buildings": [],
            "roads": [],
        }

        # Create main collection
        main_col = bpy.data.collections.new(city.name)
        bpy.context.collection.children.link(main_col)

        # Buildings collection
        buildings_col = bpy.data.collections.new("Buildings")
        main_col.children.link(buildings_col)

        # Create buildings
        for way in city.buildings:
            if len(way.nodes) < 3:
                continue

            obj = self._create_building_mesh(
                way,
                city.center_lat,
                city.center_lon,
                detail_level
            )

            if obj:
                buildings_col.objects.link(obj)
                result["buildings"].append(obj)

        print(f"  Created {len(result['buildings'])} building meshes")

        # Roads collection
        roads_col = bpy.data.collections.new("Roads")
        main_col.children.link(roads_col)

        # Create roads
        for way in city.roads:
            if len(way.nodes) < 2:
                continue

            obj = self._create_road_curve(
                way,
                city.center_lat,
                city.center_lon
            )

            if obj:
                roads_col.objects.link(obj)
                result["roads"].append(obj)

        print(f"  Created {len(result['roads'])} road curves")

        return result

    def _create_building_mesh(
        self,
        way: OSMWay,
        center_lat: float,
        center_lon: float,
        detail_level: str
    ) -> Optional[Any]:
        """Create building mesh from OSM way."""
        if not way.is_closed or len(way.nodes) < 4:
            return None

        # Convert coordinates
        coords = [
            self.coords_to_local(n.lat, n.lon, center_lat, center_lon)
            for n in way.nodes[:-1]  # Skip closing node
        ]

        # Create mesh
        bm = bmesh.new()
        mesh = bpy.data.meshes.new(f"Building_{way.id}")

        # Create footprint vertices
        z = 0
        base_verts = [bm.verts.new((x, y, z)) for x, y in coords]
        bm.verts.ensure_lookup_table()

        # Create top vertices
        height = way.height / self.scale
        top_verts = [bm.verts.new((x, y, height)) for x, y in coords]
        bm.verts.ensure_lookup_table()

        n = len(base_verts)

        # Create wall faces
        for i in range(n):
            v1 = base_verts[i]
            v2 = base_verts[(i + 1) % n]
            v3 = top_verts[(i + 1) % n]
            v4 = top_verts[i]

            try:
                bm.faces.new([v1, v2, v3, v4])
            except:
                pass

        # Create roof face
        try:
            bm.faces.new(top_verts)
        except:
            pass

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(mesh.name, mesh)

        # Apply material
        self._apply_building_material(obj, way)

        return obj

    def _create_road_curve(
        self,
        way: OSMWay,
        center_lat: float,
        center_lon: float
    ) -> Optional[Any]:
        """Create road curve from OSM way."""
        if len(way.nodes) < 2:
            return None

        # Convert coordinates
        coords = [
            self.coords_to_local(n.lat, n.lon, center_lat, center_lon)
            for n in way.nodes
        ]

        # Get road width from tags
        lanes = int(way.tags.get("lanes", 2))
        road_width = lanes * 3.5 / self.scale

        # Create curve
        curve = bpy.data.curves.new(f"Road_{way.id}", type='CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = road_width
        curve.fill_mode = 'FULL'

        spline = curve.splines.new('POLY')
        spline.points.add(len(coords) - 1)

        for i, (x, y) in enumerate(coords):
            spline.points[i].co = (x, y, 0, 1.0)

        obj = bpy.data.objects.new(curve.name, curve)

        # Apply asphalt material
        self._apply_road_material(obj)

        return obj

    def _apply_building_material(self, obj: Any, way: OSMWay) -> None:
        """Apply material to building."""
        mat_name = f"Building_{way.tags.get('building', 'generic')}"

        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True

            # Color based on building type
            building_type = way.tags.get("building", "yes")
            colors = {
                "office": (0.5, 0.6, 0.7),
                "commercial": (0.6, 0.55, 0.5),
                "residential": (0.8, 0.75, 0.7),
                "apartments": (0.75, 0.7, 0.65),
                "retail": (0.7, 0.6, 0.55),
                "house": (0.85, 0.8, 0.7),
                "industrial": (0.5, 0.5, 0.5),
                "church": (0.9, 0.85, 0.75),
                "school": (0.8, 0.8, 0.75),
                "hospital": (0.95, 0.95, 0.95),
            }
            color = colors.get(building_type, (0.7, 0.7, 0.7))

            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (*color, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.7

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    def _apply_road_material(self, obj: Any) -> None:
        """Apply asphalt material to road."""
        if "Road_Asphalt" in bpy.data.materials:
            mat = bpy.data.materials["Road_Asphalt"]
        else:
            mat = bpy.data.materials.new("Road_Asphalt")
            mat.use_nodes = True

            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.9

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)


# Convenience functions
def import_charlotte(preset: str = "uptown") -> ImportedCity:
    """Import Charlotte NC preset."""
    importer = OSMCityImporter()
    return importer.import_preset(preset)


def import_location(location: str, radius_km: float = 2.0) -> ImportedCity:
    """Import any location by name."""
    importer = OSMCityImporter()
    return importer.import_city(location, radius_km)


def create_city_from_osm(location: str, radius_km: float = 2.0) -> Dict[str, Any]:
    """Import location and create Blender scene."""
    importer = OSMCityImporter()
    city = importer.import_city(location, radius_km)
    return importer.create_blender_scene(city)
