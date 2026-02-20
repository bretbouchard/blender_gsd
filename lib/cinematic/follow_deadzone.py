"""
Follow Camera Dead Zone System

Implements dead zone calculations for stable camera framing:
- Screen position calculation
- Dead zone detection
- Reaction calculation
- Dynamic dead zones

Dead zones prevent micro-movements by ignoring small target
displacements until they exceed a threshold.

Part of Phase 6.3 - Follow Camera System
Requirements: REQ-FOLLOW-03
"""

from __future__ import annotations
import math
from typing import Tuple, Optional

from .follow_types import (
    FollowConfig,
    DeadZoneResult,
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

        def __len__(self) -> int:
            return len(self._values)

        def __add__(self, other: 'Vector') -> 'Vector':
            return Vector(tuple(a + b for a, b in zip(self._values, other._values)))

        def __sub__(self, other: 'Vector') -> 'Vector':
            return Vector(tuple(a - b for a, b in zip(self._values, other._values)))

        def __mul__(self, scalar: float) -> 'Vector':
            return Vector(tuple(a * scalar for a in self._values))

        def length(self) -> float:
            return math.sqrt(sum(a * a for a in self._values))

        def normalized(self) -> 'Vector':
            length = self.length()
            if length == 0:
                return Vector((0.0, 0.0, 0.0))
            return self / length

        def to_tuple(self) -> Tuple[float, ...]:
            return tuple(self._values)


def calculate_screen_position(
    camera_pos: Tuple[float, float, float],
    camera_rotation: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    focal_length: float = 50.0,
    sensor_width: float = 36.0,
) -> Tuple[float, float]:
    """
    Calculate where target appears in camera frame.

    Projects world position to normalized screen coordinates (0-1).
    Center of frame is (0.5, 0.5).

    Args:
        camera_pos: Camera world position
        camera_rotation: Camera Euler rotation (pitch, yaw, roll) degrees
        target_pos: Target world position
        focal_length: Camera focal length in mm
        sensor_width: Sensor width in mm

    Returns:
        Screen position (x, y) normalized 0-1
    """
    cam = Vector(camera_pos)
    target = Vector(target_pos)

    # Direction to target in world space
    world_dir = target - cam

    # Convert rotation to radians
    pitch = math.radians(camera_rotation[0])
    yaw = math.radians(camera_rotation[1])
    roll = math.radians(camera_rotation[2])

    # Build rotation matrix (simplified - assumes XYZ order)
    # First rotate around Z (yaw)
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)

    # Transform to camera space (simplified)
    # Camera looks down -Y in Blender
    cam_x = world_dir[0] * cos_y + world_dir[1] * sin_y
    cam_y = -world_dir[0] * sin_y + world_dir[1] * cos_y
    cam_z = world_dir[2]

    # Apply pitch
    cam_y_rot = cam_y * cos_p - cam_z * sin_p
    cam_z_rot = cam_y * sin_p + cam_z * cos_p

    # Check if target is behind camera
    if cam_y_rot >= 0:
        # Target is in front, calculate screen position
        # FOV based projection
        fov = 2 * math.atan(sensor_width / (2 * focal_length))
        half_fov = fov / 2

        # Project to screen
        if abs(cam_y_rot) > 0.001:
            screen_x = 0.5 + (cam_x / cam_y_rot) / (2 * math.tan(half_fov))
            screen_y = 0.5 + (cam_z_rot / cam_y_rot) / (2 * math.tan(half_fov))
        else:
            screen_x = 0.5
            screen_y = 0.5
    else:
        # Target behind camera - return center
        screen_x = 0.5
        screen_y = 0.5

    return (screen_x, screen_y)


def is_in_dead_zone(
    screen_pos: Tuple[float, float],
    dead_zone: Tuple[float, float],
) -> bool:
    """
    Check if target is within dead zone.

    Dead zone is centered at (0.5, 0.5) screen position.
    Size is percentage of screen width/height.

    Args:
        screen_pos: Screen position (0-1)
        dead_zone: Dead zone size as percentage (0-1)

    Returns:
        True if target is within dead zone
    """
    # Calculate distance from center
    center = (0.5, 0.5)
    dx = abs(screen_pos[0] - center[0])
    dy = abs(screen_pos[1] - center[1])

    # Check if within dead zone
    return dx <= dead_zone[0] / 2 and dy <= dead_zone[1] / 2


