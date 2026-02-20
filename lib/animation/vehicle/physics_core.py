"""
Physics Core - Real Vehicle Physics Foundation

Provides realistic physics simulation for all vehicle classes.
Every car moves like a real car regardless of visual style.

Usage:
    from lib.animation.vehicle.physics_core import (
        VehiclePhysics, PhysicsEngine, setup_vehicle_physics
    )

    physics = VehiclePhysics(
        mass=1500.0,
        max_power=150.0,
        drivetrain="rwd"
    )

    engine = PhysicsEngine()
    engine.setup_rigid_body(car, physics)
    engine.apply_engine_force(car, throttle=0.8, gear=2)
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sqrt, copysign
from mathutils import Vector, Matrix
from enum import Enum


class DrivetrainType(Enum):
    FWD = "fwd"
    RWD = "rwd"
    AWD = "awd"
    FOUR_WD = "4wd"


@dataclass
class VehiclePhysics:
    """Real-world physics parameters for vehicle simulation."""

    # === MASS & DISTRIBUTION ===
    mass: float = 1500.0                    # kg
    mass_front_ratio: float = 0.52          # Front weight distribution (52/48 typical)
    center_of_gravity_height: float = 0.45  # meters above ground

    # === AERODYNAMICS ===
    drag_coefficient: float = 0.32          # Cd (0.25-0.35 typical for cars)
    frontal_area: float = 2.2               # m²
    downforce_coefficient: float = 0.1      # Cl at 0° pitch
    lift_coefficient: float = 0.0           # Positive = lift, negative = downforce

    # === ENGINE ===
    max_power: float = 150.0                # kW (200 hp)
    max_torque: float = 300.0               # Nm
    peak_power_rpm: float = 6000.0
    peak_torque_rpm: float = 4000.0
    redline_rpm: float = 7000.0
    idle_rpm: float = 800.0

    # === TRANSMISSION ===
    gear_ratios: List[float] = field(default_factory=lambda: [
        0.0,    # Reverse
        3.6,    # 1st
        2.1,    # 2nd
        1.4,    # 3rd
        1.0,    # 4th
        0.8,    # 5th
        0.65    # 6th (overdrive)
    ])
    final_drive: float = 3.7
    drivetrain_efficiency: float = 0.88     # 88% power to wheels
    drivetrain: DrivetrainType = DrivetrainType.RWD

    # === BRAKES ===
    brake_bias: float = 0.60                # Front brake bias
    max_brake_torque_front: float = 2500.0  # Nm per front wheel
    max_brake_torque_rear: float = 2000.0   # Nm per rear wheel
    abs_enabled: bool = True

    # === TIRES ===
    tire_radius_front: float = 0.32
    tire_radius_rear: float = 0.32
    tire_width_front: float = 0.225         # meters
    tire_width_rear: float = 0.225
    tire_grip_front: float = 1.0            # Multiplier (1.0 = normal street tire)
    tire_grip_rear: float = 1.0

    # === DIMENSIONS (for physics calculations) ===
    wheelbase: float = 2.7                  # meters
    track_width_front: float = 1.55         # meters
    track_width_rear: float = 1.52          # meters

    @property
    def inertia_tensor(self) -> Vector:
        """Calculate approximate moment of inertia for yaw/pitch/roll."""
        # Approximate as rectangular box
        length = self.wheelbase * 1.3
        width = self.track_width_front
        height = 0.5  # Approximate body height
        m = self.mass

        # I = (1/12) * m * (w² + h²) for each axis
        return Vector((
            (1/12) * m * (width**2 + height**2),    # Roll (X)
            (1/12) * m * (length**2 + height**2),   # Pitch (Y)
            (1/12) * m * (length**2 + width**2)     # Yaw (Z)
        ))

    def get_torque_at_rpm(self, rpm: float) -> float:
        """Calculate engine torque at given RPM using simplified curve."""
        if rpm < self.idle_rpm:
            return self.max_torque * 0.3

        # Simple parabolic approximation
        # Peak torque at peak_torque_rpm, falls off on either side
        normalized = (rpm - self.idle_rpm) / (self.redline_rpm - self.idle_rpm)
        peak_normalized = (self.peak_torque_rpm - self.idle_rpm) / (self.redline_rpm - self.idle_rpm)

        # Parabolic curve centered at peak
        torque_curve = 1.0 - ((normalized - peak_normalized) ** 2) / (peak_normalized ** 2)
        torque_curve = max(0.3, min(1.0, torque_curve))  # Clamp 30-100%

        return self.max_torque * torque_curve

    def get_power_at_rpm(self, rpm: float) -> float:
        """Calculate engine power at given RPM."""
        torque = self.get_torque_at_rpm(rpm)
        # Power (kW) = Torque (Nm) * RPM / 9549
        return torque * rpm / 9549

    def get_wheel_torque(self, rpm: float, gear: int, throttle: float) -> float:
        """Calculate torque at driven wheels."""
        if gear < 1 or gear >= len(self.gear_ratios):
            return 0.0

        engine_torque = self.get_torque_at_rpm(rpm) * throttle
        gear_ratio = self.gear_ratios[gear]
        total_ratio = gear_ratio * self.final_drive

        return engine_torque * total_ratio * self.drivetrain_efficiency


@dataclass
class PhysicsState:
    """Current state of vehicle physics simulation."""
    position: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    velocity: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    angular_velocity: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    acceleration: Vector = field(default_factory=lambda: Vector((0, 0, 0)))

    rpm: float = 800.0
    gear: int = 1
    speed_kmh: float = 0.0

    steering_angle: float = 0.0            # Front wheel angle (radians)
    throttle: float = 0.0
    brake: float = 0.0
    clutch: float = 0.0

    # Per-wheel state
    wheel_rotation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wheel_slip: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    suspension_compression: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])


# === PHYSICS PRESETS ===

PHYSICS_PRESETS = {
    "economy": VehiclePhysics(
        mass=1200,
        max_power=80.0,        # ~107 hp
        max_torque=140.0,
        drivetrain=DrivetrainType.FWD,
        drag_coefficient=0.32
    ),

    "sedan": VehiclePhysics(
        mass=1500,
        max_power=130.0,       # ~175 hp
        max_torque=250.0,
        drivetrain=DrivetrainType.FWD,
        drag_coefficient=0.30
    ),

    "sports": VehiclePhysics(
        mass=1450,
        max_power=250.0,       # ~335 hp
        max_torque=450.0,
        drivetrain=DrivetrainType.RWD,
        drag_coefficient=0.28,
        center_of_gravity_height=0.38,
        tire_grip_rear=1.2
    ),

    "muscle": VehiclePhysics(
        mass=1800,
        max_power=350.0,       # ~470 hp
        max_torque=600.0,
        drivetrain=DrivetrainType.RWD,
        drag_coefficient=0.35,
        mass_front_ratio=0.55,
        tire_grip_rear=1.3
    ),

    "suv": VehiclePhysics(
        mass=2200,
        max_power=180.0,       # ~240 hp
        max_torque=380.0,
        drivetrain=DrivetrainType.AWD,
        drag_coefficient=0.38,
        center_of_gravity_height=0.65,
        tire_grip_front=0.9,
        tire_grip_rear=0.9
    ),

    "pickup": VehiclePhysics(
        mass=2500,
        max_power=220.0,       # ~295 hp
        max_torque=500.0,
        drivetrain=DrivetrainType.FOUR_WD,
        drag_coefficient=0.42,
        center_of_gravity_height=0.70,
        wheelbase=3.4,
        track_width_front=1.75
    ),

    "monster": VehiclePhysics(
        mass=4500,              # Heavy!
        max_power=750.0,        # ~1000 hp
        max_torque=1200.0,
        drivetrain=DrivetrainType.FOUR_WD,
        drag_coefficient=0.55,
        center_of_gravity_height=1.2,
        tire_radius_front=0.85,
        tire_radius_rear=0.85,
        tire_grip_front=0.7,    # Big tires, less grip
        tire_grip_rear=0.7,
        wheelbase=3.8,
        track_width_front=2.5
    ),

    "supercar": VehiclePhysics(
        mass=1400,
        max_power=500.0,        # ~670 hp
        max_torque=700.0,
        drivetrain=DrivetrainType.AWD,
        drag_coefficient=0.33,
        downforce_coefficient=0.8,
        center_of_gravity_height=0.32,
        tire_grip_front=1.4,
        tire_grip_rear=1.4
    ),
}


class PhysicsEngine:
    """
    Core physics simulation engine for vehicles.

    Integrates with Blender's rigid body system and adds vehicle-specific
    physics like tire grip, engine power curves, and suspension.
    """

    def __init__(self):
        self.vehicles: Dict[str, PhysicsState] = {}
        self.gravity = 9.81  # m/s²

    def setup_rigid_body(
        self,
        vehicle: bpy.types.Object,
        physics: VehiclePhysics,
        collision_shape: str = "CONVEX_HULL"
    ) -> bool:
        """
        Configure rigid body with proper mass distribution.

        Args:
            vehicle: The vehicle object
            physics: Physics configuration
            collision_shape: Collision shape type

        Returns:
            True if successful
        """
        # Add rigid body modifier if not present
        if not hasattr(vehicle, 'rigid_body') or vehicle.rigid_body is None:
            bpy.context.view_layer.objects.active = vehicle
            bpy.ops.rigidbody.object_add()

        rb = vehicle.rigid_body
        rb.type = 'ACTIVE'
        rb.mass = physics.mass
        rb.use_deactivation = False  # Vehicles should stay active

        # Collision shape
        rb.collision_shape = collision_shape

        # Center of mass offset (move down for stability)
        rb.use_margin = True
        rb.collision_margin = 0.02

        # Damping (very low for realistic motion)
        rb.linear_damping = 0.1
        rb.angular_damping = 0.2

        # Initialize state tracking
        self.vehicles[vehicle.name] = PhysicsState()

        # Store physics config on object
        vehicle["physics_config"] = physics
        vehicle["physics_enabled"] = True

        return True

    def create_wheel_constraints(
        self,
        vehicle: bpy.types.Object,
        wheel_pivots: List[bpy.types.Object],
        physics: VehiclePhysics
    ) -> Dict[str, Any]:
        """
        Create physics constraints for wheels with suspension.

        Each wheel gets:
        - Hinge constraint for rotation
        - Spring-damper for suspension travel
        """
        constraints = {}

        for i, pivot in enumerate(wheel_pivots):
            # Add rigid body to wheel pivot
            if pivot.rigid_body is None:
                bpy.context.view_layer.objects.active = pivot
                bpy.ops.rigidbody.object_add()
                pivot.rigid_body.type = 'ACTIVE'
                pivot.rigid_body.mass = 30.0  # Wheel assembly mass

            # Create generic spring constraint for suspension
            bpy.context.view_layer.objects.active = pivot
            bpy.ops.rigidbody.constraint_add()

            con = pivot.rigid_body_constraint
            con.type = 'GENERIC_SPRING'
            con.target = vehicle

            # Lock all except Z (suspension travel)
            con.use_limit_lin_x = True
            con.limit_lin_x_lower = 0.0
            con.limit_lin_x_upper = 0.0

            con.use_limit_lin_y = True
            con.limit_lin_y_lower = 0.0
            con.limit_lin_y_upper = 0.0

            # Suspension travel (15cm up/down)
            con.use_limit_lin_z = True
            con.limit_lin_z_lower = -0.15
            con.limit_lin_z_upper = 0.15

            # Rotation - allow wheel to spin (Y axis) and steer (Z axis for front)
            con.use_limit_ang_x = True
            con.limit_ang_x_lower = 0.0
            con.limit_ang_x_upper = 0.0

            con.use_limit_ang_y = True
            con.limit_ang_y_lower = -pi * 10  # Free rotation
            con.limit_ang_y_upper = pi * 10

            # Front wheels can steer
            is_front = i < 2
            if is_front:
                con.use_limit_ang_z = True
                con.limit_ang_z_lower = -0.6   # ~35 degrees
                con.limit_ang_z_upper = 0.6
            else:
                con.use_limit_ang_z = True
                con.limit_ang_z_lower = 0.0
                con.limit_ang_z_upper = 0.0

            # Spring settings for suspension
            con.use_spring_z = True
            con.spring_stiffness_z = 35000.0   # N/m
            con.spring_damping_z = 4000.0      # Ns/m

            constraints[pivot.name] = con

        return constraints

    def apply_engine_force(
        self,
        vehicle: bpy.types.Object,
        throttle: float,
        gear: int,
        dt: float = 1/24
    ) -> Vector:
        """
        Apply driving force through driven wheels.

        Args:
            vehicle: The vehicle object
            throttle: 0-1 throttle input
            gear: Current gear (1-6)
            dt: Time step

        Returns:
            Applied force vector
        """
        physics = vehicle.get("physics_config")
        state = self.vehicles.get(vehicle.name)

        if not physics or not state:
            return Vector((0, 0, 0))

        # Get wheel torque
        wheel_torque = physics.get_wheel_torque(state.rpm, gear, throttle)

        # Convert to force at tire contact patch
        tire_radius = physics.tire_radius_rear
        wheel_force = wheel_torque / tire_radius

        # Distribute to driven wheels
        if physics.drivetrain == DrivetrainType.FWD:
            force_per_wheel = wheel_force / 2
            driven_wheels = [0, 1]  # FL, FR
        elif physics.drivetrain == DrivetrainType.RWD:
            force_per_wheel = wheel_force / 2
            driven_wheels = [2, 3]  # RL, RR
        else:  # AWD/4WD
            force_per_wheel = wheel_force / 4
            driven_wheels = [0, 1, 2, 3]

        # Apply force in vehicle's forward direction
        forward = vehicle.matrix_world.to_3x3() @ Vector((1, 0, 0))
        force_vector = forward * force_per_wheel * len(driven_wheels)

        # Apply to rigid body
        if vehicle.rigid_body:
            # Apply at center of mass
            vehicle.rigid_body.apply_force(force_vector, False)

        # Update state
        state.throttle = throttle
        state.gear = gear

        return force_vector

    def apply_braking(
        self,
        vehicle: bpy.types.Object,
        brake_amount: float,
        dt: float = 1/24
    ) -> float:
        """
        Apply braking force with proper bias.

        Args:
            vehicle: The vehicle object
            brake_amount: 0-1 brake input
            dt: Time step

        Returns:
            Total braking force applied
        """
        physics = vehicle.get("physics_config")
        state = self.vehicles.get(vehicle.name)

        if not physics or not state:
            return 0.0

        # Calculate braking torque
        front_brake_torque = physics.max_brake_torque_front * brake_amount
        rear_brake_torque = physics.max_brake_torque_rear * brake_amount

        # Convert to force at tire contact patch
        front_force = front_brake_torque / physics.tire_radius_front
        rear_force = rear_brake_torque / physics.tire_radius_rear

        total_brake_force = (front_force * 2 + rear_force * 2)

        # Apply opposing force in vehicle's velocity direction
        if vehicle.rigid_body and state.speed_kmh > 0.1:
            velocity_dir = state.velocity.normalized()
            if velocity_dir.length > 0:
                brake_vector = -velocity_dir * total_brake_force
                vehicle.rigid_body.apply_force(brake_vector, False)

        state.brake = brake_amount
        return total_brake_force

    def apply_steering(
        self,
        vehicle: bpy.types.Object,
        wheel_pivots: List[bpy.types.Object],
        steering_input: float,
        ackermann: bool = True
    ) -> Tuple[float, float]:
        """
        Apply steering to front wheels.

        Args:
            vehicle: The vehicle object
            wheel_pivots: [FL, FR, RL, RR] wheel pivot objects
            steering_input: -1 (full left) to +1 (full right)
            ackermann: Whether to apply Ackermann geometry

        Returns:
            (left_wheel_angle, right_wheel_angle) in radians
        """
        physics = vehicle.get("physics_config")
        state = self.vehicles.get(vehicle.name)

        if not physics or len(wheel_pivots) < 2:
            return (0.0, 0.0)

        # Base steering angle (max ~35 degrees)
        max_steering = 0.61  # radians
        base_angle = steering_input * max_steering

        if ackermann and abs(base_angle) > 0.02:
            # Ackermann geometry
            # Inner wheel turns more than outer wheel
            wheelbase = physics.wheelbase
            track = physics.track_width_front

            turn_radius = wheelbase / abs(base_angle)

            # Inner wheel angle
            inner_angle = wheelbase / (turn_radius - track/2)
            inner_angle = min(atan(inner_angle), max_steering)

            # Outer wheel angle
            outer_angle = wheelbase / (turn_radius + track/2)
            outer_angle = min(atan(outer_angle), max_steering)

            if base_angle > 0:  # Turning left
                left_angle = inner_angle
                right_angle = outer_angle
            else:  # Turning right
                left_angle = -outer_angle
                right_angle = -inner_angle
        else:
            left_angle = base_angle
            right_angle = base_angle

        # Apply to wheel pivots
        # FL
        if len(wheel_pivots) > 0 and wheel_pivots[0]:
            wheel_pivots[0].rotation_euler[2] = left_angle

        # FR
        if len(wheel_pivots) > 1 and wheel_pivots[1]:
            wheel_pivots[1].rotation_euler[2] = right_angle

        if state:
            state.steering_angle = base_angle

        return (left_angle, right_angle)

    def update_simulation(
        self,
        vehicle: bpy.types.Object,
        dt: float = 1/24
    ) -> PhysicsState:
        """
        Update physics simulation for one frame.

        This should be called every frame to maintain state.

        Args:
            vehicle: The vehicle object
            dt: Time step in seconds

        Returns:
            Updated physics state
        """
        physics = vehicle.get("physics_config")
        state = self.vehicles.get(vehicle.name)

        if not physics or not state:
            return PhysicsState()

        # Update position/velocity from rigid body
        if vehicle.rigid_body:
            state.position = vehicle.location.copy()

            # Get velocity from rigid body (Blender stores it internally)
            # We track it ourselves for now
            if hasattr(state, 'prev_position'):
                state.velocity = (state.position - state.prev_position) / dt
            state.prev_position = state.position.copy()

        # Calculate speed
        state.speed_kmh = state.velocity.length * 3.6

        # Update RPM based on wheel speed and gear
        if state.gear > 0 and state.gear < len(physics.gear_ratios):
            wheel_rps = state.speed_kmh / 3.6 / (2 * pi * physics.tire_radius_rear)
            gear_ratio = physics.gear_ratios[state.gear]
            state.rpm = wheel_rps * gear_ratio * physics.final_drive * 60
            state.rpm = max(physics.idle_rpm, min(physics.redline_rpm, state.rpm))

        # Update wheel rotations
        for i in range(4):
            wheel_speed = state.speed_kmh / 3.6 / physics.tire_radius_rear
            state.wheel_rotation[i] += wheel_speed * dt

        # Calculate slip ratios for each wheel
        # (simplified - real implementation would need wheel velocities)
        for i in range(4):
            state.wheel_slip[i] = 0.0  # Placeholder

        return state

    def get_state(self, vehicle: bpy.types.Object) -> Optional[PhysicsState]:
        """Get current physics state for a vehicle."""
        return self.vehicles.get(vehicle.name)


# === CONVENIENCE FUNCTIONS ===

def setup_vehicle_physics(
    vehicle: bpy.types.Object,
    preset: str = "sedan",
    custom_physics: Optional[VehiclePhysics] = None
) -> Tuple[PhysicsEngine, VehiclePhysics]:
    """
    Convenience function to setup physics on a vehicle.

    Args:
        vehicle: The vehicle object
        preset: Physics preset name
        custom_physics: Override with custom physics config

    Returns:
        (PhysicsEngine instance, VehiclePhysics config)
    """
    physics = custom_physics or PHYSICS_PRESETS.get(preset, PHYSICS_PRESETS["sedan"])
    engine = PhysicsEngine()
    engine.setup_rigid_body(vehicle, physics)
    return engine, physics


def get_physics_preset(preset_name: str) -> VehiclePhysics:
    """Get a physics preset by name."""
    return PHYSICS_PRESETS.get(preset_name, PHYSICS_PRESETS["sedan"])


def list_physics_presets() -> List[str]:
    """List available physics presets."""
    return list(PHYSICS_PRESETS.keys())
