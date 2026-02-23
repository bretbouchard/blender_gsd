"""
POI Extractor for Charlotte NC

Specialized POI extraction and categorization for
Charlotte Digital Twin project.

Usage:
    from lib.charlotte_digital_twin.data_acquisition import POIExtractor

    extractor = POIExtractor()
    all_pois = extractor.extract_all()
    by_category = extractor.group_by_category(all_pois)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from .overpass_client import OverpassClient, POI


@dataclass
class CategorizedPOI:
    """POI with additional categorization."""
    poi: POI
    primary_category: str
    sub_category: str
    importance: float  # 0.0 to 1.0
    tags_normalized: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "osm_id": self.poi.osm_id,
            "osm_type": self.poi.osm_type,
            "name": self.poi.name,
            "lat": self.poi.lat,
            "lon": self.poi.lon,
            "primary_category": self.primary_category,
            "sub_category": self.sub_category,
            "importance": self.importance,
            "tags": self.poi.tags,
            "tags_normalized": self.tags_normalized,
        }


# Category mappings for Charlotte-specific POIs
CHARLOTTE_POI_CATEGORIES = {
    # Transportation
    "transportation": {
        "gas_station": {"amenity": "fuel"},
        "parking": {"amenity": "parking"},
        "bus_stop": {"highway": "bus_stop"},
        "train_station": {"public_transport": "station"},
        "airport": {"aeroway": "aerodrome"},
    },

    # Food & Dining
    "food": {
        "restaurant": {"amenity": "restaurant"},
        "fast_food": {"amenity": "fast_food"},
        "cafe": {"amenity": "cafe"},
        "bar": {"amenity": "bar"},
        "pub": {"amenity": "pub"},
    },

    # Lodging
    "lodging": {
        "hotel": {"tourism": "hotel"},
        "motel": {"tourism": "motel"},
        "hostel": {"tourism": "hostel"},
    },

    # Healthcare
    "healthcare": {
        "hospital": {"amenity": "hospital"},
        "clinic": {"amenity": "clinic"},
        "pharmacy": {"amenity": "pharmacy"},
        "doctors": {"amenity": "doctors"},
    },

    # Education
    "education": {
        "school": {"amenity": "school"},
        "university": {"amenity": "university"},
        "college": {"amenity": "college"},
        "library": {"amenity": "library"},
    },

    # Shopping
    "shopping": {
        "supermarket": {"shop": "supermarket"},
        "mall": {"shop": "mall"},
        "convenience": {"shop": "convenience"},
        "clothes": {"shop": "clothes"},
        "hardware": {"shop": "doityourself"},
    },

    # Recreation
    "recreation": {
        "park": {"leisure": "park"},
        "stadium": {"leisure": "stadium"},
        "sports_centre": {"leisure": "sports_centre"},
        "playground": {"leisure": "playground"},
        "golf_course": {"leisure": "golf_course"},
    },

    # Tourism
    "tourism": {
        "attraction": {"tourism": "attraction"},
        "museum": {"tourism": "museum"},
        "artwork": {"tourism": "artwork"},
        "viewpoint": {"tourism": "viewpoint"},
    },

    # Services
    "services": {
        "bank": {"amenity": "bank"},
        "atm": {"amenity": "atm"},
        "post_office": {"amenity": "post_office"},
        "police": {"amenity": "police"},
        "fire_station": {"amenity": "fire_station"},
    },

    # Entertainment
    "entertainment": {
        "cinema": {"amenity": "cinema"},
        "theatre": {"amenity": "theatre"},
        "nightclub": {"amenity": "nightclub"},
    },
}

# Charlotte-specific landmarks and their importance
CHARLOTTE_LANDMARKS = {
    # Sports venues
    "Bank of America Stadium": 1.0,
    "Spectrum Center": 0.95,
    "Truist Field": 0.85,
    "BB&T Ballpark": 0.75,

    # Major buildings
    "Bank of America Corporate Center": 0.95,
    "Duke Energy Center": 0.9,
    "Wells Fargo Capital Center": 0.85,
    "The Vue": 0.8,
    "One Wells Fargo Center": 0.8,

    # Museums & Attractions
    "NASCAR Hall of Fame": 0.9,
    "Discovery Place": 0.85,
    "Mint Museum": 0.8,
    "Bechtler Museum of Modern Art": 0.8,
    "Charlotte Museum of History": 0.75,

    # Parks
    "Freedom Park": 0.85,
    "Romare Bearden Park": 0.8,
    "Marshall Park": 0.7,

    # Educational
    "University of North Carolina at Charlotte": 0.9,
    "Davidson College": 0.8,
    "Johnson & Wales University": 0.75,
}

# Brand importance multipliers
BRAND_IMPORTANCE = {
    # Gas stations
    "Shell": 0.7,
    "Exxon": 0.7,
    "BP": 0.7,
    "Chevron": 0.7,
    "QuikTrip": 0.75,

    # Fast food
    "McDonald's": 0.7,
    "Chick-fil-A": 0.75,
    "Bojangles'": 0.8,  # Charlotte-based!
    "Cook Out": 0.75,  # NC-based
    "Wendy's": 0.65,

    # Coffee
    "Starbucks": 0.75,
    "Dunkin'": 0.65,

    # Hotels
    "Hilton": 0.8,
    "Marriott": 0.8,
    "Hyatt": 0.8,
    "Westin": 0.8,
    "Omni": 0.85,  # Has significant Charlotte presence

    # Banks
    "Bank of America": 0.9,  # HQ in Charlotte
    "Wells Fargo": 0.85,  # Major presence
    "Truist": 0.8,  # Formed in Charlotte
}


class POIExtractor:
    """
    Extracts and categorizes POIs for Charlotte Digital Twin.

    Features:
    - Fetches from Overpass API
    - Categorizes into standard groups
    - Assigns importance scores
    - Identifies Charlotte landmarks
    - Groups by category
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        bbox: Optional[tuple] = None,
    ):
        """
        Initialize POI extractor.

        Args:
            cache_dir: Cache directory
            bbox: Bounding box (default: Charlotte)
        """
        self.client = OverpassClient(
            cache_dir=cache_dir,
            bbox=bbox,
        )
        self._all_pois: List[CategorizedPOI] = []

    def extract_all(self, force_refresh: bool = False) -> List[CategorizedPOI]:
        """
        Extract all POIs and categorize them.

        Args:
            force_refresh: Force re-fetch

        Returns:
            List of categorized POIs
        """
        if self._all_pois and not force_refresh:
            return self._all_pois

        # Fetch all POI types
        raw_pois = self.client.get_all_pois()

        # Process each category
        self._all_pois = []

        for category_name, pois in raw_pois.items():
            for poi in pois:
                cat_poi = self._categorize_poi(poi, category_name)
                if cat_poi:
                    self._all_pois.append(cat_poi)

        return self._all_pois

    def _categorize_poi(self, poi: POI, api_category: str) -> Optional[CategorizedPOI]:
        """Categorize a POI and assign importance."""
        # Find primary category
        primary_category = self._find_primary_category(poi)

        # Find sub-category
        sub_category = self._find_sub_category(poi, primary_category)

        # Calculate importance
        importance = self._calculate_importance(poi, sub_category)

        # Normalize tags
        tags_normalized = self._normalize_tags(poi.tags)

        return CategorizedPOI(
            poi=poi,
            primary_category=primary_category,
            sub_category=sub_category,
            importance=importance,
            tags_normalized=tags_normalized,
        )

    def _find_primary_category(self, poi: POI) -> str:
        """Find the primary category for a POI."""
        tags = poi.tags

        for category_name, subcats in CHARLOTTE_POI_CATEGORIES.items():
            for subcat_name, required_tags in subcats.items():
                match = True
                for key, value in required_tags.items():
                    if key not in tags:
                        match = False
                        break
                    if isinstance(value, str) and tags[key] != value:
                        match = False
                        break
                if match:
                    return category_name

        return "other"

    def _find_sub_category(self, poi: POI, primary_category: str) -> str:
        """Find the sub-category for a POI."""
        tags = poi.tags

        if primary_category in CHARLOTTE_POI_CATEGORIES:
            subcats = CHARLOTTE_POI_CATEGORIES[primary_category]
            for subcat_name, required_tags in subcats.items():
                match = True
                for key, value in required_tags.items():
                    if key not in tags:
                        match = False
                        break
                    if isinstance(value, str) and tags[key] != value:
                        match = False
                        break
                if match:
                    return subcat_name

        # Fallback to first tag value
        if tags:
            return list(tags.values())[0]

        return "unknown"

    def _calculate_importance(self, poi: POI, sub_category: str) -> float:
        """Calculate importance score for a POI."""
        base_importance = 0.5

        # Check if it's a known landmark
        if poi.name in CHARLOTTE_LANDMARKS:
            return CHARLOTTE_LANDMARKS[poi.name]

        # Check brand importance
        brand = poi.tags.get("brand", poi.tags.get("operator", ""))
        if brand in BRAND_IMPORTANCE:
            base_importance = BRAND_IMPORTANCE[brand]

        # Adjust by category
        category_multipliers = {
            "hospital": 0.9,
            "university": 0.85,
            "stadium": 0.9,
            "hotel": 0.7,
            "gas_station": 0.5,
            "fast_food": 0.5,
            "restaurant": 0.6,
            "shop": 0.5,
            "park": 0.7,
            "museum": 0.8,
        }

        multiplier = category_multipliers.get(sub_category, 0.6)
        importance = base_importance * multiplier + 0.2

        # Boost named locations
        if poi.name:
            importance += 0.1

        # Cap at 1.0
        return min(1.0, importance)

    def _normalize_tags(self, tags: Dict[str, str]) -> Dict[str, str]:
        """Normalize tag keys for consistency."""
        normalized = {}

        # Key mappings
        key_map = {
            "name": "name",
            "addr:street": "street",
            "addr:city": "city",
            "addr:state": "state",
            "addr:postcode": "postcode",
            "phone": "phone",
            "website": "website",
            "opening_hours": "hours",
            "brand": "brand",
            "cuisine": "cuisine",
            "stars": "stars",
            "rooms": "rooms",
        }

        for orig_key, new_key in key_map.items():
            if orig_key in tags:
                normalized[new_key] = tags[orig_key]

        return normalized

    def get_by_category(self, category: str) -> List[CategorizedPOI]:
        """Get POIs by primary category."""
        if not self._all_pois:
            self.extract_all()
        return [p for p in self._all_pois if p.primary_category == category]

    def get_by_subcategory(self, subcategory: str) -> List[CategorizedPOI]:
        """Get POIs by sub-category."""
        if not self._all_pois:
            self.extract_all()
        return [p for p in self._all_pois if p.sub_category == subcategory]

    def get_important_pois(self, min_importance: float = 0.8) -> List[CategorizedPOI]:
        """Get POIs above importance threshold."""
        if not self._all_pois:
            self.extract_all()
        return [p for p in self._all_pois if p.importance >= min_importance]

    def get_gas_stations(self) -> List[CategorizedPOI]:
        """Get all gas stations."""
        return self.get_by_subcategory("gas_station")

    def get_restaurants(self) -> List[CategorizedPOI]:
        """Get all restaurants."""
        return self.get_by_subcategory("restaurant")

    def get_hotels(self) -> List[CategorizedPOI]:
        """Get all hotels."""
        return self.get_by_subcategory("hotel")

    def get_landmarks(self) -> List[CategorizedPOI]:
        """Get notable landmarks."""
        return self.get_important_pois(min_importance=0.85)

    def group_by_category(self, pois: Optional[List[CategorizedPOI]] = None) -> Dict[str, List[CategorizedPOI]]:
        """Group POIs by primary category."""
        if pois is None:
            if not self._all_pois:
                self.extract_all()
            pois = self._all_pois

        groups = defaultdict(list)
        for poi in pois:
            groups[poi.primary_category].append(poi)

        return dict(groups)

    def to_geojson(self, pois: Optional[List[CategorizedPOI]] = None) -> Dict[str, Any]:
        """Convert POIs to GeoJSON format."""
        if pois is None:
            if not self._all_pois:
                self.extract_all()
            pois = self._all_pois

        features = []
        for cat_poi in pois:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [cat_poi.poi.lon, cat_poi.poi.lat],
                },
                "properties": {
                    "osm_id": cat_poi.poi.osm_id,
                    "name": cat_poi.poi.name,
                    "category": cat_poi.primary_category,
                    "sub_category": cat_poi.sub_category,
                    "importance": cat_poi.importance,
                    "tags": cat_poi.poi.tags,
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def save_to_json(self, filepath: str, pois: Optional[List[CategorizedPOI]] = None) -> None:
        """Save POIs to JSON file."""
        if pois is None:
            if not self._all_pois:
                self.extract_all()
            pois = self._all_pois

        data = [p.to_dict() for p in pois]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def save_geojson(self, filepath: str, pois: Optional[List[CategorizedPOI]] = None) -> None:
        """Save POIs to GeoJSON file."""
        geojson = self.to_geojson(pois)
        with open(filepath, 'w') as f:
            json.dump(geojson, f, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about extracted POIs."""
        if not self._all_pois:
            self.extract_all()

        stats = {
            "total": len(self._all_pois),
            "by_category": {},
            "by_subcategory": {},
            "with_names": 0,
            "high_importance": 0,  # >= 0.8
        }

        for poi in self._all_pois:
            # Category counts
            if poi.primary_category not in stats["by_category"]:
                stats["by_category"][poi.primary_category] = 0
            stats["by_category"][poi.primary_category] += 1

            # Subcategory counts
            if poi.sub_category not in stats["by_subcategory"]:
                stats["by_subcategory"][poi.sub_category] = 0
            stats["by_subcategory"][poi.sub_category] += 1

            # Named POIs
            if poi.poi.name:
                stats["with_names"] += 1

            # High importance
            if poi.importance >= 0.8:
                stats["high_importance"] += 1

        return stats


__all__ = [
    "CategorizedPOI",
    "CHARLOTTE_POI_CATEGORIES",
    "CHARLOTTE_LANDMARKS",
    "BRAND_IMPORTANCE",
    "POIExtractor",
]
