"""
Export module for the tile platform system.

This module provides export functionality for the mechanical tile platform,
including FBX export for Unity, glTF export for Unreal Engine, and
production-quality render pipeline for Blender.

Example usage:
    from lib.export import (
        FBXExporter, GLTFExporter, RenderPipeline,
        create_unity_exporter, create_unreal_exporter, create_production_pipeline
    )

    # Create FBX exporter for Unity
    fbx_exporter = create_unity_exporter(platform)
    fbx_exporter.export_to_file("platform.fbx")

    # Create glTF exporter for Unreal
    gltf_exporter = create_unreal_exporter(platform)
    gltf_exporter.export_to_file("platform.glb")

    # Create render pipeline for production
    render_pipeline = create_production_pipeline(platform)
    render_pipeline.render_animation("output/", 1, 100)

    # Get export statistics
    stats = fbx_exporter.get_export_stats()
    print(f"Exported {stats['vertex_count']} vertices")
"""

from .fbx import FBXExporter, FBXExportConfig, create_unity_exporter, create_optimized_exporter
from .gltf import GLTFExporter, GLTFExportConfig, create_unreal_exporter, create_web_exporter, create_high_quality_exporter
from .render import RenderPipeline, RenderConfig, create_preview_pipeline, create_production_pipeline, create_4k_pipeline

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # FBX export
    "FBXExporter",
    "FBXExportConfig",
    "create_unity_exporter",
    "create_optimized_exporter",
    # glTF export
    "GLTFExporter",
    "GLTFExportConfig",
    "create_unreal_exporter",
    "create_web_exporter",
    "create_high_quality_exporter",
    # Render pipeline
    "RenderPipeline",
    "RenderConfig",
    "create_preview_pipeline",
    "create_production_pipeline",
    "create_4k_pipeline",
]
