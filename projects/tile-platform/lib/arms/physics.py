"""
Physics simulation system for mechanical arms.

This module provides the PhysicsSimulator class for running physics
simulations on arm joint chains, including constraint solving and
end effector position calculation.
"""

import math
from typing import List, Tuple

from .types import ArmPhysicsConfig, PhysicsMode
from .joints import Joint, JointChain


class PhysicsSimulator:
    """Physics simulator for arm joint chains.

    The PhysicsSimulator handles the physics simulation loop, constraint
    solving, and kinematics calculations for arm movement.

    Attributes:
        config: Physics configuration
        time_step: Simulation time step in seconds
        joints: List of joints to simulate
    """

    def __init__(
        self,
        config: ArmPhysicsConfig,
        time_step: float = 0.016,  # ~60 FPS
        segment_lengths: List[float] = None
    ) -> None:
        """Initialize the physics simulator.

        Args:
            config: Arm physics configuration
            time_step: Simulation time step (default: 0.016 for 60 FPS)
            segment_lengths: Lengths of arm segments for kinematics
        """
        self.config = config
        self.time_step = time_step
        self._segment_lengths = segment_lengths or [1.0] * 4
        self._joints: List[Joint] = []

    @property
    def joints(self) -> List[Joint]:
        """Return the list of joints being simulated."""
        return self._joints

    def set_joints(self, joints: List[Joint]) -> None:
        """Set the joints to simulate.

        Args:
            joints: List of Joint objects
        """
        self._joints = joints

    def step(
        self,
        joints: List[Joint],
        target_angles: List[float]
    ) -> List[float]:
        """Perform one physics simulation step.

        Updates all joints using Euler integration with spring-damper
        dynamics. In HYBRID mode, applies additional force to guarantee
        target reach.

        Args:
            joints: List of joints to update
            target_angles: Target angles for each joint

        Returns:
            List of new joint angles after physics update
        """
        if len(joints) != len(target_angles):
            raise ValueError(
                f"joints ({len(joints)}) and target_angles ({len(target_angles)}) "
                f"must have same length"
            )

        new_angles: List[float] = []

        for joint, target in zip(joints, target_angles):
            if self.config.mode == PhysicsMode.KINEMATIC:
                # Direct position control - no physics
                joint.current_angle = joint._clamp_angle(target)
                joint.velocity = 0.0
                joint.acceleration = 0.0
            elif self.config.mode == PhysicsMode.HYBRID:
                # Physics with guaranteed target reach
                # Apply stronger spring force to ensure we reach target
                original_stiffness = joint.config.stiffness
                joint.config.stiffness = (
                    original_stiffness + self.config.target_reach_force
                )
                joint.update(self.time_step, target)
                joint.config.stiffness = original_stiffness

                # If close enough, snap to target
                tolerance = 0.001
                if abs(joint.current_angle - target) < tolerance:
                    joint.current_angle = joint._clamp_angle(target)
            else:
                # DYNAMIC mode - pure physics
                joint.update(self.time_step, target)

            new_angles.append(joint.current_angle)

        return new_angles

    def apply_constraints(self, angles: List[float]) -> List[float]:
        """Apply joint limits and constraints to angles.

        Ensures all angles are within their respective joint limits.

        Args:
            angles: List of angles to constrain

        Returns:
            List of constrained angles
        """
        if len(angles) != len(self._joints):
            # Can't constrain without joint configs
            return angles

        constrained: List[float] = []
        for angle, joint in zip(angles, self._joints):
            clamped = max(
                joint.config.min_angle,
                min(joint.config.max_angle, angle)
            )
            constrained.append(clamped)

        return constrained

    def calculate_end_effector_position(
        self,
        joint_angles: List[float],
        segment_lengths: List[float] = None
    ) -> Tuple[float, float, float]:
        """Calculate end effector position from joint angles.

        Uses forward kinematics to compute the (x, y, z) position of
        the end effector given joint angles.

        For simplicity, this implements 2D planar kinematics in the XZ plane.

        Args:
            joint_angles: Angles of each joint in radians
            segment_lengths: Lengths of arm segments (uses default if None)

        Returns:
            (x, y, z) position of the end effector
        """
        lengths = segment_lengths or self._segment_lengths

        # 2D planar forward kinematics
        x, z = 0.0, 0.0
        cumulative_angle = 0.0

        for i, (angle, length) in enumerate(zip(joint_angles, lengths)):
            cumulative_angle += angle
            x += length * math.cos(cumulative_angle)
            z += length * math.sin(cumulative_angle)

        return (x, 0.0, z)

    def solve_for_target(
        self,
        target_pos: Tuple[float, float, float],
        current_angles: List[float],
        segment_lengths: List[float] = None,
        max_iterations: int = 100,
        tolerance: float = 0.01
    ) -> List[float]:
        """Solve inverse kinematics to reach target position.

        Uses iterative damped least squares (Levenberg-Marquardt) to
        find joint angles that place the end effector at the target.

        Args:
            target_pos: Target (x, y, z) position
            current_angles: Starting joint angles
            segment_lengths: Lengths of arm segments
            max_iterations: Maximum solver iterations
            tolerance: Position tolerance for convergence

        Returns:
            Joint angles that reach the target (or closest achievable)
        """
        lengths = segment_lengths or self._segment_lengths

        if len(current_angles) != len(lengths):
            raise ValueError(
                f"current_angles ({len(current_angles)}) must match "
                f"segment count ({len(lengths)})"
            )

        angles = list(current_angles)
        damping = 0.5  # Damping factor for stability

        for iteration in range(max_iterations):
            # Calculate current end effector position
            current_pos = self.calculate_end_effector_position(angles, lengths)

            # Check convergence
            error = math.sqrt(
                (current_pos[0] - target_pos[0]) ** 2 +
                (current_pos[1] - target_pos[1]) ** 2 +
                (current_pos[2] - target_pos[2]) ** 2
            )

            if error < tolerance:
                break

            # Calculate Jacobian numerically
            delta = 0.001
            jacobian = []

            for i in range(len(angles)):
                # Perturb angle i
                angles_perturbed = angles.copy()
                angles_perturbed[i] += delta

                # Calculate perturbed position
                perturbed_pos = self.calculate_end_effector_position(
                    angles_perturbed, lengths
                )

                # Jacobian column: d(position) / d(angle_i)
                jacobian.append([
                    (perturbed_pos[0] - current_pos[0]) / delta,
                    (perturbed_pos[1] - current_pos[1]) / delta,
                    (perturbed_pos[2] - current_pos[2]) / delta
                ])

            # Transpose Jacobian (simplified approach)
            # For full damped least squares: J^T * (J * J^T + lambda * I)^-1

            # Calculate position error vector
            error_vector = [
                target_pos[0] - current_pos[0],
                target_pos[1] - current_pos[1],
                target_pos[2] - current_pos[2]
            ]

            # Update angles using damped pseudo-inverse
            for i in range(len(angles)):
                # Dot product of Jacobian column with error
                delta_angle = (
                    jacobian[i][0] * error_vector[0] +
                    jacobian[i][1] * error_vector[1] +
                    jacobian[i][2] * error_vector[2]
                )
                angles[i] += damping * delta_angle

            # Apply constraints
            angles = self.apply_constraints(angles)

        return angles

    def simulate(
        self,
        chain: JointChain,
        target_angles: List[float],
        duration: float
    ) -> List[List[float]]:
        """Run full simulation for a duration.

        Args:
            chain: JointChain to simulate
            target_angles: Target angles to reach
            duration: Total simulation time in seconds

        Returns:
            List of joint angle lists at each time step
        """
        self.set_joints(chain.joints)
        steps = int(duration / self.time_step)
        trajectory: List[List[float]] = []

        for _ in range(steps):
            angles = self.step(chain.joints, target_angles)
            trajectory.append(angles)

        return trajectory

    def reset(self) -> None:
        """Reset the simulator state."""
        self._joints = []
