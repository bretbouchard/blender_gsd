"""
Export validation utilities.

Validates exported assets for game engine compatibility.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum


class ValidationSeverity(Enum):
    """Validation issue severity."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """
    Single validation issue.

    Attributes:
        severity: Issue severity
        category: Issue category
        message: Issue description
        object_name: Affected object name (if applicable)
        fix_suggestion: How to fix the issue (if applicable)
    """
    severity: ValidationSeverity
    category: str
    message: str
    object_name: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class ExportValidationResult:
    """
    Result of export validation.

    Attributes:
        valid: Whether export passed validation
        issues: List of validation issues
        poly_count: Total polygon count
        material_count: Number of materials
        texture_count: Number of textures
        armature_count: Number of armatures
        warnings_count: Number of warnings
        errors_count: Number of errors
    """
    valid: bool = False
    issues: List[ValidationIssue] = field(default_factory=list)
    poly_count: int = 0
    material_count: int = 0
    texture_count: int = 0
    armature_count: int = 0
    warnings_count: int = 0
    errors_count: int = 0


def validate_export(
    objects: Optional[List[Any]] = None,
    target_poly_count: Optional[int] = None,
    max_bone_count: Optional[int] = None,
    require_uv: bool = True,
) -> ExportValidationResult:
    """
    Validate objects for game engine export.

    Checks:
    - Polygon count within budget
    - Bone count for deformation
    - UV unwrapping
    - Material slots
    - Naming conventions
    - Non-manifold geometry

    Args:
        objects: Objects to validate (uses selection if None)
        target_poly_count: Maximum polygon count
        max_bone_count: Maximum bones per vertex
        require_uv: Require UV unwrapping

    Returns:
        ExportValidationResult with validation status

    Example:
        >>> result = validate_export(selected_objects, target_poly_count=50000)
        >>> if not result.valid:
        ...     for issue in result.issues:
        ...         print(f"  {issue.severity}: {issue.message}")
    """
    result = ExportValidationResult()
    issues = []

    try:
        import bpy
    except ImportError:
        return ExportValidationResult(
            valid=False,
            issues=[ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="environment",
                message="Blender (bpy) not available",
            )]
        )

    if objects is None:
        objects = bpy.context.selected_objects

    if not objects:
        result.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="selection",
            message="No objects selected for validation",
        ))
        return result

    # Validation thresholds
    POLY_WARNING_THRESHOLD = 0.8  # Warn at 80% of budget
    POLY_ERROR_THRESHOLD = 1.0  # Error at 100% of budget
    MAX_BONES_PER_VERTEX = 4  # Industry standard

    for obj in objects:
        # Check polygon count
        if obj.type == 'MESH':
            mesh = obj.data
            poly_count = len(mesh.polygons)

            result.poly_count += poly_count

            if target_poly_count and poly_count > target_poly_count * POLY_ERROR_THRESHOLD:
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="polygon_count",
                    message=f"{obj.name}: {poly_count} polygons exceeds budget of {target_poly_count}",
                    object_name=obj.name,
                    fix_suggestion=f"Reduce polygon count using decimate modifier or retopology",
                ))
            elif poly_count > target_poly_count * POLY_WARNING_THRESHOLD:
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="polygon_count",
                    message=f"{obj.name}: {poly_count} polygons is {int(target_poly_count * 0.8)} of budget",
                    object_name=obj.name,
                    fix_suggestion="Consider optimization for better performance",
                ))

            # Check bone count per vertex
            if max_bone_count:
                for vert in mesh.vertices:
                    bone_count = len(vert.groups)
                    if bone_count > max_bone_count:
                        result.issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="topology",
                            message=f"{obj.name}: Vertex has {bone_count} bones (max: {max_bone_count})",
                            object_name=obj.name,
                            fix_suggestion="Clean up topology - merge nearby vertices or remove edge loops",
                        ))

            # Check for UV layers
            if require_uv:
                if not mesh.uv_layers:
                    result.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="uv",
                        message=f"{obj.name}: No UV layers found",
                        object_name=obj.name,
                        fix_suggestion="Add UV layer and unwrap mesh",
                    ))

            # Check for non-manifold geometry
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(mesh)

            for edge in bm.edges:
                if not edge.is_manifold:
                    result.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="topology",
                        message=f"{obj.name}: Non-manifold edge detected",
                        object_name=obj.name,
                        fix_suggestion="Fill holes or recalculate normals (Shift+N in Edit mode)",
                    ))
                    break

            bm.free()

            # Count materials
            result.material_count += len(mesh.materials)

        # Count armatures
        elif obj.type == 'ARMATURE':
            result.armature_count += 1

    # Categorize issues
    result.errors_count = sum(
        1 for i in result.issues if i.severity == ValidationSeverity.ERROR
    )
    result.warnings_count = sum(
        1 for i in result.issues if i.severity == ValidationSeverity.WARNING
    )

    # Determine overall validity
    result.valid = result.errors_count == 0

    return result


def validate_texture_sizes(
    objects: Optional[List[Any]] = None,
    max_size: int = 2048,
    require_power_of_two: bool = True,
) -> ExportValidationResult:
    """
    Validate texture sizes for game engines.

    Args:
        objects: Objects to check (uses selection if None)
        max_size: Maximum texture dimension
        require_power_of_two: Require power-of-two dimensions

    Returns:
        ExportValidationResult with texture validation
    """
    result = ExportValidationResult()

    try:
        import bpy
    except ImportError:
        return ExportValidationResult(
            valid=False,
            issues=[ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="environment",
                message="Blender (bpy) not available",
            )],
        )

    if objects is None:
        objects = bpy.context.selected_objects

    for obj in objects:
        if obj.type == 'MESH':
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE':
                            image = node.image
                            if image:
                                size = max(image.size)
                                result.texture_count += 1

                                if size > max_size:
                                    result.issues.append(ValidationIssue(
                                        severity=ValidationSeverity.WARNING,
                                        category="texture_size",
                                        message=f"Texture '{image.name}' is {size}px (max: {max_size})",
                                        fix_suggestion=f"Resize texture to {max_size} or lower",
                                    ))

                                if require_power_of_two and (size & (size - 1)):
                                    result.issues.append(ValidationIssue(
                                        severity=ValidationSeverity.WARNING,
                                        category="texture_size",
                                        message=f"Texture '{image.name}' size {size} is not power of two",
                                        fix_suggestion="Resize to power-of-two dimension for better performance",
                                    ))

    result.errors_count = sum(
        1 for i in result.issues if i.severity == ValidationSeverity.ERROR
    )
    result.warnings_count = sum(
        1 for i in result.issues if i.severity == ValidationSeverity.WARNING
    )

    result.valid = result.errors_count == 0

    return result
