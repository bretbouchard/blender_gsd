"""
Charlotte Building Data Acquisition Module

Provides tools to fetch real building data from multiple sources:
- OpenStreetMap (Overpass API) - building footprints, heights, floors
- Microsoft Global ML Building Footprints - accurate footprints
- CTBUH Skyscraper Center - verified heights for tall buildings
- Local building database - curated Charlotte building data

Usage:
    from lib.charlotte_digital_twin.data.building_data import (
        CharlotteBuildingDataFetcher,
        fetch_osm_buildings,
        fetch_microsoft_footprints,
        get_charlotte_building_database,
    )

    # Fetch buildings from OSM
    fetcher = CharlotteBuildingDataFetcher()
    buildings = fetcher.fetch_osm_buildings()

    # Get curated database
    db = get_charlotte_building_database()
    duke_energy = db.get_building("duke_energy_center")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import urllib.request
import urllib.parse
import time

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

try:
    from shapely.geometry import Polygon, Point
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


class BuildingDataSource(Enum):
    """Sources for building data."""
    OSM = "openstreetmap"
    MICROSOFT = "microsoft_ml"
    CTBUH = "ctbuh"
    LOCAL = "local_database"
    MANUAL = "manual"


@dataclass
class BuildingData:
    """Complete building data structure."""
    # Identification
    name: str
    osm_id: Optional[int] = None
    source: BuildingDataSource = BuildingDataSource.MANUAL

    # Location
    latitude: float = 0.0
    longitude: float = 0.0
    address: str = ""
    polygon: Optional[List[Tuple[float, float]]] = None  # List of (lon, lat) pairs

    # Dimensions
    height_m: float = 0.0
    height_ft: float = 0.0
    floors: int = 0
    width_m: float = 0.0
    depth_m: float = 0.0

    # Building classification
    building_type: str = "office"  # office, residential, hotel, retail, museum, mixed
    material: str = "glass"  # glass, concrete, brick, steel, granite
    roof_type: str = "flat"  # flat, crown, spire, rounded, art_deco

    # LED lighting
    has_led: bool = False
    led_count: int = 0
    led_type: str = ""  # full_facade, crown, accent, ribbon, spire

    # Metadata
    year_built: int = 0
    architect: str = ""
    developer: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "osm_id": self.osm_id,
            "source": self.source.value,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "height_m": self.height_m,
            "height_ft": self.height_ft,
            "floors": self.floors,
            "width_m": self.width_m,
            "depth_m": self.depth_m,
            "building_type": self.building_type,
            "material": self.material,
            "roof_type": self.roof_type,
            "has_led": self.has_led,
            "led_count": self.led_count,
            "led_type": self.led_type,
            "year_built": self.year_built,
            "architect": self.architect,
            "developer": self.developer,
            "notes": self.notes,
        }


# Charlotte bounding box (approximate)
CHARLOTTE_BBOX = {
    "west": -80.9,
    "south": 35.0,
    "east": -80.5,
    "north": 35.4,
}

# Charlotte Uptown bounding box (downtown core)
CHARLOTTE_UPTOWN_BBOX = {
    "west": -80.855,
    "south": 35.215,
    "east": -80.830,
    "north": 35.235,
}


class CharlotteBuildingDataFetcher:
    """Fetches building data from multiple sources."""

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Any] = {}

    def fetch_osm_buildings(
        self,
        bbox: Optional[Dict[str, float]] = None,
        building_type: Optional[str] = None,
        min_height: float = 0.0,
    ) -> List[BuildingData]:
        """
        Fetch building data from OpenStreetMap via Overpass API.

        Args:
            bbox: Bounding box {west, south, east, north}
            building_type: Filter by building type (office, apartments, etc.)
            min_height: Minimum height in meters

        Returns:
            List of BuildingData objects
        """
        bbox = bbox or CHARLOTTE_UPTOWN_BBOX

        # Build Overpass query
        query = f"""
        [out:json][timeout:60];
        (
          way["building"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
          relation["building"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
        );
        out body;
        """

        try:
            data = urllib.parse.urlencode({"data": query}).encode('utf-8')
            req = urllib.request.Request(self.OVERPASS_URL, data=data)
            req.add_header('User-Agent', 'CharlotteDigitalTwins/1.0')

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))

            return self._parse_osm_response(result, min_height)

        except Exception as e:
            print(f"Error fetching OSM data: {e}")
            return []

    def _parse_osm_response(
        self,
        response: Dict,
        min_height: float = 0.0,
    ) -> List[BuildingData]:
        """Parse OSM Overpass API response into BuildingData objects."""
        buildings = []

        for element in response.get("elements", []):
            if element["type"] not in ["way", "relation"]:
                continue

            tags = element.get("tags", {})

            # Skip if height filter doesn't match
            height = self._parse_height(tags.get("height", "0"))
            if height < min_height:
                continue

            # Get building name
            name = tags.get("name", tags.get("building:name", ""))
            if not name:
                name = f"Building_{element['id']}"

            # Get coordinates (use first node for position)
            # Note: For full polygon, need to fetch node coordinates separately
            lat = tags.get("latitude", 0.0)
            lon = tags.get("longitude", 0.0)

            # Parse height/floors
            floors = int(tags.get("building:levels", tags.get("building:levels:underground", "0")))

            building = BuildingData(
                name=name,
                osm_id=element["id"],
                source=BuildingDataSource.OSM,
                latitude=lat,
                longitude=lon,
                address=tags.get("addr:full", tags.get("addr:housenumber", "") + " " + tags.get("addr:street", "")).strip(),
                height_m=height,
                height_ft=height * 3.28084,
                floors=floors,
                building_type=tags.get("building", "yes"),
                material=tags.get("building:material", "glass"),
                roof_type=tags.get("roof:shape", "flat"),
                year_built=int(tags.get("start_date", tags.get("year", "0"))),
            )

            buildings.append(building)

        return buildings

    def _parse_height(self, height_str: str) -> float:
        """Parse height string to meters."""
        if not height_str:
            return 0.0

        try:
            # Remove units and convert
            height_str = height_str.lower().strip()

            if height_str.endswith("m"):
                return float(height_str[:-1])
            elif height_str.endswith("ft"):
                return float(height_str[:-2]) * 0.3048
            elif height_str.endswith("'"):
                # Feet shorthand
                return float(height_str[:-1]) * 0.3048
            else:
                return float(height_str)
        except ValueError:
            return 0.0

    def fetch_tall_buildings(self) -> List[BuildingData]:
        """
        Fetch tall buildings in Charlotte using curated database.

        Returns:
            List of tall building data from local database
        """
        return get_charlotte_tall_buildings()


def get_charlotte_tall_buildings() -> List[BuildingData]:
    """
    Get curated database of Charlotte's tallest buildings.

    Data sourced from CTBUH, Wikipedia, and research.

    Returns:
        List of BuildingData for major Charlotte buildings
    """
    return [
        # Bank of America Corporate Center - Tallest in NC
        BuildingData(
            name="Bank of America Corporate Center",
            source=BuildingDataSource.CTBUH,
            latitude=35.2276,
            longitude=-80.8436,
            address="100 North Tryon Street, Charlotte, NC",
            height_m=265.0,
            height_ft=871.0,
            floors=60,
            width_m=50.0,
            depth_m=50.0,
            building_type="office",
            material="granite",
            roof_type="crown",
            has_led=True,
            led_count=350,
            led_type="crown",
            year_built=1992,
            architect="César Pelli",
            notes="Tallest building in North Carolina, distinctive granite crown",
        ),

        # Duke Energy Center (550 South Tryon)
        BuildingData(
            name="Duke Energy Center",
            source=BuildingDataSource.CTBUH,
            latitude=35.2267,
            longitude=-80.8467,
            address="550 South Tryon Street, Charlotte, NC",
            height_m=240.0,
            height_ft=786.5,
            floors=48,
            width_m=45.0,
            depth_m=45.0,
            building_type="office",
            material="glass",
            roof_type="flat",
            has_led=True,
            led_count=2500,
            led_type="full_facade",
            year_built=2010,
            architect="Smallwood, Reynolds, Stewart, Stewart & Associates",
            developer="BofA/Duke Energy",
            notes="Primary LED building, ~2,500 programmable LEDs, <$2/night operating cost",
        ),

        # Truist Center (Hearst Tower)
        BuildingData(
            name="Truist Center",
            source=BuildingDataSource.CTBUH,
            latitude=35.2252,
            longitude=-80.8401,
            address="214 North Tryon Street, Charlotte, NC",
            height_m=201.0,
            height_ft=659.0,
            floors=47,
            width_m=40.0,
            depth_m=40.0,
            building_type="office",
            material="glass",
            roof_type="art_deco",
            has_led=True,
            led_count=500,
            led_type="accent",
            year_built=2002,
            notes="Art-deco design with architectural accent lighting",
        ),

        # Bank of America Tower
        BuildingData(
            name="Bank of America Tower",
            source=BuildingDataSource.CTBUH,
            latitude=35.2270,
            longitude=-80.8420,
            address="150 North College Street, Charlotte, NC",
            height_m=193.0,
            height_ft=632.0,
            floors=33,
            width_m=40.0,
            depth_m=40.0,
            building_type="office",
            material="glass",
            roof_type="flat",
            has_led=False,
            year_built=2019,
        ),

        # One Wells Fargo Center ("The Jukebox")
        BuildingData(
            name="One Wells Fargo Center",
            source=BuildingDataSource.CTBUH,
            latitude=35.2282,
            longitude=-80.8424,
            address="301 South College Street, Charlotte, NC",
            height_m=179.0,
            height_ft=588.0,
            floors=42,
            width_m=38.0,
            depth_m=38.0,
            building_type="office",
            material="glass",
            roof_type="rounded",
            has_led=True,
            led_count=520,
            led_type="crown",
            year_built=1988,
            notes="Distinctive rounded crown, nicknamed 'The Jukebox'",
        ),

        # The Vue
        BuildingData(
            name="The Vue",
            source=BuildingDataSource.CTBUH,
            latitude=35.2290,
            longitude=-80.8470,
            address="227 East 5th Street, Charlotte, NC",
            height_m=176.0,
            height_ft=576.0,
            floors=51,
            width_m=35.0,
            depth_m=35.0,
            building_type="residential",
            material="glass",
            roof_type="flat",
            has_led=False,
            year_built=2010,
            notes="Tallest residential building in Charlotte",
        ),

        # FNB Tower
        BuildingData(
            name="FNB Tower",
            source=BuildingDataSource.LOCAL,
            latitude=35.2270,
            longitude=-80.8510,
            address="401 South Graham Street, Charlotte, NC",
            height_m=115.0,
            height_ft=377.0,
            floors=25,
            width_m=35.0,
            depth_m=35.0,
            building_type="mixed",
            material="glass",
            roof_type="flat",
            has_led=True,
            led_count=1300,
            led_type="full_facade",
            year_built=2021,
            notes="Modern tower with full LED facade",
        ),

        # Honeywell Tower
        BuildingData(
            name="Honeywell Tower",
            source=BuildingDataSource.LOCAL,
            latitude=35.2210,
            longitude=-80.8520,
            address="855 South Mint Street, Charlotte, NC",
            height_m=100.0,
            height_ft=328.0,
            floors=23,
            width_m=40.0,
            depth_m=40.0,
            building_type="office",
            material="glass",
            roof_type="flat",
            has_led=True,
            led_count=560,
            led_type="full_facade",
            year_built=2021,
            notes="Honeywell headquarters, contemporary LED lighting",
        ),

        # Ally Charlotte Center
        BuildingData(
            name="Ally Charlotte Center",
            source=BuildingDataSource.LOCAL,
            latitude=35.2245,
            longitude=-80.8440,
            address="201 South Tryon Street, Charlotte, NC",
            height_m=122.0,
            height_ft=400.0,
            floors=26,
            width_m=38.0,
            depth_m=38.0,
            building_type="office",
            material="glass",
            roof_type="flat",
            has_led=True,
            led_count=800,
            led_type="full_facade",
            year_built=2020,
            notes="Modern illuminated facade",
        ),

        # Carillon Tower
        BuildingData(
            name="Carillon Tower",
            source=BuildingDataSource.CTBUH,
            latitude=35.2265,
            longitude=-80.8475,
            address="227 West Trade Street, Charlotte, NC",
            height_m=120.0,
            height_ft=394.0,
            floors=24,
            width_m=30.0,
            depth_m=30.0,
            building_type="office",
            material="concrete",
            roof_type="spire",
            has_led=True,
            led_count=310,
            led_type="spire",
            year_built=1988,
            notes="Neo-gothic bell tower spire with accent lighting",
        ),

        # NASCAR Hall of Fame
        BuildingData(
            name="NASCAR Hall of Fame",
            source=BuildingDataSource.LOCAL,
            latitude=35.2250,
            longitude=-80.8390,
            address="400 East Martin Luther King Jr Boulevard, Charlotte, NC",
            height_m=30.0,
            height_ft=100.0,
            floors=5,
            width_m=80.0,
            depth_m=60.0,
            building_type="museum",
            material="glass",
            roof_type="flat",
            has_led=True,
            led_count=800,
            led_type="ribbon",
            year_built=2010,
            notes="Distinctive curved LED ribbon, track-inspired design",
        ),

        # 200 South Tryon
        BuildingData(
            name="200 South Tryon",
            source=BuildingDataSource.CTBUH,
            latitude=35.2255,
            longitude=-80.8450,
            address="200 South Tryon Street, Charlotte, NC",
            height_m=148.0,
            height_ft=485.0,
            floors=34,
            width_m=35.0,
            depth_m=35.0,
            building_type="office",
            material="glass",
            roof_type="flat",
            has_led=True,
            led_count=480,
            led_type="accent",
            year_built=1985,
            notes="Glass curtain wall with accent lighting",
        ),
    ]


class CharlotteBuildingDatabase:
    """Database of Charlotte buildings with search and lookup."""

    def __init__(self):
        self._buildings: Dict[str, BuildingData] = {}
        self._load_buildings()

    def _load_buildings(self):
        """Load buildings into database."""
        buildings = get_charlotte_tall_buildings()
        for building in buildings:
            key = building.name.lower().replace(" ", "_").replace("-", "_")
            self._buildings[key] = building

    def get_building(self, name: str) -> Optional[BuildingData]:
        """Get building by name."""
        key = name.lower().replace(" ", "_").replace("-", "_")
        return self._buildings.get(key)

    def get_all_buildings(self) -> List[BuildingData]:
        """Get all buildings."""
        return list(self._buildings.values())

    def get_led_buildings(self) -> List[BuildingData]:
        """Get all buildings with LED systems."""
        return [b for b in self._buildings.values() if b.has_led]

    def get_tallest_buildings(self, count: int = 10) -> List[BuildingData]:
        """Get tallest buildings."""
        sorted_buildings = sorted(
            self._buildings.values(),
            key=lambda b: b.height_m,
            reverse=True
        )
        return sorted_buildings[:count]

    def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = 1.0,
    ) -> List[BuildingData]:
        """Find buildings near a coordinate."""
        from math import radians, sin, cos, sqrt, atan2

        nearby = []
        for building in self._buildings.values():
            # Haversine distance calculation
            lat1, lon1 = radians(lat), radians(lon)
            lat2, lon2 = radians(building.latitude), radians(building.longitude)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))

            distance_km = 6371 * c  # Earth radius in km

            if distance_km <= radius_km:
                nearby.append(building)

        return nearby

    def export_json(self, filepath: str):
        """Export database to JSON file."""
        data = {
            "buildings": [b.to_dict() for b in self._buildings.values()],
            "metadata": {
                "total_buildings": len(self._buildings),
                "led_buildings": len(self.get_led_buildings()),
                "source": "Charlotte Digital Twin Project",
            }
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Singleton instance
_database: Optional[CharlotteBuildingDatabase] = None


def get_charlotte_building_database() -> CharlotteBuildingDatabase:
    """Get the singleton building database."""
    global _database
    if _database is None:
        _database = CharlotteBuildingDatabase()
    return _database


# Convenience functions
def fetch_osm_buildings(
    bbox: Optional[Dict[str, float]] = None,
) -> List[BuildingData]:
    """Fetch buildings from OpenStreetMap."""
    fetcher = CharlotteBuildingDataFetcher()
    return fetcher.fetch_osm_buildings(bbox)


def load_cached_osm_buildings() -> List[BuildingData]:
    """
    Load cached OSM building data from local JSON file.

    The file charlotte_osm_buildings.json contains 1,054 buildings
    from Charlotte Uptown fetched from OpenStreetMap.

    Returns:
        List of BuildingData objects from cached OSM data
    """
    import os

    # Find the cached file
    module_dir = os.path.dirname(__file__)
    cache_file = os.path.join(module_dir, "charlotte_osm_buildings.json")

    if not os.path.exists(cache_file):
        print(f"Cached OSM file not found: {cache_file}")
        return []

    with open(cache_file, 'r') as f:
        data = json.load(f)

    buildings = []
    for b in data.get("buildings", []):
        # Parse height
        height_str = b.get("height", "")
        height_m = 0.0
        if height_str:
            try:
                height_m = float(str(height_str).replace("m", "").strip())
            except ValueError:
                pass

        # Parse floors
        floors = 0
        if b.get("floors"):
            try:
                floors = int(b["floors"])
            except ValueError:
                pass

        building = BuildingData(
            name=b.get("name", f"Building_{b['osm_id']}"),
            osm_id=b.get("osm_id"),
            source=BuildingDataSource.OSM,
            address=b.get("address", ""),
            height_m=height_m,
            height_ft=height_m * 3.28084,
            floors=floors,
            building_type=b.get("building_type", "yes"),
            material=b.get("material", "glass"),
        )
        buildings.append(building)

    return buildings


def get_named_osm_buildings(min_floors: int = 0) -> List[BuildingData]:
    """
    Get named buildings from cached OSM data.

    Args:
        min_floors: Minimum number of floors to include

    Returns:
        List of named BuildingData objects
    """
    buildings = load_cached_osm_buildings()
    named = [b for b in buildings if not b.name.startswith("Building_")]

    if min_floors > 0:
        named = [b for b in named if b.floors >= min_floors]

    # Sort by floors (descending)
    named.sort(key=lambda b: b.floors, reverse=True)

    return named


def get_led_buildings() -> List[BuildingData]:
    """Get all Charlotte buildings with LED systems."""
    db = get_charlotte_building_database()
    return db.get_led_buildings()


def load_building_footprints(
    area: str = "uptown",
) -> Dict[str, Any]:
    """
    Load building footprint polygons from GeoJSON files.

    Args:
        area: "uptown", "named", or "all"

    Returns:
        GeoJSON FeatureCollection dict with building polygons
    """
    import os

    module_dir = os.path.dirname(__file__)

    file_map = {
        "uptown": "charlotte_uptown_buildings.geojson",
        "named": "charlotte_buildings_named.geojson",
        "all": "charlotte_buildings.geojson",
    }

    filename = file_map.get(area, "charlotte_uptown_buildings.geojson")
    filepath = os.path.join(module_dir, filename)

    if not os.path.exists(filepath):
        print(f"GeoJSON file not found: {filepath}")
        return {"type": "FeatureCollection", "features": []}

    with open(filepath, 'r') as f:
        return json.load(f)


def get_building_polygons(
    min_floors: int = 0,
    bbox: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Get building polygon data with optional filtering.

    Args:
        min_floors: Minimum number of floors
        bbox: Optional bounding box filter {west, south, east, north}

    Returns:
        List of building dicts with 'polygon', 'name', 'height', 'floors'
    """
    geojson = load_building_footprints("uptown")

    buildings = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        # Floor filter
        floors = 0
        if props.get("levels"):
            try:
                floors = int(props["levels"])
            except:
                pass

        if floors < min_floors:
            continue

        # Bbox filter
        if bbox and geom.get("type") == "Polygon":
            coords = geom["coordinates"][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            centroid_lon = sum(lons) / len(lons)
            centroid_lat = sum(lats) / len(lats)

            if not (bbox["west"] <= centroid_lon <= bbox["east"] and
                    bbox["south"] <= centroid_lat <= bbox["north"]):
                continue

        # Height parsing
        height = 0.0
        if props.get("height"):
            try:
                height = float(str(props["height"]).replace("m", "").strip())
            except:
                pass

        buildings.append({
            "osm_id": props.get("osm_id"),
            "name": props.get("name", ""),
            "building_type": props.get("building", "yes"),
            "height_m": height,
            "floors": floors,
            "polygon": geom.get("coordinates", [[]])[0] if geom.get("type") == "Polygon" else [],
        })

    return buildings


def get_building_stats() -> Dict[str, Any]:
    """
    Get statistics about available building data.

    Returns:
        Dict with building counts and file info
    """
    import os

    module_dir = os.path.dirname(__file__)

    stats = {
        "ctbuh_buildings": 0,
        "osm_buildings": 0,
        "osm_uptown": 0,
        "osm_named": 0,
        "files": {},
    }

    # CTBUH curated
    ctbuh = get_charlotte_tall_buildings()
    stats["ctbuh_buildings"] = len(ctbuh)

    # OSM cached
    osm_cached = load_cached_osm_buildings()
    stats["osm_buildings"] = len(osm_cached)

    # GeoJSON files
    files = {
        "uptown": "charlotte_uptown_buildings.geojson",
        "named": "charlotte_buildings_named.geojson",
        "all": "charlotte_buildings.geojson",
        "polygons": "charlotte_osm_polygons.json",
    }

    for key, filename in files.items():
        filepath = os.path.join(module_dir, filename)
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            stats["files"][key] = {
                "path": filepath,
                "size_kb": size_kb,
            }

            # Count features in GeoJSON
            if filename.endswith(".geojson"):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                count = len(data.get("features", []))
                stats["files"][key]["count"] = count

                if key == "uptown":
                    stats["osm_uptown"] = count
                elif key == "named":
                    stats["osm_named"] = count

    return stats
