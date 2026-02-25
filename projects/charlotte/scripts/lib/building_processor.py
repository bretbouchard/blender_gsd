"""
Charlotte Digital Twin - Building Processor

Provides building classification and neighborhood detection
for the building importer.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class BuildingData:
    """Data structure for a building."""
    osm_id: int
    name: str
    building_type: str
    lod_level: int

    # Address
    housenumber: Optional[str]
    street: Optional[str]
    city: str = "Charlotte"

    # Physical
    height: Optional[float]
    levels: Optional[int]

    # Organization
    neighborhood: Optional[str]
    block_id: Optional[str]

    # Tags
    tags: Dict[str, str]


class BuildingClassifier:
    """Classifies buildings for LOD and priority."""

    # Building importance by type
    IMPORTANCE = {
        'commercial': 10,
        'retail': 9,
        'office': 9,
        'apartments': 7,
        'house': 5,
        'terrace': 5,
        'garage': 2,
        'shed': 1,
        'yes': 3,
        'roof': 1,
        'parking': 1,
    }

    def get_lod_level(self, building: Dict) -> int:
        """
        Determine LOD level for a building.

        Priority factors:
        1. Named buildings -> LOD0
        2. Buildings with addresses -> LOD1
        3. Commercial/retail -> LOD1
        4. Type-based priority
        """
        tags = building.get('tags', {})

        # Named buildings are always hero
        if tags.get('name'):
            return 0

        # Buildings with addresses
        if tags.get('addr:housenumber') and tags.get('addr:street'):
            return 1

        # Type-based priority
        building_type = building.get('subtype', 'yes')
        importance = self.IMPORTANCE.get(building_type, 3)

        if importance >= 7:
            return 0
        elif importance >= 5:
            return 1
        else:
            return 2


class NeighborhoodDetector:
    """Groups buildings into neighborhoods."""

    # Charlotte neighborhoods with approximate centers (lat, lon)
    NEIGHBORHOODS = {
        'Uptown': (35.227, -80.843),
        'South End': (35.217, -80.855),
        'Elizabeth': (35.216, -80.822),
        'Plaza Midwood': (35.226, -80.807),
        'NoDa': (35.235, -80.835),
        'Dilworth': (35.208, -80.848),
        'Myers Park': (35.195, -80.842),
        'Fourth Ward': (35.233, -80.850),
        'First Ward': (35.230, -80.838),
        'Second Ward': (35.220, -80.838),
        'Third Ward': (35.225, -80.853),
    }

    def __init__(self, max_distance: float = 600):
        """
        Args:
            max_distance: Maximum distance (meters) to assign to a neighborhood
        """
        self.max_distance = max_distance

    def assign_neighborhood(self, lat: float, lon: float) -> str:
        """
        Find nearest neighborhood for coordinates.

        Returns:
            Neighborhood name or 'Other'
        """
        best_neighborhood = None
        best_distance = float('inf')

        for name, (center_lat, center_lon) in self.NEIGHBORHOODS.items():
            dist = self._haversine(lat, lon, center_lat, center_lon)
            if dist < best_distance:
                best_distance = dist
                best_neighborhood = name

        if best_distance <= self.max_distance:
            return best_neighborhood

        return 'Other'

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in meters between two points."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c


class BlockDetector:
    """Groups buildings into city blocks."""

    def __init__(self, max_distance: float = 30):
        """
        Args:
            max_distance: Maximum distance (meters) for buildings to be in same block
        """
        self.max_distance = max_distance

    def detect_blocks(
        self,
        buildings: List[Dict],
        node_lookup: Dict
    ) -> Dict[str, List[int]]:
        """
        Cluster buildings into blocks.

        Args:
            buildings: List of building data dicts
            node_lookup: Lookup for node positions

        Returns:
            Dict mapping block_id -> list of building osm_ids
        """
        blocks = {}
        assigned = set()
        block_num = 0

        # Calculate center for each building
        building_centers = {}
        for b in buildings:
            node_ids = b.get('node_ids', [])
            if not node_ids:
                continue

            lats = []
            lons = []
            for nid in node_ids:
                node = node_lookup.get(str(nid))
                if node:
                    lats.append(node['lat'])
                    lons.append(node['lon'])

            if lats and lons:
                building_centers[b['osm_id']] = (
                    sum(lats) / len(lats),
                    sum(lons) / len(lons)
                )

        for building in buildings:
            osm_id = building['osm_id']
            if osm_id in assigned:
                continue

            if osm_id not in building_centers:
                continue

            block_id = f"Block_{block_num:04d}"
            blocks[block_id] = [osm_id]
            assigned.add(osm_id)

            center1 = building_centers[osm_id]

            # Find nearby buildings
            for other in buildings:
                other_id = other['osm_id']
                if other_id in assigned:
                    continue

                if other_id not in building_centers:
                    continue

                center2 = building_centers[other_id]
                dist = self._haversine(center1[0], center1[1], center2[0], center2[1])

                if dist <= self.max_distance:
                    blocks[block_id].append(other_id)
                    assigned.add(other_id)

            block_num += 1

        return blocks

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in meters between two points."""
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
