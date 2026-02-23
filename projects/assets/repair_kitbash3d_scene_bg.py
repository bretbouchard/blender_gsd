#!/usr/bin/env python3
"""
Repair KitBash3D Scene Files - Background Mode

For large scene files (like LA Downtown) that:
- Have objects marked as assets but NO previews (needs GUI)
- Have materials not marked as assets (can be done in background)
- Have external textures that need packing (can be done in background)

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender --background --python repair_kitbash3d_scene_bg.py
"""

import bpy
from pathlib import Path

# Configuration
BLEND_FILE = Path("/Volumes/Storage/3d/kitbash/converted_assets/LA Downtown/LA Downtown_assets.blend")
AUTHOR = "KitBash3D"


def repair_scene():
    """Repair the scene file (materials and textures only - no previews)."""
    print("=" * 60)
    print("REPAIR KITBASH3D SCENE (Background Mode)")
    print("=" * 60)

    # Open the file
    print(f"\nOpening: {BLEND_FILE.name}")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

    # Stats before
    mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH']
    objects_with_preview = len([o for o in mesh_objects if o.preview])
    objects_asset_marked = len([o for o in mesh_objects if o.asset_data])
    materials_asset_marked = len([m for m in bpy.data.materials if m.asset_data])

    print(f"\nBefore:")
    print(f"  Mesh objects: {len(mesh_objects)}")
    print(f"  Objects with asset data: {objects_asset_marked}")
    print(f"  Objects with previews: {objects_with_preview}")
    print(f"  Materials with asset data: {materials_asset_marked}")

    # Step 1: Mark materials as assets
    print(f"\n[1/2] Marking materials as assets...")
    materials_marked = 0
    for mat in bpy.data.materials:
        if mat.name in {"Material", "Dots Stroke", "None"}:
            continue
        if not mat.asset_data:
            try:
                mat.asset_mark()
                if mat.asset_data:
                    mat.asset_data.author = AUTHOR
                    mat.asset_data.description = f"LA Downtown material"
                    tag_name = "kitbash3d_la_downtown"
                    if tag_name not in [t.name for t in mat.asset_data.tags]:
                        mat.asset_data.tags.new(tag_name)
                materials_marked += 1
            except Exception as e:
                print(f"  Error on {mat.name}: {e}")

    print(f"  Marked {materials_marked} materials")

    # Step 2: Pack textures
    print(f"\n[2/2] Packing textures...")
    try:
        bpy.ops.file.pack_all()
        packed = len([i for i in bpy.data.images if i.packed_file])
        print(f"  Packed {packed} images")
    except Exception as e:
        print(f"  Pack error: {e}")

    # Save
    print(f"\nSaving...")
    bpy.ops.wm.save_mainfile(compress=True)
    print(f"  Saved to: {BLEND_FILE}")

    # Stats after
    materials_asset_after = len([m for m in bpy.data.materials if m.asset_data])
    packed_after = len([i for i in bpy.data.images if i.packed_file])

    print(f"\nAfter:")
    print(f"  Materials with asset data: {materials_asset_after}")
    print(f"  Packed images: {packed_after}")

    print("\n" + "=" * 60)
    print("NOTE: Preview generation requires GUI mode.")
    print("Run Blender without --background to generate previews.")
    print("=" * 60)


if __name__ == "__main__":
    repair_scene()
