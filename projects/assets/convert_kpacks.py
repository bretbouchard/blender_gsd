#!/usr/bin/env python3
"""
Convert kpacks (68 collections, 2254 blend files) to Blender Asset Browser format.

This is a large collection, so it processes each kpack folder separately.

Usage:
    blender --background --python convert_kpacks.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


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


def extract_blend_file(
    source_blend: Path,
    output_dir: Path,
    collection_name: str,
    author: str = "kpacks",
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

    # Mark all mesh objects as assets and generate previews
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

                    # Generate preview thumbnail
                    if not obj.preview:
                        bpy.ops.asset.generate_preview({"id": obj})

                result.objects_extracted += 1
            except Exception:
                pass

    # Mark all used materials as assets
    materials_marked = 0
    for mat in bpy.data.materials:
        # Skip default/generic materials
        if mat.name in {"Material", "Dots Stroke", "None"}:
            continue
        # Only mark materials that are actually used
        if mat.users > 0:
            try:
                mat.asset_mark()
                if mat.asset_data:
                    mat.asset_data.author = author
                    mat.asset_data.description = f"kpacks {collection_name} material"

                    tag_name = f"kpacks_{collection_name.lower().replace(' ', '_').replace('-', '_')}"
                    if tag_name not in [t.name for t in mat.asset_data.tags]:
                        mat.asset_data.tags.new(tag_name)

                    # Generate preview thumbnail
                    if not mat.preview:
                        bpy.ops.asset.generate_preview({"id": mat})

                materials_marked += 1
            except Exception:
                pass

    result.materials_found = materials_marked

    # Try to pack textures
    try:
        bpy.ops.file.pack_all()
    except Exception:
        pass

    # Save blend file
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{source_blend.stem}_assets.blend"

    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        result.output_path = output_path
    except Exception as e:
        result.errors.append(f"Failed to save: {e}")

    return result


def convert_kpacks():
    """Convert all kpacks."""
    source_root = Path("/Volumes/Storage/3d/kitbash/kpacks")
    output_root = Path("/Volumes/Storage/3d/kitbash/converted_assets/kpacks")

    if not source_root.exists():
        print("kpacks source not found")
        return

    # Get all kpack directories
    kpack_dirs = sorted([d for d in source_root.iterdir() if d.is_dir()])

    print("=" * 60)
    print("kpacks Converter")
    print("=" * 60)
    print(f"\nFound {len(kpack_dirs)} kpack directories")
    print()

    total_objects = 0
    total_materials = 0
    total_files = 0

    for i, kpack_dir in enumerate(kpack_dirs, 1):
        kpack_name = kpack_dir.name
        kpack_output = output_root / kpack_name

        # Skip if already converted (has output folder with files)
        if kpack_output.exists():
            existing_files = list(kpack_output.glob("*.blend"))
            if len(existing_files) > 0:
                print(f"[{i}/{len(kpack_dirs)}] {kpack_name}... SKIPPED (already converted)")
                continue

        print(f"[{i}/{len(kpack_dirs)}] {kpack_name}...", end=" ", flush=True)

        # Find blend files in this kpack
        blend_files = list(kpack_dir.rglob("*.blend"))
        blend_files = [f for f in blend_files if not any(x in f.suffixes for x in [".blend1", ".blend2"])]

        if not blend_files:
            print("(no blend files)")
            continue

        # Convert each blend file
        kpack_output = output_root / kpack_name
        kpack_objects = 0
        kpack_materials = 0
        success_count = 0

        for blend_file in blend_files:
            result = extract_blend_file(
                source_blend=blend_file,
                output_dir=kpack_output,
                collection_name=kpack_name,
            )
            if result.is_success():
                kpack_objects += result.objects_extracted
                kpack_materials += result.materials_found
                success_count += 1

        print(f"{success_count}/{len(blend_files)} files, {kpack_objects} objects, {kpack_materials} mats")
        total_objects += kpack_objects
        total_materials += kpack_materials
        total_files += success_count

    print()
    print("=" * 60)
    print("kpacks Conversion Summary")
    print("=" * 60)
    print(f"Total files converted: {total_files}")
    print(f"Total objects: {total_objects}")
    print(f"Total materials: {total_materials}")
    print(f"Output: {output_root}")


if __name__ == "__main__":
    convert_kpacks()
