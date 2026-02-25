"""
Charlotte Digital Twin - Crosswalk Generation Script

Run this in Blender after importing roads to generate crosswalks
at all detected intersections.
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.crosswalk_generator import generate_all_crosswalks, create_crosswalk_collection


def main():
    """Generate crosswalks for Charlotte roads."""
    print("\n" + "=" * 50)
    print("Charlotte Crosswalk Generation")
    print("=" * 50)

    # Create crosswalk assets
    print("\nCreating crosswalk assets...")
    create_crosswalk_collection()

    # Generate crosswalks at intersections
    crosswalks = generate_all_crosswalks()

    # Save
    output_path = 'output/charlotte_with_crosswalks.blend'
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\nSaved to {output_path}")

    print(f"\nCrosswalk generation complete! ({len(crosswalks)} crosswalks created)")


if __name__ == '__main__':
    main()
