#!/usr/bin/env python3
"""
Generate Asset Previews - Simple Single-File Version

This script generates previews for ONE blend file at a time.
Run it while you have the file open in Blender.

Usage:
    1. Open a converted blend file (e.g., Aftermath_assets.blend)
    2. Go to Scripting workspace
    3. Open this script
    4. Click Run (Alt+P)
    5. Watch the status bar for progress
    6. Save the file when done (Cmd+S)
"""

import bpy


def has_preview(obj) -> bool:
    """Check if object has a valid preview."""
    try:
        return obj.preview is not None and obj.preview.image_size[0] > 0
    except:
        return False


def generate_previews_current_file():
    """Generate previews for all assets in the current file."""

    generated = 0
    skipped = 0
    errors = 0

    print("\n" + "=" * 50)
    print("Generating Asset Previews")
    print("=" * 50)

    # Get all objects with asset data
    asset_objects = [obj for obj in bpy.data.objects if obj.asset_data]
    asset_materials = [mat for mat in bpy.data.materials if mat.asset_data]
    asset_collections = [coll for coll in bpy.data.collections if coll.asset_data]

    total = len(asset_objects) + len(asset_materials) + len(asset_collections)
    print(f"Found {total} assets to check\n")

    # Process objects
    for i, obj in enumerate(asset_objects):
        print(f"[{i+1}/{len(asset_objects)}] {obj.name[:40]}...", end=" ")

        if has_preview(obj):
            print("exists")
            skipped += 1
            continue

        # Select and make active
        try:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Generate preview
            bpy.ops.asset.generate_preview()
            print("GENERATED")
            generated += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    # Process materials
    for i, mat in enumerate(asset_materials):
        print(f"[Material {i+1}/{len(asset_materials)}] {mat.name[:40]}...", end=" ")

        if has_preview(mat):
            print("exists")
            skipped += 1
            continue

        try:
            # Materials work with context override
            with bpy.context.temp_override(id=mat):
                bpy.ops.asset.generate_preview()
            print("GENERATED")
            generated += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    # Process collections
    for i, coll in enumerate(asset_collections):
        print(f"[Collection {i+1}/{len(asset_collections)}] {coll.name[:40]}...", end=" ")

        if has_preview(coll):
            print("exists")
            skipped += 1
            continue

        try:
            with bpy.context.temp_override(id=coll):
                bpy.ops.asset.generate_preview()
            print("GENERATED")
            generated += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Generated: {generated}")
    print(f"Already existed: {skipped}")
    print(f"Errors: {errors}")
    print(f"Total: {total}")

    if generated > 0:
        print("\n>>> Remember to SAVE the file! (Cmd+S)")

    return generated, skipped, errors


# Run it
if __name__ == "__main__":
    generate_previews_current_file()
