"""
KitBash3D Asset Converter for Blender Asset Browser.

Converts KitBash3D OBJ/FBX packs to individual Blender assets
with PBR materials, ready for the Asset Browser.

Usage:
    # In Blender Python console:
    from lib.assets import KitBashConverter

    converter = KitBashConverter()
    result = converter.convert_pack(
        pack_name="Aftermath",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Aftermath",
        output_dir="/Volumes/Storage/3d/kitbash/converted_assets/Aftermath",
    )

    print(f"Converted {result.objects_created} objects")
    print(f"Created {result.materials_created} materials")
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .material_builder import PBRMaterialBuilder, TextureSet

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, Material, Collection


@dataclass
class ConversionResult:
    """Result of a KitBash pack conversion."""

    pack_name: str
    """Name of the converted pack."""

    output_path: Path | None = None
    """Path to the created .blend file."""

    objects_created: int = 0
    """Number of objects converted."""

    materials_created: int = 0
    """Number of materials created."""

    textures_linked: int = 0
    """Number of texture files linked."""

    warnings: list[str] = field(default_factory=list)
    """Non-fatal issues encountered."""

    errors: list[str] = field(default_factory=list)
    """Fatal errors that stopped conversion."""

    def is_success(self) -> bool:
        """Check if conversion was successful."""
        return self.output_path is not None and len(self.errors) == 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "pack_name": self.pack_name,
            "output_path": str(self.output_path) if self.output_path else None,
            "objects_created": self.objects_created,
            "materials_created": self.materials_created,
            "textures_linked": self.textures_linked,
            "warnings": self.warnings,
            "errors": self.errors,
            "success": self.is_success(),
        }


@dataclass
class PackInfo:
    """Information about a KitBash pack."""

    name: str
    """Pack name."""

    source_path: Path
    """Path to pack directory."""

    obj_file: Path | None = None
    """Main OBJ file."""

    fbx_file: Path | None = None
    """Main FBX file."""

    texture_dir: Path | None = None
    """Texture directory."""

    material_names: list[str] = field(default_factory=list)
    """Materials detected from MTL file."""

    def has_source(self) -> bool:
        """Check if pack has importable source."""
        return self.obj_file is not None or self.fbx_file is not None


class KitBashConverter:
    """
    Converts KitBash3D packs to Blender Asset Browser format.

    Process:
    1. Import OBJ/FBX file
    2. Separate mesh by material into individual objects
    3. Build PBR materials from texture files
    4. Mark objects as assets with metadata
    5. Save as asset library .blend

    Example:
        >>> converter = KitBashConverter()
        >>> result = converter.convert_pack("Aftermath", source, output)
        >>> if result.is_success():
        ...     print(f"Created {result.output_path}")
    """

    # Common KitBash texture prefixes
    TEXTURE_PREFIXES = [
        "KB3D_WZT",  # Warzone/Aftermath
        "KB3D_CYB",  # Cyberpunk
        "KB3D_AM",   # Americana
        "KB3D_EJ",   # Edo Japan
        "KB3D_AP",   # Atompunk
        "KB3D_DP",   # Dieselpunk
        "KB3D",      # Generic
    ]

    def __init__(self):
        """Initialize the converter."""
        self.material_builder = PBRMaterialBuilder()

    def scan_pack(self, pack_path: Path) -> PackInfo:
        """
        Scan a KitBash pack directory and gather info.

        Args:
            pack_path: Path to pack directory

        Returns:
            PackInfo with detected files and structure.
        """
        pack_name = pack_path.name
        info = PackInfo(
            name=pack_name,
            source_path=pack_path,
        )

        if not pack_path.exists():
            return info

        # Find OBJ/FBX files
        for file_path in pack_path.glob("*.obj"):
            info.obj_file = file_path
            break

        for file_path in pack_path.glob("*.fbx"):
            info.fbx_file = file_path
            break

        # Find texture directories
        for dir_name in ["KB3DTextures", "Textures", "textures", "maps"]:
            tex_dir = pack_path / dir_name
            if tex_dir.exists():
                info.texture_dir = tex_dir
                break

        # Parse MTL for material names
        mtl_file = None
        for pattern in ["*.mtl"]:
            for f in pack_path.glob(pattern):
                mtl_file = f
                break
            if mtl_file:
                break

        if mtl_file:
            info.material_names = self._parse_mtl_materials(mtl_file)

        return info

    def _parse_mtl_materials(self, mtl_path: Path) -> list[str]:
        """Extract material names from MTL file."""
        materials = []
        with open(mtl_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("newmtl "):
                    mat_name = line[7:].strip()
                    materials.append(mat_name)
        return materials

    def convert_pack(
        self,
        pack_name: str,
        source_dir: Path | str,
        output_dir: Path | str,
        prefix: str | None = None,
        split_by_material: bool = True,
        generate_previews: bool = True,
        copy_textures: bool = False,
    ) -> ConversionResult:
        """
        Convert a KitBash pack to Blender asset library.

        Args:
            pack_name: Name for the pack (used for output file)
            source_dir: Source pack directory
            output_dir: Output directory for .blend file
            prefix: Texture prefix (auto-detected if None)
            split_by_material: Split mesh into objects by material
            generate_previews: Generate asset previews
            copy_textures: Copy textures to output (otherwise keep references)

        Returns:
            ConversionResult with details and status.
        """
        import bpy

        source_dir = Path(source_dir)
        output_dir = Path(output_dir)

        result = ConversionResult(pack_name=pack_name)

        # Scan pack
        pack_info = self.scan_pack(source_dir)

        if not pack_info.has_source():
            result.errors.append(f"No OBJ or FBX file found in {source_dir}")
            return result

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Detect texture prefix
        if prefix is None:
            prefix = self._detect_texture_prefix(pack_info)

        # Create new blend file
        bpy.ops.wm.read_homefile(app_template="")

        # Import the file
        if pack_info.obj_file:
            imported = self._import_obj(pack_info.obj_file)
        else:
            imported = self._import_fbx(pack_info.fbx_file)
            # FBX returns objects directly
            imported = list(bpy.context.selected_objects)

        if not imported:
            result.errors.append("No objects imported")
            return result

        # Create a collection for the pack
        pack_collection = bpy.data.collections.new(pack_name)
        bpy.context.scene.collection.children.link(pack_collection)

        # Build materials from textures
        if pack_info.texture_dir and pack_info.material_names:
            self._build_materials(
                pack_info.material_names,
                pack_info.texture_dir,
                prefix,
                result,
            )

        # Process objects
        objects_to_process = []
        objects_to_cleanup = []  # Track objects that need cleanup

        if split_by_material:
            # Split meshes by material
            for obj in imported:
                if obj.type == "MESH":
                    # _split_by_material removes the original and creates new ones
                    split_objects = self._split_by_material(obj, pack_collection)
                    objects_to_process.extend(split_objects)
                    # Original object was already removed by _split_by_material
                else:
                    objects_to_process.append(obj)
                    pack_collection.objects.link(obj)
        else:
            objects_to_process = list(imported)
            for obj in imported:
                if obj not in pack_collection.objects.values():
                    pack_collection.objects.link(obj)

        # Clean up any remaining original objects that weren't processed
        for obj in imported:
            try:
                # Check if object still exists and isn't in our result set
                if obj and obj.name in bpy.data.objects and obj not in objects_to_process:
                    bpy.data.objects.remove(obj, do_unlink=True)
            except ReferenceError:
                # Object was already removed
                pass

        # Mark objects as assets
        for obj in objects_to_process:
            self._mark_as_asset(obj, pack_name, generate_previews)
            result.objects_created += 1

        # Save blend file
        output_path = output_dir / f"{pack_name}_assets.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

        result.output_path = output_path

        # Save metadata
        metadata_path = output_dir / f"{pack_name}_conversion.json"
        with open(metadata_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        return result

    def _detect_texture_prefix(self, pack_info: PackInfo) -> str:
        """Detect texture naming prefix from pack."""
        if not pack_info.texture_dir:
            return "KB3D"

        # Look at texture files
        for tex_file in pack_info.texture_dir.glob("*.jpg"):
            name = tex_file.stem
            # Find prefix pattern (e.g., KB3D_WZT_assetsA_basecolor)
            # Use [A-Z0-9]+ to handle prefixes with digits like KB3D
            match = re.match(r"([A-Z0-9]+_[A-Z0-9]+)_", name)
            if match:
                return match.group(1)

        return "KB3D"

    def _import_obj(self, obj_path: Path) -> list[Object]:
        """Import OBJ file."""
        import bpy

        bpy.ops.object.select_all(action="DESELECT")

        # Blender 5.0+ uses wm.obj_import
        try:
            bpy.ops.wm.obj_import(
                filepath=str(obj_path),
            )
        except AttributeError:
            # Fallback for older Blender versions
            bpy.ops.import_scene.obj(
                filepath=str(obj_path),
                use_split_objects=False,
                use_split_groups=False,
            )

        return list(bpy.context.selected_objects)

    def _import_fbx(self, fbx_path: Path) -> list[Object]:
        """Import FBX file."""
        import bpy

        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.import_scene.fbx(
            filepath=str(fbx_path),
            use_custom_normals=True,
            ignore_leaf_bones=True,
        )

        return list(bpy.context.selected_objects)

    def _build_materials(
        self,
        material_names: list[str],
        texture_dir: Path,
        prefix: str,
        result: ConversionResult,
    ):
        """Build PBR materials from textures."""
        import bpy

        for mat_name in material_names:
            # Try to build material from textures
            build_result = self.material_builder.build_from_kitbash_textures(
                mat_name,
                texture_dir,
                prefix,
            )

            if build_result.material:
                result.materials_created += 1
                result.warnings.extend(build_result.warnings)

                # Replace any imported material with our PBR version
                for obj in bpy.data.objects:
                    for slot in obj.material_slots:
                        if slot.material and slot.material.name == mat_name:
                            slot.material = build_result.material
            else:
                result.warnings.extend(build_result.errors)

    def _split_by_material(
        self,
        obj: Object,
        collection: Collection,
    ) -> list[Object]:
        """Split a mesh into separate objects by material."""
        import bpy
        import bmesh

        if not obj.data.materials:
            # No materials, return as-is
            if obj.name not in collection.objects:
                collection.objects.link(obj)
            return [obj]

        result_objects = []

        # Create a bmesh from the object
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        # Get material slots
        materials = obj.data.materials

        for mat_idx, mat in enumerate(materials):
            if mat is None:
                continue

            # Select faces with this material
            bmesh.ops.split_edges(
                bm,
                edges=[e for e in bm.edges if e.seam],
            )

            # Get faces for this material
            faces = [f for f in bm.faces if f.material_index == mat_idx]

            if not faces:
                continue

            # Create new object for this material
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            new_obj.name = f"{obj.name}_{mat.name}"
            collection.objects.link(new_obj)

            # Delete all other faces
            new_bm = bmesh.new()
            new_bm.from_mesh(new_obj.data)

            # Remove faces not belonging to this material
            faces_to_remove = [
                f for f in new_bm.faces if f.material_index != mat_idx
            ]
            bmesh.ops.delete(new_bm, geom=faces_to_remove, context="FACES")

            new_bm.to_mesh(new_obj.data)
            new_bm.free()

            # Clean up unused material slots
            for i in reversed(range(len(new_obj.material_slots))):
                if i != 0:
                    new_obj.active_material_index = i
                    bpy.context.view_layer.objects.active = new_obj
                    bpy.ops.object.material_slot_remove()

            result_objects.append(new_obj)

        bm.free()

        # Remove original object
        bpy.data.objects.remove(obj, do_unlink=True)

        return result_objects

    def _mark_as_asset(
        self,
        obj: Object,
        pack_name: str,
        generate_preview: bool,
    ):
        """Mark an object as a Blender asset."""
        import bpy

        # Mark as asset
        obj.asset_mark()

        # Set metadata
        if obj.asset_data:
            obj.asset_data.description = f"KitBash3D {pack_name} asset"
            obj.asset_data.author = "KitBash3D"

            # Add tags
            tag_names = [t.name.lower() for t in obj.asset_data.tags]

            # Add pack name as tag
            tag_name = pack_name.lower().replace(" ", "_")
            if tag_name not in tag_names:
                obj.asset_data.tags.new(tag_name)

            # Add category tags based on name
            name_lower = obj.name.lower()
            if any(x in name_lower for x in ["wall", "floor", "ceiling", "roof"]):
                if "architecture" not in tag_names:
                    obj.asset_data.tags.new("architecture")
            if any(x in name_lower for x in ["door", "window", "gate"]):
                if "fixture" not in tag_names:
                    obj.asset_data.tags.new("fixture")
            if any(x in name_lower for x in ["prop", "item", "object"]):
                if "prop" not in tag_names:
                    obj.asset_data.tags.new("prop")

            # Generate preview
            if generate_preview:
                try:
                    bpy.ops.ed.lib_id_generate_preview({"id": obj})
                except Exception:
                    pass  # Preview generation can fail in headless mode

    def batch_convert(
        self,
        source_root: Path | str,
        output_root: Path | str,
        pack_names: list[str] | None = None,
    ) -> list[ConversionResult]:
        """
        Convert multiple KitBash packs.

        Args:
            source_root: Root directory containing pack folders
            output_root: Output root directory
            pack_names: Specific packs to convert (None = all)

        Returns:
            List of ConversionResults for each pack.
        """
        source_root = Path(source_root)
        output_root = Path(output_root)

        results = []

        # Find pack directories
        pack_dirs = []
        for item in source_root.iterdir():
            if item.is_dir() and "KitBash" in item.name:
                pack_dirs.append(item)

        # Filter to specific packs if requested
        if pack_names:
            pack_dirs = [
                d for d in pack_dirs
                if any(name.lower() in d.name.lower() for name in pack_names)
            ]

        # Convert each pack
        for pack_dir in pack_dirs:
            pack_name = pack_dir.name.replace("KitBash3D - ", "").replace("KitBash3D-", "")
            output_dir = output_root / pack_name

            print(f"Converting: {pack_name}")
            result = self.convert_pack(
                pack_name=pack_name,
                source_dir=pack_dir,
                output_dir=output_dir,
            )
            results.append(result)

            if result.is_success():
                print(f"  ✓ Created {result.objects_created} objects")
            else:
                print(f"  ✗ Failed: {result.errors}")

        return results
