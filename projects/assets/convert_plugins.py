#!/usr/bin/env python3
"""
Convert plugin assets to Blender Asset Browser format.

Handles:
- Car Transportation materials (100+ car paints)
- ScifiFlex dpacks (7 sci-fi panel kits)
- Trash Kit (debris assets)
- Shwifty Shaders (shader library)
- Procedural Building Generator samples
- Plating Generator samples

Usage:
    blender --background --python convert_plugins.py
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
    node_groups_found: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def is_success(self) -> bool:
        return self.output_path is not None and len(self.errors) == 0


def extract_blend_file(
    source_blend: Path,
    output_dir: Path,
    collection_name: str,
    author: str = "Plugin",
    include_node_groups: bool = False,
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
            if include_node_groups:
                data_to.node_groups = data_from.node_groups
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
        if obj:
            if obj.name not in linked_object_names:
                try:
                    if obj.name not in scene_collection.objects:
                        scene_collection.objects.link(obj)
                except Exception:
                    pass

    # Mark mesh objects as assets
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            try:
                obj.asset_mark()
                if obj.asset_data:
                    obj.asset_data.author = author
                    obj.asset_data.description = f"{collection_name} asset"
                    tag_name = collection_name.lower().replace(" ", "_").replace("-", "_")
                    if tag_name not in [t.name for t in obj.asset_data.tags]:
                        obj.asset_data.tags.new(tag_name)
                result.objects_extracted += 1
            except Exception:
                pass

    # Mark materials as assets
    for mat in bpy.data.materials:
        if mat.users > 0:
            try:
                mat.asset_mark()
                if mat.asset_data:
                    mat.asset_data.author = author
                    mat.asset_data.description = f"{collection_name} material"
                result.materials_found += 1
            except Exception:
                pass

    # Count node groups if included
    if include_node_groups:
        result.node_groups_found = len([ng for ng in bpy.data.node_groups if ng.users > 0])

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


# =============================================================================
# PLUGIN COLLECTIONS
# =============================================================================

PLUGIN_SOURCES = [
    # Car Transportation Materials
    {
        "name": "CarMaterials_Glossy",
        "source": "/Volumes/Storage/3d/animation/plugins/Car Transportation v4/data/materials/glossy",
        "author": "Car Transportation",
        "recursive": True,
    },
    {
        "name": "CarMaterials_Matt",
        "source": "/Volumes/Storage/3d/animation/plugins/Car Transportation v4/data/materials/matt",
        "author": "Car Transportation",
        "recursive": True,
    },
    {
        "name": "CarMaterials_Metallic",
        "source": "/Volumes/Storage/3d/animation/plugins/Car Transportation v4/data/materials/metallic",
        "author": "Car Transportation",
        "recursive": True,
    },

    # ScifiFlex dpacks
    {
        "name": "ScifiFlex_CITOPIA",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/CITOPIA",
        "author": "ScifiFlex",
        "recursive": True,
    },
    {
        "name": "ScifiFlex_EXXODUS",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/EXXODUS",
        "author": "ScifiFlex",
        "recursive": True,
    },
    {
        "name": "ScifiFlex_INDUSTRIA",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/INDUSTRIA",
        "author": "ScifiFlex",
        "recursive": True,
    },
    {
        "name": "ScifiFlex_PANELX",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/PANEL-X",
        "author": "ScifiFlex",
        "recursive": True,
    },
    {
        "name": "ScifiFlex_PANELY",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/PANEL-Y",
        "author": "ScifiFlex",
        "recursive": True,
    },
    {
        "name": "ScifiFlex_PIPER",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/PIPER",
        "author": "ScifiFlex",
        "recursive": True,
    },
    {
        "name": "ScifiFlex_RIYA",
        "source": "/Volumes/Storage/3d/animation/plugins/scififlex/dpacks/RIYA",
        "author": "ScifiFlex",
        "recursive": True,
    },

    # Trash Kit
    {
        "name": "TrashKit",
        "source": "/Volumes/Storage/3d/animation/plugins/Blender Market – Trash Kit - 3d Assetkit",
        "author": "Trash Kit",
        "recursive": False,
    },

    # Shaders
    {
        "name": "ShwiftyShaders",
        "source": "/Volumes/Storage/3d/animation/plugins/Shwifty Shaders v1.2",
        "author": "Shwifty",
        "recursive": False,
        "include_node_groups": True,
    },

    # Procedural Building
    {
        "name": "ProceduralBuilding",
        "source": "/Volumes/Storage/3d/animation/plugins/Procedural Building Generator 2",
        "author": "PBG",
        "recursive": False,
    },

    # Plating Generator
    {
        "name": "PlatingGenerator",
        "source": "/Volumes/Storage/3d/animation/plugins/Plating Generator and Greebles v2.0/plating_generator_greebles_2.0.0_samples_unzip.me",
        "author": "Plating Generator",
        "recursive": False,
    },
]


def convert_plugin_source(source_config: dict, output_root: Path) -> list[ExtractionResult]:
    """Convert all blend files from a plugin source."""
    source_path = Path(source_config["source"])
    output_dir = output_root / source_config["name"]

    if not source_path.exists():
        print(f"  Source not found: {source_path}")
        return []

    # Find blend files
    if source_config.get("recursive", False):
        blend_files = list(source_path.rglob("*.blend"))
    else:
        blend_files = list(source_path.glob("*.blend"))

    blend_files = [f for f in blend_files if not any(x in f.suffixes for x in [".blend1", ".blend2"])]

    if not blend_files:
        print(f"  No blend files found")
        return []

    print(f"  Found {len(blend_files)} blend files")

    results = []
    for i, blend_file in enumerate(blend_files, 1):
        print(f"    [{i}/{len(blend_files)}] {blend_file.name}...", end=" ", flush=True)

        result = extract_blend_file(
            source_blend=blend_file,
            output_dir=output_dir,
            collection_name=source_config["name"],
            author=source_config["author"],
            include_node_groups=source_config.get("include_node_groups", False),
        )
        results.append(result)

        if result.is_success():
            extra = ""
            if result.node_groups_found > 0:
                extra = f", {result.node_groups_found} nodes"
            print(f"✓ {result.objects_extracted} obj, {result.materials_found} mat{extra}")
        else:
            print(f"✗ {result.errors[0] if result.errors else 'Unknown error'}")

    return results


def main():
    """Convert all plugin assets."""
    output_root = Path("/Volumes/Storage/3d/kitbash/converted_assets/plugins")

    print("=" * 60)
    print("Plugin Assets Converter")
    print("=" * 60)
    print(f"\nConverting {len(PLUGIN_SOURCES)} plugin sources...")
    print()

    total_objects = 0
    total_materials = 0
    total_node_groups = 0

    for i, source in enumerate(PLUGIN_SOURCES, 1):
        print(f"[{i}/{len(PLUGIN_SOURCES)}] {source['name']}:")

        results = convert_plugin_source(source, output_root)

        for r in results:
            if r.is_success():
                total_objects += r.objects_extracted
                total_materials += r.materials_found
                total_node_groups += r.node_groups_found

        print()

    print("=" * 60)
    print("Plugin Assets Conversion Summary")
    print("=" * 60)
    print(f"Total objects: {total_objects}")
    print(f"Total materials: {total_materials}")
    print(f"Total node groups: {total_node_groups}")
    print(f"Output: {output_root}")


if __name__ == "__main__":
    main()
