#!/usr/bin/env python3
"""
Charlotte Digital Twin - Assign Proper Building Heights

This script:
1. Loads the OSM manifest with building data
2. Matches buildings to the accurate heights database
3. Creates a new manifest with correct heights
4. Exports a report of all buildings with assigned heights
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from building_heights import CHARLOTTE_BUILDINGS, get_building_heights_dict, BuildingHeight


@dataclass
class BuildingMatch:
    """Result of matching an OSM building to height database."""
    osm_id: int
    osm_name: str
    matched_name: Optional[str]
    height_m: float
    height_ft: float
    floors: int
    confidence: str  # 'exact', 'partial', 'address', 'default'
    source: str


# Name mappings: OSM name -> building_heights.py name
NAME_MAPPINGS = {
    # =========================================================================
    # TIER 1: MAJOR SKYSCRAPERS
    # =========================================================================
    '550 South Tryon': '550 South Tryon',
    'Duke Energy Center': '550 South Tryon',
    'Bank of America Corporate Center': 'Bank of America Corporate Center',
    'Bank of America': 'Bank of America Corporate Center',  # OSM uses this name
    'Truist Center': 'Truist Center',
    'Hearst Tower': 'Truist Center',
    'Bank of America Tower': 'Bank of America Tower',
    'Charlotte Metro Tower': 'Bank of America Tower',
    'Duke Energy Plaza': 'Duke Energy Plaza',
    'Duke Energy': 'Duke Energy Plaza',

    # =========================================================================
    # TIER 2: HIGH-RISES
    # =========================================================================
    '301 South College': '301 South College',
    'One Wells Fargo Center': '301 South College',
    'The Vue': 'The Vue',
    'The VUE': 'The Vue',
    'One South': 'One South at The Plaza',
    '1 Bank of America Center': '1 Bank of America Center',
    '300 South Tryon': '300 South Tryon',
    '121 West Trade': '121 West Trade',
    'Interstate Tower': '121 West Trade',
    'Three Wells Fargo Center': 'Three Wells Fargo Center',
    '201 North Tryon': '201 North Tryon',
    'IJL Financial Center': '201 North Tryon',
    'Museum Tower': 'Museum Tower',
    'Two Wells Fargo Center': 'Two Wells Fargo Center',
    '400 South Tryon': '400 South Tryon',
    'Carillon Tower': 'Carillon Tower',
    'Charlotte Plaza': 'Charlotte Plaza',
    'The Ellis': 'The Ellis',
    'Ally Charlotte Center': 'Ally Charlotte Center',
    'FNB Tower Charlotte': 'FNB Tower Charlotte',
    'Honeywell Tower': 'Honeywell Tower',
    '525 North Tryon': '525 North Tryon',
    'TradeMark': 'TradeMark',
    'First Citizens Plaza': 'First Citizens Plaza',
    'First Citizens Bank Plaza': 'First Citizens Plaza',
    'Avenue': 'Avenue',
    '200 South College': 'Two Wells Fargo Center',
    '200 South Tryon Street': '200 South Tryon',  # Historic building

    # =========================================================================
    # HOTELS
    # =========================================================================
    'The Westin Charlotte': 'The Westin Charlotte',
    'Westin Charlotte': 'The Westin Charlotte',
    'Ritz-Carlton Charlotte': 'Ritz-Carlton Charlotte',
    'The Ritz-Carlton, Charlotte': 'Ritz-Carlton Charlotte',
    'Charlotte Marriott City Center': 'Charlotte Marriott City Center',
    'Marriott City Center': 'Charlotte Marriott City Center',
    'Hilton Charlotte Center City': 'Hilton Charlotte Center City',
    'Hilton Charlotte Uptown': 'Hilton Charlotte Center City',
    'JW Marriott Charlotte': 'JW Marriott Charlotte',
    'Le Méridien Charlotte': 'Le Méridien Charlotte',
    'Le Meridien Charlotte': 'Le Méridien Charlotte',
    'Kimpton Tryon Park': 'Kimpton Tryon Park',
    'Kimpton Hotel': 'Kimpton Tryon Park',
    '550 South': '550 South',
    'NASCAR Plaza': '550 South',
    '650 South Tryon': '650 S Tryon',

    # =========================================================================
    # RESIDENTIAL
    # =========================================================================
    'Catalyst': 'Catalyst',
    'The Arlington': 'The Arlington',
    'Skye': 'Skye',
    'SKYE': 'Skye',
    'Ascent Uptown': 'Ascent Uptown',
    'Bell Uptown Charlotte': 'Bell Uptown Charlotte',
    'The Ascher': 'The Ascher North Tower',
    'Ascher Uptown': 'The Ascher North Tower',
    'The Francis Apartments': 'The Francis Apartments',
    'Uptown 550': 'Uptown 550',

    # =========================================================================
    # HISTORIC / SMALLER
    # =========================================================================
    '112 Tryon Plaza': '112 Tryon Plaza',
    'Johnston Building': 'Johnston Building',
    '129 West Trade': '129 West Trade',
    '440 South Church': '440 South Church',
    'Regions 615': 'Regions 615',
    '615 South College': 'Regions 615',
    'Charlotte-Mecklenburg Government Center': 'Charlotte-Mecklenburg Government Center',
    'Char-Meck Government Center': 'Charlotte-Mecklenburg Government Center',

    # =========================================================================
    # SOUTH END
    # =========================================================================
    '110 East': '110 East',
    'Lowe\'s Global Technology Center': 'Lowe\'s Global Technology Center',
    'The Line': 'The Line',
}


def normalize_name(name: str) -> str:
    """Normalize a building name for matching."""
    if not name:
        return ""
    # Lowercase, remove common suffixes
    name = name.lower().strip()
    for suffix in [' building', ' tower', ' center', ' plaza', ' office']:
        name = name.replace(suffix, '')
    return name


def match_building(osm_name: str, osm_tags: Dict) -> Optional[BuildingHeight]:
    """Try to match an OSM building to the heights database."""
    heights_db = get_building_heights_dict()

    if not osm_name:
        return None

    # 1. Try exact name match via mapping
    if osm_name in NAME_MAPPINGS:
        mapped_name = NAME_MAPPINGS[osm_name]
        if mapped_name in heights_db:
            return heights_db[mapped_name]

    # 2. Try exact match with heights db
    if osm_name in heights_db:
        return heights_db[osm_name]

    # 3. Try normalized matching (only if very close)
    osm_norm = normalize_name(osm_name)
    for db_name, building in heights_db.items():
        db_norm = normalize_name(db_name)
        # Only match if very similar (one is substring of other AND significant overlap)
        if osm_norm == db_norm:
            return building

    # 4. Try partial matching (must be significant portion - at least 10 chars or 70%)
    for db_name, building in heights_db.items():
        db_norm = normalize_name(db_name)
        if len(osm_norm) >= 10 and osm_norm in db_norm:
            return building
        if len(db_norm) >= 10 and db_norm in osm_norm:
            return building
        # Also check if they share a significant common prefix (like "bank of america")
        if len(osm_norm) >= 15 and len(db_norm) >= 15:
            if osm_norm[:15] == db_norm[:15]:
                return building

    return None


def estimate_height_from_levels(levels: int) -> float:
    """Estimate building height from floor count."""
    # Commercial: ~4m per floor, Residential: ~3.5m per floor
    # Use average of 3.8m
    return levels * 3.8


def get_building_type_multiplier(building_type: str) -> float:
    """Get height multiplier based on building type."""
    multipliers = {
        'commercial': 1.0,
        'office': 1.0,
        'retail': 0.8,
        'apartments': 0.9,
        'residential': 0.9,
        'house': 0.5,
        'garage': 0.6,
        'parking': 0.5,
        'hotel': 0.95,
        'yes': 0.8,
    }
    return multipliers.get(building_type, 0.8)


def process_manifest(manifest_path: str, output_path: str):
    """Process manifest and assign proper heights."""
    print(f"Loading manifest from {manifest_path}...")
    with open(manifest_path) as f:
        manifest = json.load(f)

    ways = manifest.get('ways', {})
    nodes = manifest.get('nodes', {})

    # Statistics
    stats = {
        'total_buildings': 0,
        'named_buildings': 0,
        'matched_exact': 0,
        'matched_partial': 0,
        'osm_original': 0,
        'estimated_from_levels': 0,
        'default_height': 0,
    }

    matches: List[BuildingMatch] = []

    # Process each building
    for osm_id, way in ways.items():
        if way.get('way_type') != 'building':
            continue

        stats['total_buildings'] += 1
        tags = way.get('tags', {})
        osm_name = tags.get('name', '')
        building_type = way.get('subtype', 'yes')

        if osm_name:
            stats['named_buildings'] += 1

        # Try to match to heights database
        matched = match_building(osm_name, tags)

        if matched:
            # Use accurate height from database
            if osm_name.lower() == matched.name.lower():
                stats['matched_exact'] += 1
            else:
                stats['matched_partial'] += 1

            match = BuildingMatch(
                osm_id=int(osm_id),
                osm_name=osm_name or f"Building_{osm_id}",
                matched_name=matched.name,
                height_m=matched.height_m,
                height_ft=matched.height_ft,
                floors=matched.floors,
                confidence='exact' if osm_name.lower() == matched.name.lower() else 'partial',
                source='database'
            )
            matches.append(match)

            # Update the manifest
            way['height'] = matched.height_m
            way['building:levels'] = matched.floors
            way['height_source'] = 'charlotte_heights_db'

        else:
            # No match - check OSM height, estimate from levels, or use default
            levels = tags.get('building:levels')
            existing_height = tags.get('height')

            # First, try to parse existing OSM height
            osm_height = None
            if existing_height:
                try:
                    # Handle various formats: '30', '30m', "19'", etc.
                    h_clean = existing_height.replace('m','').replace("'","").replace('ft','').strip()
                    osm_height = float(h_clean)
                except:
                    pass

            # Use OSM height if it's reasonable (between 3m and 500m)
            if osm_height and 3 <= osm_height <= 500:
                way['height'] = osm_height
                way['height_source'] = 'osm_original'
                stats['osm_original'] += 1
            elif levels:
                try:
                    levels_int = int(levels)
                    height = estimate_height_from_levels(levels_int)
                    way['height'] = height
                    way['height_source'] = 'estimated_from_levels'
                    stats['estimated_from_levels'] += 1
                except (ValueError, TypeError):
                    # Use default based on building type
                    multiplier = get_building_type_multiplier(building_type)
                    way['height'] = 10.0 * multiplier
                    way['height_source'] = 'default'
                    stats['default_height'] += 1
            else:
                # Use default based on building type
                multiplier = get_building_type_multiplier(building_type)
                way['height'] = 10.0 * multiplier
                way['height_source'] = 'default'
                stats['default_height'] += 1

    # Save updated manifest
    print(f"Saving updated manifest to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print statistics
    print("\n" + "=" * 60)
    print("BUILDING HEIGHT ASSIGNMENT RESULTS")
    print("=" * 60)
    print(f"\nTotal buildings: {stats['total_buildings']}")
    print(f"Named buildings: {stats['named_buildings']}")
    print(f"\nHeight sources:")
    print(f"  Matched to database: {stats['matched_exact'] + stats['matched_partial']}")
    print(f"  From OSM data:       {stats['osm_original']}")
    print(f"  From levels:         {stats['estimated_from_levels']}")
    print(f"  Default/estimated:   {stats['default_height']}")

    # Print matched buildings
    if matches:
        print("\n" + "=" * 60)
        print("MATCHED BUILDINGS WITH ACCURATE HEIGHTS")
        print("=" * 60)
        matches.sort(key=lambda m: m.height_m, reverse=True)
        for m in matches[:50]:  # Show top 50
            print(f"  {m.osm_name:40} → {m.matched_name or 'N/A':35} {m.height_ft:4}ft")

    # Export full report
    report_path = output_path.replace('.json', '_heights_report.txt')
    with open(report_path, 'w') as f:
        f.write("CHARLOTTE BUILDING HEIGHTS REPORT\n")
        f.write("=" * 60 + "\n\n")

        f.write("STATISTICS\n")
        f.write("-" * 40 + "\n")
        for k, v in stats.items():
            f.write(f"  {k}: {v}\n")

        f.write("\n\nMATCHED BUILDINGS (sorted by height)\n")
        f.write("-" * 40 + "\n")
        for m in sorted(matches, key=lambda x: x.height_m, reverse=True):
            f.write(f"{m.osm_name:40} → {m.matched_name or 'N/A':30} {m.height_ft:4}ft ({m.floors} fl)\n")

    print(f"\nReport saved to: {report_path}")

    return stats, matches


def export_heights_for_blender(output_path: str):
    """Export a simple JSON for Blender to use."""
    heights_dict = {}

    for building in CHARLOTTE_BUILDINGS:
        # Create multiple name variants for matching
        names = [
            building.name,
            building.name.lower(),
            building.name.replace(' ', '_'),
        ]

        # Add common aliases
        if building.name == "Bank of America Corporate Center":
            names.extend(["BOA Corporate Center", "Bank of America Center"])
        elif building.name == "550 South Tryon":
            names.extend(["Duke Energy Center", "550 S Tryon"])
        elif building.name == "Truist Center":
            names.extend(["Hearst Tower"])
        elif building.name == "One South at The Plaza":
            names.extend(["One South", "1 South", "1 S Tryon"])

        height_data = {
            'height_m': building.height_m,
            'height_ft': building.height_ft,
            'floors': building.floors,
            'lat': building.lat,
            'lon': building.lon,
            'address': building.address,
        }

        for name in names:
            heights_dict[name] = height_data

    with open(output_path, 'w') as f:
        json.dump(heights_dict, f, indent=2)

    print(f"Blender heights file saved to: {output_path}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Assign proper heights to Charlotte buildings')
    parser.add_argument(
        '--manifest', '-m',
        default='output/osm_manifest.json',
        help='Input OSM manifest file'
    )
    parser.add_argument(
        '--output', '-o',
        default='output/osm_manifest_with_heights.json',
        help='Output manifest file'
    )
    parser.add_argument(
        '--blender-export',
        default='output/building_heights_blender.json',
        help='Output file for Blender'
    )

    args = parser.parse_args()

    # Process manifest
    stats, matches = process_manifest(args.manifest, args.output)

    # Export for Blender
    export_heights_for_blender(args.blender_export)

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nUpdated manifest: {args.output}")
    print(f"Blender heights:  {args.blender_export}")
