"""
Safe mathematical operations for Blender GSD pipeline.

Provides quaternion-based rotation interpolation, smooth falloff functions,
and safe geometric operations to avoid gimbal lock and numerical instability.

Usage:
    from lib.utils.math_safe import (
        interpolate_rotation,
        smooth_falloff,
        safe_scale_blend,
        clamp_vector,
    )
"""

import math
import warnings
from typing import Tuple, List, Union, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Type aliases
Vector3 = Tuple[float, float, float]
Vector4 = Tuple[float, float, float, float]
Euler = Tuple[float, float, float]  # In radians
Quaternion = Tuple[float, float, float, float]  # (w, x, y, z)


# ============================================================================
# QUATERNION OPERATIONS
# ============================================================================

def euler_to_quaternion(euler: Euler, order: str = 'XYZ') -> Quaternion:
    """
    Convert Euler angles to quaternion.

    Args:
        euler: Euler angles in radians (x, y, z)
        order: Rotation order ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX')

    Returns:
        Quaternion as (w, x, y, z)
    """
    x, y, z = euler

    # Compute half angles
    cx = math.cos(x / 2)
    sx = math.sin(x / 2)
    cy = math.cos(y / 2)
    sy = math.sin(y / 2)
    cz = math.cos(z / 2)
    sz = math.sin(z / 2)

    # XYZ order (most common)
    if order == 'XYZ':
        w = cx * cy * cz - sx * sy * sz
        qx = sx * cy * cz + cx * sy * sz
        qy = cx * sy * cz - sx * cy * sz
        qz = cx * cy * sz + sx * sy * cz
    elif order == 'ZYX':
        w = cx * cy * cz + sx * sy * sz
        qx = sx * cy * cz - cx * sy * sz
        qy = cx * sy * cz + sx * cy * sz
        qz = cx * cy * sz - sx * sy * cz
    else:
        # Fallback to mathutils if available
        try:
            from mathutils import Euler as BlenderEuler
            e = BlenderEuler(euler, order)
            q = e.to_quaternion()
            return (q.w, q.x, q.y, q.z)
        except ImportError:
            warnings.warn(f"Rotation order {order} not implemented, using XYZ")
            return euler_to_quaternion(euler, 'XYZ')

    # Normalize
    length = math.sqrt(w*w + qx*qx + qy*qy + qz*qz)
    if length > 0:
        w, qx, qy, qz = w/length, qx/length, qy/length, qz/length

    return (w, qx, qy, qz)


def quaternion_to_euler(quat: Quaternion, order: str = 'XYZ') -> Euler:
    """
    Convert quaternion to Euler angles.

    Args:
        quat: Quaternion as (w, x, y, z)
        order: Target rotation order

    Returns:
        Euler angles in radians (x, y, z)
    """
    w, x, y, z = quat

    # Normalize input
    length = math.sqrt(w*w + x*x + y*y + z*z)
    if length > 0:
        w, x, y, z = w/length, x/length, y/length, z/length

    # XYZ order conversion
    if order == 'XYZ':
        # Roll (X-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        rx = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (Y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            ry = math.copysign(math.pi / 2, sinp)  # Clamp to 90 degrees
        else:
            ry = math.asin(sinp)

        # Yaw (Z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        rz = math.atan2(siny_cosp, cosy_cosp)

        return (rx, ry, rz)

    # Try mathutils for other orders
    try:
        from mathutils import Quaternion as BlenderQuat, Euler as BlenderEuler
        q = BlenderQuat((w, x, y, z))
        e = q.to_euler(order)
        return (e.x, e.y, e.z)
    except ImportError:
        warnings.warn(f"Rotation order {order} fallback to XYZ")
        return quaternion_to_euler(quat, 'XYZ')


