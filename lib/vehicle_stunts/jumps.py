"""
Jump Trajectory Module

Calculate and visualize vehicle jump trajectories.

Phase 17.1: Ramp & Jump Generation (REQ-STUNT-02)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import math

from .types import (
    TrajectoryPoint,
    LandingZone,
    RampConfig,
    RampType,
    LaunchParams,
    TrajectoryResult,
)


# Predefined jump presets
JUMP_PRESETS: Dict[str, Dict[str, Any]] = {
    "small_jump": {
        "distance": 5.0,
        "height": 1.0,
        "speed": 15.0,
        "angle": 25.0,
    },
    "medium_jump": {
        "distance": 10.0,
        "height": 2.0,
        "speed": 20.0,
        "angle": 30.0,
    },
    "large_jump": {
        "distance": 20.0,
        "height": 4.0,
        "speed": 30.0,
        "angle": 35.0,
    },
    "long_jump": {
        "distance": 30.0,
        "height": 3.0,
        "speed": 35.0,
        "angle": 25.0,
    },
    "high_jump": {
        "distance": 8.0,
        "height": 6.0,
        "speed": 25.0,
        "angle": 45.0,
    },
}

# Physics constants
GRAVITY = 9.81  # m/s²
AIR_DENSITY = 1.225  # kg/m³
DRAG_COEFFICIENT = 0.35  # typical car
FRONTAL_AREA = 2.5  # m² typical car


def calculate_trajectory(
    launch_params: LaunchParams,
    ramp_config: Optional[RampConfig] = None,
    frame_rate: int = 24,
    include_drag: bool = False,
    vehicle_mass: float = 1500.0,
) -> TrajectoryResult:
    """Calculate complete jump trajectory.

    Args:
        launch_params: Launch speed, angle, height
        ramp_config: Optional ramp configuration
        frame_rate: Frames per second
        include_drag: Whether to include air resistance
        vehicle_mass: Vehicle mass in kg

    Returns:
        TrajectoryResult with all trajectory points
    """
    g = GRAVITY
    v0 = launch_params.speed
    angle_rad = math.radians(launch_params.angle)
    h0 = launch_params.height

    # Initial velocity components
    vx = v0 * math.cos(angle_rad)
    vy = v0 * math.sin(angle_rad)
    vz = 0.0  # No lateral velocity initially

    # Calculate flight time (without drag)
    # h = h0 + vy*t - 0.5*g*t²
    # Solving for h = 0: t = (vy + sqrt(vy² + 2*g*h0)) / g
    discriminant = vy**2 + 2 * g * h0
    if discriminant < 0:
        # Cannot reach ground (shouldn't happen)
        t_flight = 0
    else:
        t_flight = (vy + math.sqrt(discriminant)) / g

    # Calculate peak height
    t_peak = vy / g
    peak_height = h0 + vy * t_peak - 0.5 * g * t_peak**2

    # Calculate horizontal distance
    horizontal_distance = vx * t_flight

    # Generate trajectory points
    points: List[TrajectoryPoint] = []
    dt = 1.0 / frame_rate
    t = 0.0
    frame = 0

    max_g_force = 1.0
    warnings: List[str] = []

    while t <= t_flight + dt:
        # Position
        x = vx * t
        y = h0 + vy * t - 0.5 * g * t**2
        z = vz * t

        # Velocity
        current_vx = vx
        current_vy = vy - g * t
        current_vz = vz

        if include_drag:
            # Simple drag model
            v_mag = math.sqrt(current_vx**2 + current_vy**2 + current_vz**2)
            if v_mag > 0:
                drag_force = 0.5 * AIR_DENSITY * DRAG_COEFFICIENT * FRONTAL_AREA * v_mag**2
                drag_acc = drag_force / vehicle_mass
                # Apply drag opposite to velocity
                current_vx -= (current_vx / v_mag) * drag_acc * dt
                current_vy -= (current_vy / v_mag) * drag_acc * dt

        # Rotation (simplified - vehicle follows trajectory angle)
        pitch = -math.atan2(current_vy, current_vx)
        roll = 0.0
        yaw = 0.0

        # Apply rotation rate from launch params
        rotation_rate = launch_params.rotation_rate
        roll += math.radians(rotation_rate[0] * t)
        pitch += math.radians(rotation_rate[1] * t)
        yaw += math.radians(rotation_rate[2] * t)

        # Determine phase
        if t < 0.1:
            phase = "launch"
        elif y > peak_height * 0.9:
            phase = "flight"
        elif t > t_flight - 0.2:
            phase = "landing"
        else:
            phase = "flight"

        point = TrajectoryPoint(
            frame=frame,
            position=(x, z, max(0, y)),  # Z-up convention
            velocity=(current_vx, current_vz, current_vy),
            rotation=(roll, pitch, yaw),
            angular_velocity=rotation_rate,
            phase=phase,
        )
        points.append(point)

        t += dt
        frame += 1

    # Landing velocity
    landing_vx = vx
    landing_vy = vy - g * t_flight
    landing_vz = vz
    landing_velocity = (landing_vx, landing_vz, landing_vy)

    # Calculate landing G-force
    landing_speed = math.sqrt(landing_vx**2 + landing_vy**2 + landing_vz**2) if landing_vz else landing_vy
    # G = v² / (2 * g * compression_distance), assume 0.3m compression
    landing_g = (landing_speed**2) / (2 * g * 0.3) / g
    max_g_force = max(1.0, landing_g)

    # Safety check
    is_safe = True
    if max_g_force > 5.0:
        warnings.append(f"High landing G-force: {max_g_force:.1f}G")
        is_safe = max_g_force < 8.0
    if peak_height > 10.0:
        warnings.append(f"Very high jump: {peak_height:.1f}m")
    if horizontal_distance > 50.0:
        warnings.append(f"Long distance jump: {horizontal_distance:.1f}m")

    return TrajectoryResult(
        launch_params=launch_params,
        points=points,
        peak_height=peak_height,
        horizontal_distance=horizontal_distance,
        air_time=t_flight,
        landing_velocity=landing_velocity,
        max_g_force=max_g_force,
        is_safe=is_safe,
        warnings=warnings,
    )


def generate_landing_zone(
    trajectory: TrajectoryResult,
    width: float = 5.0,
    length: float = 10.0,
    slope_angle: float = -5.0,
) -> LandingZone:
    """Generate landing zone from trajectory.

    Args:
        trajectory: Calculated trajectory
        width: Landing zone width
        length: Landing zone length
        slope_angle: Landing slope angle (negative = downhill)

    Returns:
        LandingZone configuration
    """
    # Find landing point
    landing_point = None
    for point in reversed(trajectory.points):
        if point.phase == "landing":
            landing_point = point
            break

    if landing_point is None:
        landing_point = trajectory.points[-1]

    center = landing_point.position

    return LandingZone(
        center=center,
        width=width,
        length=length,
        slope_angle=slope_angle,
        surface_type="packed_dirt",
        is_clear=True,
        obstacles=[],
    )


def visualize_trajectory(
    trajectory: TrajectoryResult,
    style: str = "arc",
    resolution: int = 50,
) -> Dict[str, Any]:
    """Generate visualization data for trajectory.

    Args:
        trajectory: Calculated trajectory
        style: Visualization style (arc, points, curve)
        resolution: Number of points for curve

    Returns:
        Dictionary with visualization data
    """
    viz_data = {
        'style': style,
        'points': [],
        'arc': {},
        'bounds': {
            'min': (float('inf'), float('inf'), float('inf')),
            'max': (float('-inf'), float('-inf'), float('-inf')),
        },
        'markers': [],
    }

    # Sample points
    step = max(1, len(trajectory.points) // resolution)
    sampled_points = trajectory.points[::step]

    for point in sampled_points:
        viz_data['points'].append({
            'frame': point.frame,
            'position': point.position,
            'velocity': point.velocity,
            'phase': point.phase,
        })

        # Update bounds
        for i in range(3):
            if point.position[i] < viz_data['bounds']['min'][i]:
                viz_data['bounds']['min'] = (
                    min(viz_data['bounds']['min'][0], point.position[0]),
                    min(viz_data['bounds']['min'][1], point.position[1]),
                    min(viz_data['bounds']['min'][2], point.position[2]),
                )
            if point.position[i] > viz_data['bounds']['max'][i]:
                viz_data['bounds']['max'] = (
                    max(viz_data['bounds']['max'][0], point.position[0]),
                    max(viz_data['bounds']['max'][1], point.position[1]),
                    max(viz_data['bounds']['max'][2], point.position[2]),
                )

    # Arc visualization
    if style == "arc" and len(viz_data['points']) >= 3:
        start = viz_data['points'][0]['position']
        mid = viz_data['points'][len(viz_data['points']) // 2]['position']
        end = viz_data['points'][-1]['position']

        viz_data['arc'] = {
            'start': start,
            'peak': mid,
            'end': end,
            'peak_height': trajectory.peak_height,
            'distance': trajectory.horizontal_distance,
        }

    # Add markers for key points
    viz_data['markers'].append({
        'type': 'launch',
        'position': trajectory.points[0].position if trajectory.points else (0, 0, 0),
        'label': f"Launch: {trajectory.launch_params.speed:.1f} m/s",
    })

    viz_data['markers'].append({
        'type': 'peak',
        'position': viz_data['arc'].get('peak', (0, 0, 0)),
        'label': f"Peak: {trajectory.peak_height:.1f}m",
    })

    viz_data['markers'].append({
        'type': 'landing',
        'position': trajectory.points[-1].position if trajectory.points else (0, 0, 0),
        'label': f"Distance: {trajectory.horizontal_distance:.1f}m",
    })

    return viz_data


def calculate_optimal_launch_angle(distance: float, height_diff: float = 0.0) -> float:
    """Calculate optimal launch angle for a given distance.

    Args:
        distance: Horizontal distance to target
        height_diff: Height difference (positive = landing higher)

    Returns:
        Optimal angle in degrees
    """
    # For flat ground, optimal is 45 degrees
    # For height difference, we adjust

    if abs(height_diff) < 0.1:
        return 45.0

    # With height difference:
    # θ = atan((v² ± sqrt(v⁴ - g(gx² + 2hv²))) / (gx))
    # Simplified approximation:
    angle = 45.0 - math.degrees(math.atan(height_diff / distance)) / 2

    return max(15.0, min(60.0, angle))


def calculate_required_speed(
    distance: float,
    angle: float,
    height_diff: float = 0.0,
) -> float:
    """Calculate required launch speed for a jump.

    Args:
        distance: Horizontal distance in meters
        angle: Launch angle in degrees
        height_diff: Height difference (positive = landing higher)

    Returns:
        Required speed in m/s
    """
    g = GRAVITY
    angle_rad = math.radians(angle)

    sin_theta = math.sin(angle_rad)
    cos_theta = math.cos(angle_rad)
    sin_2theta = math.sin(2 * angle_rad)

    if sin_2theta <= 0:
        return 0.0

    # Range formula with height difference:
    # d = (v² * sin(2θ)) / (g * cos(φ)) where φ is slope
    # Simplified: v = sqrt(d * g / sin(2θ))

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

    return v_adjusted


def calculate_air_time(speed: float, angle: float, height: float = 0.0) -> float:
    """Calculate air time for a jump.

    Args:
        speed: Launch speed in m/s
        angle: Launch angle in degrees
        height: Launch height in meters

    Returns:
        Air time in seconds
    """
    g = GRAVITY
    angle_rad = math.radians(angle)

    vy = speed * math.sin(angle_rad)

    # Time to reach ground: t = (vy + sqrt(vy² + 2gh)) / g
    discriminant = vy**2 + 2 * g * height

    if discriminant < 0:
        return 0.0

    return (vy + math.sqrt(discriminant)) / g


def find_safe_landing_zones(
    trajectory: TrajectoryResult,
    obstacles: List[Tuple[float, float, float, float]],  # (x, y, z, radius)
    search_radius: float = 10.0,
) -> List[LandingZone]:
    """Find safe landing zones avoiding obstacles.

    Args:
        trajectory: Calculated trajectory
        obstacles: List of obstacle positions and radii
        search_radius: Search radius around landing point

    Returns:
        List of safe landing zones
    """
    landing_pos = trajectory.points[-1].position if trajectory.points else (0, 0, 0)
    zones = []

    # Check area around predicted landing
    for dx in [-search_radius, 0, search_radius]:
        for dy in [-search_radius, 0, search_radius]:
            center = (
                landing_pos[0] + dx,
                landing_pos[1] + dy,
                landing_pos[2],
            )

            # Check if clear of obstacles
            is_clear = True
            for obs_x, obs_y, obs_z, obs_radius in obstacles:
                dist = math.sqrt(
                    (center[0] - obs_x)**2 +
                    (center[1] - obs_y)**2
                )
                if dist < obs_radius + 3.0:  # 3m safety margin
                    is_clear = False
                    break

            if is_clear:
                zones.append(LandingZone(
                    center=center,
                    width=5.0,
                    length=10.0,
                    slope_angle=-5.0,
                    is_clear=True,
                ))

    return zones
