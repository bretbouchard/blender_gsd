"""
Geo Data Bridge - Real-world Location Import

Provides integration with BlenderGIS and OpenStreetMap for importing
real-world geographic data into Blender city scenes.

Supports:
- OpenStreetMap (OSM) data import
- Digital Elevation Model (DEM) terrain
- Building footprint extraction
- Road network data
- Coordinate transformations (lat/lon to Blender units)

Usage:
    from lib.animation.city.geo_data import GeoDataBridge

    # Initialize bridge for Charlotte, NC
    bridge = GeoDataBridge()

    # Import OSM data for bounding box
    data = bridge.import_area(
        south=35.14, west=-80.92, north=35.32, east=-80.68
    )

    # Or use preset locations
    data = bridge.import_preset("charlotte_uptown")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from pathlib import Path
import json
import math
import urllib.request
import urllib.parse

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Matrix = None
    BLENDER_AVAILABLE = False


@dataclass
class GeoBoundingBox:
    """Geographic bounding box in WGS84 coordinates."""
    south: float  # Minimum latitude
    west: float   # Minimum longitude
    north: float  # Maximum latitude
    east: float   # Maximum longitude

    @property
    def center(self) -> Tuple[float, float]:
        """Get center point (lat, lon)."""
        return (
            (self.south + self.north) / 2,
            (self.west + self.east) / 2
        )

    @property
    def width_degrees(self) -> float:
        """Width in degrees longitude."""
        return self.east - self.west

    @property
    def height_degrees(self) -> float:
        """Height in degrees latitude."""
        return self.north - self.south

    def to_blender_units(self, scale: float = 1000.0) -> Tuple[float, float]:
        """Convert to approximate Blender units (meters)."""
        # Approximate conversion at Charlotte's latitude (~35.2°)
        lat = (self.south + self.north) / 2
        meters_per_degree_lat = 111320.0
        meters_per_degree_lon = 111320.0 * math.cos(math.radians(lat))

        width_m = self.width_degrees * meters_per_degree_lon
        height_m = self.height_degrees * meters_per_degree_lat

        return (width_m / scale, height_m / scale)


@dataclass
class GeoLocation:
    """A geographic location with metadata."""
    name: str
    latitude: float
    longitude: float
    country: str = "USA"
    state: str = ""
    city: str = ""
    timezone: str = "America/New_York"

    def to_vector(self, origin: 'GeoLocation', scale: float = 1000.0) -> Tuple[float, float]:
        """Convert to local coordinates relative to origin."""
        # Simple equirectangular projection
        meters_per_degree_lat = 111320.0
        meters_per_degree_lon = 111320.0 * math.cos(math.radians(self.latitude))

        x = (self.longitude - origin.longitude) * meters_per_degree_lon / scale
        y = (self.latitude - origin.latitude) * meters_per_degree_lat / scale

        return (x, y)


@dataclass
class TerrainData:
    """Digital Elevation Model terrain data."""
    bbox: GeoBoundingBox
    elevation_data: List[List[float]] = field(default_factory=list)
    resolution: Tuple[int, int] = (100, 100)
    min_elevation: float = 0.0
    max_elevation: float = 500.0
    nodata_value: float = -9999.0

    def get_elevation_at(self, lat: float, lon: float) -> float:
        """Get interpolated elevation at coordinates."""
        if not self.elevation_data:
            return 0.0

        # Convert coords to grid indices
        x_ratio = (lon - self.bbox.west) / self.bbox.width_degrees
        y_ratio = (lat - self.bbox.south) / self.bbox.height_degrees

        x_idx = int(x_ratio * (self.resolution[0] - 1))
        y_idx = int(y_ratio * (self.resolution[1] - 1))

        # Clamp to valid range
        x_idx = max(0, min(x_idx, self.resolution[0] - 1))
        y_idx = max(0, min(y_idx, self.resolution[1] - 1))

        return self.elevation_data[y_idx][x_idx]

    def to_blender_mesh(self, name: str = "Terrain", scale: float = 1.0) -> Optional[Any]:
        """Convert terrain to Blender mesh."""
        if not BLENDER_AVAILABLE or not self.elevation_data:
            return None

        import bmesh

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Create bmesh
        bm = bmesh.new()

        width, height = self.resolution
        bbox_width, bbox_height = self.bbox.to_blender_units(scale)

        # Create vertices
        for y_idx in range(height):
            for x_idx in range(width):
                x = (x_idx / (width - 1)) * bbox_width - bbox_width / 2
                y = (y_idx / (height - 1)) * bbox_height - bbox_height / 2
                z = self.elevation_data[y_idx][x_idx] * scale

                bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        for y_idx in range(height - 1):
            for x_idx in range(width - 1):
                v1 = bm.verts[y_idx * width + x_idx]
                v2 = bm.verts[y_idx * width + x_idx + 1]
                v3 = bm.verts[(y_idx + 1) * width + x_idx + 1]
                v4 = bm.verts[(y_idx + 1) * width + x_idx]

                try:
                    bm.faces.new([v1, v2, v3, v4])
                except:
                    pass

        bm.to_mesh(mesh)
        bm.free()

        bpy.context.collection.objects.link(obj)
        return obj


@dataclass
class OSMData:
    """OpenStreetMap imported data."""
    bbox: GeoBoundingBox
    buildings: List[Dict[str, Any]] = field(default_factory=list)
    roads: List[Dict[str, Any]] = field(default_factory=list)
    waterways: List[Dict[str, Any]] = field(default_factory=list)
    parks: List[Dict[str, Any]] = field(default_factory=list)
    points_of_interest: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def building_count(self) -> int:
        return len(self.buildings)

    @property
    def road_count(self) -> int:
        return len(self.roads)


# Preset locations
GEO_PRESETS = {
    "charlotte_uptown": GeoBoundingBox(
        south=35.220, west=-80.850, north=35.235, east=-80.835
    ),
    "charlotte_downtown": GeoBoundingBox(
        south=35.210, west=-80.860, north=35.250, east=-80.820
    ),
    "charlotte_full": GeoBoundingBox(
        south=35.140, west=-80.920, north=35.320, east=-80.680
    ),
    "charlotte_airport": GeoBoundingBox(
        south=35.195, west=-80.965, north=35.240, east=-80.910
    ),
    "charlotte_university": GeoBoundingBox(
        south=35.290, west=-80.760, north=35.330, east=-80.720
    ),
    "new_york_midtown": GeoBoundingBox(
        south=40.750, west=-74.000, north=40.765, east=-73.980
    ),
    "los_angeles_downtown": GeoBoundingBox(
        south=34.045, west=-118.270, north=34.060, east=-118.240
    ),
}


class GeoDataBridge:
    """
    Bridge between real-world geo data and Blender scenes.

    Provides methods to:
    - Import OSM data via Overpass API
    - Download elevation data
    - Transform coordinates to Blender space
    - Generate procedural city layouts from real data
    """

    def __init__(
        self,
        origin: Optional[GeoLocation] = None,
        scale: float = 1000.0,
        use_metric: bool = True
    ):
        """
        Initialize geo data bridge.

        Args:
            origin: Origin point for coordinate transformation
            scale: Scale factor (1 Blender unit = scale meters)
            use_metric: Use metric units
        """
        self.origin = origin or GeoLocation(
            name="Origin",
            latitude=35.227,
            longitude=-80.843,
            city="Charlotte",
            state="North Carolina"
        )
        self.scale = scale
        self.use_metric = use_metric
        self._osm_cache: Dict[str, OSMData] = {}

    def import_area(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        include_buildings: bool = True,
        include_roads: bool = True,
        include_water: bool = True,
        include_parks: bool = True
    ) -> OSMData:
        """
        Import OSM data for a bounding box area.

        Args:
            south, west, north, east: Bounding box coordinates
            include_buildings: Import building footprints
            include_roads: Import road network
            include_water: Import waterways
            include_parks: Import parks and green spaces

        Returns:
            OSMData with imported features
        """
        bbox = GeoBoundingBox(south, west, north, east)

        osm_data = OSMData(bbox=bbox)

        # Query Overpass API for data
        if include_buildings:
            osm_data.buildings = self._query_buildings(bbox)

        if include_roads:
            osm_data.roads = self._query_roads(bbox)

        if include_water:
            osm_data.waterways = self._query_waterways(bbox)

        if include_parks:
            osm_data.parks = self._query_parks(bbox)

        return osm_data

    def import_preset(self, preset_name: str, **kwargs) -> OSMData:
        """
        Import data for a preset location.

        Args:
            preset_name: Name of preset (e.g., "charlotte_uptown")
            **kwargs: Additional arguments passed to import_area

        Returns:
            OSMData with imported features
        """
        if preset_name not in GEO_PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}. "
                           f"Available: {list(GEO_PRESETS.keys())}")

        bbox = GEO_PRESETS[preset_name]
        return self.import_area(
            south=bbox.south,
            west=bbox.west,
            north=bbox.north,
            east=bbox.east,
            **kwargs
        )

    def _query_overpass(self, query: str) -> Dict:
        """Execute Overpass API query."""
        overpass_url = "https://overpass-api.de/api/interpreter"

        try:
            data = urllib.parse.urlencode({"data": query}).encode('utf-8')
            req = urllib.request.Request(overpass_url, data=data)

            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Overpass API error: {e}")
            return {"elements": []}

    def _query_buildings(self, bbox: GeoBoundingBox) -> List[Dict]:
        """Query building footprints from OSM."""
        query = f"""
        [out:json][timeout:60];
        (
          way["building"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
          relation["building"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
        );
        out body;
        >;
        out skel qt;
        """

        result = self._query_overpass(query)
        buildings = []

        # Parse building data
        nodes = {e["id"]: (e["lat"], e["lon"])
                for e in result.get("elements", []) if e["type"] == "node"}

        for element in result.get("elements", []):
            if element["type"] == "way" and "nodes" in element:
                coords = [nodes.get(n) for n in element["nodes"] if n in nodes]
                if coords:
                    tags = element.get("tags", {})
                    buildings.append({
                        "id": element["id"],
                        "coordinates": coords,
                        "height": self._parse_height(tags.get("height", "10")),
                        "levels": int(tags.get("building:levels", 3)),
                        "name": tags.get("name", ""),
                        "type": tags.get("building", "yes"),
                        "material": tags.get("building:material", "concrete"),
                    })

        return buildings

    def _query_roads(self, bbox: GeoBoundingBox) -> List[Dict]:
        """Query road network from OSM."""
        query = f"""
        [out:json][timeout:60];
        (
          way["highway"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
        );
        out body;
        >;
        out skel qt;
        """

        result = self._query_overpass(query)
        roads = []

        nodes = {e["id"]: (e["lat"], e["lon"])
                for e in result.get("elements", []) if e["type"] == "node"}

        for element in result.get("elements", []):
            if element["type"] == "way" and "nodes" in element:
                coords = [nodes.get(n) for n in element["nodes"] if n in nodes]
                if coords:
                    tags = element.get("tags", {})
                    roads.append({
                        "id": element["id"],
                        "coordinates": coords,
                        "name": tags.get("name", ""),
                        "type": tags.get("highway", "road"),
                        "lanes": int(tags.get("lanes", 2)),
                        "surface": tags.get("surface", "asphalt"),
                        "oneway": tags.get("oneway", "no") == "yes",
                        "max_speed": tags.get("maxspeed", ""),
                    })

        return roads

    def _query_waterways(self, bbox: GeoBoundingBox) -> List[Dict]:
        """Query water features from OSM."""
        query = f"""
        [out:json][timeout:60];
        (
          way["waterway"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
          way["natural"="water"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
        );
        out body;
        >;
        out skel qt;
        """

        result = self._query_overpass(query)
        waterways = []

        nodes = {e["id"]: (e["lat"], e["lon"])
                for e in result.get("elements", []) if e["type"] == "node"}

        for element in result.get("elements", []):
            if element["type"] == "way" and "nodes" in element:
                coords = [nodes.get(n) for n in element["nodes"] if n in nodes]
                if coords:
                    waterways.append({
                        "id": element["id"],
                        "coordinates": coords,
                        "type": element.get("tags", {}).get("waterway", "river"),
                        "name": element.get("tags", {}).get("name", ""),
                    })

        return waterways

    def _query_parks(self, bbox: GeoBoundingBox) -> List[Dict]:
        """Query parks and green spaces from OSM."""
        query = f"""
        [out:json][timeout:60];
        (
          way["leisure"="park"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
          way["landuse"="grass"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
          relation["leisure"="park"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
        );
        out body;
        >;
        out skel qt;
        """

        result = self._query_overpass(query)
        parks = []

        nodes = {e["id"]: (e["lat"], e["lon"])
                for e in result.get("elements", []) if e["type"] == "node"}

        for element in result.get("elements", []):
            if element["type"] == "way" and "nodes" in element:
                coords = [nodes.get(n) for n in element["nodes"] if n in nodes]
                if coords:
                    parks.append({
                        "id": element["id"],
                        "coordinates": coords,
                        "name": element.get("tags", {}).get("name", ""),
                        "type": element.get("tags", {}).get("leisure", "park"),
                    })

        return parks

    def _parse_height(self, height_str: str) -> float:
        """Parse height string to meters."""
        if not height_str:
            return 10.0

        try:
            # Handle "15 m" or "15m" format
            height_str = height_str.strip().lower()
            if height_str.endswith("m"):
                height_str = height_str[:-1].strip()
            elif height_str.endswith("ft") or height_str.endswith("'"):
                # Convert feet to meters
                height_str = height_str.replace("ft", "").replace("'", "").strip()
                return float(height_str) * 0.3048

            return float(height_str)
        except ValueError:
            return 10.0

    def coords_to_blender(
        self,
        lat: float,
        lon: float,
        elevation: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Convert geographic coordinates to Blender world coordinates.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            elevation: Height above sea level in meters

        Returns:
            Tuple of (x, y, z) in Blender units
        """
        # Equirectangular projection centered on origin
        meters_per_degree_lat = 111320.0
        meters_per_degree_lon = 111320.0 * math.cos(math.radians(lat))

        x = (lon - self.origin.longitude) * meters_per_degree_lon / self.scale
        y = (lat - self.origin.latitude) * meters_per_degree_lat / self.scale
        z = elevation / self.scale

        return (x, y, z)

    def blender_to_coords(
        self,
        x: float,
        y: float,
        z: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Convert Blender world coordinates to geographic coordinates.

        Args:
            x, y, z: Blender world coordinates

        Returns:
            Tuple of (lat, lon, elevation) in degrees/meters
        """
        meters_per_degree_lat = 111320.0
        meters_per_degree_lon = 111320.0 * math.cos(math.radians(self.origin.latitude))

        lon = (x * self.scale / meters_per_degree_lon) + self.origin.longitude
        lat = (y * self.scale / meters_per_degree_lat) + self.origin.latitude
        elevation = z * self.scale

        return (lat, lon, elevation)

    def create_blender_scene(
        self,
        osm_data: OSMData,
        generate_buildings: bool = True,
        generate_roads: bool = True,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create Blender objects from imported OSM data.

        Args:
            osm_data: Imported OSM data
            generate_buildings: Create building meshes
            generate_roads: Create road curves
            detail_level: "low", "medium", "high"

        Returns:
            Dictionary of created Blender objects
        """
        if not BLENDER_AVAILABLE:
            return {}

        result = {
            "buildings": [],
            "roads": [],
            "waterways": [],
            "parks": [],
        }

        # Create collection for city
        city_collection = bpy.data.collections.new("City")
        bpy.context.collection.children.link(city_collection)

        # Generate buildings
        if generate_buildings:
            buildings_col = bpy.data.collections.new("Buildings")
            city_collection.children.link(buildings_col)

            for building in osm_data.buildings:
                obj = self._create_building_object(building, detail_level)
                if obj:
                    buildings_col.objects.link(obj)
                    result["buildings"].append(obj)

        # Generate roads
        if generate_roads:
            roads_col = bpy.data.collections.new("Roads")
            city_collection.children.link(roads_col)

            for road in osm_data.roads:
                obj = self._create_road_object(road, detail_level)
                if obj:
                    roads_col.objects.link(obj)
                    result["roads"].append(obj)

        return result

    def _create_building_object(
        self,
        building: Dict,
        detail_level: str
    ) -> Optional[Any]:
        """Create a Blender mesh object for a building."""
        if not BLENDER_AVAILABLE or len(building["coordinates"]) < 3:
            return None

        import bmesh

        # Convert coordinates to Blender space
        coords = [
            self.coords_to_blender(lat, lon)
            for lat, lon in building["coordinates"]
        ]

        # Create building footprint
        bm = bmesh.new()

        # Create base vertices
        base_verts = [bm.verts.new((x, y, 0.0)) for x, y, z in coords]

        # Calculate building height
        height = building.get("height", 10.0) / self.scale
        levels = building.get("levels", 3)

        # Create top vertices
        top_verts = [bm.verts.new((x, y, height)) for x, y, z in coords]

        bm.verts.ensure_lookup_table()

        # Create faces
        n = len(base_verts)

        # Create walls
        for i in range(n):
            v1 = base_verts[i]
            v2 = base_verts[(i + 1) % n]
            v3 = top_verts[(i + 1) % n]
            v4 = top_verts[i]

            try:
                bm.faces.new([v1, v2, v3, v4])
            except:
                pass

        # Create top face
        try:
            bm.faces.new(top_verts)
        except:
            pass

        # Create mesh
        mesh = bpy.data.meshes.new(f"Building_{building['id']}")
        bm.to_mesh(mesh)
        bm.free()

        # Create object
        obj = bpy.data.objects.new(mesh.name, mesh)

        # Add material based on building type
        self._apply_building_material(obj, building)

        return obj

    def _create_road_object(
        self,
        road: Dict,
        detail_level: str
    ) -> Optional[Any]:
        """Create a Blender curve object for a road."""
        if not BLENDER_AVAILABLE or len(road["coordinates"]) < 2:
            return None

        # Create curve
        curve = bpy.data.curves.new(f"Road_{road['id']}", type='CURVE')
        curve.dimensions = '3D'

        # Create spline
        spline = curve.splines.new('POLY')

        # Convert coordinates
        coords = [
            self.coords_to_blender(lat, lon)
            for lat, lon in road["coordinates"]
        ]

        spline.points.add(len(coords) - 1)
        for i, (x, y, z) in enumerate(coords):
            spline.points[i].co = (x, y, z, 1.0)

        # Set road width based on lanes
        lanes = road.get("lanes", 2)
        curve.bevel_depth = 0.001 * lanes  # Road width
        curve.fill_mode = 'FULL'

        # Create object
        obj = bpy.data.objects.new(curve.name, curve)

        return obj

    def _apply_building_material(self, obj: Any, building: Dict) -> None:
        """Apply procedural material to building based on type."""
        if not BLENDER_AVAILABLE:
            return

        building_type = building.get("type", "yes")
        material = building.get("material", "concrete")

        # Create simple material
        mat = bpy.data.materials.new(name=f"BuildingMat_{building['id']}")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Color based on building type
            colors = {
                "office": (0.7, 0.75, 0.8),
                "apartments": (0.85, 0.8, 0.75),
                "commercial": (0.75, 0.75, 0.8),
                "residential": (0.9, 0.85, 0.8),
                "retail": (0.8, 0.75, 0.7),
            }
            color = colors.get(building_type, (0.8, 0.8, 0.8))
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)


def import_osm_data(
    bbox: GeoBoundingBox,
    include_buildings: bool = True,
    include_roads: bool = True,
    **kwargs
) -> OSMData:
    """Convenience function to import OSM data."""
    bridge = GeoDataBridge()
    return bridge.import_area(
        south=bbox.south,
        west=bbox.west,
        north=bbox.north,
        east=bbox.east,
        include_buildings=include_buildings,
        include_roads=include_roads,
        **kwargs
    )


def import_terrain(
    bbox: GeoBoundingBox,
    resolution: Tuple[int, int] = (100, 100)
) -> TerrainData:
    """
    Import terrain elevation data.

    Note: This requires an elevation data source like OpenTopography.
    For now, generates procedural terrain based on location.
    """
    terrain = TerrainData(
        bbox=bbox,
        resolution=resolution,
        elevation_data=[],
        min_elevation=200.0,  # Charlotte elevation ~230m
        max_elevation=280.0
    )

    # Generate procedural terrain (would be replaced with real DEM data)
    import random
    random.seed(42)

    width, height = resolution
    for y_idx in range(height):
        row = []
        for x_idx in range(width):
            # Simple noise-based terrain
            base = 230.0  # Base elevation for Charlotte
            noise = (
                math.sin(x_idx * 0.1) * 10 +
                math.cos(y_idx * 0.1) * 10 +
                random.uniform(-5, 5)
            )
            row.append(base + noise)
        terrain.elevation_data.append(row)

    terrain.min_elevation = min(min(row) for row in terrain.elevation_data)
    terrain.max_elevation = max(max(row) for row in terrain.elevation_data)

    return terrain


def geocode_location(query: str) -> Optional[GeoLocation]:
    """
    Geocode a location string to coordinates.

    Uses Nominatim (OSM geocoding service).

    Args:
        query: Location to search (e.g., "Charlotte, NC")

    Returns:
        GeoLocation if found, None otherwise
    """
    nominatim_url = "https://nominatim.openstreetmap.org/search"

    try:
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "limit": 1
        })

        url = f"{nominatim_url}?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BlenderGSD/1.0"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            results = json.loads(response.read().decode('utf-8'))

            if results:
                result = results[0]
                return GeoLocation(
                    name=query,
                    latitude=float(result["lat"]),
                    longitude=float(result["lon"]),
                    city=result.get("display_name", "").split(",")[0]
                )
    except Exception as e:
        print(f"Geocoding error: {e}")

    return None


def create_city_from_geo(
    location: str,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    detail_level: str = "full"
) -> Dict[str, Any]:
    """
    Create a city from geographic data.

    Args:
        location: Location name or preset
        bbox: Optional bounding box (south, west, north, east)
        detail_level: "minimal", "low", "medium", "full"

    Returns:
        Dictionary with created city data
    """
    bridge = GeoDataBridge()

    # Determine bounding box
    if bbox:
        osm_data = bridge.import_area(*bbox)
    elif location in GEO_PRESETS:
        osm_data = bridge.import_preset(location)
    else:
        # Geocode location
        geo_loc = geocode_location(location)
        if geo_loc:
            # Create bbox around location
            delta = 0.01  # ~1km
            osm_data = bridge.import_area(
                south=geo_loc.latitude - delta,
                west=geo_loc.longitude - delta,
                north=geo_loc.latitude + delta,
                east=geo_loc.longitude + delta
            )
        else:
            raise ValueError(f"Could not find location: {location}")

    # Create Blender scene
    return bridge.create_blender_scene(osm_data, detail_level=detail_level)
