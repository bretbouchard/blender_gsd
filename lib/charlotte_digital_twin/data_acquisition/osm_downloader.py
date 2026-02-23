"""
OpenStreetMap Data Downloader for Charlotte NC

Downloads and caches OSM data for the Charlotte metropolitan area.
Supports multiple data sources including Geofabrik and Overpass API.

Usage:
    from lib.charlotte_digital_twin.data_acquisition import OSMDownloader

    downloader = OSMDownloader()
    data = downloader.download_charlotte_extract()
    roads = downloader.extract_roads(data)
"""

import os
import time
import json
import gzip
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from xml.etree import ElementTree

from .base_client import DataClient, RateLimitedClient


@dataclass
class OSMNode:
    """Represents an OSM node."""
    id: int
    lat: float
    lon: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OSMWay:
    """Represents an OSM way."""
    id: int
    node_ids: List[int]
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OSMRelation:
    """Represents an OSM relation."""
    id: int
    members: List[Dict[str, Any]]
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OSMData:
    """Container for parsed OSM data."""
    nodes: Dict[int, OSMNode] = field(default_factory=dict)
    ways: Dict[int, OSMWay] = field(default_factory=dict)
    relations: Dict[int, OSMRelation] = field(default_factory=dict)
    bounds: Optional[Dict[str, float]] = None
    source: str = ""
    timestamp: str = ""

    def get_way_nodes(self, way_id: int) -> List[OSMNode]:
        """Get all nodes for a way."""
        way = self.ways.get(way_id)
        if not way:
            return []
        return [self.nodes[nid] for nid in way.node_ids if nid in self.nodes]


