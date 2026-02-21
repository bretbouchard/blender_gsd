"""
Sanctus Library - Procedural Materials System
=============================================

A comprehensive procedural materials library for Blender featuring:
- 1000+ procedural material presets
- 32+ Shader Tools for damage, weathering, and pattern generation
- Performance-optimized node groups (E=Eevee, C=Cycles compatible)
- Texture baking utilities
- Geometry Nodes-based generators

Performance Color Coding:
- Green: Fast (real-time in Eevee)
- Yellow: Medium (good performance)
- Red: Slow (Cycles recommended)

Usage:
    from lib.materials.sanctus import (
        SanctusShaderTools,
        SanctusMaterials,
        DamageTools,
        WeatheringTools,
        PatternGenerator,
        SanctusBaker,
        SanctusGNGenerator,
    )

    # Apply damage to a material
    tools = SanctusShaderTools()
    tools.apply_damage(material, damage_type="scratches", intensity=0.5)

    # Get a material preset
    materials = SanctusMaterials()
    wood = materials.get_material("wood", "wood_planks", apply_damage=True)

    # Bake textures
    baker = SanctusBaker(wood)
    textures = baker.bake_all(resolution=2048)
"""

__version__ = "1.0.0"
__author__ = "Bret Bouchard"
__license__ = "MIT"

# Core API classes
from .shader_tools import (
    SanctusShaderTools,
    DamageGenerator,
    WeatheringGenerator,
    ShaderToolRegistry,
    ToolCategory,
    PerformanceRating,
)

from .materials import (
    SanctusMaterials,
    MaterialCategory,
    MaterialPreset,
    MATERIAL_PRESETS,
)

from .damage import (
    DamageTools,
    DamageType,
    DamageParameters,
)

from .weathering import (
    WeatheringTools,
    WeatheringType,
    WeatheringParameters,
)

from .patterns import (
    PatternGenerator,
    PatternType,
    PatternParameters,
)

from .baker import (
    SanctusBaker,
    BakeChannel,
    BakeSettings,
    ExportEngine,
)

from .geometry_nodes import (
    SanctusGNGenerator,
    GNDamageType,
    GNWearType,
)

# Convenience exports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Main API
    "SanctusShaderTools",
    "SanctusMaterials",
    "SanctusBaker",
    "SanctusGNGenerator",
    # Generators
    "DamageGenerator",
    "WeatheringGenerator",
    "PatternGenerator",
    # Tool classes
    "DamageTools",
    "WeatheringTools",
    # Enums and registries
    "ShaderToolRegistry",
    "ToolCategory",
    "PerformanceRating",
    "MaterialCategory",
    "MaterialPreset",
    "MATERIAL_PRESETS",
    "DamageType",
    "DamageParameters",
    "WeatheringType",
    "WeatheringParameters",
    "PatternType",
    "PatternParameters",
    "BakeChannel",
    "BakeSettings",
    "ExportEngine",
    "GNDamageType",
    "GNWearType",
]


def get_version() -> str:
    """Get the current version of Sanctus Library."""
    return __version__


def get_tool_count() -> int:
    """Get the number of available shader tools."""
    return len(ShaderToolRegistry.list_tools())


def get_material_count() -> int:
    """Get the number of available material presets."""
    materials = SanctusMaterials()
    count = 0
    for category in materials.CATEGORIES:
        count += len(materials.list_category(category))
    return count


def initialize() -> bool:
    """
    Initialize the Sanctus Library system.

    Ensures all required node groups are registered and
    shader tools are available.

    Returns:
        bool: True if initialization successful
    """
    try:
        # Initialize shader tools registry
        SanctusShaderTools()

        # Initialize materials system
        SanctusMaterials()

        return True
    except Exception as e:
        print(f"Sanctus Library initialization failed: {e}")
        return False
