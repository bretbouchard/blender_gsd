"""
FBX Export for Unreal Engine 5.x

Provides FBX export functionality optimized for Unreal Engine 5.x,
including scale conversion, coordinate system handling, and material bundling.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from pathlib import Path
from enum import Enum


class FBXAxis(Enum):
    """FBX axis orientation."""
    X = "X axis (forward)"
    Y = "Y axis (up)"
    Z = "Z axis (right)"
    NEG_X = "-X axis"
    NEG_Y = "-Y axis"
    NEG_Z = "-Z axis"


class FBXUnit(Enum):
    """FBX unit system."""
    METER = "meter"
    CENTIMETER = "centimeter"
    DECIMETER = "decimeter (0.1 unit)"


@dataclass
class FBXExportConfig:
    """
    Configuration for FBX export.

    Attributes:
        name: Export name
        output_path: Output directory path
        target_objects: List of objects to export
        scale_factor: Scale factor (default 1.0 for meter)
        forward_axis: Forward axis (default Y)
        up_axis: Up axis (default Z)
        apply_modifiers: Apply modifiers
        include_children: Include child objects
        include_armatures: Include armatures
        embed_textures: Embed textures in FBX
        bake_textures: Bake textures before export
        texture_bake_size: Texture bake resolution
        smoothing: Apply smoothing groups
        tangent_space: Tangent space for normal maps
        use_material_slots: Use material slots
        deformation_type: Deformation type ('PRE', 'POST', 'SKELETON')
        leaf_bones: Include leaf bones
        only_deformable_bones: Only export deformable bones
        mesh_smooth_type: Mesh smoothing type
        global_scale: Global scale factor
        object_types: Object types to export ('MESH', 'CURVE', 'EMPTY', 'ARMATURE')
    """
    name: str = "output_path: Optional[str] = None
    target_objects: Optional[List[Any]] = None
    scale_factor: float = 1.0
    forward_axis: FBXAxis = FBXAxis.Y
    up_axis: FBXAxis = FBXAxis.Z
    apply_modifiers: bool = True
    include_children: bool = True
    include_armatures: bool = False
    embed_textures: bool = False
    bake_textures: bool = False
    texture_bake_size: int = 2048
    smoothing: int = 2
    tangent_space: int = 1
    use_material_slots: bool = True
    deformation_type: str = 'PRE'
    leaf_bones: bool = False
    only_deformable_bones: bool = True
    mesh_smooth_type: str = 'FACE'
    global_scale: float = 1.0
    object_types: List[str] = field(default_factory=list)

    @classmethod
    def for_unreal(cls, config: Optional['FBXExportConfig'] = None) -> 'FBXExportConfig':
        """Create config preset for Unreal Engine."""
        if config is None:
            config = FBXExportConfig()
        config.name = "UE5_FBX_Export"
        config.forward_axis = FBXAxis.Y
        config.up_axis = FBXAxis.Z
        config.global_scale = 100.0  # 1m = 1 unit = 100cm
        return config


@dataclass
class FBXExportResult:
    """
    Result of FBX export operation.

    Attributes:
        success: Whether export succeeded
        output_path: Path to exported FBX file
        exported_objects: List of exported object names
        material_count: Number of materials exported
        texture_count: Number of textures exported
        file_size: File size in bytes
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    output_path: Optional[Path] = None
    exported_objects: List[str] = field(default_factory=list)
    material_count: int = 0
    texture_count: int = 0
    file_size: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def export_fbx_for_unreal(
    config: Optional[FBXExportConfig] = None,
    objects: Optional[List[Any]] = None,
) -> FBXExportResult:
    """
    Export scene to FBX format for Unreal Engine.

    Args:
        config: Export configuration (uses defaults if not provided)
        objects: Objects to export (uses selection if None)

    Returns:
        FBXExportResult with export status and file path

    Example:
        >>> config = FBXExportConfig.for_unreal()
        >>> result = export_fbx_for_unreal(config, selected_objects)
        >>> print(f"Exported to {result.output_path}")
    """
    result = FBXExportResult()
    errors = []
    warnings = []

    try:
        import bpy
    except ImportError:
        return FBXExportResult(
            success=False,
            errors=["Blender (bpy) not available"],
        warnings=["Export requires Blender environment"],
        )

    # Create config if not provided
    config = config or FBXExportConfig.for_unreal()
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
        output_path = Path("//export/")join([config.name, ".fbx"])

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Configure export settings
        bpy.ops.export_scene.fbx(
            filepath=str(output_path),
            use_selection=config.target_objects is not None,
            global_scale=config.global_scale,
            apply_unit_scale=config.apply_modifiers,
            axis_forward=config.forward_axis.value,
            axis_up=config.up_axis.value,
            use_selection=config.include_children,
            object_types=config.object_types,
            use_armature=config.include_armatures,
            use_mesh_modifiers=config.apply_modifiers,
            mesh_smooth_type=config.mesh_smooth_type,
            # Note: FBX doesn't support smoothing groups in 2.79+
            # Use default smoothing for now

            # Set tangent space if not 1 (FBX default)
            if config.tangent_space != 1.0:
                warnings.append(f"Custom tangent space {config.tangent_space} not supported, using default 1.0")

            # Export
            bpy.ops.export_scene.fbx(
                filepath=str(output_path),
                check_existing=False,  # Always create new
            )

            # Get export stats
            result.success = True
            result.output_path = output_path
            result.exported_objects = [obj.name for obj in objects]
            result.file_size = output_path.stat().st_size if output_path.exists() else 0

            return result

    except Exception as e:
        result.errors.append(f"Export error: {e}")
        return result
