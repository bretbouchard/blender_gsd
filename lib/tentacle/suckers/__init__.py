"""Sucker system for tentacle generation."""

from .types import (
    SuckerStyle,
    SuckerPlacement,
    SuckerConfig,
    SuckerInstance,
    SuckerResult,
    SuckerPreset,
)
from .placement import (
    calculate_sucker_positions,
    calculate_sucker_mesh_size,
)
from .generator import (
    SuckerGenerator,
    generate_suckers,
)

__all__ = [
    # Types
    "SuckerStyle",
    "SuckerPlacement",
    "SuckerConfig",
    "SuckerInstance",
    "SuckerResult",
    "SuckerPreset",

    # Placement
    "calculate_sucker_positions",
    "calculate_sucker_mesh_size",

    # Generator
    "SuckerGenerator",
    "generate_suckers",
]