class OSMDownloader(DataClient):
    """
    Downloads OpenStreetMap data for Charlotte NC.

    Features:
    - Downloads from Geofabrik (pre-processed extracts)
    - Parses OSM XML and PBF formats
    - Caches downloaded data
    - Extracts specific feature types (roads, buildings, POIs)
    """

    # Charlotte metropolitan area bounds
    CHARLOTTE_BOUNDS = {
        "north": 35.4,
        "south": 35.0,
        "east": -80.5,
        "west": -80.9,
    }

    # Geofabrik North Carolina extract URL
    GEOFABRIK_NC_URL = "https://download.geofabrik.de/north-america/us/north-carolina-latest.osm.pbf"

    # Overpass API endpoints (for smaller queries)
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    RATE_LIMIT = 2.0  # Be respectful to OSM servers
    MAX_RETRIES = 3
    CACHE_TTL_DAYS = 30  # OSM data changes slowly

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        use_geofabrik: bool = True,
        **kwargs
    ):
        """
        Initialize the OSM downloader.

        Args:
            cache_dir: Directory for caching downloads
            use_geofabrik: Use Geofabrik extracts (recommended)
        """
        super().__init__(cache_dir=cache_dir, **kwargs)
        self.use_geofabrik = use_geofabrik

        # Try to import requests
        try:
            import requests
            self._requests = requests
        except ImportError:
            self._requests = None

    def download_charlotte_extract(
        self,
        bounds: Optional[Dict[str, float]] = None,
        force_refresh: bool = False,
    ) -> OSMData:
        """
        Download OSM data for Charlotte area.

        Args:
            bounds: Custom bounds (default: Charlotte metro)
            force_refresh: Force re-download

        Returns:
            Parsed OSMData object
        """
        if self._requests is None:
            raise ImportError("requests library required for OSM downloads")

        bounds = bounds or self.CHARLOTTE_BOUNDS
        cache_key = self._get_cache_key("charlotte_osm", bounds)

        # Check cache
        if not force_refresh:
            cached = self._load_from_cache(cache_key)
            if cached:
                return self._dict_to_osm_data(cached)

        # Download via Overpass API (smaller area)
        osm_data = self._download_via_overpass(bounds)

        # Cache result
        self._save_to_cache(cache_key, self._osm_data_to_dict(osm_data))

        return osm_data

    def _download_via_overpass(self, bounds: Dict[str, float]) -> OSMData:
        """Download data via Overpass API."""
        query = f"""
        [out:xml][timeout:300];
        (
            node({bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']});
            way({bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']});
            relation({bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']});
        );
        (._;>;);
        out meta;
        """

        # Try each Overpass endpoint
        for endpoint in self.OVERPASS_ENDPOINTS:
            try:
                self._rate_limit_wait()
                response = self._requests.post(
                    endpoint,
                    data={"data": query},
                    timeout=300,
                )
                response.raise_for_status()

                # Parse XML
                return self._parse_osm_xml(response.content)

            except Exception as e:
                print(f"Overpass endpoint {endpoint} failed: {e}")
                continue

        raise RuntimeError("All Overpass endpoints failed")

    def _parse_osm_xml(self, xml_content: bytes) -> OSMData:
        """Parse OSM XML content."""
        osm_data = OSMData()

        try:
            root = ElementTree.fromstring(xml_content)
        except ElementTree.ParseError:
            raise ValueError("Invalid OSM XML")

        # Parse bounds
        bounds_elem = root.find("bounds")
        if bounds_elem is not None:
            osm_data.bounds = {
                "minlat": float(bounds_elem.get("minlat", 0)),
                "minlon": float(bounds_elem.get("minlon", 0)),
                "maxlat": float(bounds_elem.get("maxlat", 0)),
                "maxlon": float(bounds_elem.get("maxlon", 0)),
            }

        # Parse nodes
        for node_elem in root.findall("node"):
            node = OSMNode(
                id=int(node_elem.get("id")),
                lat=float(node_elem.get("lat")),
                lon=float(node_elem.get("lon")),
            )
            # Parse tags
            for tag in node_elem.findall("tag"):
                node.tags[tag.get("k")] = tag.get("v")
            osm_data.nodes[node.id] = node

        # Parse ways
        for way_elem in root.findall("way"):
            way = OSMWay(
                id=int(way_elem.get("id")),
                node_ids=[int(nd.get("ref")) for nd in way_elem.findall("nd")],
            )
            # Parse tags
            for tag in way_elem.findall("tag"):
                way.tags[tag.get("k")] = tag.get("v")
            osm_data.ways[way.id] = way

        # Parse relations
        for rel_elem in root.findall("relation"):
            relation = OSMRelation(
                id=int(rel_elem.get("id")),
                members=[
                    {
                        "type": m.get("type"),
                        "ref": int(m.get("ref")),
                        "role": m.get("role", ""),
                    }
                    for m in rel_elem.findall("member")
                ],
            )
            # Parse tags
            for tag in rel_elem.findall("tag"):
                relation.tags[tag.get("k")] = tag.get("v")
            osm_data.relations[relation.id] = relation

        osm_data.source = "overpass_api"
        osm_data.timestamp = datetime.now().isoformat()

        return osm_data

    def extract_roads(
        self,
        osm_data: OSMData,
        highway_types: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract road network from OSM data.

        Args:
            osm_data: Parsed OSM data
            highway_types: Filter to specific highway types

        Returns:
            List of road segments with geometry
        """
        if highway_types is None:
            highway_types = {
                "motorway", "motorway_link",
                "trunk", "trunk_link",
                "primary", "primary_link",
                "secondary", "secondary_link",
                "tertiary", "tertiary_link",
                "residential", "service",
            }

        roads = []

        for way_id, way in osm_data.ways.items():
            highway = way.tags.get("highway")
            if highway not in highway_types:
                continue

            # Get coordinates
            coords = []
            for node_id in way.node_ids:
                node = osm_data.nodes.get(node_id)
                if node:
                    coords.append({"lat": node.lat, "lon": node.lon})

            if len(coords) < 2:
                continue

            road = {
                "osm_id": way_id,
                "highway_type": highway,
                "name": way.tags.get("name", ""),
                "ref": way.tags.get("ref", ""),  # Route number (I-77, etc.)
                "lanes": way.tags.get("lanes"),
                "surface": way.tags.get("surface"),
                "maxspeed": way.tags.get("maxspeed"),
                "oneway": way.tags.get("oneway") == "yes",
                "bridge": way.tags.get("bridge") == "yes",
                "tunnel": way.tags.get("tunnel") == "yes",
                "layer": way.tags.get("layer", "0"),
                "coordinates": coords,
                "tags": way.tags,
            }
            roads.append(road)

        return roads

    def extract_buildings(
        self,
        osm_data: OSMData,
        min_height: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract buildings from OSM data.

        Args:
            osm_data: Parsed OSM data
            min_height: Filter to buildings above this height (meters)

        Returns:
            List of buildings with geometry
        """
        buildings = []

        for way_id, way in osm_data.ways.items():
            if "building" not in way.tags:
                continue

            # Get footprint coordinates
            coords = []
            for node_id in way.node_ids:
                node = osm_data.nodes.get(node_id)
                if node:
                    coords.append({"lat": node.lat, "lon": node.lon})

            if len(coords) < 3:
                continue

            # Parse height
            height = None
            height_str = way.tags.get("height", way.tags.get("building:height"))
            if height_str:
                try:
                    # Remove units and parse
                    height = float(height_str.rstrip("m").strip())
                except ValueError:
                    pass

            # Apply height filter
            if min_height is not None and (height is None or height < min_height):
                continue

            building = {
                "osm_id": way_id,
                "name": way.tags.get("name", ""),
                "building_type": way.tags.get("building", "yes"),
                "height": height,
                "levels": way.tags.get("building:levels"),
                "footprint": coords,
                "tags": way.tags,
            }
            buildings.append(building)

        return buildings

    def extract_water_features(
        self,
        osm_data: OSMData,
    ) -> List[Dict[str, Any]]:
        """
        Extract water features (rivers, lakes, etc.) from OSM data.

        Args:
            osm_data: Parsed OSM data

        Returns:
            List of water features
        """
        water_types = {"water", "river", "stream", "canal", "lake", "reservoir"}
        features = []

        for way_id, way in osm_data.ways.items():
            water = way.tags.get("water") or way.tags.get("waterway")
            natural = way.tags.get("natural")

            if water not in water_types and natural != "water":
                continue

            coords = []
            for node_id in way.node_ids:
                node = osm_data.nodes.get(node_id)
                if node:
                    coords.append({"lat": node.lat, "lon": node.lon})

            if len(coords) < 2:
                continue

            feature = {
                "osm_id": way_id,
                "type": water or natural,
                "name": way.tags.get("name", ""),
                "coordinates": coords,
                "tags": way.tags,
            }
            features.append(feature)

        return features

    def get_charlotte_highways(self, osm_data: OSMData) -> Dict[str, List[Dict]]:
        """
        Extract Charlotte's major highways (I-77, I-85, I-277, I-485).

        Args:
            osm_data: Parsed OSM data

        Returns:
            Dictionary mapping highway names to segments
        """
        roads = self.extract_roads(osm_data, {"motorway", "motorway_link", "trunk"})

        highways = {
            "I-77": [],
            "I-85": [],
            "I-277": [],
            "I-485": [],
            "US-74": [],
            "NC-49": [],
            "other": [],
        }

        for road in roads:
            ref = road.get("ref", "")
            name = road.get("name", "")

            assigned = False
            for hw_name in ["I-77", "I-85", "I-277", "I-485"]:
                if hw_name in ref or hw_name in name:
                    highways[hw_name].append(road)
                    assigned = True
                    break

            if not assigned:
                if "US 74" in ref or "US 74" in name:
                    highways["US-74"].append(road)
                elif "NC 49" in ref or "NC 49" in name:
                    highways["NC-49"].append(road)
                elif road["highway_type"] == "motorway":
                    highways["other"].append(road)

        return highways

    def to_json(self, data: Any, filepath: str) -> None:
        """Save data to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _osm_data_to_dict(self, osm_data: OSMData) -> Dict[str, Any]:
        """Convert OSMData to dictionary for caching."""
        return {
            "nodes": {
                k: {"id": v.id, "lat": v.lat, "lon": v.lon, "tags": v.tags}
                for k, v in osm_data.nodes.items()
            },
            "ways": {
                k: {"id": v.id, "node_ids": v.node_ids, "tags": v.tags}
                for k, v in osm_data.ways.items()
            },
            "relations": {
                k: {"id": v.id, "members": v.members, "tags": v.tags}
                for k, v in osm_data.relations.items()
            },
            "bounds": osm_data.bounds,
            "source": osm_data.source,
            "timestamp": osm_data.timestamp,
        }

    def _dict_to_osm_data(self, data: Dict[str, Any]) -> OSMData:
        """Convert dictionary back to OSMData."""
        osm_data = OSMData()

        osm_data.nodes = {
            int(k): OSMNode(
                id=v["id"],
                lat=v["lat"],
                lon=v["lon"],
                tags=v.get("tags", {}),
            )
            for k, v in data.get("nodes", {}).items()
        }

        osm_data.ways = {
            int(k): OSMWay(
                id=v["id"],
                node_ids=v["node_ids"],
                tags=v.get("tags", {}),
            )
            for k, v in data.get("ways", {}).items()
        }

        osm_data.relations = {
            int(k): OSMRelation(
                id=v["id"],
                members=v["members"],
                tags=v.get("tags", {}),
            )
            for k, v in data.get("relations", {}).items()
        }

        osm_data.bounds = data.get("bounds")
        osm_data.source = data.get("source", "")
        osm_data.timestamp = data.get("timestamp", "")

        return osm_data

    def fetch(self, *args, **kwargs) -> OSMData:
        """Implementation of abstract fetch method."""
        return self.download_charlotte_extract(*args, **kwargs)


__all__ = [
    "OSMNode",
    "OSMWay",
    "OSMRelation",
    "OSMData",
    "OSMDownloader",
]
