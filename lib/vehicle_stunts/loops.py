"""
Loop & Curve Generation Module

Create loop-the-loops, banked turns, and curved stunt elements.

Phase 17.3: Loop & Curve Generation (REQ-STUNT-04)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import math

from .types import (
    LoopType,
    LoopConfig,
    BankedTurnConfig,
    HalfPipeConfig,
    WaveConfig,
    BarrelRollConfig,
)


# Loop presets
LOOP_PRESETS: Dict[str, LoopConfig] = {
    "small_loop": LoopConfig(
        loop_type=LoopType.CIRCULAR,
        radius=4.0,
        width=4.0,
    ),
    "medium_loop": LoopConfig(
        loop_type=LoopType.CIRCULAR,
        radius=6.0,
        width=5.0,
    ),
    "large_loop": LoopConfig(
        loop_type=LoopType.CIRCULAR,
        radius=8.0,
        width=6.0,
    ),
    "clothoid_loop": LoopConfig(
        loop_type=LoopType.CLOTHOID,
        radius=6.0,
        width=5.0,
        clothoid_param=0.5,
    ),
    "egg_loop": LoopConfig(
        loop_type=LoopType.EGG,
        radius=5.0,
        width=5.0,
        height_ratio=1.3,
    ),
    "helix_double": LoopConfig(
        loop_type=LoopType.HELIX,
        radius=6.0,
        width=5.0,
    ),
}

# Banked turn presets
TURN_PRESETS: Dict[str, BankedTurnConfig] = {
    "gentle_turn": BankedTurnConfig(
        radius=20.0,
        angle=20.0,
        arc_degrees=45.0,
    ),
    "medium_turn": BankedTurnConfig(
        radius=15.0,
        angle=35.0,
        arc_degrees=90.0,
    ),
    "tight_turn": BankedTurnConfig(
        radius=10.0,
        angle=45.0,
        arc_degrees=90.0,
    ),
    "hairpin": BankedTurnConfig(
        radius=8.0,
        angle=50.0,
        arc_degrees=180.0,
    ),
}

# Half-pipe presets
HALFPIPE_PRESETS: Dict[str, HalfPipeConfig] = {
    "minipipe": HalfPipeConfig(
        width=6.0,
        height=2.0,
        radius=1.5,
        length=12.0,
    ),
    "standard": HalfPipeConfig(
        width=8.0,
        height=3.0,
        radius=2.5,
        length=20.0,
    ),
    "mega": HalfPipeConfig(
        width=10.0,
        height=4.0,
        radius=3.0,
        length=30.0,
    ),
}


def create_loop(
    config: LoopConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a loop stunt element.

    Args:
        config: Loop configuration
        location: Base position
        direction: Direction angle in degrees

    Returns:
        Dictionary with loop geometry and physics
    """
    g = 9.81
    dir_rad = math.radians(direction)

    # Calculate geometry based on loop type
    if config.loop_type == LoopType.CIRCULAR:
        geometry = _create_circular_loop_geometry(config, location, dir_rad)
    elif config.loop_type == LoopType.CLOTHOID:
        geometry = _create_clothoid_loop_geometry(config, location, dir_rad)
    elif config.loop_type == LoopType.EGG:
        geometry = _create_egg_loop_geometry(config, location, dir_rad)
    elif config.loop_type == LoopType.HELIX:
        geometry = _create_helix_loop_geometry(config, location, dir_rad)
    else:
        geometry = _create_circular_loop_geometry(config, location, dir_rad)

    # Calculate physics
    min_speed = config.get_min_speed()

    # Entry and exit points
    entry_point = (
        location[0] - config.entry_length * math.cos(dir_rad),
        location[1] - config.entry_length * math.sin(dir_rad),
        location[2],
    )
    exit_point = (
        location[0] + config.exit_length * math.cos(dir_rad),
        location[1] + config.exit_length * math.sin(dir_rad),
        location[2],
    )

    return {
        'type': 'loop',
        'loop_type': config.loop_type.name,
        'config': config,
        'location': location,
        'direction': direction,
        'geometry': geometry,
        'entry': entry_point,
        'exit': exit_point,
        'physics': {
            'min_entry_speed': min_speed,
            'optimal_speed': min_speed * 1.2,
            'max_safe_speed': min_speed * 1.8,
            'max_g_force': (min_speed * 1.2)**2 / (config.radius * g),
        },
        'dimensions': {
            'radius': config.radius,
            'width': config.width,
            'height': config.radius * 2 * config.height_ratio if config.loop_type == LoopType.EGG else config.radius * 2,
            'total_length': config.entry_length + geometry.get('arc_length', math.pi * config.radius) + config.exit_length,
        },
    }


