"""
Control System Package

Provides parameter hierarchy and color system utilities for control surface generation.
"""

from .parameters import (
    ParameterGroup,
    ParameterHierarchy,
    resolve_task_parameters
)
from .colors import (
    ColorToken,
    ColorSystem,
    create_default_color_system
)

__all__ = [
    "ParameterGroup",
    "ParameterHierarchy",
    "resolve_task_parameters",
    "ColorToken",
    "ColorSystem",
    "create_default_color_system",
]
