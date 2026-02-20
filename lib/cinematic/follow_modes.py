"""
Follow Camera Mode Implementations

Implements five cinematic follow modes:
- tight: Immediate response, centered on subject
- loose: Smooth delay, natural lag feel
- anticipatory: Velocity prediction, moves before subject
- elastic: Spring physics, snaps back to center
- orbit: Circular path around subject

Part of Phase 6.3 - Follow Camera System
Requirements: REQ-FOLLOW-01, REQ-FOLLOW-05
"""

from __future__ import annotations
import math
from typing import Tuple, Optional

from .follow_types import (
    FollowConfig,
    FollowState,
    FollowResult,
)

# Blender API guard for testing outside Blender
try:
    import mathutils
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

    class Vector:
        """Fallback Vector class for testing outside Blender."""
        def __init__(self, values: Tuple[float, ...] = (0.0, 0.0, 0.0)):
            if isinstance(values, Vector):
                self._values = list(values._values)
            else:
                self._values = list(values)

        def __getitem__(self, index: int) -> float:
            return self._values[index]

        def __setitem__(self, index: int, value: float):
            self._values[index] = value

        def __len__(self) -> int:
            return len(self._values)

        def __add__(self, other: 'Vector') -> 'Vector':
            return Vector(tuple(a + b for a, b in zip(self._values, other._values)))

        def __sub__(self, other: 'Vector') -> 'Vector':
            return Vector(tuple(a - b for a, b in zip(self._values, other._values)))

        def __mul__(self, scalar: float) -> 'Vector':
            return Vector(tuple(a * scalar for a in self._values))

        def __rmul__(self, scalar: float) -> 'Vector':
            return self.__mul__(scalar)

        def __truediv__(self, scalar: float) -> 'Vector':
            return Vector(tuple(a / scalar for a in self._values))

        def __neg__(self) -> 'Vector':
            return Vector(tuple(-a for a in self._values))

        @property
        def x(self) -> float:
            return self._values[0]

        @x.setter
        def x(self, value: float):
            self._values[0] = value

        @property
        def y(self) -> float:
            return self._values[1]

        @y.setter
        def y(self, value: float):
            self._values[1] = value

        @property
        def z(self) -> float:
            return self._values[2]

        @z.setter
        def z(self, value: float):
            self._values[2] = value

        def length(self) -> float:
            return math.sqrt(sum(a * a for a in self._values))

        def normalized(self) -> 'Vector':
            length = self.length()
            if length == 0:
                return Vector((0.0, 0.0, 0.0))
            return self / length

        def copy(self) -> 'Vector':
            return Vector(tuple(self._values))

        def dot(self, other: 'Vector') -> float:
            return sum(a * b for a, b in zip(self._values, other._values))

        def cross(self, other: 'Vector') -> 'Vector':
            return Vector((
                self._values[1] * other._values[2] - self._values[2] * other._values[1],
                self._values[2] * other._values[0] - self._values[0] * other._values[2],
                self._values[0] * other._values[1] - self._values[1] * other._values[0],
            ))

        def lerp(self, other: 'Vector', factor: float) -> 'Vector':
            return self + (other - self) * factor

        def to_tuple(self) -> Tuple[float, ...]:
            return tuple(self._values)


def follow_tight(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    config: FollowConfig,
    delta_time: float = 1/24,
) -> Tuple[float, float, float]:
    """
    Tight following - camera stays centered on subject.

    Immediate response with minimal smoothing. Good for:
    - Action sequences
    - Precise subject tracking
    - When every movement matters

    Args:
        camera_pos: Current camera position
        target_pos: Target world position
        config: Follow configuration
        delta_time: Time since last update

    Returns:
        New camera position
    """
    cam = Vector(camera_pos)
    target = Vector(target_pos)

    # Calculate ideal position
    direction = target - cam
    distance = direction.length()

    if distance < 0.001:
        return camera_pos

    # Calculate position at keep_distance from target
    ideal_pos = target - direction.normalized() * config.keep_distance
    ideal_pos.z = target.z + config.keep_height

    # Apply offset
    offset = Vector(config.offset)
    ideal_pos = ideal_pos + offset

    # Minimal smoothing for tight mode
    smoothing = config.smoothing * 0.3  # Reduce smoothing for tighter response
    t = 1.0 - math.exp(-delta_time / max(smoothing, 0.01))

    new_pos = cam.lerp(ideal_pos, t)
    return tuple(new_pos._values)


