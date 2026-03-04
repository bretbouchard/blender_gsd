"""
Development Tools Package

Provides tools for generating and managing blender_gsd modules.

Usage:
    from lib.dev import ModuleTemplate, create_module, list_features

    # Create a new module
    code = create_module("my_effect", features=["nodekit", "hud"])

    # Generate from template
    from lib.dev import create_from_template
    code = create_from_template("full_featured", "CrystalGrowth")
"""

from .templates import (
    ModuleTemplate,
    ModuleConfig,
    create_module,
    list_features,
    generate_hud_class,
    create_from_template,
    EXAMPLE_TEMPLATES,
)

__all__ = [
    "ModuleTemplate",
    "ModuleConfig",
    "create_module",
    "list_features",
    "generate_hud_class",
    "create_from_template",
    "EXAMPLE_TEMPLATES",
]
