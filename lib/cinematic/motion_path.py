"""
Motion Path Module

Provides procedural motion path generation for camera animations:
- Bezier curve path generation
- Arc and orbit path generation
- Catmull-Rom spline interpolation
- Blender curve object creation
- Follow Path constraint setup

Used for complex camera moves that don't fit standard animation patterns.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import math

from .types import MotionPathConfig
from .preset_loader import get_camera_move_preset

# Guarded imports for Blender API
try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    BLENDER_AVAILABLE = False


# =============================================================================
# BEZIER PATH GENERATION
# =============================================================================

def generate_bezier_path(
    control_points: List[Tuple[float, float, float]],
    segments: int = 100
) -> List[Tuple[Tuple[float, float, float], float]]:
    """
    Generate points along a cubic Bezier curve.

    Args:
        control_points: List of 4 control points as (x, y, z) tuples
                       P0=start, P1=control1, P2=control2, P3=end
        segments: Number of segments to generate

    Returns:
        List of (position, t_value) tuples where position is (x, y, z)
        and t_value is the parameter (0.0 to 1.0)
    """
    if len(control_points) < 4:
        raise ValueError("Cubic Bezier requires at least 4 control points")

    p0 = control_points[0]
    p1 = control_points[1]
    p2 = control_points[2]
    p3 = control_points[3]

    points = []
    for i in range(segments + 1):
        t = i / segments if segments > 0 else 0

        # Cubic Bezier formula: B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
        t_inv = 1.0 - t
        t_inv2 = t_inv * t_inv
        t_inv3 = t_inv2 * t_inv
        t2 = t * t
        t3 = t2 * t

        x = t_inv3 * p0[0] + 3 * t_inv2 * t * p1[0] + 3 * t_inv * t2 * p2[0] + t3 * p3[0]
        y = t_inv3 * p0[1] + 3 * t_inv2 * t * p1[1] + 3 * t_inv * t2 * p2[1] + t3 * p3[1]
        z = t_inv3 * p0[2] + 3 * t_inv2 * t * p1[2] + 3 * t_inv * t2 * p2[2] + t3 * p3[2]

        points.append(((x, y, z), t))

    return points


# =============================================================================
# ARC PATH GENERATION
# =============================================================================

def generate_arc_path(
    center: Tuple[float, float, float],
    radius: float,
    angle_start: float,
    angle_end: float,
    segments: int = 32,
    axis: str = "Z"
) -> List[Tuple[float, float, float]]:
    """
    Generate arc path points around a center point.

    Args:
        center: Center point of the arc (x, y, z)
        radius: Radius of the arc in meters
        angle_start: Starting angle in degrees
        angle_end: Ending angle in degrees
        segments: Number of segments to generate
        axis: Rotation axis (X, Y, or Z)

    Returns:
        List of (x, y, z) position tuples
    """
    start_rad = math.radians(angle_start)
    end_rad = math.radians(angle_end)

    points = []
    for i in range(segments + 1):
        t = i / segments if segments > 0 else 0
        angle = start_rad + (end_rad - start_rad) * t

        if axis.upper() == "Z":
            # Horizontal arc (around Z axis)
            x = center[0] + radius * math.sin(angle)
            y = center[1] - radius * math.cos(angle)
            z = center[2]
        elif axis.upper() == "Y":
            # Arc around Y axis
            x = center[0] + radius * math.sin(angle)
            y = center[1]
            z = center[2] - radius * math.cos(angle)
        else:  # X axis
            # Vertical arc (around X axis)
            x = center[0]
            y = center[1] + radius * math.sin(angle)
            z = center[2] - radius * math.cos(angle)

        points.append((x, y, z))

    return points


# =============================================================================
# ORBIT PATH GENERATION
# =============================================================================

def generate_orbit_path(
    center: Tuple[float, float, float],
    radius: float,
    angle_range: Tuple[float, float] = (0.0, 360.0),
    elevation: float = 0.0,
    segments: int = 64
) -> List[Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]]:
    """
    Generate procedural orbit path with look-at rotation.

    Args:
        center: Center point to orbit around (x, y, z)
        radius: Orbit radius in meters
        angle_range: Start and end angles in degrees
        elevation: Height offset from center in meters
        segments: Number of segments to generate

    Returns:
        List of (position, quaternion) tuples where quaternion is (w, x, y, z)
        for camera orientation looking at center
    """
    start_rad = math.radians(angle_range[0])
    end_rad = math.radians(angle_range[1])

    points = []
    for i in range(segments + 1):
        t = i / segments if segments > 0 else 0
        angle = start_rad + (end_rad - start_rad) * t

        # Calculate position
        x = center[0] + radius * math.sin(angle)
        y = center[1] - radius * math.cos(angle)
        z = center[2] + elevation
        position = (x, y, z)

        # Calculate look-at direction
        dx = center[0] - x
        dy = center[1] - y
        dz = center[2] - z

        # Convert direction to quaternion
        # This is a simplified look-at; use mathutils for accurate rotation
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length > 0:
            dx /= length
            dy /= length
            dz /= length

            # Create rotation from forward direction
            # Using -Z as forward, Y as up
            forward = (-dx, -dy, -dz)
            up = (0, 0, 1)

            # Cross product for right vector
            rx = up[1] * forward[2] - up[2] * forward[1]
            ry = up[2] * forward[0] - up[0] * forward[2]
            rz = up[0] * forward[1] - up[1] * forward[0]

            # Normalize right
            rlen = math.sqrt(rx*rx + ry*ry + rz*rz)
            if rlen > 0:
                rx /= rlen
                ry /= rlen
                rz /= rlen

            # Recalculate up as cross of forward and right
            ux = forward[1] * rz - forward[2] * ry
            uy = forward[2] * rx - forward[0] * rz
            uz = forward[0] * ry - forward[1] * rx

            # Convert rotation matrix to quaternion (simplified)
            # For accuracy, use mathutils.Vector.rotation_difference
            quaternion = _matrix_to_quaternion(forward, (rx, ry, rz), (ux, uy, uz))
        else:
            quaternion = (1, 0, 0, 0)  # Identity quaternion

        points.append((position, quaternion))

    return points


def _matrix_to_quaternion(
    forward: Tuple[float, float, float],
    right: Tuple[float, float, float],
    up: Tuple[float, float, float]
) -> Tuple[float, float, float, float]:
    """
    Convert orthonormal basis vectors to quaternion.

    Simplified conversion - for accuracy use mathutils.Matrix.to_quaternion().
    Returns quaternion as (w, x, y, z).
    """
    # Trace of rotation matrix
    trace = right[0] + up[1] + forward[2]

    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (up[2] - forward[1]) * s
        y = (forward[0] - right[2]) * s
        z = (right[1] - up[0]) * s
    elif right[0] > up[1] and right[0] > forward[2]:
        s = 2.0 * math.sqrt(1.0 + right[0] - up[1] - forward[2])
        w = (up[2] - forward[1]) / s
        x = 0.25 * s
        y = (up[0] + right[1]) / s
        z = (forward[0] + right[2]) / s
    elif up[1] > forward[2]:
        s = 2.0 * math.sqrt(1.0 + up[1] - right[0] - forward[2])
        w = (forward[0] - right[2]) / s
        x = (up[0] + right[1]) / s
        y = 0.25 * s
        z = (forward[1] + up[2]) / s
    else:
        s = 2.0 * math.sqrt(1.0 + forward[2] - right[0] - up[1])
        w = (right[1] - up[0]) / s
        x = (forward[0] + right[2]) / s
        y = (forward[1] + up[2]) / s
        z = 0.25 * s

    return (w, x, y, z)


# =============================================================================
# CATMULL-ROM SPLINE
# =============================================================================

def interpolate_catmull_rom(
    points: List[Tuple[float, float, float]],
    segments: int = 20
) -> List[Tuple[float, float, float]]:
    """
    Interpolate smooth path through multiple points using Catmull-Rom spline.

    Args:
        points: List of control points to interpolate through
        segments: Number of segments between each pair of points

    Returns:
        List of interpolated (x, y, z) position tuples
    """
    if len(points) < 2:
        return points

    result = []

    for i in range(len(points) - 1):
        # Get 4 control points (duplicate ends if needed)
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]

        # Generate segments between p1 and p2
        for j in range(segments):
            t = j / segments

            # Catmull-Rom basis functions
            t2 = t * t
            t3 = t2 * t

            b0 = -0.5 * t3 + t2 - 0.5 * t
            b1 = 1.5 * t3 - 2.5 * t2 + 1.0
            b2 = -1.5 * t3 + 2.0 * t2 + 0.5 * t
            b3 = 0.5 * t3 - 0.5 * t2

            x = b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0]
            y = b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]
            z = b0 * p0[2] + b1 * p1[2] + b2 * p2[2] + b3 * p3[2]

            result.append((x, y, z))

    # Add final point
    result.append(points[-1])

    return result


# =============================================================================
# PATH OBJECT CREATION
# =============================================================================

def create_motion_path_curve(
    points: List[Tuple[float, float, float]],
    name: str = "motion_path"
) -> Optional[Any]:
    """
    Create Blender Curve object from path points.

    Creates a Curve object with a Bezier spline following the points.
    The curve can be used for Follow Path constraints.

    Args:
        points: List of (x, y, z) position tuples
        name: Name for the curve object

    Returns:
        Blender curve object, or None if Blender not available
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    if len(points) < 2:
        return None

    # Create curve data
    curve_data = bpy.data.curves.new(name=f"{name}_data", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 12  # Resolution for rendering

    # Create spline
    spline = curve_data.splines.new(type="BEZIER")
    spline.bezier_points.add(len(points) - 1)  # Add points (one already exists)

    # Set point positions
    for i, point in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = point
        bp.handle_type_left = "AUTO"
        bp.handle_type_right = "AUTO"

    # Create curve object
    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_obj)

    return curve_obj


