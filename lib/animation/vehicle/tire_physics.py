"""
Tire Physics - Pacejka Magic Formula

Implements realistic tire physics using the Pacejka "Magic Formula"
for longitudinal and lateral force generation.

The Magic Formula is the industry standard for tire simulation:
F = D * sin(C * atan(B * x - E * (B * x - atan(B * x))))

Where:
- B = Stiffness factor
- C = Shape factor
- D = Peak factor
- E = Curvature factor
- x = Slip ratio or slip angle

Usage:
    from lib.animation.vehicle.tire_physics import (
        TirePhysics, TireSystem, calculate_tire_forces
    )

    tire = TirePhysics(grip_multiplier=1.2)  # High-grip tire

    # Calculate forces
    longitudinal = tire.calculate_longitudinal_force(slip_ratio=0.1, normal_force=4000)
    lateral = tire.calculate_lateral_force(slip_angle=0.05, normal_force=4000)
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos, atan, tan, sqrt, copysign
from mathutils import Vector
from enum import Enum


class TireType(Enum):
    STREET = "street"
    PERFORMANCE = "performance"
    RACING_SLICK = "racing_slick"
    OFFROAD = "offroad"
    MUD_TERRAIN = "mud_terrain"
    WINTER = "winter"
    DRAG = "drag"
    MONSTER = "monster"


class TireCondition(Enum):
    NEW = "new"
    NORMAL = "normal"
    WORN = "worn"
    BALD = "bald"
    DAMAGED = "damaged"


@dataclass
class TirePhysics:
    """
    Pacejka Magic Formula tire parameters.

    The coefficients are fitted from real tire test data.
    These defaults represent a typical street tire.
    """

    # === TIRE IDENTITY ===
    tire_type: TireType = TireType.STREET
    condition: TireCondition = TireCondition.NORMAL

    # === PHYSICAL PROPERTIES ===
    radius: float = 0.32              # meters
    width: float = 0.225              # meters
    aspect_ratio: float = 0.45        # sidewall height / width

    # === LOAD CAPACITY ===
    max_load: float = 4500.0          # N (load index)
    rated_pressure: float = 2.4       # bar

    # === GRIP ===
    grip_multiplier: float = 1.0      # Overall grip adjustment
    longitudinal_grip: float = 1.0    # Forward/backward grip
    lateral_grip: float = 1.0         # Cornering grip

    # === PACEMAN MAGIC FORMULA COEFFICIENTS ===
    # These define the tire's force characteristics

    # Longitudinal (acceleration/braking)
    b0_long: float = 1.65             # Shape factor
    b1_long: float = 0.0              # Load sensitivity
    b2_long: float = 1688.0           # Stiffness
    b3_long: float = 0.0              # Curvature
    b4_long: float = 229.0            # Peak factor
    b5_long: float = 0.0              # Load at peak
    b6_long: float = 0.0              # Combined slip

    # Lateral (cornering)
    a0_lat: float = 1.65
    a1_lat: float = 0.0
    a2_lat: float = 1688.0
    a3_lat: float = 0.0
    a4_lat: float = 229.0
    a5_lat: float = 0.0
    a6_lat: float = 0.0

    # Combined slip (when both lateral and longitudinal)
    combine_method: str = "pacejka"   # pacejka, ellipse, friction_circle

    # === TEMPERATURE ===
    optimal_temp: float = 85.0        # °C (optimal operating temp)
    temp_sensitivity: float = 0.02    # Grip reduction per °C from optimal

    # === CAMBER ===
    camber_thrust: float = 0.1        # Lateral force from camber
    camber_sensitivity: float = 0.05  # How much camber affects grip

    @property
    def circumference(self) -> float:
        """Tire circumference in meters."""
        return 2 * pi * self.radius

    @property
    def contact_patch_area(self) -> float:
        """Approximate contact patch area in m²."""
        # Simplified: assumes rectangular patch
        # Length depends on load and tire stiffness
        typical_length = 0.15  # meters (typical)
        return self.width * typical_length

    def calculate_longitudinal_force(
        self,
        slip_ratio: float,
        normal_force: float,
        camber: float = 0.0
    ) -> float:
        """
        Calculate longitudinal force (acceleration/braking).

        Uses Pacejka Magic Formula:
        Fx = D * sin(C * atan(B * k - E * (B * k - atan(B * k))))

        Args:
            slip_ratio: Longitudinal slip ratio (-1 to 1)
                       Positive = driving, Negative = braking
            normal_force: Vertical load on tire (N)
            camber: Camber angle in radians

        Returns:
            Longitudinal force in Newtons
        """
        # Slip ratio limits
        slip_ratio = max(-1.0, min(1.0, slip_ratio))

        # Normalized load (fraction of max load)
        fnorm = normal_force / self.max_load
        fnorm = min(1.5, fnorm)  # Cap at 150% load

        # Magic Formula coefficients for current load
        B = self.b2_long / 1000.0                      # Stiffness
        C = self.b0_long                                # Shape
        D = self.b4_long * fnorm * self.longitudinal_grip * self.grip_multiplier  # Peak
        E = self.b3_long                                # Curvature

        # Magic Formula
        x = abs(slip_ratio)
        fx = D * sin(C * atan(B * x - E * (B * x - atan(B * x))))

        # Apply sign (direction of force)
        fx = copysign(fx, slip_ratio)

        # Scale by normal force
        fx *= normal_force / 1000.0  # Scale to reasonable forces

        return fx

    def calculate_lateral_force(
        self,
        slip_angle: float,
        normal_force: float,
        camber: float = 0.0
    ) -> float:
        """
        Calculate lateral force (cornering).

        Uses Pacejka Magic Formula for lateral slip.

        Args:
            slip_angle: Slip angle in radians (0 = rolling, pi/2 = sliding)
            normal_force: Vertical load on tire (N)
            camber: Camber angle in radians

        Returns:
            Lateral force in Newtons
        """
        # Slip angle limits
        slip_angle = max(-pi/2, min(pi/2, slip_angle))

        # Normalized load
        fnorm = normal_force / self.max_load
        fnorm = min(1.5, fnorm)

        # Magic Formula coefficients
        B = self.a2_lat / 1000.0
        C = self.a0_lat
        D = self.a4_lat * fnorm * self.lateral_grip * self.grip_multiplier
        E = self.a3_lat

        # Magic Formula
        x = abs(slip_angle) * 10  # Scale slip angle
        fy = D * sin(C * atan(B * x - E * (B * x - atan(B * x))))

        # Apply sign
        fy = copysign(fy, slip_angle)

        # Scale by normal force
        fy *= normal_force / 1000.0

        # Add camber thrust
        fy += normal_force * self.camber_thrust * sin(camber)

        return fy

    def calculate_combined_force(
        self,
        slip_ratio: float,
        slip_angle: float,
        normal_force: float,
        camber: float = 0.0
    ) -> Tuple[float, float]:
        """
        Calculate combined longitudinal and lateral forces.

        When both slip types occur, they share the available friction.
        Uses friction ellipse method.

        Args:
            slip_ratio: Longitudinal slip ratio
            slip_angle: Lateral slip angle (radians)
            normal_force: Vertical load (N)
            camber: Camber angle (radians)

        Returns:
            (longitudinal_force, lateral_force) in Newtons
        """
        # Calculate pure forces
        fx_pure = self.calculate_longitudinal_force(slip_ratio, normal_force, camber)
        fy_pure = self.calculate_lateral_force(slip_angle, normal_force, camber)

        # Friction ellipse combination
        # Fx²/Fx_max² + Fy²/Fy_max² ≤ 1
        if self.combine_method == "friction_circle":
            # Simple friction circle
            combined = sqrt(fx_pure**2 + fy_pure**2)
            max_friction = normal_force * self.grip_multiplier * 1.0

            if combined > max_friction:
                scale = max_friction / combined
                fx_pure *= scale
                fy_pure *= scale

        elif self.combine_method == "ellipse":
            # Friction ellipse
            fx_max = abs(self.calculate_longitudinal_force(
                copysign(0.1, slip_ratio), normal_force, camber
            ))
            fy_max = abs(self.calculate_lateral_force(
                copysign(0.1, slip_angle), normal_force, camber
            ))

            if fx_max > 0 and fy_max > 0:
                # Check if outside ellipse
                outside = (fx_pure/fx_max)**2 + (fy_pure/fy_max)**2
                if outside > 1:
                    scale = 1.0 / sqrt(outside)
                    fx_pure *= scale
                    fy_pure *= scale

        return fx_pure, fy_pure


@dataclass
class WheelTireState:
    """Runtime state for a single wheel's tire."""
    slip_ratio: float = 0.0
    slip_angle: float = 0.0
    longitudinal_force: float = 0.0
    lateral_force: float = 0.0
    normal_force: float = 0.0
    temperature: float = 20.0          # °C

    # Animation outputs
    spin_rate: float = 0.0             # rad/s
    smoke_intensity: float = 0.0       # 0-1
    squeal_intensity: float = 0.0      # 0-1


