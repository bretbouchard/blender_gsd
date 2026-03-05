"""
Joint definitions and constraints for mechanical arms.

This module provides the Joint class for individual joint physics and
the JointChain class for managing multiple joints in an arm.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from .types import JointConfig, JointType


@dataclass
class Joint:
    """A single joint in a mechanical arm.

    The Joint class handles the physics simulation for a single joint,
    including angle constraints, damping, and stiffness.

    Attributes:
        config: Configuration for this joint
        current_angle: Current angle in radians
        target_angle: Target angle we're trying to reach
        velocity: Current angular velocity in radians/second
        acceleration: Current angular acceleration in radians/second^2
    """
    config: JointConfig
    current_angle: float = 0.0
    target_angle: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0

    def __post_init__(self) -> None:
        """Ensure initial angle is within limits."""
        self.current_angle = self._clamp_angle(self.current_angle)
        self.target_angle = self._clamp_angle(self.target_angle)

    def _clamp_angle(self, angle: float) -> float:
        """Clamp angle to joint limits.

        Args:
            angle: The angle to clamp

        Returns:
            Angle clamped to [min_angle, max_angle]
        """
        return max(self.config.min_angle, min(self.config.max_angle, angle))

    def update(self, dt: float, target_angle: float) -> float:
        """Update joint physics for one time step.

        Uses spring-damper dynamics to smoothly move toward the target.
        Applies Euler integration for velocity and position updates.

        Args:
            dt: Time step in seconds
            target_angle: Target angle to reach in radians

        Returns:
            New current angle after physics update
        """
        if self.config.joint_type == JointType.FIXED:
            # Fixed joints don't move
            return self.current_angle

        # Clamp target to limits
        self.target_angle = self._clamp_angle(target_angle)

        # Calculate spring force (stiffness * displacement)
        displacement = self.target_angle - self.current_angle
        spring_force = self.config.stiffness * displacement

        # Calculate damping force (damping * velocity)
        damping_force = self.config.damping * self.velocity

        # Net acceleration (F = ma, assume m = 1)
        self.acceleration = spring_force - damping_force

        # Euler integration
        self.velocity += self.acceleration * dt
        self.current_angle += self.velocity * dt

        # Clamp to limits
        self.current_angle = self._clamp_angle(self.current_angle)

        # Zero velocity if at limit and trying to go further
        if self.is_at_limit():
            self.velocity = 0.0

        return self.current_angle

    def get_torque(self) -> float:
        """Calculate torque needed to reach target angle.

        Returns:
            Torque value (stiffness * displacement)
        """
        displacement = self.target_angle - self.current_angle
        return self.config.stiffness * displacement

    def is_at_limit(self) -> bool:
        """Check if joint is at its angular limits.

        Returns:
            True if current angle is at min or max limit
        """
        tolerance = 1e-6
        at_min = abs(self.current_angle - self.config.min_angle) < tolerance
        at_max = abs(self.current_angle - self.config.max_angle) < tolerance
        return at_min or at_max

    def reset(self, angle: float = 0.0) -> None:
        """Reset joint to a specific angle.

        Args:
            angle: Angle to set (default: 0.0)
        """
        self.current_angle = self._clamp_angle(angle)
        self.target_angle = self.current_angle
        self.velocity = 0.0
        self.acceleration = 0.0


class JointChain:
    """A chain of joints forming an arm.

    The JointChain manages multiple joints and provides kinematics
    calculations for forward and inverse kinematics.

    Attributes:
        joints: List of Joint objects in the chain
        segment_lengths: Length of each segment between joints
    """

    def __init__(
        self,
        joint_configs: List[JointConfig],
        segment_lengths: List[float]
    ) -> None:
        """Initialize a joint chain.

        Args:
            joint_configs: Configurations for each joint
            segment_lengths: Length of each segment (should be len(joints) + 1)

        Raises:
            ValueError: If lengths don't match
        """
        if len(segment_lengths) != len(joint_configs) + 1:
            raise ValueError(
                f"segment_lengths ({len(segment_lengths)}) must be one more than "
                f"joint_configs ({len(joint_configs)})"
            )

        self.joints: List[Joint] = [
            Joint(config=config) for config in joint_configs
        ]
        self.segment_lengths = segment_lengths

    def forward_kinematics(self, from_base: bool = True) -> List[Tuple[float, float, float]]:
        """Calculate positions of all joints using forward kinematics.

        Uses DH parameters to compute joint positions in 2D (x, z plane),
        returning 3D coordinates with y = 0.

        Args:
            from_base: If True, return positions relative to base (default True)

        Returns:
            List of (x, y, z) positions for each joint and the end effector
        """
        positions: List[Tuple[float, float, float]] = []

        # Start at origin
        x, y, z = 0.0, 0.0, 0.0
        cumulative_angle = 0.0

        # Base position
        positions.append((x, y, z))

        for i, joint in enumerate(self.joints):
            # Accumulate angle (assuming planar arm for simplicity)
            cumulative_angle += joint.current_angle

            # Get segment length (the segment after this joint)
            segment_length = self.segment_lengths[i + 1] if i + 1 < len(self.segment_lengths) else 0.0

            # Calculate new position
            x += segment_length * (1.0 if cumulative_angle == 0 else 1.0)
            z += 0.0  # For 2D simplified kinematics

        # Simple 2D forward kinematics for planar arm
        positions = []
        x, z = 0.0, 0.0
        cumulative_angle = 0.0
        positions.append((x, 0.0, z))

        for i, joint in enumerate(self.joints):
            cumulative_angle += joint.current_angle
            length = self.segment_lengths[i]
            x += length * (1.0)  # Simplified: assume horizontal segments
            positions.append((x, 0.0, z))

        if not from_base:
            # Return relative positions (each relative to previous)
            relative_positions = [(0.0, 0.0, 0.0)]
            for i in range(1, len(positions)):
                prev = positions[i - 1]
                curr = positions[i]
                relative_positions.append((
                    curr[0] - prev[0],
                    curr[1] - prev[1],
                    curr[2] - prev[2]
                ))
            return relative_positions

        return positions

    def inverse_kinematics(self, target_angles: List[float]) -> List[float]:
        """Calculate joint angles to achieve target configuration.

        This is a simplified implementation that directly maps target
        values to joint angles, clamping to joint limits.

        Args:
            target_angles: Desired angles for each joint

        Returns:
            List of achievable angles (clamped to limits)
        """
        if len(target_angles) != len(self.joints):
            raise ValueError(
                f"target_angles ({len(target_angles)}) must match "
                f"joint count ({len(self.joints)})"
            )

        achievable_angles: List[float] = []
        for joint, target in zip(self.joints, target_angles):
            clamped = max(
                joint.config.min_angle,
                min(joint.config.max_angle, target)
            )
            achievable_angles.append(clamped)

        return achievable_angles

    def get_joint_angles(self) -> List[float]:
        """Get current angles of all joints.

        Returns:
            List of current joint angles
        """
        return [joint.current_angle for joint in self.joints]

    def set_joint_angles(self, angles: List[float]) -> None:
        """Set all joint angles directly.

        Args:
            angles: New angles for each joint
        """
        if len(angles) != len(self.joints):
            raise ValueError(
                f"angles ({len(angles)}) must match joint count ({len(self.joints)})"
            )

        for joint, angle in zip(self.joints, angles):
            joint.current_angle = joint._clamp_angle(angle)

    def update_all(self, dt: float, target_angles: List[float]) -> List[float]:
        """Update all joints for one time step.

        Args:
            dt: Time step in seconds
            target_angles: Target angles for each joint

        Returns:
            List of new joint angles
        """
        if len(target_angles) != len(self.joints):
            raise ValueError(
                f"target_angles ({len(target_angles)}) must match "
                f"joint count ({len(self.joints)})"
            )

        return [
            joint.update(dt, target)
            for joint, target in zip(self.joints, target_angles)
        ]

    def __len__(self) -> int:
        """Return number of joints in chain."""
        return len(self.joints)

    def __getitem__(self, index: int) -> Joint:
        """Get joint by index."""
        return self.joints[index]