# =============================================================================
# FOLLOW PATH CONSTRAINT
# =============================================================================

def setup_camera_follow_path(
    camera_name: str,
    curve_name: str,
    duration: int = 120,
    look_at: str = "forward",
    start_frame: int = 1
) -> bool:
    """
    Setup Follow Path constraint on camera.

    Configures a camera to follow a curve path with optional look-at behavior.

    Args:
        camera_name: Name of the camera object
        curve_name: Name of the curve object to follow
        duration: Duration of path traversal in frames
        look_at: Look-at mode ("plumb_bob", "forward", "manual")
        start_frame: First frame of animation

    Returns:
        True if constraint was set up successfully
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    cam_obj = bpy.data.objects.get(camera_name)
    curve_obj = bpy.data.objects.get(curve_name)

    if not cam_obj or not curve_obj:
        return False

    # Add Follow Path constraint
    constraint = cam_obj.constraints.new(type="FOLLOW_PATH")
    constraint.target = curve_obj
    constraint.use_curve_follow = True
    constraint.forward_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    # Animate the offset factor from 0 to 100 (or use curve path duration)
    curve_obj.data.path_duration = duration
    curve_obj.data.use_path = True

    # Set keyframes for evaluation time on the curve
    curve_obj.keyframe_insert(data_path="eval_time", frame=start_frame)
    curve_obj.data.eval_time = duration
    curve_obj.keyframe_insert(data_path="eval_time", frame=start_frame + duration)

    # For camera rotation based on look_at mode
    if look_at == "forward":
        # Use curve follow for rotation (already enabled)
        pass
    elif look_at == "plumb_bob":
        # Would need a Track To constraint to plumb bob target
        # This requires additional target setup
        pass
    elif look_at == "manual":
        # Camera keeps its own rotation
        constraint.use_curve_follow = False

    return True


# =============================================================================
# PATH UTILITIES
# =============================================================================

def calculate_path_length(
    points: List[Tuple[float, float, float]]
) -> float:
    """
    Calculate total path length by summing segment distances.

    Args:
        points: List of (x, y, z) position tuples

    Returns:
        Total path length in meters
    """
    if len(points) < 2:
        return 0.0

    total_length = 0.0
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        total_length += math.sqrt(dx*dx + dy*dy + dz*dz)

    return total_length


def get_point_at_distance(
    points: List[Tuple[float, float, float]],
    distance: float
) -> Tuple[float, float, float]:
    """
    Get interpolated point at specific distance along path.

    Args:
        points: List of (x, y, z) position tuples
        distance: Distance along path in meters

    Returns:
        Interpolated (x, y, z) position
    """
    if len(points) < 2:
        return points[0] if points else (0, 0, 0)

    accumulated = 0.0
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        segment_length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if accumulated + segment_length >= distance:
            # Interpolate within this segment
            t = (distance - accumulated) / segment_length if segment_length > 0 else 0
            return (
                p1[0] + dx * t,
                p1[1] + dy * t,
                p1[2] + dz * t
            )

        accumulated += segment_length

    # Return last point if distance exceeds path length
    return points[-1]


def sample_path_uniformly(
    points: List[Tuple[float, float, float]],
    sample_count: int
) -> List[Tuple[float, float, float]]:
    """
    Resample path for uniform distribution of points.

    Args:
        points: List of (x, y, z) position tuples
        sample_count: Number of samples to generate

    Returns:
        List of uniformly distributed (x, y, z) positions
    """
    if sample_count < 2:
        return points[:sample_count]

    total_length = calculate_path_length(points)
    if total_length == 0:
        return points[:sample_count]

    samples = []
    for i in range(sample_count):
        distance = (i / (sample_count - 1)) * total_length
        samples.append(get_point_at_distance(points, distance))

    return samples


# =============================================================================
# CONFIG-BASED FUNCTIONS
# =============================================================================

def create_motion_path_from_config(
    config: MotionPathConfig,
    target_position: Optional[Tuple[float, float, float]] = None
) -> Optional[Any]:
    """
    Create motion path from MotionPathConfig.

    Dispatches to appropriate generation function based on path_type
    and creates a Blender curve object.

    Args:
        config: MotionPathConfig with path settings
        target_position: Target/center position for orbit/arc paths

    Returns:
        Blender curve object, or None if creation failed
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    if target_position is None:
        target_position = (0, 0, 0)

    points = []

    if config.path_type == "bezier":
        # Get control points from config
        if config.points and len(config.points) >= 4:
            control_points = [
                tuple(p.get("position", (0, 0, 0)))
                for p in config.points[:4]
            ]
            bezier_result = generate_bezier_path(control_points, config.duration)
            points = [p[0] for p in bezier_result]

    elif config.path_type == "arc":
        # Generate arc path
        radius = config.points[0].get("radius", 1.0) if config.points else 1.0
        angle_range = (
            config.points[0].get("angle_start", 0),
            config.points[0].get("angle_end", 360)
        ) if config.points else (0, 360)
        axis = config.points[0].get("axis", "Z") if config.points else "Z"
        points = generate_arc_path(
            target_position, radius,
            angle_range[0], angle_range[1],
            config.duration, axis
        )

    elif config.path_type == "spline":
        # Catmull-Rom spline through points
        if config.points:
            control_points = [
                tuple(p.get("position", (0, 0, 0)))
                for p in config.points
            ]
            points = interpolate_catmull_rom(control_points, 20)

    elif config.path_type == "linear":
        # Simple linear path through points
        if config.points:
            points = [
                tuple(p.get("position", (0, 0, 0)))
                for p in config.points
            ]

    else:
        # Default to linear
        if config.points:
            points = [
                tuple(p.get("position", (0, 0, 0)))
                for p in config.points
            ]

    if not points:
        return None

    # Create curve object
    curve_name = f"motion_path_{config.path_type}"
    return create_motion_path_curve(points, curve_name)


