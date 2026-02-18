"""
Control System Package

A comprehensive system for generating procedural control surface elements.

Modules:
- parameters: Hierarchical parameter resolution
- colors: Color system with LAB interpolation
- profiles: Knob geometry profile definitions

Quick Start:
    from lib.control_system import ParameterHierarchy, get_profile

    # Get a knob profile
    profile = get_profile("chicken_head")
    params = profile.to_params()

    # Resolve parameters with hierarchy
    hierarchy = ParameterHierarchy()
    params = hierarchy.resolve(
        category_preset="consoles/neve_1073",
        instance_params={"base_color": [1, 0, 0]}
    )
"""

from .parameters import (
    ParameterGroup,
    ParameterHierarchy,
    resolve_task_parameters,
)

from .colors import (
    ColorToken,
    ColorSystem,
    create_default_color_system,
)

from .profiles import (
    KnobProfile,
    KnobProfileType,
    get_profile,
    list_profiles,
    create_custom_profile,
    PROFILES,
)

__all__ = [
    # Parameters
    "ParameterGroup",
    "ParameterHierarchy",
    "resolve_task_parameters",

    # Colors
    "ColorToken",
    "ColorSystem",
    "create_default_color_system",

    # Profiles
    "KnobProfile",
    "KnobProfileType",
    "get_profile",
    "list_profiles",
    "create_custom_profile",
    "PROFILES",
]

__version__ = "0.1.0"
