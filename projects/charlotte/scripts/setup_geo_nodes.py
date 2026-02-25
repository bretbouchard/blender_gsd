"""
Charlotte Digital Twin - Building Geometry Nodes Setup

Creates and applies TRUE Geometry Nodes for procedural building details.
These are non-destructive, adjustable modifiers.

Usage:
    # Create node groups only
    blender charlotte.blend --python scripts/setup_geo_nodes.py -- --create

    # Create and apply to all buildings
    blender charlotte.blend --python scripts/setup_geo_nodes.py

    # Apply with custom settings
    blender charlotte.blend --python scripts/setup_geo_nodes.py -- --min-height 20

After running, adjust parameters in Blender's modifier panel:
    - Select any building with the modifier
    - Adjust Seed, Min Height, Density, Scale
    - Changes propagate to all buildings using the same node group
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_rooftop import (
    create_rooftop_units_node_group_v2,
    apply_rooftop_modifier_to_buildings,
    create_all_node_groups,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Setup Building Geo Nodes')
    parser.add_argument('--create', '-c', action='store_true',
                        help='Only create node groups, do not apply')
    parser.add_argument('--apply', '-a', action='store_true',
                        help='Apply modifiers to buildings')
    parser.add_argument('--min-height', type=float, default=30.0,
                        help='Minimum building height for rooftop units')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CHARLOTTE BUILDING GEOMETRY NODES")
    print("=" * 60)

    if args.create:
        # Only create node groups
        create_all_node_groups()
        print("\n✓ Node groups created")
        print("  Apply manually via: Add Modifier > Geometry Nodes > Building_Rooftop_Units")

    elif args.apply:
        # Only apply (assumes groups exist)
        apply_rooftop_modifier_to_buildings(min_height=args.min_height)

    else:
        # Default: create and apply
        create_all_node_groups()
        apply_rooftop_modifier_to_buildings(min_height=args.min_height)
        print("\n✓ Setup complete!")
        print("\nTo adjust all buildings at once:")
        print("  1. Open Shader Editor > Geometry Nodes")
        print("  2. Select 'Building_Rooftop_Units' node group")
        print("  3. Changes affect ALL buildings with this modifier")


if __name__ == '__main__':
    main()