# === TIRE PRESETS ===

TIRE_PRESETS = {
    "street": TirePhysics(
        tire_type=TireType.STREET,
        grip_multiplier=1.0,
        b2_long=1688.0, b4_long=229.0,
        a2_lat=1688.0, a4_lat=229.0
    ),

    "performance": TirePhysics(
        tire_type=TireType.PERFORMANCE,
        grip_multiplier=1.2,
        longitudinal_grip=1.15,
        lateral_grip=1.25,
        b2_long=2100.0, b4_long=275.0,
        a2_lat=2200.0, a4_lat=290.0,
        optimal_temp=90.0
    ),

    "racing_slick": TirePhysics(
        tire_type=TireType.RACING_SLICK,
        grip_multiplier=1.5,
        longitudinal_grip=1.4,
        lateral_grip=1.6,
        b2_long=2800.0, b4_long=350.0,
        a2_lat=3000.0, a4_lat=380.0,
        optimal_temp=95.0,
        temp_sensitivity=0.03
    ),

    "offroad": TirePhysics(
        tire_type=TireType.OFFROAD,
        grip_multiplier=0.85,
        longitudinal_grip=0.9,
        lateral_grip=0.8,
        b2_long=1200.0, b4_long=180.0,
        a2_lat=1100.0, a4_lat=160.0,
        radius=0.38,
        width=0.265
    ),

    "mud_terrain": TirePhysics(
        tire_type=TireType.MUD_TERRAIN,
        grip_multiplier=0.75,
        longitudinal_grip=0.85,
        lateral_grip=0.65,
        b2_long=900.0, b4_long=140.0,
        a2_lat=800.0, a4_lat=120.0,
        radius=0.40,
        width=0.285
    ),

    "winter": TirePhysics(
        tire_type=TireType.WINTER,
        grip_multiplier=0.9,
        b2_long=1400.0, b4_long=190.0,
        a2_lat=1300.0, a4_lat=170.0,
        optimal_temp=5.0
    ),

    "drag": TirePhysics(
        tire_type=TireType.DRAG,
        grip_multiplier=1.8,
        longitudinal_grip=2.0,
        lateral_grip=0.7,
        b2_long=3500.0, b4_long=450.0,
        a2_lat=1000.0, a4_lat=100.0,
        radius=0.45,
        width=0.35
    ),

    "monster": TirePhysics(
        tire_type=TireType.MONSTER,
        grip_multiplier=0.65,
        longitudinal_grip=0.7,
        lateral_grip=0.6,
        b2_long=800.0, b4_long=120.0,
        a2_lat=700.0, a4_lat=100.0,
        radius=0.85,
        width=0.45
    ),
}


