#!/usr/bin/env python3
"""
Reconvert Corrupted Blend Files

Identifies corrupted 17-byte files and re-converts them from source.
Must run in GUI mode for preview generation.

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender --python reconvert_corrupted.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration
CONVERTED_ROOT = Path("/Volumes/Storage/3d/kitbash/converted_assets")
SOURCE_ROOT = Path("/Volumes/Storage/3d/kitbash/kpacks")
LOG_FILE = Path("reconvert_log.txt")

# Size threshold for corruption detection
CORRUPTED_SIZE = 17  # bytes


def find_corrupted_files(root: Path) -> list[Path]:
    """Find all corrupted (17-byte) .blend files."""
    corrupted = []
    for blend_file in root.rglob("*.blend"):
        if blend_file.stat().st_size == CORRUPTED_SIZE:
            corrupted.append(blend_file)
    return corrupted


def find_source_file(corrupted_path: Path, source_root: Path) -> Path | None:
    """
    Find the source FBX or OBJ file for a corrupted blend.

    Args:
        corrupted_path: Path like .../kpacks/KB 04 Frames/421_assets.blend
        source_root: Path to kpacks directory

    Returns:
        Path to source FBX/OBJ file or None if not found
    """
    # Get relative path parts
    rel_path = corrupted_path.relative_to(CONVERTED_ROOT)
    kit_name = rel_path.parts[1]  # e.g., "KB 04 Frames"
    asset_num = corrupted_path.stem.replace("_assets", "")  # e.g., "421"

    # Source directory
    source_dir = source_root / kit_name

    if not source_dir.exists():
        return None

    # Look for matching FBX or OBJ
    for ext in [".FBX", ".fbx", ".OBJ", ".obj"]:
        source_file = source_dir / f"{asset_num}{ext}"
        if source_file.exists():
            return source_file

    return None


def reconvert_file(
    source_path: Path,
    output_path: Path,
    log_file,
) -> bool:
    """
    Re-convert a single source file to blend.

    Returns True on success.
    """
    import bpy

    # Clear existing data
    bpy.ops.wm.read_homefile(app_template="", use_empty=True)

    kit_name = source_path.parent.name
    asset_name = source_path.stem

    try:
        # Import based on extension
        if source_path.suffix.lower() == '.fbx':
            bpy.ops.import_scene.fbx(filepath=str(source_path))
        elif source_path.suffix.lower() == '.obj':
            try:
                bpy.ops.wm.obj_import(filepath=str(source_path))
            except AttributeError:
                bpy.ops.import_scene.obj(filepath=str(source_path))
        elif source_path.suffix.lower() in ['.glb', '.gltf']:
            bpy.ops.import_scene.gltf(filepath=str(source_path))
        else:
            log_file.write(f"  [SKIP] Unknown format: {source_path}\n")
            return False

        # Mark all meshes as assets
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                try:
                    obj.asset_mark()
                    if obj.asset_data:
                        obj.asset_data.author = "KitBash3D"
                        obj.asset_data.description = f"{kit_name} - {obj.name}"
                        tag_name = f"kpacks_{kit_name.lower().replace(' ', '_').replace('-', '_')}"
                        if tag_name not in [t.name for t in obj.asset_data.tags]:
                            obj.asset_data.tags.new(tag_name)
                except Exception:
                    pass

        # Mark all used materials as assets
        for mat in bpy.data.materials:
            if mat.name in {"Material", "Dots Stroke", "None"}:
                continue
            if mat.users > 0:
                try:
                    mat.asset_mark()
                    if mat.asset_data:
                        mat.asset_data.author = "KitBash3D"
                        mat.asset_data.description = f"{kit_name} material"
                        tag_name = f"kpacks_{kit_name.lower().replace(' ', '_').replace('-', '_')}"
                        if tag_name not in [t.name for t in mat.asset_data.tags]:
                            mat.asset_data.tags.new(tag_name)
                except Exception:
                    pass

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)

        log_file.write(f"  [OK] {output_path.name}\n")
        return True

    except Exception as e:
        log_file.write(f"  [FAIL] {source_path.name}: {e}\n")
        return False


def main():
    print("=" * 60)
    print("RECONVERT CORRUPTED FILES")
    print("=" * 60)

    # Find corrupted files
    print("\nScanning for corrupted files...")
    corrupted = find_corrupted_files(CONVERTED_ROOT)
    print(f"Found {len(corrupted)} corrupted files (17 bytes)")

    if not corrupted:
        print("No corrupted files found. Nothing to do.")
        return

    # Open log file
    with open(LOG_FILE, 'w') as log:
        log.write(f"Reconvert Log - {datetime.now().isoformat()}\n")
        log.write(f"Total corrupted files: {len(corrupted)}\n")
        log.write("=" * 60 + "\n\n")

        success_count = 0
        fail_count = 0
        skip_count = 0

        for i, corrupted_path in enumerate(corrupted):
            print(f"\n[{i+1}/{len(corrupted)}] Processing: {corrupted_path.name}")

            # Find source file
            source_path = find_source_file(corrupted_path, SOURCE_ROOT)

            if source_path is None:
                log.write(f"[SKIP] No source found for: {corrupted_path}\n")
                skip_count += 1
                continue

            log.write(f"Converting: {source_path.name}\n")

            # Reconvert
            if reconvert_file(source_path, corrupted_path, log):
                success_count += 1
            else:
                fail_count += 1

        # Summary
        log.write("\n" + "=" * 60 + "\n")
        log.write("SUMMARY\n")
        log.write(f"  Success: {success_count}\n")
        log.write(f"  Failed:  {fail_count}\n")
        log.write(f"  Skipped: {skip_count}\n")

    print("\n" + "=" * 60)
    print("COMPLETE")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Skipped: {skip_count}")
    print(f"\nLog saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
