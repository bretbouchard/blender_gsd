"""
Charlotte Digital Twin - Apply Smart Geometry Nodes

Applies Geometry Nodes to all buildings with a unified system that supports:
1. Global defaults (applied to all buildings)
2. Style presets (groups of settings)
3. Per-building overrides (via custom properties)

Usage:
    # Basic - apply with defaults
    blender charlotte.blend --python scripts/apply_geo_nodes.py

    # With custom global settings
    blender charlotte.blend --python scripts/apply_geo_nodes.py -- --density 0.002 --min-height 25

    # Also auto-apply style presets based on building types
    blender charlotte.blend --python scripts/apply_geo_nodes.py -- --setup-styles

After running, use Blender Python Console to customize:

    # Set a landmark building
    set_building_style(bpy.data.objects["Building_BOA_Corporate"], "landmark_tower")

    # Override specific property
    set_building_override(bpy.data.objects["Building_BOA_Corporate"], "rooftop_scale", 1.5)

    # Disable rooftop units for a specific building
    set_building_override(bpy.data.objects["Building_Historic"], "rooftop_enabled", False)
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_buildings import (
    apply_geo_nodes_to_all_buildings,
    set_building_style,
    set_building_override,
    clear_building_overrides,
    setup_all_styles,
    setup_landmark_buildings,
    setup_historic_buildings,
    setup_residential_buildings,
    BUILDING_PRESETS,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Smart Building Geo Nodes')
    parser.add_argument('--min-height', type=float, default=30.0,
                        help='Global minimum height for rooftop units')
    parser.add_argument('--density', type=float, default=0.001,
                        help='Global rooftop unit density')
    parser.add_argument('--scale', type=float, default=1.0,
                        help='Global rooftop unit scale')
    parser.add_argument('--setup-styles', action='store_true',
                        help='Auto-apply style presets based on building type')
    parser.add_argument('--create-only', action='store_true',
                        help='Only create node group, do not apply to buildings')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CHARLOTTE SMART GEOMETRY NODES")
    print("=" * 60)

    if args.create_only:
        # Just create the node group
        from lib.geo_nodes_buildings import create_rooftop_units_node_group
        create_rooftop_units_node_group()
        print("\n✓ Node group created (not applied to buildings)")
        return

    # Apply Geo Nodes with global defaults
    apply_geo_nodes_to_all_buildings(
        global_min_height=args.min_height,
        global_density=args.density,
        global_scale=args.scale,
    )

    # Optionally auto-setup styles
    if args.setup_styles:
        setup_all_styles()

    # Print usage guide
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
Available Style Presets:""")

    for name, preset in BUILDING_PRESETS.items():
        print(f"  {name}:")
        print(f"    rooftop_enabled: {preset['rooftop_enabled']}")
        print(f"    rooftop_density: {preset['rooftop_density']}")
        print(f"    window_pattern: {preset['window_pattern']}")

    print("""
In Blender Python Console:

    # Set building style
    set_building_style(bpy.data.objects["Building_Name"], "landmark_tower")

    # Override specific property
    set_building_override(bpy.data.objects["Building_Name"], "rooftop_scale", 1.5)

    # Disable rooftop units
    set_building_override(bpy.data.objects["Building_Name"], "rooftop_enabled", False)

    # Batch operations
    setup_landmark_buildings()   # Apply to known landmarks
    setup_historic_buildings()   # Apply to historic buildings
    setup_residential_buildings() # Apply to residential towers

To update ALL buildings globally:
    1. Open Shader Editor > Geometry Nodes
    2. Select "Building_Rooftop_Units" node group
    3. Edit nodes - changes affect all buildings
""")


if __name__ == '__main__':
    main()
