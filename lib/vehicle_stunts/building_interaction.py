"""
Building Interaction Module

Detect and create rideable surfaces on buildings for stunts.

Phase 17.2: Building Interaction (REQ-STUNT-03)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import math

from .types import LandingZone


# Building interaction presets
BUILDING_PRESETS: Dict[str, Dict[str, Any]] = {
    "wall_ride_basic": {
        "height": 4.0,
        "length": 10.0,
        "angle": 45.0,
        "entry_speed": 20.0,
    },
    "wall_ride_steep": {
        "height": 6.0,
        "length": 8.0,
        "angle": 60.0,
        "entry_speed": 25.0,
    },
    "corner_bank": {
        "radius": 8.0,
        "angle": 30.0,
        "width": 6.0,
    },
    "roof_gap": {
        "gap_distance": 8.0,
        "height_diff": 2.0,
        "landing_area": 5.0,
    },
}


@dataclass
class RideableSurface:
    """A surface that can be ridden by a vehicle."""
    start_point: Tuple[float, float, float]
    end_point: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    width: float
    friction: float = 0.8
    surface_type: str = "concrete"
    min_speed: float = 15.0
    max_speed: float = 40.0


@dataclass
class WallRideConfig:
    """Configuration for a wall ride stunt."""
    start_height: float
    end_height: float
    length: float
    angle: float              # degrees from vertical
    width: float = 4.0
    entry_transition: float = 2.0  # meters
    exit_transition: float = 2.0


@dataclass
class CornerBankConfig:
    """Configuration for a corner bank stunt."""
    corner_radius: float
    bank_angle: float         # degrees
    bank_height: float
    arc_degrees: float = 90.0
    width: float = 5.0


def detect_rideable_surface(
    building_mesh: Any,
    min_area: float = 10.0,
    max_slope: float = 70.0,
    min_slope: float = 20.0,
) -> List[RideableSurface]:
    """Detect rideable surfaces on a building mesh.

    Args:
        building_mesh: Building mesh data
        min_area: Minimum surface area in m²
        max_slope: Maximum slope angle from horizontal
        min_slope: Minimum slope angle from horizontal

    Returns:
        List of rideable surfaces
    """
    # This would analyze mesh polygons in a real implementation
    # For now, return placeholder
    surfaces = []

    # Placeholder - in real implementation would:
    # 1. Iterate through mesh polygons
    # 2. Calculate face normal and slope angle
    # 3. Check if slope is within rideable range
    # 4. Calculate surface area
    # 5. Return qualifying surfaces

    return surfaces


def create_wall_ride(
    config: WallRideConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a wall ride stunt element.

    Args:
        config: Wall ride configuration
        location: Starting position
        direction: Direction angle in degrees

    Returns:
        Dictionary with wall ride data
    """
    angle_rad = math.radians(config.angle)
    dir_rad = math.radians(direction)

    # Calculate geometry
    horizontal_length = config.length * math.cos(angle_rad)
    vertical_rise = config.length * math.sin(angle_rad)

    # Start and end points
    start_x, start_y, start_z = location
    end_x = start_x + horizontal_length * math.cos(dir_rad)
    end_y = start_y + horizontal_length * math.sin(dir_rad)
    end_z = start_z + vertical_rise

    # Normal vector (perpendicular to surface)
    normal = (
        -math.sin(angle_rad) * math.cos(dir_rad),
        -math.sin(angle_rad) * math.sin(dir_rad),
        math.cos(angle_rad),
    )

    # Required entry speed
    # v = sqrt(2 * g * h / sin(2θ))
    g = 9.81
    min_speed = math.sqrt(2 * g * vertical_rise / math.sin(2 * angle_rad))

    return {
        'type': 'wall_ride',
        'config': config,
        'start': location,
        'end': (end_x, end_y, end_z),
        'normal': normal,
        'dimensions': {
            'length': config.length,
            'width': config.width,
            'height_gain': vertical_rise,
        },
        'physics': {
            'min_entry_speed': min_speed * 1.2,  # safety margin
            'optimal_speed': min_speed * 1.5,
            'max_safe_speed': min_speed * 2.0,
        },
        'surface': {
            'type': 'concrete',
            'friction': 0.7,
        },
    }


