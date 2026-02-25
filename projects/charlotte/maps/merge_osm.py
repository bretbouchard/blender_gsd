#!/usr/bin/env python3
"""
Merge multiple OSM files into a single file.
Handles overlapping data by deduplicating nodes, ways, and relations.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def get_bounds(file_path):
    """Extract bounds from an OSM file."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    bounds = root.find('bounds')
    if bounds is not None:
        return {
            'minlat': float(bounds.get('minlat')),
            'minlon': float(bounds.get('minlon')),
            'maxlat': float(bounds.get('maxlat')),
            'maxlon': float(bounds.get('maxlon'))
        }
    return None

def merge_osm_files(input_files, output_file):
    """Merge multiple OSM files into one."""

    # Track all unique elements by type and id
    nodes = {}
    ways = {}
    relations = {}

    # Track combined bounds
    minlat, minlon = float('inf'), float('inf')
    maxlat, maxlon = float('-inf'), float('-inf')

    print(f"Merging {len(input_files)} OSM files...")

    for file_path in input_files:
        print(f"  Processing: {file_path.name}")
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Update bounds
        bounds = root.find('bounds')
        if bounds is not None:
            b = {
                'minlat': float(bounds.get('minlat')),
                'minlon': float(bounds.get('minlon')),
                'maxlat': float(bounds.get('maxlat')),
                'maxlon': float(bounds.get('maxlon'))
            }
            minlat = min(minlat, b['minlat'])
            minlon = min(minlon, b['minlon'])
            maxlat = max(maxlat, b['maxlat'])
            maxlon = max(maxlon, b['maxlon'])

        # Collect nodes
        for node in root.findall('node'):
            node_id = node.get('id')
            if node_id and node_id not in nodes:
                nodes[node_id] = node

        # Collect ways
        for way in root.findall('way'):
            way_id = way.get('id')
            if way_id and way_id not in ways:
                ways[way_id] = way

        # Collect relations
        for rel in root.findall('relation'):
            rel_id = rel.get('id')
            if rel_id and rel_id not in relations:
                relations[rel_id] = rel

    print(f"\nUnique elements found:")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Ways: {len(ways)}")
    print(f"  Relations: {len(relations)}")
    print(f"\nCombined bounds:")
    print(f"  minlat={minlat:.6f}, minlon={minlon:.6f}")
    print(f"  maxlat={maxlat:.6f}, maxlon={maxlon:.6f}")

    # Create output XML
    osm = ET.Element('osm')
    osm.set('version', '0.6')
    osm.set('generator', 'merge_osm.py')

    # Add combined bounds
    bounds = ET.SubElement(osm, 'bounds')
    bounds.set('minlat', f'{minlat:.7f}')
    bounds.set('minlon', f'{minlon:.7f}')
    bounds.set('maxlat', f'{maxlat:.7f}')
    bounds.set('maxlon', f'{maxlon:.7f}')

    # Add all nodes
    for node_id in sorted(nodes.keys(), key=lambda x: int(x)):
        osm.append(nodes[node_id])

    # Add all ways
    for way_id in sorted(ways.keys(), key=lambda x: int(x)):
        osm.append(ways[way_id])

    # Add all relations
    for rel_id in sorted(relations.keys(), key=lambda x: int(x)):
        osm.append(relations[rel_id])

    # Write output
    tree = ET.ElementTree(osm)
    ET.indent(tree, space=' ')
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

    print(f"\nMerged file written to: {output_file}")
    return True

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Merge OSM files')
    parser.add_argument('inputs', nargs='+', help='Input OSM files')
    parser.add_argument('-o', '--output', required=True, help='Output file')

    args = parser.parse_args()

    input_files = [Path(f) for f in args.inputs]
    output_file = Path(args.output)

    merge_osm_files(input_files, output_file)
