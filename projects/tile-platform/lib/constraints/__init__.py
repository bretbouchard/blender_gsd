"""
Constraints module for the tile platform system.

This module provides constraint systems that ensure mechanical arms
reach their target positions and maintain valid configurations.

Example usage:
    from lib.constraints import (
        TargetReachConstraint,
        JointLimiter,
        JointLimitConfig,
        HINGE_PRESET,
        TELESCOPE_PRESET,
        PRISMATIC_PRESET
    )

    # Create target reach constraint
    reach_constraint = TargetReachConstraint(
        max_deviation=0.1,
        correction_force=10.0
    )

    # Check if target is reached
    is_reached = reach_constraint.is_reached(
        current_pos=(1.0, 0.0, 1.5),
        target_pos=(1.05, 0.0, 1.48),
        velocity=(0.001, 0.0, 0.001)
    )

    # Create joint limiter with presets
    limiter = JointLimiter.from_presets([
        HINGE_PRESET,
        TELESCOPE_PRESET,
        PRISMATIC_PRESET
    ])

    # Clamp joint angle to valid range
    clamped = limiter.clamp_angle(
        joint_id=0,
        current_angle=0.0,
        target_angle=1.8  # Will be clamped to ~1.57 for hinge
    )
"""

from .target_reach import TargetReachConstraint
from .limiters import (
    JointLimiter,
    JointLimitConfig,
    HINGE_PRESET,
    TELESCOPE_PRESET,
    PRISMATIC_PRESET
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Target reach constraint
    "TargetReachConstraint",
    # Joint limiters
    "JointLimiter",
    "JointLimitConfig",
    # Presets
    "HINGE_PRESET",
    "TELESCOPE_PRESET",
    "PRISMATIC_PRESET",
]
