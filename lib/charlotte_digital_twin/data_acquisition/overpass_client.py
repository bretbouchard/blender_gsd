"""
Overpass API Client for Charlotte POI Extraction

Provides specialized queries for extracting Points of Interest
from OpenStreetMap via the Overpass API.

Usage:
    from lib.charlotte_digital_twin.data_acquisition import OverpassClient

    client = OverpassClient()
    gas_stations = client.get_gas_stations()
    restaurants = client.get_restaurants(cuisine="mexican")
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from .base_client import DataClient


@dataclass
class POI:
    """Represents a Point of Interest."""
    osm_id: int
    osm_type: str  # node, way, relation
    name: str
    lat: float
    lon: float
    category: str
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "osm_id": self.osm_id,
            "osm_type": self.osm_type,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "category": self.category,
            "tags": self.tags,
        }


class OverpassClient(DataClient):
    """
    Client for querying Overpass API for Charlotte POIs.

    Features:
    - Rate-limited queries
    - Response caching
    - Retry logic with fallback endpoints
    - Specialized POI queries
    """

    # Charlotte bounding box
    CHARLOTTE_BBOX = (35.0, -80.9, 35.4, -80.5)  # south, west, north, east

    # Overpass API endpoints
    ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    RATE_LIMIT = 2.0  # Seconds between requests
    MAX_RETRIES = 3
    CACHE_TTL_DAYS = 14

    def __init__(
        self,
        bbox: Optional[tuple] = None,
        cache_dir: Optional[Path] = None,
        **kwargs
    ):
        """
        Initialize Overpass client.

        Args:
            bbox: Bounding box (south, west, north, east)
            cache_dir: Cache directory
        """
        super().__init__(cache_dir=cache_dir, **kwargs)
        self.bbox = bbox or self.CHARLOTTE_BBOX

        # Try to import requests
        try:
            import requests
            self._requests = requests
        except ImportError:
            self._requests = None

    def _build_bbox_string(self) -> str:
        """Build Overpass bbox string."""
        south, west, north, east = self.bbox
        return f"{south},{west},{north},{east}"

    def _execute_query(
        self,
        query: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute Overpass query with retry logic.

        Args:
            query: Overpass QL query
            use_cache: Use cached results

        Returns:
            List of elements from query
        """
        if self._requests is None:
            raise ImportError("requests library required for Overpass API")

        cache_key = self._get_cache_key("overpass", {"query": query})

        # Check cache
        if use_cache:
            cached = self._load_from_cache(cache_key)
            if cached:
                return cached

        # Try each endpoint
        last_error = None
        for endpoint in self.ENDPOINTS:
            try:
                self._rate_limit_wait()
                response = self._requests.post(
                    endpoint,
                    data={"data": query},
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()

                elements = data.get("elements", [])

                # Cache results
                if use_cache:
                    self._save_to_cache(cache_key, elements)

                return elements

            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All Overpass endpoints failed: {last_error}")

    def _parse_poi(self, element: Dict[str, Any], category: str) -> Optional[POI]:
        """Parse POI from Overpass element."""
        tags = element.get("tags", {})

        # Get coordinates
        if element["type"] == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        else:
            # Way or relation - use center if available
            center = element.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")

        if lat is None or lon is None:
            return None

        return POI(
            osm_id=element["id"],
            osm_type=element["type"],
            name=tags.get("name", ""),
            lat=lat,
            lon=lon,
            category=category,
            tags=tags,
        )

    def get_gas_stations(self) -> List[POI]:
        """
        Get all gas stations in Charlotte area.

        Returns:
            List of gas station POIs
        """
        bbox = self._build_bbox_string()
        query = f"""
        [out:json][timeout:60];
        (
            node["amenity"="fuel"]({bbox});
            way["amenity"="fuel"]({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            poi = self._parse_poi(elem, "gas_station")
            if poi:
                pois.append(poi)

        return pois

    def get_restaurants(
        self,
        cuisine: Optional[str] = None,
        min_rating: Optional[float] = None,
    ) -> List[POI]:
        """
        Get restaurants in Charlotte area.

        Args:
            cuisine: Filter by cuisine type
            min_rating: Minimum rating (if available)

        Returns:
            List of restaurant POIs
        """
        bbox = self._build_bbox_string()

        if cuisine:
            filter_str = f'["amenity"="restaurant"]["cuisine"="{cuisine}"]'
        else:
            filter_str = '["amenity"="restaurant"]'

        query = f"""
        [out:json][timeout:60];
        (
            node{filter_str}({bbox});
            way{filter_str}({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            poi = self._parse_poi(elem, "restaurant")
            if poi:
                # Apply rating filter if specified
                if min_rating is not None:
                    rating = poi.tags.get("rating")
                    if rating:
                        try:
                            if float(rating) < min_rating:
                                continue
                        except ValueError:
                            pass
                pois.append(poi)

        return pois

    def get_fast_food(self, brand: Optional[str] = None) -> List[POI]:
        """
        Get fast food establishments.

        Args:
            brand: Filter by brand (e.g., "McDonald's")

        Returns:
            List of fast food POIs
        """
        bbox = self._build_bbox_string()

        if brand:
            filter_str = f'["amenity"="fast_food"]["brand"="{brand}"]'
        else:
            filter_str = '["amenity"="fast_food"]'

        query = f"""
        [out:json][timeout:60];
        (
            node{filter_str}({bbox});
            way{filter_str}({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            poi = self._parse_poi(elem, "fast_food")
            if poi:
                pois.append(poi)

        return pois

    def get_hotels(self, min_stars: Optional[int] = None) -> List[POI]:
        """
        Get hotels in Charlotte area.

        Args:
            min_stars: Minimum star rating

        Returns:
            List of hotel POIs
        """
        bbox = self._build_bbox_string()
        filter_str = '["tourism"="hotel"]'

        query = f"""
        [out:json][timeout:60];
        (
            node{filter_str}({bbox});
            way{filter_str}({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            poi = self._parse_poi(elem, "hotel")
            if poi:
                if min_stars is not None:
                    stars = poi.tags.get("stars")
                    if stars:
                        try:
                            if int(stars) < min_stars:
                                continue
                        except ValueError:
                            pass
                pois.append(poi)

        return pois

    def get_hospitals(self) -> List[POI]:
        """Get hospitals and medical facilities."""
        bbox = self._build_bbox_string()

        query = f"""
        [out:json][timeout:60];
        (
            node["amenity"~"^(hospital|clinic|doctors)$"]({bbox});
            way["amenity"~"^(hospital|clinic|doctors)$"]({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            amenity = elem.get("tags", {}).get("amenity", "medical")
            poi = self._parse_poi(elem, amenity)
            if poi:
                pois.append(poi)

        return pois

    def get_schools(self) -> List[POI]:
        """Get schools and educational institutions."""
        bbox = self._build_bbox_string()

        query = f"""
        [out:json][timeout:60];
        (
            node["amenity"="school"]({bbox});
            way["amenity"="school"]({bbox});
            node["amenity"="university"]({bbox});
            way["amenity"="university"]({bbox});
            node["amenity"="college"]({bbox});
            way["amenity"="college"]({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            amenity = elem.get("tags", {}).get("amenity", "school")
            poi = self._parse_poi(elem, amenity)
            if poi:
                pois.append(poi)

        return pois

    def get_shopping(
        self,
        shop_type: Optional[str] = None,
    ) -> List[POI]:
        """
        Get shopping locations.

        Args:
            shop_type: Filter by shop type (supermarket, mall, etc.)

        Returns:
            List of shopping POIs
        """
        bbox = self._build_bbox_string()

        if shop_type:
            filter_str = f'["shop"="{shop_type}"]'
        else:
            filter_str = '["shop"]'

        query = f"""
        [out:json][timeout:90];
        (
            node{filter_str}({bbox});
            way{filter_str}({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            shop = elem.get("tags", {}).get("shop", "shop")
            poi = self._parse_poi(elem, f"shop_{shop}")
            if poi:
                pois.append(poi)

        return pois

    def get_attractions(self) -> List[POI]:
        """Get tourist attractions and points of interest."""
        bbox = self._build_bbox_string()

        query = f"""
        [out:json][timeout:60];
        (
            node["tourism"~"^(attraction|museum|artwork|gallery)$"]({bbox});
            way["tourism"~"^(attraction|museum|artwork|gallery)$"]({bbox});
            node["historic"]({bbox});
            way["historic"]({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            tags = elem.get("tags", {})
            tourism = tags.get("tourism")
            historic = tags.get("historic")
            category = tourism or historic or "attraction"
            poi = self._parse_poi(elem, category)
            if poi:
                pois.append(poi)

        return pois

    def get_parks(self) -> List[POI]:
        """Get parks and recreational areas."""
        bbox = self._build_bbox_string()

        query = f"""
        [out:json][timeout:60];
        (
            node["leisure"="park"]({bbox});
            way["leisure"="park"]({bbox});
            node["leisure"="garden"]({bbox});
            way["leisure"="garden"]({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            leisure = elem.get("tags", {}).get("leisure", "park")
            poi = self._parse_poi(elem, leisure)
            if poi:
                pois.append(poi)

        return pois

    def get_sports_facilities(self) -> List[POI]:
        """Get sports facilities (stadiums, arenas, etc.)."""
        bbox = self._build_bbox_string()

        query = f"""
        [out:json][timeout:60];
        (
            node["leisure"="stadium"]({bbox});
            way["leisure"="stadium"]({bbox});
            node["leisure"="sports_centre"]({bbox});
            way["leisure"="sports_centre"]({bbox});
        );
        out center tags;
        """

        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            leisure = elem.get("tags", {}).get("leisure", "sports")
            poi = self._parse_poi(elem, leisure)
            if poi:
                pois.append(poi)

        return pois

    def get_all_pois(self, categories: Optional[List[str]] = None) -> Dict[str, List[POI]]:
        """
        Get all POIs by category.

        Args:
            categories: Specific categories to fetch (default: all)

        Returns:
            Dictionary mapping category to POI list
        """
        categories = categories or [
            "gas_stations",
            "restaurants",
            "hotels",
            "hospitals",
            "schools",
            "shopping",
            "attractions",
            "parks",
            "sports",
        ]

        results = {}

        if "gas_stations" in categories:
            results["gas_stations"] = self.get_gas_stations()

        if "restaurants" in categories:
            results["restaurants"] = self.get_restaurants()

        if "hotels" in categories:
            results["hotels"] = self.get_hotels()

        if "hospitals" in categories:
            results["hospitals"] = self.get_hospitals()

        if "schools" in categories:
            results["schools"] = self.get_schools()

        if "shopping" in categories:
            results["shopping"] = self.get_shopping()

        if "attractions" in categories:
            results["attractions"] = self.get_attractions()

        if "parks" in categories:
            results["parks"] = self.get_parks()

        if "sports" in categories:
            results["sports"] = self.get_sports_facilities()

        return results

    def custom_query(
        self,
        query: str,
        category: str = "custom",
    ) -> List[POI]:
        """
        Execute a custom Overpass query.

        Args:
            query: Overpass QL query
            category: Category label for results

        Returns:
            List of POIs
        """
        elements = self._execute_query(query)
        pois = []

        for elem in elements:
            poi = self._parse_poi(elem, category)
            if poi:
                pois.append(poi)

        return pois

    def fetch(self, *args, **kwargs) -> List[POI]:
        """Implementation of abstract fetch method."""
        return self.get_all_pois(*args, **kwargs)


__all__ = [
    "POI",
    "OverpassClient",
]
