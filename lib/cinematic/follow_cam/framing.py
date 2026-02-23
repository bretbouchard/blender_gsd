"""
Follow Camera Intelligent Framing

Implements intelligent framing rules:
- Rule of thirds positioning
- Headroom and look room
- Dead zone for subtle movements
- Dynamic framing
- Multi-subject framing

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-62
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass

from .types import (
    FollowCameraConfig,
    FollowTarget,
)

# Blender API guard for testing outside Blender
try:
    import mathutils
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    from .follow_modes import Vector


@dataclass
class FramingResult:
    """
    Result of framing calculation.

    Attributes:
        target_offset: Offset to apply to camera target for framing
        horizontal_shift: Horizontal shift for rule of thirds
        vertical_shift: Vertical shift for headroom
        is_within_dead_zone: Whether target is in dead zone
        framing_quality: Quality of current framing (0-1)
    """
    target_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    horizontal_shift: float = 0.0
    vertical_shift: float = 0.0
    is_within_dead_zone: bool = False
    framing_quality: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_offset": list(self.target_offset),
            "horizontal_shift": self.horizontal_shift,
            "vertical_shift": self.vertical_shift,
            "is_within_dead_zone": self.is_within_dead_zone,
            "framing_quality": self.framing_quality,
        }


# Rule of thirds grid positions (0-1 normalized)
RULE_OF_THIRDS_POINTS = {
    "left_third": 0.33,
    "right_third": 0.67,
    "top_third": 0.67,
    "bottom_third": 0.33,
    "center": 0.5,
}


def calculate_framing_offset(
    target_position: Tuple[float, float, float],
    camera_position: Tuple[float, float, float],
    camera_rotation: Tuple[float, float, float],
    config: FollowCameraConfig,
    screen_velocity: Optional[Tuple[float, float]] = None,
) -> FramingResult:
    """
    Calculate framing offset for camera.

    Applies rule of thirds, headroom, and dead zone rules.

    Args:
        target_position: Target world position
        camera_position: Camera world position
        camera_rotation: Camera Euler rotation (degrees)
        config: Camera configuration
        screen_velocity: Optional target velocity in screen space

    Returns:
        FramingResult with offset and framing metadata
    """
    target_pos = Vector(target_position)
    cam_pos = Vector(camera_position)

    # Calculate current direction to target
    to_target = target_pos - cam_pos
    distance = to_target.length()

    if distance < 0.01:
        return FramingResult()

    # Apply rule of thirds offset
    horizontal_shift, vertical_shift = _calculate_rule_of_thirds_offset(
        camera_rotation, config
    )

    # Apply headroom
    vertical_shift += _calculate_headroom_offset(config)

    # Calculate offset in world space
    # This is a simplified version - full implementation would project
    # through camera frustum
    offset = Vector((horizontal_shift, 0.0, vertical_shift))

    # Check dead zone
    is_in_dead_zone = False
    if screen_velocity:
        vel_magnitude = math.sqrt(screen_velocity[0]**2 + screen_velocity[1]**2)
        is_in_dead_zone = vel_magnitude < config.dead_zone_radius

    # Calculate framing quality
    quality = _calculate_framing_quality(horizontal_shift, vertical_shift, is_in_dead_zone)

    return FramingResult(
        target_offset=tuple(offset._values),
        horizontal_shift=horizontal_shift,
        vertical_shift=vertical_shift,
        is_within_dead_zone=is_in_dead_zone,
        framing_quality=quality,
    )


def _calculate_rule_of_thirds_offset(
    camera_rotation: Tuple[float, float, float],
    config: FollowCameraConfig,
) -> Tuple[float, float]:
    """
    Calculate rule of thirds offset.

    Positions subject at intersection of thirds lines.
    """
    # Use config offset
    ro_thirds = config.rule_of_thirds_offset

    # Scale to reasonable world units
    horizontal = ro_thirds[0] * 2.0  # meters
    vertical = ro_thirds[1] * 1.0   # meters

    return horizontal, vertical


def _calculate_headroom_offset(config: FollowCameraConfig) -> float:
    """
    Calculate headroom offset.

    Ensures subject has appropriate headroom in frame.
    """
    # Headroom is typically 10-20% of frame height
    # Config headroom of 1.1 means 10% extra
    return (config.headroom - 1.0) * -0.5  # Negative to shift camera up


def _calculate_framing_quality(
    horizontal_shift: float,
    vertical_shift: float,
    is_in_dead_zone: bool,
) -> float:
    """
    Calculate quality of current framing.

    Higher quality = better composition.
    """
    # Penalize large offsets (centered is often best)
    h_penalty = min(abs(horizontal_shift) / 2.0, 1.0)
    v_penalty = min(abs(vertical_shift) / 1.0, 1.0)

    # Base quality
    quality = 1.0 - (h_penalty + v_penalty) / 2.0

    # Bonus for being in dead zone (stable framing)
    if is_in_dead_zone:
        quality = min(quality + 0.1, 1.0)

    return max(0.0, min(1.0, quality))


def calculate_look_room(
    facing_direction: Tuple[float, float, float],
    camera_direction: Tuple[float, float, float],
) -> float:
    """
    Calculate look room offset.

    Subjects should have more space in the direction they're facing.

    Args:
        facing_direction: Direction subject is facing
        camera_direction: Direction camera is looking

    Returns:
        Look room offset (positive = more room in facing direction)
    """
    facing = Vector(facing_direction).normalized()
    cam_dir = Vector(camera_direction).normalized()

    # Dot product gives facing relative to camera
    dot = facing.dot(cam_dir)

    # Positive dot means facing away, negative means facing camera
    # We want more room in facing direction
    return dot * 0.5


def calculate_multi_subject_framing(
    subject_positions: List[Tuple[float, float, float]],
    weights: Optional[List[float]] = None,
) -> Tuple[Tuple[float, float, float], float]:
    """
    Calculate framing for multiple subjects.

    Finds the center point and required distance to frame all subjects.

    Args:
        subject_positions: List of subject world positions
        weights: Optional weights for each subject

    Returns:
        Tuple of (center_position, required_distance)
    """
    if not subject_positions:
        return (0.0, 0.0, 0.0), 5.0

    positions = [Vector(p) for p in subject_positions]

    if weights:
        # Weighted average
        total_weight = sum(weights)
        weighted_sum = Vector((0.0, 0.0, 0.0))
        for p, w in zip(positions, weights):
            weighted_sum = weighted_sum + (p * w)
        center = weighted_sum / total_weight
    else:
        # Simple average
        center = sum(positions, Vector((0.0, 0.0, 0.0))) / len(positions)

    # Calculate required distance based on spread
    max_distance = 0.0
    for pos in positions:
        dist = (pos - center).length()
        max_distance = max(max_distance, dist)

    # Add margin
    required_distance = max_distance * 2.5

    return tuple(center._values), required_distance


def apply_dead_zone(
    current_offset: Tuple[float, float],
    target_offset: Tuple[float, float],
    dead_zone_radius: float,
) -> Tuple[float, float]:
    """
    Apply dead zone to offset changes.

    Small changes within dead zone radius are ignored for stability.

    Args:
        current_offset: Current offset
        target_offset: Target offset
        dead_zone_radius: Dead zone radius

    Returns:
        Offset to apply (unchanged if within dead zone)
    """
    current = Vector((current_offset[0], current_offset[1], 0.0))
    target = Vector((target_offset[0], target_offset[1], 0.0))

    diff = target - current
    distance = diff.length()

    if distance < dead_zone_radius:
        # Within dead zone - don't change
        return current_offset

    # Outside dead zone - apply smoothly
    return target_offset


# =============================================================================
# COMPOSITION GUIDES
# =============================================================================

def get_rule_of_thirds_lines() -> Dict[str, float]:
    """
    Get rule of thirds line positions.

    Returns:
        Dictionary with line positions (0-1 normalized)
    """
    return RULE_OF_THIRDS_POINTS.copy()


def calculate_golden_ratio_offset() -> Tuple[float, float]:
    """
    Calculate golden ratio framing offset.

    Alternative to rule of thirds using golden ratio.
    """
    golden_ratio = (1 + math.sqrt(5)) / 2  # ~1.618
    golden_point = 1 / golden_ratio  # ~0.618

    return golden_point - 0.5, golden_point - 0.5


def calculate_center_weighted_framing(
    primary_position: Tuple[float, float, float],
    secondary_positions: List[Tuple[float, float, float]],
    primary_weight: float = 0.7,
) -> Tuple[float, float, float]:
    """
    Calculate center-weighted framing.

    Primarily frames main subject while considering others.

    Args:
        primary_position: Main subject position
        secondary_positions: Other subject positions
        primary_weight: Weight given to primary (0-1)

    Returns:
        Weighted center position
    """
    primary = Vector(primary_position)
    secondary_weight = (1.0 - primary_weight) / max(len(secondary_positions), 1)

    center = primary * primary_weight

    for pos in secondary_positions:
        center += Vector(pos) * secondary_weight

    return tuple(center._values)


# =============================================================================
# DYNAMIC FRAMING (Phase 8.4)
# =============================================================================

def calculate_dynamic_framing(
    target_velocity: Tuple[float, float, float],
    current_framing: FramingResult,
    speed_threshold: float = 2.0,
    anticipation_factor: float = 0.3,
) -> FramingResult:
    """
    Calculate dynamic framing based on target speed.

    Adjusts framing to anticipate movement direction and
    provide more lead room for fast-moving subjects.

    Args:
        target_velocity: Current target velocity (m/s)
        current_framing: Current framing result
        speed_threshold: Speed above which dynamic framing activates
        anticipation_factor: How much to anticipate movement (0-1)

    Returns:
        Adjusted FramingResult with dynamic framing applied
    """
    velocity = Vector(target_velocity)
    speed = velocity.length()

    if speed < speed_threshold:
        # Below threshold - use standard framing
        return current_framing

    # Calculate dynamic offset based on velocity direction
    if speed > 0.01:
        velocity_dir = velocity / speed
    else:
        velocity_dir = Vector((0, 1, 0))

    # Scale anticipation by speed
    anticipation_scale = min((speed - speed_threshold) / speed_threshold, 1.0)
    anticipation_scale *= anticipation_factor

    # Shift framing in direction of movement
    dynamic_offset = velocity_dir * anticipation_scale

    # Apply to framing result
    new_offset = (
        current_framing.target_offset[0] + dynamic_offset.x,
        current_framing.target_offset[1] + dynamic_offset.y,
        current_framing.target_offset[2] + dynamic_offset.z,
    )

    return FramingResult(
        target_offset=new_offset,
        horizontal_shift=current_framing.horizontal_shift + dynamic_offset.x,
        vertical_shift=current_framing.vertical_shift + dynamic_offset.z,
        is_within_dead_zone=current_framing.is_within_dead_zone,
        framing_quality=current_framing.framing_quality,
    )


def calculate_action_framing(
    is_action: bool,
    action_intensity: float,
    base_framing: FramingResult,
    zoom_out_factor: float = 1.5,
) -> FramingResult:
    """
    Calculate framing for action sequences.

    During action, widen the framing to capture movement.

    Args:
        is_action: Whether action is occurring
        action_intensity: Intensity of action (0-1)
        base_framing: Base framing to modify
        zoom_out_factor: How much to zoom out during action

    Returns:
        Adjusted FramingResult for action
    """
    if not is_action or action_intensity <= 0:
        return base_framing

    # Reduce offset to center subject more during action
    centering = 1.0 - (action_intensity * 0.5)

    new_offset = (
        base_framing.target_offset[0] * centering,
        base_framing.target_offset[1] * centering,
        base_framing.target_offset[2] * centering,
    )

    # Lower quality during action is acceptable
    quality_adjust = base_framing.framing_quality * (1.0 - action_intensity * 0.2)

    return FramingResult(
        target_offset=new_offset,
        horizontal_shift=base_framing.horizontal_shift * centering,
        vertical_shift=base_framing.vertical_shift * centering,
        is_within_dead_zone=base_framing.is_within_dead_zone,
        framing_quality=quality_adjust,
    )


def calculate_speed_based_distance(
    base_distance: float,
    target_speed: float,
    min_distance: float = 1.0,
    max_distance: float = 10.0,
    speed_scale: float = 0.5,
) -> float:
    """
    Calculate ideal distance based on target speed.

    Faster targets need more distance to stay in frame.

    Args:
        base_distance: Default distance
        target_speed: Current target speed (m/s)
        min_distance: Minimum allowed distance
        max_distance: Maximum allowed distance
        speed_scale: How much speed affects distance

    Returns:
        Calculated ideal distance
    """
    # Add distance proportional to speed
    speed_adjustment = target_speed * speed_scale
    ideal_distance = base_distance + speed_adjustment

    # Clamp to valid range
    return max(min_distance, min(max_distance, ideal_distance))
