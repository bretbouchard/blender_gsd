"""
Steering System - Steering Wheel to Tire Connection

Provides steering column rig with proper ratio, Ackermann geometry,
and auto-steering from path following.

Usage:
    from lib.animation.vehicle.steering import (
        SteeringColumn, SteeringConfig, setup_steering
    )

    # Create steering rig
    column = SteeringColumn()
    column.create_rig(vehicle)

    # Connect to front wheels with 15:1 ratio
    column.connect_to_wheels(wheel_FL, wheel_FR, ratio=15.0)

    # Add auto-steering from path
    column.add_path_steering(path_curve, look_ahead=5.0)
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos, atan, tan, degrees, radians
from mathutils import Vector, Matrix
from enum import Enum


class SteeringStyle(Enum):
    STANDARD = "standard"       # Regular car
    SPORT = "sport"             # Quick ratio
    TRUCK = "truck"             # Slow ratio, many turns
    RACING = "racing"           # Very quick, few turns
    OFFROAD = "offroad"         # Variable ratio


@dataclass
class SteeringConfig:
    """Configuration for steering system."""

    # === RATIO ===
    steering_ratio: float = 15.0      # Steering wheel : wheel angle
                                       # 15:1 = 540° wheel = 36° tire
    lock_to_lock: float = 2.5         # Turns lock to lock

    # === GEOMETRY ===
    ackermann_enabled: bool = True    # Use Ackermann geometry
    ackermann_percent: float = 100.0  # 100% = perfect Ackermann

    # === LIMITS ===
    max_wheel_angle: float = 35.0     # Degrees (max tire angle)

    # === ASSIST ===
    power_steering: bool = True
    steering_effort: float = 0.3      # 0 = very light, 1 = heavy

    # === STYLE ===
    steering_style: SteeringStyle = SteeringStyle.STANDARD

    @property
    def max_steering_wheel_rotation(self) -> float:
        """Maximum steering wheel rotation in radians."""
        return self.max_wheel_angle * self.steering_ratio * (pi / 180)

    @property
    def degrees_per_turn(self) -> float:
        """Degrees of tire rotation per full steering wheel turn."""
        return 360.0 / self.steering_ratio


# === STEERING PRESETS ===

STEERING_PRESETS = {
    "standard": SteeringConfig(
        steering_ratio=15.0,
        lock_to_lock=2.5,
        max_wheel_angle=35.0,
        steering_style=SteeringStyle.STANDARD
    ),

    "sport": SteeringConfig(
        steering_ratio=12.0,
        lock_to_lock=2.0,
        max_wheel_angle=38.0,
        steering_style=SteeringStyle.SPORT,
        steering_effort=0.5
    ),

    "truck": SteeringConfig(
        steering_ratio=22.0,
        lock_to_lock=4.0,
        max_wheel_angle=45.0,
        steering_style=SteeringStyle.TRUCK,
        steering_effort=0.7
    ),

    "racing": SteeringConfig(
        steering_ratio=10.0,
        lock_to_lock=1.5,
        max_wheel_angle=35.0,
        steering_style=SteeringStyle.RACING,
        steering_effort=0.8
    ),

    "offroad": SteeringConfig(
        steering_ratio=18.0,
        lock_to_lock=3.5,
        max_wheel_angle=50.0,
        steering_style=SteeringStyle.OFFROAD,
        ackermann_percent=75.0  # More tolerance for off-camber
    ),
}


class SteeringColumn:
    """
    Steering column rig connecting wheel to tires.

    Features:
    - Configurable steering ratio
    - Ackermann geometry
    - Auto-steering from path
    - Manual control empty
    """

    def __init__(self, config: Optional[SteeringConfig] = None):
        self.config = config or STEERING_PRESETS["standard"]
        self.steering_wheel: Optional[bpy.types.Object] = None
        self.front_wheels: List[bpy.types.Object] = []
        self.control_empty: Optional[bpy.types.Object] = None

    def create_rig(
        self,
        vehicle: bpy.types.Object,
        steering_wheel_obj: Optional[bpy.types.Object] = None,
        create_control: bool = True
    ) -> Dict[str, bpy.types.Object]:
        """
        Create steering column rig.

        Args:
            vehicle: The vehicle object
            steering_wheel_obj: Existing steering wheel (or create new)
            create_control: Whether to create a control empty

        Returns:
            Dictionary with rig components
        """
        result = {}

        # Use existing or create control empty
        if create_control:
            control_name = f"{vehicle.name}_steering_control"
            control = bpy.data.objects.new(control_name, None)
            control.empty_display_type = 'ARROWS'
            control.empty_display_size = 0.3

            # Position in front of vehicle
            control.location = Vector(vehicle.location) + Vector((2, 0, 1))
            bpy.context.collection.objects.link(control)
            result['control'] = control
            self.control_empty = control

        # Store steering wheel reference
        if steering_wheel_obj:
            self.steering_wheel = steering_wheel_obj
            result['steering_wheel'] = steering_wheel_obj

        return result

    def connect_to_wheels(
        self,
        wheel_FL: bpy.types.Object,
        wheel_FR: bpy.types.Object,
        config: Optional[SteeringConfig] = None
    ) -> None:
        """
        Connect steering wheel rotation to front wheel pivots.

        Creates driver constraints that convert steering wheel rotation
        to wheel steering angle.

        Args:
            wheel_FL: Front left wheel pivot
            wheel_FR: Front right wheel pivot
            config: Override steering config
        """
        config = config or self.config
        self.front_wheels = [wheel_FL, wheel_FR]

        # Get steering source (control empty or steering wheel)
        steering_source = self.control_empty or self.steering_wheel
        if not steering_source:
            return

        # Calculate max angles
        max_angle_rad = radians(config.max_wheel_angle)

        for i, wheel in enumerate([wheel_FL, wheel_FR]):
            if wheel is None:
                continue

            # Add driver to wheel Z rotation (steering axis)
            fcurve = wheel.driver_add("rotation_euler", 2)
            driver = fcurve.driver

            # Add steering input variable
            var = driver.variables.new()
            var.name = "steer"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = steering_source
            var.targets[0].data_path = "rotation_euler[1]"  # Y rotation

            # Add wheelbase and track variables for Ackermann
            var_wb = driver.variables.new()
            var_wb.name = "wheelbase"
            var_wb.targets[0].id_type = 'OBJECT'
            var_wb.targets[0].id = wheel.parent if wheel.parent else wheel
            var_wb.targets[0].data_path = '["wheelbase"]' if wheel.parent and "wheelbase" in wheel.parent else "0"

            var_tr = driver.variables.new()
            var_tr.name = "track"
            var_tr.targets[0].id_type = 'OBJECT'
            var_tr.targets[0].id = wheel.parent if wheel.parent else wheel
            var_tr.targets[0].data_path = '["track_width"]' if wheel.parent and "track_width" in wheel.parent else "0"

            if config.ackermann_enabled:
                # Ackermann-corrected steering
                is_left = (i == 0)
                driver.expression = self._create_ackermann_expression(
                    is_left, config.steering_ratio, config.max_wheel_angle, config.ackermann_percent
                )
            else:
                # Simple parallel steering
                driver.expression = f"steer / {config.steering_ratio}"

    def _create_ackermann_expression(
        self,
        is_left: bool,
        ratio: float,
        max_angle: float,
        ackermann_pct: float
    ) -> str:
        """
        Create driver expression for Ackermann steering.

        For left wheel turning left (positive steer):
        angle_L = atan(L / (R - w/2))
        For right wheel turning left:
        angle_R = atan(L / (R + w/2))

        Where R = L / tan(steering_angle)
        """
        max_rad = max_angle * (pi / 180)
        ack_factor = ackermann_pct / 100.0

        if is_left:
            # Left wheel
            return f"""
