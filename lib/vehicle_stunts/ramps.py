"""
Ramp Generation Module

Create and configure stunt ramps.

Phase 17.1: Ramp & Jump Generation (REQ-STUNT-02)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import math

from .types import (
    RampType,
    RampConfig,
    KickerConfig,
    TableConfig,
    HipConfig,
    QuarterPipeConfig,
    SpineConfig,
    RollerConfig,
    StepUpConfig,
    StepDownConfig,
)


# Predefined ramp presets
RAMP_PRESETS: Dict[str, RampConfig] = {
    # Beginner ramps
    "beginner_kicker": RampConfig(
        ramp_type=RampType.KICKER,
        width=4.0,
        height=1.0,
        length=3.0,
        angle=20.0,
    ),
    "beginner_table": RampConfig(
        ramp_type=RampType.TABLE,
        width=4.0,
        height=1.2,
        length=5.0,
        angle=20.0,
        table_length=2.0,
    ),

    # Intermediate ramps
    "intermediate_kicker": RampConfig(
        ramp_type=RampType.KICKER,
        width=5.0,
        height=1.8,
        length=5.0,
        angle=30.0,
    ),
    "intermediate_table": RampConfig(
        ramp_type=RampType.TABLE,
        width=5.0,
        height=2.0,
        length=8.0,
        angle=30.0,
        table_length=3.0,
    ),
    "hip_45": RampConfig(
        ramp_type=RampType.HIP,
        width=5.0,
        height=2.0,
        length=6.0,
        angle=30.0,
        hip_angle=45.0,
    ),

    # Advanced ramps
    "advanced_kicker": RampConfig(
        ramp_type=RampType.KICKER,
        width=6.0,
        height=2.5,
        length=6.0,
        angle=40.0,
    ),
    "pro_table": RampConfig(
        ramp_type=RampType.TABLE,
        width=6.0,
        height=2.5,
        length=10.0,
        angle=35.0,
        table_length=4.0,
    ),
    "spine_double": RampConfig(
        ramp_type=RampType.SPINE,
        width=5.0,
        height=2.5,
        length=4.0,
        angle=45.0,
    ),

    # Special purpose
    "quarter_pipe": RampConfig(
        ramp_type=RampType.QUARTER_PIPE,
        width=5.0,
        height=3.0,
        length=3.0,
        curve_radius=2.5,
    ),
    "wall_ride_45": RampConfig(
        ramp_type=RampType.WALL_RIDE,
        width=6.0,
        height=3.0,
        length=4.0,
        angle=45.0,
    ),
    "step_up_medium": RampConfig(
        ramp_type=RampType.STEP_UP,
        width=5.0,
        height=2.0,
        length=5.0,
        angle=35.0,
    ),
    "step_down_medium": RampConfig(
        ramp_type=RampType.STEP_DOWN,
        width=5.0,
        height=1.5,
        length=5.0,
        angle=25.0,
    ),

    # Roller sections
    "whoops_small": RampConfig(
        ramp_type=RampType.ROLLER,
        width=4.0,
        height=0.5,
        length=2.0,
    ),
    "whoops_large": RampConfig(
        ramp_type=RampType.ROLLER,
        width=5.0,
        height=0.8,
        length=3.0,
    ),
}


def get_ramp_preset(name: str) -> Optional[RampConfig]:
    """Get a ramp preset by name.

    Args:
        name: Preset name

    Returns:
        RampConfig or None if not found
    """
    return RAMP_PRESETS.get(name.lower())


def list_ramp_presets() -> List[str]:
    """List all available ramp presets.

    Returns:
        List of preset names
    """
    return list(RAMP_PRESETS.keys())


def create_ramp(
    ramp_type: RampType,
    width: float = 4.0,
    height: float = 2.0,
    length: float = 6.0,
    angle: float = 30.0,
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: float = 0.0,
    preset: Optional[str] = None,
    **kwargs
) -> RampConfig:
    """Create a ramp configuration.

    Args:
        ramp_type: Type of ramp
        width: Ramp width in meters
        height: Ramp height in meters
        length: Ramp length in meters
        angle: Launch angle in degrees
        location: Position in 3D space
        rotation: Rotation around Z axis in degrees
        preset: Optional preset name to use as base
        **kwargs: Additional configuration options

    Returns:
        RampConfig instance
    """
    if preset and preset.lower() in RAMP_PRESETS:
        config = RAMP_PRESETS[preset.lower()]
        # Override with provided values
        return RampConfig(
            ramp_type=config.ramp_type,
            width=width if width != 4.0 else config.width,
            height=height if height != 2.0 else config.height,
            length=length if length != 6.0 else config.length,
            angle=angle if angle != 30.0 else config.angle,
            curve_radius=config.curve_radius,
            transition_radius=config.transition_radius,
            table_length=config.table_length,
            hip_angle=config.hip_angle,
            surface_material=kwargs.get('surface_material', config.surface_material),
            friction=kwargs.get('friction', config.friction),
            location=location,
            rotation=rotation,
        )

    return RampConfig(
        ramp_type=ramp_type,
        width=width,
        height=height,
        length=length,
        angle=angle,
        curve_radius=kwargs.get('curve_radius'),
        transition_radius=kwargs.get('transition_radius', 2.0),
        table_length=kwargs.get('table_length', 3.0),
        hip_angle=kwargs.get('hip_angle', 45.0),
        surface_material=kwargs.get('surface_material', 'concrete'),
        friction=kwargs.get('friction', 0.8),
        location=location,
        rotation=rotation,
    )


def create_kicker(config: KickerConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a kicker ramp from KickerConfig.

    Args:
        config: KickerConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the kicker
    """
    ramp_type = RampType.KICKER
    if config.curve_type == "kinked" and config.kink_angle:
        ramp_type = RampType.KICKER_KINK

    return RampConfig(
        ramp_type=ramp_type,
        width=config.width,
        height=config.height,
        length=config.length,
        angle=config.angle,
        location=location,
    )