def follow_loose(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    config: FollowConfig,
    state: Optional[FollowState] = None,
    delta_time: float = 1/24,
) -> Tuple[float, float, float]:
    """
    Loose following - camera lags behind subject movement.

    Smooth delay for natural feel. Good for:
    - Documentary style
    - Casual following
    - Relaxed pacing

    Uses exponential decay smoothing for natural lag.

    Args:
        camera_pos: Current camera position
        target_pos: Target world position
        config: Follow configuration
        state: Current follow state (optional)
        delta_time: Time since last update

    Returns:
        New camera position
    """
    cam = Vector(camera_pos)
    target = Vector(target_pos)

    # Calculate ideal position behind target
    ideal_pos = Vector((
        target.x,
        target.y - config.keep_distance,  # Behind target
        target.z + config.keep_height,
    ))

    # Apply offset
    offset = Vector(config.offset)
    ideal_pos = ideal_pos + offset

    # Apply exponential decay smoothing
    # Higher smoothing = slower movement
    t = 1.0 - math.exp(-delta_time / max(config.smoothing, 0.01))
    new_pos = cam.lerp(ideal_pos, t)

    # Apply max speed limit
    if state:
        velocity = new_pos - cam
        speed = velocity.length() / delta_time
        max_speed_per_frame = config.max_speed

        if speed > max_speed_per_frame:
            velocity = velocity.normalized() * max_speed_per_frame
            new_pos = cam + velocity

    return tuple(new_pos._values)


def follow_anticipatory(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    target_velocity: Tuple[float, float, float],
    config: FollowConfig,
    state: Optional[FollowState] = None,
    delta_time: float = 1/24,
) -> Tuple[float, float, float]:
    """
    Anticipatory - camera moves before subject arrives.

    Uses velocity prediction to position camera ahead of subject.
    Good for:
    - Sports broadcasting
    - Fast action
    - Predictable movement

    Args:
        camera_pos: Current camera position
        target_pos: Target world position
        target_velocity: Target velocity vector (m/frame)
        config: Follow configuration
        state: Current follow state (optional)
        delta_time: Time since last update

    Returns:
        New camera position
    """
    cam = Vector(camera_pos)
    target = Vector(target_pos)
    velocity = Vector(target_velocity)

    # Predict future position
    look_ahead = config.look_ahead_frames
    predicted_pos = target + velocity * look_ahead

    # Calculate ideal position based on predicted position
    direction = predicted_pos - cam
    distance = direction.length()

    if distance < 0.001:
        direction = Vector((0, -1, 0))
    else:
        direction = direction.normalized()

    # Position behind predicted position
    ideal_pos = predicted_pos - direction * config.keep_distance
    ideal_pos.z = predicted_pos.z + config.keep_height

    # Apply offset
    offset = Vector(config.offset)
    ideal_pos = ideal_pos + offset

    # Apply smoothing
    t = 1.0 - math.exp(-delta_time / max(config.smoothing, 0.01))
    new_pos = cam.lerp(ideal_pos, t)

    return tuple(new_pos._values)


def follow_elastic(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    config: FollowConfig,
    state: Optional[FollowState] = None,
    delta_time: float = 1/24,
) -> Tuple[float, float, float]:
    """
    Elastic - camera snaps back to center with spring physics.

    Spring-like behavior with configurable stiffness and damping.
    Good for:
    - Cinematic dolly feel
    - Smooth but responsive
    - Natural settling

    Uses Hooke's law: F = -k*x - c*v

    Args:
        camera_pos: Current camera position
        target_pos: Target world position
        config: Follow configuration
        state: Current follow state (for spring velocity)
        delta_time: Time since last update

    Returns:
        New camera position
    """
    cam = Vector(camera_pos)
    target = Vector(target_pos)

    # Calculate ideal position
    ideal_pos = Vector((
        target.x,
        target.y - config.keep_distance,
        target.z + config.keep_height,
    ))

    # Apply offset
    offset = Vector(config.offset)
    ideal_pos = ideal_pos + offset

    # Spring physics
    # Get or initialize spring velocity
    if state and state.spring_velocity:
        spring_vel = Vector(state.spring_velocity)
    else:
        spring_vel = Vector((0.0, 0.0, 0.0))

    # Calculate spring force
    displacement = cam - ideal_pos
    k = config.spring_stiffness  # Stiffness
    c = config.spring_damping    # Damping

    # F = -k*x - c*v (Hooke's law with damping)
    spring_force = -displacement * k - spring_vel * c

    # Update velocity
    spring_vel = spring_vel + spring_force * delta_time

    # Update position
    new_pos = cam + spring_vel * delta_time

    return tuple(new_pos._values)


def follow_orbit(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    config: FollowConfig,
    state: Optional[FollowState] = None,
    delta_time: float = 1/24,
) -> Tuple[float, float, float]:
    """
    Orbit - camera circles subject while following.

    Creates dynamic, cinematic camera movement. Good for:
    - Dramatic reveals
    - Hero shots
    - 360-degree views

    Args:
        camera_pos: Current camera position
        target_pos: Target world position
        config: Follow configuration
        state: Current follow state (for orbit angle)
        delta_time: Time since last update

    Returns:
        New camera position
    """
    target = Vector(target_pos)

    # Get current orbit angle
    if state:
        orbit_angle = state.orbit_angle
    else:
        # Calculate from current position
        cam = Vector(camera_pos)
        to_target = target - cam
        orbit_angle = math.degrees(math.atan2(to_target.x, to_target.y))

    # Update orbit angle
    orbit_angle += config.orbit_speed
    if orbit_angle >= 360:
        orbit_angle -= 360
    elif orbit_angle < 0:
        orbit_angle += 360

    # Use orbit radius or fall back to keep_distance
    radius = config.orbit_radius if config.orbit_radius else config.keep_distance

    # Calculate position on orbit circle
    orbit_rad = math.radians(orbit_angle)
    orbit_x = math.sin(orbit_rad) * radius
    orbit_y = math.cos(orbit_rad) * radius

    # Position camera
    new_pos = Vector((
        target.x + orbit_x,
        target.y + orbit_y,
        target.z + config.keep_height,
    ))

    # Apply offset
    offset = Vector(config.offset)
    new_pos = new_pos + offset

    return tuple(new_pos._values)


