"""
Vehicle Physics System for Launch Control

Physics-based vehicle movement simulation including path following,
drift mechanics, jumps, and offroad behavior.

Features:
- Path-based driving with speed control
- Drift mode with counter-steering
- Jump simulation with rotation
- Offroad suspension behavior
- Speed-based animation segments
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

# Type hints for Blender API (runtime optional)
try:
    import bpy
    from mathutils import Vector, Matrix, Quaternion

    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None  # type: ignore
    Vector = Any  # type: ignore
    Matrix = Any  # type: ignore
    Quaternion = Any  # type: ignore

if TYPE_CHECKING:
    from .auto_rig import LaunchControlRig


@dataclass
class PhysicsConfig:
    """Configuration for vehicle physics."""

    mass: float = 1500.0  # kg
    drag_coefficient: float = 0.3
    frontal_area: float = 2.2  # m^2
    engine_power: float = 150000.0  # Watts (150 kW)
    braking_force: float = 30000.0  # Newtons
    center_of_mass: tuple[float, float, float] = (0, 0, 0.5)
    air_density: float = 1.225  # kg/m^3
    rolling_resistance: float = 0.015
    wheel_radius: float = 0.35  # meters


@dataclass
class DriftConfig:
    """Configuration for drift mode."""

    enabled: bool = False
    drift_factor: float = 0.7  # 0 = grip, 1 = full drift
    countersteer_enabled: bool = True
    throttle_oversteer: float = 0.3  # Additional rotation from throttle
    brake_oversteer: float = 0.5  # Rotation from braking in drift


@dataclass
class JumpConfig:
    """Configuration for jump simulation."""

    launch_velocity: tuple[float, float, float] = (0, 15, 5)  # m/s
    rotation_axis: tuple[float, float, float] = (1, 0, 0)
    rotation_speed: float = 0.0  # radians/second
    gravity: float = 9.81  # m/s^2


@dataclass
class OffroadConfig:
    """Configuration for offroad mode."""

    enabled: bool = False
    roughness: float = 0.5  # 0 = smooth, 1 = very rough
    suspension_travel_multiplier: float = 1.5
    damping_reduction: float = 0.7  # Reduce damping for more bounce
    wheel_spin_factor: float = 0.3  # Slip on loose surfaces


@dataclass
class SpeedSegment:
    """A segment of animation with target speed."""

    frame_start: int
    frame_end: int
    target_speed: float  # m/s
    acceleration: Optional[float] = None  # m/s^2, None = auto
    current_speed: float = 0.0  # Set during generation


class VehiclePhysics:
    """Physics-based vehicle movement simulation.

    Provides realistic vehicle dynamics including acceleration,
    braking, drag, and special driving modes.

    Example:
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        physics = VehiclePhysics(rig)
        physics.configure(
            mass=1500,
            engine_power=150000,
            drag_coefficient=0.3
        )

        # Drive along a path
        physics.drive_path(path_curve, speed=15.0, follow_terrain=True)

        # Enable drift mode
        physics.enable_drift_mode(drift_factor=0.7)

        # Simulate a jump
        physics.simulate_jump(
            launch_velocity=(0, 15, 8),
            rotation_axis=(1, 0, 0),
            rotation_speed=2.0
        )
    """

    def __init__(self, rig: "LaunchControlRig"):
        """Initialize physics system.

        Args:
            rig: The LaunchControlRig instance
        """
        self.rig = rig
        self.config = PhysicsConfig()
        self.drift_config = DriftConfig()
        self.jump_config = JumpConfig()
        self.offroad_config = OffroadConfig()
        self.current_speed: float = 0.0
        self.current_velocity: Vector = Vector((0, 0, 0)) if BLENDER_AVAILABLE else (0, 0, 0)  # type: ignore
        self._path_follow_data: Optional[dict[str, Any]] = None

    def configure(
        self,
        mass: float = 1500.0,
        drag_coefficient: float = 0.3,
        frontal_area: float = 2.2,
        engine_power: float = 150000.0,
        braking_force: float = 30000.0,
        center_of_mass: tuple[float, float, float] = (0, 0, 0.5),
    ) -> None:
        """Configure vehicle physics parameters.

        Args:
            mass: Vehicle mass in kg
            drag_coefficient: Aerodynamic drag coefficient (Cd)
            frontal_area: Frontal cross-section area in m^2
            engine_power: Maximum engine power in Watts
            braking_force: Maximum braking force in Newtons
            center_of_mass: Local offset for center of mass
        """
        self.config.mass = mass
        self.config.drag_coefficient = drag_coefficient
        self.config.frontal_area = frontal_area
        self.config.engine_power = engine_power
        self.config.braking_force = braking_force
        self.config.center_of_mass = center_of_mass

    def calculate_drag_force(self, speed: float) -> float:
        """Calculate aerodynamic drag force.

        F_drag = 0.5 * rho * Cd * A * v^2

        Args:
            speed: Current speed in m/s

        Returns:
            Drag force in Newtons
        """
        return (
            0.5
            * self.config.air_density
            * self.config.drag_coefficient
            * self.config.frontal_area
            * speed
            * speed
        )

    def calculate_rolling_resistance(self) -> float:
        """Calculate rolling resistance force.

        Returns:
            Rolling resistance force in Newtons
        """
        return self.config.rolling_resistance * self.config.mass * 9.81

    def calculate_max_speed(self) -> float:
        """Calculate theoretical maximum speed.

        When engine force equals drag + rolling resistance.

        Returns:
            Maximum speed in m/s
        """
        # At max speed: P = F * v where F = drag + rolling
        # P = (0.5 * rho * Cd * A * v^2 + Crr * m * g) * v
        # This is a cubic equation, solve numerically
        # Simplified approximation:
        max_force = self.config.engine_power / 20  # Force at typical cruising speed
        drag_at_speed = self.calculate_drag_force(20)
        rolling = self.calculate_rolling_resistance()

        if drag_at_speed + rolling > 0:
            # Iterate to find equilibrium
            for speed in range(1, 200):
                drag = self.calculate_drag_force(speed)
                power_needed = (drag + rolling) * speed
                if power_needed > self.config.engine_power:
                    return float(speed - 1)

        return 60.0  # Default ~216 km/h

    def drive_path(
        self,
        path: Any,
        speed: float = 10.0,
        follow_terrain: bool = True,
        frame_start: int = 1,
        align_to_path: bool = True,
    ) -> None:
        """Drive vehicle along a path curve.

        Args:
            path: Blender curve object defining the path
            speed: Target speed in m/s
            follow_terrain: Whether to adjust height to terrain
            frame_start: Starting frame for animation
            align_to_path: Rotate vehicle to follow path tangent
        """
        if not BLENDER_AVAILABLE:
            return

        armature = self.rig.rig_objects.get("armature")
        if not armature:
            return

        # Get path data
        if not hasattr(path, "data") or not hasattr(path.data, "splines"):
            return

        # Calculate path length and frame range
        path_length = self._calculate_path_length(path)
        duration = path_length / speed
        fps = bpy.context.scene.render.fps
        frame_end = frame_start + int(duration * fps)

        # Setup follow path constraint
        self._setup_path_constraint(armature, path, frame_start, frame_end, align_to_path)

        # Store path following data
        self._path_follow_data = {
            "path": path,
            "speed": speed,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "follow_terrain": follow_terrain,
            "path_length": path_length,
        }

        if follow_terrain:
            self._setup_terrain_following(armature, path, frame_start, frame_end)

    def _calculate_path_length(self, path: Any) -> float:
        """Calculate total length of a path curve.

        Args:
            path: Curve object

        Returns:
            Path length in Blender units
        """
        if not BLENDER_AVAILABLE:
            return 0.0

        # Use Blender's curve length calculation
        if hasattr(path, "data") and hasattr(path.data, "splines"):
            total_length = 0.0
            for spline in path.data.splines:
                total_length += spline.calc_length()
            return total_length

        return 0.0

    def _setup_path_constraint(
        self,
        armature: Any,
        path: Any,
        frame_start: int,
        frame_end: int,
        align_to_path: bool,
    ) -> None:
        """Setup follow path constraint.

        Args:
            armature: Rig armature
            path: Path curve
            frame_start: Start frame
            frame_end: End frame
            align_to_path: Whether to align rotation
        """
        if not BLENDER_AVAILABLE:
            return

        # Add Follow Path constraint
        constraint = armature.constraints.new("FOLLOW_PATH")
        constraint.target = path
        constraint.use_curve_follow = align_to_path
        constraint.use_fixed_location = True

        # Animate offset factor
        armature["path_offset"] = 0.0
        armature.keyframe_insert('["path_offset"]', frame=frame_start)

        armature["path_offset"] = 1.0
        armature.keyframe_insert('["path_offset"]', frame=frame_end)

    def _setup_terrain_following(
        self,
        armature: Any,
        path: Any,
        frame_start: int,
        frame_end: int,
    ) -> None:
        """Setup terrain height following.

        Args:
            armature: Rig armature
            path: Path curve
            frame_start: Start frame
            frame_end: End frame
        """
        # This would sample the terrain at each path point
        # and adjust the vehicle height accordingly
        # Implementation depends on terrain object reference
        pass

    def enable_drift_mode(
        self,
        drift_factor: float = 0.7,
        countersteer: bool = True,
    ) -> None:
        """Enable drift mode for oversteer behavior.

        Args:
            drift_factor: Amount of drift (0 = grip, 1 = full slide)
            countersteer: Enable automatic countersteering
        """
        self.drift_config.enabled = True
        self.drift_config.drift_factor = drift_factor
        self.drift_config.countersteer_enabled = countersteer

    def disable_drift_mode(self) -> None:
        """Disable drift mode."""
        self.drift_config.enabled = False

    def apply_drift_rotation(
        self,
        base_rotation: float,
        speed: float,
        throttle: float = 0.0,
    ) -> float:
        """Apply drift rotation to steering input.

        Args:
            base_rotation: Base steering rotation in degrees
            speed: Current speed in m/s
            throttle: Throttle input (-1 to 1)

        Returns:
            Modified rotation for drift effect
        """
        if not self.drift_config.enabled:
            return base_rotation

        # Drift adds oversteer based on speed and steering input
        drift_amount = (
            abs(base_rotation)
            * speed
            * self.drift_config.drift_factor
            * 0.1
        )

        # Countersteer effect
        if self.drift_config.countersteer_enabled:
            drift_amount *= (1 - abs(throttle) * 0.3)

        # Apply in direction of steering
        sign = 1 if base_rotation >= 0 else -1
        return base_rotation + drift_amount * sign

    def simulate_jump(
        self,
        launch_velocity: tuple[float, float, float],
        rotation_axis: tuple[float, float, float] = (1, 0, 0),
        rotation_speed: float = 0.0,
        frame_start: Optional[int] = None,
    ) -> tuple[int, int]:
        """Simulate a jump trajectory.

        Args:
            launch_velocity: Initial velocity (vx, vy, vz) in m/s
            rotation_axis: Axis of rotation during jump
            rotation_speed: Rotation speed in radians/second
            frame_start: Start frame (current if None)

        Returns:
            Tuple of (start_frame, end_frame) for the jump
        """
        if not BLENDER_AVAILABLE:
            return (0, 0)

        armature = self.rig.rig_objects.get("armature")
        if not armature:
            return (0, 0)

        start_frame = frame_start or bpy.context.scene.frame_current
        fps = bpy.context.scene.render.fps

        # Calculate flight time (using vz and gravity)
        vx, vy, vz = launch_velocity
        g = self.jump_config.gravity

        # Time to apex: t_apex = vz / g
        # Total time: t_total = 2 * t_apex (symmetric)
        # Handle non-symmetric with landing height detection
        flight_time = 2 * vz / g if g > 0 else 2.0
        end_frame = start_frame + int(flight_time * fps)

        # Get starting position
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Animate trajectory
        for frame in range(start_frame, end_frame + 1):
            t = (frame - start_frame) / fps

            # Position: p = p0 + v*t + 0.5*a*t^2
            # For z: z = z0 + vz*t - 0.5*g*t^2
            x = start_pos.x + vx * t
            y = start_pos.y + vy * t
            z = start_pos.z + vz * t - 0.5 * g * t * t

            armature.location = (x, y, z)
            armature.keyframe_insert(data_path="location", frame=frame)

            # Rotation during jump
            if rotation_speed > 0:
                angle = rotation_speed * t
                # Apply rotation around axis
                armature.rotation_euler = self._calculate_rotation(
                    rotation_axis, angle
                )
                armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return (start_frame, end_frame)

    def _calculate_rotation(
        self,
        axis: tuple[float, float, float],
        angle: float,
    ) -> tuple[float, float, float]:
        """Calculate Euler rotation from axis-angle.

        Args:
            axis: Rotation axis (normalized)
            angle: Rotation angle in radians

        Returns:
            Euler angles (XYZ)
        """
        if not BLENDER_AVAILABLE:
            return (0, 0, 0)

        quat = Quaternion(Vector(axis), angle)
        return quat.to_euler("XYZ")

    def offroad_mode(
        self,
        roughness: float = 0.5,
        suspension_travel: float = 0.4,
    ) -> None:
        """Enable offroad driving mode.

        Adjusts suspension and adds terrain-affected movement.

        Args:
            roughness: Terrain roughness (0 = smooth, 1 = very rough)
            suspension_travel: Suspension travel in meters
        """
        self.offroad_config.enabled = True
        self.offroad_config.roughness = roughness
        self.offroad_config.suspension_travel_multiplier = (
            suspension_travel / 0.3  # Normalize to base travel
        )

    def disable_offroad_mode(self) -> None:
        """Disable offroad mode."""
        self.offroad_config.enabled = False

    def get_acceleration_distance(
        self,
        target_speed: float,
        current_speed: float = 0.0,
    ) -> float:
        """Calculate distance needed to reach target speed.

        Args:
            target_speed: Desired speed in m/s
            current_speed: Current speed in m/s

        Returns:
            Distance in meters
        """
        delta_v = target_speed - current_speed
        if abs(delta_v) < 0.1:
            return 0.0

        # Use kinematic equation: v^2 = v0^2 + 2*a*d
        # Assume constant acceleration at 50% engine power
        force = self.config.engine_power / max(target_speed, 1.0) * 0.5
        drag = self.calculate_drag_force((target_speed + current_speed) / 2)
        net_force = force - drag
        acceleration = net_force / self.config.mass

        if acceleration <= 0:
            return float("inf")

        distance = (target_speed ** 2 - current_speed ** 2) / (2 * acceleration)
        return distance

    def get_braking_distance(
        self,
        current_speed: float,
        target_speed: float = 0.0,
    ) -> float:
        """Calculate distance needed to brake.

        Args:
            current_speed: Current speed in m/s
            target_speed: Target speed in m/s

        Returns:
            Braking distance in meters
        """
        delta_v = current_speed - target_speed
        if delta_v <= 0:
            return 0.0

        deceleration = self.config.braking_force / self.config.mass
        distance = (current_speed ** 2 - target_speed ** 2) / (2 * deceleration)
        return distance


class SpeedSegments:
    """Speed-based animation workflow.

    Allows defining animation by specifying speed targets at
    different frame ranges, with automatic interpolation.

    Example:
        rig = LaunchControlRig(vehicle_body)
        physics = VehiclePhysics(rig)

        segments = SpeedSegments(rig)

        # Add speed segments
        segments.add_segment(1, 60, target_speed=20.0)  # Accelerate
        segments.add_segment(61, 120, target_speed=20.0)  # Cruise
        segments.add_segment(121, 180, target_speed=0.0)  # Brake

        # Generate animation
        segments.generate_animation()
    """

    def __init__(self, rig: "LaunchControlRig"):
        """Initialize speed segments system.

        Args:
            rig: The LaunchControlRig instance
        """
        self.rig = rig
        self.segments: list[SpeedSegment] = []
        self.physics = VehiclePhysics(rig)

    def add_segment(
        self,
        frame_start: int,
        frame_end: int,
        target_speed: float,
        acceleration: Optional[float] = None,
    ) -> SpeedSegment:
        """Add a speed segment.

        Args:
            frame_start: Start frame
            frame_end: End frame
            target_speed: Target speed in m/s
            acceleration: Optional specific acceleration (auto if None)

        Returns:
            Created SpeedSegment
        """
        segment = SpeedSegment(
            frame_start=frame_start,
            frame_end=frame_end,
            target_speed=target_speed,
            acceleration=acceleration,
        )
        self.segments.append(segment)
        return segment

    def clear_segments(self) -> None:
        """Clear all segments."""
        self.segments.clear()

    def generate_animation(self) -> dict[str, Any]:
        """Generate animation from speed segments.

        Creates keyframes for vehicle movement based on
        defined speed segments.

        Returns:
            Dictionary with generation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        if not self.segments:
            return {"success": False, "error": "No segments defined"}

        # Sort segments by start frame
        self.segments.sort(key=lambda s: s.frame_start)

        armature = self.rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps

        # Calculate speeds for each segment
        current_speed = 0.0
        total_distance = 0.0

        for i, segment in enumerate(self.segments):
            segment.current_speed = current_speed

            duration = (segment.frame_end - segment.frame_start) / fps

            # Calculate acceleration if auto
            if segment.acceleration is None:
                speed_delta = segment.target_speed - current_speed
                if duration > 0:
                    segment.acceleration = speed_delta / duration
                else:
                    segment.acceleration = 0.0

            # Calculate distance covered
            if segment.acceleration:
                # d = v0*t + 0.5*a*t^2
                distance = (
                    current_speed * duration
                    + 0.5 * segment.acceleration * duration * duration
                )
            else:
                distance = current_speed * duration

            total_distance += distance
            current_speed = segment.target_speed

        # Animate position along forward axis (Y in Blender vehicle convention)
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)
        current_distance = 0.0
        current_speed = 0.0

        for segment in self.segments:
            frames = segment.frame_end - segment.frame_start
            duration = frames / fps

            for frame_offset in range(frames + 1):
                frame = segment.frame_start + frame_offset
                t = frame_offset / fps

                # Current speed with acceleration
                if segment.acceleration:
                    speed = current_speed + segment.acceleration * t
                else:
                    speed = segment.target_speed

                # Distance traveled this frame
                if segment.acceleration:
                    d = current_speed * t + 0.5 * segment.acceleration * t * t
                else:
                    d = speed * t

                # Update position
                y = start_pos.y + current_distance + d
                armature.location = (start_pos.x, y, start_pos.z)
                armature.keyframe_insert(data_path="location", frame=frame)

            # Update for next segment
            if segment.acceleration:
                current_distance += (
                    current_speed * duration
                    + 0.5 * segment.acceleration * duration * duration
                )
            else:
                current_distance += current_speed * duration

            current_speed = segment.target_speed

        return {
            "success": True,
            "total_distance": total_distance,
            "segments": len(self.segments),
            "final_speed": current_speed,
        }

    def get_segment_at_frame(self, frame: int) -> Optional[SpeedSegment]:
        """Get segment active at given frame.

        Args:
            frame: Frame number

        Returns:
            SpeedSegment or None
        """
        for segment in self.segments:
            if segment.frame_start <= frame <= segment.frame_end:
                return segment
        return None

    def get_speed_at_frame(self, frame: int) -> float:
        """Calculate speed at given frame.

        Args:
            frame: Frame number

        Returns:
            Speed in m/s
        """
        segment = self.get_segment_at_frame(frame)
        if not segment:
            return 0.0

        t = (frame - segment.frame_start) / (
            segment.frame_end - segment.frame_start
        ) if segment.frame_end > segment.frame_start else 0

        if segment.acceleration:
            return segment.current_speed + segment.acceleration * t
        return segment.target_speed