def _create_circular_loop_geometry(
    config: LoopConfig,
    location: Tuple[float, float, float],
    dir_rad: float,
) -> Dict[str, Any]:
    """Create circular loop geometry."""
    radius = config.radius
    arc_length = 2 * math.pi * radius

    # Center of loop
    center = (
        location[0],
        location[1],
        location[2] + radius,
    )

    return {
        'shape': 'circular',
        'center': center,
        'radius': radius,
        'arc_length': arc_length,
        'points': _generate_loop_points(config, location, dir_rad),
    }


def _create_clothoid_loop_geometry(
    config: LoopConfig,
    location: Tuple[float, float, float],
    dir_rad: float,
) -> Dict[str, Any]:
    """Create clothoid (teardrop) loop geometry."""
    # Clothoid has tighter radius at top
    # A = L * R where A is clothoid parameter
    radius = config.radius
    a = config.clothoid_param

    # Approximate arc length
    arc_length = math.pi * radius * 1.2  # slightly longer than circle

    center = (
        location[0],
        location[1],
        location[2] + radius * 0.9,  # slightly lower center
    )

    return {
        'shape': 'clothoid',
        'center': center,
        'radius': radius,
        'clothoid_param': a,
        'arc_length': arc_length,
        'points': _generate_loop_points(config, location, dir_rad),
    }


def _create_egg_loop_geometry(
    config: LoopConfig,
    location: Tuple[float, float, float],
    dir_rad: float,
) -> Dict[str, Any]:
    """Create egg-shaped loop geometry."""
    radius = config.radius
    height_ratio = config.height_ratio

    # Egg is taller than wide
    height = radius * 2 * height_ratio
    width = radius * 2

    arc_length = math.pi * (1.5 * (radius + radius * height_ratio) - math.sqrt(radius * radius * height_ratio))

    center = (
        location[0],
        location[1],
        location[2] + height / 2,
    )

    return {
        'shape': 'egg',
        'center': center,
        'radius': radius,
        'height': height,
        'width': width,
        'arc_length': arc_length,
        'points': _generate_loop_points(config, location, dir_rad),
    }


def _create_helix_loop_geometry(
    config: LoopConfig,
    location: Tuple[float, float, float],
    dir_rad: float,
) -> Dict[str, Any]:
    """Create helix (spiral) loop geometry."""
    radius = config.radius
    # Double rotation helix
    arc_length = 4 * math.pi * radius

    center = (
        location[0],
        location[1],
        location[2] + radius,
    )

    return {
        'shape': 'helix',
        'center': center,
        'radius': radius,
        'rotations': 2,
        'arc_length': arc_length,
        'points': _generate_loop_points(config, location, dir_rad, rotations=2),
    }


def _generate_loop_points(
    config: LoopConfig,
    location: Tuple[float, float, float],
    dir_rad: float,
    num_points: int = 36,
    rotations: int = 1,
) -> List[Tuple[float, float, float]]:
    """Generate points along loop path."""
    points = []

    for i in range(num_points * rotations):
        t = (i / num_points) * 2 * math.pi * rotations

        # Parametric position on loop
        x = location[0]
        y = location[1] + config.radius * math.sin(t)
        z = location[2] + config.radius * (1 - math.cos(t))

        # Rotate by direction
        rx = location[0] + (x - location[0]) * math.cos(dir_rad) - (y - location[1]) * math.sin(dir_rad)
        ry = location[1] + (x - location[0]) * math.sin(dir_rad) + (y - location[1]) * math.cos(dir_rad)

        points.append((rx, ry, z))

    return points


