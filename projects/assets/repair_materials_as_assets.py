#!/usr/bin/env python3
"""
Repair Script: Mark Materials as Assets in Existing Converted Files

This script repairs existing converted .blend files by:
1. Opening each file
2. Marking all used materials as assets (skipping defaults)
3. Adding proper metadata (author, description, tags)
4. Saving the file

IMPORTANT: This must be run in GUI mode, NOT background mode!
The asset preview generation requires OpenGL context.

Usage:
    # Run in Blender GUI (open Blender first, then run script)
    # In Script Editor: Open this file and click Run

    # Or from command line with GUI:
    blender --python repair_materials_as_assets.py

    # Process specific directory:
    blender --python repair_materials_as_assets.py -- --dir "/path/to/assets"

Output:
    - Updates all .blend files in place
    - Logs progress to repair_materials_log.txt
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# Try to import bpy - will fail if not running in Blender
try:
    import bpy
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False
    print("ERROR: This script must be run inside Blender!")
    print("Usage: blender --python repair_materials_as_assets.py")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default root directory to process
DEFAULT_ROOT = "/Volumes/Storage/3d/kitbash/converted_assets"

# Materials to skip (default Blender materials)
SKIP_MATERIALS = {"Material", "Dots Stroke", "None", "Material.001"}

# Log file
LOG_FILE = Path(__file__).parent / "repair_materials_log.txt"


# =============================================================================
# REPAIR FUNCTIONS
# =============================================================================

def get_category_from_path(file_path: Path) -> str:
    """Extract category name from file path."""
    parts = file_path.parts
    try:
        # Find 'converted_assets' in path and get next part
        idx = parts.index("converted_assets")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return "unknown"


def repair_file(file_path: Path, log_file) -> dict:
    """
    Repair a single .blend file by marking materials as assets.

    Returns dict with results.
    """
    result = {
        "file": str(file_path),
        "materials_found": 0,
        "materials_marked": 0,
        "materials_skipped": 0,
        "errors": [],
    }

    try:
        # Open the file
        bpy.ops.wm.open_mainfile(filepath=str(file_path))

        category = get_category_from_path(file_path)
        tag_name = f"{category.lower().replace(' ', '_').replace('-', '_')}"

        # Process all materials
        for mat in bpy.data.materials:
            result["materials_found"] += 1

            # Skip default materials
            if mat.name in SKIP_MATERIALS:
                result["materials_skipped"] += 1
                continue

            # Skip if already an asset
            if mat.asset_data is not None:
                result["materials_skipped"] += 1
                continue

            # Only mark used materials
            if mat.users <= 0:
                result["materials_skipped"] += 1
                continue

            try:
                # Mark as asset
                mat.asset_mark()

                if mat.asset_data:
                    # Set metadata
                    mat.asset_data.author = "KitBash3D"
                    mat.asset_data.description = f"{category} material"

                    # Add tag
                    if tag_name not in [t.name for t in mat.asset_data.tags]:
                        mat.asset_data.tags.new(tag_name)

                    # Generate preview (this requires GUI!)
                    if not mat.preview:
                        try:
                            bpy.ops.asset.generate_preview({"id": mat})
                        except Exception:
                            pass  # Preview generation may fail in some contexts

                result["materials_marked"] += 1

            except Exception as e:
                result["errors"].append(f"Material '{mat.name}': {e}")

        # Save if we made changes
        if result["materials_marked"] > 0:
            bpy.ops.wm.save_mainfile()

    except Exception as e:
        result["errors"].append(f"File error: {e}")

    return result


def repair_directory(directory: Path, log_file, max_files: int = None) -> dict:
    """
    Repair all .blend files in a directory.

    Returns summary dict.
    """
    summary = {
        "files_processed": 0,
        "files_with_changes": 0,
        "total_materials_found": 0,
        "total_materials_marked": 0,
        "total_errors": 0,
        "start_time": datetime.now(),
    }

    # Find all .blend files
    blend_files = list(directory.rglob("*.blend"))
    blend_files = [f for f in blend_files if ".blend1" not in f.name and ".blend2" not in f.name]

    if max_files:
        blend_files = blend_files[:max_files]

    print(f"\nFound {len(blend_files)} .blend files to process\n")

    for i, blend_file in enumerate(blend_files, 1):
        rel_path = blend_file.relative_to(directory) if blend_file.is_relative_to(directory) else blend_file
        print(f"[{i}/{len(blend_files)}] {rel_path}...", end=" ", flush=True)

        result = repair_file(blend_file, log_file)

        summary["files_processed"] += 1
        summary["total_materials_found"] += result["materials_found"]
        summary["total_materials_marked"] += result["materials_marked"]

        if result["materials_marked"] > 0:
            summary["files_with_changes"] += 1

        if result["errors"]:
            summary["total_errors"] += len(result["errors"])
            print(f"ERRORS: {len(result['errors'])}")
            for err in result["errors"]:
                log_file.write(f"  ERROR: {err}\n")
        else:
            print(f"+{result['materials_marked']} materials")

        # Log result
        log_file.write(f"{rel_path}: found={result['materials_found']}, marked={result['materials_marked']}, skipped={result['materials_skipped']}\n")
        log_file.flush()

    summary["end_time"] = datetime.now()
    summary["duration"] = summary["end_time"] - summary["start_time"]

    return summary


def repair_single_current_file():
    """
    Repair the currently open Blender file.
    Use this when you manually open a file and run the script.
    """
    if not bpy.data.filepath:
        print("ERROR: No file is currently open!")
        return

    file_path = Path(bpy.data.filepath)
    category = get_category_from_path(file_path)
    tag_name = f"{category.lower().replace(' ', '_').replace('-', '_')}"

    print(f"\nRepairing: {file_path.name}")
    print(f"Category: {category}")
    print()

    marked = 0
    skipped = 0

    for mat in bpy.data.materials:
        if mat.name in SKIP_MATERIALS:
            skipped += 1
            continue

        if mat.asset_data is not None:
            skipped += 1
            continue

        if mat.users <= 0:
            skipped += 1
            continue

        try:
            mat.asset_mark()
            if mat.asset_data:
                mat.asset_data.author = "KitBash3D"
                mat.asset_data.description = f"{category} material"
                if tag_name not in [t.name for t in mat.asset_data.tags]:
                    mat.asset_data.tags.new(tag_name)
                if not mat.preview:
                    bpy.ops.asset.generate_preview({"id": mat})
            marked += 1
            print(f"  ✓ Marked: {mat.name}")
        except Exception as e:
            print(f"  ✗ Error: {mat.name} - {e}")

    print()
    print(f"Marked {marked} materials as assets ({skipped} skipped)")

    if marked > 0:
        bpy.ops.wm.save_mainfile()
        print("File saved!")


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Repair materials as assets")
    parser.add_argument("--dir", "-d", default=DEFAULT_ROOT, help="Directory to process")
    parser.add_argument("--file", "-f", help="Process single file instead of directory")
    parser.add_argument("--max", "-m", type=int, help="Maximum files to process")
    parser.add_argument("--current", "-c", action="store_true", help="Repair currently open file only")
    args, _ = parser.parse_known_args()

    # Repair current file only
    if args.current:
        repair_single_current_file()
        return

    # Single file mode
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ERROR: File not found: {file_path}")
            return

        with open(LOG_FILE, "w") as log:
            result = repair_file(file_path, log)
            print(f"Marked {result['materials_marked']} materials")
            if result['errors']:
                for err in result['errors']:
                    print(f"  ERROR: {err}")
        return

    # Directory mode
    directory = Path(args.dir)
    if not directory.exists():
        print(f"ERROR: Directory not found: {directory}")
        return

    print("=" * 60)
    print("MATERIAL ASSET REPAIR SCRIPT")
    print("=" * 60)
    print(f"Directory: {directory}")
    print(f"Log file: {LOG_FILE}")
    print()

    with open(LOG_FILE, "w") as log:
        log.write(f"Material Repair Log - {datetime.now()}\n")
        log.write("=" * 60 + "\n\n")

        summary = repair_directory(directory, log, max_files=args.max)

        # Print summary
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Files processed: {summary['files_processed']}")
        print(f"Files with changes: {summary['files_with_changes']}")
        print(f"Materials found: {summary['total_materials_found']}")
        print(f"Materials marked as assets: {summary['total_materials_marked']}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Duration: {summary['duration']}")
        print()
        print(f"Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
