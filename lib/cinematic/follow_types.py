"""
Follow Camera Types and Configurations

Defines dataclasses for cinematic follow camera modes, targeting, and
camera configuration for smooth subject tracking.

Part of Phase 6.3 - Follow Camera System
Requirements: REQ-FOLLOW-01 through REQ-FOLLOW-05
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum


class FollowModeType(Enum):
    """
    Cinematic follow modes for different shooting styles.

    Each mode defines how the camera tracks and follows the subject:
    - tight: Camera stays centered, immediate response
    - loose: Camera lags behind, smooth delayed feel
    - anticipatory: Camera moves before subject using velocity prediction
    - elastic: Spring-like behavior, camera snaps back to center
    - orbit: Camera circles subject while following
    """
    TIGHT = "tight"
    LOOSE = "loose"
    ANTICIPATORY = "anticipatory"
    ELASTIC = "elastic"
    ORBIT = "orbit"


@dataclass
class FollowConfig:
    """
    Configuration for camera following behavior.

    Defines all parameters for subject tracking including smoothing,
    dead zones, speed limits, and positioning preferences.

    Attributes:
        mode: Following mode (tight, loose, anticipatory, elastic, orbit)
        dead_zone: Screen space percentage before camera moves (x, y)
        look_ahead_frames: Frames to predict ahead for anticipatory mode
        smoothing: Smoothing factor (0=immediate, 1=very slow)
        max_speed: Maximum camera speed in meters per frame
        acceleration: Speed change per frame (for smooth ramping)
        offset: Offset from subject in world space (x, y, z)
        keep_distance: Preferred subject distance in meters
        keep_height: Preferred camera height in meters
        spring_stiffness: Spring stiffness for elastic mode
        spring_damping: Spring damping for elastic mode
        orbit_speed: Rotation speed for orbit mode (degrees per frame)
        orbit_radius: Fixed radius for orbit mode (meters)
    """
    mode: str = "loose"  # tight, loose, anticipatory, elastic, orbit
    dead_zone: Tuple[float, float] = (0.1, 0.1)  # Screen space % before moving
    look_ahead_frames: int = 10
    smoothing: float = 0.3  # 0=immediate, 1=very slow
    max_speed: float = 2.0  # meters per frame
    acceleration: float = 0.1  # speed change per frame
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Offset from subject
    keep_distance: float = 3.0  # Preferred subject distance
    keep_height: float = 1.6  # Preferred camera height

    # Elastic mode specific
    spring_stiffness: float = 10.0
    spring_damping: float = 0.5

    # Orbit mode specific
    orbit_speed: float = 0.5  # degrees per frame
    orbit_radius: Optional[float] = None  # None = use keep_distance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "dead_zone": list(self.dead_zone),
            "look_ahead_frames": self.look_ahead_frames,
            "smoothing": self.smoothing,
            "max_speed": self.max_speed,
            "acceleration": self.acceleration,
            "offset": list(self.offset),
            "keep_distance": self.keep_distance,
            "keep_height": self.keep_height,
            "spring_stiffness": self.spring_stiffness,
            "spring_damping": self.spring_damping,
            "orbit_speed": self.orbit_speed,
            "orbit_radius": self.orbit_radius,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FollowConfig:
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "loose"),
            dead_zone=tuple(data.get("dead_zone", (0.1, 0.1))),
            look_ahead_frames=data.get("look_ahead_frames", 10),
            smoothing=data.get("smoothing", 0.3),
            max_speed=data.get("max_speed", 2.0),
            acceleration=data.get("acceleration", 0.1),
            offset=tuple(data.get("offset", (0.0, 0.0, 0.0))),
            keep_distance=data.get("keep_distance", 3.0),
            keep_height=data.get("keep_height", 1.6),
            spring_stiffness=data.get("spring_stiffness", 10.0),
            spring_damping=data.get("spring_damping", 0.5),
            orbit_speed=data.get("orbit_speed", 0.5),
            orbit_radius=data.get("orbit_radius"),
        )


@dataclass
class FollowState:
    """
    Current state of follow rig.

    Tracks runtime state for smooth interpolation and debugging.

    Attributes:
        current_velocity: Camera velocity in meters per frame
        target_position: Current target position in world space
        is_in_dead_zone: Whether target is within dead zone
        frames_since_move: Frames since camera last moved
        current_position: Current camera position
        current_distance: Current distance to target
        current_height: Current height above target
        orbit_angle: Current orbit angle (for orbit mode)
        spring_velocity: Spring velocity (for elastic mode)
        last_target_velocity: Last known target velocity for prediction
    """
    current_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    is_in_dead_zone: bool = True
    frames_since_move: int = 0
    current_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    current_distance: float = 3.0
    current_height: float = 1.6
    orbit_angle: float = 0.0
    spring_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    last_target_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_velocity": list(self.current_velocity),
            "target_position": list(self.target_position),
            "is_in_dead_zone": self.is_in_dead_zone,
            "frames_since_move": self.frames_since_move,
            "current_position": list(self.current_position),
            "current_distance": self.current_distance,
            "current_height": self.current_height,
            "orbit_angle": self.orbit_angle,
            "spring_velocity": list(self.spring_velocity),
            "last_target_velocity": list(self.last_target_velocity),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FollowState:
        """Create from dictionary."""
        return cls(
            current_velocity=tuple(data.get("current_velocity", (0.0, 0.0, 0.0))),
            target_position=tuple(data.get("target_position", (0.0, 0.0, 0.0))),
            is_in_dead_zone=data.get("is_in_dead_zone", True),
            frames_since_move=data.get("frames_since_move", 0),
            current_position=tuple(data.get("current_position", (0.0, 0.0, 0.0))),
            current_distance=data.get("current_distance", 3.0),
            current_height=data.get("current_height", 1.6),
            orbit_angle=data.get("orbit_angle", 0.0),
            spring_velocity=tuple(data.get("spring_velocity", (0.0, 0.0, 0.0))),
            last_target_velocity=tuple(data.get("last_target_velocity", (0.0, 0.0, 0.0))),
        )


@dataclass
class FollowRig:
    """
    Camera rig that follows a subject.

    Combines configuration, state, and references for a complete
    follow camera setup.

    Attributes:
        name: Rig identifier
        camera: Camera object name in Blender
        target: Target object/marker name
        config: Follow configuration
        state: Runtime state
    """
    name: str = "follow_rig"
    camera: str = ""
    target: str = ""
    config: FollowConfig = field(default_factory=FollowConfig)
    state: FollowState = field(default_factory=FollowState)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "camera": self.camera,
            "target": self.target,
            "config": self.config.to_dict(),
            "state": self.state.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FollowRig:
        """Create from dictionary."""
        config_data = data.get("config", {})
        state_data = data.get("state", {})

        return cls(
            name=data.get("name", "follow_rig"),
            camera=data.get("camera", ""),
            target=data.get("target", ""),
            config=FollowConfig.from_dict(config_data) if config_data else FollowConfig(),
            state=FollowState.from_dict(state_data) if state_data else FollowState(),
        )


@dataclass
class DeadZoneResult:
    """
    Result of dead zone calculation.

    Attributes:
        screen_position: Target position in screen space (0-1)
        is_in_dead_zone: Whether target is within dead zone
        reaction_needed: Camera movement needed to recenter
        dead_zone_size: Current dead zone size (may be dynamic)
    """
    screen_position: Tuple[float, float] = (0.5, 0.5)
    is_in_dead_zone: bool = True
    reaction_needed: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    dead_zone_size: Tuple[float, float] = (0.1, 0.1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "screen_position": list(self.screen_position),
            "is_in_dead_zone": self.is_in_dead_zone,
            "reaction_needed": list(self.reaction_needed),
            "dead_zone_size": list(self.dead_zone_size),
        }


@dataclass
class FollowResult:
    """
    Result of follow calculation for a single frame.

    Attributes:
        position: Calculated camera position
        rotation: Calculated camera rotation (Euler degrees)
        distance: Distance to target
        height: Height above target
        mode_used: Follow mode that was applied
        is_smoothed: Whether smoothing was applied
        prediction_used: Whether look-ahead prediction was used
    """
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    distance: float = 3.0
    height: float = 1.6
    mode_used: str = "loose"
    is_smoothed: bool = False
    prediction_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "distance": self.distance,
            "height": self.height,
            "mode_used": self.mode_used,
            "is_smoothed": self.is_smoothed,
            "prediction_used": self.prediction_used,
        }
