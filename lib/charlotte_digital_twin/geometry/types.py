"""
Geometry Types for Charlotte Digital Twin

Core data types for coordinate transformation, scene configuration,
and geometry generation.

Usage:
    from lib.charlotte_digital_twin.geometry import (
        SceneOrigin,
        GeometryConfig,
        CoordinateTransformer,
    )

    # Configure scene
    config = GeometryConfig(
        origin=SceneOrigin(
            lat=35.2271,
            lon=-80.8431,
            name="Charlotte Downtown"
        )
    )

    # Transform coordinates
    transformer = CoordinateTransformer(config)
    world_pos = transformer.latlon_to_world(35.2280, -80.8420)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class DetailLevel(Enum):
    """Level of detail for geometry generation."""
    MINIMAL = "minimal"       # Low poly, simple shapes
    STANDARD = "standard"     # Normal detail
    HIGH = "high"             # High detail with features
    ULTRA = "ultra"           # Maximum detail


class RoadType(Enum):
    """Road classification types."""
    MOTORWAY = "motorway"
    MOTORWAY_LINK = "motorway_link"
    TRUNK = "trunk"
    TRUNK_LINK = "trunk_link"
    PRIMARY = "primary"
    PRIMARY_LINK = "primary_link"
    SECONDARY = "secondary"
    SECONDARY_LINK = "secondary_link"
    TERTIARY = "tertiary"
    TERTIARY_LINK = "tertiary_link"
    RESIDENTIAL = "residential"
    SERVICE = "service"
    UNCLASSIFIED = "unclassified"
    FOOTWAY = "footway"
    PEDESTRIAN = "pedestrian"
    CYCLEWAY = "cycleway"
    PATH = "path"
    TRACK = "track"
    STEPS = "steps"


class BuildingType(Enum):
    """Building classification types."""
    YES = "yes"               # Generic building
    APARTMENTS = "apartments"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    RETAIL = "retail"
    RESIDENTIAL = "residential"
    HOUSE = "house"
    DETACHED = "detached"
    TERRACE = "terrace"
    HOTEL = "hotel"
    SCHOOL = "school"
    UNIVERSITY = "university"
    COLLEGE = "college"
    HOSPITAL = "hospital"
    CHURCH = "church"
    CIVIC = "civic"
    GOVERNMENT = "government"
    INDUSTRIAL = "industrial"
    WAREHOUSE = "warehouse"
    PARKING = "parking"
    STADIUM = "stadium"
    TRAIN_STATION = "train_station"


class POICategory(Enum):
    """POI classification types."""
    RESTAURANT = "RESTAURANT"
    CAFE = "CAFE"
    BAR = "BAR"
    SHOP = "SHOP"
    HOTEL = "HOTEL"
    ATTRACTION = "ATTRACTION"
    MUSEUM = "MUSEUM"
    PARK = "PARK"
    SCHOOL = "SCHOOL"
    HOSPITAL = "HOSPITAL"
    POLICE = "POLICE"
    FIRE_STATION = "FIRE_STATION"
    PUBLIC_TRANSPORT = "PUBLIC_TRANSPORT"
    PARKING = "PARKING"
    FUEL = "FUEL"
    BANK = "BANK"
    POST_OFFICE = "POST_OFFICE"
    LIBRARY = "LIBRARY"
    PLACE_OF_WORSHIP = "PLACE_OF_WORSHIP"
    SPORTS = "SPORTS"
    ENTERTAINMENT = "ENTERTAINMENT"
    OFFICE = "OFFICE"
    OTHER = "OTHER"


@dataclass
class SceneOrigin:
    """
    Defines the origin point for the scene in geographic coordinates.
    All other coordinates are transformed relative to this origin.

    Charlotte NC default: Downtown (35.2271, -80.8431)
    """
    lat: float = 35.2271
    lon: float = -80.8431
    name: str = "Charlotte Downtown"
    elevation: float = 230.0  # meters, Charlotte average

    # UTM zone (Charlotte is Zone 17N)
    utm_zone: int = 17
    utm_hemisphere: str = "N"


@dataclass
class GeometryConfig:
    """
    Configuration for geometry generation.

    Controls how geographic data is converted to Blender geometry.
    """
    # Scene origin
    origin: SceneOrigin = field(default_factory=SceneOrigin)

    # Scale: how many Blender units per meter
    # Default: 1.0 (1 meter = 1 Blender unit)
    scale: float = 1.0

    # Detail level for geometry generation
    detail_level: DetailLevel = DetailLevel.STANDARD

    # Coordinate system settings
    flatten_to_plane: bool = True  # Ignore elevation for 2D layout
    z_offset: float = 0.0          # Base Z offset for all geometry

    # Road settings
    default_road_width: float = 7.0   # meters
    road_height: float = 0.1          # meters (road thickness)

    # Building settings
    default_building_height: float = 10.0  # meters (when not specified)
    max_building_height: float = 500.0      # meters (cap for tall buildings)
    min_building_height: float = 3.0        # meters (minimum height)

    # POI settings
    poi_marker_size: float = 2.0  # meters
    poi_marker_height: float = 5.0  # meters

    # Material settings
    use_procedural_materials: bool = True
    default_material_color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "origin": {
                "lat": self.origin.lat,
                "lon": self.origin.lon,
                "name": self.origin.name,
                "elevation": self.origin.elevation,
                "utm_zone": self.origin.utm_zone,
                "utm_hemisphere": self.origin.utm_hemisphere,
            },
            "scale": self.scale,
            "detail_level": self.detail_level.value,
            "flatten_to_plane": self.flatten_to_plane,
            "z_offset": self.z_offset,
            "default_road_width": self.default_road_width,
            "road_height": self.road_height,
            "default_building_height": self.default_building_height,
            "max_building_height": self.max_building_height,
            "min_building_height": self.min_building_height,
            "poi_marker_size": self.poi_marker_size,
            "poi_marker_height": self.poi_marker_height,
            "use_procedural_materials": self.use_procedural_materials,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeometryConfig":
        """Create from dictionary."""
        origin_data = data.get("origin", {})
        origin = SceneOrigin(
            lat=origin_data.get("lat", 35.2271),
            lon=origin_data.get("lon", -80.8431),
            name=origin_data.get("name", "Charlotte Downtown"),
            elevation=origin_data.get("elevation", 230.0),
            utm_zone=origin_data.get("utm_zone", 17),
            utm_hemisphere=origin_data.get("utm_hemisphere", "N"),
        )
        return cls(
            origin=origin,
            scale=data.get("scale", 1.0),
            detail_level=DetailLevel(data.get("detail_level", "standard")),
            flatten_to_plane=data.get("flatten_to_plane", True),
            z_offset=data.get("z_offset", 0.0),
            default_road_width=data.get("default_road_width", 7.0),
            road_height=data.get("road_height", 0.1),
            default_building_height=data.get("default_building_height", 10.0),
            max_building_height=data.get("max_building_height", 500.0),
            min_building_height=data.get("min_building_height", 3.0),
            poi_marker_size=data.get("poi_marker_size", 2.0),
            poi_marker_height=data.get("poi_marker_height", 5.0),
            use_procedural_materials=data.get("use_procedural_materials", True),
        )


@dataclass
class WorldCoordinate:
    """3D coordinate in Blender world space."""
    x: float  # East-West (meters from origin)
    y: float  # North-South (meters from origin)
    z: float  # Up-Down (meters from origin/elevation)

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)

    def to_list(self) -> List[float]:
        """Convert to list."""
        return [self.x, self.y, self.z]


@dataclass
class GeoCoordinate:
    """Geographic coordinate (WGS84)."""
    lat: float
    lon: float
    elevation: float = 0.0


@dataclass
class UTMCoordinate:
    """UTM coordinate."""
    easting: float   # X in meters
    northing: float  # Y in meters
    zone: int        # UTM zone
    hemisphere: str  # N or S


@dataclass
class RoadSegment:
    """Processed road segment ready for geometry generation."""
    osm_id: int
    name: str
    road_type: RoadType
    coordinates: List[WorldCoordinate]  # World coordinates
    width: float  # meters
    lanes: int
    surface: str
    is_bridge: bool
    is_tunnel: bool
    is_oneway: bool

    # Tags from OSM
    tags: Dict[str, str] = field(default_factory=dict)

    def get_length(self) -> float:
        """Calculate approximate length of segment in meters."""
        total = 0.0
        for i in range(len(self.coordinates) - 1):
            p1 = self.coordinates[i]
            p2 = self.coordinates[i + 1]
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            total += (dx * dx + dy * dy) ** 0.5
        return total


@dataclass
class BuildingFootprint:
    """Processed building footprint ready for geometry generation."""
    osm_id: int
    name: str
    building_type: BuildingType
    coordinates: List[WorldCoordinate]  # Footprint vertices
    height: float  # meters
    levels: Optional[int]
    outline: List[WorldCoordinate]  # Same as coordinates, explicit

    # Tags from OSM
    tags: Dict[str, str] = field(default_factory=dict)

    def get_center(self) -> WorldCoordinate:
        """Calculate center of footprint."""
        if not self.coordinates:
            return WorldCoordinate(0, 0, 0)
        x = sum(c.x for c in self.coordinates) / len(self.coordinates)
        y = sum(c.y for c in self.coordinates) / len(self.coordinates)
        z = sum(c.z for c in self.coordinates) / len(self.coordinates)
        return WorldCoordinate(x, y, z)

    def get_area(self) -> float:
        """Calculate approximate footprint area in square meters."""
        if len(self.coordinates) < 3:
            return 0.0
        # Shoelace formula
        n = len(self.coordinates)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.coordinates[i].x * self.coordinates[j].y
            area -= self.coordinates[j].x * self.coordinates[i].y
        return abs(area) / 2.0


@dataclass
class POIMarker:
    """POI marker for geometry generation."""
    osm_id: int
    name: str
    category: POICategory
    position: WorldCoordinate
    importance: float = 0.5  # 0.0 to 1.0

    # Tags from OSM
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SceneBounds:
    """Bounding box for scene area."""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    @classmethod
    def from_center_radius(
        cls,
        center_lat: float,
        center_lon: float,
        radius_km: float
    ) -> "SceneBounds":
        """Create bounds from center point and radius in km."""
        # Approximate: 1 degree ≈ 111 km
        delta = radius_km / 111.0
        return cls(
            min_lat=center_lat - delta,
            max_lat=center_lat + delta,
            min_lon=center_lon - delta,
            max_lon=center_lon + delta,
        )

    @classmethod
    def charlotte_downtown(cls, radius_km: float = 2.0) -> "SceneBounds":
        """Create bounds for Charlotte downtown area."""
        return cls.from_center_radius(35.2271, -80.8431, radius_km)

    @classmethod
    def charlotte_metro(cls) -> "SceneBounds":
        """Create bounds for Charlotte metropolitan area."""
        return cls(
            min_lat=35.0,
            max_lat=35.4,
            min_lon=-80.9,
            max_lon=-80.5,
        )

    def contains(self, lat: float, lon: float) -> bool:
        """Check if coordinate is within bounds."""
        return (
            self.min_lat <= lat <= self.max_lat and
            self.min_lon <= lon <= self.max_lon
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "min_lat": self.min_lat,
            "max_lat": self.max_lat,
            "min_lon": self.min_lon,
            "max_lon": self.max_lon,
        }


# Road width defaults by type (in meters)
ROAD_WIDTHS: Dict[RoadType, float] = {
    RoadType.MOTORWAY: 25.0,
    RoadType.MOTORWAY_LINK: 12.0,
    RoadType.TRUNK: 20.0,
    RoadType.TRUNK_LINK: 10.0,
    RoadType.PRIMARY: 12.0,
    RoadType.PRIMARY_LINK: 8.0,
    RoadType.SECONDARY: 10.0,
    RoadType.SECONDARY_LINK: 7.0,
    RoadType.TERTIARY: 8.0,
    RoadType.TERTIARY_LINK: 6.0,
    RoadType.RESIDENTIAL: 7.0,
    RoadType.SERVICE: 4.0,
    RoadType.UNCLASSIFIED: 5.0,
    RoadType.FOOTWAY: 2.0,
    RoadType.PEDESTRIAN: 3.0,
    RoadType.CYCLEWAY: 2.0,
    RoadType.PATH: 1.0,
    RoadType.TRACK: 2.5,
    RoadType.STEPS: 1.5,
}

# Default lane counts by road type
ROAD_LANES: Dict[RoadType, int] = {
    RoadType.MOTORWAY: 4,
    RoadType.MOTORWAY_LINK: 2,
    RoadType.TRUNK: 4,
    RoadType.TRUNK_LINK: 2,
    RoadType.PRIMARY: 2,
    RoadType.PRIMARY_LINK: 1,
    RoadType.SECONDARY: 2,
    RoadType.SECONDARY_LINK: 1,
    RoadType.TERTIARY: 2,
    RoadType.TERTIARY_LINK: 1,
    RoadType.RESIDENTIAL: 2,
    RoadType.SERVICE: 1,
    RoadType.UNCLASSIFIED: 1,
    RoadType.FOOTWAY: 1,
    RoadType.PEDESTRIAN: 1,
    RoadType.CYCLEWAY: 1,
    RoadType.PATH: 1,
    RoadType.TRACK: 1,
    RoadType.STEPS: 1,
}


__all__ = [
    # Enums
    "DetailLevel",
    "RoadType",
    "BuildingType",
    "POICategory",
    # Data classes
    "SceneOrigin",
    "GeometryConfig",
    "WorldCoordinate",
    "GeoCoordinate",
    "UTMCoordinate",
    "RoadSegment",
    "BuildingFootprint",
    "POIMarker",
    "SceneBounds",
    # Constants
    "ROAD_WIDTHS",
    "ROAD_LANES",
]
