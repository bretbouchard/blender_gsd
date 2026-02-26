"""
GLB Export for Web/AR/VR.

Provides GLB/GLTF export functionality optimized for web applications,
Unity, and AR/VR experiences.

Features:
- Draco compression for smaller file sizes
- Material extensions for PBR
- Animation support
- Morph targets for blend shapes
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from pathlib import Path
from enum import Enum


class GLBCompressionMode(Enum):
    """GLB compression modes."""
    NONE = "none"
    DRACO = "draco"
    MESH_QUANTIZATION = "mesh_quantization"


class GLBMaterialMode(Enum):
    """GLB material export modes."""
    KHRONOS_MATERIALS = "KHR_materials"
    SPECULAR_GLOSSES = "specular_glosses"


@dataclass
class GLBExportConfig:
    """
    Configuration for GLB export.

    Attributes:
        name: Export name
        output_path: Output directory path
        target_objects: List of objects to export
        compression: Compression mode
        draco_compression_level: Draco compression level (0-10)
        draco_quantization: Use Draco quantization
        material_mode: Material export mode
        export_animations: Export animations
        export_morph_targets: Export morph targets
        export_cameras: Export cameras
        export_lights: Export lights
        texture_resolution: Maximum texture resolution
        copyright: Copyright info to embed
        apply_modifiers: Apply modifiers before export
    """
    name: str = "WebGLB_Export"
    output_path: Optional[str] = None
    target_objects: Optional[List[Any]] = None
    compression: GLBCompressionMode = GLBCompressionMode.DRACO
    draco_compression_level: int = 6
    draco_quantization: bool = True
    material_mode: GLBMaterialMode = GLBMaterialMode.KHRONOS_MATERIALS
    export_animations: bool = True
    export_morph_targets: bool = False
    export_cameras: bool = False
    export_lights: bool = False
    texture_resolution: int = 2048
    copyright: Optional[str] = None
    apply_modifiers: bool = True

    @classmethod
    def for_web(cls, config: Optional['GLBExportConfig'] = None) -> 'GLBExportConfig':
        """Create config preset for web/AR/VR."""
        if config is None:
            config = GLBExportConfig()
        config.compression = GLBCompressionMode.DRACO
        config.draco_compression_level = 6
        config.material_mode = GLBMaterialMode.KHRONOS_MATERIALS
        return config

    @classmethod
    def for_unity(cls, config: Optional['GLBExportConfig'] = None) -> 'GLBExportConfig':
        """Create config preset for Unity."""
        if config is None:
            config = GLBExportConfig()
        config.compression = GLBCompressionMode.DRACO
        config.draco_compression_level = 4
        config.export_cameras = True
        config.export_lights = True
        return config

    @classmethod
    def for_ar_vr(cls, config: Optional['GLBExportConfig'] = None) -> 'GLBExportConfig':
        """Create config preset for AR/VR (maximum quality)."""
        if config is None:
            config = GLBExportConfig()
        config.compression = GLBCompressionMode.NONE  # No compression for quality
        config.material_mode = GLBMaterialMode.KHRONOS_MATERIALS
        config.texture_resolution = 4096
        return config


@dataclass
class GLBExportResult:
    """
    Result of GLB export operation.

    Attributes:
        success: Whether export succeeded
        output_path: Path to exported GLB file
        exported_objects: List of exported object names
        texture_count: Number of textures exported
        file_size: File size in bytes
        compression_ratio: Compression ratio (estimated)
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    output_path: Optional[Path] = None
    exported_objects: List[str] = field(default_factory=list)
    texture_count: int = 0
    file_size: int = 0
    compression_ratio: float = 1.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def export_glb_for_web(
    config: Optional[GLBExportConfig] = None,
    objects: Optional[List[Any]] = None,
) -> GLBExportResult:
    """
    Export scene to GLB format for web/AR/VR.

    Args:
        config: Export configuration (uses defaults if not provided)
        objects: Objects to export (uses selection if None)

    Returns:
        GLBExportResult with export status, file path

    Example:
        >>> config = GLBExportConfig.for_web()
        >>> result = export_glb_for_web(config)
        >>> print(f"Exported to {result.output_path}")
    """
    result = GLBExportResult()
    errors = []
    warnings = []

    try:
        import bpy
    except ImportError:
        return GLBExportResult(
            success=False,
            errors=["Blender (bpy) not available"],
            warnings=["Export requires Blender environment"],
        )

    # Create config if not provided
    config = config or GLBExportConfig.for_web()
    if objects is None:
        objects = bpy.context.selected_objects

    # Validate objects
    if not objects:
        result.errors.append("No objects selected for export")
        return result

    # Set output path
    if config.output_path:
        output_path = Path(config.output_path)
    else:
        output_path = Path("//export/").with_suffix(".glb")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Configure GLB export settings
        bpy.ops.export_scene.gltf(
            filepath=str(output_path),
            export_format='GLB',
            use_selection=config.target_objects is not None,
            export_draco_mesh_compression=config.compression == GLBCompressionMode.DRACO,
            export_draco_mesh_compression_level=config.draco_compression_level,
            export_tangent_space=32 if config.material_mode == GLBMaterialMode.KHRONOS_MATERIALS else 16,
            export_materials=config.material_mode == GLBMaterialMode.KHRONOS_MATERIALS,
            export_colors=True,
            export_cameras=config.export_cameras,
            export_extras=True,
            export_animations=config.export_animations,
            export_frame_range=(1, 250),
            export_apply_unit_scale=config.apply_modifiers,
        )

        # Execute export
        bpy.ops.export_scene.gltf(
            filepath=str(output_path),
            check_existing=False,
        )

        # Get export stats
        result.success = True
        result.output_path = output_path
        result.exported_objects = [obj.name for obj in objects]
        result.file_size = output_path.stat().st_size if output_path.exists() else 0

        # Estimate compression ratio
        if config.compression == GLBCompressionMode.DRACO:
            # Draco typically achieves 10:1 compression
            result.compression_ratio = 0.1
            result.warnings.append("Estimated compression ratio - actual ratio depends on content")

        return result

    except Exception as e:
        result.errors.append(f"Export error: {e}")
        return result