def create_table(config: TableConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a table jump from TableConfig.

    Args:
        config: TableConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the table
    """
    return RampConfig(
        ramp_type=RampType.TABLE,
        width=config.width,
        height=config.height,
        length=config.length,
        angle=config.angle,
        table_length=config.table_length,
        location=location,
    )


def create_hip(config: HipConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a hip jump from HipConfig.

    Args:
        config: HipConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the hip
    """
    return RampConfig(
        ramp_type=RampType.HIP,
        width=config.width,
        height=config.height,
        length=config.length,
        angle=config.angle,
        hip_angle=config.landing_angle,
        location=location,
    )


def create_quarter_pipe(config: QuarterPipeConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a quarter pipe from QuarterPipeConfig.

    Args:
        config: QuarterPipeConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the quarter pipe
    """
    return RampConfig(
        ramp_type=RampType.QUARTER_PIPE,
        width=config.width,
        height=config.height,
        length=config.radius,
        curve_radius=config.radius,
        location=location,
    )


def create_spine(config: SpineConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a spine ramp from SpineConfig.

    Args:
        config: SpineConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the spine
    """
    return RampConfig(
        ramp_type=RampType.SPINE,
        width=config.width,
        height=config.height,
        length=config.radius * 2 + config.deck_width,
        curve_radius=config.radius,
        location=location,
    )


def create_roller_section(config: RollerConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> List[RampConfig]:
    """Create a series of roller ramps.

    Args:
        config: RollerConfig instance
        location: Starting position

    Returns:
        List of RampConfig for each roller
    """
    rollers = []
    x, y, z = location

    for i in range(config.count):
        roller = RampConfig(
            ramp_type=RampType.ROLLER,
            width=config.width,
            height=config.height,
            length=config.length,
            location=(x + i * (config.length + config.spacing), y, z),
        )
        rollers.append(roller)

    return rollers


def create_step_up(config: StepUpConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a step-up jump from StepUpConfig.

    Args:
        config: StepUpConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the step-up
    """
    return RampConfig(
        ramp_type=RampType.STEP_UP,
        width=config.width,
        height=config.height,
        length=config.length,
        angle=config.angle,
        location=location,
    )


def create_step_down(config: StepDownConfig, location: Tuple[float, float, float] = (0, 0, 0)) -> RampConfig:
    """Create a step-down jump from StepDownConfig.

    Args:
        config: StepDownConfig instance
        location: Position in 3D space

    Returns:
        RampConfig for the step-down
    """
    return RampConfig(
        ramp_type=RampType.STEP_DOWN,
        width=config.width,
        height=config.height,
        length=config.length,
        angle=config.angle,
        location=location,
    )


def calculate_ramp_geometry(config: RampConfig) -> Dict[str, Any]:
    """Calculate detailed geometry for a ramp.

    Args:
        config: RampConfig instance

    Returns:
        Dictionary with geometry details
    """
    geometry = {
        'type': config.ramp_type.name,
        'dimensions': {
            'width': config.width,
            'height': config.height,
            'length': config.length,
        },
        'surface_area': 0.0,
        'volume': 0.0,
        'vertices': [],
    }

    if config.ramp_type == RampType.KICKER:
        # Simple wedge shape
        geometry['surface_area'] = config.width * config.length
        geometry['volume'] = 0.5 * config.width * config.height * config.length
        geometry['launch_angle'] = config.angle
        geometry['launch_height'] = config.height

    elif config.ramp_type == RampType.TABLE:
        # Wedge up + flat + wedge down
        up_area = config.width * config.up_length if hasattr(config, 'up_length') else config.width * config.length * 0.3
        table_area = config.width * config.table_length
        down_area = config.width * config.down_length if hasattr(config, 'down_length') else config.width * config.length * 0.3
        geometry['surface_area'] = up_area + table_area + down_area
        geometry['gap_distance'] = config.table_length

    elif config.ramp_type == RampType.QUARTER_PIPE:
        # Curved surface
        if config.curve_radius:
            arc_length = math.pi * config.curve_radius / 2  # quarter circle
            geometry['surface_area'] = config.width * arc_length
            geometry['curve_arc'] = 90.0  # degrees

    elif config.ramp_type == RampType.HIP:
        # Two-part landing
        geometry['landing_angle'] = config.hip_angle
        geometry['surface_area'] = config.width * config.length * 1.5  # approximate

    return geometry


def estimate_launch_speed(config: RampConfig, target_distance: float) -> float:
    """Estimate required launch speed for a ramp.

    Args:
        config: RampConfig instance
        target_distance: Target landing distance in meters

    Returns:
        Required speed in m/s
    """
    g = 9.81
    angle_rad = math.radians(config.angle)

    # Projectile range formula: R = v² * sin(2θ) / g
    # v = sqrt(R * g / sin(2θ))

    sin_2theta = math.sin(2 * angle_rad)
    if sin_2theta <= 0:
        return 0.0

    v_required = math.sqrt(target_distance * g / sin_2theta)

    # Add safety margin
    return v_required * 1.1


def estimate_jump_distance(config: RampConfig, speed: float) -> float:
    """Estimate jump distance for given speed.

    Args:
        config: RampConfig instance
        speed: Launch speed in m/s

    Returns:
        Estimated distance in meters
    """
    g = 9.81
    angle_rad = math.radians(config.angle)

    # R = v² * sin(2θ) / g
    distance = (speed ** 2) * math.sin(2 * angle_rad) / g

    # Add height factor
    height_bonus = config.height * 2  # approximate

    return distance + height_bonus
