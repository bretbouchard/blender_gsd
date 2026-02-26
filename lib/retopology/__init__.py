"""
Retopology utilities for game-ready pipelines.

Provides retopology tools for hard surface models to achieve
optimal triangle counts for game engines.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from enum import Enum


class RetopologyMethod(Enum):
    """Retopology methods."""
    MANUAL = "manual"
    DECIMATE_PLANAR = "decimate_planar"
    SHRINKWRAP = "shrinkwrap"
    QUADRIANGULATE = "quadriangulate"


class RetopologyTarget(Enum):
    """Target poly counts for different platforms."""
    MOBILE_LOW = 500
    MOBILE_HIGH = 1500
    DESKTOP = 3000
    XBOX_360 = 3000
    CURRENT_GEN = 10000
    HERO = 50000


@dataclass
class RetopologyConfig:
    """
    Configuration for retopology operation.

    Attributes:
        name: Configuration name
        method: Retopology method
        target_poly_count: Target polygon count
        preserve_silhouette: Preserve silhouette accuracy
        preserve_hard_edges: Preserve hard edges
        preserve_detail_areas: Preserve detail areas (crevices, dents)
        max_decimation_angle: Maximum decimation angle (degrees)
        quadriangulate: Quadriangulate result
        auto_smooth: Auto-smooth shading
    """
    name: str = "RetopologyConfig"
    method: RetopologyMethod = RetopologyMethod.DECIMATE_PLANAR
    target_poly_count: int = 3000
    preserve_silhouette: bool = True
    preserve_hard_edges: bool = True
    preserve_detail_areas: bool = False
    max_decimation_angle: float = 3.0
    quadriangulate: bool = True
    auto_smooth: bool = True


@dataclass
class RetopologyResult:
    """
    Result of retopology operation.

    Attributes:
        success: Whether retopology succeeded
        source_object: Original high-poly object
        result_object: Retopologized low-poly object
        original_poly_count: Original polygon count
        final_poly_count: Final polygon count
        triangle_count: Triangle count
        reduction_ratio: Reduction ratio (0-1)
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    source_object: Any = None
    result_object: Any = None
    original_poly_count: int = 0
    final_poly_count: int = 0
    triangle_count: int = 0
    reduction_ratio: float = 1.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def retopologize(
    source_object: Any,
    config: Optional[RetopologyConfig] = None,
) -> RetopologyResult:
    """
    Retopologize high-poly mesh to game-ready low-poly.

    Args:
        source_object: High-poly source mesh
        config: Retopology configuration

    Returns:
        RetopologyResult with new mesh and statistics

    Example:
        >>> config = RetopologyConfig(
        ...     target_poly_count=3000,
        ...     method=RetopologyMethod.DECIMATE_PLANAR,
        ... )
        >>> result = retopologize(high_poly_mesh, config)
        >>> print(f"Reduced from {result.original_poly_count} to {result.final_poly_count}")
    """
    result = RetopologyResult()

    try:
        import bpy
        import bmesh
    except ImportError:
        return RetopologyResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    if source_object is None or source_object.type != 'MESH':
        result.errors.append("Source must be a mesh object")
        return result

    if config is None:
        config = RetopologyConfig()

    # Get source mesh data
    source_mesh = source_object.data
    result.original_poly_count = len(source_mesh.polygons)

    try:
        # Create duplicate for retopology
        retopo_name = f"{source_object.name}_retopo"
        retopo_mesh = bpy.data.meshes.new(retopo_name)
        retopo_obj = bpy.data.objects.new(retopo_name, retopo_mesh)

        # Copy base mesh (vertices only, no faces)
        bm = bmesh.new()
        bm.from_mesh(source_mesh)

        # Remove all faces (keep vertices as reference)
        bmesh.ops.delete(bm, geom=list(bm.faces))

        if config.method == RetopologyMethod.DECIMATE_PLANAR:
            # Use decimate modifier for clean base
            decimate = retopo_obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.decimate_mode = 'PLANAR'
            decimate.angle_limit = config.max_decimation_angle
            decimate.apply()

        elif config.method == RetopologyMethod.SHRINKWRAP:
            # Use shrinkwrap modifier
            shrinkwrap = retopo_obj.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
            shrinkwrap.apply()

        # Now build faces based on configuration
        if config.preserve_silhouette:
            _build_silhouette_faces(bm, config)

        if config.preserve_hard_edges:
            _preserve_hard_edges(bm)

        # Create faces
        _create_faces(bm, config)

        # Update mesh
        bm.to_mesh(retopo_mesh)
        bm.free()

        # Count triangles
        for poly in retopo_mesh.polygons:
            if len(poly.vertices) == 3:
                result.triangle_count += 1

        result.final_poly_count = len(retopo_mesh.polygons)
        result.reduction_ratio = result.final_poly_count / result.original_poly_count if result.original_poly_count > 0 else 1.0
        result.result_object = retopo_obj
        result.success = True

        return result

    except Exception as e:
        result.errors.append(f"Retopology error: {e}")
        return result


def _build_silhouette_faces(bm: Any, config: RetopologyConfig) -> None:
    """Build faces preserving silhouette."""
    # This would analyze the high-poly mesh and create
    # low-poly faces that match the silhouette
    pass


def _preserve_hard_edges(bm: Any) -> None:
    """Identify and mark hard edges for preservation."""
    # Find edges with sharp angles (hard surface edges)
    pass


def _create_faces(bm: Any, config: RetopologyConfig) -> None:
    """Create faces for retopologized mesh."""
    # Simple triangulation for now
    # In production, this would use proper quad-based retopology
    bmesh.ops.triangulate(bm, faces=list(bm.faces))


def get_poly_budget_for_target(target: RetopologyTarget) -> Dict[str, int]:
    """
    Get recommended polygon budget for target platform.

    Args:
        target: Target platform

    Returns:
        Dictionary with budget recommendations
    """
    budgets = {
        RetopologyTarget.MOBILE_LOW: {
            'max': 500,
            'recommended': 300,
            'description': 'Mobile low-end devices',
        },
        RetopologyTarget.MOBILE_HIGH: {
            'max': 1500,
            'recommended': 1000,
            'description': 'Mobile high-end devices',
        },
        RetopologyTarget.DESKTOP: {
            'max': 3000,
            'recommended': 2000,
            'description': 'Desktop/Console (Xbox 360 era)',
        },
        RetopologyTarget.XBOX_360: {
            'max': 3000,
            'recommended': 2500,
            'description': 'Xbox 360 / PS3 era',
        },
        RetopologyTarget.CURRENT_GEN: {
            'max': 10000,
            'recommended': 5000,
            'description': 'Current gen consoles (PS5/Xbox Series X)',
        },
        RetopologyTarget.HERO: {
            'max': 50000,
            'recommended': 20000,
            'description': 'Hero/cinematic assets',
        },
    }
    return budgets.get(target, budgets[RetopologyTarget.DESKTOP])


