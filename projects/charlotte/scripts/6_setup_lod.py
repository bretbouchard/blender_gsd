"""
Charlotte Digital Twin - LOD Setup Script

Run this in Blender after importing buildings and roads
to organize them into LOD collections.
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.lod_system import LODOrganizer, setup_visibility_toggles


def main():
    """Setup LOD system for Charlotte scene."""
    print("\n" + "=" * 50)
    print("Charlotte LOD Setup")
    print("=" * 50)

    # Create LOD organization
    organizer = LODOrganizer()
    organizer.organize_all()

    # Setup visibility toggles
    setup_visibility_toggles()

    # Save
    output_path = 'output/charlotte.blend'
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\nSaved to {output_path}")

    print("\nLOD setup complete!")


if __name__ == '__main__':
    main()
