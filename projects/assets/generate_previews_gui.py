#!/usr/bin/env python3
"""
Generate Previews for KitBash3D Scene Files - GUI Mode Required

This script MUST be run in GUI mode (no --background).

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender --python generate_previews_gui.py

The script will:
1. Open the file
2. Generate previews for all asset objects
3. Save and quit
"""

import bpy
import sys
from pathlib import Path
import time

# Configuration
BLEND_FILE = Path("/Volumes/Storage/3d/kitbash/converted_assets/LA Downtown/LA Downtown_assets.blend")


def generate_previews():
    """Generate previews for all asset objects."""
    print("=" * 60)
    print("GENERATE PREVIEWS (GUI Mode)")
    print("=" * 60)

    # Open the file
    print(f"\nOpening: {BLEND_FILE.name}")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

    # Get mesh objects with asset data but no preview
    mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH' and o.asset_data]
    objects_without_preview = [o for o in mesh_objects if not o.preview]

    print(f"\nObjects with asset data: {len(mesh_objects)}")
    print(f"Objects without preview: {len(objects_without_preview)}")

    if not objects_without_preview:
        print("\nAll objects already have previews!")
        bpy.ops.wm.quit_blender()
        return

    # Generate previews
    print(f"\nGenerating previews for {len(objects_without_preview)} objects...")
    start_time = time.time()
    previews_generated = 0

    for i, obj in enumerate(objects_without_preview):
        try:
            # Select the object
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            # Generate preview
            bpy.ops.asset.generate_preview()
            previews_generated += 1

            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (len(objects_without_preview) - i - 1) / rate
                print(f"  Progress: {i+1}/{len(objects_without_preview)} ({previews_generated} previews)")
                print(f"  Elapsed: {elapsed:.0f}s, Est. remaining: {remaining:.0f}s")

        except Exception as e:
            print(f"  Error on {obj.name}: {e}")

        # Deselect
        obj.select_set(False)

    elapsed = time.time() - start_time
    print(f"\nGenerated {previews_generated} previews in {elapsed:.1f}s")

    # Save
    print(f"\nSaving...")
    bpy.ops.wm.save_mainfile(compress=True)
    print(f"  Saved to: {BLEND_FILE}")

    # Verify
    objects_with_preview_after = len([o for o in mesh_objects if o.preview])
    print(f"\nObjects with previews: {objects_with_preview_after}/{len(mesh_objects)}")

    print("\n" + "=" * 60)
    print("PREVIEW GENERATION COMPLETE")
    print("=" * 60)

    # Quit Blender
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    generate_previews()