def create_motion_path_from_preset(
    preset_name: str,
    target_position: Optional[Tuple[float, float, float]] = None
) -> Optional[Any]:
    """
    Create motion path from a preset.

    Args:
        preset_name: Name of the camera move preset
        target_position: Target position for orbit/arc paths

    Returns:
        Blender curve object, or None if creation failed
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    try:
        preset = get_camera_move_preset(preset_name)
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to load preset '{preset_name}': {e}")
        return None

    if target_position is None:
        target_position = (0, 0, 0)

    move_type = preset.get("type", "static")

    if move_type == "orbit":
        radius = preset.get("radius", 1.0)
        angle_range = tuple(preset.get("angle_range", [0, 360]))
        axis = preset.get("axis", "Z")
        duration = preset.get("duration", 120)
        points = generate_arc_path(
            target_position, radius,
            angle_range[0], angle_range[1],
            duration, axis
        )
        return create_motion_path_curve(points, f"orbit_path_{preset_name}")

    return None


def remove_motion_path(curve_name: str) -> bool:
    """
    Remove a motion path curve object.

    Args:
        curve_name: Name of the curve object to remove

    Returns:
        True if curve was removed, False if not found
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender not available")

    curve_obj = bpy.data.objects.get(curve_name)
    if not curve_obj:
        return False

    # Remove curve data
    curve_data = curve_obj.data

    # Unlink from all collections
    for collection in bpy.data.collections:
        if curve_obj.name in collection.objects:
            collection.objects.unlink(curve_obj)

    # Delete object and data
    bpy.data.objects.remove(curve_obj)
    bpy.data.curves.remove(curve_data)

    return True
