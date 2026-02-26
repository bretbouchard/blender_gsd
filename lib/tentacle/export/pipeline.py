"""
Tentacle Export Pipeline

Complete export pipeline combining LOD generation, material setup, and FBX export.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import time

try:
    import bpy
    from bpy.types import Object
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None

from .types import (
    ExportPreset,
    LODConfig,
    FBXExportConfig,
    ExportResult,
    LODResult,
)
from .lod import LODGenerator
from .fbx import FBXExporter


@dataclass
class PipelineResult:
    """Result of complete export pipeline."""
    success: bool
    output_directory: str = ""
    lod_results: List[LODResult] = field(default_factory=list)
    export_results: List[ExportResult] = field(default_factory=list)
    total_time_seconds: float = 0.0
    error: Optional[str] = None


class ExportPipeline:
    """Complete export pipeline for tentacle meshes."""

    def __init__(
        self,
        preset: Optional[ExportPreset] = None,
        output_dir: Optional[str] = None,
    ):
        """Initialize export pipeline.

        Args:
            preset: Export preset (uses default if None)
            output_dir: Output directory (uses preset default if None)
        """
        self.preset = preset or ExportPreset.default()
        self.output_dir = output_dir or self.preset.output_dir
        self.lod_config = self.preset.lod_config
        self.fbx_config = self.preset.fbx_config

        # Ensure output directory exists
        if BLENDER_AVAILABLE:
            os.makedirs(self.output_dir, exist_ok=True)

    def run(
        self,
        mesh_obj: Optional["Object"] = None,
        armature_obj: Optional["Object"] = None,
        base_name: str = "Tentacle",
    ) -> PipelineResult:
        """Run complete export pipeline.

        Args:
            mesh_obj: Mesh object to export
            armature_obj: Optional armature
            base_name: Base name for output files

        Returns:
            PipelineResult with all export details
        """
        start_time = time.time()
        result = PipelineResult(success=False, output_directory=self.output_dir)

        if not BLENDER_AVAILABLE:
            result.error = "Blender not available"
            return result

        if mesh_obj is None:
            result.error = "mesh_obj required"
            return result

        try:
            # Step 1: Generate LODs
            lod_generator = LODGenerator(self.lod_config)
            lod_results = lod_generator.generate_lods(mesh_obj=mesh_obj)
            result.lod_results = lod_results

            # Get LOD objects
            lod_objects = self._get_lod_objects(mesh_obj, lod_results)

            # Step 2: Export FBX files
            fbx_exporter = FBXExporter(self.fbx_config)

            for i, lod_obj in enumerate(lod_objects):
                output_path = os.path.join(
                    self.output_dir,
                    f"{base_name}_LOD{i}.fbx"
                )
                export_result = fbx_exporter.export(
                    mesh_obj=lod_obj,
                    armature_obj=armature_obj,
                    output_path=output_path,
                )
                export_result.lod_level = i
                result.export_results.append(export_result)

            # Step 3: Cleanup LOD copies (except LOD0)
            self._cleanup_lod_copies(lod_objects[1:])

            # Mark success if all exports succeeded
            result.success = all(er.success for er in result.export_results)

        except Exception as e:
            result.error = str(e)

        result.total_time_seconds = time.time() - start_time
        return result

    def _get_lod_objects(
        self,
        base_mesh: "Object",
        lod_results: List[LODResult],
    ) -> List["Object"]:
        """Get or create LOD objects from results."""
        objects = []

        for i, lod_result in enumerate(lod_results):
            if lod_result.object_name:
                obj = bpy.data.objects.get(lod_result.object_name)
                if obj:
                    objects.append(obj)
                    continue

            # Fallback to base mesh for LOD0
            if i == 0:
                objects.append(base_mesh)
            else:
                # Create LOD copy if not found
                lod_level = self.lod_config.levels[i]
                generator = LODGenerator(self.lod_config)
                lod_obj = generator._create_lod_copy(base_mesh, lod_level, i)
                objects.append(lod_obj)

        return objects

    def _cleanup_lod_copies(self, lod_objects: List["Object"]) -> None:
        """Remove temporary LOD copies after export."""
        for obj in lod_objects:
            if obj and obj.name in bpy.data.objects:
                # Remove mesh data
                mesh = obj.data
                bpy.data.objects.remove(obj)
                if mesh and mesh.name in bpy.data.meshes:
                    bpy.data.meshes.remove(mesh)

    def export_single(
        self,
        mesh_obj: "Object",
        armature_obj: Optional["Object"] = None,
        output_name: str = "Tentacle",
    ) -> ExportResult:
        """Export single mesh without LOD generation.

        Args:
            mesh_obj: Mesh to export
            armature_obj: Optional armature
            output_name: Output file name

        Returns:
            ExportResult
        """
        output_path = os.path.join(self.output_dir, f"{output_name}.fbx")
        exporter = FBXExporter(self.fbx_config)
        return exporter.export(mesh_obj, armature_obj, output_path)


def export_tentacle_package(
    mesh_obj: "Object",
    output_dir: str,
    armature_obj: Optional["Object"] = None,
    preset: Optional[ExportPreset] = None,
    base_name: str = "Tentacle",
) -> PipelineResult:
    """Convenience function to export complete tentacle package.

    Args:
        mesh_obj: Mesh to export
        output_dir: Output directory
        armature_obj: Optional armature
        preset: Export preset
        base_name: Base name for files

    Returns:
        PipelineResult with export details
    """
    pipeline = ExportPipeline(preset=preset, output_dir=output_dir)
    return pipeline.run(mesh_obj, armature_obj, base_name)