max({-max_rad:.4f}, min({max_rad:.4f},
    (steer / {ratio}) * (1.0 - 0.15 * max(0, steer / {ratio}) * {ack_factor})
))
""".replace('\n', '').strip()
        else:
            # Right wheel
            return f"""
max({-max_rad:.4f}, min({max_rad:.4f},
    (steer / {ratio}) * (1.0 + 0.15 * max(0, steer / {ratio}) * {ack_factor})
))
""".replace('\n', '').strip()

    def add_path_steering(
        self,
        path_curve: bpy.types.Curve,
        vehicle: bpy.types.Object,
        look_ahead: float = 5.0,
        sensitivity: float = 1.0
    ) -> None:
        """
        Add automatic steering based on path curvature.

        The steering will automatically turn to follow the path.

        Args:
            path_curve: The path curve to follow
            vehicle: The vehicle object
            look_ahead: How far ahead to sample the path
            sensitivity: Steering sensitivity multiplier
        """
        steering_source = self.control_empty or self.steering_wheel
        if not steering_source:
            return

        # Create a Follow Path constraint helper
        helper_name = f"{vehicle.name}_path_helper"
        helper = bpy.data.objects.new(helper_name, None)
        helper.empty_display_type = 'ARROWS'
        bpy.context.collection.objects.link(helper)

        # Add follow path constraint
        con = helper.constraints.new('FOLLOW_PATH')
        con.target = path_curve
        con.use_curve_follow = True
        con.forward_axis = 'FORWARD_X'

        # Now drive steering from helper's deviation
        # This is a simplified approach - real implementation would
        # sample the path at look_ahead distance

        # Add driver to steering source
        fcurve = steering_source.driver_add("rotation_euler", 1)
        driver = fcurve.driver

        # Variables for path following
        var = driver.variables.new()
        var.name = "helper_angle"
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = helper
        var.targets[0].data_path = "rotation_euler[2]"

        driver.expression = f"helper_angle * {sensitivity}"

    def set_steering_angle(
        self,
        angle_degrees: float,
        apply_ackermann: bool = True
    ) -> Tuple[float, float]:
        """
        Manually set steering angle.

        Args:
            angle_degrees: Desired wheel angle (-35 to +35 typically)
            apply_ackermann: Whether to apply Ackermann correction

        Returns:
            (left_wheel_angle, right_wheel_angle) in degrees
        """
        steering_source = self.control_empty or self.steering_wheel
        if not steering_source:
            return (0.0, 0.0)

        # Convert wheel angle to steering wheel rotation
        steering_rotation = angle_degrees * self.config.steering_ratio

        # Set steering wheel rotation (in radians)
        steering_source.rotation_euler[1] = radians(steering_rotation)

        if apply_ackermann and len(self.front_wheels) >= 2:
            # Calculate Ackermann angles
            left_angle, right_angle = calculate_ackermann_angles(
                angle_degrees,
                wheelbase=2.7,
                track_width=1.55
            )

            # Apply to wheels
            if self.front_wheels[0]:
                self.front_wheels[0].rotation_euler[2] = radians(left_angle)
            if self.front_wheels[1]:
                self.front_wheels[1].rotation_euler[2] = radians(right_angle)

            return (left_angle, right_angle)

        return (angle_degrees, angle_degrees)

    def animate_steering(
        self,
        start_frame: int,
        end_frame: int,
        start_angle: float,
        end_angle: float
    ) -> None:
        """
        Animate steering from one angle to another.

        Args:
            start_frame: Starting frame
            end_frame: Ending frame
            start_angle: Starting wheel angle (degrees)
            end_angle: Ending wheel angle (degrees)
        """
        steering_source = self.control_empty or self.steering_wheel
        if not steering_source:
            return

        # Convert to steering wheel rotation
        start_rotation = start_angle * self.config.steering_ratio
        end_rotation = end_angle * self.config.steering_ratio

        # Keyframe start
        steering_source.rotation_euler[1] = radians(start_rotation)
        steering_source.keyframe_insert("rotation_euler", index=1, frame=start_frame)

        # Keyframe end
        steering_source.rotation_euler[1] = radians(end_rotation)
        steering_source.keyframe_insert("rotation_euler", index=1, frame=end_frame)

        # Add easing
        try:
            fcurve = steering_source.animation_data.action.fcurves.find("rotation_euler", index=1)
            if fcurve:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.easing = 'EASE_IN_OUT'
        except:
            pass


def calculate_ackermann_angles(
    steering_angle: float,
    wheelbase: float,
    track_width: float
) -> Tuple[float, float]:
    """
    Calculate Ackermann-corrected steering angles.

    Args:
        steering_angle: Desired steering angle (degrees)
                       Positive = left turn, Negative = right turn
        wheelbase: Vehicle wheelbase (meters)
        track_width: Vehicle track width (meters)

    Returns:
        (left_wheel_angle, right_wheel_angle) in degrees
    """
    if abs(steering_angle) < 0.5:
        return (steering_angle, steering_angle)

    steer_rad = radians(steering_angle)

    # Turn radius based on steering angle
    turn_radius = wheelbase / tan(abs(steer_rad))

    # Inner wheel angle (turns more)
    inner_angle = degrees(atan(wheelbase / (turn_radius - track_width / 2)))

    # Outer wheel angle (turns less)
    outer_angle = degrees(atan(wheelbase / (turn_radius + track_width / 2)))

    # Clamp to reasonable values
    inner_angle = max(-60, min(60, inner_angle))
    outer_angle = max(-60, min(60, outer_angle))

    if steering_angle > 0:
        # Turning left
        return (inner_angle, outer_angle)
    else:
        # Turning right
        return (-outer_angle, -inner_angle)


def setup_steering(
    vehicle: bpy.types.Object,
    wheel_FL: bpy.types.Object,
    wheel_FR: bpy.types.Object,
    steering_wheel: Optional[bpy.types.Object] = None,
    preset: str = "standard"
) -> SteeringColumn:
    """
    Convenience function to setup steering system.

    Args:
        vehicle: The vehicle object
        wheel_FL: Front left wheel pivot
        wheel_FR: Front right wheel pivot
        steering_wheel: Optional steering wheel object
        preset: Steering preset name

    Returns:
        Configured SteeringColumn instance
    """
    config = STEERING_PRESETS.get(preset, STEERING_PRESETS["standard"])
    column = SteeringColumn(config)
    column.create_rig(vehicle, steering_wheel)
    column.connect_to_wheels(wheel_FL, wheel_FR)
    return column


def get_steering_preset(preset_name: str) -> SteeringConfig:
    """Get a steering preset by name."""
    return STEERING_PRESETS.get(preset_name, STEERING_PRESETS["standard"])


def list_steering_presets() -> List[str]:
    """List available steering presets."""
    return list(STEERING_PRESETS.keys())
