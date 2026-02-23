#!/usr/bin/env python3
"""
Inspect LA Downtown blend file to check asset status.

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender --python inspect_la_downtown.py
"""

import bpy
from pathlib import Path

BLEND_FILE = Path("/Volumes/Storage/3d/kitbash/converted_assets/LA Downtown/LA Downtown_assets.blend")


def inspect_file():
    """Open the file and check asset status."""
    print("=" * 60)
    print("INSPECTING LA Downtown_assets.blend")
    print("=" * 60)

    # Open the file
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

    # Count objects
    total_objects = len(bpy.data.objects)
    mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH']
    asset_objects = [o for o in mesh_objects if o.asset_data is not None]

    print(f"\n=== OBJECTS ===")
    print(f"Total objects: {total_objects}")
    print(f"Mesh objects: {len(mesh_objects)}")
    print(f"Objects marked as assets: {len(asset_objects)}")

    # Count materials
    total_materials = len(bpy.data.materials)
    asset_materials = [m for m in bpy.data.materials if m.asset_data is not None]

    print(f"\n=== MATERIALS ===")
    print(f"Total materials: {total_materials}")
    print(f"Materials marked as assets: {len(asset_materials)}")

    # Check collections
    print(f"\n=== COLLECTIONS ===")
    print(f"Total collections: {len(bpy.data.collections)}")
    for coll in bpy.data.collections[:10]:
        print(f"  {coll.name}: {len(coll.objects)} objects")

    # Sample objects without asset data
    non_asset_meshes = [o for o in mesh_objects if o.asset_data is None]
    if non_asset_meshes:
        print(f"\n=== SAMPLE OBJECTS WITHOUT ASSET DATA ({len(non_asset_meshes)}) ===")
        for obj in non_asset_meshes[:5]:
            print(f"  {obj.name}")

    # Sample objects with asset data
    if asset_objects:
        print(f"\n=== SAMPLE OBJECTS WITH ASSET DATA ({len(asset_objects)}) ===")
        for obj in asset_objects[:5]:
            has_preview = "YES" if obj.preview else "NO"
            print(f"  {obj.name} - Preview: {has_preview}")

    # Check if packed textures
    print(f"\n=== TEXTURES ===")
    packed = len([i for i in bpy.data.images if i.packed_file])
    total_images = len(bpy.data.images)
    print(f"Total images: {total_images}")
    print(f"Packed images: {packed}")


if __name__ == "__main__":
    inspect_file()
