"""
Style system for sleek brutalist mecha aesthetic.

Provides materials, lighting, and motion polish for the
mechanical tile platform.
"""

from .materials import (
    MaterialSystem,
    MaterialPreset,
    MaterialConfig,
)

from .lighting import (
    LightingSystem,
    LightingPreset,
    LightingConfig,
)

__all__ = [
    # Materials
    "MaterialSystem",
    "MaterialPreset",
    "MaterialConfig",
    # Lighting
    "LightingSystem",
    "LightingPreset",
    "LightingConfig",
]
