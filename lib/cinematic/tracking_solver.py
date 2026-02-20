"""
Tracking Solver Module

Implements motion calculation for object tracking markers including:
- Position solving (objects, bones, empties)
- Velocity calculation
- Acceleration calculation
- Predictive interpolation for smooth following
- Temporal smoothing algorithms

Used by follow-focus automation and camera tracking systems.
"""

from __future__ import annotations
from typing import Dict, Tuple, Optional, List, Any
import math

from .tracking_types import TrackingMarker, TrackingData, TrackingConfig

# Check if Blender is available
try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    # Create mock types for testing without Blender
    Vector = None
    Matrix = None


def solve_marker_position(
    marker: TrackingMarker,
    frame: int
) -> Optional[Tuple[float, float, float]]:
    """
    Calculate marker world position at frame.

    Handles objects, bones, and empties with local offset.

    Args:
        marker: Tracking marker configuration
        frame: Frame number to solve

    Returns:
        World position (x, y, z) or None if not solvable
    """
    if not BLENDER_AVAILABLE:
        # Return placeholder for testing
        return (0.0, 0.0, 0.0)

    if not marker.enabled:
        return None

    if frame < marker.frame_start or frame > marker.frame_end:
        return None

    # Get object
    obj = bpy.data.objects.get(marker.object_ref)
    if obj is None:
        return None

    # Set scene frame
    scene = bpy.context.scene
    scene.frame_set(frame)

    # Get world position
    if marker.bone_name:
        # Bone tracking
        if obj.type != 'ARMATURE':
            return None
        bone = obj.data.bones.get(marker.bone_name)
        if bone is None:
            return None
        pose_bone = obj.pose.bones.get(marker.bone_name)
        if pose_bone is None:
            return None

        # Get bone head position in world space
        bone_matrix = obj.matrix_world @ pose_bone.matrix
        world_pos = bone_matrix.translation
    else:
        # Object tracking
        world_pos = obj.matrix_world.translation.copy()

    # Apply offset in world space
    offset_vec = Vector(marker.offset)
    # Transform offset by object's rotation
    world_offset = obj.matrix_world.to_3x3() @ offset_vec
    final_pos = world_pos + world_offset

    return (final_pos.x, final_pos.y, final_pos.z)


def solve_tracking_data(config: TrackingConfig) -> Dict[str, TrackingData]:
    """
    Solve all markers for frame range.

    Calculates positions, velocities, and accelerations for each marker
    over the frame range defined by the markers.

    Args:
        config: Complete tracking configuration

    Returns:
        Dictionary of marker_name -> TrackingData
    """
    results: Dict[str, TrackingData] = {}

    for marker in config.markers:
        if not marker.enabled:
            continue

        data = TrackingData(marker_name=marker.name)

        # Solve positions for each frame
        positions: Dict[int, Tuple[float, float, float]] = {}
        for frame in range(marker.frame_start, marker.frame_end + 1):
            pos = solve_marker_position(marker, frame)
            if pos is not None:
                positions[frame] = pos

        data.positions = positions

        # Calculate velocities
        data.velocities = calculate_velocities(positions)

        # Calculate accelerations
        data.accelerations = calculate_accelerations(data.velocities)

        results[marker.name] = data

    return results


