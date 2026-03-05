"""
Tiles module for the tile platform system.

This module provides tile placement, retraction, and connection logic for
path following, including state management via TileRegistry, placement/removal
via TilePlacer and TileRetractor, and magneto-mechanical connections via
MagnetoMechanical with visual feedback.

Example usage:
    from lib.tiles import (
        TileRegistry, TilePlacer, TileRetractor, TileState,
        MagnetoMechanical, MagnetoConfig, ConnectionStyle,
        VisualEffect, TileFeedback
    )
    from lib.foundation import Platform

    # Create platform and registry
    platform = Platform()
    registry = TileRegistry()

    # Set a target path
    registry.set_target_path([(0, 0), (1, 0), (2, 0), (3, 0)])

    # Create placer and retractor
    placer = TilePlacer(platform, registry, lookahead_distance=5)
    retractor = TileRetractor(platform, registry, keep_distance=3)

    # Create magneto-mechanical connection system
    config = MagnetoConfig(style=ConnectionStyle.HIGH_TECH)
    magneto = MagnetoMechanical(config=config)

    # Update placements based on current position
    to_place = placer.update_placements((0, 0))
    placer.place_tiles(to_place)

    # Connect tiles with visual feedback
    for pos in to_place:
        feedback = magneto.connect_tile(pos)
        # Play feedback animation...

    # Update removals as we move along the path
    to_remove = retractor.update_removals((3, 0))
    retractor.remove_tiles(to_remove)

    # Disconnect tiles with visual feedback
    for pos in to_remove:
        feedback = magneto.disconnect_tile(pos)
        # Play feedback animation...
"""

from .registry import TileRegistry, TileState
from .placer import TilePlacer
from .retractor import TileRetractor
from .feedback import (
    VisualEffect,
    TileFeedback,
    FeedbackSequence,
    connection_sequence,
    disconnection_sequence,
)
from .magneto import MagnetoConfig, MagnetoMechanical, ConnectionStyle

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
    # Feedback
    "VisualEffect",
    "TileFeedback",
    "FeedbackSequence",
    "connection_sequence",
    "disconnection_sequence",
    # Magneto-mechanical
    "MagnetoConfig",
    "MagnetoMechanical",
    "ConnectionStyle",
]
