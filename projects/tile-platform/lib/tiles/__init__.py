"""
Tiles module for the tile platform system.

This module provides tile placement and retraction logic for path following,
including state management via TileRegistry and placement/removal via
TilePlacer and TileRetractor.

Example usage:
    from lib.tiles import TileRegistry, TilePlacer, TileRetractor, TileState
    from lib.foundation import Platform

    # Create platform and registry
    platform = Platform()
    registry = TileRegistry()

    # Set a target path
    registry.set_target_path([(0, 0), (1, 0), (2, 0), (3, 0)])

    # Create placer and retractor
    placer = TilePlacer(platform, registry, lookahead_distance=5)
    retractor = TileRetractor(platform, registry, keep_distance=3)

    # Update placements based on current position
    to_place = placer.update_placements((0, 0))
    placer.place_tiles(to_place)

    # Update removals as we move along the path
    to_remove = retractor.update_removals((3, 0))
    retractor.remove_tiles(to_remove)
"""

from .registry import TileRegistry, TileState
from .placer import TilePlacer
from .retractor import TileRetractor

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Registry
    "TileRegistry",
    "TileState",
    # Placement
    "TilePlacer",
    # Retraction
    "TileRetractor",
]
