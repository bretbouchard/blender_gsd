"""
Target reach constraint system for mechanical arms.

This module provides the TargetReachConstraint class which guarantees
that arms reach their target positions within a specified tolerance.
"""

import math
from typing import Tuple


class TargetReachConstraint:
    """Constraint that ensures arms reach their target positions.

    Uses a spring-damper model to compute correction forces that guide
    the arm towards the target while preventing overshoot and oscillation.

    Attributes:
        max_deviation: Maximum allowed deviation from target (default: 0.1)
        overshoot_damping: Damping factor to prevent overshoot (default: 0.5)
        settling_threshold: Velocity threshold for settling detection (default: 0.01)
        correction_force: Force magnitude for correction (default: 10.0)
    """

    def __init__(
        self,
        max_deviation: float = 0.1,
        overshoot_damping: float = 0.5,
        settling_threshold: float = 0.01,
        correction_force: float = 10.0
    ) -> None:
        """Initialize the target reach constraint.

        Args:
            max_deviation: Maximum allowed distance from target
            overshoot_damping: Damping factor (0-1) to reduce overshoot
            settling_threshold: Velocity below which arm is considered settled
            correction_force: Spring force constant for corrections
        """
        self.max_deviation = max_deviation
        self.overshoot_damping = overshoot_damping
        self.settling_threshold = settling_threshold
        self.correction_force = correction_force

    def compute_correction(
        self,
        current_pos: Tuple[float, float, float],
        target_pos: Tuple[float, float, float],
        velocity: Tuple[float, float, float],
        dt: float
    ) -> Tuple[float, float, float]:
        """Compute correction force to apply to reach target.

        Uses a spring-damper model that applies forces proportional to
        position error and velocity. This creates smooth, stable motion
        that converges to the target.

        Args:
            current_pos: Current position (x, y, z)
            target_pos: Target position (x, y, z)
            velocity: Current velocity (vx, vy, vz)
            dt: Time step in seconds

        Returns:
            Correction force vector (fx, fy, fz) to apply
        """
        # Calculate position error
        error = (
            target_pos[0] - current_pos[0],
            target_pos[1] - current_pos[1],
            target_pos[2] - current_pos[2]
        )

        # Calculate distance (magnitude of error)
        distance = math.sqrt(error[0]**2 + error[1]**2 + error[2]**2)

        # If already at target, no correction needed
        if distance < 0.0001:
            return (0.0, 0.0, 0.0)

        # Normalize error direction
        error_normalized = (
            error[0] / distance,
            error[1] / distance,
            error[2] / distance
        )

        # Spring force: proportional to distance
        spring_force = self.correction_force * distance

        # Damper force: opposes velocity
        velocity_magnitude = math.sqrt(
            velocity[0]**2 + velocity[1]**2 + velocity[2]**2
        )

        # Only apply damping if moving towards target
        if velocity_magnitude > 0.0001:
            # Dot product to check if moving towards target
            velocity_normalized = (
                velocity[0] / velocity_magnitude,
                velocity[1] / velocity_magnitude,
                velocity[2] / velocity_magnitude
            )

            # Calculate alignment (1 = directly towards, -1 = directly away)
            alignment = (
                error_normalized[0] * velocity_normalized[0] +
                error_normalized[1] * velocity_normalized[1] +
                error_normalized[2] * velocity_normalized[2]
            )

            # Apply damping based on alignment and overshoot damping factor
            if alignment > 0:
                # Moving towards target - apply damping to prevent overshoot
                damper_force = (
                    self.overshoot_damping * velocity_magnitude * alignment
                )
            else:
                # Moving away from target - no damping
                damper_force = 0.0
        else:
            damper_force = 0.0

        # Net force: spring - damper
        net_force = spring_force - damper_force

        # Apply in direction of error
        correction = (
            net_force * error_normalized[0] * dt,
            net_force * error_normalized[1] * dt,
            net_force * error_normalized[2] * dt
        )

        return correction

    def is_reached(
        self,
        current_pos: Tuple[float, float, float],
        target_pos: Tuple[float, float, float],
        velocity: Tuple[float, float, float]
    ) -> bool:
        """Check if arm has settled at target position.

        Returns True if the arm is within max_deviation of the target
        AND the velocity is below settling_threshold.

        Args:
            current_pos: Current position (x, y, z)
            target_pos: Target position (x, y, z)
            velocity: Current velocity (vx, vy, vz)

        Returns:
            True if target has been reached and arm is settled
        """
        # Check position
        deviation = self.get_deviation(current_pos, target_pos)
        if deviation > self.max_deviation:
            return False

        # Check velocity
        velocity_magnitude = math.sqrt(
            velocity[0]**2 + velocity[1]**2 + velocity[2]**2
        )

        return velocity_magnitude < self.settling_threshold

    def get_deviation(
        self,
        current_pos: Tuple[float, float, float],
        target_pos: Tuple[float, float, float]
    ) -> float:
        """Calculate distance from current position to target.

        Args:
            current_pos: Current position (x, y, z)
            target_pos: Target position (x, y, z)

        Returns:
            Euclidean distance between positions
        """
        dx = current_pos[0] - target_pos[0]
        dy = current_pos[1] - target_pos[1]
        dz = current_pos[2] - target_pos[2]

        return math.sqrt(dx**2 + dy**2 + dz**2)

    def is_converged(
        self,
        deviation_history: list,
        window_size: int = 5,
        threshold: float = 0.001
    ) -> bool:
        """Check if constraint has converged based on deviation history.

        Analyzes recent deviation values to determine if the arm has
        stabilized at the target.

        Args:
            deviation_history: List of recent deviation measurements
            window_size: Number of recent values to check
            threshold: Maximum variation allowed for convergence

        Returns:
            True if deviation has stabilized within threshold
        """
        if len(deviation_history) < window_size:
            return False

        recent = deviation_history[-window_size:]

        # Check if all recent values are below max_deviation
        if any(d > self.max_deviation for d in recent):
            return False

        # Check variation in recent values
        avg = sum(recent) / len(recent)
        variation = max(abs(d - avg) for d in recent)

        return variation < threshold
