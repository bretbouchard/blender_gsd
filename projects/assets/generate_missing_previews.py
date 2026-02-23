#!/usr/bin/env python3
"""
Generate missing asset previews for converted assets.

Run this AFTER conversion to add thumbnails to assets that are missing them.
This avoids re-converting everything.

Usage:
    blender --background --python generate_missing_previews.py

Or run in Blender GUI:
    Open this file in Scripting workspace and click Run
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def generate_previews_for_file(blend_path: Path) -> tuple[int, int]:
    """
    Generate previews for assets in a blend file.

    Returns:
        (previews_generated, total_assets)
    """
    import bpy

    # Open the file
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    generated = 0
    total = 0

    # Check all asset types
    for obj in bpy.data.objects:
        if obj.asset_data:
            total += 1
            if not obj.preview:
                try:
                    bpy.ops.asset.generate_preview({"id": obj})
                    generated += 1
                except Exception as e:
                    print(f"  Error generating preview for {obj.name}: {e}")

    for mat in bpy.data.materials:
        if mat.asset_data:
            total += 1
            if not mat.preview:
                try:
                    bpy.ops.asset.generate_preview({"id": mat})
                    generated += 1
                except Exception as e:
                    print(f"  Error generating preview for {mat.name}: {e}")

    for coll in bpy.data.collections:
        if coll.asset_data:
            total += 1
            if not coll.preview:
                try:
                    bpy.ops.asset.generate_preview({"id": coll})
                    generated += 1
                except Exception as e:
                    print(f"  Error generating preview for {coll.name}: {e}")

    # Save if we generated any previews
    if generated > 0:
        bpy.ops.wm.save_mainfile()

    return generated, total


def generate_all_missing_previews():
    """Generate previews for all converted asset libraries."""

    # Define your converted asset directories
    asset_roots = [
        Path("/Volumes/Storage/3d/kitbash/converted_assets"),
        Path("/Volumes/Storage/3d/animation/converted_assets"),
        Path("/Volumes/Storage/3d/plugins/converted_assets"),
    ]

    print("=" * 60)
    print("Asset Preview Generator")
    print("=" * 60)

    total_generated = 0
    total_assets = 0
    files_processed = 0

    for asset_root in asset_roots:
        if not asset_root.exists():
            print(f"\nSkipping {asset_root} (not found)")
            continue

        print(f"\nScanning {asset_root}...")

        # Find all blend files
        blend_files = list(asset_root.rglob("*.blend"))
        blend_files = [f for f in blend_files if not any(x in f.suffixes for x in [".blend1", ".blend2"])]

        print(f"Found {len(blend_files)} blend files")

        for i, blend_file in enumerate(blend_files, 1):
            rel_path = blend_file.relative_to(asset_root)
            print(f"  [{i}/{len(blend_files)}] {rel_path}...", end=" ", flush=True)

            try:
                generated, total = generate_previews_for_file(blend_file)
                total_generated += generated
                total_assets += total
                files_processed += 1

                if generated > 0:
                    print(f"generated {generated}/{total} previews")
                else:
                    print(f"all {total} previews exist")

            except Exception as e:
                print(f"ERROR: {e}")

    print()
    print("=" * 60)
    print("Preview Generation Summary")
    print("=" * 60)
    print(f"Files processed: {files_processed}")
    print(f"Total assets checked: {total_assets}")
    print(f"Previews generated: {total_generated}")


def generate_previews_current_file():
    """
    Generate previews for assets in the currently open Blender file.

    Run this in the GUI when you have a file open.
    """
    import bpy

    generated = 0
    total = 0

    print("\nGenerating previews for current file...")

    for obj in bpy.data.objects:
        if obj.asset_data:
            total += 1
            if not obj.preview:
                try:
                    bpy.ops.asset.generate_preview({"id": obj})
                    generated += 1
                    print(f"  Generated: {obj.name}")
                except Exception as e:
                    print(f"  Error: {obj.name} - {e}")

    for mat in bpy.data.materials:
        if mat.asset_data:
            total += 1
            if not mat.preview:
                try:
                    bpy.ops.asset.generate_preview({"id": mat})
                    generated += 1
                    print(f"  Generated: {mat.name}")
                except Exception as e:
                    print(f"  Error: {mat.name} - {e}")

    for coll in bpy.data.collections:
        if coll.asset_data:
            total += 1
            if not coll.preview:
                try:
                    bpy.ops.asset.generate_preview({"id": coll})
                    generated += 1
                    print(f"  Generated: {coll.name}")
                except Exception as e:
                    print(f"  Error: {coll.name} - {e}")

    print(f"\nDone! Generated {generated}/{total} previews")

    if generated > 0:
        bpy.ops.wm.save_mainfile()
        print("File saved.")


if __name__ == "__main__":
    import bpy

    # Check if we're in background mode (CLI) or GUI
    if bpy.app.background:
        # Running from command line - process all files
        generate_all_missing_previews()
    else:
        # Running in GUI - just do current file
        generate_previews_current_file()
