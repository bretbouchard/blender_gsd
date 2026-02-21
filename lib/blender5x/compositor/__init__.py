"""
Compositor Module for Blender 5.0+.

Provides VSE compositor integration and asset shelf utilities
for applying real-time effects to video strips.

Example:
    >>> from lib.blender5x.compositor import CompositorVSE, AssetShelf
    >>> CompositorVSE.create_glow(strip, intensity=1.5)
    >>> AssetShelf.apply_preset("glow")
"""

from .vse_integration import (
    CompositorVSE,
    AssetShelf,
    CompositorEffectType,
    CompositorEffectSettings,
)

from .asset_shelf import (
    EffectPresets,
    EffectTemplates,
    EffectCategory,
    EffectPreset,
    BUILTIN_EFFECT_PRESETS,
)

__all__ = [
    # VSE Integration
    "CompositorVSE",
    "AssetShelf",
    "CompositorEffectType",
    "CompositorEffectSettings",
    # Asset Shelf
    "EffectPresets",
    "EffectTemplates",
    "EffectCategory",
    "EffectPreset",
    "BUILTIN_EFFECT_PRESETS",
]
