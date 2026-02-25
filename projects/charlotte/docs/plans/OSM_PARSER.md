# Charlotte - OSM Parser Plan

## Goal
Parse the merged OSM file and classify all elements into categories for processing, extracting all relevant attributes and building a clean data structure for downstream importers.

## Requirements
- Parse `charlotte-merged.osm` efficiently (132k nodes, 18k ways)
- Classify ways into: buildings, roads, bridges, other
- Extract all tags as attributes
- Build node position lookup
- Generate classification manifest

## Output Data Structures

### Node Cache
```python
nodes = {
    osm_id: {
        'lat': float,
        'lon': float,
        'ele': float,  # elevation (if available)
        'tags': dict,
    }
}
```

### Classified Ways
```python
ways = {
    osm_id: {
        'type': 'building' | 'road' | 'bridge' | 'water' | 'other',
        'node_ids': [int],
        'tags': dict,
        'classification': {
            'subtype': str,  # building: house, commercial, etc.
            'priority': int, # processing priority
            'lod_hint': int, # suggested LOD level
        }
    }
}
```

## Implementation

### File: `scripts/1_parse_osm.py`

```python
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional
import json

@dataclass
class NodeData:
    osm_id: int
    lat: float
    lon: float
    ele: Optional[float]
    tags: Dict[str, str]

@dataclass
class WayData:
    osm_id: int
    node_ids: List[int]
    tags: Dict[str, str]
    way_type: str  # building, road, bridge, other
    subtype: str

class OSMParser:
    """Parses OSM XML and classifies elements."""

    WAY_CLASSIFICATION = {
        # Buildings
        'building': 'building',
        'building:part': 'building',

        # Roads (by highway tag)
        'highway': 'road',

        # Water
        'waterway': 'water',
        'natural': 'water',  # if value is water

        # Landuse
        'landuse': 'landuse',
        'leisure': 'leisure',

        # Other
        'amenity': 'amenity',
    }

    def __init__(self, osm_path: str):
        self.osm_path = osm_path
        self.nodes: Dict[int, NodeData] = {}
        self.ways: Dict[int, WayData] = {}
        self.relations: List[dict] = []

    def parse(self) -> None:
        """Parse the OSM file."""
        tree = ET.parse(self.osm_path)
        root = tree.getroot()

        self._parse_nodes(root)
        self._parse_ways(root)
        self._parse_relations(root)

    def _parse_nodes(self, root) -> None:
        """Extract all nodes with their data."""
        pass

    def _parse_ways(self, root) -> None:
        """Extract and classify all ways."""
        pass

    def _parse_relations(self, root) -> None:
        """Extract relations (for multipolygons, routes)."""
        pass

    def classify_way(self, tags: Dict[str, str]) -> tuple:
        """Classify a way based on its tags."""
        # Check for building
        if 'building' in tags:
            return 'building', tags.get('building', 'yes')

        # Check for road/highway
        if 'highway' in tags:
            # Check if it's also a bridge
            if tags.get('bridge') == 'yes':
                return 'bridge', tags['highway']
            return 'road', tags['highway']

        # Check other types
        for key, way_type in self.WAY_CLASSIFICATION.items():
            if key in tags:
                return way_type, tags.get(key, 'unknown')

        return 'other', 'unknown'

    def get_statistics(self) -> dict:
        """Get parsing statistics."""
        stats = {
            'total_nodes': len(self.nodes),
            'total_ways': len(self.ways),
            'by_type': {},
            'by_subtype': {},
        }

        for way in self.ways.values():
            stats['by_type'][way.way_type] = stats['by_type'].get(way.way_type, 0) + 1
            key = f"{way.way_type}:{way.subtype}"
            stats['by_subtype'][key] = stats['by_subtype'].get(key, 0) + 1

        return stats

    def save_manifest(self, output_path: str) -> None:
        """Save classification manifest to JSON."""
        manifest = {
            'statistics': self.get_statistics(),
            'nodes': {k: v.__dict__ for k, v in self.nodes.items()},
            'ways': {k: v.__dict__ for k, v in self.ways.items()},
        }
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

class OSMClassifier:
    """Provides detailed classification for ways."""

    # Building subtypes and their LOD hints
    BUILDING_TYPES = {
        'commercial': {'lod': 0, 'priority': 1},
        'retail': {'lod': 0, 'priority': 1},
        'office': {'lod': 0, 'priority': 1},
        'apartments': {'lod': 1, 'priority': 2},
        'house': {'lod': 2, 'priority': 3},
        'garage': {'lod': 3, 'priority': 4},
        'shed': {'lod': 3, 'priority': 4},
        'yes': {'lod': 2, 'priority': 3},  # Generic building
    }

    # Road types and their properties
    ROAD_TYPES = {
        'motorway': {'width': 25, 'lanes': 6, 'priority': 1},
        'motorway_link': {'width': 10, 'lanes': 2, 'priority': 1},
        'primary': {'width': 15, 'lanes': 4, 'priority': 1},
        'secondary': {'width': 12, 'lanes': 3, 'priority': 2},
        'tertiary': {'width': 10, 'lanes': 2, 'priority': 2},
        'residential': {'width': 8, 'lanes': 2, 'priority': 3},
        'service': {'width': 5, 'lanes': 1, 'priority': 4},
        'footway': {'width': 2, 'lanes': 0, 'priority': 5},
    }

    def classify_building(self, tags: dict) -> dict:
        """Get detailed building classification."""
        building_type = tags.get('building', 'yes')
        spec = self.BUILDING_TYPES.get(building_type, self.BUILDING_TYPES['yes'])

        return {
            'type': 'building',
            'subtype': building_type,
            'lod_hint': spec['lod'],
            'priority': spec['priority'],
            'has_address': 'addr:street' in tags or 'addr:housenumber' in tags,
            'height': tags.get('height'),
            'levels': tags.get('building:levels'),
        }

    def classify_road(self, tags: dict) -> dict:
        """Get detailed road classification."""
        highway_type = tags.get('highway', 'unclassified')
        spec = self.ROAD_TYPES.get(highway_type, {'width': 8, 'lanes': 2, 'priority': 3})

        return {
            'type': 'road',
            'subtype': highway_type,
            'width': float(tags.get('width', spec['width'])),
            'lanes': int(tags.get('lanes', spec['lanes'])),
            'priority': spec['priority'],
            'is_bridge': tags.get('bridge') == 'yes',
            'is_oneway': tags.get('oneway') == 'yes',
            'name': tags.get('name', ''),
            'surface': tags.get('surface', 'asphalt'),
        }

def main():
    """Main entry point for parsing."""
    parser = OSMParser('maps/charlotte-merged.osm')
    parser.parse()

    stats = parser.get_statistics()
    print(f"Parsed {stats['total_nodes']} nodes, {stats['total_ways']} ways")

    for way_type, count in sorted(stats['by_type'].items()):
        print(f"  {way_type}: {count}")

    parser.save_manifest('output/osm_manifest.json')
    print("Manifest saved to output/osm_manifest.json")

if __name__ == '__main__':
    main()
```

## Classification Rules

### Buildings
```
Has 'building' tag → building
  - building=yes → generic (LOD2)
  - building=commercial/retail/office → LOD0
  - building=house → LOD2
  - building=apartments → LOD1
```

### Roads
```
Has 'highway' tag → road (or bridge if bridge=yes)
  - highway=motorway → highway
  - highway=primary/secondary → arterial
  - highway=residential → local
  - highway=service → service
  - highway=footway → pedestrian
```

### Bridges
```
highway=* AND bridge=yes → bridge
  - Preserve road type as subtype
  - Flag for elevation processing
```

## Output Files
- `scripts/1_parse_osm.py` - Main parser script
- `output/osm_manifest.json` - Classification data (for debugging)
- `output/parsing_stats.json` - Statistics summary

## Success Criteria
- [ ] All 132k nodes parsed with positions
- [ ] All 18k ways classified
- [ ] Buildings correctly identified (3,739 expected)
- [ ] Roads separated by type
- [ ] Bridges flagged for special handling
- [ ] All tags preserved as attributes

## Estimated Effort
- Core parser: 1-2 hours
- Classification logic: 1 hour
- Testing and validation: 1 hour
