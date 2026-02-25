"""
Charlotte Digital Twin - Geometry Nodes Road Setup

Run this in Blender after importing road curves to set up
geometry nodes for procedural road building.
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.geo_nodes_road import setup_road_geometry_nodes


def main():
    """Setup geometry nodes for Charlotte roads."""
    print("\n" + "=" * 50)
    print("Charlotte Geometry Nodes Setup")
    print("=" * 50)

    setup_road_geometry_nodes()

    # Save
    output_path = 'output/charlotte_roads_geo_nodes.blend'
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\nSaved to {output_path}")

    print("\nGeometry nodes setup complete!")


if __name__ == '__main__':
    main()
