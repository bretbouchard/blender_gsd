"""
MSG-1998 Road Classification System

Classifies roads from OSM data into NYC-appropriate categories
with proper widths, lanes, and detail levels.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from enum import Enum
import re


class RoadClass(Enum):
    """NYC road classification types."""
    ARTERIAL = "arterial"       # Major avenues (7th Ave, 34th St)
    COLLECTOR = "collector"     # Mid-size streets
    LOCAL = "local"             # Residential streets
    SERVICE = "service"         # Alleys, driveways
    HIGHWAY = "highway"         # Elevated highways, expressways
    PEDESTRIAN = "pedestrian"   # Pedestrian plazas, walkways
    HERO = "hero"               # High-detail hero roads (manual override)


class LODLevel(Enum):
    """Level of detail for road geometry."""
    LOD0 = 0  # Hero detail: individual markings, cracks, patches
    LOD1 = 1  # High detail: full markings, simplified furniture
    LOD2 = 2  # Medium detail: basic markings, implied furniture
    LOD3 = 3  # Low detail: flat textured surface only


@dataclass
class NYCRoadSpec:
    """Specifications for a NYC road type."""
    road_class: RoadClass
    width_meters: float
    lanes: int
    lane_width: float
    has_sidewalk: bool
    sidewalk_width: float
    has_curb: bool
    curb_height: float
    has_markings: bool
    marking_detail: str  # "full", "basic", "minimal", "none"
    has_parking: bool
    is_oneway: bool
    default_material: str
    lod_default: LODLevel

    @property
    def total_width(self) -> float:
        """Calculate total road width including sidewalks."""
        width = self.width_meters
        if self.has_sidewalk:
            width += self.sidewalk_width * 2  # Both sides
        if self.has_curb:
            width += 0.3 * 2  # Curb width on both sides
        return width


# NYC 1998 Road Specifications
NYC_ROAD_SPECS: Dict[RoadClass, NYCRoadSpec] = {
    RoadClass.ARTERIAL: NYCRoadSpec(
        road_class=RoadClass.ARTERIAL,
        width_meters=18.0,
        lanes=4,
        lane_width=3.5,
        has_sidewalk=True,
        sidewalk_width=3.0,
        has_curb=True,
        curb_height=0.15,
        has_markings=True,
        marking_detail="full",
        has_parking=False,
        is_oneway=False,
        default_material="asphalt_arterial",
        lod_default=LODLevel.LOD1,
    ),
    RoadClass.COLLECTOR: NYCRoadSpec(
        road_class=RoadClass.COLLECTOR,
        width_meters=12.0,
        lanes=2,
        lane_width=3.5,
        has_sidewalk=True,
        sidewalk_width=2.5,
        has_curb=True,
        curb_height=0.15,
        has_markings=True,
        marking_detail="full",
        has_parking=True,
        is_oneway=False,
        default_material="asphalt_collector",
        lod_default=LODLevel.LOD1,
    ),
    RoadClass.LOCAL: NYCRoadSpec(
        road_class=RoadClass.LOCAL,
        width_meters=9.0,
        lanes=2,
        lane_width=3.0,
        has_sidewalk=True,
        sidewalk_width=2.0,
        has_curb=True,
        curb_height=0.15,
        has_markings=True,
        marking_detail="basic",
        has_parking=True,
        is_oneway=False,
        default_material="asphalt_local",
        lod_default=LODLevel.LOD2,
    ),
    RoadClass.SERVICE: NYCRoadSpec(
        road_class=RoadClass.SERVICE,
        width_meters=5.0,
        lanes=1,
        lane_width=4.0,
        has_sidewalk=False,
        sidewalk_width=0.0,
        has_curb=True,
        curb_height=0.10,
        has_markings=False,
        marking_detail="none",
        has_parking=False,
        is_oneway=True,
        default_material="asphalt_service",
        lod_default=LODLevel.LOD3,
    ),
    RoadClass.HIGHWAY: NYCRoadSpec(
        road_class=RoadClass.HIGHWAY,
        width_meters=25.0,
        lanes=6,
        lane_width=3.75,
        has_sidewalk=False,
        sidewalk_width=0.0,
        has_curb=True,
        curb_height=0.20,
        has_markings=True,
        marking_detail="full",
        has_parking=False,
        is_oneway=False,
        default_material="asphalt_highway",
        lod_default=LODLevel.LOD2,
    ),
    RoadClass.PEDESTRIAN: NYCRoadSpec(
        road_class=RoadClass.PEDESTRIAN,
        width_meters=10.0,
        lanes=0,
        lane_width=0.0,
        has_sidewalk=True,
        sidewalk_width=5.0,
        has_curb=True,
        curb_height=0.05,
        has_markings=False,
        marking_detail="none",
        has_parking=False,
        is_oneway=False,
        default_material="concrete_pedestrian",
        lod_default=LODLevel.LOD2,
    ),
    RoadClass.HERO: NYCRoadSpec(
        road_class=RoadClass.HERO,
        width_meters=18.0,
        lanes=4,
        lane_width=3.5,
        has_sidewalk=True,
        sidewalk_width=3.0,
        has_curb=True,
        curb_height=0.15,
        has_markings=True,
        marking_detail="full",
        has_parking=True,
        is_oneway=False,
        default_material="asphalt_hero",
        lod_default=LODLevel.LOD0,
    ),
}


class RoadClassifier:
    """
    Classifies roads from OSM data into NYC road classes.

    Uses multiple signals:
    - OSM highway tag (primary, secondary, etc.)
    - Road name patterns (Avenue, Street, Place, etc.)
    - Explicit width/lane tags
    - Manual overrides
    """

    # OSM highway tag to RoadClass mapping
    OSM_HIGHWAY_MAP: Dict[str, RoadClass] = {
        "motorway": RoadClass.HIGHWAY,
        "motorway_link": RoadClass.HIGHWAY,
        "trunk": RoadClass.HIGHWAY,
        "trunk_link": RoadClass.HIGHWAY,
        "primary": RoadClass.ARTERIAL,
        "primary_link": RoadClass.ARTERIAL,
        "secondary": RoadClass.COLLECTOR,
        "secondary_link": RoadClass.COLLECTOR,
        "tertiary": RoadClass.COLLECTOR,
        "tertiary_link": RoadClass.COLLECTOR,
        "residential": RoadClass.LOCAL,
        "unclassified": RoadClass.LOCAL,
        "service": RoadClass.SERVICE,
        "alley": RoadClass.SERVICE,
        "driveway": RoadClass.SERVICE,
        "pedestrian": RoadClass.PEDESTRIAN,
        "footway": RoadClass.PEDESTRIAN,
    }

    # NYC street name patterns
    ARTERIAL_PATTERNS = [
        r"\b(avenue|ave)\b",
        r"\b(boulevard|blvd)\b",
        r"\b(expressway)\b",
        r"\b(parkway)\b",
        r"^\d+(st|nd|rd|th)\s+(street|st)\b",  # Numbered streets (34th St)
    ]

    COLLECTOR_PATTERNS = [
        r"\b(street|st)\b",
        r"\b(place|pl)\b",
        r"\b(drive|dr)\b",
    ]

    LOCAL_PATTERNS = [
        r"\b(lane|ln)\b",
        r"\b(court|ct)\b",
        r"\b(way)\b",
        r"\b(road|rd)\b",
    ]

    def __init__(self, hero_roads: Optional[Set[str]] = None):
        """
        Initialize classifier.

        Args:
            hero_roads: Set of road names that should be hero-class
        """
        self.hero_roads = hero_roads or set()

    def classify(
        self,
        name: str,
        osm_highway: Optional[str] = None,
        width: Optional[float] = None,
        lanes: Optional[int] = None,
        is_oneway: bool = False,
        tags: Optional[Dict[str, str]] = None,
    ) -> RoadClass:
        """
        Classify a road based on available information.

        Args:
            name: Road name
            osm_highway: OSM highway tag value
            width: Road width in meters (from OSM)
            lanes: Number of lanes (from OSM)
            is_oneway: Whether road is one-way
            tags: Additional OSM tags

        Returns:
            RoadClass for this road
        """
        tags = tags or {}
        name_lower = name.lower()

        # Check for hero road override
        if name in self.hero_roads or any(h.lower() in name_lower for h in self.hero_roads):
            return RoadClass.HERO

        # Use OSM highway tag as primary signal
        if osm_highway and osm_highway in self.OSM_HIGHWAY_MAP:
            base_class = self.OSM_HIGHWAY_MAP[osm_highway]
        else:
            # Fall back to name pattern matching
            base_class = self._classify_by_name(name_lower)

        # Refine based on width/lanes
        if width is not None:
            if width >= 20:
                base_class = RoadClass.ARTERIAL
            elif width >= 12:
                base_class = max(base_class, RoadClass.COLLECTOR, key=lambda x: x.value)
            elif width < 6:
                base_class = RoadClass.SERVICE

        if lanes is not None:
            if lanes >= 4:
                base_class = max(base_class, RoadClass.ARTERIAL, key=lambda x: x.value)
            elif lanes == 1:
                base_class = min(base_class, RoadClass.SERVICE, key=lambda x: x.value)

        return base_class

    def _classify_by_name(self, name_lower: str) -> RoadClass:
        """Classify road based on name patterns."""
        for pattern in self.ARTERIAL_PATTERNS:
            if re.search(pattern, name_lower):
                return RoadClass.ARTERIAL

        for pattern in self.COLLECTOR_PATTERNS:
            if re.search(pattern, name_lower):
                return RoadClass.COLLECTOR

        for pattern in self.LOCAL_PATTERNS:
            if re.search(pattern, name_lower):
                return RoadClass.LOCAL

        # Default to local for unknown patterns
        return RoadClass.LOCAL

    def get_spec(self, road_class: RoadClass) -> NYCRoadSpec:
        """Get specifications for a road class."""
        return NYC_ROAD_SPECS[road_class]


@dataclass
class ClassifiedRoad:
    """A road with its classification and specifications."""
    name: str
    road_class: RoadClass
    spec: NYCRoadSpec
    osm_id: Optional[int] = None
    width_override: Optional[float] = None
    is_hero: bool = False
    lod_level: LODLevel = LODLevel.LOD2
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def effective_width(self) -> float:
        """Get effective road width (override or spec default)."""
        return self.width_override or self.spec.width_meters


def classify_road(
    name: str,
    osm_highway: Optional[str] = None,
    width: Optional[float] = None,
    lanes: Optional[int] = None,
    is_oneway: bool = False,
    hero_roads: Optional[Set[str]] = None,
) -> ClassifiedRoad:
    """
    Convenience function to classify a road.

    Args:
        name: Road name
        osm_highway: OSM highway tag
        width: Road width in meters
        lanes: Number of lanes
        is_oneway: Whether one-way
        hero_roads: Set of hero road names

    Returns:
        ClassifiedRoad with class and spec
    """
    classifier = RoadClassifier(hero_roads=hero_roads)
    road_class = classifier.classify(
        name=name,
        osm_highway=osm_highway,
        width=width,
        lanes=lanes,
        is_oneway=is_oneway,
    )
    spec = classifier.get_spec(road_class)

    return ClassifiedRoad(
        name=name,
        road_class=road_class,
        spec=spec,
        is_hero=road_class == RoadClass.HERO,
        lod_level=spec.lod_default,
    )


def get_road_spec(road_class: RoadClass) -> NYCRoadSpec:
    """Get specifications for a road class."""
    return NYC_ROAD_SPECS[road_class]


# NYC Hero Roads for MSG area (1998)
MSG_HERO_ROADS = {
    "8th Avenue",
    "7th Avenue",
    "33rd Street",
    "34th Street",
    "31st Street",
    "Penn Station Plaza",
    "West 31st Street",
    "West 33rd Street",
    "West 34th Street",
}


__all__ = [
    "RoadClass",
    "LODLevel",
    "NYCRoadSpec",
    "NYC_ROAD_SPECS",
    "RoadClassifier",
    "ClassifiedRoad",
    "classify_road",
    "get_road_spec",
    "MSG_HERO_ROADS",
]
