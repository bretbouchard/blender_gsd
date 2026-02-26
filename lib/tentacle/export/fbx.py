"""
Tentacle FBX Exporter

FBX export for Unreal Engine with skeleton, morph targets, and skin weights.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import os

try:
    import bpy
    from bpy.types import Object, Armature
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Armature = None

from .types import FBXExportConfig, ExportResult, MaterialSlotResult


class FBXExporter:
    """Export tentacle meshes to FBX for Unreal Engine."""

    def __init__(self, config: FBXExportConfig):
        """Initialize FBX exporter.

        Args:
            config: FBX export configuration
        """
        self.config = config

    def export(
        self,
        mesh_obj: Optional["Object"] = None,
        armature_obj: Optional["Object"] = None,
        output_path: Optional[str] = None,
    ) -> ExportResult:
        """Export mesh to FBX.

        Args:
            mesh_obj: Mesh object to export
            armature_obj: Optional armature for skeletal mesh
            output_path: Output file path (uses config default if None)

        Returns:
            ExportResult with export details
        """
        if not BLENDER_AVAILABLE:
            return ExportResult(
                success=False,
                output_path="",
                error="Blender not available for FBX export",
            )

        if mesh_obj is None:
            return ExportResult(
                success=False,
                output_path="",
                error="mesh_obj required for export",
            )

        output_path = output_path or self.config.output_path

        try:
            # Prepare objects for export
            objects_to_export = [mesh_obj]
            if armature_obj is not None:
                objects_to_export.append(armature_obj)

            # Select objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_export:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = mesh_obj

            # Build export kwargs
            export_kwargs = self._build_export_kwargs(output_path, mesh_obj, armature_obj)

            # Export FBX
            bpy.ops.export_scene.fbx(**export_kwargs)

            # Get file size
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

            return ExportResult(
                success=True,
                output_path=output_path,
                triangle_count=len(mesh_obj.data.polygons),
                vertex_count=len(mesh_obj.data.vertices),
                material_slots=len(mesh_obj.material_slots),
                has_skeleton=armature_obj is not None,
                has_morph_targets=self.config.include_shape_keys,
                file_size_bytes=file_size,
            )

        except Exception as e:
            return ExportResult(
                success=False,
                output_path=output_path or "",
                error=str(e),
            )

    def _build_export_kwargs(
        self,
        output_path: str,
        mesh_obj: "Object",
        armature_obj: Optional["Object"],
    ) -> Dict[str, Any]:
        """Build kwargs for bpy.ops.export_scene.fbx."""
        kwargs = {
            'filepath': output_path,
            'use_selection': True,
            'global_scale': self.config.global_scale,
            'apply_unit_scale': True,
            'apply_scale_options': 'FBX_SCALE_ALL',
            'axis_forward': self.config.axis_forward,
            'axis_up': self.config.axis_up,
            'object_types': {'MESH'},
            'use_mesh_modifiers': self.config.apply_modifiers,
            'mesh_smooth_type': self.config.smoothing_mode,
            'use_tspace': self.config.tangent_space,
            'embed_textures': self.config.embed_textures,
            'path_mode': 'COPY' if not self.config.embed_textures else 'AUTO',
        }

        # Add armature settings
        if armature_obj is not None:
            kwargs['object_types'].add('ARMATURE')
            kwargs['use_armature_deform_add_only'] = False
            kwargs['primary_bone_axis'] = 'Y'
            kwargs['secondary_bone_axis'] = 'X'
            kwargs['armature_nodetype'] = 'ROOT'

        # Add shape key settings
        if self.config.include_shape_keys:
            if mesh_obj.data.shape_keys:
                kwargs['bake_anim_use'] = False  # Don't bake animation
                # Shape keys are included by default when present

        return kwargs

    def export_lod_set(
        self,
        lod_objects: List["Object"],
        armature_obj: Optional["Object"] = None,
        output_path: Optional[str] = None,
    ) -> List[ExportResult]:
        """Export LOD set as separate FBX files.

        Args:
            lod_objects: List of LOD mesh objects (LOD0, LOD1, etc.)
            armature_obj: Optional armature for skeletal mesh
            output_path: Base output path (_LOD0.fbx, _LOD1.fbx appended)

        Returns:
            List of ExportResult for each LOD
        """
        results = []

        if output_path:
            base_path = Path(output_path).with_suffix('')
        else:
            base_path = Path(self.config.output_path).with_suffix('')

        for i, lod_obj in enumerate(lod_objects):
            lod_path = f"{base_path}_LOD{i}.fbx"
            result = self.export(
                mesh_obj=lod_obj,
                armature_obj=armature_obj,
                output_path=lod_path,
            )
            result.lod_level = i
            results.append(result)

        return results


def export_for_unreal(
    mesh_obj: "Object",
    output_path: str,
    armature_obj: Optional["Object"] = None,
    include_shape_keys: bool = True,
) -> ExportResult:
    """Convenience function for Unreal-optimized FBX export.

    Args:
        mesh_obj: Mesh to export
        output_path: Output file path
        armature_obj: Optional armature
        include_shape_keys: Include morph targets

    Returns:
        ExportResult with export details
    """
    config = FBXExportConfig(
        output_path=output_path,
        include_shape_keys=include_shape_keys,
    )
    exporter = FBXExporter(config)
    return exporter.export(mesh_obj, armature_obj)


def export_tentacle_fbx(
    tentacle_result,  # TentacleResult from geometry.body
    output_path: str,
    rig_result=None,  # RigResult from animation.rig
) -> ExportResult:
    """Export complete tentacle with optional rig.

    Args:
        tentacle_result: TentacleResult from body generator
        output_path: Output file path
        rig_result: Optional RigResult from rig generator

    Returns:
        ExportResult with export details
    """
    if not BLENDER_AVAILABLE:
        return ExportResult(
            success=False,
            output_path=output_path,
            error="Blender not available",
        )

    mesh_obj = tentacle_result.object
    armature_obj = rig_result.mesh_object if rig_result else None

    # Check if rig was generated
    has_rig = rig_result is not None and rig_result.success

    config = FBXExportConfig(
        output_path=output_path,
        include_shape_keys=True,
    )
    exporter = FBXExporter(config)

    return exporter.export(
        mesh_obj=mesh_obj,
        armature_obj=armature_obj if has_rig else None,
    )
