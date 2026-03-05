"""
Arm physics type definitions for the tile platform system.

This module defines the core data types, enums, and configuration classes
used for arm physics simulation. It is designed to be pure Python
without Blender dependencies for maximum testability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


class JointType(Enum):
    """Enumeration of supported joint types for mechanical arms.

    HINGE: Single-axis rotation (like a door hinge)
    BALL: Multi-axis rotation (like a ball joint)
    PRISMATIC: Linear sliding motion (like a drawer)
    FIXED: No movement (rigid connection)
    """
    HINGE = "hinge"
    BALL = "ball"
    PRISMATIC = "prismatic"
    FIXED = "fixed"


class ArmState(Enum):
    """Enumeration of arm operational states.

    IDLE: Arm is not moving
    EXTENDING: Arm is reaching out to place a tile
    PLACING: Arm is in the process of placing a tile
    RETRACTING: Arm is pulling back after placing
    """
    IDLE = "idle"
    EXTENDING = "extending"
    PLACING = "placing"
    RETRACTING = "retracting"


class PhysicsMode(Enum):
    """Enumeration of physics simulation modes.

    DYNAMIC: Full physics simulation with forces and torques
    KINEMATIC: Direct position control without physics
    HYBRID: Physics simulation with guaranteed target reach
    """
    DYNAMIC = "dynamic"
    KINEMATIC = "kinematic"
    HYBRID = "hybrid"


@dataclass
class JointConfig:
    """Configuration for a single joint in the arm.

    Attributes:
        joint_type: The type of joint (HINGE, BALL, PRISMATIC, FIXED)
        min_angle: Minimum angle in radians (default: -pi)
        max_angle: Maximum angle in radians (default: pi)
        damping: Damping coefficient for velocity reduction (default: 0.5)
        stiffness: Stiffness coefficient for spring-like behavior (default: 1.0)
    """
    joint_type: JointType
    min_angle: float = -3.14159  # -pi
    max_angle: float = 3.14159   # pi
    damping: float = 0.5
    stiffness: float = 1.0

    def __post_init__(self) -> None:
        """Validate joint configuration after initialization."""
        if self.min_angle > self.max_angle:
            raise ValueError(
                f"min_angle ({self.min_angle}) must be <= max_angle ({self.max_angle})"
            )
        if self.damping < 0:
            raise ValueError(f"Damping must be non-negative, got {self.damping}")
        if self.stiffness < 0:
            raise ValueError(f"Stiffness must be non-negative, got {self.stiffness}")


@dataclass
class ArmSegmentConfig:
    """Configuration for a physical segment of the arm.

    Attributes:
        length: Length of the segment in world units (default: 1.0)
        width: Width of the segment (default: 0.1)
        height: Height of the segment (default: 0.1)
        mass: Mass of the segment in kg (default: 1.0)
    """
    length: float = 1.0
    width: float = 0.1
    height: float = 0.1
    mass: float = 1.0

    def __post_init__(self) -> None:
        """Validate arm segment configuration after initialization."""
        if self.length <= 0:
            raise ValueError(f"Length must be positive, got {self.length}")
        if self.width <= 0:
            raise ValueError(f"Width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"Height must be positive, got {self.height}")
        if self.mass <= 0:
            raise ValueError(f"Mass must be positive, got {self.mass}")


@dataclass
class ArmPhysicsConfig:
    """Configuration for arm physics simulation.

    Attributes:
        mode: Physics simulation mode (default: HYBRID)
        gravity: Gravitational acceleration (default: -9.81)
        air_resistance: Air resistance coefficient (default: 0.1)
        target_reach_force: Force applied to reach target position (default: 10.0)
        segment_configs: Optional list of segment configurations
    """
    mode: PhysicsMode = PhysicsMode.HYBRID
    gravity: float = -9.81
    air_resistance: float = 0.1
    target_reach_force: float = 10.0
    segment_configs: Tuple[ArmSegmentConfig, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate arm physics configuration after initialization."""
        if self.air_resistance < 0:
            raise ValueError(
                f"Air resistance must be non-negative, got {self.air_resistance}"
            )
        if self.target_reach_force < 0:
            raise ValueError(
                f"Target reach force must be non-negative, got {self.target_reach_force}"
            )
