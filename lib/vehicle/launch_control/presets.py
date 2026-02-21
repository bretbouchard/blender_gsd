"""
Animation Presets for Launch Control

Pre-built animation presets for common vehicle maneuvers
including drifts, jumps, slaloms, and more.

Features:
- Drift donut animation
- Figure-eight driving pattern
- Slalom course navigation
- Jump ramp simulation
- Offroad bouncing behavior
- Emergency braking
- Acceleration squat effect
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Union

# Type hints for Blender API (runtime optional)
try:
    import bpy
    from mathutils import Vector, Matrix, Euler

    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None  # type: ignore
    Vector = Any  # type: ignore
    Matrix = Any  # type: ignore
    Euler = Any  # type: ignore

if TYPE_CHECKING:
    from .auto_rig import LaunchControlRig
    from .steering import SteeringSystem
    from .suspension import SuspensionSystem
    from .physics import VehiclePhysics


@dataclass
class PresetConfig:
    """Base configuration for animation presets."""

    frame_start: int = 1
    ease_frames: int = 10  # Frames for easing in/out


@dataclass
class DriftDonutConfig(PresetConfig):
    """Configuration for drift donut animation."""

    duration: int = 120  # Total frames
    direction: str = "left"  # "left" or "right"
    radius: float = 8.0  # Donut radius in meters
    speed: float = 12.0  # m/s
    drift_angle: float = 30.0  # degrees
    countersteer: float = 15.0  # degrees


@dataclass
class FigureEightConfig(PresetConfig):
    """Configuration for figure-eight animation."""

    duration: int = 240  # Total frames
    radius: float = 10.0  # Loop radius in meters
    speed: float = 15.0  # m/s
    crossover_frames: int = 20  # Frames at crossover point


@dataclass
class SlalomConfig(PresetConfig):
    """Configuration for slalom course animation."""

    cone_count: int = 5
    spacing: float = 10.0  # meters between cones
    speed: float = 18.0  # m/s
    weave_angle: float = 25.0  # degrees


@dataclass
class JumpRampConfig(PresetConfig):
    """Configuration for jump ramp animation."""

    approach_speed: float = 15.0  # m/s
    ramp_angle: float = 30.0  # degrees
    ramp_length: float = 5.0  # meters
    rotation_during_jump: float = 0.0  # radians total


@dataclass
class OffroadBounceConfig(PresetConfig):
    """Configuration for offroad bounce animation."""

    duration: int = 120
    roughness: float = 0.3  # 0-1 roughness factor
    speed: float = 8.0  # m/s
    suspension_travel: float = 0.4  # meters


@dataclass
class EmergencyBrakeConfig(PresetConfig):
    """Configuration for emergency brake animation."""

    initial_speed: float = 20.0  # m/s
    brake_frame: int = 60
    brake_force: float = 30000.0  # Newtons


@dataclass
class AccelerationSquatConfig(PresetConfig):
    """Configuration for acceleration squat animation."""

    acceleration: float = 5.0  # m/s^2
    duration: int = 60
    max_squat: float = 0.05  # meters


class AnimationPresets:
    """Pre-built animation presets for vehicle maneuvers.

    Provides static methods for creating common vehicle animations
    with configurable parameters.

    Example:
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        # Drift donut
        AnimationPresets.drift_donut(rig, duration=120, direction="left")

        # Figure eight
        AnimationPresets.figure_eight(rig, duration=240)

        # Slalom course
        AnimationPresets.slalom(rig, cone_count=5, spacing=10.0)

        # Jump ramp
        AnimationPresets.jump_ramp(rig, approach_speed=15.0, ramp_angle=30.0)

        # Offroad bouncing
        AnimationPresets.offroad_bounce(rig, roughness=0.3)

        # Emergency brake
        AnimationPresets.emergency_brake(rig, initial_speed=20.0, frame=60)

        # Acceleration squat
        AnimationPresets.acceleration_squat(rig, acceleration=5.0)
    """

    @staticmethod
    def drift_donut(
        rig: "LaunchControlRig",
        duration: int = 120,
        direction: str = "left",
        radius: float = 8.0,
        speed: float = 12.0,
        frame_start: int = 1,
    ) -> dict[str, Any]:
        """Create a drift donut animation.

        Animates the vehicle in a continuous circular drift pattern
        with appropriate body rotation and suspension response.

        Args:
            rig: The LaunchControlRig instance
            duration: Total animation duration in frames
            direction: Drift direction - "left" or "right"
            radius: Radius of the donut circle in meters
            speed: Vehicle speed in m/s
            frame_start: Starting frame

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        direction_sign = -1 if direction.lower() == "left" else 1

        # Calculate angular velocity
        circumference = 2 * math.pi * radius
        angular_velocity = speed / radius * direction_sign

        # Get starting position
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)
        center = Vector((start_pos.x, start_pos.y - radius * direction_sign, start_pos.z))

        # Animate full rotation
        for frame in range(frame_start, frame_start + duration):
            t = (frame - frame_start) / fps
            angle = angular_velocity * t

            # Position on circle
            x = center.x + radius * math.sin(angle)
            y = center.y + radius * math.cos(angle)

            armature.location = (x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)

            # Rotation - car points tangent to circle plus drift angle
            heading = angle + math.pi / 2  # Tangent direction
            drift_offset = math.radians(30 * direction_sign)  # Drift angle
            armature.rotation_euler = Euler((0, 0, heading + drift_offset), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_start + duration,
            "total_rotation": angular_velocity * duration / fps,
            "direction": direction,
        }

    @staticmethod
    def figure_eight(
        rig: "LaunchControlRig",
        duration: int = 240,
        radius: float = 10.0,
        speed: float = 15.0,
        frame_start: int = 1,
    ) -> dict[str, Any]:
        """Create a figure-eight driving pattern.

        Args:
            rig: The LaunchControlRig instance
            duration: Total animation duration in frames
            radius: Radius of each loop in meters
            speed: Vehicle speed in m/s
            frame_start: Starting frame

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Figure eight uses parametric curve
        # x = r * sin(t)
        # y = r * sin(t) * cos(t)  (Lemniscate approximation)

        for frame in range(frame_start, frame_start + duration):
            t = (frame - frame_start) / fps
            # Parameter for full figure eight
            param = 2 * math.pi * t / (duration / fps)  # Full rotation

            # Lemniscate of Bernoulli approximation
            scale = radius / (1 + math.sin(param) ** 2)
            x = start_pos.x + scale * math.cos(param)
            y = start_pos.y + scale * math.sin(param) * math.cos(param)

            armature.location = (x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)

            # Calculate heading from velocity direction
            dt = 0.01
            param_next = 2 * math.pi * (t + dt) / (duration / fps)
            scale_next = radius / (1 + math.sin(param_next) ** 2)
            x_next = start_pos.x + scale_next * math.cos(param_next)
            y_next = start_pos.y + scale_next * math.sin(param_next) * math.cos(param_next)

            heading = math.atan2(y_next - y, x_next - x)
            armature.rotation_euler = Euler((0, 0, heading), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_start + duration,
            "radius": radius,
        }

    @staticmethod
    def slalom(
        rig: "LaunchControlRig",
        cone_count: int = 5,
        spacing: float = 10.0,
        speed: float = 18.0,
        weave_angle: float = 25.0,
        frame_start: int = 1,
    ) -> dict[str, Any]:
        """Create a slalom course navigation animation.

        Args:
            rig: The LaunchControlRig instance
            cone_count: Number of cones to weave through
            spacing: Distance between cones in meters
            speed: Vehicle speed in m/s
            weave_angle: Maximum steering angle in degrees
            frame_start: Starting frame

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Calculate total distance and frames
        total_distance = spacing * (cone_count - 1)
        duration = int(total_distance / speed * fps)

        # Weave pattern: alternate left/right
        weave_amplitude = spacing / 3  # Lateral movement

        for frame in range(frame_start, frame_start + duration):
            t = (frame - frame_start) / fps
            progress = t * speed  # Distance traveled

            # Forward progress
            y = start_pos.y + progress

            # Lateral weave (sine wave)
            weave_freq = (cone_count - 1) / total_distance * 2 * math.pi
            x = start_pos.x + weave_amplitude * math.sin(weave_freq * progress)

            armature.location = (x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)

            # Heading follows weave direction
            heading = math.atan2(
                weave_amplitude * weave_freq * math.cos(weave_freq * progress) * speed,
                speed
            )
            armature.rotation_euler = Euler((0, 0, heading), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_start + duration,
            "cone_count": cone_count,
            "total_distance": total_distance,
        }

    @staticmethod
    def jump_ramp(
        rig: "LaunchControlRig",
        approach_speed: float = 15.0,
        ramp_angle: float = 30.0,
        ramp_length: float = 5.0,
        rotation_during_jump: float = 0.0,
        frame_start: int = 1,
    ) -> dict[str, Any]:
        """Create a jump ramp animation with ballistic trajectory.

        Args:
            rig: The LaunchControlRig instance
            approach_speed: Speed approaching ramp in m/s
            ramp_angle: Launch angle in degrees
            ramp_length: Length of ramp in meters
            rotation_during_jump: Total rotation during jump in radians
            frame_start: Starting frame

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        g = 9.81  # Gravity

        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Approach phase
        approach_distance = 20.0  # meters before ramp
        approach_frames = int(approach_distance / approach_speed * fps)

        for frame in range(frame_start, frame_start + approach_frames):
            t = (frame - frame_start) / fps
            y = start_pos.y + approach_speed * t

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Launch phase (on ramp)
        launch_frame = frame_start + approach_frames
        ramp_frames = int(ramp_length / approach_speed * fps)
        ramp_angle_rad = math.radians(ramp_angle)

        for frame in range(launch_frame, launch_frame + ramp_frames):
            t = (frame - launch_frame) / fps
            distance = approach_speed * t
            height = distance * math.tan(ramp_angle_rad)

            armature.location = (
                start_pos.x,
                start_pos.y + approach_distance + distance,
                start_pos.z + height,
            )
            armature.keyframe_insert(data_path="location", frame=frame)
            # Pitch up on ramp
            armature.rotation_euler = Euler((ramp_angle_rad, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Flight phase
        flight_start_frame = launch_frame + ramp_frames
        launch_pos = (
            start_pos.x,
            start_pos.y + approach_distance + ramp_length,
            start_pos.z + ramp_length * math.tan(ramp_angle_rad),
        )

        # Launch velocity components
        vx = approach_speed * math.cos(ramp_angle_rad)
        vy = approach_speed * math.sin(ramp_angle_rad)

        # Time of flight
        flight_time = 2 * vy / g
        flight_frames = int(flight_time * fps)

        for frame in range(flight_start_frame, flight_start_frame + flight_frames + 1):
            t = (frame - flight_start_frame) / fps

            # Ballistic trajectory
            x = launch_pos[0] + vx * t
            y = launch_pos[1] + vx * t  # Forward motion continues
            z = launch_pos[2] + vy * t - 0.5 * g * t * t

            armature.location = (x, y, max(z, start_pos.z))
            armature.keyframe_insert(data_path="location", frame=frame)

            # Rotation during jump
            if rotation_during_jump != 0:
                rotation_progress = t / flight_time
                current_rotation = rotation_during_jump * rotation_progress
                armature.rotation_euler = Euler((current_rotation, 0, 0), "XYZ")
                armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        end_frame = flight_start_frame + flight_frames

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": end_frame,
            "approach_frames": approach_frames,
            "ramp_frames": ramp_frames,
            "flight_frames": flight_frames,
            "max_height": launch_pos[2] + vy * vy / (2 * g),
        }

    @staticmethod
    def offroad_bounce(
        rig: "LaunchControlRig",
        duration: int = 120,
        roughness: float = 0.3,
        speed: float = 8.0,
        frame_start: int = 1,
    ) -> dict[str, Any]:
        """Create offroad bouncing animation.

        Simulates suspension response to rough terrain.

        Args:
            rig: The LaunchControlRig instance
            duration: Animation duration in frames
            roughness: Terrain roughness factor (0-1)
            speed: Vehicle speed in m/s
            frame_start: Starting frame

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Bounce parameters
        bounce_freq = 3.0  # Hz
        bounce_amplitude = 0.05 * roughness  # meters

        for frame in range(frame_start, frame_start + duration):
            t = (frame - frame_start) / fps

            # Forward motion
            y = start_pos.y + speed * t

            # Random-ish bounce using multiple sine waves
            bounce = (
                bounce_amplitude * math.sin(2 * math.pi * bounce_freq * t) +
                bounce_amplitude * 0.5 * math.sin(2 * math.pi * bounce_freq * 1.3 * t + 0.5) +
                bounce_amplitude * 0.3 * math.sin(2 * math.pi * bounce_freq * 0.7 * t + 1.2)
            )

            # Pitch variation
            pitch = roughness * 0.05 * math.sin(2 * math.pi * bounce_freq * 0.8 * t)

            # Roll variation
            roll = roughness * 0.03 * math.sin(2 * math.pi * bounce_freq * 1.1 * t + 0.3)

            armature.location = (start_pos.x, y, start_pos.z + bounce)
            armature.keyframe_insert(data_path="location", frame=frame)

            armature.rotation_euler = Euler((roll, pitch, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_start + duration,
            "roughness": roughness,
            "max_bounce": bounce_amplitude * 1.8,  # Approximate max
        }

    @staticmethod
    def emergency_brake(
        rig: "LaunchControlRig",
        initial_speed: float = 20.0,
        brake_frame: int = 60,
        frame_start: int = 1,
    ) -> dict[str, Any]:
        """Create emergency braking animation with weight transfer.

        Args:
            rig: The LaunchControlRig instance
            initial_speed: Initial speed in m/s
            brake_frame: Frame when braking starts
            frame_start: Starting frame

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Braking deceleration
        deceleration = 10.0  # m/s^2 (roughly 1g)
        braking_distance = initial_speed ** 2 / (2 * deceleration)
        braking_frames = int(initial_speed / deceleration * fps)

        total_frames = brake_frame + braking_frames

        # Coast phase before braking
        for frame in range(frame_start, brake_frame):
            t = (frame - frame_start) / fps
            y = start_pos.y + initial_speed * t

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Braking phase with dive
        coast_distance = initial_speed * (brake_frame - frame_start) / fps
        current_speed = initial_speed

        for frame in range(brake_frame, total_frames + 1):
            t = (frame - brake_frame) / fps

            # Distance with deceleration
            distance = initial_speed * t - 0.5 * deceleration * t * t
            current_speed = max(0, initial_speed - deceleration * t)

            y = start_pos.y + coast_distance + distance

            # Dive angle based on deceleration
            dive = math.radians(3) * (current_speed / initial_speed)

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)

            # Nose dive
            armature.rotation_euler = Euler((0, dive, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": total_frames,
            "brake_frame": brake_frame,
            "stopping_distance": coast_distance + braking_distance,
        }

    @staticmethod
    def acceleration_squat(
        rig: "LaunchControlRig",
        acceleration: float = 5.0,
        duration: int = 60,
        frame_start: int = 1,
        max_squat: float = 0.05,
    ) -> dict[str, Any]:
        """Create acceleration squat animation.

        Simulates rear suspension compression during hard acceleration.

        Args:
            rig: The LaunchControlRig instance
            acceleration: Acceleration in m/s^2
            duration: Animation duration in frames
            frame_start: Starting frame
            max_squat: Maximum rear suspension compression in meters

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = armature.location.copy() if hasattr(armature.location, "copy") else Vector(armature.location)

        # Squat builds up and holds
        squat_buildup_frames = duration // 3
        hold_frames = duration // 3
        release_frames = duration - squat_buildup_frames - hold_frames

        for frame in range(frame_start, frame_start + duration):
            t = (frame - frame_start) / fps
            frame_offset = frame - frame_start

            # Calculate speed
            speed = acceleration * t

            # Calculate squat
            if frame_offset < squat_buildup_frames:
                # Building up
                progress = frame_offset / squat_buildup_frames
                # Ease-in
                squat = max_squat * (progress ** 2)
            elif frame_offset < squat_buildup_frames + hold_frames:
                # Holding
                squat = max_squat
            else:
                # Releasing
                progress = (frame_offset - squat_buildup_frames - hold_frames) / release_frames
                squat = max_squat * (1 - progress)

            # Position
            distance = 0.5 * acceleration * t * t
            y = start_pos.y + distance

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)

            # Pitch (rear down = squat)
            pitch = -math.asin(squat / 1.5) if squat > 0 else 0  # Approximate
            armature.rotation_euler = Euler((0, pitch, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_start + duration,
            "final_speed": acceleration * (duration / fps),
            "max_squat": max_squat,
        }

    @staticmethod
    def create_preset(
        rig: "LaunchControlRig",
        preset_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create animation from preset name.

        Args:
            rig: The LaunchControlRig instance
            preset_name: Name of preset to apply
            **kwargs: Preset-specific parameters

        Returns:
            Dictionary with animation results
        """
        preset_map = {
            "drift_donut": AnimationPresets.drift_donut,
            "figure_eight": AnimationPresets.figure_eight,
            "slalom": AnimationPresets.slalom,
            "jump_ramp": AnimationPresets.jump_ramp,
            "offroad_bounce": AnimationPresets.offroad_bounce,
            "emergency_brake": AnimationPresets.emergency_brake,
            "acceleration_squat": AnimationPresets.acceleration_squat,
        }

        if preset_name not in preset_map:
            return {
                "success": False,
                "error": f"Unknown preset: {preset_name}",
                "available": list(preset_map.keys()),
            }

        return preset_map[preset_name](rig, **kwargs)

    @staticmethod
    def list_presets() -> list[str]:
        """List available animation presets.

        Returns:
            List of preset names
        """
        return [
            "drift_donut",
            "figure_eight",
            "slalom",
            "jump_ramp",
            "offroad_bounce",
            "emergency_brake",
            "acceleration_squat",
        ]
