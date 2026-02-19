"""
Follow Camera Mode Implementations

Implements all follow camera modes:
- Side-Scroller: Locked plane following for 2.5D platformer
- Over-Shoulder: Third-person behind subject with offset
- Chase: Chase from behind/side with speed response
- Orbit-Follow: Orbiting while following subject
- Lead: Camera ahead of subject
- Aerial: Top-down bird's eye view
- Free Roam: Free camera with collision detection

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-52, 53, 54, 55
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any

from .types import (
    FollowMode,
    LockedPlane,
    FollowCameraConfig,
    CameraState,
    FollowTarget,
)

# Blender API guard for testing outside Blender
try:
    import mathutils
    from mathutils import Vector, Matrix, Euler
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Fallback Vector class for testing
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

        def rotate(self, euler: 'Euler'):
            """Rotate vector by Euler angles (simplified)."""
            # Simplified rotation - just for testing
            pass

        def to_tuple(self) -> Tuple[float, ...]:
            return tuple(self._values)

    class Euler:
        """Fallback Euler class for testing outside Blender."""
        def __init__(self, angles: Tuple[float, ...] = (0.0, 0.0, 0.0), order: str = 'XYZ'):
            self._angles = list(angles)
            self.order = order

        def to_matrix(self) -> 'Matrix':
            return Matrix()

    class Matrix:
        """Fallback Matrix class for testing outside Blender."""
        def __init__(self):
            self._data = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def calculate_ideal_position(
    target_position: Tuple[float, float, float],
    target_forward: Tuple[float, float, float],
    target_velocity: Tuple[float, float, float],
    config: FollowCameraConfig,
    current_yaw: float = 0.0,
    delta_time: float = 1/60,
) -> Tuple[Vector, float, float]:
    """
    Calculate ideal camera position based on follow mode.

    This is the main dispatcher that routes to mode-specific calculations.

    Args:
        target_position: Current target world position
        target_forward: Target's forward direction (normalized)
        target_velocity: Target's velocity vector
        config: Follow camera configuration
        current_yaw: Current camera yaw angle (for smoothing)
        delta_time: Time since last update

    Returns:
        Tuple of (ideal_position, ideal_yaw, ideal_pitch)
    """
    target_pos = Vector(target_position)
    target_fwd = Vector(target_forward)
    target_vel = Vector(target_velocity)

    # Calculate speed for speed-dependent modes
    speed = target_vel.length()

    if config.follow_mode == FollowMode.SIDE_SCROLLER:
        return _calc_side_scroller(target_pos, config, delta_time)
    elif config.follow_mode == FollowMode.OVER_SHOULDER:
        return _calc_over_shoulder(target_pos, target_fwd, config, current_yaw, delta_time)
    elif config.follow_mode == FollowMode.CHASE:
        return _calc_chase(target_pos, target_fwd, target_vel, config, current_yaw, delta_time)
    elif config.follow_mode == FollowMode.CHASE_SIDE:
        return _calc_chase_side(target_pos, target_fwd, target_vel, config, current_yaw, delta_time)
    elif config.follow_mode == FollowMode.ORBIT_FOLLOW:
        return _calc_orbit_follow(target_pos, config, current_yaw, delta_time)
    elif config.follow_mode == FollowMode.LEAD:
        return _calc_lead(target_pos, target_fwd, config, current_yaw, delta_time)
    elif config.follow_mode == FollowMode.AERIAL:
        return _calc_aerial(target_pos, config, delta_time)
    elif config.follow_mode == FollowMode.FREE_ROAM:
        return _calc_free_roam(target_pos, config, current_yaw, delta_time)
    else:
        # Default to over-shoulder
        return _calc_over_shoulder(target_pos, target_fwd, config, current_yaw, delta_time)


# =============================================================================
# SIDE-SCROLLER MODE (blender_gsd-52)
# =============================================================================

def _calc_side_scroller(
    target_pos: Vector,
    config: FollowCameraConfig,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate side-scroller camera position.

    Locked plane following for 2.5D platformer view.
    Camera moves freely on two axes while staying fixed on the third.

    Locked Plane Options:
    - XZ: Y-axis locked (traditional side-scrolling)
    - XY: Z-axis locked (top-down platformer)
    - YZ: X-axis locked (front-facing platformer)

    Args:
        target_pos: Target world position
        config: Camera configuration
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Start with target position
    cam_pos = target_pos.copy()

    # Apply locked plane constraint
    if config.locked_plane == LockedPlane.XZ:
        # Y-axis locked (traditional side-scrolling)
        # Camera is to the side, looking at the action
        cam_pos.x = target_pos.x
        cam_pos.y = config.locked_axis_value  # Fixed Y position
        cam_pos.z = target_pos.z + config.ideal_height

        # Look perpendicular to locked axis
        yaw = 90.0 if config.locked_axis_value > target_pos.y else -90.0
        pitch = 0.0

    elif config.locked_plane == LockedPlane.XY:
        # Z-axis locked (top-down platformer)
        cam_pos.x = target_pos.x
        cam_pos.y = target_pos.y
        cam_pos.z = config.locked_axis_value  # Fixed Z height

        # Look straight down
        yaw = 0.0
        pitch = -90.0

    else:  # LockedPlane.YZ
        # X-axis locked (front-facing platformer)
        cam_pos.x = config.locked_axis_value  # Fixed X position
        cam_pos.y = target_pos.y
        cam_pos.z = target_pos.z + config.ideal_height

        # Look perpendicular to locked axis
        yaw = 0.0 if config.locked_axis_value > target_pos.x else 180.0
        pitch = 0.0

    # Apply distance offset (for modes that use it)
    if config.locked_plane != LockedPlane.XY:
        # Add some distance for non-top-down views
        pass  # Position is already calculated above

    return cam_pos, yaw, pitch


def _apply_axis_lock(
    position: Vector,
    locked_plane: LockedPlane,
    locked_value: float,
) -> Vector:
    """
    Apply axis locking to a position.

    Args:
        position: Position to lock
        locked_plane: Which plane to lock to
        locked_value: Value for the locked axis

    Returns:
        Position with locked axis applied
    """
    result = position.copy()

    if locked_plane == LockedPlane.XZ:
        result.y = locked_value
    elif locked_plane == LockedPlane.XY:
        result.z = locked_value
    else:  # YZ
        result.x = locked_value

    return result


# =============================================================================
# OVER-SHOULDER MODE (blender_gsd-53)
# =============================================================================

def _calc_over_shoulder(
    target_pos: Vector,
    target_fwd: Vector,
    config: FollowCameraConfig,
    current_yaw: float,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate over-shoulder camera position.

    Third-person behind subject with horizontal offset for shoulder framing.
    Camera follows behind and above the subject with smooth interpolation.

    Args:
        target_pos: Target world position
        target_fwd: Target forward direction (normalized)
        config: Camera configuration
        current_yaw: Current camera yaw for smoothing
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Calculate camera position behind target
    # Offset to the side based on shoulder_offset
    # Negative = left shoulder, Positive = right shoulder

    # Get right vector for shoulder offset
    up = Vector((0.0, 0.0, 1.0))
    right = up.cross(target_fwd).normalized()

    # Calculate base position behind target
    back_offset = -target_fwd * config.ideal_distance
    height_offset = up * config.ideal_height
    shoulder_offset = right * config.shoulder_offset

    cam_pos = target_pos + back_offset + height_offset + shoulder_offset

    # Calculate look direction (yaw and pitch)
    look_dir = (target_pos - cam_pos).normalized()

    # Calculate yaw (horizontal rotation)
    yaw = math.degrees(math.atan2(look_dir.x, look_dir.y))

    # Calculate pitch (vertical rotation)
    horizontal_dist = math.sqrt(look_dir.x ** 2 + look_dir.y ** 2)
    pitch = math.degrees(math.atan2(look_dir.z, horizontal_dist))

    return cam_pos, yaw, pitch


# =============================================================================
# CHASE MODES (blender_gsd-54)
# =============================================================================

def _calc_chase(
    target_pos: Vector,
    target_fwd: Vector,
    target_vel: Vector,
    config: FollowCameraConfig,
    current_yaw: float,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate chase camera position from behind.

    Camera chases from behind with speed-based distance adjustment.
    Faster movement = camera pulls back further.

    Args:
        target_pos: Target world position
        target_fwd: Target forward direction
        target_vel: Target velocity for speed calculation
        config: Camera configuration
        current_yaw: Current camera yaw
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Calculate speed-based distance
    speed = target_vel.length()
    speed_factor = min(speed * config.speed_distance_factor, config.max_speed_distance)
    effective_distance = config.ideal_distance + speed_factor

    # Clamp to min/max
    effective_distance = max(config.min_distance,
                            min(effective_distance, config.max_distance))

    up = Vector((0.0, 0.0, 1.0))

    # Position behind target at speed-adjusted distance
    back_offset = -target_fwd * effective_distance
    height_offset = up * config.ideal_height

    cam_pos = target_pos + back_offset + height_offset

    # Calculate look direction
    look_dir = (target_pos - cam_pos).normalized()

    # Calculate yaw and pitch
    yaw = math.degrees(math.atan2(look_dir.x, look_dir.y))
    horizontal_dist = math.sqrt(look_dir.x ** 2 + look_dir.y ** 2)
    pitch = math.degrees(math.atan2(look_dir.z, horizontal_dist))

    return cam_pos, yaw, pitch


def _calc_chase_side(
    target_pos: Vector,
    target_fwd: Vector,
    target_vel: Vector,
    config: FollowCameraConfig,
    current_yaw: float,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate chase-side camera position.

    Camera chases from the side, commonly used for racing games
    and vehicle sequences.

    Args:
        target_pos: Target world position
        target_fwd: Target forward direction
        target_vel: Target velocity for speed calculation
        config: Camera configuration
        current_yaw: Current camera yaw
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Calculate speed-based distance
    speed = target_vel.length()
    speed_factor = min(speed * config.speed_distance_factor, config.max_speed_distance)
    effective_distance = config.ideal_distance + speed_factor

    up = Vector((0.0, 0.0, 1.0))
    right = up.cross(target_fwd).normalized()

    # Position to the side of target
    side_offset = right * config.shoulder_offset  # Uses shoulder_offset as side distance
    back_offset = -target_fwd * effective_distance * 0.5  # Slightly behind
    height_offset = up * config.ideal_height

    cam_pos = target_pos + side_offset + back_offset + height_offset

    # Calculate look direction
    look_dir = (target_pos - cam_pos).normalized()

    # Calculate yaw and pitch
    yaw = math.degrees(math.atan2(look_dir.x, look_dir.y))
    horizontal_dist = math.sqrt(look_dir.x ** 2 + look_dir.y ** 2)
    pitch = math.degrees(math.atan2(look_dir.z, horizontal_dist))

    return cam_pos, yaw, pitch


# =============================================================================
# ADVANCED MODES (blender_gsd-55)
# =============================================================================

def _calc_orbit_follow(
    target_pos: Vector,
    config: FollowCameraConfig,
    current_yaw: float,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate orbit-follow camera position.

    Camera orbits around the subject while following.
    Creates dynamic, cinematic camera movement.

    Args:
        target_pos: Target world position
        config: Camera configuration
        current_yaw: Current camera yaw (used for orbit angle)
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Update orbit angle based on orbit speed
    orbit_angle = current_yaw + config.orbit_speed * delta_time
    orbit_rad = math.radians(orbit_angle)

    # Calculate position on orbit circle
    up = Vector((0.0, 0.0, 1.0))

    # Orbit position relative to target
    orbit_x = math.sin(orbit_rad) * config.ideal_distance
    orbit_y = math.cos(orbit_rad) * config.ideal_distance

    cam_pos = Vector((
        target_pos.x + orbit_x,
        target_pos.y + orbit_y,
        target_pos.z + config.ideal_height,
    ))

    # Look at target
    look_dir = (target_pos - cam_pos).normalized()

    # Calculate yaw and pitch
    yaw = math.degrees(math.atan2(look_dir.x, look_dir.y))
    horizontal_dist = math.sqrt(look_dir.x ** 2 + look_dir.y ** 2)
    pitch = math.degrees(math.atan2(look_dir.z, horizontal_dist))

    return cam_pos, yaw, pitch


def _calc_lead(
    target_pos: Vector,
    target_fwd: Vector,
    config: FollowCameraConfig,
    current_yaw: float,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate lead camera position.

    Camera is positioned ahead of the subject, looking back.
    Great for action preview and dramatic shots.

    Args:
        target_pos: Target world position
        target_fwd: Target forward direction
        config: Camera configuration
        current_yaw: Current camera yaw
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    up = Vector((0.0, 0.0, 1.0))

    # Position ahead of target
    forward_offset = target_fwd * config.lead_distance
    height_offset = up * config.ideal_height

    cam_pos = target_pos + forward_offset + height_offset

    # Look back at target
    look_dir = (target_pos - cam_pos).normalized()

    # Calculate yaw and pitch
    yaw = math.degrees(math.atan2(look_dir.x, look_dir.y))
    horizontal_dist = math.sqrt(look_dir.x ** 2 + look_dir.y ** 2)
    pitch = math.degrees(math.atan2(look_dir.z, horizontal_dist))

    return cam_pos, yaw, pitch


def _calc_aerial(
    target_pos: Vector,
    config: FollowCameraConfig,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate aerial camera position.

    Top-down bird's eye view for strategic overview
    or dramatic establishing shots.

    Args:
        target_pos: Target world position
        config: Camera configuration
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Position directly above target
    cam_pos = Vector((
        target_pos.x,
        target_pos.y,
        target_pos.z + config.ideal_height,
    ))

    # Look straight down
    yaw = 0.0
    pitch = -89.0  # Not quite -90 to avoid gimbal lock issues

    return cam_pos, yaw, pitch


def _calc_free_roam(
    target_pos: Vector,
    config: FollowCameraConfig,
    current_yaw: float,
    delta_time: float,
) -> Tuple[Vector, float, float]:
    """
    Calculate free roam camera position.

    Free camera with collision detection.
    Camera can move anywhere but avoids obstacles.

    Note: Actual collision handling is done by the collision module.
    This calculates the ideal position; collision detection adjusts it.

    Args:
        target_pos: Target world position
        config: Camera configuration
        current_yaw: Current camera yaw
        delta_time: Time since last update

    Returns:
        Tuple of (position, yaw, pitch)
    """
    # Default to orbit-style following but with more freedom
    # Actual position will be adjusted by collision detection
    up = Vector((0.0, 0.0, 1.0))

    # Calculate position using current yaw
    yaw_rad = math.radians(current_yaw)

    orbit_x = math.sin(yaw_rad) * config.ideal_distance
    orbit_y = math.cos(yaw_rad) * config.ideal_distance

    cam_pos = Vector((
        target_pos.x + orbit_x,
        target_pos.y + orbit_y,
        target_pos.z + config.ideal_height,
    ))

    # Look at target
    look_dir = (target_pos - cam_pos).normalized()

    # Calculate yaw and pitch
    yaw = current_yaw
    horizontal_dist = math.sqrt(look_dir.x ** 2 + look_dir.y ** 2)
    pitch = math.degrees(math.atan2(look_dir.z, horizontal_dist))

    return cam_pos, yaw, pitch


# =============================================================================
# SMOOTHING UTILITIES
# =============================================================================

def smooth_position(
    current: Vector,
    target: Vector,
    smoothing: float,
    delta_time: float,
) -> Vector:
    """
    Smoothly interpolate between current and target positions.

    Uses exponential decay for natural camera movement.

    Args:
        current: Current camera position
        target: Target position
        smoothing: Smoothing factor (0 = instant, 1 = very slow)
        delta_time: Time since last update

    Returns:
        Smoothed position
    """
    if smoothing <= 0:
        return target.copy()

    # Exponential decay smoothing
    # Higher smoothing = slower movement
    t = 1.0 - math.exp(-delta_time / smoothing)
    return current.lerp(target, t)


def smooth_angle(
    current: float,
    target: float,
    smoothing: float,
    delta_time: float,
) -> float:
    """
    Smoothly interpolate between current and target angles.

    Handles angle wrapping (e.g., 350 -> 10 degrees).

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

    # Apply smoothing
    t = 1.0 - math.exp(-delta_time / smoothing)
    return current + diff * t


