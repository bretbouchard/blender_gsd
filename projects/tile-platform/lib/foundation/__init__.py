"""
Foundation module for the tile platform system.

This module provides the core classes and types for the mechanical
tile platform, including Platform, Grid, TileConfig, and related types.

Example usage:
    from lib.foundation import Platform, PlatformConfig, TileShape

    config = PlatformConfig(
        initial_size=(3, 3),
        tile_shape=TileShape.SQUARE,
        arm_count=4
    )
    platform = Platform(config)
    platform.place_tile((5, 5))  # Extend platform
"""

from .types import TileConfig, TileShape, PlatformConfig, ArmConfig
from .grid import Grid
from .platform import Platform

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Types
    "TileConfig",
    "TileShape",
    "PlatformConfig",
    "ArmConfig",
    # Core classes
    "Grid",
    "Platform",
]
