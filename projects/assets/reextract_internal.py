#!/usr/bin/env python3
"""
Re-Extract Remaining Corrupted Files from Internal Drive

Reads source from /tmp/kpacks_source (internal drive)
Writes output to /tmp/kpacks_output (internal drive)
Then copies completed files to external drive

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender --python reextract_internal.py
"""

from __future__ import annotations

import os
import sys
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration - Use internal drive for speed
SOURCE_ROOT = Path("/tmp/kpacks_source")  # Internal drive (fast)
OUTPUT_TEMP = Path("/tmp/kpacks_output")   # Internal drive (fast)
CONVERTED_ROOT = Path("/Volumes/Storage/3d/kitbash/converted_assets/kpacks")  # External (final)
LOG_FILE = Path(PROJECT_ROOT / "projects/assets/reextract_internal_log.txt")
CORRUPTED_SIZE = 17  # bytes


@dataclass
class ExtractionResult:
    """Result of extracting assets from a blend file."""
    source_file: str
    output_path: Path | None = None
    objects_extracted: int = 0
    materials_found: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def is_success(self) -> bool:
        return self.output_path is not None and len(self.errors) == 0


def find_corrupted_files(root: Path) -> list[Path]:
    """Find all corrupted (17-byte) .blend files."""
    corrupted = []
    for blend_file in root.rglob("*.blend"):
        if blend_file.stat().st_size == CORRUPTED_SIZE:
            corrupted.append(blend_file)
    return corrupted


def find_source_file(corrupted_path: Path, source_root: Path) -> Path | None:
    """
    Find the source .blend file for a corrupted output.
    """
    rel_path = corrupted_path.relative_to(CONVERTED_ROOT)
    kit_name = rel_path.parts[0]
    asset_stem = corrupted_path.stem.replace("_assets", "")

    source_file = source_root / kit_name / f"{asset_stem}.blend"

    if source_file.exists():
        return source_file

    return None


def extract_blend_file(
    source_blend: Path,
    output_path: Path,
    collection_name: str,
    author: str = "KitBash3D",
) -> ExtractionResult:
    """Extract assets from a blend file and mark them as assets."""
    import bpy

    result = ExtractionResult(source_file=str(source_blend))

    if not source_blend.exists():
        result.errors.append(f"Blend file not found: {source_blend}")
        return result

    # Start fresh
    bpy.ops.wm.read_homefile(app_template="")

    # Append all collections, objects, and materials
    try:
        with bpy.data.libraries.load(str(source_blend)) as (data_from, data_to):
            data_to.collections = data_from.collections
            data_to.objects = data_from.objects
            data_to.materials = data_from.materials
    except Exception as e:
        result.errors.append(f"Failed to load library: {e}")
        return result

    # Link collections to scene
    for coll in data_to.collections:
        if coll and coll.name not in bpy.context.scene.collection.children:
            try:
                bpy.context.scene.collection.children.link(coll)
            except Exception:
                pass

    # Track objects already in collections
    linked_object_names = set()
    for coll in bpy.data.collections:
        for obj in coll.all_objects:
            linked_object_names.add(obj.name)

    # Link orphaned objects to scene
    scene_collection = bpy.context.scene.collection
    for obj in data_to.objects:
        if obj and obj.type == "MESH":
            if obj.name not in linked_object_names:
                try:
                    if obj.name not in scene_collection.objects:
                        scene_collection.objects.link(obj)
                except Exception:
                    pass

    # Mark all mesh objects as assets
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            try:
                obj.asset_mark()
                if obj.asset_data:
                    obj.asset_data.author = author
                    obj.asset_data.description = f"kpacks {collection_name} asset"

                    tag_name = f"kpacks_{collection_name.lower().replace(' ', '_').replace('-', '_')}"
                    if tag_name not in [t.name for t in obj.asset_data.tags]:
                        obj.asset_data.tags.new(tag_name)

                    if not obj.preview:
                        try:
                            bpy.ops.asset.generate_preview({"id": obj})
                        except Exception:
                            pass

                result.objects_extracted += 1
            except Exception:
                pass

    # Mark all used materials as assets
    materials_marked = 0
    for mat in bpy.data.materials:
        if mat.name in {"Material", "Dots Stroke", "None"}:
            continue
        if mat.users > 0:
            try:
                mat.asset_mark()
                if mat.asset_data:
                    mat.asset_data.author = author
                    mat.asset_data.description = f"kpacks {collection_name} material"

                    tag_name = f"kpacks_{collection_name.lower().replace(' ', '_').replace('-', '_')}"
                    if tag_name not in [t.name for t in mat.asset_data.tags]:
                        mat.asset_data.tags.new(tag_name)

                    if not mat.preview:
                        try:
                            bpy.ops.asset.generate_preview({"id": mat})
                        except Exception:
                            pass

                materials_marked += 1
            except Exception:
                pass

    result.materials_found = materials_marked

    # Pack textures
    try:
        bpy.ops.file.pack_all()
    except Exception:
        pass

    # Save to temp location (internal drive)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True)
        result.output_path = output_path
    except Exception as e:
        result.errors.append(f"Failed to save: {e}")

    return result


