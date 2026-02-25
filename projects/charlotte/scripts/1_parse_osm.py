#!/usr/bin/env python3
"""
Charlotte Digital Twin - OSM Parser

Parses the merged OSM file and classifies all elements into categories:
- Buildings (has 'building' tag)
- Roads (has 'highway' tag)
- Bridges (highway + bridge=yes)
- Other

Extracts all tags as attributes and builds a clean data structure
for downstream importers.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.elevation import ElevationManager


class WayType(Enum):
    """Classification of OSM ways."""
    BUILDING = "building"
    ROAD = "road"
    BRIDGE = "bridge"
    WATER = "water"
    LANDUSE = "landuse"
    OTHER = "other"


@dataclass
class NodeData:
    """Data for a single OSM node."""
    osm_id: int
    lat: float
    lon: float
    ele: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class WayData:
    """Data for a single OSM way."""
    osm_id: int
    way_type: WayType
    subtype: str  # building type, highway type, etc.
    node_ids: List[int] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    # Classification details
    lod_hint: int = 2
    priority: int = 3
    is_bridge: bool = False
    has_address: bool = False


class OSMClassifier:
    """Classifies OSM ways into categories."""

    # Building types with LOD hints
    BUILDING_TYPES = {
        'commercial': {'lod': 0, 'priority': 1},
        'retail': {'lod': 0, 'priority': 1},
        'office': {'lod': 0, 'priority': 1},
        'apartments': {'lod': 1, 'priority': 2},
        'house': {'lod': 2, 'priority': 3},
        'terrace': {'lod': 2, 'priority': 3},
        'garage': {'lod': 3, 'priority': 4},
        'shed': {'lod': 3, 'priority': 4},
        'yes': {'lod': 2, 'priority': 3},
        'roof': {'lod': 3, 'priority': 4},
        'parking': {'lod': 3, 'priority': 4},
    }

    # Highway types with specs
    HIGHWAY_TYPES = {
        'motorway': {'width': 25.0, 'lanes': 6, 'priority': 1, 'class': 'highway'},
        'motorway_link': {'width': 10.0, 'lanes': 2, 'priority': 1, 'class': 'highway'},
        'trunk': {'width': 22.0, 'lanes': 4, 'priority': 1, 'class': 'highway'},
        'trunk_link': {'width': 10.0, 'lanes': 2, 'priority': 1, 'class': 'highway'},
        'primary': {'width': 15.0, 'lanes': 4, 'priority': 1, 'class': 'arterial'},
        'primary_link': {'width': 12.0, 'lanes': 2, 'priority': 1, 'class': 'arterial'},
        'secondary': {'width': 12.0, 'lanes': 3, 'priority': 2, 'class': 'collector'},
        'secondary_link': {'width': 10.0, 'lanes': 2, 'priority': 2, 'class': 'collector'},
        'tertiary': {'width': 10.0, 'lanes': 2, 'priority': 2, 'class': 'collector'},
        'tertiary_link': {'width': 8.0, 'lanes': 2, 'priority': 2, 'class': 'collector'},
        'residential': {'width': 9.0, 'lanes': 2, 'priority': 3, 'class': 'local'},
        'unclassified': {'width': 8.0, 'lanes': 2, 'priority': 3, 'class': 'local'},
        'living_street': {'width': 7.0, 'lanes': 2, 'priority': 3, 'class': 'local'},
        'service': {'width': 5.0, 'lanes': 1, 'priority': 4, 'class': 'service'},
        'driveway': {'width': 4.0, 'lanes': 1, 'priority': 4, 'class': 'service'},
        'parking_aisle': {'width': 4.0, 'lanes': 1, 'priority': 4, 'class': 'service'},
        'footway': {'width': 2.0, 'lanes': 0, 'priority': 5, 'class': 'pedestrian'},
        'pedestrian': {'width': 3.0, 'lanes': 0, 'priority': 5, 'class': 'pedestrian'},
        'path': {'width': 1.5, 'lanes': 0, 'priority': 5, 'class': 'pedestrian'},
        'cycleway': {'width': 2.0, 'lanes': 1, 'priority': 5, 'class': 'pedestrian'},
        'steps': {'width': 2.0, 'lanes': 0, 'priority': 5, 'class': 'pedestrian'},
    }

    def classify_way(self, tags: Dict[str, str]) -> Tuple[WayType, str]:
        """
        Classify a way based on its tags.

        Returns:
            (WayType, subtype) tuple
        """
        # Check for building
        if 'building' in tags:
            return (WayType.BUILDING, tags.get('building', 'yes'))

        # Check for highway/road
        if 'highway' in tags:
            highway_type = tags['highway']

            # Check if it's a bridge
            if tags.get('bridge') == 'yes':
                return (WayType.BRIDGE, highway_type)

            return (WayType.ROAD, highway_type)

        # Check for water
        if 'waterway' in tags:
            return (WayType.WATER, tags['waterway'])
        if tags.get('natural') == 'water':
            return (WayType.WATER, 'water')

        # Check for landuse
        if 'landuse' in tags:
            return (WayType.LANDUSE, tags['landuse'])
        if 'leisure' in tags:
            return (WayType.LANDUSE, tags['leisure'])

        return (WayType.OTHER, 'unknown')

    def get_building_spec(self, building_type: str) -> Dict:
        """Get specification for a building type."""
        return self.BUILDING_TYPES.get(building_type, self.BUILDING_TYPES['yes'])

    def get_highway_spec(self, highway_type: str) -> Dict:
        """Get specification for a highway type."""
        return self.HIGHWAY_TYPES.get(highway_type, {
            'width': 8.0, 'lanes': 2, 'priority': 3, 'class': 'local'
        })


class OSMParser:
    """
    Parses OSM XML and classifies elements.

    Creates a manifest with:
    - All nodes with positions
    - All ways classified by type
    - Statistics for the dataset
    """

    def __init__(self, osm_path: str):
        self.osm_path = osm_path
        self.nodes: Dict[int, NodeData] = {}
        self.ways: Dict[int, WayData] = {}
        self.relations: List[Dict] = []
        self.classifier = OSMClassifier()
        self.elevation_manager: Optional[ElevationManager] = None

    def parse(self) -> None:
        """Parse the OSM file."""
        print(f"Parsing {self.osm_path}...")

        tree = ET.parse(self.osm_path)
        root = tree.getroot()

        # Parse bounds
        bounds = root.find('bounds')
        if bounds is not None:
            self.bounds = {
                'minlat': float(bounds.get('minlat')),
                'minlon': float(bounds.get('minlon')),
                'maxlat': float(bounds.get('maxlat')),
                'maxlon': float(bounds.get('maxlon')),
            }
            print(f"  Bounds: {self.bounds['minlat']:.4f}, {self.bounds['minlon']:.4f} to "
                  f"{self.bounds['maxlat']:.4f}, {self.bounds['maxlon']:.4f}")

        # Parse nodes
        self._parse_nodes(root)
        print(f"  Parsed {len(self.nodes)} nodes")

        # Parse ways
        self._parse_ways(root)
        print(f"  Parsed {len(self.ways)} ways")

        # Parse relations
        self._parse_relations(root)
        print(f"  Parsed {len(self.relations)} relations")

        # Load elevation data
        self.elevation_manager = ElevationManager()
        self.elevation_manager.nodes = {
            nid: {
                'lat': n.lat,
                'lon': n.lon,
                'ele': n.ele,
                'tags': n.tags,
            }
            for nid, n in self.nodes.items()
        }
        # Extract known elevations
        for nid, n in self.nodes.items():
            if n.ele is not None:
                self.elevation_manager.elevations[nid] = n.ele
                self.elevation_manager.known_points.append((n.lat, n.lon, n.ele))

        self.elevation_manager.report.total_nodes = len(self.nodes)
        self.elevation_manager.report.nodes_with_elevation = len(
            self.elevation_manager.elevations
        )

    def _parse_nodes(self, root: ET.Element) -> None:
        """Extract all nodes with their data."""
        for node in root.findall('node'):
            node_id = int(node.get('id'))
            lat = float(node.get('lat'))
            lon = float(node.get('lon'))

            # Extract tags
            tags = {}
            ele = None

            for tag in node.findall('tag'):
                k = tag.get('k')
                v = tag.get('v')
                tags[k] = v

                if k == 'ele':
                    try:
                        ele = float(v)
                    except ValueError:
                        pass

            self.nodes[node_id] = NodeData(
                osm_id=node_id,
                lat=lat,
                lon=lon,
                ele=ele,
                tags=tags,
            )

    def _parse_ways(self, root: ET.Element) -> None:
        """Extract and classify all ways."""
        for way in root.findall('way'):
            way_id = int(way.get('id'))

            # Get node references
            node_refs = [
                int(nd.get('ref'))
                for nd in way.findall('nd')
            ]

            # Get tags
            tags = {
                tag.get('k'): tag.get('v')
                for tag in way.findall('tag')
            }

            # Classify the way
            way_type, subtype = self.classifier.classify_way(tags)

            # Get additional classification details
            lod_hint = 2
            priority = 3
            is_bridge = way_type == WayType.BRIDGE
            has_address = 'addr:street' in tags or 'addr:housenumber' in tags

            if way_type == WayType.BUILDING:
                spec = self.classifier.get_building_spec(subtype)
                lod_hint = spec['lod']
                priority = spec['priority']
            elif way_type in (WayType.ROAD, WayType.BRIDGE):
                spec = self.classifier.get_highway_spec(subtype)
                priority = spec['priority']
                if spec['class'] == 'highway':
                    lod_hint = 1
                elif spec['class'] in ('arterial', 'collector'):
                    lod_hint = 1
                else:
                    lod_hint = 2

            self.ways[way_id] = WayData(
                osm_id=way_id,
                way_type=way_type,
                subtype=subtype,
                node_ids=node_refs,
                tags=tags,
                lod_hint=lod_hint,
                priority=priority,
                is_bridge=is_bridge,
                has_address=has_address,
            )

    def _parse_relations(self, root: ET.Element) -> None:
        """Extract relations (for multipolygons, routes)."""
        for rel in root.findall('relation'):
            rel_id = int(rel.get('id'))

            members = [
                {
                    'type': m.get('type'),
                    'ref': int(m.get('ref')),
                    'role': m.get('role', ''),
                }
                for m in rel.findall('member')
            ]

            tags = {
                tag.get('k'): tag.get('v')
                for tag in rel.findall('tag')
            }

            self.relations.append({
                'osm_id': rel_id,
                'members': members,
                'tags': tags,
            })

    def get_statistics(self) -> Dict:
        """Get parsing statistics."""
        stats = {
            'total_nodes': len(self.nodes),
            'total_ways': len(self.ways),
            'total_relations': len(self.relations),
            'nodes_with_elevation': len([
                n for n in self.nodes.values() if n.ele is not None
            ]),
            'by_type': {},
            'by_subtype': {},
            'buildings_with_address': 0,
            'bridges': 0,
        }

        for way in self.ways.values():
            # Count by type
            type_name = way.way_type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1

            # Count by subtype
            key = f"{way.way_type.value}:{way.subtype}"
            stats['by_subtype'][key] = stats['by_subtype'].get(key, 0) + 1

            # Count special cases
            if way.way_type == WayType.BUILDING and way.has_address:
                stats['buildings_with_address'] += 1

            if way.is_bridge:
                stats['bridges'] += 1

        # Sort by count
        stats['by_subtype'] = dict(
            sorted(stats['by_subtype'].items(), key=lambda x: -x[1])
        )

        return stats

    def get_buildings(self) -> List[WayData]:
        """Get all building ways."""
        return [w for w in self.ways.values() if w.way_type == WayType.BUILDING]

    def get_roads(self) -> List[WayData]:
        """Get all road ways (not bridges)."""
        return [w for w in self.ways.values() if w.way_type == WayType.ROAD]

    def get_bridges(self) -> List[WayData]:
        """Get all bridge ways."""
        return [w for w in self.ways.values() if w.way_type == WayType.BRIDGE]

    def save_manifest(self, output_path: str) -> None:
        """Save parsed data to JSON manifest."""
        print(f"Saving manifest to {output_path}...")

        manifest = {
            'bounds': getattr(self, 'bounds', None),
            'statistics': self.get_statistics(),
            'nodes': {
                str(nid): {
                    'osm_id': n.osm_id,
                    'lat': n.lat,
                    'lon': n.lon,
                    'ele': n.ele,
                    'tags': n.tags,
                }
                for nid, n in self.nodes.items()
            },
            'ways': {
                str(wid): {
                    'osm_id': w.osm_id,
                    'way_type': w.way_type.value,
                    'subtype': w.subtype,
                    'node_ids': w.node_ids,
                    'tags': w.tags,
                    'lod_hint': w.lod_hint,
                    'priority': w.priority,
                    'is_bridge': w.is_bridge,
                    'has_address': w.has_address,
                }
                for wid, w in self.ways.items()
            },
        }

        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"  Saved {len(self.nodes)} nodes, {len(self.ways)} ways")


def main():
    """Main entry point for parsing."""
    import argparse

    parser = argparse.ArgumentParser(description='Parse Charlotte OSM data')
    parser.add_argument(
        '--input', '-i',
        default='maps/charlotte-merged.osm',
        help='Input OSM file'
    )
    parser.add_argument(
        '--output', '-o',
        default='output/osm_manifest.json',
        help='Output manifest file'
    )

    args = parser.parse_args()

    # Parse
    osm = OSMParser(args.input)
    osm.parse()

    # Print statistics
    stats = osm.get_statistics()
    print("\n=== OSM Statistics ===")
    print(f"Nodes: {stats['total_nodes']:,}")
    print(f"Ways: {stats['total_ways']:,}")
    print(f"Nodes with elevation: {stats['nodes_with_elevation']:,}")
    print(f"\nBy Type:")
    for type_name, count in sorted(stats['by_type'].items()):
        print(f"  {type_name}: {count:,}")
    print(f"\nBuildings with address: {stats['buildings_with_address']:,}")
    print(f"Bridges: {stats['bridges']:,}")
    print(f"\nTop Subtypes:")
    for subtype, count in list(stats['by_subtype'].items())[:15]:
        print(f"  {subtype}: {count:,}")

    # Save manifest
    osm.save_manifest(args.output)

    # Save elevation report
    osm.elevation_manager.save_report('output/elevation_report.json')

    print("\nParsing complete!")


if __name__ == '__main__':
    main()