def create_banked_turn(
    config: BankedTurnConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    start_direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a banked turn stunt element.

    Args:
        config: Banked turn configuration
        location: Starting position
        start_direction: Initial direction in degrees

    Returns:
        Dictionary with turn geometry and physics
    """
    g = 9.81
    design_speed = config.get_design_speed()

    # Calculate turn geometry
    arc_length = config.radius * math.radians(config.arc_degrees)

    # Entry and exit points
    start_rad = math.radians(start_direction)
    end_rad = math.radians(start_direction + config.arc_degrees)

    entry_point = (
        location[0] - config.entry_length * math.cos(start_rad),
        location[1] - config.entry_length * math.sin(start_rad),
        location[2],
    )

    exit_x = location[0] + config.radius * (math.sin(end_rad) - math.sin(start_rad))
    exit_y = location[1] + config.radius * (math.cos(start_rad) - math.cos(end_rad))

    exit_point = (exit_x, exit_y, location[2])

    # Center of turn arc
    center = (
        location[0] - config.radius * math.sin(start_rad),
        location[1] + config.radius * math.cos(start_rad),
        location[2],
    )

    # Banking height
    bank_height = config.width * math.tan(math.radians(config.angle)) / 2

    return {
        'type': 'banked_turn',
        'config': config,
        'location': location,
        'start_direction': start_direction,
        'entry': entry_point,
        'exit': exit_point,
        'center': center,
        'geometry': {
            'radius': config.radius,
            'arc_degrees': config.arc_degrees,
            'arc_length': arc_length,
            'bank_angle': config.angle,
            'bank_height': bank_height,
            'width': config.width,
        },
        'physics': {
            'design_speed': design_speed,
            'min_speed': design_speed * 0.6,
            'max_safe_speed': design_speed * 1.5,
            'lateral_g': design_speed**2 / (config.radius * g),
        },
        'points': _generate_turn_points(config, center, start_rad),
    }


def _generate_turn_points(
    config: BankedTurnConfig,
    center: Tuple[float, float, float],
    start_rad: float,
    num_points: int = 20,
) -> List[Tuple[float, float, float]]:
    """Generate points along turn path."""
    points = []
    arc_rad = math.radians(config.arc_degrees)

    for i in range(num_points + 1):
        t = i / num_points
        angle = start_rad + arc_rad * t

        x = center[0] + config.radius * math.sin(angle)
        y = center[1] - config.radius * math.cos(angle)
        z = center[2]

        points.append((x, y, z))

    return points


def create_half_pipe(
    config: HalfPipeConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a half-pipe stunt element.

    Args:
        config: Half-pipe configuration
        location: Starting position
        direction: Direction angle in degrees

    Returns:
        Dictionary with half-pipe geometry
    """
    g = 9.81

    # Calculate min speed to reach top
    min_speed = math.sqrt(2 * g * config.height)

    # Entry and exit points (same for half-pipe)
    dir_rad = math.radians(direction)
    entry_point = location
    exit_point = (
        location[0] + config.length * math.cos(dir_rad),
        location[1] + config.length * math.sin(dir_rad),
        location[2],
    )

    return {
        'type': 'half_pipe',
        'config': config,
        'location': location,
        'direction': direction,
        'entry': entry_point,
        'exit': exit_point,
        'geometry': {
            'width': config.width,
            'height': config.height,
            'length': config.length,
            'radius': config.radius,
            'deck_width': config.deck_width,
            'flat_width': config.width - 2 * config.radius,
        },
        'physics': {
            'min_speed_to_top': min_speed,
            'optimal_speed': min_speed * 1.3,
            'max_airtime': 2 * min_speed / g,
        },
        'cross_section': _generate_halfpipe_cross_section(config),
    }


def _generate_halfpipe_cross_section(
    config: HalfPipeConfig,
    num_points: int = 20,
) -> List[Tuple[float, float]]:
    """Generate half-pipe cross-section points."""
    points = []

    # Left deck
    points.append((-config.width/2 - config.deck_width, config.height))
    points.append((-config.width/2, config.height))

    # Left transition
    for i in range(num_points // 2):
        t = i / (num_points // 2 - 1)
        angle = math.pi / 2 * (1 - t)
        x = -config.width/2 + config.radius + config.radius * math.cos(angle)
        z = config.height - config.radius + config.radius * math.sin(angle)
        points.append((x, z))

    # Flat bottom
    points.append((0, 0))

    # Right transition
    for i in range(num_points // 2):
        t = i / (num_points // 2 - 1)
        angle = math.pi / 2 * t
        x = config.width/2 - config.radius + config.radius * math.cos(angle)
        z = config.height - config.radius + config.radius * math.sin(angle)
        points.append((x, z))

    # Right deck
    points.append((config.width/2, config.height))
    points.append((config.width/2 + config.deck_width, config.height))

    return points


def create_wave(
    config: WaveConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a wave/rolling section.

    Args:
        config: Wave configuration
        location: Starting position
        direction: Direction angle in degrees

    Returns:
        Dictionary with wave geometry
    """
    dir_rad = math.radians(direction)

    # Total length
    total_length = config.wavelength * config.count

    # End point
    end_point = (
        location[0] + total_length * math.cos(dir_rad),
        location[1] + total_length * math.sin(dir_rad),
        location[2],
    )

    return {
        'type': 'wave',
        'config': config,
        'location': location,
        'direction': direction,
        'entry': location,
        'exit': end_point,
        'geometry': {
            'amplitude': config.amplitude,
            'wavelength': config.wavelength,
            'count': config.count,
            'total_length': total_length,
            'width': config.width,
        },
        'points': _generate_wave_points(config, location, dir_rad),
    }


def _generate_wave_points(
    config: WaveConfig,
    location: Tuple[float, float, float],
    dir_rad: float,
    points_per_wave: int = 10,
) -> List[Tuple[float, float, float]]:
    """Generate points along wave path."""
    points = []
    total_points = points_per_wave * config.count

    for i in range(total_points + 1):
        t = i / total_points
        x_local = t * config.wavelength * config.count
        z_local = config.amplitude * math.sin(2 * math.pi * t * config.count + config.phase)

        # Rotate to direction
        x = location[0] + x_local * math.cos(dir_rad)
        y = location[1] + x_local * math.sin(dir_rad)
        z = location[2] + z_local

        points.append((x, y, z))

    return points


def create_barrel_roll(
    config: BarrelRollConfig,
    location: Tuple[float, float, float] = (0, 0, 0),
    direction: float = 0.0,
) -> Dict[str, Any]:
    """Create a barrel roll section.

    Args:
        config: Barrel roll configuration
        location: Starting position
        direction: Direction angle in degrees

    Returns:
        Dictionary with barrel roll geometry
    """
    dir_rad = math.radians(direction)

    # End point
    end_point = (
        location[0] + config.length * math.cos(dir_rad),
        location[1] + config.length * math.sin(dir_rad),
        location[2],
    )

    # Roll rate (degrees per meter)
    roll_rate = (config.rotations * 360) / config.length

    return {
        'type': 'barrel_roll',
        'config': config,
        'location': location,
        'direction': direction,
        'entry': location,
        'exit': end_point,
        'geometry': {
            'length': config.length,
            'width': config.width,
            'radius': config.radius,
            'rotations': config.rotations,
            'roll_rate': roll_rate,
        },
        'physics': {
            'required_speed': config.length / 2.0,  # 2 seconds to complete
            'roll_angular_velocity': config.rotations * 360,  # deg/s
        },
    }


def get_loop_preset(name: str) -> Optional[LoopConfig]:
    """Get a loop preset by name."""
    return LOOP_PRESETS.get(name.lower())


def get_turn_preset(name: str) -> Optional[BankedTurnConfig]:
    """Get a turn preset by name."""
    return TURN_PRESETS.get(name.lower())


def get_halfpipe_preset(name: str) -> Optional[HalfPipeConfig]:
    """Get a half-pipe preset by name."""
    return HALFPIPE_PRESETS.get(name.lower())


def list_loop_presets() -> List[str]:
    """List all loop presets."""
    return list(LOOP_PRESETS.keys())


def list_turn_presets() -> List[str]:
    """List all turn presets."""
    return list(TURN_PRESETS.keys())


def list_halfpipe_presets() -> List[str]:
    """List all half-pipe presets."""
    return list(HALFPIPE_PRESETS.keys())