def quaternion_slerp(
    quat_a: Quaternion,
    quat_b: Quaternion,
    t: float,
    shortest_path: bool = True
) -> Quaternion:
    """
    Spherical linear interpolation between two quaternions.

    This is the safe way to interpolate rotations, avoiding gimbal lock
    and ensuring constant angular velocity.

    Args:
        quat_a: Start quaternion (w, x, y, z)
        quat_b: End quaternion (w, x, y, z)
        t: Interpolation factor (0.0 to 1.0)
        shortest_path: Take shortest path on hypersphere

    Returns:
        Interpolated quaternion (w, x, y, z)
    """
    # Clamp t
    t = max(0.0, min(1.0, t))

    # Extract components
    w1, x1, y1, z1 = quat_a
    w2, x2, y2, z2 = quat_b

    # Compute dot product (cosine of angle between quaternions)
    dot = w1*w2 + x1*x2 + y1*y2 + z1*z2

    # If negative dot, negate one quaternion to take shorter path
    if shortest_path and dot < 0:
        w2, x2, y2, z2 = -w2, -x2, -y2, -z2
        dot = -dot

    # Clamp dot to valid range
    dot = max(-1.0, min(1.0, dot))

    # If quaternions are close, use linear interpolation
    if dot > 0.9995:
        # Linear interpolation
        w = w1 + t * (w2 - w1)
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        z = z1 + t * (z2 - z1)

        # Normalize
        length = math.sqrt(w*w + x*x + y*y + z*z)
        if length > 0:
            w, x, y, z = w/length, x/length, y/length, z/length

        return (w, x, y, z)

    # Calculate interpolation coefficients
    theta = math.acos(dot)
    sin_theta = math.sin(theta)

    # Handle near-zero sin_theta
    if abs(sin_theta) < 1e-10:
        return quat_a

    # Slerp formula
    wa = math.sin((1 - t) * theta) / sin_theta
    wb = math.sin(t * theta) / sin_theta

    w = wa * w1 + wb * w2
    x = wa * x1 + wb * x2
    y = wa * y1 + wb * y2
    z = wa * z1 + wb * z2

    return (w, x, y, z)


def quaternion_multiply(quat_a: Quaternion, quat_b: Quaternion) -> Quaternion:
    """Multiply two quaternions (combine rotations)."""
    w1, x1, y1, z1 = quat_a
    w2, x2, y2, z2 = quat_b

    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2

    return (w, x, y, z)


def quaternion_normalize(quat: Quaternion) -> Quaternion:
    """Normalize a quaternion."""
    w, x, y, z = quat
    length = math.sqrt(w*w + x*x + y*y + z*z)

    if length < 1e-10:
        return (1.0, 0.0, 0.0, 0.0)  # Identity quaternion

    return (w/length, x/length, y/length, z/length)


# ============================================================================
# SAFE ROTATION INTERPOLATION
# ============================================================================

def interpolate_rotation(
    rot_a: Union[Euler, Quaternion],
    rot_b: Union[Euler, Quaternion],
    t: float,
    mode: str = 'quaternion',
    euler_order: str = 'XYZ'
) -> Union[Euler, Quaternion]:
    """
    Safely interpolate between two rotations.

    Args:
        rot_a: Start rotation (Euler radians or Quaternion)
        rot_b: End rotation (Euler radians or Quaternion)
        t: Interpolation factor (0.0 to 1.0)
        mode: 'quaternion' for slerp, 'euler' for linear (avoid for gimbal lock)
        euler_order: Rotation order for Euler mode

    Returns:
        Interpolated rotation in same format as input
    """
    t = max(0.0, min(1.0, t))

    # Detect input type
    is_quat = len(rot_a) == 4 and len(rot_b) == 4

    if mode == 'quaternion':
        if is_quat:
            return quaternion_slerp(rot_a, rot_b, t)
        else:
            # Convert to quat, slerp, convert back
            quat_a = euler_to_quaternion(rot_a, euler_order)
            quat_b = euler_to_quaternion(rot_b, euler_order)
            result_quat = quaternion_slerp(quat_a, quat_b, t)
            return quaternion_to_euler(result_quat, euler_order)

    elif mode == 'euler':
        # Linear interpolation (can cause gimbal lock!)
        if is_quat:
            warnings.warn("Euler interpolation requested for quaternion input")
            euler_a = quaternion_to_euler(rot_a, euler_order)
            euler_b = quaternion_to_euler(rot_b, euler_order)
        else:
            euler_a = rot_a
            euler_b = rot_b

        # Linear interp
        result = tuple(euler_a[i] + t * (euler_b[i] - euler_a[i]) for i in range(3))

        if is_quat:
            return euler_to_quaternion(result, euler_order)
        return result

    else:
        raise ValueError(f"Unknown interpolation mode: {mode}")


