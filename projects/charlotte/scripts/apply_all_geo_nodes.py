"""
Charlotte Digital Twin - Apply All Geometry Nodes

Unified script to apply all procedural geometry to the scene:
- Building rooftop units
- Building window grids
- Road street lights
- Road sidewalks
- Road manholes
- Road furniture

Usage:
    # Apply everything with defaults
    blender charlotte.blend --python scripts/apply_all_geo_nodes.py

    # Apply with custom settings
    blender charlotte.blend --python scripts/apply_all_geo_nodes.py -- --setup-styles

    # Apply only buildings
    blender charlotte.blend --python scripts/apply_all_geo_nodes.py -- --buildings-only

    # Apply only roads
    blender charlotte.blend --python scripts/apply_all_geo_nodes.py -- --roads-only
"""

import bpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_buildings import (
    apply_geo_nodes_to_all_buildings,
    setup_all_styles as setup_building_styles,
    set_building_style,
    set_building_override,
    BUILDING_PRESETS,
)

from lib.geo_nodes_roads import (
    apply_geo_nodes_to_all_roads,
    setup_road_styles,
    set_road_style,
    set_road_override,
    ROAD_PRESETS,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Apply All Geo Nodes')
    parser.add_argument('--buildings-only', action='store_true',
                        help='Only apply to buildings')
    parser.add_argument('--roads-only', action='store_true',
                        help='Only apply to roads')
    parser.add_argument('--setup-styles', action='store_true',
                        help='Auto-apply style presets')
    parser.add_argument('--min-height', type=float, default=30.0,
                        help='Min building height for rooftop units')
    parser.add_argument('--light-spacing', type=float, default=30.0,
                        help='Street light spacing')
    parser.add_argument('--sidewalk-width', type=float, default=2.0,
                        help='Sidewalk width')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CHARLOTTE DIGITAL TWIN - ALL GEOMETRY NODES")
    print("=" * 60)

    if args.roads_only:
        # Roads only
        apply_geo_nodes_to_all_roads(
            global_light_spacing=args.light_spacing,
            global_sidewalk_width=args.sidewalk_width,
        )
        if args.setup_styles:
            setup_road_styles()

    elif args.buildings_only:
        # Buildings only
        apply_geo_nodes_to_all_buildings(
            global_min_height=args.min_height,
        )
        if args.setup_styles:
            setup_building_styles()

    else:
        # Everything
        print("\n--- BUILDINGS ---")
        apply_geo_nodes_to_all_buildings(
            global_min_height=args.min_height,
        )
        if args.setup_styles:
            setup_building_styles()

        print("\n--- ROADS ---")
        apply_geo_nodes_to_all_roads(
            global_light_spacing=args.light_spacing,
            global_sidewalk_width=args.sidewalk_width,
        )
        if args.setup_styles:
            setup_road_styles()

    # Summary
    print("\n" + "=" * 60)
    print("GEOMETRY NODES APPLIED")
    print("=" * 60)
    print("""
Node Groups Created:
  Buildings:
    - Building_Rooftop_Units
  Roads:
    - Road_Street_Lights
    - Road_Sidewalk
    - Road_Manhole_Covers
    - Road_Furniture

To adjust globally:
  1. Open Shader Editor > Geometry Nodes
  2. Select any node group
  3. Edit nodes - changes affect all objects

To adjust per-object:
  # Buildings
  set_building_style(obj, "landmark_tower")
  set_building_override(obj, "rooftop_scale", 1.5)

  # Roads
  set_road_style(obj, "downtown")
  set_road_override(obj, "light_spacing", 20)
""")


if __name__ == '__main__':
    main()
