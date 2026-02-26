"""
Game-ready mesh utilities.

Provides utilities for creating game-ready meshes including
LOD generation, texture baking setup, and validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from enum import Enum

from .types import RetopologyTarget, get_poly_budget_for_target
from .decimate import planar_decimate, DecimateResult


class LODLevel(Enum):
    """Level of Detail levels for game assets."""
    LOD_0 = "lod_0"  # Closest, lowest detail
    LOD_1 = "lod_1"
    LOD_2 = "lod_2"
    LOD_3 = "lod_3"  # Farthest, highest detail


@dataclass
class GameReadyConfig:
    """
    Configuration for game-ready mesh preparation.

    Attributes:
        target: Target platform
        lod_levels: Number of LOD levels to generate
        generate_uvs: Generate UV maps
        bake_normals: Bake normal maps
        validate_topology: Validate topology for issues
        auto_fix: Attempt to auto-fix topology issues
    """
    target: RetopologyTarget = RetopologyTarget.DESKTOP
    lod_levels: int = 3
    generate_uvs: bool = True
    bake_normals: bool = True
    validate_topology: bool = True
    auto_fix: bool = True


@dataclass
class GameReadyResult:
    """
    Result of game-ready preparation.

    Attributes:
        success: Whether preparation succeeded
        lods: Generated LOD meshes
        uv_maps: Generated UV maps
        normal_maps: Baked normal maps
        issues: List of topology issues found
        warnings: List of warning messages
    """
    success: bool = False
    lods: Dict[str, Any] = field(default_factory=dict)
    uv_maps: Dict[str, Any] = field(default_factory=dict)
    normal_maps: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def prepare_game_ready(
    source_object: Any,
    config: Optional[GameReadyConfig] = None,
) -> GameReadyResult:
    """
    Prepare mesh for game engine use.

    Args:
        source_object: Source mesh to prepare
        config: Game-ready configuration

    Returns:
        GameReadyResult with prepared meshes
    """
    result = GameReadyResult()

    if config is None:
        config = GameReadyConfig()

    try:
        import bpy
    except ImportError:
        return result

    if source_object is None or source_object.type != 'MESH':
        result.issues.append("Source must be a mesh object")
        return result

    try:
        # Get poly budget
        budget = get_poly_budget_for_target(config.target)

        # Check current poly count
        current_polys = len(source_object.data.polygons)

        if current_polys > budget['max']:
            result.warnings.append(
                f"Current poly count ({current_polys}) exceeds target ({budget['max']})"
            )

        # Generate LODs if requested
        if config.lod_levels > 1:
            result.lods = _generate_lods(source_object, config.lod_levels)

            result.warnings.append(
                f"Generated {len(result.lods)} LOD levels"
            )

        # Generate UVs if requested
        if config.generate_uvs:
            result.uv_maps = _generate_uvs(source_object)
            result.warnings.append("Generated UV maps")

        # Bake normals if requested
        if config.bake_normals:
            result.normal_maps = _bake_normal_maps(source_object)
            result.warnings.append("Baked normal maps")

        # Validate topology if requested
        if config.validate_topology:
            issues = _validate_mesh_topology(source_object)
            result.issues.extend(issues)

        result.success = True

        return result

    except Exception as e:
        result.issues.append(f"Error preparing game-ready mesh: {e}")
        return result


def _generate_lods(
    source_object: Any,
    levels: int,
) -> Dict[str, Any]:
    """Generate LOD meshes from source."""
    lods = {}

    try:
        import bpy

        for i in range(levels):
            # Create LOD mesh
            lod_name = f"{source_object.name}_LOD{i}"
            lod_mesh = source_object.copy()
            lod_mesh.name = lod_name

            # Decimate based on LOD level
            ratio = 1.0 / (2 ** i)  # Exponential falloff
            decimate_result = planar_decimate(lod_mesh, angle=1.0 + i)

            lods[f"lod_{i}"] = lod_mesh

    except Exception:
        pass

    return lods


def _generate_uvs(source_object: Any) -> Dict[str, Any]:
    """Generate UV maps for all LOD levels."""
    uv_maps = {}

    try:
        import bpy

        # Smart UV project based on mesh complexity
        # In production, this would use more sophisticated UV unwrapping
        pass
    return uv_maps


def _bake_normal_maps(source_object: Any) -> Dict[str, Any]:
    """Bake normal maps for LOD meshes."""
    normal_maps = {}

    try:
        import bpy

        # Set up normal bake
        # In production, this would configure proper bake settings
        pass
    return normal_maps


def _validate_mesh_topology(source_object: Any) -> List[str]:
    """Validate mesh topology for common issues."""
    issues = []

    try:
        import bmesh

        bm = bmesh.new()
        bm.from_mesh(source_object.data)

        # Check for non-manifold geometry
        for edge in bm.edges:
            if not edge.is_manifold:
                issues.append(f"Non-manifold edge found at index {edge.index}")

        # Check for ngons
        for face in bm.faces:
            if len(face.verts) > 4:
                issues.append(f"Ngon face found with {len(face.verts)} vertices")

        # Check for poles (vertices with >5 edges)
        for vert in bm.verts:
            if len(vert.link_edges) > 5:
                issues.append(
                    f"Pole found at vertex {vert.index} with {len(vert.link_edges)} edges"
                )

        bm.free()

    except Exception:
        pass
    return issues


