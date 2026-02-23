#!/usr/bin/env blender --python
"""
Test script to verify the KitBash conversion module imports correctly.
"""

import sys
from pathlib import Path

# Add project root to path - go up 2 levels from this script
# This script is at: projects/assets/test_import.py
# Project root is: blender_gsd/
_script_path = Path(__file__).resolve()
_project_root = _script_path.parent.parent.parent  # Go up to blender_gsd
sys.path.insert(0, str(_project_root))
print(f"Added to path: {_project_root}")

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")

    try:
        from lib.assets import KitBashConverter, ConversionResult
        print("  ✓ KitBashConverter imported")
    except ImportError as e:
        print(f"  ✗ Failed to import KitBashConverter: {e}")
        return False

    try:
        from lib.assets import PBRMaterialBuilder, TextureSet
        print("  ✓ PBRMaterialBuilder imported")
    except ImportError as e:
        print(f"  ✗ Failed to import PBRMaterialBuilder: {e}")
        return False

    try:
        from lib.assets.material_builder import TEXTURE_PATTERNS
        print(f"  ✓ Texture patterns loaded ({len(TEXTURE_PATTERNS)} types)")
    except ImportError as e:
        print(f"  ✗ Failed to import texture patterns: {e}")
        return False

    return True


def test_scan_pack():
    """Test scanning a KitBash pack."""
    print("\nTesting pack scan...")

    from lib.assets import KitBashConverter

    converter = KitBashConverter()
    pack_path = Path("/Volumes/Storage/3d/kitbash/KitBash3D - Aftermath")

    if not pack_path.exists():
        print(f"  ✗ Pack path not found: {pack_path}")
        return False

    info = converter.scan_pack(pack_path)

    print(f"  Pack: {info.name}")
    print(f"  OBJ file: {info.obj_file}")
    print(f"  FBX file: {info.fbx_file}")
    print(f"  Textures: {info.texture_dir}")
    print(f"  Materials found: {len(info.material_names)}")
    if info.material_names:
        print(f"    - {', '.join(info.material_names[:5])}...")

    return info.has_source()


def main():
    print("=" * 50)
    print("KitBash Conversion Module Test")
    print("=" * 50)

    # Test imports
    if not test_imports():
        print("\n✗ Import tests failed")
        return

    # Test pack scanning
    if not test_scan_pack():
        print("\n✗ Pack scan failed")
        return

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    try:
        import bpy
        print("Running in Blender")
    except ImportError:
        print("Warning: Not running in Blender, some features unavailable")

    main()
