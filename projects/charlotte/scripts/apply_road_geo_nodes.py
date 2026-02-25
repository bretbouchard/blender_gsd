"""
Charlotte Digital Twin - Apply Road Infrastructure Geo Nodes

Applies procedural infrastructure to all roads:
- Street lights (spacing, type, height)
- Sidewalks (width, curb height)
- Manhole covers (density)
- Street furniture (benches, trash cans)

Usage:
    # Apply to all roads with defaults
    blender charlotte.blend --python scripts/apply_road_geo_nodes.py

    # Custom global settings
    blender charlotte.blend --python scripts/apply_road_geo_nodes.py -- --light-spacing 25 --sidewalk-width 3

    # Auto-apply styles based on road type
    blender charlotte.blend --python scripts/apply_road_geo_nodes.py -- --setup-styles

After running, customize in Blender Python Console:

    # Set road style
    set_road_style(bpy.data.objects["Road_Tryon"], "downtown")

    # Override specific property
    set_road_override(bpy.data.objects["Road_Tryon"], "light_spacing", 20)
    set_road_override(bpy.data.objects["Road_Tryon"], "sidewalk_width", 4)

    # Disable sidewalks on a road
    set_road_override(bpy.data.objects["Road_Highway"], "sidewalk_enabled", False)
"""

import bpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_roads import (
    apply_geo_nodes_to_all_roads,
    set_road_style,
    set_road_override,
    setup_road_styles,
    create_all_road_node_groups,
    ROAD_PRESETS,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Road Infrastructure Geo Nodes')
    parser.add_argument('--create', '-c', action='store_true',
                        help='Create node groups only')
    parser.add_argument('--apply', '-a', action='store_true',
                        help='Apply to roads')
    parser.add_argument('--setup-styles', action='store_true',
                        help='Auto-apply styles based on road type')
    parser.add_argument('--light-spacing', type=float, default=30.0,
                        help='Global street light spacing (meters)')
    parser.add_argument('--sidewalk-width', type=float, default=2.0,
                        help='Global sidewalk width (meters)')
    parser.add_argument('--manhole-density', type=float, default=0.5,
                        help='Global manhole density factor')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CHARLOTTE ROAD INFRASTRUCTURE GEOMETRY NODES")
    print("=" * 60)

    if args.create:
        create_all_road_node_groups()
        print("\n✓ Node groups created")
        return

    # Apply with settings
    apply_geo_nodes_to_all_roads(
        global_light_spacing=args.light_spacing,
        global_sidewalk_width=args.sidewalk_width,
        global_manhole_density=args.manhole_density,
    )

    if args.setup_styles:
        setup_road_styles()

    # Print usage
    print("\n" + "=" * 60)
    print("ROAD STYLE PRESETS")
    print("=" * 60)

    for name, preset in ROAD_PRESETS.items():
        print(f"\n{name}:")
        print(f"  Light spacing: {preset['light_spacing']}m")
        print(f"  Sidewalk: {preset['sidewalk_width']}m {'(enabled)' if preset['sidewalk_enabled'] else '(disabled)'}")
        print(f"  Manhole density: {preset['manhole_density']}")

    print("\n" + "=" * 60)
    print("BLENDER PYTHON CONSOLE USAGE")
    print("=" * 60)
    print("""
# Set road style
set_road_style(bpy.data.objects["Road_Name"], "downtown")

# Override properties
set_road_override(bpy.data.objects["Road_Name"], "light_spacing", 20)
set_road_override(bpy.data.objects["Road_Name"], "sidewalk_width", 4)
set_road_override(bpy.data.objects["Road_Name"], "sidewalk_enabled", False)
set_road_override(bpy.data.objects["Road_Name"], "manhole_density", 0.8)

# Auto-setup all road styles
setup_road_styles()
""")


if __name__ == '__main__':
    main()
