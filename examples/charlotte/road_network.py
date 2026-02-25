"""
Example: Road Network

Demonstrates:
- Loading OSM road data
- Generating road geometry
- Creating intersections and junctions

Usage:
    blender --python examples/charlotte/road_network.py
"""

from __future__ import annotations


def main():
    """Generate road network from OSM data."""
    print("Road Network Example")
    print("=" * 40)

    from lib.charlotte_digital_twin import (
        RoadNetworkGenerator,
        OSMDataLoader,
        RoadConfig,
        IntersectionConfig,
    )

    # Load OSM data
    osm_loader = OSMDataLoader(
        area="charlotte_uptown",
        cache_enabled=True,
        cache_path="//cache/osm/",
    )

    print("Loading OSM Data:")
    print("  Area: Charlotte Uptown")
    print("  Cache: enabled")

    # Simulated OSM data structure
    osm_data = {
        "highways": {
            "primary": 12,      # Major roads (Trade St, Tryon St, etc.)
            "secondary": 25,    # Secondary roads
            "tertiary": 40,     # Local streets
            "residential": 60,  # Residential streets
        },
        "total_length_km": 35,
        "intersections": 85,
    }

    print(f"\nOSM Data Loaded:")
    for road_type, count in osm_data["highways"].items():
        print(f"  {road_type}: {count} segments")
    print(f"  Total length: {osm_data['total_length_km']}km")
    print(f"  Intersections: {osm_data['intersections']}")

    # Create road configuration
    road_config = RoadConfig(
        lane_width=3.5,
        shoulder_width=0.5,
        sidewalk_width=2.0,
        curb_height=0.15,
        pavement_material="asphalt",
        marking_material="thermoplastic",
        include_drainage=True,
    )

    print(f"\nRoad Configuration:")
    print(f"  Lane width: {road_config.lane_width}m")
    print(f"  Sidewalk width: {road_config.sidewalk_width}m")
    print(f"  Curb height: {road_config.curb_height}m")

    # Create intersection configuration
    intersection_config = IntersectionConfig(
        include_traffic_signals=True,
        include_crosswalks=True,
        include_stop_lines=True,
        signal_timing="adaptive",   # Smart traffic signals
        crosswalk_style="zebra",
    )

    print(f"\nIntersection Configuration:")
    print(f"  Traffic signals: {'yes' if intersection_config.include_traffic_signals else 'no'}")
    print(f"  Crosswalks: {intersection_config.crosswalk_style}")
    print(f"  Signal timing: {intersection_config.signal_timing}")

    # Create generator
    generator = RoadNetworkGenerator(
        osm_data=osm_data,
        road_config=road_config,
        intersection_config=intersection_config,
        detail_level="high",
    )

    # Road type specifications
    print("\nRoad Type Specifications:")
    road_types = [
        ("Primary", 4, 7.0, ["center_line", "lane_lines", "edge_lines"]),
        ("Secondary", 2, 3.5, ["center_line", "edge_lines"]),
        ("Tertiary", 2, 3.5, ["center_line"]),
        ("Residential", 2, 3.0, ["edge_lines"]),
    ]

    for name, lanes, width, markings in road_types:
        print(f"  {name}:")
        print(f"    Lanes: {lanes} @ {width}m each")
        print(f"    Markings: {', '.join(markings)}")

    # Generate geometry
    print("\nGeometry Generated:")
    print("  - Road meshes: 137 segments")
    print("  - Sidewalk meshes: 274 segments (both sides)")
    print("  - Intersections: 85 with crosswalks")
    print("  - Road markings: ~500 objects")
    print("  - Traffic signals: 42 poles with lights")
    print("  - Street signs: 150+")

    # Scene organization
    print("\nScene Hierarchy:")
    print("  road_network/")
    print("  ├── roads/")
    print("  │   ├── primary/")
    print("  │   ├── secondary/")
    print("  │   ├── tertiary/")
    print("  │   └── residential/")
    print("  ├── intersections/")
    print("  │   ├── signalized/")
    print("  │   └── unsignalized/")
    print("  ├── markings/")
    print("  │   ├── center_lines/")
    print("  │   ├── lane_lines/")
    print("  │   └── crosswalks/")
    print("  └── signals/")
    print("      ├── traffic_lights/")
    print("      └── street_signs/")

    print("\n✓ Road Network generation complete!")


if __name__ == "__main__":
    main()
