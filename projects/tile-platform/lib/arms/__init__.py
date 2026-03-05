"""
Arms module for the tile platform system.

This module provides arm physics simulation, joint management, and
kinematics calculations for mechanical arms in the tile platform.

Example usage:
    from lib.arms import (
        JointType, ArmState, PhysicsMode,
        JointConfig, ArmSegmentConfig, ArmPhysicsConfig,
        Joint, JointChain, PhysicsSimulator,
        Arm, ArmController
    )

    # Create a standard arm at a base position
    arm = Arm.create_standard_arm(base_pos=(0.0, 0.0, 0.0))

    # Update arm towards a target
    end_pos = arm.update(dt=0.016, target_pos=(2.0, 0.0, 1.5))

    # Create arm controller for multiple arms
    controller = ArmController()
    arm1 = Arm.create_standard_arm(base_pos=(0.0, 0.0, 0.0))
    arm2 = Arm.create_long_arm(base_pos=(3.0, 0.0, 0.0))

    idx1 = controller.add_arm(arm1)
    idx2 = controller.add_arm(arm2)

    # Assign targets and update
    controller.assign_target(idx1, (2.0, 0.0, 1.5))
    controller.assign_target(idx2, (4.0, 0.0, 1.0))
    positions = controller.update_all(dt=0.016)

    # Check for collisions
    collisions = controller.check_arm_collisions()
"""

from .types import (
    JointType,
    ArmState,
    PhysicsMode,
    JointConfig,
    ArmSegmentConfig,
    ArmPhysicsConfig,
)
from .joints import Joint, JointChain
from .physics import PhysicsSimulator
from .arm import Arm
from .controller import ArmController

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Enums
    "JointType",
    "ArmState",
    "PhysicsMode",
    # Configuration dataclasses
    "JointConfig",
    "ArmSegmentConfig",
    "ArmPhysicsConfig",
    # Core classes
    "Joint",
    "JointChain",
    "PhysicsSimulator",
    # Arm assembly and controller
    "Arm",
    "ArmController",
]
