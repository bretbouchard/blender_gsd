"""
Geometry Nodes Module for Blender 5.0+.

Provides volume operations, SDF modeling, and bundles/closures support
for the enhanced Geometry Nodes system in Blender 5.0.

Example:
    >>> from lib.blender5x.geometry_nodes import VolumeGeometryNodes, SDFModeling
    >>> points = VolumeGeometryNodes.smoke_to_points(volume)
    >>> blended = SDFModeling.smooth_union(sdf_a, sdf_b, smoothness=0.1)
"""

from .volume_ops import (
    VolumeGeometryNodes,
    VolumeGrid,
    VolumeGridType,
    VolumeInfo,
)

from .sdf_modeling import (
    SDFModeling,
    SDFBlendMode,
    SDFInfo,
)

from .bundles import (
    Bundles,
    Closures,
    LazyEvaluation,
    BundleSchema,
    BundleField,
    BundleDataType,
    ClosureInfo,
)

__all__ = [
    # Volume operations
    "VolumeGeometryNodes",
    "VolumeGrid",
    "VolumeGridType",
    "VolumeInfo",
    # SDF modeling
    "SDFModeling",
    "SDFBlendMode",
    "SDFInfo",
    # Bundles and closures
    "Bundles",
    "Closures",
    "LazyEvaluation",
    "BundleSchema",
    "BundleField",
    "BundleDataType",
    "ClosureInfo",
]
