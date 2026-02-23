#!/usr/bin/env python3
"""
Batch convert all KitBash3D kits to Blender Asset Browser format.

Handles two types of kits:
1. OBJ/FBX with textures - uses KitBashConverter
2. Native .blend files - extracts and marks assets

Usage:
    # In Blender (background mode):
    blender --background --python convert_all_kits.py

    # Convert specific kit:
    blender --background --python convert_all_kits.py -- --kit "Dieselpunk"
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.assets.converter import KitBashConverter, ConversionResult


# =============================================================================
# KIT CONFIGURATIONS
# =============================================================================

@dataclass
class KitConfig:
    """Configuration for a KitBash3D kit."""
    name: str
    source_dir: str
    kit_type: str  # "obj_fbx", "native_blend", "hybrid"
    texture_dir: str | None = None
    texture_prefix: str | None = None
    obj_file: str | None = None
    fbx_file: str | None = None
    blend_file: str | None = None
    notes: str = ""


# All KitBash3D kits configuration
KITS: list[KitConfig] = [
    # Category A: OBJ/FBX with textures (already done)
    KitConfig(
        name="Aftermath",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Aftermath",
        kit_type="obj_fbx",
        texture_dir="KB3DTextures",
        texture_prefix="KB3D_WZT",
        obj_file="Kitbash3d_Warzone2.obj",
        notes="COMPLETED - 575 objects, 17 materials",
    ),

    # Category A: OBJ/FBX with textures (to convert)
    KitConfig(
        name="Aristocracy",
        source_dir="/Volumes/Storage/3d/kitbash/Kitbash3D - Aristocracy",
        kit_type="obj_fbx",
        texture_dir="KB3DTextures",
        texture_prefix="KB3D",  # KB3D_Bricks1_Diffuse.jpg
        obj_file="Kitbash3d_Aristocracy_MiniKit.obj",
    ),
    KitConfig(
        name="Dieselpunk",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Dieselpunk",
        kit_type="obj_fbx",
        texture_dir="KB3DTextures/2k",  # Nested in 2k folder
        texture_prefix="KB3D_DPK",
        obj_file="kb3d_dieselpunk-native.obj",
    ),
    KitConfig(
        name="Sci-Fi Industrial",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Sci-Fi Industrial",
        kit_type="obj_fbx",
        texture_dir="KB3DTextures",
        texture_prefix="KB3D_SF",  # KB3D_SF_Floor_ao.jpg
        obj_file="KB3D_SciFiIndustrial.obj",
    ),
    KitConfig(
        name="Savage",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Savage",
        kit_type="hybrid",  # Has FBX+OBJ folder and Blender folder
        texture_dir="KB3DTextures",
        texture_prefix="KB3D",  # KB3D_BarkCharred_*
        notes="Check FBX+OBJ folder for source files",
    ),
    KitConfig(
        name="Veh Supercars",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Veh Supercars",
        kit_type="hybrid",
        texture_dir="KB3DTextures",
        texture_prefix="KB3D",  # KB3D_CarbonFiber_*
        notes="Check FBX+OBJ folder for source files",
    ),

    # Category B: Native blend files (extract assets)
    KitConfig(
        name="Americana",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Americana",
        kit_type="native_blend",
        blend_file="Blender/americana.blend",  # Check actual path
        notes="Has Blender folder with native file",
    ),
    KitConfig(
        name="Atompunk",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Atompunk",
        kit_type="native_blend",
        blend_file="kb3d_atompunk-native.blend",
    ),
    KitConfig(
        name="Art Deco",
        source_dir="/Volumes/Storage/3d/kitbash/Kitbash3D - Art Deco",
        kit_type="native_blend",
        blend_file="Art Deco.blend",
        texture_dir="TEXTURES",
    ),
    KitConfig(
        name="Brooklyn",
        source_dir="/Volumes/Storage/3d/kitbash/Kitbash3D - Brooklyn",
        kit_type="native_blend",
        blend_file="Blender/brooklyn.blend",  # Check actual path
        notes="Has Blender folder",
    ),
    KitConfig(
        name="Brutalist",
        source_dir="/Volumes/Storage/3d/kitbash/Kitbash3D - Brutalist",
        kit_type="native_blend",
        blend_file="brutalist.blend",
        texture_dir="Textures",
    ),
    KitConfig(
        name="Cyberdistrict",
        source_dir="/Volumes/Storage/3d/kitbash/Kitbash3D - cyberdistrict",
        kit_type="native_blend",
        blend_file="kb3d_cyberdistrict-native.blend",
    ),
    KitConfig(
        name="LA Downtown",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - LA Downtown",
        kit_type="native_blend",
        blend_file="KB3D_DTLA-Native.blend",
        texture_dir="KB3DTextures",
    ),

    # Category C: Special handling
    KitConfig(
        name="Edo Japan",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Edo Japan",
        kit_type="fbx_only",
        fbx_file="KITBASH3D_EDOJAPAN.fbx",
        notes="FBX only, no textures found - may need manual texture assignment",
    ),
]


# =============================================================================
# BLEND FILE ASSET EXTRACTOR
# =============================================================================

@dataclass
class ExtractionResult:
    """Result of extracting assets from a blend file."""
    pack_name: str
    output_path: Path | None = None
    objects_extracted: int = 0
    materials_found: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def is_success(self) -> bool:
        return self.output_path is not None and len(self.errors) == 0


def extract_from_blend(
    pack_name: str,
    source_blend: Path,
    output_dir: Path,
    texture_dir: Path | None = None,
) -> ExtractionResult:
    """
    Extract assets from a native KitBash3D blend file.

    Native blends often already have:
    - Objects organized in collections
    - Materials with textures linked
    - Proper naming

    We need to:
    1. Link/append all collections and objects
    2. Mark objects as assets
    3. Pack external textures if needed
    4. Save to asset library
    """
    import bpy

    result = ExtractionResult(pack_name=pack_name)

    if not source_blend.exists():
        result.errors.append(f"Blend file not found: {source_blend}")
        return result

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Start fresh
    bpy.ops.wm.read_homefile(app_template="")

    # Append all collections and objects from the source blend
    with bpy.data.libraries.load(str(source_blend)) as (data_from, data_to):
        # Get all collections
        data_to.collections = data_from.collections

        # Get all objects (many kits have objects directly, not in collections)
        data_to.objects = data_from.objects

        # Also get materials
        data_to.materials = data_from.materials

    # Link collections to scene
    for coll in data_to.collections:
        if coll and coll.name not in bpy.context.scene.collection.children:
            try:
                bpy.context.scene.collection.children.link(coll)
            except Exception as e:
                result.warnings.append(f"Could not link collection {coll.name}: {e}")

    # Link orphaned objects directly to scene collection
    scene_collection = bpy.context.scene.collection
    linked_object_names = set()

    # First, collect all objects already in linked collections
    for coll in bpy.data.collections:
        for obj in coll.all_objects:
            linked_object_names.add(obj.name)

    # Then link objects not in any collection to the scene
    for obj in data_to.objects:
        if obj and obj.type == "MESH":
            if obj.name not in linked_object_names:
                try:
                    if obj.name not in scene_collection.objects:
                        scene_collection.objects.link(obj)
                except Exception as e:
                    result.warnings.append(f"Could not link object {obj.name}: {e}")

    # Mark all mesh objects as assets and generate previews
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            try:
                obj.asset_mark()
                if obj.asset_data:
                    obj.asset_data.author = "KitBash3D"
                    obj.asset_data.description = f"KitBash3D {pack_name} asset"

                    # Add tag
                    tag_name = pack_name.lower().replace(" ", "_").replace("-", "_")
                    if tag_name not in [t.name for t in obj.asset_data.tags]:
                        obj.asset_data.tags.new(tag_name)

                    # Generate preview thumbnail
                    if not obj.preview:
                        bpy.ops.asset.generate_preview({"id": obj})

                result.objects_extracted += 1
            except Exception as e:
                result.warnings.append(f"Could not mark {obj.name} as asset: {e}")

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
                    mat.asset_data.author = "KitBash3D"
                    mat.asset_data.description = f"KitBash3D {pack_name} material"

                    # Add tag
                    tag_name = pack_name.lower().replace(" ", "_").replace("-", "_")
                    if tag_name not in [t.name for t in mat.asset_data.tags]:
                        mat.asset_data.tags.new(tag_name)

                    # Generate preview thumbnail
                    if not mat.preview:
                        bpy.ops.asset.generate_preview({"id": mat})

                materials_marked += 1
            except Exception as e:
                result.warnings.append(f"Could not mark material {mat.name} as asset: {e}")

    result.materials_found = materials_marked

    # Pack textures if requested
    if texture_dir and texture_dir.exists():
        try:
            bpy.ops.file.pack_all()
        except Exception:
            pass  # Some textures might already be packed

    # Save blend file
    output_path = output_dir / f"{pack_name}_assets.blend"
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        result.output_path = output_path
    except Exception as e:
        result.errors.append(f"Failed to save: {e}")

    return result


# =============================================================================
# BATCH CONVERTER
# =============================================================================

def convert_obj_fbx_kit(config: KitConfig, output_root: Path) -> ConversionResult:
    """Convert an OBJ/FBX kit using KitBashConverter."""
    import bpy

    source_dir = Path(config.source_dir)
    output_dir = output_root / config.name

    # Find OBJ file if not specified
    obj_file = None
    if config.obj_file:
        obj_file = source_dir / config.obj_file
        if not obj_file.exists():
            obj_file = None

    if not obj_file:
        for f in source_dir.glob("*.obj"):
            obj_file = f
            break

    # Find texture directory
    texture_dir = None
    if config.texture_dir:
        texture_dir = source_dir / config.texture_dir
        if not texture_dir.exists():
            # Try without nested path
            texture_dir = source_dir / config.texture_dir.split("/")[0]

    # Use converter
    converter = KitBashConverter()
    result = converter.convert_pack(
        pack_name=config.name,
        source_dir=source_dir,
        output_dir=output_dir,
        prefix=config.texture_prefix,
    )

    return result


def convert_hybrid_kit(config: KitConfig, output_root: Path) -> ConversionResult | ExtractionResult:
    """Convert a hybrid kit (has both blend and OBJ/FBX)."""
    source_dir = Path(config.source_dir)

    # Check for FBX+OBJ folder
    fbx_obj_dir = source_dir / "FBX+OBJ"
    if fbx_obj_dir.exists():
        # Look for OBJ files
        obj_files = list(fbx_obj_dir.glob("*.obj"))
        if obj_files:
            # Create modified config pointing to FBX+OBJ folder
            modified_config = KitConfig(
                name=config.name,
                source_dir=str(fbx_obj_dir),
                kit_type="obj_fbx",
                texture_dir=config.texture_dir,
                texture_prefix=config.texture_prefix,
            )
            return convert_obj_fbx_kit(modified_config, output_root)

    # Check for Blender folder
    blender_dir = source_dir / "Blender"
    if blender_dir.exists():
        blend_files = list(blender_dir.glob("*.blend"))
        if blend_files:
            return extract_from_blend(
                pack_name=config.name,
                source_blend=blend_files[0],
                output_dir=output_root / config.name,
                texture_dir=source_dir / config.texture_dir if config.texture_dir else None,
            )

    # Fallback to regular OBJ/FBX conversion
    return convert_obj_fbx_kit(config, output_root)


def convert_native_blend_kit(config: KitConfig, output_root: Path) -> ExtractionResult:
    """Extract assets from a native blend file."""
    source_dir = Path(config.source_dir)
    blend_path = source_dir / config.blend_file if config.blend_file else None

    # If blend path doesn't exist, search for it
    if not blend_path or not blend_path.exists():
        for f in source_dir.glob("**/*.blend"):
            # Skip backup files
            if ".blend1" in f.name or ".blend2" in f.name:
                continue
            blend_path = f
            break

    if not blend_path:
        return ExtractionResult(
            pack_name=config.name,
            errors=[f"No blend file found in {source_dir}"],
        )

    texture_dir = None
    if config.texture_dir:
        texture_dir = source_dir / config.texture_dir

    return extract_from_blend(
        pack_name=config.name,
        source_blend=blend_path,
        output_dir=output_root / config.name,
        texture_dir=texture_dir,
    )


def convert_fbx_only_kit(config: KitConfig, output_root: Path) -> ConversionResult:
    """Convert an FBX-only kit."""
    import bpy

    source_dir = Path(config.source_dir)
    output_dir = output_root / config.name
    output_dir.mkdir(parents=True, exist_ok=True)

    result = ConversionResult(pack_name=config.name)

    fbx_path = source_dir / config.fbx_file if config.fbx_file else None
    if not fbx_path or not fbx_path.exists():
        for f in source_dir.glob("*.fbx"):
            fbx_path = f
            break

    if not fbx_path:
        result.errors.append(f"No FBX file found in {source_dir}")
        return result

    # Start fresh
    bpy.ops.wm.read_homefile(app_template="")

    # Import FBX
    try:
        bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    except Exception as e:
        result.errors.append(f"FBX import failed: {e}")
        return result

    imported = list(bpy.context.selected_objects)

    if not imported:
        result.errors.append("No objects imported from FBX")
        return result

    # Create collection
    pack_collection = bpy.data.collections.new(config.name)
    bpy.context.scene.collection.children.link(pack_collection)

    # Process objects
    for obj in imported:
        if obj.type == "MESH":
            pack_collection.objects.link(obj)
            obj.asset_mark()
            if obj.asset_data:
                obj.asset_data.author = "KitBash3D"
                obj.asset_data.description = f"KitBash3D {config.name} asset"
                # Generate preview thumbnail
                if not obj.preview:
                    bpy.ops.asset.generate_preview({"id": obj})
            result.objects_created += 1

    # Mark materials as assets
    for mat in bpy.data.materials:
        if mat.name in {"Material", "Dots Stroke", "None"}:
            continue
        if mat.users > 0:
            try:
                mat.asset_mark()
                if mat.asset_data:
                    mat.asset_data.author = "KitBash3D"
                    mat.asset_data.description = f"KitBash3D {config.name} material"
                    if not mat.preview:
                        bpy.ops.asset.generate_preview({"id": mat})
                result.materials_created += 1
            except Exception:
                pass

    # Save
    output_path = output_dir / f"{config.name}_assets.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    result.output_path = output_path

    return result


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run batch conversion."""
    import argparse

    parser = argparse.ArgumentParser(description="Convert KitBash3D kits")
    parser.add_argument("--kit", help="Convert specific kit by name")
    parser.add_argument("--type", choices=["obj_fbx", "native_blend", "all"],
                        default="all", help="Kit type to convert")
    parser.add_argument("--list", action="store_true", help="List kits and exit")
    args, _ = parser.parse_known_args()

    output_root = Path("/Volumes/Storage/3d/kitbash/converted_assets")

    print("=" * 50)
    print("KitBash3D Batch Converter")
    print("=" * 50)

    # List mode (doesn't need Blender)
    if args.list:
        print("\nAvailable Kits:")
        print("-" * 50)
        for kit in KITS:
            status = "✓ DONE" if "COMPLETED" in kit.notes else ""
            print(f"  {kit.name:<20} [{kit.kit_type}] {status}")
            if kit.notes and "COMPLETED" not in kit.notes:
                print(f"    → {kit.notes}")

        print("\nUsage:")
        print("  List kits:     blender --background --python convert_all_kits.py -- --list")
        print("  Convert all:   blender --background --python convert_all_kits.py")
        print("  Convert one:   blender --background --python convert_all_kits.py -- --kit Dieselpunk")

        # Exit Blender if running in that context
        try:
            import bpy
            bpy.ops.wm.quit_blender()
        except ImportError:
            pass
        return

    # Filter kits
    kits_to_convert = KITS
    if args.kit:
        kits_to_convert = [k for k in KITS if args.kit.lower() in k.name.lower()]
        if not kits_to_convert:
            print(f"Kit '{args.kit}' not found")
            return

    # Skip already completed
    kits_to_convert = [k for k in kits_to_convert if "COMPLETED" not in k.notes]

    print(f"\nConverting {len(kits_to_convert)} kits...")
    print()

    results = []

    for kit in kits_to_convert:
        print(f"Converting: {kit.name} ({kit.kit_type})")

        try:
            if kit.kit_type == "obj_fbx":
                result = convert_obj_fbx_kit(kit, output_root)
            elif kit.kit_type == "native_blend":
                result = convert_native_blend_kit(kit, output_root)
            elif kit.kit_type == "hybrid":
                result = convert_hybrid_kit(kit, output_root)
            elif kit.kit_type == "fbx_only":
                result = convert_fbx_only_kit(kit, output_root)
            else:
                result = ConversionResult(pack_name=kit.name)
                result.errors.append(f"Unknown kit type: {kit.kit_type}")

            results.append((kit, result))

            if result.is_success():
                if hasattr(result, 'objects_extracted'):
                    print(f"  ✓ Extracted {result.objects_extracted} objects, {result.materials_found} materials")
                else:
                    print(f"  ✓ Created {result.objects_created} objects, {result.materials_created} materials")
                print(f"    Output: {result.output_path}")
            else:
                print(f"  ✗ Failed: {result.errors}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append((kit, ConversionResult(pack_name=kit.name, errors=[str(e)])))

        print()

    # Summary
    print("=" * 50)
    print("Conversion Summary")
    print("=" * 50)

    success_count = sum(1 for _, r in results if r.is_success())
    print(f"Successful: {success_count}/{len(results)}")

    for kit, result in results:
        status = "✓" if result.is_success() else "✗"
        print(f"  {status} {kit.name}")


if __name__ == "__main__":
    main()