def calculate_velocities(
    positions: Dict[int, Tuple[float, float, float]]
) -> Dict[int, Tuple[float, float, float]]:
    """
    Calculate velocity vectors from positions.

    Uses central difference for interior frames, forward/backward
    difference for endpoints.

    Args:
        positions: Frame -> position mapping

    Returns:
        Frame -> velocity mapping
    """
    if len(positions) < 2:
        return {}

    velocities: Dict[int, Tuple[float, float, float]] = {}
    frames = sorted(positions.keys())

    for i, frame in enumerate(frames):
        if i == 0:
            # Forward difference for first frame
            next_frame = frames[i + 1]
            dt = next_frame - frame
            if dt > 0:
                pos1 = positions[frame]
                pos2 = positions[next_frame]
                velocities[frame] = (
                    (pos2[0] - pos1[0]) / dt,
                    (pos2[1] - pos1[1]) / dt,
                    (pos2[2] - pos1[2]) / dt,
                )
        elif i == len(frames) - 1:
            # Backward difference for last frame
            prev_frame = frames[i - 1]
            dt = frame - prev_frame
            if dt > 0:
                pos1 = positions[prev_frame]
                pos2 = positions[frame]
                velocities[frame] = (
                    (pos2[0] - pos1[0]) / dt,
                    (pos2[1] - pos1[1]) / dt,
                    (pos2[2] - pos1[2]) / dt,
                )
        else:
            # Central difference for interior frames
            prev_frame = frames[i - 1]
            next_frame = frames[i + 1]
            dt = next_frame - prev_frame
            if dt > 0:
                pos1 = positions[prev_frame]
                pos2 = positions[next_frame]
                velocities[frame] = (
                    (pos2[0] - pos1[0]) / dt,
                    (pos2[1] - pos1[1]) / dt,
                    (pos2[2] - pos1[2]) / dt,
                )

    return velocities


def calculate_accelerations(
    velocities: Dict[int, Tuple[float, float, float]]
) -> Dict[int, Tuple[float, float, float]]:
    """
    Calculate acceleration vectors from velocities.

    Uses the same finite difference approach as velocity calculation.

    Args:
        velocities: Frame -> velocity mapping

    Returns:
        Frame -> acceleration mapping
    """
    # Acceleration is derivative of velocity, so same algorithm
    return calculate_velocities(velocities)


def interpolate_position(
    data: TrackingData,
    frame: int
) -> Optional[Tuple[float, float, float]]:
    """
    Interpolate position between keyframes.

    Uses linear interpolation for positions. For frames outside the
    tracked range, returns the nearest known position.

    Args:
        data: Tracking data with positions
        frame: Frame to interpolate

    Returns:
        Interpolated position or None
    """
    if not data.positions:
        return None

    # Check for exact match
    if frame in data.positions:
        return data.positions[frame]

    frames = sorted(data.positions.keys())
    start_frame = frames[0]
    end_frame = frames[-1]

    # Clamp to range
    if frame <= start_frame:
        return data.positions[start_frame]
    if frame >= end_frame:
        return data.positions[end_frame]

    # Find surrounding frames
    prev_frame = None
    next_frame = None
    for f in frames:
        if f < frame:
            prev_frame = f
        elif f > frame and next_frame is None:
            next_frame = f
            break

    if prev_frame is None or next_frame is None:
        return data.positions[frame] if frame in data.positions else None

    # Linear interpolation
    t = (frame - prev_frame) / (next_frame - prev_frame)
    pos1 = data.positions[prev_frame]
    pos2 = data.positions[next_frame]

    return (
        pos1[0] + t * (pos2[0] - pos1[0]),
        pos1[1] + t * (pos2[1] - pos1[1]),
        pos1[2] + t * (pos2[2] - pos1[2]),
    )


def predict_position(
    data: TrackingData,
    frame: int,
    lookahead: int
) -> Optional[Tuple[float, float, float]]:
    """
    Predict future position for smooth following.

    Uses velocity and acceleration to predict where the target
    will be in the future, allowing the camera to follow smoothly.

    Args:
        data: Tracking data with positions and velocities
        frame: Current frame
        lookahead: Number of frames to predict ahead

    Returns:
        Predicted position or None
    """
    if not data.positions:
        return None

    # Get current position
    current_pos = interpolate_position(data, frame)
    if current_pos is None:
        return None

    if lookahead <= 0:
        return current_pos

    # Get velocity at current frame
    velocity = data.velocities.get(frame)
    if velocity is None:
        return current_pos

    # Get acceleration for more accurate prediction
    acceleration = data.accelerations.get(frame, (0.0, 0.0, 0.0))

    # Predict using kinematic equation:
    # p_future = p_current + v * t + 0.5 * a * t^2
    t = float(lookahead)
    t2 = t * t

    predicted = (
        current_pos[0] + velocity[0] * t + 0.5 * acceleration[0] * t2,
        current_pos[1] + velocity[1] * t + 0.5 * acceleration[1] * t2,
        current_pos[2] + velocity[2] * t + 0.5 * acceleration[2] * t2,
    )

    return predicted


