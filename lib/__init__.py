"""
Blender GSD Framework Library

Core modules for procedural artifact generation.

Note: Blender-dependent modules are imported lazily to allow
testing of non-Blender code (oracle, cinematic types) without
requiring Blender to be installed.
"""

import sys

# Check if we're in a Blender environment
_IN_BLENDER = 'bpy' in sys.modules or 'bpy' in sys.builtin_module_names

# Always-available modules (no Blender dependency)
# These can be imported for unit testing

__version__ = "0.4.0"
__version_info__ = (0, 4, 0)

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    # Blender-dependent (import lazily or in Blender context)
    "Pipeline",
    "NodeKit",
    "reset_scene",
    "ensure_collection",
    "load_task",
]


def __getattr__(name: str):
    """
    Lazy import of Blender-dependent modules.

    This allows 'from lib import oracle' to work without loading
    Blender-dependent modules like nodekit.
    """
    if name == "Pipeline":
        from .pipeline import Pipeline
        return Pipeline
    elif name == "NodeKit":
        from .nodekit import NodeKit
        return NodeKit
    elif name == "reset_scene":
        from .scene_ops import reset_scene
        return reset_scene
    elif name == "ensure_collection":
        from .scene_ops import ensure_collection
        return ensure_collection
    elif name == "load_task":
        from .gsd_io import load_task
        return load_task

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
