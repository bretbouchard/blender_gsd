"""
Folding module for the tile platform system.

This module provides arm folding systems for compact storage,
including pose management, animation, and controller integration.

Example usage:
    from lib.folding import (
        FoldingPoseState,
        FoldingConfig,
        FoldingPose,
        FoldingAnimator,
        FoldingController
    )

    # Create folding configuration for an arm
    config = FoldingConfig(
        arm_index=0,
        folded_angles={0: 0.0, 1: -1.57, 2: -1.57},
        deployed_angles={0: 0.0, 1: 0.0, 2: 0.0},
        transition_duration=0.5
    )

    # Create animator with configuration
    animator = FoldingAnimator(
        folding_configs={0: config},
        transition_easing="smooth"
    )

    # Fold an arm
    animator.fold_arm(0)

    # Update animation
    poses = animator.update(dt=0.016)

    # Check status
    folded = animator.get_folded_positions()
    deployed = animator.get_deployed_positions()

    # Create controller for tile integration
    from lib.tiles import TileRegistry
    registry = TileRegistry()
    controller = FoldingController(animator, registry)

    # Respond to tile events
    controller.on_tile_placed((0, 0), arm_index=0)
    controller.on_tile_removed((0, 0), arm_index=0)
"""

from .pose import (
    FoldingPoseState,
    FoldingConfig,
    FoldingPose,
)

# Note: FoldingController will be added in 05-02
from .animator import (
    FoldingAnimator,
    ease_linear,
    ease_in_out,
    ease_smooth,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Pose system
    "FoldingPoseState",
    "FoldingConfig",
    "FoldingPose",
    # Animator
    "FoldingAnimator",
    # Easing functions
    "ease_linear",
    "ease_in_out",
    "ease_smooth",
]
