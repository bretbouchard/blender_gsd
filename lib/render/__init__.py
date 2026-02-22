"""
Render System - Profiles, Engine Configurations, and Pipeline

This module provides render profiles and engine-specific configurations
for Blender 5.x production rendering.

Key Components:
- profiles: RenderProfile dataclass and preset management
- cycles_config: Cycles X configuration utilities
- eevee_config: EEVEE Next configuration utilities
- passes: Render pass management

Design Philosophy:
- Profiles drive settings. Same artifact = same preview.
- Engine-agnostic profile system with engine-specific implementations
- YAML-based presets for easy customization

Usage:
    from lib.render import get_profile, apply_profile

    # Apply a preset profile
    profile = get_profile('preview')
    apply_profile(profile)

    # Create custom profile
    custom = RenderProfile(
        name='custom',
        engine='CYCLES',
        resolution=(1920, 1080),
        samples=128,
    )
    apply_profile(custom)
"""

from .profiles import (
    RenderProfile,
    get_profile,
    get_all_profiles,
    apply_profile,
    create_profile_from_scene,
    PROFILES,
)

from .cycles_config import (
    CyclesConfig,
    get_cycles_preset,
    apply_cycles_config,
    configure_optix,
    configure_hip,
    configure_metal,
    configure_cpu,
    CYCLES_PRESETS,
)

from .eevee_config import (
    EEVEENextConfig,
    get_eevee_preset,
    apply_eevee_config,
    configure_raytracing,
    configure_taa,
    EEVEE_PRESETS,
)


__all__ = [
    # Profiles
    "RenderProfile",
    "get_profile",
    "get_all_profiles",
    "apply_profile",
    "create_profile_from_scene",
    "PROFILES",
    # Cycles
    "CyclesConfig",
    "get_cycles_preset",
    "apply_cycles_config",
    "configure_optix",
    "configure_hip",
    "configure_metal",
    "configure_cpu",
    "CYCLES_PRESETS",
    # EEVEE Next
    "EEVEENextConfig",
    "get_eevee_preset",
    "apply_eevee_config",
    "configure_raytracing",
    "configure_taa",
    "EEVEE_PRESETS",
]

__version__ = "0.1.0"
