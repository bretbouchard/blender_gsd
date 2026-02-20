"""
Animation Hooks - Connect Physics to Animation

Provides animation-ready outputs from all vehicle systems.
Connects physics simulation to visual animation and effects.

Usage:
    from lib.animation.vehicle.animation_hooks import (
        AnimationHooks, AnimationController, setup_animation_hooks
    )

    # Setup hooks on vehicle
    hooks = setup_animation_hooks(vehicle)

    # Get current state
    state = hooks.get_state()
    print(f"Speed: {state.speed_kmh} km/h")
    print(f"RPM: {state.rpm}")
    print(f"Wheel rotation: {state.wheel_rotation}")

    # Export animation data
    hooks.export_to_alembic("vehicle_anim.abc")
    hooks.generate_audio_markers()  # For sound sync
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos, floor, ceil
from mathutils import Vector, Matrix
from enum import Enum
import json


class AnimationOutputType(Enum):
    CUSTOM_PROPERTIES = "custom_properties"
    DRIVERS = "drivers"
    SHAPE_KEYS = "shape_keys"
    PARTICLES = "particles"


@dataclass
class AnimationState:
    """Current animation-relevant state from all vehicle systems."""

    # === MOTION ===
    speed_kmh: float = 0.0
    speed_ms: float = 0.0
    acceleration: float = 0.0
    direction: Vector = field(default_factory=lambda: Vector((1, 0, 0)))

    # === WHEELS ===
    wheel_rotation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wheel_spin_rate: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])  # rad/s
    wheel_slip: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tire_smoke_intensity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])

    # === STEERING ===
    steering_angle: float = 0.0             # Front wheel angle (radians)
    steering_wheel_rotation: float = 0.0    # Steering wheel rotation (radians)

    # === SUSPENSION ===
    suspension_compression: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    body_roll: float = 0.0
    body_pitch: float = 0.0

    # === ENGINE ===
    rpm: float = 800.0
    gear: int = 1
    throttle: float = 0.0
    brake: float = 0.0
    clutch: float = 0.0

    # === EXHAUST ===
    exhaust_smoke_intensity: float = 0.0
    exhaust_flame_intensity: float = 0.0
    backfire: bool = False

    # === DAMAGE ===
    damage_level: float = 0.0
    detached_parts: List[str] = field(default_factory=list)
    spark_locations: List[Vector] = field(default_factory=list)

    # === EFFECTS ===
    dust_intensity: float = 0.0
    splash_intensity: float = 0.0
    wind_noise: float = 0.0

    # === AUDIO MARKERS ===
    audio_markers: List[Dict] = field(default_factory=list)


@dataclass
class AudioMarker:
    """Audio sync marker for sound design."""
    frame: int
    marker_type: str           # rev, shift, skid, crash, horn, etc.
    intensity: float = 1.0
    properties: Dict = field(default_factory=dict)


class AnimationController:
    """
    Main controller for vehicle animation.

    Collects data from all vehicle systems and provides
    animation-ready outputs.
    """

    def __init__(self):
        self.vehicles: Dict[str, AnimationState] = {}
        self.audio_markers: List[AudioMarker] = []

    def register_vehicle(self, vehicle: bpy.types.Object) -> AnimationState:
        """Register a vehicle for animation tracking."""
        state = AnimationState()
        self.vehicles[vehicle.name] = state

        # Create custom properties on vehicle for animation access
        self._create_animation_properties(vehicle)

        return state

    def _create_animation_properties(self, vehicle: bpy.types.Object) -> None:
        """Create custom properties for animation hooks."""
        # Motion properties
        vehicle["anim_speed_kmh"] = 0.0
        vehicle["anim_speed_ms"] = 0.0
        vehicle["anim_acceleration"] = 0.0

        # Engine properties
        vehicle["anim_rpm"] = 800.0
        vehicle["anim_gear"] = 1
        vehicle["anim_throttle"] = 0.0
        vehicle["anim_brake"] = 0.0

        # Steering
        vehicle["anim_steering_angle"] = 0.0
        vehicle["anim_steering_wheel"] = 0.0

        # Suspension
        vehicle["anim_suspension_FL"] = 0.0
        vehicle["anim_suspension_FR"] = 0.0
        vehicle["anim_suspension_RL"] = 0.0
        vehicle["anim_suspension_RR"] = 0.0
        vehicle["anim_body_roll"] = 0.0
        vehicle["anim_body_pitch"] = 0.0

        # Effects
        vehicle["anim_exhaust_smoke"] = 0.0
        vehicle["anim_tire_smoke_FL"] = 0.0
        vehicle["anim_tire_smoke_FR"] = 0.0
        vehicle["anim_tire_smoke_RL"] = 0.0
        vehicle["anim_tire_smoke_RR"] = 0.0
        vehicle["anim_dust"] = 0.0

        # Damage
        vehicle["anim_damage"] = 0.0

    def update_state(
        self,
        vehicle: bpy.types.Object,
        physics_state: Optional[Any] = None,
        suspension_states: Optional[List[Any]] = None,
        tire_states: Optional[List[Any]] = None
    ) -> AnimationState:
        """
        Update animation state from all vehicle systems.

        Args:
            vehicle: The vehicle object
            physics_state: State from PhysicsEngine
            suspension_states: States from SuspensionSystem
            tire_states: States from TireSystem

        Returns:
            Updated AnimationState
        """
        state = self.vehicles.get(vehicle.name)
        if not state:
            state = self.register_vehicle(vehicle)

        # Update from physics
        if physics_state:
            state.speed_kmh = getattr(physics_state, 'speed_kmh', 0.0)
            state.speed_ms = state.speed_kmh / 3.6
            state.rpm = getattr(physics_state, 'rpm', 800.0)
            state.gear = getattr(physics_state, 'gear', 1)
            state.throttle = getattr(physics_state, 'throttle', 0.0)
            state.brake = getattr(physics_state, 'brake', 0.0)
            state.steering_angle = getattr(physics_state, 'steering_angle', 0.0)
            state.wheel_rotation = list(getattr(physics_state, 'wheel_rotation', [0, 0, 0, 0]))

        # Update from suspension
        if suspension_states:
            for i, susp_state in enumerate(suspension_states):
                if i < 4:
                    state.suspension_compression[i] = getattr(susp_state, 'compression_ratio', 0.0)

            # Calculate body roll and pitch
            if len(state.suspension_compression) >= 4:
                left_avg = (state.suspension_compression[0] + state.suspension_compression[2]) / 2
                right_avg = (state.suspension_compression[1] + state.suspension_compression[3]) / 2
                state.body_roll = (right_avg - left_avg) * 0.1  # Scale to radians

                front_avg = (state.suspension_compression[0] + state.suspension_compression[1]) / 2
                rear_avg = (state.suspension_compression[2] + state.suspension_compression[3]) / 2
                state.body_pitch = (front_avg - rear_avg) * 0.05

        # Update from tires
        if tire_states:
            for i, tire_state in enumerate(tire_states):
                if i < 4:
                    state.wheel_slip[i] = getattr(tire_state, 'slip_ratio', 0.0)
                    state.tire_smoke_intensity[i] = getattr(tire_state, 'smoke_intensity', 0.0)
                    state.wheel_spin_rate[i] = getattr(tire_state, 'spin_rate', 0.0)

        # Calculate derived values
        state.exhaust_smoke_intensity = self._calculate_exhaust_smoke(state)
        state.dust_intensity = self._calculate_dust(state)
        state.wind_noise = min(1.0, state.speed_kmh / 200.0)

        # Update vehicle properties
        self._update_vehicle_properties(vehicle, state)

        return state

    def _calculate_exhaust_smoke(self, state: AnimationState) -> float:
        """Calculate exhaust smoke intensity."""
        # More smoke at high throttle, low speed (acceleration)
        # Also more smoke at low RPM with high throttle
        base = state.throttle * 0.5

        # Extra smoke during acceleration
        accel_boost = max(0, state.throttle - 0.5) * 0.5

        # Backfire smoke on sudden throttle lift
        if state.throttle < 0.2 and state.rpm > 4000:
            base += 0.3
            state.backfire = True
        else:
            state.backfire = False

        return min(1.0, base + accel_boost)

    def _calculate_dust(self, state: AnimationState) -> float:
        """Calculate dust/dirt kick-up intensity."""
        # Dust depends on speed and tire slip
        slip_avg = sum(abs(s) for s in state.wheel_slip) / max(1, len(state.wheel_slip))

        dust = (state.speed_kmh / 100.0) * 0.3
        dust += slip_avg * 0.7

        return min(1.0, dust)

    def _update_vehicle_properties(self, vehicle: bpy.types.Object, state: AnimationState) -> None:
        """Update vehicle custom properties from state."""
        vehicle["anim_speed_kmh"] = state.speed_kmh
        vehicle["anim_speed_ms"] = state.speed_ms
        vehicle["anim_rpm"] = state.rpm
        vehicle["anim_gear"] = state.gear
        vehicle["anim_throttle"] = state.throttle
        vehicle["anim_brake"] = state.brake
        vehicle["anim_steering_angle"] = state.steering_angle
        vehicle["anim_steering_wheel"] = state.steering_angle * 15  # Approximate
        vehicle["anim_exhaust_smoke"] = state.exhaust_smoke_intensity
        vehicle["anim_dust"] = state.dust_intensity
        vehicle["anim_damage"] = state.damage_level

        # Suspension
        if len(state.suspension_compression) >= 4:
            vehicle["anim_suspension_FL"] = state.suspension_compression[0]
            vehicle["anim_suspension_FR"] = state.suspension_compression[1]
            vehicle["anim_suspension_RL"] = state.suspension_compression[2]
            vehicle["anim_suspension_RR"] = state.suspension_compression[3]

        # Tire smoke
        if len(state.tire_smoke_intensity) >= 4:
            vehicle["anim_tire_smoke_FL"] = state.tire_smoke_intensity[0]
            vehicle["anim_tire_smoke_FR"] = state.tire_smoke_intensity[1]
            vehicle["anim_tire_smoke_RL"] = state.tire_smoke_intensity[2]
            vehicle["anim_tire_smoke_RR"] = state.tire_smoke_intensity[3]

    def get_state(self, vehicle: bpy.types.Object) -> Optional[AnimationState]:
        """Get current animation state for a vehicle."""
        return self.vehicles.get(vehicle.name)


class AnimationHooks:
    """
    Provides hooks to connect animation to vehicle state.

    Creates drivers, particle systems, and other animation
    outputs based on vehicle physics.
    """

    def __init__(self):
        self.controller = AnimationController()

    def setup_hooks(
        self,
        vehicle: bpy.types.Object,
        wheel_objects: List[bpy.types.Object],
        steering_wheel: Optional[bpy.types.Object] = None
    ) -> Dict[str, Any]:
        """
        Setup all animation hooks on a vehicle.

        Args:
            vehicle: The vehicle object
            wheel_objects: Wheel mesh objects [FL, FR, RL, RR]
            steering_wheel: Optional steering wheel object

        Returns:
            Dictionary with hook references
        """
        result = {
            'controller': self.controller,
            'wheel_drivers': [],
            'suspension_hooks': [],
            'effect_hooks': []
        }

        # Register vehicle
        self.controller.register_vehicle(vehicle)

        # Setup wheel rotation drivers
        for i, wheel in enumerate(wheel_objects):
            if wheel:
                driver = self._setup_wheel_rotation_driver(vehicle, wheel, i)
                result['wheel_drivers'].append(driver)

        # Setup steering wheel driver
        if steering_wheel:
            self._setup_steering_wheel_driver(vehicle, steering_wheel)

        # Setup suspension visual hooks
        result['suspension_hooks'] = self._setup_suspension_hooks(vehicle)

        # Setup exhaust smoke particles
        result['effect_hooks'] = self._setup_exhaust_particles(vehicle)

        return result

    def _setup_wheel_rotation_driver(
        self,
        vehicle: bpy.types.Object,
        wheel: bpy.types.Object,
        wheel_index: int
    ) -> Optional[bpy.types.FCurve]:
        """Setup driver for wheel rotation based on vehicle speed."""
        # Add driver to wheel Y rotation (typical spin axis)
        try:
            fcurve = wheel.driver_add("rotation_euler", 1)  # Y rotation
            driver = fcurve.driver

            # Add variable for distance traveled
            var = driver.variables.new()
            var.name = "dist"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = vehicle
            var.targets[0].data_path = "location[0]"  # X position

            # Add variable for tire radius
            var2 = driver.variables.new()
            var2.name = "radius"
            var2.targets[0].id_type = 'OBJECT'
            var2.targets[0].id = vehicle
            var2.targets[0].data_path = '["tire_radius"]' if "tire_radius" in vehicle else ""

            # Expression: rotation = distance / circumference
            # circumference = 2 * pi * radius
            radius = vehicle.get("tire_radius", 0.35)
            driver.expression = f"dist / (2 * {pi} * {radius})"

            return fcurve

        except:
            return None

    def _setup_steering_wheel_driver(
        self,
        vehicle: bpy.types.Object,
        steering_wheel: bpy.types.Object
    ) -> Optional[bpy.types.FCurve]:
        """Setup driver for steering wheel rotation."""
        try:
            fcurve = steering_wheel.driver_add("rotation_euler", 1)  # Y rotation
            driver = fcurve.driver

            var = driver.variables.new()
            var.name = "steer"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = vehicle
            var.targets[0].data_path = '["anim_steering_angle"]'

            # Steering wheel rotates opposite to wheel angle, multiplied by ratio
            ratio = vehicle.get("steering_ratio", 15.0)
            driver.expression = f"steer * {ratio}"

            return fcurve

        except:
            return None

    def _setup_suspension_hooks(self, vehicle: bpy.types.Object) -> List[Any]:
        """Setup visual suspension hooks (body roll/pitch)."""
        hooks = []

        # Add drivers for body roll and pitch
        try:
            # Body roll
            fcurve_roll = vehicle.driver_add("rotation_euler", 2)  # Z rotation
            driver_roll = fcurve_roll.driver

            var = driver_roll.variables.new()
            var.name = "roll"
            var.targets[0].id_type = 'OBJECT'
            var.targets[0].id = vehicle
            var.targets[0].data_path = '["anim_body_roll"]'
            driver_roll.expression = "roll"

            hooks.append(fcurve_roll)

        except:
            pass

        return hooks

    def _setup_exhaust_particles(self, vehicle: bpy.types.Object) -> Optional[Any]:
        """Setup exhaust smoke particle system."""
        # This would create a particle system controlled by anim_exhaust_smoke
        # Simplified for now - in practice would use bpy.data.particles

        # Create exhaust empty
        exhaust_name = f"{vehicle.name}_exhaust"
        exhaust = bpy.data.objects.new(exhaust_name, None)
        exhaust.empty_display_type = 'SPHERE'
        exhaust.empty_display_size = 0.05
        exhaust.location = (-1.5, 0.3, 0.2)
        exhaust.parent = vehicle
        bpy.context.collection.objects.link(exhaust)

        # Store reference for particle system
        vehicle["exhaust_empty"] = exhaust.name

        return exhaust

    def generate_audio_markers(
        self,
        vehicle: bpy.types.Object,
        frame_range: Tuple[int, int]
    ) -> List[AudioMarker]:
        """
        Generate audio sync markers for sound design.

        Args:
            vehicle: The vehicle object
            frame_range: (start_frame, end_frame)

        Returns:
            List of audio markers
        """
        markers = []
        state = self.controller.get_state(vehicle)

        if not state:
            return markers

        start, end = frame_range

        # Generate markers based on vehicle events

        # Engine rev points (RPM milestones)
        rpm_thresholds = [2000, 4000, 6000, state.rpm]  # Simplified
        for rpm_point in rpm_thresholds:
            if state.rpm >= rpm_point:
                markers.append(AudioMarker(
                    frame=start,
                    marker_type="rev",
                    intensity=state.throttle,
                    properties={"rpm": rpm_point}
                ))

        # Gear shifts (when throttle drops and gear changes)
        # Would need frame-by-frame analysis for real implementation

        # Tire squeal (high slip)
        if max(state.wheel_slip) > 0.3:
            markers.append(AudioMarker(
                frame=start,
                marker_type="skid",
                intensity=max(state.tire_smoke_intensity)
            ))

        # Backfire
        if state.backfire:
            markers.append(AudioMarker(
                frame=start,
                marker_type="backfire",
                intensity=1.0
            ))

        self.controller.audio_markers.extend(markers)
        return markers

    def export_to_alembic(
        self,
        vehicles: List[bpy.types.Object],
        filepath: str,
        frame_start: int = 1,
        frame_end: int = 250
    ) -> bool:
        """
        Export animation to Alembic format.

        Args:
            vehicles: List of vehicle objects
            filepath: Output file path
            frame_start: Start frame
            frame_end: End frame

        Returns:
            True if export successful
        """
        try:
            # Select all vehicles and their children
            bpy.ops.object.select_all(action='DESELECT')

            for vehicle in vehicles:
                vehicle.select_set(True)
                for child in vehicle.children_recursive:
                    child.select_set(True)

            # Export to Alembic
            bpy.ops.wm.alembic_export(
                filepath=filepath,
                frame_start=frame_start,
                frame_end=frame_end,
                selected=True,
                visible_objects_only=True
            )

            return True

        except Exception as e:
            print(f"Alembic export failed: {e}")
            return False

    def export_markers_to_json(
        self,
        filepath: str
    ) -> bool:
        """
        Export audio markers to JSON for audio software.

        Args:
            filepath: Output JSON file path

        Returns:
            True if export successful
        """
        try:
            data = {
                "markers": [
                    {
                        "frame": m.frame,
                        "type": m.marker_type,
                        "intensity": m.intensity,
                        "properties": m.properties
                    }
                    for m in self.controller.audio_markers
                ]
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"Marker export failed: {e}")
            return False


def setup_animation_hooks(
    vehicle: bpy.types.Object,
    wheel_objects: Optional[List[bpy.types.Object]] = None,
    steering_wheel: Optional[bpy.types.Object] = None
) -> AnimationHooks:
    """
    Convenience function to setup animation hooks.

    Args:
        vehicle: The vehicle object
        wheel_objects: Wheel mesh objects (optional, will search children)
        steering_wheel: Steering wheel object (optional)

    Returns:
        Configured AnimationHooks instance
    """
    hooks = AnimationHooks()

    # Find wheel objects if not provided
    if not wheel_objects:
        wheel_objects = []
        for child in vehicle.children:
            if 'wheel' in child.name.lower() or 'tire' in child.name.lower():
                wheel_objects.append(child)

    # Ensure we have at least 4 slots
    while len(wheel_objects) < 4:
        wheel_objects.append(None)

    hooks.setup_hooks(vehicle, wheel_objects[:4], steering_wheel)

    return hooks


def get_animation_state(vehicle: bpy.types.Object) -> AnimationState:
    """Get current animation state for a vehicle."""
    controller = AnimationController()
    if vehicle.name in controller.vehicles:
        return controller.vehicles[vehicle.name]
    return AnimationState()
