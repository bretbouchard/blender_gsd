"""
Blender 5.x New Features Utilities.

This module provides production-ready utilities for Blender 5.0+ features
including ACES 2.0, Volume in Geometry Nodes, SDF modeling, thin film
iridescence, new modifiers, and compositor VSE integration.

Blender 5.0 was released November 2025 with major feature updates.

Example:
    >>> from lib.blender5x import color_management, geometry_nodes
    >>> color_management.ACESWorkflow.setup_acescg()
    >>> geometry_nodes.SDFModeling.boolean_union(sdf_a, sdf_b)
"""

__version__ = "1.0.0"
__blender_min_version__ = (5, 0, 0)

# Submodule imports
from . import color_management
from . import geometry_nodes
from . import rendering
from . import modifiers
from . import compositor
from . import animation

# Convenience imports for common operations
from .color_management.aces import ACESWorkflow, HDRVideoExport
from .geometry_nodes.volume_ops import VolumeGeometryNodes, VolumeGrid
from .geometry_nodes.sdf_modeling import SDFModeling
from .rendering.thin_film import ThinFilmIridescence
from .rendering.nano_vdb import NanoVDBIntegration
from .modifiers.array_new import NewArrayModifier, SurfaceDistribute
from .compositor.vse_integration import CompositorVSE, AssetShelf

__all__ = [
    # Submodules
    "color_management",
    "geometry_nodes",
    "rendering",
    "modifiers",
    "compositor",
    "animation",
    # Color management
    "ACESWorkflow",
    "HDRVideoExport",
    # Geometry nodes
    "VolumeGeometryNodes",
    "VolumeGrid",
    "SDFModeling",
    # Rendering
    "ThinFilmIridescence",
    "NanoVDBIntegration",
    # Modifiers
    "NewArrayModifier",
    "SurfaceDistribute",
    # Compositor
    "CompositorVSE",
    "AssetShelf",
]


def check_blender_version() -> tuple[int, int, int]:
    """
    Check and return the current Blender version.

    Returns:
        Tuple of (major, minor, patch) version numbers.

    Raises:
        ImportError: If running outside of Blender.
    """
    try:
        import bpy

        return bpy.app.version
    except ImportError:
        raise ImportError(
            "This module requires Blender's Python environment. "
            "Run from within Blender or use bpy module."
        )


def is_blender_5x() -> bool:
    """
    Check if current Blender version is 5.x or later.

    Returns:
        True if Blender 5.0 or later, False otherwise.
    """
    version = check_blender_version()
    return version >= (5, 0, 0)


def require_blender_5x() -> None:
    """
    Ensure Blender 5.x is being used.

    Raises:
        RuntimeError: If Blender version is less than 5.0.
    """
    if not is_blender_5x():
        version = check_blender_version()
        raise RuntimeError(
            f"Blender 5.0+ required, but version {version[0]}.{version[1]}.{version[2]} "
            "is running. Some features may not be available."
        )
