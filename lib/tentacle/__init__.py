"""
Tentacle System - Procedural generation for organic tentacles.

Primary use case: Zombie mouth tentacles for horror characters.

This module provides:
- Core data types for tentacle configuration
- YAML preset loading with caching
- Taper profile calculations
- Zombie mouth multi-tentacle configurations

Usage:
    from lib.tentacle import (
        # Types
        TentacleConfig,
        TaperProfile,
        SegmentConfig,
        ZombieMouthConfig,

        # Preset loader
        TentaclePresetLoader,

        # Convenience functions
        load_tentacle,
        load_zombie_mouth,
        list_tentacle_presets,
        list_zombie_mouth_presets,
    )

    # Load a preset
    config = load_tentacle("zombie_main")
    print(f"Length: {config.length}m")

    # Create custom configuration
    custom = TentacleConfig(
        length=1.5,
        base_diameter=0.10,
        tip_diameter=0.02,
        segments=30,
        taper_profile="organic",
        twist=20.0,
    )

    # Load zombie mouth configuration
    mouth = load_zombie_mouth("standard")
    for tentacle_config in mouth.get_tentacle_configs():
        print(f"Tentacle: {tentacle_config.name}")

Part of Phase 19.1: Tentacle Geometry System
"""

__version__ = "0.1.0"

# Core types
from .types import (
    TentacleConfig,
    TaperProfile,
    SegmentConfig,
    ZombieMouthConfig,
)

# Preset loader
from .presets import (
    TentaclePresetLoader,
    load_tentacle,
    load_zombie_mouth,
    list_tentacle_presets,
    list_zombie_mouth_presets,
)

__all__ = [
    # Version
    "__version__",

    # Types
    "TentacleConfig",
    "TaperProfile",
    "SegmentConfig",
    "ZombieMouthConfig",

    # Presets
    "TentaclePresetLoader",
    "load_tentacle",
    "load_zombie_mouth",
    "list_tentacle_presets",
    "list_zombie_mouth_presets",
]
