"""
Stunt Physics Module

Physics calculations for vehicle stunts.

Phase 17.4: Launch Control & Physics (REQ-STUNT-05)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import math


# Physics constants
PHYSICS_CONSTANTS = {
    'gravity': 9.81,           # m/s²
    'air_density': 1.225,      # kg/m³ at sea level
    'drag_coefficient': 0.35,  # typical car
    'friction_concrete': 0.8,
    'friction_dirt': 0.6,
    'friction_grass': 0.4,
}

GRAVITY = PHYSICS_CONSTANTS['gravity']


def calculate_launch_velocity(
    distance: float,
    angle: float,
    height_diff: float = 0.0,
    include_drag: bool = False,
    drag_coefficient: float = 0.35,
    vehicle_mass: float = 1500.0,
    frontal_area: float = 2.5,
) -> float:
    """Calculate required launch velocity for a jump.

    Args:
        distance: Horizontal distance in meters
        angle: Launch angle in degrees
        height_diff: Height difference (positive = landing higher)
        include_drag: Whether to account for air resistance
        drag_coefficient: Aerodynamic drag coefficient
        vehicle_mass: Vehicle mass in kg
        frontal_area: Frontal area in m²

    Returns:
        Required launch velocity in m/s
    """
    g = GRAVITY
    angle_rad = math.radians(angle)

    # Basic projectile motion (no drag)
    # d = v² * sin(2θ) / g
    # v = sqrt(d * g / sin(2θ))

    sin_2theta = math.sin(2 * angle_rad)
    if sin_2theta <= 0:
        return 0.0

    v_base = math.sqrt(distance * g / sin_2theta)

    # Adjust for height difference
    if height_diff > 0:
        # Landing higher - need more speed
        v_adjusted = math.sqrt(v_base**2 + 2 * g * height_diff)
    elif height_diff < 0:
        # Landing lower - need less speed
        v_adjusted = math.sqrt(max(0.01, v_base**2 + 2 * g * height_diff))
    else:
        v_adjusted = v_base

    # Add drag correction
    if include_drag:
        # Approximate drag effect (iterative solution)
        # F_drag = 0.5 * ρ * Cd * A * v²
        # This is simplified - real solution requires integration

        drag_factor = 0.5 * PHYSICS_CONSTANTS['air_density'] * drag_coefficient * frontal_area
        ballistic_coefficient = vehicle_mass / drag_factor

        # Approximate velocity loss due to drag
        # v_loss ≈ (d * drag_factor * v²) / m
        drag_correction = 1.0 + (distance * drag_factor) / (vehicle_mass * 10)
        v_adjusted = v_adjusted * drag_correction

    return v_adjusted


def calculate_air_time(
    velocity: float,
    angle: float,
    height: float = 0.0,
) -> float:
    """Calculate total air time for a jump.

    Args:
        velocity: Launch velocity in m/s
        angle: Launch angle in degrees
        height: Launch height in meters

    Returns:
        Air time in seconds
    """
    g = GRAVITY
    angle_rad = math.radians(angle)

    vy = velocity * math.sin(angle_rad)

    # Time to reach ground: t = (vy + sqrt(vy² + 2gh)) / g
    discriminant = vy**2 + 2 * g * height

    if discriminant < 0:
        return 0.0

    return (vy + math.sqrt(discriminant)) / g


def calculate_landing_velocity(
    launch_velocity: float,
    angle: float,
    height_diff: float = 0.0,
    include_drag: bool = False,
) -> Tuple[float, float, float]:
    """Calculate landing velocity components.

    Args:
        launch_velocity: Initial velocity in m/s
        angle: Launch angle in degrees
        height_diff: Height difference (positive = landing higher)
        include_drag: Whether to account for air resistance

    Returns:
        Tuple of (vx, vy, vz) landing velocity components
    """
    g = GRAVITY
    angle_rad = math.radians(angle)

    # Initial velocity components
    vx = launch_velocity * math.cos(angle_rad)
    vy = launch_velocity * math.sin(angle_rad)

    # Calculate air time
    t = calculate_air_time(launch_velocity, angle, -height_diff)

    # Final velocity components (no drag)
    final_vx = vx
    final_vy = vy - g * t

    if include_drag:
        # Approximate drag effect
        drag_factor = 0.02  # Simplified
        final_vx *= (1 - drag_factor)
        final_vy *= (1 - drag_factor * 0.5)

    return (final_vx, final_vy, 0.0)


def calculate_g_force(
    velocity: float,
    radius: float,
) -> float:
    """Calculate G-force for circular motion.

    Args:
        velocity: Speed in m/s
        radius: Turn radius in meters

    Returns:
        G-force (multiples of gravity)
    """
    g = GRAVITY

    # a = v² / r
    centripetal_acc = velocity**2 / radius

    # G-force = a / g
    return centripetal_acc / g


def calculate_impact_g_force(
    landing_velocity: float,
    compression_distance: float = 0.3,
) -> float:
    """Calculate G-force on landing impact.

    Args:
        landing_velocity: Vertical landing speed in m/s
        compression_distance: Suspension compression distance in meters

    Returns:
        Peak G-force on impact
    """
    g = GRAVITY

    # v² = 2 * a * d
    # a = v² / (2 * d)
    deceleration = landing_velocity**2 / (2 * compression_distance)

    return deceleration / g


def calculate_loop_physics(
    radius: float,
    entry_speed: float,
    vehicle_mass: float = 1500.0,
) -> Dict[str, float]:
    """Calculate physics for loop-the-loop.

    Args:
        radius: Loop radius in meters
        entry_speed: Entry speed in m/s
        vehicle_mass: Vehicle mass in kg

    Returns:
        Dictionary with physics values
    """
    g = GRAVITY

    # Minimum speed at top to maintain contact: v_top = sqrt(g * r)
    v_min_top = math.sqrt(g * radius)

    # Entry speed needed (energy conservation)
    # 0.5 * m * v_entry² = 0.5 * m * v_top² + m * g * 2r
    v_min_entry = math.sqrt(v_min_top**2 + 2 * g * 2 * radius)

    # Speed at top with given entry speed
    v_top = math.sqrt(max(0, entry_speed**2 - 4 * g * radius))

    # G-forces
    g_entry = entry_speed**2 / (radius * g)
    g_top = (v_top**2 / radius + g) / g  # Include gravity at top
    g_exit = entry_speed**2 / (radius * g)  # Approximate

    return {
        'min_entry_speed': v_min_entry,
        'min_top_speed': v_min_top,
        'actual_top_speed': v_top,
        'can_complete': entry_speed >= v_min_entry,
        'g_entry': g_entry,
        'g_top': g_top,
        'g_exit': g_exit,
        'max_g_force': max(g_entry, g_top, g_exit),
    }


def calculate_banked_turn_physics(
    radius: float,
    bank_angle: float,
    speed: float,
) -> Dict[str, float]:
    """Calculate physics for banked turn.

    Args:
        radius: Turn radius in meters
        bank_angle: Banking angle in degrees
        speed: Vehicle speed in m/s

    Returns:
        Dictionary with physics values
    """
    g = GRAVITY
    angle_rad = math.radians(bank_angle)

    # Design speed (no lateral force needed)
    # tan(θ) = v² / (r * g)
    design_speed = math.sqrt(radius * g * math.tan(angle_rad))

    # Actual lateral G-force
    # a_lateral = v² / r
    lateral_acc = speed**2 / radius
    lateral_g = lateral_acc / g

    # Vertical G-force (apparent weight)
    # Normal force components
    normal_g = 1.0 / math.cos(angle_rad)  # Base weight
    centripetal_component = lateral_g * math.sin(angle_rad)

    total_g = normal_g + centripetal_component

    # Friction required (if speed != design speed)
    # f = (v²/r * cos(θ) - g * sin(θ)) / (g * cos(θ) + v²/r * sin(θ))
    numerator = (lateral_acc * math.cos(angle_rad) - g * math.sin(angle_rad))
    denominator = (g * math.cos(angle_rad) + lateral_acc * math.sin(angle_rad))

    if denominator != 0:
        friction_required = abs(numerator / denominator)
    else:
        friction_required = 0.0

    return {
        'design_speed': design_speed,
        'lateral_g': lateral_g,
        'total_g': total_g,
        'friction_required': friction_required,
        'is_safe': friction_required < 0.8,  # Typical tire friction
        'speed_margin': (speed / design_speed - 1) * 100 if design_speed > 0 else 0,
    }


def calculate_wall_ride_physics(
    speed: float,
    wall_angle: float,
    wall_length: float,
    vehicle_mass: float = 1500.0,
    friction_coeff: float = 0.7,
) -> Dict[str, Any]:
    """Calculate physics for wall ride.

    Args:
        speed: Entry speed in m/s
        wall_angle: Wall angle from horizontal in degrees
        wall_length: Wall length in meters
        vehicle_mass: Vehicle mass in kg
        friction_coeff: Surface friction coefficient

    Returns:
        Dictionary with physics values
    """
    g = GRAVITY
    angle_rad = math.radians(wall_angle)

    # Time on wall
    time_on_wall = wall_length / speed

    # Normal force (perpendicular to wall)
    normal_force = vehicle_mass * g * math.cos(angle_rad)

    # Friction force (parallel to wall, opposing gravity component)
    friction_force = friction_coeff * normal_force

    # Gravity component along wall
    gravity_component = vehicle_mass * g * math.sin(angle_rad)

    # Can vehicle stick to wall?
    can_stick = friction_force >= gravity_component

    # Net acceleration along wall
    if can_stick:
        net_acceleration = 0
    else:
        net_acceleration = (gravity_component - friction_force) / vehicle_mass

    # Distance traveled before sliding off (if can't stick)
    if not can_stick and net_acceleration > 0:
        slide_distance = speed**2 / (2 * net_acceleration)
        can_complete = slide_distance >= wall_length
    else:
        can_complete = can_stick

    # Required minimum speed
    min_speed = math.sqrt(2 * g * wall_length * math.sin(angle_rad))

    # Exit speed
    exit_speed = speed * 0.9  # Approximate 10% loss

    return {
        'time_on_wall': time_on_wall,
        'normal_force': normal_force,
        'friction_force': friction_force,
        'gravity_component': gravity_component,
        'can_stick': can_stick,
        'net_acceleration': net_acceleration,
        'can_complete': can_complete,
        'min_entry_speed': min_speed * 1.2,
        'exit_speed': exit_speed,
        'is_safe': can_stick and speed >= min_speed,
    }


def calculate_optimal_trajectory(
    start_pos: Tuple[float, float, float],
    end_pos: Tuple[float, float, float],
    max_height: Optional[float] = None,
    constraints: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate optimal trajectory between two points.

    Args:
        start_pos: Starting position (x, y, z)
        end_pos: Ending position (x, y, z)
        max_height: Optional maximum height constraint
        constraints: Optional physics constraints

    Returns:
        Dictionary with trajectory parameters
    """
    g = GRAVITY

    # Calculate distance and height difference
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    dz = end_pos[2] - start_pos[2]

    horizontal_dist = math.sqrt(dx**2 + dy**2)
    height_diff = dz

    # Calculate optimal angle
    if abs(height_diff) < 0.1:
        # Flat landing - 45 degrees is optimal
        optimal_angle = 45.0
    elif height_diff > 0:
        # Landing higher - need steeper angle
        optimal_angle = 45.0 + math.degrees(math.atan(height_diff / horizontal_dist)) / 2
    else:
        # Landing lower - can use shallower angle
        optimal_angle = 45.0 - math.degrees(math.atan(abs(height_diff) / horizontal_dist)) / 2

    # Clamp angle
    optimal_angle = max(15.0, min(60.0, optimal_angle))

    # Calculate required speed
    angle_rad = math.radians(optimal_angle)
    sin_2theta = math.sin(2 * angle_rad)

    if sin_2theta > 0:
        required_speed = math.sqrt(horizontal_dist * g / sin_2theta)

        # Adjust for height
        if height_diff != 0:
            required_speed = math.sqrt(required_speed**2 + 2 * g * abs(height_diff))
    else:
        required_speed = 0.0

    # Calculate peak height
    vy = required_speed * math.sin(angle_rad)
    peak_height = start_pos[2] + vy**2 / (2 * g)

    # Check height constraint
    if max_height is not None and peak_height > max_height:
        # Need flatter trajectory
        # This is a simplification - real solution would iterate
        height_reduction = peak_height - max_height
        optimal_angle = max(15.0, optimal_angle - height_reduction * 2)

        # Recalculate
        angle_rad = math.radians(optimal_angle)
        sin_2theta = math.sin(2 * angle_rad)
        if sin_2theta > 0:
            required_speed = math.sqrt(horizontal_dist * g / sin_2theta)
            if height_diff != 0:
                required_speed = math.sqrt(required_speed**2 + 2 * g * abs(height_diff))

        vy = required_speed * math.sin(angle_rad)
        peak_height = start_pos[2] + vy**2 / (2 * g)

    # Calculate air time
    air_time = calculate_air_time(required_speed, optimal_angle, -height_diff)

    return {
        'distance': horizontal_dist,
        'height_diff': height_diff,
        'optimal_angle': optimal_angle,
        'required_speed': required_speed,
        'peak_height': peak_height,
        'air_time': air_time,
        'landing_speed': math.sqrt(
            (required_speed * math.cos(angle_rad))**2 +
            (required_speed * math.sin(angle_rad) - g * air_time)**2
        ),
    }


