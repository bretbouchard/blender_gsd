"""
Blender operators for KitBash3D asset conversion.

Provides UI operators and panels for the conversion workflow.

Usage:
    # Operators appear in:
    # - View3D > Sidebar > KitBash Tools
    # - Search (F3) > "Convert KitBash Pack"
"""

from __future__ import annotations

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from pathlib import Path

from .converter import KitBashConverter, ConversionResult


class KitBashConversionSettings(PropertyGroup):
    """Settings for KitBash conversion."""

    source_dir: StringProperty(
        name="Source Directory",
        description="Directory containing KitBash3D packs",
        default="/Volumes/Storage/3d/kitbash",
        subtype="DIR_PATH",
    )

    output_dir: StringProperty(
        name="Output Directory",
        description="Directory for converted assets",
        default="/Volumes/Storage/3d/kitbash/converted_assets",
        subtype="DIR_PATH",
    )

    pack_name: StringProperty(
        name="Pack Name",
        description="Name of the pack to convert (leave empty for all)",
        default="",
    )

    split_by_material: BoolProperty(
        name="Split by Material",
        description="Split mesh into separate objects by material",
        default=True,
    )

    generate_previews: BoolProperty(
        name="Generate Previews",
        description="Generate asset browser previews",
        default=True,
    )

    texture_prefix: StringProperty(
        name="Texture Prefix",
        description="Override texture prefix (auto-detected if empty)",
        default="",
    )


class OBJECT_OT_convert_kitbash_pack(Operator):
    """Convert a KitBash3D pack to Blender assets."""

    bl_idname = "kitbash.convert_pack"
    bl_label = "Convert KitBash Pack"
    bl_description = "Convert a KitBash3D pack to individual Blender assets"
    bl_options = {"REGISTER", "UNDO"}

    pack_name: StringProperty(
        name="Pack Name",
        description="Name of the pack to convert",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.kitbash_settings

        source_dir = Path(settings.source_dir)
        output_dir = Path(settings.output_dir)

        if not source_dir.exists():
            self.report({"ERROR"}, f"Source directory not found: {source_dir}")
            return {"CANCELLED"}

        # Find pack directory
        pack_name = self.pack_name or settings.pack_name
        if not pack_name:
            self.report({"ERROR"}, "No pack name specified")
            return {"CANCELLED"}

        # Search for pack
        pack_dir = None
        for item in source_dir.iterdir():
            if item.is_dir() and pack_name.lower() in item.name.lower():
                pack_dir = item
                break

        if not pack_dir:
            self.report({"ERROR"}, f"Pack not found: {pack_name}")
            return {"CANCELLED"}

        # Get prefix override
        prefix = settings.texture_prefix if settings.texture_prefix else None

        # Run conversion
        converter = KitBashConverter()
        result = converter.convert_pack(
            pack_name=pack_name,
            source_dir=pack_dir,
            output_dir=output_dir / pack_name,
            prefix=prefix,
            split_by_material=settings.split_by_material,
            generate_previews=settings.generate_previews,
        )

        if result.is_success():
            self.report(
                {"INFO"},
                f"Converted {result.objects_created} objects, "
                f"{result.materials_created} materials to {result.output_path}",
            )
            return {"FINISHED"}
        else:
            for error in result.errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}


class OBJECT_OT_scan_kitbash_packs(Operator):
    """Scan for available KitBash packs."""

    bl_idname = "kitbash.scan_packs"
    bl_label = "Scan KitBash Packs"
    bl_description = "Scan source directory for available KitBash packs"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.kitbash_settings
        source_dir = Path(settings.source_dir)

        if not source_dir.exists():
            self.report({"ERROR"}, f"Source directory not found: {source_dir}")
            return {"CANCELLED"}

        # Find packs
        packs = []
        for item in source_dir.iterdir():
            if item.is_dir() and "KitBash" in item.name:
                pack_name = item.name.replace("KitBash3D - ", "").replace("KitBash3D-", "")
                packs.append((item.name, pack_name))

        if packs:
            pack_list = "\n".join(f"  - {name}" for _, name in packs)
            self.report({"INFO"}, f"Found {len(packs)} packs:\n{pack_list}")
        else:
            self.report({"WARNING"}, "No KitBash packs found in source directory")

        return {"FINISHED"}


class OBJECT_OT_convert_all_packs(Operator):
    """Convert all found KitBash packs."""

    bl_idname = "kitbash.convert_all"
    bl_label = "Convert All Packs"
    bl_description = "Convert all found KitBash packs in the source directory"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.scene.kitbash_settings
        source_dir = Path(settings.source_dir)
        output_dir = Path(settings.output_dir)

        if not source_dir.exists():
            self.report({"ERROR"}, f"Source directory not found: {source_dir}")
            return {"CANCELLED"}

        converter = KitBashConverter()
        results = converter.batch_convert(source_dir, output_dir)

        # Count successes
        successes = sum(1 for r in results if r.is_success())
        total_objects = sum(r.objects_created for r in results)

        self.report(
            {"INFO"},
            f"Converted {successes}/{len(results)} packs, {total_objects} total objects",
        )

        return {"FINISHED"}


class VIEW3D_PT_kitbash_tools(Panel):
    """Panel for KitBash conversion tools."""

    bl_label = "KitBash Tools"
    bl_idname = "VIEW3D_PT_kitbash_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KitBash"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kitbash_settings

        # Directory settings
        box = layout.box()
        box.label(text="Directories", icon="FILE_FOLDER")
        box.prop(settings, "source_dir")
        box.prop(settings, "output_dir")

        # Pack settings
        box = layout.box()
        box.label(text="Conversion Settings", icon="MODIFIER")
        box.prop(settings, "pack_name")
        box.prop(settings, "texture_prefix")
        box.prop(settings, "split_by_material")
        box.prop(settings, "generate_previews")

        # Actions
        layout.separator()
        row = layout.row()
        row.operator("kitbash.scan_packs", icon="VIEWZOOM")

        row = layout.row()
        row.operator("kitbash.convert_pack", icon="IMPORT")

        row = layout.row()
        row.operator("kitbash.convert_all", icon="FILE_CACHE")


# List of classes to register
_classes = [
    KitBashConversionSettings,
    OBJECT_OT_convert_kitbash_pack,
    OBJECT_OT_scan_kitbash_packs,
    OBJECT_OT_convert_all_packs,
    VIEW3D_PT_kitbash_tools,
]


def register():
    """Register KitBash operators and panels."""
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.kitbash_settings = bpy.props.PointerProperty(
        type=KitBashConversionSettings
    )


def unregister():
    """Unregister KitBash operators and panels."""
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.kitbash_settings


if __name__ == "__main__":
    register()