# ============================================================================
# SMOOTH FALLOFF FUNCTIONS
# ============================================================================

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """
    Hermite smoothstep interpolation.

    Args:
        edge0: Lower edge
        edge1: Upper edge
        x: Value to interpolate

    Returns:
        Smoothly interpolated value in [0, 1]
    """
    # Clamp x to [0, 1] range relative to edges
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0) if edge1 != edge0 else 0.5))

    # Hermite smoothstep: 3t^2 - 2t^3
    return t * t * (3.0 - 2.0 * t)


def smootherstep(edge0: float, edge1: float, x: float) -> float:
    """
    Ken Perlin's improved smoothstep (6t^5 - 15t^4 + 10t^3).

    Args:
        edge0: Lower edge
        edge1: Upper edge
        x: Value to interpolate

    Returns:
        Smoothly interpolated value in [0, 1]
    """
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0) if edge1 != edge0 else 0.5))

    # Perlin smootherstep: 6t^5 - 15t^4 + 10t^3
    return t * t * t * (t * (t * 6 - 15) + 10)


def smooth_falloff(value: float, threshold: float = 0.5) -> float:
    """
    Apply smooth polynomial falloff for small values.

    Use this instead of hard cutoffs (e.g., in Ackermann steering).

    Args:
        value: Input value
        threshold: Threshold below which falloff applies

    Returns:
        Value with smooth falloff applied
    """
    # Zero within floating point tolerance
    if abs(value) < 1e-6:
        return 0.0

    # Full value above threshold
    if abs(value) >= threshold:
        return value

    # Smooth falloff below threshold
    t = abs(value) / threshold
    factor = t * t * (3.0 - 2.0 * t)  # smoothstep

    return value * factor


def exponential_falloff(value: float, rate: float = 1.0) -> float:
    """
    Exponential falloff function.

    Args:
        value: Input value
        rate: Falloff rate (higher = faster falloff)

    Returns:
        Value with exponential falloff
    """
    return value * math.exp(-rate * abs(value))


# ============================================================================
# SAFE SCALE BLENDING
# ============================================================================

def safe_scale_blend(
    current_scale: Vector3,
    delta_scale: Vector3,
    opacity: float,
    mode: str = 'multiplicative'
) -> Vector3:
    """
    Safely blend scale values.

    The naive approach using power function fails for negative values.
    This uses a safe multiplicative approach instead.

    Args:
        current_scale: Current scale (x, y, z)
        delta_scale: Scale delta from layer (x, y, z)
        opacity: Blend opacity (0 to 1)
        mode: 'multiplicative' or 'additive'

    Returns:
        Blended scale (x, y, z)
    """
    result = []

    for i in range(3):
        curr = current_scale[i]
        delta = delta_scale[i]

        if mode == 'multiplicative':
            # Safe multiplicative: scale * (1 + (delta - 1) * opacity)
            # This works correctly for all delta values
            blended = curr * (1.0 + (delta - 1.0) * opacity)
        elif mode == 'additive':
            # Simple additive blend
            blended = curr + delta * opacity
        else:
            raise ValueError(f"Unknown scale blend mode: {mode}")

        # Prevent zero or negative scale (can cause rendering issues)
        blended = max(0.001, blended)

        result.append(blended)

    return tuple(result)


def safe_scale_power(scale: Vector3, exponent: float) -> Vector3:
    """
    Safely raise scale to a power.

    Handles negative and zero values correctly.

    Args:
        scale: Scale values (x, y, z)
        exponent: Power to raise to

    Returns:
        Resulting scale (x, y, z)
    """
    result = []

    for s in scale:
        if s >= 0:
            result.append(math.pow(max(0.001, s), exponent))
        else:
            # For negative scale, maintain sign
            result.append(-math.pow(max(0.001, abs(s)), exponent))

    return tuple(result)


# ============================================================================
# VECTOR UTILITIES
# ============================================================================

