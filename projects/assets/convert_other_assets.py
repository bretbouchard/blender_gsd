#!/usr/bin/env python3
"""
Convert non-KitBash3D asset collections to Blender Asset Browser format.

Handles:
- Vitaly Sets (mech, robots, buildings)
- Benianus 3D Architecture products
- kpacks (68 collections)
- 3D Kitbashing library
- spock kit

Usage:
    # Convert specific collection:
    blender --background --python convert_other_assets.py -- --collection vitaly

    # Convert all:
    blender --background --python convert_other_assets.py -- --all
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object

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
    recursive: bool = True  # Search subdirectories for blend files


# All non-KitBash3D collections
COLLECTIONS: list[AssetCollection] = [
    # Vitaly Sets - Mechs and robots
    AssetCollection(
        name="Vitaly",
        source_root="/Volumes/Storage/3d/kitbash/Vitaly sets",
        description="Vitaly robot/mech sets, buildings, props",
        blend_files=[
            "building/FloorPanels.blend",
            "building/Megastructure.blend",
            "mech/ArmorPack.blend",
            "mech/BlackPhoenix.blend",
            "mech/BlackWidow.blend",
            "mech/CyberMusclesPack.blend",
            "mech/PistonsCaps.blend",
            "mech/RoboGuts.blend",
            "mech/WiresCables.blend",
            "props/SciFi_Crates.blend",
            "props/SciFi_Props.blend",
        ],
        recursive=False,
    ),

    # Benianus 3D Architecture
    AssetCollection(
        name="Benianus",
        source_root="/Volumes/Storage/3d/kitbash/Benianus 3D - Architecture products",
        description="Architecture products - furniture, bathrooms, kitchen",
        recursive=True,
    ),

    # 3D Kitbashing library
    AssetCollection(
        name="3DKitbashing",
        source_root="/Volumes/Storage/3d/kitbash/3D Kitbashing library",
        description="Furniture, lighting studios",
        recursive=True,
    ),

    # Spock kit
    AssetCollection(
        name="Spock",
        source_root="/Volumes/Storage/3d/kitbash/spock",
        description="Spock kit",
        recursive=True,
    ),

    # kpacks - SKIPPED (user requested to leave as-is)
    # AssetCollection(
    #     name="kpacks",
    #     source_root="/Volumes/Storage/3d/kitbash/kpacks",
    #     description="68 kitbash collections - DM-, Arch-, Hexes, Dots, etc.",
    #     recursive=True,
    # ),
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
    """
    Extract assets from a blend file and mark them as assets.

    Uses the improved approach:
    1. Append all collections, objects, and materials
    2. Link collections to scene
    3. Link orphaned objects to scene
    4. Mark all mesh objects as assets
    5. Save to output directory
    """
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
            except Exception as e:
                result.warnings.append(f"Could not link collection {coll.name}: {e}")

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
                except Exception as e:
                    result.warnings.append(f"Could not link object {obj.name}: {e}")

    # Mark all mesh objects as assets
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            try:
                obj.asset_mark()
                if obj.asset_data:
                    obj.asset_data.author = author
                    obj.asset_data.description = f"{collection_name} asset from {source_blend.stem}"

                    # Add collection tag
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
        # Use explicit list
        for rel_path in collection.blend_files:
            full_path = source_root / rel_path
            if full_path.exists():
                blend_files.append(full_path)
    else:
        # Search recursively
        if collection.recursive:
            for f in source_root.rglob("*.blend"):
                # Skip backup files
                if any(x in f.suffixes for x in [".blend1", ".blend2"]):
                    continue
                blend_files.append(f)
        else:
            for f in source_root.glob("*.blend"):
                if any(x in f.suffixes for x in [".blend1", ".blend2"]):
                    continue
                blend_files.append(f)

    return blend_files


# =============================================================================
# CONVERTERS
# =============================================================================

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


def convert_kpacks(output_root: Path) -> list[ExtractionResult]:
    """
    Special handling for kpacks - 68 subfolders, each a mini collection.

    Instead of one giant output, creates separate outputs per kpack.
    """
    source_root = Path("/Volumes/Storage/3d/kitbash/kpacks")

    if not source_root.exists():
        print("  kpacks source not found")
        return []

    # Get all subdirectories
    kpack_dirs = sorted([d for d in source_root.iterdir() if d.is_dir()])

    print(f"  Found {len(kpack_dirs)} kpack directories")

    all_results = []
    output_dir = output_root / "kpacks"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, kpack_dir in enumerate(kpack_dirs, 1):
        kpack_name = kpack_dir.name
        print(f"  [{i}/{len(kpack_dirs)}] {kpack_name}...", end=" ", flush=True)

        # Find blend files in this kpack
        blend_files = list(kpack_dir.rglob("*.blend"))
        blend_files = [f for f in blend_files if not any(x in f.suffixes for x in [".blend1", ".blend2"])]

        if not blend_files:
            print("(no blend files)")
            continue

        # Convert each blend file
        kpack_results = []
        for blend_file in blend_files:
            result = extract_blend_file(
                source_blend=blend_file,
                output_dir=output_dir / kpack_name,
                collection_name=f"kpacks_{kpack_name}",
                author="kpacks",
            )
            kpack_results.append(result)

        # Summary for this kpack
        total_objects = sum(r.objects_extracted for r in kpack_results)
        success = sum(1 for r in kpack_results if r.is_success())
        print(f"{success}/{len(kpack_results)} files, {total_objects} objects")

        all_results.extend(kpack_results)

    return all_results


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run conversion."""
    # Parse arguments manually (Blender passes -- as separator)
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
    print("Non-KitBash3D Asset Converter")
    print("=" * 60)

    # List mode
    if list_only:
        print("\nAvailable Collections:")
        print("-" * 60)
        for coll in COLLECTIONS:
            source = Path(coll.source_root)
            exists = "✓" if source.exists() else "✗"
            blend_count = len(find_blend_files(source, coll)) if source.exists() else 0
            print(f"  {exists} {coll.name:<15} ({blend_count} blend files)")
            print(f"      {coll.description}")
        print()
        print("Usage:")
        print("  List:      blender --background --python convert_other_assets.py -- --list")
        print("  Convert:   blender --background --python convert_other_assets.py -- --collection Vitaly")
        print("  All:       blender --background --python convert_other_assets.py -- --all")

        try:
            import bpy
            bpy.ops.wm.quit_blender()
        except ImportError:
            pass
        return

    # Determine what to convert
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

        # Special handling for kpacks
        if coll.name.lower() == "kpacks":
            results = convert_kpacks(output_root)
        else:
            results = convert_collection(coll, output_root)

        # Tally
        for r in results:
            if r.is_success():
                total_objects += r.objects_extracted
                total_materials += r.materials_found

    # Summary
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Total objects: {total_objects}")
    print(f"Total materials: {total_materials}")
    print(f"Output: {output_root}")


if __name__ == "__main__":
    main()
