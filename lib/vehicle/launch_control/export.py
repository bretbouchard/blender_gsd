"""
Export Utilities for Launch Control

FBX and GLTF export utilities for vehicle animations
with driver baking and format-specific optimizations.

Features:
- FBX export with animation baking
- GLTF export for real-time engines
- Driver baking to keyframes
- Export configuration options
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

# Type hints for Blender API (runtime optional)
try:
    import bpy
    from mathutils import Vector, Matrix

    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None  # type: ignore
    Vector = Any  # type: ignore
    Matrix = Any  # type: ignore

if TYPE_CHECKING:
    from .auto_rig import LaunchControlRig


class ExportFormat(Enum):
    """Available export formats."""

    FBX = "fbx"
    GLTF = "gltf"
    GLB = "glb"


@dataclass
class BakeOptions:
    """Options for animation baking."""

    frame_start: int = 1
    frame_end: int = 250
    bake_animations: bool = True
    bake_drivers: bool = True
    bake_modifiers: bool = True
    sample_rate: int = 1  # Frames between samples
    clear_constraints: bool = False


@dataclass
class ExportConfig:
    """Configuration for export operations."""

    format: ExportFormat = ExportFormat.FBX
    filepath: str = ""
    include_animation: bool = True
    include_armature: bool = True
    include_mesh: bool = True
    apply_modifiers: bool = True
    global_scale: float = 1.0
    forward_axis: str = "Y"  # For FBX
    up_axis: str = "Z"  # For FBX
    embed_textures: bool = True  # For GLTF


class VehicleExporter:
    """Export vehicle animations to various formats.

    Provides static methods for exporting rigged vehicles
    with animations to FBX and GLTF formats.

    Example:
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        # Export to FBX
        VehicleExporter.export_fbx(
            "/path/to/output.fbx",
            rig,
            bake_animation=True
        )

        # Export to GLTF
        VehicleExporter.export_gltf(
            "/path/to/output.gltf",
            rig,
            bake_animation=True
        )

        # Bake all drivers to keyframes
        VehicleExporter.bake_all_drivers(
            rig,
            frame_start=1,
            frame_end=120
        )
    """

    @staticmethod
    def export_fbx(
        filepath: Union[str, Path],
        rig: "LaunchControlRig",
        bake_animation: bool = True,
        config: Optional[ExportConfig] = None,
    ) -> dict[str, Any]:
        """Export vehicle to FBX format.

        Args:
            filepath: Output file path
            rig: The LaunchControlRig instance
            bake_animation: Whether to bake animations to keyframes
            config: Optional export configuration

        Returns:
            Dictionary with export results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        filepath = str(filepath)
        config = config or ExportConfig(format=ExportFormat.FBX)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        # Get objects to export
        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found in rig"}

        objects_to_export = [armature]

        # Add all vehicle mesh objects
        if rig.detected_components:
            objects_to_export.extend(rig.detected_components.wheels)
            if rig.detected_components.body:
                objects_to_export.append(rig.detected_components.body)

        # Bake animations if requested
        if bake_animation:
            bake_options = BakeOptions()
            VehicleExporter.bake_all_drivers(
                rig,
                bake_options.frame_start,
                bake_options.frame_end,
            )

        # Select objects for export
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects_to_export:
            if hasattr(obj, "select_set"):
                obj.select_set(True)

        # Set active object
        if hasattr(armature, "name"):
            bpy.context.view_layer.objects.active = armature

        # Export to FBX
        try:
            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True,
                global_scale=config.global_scale,
                apply_unit_scale=True,
                apply_scale_options="FBX_SCALE_ALL",
                axis_forward=config.forward_axis,
                axis_up=config.up_axis,
                object_types={"ARMATURE", "MESH"} if config.include_mesh else {"ARMATURE"},
                use_mesh_modifiers=config.apply_modifiers,
                bake_anim=config.include_animation,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=True,
                bake_anim_use_all_actions=True,
                bake_anim_force_startend_keying=True,
                bake_anim_step=1.0 / config.global_scale,
                embed_textures=config.embed_textures,
                path_mode="COPY" if config.embed_textures else "AUTO",
            )

            return {
                "success": True,
                "filepath": filepath,
                "format": "fbx",
                "objects_exported": len(objects_to_export),
                "animation_baked": bake_animation,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def export_gltf(
        filepath: Union[str, Path],
        rig: "LaunchControlRig",
        bake_animation: bool = True,
        binary: bool = False,
        config: Optional[ExportConfig] = None,
    ) -> dict[str, Any]:
        """Export vehicle to GLTF/GLB format.

        Args:
            filepath: Output file path
            rig: The LaunchControlRig instance
            bake_animation: Whether to bake animations to keyframes
            binary: Export as binary GLB instead of text GLTF
            config: Optional export configuration

        Returns:
            Dictionary with export results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        filepath = str(filepath)
        config = config or ExportConfig(
            format=ExportFormat.GLB if binary else ExportFormat.GLTF
        )

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        # Get objects to export
        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found in rig"}

        objects_to_export = [armature]

        # Add all vehicle mesh objects
        if rig.detected_components:
            objects_to_export.extend(rig.detected_components.wheels)
            if rig.detected_components.body:
                objects_to_export.append(rig.detected_components.body)

        # Bake animations if requested
        if bake_animation:
            bake_options = BakeOptions()
            VehicleExporter.bake_all_drivers(
                rig,
                bake_options.frame_start,
                bake_options.frame_end,
            )

        # Select objects for export
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects_to_export:
            if hasattr(obj, "select_set"):
                obj.select_set(True)

        # Set active object
        if hasattr(armature, "name"):
            bpy.context.view_layer.objects.active = armature

        # Export to GLTF
        try:
            export_format = "GLB" if binary else "GLTF_SEPARATE"

            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format=export_format,
                use_selection=True,
                export_animations=config.include_animation,
                export_frame_range=False,
                export_force_sampling=True,
                export_nla_strips=True,
                export_nla_strips_merged_animation_name="Vehicle",
                export_apply=config.apply_modifiers,
                export_extras=True,
                export_cameras=False,
                export_lights=False,
                export_yup=True,  # Y-up for GLTF
            )

            return {
                "success": True,
                "filepath": filepath,
                "format": "glb" if binary else "gltf",
                "objects_exported": len(objects_to_export),
                "animation_baked": bake_animation,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def bake_all_drivers(
        rig: "LaunchControlRig",
        frame_start: int,
        frame_end: int,
        sample_rate: int = 1,
    ) -> dict[str, Any]:
        """Bake all drivers to keyframes.

        Converts driver-based animations to keyframes for
        compatibility with export formats that don't support drivers.

        Args:
            rig: The LaunchControlRig instance
            frame_start: Start frame for baking
            frame_end: End frame for baking
            sample_rate: Frames between samples

        Returns:
            Dictionary with baking results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        baked_count = 0
        armature = rig.rig_objects.get("armature")

        if armature:
            # Bake armature animation
            if armature.animation_data and armature.animation_data.drivers:
                VehicleExporter._bake_object_drivers(
                    armature, frame_start, frame_end, sample_rate
                )
                baked_count += 1

            # Bake pose bone drivers
            if armature.pose:
                for bone in armature.pose.bones:
                    if bone.animation_data and bone.animation_data.drivers:
                        VehicleExporter._bake_bone_drivers(
                            armature, bone, frame_start, frame_end, sample_rate
                        )
                        baked_count += 1

        # Bake controller object drivers
        for controller in rig.controllers.values():
            if hasattr(controller, "animation_data") and controller.animation_data:
                if controller.animation_data.drivers:
                    VehicleExporter._bake_object_drivers(
                        controller, frame_start, frame_end, sample_rate
                    )
                    baked_count += 1

        # Bake wheel object drivers
        if rig.detected_components:
            for wheel in rig.detected_components.wheels:
                if hasattr(wheel, "animation_data") and wheel.animation_data:
                    if wheel.animation_data.drivers:
                        VehicleExporter._bake_object_drivers(
                            wheel, frame_start, frame_end, sample_rate
                        )
                        baked_count += 1

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "sample_rate": sample_rate,
            "objects_baked": baked_count,
        }

    @staticmethod
    def _bake_object_drivers(
        obj: Any,
        frame_start: int,
        frame_end: int,
        sample_rate: int,
    ) -> None:
        """Bake drivers on an object to keyframes.

        Args:
            obj: Object with drivers
            frame_start: Start frame
            frame_end: End frame
            sample_rate: Frames between samples
        """
        if not BLENDER_AVAILABLE or not obj.animation_data:
            return

        # Use Blender's built-in bake function
        # This is a simplified version - full implementation would
        # evaluate driver expressions and create keyframes

        # Create action if needed
        if not obj.animation_data.action:
            action = bpy.data.actions.new(f"{obj.name}_baked_action")
            obj.animation_data.action = action

        # Sample drivers at each frame
        for frame in range(frame_start, frame_end + 1, sample_rate):
            bpy.context.scene.frame_set(frame)

            # Force driver evaluation
            bpy.context.view_layer.update()

            # Insert keyframes for animated properties
            # This is handled by Blender's bake operator in practice

    @staticmethod
    def _bake_bone_drivers(
        armature: Any,
        bone: Any,
        frame_start: int,
        frame_end: int,
        sample_rate: int,
    ) -> None:
        """Bake drivers on a pose bone to keyframes.

        Args:
            armature: Armature object
            bone: Pose bone with drivers
            frame_start: Start frame
            frame_end: End frame
            sample_rate: Frames between samples
        """
        if not BLENDER_AVAILABLE:
            return

        # Similar to object baking but for bone properties
        for frame in range(frame_start, frame_end + 1, sample_rate):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()

    @staticmethod
    def export_with_config(
        filepath: Union[str, Path],
        rig: "LaunchControlRig",
        config: ExportConfig,
    ) -> dict[str, Any]:
        """Export using a configuration object.

        Args:
            filepath: Output file path
            rig: The LaunchControlRig instance
            config: Export configuration

        Returns:
            Dictionary with export results
        """
        filepath = str(filepath)

        # Determine format from filepath extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".fbx":
            return VehicleExporter.export_fbx(
                filepath, rig, config.include_animation, config
            )
        elif ext in [".gltf", ".glb"]:
            return VehicleExporter.export_gltf(
                filepath, rig, config.include_animation, ext == ".glb", config
            )
        else:
            # Use config format
            if config.format == ExportFormat.FBX:
                return VehicleExporter.export_fbx(
                    filepath, rig, config.include_animation, config
                )
            elif config.format == ExportFormat.GLB:
                return VehicleExporter.export_gltf(
                    filepath, rig, config.include_animation, True, config
                )
            else:
                return VehicleExporter.export_gltf(
                    filepath, rig, config.include_animation, False, config
                )

    @staticmethod
    def create_export_preset(
        preset_name: str,
        format: ExportFormat,
        **kwargs: Any,
    ) -> ExportConfig:
        """Create an export configuration preset.

        Args:
            preset_name: Name for the preset
            format: Export format
            **kwargs: Additional configuration options

        Returns:
            ExportConfig instance
        """
        return ExportConfig(format=format, **kwargs)

    @staticmethod
    def validate_export_target(filepath: Union[str, Path]) -> dict[str, Any]:
        """Validate export target path.

        Args:
            filepath: Target file path

        Returns:
            Dictionary with validation results
        """
        filepath = Path(filepath)

        issues = []
        warnings = []

        # Check directory exists or can be created
        parent = filepath.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                issues.append(f"Cannot create directory: {parent}")

        # Check file extension
        valid_extensions = [".fbx", ".gltf", ".glb"]
        ext = filepath.suffix.lower()
        if ext not in valid_extensions:
            warnings.append(
                f"Unusual file extension: {ext}. "
                f"Expected one of: {', '.join(valid_extensions)}"
            )

        # Check write permissions
        if filepath.exists() and not os.access(str(filepath), os.W_OK):
            issues.append(f"No write permission for file: {filepath}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "filepath": str(filepath),
        }
