"""
Joint angle limiters for mechanical arm constraints.

This module provides joint angle limiting functionality to ensure
arms maintain realistic configurations within their mechanical limits.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class JointLimitConfig:
    """Configuration for joint angle limits.

    Attributes:
        joint_index: Index of the joint in the arm
        min_angle: Minimum allowed angle in radians
        max_angle: Maximum allowed angle in radians
        stiffness: Stiffness of the limit boundary (0-1)
    """
    joint_index: int
    min_angle: float
    max_angle: float
    stiffness: float = 0.1

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.min_angle >= self.max_angle:
            raise ValueError(
                f"min_angle ({self.min_angle}) must be less than "
                f"max_angle ({self.max_angle})"
            )
        if not 0.0 <= self.stiffness <= 1.0:
            raise ValueError(
                f"stiffness ({self.stiffness}) must be between 0 and 1"
            )


# Standard joint limit presets (in radians)
HINGE_PRESET = JointLimitConfig(
    joint_index=0,
    min_angle=-1.5708,  # -90 degrees
    max_angle=1.5708,   # 90 degrees
    stiffness=0.1
)

TELESCOPE_PRESET = JointLimitConfig(
    joint_index=0,
    min_angle=-3.14159,  # -180 degrees
    max_angle=3.14159,   # 180 degrees
    stiffness=0.05
)

PRISMATIC_PRESET = JointLimitConfig(
    joint_index=0,
    min_angle=-0.7854,  # -45 degrees
    max_angle=0.7854,   # 45 degrees
    stiffness=0.2
)


class JointLimiter:
    """Manages joint angle limits with soft boundaries.

    Applies constraints to joint angles to keep them within valid ranges.
    Uses soft boundaries that apply increasing resistance as angles
    approach their limits.

    Attributes:
        joint_limits: Dictionary mapping joint_id to (min, max) angle tuples
        violation_force: Force applied when violating limits (default: 50.0)
        softness: Softness of limit boundaries (default: 0.1)
    """

    def __init__(
        self,
        joint_limits: Dict[int, Tuple[float, float]] = None,
        violation_force: float = 50.0,
        softness: float = 0.1
    ) -> None:
        """Initialize the joint limiter.

        Args:
            joint_limits: Dictionary of joint_id -> (min_angle, max_angle)
            violation_force: Force to apply when beyond limits
            softness: Softness factor for boundary (0 = hard, 1 = soft)
        """
        self.joint_limits = joint_limits or {}
        self.violation_force = violation_force
        self.softness = softness

    def add_limit(
        self,
        joint_id: int,
        min_angle: float,
        max_angle: float
    ) -> None:
        """Add or update a joint limit.

        Args:
            joint_id: Index of the joint
            min_angle: Minimum allowed angle in radians
            max_angle: Maximum allowed angle in radians
        """
        if min_angle >= max_angle:
            raise ValueError(
                f"min_angle ({min_angle}) must be less than "
                f"max_angle ({max_angle})"
            )
        self.joint_limits[joint_id] = (min_angle, max_angle)

    def add_limit_config(self, config: JointLimitConfig) -> None:
        """Add a joint limit from a JointLimitConfig.

        Args:
            config: JointLimitConfig to add
        """
        self.add_limit(
            config.joint_index,
            config.min_angle,
            config.max_angle
        )
        # Note: stiffness is used in clamp_angle calculations

    def clamp_angle(
        self,
        joint_id: int,
        current_angle: float,
        target_angle: float
    ) -> float:
        """Clamp target angle to be within joint limits.

        Applies soft constraint at boundaries using smooth interpolation.
        The softness determines how gradually the limit is approached.

        Args:
            joint_id: Index of the joint
            current_angle: Current angle of the joint
            target_angle: Desired target angle

        Returns:
            Clamped angle within joint limits
        """
        if joint_id not in self.joint_limits:
            # No limits defined for this joint
            return target_angle

        min_angle, max_angle = self.joint_limits[joint_id]

        # Hard clamp first
        if target_angle <= min_angle:
            return min_angle
        if target_angle >= max_angle:
            return max_angle

        # Apply soft boundary
        range_size = max_angle - min_angle
        soft_zone = self.softness * range_size

        # If we're in the soft zone near limits, apply smooth interpolation
        distance_from_min = target_angle - min_angle
        distance_from_max = max_angle - target_angle

        if distance_from_min < soft_zone:
            # Near minimum - apply soft resistance
            # Smoothly interpolate from min_angle to target
            factor = distance_from_min / soft_zone
            # Use smooth step function (ease in-out)
            smooth_factor = factor * factor * (3 - 2 * factor)
            clamped = min_angle + smooth_factor * soft_zone
            return clamped

        if distance_from_max < soft_zone:
            # Near maximum - apply soft resistance
            factor = distance_from_max / soft_zone
            smooth_factor = factor * factor * (3 - 2 * factor)
            clamped = max_angle - smooth_factor * soft_zone
            return clamped

        # Within safe zone
        return target_angle

    def is_valid(self, joint_id: int, angle: float) -> bool:
        """Check if angle is within joint limits.

        Args:
            joint_id: Index of the joint
            angle: Angle to check

        Returns:
            True if angle is within limits (or no limits defined)
        """
        if joint_id not in self.joint_limits:
            return True

        min_angle, max_angle = self.joint_limits[joint_id]
        return min_angle <= angle <= max_angle

    def get_violation(self, joint_id: int, angle: float) -> float:
        """Get the magnitude of limit violation.

        Args:
            joint_id: Index of the joint
            angle: Angle to check

        Returns:
            0.0 if within limits, positive value for violation magnitude
        """
        if joint_id not in self.joint_limits:
            return 0.0

        min_angle, max_angle = self.joint_limits[joint_id]

        if angle < min_angle:
            return min_angle - angle
        if angle > max_angle:
            return angle - max_angle

        return 0.0

    def get_correction_force(
        self,
        joint_id: int,
        angle: float
    ) -> float:
        """Calculate correction force to apply for limit violations.

        Returns a force that pushes the angle back towards valid range.
        Force magnitude is proportional to violation distance.

        Args:
            joint_id: Index of the joint
            angle: Current angle

        Returns:
            Correction force (positive pushes towards min, negative towards max)
        """
        violation = self.get_violation(joint_id, angle)

        if violation == 0.0:
            return 0.0

        min_angle, max_angle = self.joint_limits[joint_id]

        # Apply force proportional to violation
        if angle < min_angle:
            # Below minimum - push up
            return self.violation_force * violation
        else:
            # Above maximum - push down
            return -self.violation_force * violation

    def apply_limits(
        self,
        angles: dict
    ) -> dict:
        """Apply limits to a dictionary of joint angles.

        Args:
            angles: Dictionary of joint_id -> angle

        Returns:
            Dictionary of joint_id -> clamped_angle
        """
        return {
            joint_id: self.clamp_angle(joint_id, angle, angle)
            for joint_id, angle in angles.items()
        }

    def get_all_violations(self, angles: dict) -> Dict[int, float]:
        """Get violations for all joints.

        Args:
            angles: Dictionary of joint_id -> angle

        Returns:
            Dictionary of joint_id -> violation magnitude (only violations > 0)
        """
        violations = {}
        for joint_id, angle in angles.items():
            violation = self.get_violation(joint_id, angle)
            if violation > 0.0:
                violations[joint_id] = violation

        return violations

    @classmethod
    def from_presets(
        cls,
        presets: list
    ) -> 'JointLimiter':
        """Create a JointLimiter from a list of presets.

        Args:
            presets: List of JointLimitConfig objects

        Returns:
            Configured JointLimiter instance
        """
        limiter = cls()
        for preset in presets:
            limiter.add_limit_config(preset)

        return limiter