class TireSystem:
    """
    Complete tire physics system.

    Manages tire state for all wheels and provides force calculations
    for the vehicle physics simulation.
    """

    def __init__(self):
        self.wheel_states: Dict[str, WheelTireState] = {}

    def calculate_slip_ratio(
        self,
        wheel_speed: float,
        vehicle_speed: float,
        tire_radius: float
    ) -> float:
        """
        Calculate longitudinal slip ratio.

        Slip ratio = (wheel_speed - vehicle_speed) / max(abs(wheel_speed), abs(vehicle_speed))

        Args:
            wheel_speed: Wheel rotational speed (rad/s)
            vehicle_speed: Vehicle ground speed (m/s)
            tire_radius: Tire radius (m)

        Returns:
            Slip ratio (-1 to 1)
                   0 = rolling freely
                   +1 = wheel spinning (acceleration)
                   -1 = wheel locked (braking)
        """
        # Convert wheel angular velocity to linear velocity
        wheel_linear = wheel_speed * tire_radius

        # Avoid division by zero
        max_speed = max(abs(wheel_linear), abs(vehicle_speed), 0.01)

        slip = (wheel_linear - vehicle_speed) / max_speed
        return max(-1.0, min(1.0, slip))

    def calculate_slip_angle(
        self,
        wheel_velocity: Vector,
        wheel_heading: Vector
    ) -> float:
        """
        Calculate lateral slip angle.

        Slip angle = atan(lateral_velocity / longitudinal_velocity)

        Args:
            wheel_velocity: Wheel's velocity vector in world space
            wheel_heading: Wheel's forward direction (unit vector)

        Returns:
            Slip angle in radians
        """
        # Decompose velocity into longitudinal and lateral components
        long_vel = wheel_velocity.dot(wheel_heading)
        lateral_vel = wheel_velocity.dot(Vector((-wheel_heading.y, wheel_heading.x, 0)))

        # Calculate slip angle
        if abs(long_vel) < 0.1:
            return 0.0

        slip_angle = atan(lateral_vel / long_vel)
        return slip_angle

    def update_wheel(
        self,
        wheel_name: str,
        tire_config: TirePhysics,
        wheel_speed: float,
        vehicle_speed: float,
        normal_force: float,
        slip_angle: float = 0.0,
        camber: float = 0.0,
        dt: float = 1/24
    ) -> WheelTireState:
        """
        Update tire physics for a single wheel.

        Args:
            wheel_name: Identifier for the wheel
            tire_config: Tire physics configuration
            wheel_speed: Wheel rotational speed (rad/s)
            vehicle_speed: Vehicle ground speed (m/s)
            normal_force: Vertical load on tire (N)
            slip_angle: Lateral slip angle (radians)
            camber: Camber angle (radians)
            dt: Time step

        Returns:
            Updated wheel tire state
        """
        # Get or create state
        if wheel_name not in self.wheel_states:
            self.wheel_states[wheel_name] = WheelTireState()
        state = self.wheel_states[wheel_name]

        # Calculate slip ratio
        state.slip_ratio = self.calculate_slip_ratio(
            wheel_speed, vehicle_speed, tire_config.radius
        )
        state.slip_angle = slip_angle

        # Calculate forces
        state.normal_force = normal_force
        state.longitudinal_force, state.lateral_force = tire_config.calculate_combined_force(
            state.slip_ratio,
            slip_angle,
            normal_force,
            camber
        )

        # Update wheel spin rate
        state.spin_rate = wheel_speed

        # Calculate smoke intensity (high slip = smoke)
        total_slip = sqrt(state.slip_ratio**2 + (slip_angle / 0.5)**2)
        state.smoke_intensity = min(1.0, total_slip * 2)

        # Calculate squeal intensity (moderate slip = squeal)
        if 0.05 < abs(state.slip_ratio) < 0.3 or 0.02 < abs(slip_angle) < 0.15:
            state.squeal_intensity = min(1.0, total_slip * 4)
        else:
            state.squeal_intensity = 0.0

        # Update temperature
        heat_generated = total_slip * abs(state.longitudinal_force) * 0.001
        cooling = (state.temperature - 20.0) * 0.01  # Ambient = 20°C
        state.temperature += heat_generated - cooling

        return state

    def get_state(self, wheel_name: str) -> Optional[WheelTireState]:
        """Get tire state for a wheel."""
        return self.wheel_states.get(wheel_name)

    def get_all_states(self) -> Dict[str, WheelTireState]:
        """Get all wheel tire states."""
        return self.wheel_states.copy()


def calculate_tire_forces(
    wheel_speed: float,
    vehicle_speed: float,
    normal_force: float,
    tire_preset: str = "street"
) -> Tuple[float, float]:
    """
    Convenience function for quick tire force calculation.

    Args:
        wheel_speed: Wheel rotational speed (rad/s)
        vehicle_speed: Vehicle ground speed (m/s)
        normal_force: Vertical load (N)
        tire_preset: Tire preset name

    Returns:
        (longitudinal_force, slip_ratio)
    """
    tire = TIRE_PRESETS.get(tire_preset, TIRE_PRESETS["street"])
    system = TireSystem()

    slip_ratio = system.calculate_slip_ratio(wheel_speed, vehicle_speed, tire.radius)
    long_force = tire.calculate_longitudinal_force(slip_ratio, normal_force)

    return long_force, slip_ratio


def get_tire_preset(preset_name: str) -> TirePhysics:
    """Get a tire preset by name."""
    return TIRE_PRESETS.get(preset_name, TIRE_PRESETS["street"])


def list_tire_presets() -> List[str]:
    """List available tire presets."""
    return list(TIRE_PRESETS.keys())