def main():
    print("=" * 60)
    print("RE-EXTRACT FROM INTERNAL DRIVE")
    print("=" * 60)

    # Create temp output directory
    OUTPUT_TEMP.mkdir(parents=True, exist_ok=True)

    # Find corrupted files
    print("\nScanning for corrupted files...")
    corrupted = find_corrupted_files(CONVERTED_ROOT)
    print(f"Found {len(corrupted)} corrupted files (17 bytes)")

    if not corrupted:
        print("No corrupted files found. Nothing to do.")
        return

    # Open log file
    with open(LOG_FILE, 'w') as log:
        log.write(f"Re-Extract (Internal) Log - {datetime.now().isoformat()}\n")
        log.write(f"Total corrupted files: {len(corrupted)}\n")
        log.write("=" * 60 + "\n\n")

        success_count = 0
        fail_count = 0
        skip_count = 0
        total_objects = 0
        total_materials = 0

        # Also track files to copy at end
        files_to_copy = []

        for i, corrupted_path in enumerate(corrupted):
            rel_path = corrupted_path.relative_to(CONVERTED_ROOT)
            print(f"\n[{i+1}/{len(corrupted)}] {rel_path}")

            # Find source file
            source_path = find_source_file(corrupted_path, SOURCE_ROOT)

            if source_path is None:
                log.write(f"[SKIP] No source found for: {rel_path}\n")
                print("  SKIP - No source found")
                skip_count += 1
                continue

            log.write(f"[{i+1}] {source_path.name} -> {rel_path}\n")

            # Get collection name from path
            collection_name = rel_path.parts[0]

            # Output to temp location first (internal drive)
            temp_output = OUTPUT_TEMP / rel_path

            # Re-extract
            result = extract_blend_file(
                source_blend=source_path,
                output_path=temp_output,
                collection_name=collection_name,
            )

            if result.is_success():
                log.write(f"  OK: {result.objects_extracted} objects, {result.materials_found} materials\n")
                print(f"  OK: {result.objects_extracted} objects, {result.materials_found} materials")
                success_count += 1
                total_objects += result.objects_extracted
                total_materials += result.materials_found

                # Track for final copy
                files_to_copy.append((temp_output, corrupted_path))
            else:
                log.write(f"  FAIL: {result.errors}\n")
                print(f"  FAIL: {result.errors}")
                fail_count += 1

        # Summary
        log.write("\n" + "=" * 60 + "\n")
        log.write("EXTRACTION SUMMARY\n")
        log.write(f"  Success:  {success_count}\n")
        log.write(f"  Failed:   {fail_count}\n")
        log.write(f"  Skipped:  {skip_count}\n")
        log.write(f"  Objects:  {total_objects}\n")
        log.write(f"  Materials: {total_materials}\n")

        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE")
        print("=" * 60)
        print(f"  Success:   {success_count}")
        print(f"  Failed:    {fail_count}")
        print(f"  Skipped:   {skip_count}")
        print(f"  Objects:   {total_objects}")
        print(f"  Materials: {total_materials}")

        # Copy files to external drive
        if files_to_copy:
            print(f"\nCopying {len(files_to_copy)} files to external drive...")
            log.write("\n" + "=" * 60 + "\n")
            log.write("COPYING TO EXTERNAL DRIVE\n")

            copy_success = 0
            copy_fail = 0

            for temp_path, final_path in files_to_copy:
                try:
                    # Verify temp file is valid
                    if temp_path.stat().st_size > CORRUPTED_SIZE:
                        # Delete corrupted file first
                        if final_path.exists():
                            final_path.unlink()
                        # Copy from temp to final
                        shutil.copy2(str(temp_path), str(final_path))
                        copy_success += 1
                        if copy_success % 50 == 0:
                            print(f"  Copied {copy_success}/{len(files_to_copy)}...")
                    else:
                        log.write(f"  SKIP (temp corrupted): {temp_path}\n")
                        copy_fail += 1
                except Exception as e:
                    log.write(f"  COPY FAIL: {final_path}: {e}\n")
                    copy_fail += 1

            log.write(f"\nCOPY SUMMARY\n")
            log.write(f"  Copied: {copy_success}\n")
            log.write(f"  Failed: {copy_fail}\n")

            print(f"\nCopy complete: {copy_success} success, {copy_fail} failed")
            print(f"\nLog saved to: {LOG_FILE}")

        # Cleanup temp
        print("\nCleaning up temp files...")
        shutil.rmtree(OUTPUT_TEMP, ignore_errors=True)


if __name__ == "__main__":
    main()
