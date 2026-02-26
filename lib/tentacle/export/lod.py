"""
Tentacle LOD Generator

Level-of-detail generation for Unreal Engine export.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

try:
    import bpy
    from bpy.types import Object, Mesh
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Mesh = None

from .types import LODConfig, LODLevel, LODResult, LODStrategy


class LODGenerator:
    """Generate LOD levels for tentacle meshes."""

    def __init__(self, config: LODConfig):
        """Initialize LOD generator.

        Args:
            config: LOD configuration
        """
        self.config = config

    def generate_lods(
        self,
        mesh_obj: Optional["Object"] = None,
        base_vertices: Optional[np.ndarray] = None,
        base_faces: Optional[np.ndarray] = None,
    ) -> List[LODResult]:
        """Generate all LOD levels.

        Args:
            mesh_obj: Blender mesh object (required for Blender mode)
            base_vertices: Base mesh vertices (for numpy mode)
            base_faces: Base mesh faces (for numpy mode)

        Returns:
            List of LODResult for each level
        """
        if BLENDER_AVAILABLE and mesh_obj is not None:
            return self._generate_blender(mesh_obj)
        elif base_vertices is not None and base_faces is not None:
            return self._generate_numpy(base_vertices, base_faces)
        else:
            raise ValueError("Either mesh_obj (Blender) or base_vertices/faces (numpy) required")

    def _generate_blender(self, mesh_obj: "Object") -> List[LODResult]:
        """Generate LODs using Blender's decimate modifier."""
        results = []

        for i, lod_level in enumerate(self.config.levels):
            if i == 0:
                # LOD0 is the original mesh
                mesh = mesh_obj.data
                results.append(LODResult(
                    level_name=lod_level.name,
                    triangle_count=len(mesh.polygons),
                    vertex_count=len(mesh.vertices),
                    screen_size_ratio=lod_level.screen_size,
                    object_name=mesh_obj.name,
                    success=True,
                ))
            else:
                # Create LOD copy with decimate
                lod_obj = self._create_lod_copy(mesh_obj, lod_level, i)
                if lod_obj:
                    mesh = lod_obj.data
                    results.append(LODResult(
                        level_name=lod_level.name,
                        triangle_count=len(mesh.polygons),
                        vertex_count=len(mesh.vertices),
                        screen_size_ratio=lod_level.screen_size,
                        object_name=lod_obj.name,
                        success=True,
                    ))
                    # Clean up LOD object (keep for export, cleanup later)
                else:
                    results.append(LODResult(
                        level_name=lod_level.name,
                        triangle_count=0,
                        vertex_count=0,
                        screen_size_ratio=lod_level.screen_size,
                        success=False,
                        error="Failed to create LOD copy",
                    ))

        return results

    def _create_lod_copy(
        self,
        source_obj: "Object",
        lod_level: LODLevel,
        lod_index: int,
    ) -> Optional["Object"]:
        """Create a decimated copy for LOD level."""
        # Copy mesh
        lod_obj = source_obj.copy()
        lod_obj.data = source_obj.data.copy()
        lod_obj.name = f"{source_obj.name}_{lod_level.name}"

        # Link to scene
        bpy.context.collection.objects.link(lod_obj)

        # Add decimate modifier
        decimate = lod_obj.modifiers.new(name="LOD_Decimate", type='DECIMATE')
        decimate.ratio = lod_level.ratio
        decimate.use_collapse_triangulate = True

        # Apply modifier
        bpy.context.view_layer.objects.active = lod_obj
        lod_obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier="LOD_Decimate")

        return lod_obj

    def _generate_numpy(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
    ) -> List[LODResult]:
        """Generate LOD results using numpy (simplified for testing).

        Note: Actual decimation requires Blender. This provides
        approximate results for testing without Blender.
        """
        results = []
        base_tri_count = len(faces)
        base_vert_count = len(vertices)

        for i, lod_level in enumerate(self.config.levels):
            # Approximate decimated counts
            tri_count = int(base_tri_count * lod_level.ratio)
            vert_count = int(base_vert_count * lod_level.ratio)

            results.append(LODResult(
                level_name=lod_level.name,
                triangle_count=max(4, tri_count),  # Minimum 4 triangles
                vertex_count=max(4, vert_count),   # Minimum 4 vertices
                screen_size_ratio=lod_level.screen_size,
                success=True,
            ))

        return results


def generate_lods(
    mesh_obj: Optional["Object"] = None,
    vertices: Optional[np.ndarray] = None,
    faces: Optional[np.ndarray] = None,
    config: Optional[LODConfig] = None,
) -> List[LODResult]:
    """Convenience function to generate LODs.

    Args:
        mesh_obj: Blender mesh object
        vertices: Vertex array (for numpy mode)
        faces: Face array (for numpy mode)
        config: LOD configuration (uses default if None)

    Returns:
        List of LODResult for each level
    """
    config = config or LODConfig()
    generator = LODGenerator(config)

    if BLENDER_AVAILABLE and mesh_obj is not None:
        return generator.generate_lods(mesh_obj=mesh_obj)
    elif vertices is not None and faces is not None:
        return generator.generate_lods(base_vertices=vertices, base_faces=faces)
    else:
        raise ValueError("Either mesh_obj or vertices/faces required")


def generate_lod_levels(
    base_triangle_count: int,
    strategy: LODStrategy = LODStrategy.DECIMATE,
    levels: int = 4,
) -> List[LODLevel]:
    """Generate LOD level configurations based on base mesh.

    Args:
        base_triangle_count: Triangle count of base mesh
        strategy: LOD generation strategy
        levels: Number of LOD levels to generate

    Returns:
        List of LODLevel configurations
    """
    if strategy == LODStrategy.DECIMATE:
        # Standard decimation ratios
        ratios = [1.0, 0.5, 0.25, 0.12]
        screen_sizes = [1.0, 0.5, 0.25, 0.1]
    elif strategy == LODStrategy.REMESH:
        # Remesh tends to preserve more detail
        ratios = [1.0, 0.6, 0.35, 0.2]
        screen_sizes = [1.0, 0.5, 0.25, 0.1]
    else:
        ratios = [1.0, 0.5, 0.25, 0.12]
        screen_sizes = [1.0, 0.5, 0.25, 0.1]

    # Limit to requested levels
    ratios = ratios[:levels]
    screen_sizes = screen_sizes[:levels]

    lod_levels = []
    for i, (ratio, screen_size) in enumerate(zip(ratios, screen_sizes)):
        expected_tris = int(base_triangle_count * ratio)
        lod_levels.append(LODLevel(
            name=f"LOD{i}",
            ratio=ratio,
            screen_size=screen_size,
        ))

    return lod_levels