def calculate_follow(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    target_velocity: Tuple[float, float, float],
    config: FollowConfig,
    state: Optional[FollowState] = None,
    delta_time: float = 1/24,
) -> FollowResult:
    """
    Calculate follow position based on mode.

    Main dispatcher that routes to appropriate follow function.

    Args:
        camera_pos: Current camera position
        target_pos: Target world position
        target_velocity: Target velocity vector
        config: Follow configuration
        state: Current follow state
        delta_time: Time since last update

    Returns:
        FollowResult with position, rotation, and metadata
    """
    # Dispatch to appropriate mode
    mode = config.mode.lower()

    if mode == "tight":
        new_pos = follow_tight(camera_pos, target_pos, config, delta_time)
        prediction_used = False
    elif mode == "loose":
        new_pos = follow_loose(camera_pos, target_pos, config, state, delta_time)
        prediction_used = False
    elif mode == "anticipatory":
        new_pos = follow_anticipatory(
            camera_pos, target_pos, target_velocity, config, state, delta_time
        )
        prediction_used = True
    elif mode == "elastic":
        new_pos = follow_elastic(camera_pos, target_pos, config, state, delta_time)
        prediction_used = False
    elif mode == "orbit":
        new_pos = follow_orbit(camera_pos, target_pos, config, state, delta_time)
        prediction_used = False
    else:
        # Default to loose
        new_pos = follow_loose(camera_pos, target_pos, config, state, delta_time)
        prediction_used = False

    # Calculate distance and height
    cam = Vector(new_pos)
    target = Vector(target_pos)
    distance = (target - cam).length()
    height = cam.z - target.z

    # Calculate rotation (look at target)
    rotation = calculate_look_at_rotation(new_pos, target_pos)

    return FollowResult(
        position=new_pos,
        rotation=rotation,
        distance=distance,
        height=height,
        mode_used=mode,
        is_smoothed=config.smoothing > 0,
        prediction_used=prediction_used,
    )


def calculate_look_at_rotation(
    camera_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """
    Calculate Euler rotation to look at target.

    Args:
        camera_pos: Camera world position
        target_pos: Target world position

    Returns:
        Euler rotation (pitch, yaw, roll) in degrees
    """
    cam = Vector(camera_pos)
    target = Vector(target_pos)

    direction = target - cam
    length = direction.length()

    if length < 0.001:
        return (0.0, 0.0, 0.0)

    direction = direction.normalized()

    # Calculate yaw (rotation around Z)
    yaw = math.degrees(math.atan2(direction.x, direction.y))

    # Calculate pitch (rotation around X)
    horizontal_dist = math.sqrt(direction.x ** 2 + direction.y ** 2)
    pitch = math.degrees(math.atan2(-direction.z, horizontal_dist))

    # Roll is 0 for standard cameras
    roll = 0.0

    return (pitch, yaw, roll)


def smooth_position(
    current: Tuple[float, float, float],
    target: Tuple[float, float, float],
    smoothing: float,
    delta_time: float = 1/24,
) -> Tuple[float, float, float]:
    """
    Smoothly interpolate between current and target positions.

    Uses exponential decay for natural camera movement.

    Args:
        current: Current position
        target: Target position
        smoothing: Smoothing factor (0=instant, 1=very slow)
        delta_time: Time since last update

    Returns:
        Smoothed position
    """
    if smoothing <= 0:
        return target

    curr = Vector(current)
    tgt = Vector(target)

    t = 1.0 - math.exp(-delta_time / smoothing)
    result = curr.lerp(tgt, t)

    return tuple(result._values)


def smooth_angle(
    current: float,
    target: float,
    smoothing: float,
    delta_time: float = 1/24,
) -> float:
    """
    Smoothly interpolate between current and target angles.

    Handles angle wrapping (e.g., 350 to 10 degrees).

    Args:
        current: Current angle in degrees
        target: Target angle in degrees
        smoothing: Smoothing factor
        delta_time: Time since last update

    Returns:
        Smoothed angle in degrees
    """
    if smoothing <= 0:
        return target

    # Normalize angle difference to -180 to 180
    diff = target - current
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360

    t = 1.0 - math.exp(-delta_time / smoothing)
    return current + diff * t