def calculate_dead_zone_reaction(
    screen_pos: Tuple[float, float],
    dead_zone: Tuple[float, float],
    strength: float = 1.0,
) -> Tuple[float, float, float]:
    """
    Calculate camera movement needed to recenter target.

    Returns a world-space offset that moves camera to recenter
    the target in the frame.

    Args:
        screen_pos: Current target screen position (0-1)
        dead_zone: Dead zone size (0-1)
        strength: Reaction strength (0-1, higher = faster response)

    Returns:
        World-space offset (x, y, z) to apply to camera
    """
    # Calculate offset from center
    center = (0.5, 0.5)
    dx = screen_pos[0] - center[0]
    dy = screen_pos[1] - center[1]

    # Only react if outside dead zone
    dead_x = dead_zone[0] / 2
    dead_y = dead_zone[1] / 2

    reaction_x = 0.0
    reaction_y = 0.0

    if abs(dx) > dead_x:
        # Calculate how far outside dead zone
        overflow = dx - (dead_x if dx > 0 else -dead_x)
        reaction_x = overflow * strength

    if abs(dy) > dead_y:
        overflow = dy - (dead_y if dy > 0 else -dead_y)
        reaction_y = overflow * strength

    # Convert screen offset to approximate world offset
    # This is a simplification - proper implementation would
    # account for distance and FOV
    world_x = reaction_x * 2.0  # Scale factor
    world_y = 0.0  # Y is forward/back
    world_z = reaction_y * 2.0  # Vertical reaction

    return (world_x, world_y, world_z)


def create_dynamic_dead_zone(
    velocity: Tuple[float, float, float],
    base_size: float = 0.1,
    max_size: float = 0.3,
    velocity_scale: float = 0.02,
) -> Tuple[float, float]:
    """
    Create dead zone that expands with speed.

    Faster movement = larger dead zone = less micro-movements.
    This creates smoother tracking during fast action while
    maintaining precision during slow movement.

    Args:
        velocity: Target velocity vector (m/frame)
        base_size: Minimum dead zone size (0-1)
        max_size: Maximum dead zone size (0-1)
        velocity_scale: How much velocity affects size

    Returns:
        Dynamic dead zone size (x, y)
    """
    # Calculate speed
    speed = math.sqrt(sum(v**2 for v in velocity))

    # Calculate expansion factor
    expansion = min(speed * velocity_scale, max_size - base_size)

    # Apply expansion
    size = base_size + expansion

    # Return uniform dead zone
    return (size, size)


def calculate_dead_zone_result(
    camera_pos: Tuple[float, float, float],
    camera_rotation: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    target_velocity: Tuple[float, float, float],
    config: FollowConfig,
    use_dynamic_dead_zone: bool = True,
) -> DeadZoneResult:
    """
    Calculate complete dead zone result.

    Combines screen position, dead zone detection, and reaction
    calculation into a single result.

    Args:
        camera_pos: Camera world position
        camera_rotation: Camera Euler rotation (degrees)
        target_pos: Target world position
        target_velocity: Target velocity vector
        config: Follow configuration
        use_dynamic_dead_zone: Whether to use dynamic dead zones

    Returns:
        DeadZoneResult with all calculated values
    """
    # Calculate screen position
    screen_pos = calculate_screen_position(
        camera_pos, camera_rotation, target_pos
    )

    # Get dead zone size (possibly dynamic)
    if use_dynamic_dead_zone:
        dead_zone = create_dynamic_dead_zone(
            target_velocity,
            base_size=config.dead_zone[0],
        )
    else:
        dead_zone = config.dead_zone

    # Check if in dead zone
    in_dead_zone = is_in_dead_zone(screen_pos, dead_zone)

    # Calculate reaction if needed
    if in_dead_zone:
        reaction = (0.0, 0.0, 0.0)
    else:
        reaction = calculate_dead_zone_reaction(
            screen_pos, dead_zone, strength=1.0 - config.smoothing
        )

    return DeadZoneResult(
        screen_position=screen_pos,
        is_in_dead_zone=in_dead_zone,
        reaction_needed=reaction,
        dead_zone_size=dead_zone,
    )


def get_dead_zone_center(dead_zone: Tuple[float, float]) -> Tuple[float, float]:
    """
    Get the center point of the dead zone.

    For standard dead zones, this is always (0.5, 0.5).

    Args:
        dead_zone: Dead zone size (x, y)

    Returns:
        Center point (always 0.5, 0.5 for standard dead zones)
    """
    return (0.5, 0.5)


def calculate_edge_distance(
    screen_pos: Tuple[float, float],
    dead_zone: Tuple[float, float],
) -> float:
    """
    Calculate distance from target to dead zone edge.

    Positive = outside dead zone
    Negative = inside dead zone
    Zero = on edge

    Args:
        screen_pos: Screen position (0-1)
        dead_zone: Dead zone size (0-1)

    Returns:
        Distance to edge (normalized)
    """
    center = (0.5, 0.5)
    dx = abs(screen_pos[0] - center[0]) - dead_zone[0] / 2
    dy = abs(screen_pos[1] - center[1]) - dead_zone[1] / 2

    # Return the larger of the two distances
    return max(dx, dy)