def calculate_camera_rotation(
    camera_pos: Vector,
    target_pos: Vector,
) -> Tuple[float, float, float]:
    """
    Calculate Euler rotation to look at target.

    Args:
        camera_pos: Camera world position
        target_pos: Target world position

    Returns:
        Tuple of (yaw, pitch, roll) in degrees
    """
    direction = target_pos - camera_pos
    direction_normalized = direction.normalized()

    # Calculate yaw (rotation around Z axis)
    yaw = math.degrees(math.atan2(direction_normalized.x, direction_normalized.y))

    # Calculate pitch (rotation around X axis)
    horizontal_dist = math.sqrt(
        direction_normalized.x ** 2 + direction_normalized.y ** 2
    )
    pitch = math.degrees(math.atan2(direction_normalized.z, horizontal_dist))

    # Roll is typically 0 for follow cameras
    roll = 0.0

    return yaw, pitch, roll


def get_target_forward_direction(
    target_velocity: Vector,
    default_forward: Tuple[float, float, float] = (0.0, 1.0, 0.0),
) -> Vector:
    """
    Get target's forward direction based on velocity.

    If target is stationary, returns default forward direction.

    Args:
        target_velocity: Target's velocity vector
        default_forward: Default forward when stationary

    Returns:
        Normalized forward direction vector
    """
    speed = target_velocity.length()

    if speed > 0.1:  # Moving
        return target_velocity.normalized()
    else:
        return Vector(default_forward).normalized()