def clamp_vector(
    vector: Vector3,
    min_val: Union[float, Vector3],
    max_val: Union[float, Vector3]
) -> Vector3:
    """
    Clamp vector components to range.

    Args:
        vector: Input vector (x, y, z)
        min_val: Minimum value (scalar or per-component)
        max_val: Maximum value (scalar or per-component)

    Returns:
        Clamped vector (x, y, z)
    """
    if isinstance(min_val, (int, float)):
        min_val = (min_val, min_val, min_val)
    if isinstance(max_val, (int, float)):
        max_val = (max_val, max_val, max_val)

    return tuple(
        max(min_val[i], min(max_val[i], vector[i]))
        for i in range(3)
    )


def lerp_vector(a: Vector3, b: Vector3, t: float) -> Vector3:
    """
    Linear interpolation between two vectors.

    Args:
        a: Start vector
        b: End vector
        t: Interpolation factor (0 to 1)

    Returns:
        Interpolated vector
    """
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + t * (b[i] - a[i]) for i in range(3))


def vector_length(vector: Vector3) -> float:
    """Calculate vector length."""
    return math.sqrt(sum(v * v for v in vector))


def normalize_vector(vector: Vector3) -> Vector3:
    """Normalize a vector to unit length."""
    length = vector_length(vector)
    if length < 1e-10:
        return (0.0, 0.0, 0.0)
    return tuple(v / length for v in vector)


def vector_dot(a: Vector3, b: Vector3) -> float:
    """Dot product of two vectors."""
    return sum(a[i] * b[i] for i in range(3))


def vector_cross(a: Vector3, b: Vector3) -> Vector3:
    """Cross product of two vectors."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )


# ============================================================================
# ANGLE UTILITIES
# ============================================================================

def normalize_angle(angle: float, center: float = 0.0) -> float:
    """
    Normalize angle to [center - pi, center + pi] range.

    Args:
        angle: Angle in radians
        center: Center of output range

    Returns:
        Normalized angle in radians
    """
    two_pi = 2.0 * math.pi
    return angle - two_pi * math.floor((angle + math.pi - center) / two_pi)


def angle_difference(angle_a: float, angle_b: float) -> float:
    """
    Calculate shortest angular difference.

    Args:
        angle_a: First angle in radians
        angle_b: Second angle in radians

    Returns:
        Shortest difference in radians (-pi to pi)
    """
    diff = angle_b - angle_a
    return normalize_angle(diff)


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * math.pi / 180.0


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * 180.0 / math.pi


def euler_degrees_to_radians(euler_deg: Euler) -> Euler:
    """Convert Euler angles from degrees to radians."""
    return tuple(degrees_to_radians(a) for a in euler_deg)


def euler_radians_to_degrees(euler_rad: Euler) -> Euler:
    """Convert Euler angles from radians to degrees."""
    return tuple(radians_to_degrees(a) for a in euler_rad)


# ============================================================================
# BONE CHAIN VALIDATION
# ============================================================================

@dataclass
class BoneInfo:
    """Information about a bone for validation."""
    name: str
    parent: Optional[str]
    head: Vector3
    tail: Vector3


def validate_bone_chain(bones: List[BoneInfo], expected_length: int) -> Tuple[bool, List[str]]:
    """
    Validate that bones form a contiguous chain.

    Args:
        bones: List of bone information
        expected_length: Expected number of bones in chain

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    if len(bones) != expected_length:
        issues.append(f"Chain has {len(bones)} bones, expected {expected_length}")

    # Check connectivity
    for i in range(1, len(bones)):
        prev = bones[i - 1]
        curr = bones[i]

        # Check if current bone's parent is previous bone
        if curr.parent != prev.name:
            issues.append(f"Bone {curr.name} parent is {curr.parent}, expected {prev.name}")

        # Check if head of current matches tail of previous (within tolerance)
        if prev.tail and curr.head:
            dist = vector_length(tuple(curr.head[i] - prev.tail[i] for i in range(3)))
            if dist > 0.001:
                issues.append(f"Gap of {dist:.4f} between {prev.name} and {curr.name}")

    return len(issues) == 0, issues
