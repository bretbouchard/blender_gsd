"""
Arms module for the tile platform system.

This module provides arm physics simulation, joint management, and
kinematics calculations for mechanical arms in the tile platform.

Example usage:
    from lib.arms import (
        JointType, ArmState, PhysicsMode,
        JointConfig, ArmSegmentConfig, ArmPhysicsConfig,
        Joint, JointChain, PhysicsSimulator
    )

    # Create joint configurations
    joint_configs = [
        JointConfig(JointType.HINGE, min_angle=-1.57, max_angle=1.57),
        JointConfig(JointType.HINGE, min_angle=-1.57, max_angle=1.57),
        JointConfig(JointType.BALL, min_angle=-3.14, max_angle=3.14),
    ]

    # Create joint chain
    chain = JointChain(joint_configs, segment_lengths=[0.5, 1.0, 1.0, 0.5])

    # Create physics simulator
    physics_config = ArmPhysicsConfig(mode=PhysicsMode.HYBRID)
    simulator = PhysicsSimulator(config=physics_config, segment_lengths=[0.5, 1.0, 1.0, 0.5])
    simulator.set_joints(chain.joints)

    # Run simulation step
    target_angles = [0.5, 0.3, 0.2]
    new_angles = simulator.step(chain.joints, target_angles)

    # Calculate end effector position
    end_pos = simulator.calculate_end_effector_position(new_angles, [0.5, 1.0, 1.0, 0.5])

    # Solve for target position
    target_pos = (2.0, 0.0, 1.5)
    ik_angles = simulator.solve_for_target(target_pos, chain.get_joint_angles())
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
]
