"""
Node Groups for Input System

Reusable geometry node groups for control surface generation.

Modules:
    debug_switcher: Debug_Material_Switcher node group for per-section visualization
"""

from .debug_switcher import (
    create_debug_material_switcher,
    DebugMaterialSwitcherBuilder,
)

__all__ = [
    "create_debug_material_switcher",
    "DebugMaterialSwitcherBuilder",
]
