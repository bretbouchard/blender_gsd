"""
Charlotte Digital Twin - Road Classification

Classifies Charlotte roads from OSM data with Charlotte-specific
road types and specifications.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class RoadClass(Enum):
    """Charlotte road classification."""
    HIGHWAY = "highway"       # Motorways (I-77, I-85, I-277)
    ARTERIAL = "arterial"     # Primary roads
    COLLECTOR = "collector"   # Secondary/tertiary
    LOCAL = "local"           # Residential
    SERVICE = "service"       # Driveways, parking
    PEDESTRIAN = "pedestrian" # Footways, paths


@dataclass
class CharlotteRoadSpec:
    """Specifications for Charlotte road types."""
    road_class: RoadClass
    width_meters: float
    lanes: int
    has_sidewalk: bool
    has_markings: bool
    default_material: str
    lod_default: int


# Charlotte road specifications
CHARLOTTE_ROAD_SPECS: Dict[RoadClass, CharlotteRoadSpec] = {
    RoadClass.HIGHWAY: CharlotteRoadSpec(
        road_class=RoadClass.HIGHWAY,
        width_meters=25.0,
        lanes=6,
        has_sidewalk=False,
        has_markings=True,
        default_material="asphalt_highway",
        lod_default=1,
    ),
    RoadClass.ARTERIAL: CharlotteRoadSpec(
        road_class=RoadClass.ARTERIAL,
        width_meters=15.0,
        lanes=4,
        has_sidewalk=True,
        has_markings=True,
        default_material="asphalt_arterial",
        lod_default=1,
    ),
    RoadClass.COLLECTOR: CharlotteRoadSpec(
        road_class=RoadClass.COLLECTOR,
        width_meters=12.0,
        lanes=2,
        has_sidewalk=True,
        has_markings=True,
        default_material="asphalt_collector",
        lod_default=2,
    ),
    RoadClass.LOCAL: CharlotteRoadSpec(
        road_class=RoadClass.LOCAL,
        width_meters=9.0,
        lanes=2,
        has_sidewalk=True,
        has_markings=True,
        default_material="asphalt_local",
        lod_default=2,
    ),
    RoadClass.SERVICE: CharlotteRoadSpec(
        road_class=RoadClass.SERVICE,
        width_meters=5.0,
        lanes=1,
        has_sidewalk=False,
        has_markings=False,
        default_material="asphalt_service",
        lod_default=3,
    ),
    RoadClass.PEDESTRIAN: CharlotteRoadSpec(
        road_class=RoadClass.PEDESTRIAN,
        width_meters=2.0,
        lanes=0,
        has_sidewalk=False,
        has_markings=False,
        default_material="concrete_path",
        lod_default=3,
    ),
}


class RoadClassifier:
    """Classifies Charlotte roads from OSM data."""

    OSM_HIGHWAY_MAP = {
        'motorway': RoadClass.HIGHWAY,
        'motorway_link': RoadClass.HIGHWAY,
        'trunk': RoadClass.HIGHWAY,
        'trunk_link': RoadClass.HIGHWAY,
        'primary': RoadClass.ARTERIAL,
        'primary_link': RoadClass.ARTERIAL,
        'secondary': RoadClass.COLLECTOR,
        'secondary_link': RoadClass.COLLECTOR,
        'tertiary': RoadClass.COLLECTOR,
        'tertiary_link': RoadClass.COLLECTOR,
        'residential': RoadClass.LOCAL,
        'unclassified': RoadClass.LOCAL,
        'living_street': RoadClass.LOCAL,
        'service': RoadClass.SERVICE,
        'driveway': RoadClass.SERVICE,
        'parking_aisle': RoadClass.SERVICE,
        'footway': RoadClass.PEDESTRIAN,
        'pedestrian': RoadClass.PEDESTRIAN,
        'path': RoadClass.PEDESTRIAN,
        'cycleway': RoadClass.PEDESTRIAN,
        'steps': RoadClass.PEDESTRIAN,
    }

    def classify(self, osm_highway: str) -> RoadClass:
        """Classify road from OSM highway tag."""
        return self.OSM_HIGHWAY_MAP.get(osm_highway, RoadClass.LOCAL)

    def get_spec(self, road_class: RoadClass) -> CharlotteRoadSpec:
        """Get specifications for a road class."""
        return CHARLOTTE_ROAD_SPECS[road_class]

    def get_road_class_for_highway(self, highway_type: str) -> RoadClass:
        """Get RoadClass for an OSM highway type."""
        return self.OSM_HIGHWAY_MAP.get(highway_type, RoadClass.LOCAL)
