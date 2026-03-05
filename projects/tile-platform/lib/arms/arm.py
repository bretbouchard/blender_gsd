"""
Arm assembly class for complete mechanical arm systems.

This module provides the Arm class representing a complete arm assembly
with multiple segments, joints, and kinematics calculations.
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

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


@dataclass
class Arm:
    """Complete arm assembly with segments, joints, and physics.

    The Arm class represents a full mechanical arm with multiple segments
    and joints, providing forward/inverse kinematics and physics simulation.

    Attributes:
        segments: List of arm segment configurations
        joints: JointChain managing all joints
        state: Current operational state of the arm
        base_position: World position of the arm base (x, y, z)
        end_effector_position: Current world position of end effector
        physics_simulator: Physics simulator for arm movement
    """
    segments: List[ArmSegmentConfig]
    joints: JointChain
    state: ArmState = ArmState.IDLE
    base_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    end_effector_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    physics_simulator: Optional[PhysicsSimulator] = None
    _target_position: Tuple[float, float, float] = field(default=(0.0, 0.0, 0.0), repr=False)

    def __post_init__(self) -> None:
        """Initialize physics simulator if not provided."""
        if self.physics_simulator is None:
            config = ArmPhysicsConfig(mode=PhysicsMode.HYBRID)
            segment_lengths = [seg.length for seg in self.segments]
            self.physics_simulator = PhysicsSimulator(
                config=config,
                segment_lengths=segment_lengths
            )
            self.physics_simulator.set_joints(self.joints.joints)

        # Calculate initial end effector position
        self.end_effector_position = self.calculate_end_position(
            self.joints.get_joint_angles()
        )

    def calculate_end_position(
        self,
        joint_angles: List[float]
    ) -> Tuple[float, float, float]:
        """Calculate end effector position using forward kinematics.

        Computes the world position of the end effector given joint angles.
        The calculation is relative to the arm's base position.

        Args:
            joint_angles: List of joint angles in radians

        Returns:
            World position (x, y, z) of the end effector
        """
        if self.physics_simulator is None:
            return self.base_position

        segment_lengths = [seg.length for seg in self.segments]

        # Get local position from physics simulator
        local_pos = self.physics_simulator.calculate_end_effector_position(
            joint_angles,
            segment_lengths
        )

        # Transform to world coordinates by adding base position
        world_pos = (
            self.base_position[0] + local_pos[0],
            self.base_position[1] + local_pos[1],
            self.base_position[2] + local_pos[2]
        )

        return world_pos

    def solve_for_target(
        self,
        target_pos: Tuple[float, float, float]
    ) -> List[float]:
        """Solve inverse kinematics to reach target position.

        Finds joint angles that place the end effector at the target position.
        Uses iterative damped least squares for robust convergence.

        Args:
            target_pos: Target world position (x, y, z)

        Returns:
            List of joint angles that reach the target (or closest achievable)
        """
        if self.physics_simulator is None:
            return self.joints.get_joint_angles()

        # Transform target to local coordinates (relative to base)
        local_target = (
            target_pos[0] - self.base_position[0],
            target_pos[1] - self.base_position[1],
            target_pos[2] - self.base_position[2]
        )

        segment_lengths = [seg.length for seg in self.segments]
        current_angles = self.joints.get_joint_angles()

        # Solve IK in local space
        angles = self.physics_simulator.solve_for_target(
            local_target,
            current_angles,
            segment_lengths
        )

        return angles

    def update(
        self,
        dt: float,
        target_pos: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """Perform physics simulation step towards target.

        Updates joint angles using physics simulation and recalculates
        the end effector position.

        Args:
            dt: Time step in seconds
            target_pos: Target world position for end effector

        Returns:
            New end effector world position after update
        """
        self._target_position = target_pos

        # Update arm state based on movement
        current_end = self.end_effector_position
        distance_to_target = math.sqrt(
            (current_end[0] - target_pos[0]) ** 2 +
            (current_end[1] - target_pos[1]) ** 2 +
            (current_end[2] - target_pos[2]) ** 2
        )

        if distance_to_target < 0.01:
            self.state = ArmState.IDLE
        elif self.state == ArmState.IDLE:
            self.state = ArmState.EXTENDING

        # Solve for target angles
        target_angles = self.solve_for_target(target_pos)

        # Update physics simulator time step
        if self.physics_simulator:
            self.physics_simulator.time_step = dt

        # Update joint chain
        new_angles = self.joints.update_all(dt, target_angles)

        # Calculate new end effector position
        self.end_effector_position = self.calculate_end_position(new_angles)

        return self.end_effector_position

    def get_bounds(self) -> Tuple[float, float, float, float, float, float]:
        """Calculate bounding box of arm in current configuration.

        Returns the axis-aligned bounding box encompassing all arm segments
        in their current configuration.

        Returns:
            Tuple of (min_x, min_y, min_z, max_x, max_y, max_z)
        """
        # Get all joint positions
        positions = self._get_all_segment_positions()

        if not positions:
            return (*self.base_position, *self.base_position)

        # Find min/max for each axis
        min_x = min(p[0] for p in positions)
        min_y = min(p[1] for p in positions)
        min_z = min(p[2] for p in positions)
        max_x = max(p[0] for p in positions)
        max_y = max(p[1] for p in positions)
        max_z = max(p[2] for p in positions)

        return (min_x, min_y, min_z, max_x, max_y, max_z)

    def _get_all_segment_positions(self) -> List[Tuple[float, float, float]]:
        """Get world positions of all segment endpoints.

        Returns:
            List of (x, y, z) positions including base and end effector
        """
        positions = [self.base_position]

        # Get joint angles
        angles = self.joints.get_joint_angles()
        segment_lengths = [seg.length for seg in self.segments]

        # Calculate positions using forward kinematics
        x, y, z = self.base_position
        cumulative_angle = 0.0

        for i, (angle, length) in enumerate(zip(angles, segment_lengths)):
            cumulative_angle += angle
            x += length * math.cos(cumulative_angle)
            z += length * math.sin(cumulative_angle)
            positions.append((x, y, z))

        return positions

    def get_reach(self) -> float:
        """Calculate maximum reach of the arm.

        Returns:
            Maximum reach distance (sum of all segment lengths)
        """
        return sum(seg.length for seg in self.segments)

    def can_reach(self, target_pos: Tuple[float, float, float]) -> bool:
        """Check if target position is within arm's reach.

        Args:
            target_pos: Target world position (x, y, z)

        Returns:
            True if target is within maximum reach
        """
        distance = math.sqrt(
            (target_pos[0] - self.base_position[0]) ** 2 +
            (target_pos[1] - self.base_position[1]) ** 2 +
            (target_pos[2] - self.base_position[2]) ** 2
        )
        return distance <= self.get_reach()

    def reset(self, base_position: Tuple[float, float, float] = None) -> None:
        """Reset arm to initial state.

        Args:
            base_position: Optional new base position
        """
        if base_position is not None:
            self.base_position = base_position

        # Reset all joints
        for joint in self.joints.joints:
            joint.reset(0.0)

        # Recalculate end effector
        self.end_effector_position = self.calculate_end_position(
            self.joints.get_joint_angles()
        )
        self.state = ArmState.IDLE

    @classmethod
    def create_standard_arm(
        cls,
        base_pos: Tuple[float, float, float]
    ) -> "Arm":
        """Create a typical 3-segment arm with standard configuration.

        Factory method for creating a standard arm suitable for most
        tile placement operations.

        Args:
            base_pos: World position for arm base (x, y, z)

        Returns:
            Configured Arm instance
        """
        # Standard joint configurations
        joint_configs = [
            JointConfig(
                joint_type=JointType.HINGE,
                min_angle=-2.0,
                max_angle=2.0,
                damping=0.8,
                stiffness=2.0
            ),
            JointConfig(
                joint_type=JointType.HINGE,
                min_angle=-2.5,
                max_angle=2.5,
                damping=0.7,
                stiffness=1.8
            ),
            JointConfig(
                joint_type=JointType.HINGE,
                min_angle=-2.0,
                max_angle=2.0,
                damping=0.6,
                stiffness=1.5
            ),
        ]

        # Standard segment configurations
        segments = [
            ArmSegmentConfig(length=0.8, width=0.15, height=0.15, mass=2.0),
            ArmSegmentConfig(length=1.0, width=0.12, height=0.12, mass=1.5),
            ArmSegmentConfig(length=0.8, width=0.10, height=0.10, mass=1.0),
            ArmSegmentConfig(length=0.3, width=0.08, height=0.08, mass=0.5),
        ]

        # Create joint chain (n+1 segments for n joints)
        segment_lengths = [seg.length for seg in segments]
        chain = JointChain(joint_configs, segment_lengths)

        # Create physics configuration
        physics_config = ArmPhysicsConfig(
            mode=PhysicsMode.HYBRID,
            target_reach_force=15.0
        )

        # Create physics simulator
        simulator = PhysicsSimulator(
            config=physics_config,
            segment_lengths=segment_lengths
        )
        simulator.set_joints(chain.joints)

        return cls(
            segments=segments,
            joints=chain,
            state=ArmState.IDLE,
            base_position=base_pos,
            physics_simulator=simulator
        )

    @classmethod
    def create_long_arm(
        cls,
        base_pos: Tuple[float, float, float]
    ) -> "Arm":
        """Create extended 4-segment arm for longer reach.

        Factory method for creating a long arm suitable for extended
        range operations.

        Args:
            base_pos: World position for arm base (x, y, z)

        Returns:
            Configured Arm instance with extended reach
        """
        # Extended joint configurations
        joint_configs = [
            JointConfig(
                joint_type=JointType.HINGE,
                min_angle=-2.0,
                max_angle=2.0,
                damping=0.9,
                stiffness=2.5
            ),
            JointConfig(
                joint_type=JointType.HINGE,
                min_angle=-2.2,
                max_angle=2.2,
                damping=0.8,
                stiffness=2.0
            ),
            JointConfig(
                joint_type=JointType.HINGE,
                min_angle=-2.2,
                max_angle=2.2,
                damping=0.7,
                stiffness=1.8
            ),
            JointConfig(
                joint_type=JointType.BALL,
                min_angle=-2.0,
                max_angle=2.0,
                damping=0.6,
                stiffness=1.5
            ),
        ]

        # Extended segment configurations
        segments = [
            ArmSegmentConfig(length=1.0, width=0.18, height=0.18, mass=2.5),
            ArmSegmentConfig(length=1.2, width=0.15, height=0.15, mass=2.0),
            ArmSegmentConfig(length=1.0, width=0.12, height=0.12, mass=1.5),
            ArmSegmentConfig(length=0.8, width=0.10, height=0.10, mass=1.0),
            ArmSegmentConfig(length=0.3, width=0.08, height=0.08, mass=0.5),
        ]

        # Create joint chain
        segment_lengths = [seg.length for seg in segments]
        chain = JointChain(joint_configs, segment_lengths)

        # Create physics configuration with stronger force for longer arm
        physics_config = ArmPhysicsConfig(
            mode=PhysicsMode.HYBRID,
            target_reach_force=20.0
        )

        # Create physics simulator
        simulator = PhysicsSimulator(
            config=physics_config,
            segment_lengths=segment_lengths
        )
        simulator.set_joints(chain.joints)

        return cls(
            segments=segments,
            joints=chain,
            state=ArmState.IDLE,
            base_position=base_pos,
            physics_simulator=simulator
        )
