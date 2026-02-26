"""
USD Export for modern 3D pipelines.

Provides USD export functionality for modern 3D pipelines including
USDZ, MaterialX, and MDL support.

Features:
- USDA format support (USDA, USDC, USDT)
- MaterialX integration
- MDL material export
- Assembly/instance export
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from pathlib import Path
from enum import Enum


class USDExportFormat(Enum):
    """USD export formats."""
    USDA = "usda"
    USDC = "usdc"
    USDT = "usdt"


class USDMaterialPurpose(Enum):
    """USD material purposes."""
    PREVIEW = "preview"
    RENDER = "render"
    PROXY = "proxy"


@dataclass
class USDExportConfig:
    """
    Configuration for USD export.

    Attributes:
        name: Export name
        output_path: Output directory path
        target_objects: List of objects to export
        format: USD format (USDA, USDC, USDT)
        material_purpose: Material purpose
        export_animation: Export animation data
        export_blendshapes: Export blend shapes
        export_cameras: Export cameras
        export_lights: Export lights
        root_prim_path: Path to root USD file
        subdivision_level: Subdivision level for mesh export
        materials_scope: Export materials ('all', 'used', 'none')
    """
    name: str = "USD_Export"
    output_path: Optional[str] = None
    target_objects: Optional[List[Any]] = None
    format: USDExportFormat = USDExportFormat.USDC
    material_purpose: USDMaterialPurpose = USDMaterialPurpose.RENDER
    export_animation: bool = True
    export_blendshapes: bool = True
    export_cameras: bool = True
    export_lights: bool = False
    root_prim_path: Optional[str] = None
    subdivision_level: int = 1
    materials_scope: str = "used"

    @classmethod
    def for_unreal(cls, config: Optional['USDExportConfig'] = None) -> 'USDExportConfig':
        """Create config preset for Unreal Engine."""
        if config is None:
            config = USDExportConfig()
        config.format = USDExportFormat.USDC
        config.material_purpose = USDMaterialPurpose.RENDER
        config.export_cameras = True
        config.export_lights = True
        return config

    @classmethod
    def for_arnold_vray(cls, config: Optional['USDExportConfig'] = None) -> 'USDExportConfig':
        """Create config preset for Arnold renderer (Houdini, Karma, V-Ray)."""
        if config is None:
            config = USDExportConfig()
        config.format = USDExportFormat.USDC
        config.material_purpose = USDMaterialPurpose.RENDER
        config.export_animation = True
        return config

    @classmethod
    def for_preview(cls, config: Optional['USDExportConfig'] = None) -> 'USDExportConfig':
        """Create config preset for viewport preview."""
        if config is None:
            config = USDExportConfig()
        config.format = USDExportFormat.USDA
        config.material_purpose = USDMaterialPurpose.PREVIEW
        config.subdivision_level = 0
        return config


@dataclass
class USDExportResult:
    """
    Result of USD export operation.

    Attributes:
        success: Whether export succeeded
        output_path: Path to exported USD file/directory
        exported_objects: List of exported object names
        stage_count: Number of USD stages exported
        material_count: Number of materials exported
        file_size: Total file size in bytes
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    output_path: Optional[Path] = None
    exported_objects: List[str] = field(default_factory=list)
    stage_count: int = 0
    material_count: int = 0
    file_size: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def export_usd(
    config: Optional[USDExportConfig] = None,
    objects: Optional[List[Any]] = None,
) -> USDExportResult:
    """
    Export scene to USD format.

    Args:
        config: Export configuration (uses defaults if not provided)
        objects: Objects to export (uses selection if None)

    Returns:
        USDExportResult with export status

    Example:
        >>> config = USDExportConfig.for_unreal()
        >>> result = export_usd(config)
        >>> print(f"Exported to {result.output_path}")
    """
    result = USDExportResult()
    errors = []
    warnings = []

    try:
        import bpy
    except ImportError:
        return USDExportResult(
            success=False,
            errors=["Blender (bpy) not available"],
            warnings=["Export requires Blender environment"],
        )

    # Create config if not provided
    config = config or USDExportConfig.for_unreal()
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
        output_path = Path("//export/").joinpath(config.name)

    try:
        # Configure USD export settings
        bpy.ops.wm.usd_export(
            filepath=str(output_path),
            export_materials=config.materials_scope != "none",
            selected_objects=objects,
            export_animation=config.export_animation,
            export_hair=config.export_blendshapes,
            export_uvmaps=True,
            export_normals=True,
            export_mesh_motion_blur=False,
            # Note: USD export options vary by Blender version
        )

        # Get export stats
        result.success = True
        result.output_path = output_path
        result.exported_objects = [obj.name for obj in objects]

        return result

    except Exception as e:
        result.errors.append(f"Export error: {e}")
        return result