def check_safety_constraints(
    trajectory_params: Dict[str, Any],
    max_g: float = 5.0,
    max_height: float = 15.0,
    min_landing_zone: float = 3.0,
) -> Tuple[bool, List[str]]:
    """Check if trajectory meets safety constraints.

    Args:
        trajectory_params: Trajectory parameters from calculate_optimal_trajectory
        max_g: Maximum allowed G-force
        max_height: Maximum allowed height
        min_landing_zone: Minimum landing zone size

    Returns:
        Tuple of (is_safe, warnings)
    """
    is_safe = True
    warnings = []

    # Check height
    if trajectory_params.get('peak_height', 0) > max_height:
        warnings.append(f"Peak height {trajectory_params['peak_height']:.1f}m exceeds max {max_height}m")
        is_safe = False

    # Check speed
    if trajectory_params.get('required_speed', 0) > 50:
        warnings.append(f"Required speed {trajectory_params['required_speed']:.1f} m/s is very high")
        is_safe = False

    # Check landing speed
    landing_speed = trajectory_params.get('landing_speed', 0)
    impact_g = calculate_impact_g_force(landing_speed * 0.3)  # Estimate vertical component
    if impact_g > max_g:
        warnings.append(f"Landing G-force {impact_g:.1f}G exceeds max {max_g}G")
        is_safe = False

    # Check angle
    angle = trajectory_params.get('optimal_angle', 45)
    if angle > 50:
        warnings.append(f"Launch angle {angle:.1f}° is steep - difficult landing")
    elif angle < 20:
        warnings.append(f"Launch angle {angle:.1f}° is shallow - long distance needed")

    return is_safe, warnings
