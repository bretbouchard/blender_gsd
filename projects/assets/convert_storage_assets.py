#!/usr/bin/env python3
"""
Convert additional storage assets to Blender Asset Browser format.

Handles:
- Mech Warrior (3 large mech models)
- Dune Packs (8 landscape files)
- VFX Asset Library (200+ FX assets)

Usage:
    blender --background --python convert_storage_assets.py -- --all
    blender --background --python convert_storage_assets.py -- --collection MechWarrior
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


# =============================================================================
# COLLECTION CONFIGURATIONS
# =============================================================================

@dataclass
class AssetCollection:
    """Configuration for an asset collection."""
    name: str
    source_root: str
    description: str = ""
    blend_files: list[str] = field(default_factory=list)
    recursive: bool = True


COLLECTIONS: list[AssetCollection] = [
    # Mech Warrior
    AssetCollection(
        name="MechWarrior",
        source_root="/Volumes/Storage/3d/kitbash/mech warrior/blender",
        description="Large mech models (3 files)",
        blend_files=[
            "mech_1.blend",
            "mech_2.blend",
            "mech_3.blend",
        ],
        recursive=False,
    ),

    # Dune Packs
    AssetCollection(
        name="Dune",
        source_root="/Volumes/Storage/3d/kitbash/dpacks",
        description="Dune landscape packs",
        recursive=True,
    ),

    # VFX Asset Library
    AssetCollection(
        name="VFX",
        source_root="/Volumes/Storage/3d/animation/VFX Asset Library - 200 FX Alpha",
        description="200+ VFX assets - particles, energy, shockwaves",
        recursive=True,
    ),
]


# =============================================================================
# BLEND FILE EXTRACTOR
# =============================================================================

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
    author: str = "Unknown",
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
            # Also get node groups for VFX
            data_to.node_groups = data_from.node_groups
    except Exception as e:
        result.errors.append(f"Failed to load library: {e}")
        return result

    # Link collections to scene
    for coll in data_to.collections:
        if coll and coll.name not in bpy.context.scene.collection.children:
            try:
                bpy.context.scene.collection.children.link(coll)
            except Exception as e:
                result.warnings.append(f"Could not link collection {coll.name}: {e}")

    # Track objects already in collections
    linked_object_names = set()
    for coll in bpy.data.collections:
        for obj in coll.all_objects:
            linked_object_names.add(obj.name)

    # Link orphaned objects to scene (including CURVE, LIGHT, etc for VFX)
    scene_collection = bpy.context.scene.collection
    for obj in data_to.objects:
        if obj:
            if obj.name not in linked_object_names:
                try:
                    if obj.name not in scene_collection.objects:
                        scene_collection.objects.link(obj)
                except Exception as e:
                    result.warnings.append(f"Could not link object {obj.name}: {e}")

    # Mark objects as assets (MESH, CURVE, LIGHT for VFX)
    asset_types = {"MESH", "CURVE", "LIGHT", "CAMERA", "EMPTY"}
    for obj in bpy.data.objects:
        if obj.type in asset_types:
            try:
                obj.asset_mark()
                if obj.asset_data:
                    obj.asset_data.author = author
                    obj.asset_data.description = f"{collection_name} asset from {source_blend.stem}"

                    tag_name = collection_name.lower().replace(" ", "_").replace("-", "_")
                    if tag_name not in [t.name for t in obj.asset_data.tags]:
                        obj.asset_data.tags.new(tag_name)

                result.objects_extracted += 1
            except Exception as e:
                result.warnings.append(f"Could not mark {obj.name} as asset: {e}")

    result.materials_found = len([m for m in bpy.data.materials if m.users > 0])

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


def find_blend_files(source_root: Path, collection: AssetCollection) -> list[Path]:
    """Find all blend files in a collection."""
    blend_files = []

    if collection.blend_files:
        for rel_path in collection.blend_files:
            full_path = source_root / rel_path
            if full_path.exists():
                blend_files.append(full_path)
    else:
        if collection.recursive:
            for f in source_root.rglob("*.blend"):
                if any(x in f.suffixes for x in [".blend1", ".blend2"]):
                    continue
                blend_files.append(f)
        else:
            for f in source_root.glob("*.blend"):
                if any(x in f.suffixes for x in [".blend1", ".blend2"]):
                    continue
                blend_files.append(f)

    return blend_files


def convert_collection(
    collection: AssetCollection,
    output_root: Path,
) -> list[ExtractionResult]:
    """Convert all blend files in a collection."""
    source_root = Path(collection.source_root)
    output_dir = output_root / collection.name

    if not source_root.exists():
        print(f"  Source not found: {source_root}")
        return []

    blend_files = find_blend_files(source_root, collection)

    if not blend_files:
        print(f"  No blend files found in {source_root}")
        return []

    print(f"  Found {len(blend_files)} blend files")

    results = []
    for i, blend_file in enumerate(blend_files, 1):
        print(f"  [{i}/{len(blend_files)}] {blend_file.name}...", end=" ", flush=True)

        result = extract_blend_file(
            source_blend=blend_file,
            output_dir=output_dir,
            collection_name=collection.name,
            author=collection.name,
        )
        results.append(result)

        if result.is_success():
            print(f"✓ {result.objects_extracted} objects, {result.materials_found} materials")
        else:
            print(f"✗ {result.errors[0] if result.errors else 'Unknown error'}")

    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run conversion."""
    args_list = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    collection_name = None
    convert_all = False
    list_only = False

    i = 0
    while i < len(args_list):
        arg = args_list[i]
        if arg in ["--collection", "-c"] and i + 1 < len(args_list):
            collection_name = args_list[i + 1]
            i += 2
        elif arg in ["--all", "-a"]:
            convert_all = True
            i += 1
        elif arg in ["--list", "-l"]:
            list_only = True
            i += 1
        else:
            i += 1

    output_root = Path("/Volumes/Storage/3d/kitbash/converted_assets")

    print("=" * 60)
    print("Storage Assets Converter")
    print("=" * 60)

    if list_only:
        print("\nAvailable Collections:")
        print("-" * 60)
        for coll in COLLECTIONS:
            source = Path(coll.source_root)
            exists = "✓" if source.exists() else "✗"
            blend_count = len(find_blend_files(source, coll)) if source.exists() else 0
            print(f"  {exists} {coll.name:<15} ({blend_count} blend files)")
            print(f"      {coll.description}")
        return

    if collection_name:
        collections_to_convert = [
            c for c in COLLECTIONS
            if collection_name.lower() in c.name.lower()
        ]
        if not collections_to_convert:
            print(f"Collection '{collection_name}' not found")
            print(f"Available: {[c.name for c in COLLECTIONS]}")
            return
    elif convert_all:
        collections_to_convert = COLLECTIONS
    else:
        print("Specify --collection NAME or --all")
        print("Use --list to see available collections")
        return

    print(f"\nConverting {len(collections_to_convert)} collections...")
    print()

    total_objects = 0
    total_materials = 0

    for coll in collections_to_convert:
        print(f"\n{coll.name}:")
        print(f"  {coll.description}")

        results = convert_collection(coll, output_root)

        for r in results:
            if r.is_success():
                total_objects += r.objects_extracted
                total_materials += r.materials_found

    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Total objects: {total_objects}")
    print(f"Total materials: {total_materials}")
    print(f"Output: {output_root}")


if __name__ == "__main__":
    main()