def create_corner_bank(
    config: CornerBankConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    start_direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a corner bank stunt element.

    Args:
        config: Corner bank configuration
        location: Starting position
        start_direction: Initial direction in degrees

    Returns:
        Dictionary with corner bank data
    """
    start_dir_rad = math.radians(start_direction)
    arc_rad = math.radians(config.arc_degrees)

    # Calculate arc length
    arc_length = config.corner_radius * arc_rad

    # Bank height based on angle
    bank_height = config.corner_radius * math.tan(math.radians(config.bank_angle))

    # Entry and exit points
    start_x, start_y, start_z = location
    mid_angle = start_dir_rad + arc_rad / 2
    end_dir = start_direction + config.arc_degrees

    end_x = start_x + config.corner_radius * (math.sin(math.radians(end_dir)) - math.sin(start_dir_rad))
    end_y = start_y + config.corner_radius * (math.cos(start_dir_rad) - math.cos(math.radians(end_dir)))
    end_z = start_z

    # Design speed for banked turn
    g = 9.81
    design_speed = math.sqrt(config.corner_radius * g * math.tan(math.radians(config.bank_angle)))

    return {
        'type': 'corner_bank',
        'config': config,
        'start': location,
        'end': (end_x, end_y, end_z),
        'center': (
            start_x - config.corner_radius * math.sin(start_dir_rad),
            start_y + config.corner_radius * math.cos(start_dir_rad),
            start_z,
        ),
        'arc': {
            'radius': config.corner_radius,
            'degrees': config.arc_degrees,
            'length': arc_length,
        },
        'bank': {
            'angle': config.bank_angle,
            'height': bank_height,
            'width': config.width,
        },
        'physics': {
            'design_speed': design_speed,
            'min_speed': design_speed * 0.7,
            'max_safe_speed': design_speed * 1.5,
        },
    }


def detect_landing_zones(
    building_heights: List[Tuple[float, float, float, float]],  # (x, y, z, area)
    vehicle_trajectory_end: Tuple[float, float, float],
    search_radius: float = 20.0,
    min_area: float = 20.0,
) -> List[LandingZone]:
    """Detect potential landing zones on buildings.

    Args:
        building_heights: List of building rooftops (x, y, z, area)
        vehicle_trajectory_end: Expected landing position
        search_radius: Search radius in meters
        min_area: Minimum landing area required

    Returns:
        List of suitable landing zones
    """
    zones = []
    tx, ty, tz = vehicle_trajectory_end

    for bx, by, bz, area in building_heights:
        # Check distance
        dist = math.sqrt((bx - tx)**2 + (by - ty)**2)
        if dist > search_radius:
            continue

        # Check area
        if area < min_area:
            continue

        # Check height difference (prefer lower or equal)
        height_diff = bz - tz
        if height_diff > 5.0:  # Landing too high
            continue

        # Calculate landing zone dimensions
        side = math.sqrt(area)
        zones.append(LandingZone(
            center=(bx, by, bz),
            width=side,
            length=side,
            slope_angle=0.0,
            surface_type="roof",
            is_clear=True,
        ))

    # Sort by distance from trajectory end
    zones.sort(key=lambda z: (
        (z.center[0] - tx)**2 + (z.center[1] - ty)**2
    ))

    return zones


def create_rooftop_gap(
    start_building: Tuple[float, float, float],
    end_building: Tuple[float, float, float],
    gap_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a rooftop gap jump configuration.

    Args:
        start_building: Start building position and height
        end_building: End building position and height
        gap_config: Optional gap configuration

    Returns:
        Dictionary with gap jump data
    """
    sx, sy, sz = start_building
    ex, ey, ez = end_building

    # Calculate gap parameters
    horizontal_dist = math.sqrt((ex - sx)**2 + (ey - sy)**2)
    height_diff = ez - sz

    # Required launch parameters
    g = 9.81
    optimal_angle = 35.0  # degrees

    if height_diff > 0:
        # Landing higher - need steeper angle
        optimal_angle = max(30.0, 45.0 - math.degrees(math.atan(height_diff / horizontal_dist)))
    elif height_diff < 0:
        # Landing lower - can use shallower angle
        optimal_angle = min(45.0, 30.0 + math.degrees(math.atan(abs(height_diff) / horizontal_dist)))

    angle_rad = math.radians(optimal_angle)
    required_speed = math.sqrt(horizontal_dist * g / math.sin(2 * angle_rad))

    # Adjust for height difference
    if height_diff != 0:
        required_speed = math.sqrt(required_speed**2 + 2 * g * abs(height_diff))

    return {
        'type': 'rooftop_gap',
        'start': start_building,
        'end': end_building,
        'gap': {
            'horizontal_distance': horizontal_dist,
            'height_difference': height_diff,
        },
        'launch': {
            'angle': optimal_angle,
            'speed': required_speed * 1.1,  # safety margin
        },
        'landing': {
            'zone_center': end_building,
            'zone_size': min(5.0, horizontal_dist * 0.2),
        },
    }


def analyze_building_for_stunts(
    building_data: Dict[str, Any],
    min_height: float = 3.0,
    min_surface: float = 10.0,
) -> List[Dict[str, Any]]:
    """Analyze a building for potential stunt opportunities.

    Args:
        building_data: Building geometry and property data
        min_height: Minimum height for stunts
        min_surface: Minimum surface area

    Returns:
        List of potential stunt configurations
    """
    opportunities = []

    height = building_data.get('height', 0)
    if height < min_height:
        return opportunities

    # Check for wall rides
    walls = building_data.get('walls', [])
    for wall in walls:
        wall_height = wall.get('height', 0)
        wall_length = wall.get('length', 0)
        wall_angle = wall.get('angle', 90)  # from horizontal

        # Wall ride opportunity
        if 30 <= (90 - wall_angle) <= 60:  # 30-60 degree bank
            opportunities.append({
                'type': 'wall_ride',
                'location': wall.get('center', (0, 0, 0)),
                'direction': wall.get('direction', 0),
                'config': WallRideConfig(
                    start_height=0,
                    end_height=wall_height,
                    length=wall_length,
                    angle=90 - wall_angle,
                ),
            })

    # Check for rooftop landing
    roof = building_data.get('roof', {})
    roof_area = roof.get('area', 0)
    if roof_area >= min_surface:
        opportunities.append({
            'type': 'landing_zone',
            'location': roof.get('center', (0, 0, height)),
            'config': {
                'width': math.sqrt(roof_area),
                'length': math.sqrt(roof_area),
                'height': height,
            },
        })

    # Check for corner banks
    corners = building_data.get('corners', [])
    for corner in corners:
        if corner.get('has_bank', False):
            opportunities.append({
                'type': 'corner_bank',
                'location': corner.get('position', (0, 0, 0)),
                'config': CornerBankConfig(
                    corner_radius=corner.get('radius', 8.0),
                    bank_angle=corner.get('bank_angle', 30.0),
                    bank_height=corner.get('bank_height', 2.0),
                ),
            })

    return opportunities


def calculate_wall_ride_physics(
    speed: float,
    angle: float,
    length: float,
    vehicle_mass: float = 1500.0,
) -> Dict[str, float]:
    """Calculate physics for a wall ride.

    Args:
        speed: Entry speed in m/s
        angle: Wall angle from horizontal in degrees
        length: Wall ride length in meters
        vehicle_mass: Vehicle mass in kg

    Returns:
        Dictionary with physics values
    """
    g = 9.81
    angle_rad = math.radians(angle)

    # Time on wall
    time_on_wall = length / speed

    # Normal force (perpendicular to wall)
    normal_force = vehicle_mass * g * math.cos(angle_rad)

    # Friction force (parallel to wall, opposing gravity component)
    friction_coeff = 0.7
    friction_force = friction_coeff * normal_force

    # Gravity component along wall
    gravity_component = vehicle_mass * g * math.sin(angle_rad)

    # Net acceleration along wall
    if friction_force >= gravity_component:
        # Vehicle can stick to wall
        net_acceleration = 0
        can_complete = True
    else:
        # Vehicle will slide down
        net_acceleration = (gravity_component - friction_force) / vehicle_mass
        can_complete = speed**2 / (2 * net_acceleration) >= length if net_acceleration > 0 else True

    # Required minimum speed to complete wall ride
    min_speed = math.sqrt(2 * g * length * math.sin(angle_rad))

    return {
        'time_on_wall': time_on_wall,
        'normal_force': normal_force,
        'friction_force': friction_force,
        'gravity_component': gravity_component,
        'net_acceleration': net_acceleration,
        'can_complete': can_complete,
        'min_speed': min_speed * 1.2,  # safety margin
        'exit_speed': speed * 0.9,  # approximate speed loss
    }