def apply_smoothing(
    data: TrackingData,
    amount: float
) -> TrackingData:
    """
    Apply temporal smoothing to tracking data.

    Uses exponential moving average for smooth tracking data
    that reduces jitter while maintaining responsiveness.

    Args:
        data: Original tracking data
        amount: Smoothing amount 0-1 (0 = none, 1 = maximum)

    Returns:
        Smoothed tracking data
    """
    if amount <= 0.0 or not data.positions:
        return data

    # Clamp smoothing amount
    amount = max(0.0, min(1.0, amount))

    # Calculate alpha for exponential smoothing
    # Higher smoothing = lower alpha = more averaging
    alpha = 1.0 - amount

    smoothed = TrackingData(marker_name=data.marker_name)
    frames = sorted(data.positions.keys())

    # Smooth positions
    prev_pos = data.positions[frames[0]]
    smoothed.positions[frames[0]] = prev_pos

    for frame in frames[1:]:
        current_pos = data.positions[frame]
        smoothed_pos = (
            alpha * current_pos[0] + (1.0 - alpha) * prev_pos[0],
            alpha * current_pos[1] + (1.0 - alpha) * prev_pos[1],
            alpha * current_pos[2] + (1.0 - alpha) * prev_pos[2],
        )
        smoothed.positions[frame] = smoothed_pos
        prev_pos = smoothed_pos

    # Recalculate velocities and accelerations for smoothed data
    smoothed.velocities = calculate_velocities(smoothed.positions)
    smoothed.accelerations = calculate_accelerations(smoothed.velocities)

    return smoothed


def apply_gaussian_smoothing(
    data: TrackingData,
    sigma: float = 1.0
) -> TrackingData:
    """
    Apply Gaussian smoothing to tracking data.

    Provides smoother results than exponential smoothing but
    requires more computation and future knowledge.

    Args:
        data: Original tracking data
        sigma: Gaussian kernel width in frames

    Returns:
        Smoothed tracking data
    """
    if sigma <= 0.0 or not data.positions:
        return data

    frames = sorted(data.positions.keys())
    n = len(frames)
    if n < 3:
        return data

    # Calculate Gaussian kernel
    kernel_size = int(sigma * 3) * 2 + 1
    kernel: List[float] = []
    for i in range(kernel_size):
        x = (i - kernel_size // 2) / sigma if sigma > 0 else 0
        kernel.append(math.exp(-0.5 * x * x))
    kernel_sum = sum(kernel)
    kernel = [k / kernel_sum for k in kernel]

    smoothed = TrackingData(marker_name=data.marker_name)

    # Apply Gaussian filter
    half_kernel = kernel_size // 2
    for i, frame in enumerate(frames):
        weighted_sum = [0.0, 0.0, 0.0]
        weight_total = 0.0

        for j in range(-half_kernel, half_kernel + 1):
            idx = i + j
            if 0 <= idx < n:
                kernel_idx = j + half_kernel
                weight = kernel[kernel_idx]
                pos = data.positions[frames[idx]]
                weighted_sum[0] += weight * pos[0]
                weighted_sum[1] += weight * pos[1]
                weighted_sum[2] += weight * pos[2]
                weight_total += weight

        if weight_total > 0:
            smoothed.positions[frame] = (
                weighted_sum[0] / weight_total,
                weighted_sum[1] / weight_total,
                weighted_sum[2] / weight_total,
            )

    # Recalculate velocities and accelerations
    smoothed.velocities = calculate_velocities(smoothed.positions)
    smoothed.accelerations = calculate_accelerations(smoothed.velocities)

    return smoothed
