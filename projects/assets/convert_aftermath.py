#!/usr/bin/env blender --python
"""
KitBash3D Pack Converter - Aftermath Edition

Converts the KitBash3D Aftermath pack to Blender Asset Browser format.

Usage:
    blender --background --python convert_aftermath.py
"""

import sys
from pathlib import Path

# Add the lib directory to path
# This script is at: projects/assets/convert_aftermath.py
# Project root is: blender_gsd/
_script_path = Path(__file__).resolve()
_project_root = _script_path.parent.parent.parent  # Go up to blender_gsd
sys.path.insert(0, str(_project_root))
print(f"Project root: {_project_root}")

from lib.assets import KitBashConverter, ConversionResult

# Paths
SOURCE_DIR = Path("/Volumes/Storage/3d/kitbash/KitBash3D - Aftermath")
OUTPUT_DIR = Path("/Volumes/Storage/3d/kitbash/converted_assets/Aftermath")


def main():
    """Convert the Aftermath pack."""
    print("=" * 50)
    print("Converting KitBash3D Aftermath Pack")
    print("=" * 50)

    if not SOURCE_DIR.exists():
        print(f"Error: Source directory not found: {SOURCE_DIR}")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run conversion
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    converter = KitBashConverter()

    # Scan pack first
    print("Scanning pack...")
    info = converter.scan_pack(SOURCE_DIR)
    print(f"  OBJ: {info.obj_file}")
    print(f"  Textures: {info.texture_dir}")
    print(f"  Materials: {len(info.material_names)}")
    print()

    # Run conversion
    print("Converting...")
    result = converter.convert_pack(
        pack_name="Aftermath",
        source_dir=SOURCE_DIR,
        output_dir=OUTPUT_DIR,
        split_by_material=True,
        generate_previews=False,  # Faster for testing
    )

    # Print results
    print()
    print("=" * 50)
    if result.is_success():
        print("✓ Conversion Complete!")
        print(f"  Objects created: {result.objects_created}")
        print(f"  Materials created: {result.materials_created}")
        print(f"  Output: {result.output_path}")
    else:
        print("✗ Conversion Failed")
        for error in result.errors:
            print(f"  Error: {error}")

    for warning in result.warnings:
        print(f"  Warning: {warning}")

    print("=" * 50)


if __name__ == "__main__":
    try:
        import bpy
        print("Running in Blender")
        main()
    except ImportError:
        print("Error: This script must be run with Blender:")
        print("  /Applications/Blender.app/Contents/MacOS/Blender --background --python convert_aftermath.py")
        sys.exit(1)
