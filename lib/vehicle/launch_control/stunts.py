"""
Stunt Driving Presets for Launch Control

Advanced stunt animations including barrel rolls, J-turns, bootleg turns,
two-wheel driving, and coordinated chase sequences.

Usage:
    from lib.vehicle.launch_control.stunts import StuntPresets

    rig = LaunchControlRig(vehicle_body)
    rig.one_click_rig()

    # Barrel roll
    StuntPresets.barrel_roll(rig, jump_height=3.0, rotations=1.0)

    # J-turn (reverse 180)
    StuntPresets.j_turn(rig, direction="left")

    # Bootleg turn (forward 180)
    StuntPresets.bootleg_turn(rig, speed=20.0)

    # Two-wheel driving
    StuntPresets.two_wheel_drive(rig, duration=120, side="left")

    # Coordinated chase sequence
    StuntPresets.chase_sequence(rig, scenario="urban_pursuit")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from enum import Enum

try:
    import bpy
    from mathutils import Vector, Matrix, Euler, Quaternion
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None
    Vector = Any
    Matrix = Any
    Euler = Any
    Quaternion = Any

if TYPE_CHECKING:
    from .auto_rig import LaunchControlRig


class StuntType(Enum):
    """Types of stunt maneuvers."""
    BARREL_ROLL = "barrel_roll"
    J_TURN = "j_turn"               # Reverse 180
    BOOTLEG_TURN = "bootleg"        # Forward 180
    TWO_WHEEL = "two_wheel"
    HAND_BRAKE_TURN = "handbrake"
    POWERSLIDE = "powerslide"
    ROCKFORD = "rockford"           # Reverse J-turn
    IMMELMANN = "immelmann"         # Jump with half roll
    SPLIT_S = "split_s"             # Dive and roll


@dataclass
class StuntConfig:
    """Base configuration for stunts."""
    frame_start: int = 1
    approach_frames: int = 30
    recovery_frames: int = 30


@dataclass
class BarrelRollConfig(StuntConfig):
    """Barrel roll stunt configuration."""
    rotations: float = 1.0          # Number of full rotations
    jump_height: float = 2.0        # Jump apex height
    jump_distance: float = 15.0     # Horizontal distance
    approach_speed: float = 20.0    # m/s
    axis: str = "longitudinal"      # longitudinal (X) or lateral (Y)


@dataclass
class JTurnConfig(StuntConfig):
    """J-turn (reverse 180) configuration."""
    direction: str = "left"         # left or right
    reverse_speed: float = 8.0      # m/s
    pivot_frames: int = 20          # Frames for rotation
    exit_speed: float = 15.0        # m/s forward


@dataclass
class BootlegConfig(StuntConfig):
    """Bootleg turn (forward 180) configuration."""
    direction: str = "left"
    entry_speed: float = 25.0       # m/s
    slide_angle: float = 45.0       # degrees
    rotation_frames: int = 25


@dataclass
class TwoWheelConfig(StuntConfig):
    """Two-wheel driving configuration."""
    side: str = "left"              # left or right
    duration: int = 120             # Frames on two wheels
    tilt_angle: float = 35.0        # degrees from horizontal
    speed: float = 12.0             # m/s


@dataclass
class ChaseSequenceConfig(StuntConfig):
    """Chase sequence configuration."""
    scenario: str = "urban_pursuit"
    duration: int = 600             # Total frames
    hero_stunts: List[str] = field(default_factory=list)
    near_miss_count: int = 3
    pedestrian_dodges: int = 5


class StuntPresets:
    """
    Advanced stunt driving presets.

    Provides static methods for creating dramatic vehicle stunts
    with proper physics and animation.
    """

    @staticmethod
    def barrel_roll(
        rig: "LaunchControlRig",
        rotations: float = 1.0,
        jump_height: float = 2.0,
        jump_distance: float = 15.0,
        approach_speed: float = 20.0,
        frame_start: int = 1,
    ) -> Dict[str, Any]:
        """
        Create barrel roll stunt (jump with rotation).

        Args:
            rig: LaunchControlRig instance
            rotations: Number of full rotations
            jump_height: Apex height in meters
            jump_distance: Horizontal jump distance
            approach_speed: Speed approaching ramp
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
        start_pos = Vector(armature.location) if hasattr(armature.location, "__iter__") else Vector((0, 0, 0))

        # Physics calculations
        g = 9.81  # gravity
        ramp_angle = math.atan2(jump_height * 2, jump_distance)  # Approximate ramp angle

        # Time of flight (simplified ballistic)
        vertical_speed = approach_speed * math.sin(ramp_angle)
        flight_time = 2 * vertical_speed / g
        flight_frames = int(flight_time * fps)

        # Approach phase
        approach_distance = 15.0
        approach_frames = int(approach_distance / approach_speed * fps)

        # Phase 1: Approach
        for frame in range(frame_start, frame_start + approach_frames):
            t = (frame - frame_start) / fps
            y = start_pos.y + approach_speed * t

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 2: Jump with rotation
        jump_start_frame = frame_start + approach_frames
        jump_start_pos = Vector((
            start_pos.x,
            start_pos.y + approach_distance,
            start_pos.z,
        ))

        for frame in range(jump_start_frame, jump_start_frame + flight_frames + 1):
            t = (frame - jump_start_frame) / fps

            # Ballistic trajectory
            horizontal_progress = approach_speed * math.cos(ramp_angle) * t
            vertical_pos = vertical_speed * t - 0.5 * g * t * t

            armature.location = (
                start_pos.x,
                jump_start_pos.y + horizontal_progress,
                start_pos.z + vertical_pos,
            )
            armature.keyframe_insert(data_path="location", frame=frame)

            # Rotation during jump
            rotation_progress = t / flight_time
            roll = rotations * 2 * math.pi * rotation_progress

            armature.rotation_euler = Euler((roll, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 3: Landing and recovery
        landing_frame = jump_start_frame + flight_frames
        landing_pos = armature.location.copy()

        recovery_frames = 20
        for frame in range(landing_frame, landing_frame + recovery_frames):
            t = (frame - landing_frame) / fps

            # Continue forward motion
            armature.location = (
                landing_pos.x,
                landing_pos.y + approach_speed * 0.8 * t,
                landing_pos.z,
            )
            armature.keyframe_insert(data_path="location", frame=frame)

            # Settle rotation
            settle = 1 - t / (recovery_frames / fps)
            armature.rotation_euler = Euler((settle * 0.1, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": landing_frame + recovery_frames,
            "rotations": rotations,
            "flight_frames": flight_frames,
            "max_height": vertical_speed ** 2 / (2 * g),
        }

    @staticmethod
    def j_turn(
        rig: "LaunchControlRig",
        direction: str = "left",
        reverse_speed: float = 8.0,
        exit_speed: float = 15.0,
        frame_start: int = 1,
    ) -> Dict[str, Any]:
        """
        Create J-turn (reverse 180 degree turn).

        The classic movie stunt: reverse, spin 180, drive away forward.

        Args:
            rig: LaunchControlRig instance
            direction: Turn direction ("left" or "right")
            reverse_speed: Speed while reversing
            exit_speed: Speed after turn
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
        start_pos = Vector(armature.location) if hasattr(armature.location, "__iter__") else Vector((0, 0, 0))

        direction_sign = 1 if direction.lower() == "left" else -1

        # Phase 1: Reverse straight
        reverse_frames = 40
        for frame in range(frame_start, frame_start + reverse_frames):
            t = (frame - frame_start) / fps
            y = start_pos.y - reverse_speed * t

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            # Facing backward
            armature.rotation_euler = Euler((0, 0, math.pi), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 2: Pivot (180 spin)
        pivot_start = frame_start + reverse_frames
        pivot_frames = 25
        pivot_center = Vector(armature.location)

        for frame in range(pivot_start, pivot_start + pivot_frames):
            progress = (frame - pivot_start) / pivot_frames
            # Ease in-out for rotation
            ease = 0.5 - 0.5 * math.cos(progress * math.pi)
            rotation = math.pi + ease * math.pi * direction_sign

            # Slight lateral movement during pivot
            lateral = direction_sign * 3.0 * ease

            armature.location = (
                start_pos.x + lateral,
                pivot_center.y,
                start_pos.z,
            )
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, rotation), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 3: Accelerate forward
        exit_start = pivot_start + pivot_frames
        exit_frames = 40
        exit_pos = Vector(armature.location)

        for frame in range(exit_start, exit_start + exit_frames):
            t = (frame - exit_start) / fps
            current_speed = exit_speed * min(1.0, t * 2)  # Accelerate
            y = exit_pos.y + current_speed * t

            armature.location = (exit_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            # Now facing forward
            armature.rotation_euler = Euler((0, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": exit_start + exit_frames,
            "direction": direction,
            "total_rotation": 180,
        }

    @staticmethod
    def bootleg_turn(
        rig: "LaunchControlRig",
        direction: str = "left",
        entry_speed: float = 25.0,
        frame_start: int = 1,
    ) -> Dict[str, Any]:
        """
        Create bootleg turn (forward 180 handbrake turn).

        Args:
            rig: LaunchControlRig instance
            direction: Turn direction
            entry_speed: Entry speed
            frame_start: Starting frame

        Returns:
            Animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = Vector(armature.location) if hasattr(armature.location, "__iter__") else Vector((0, 0, 0))

        direction_sign = 1 if direction.lower() == "left" else -1

        # Phase 1: Approach
        approach_frames = 30
        for frame in range(frame_start, frame_start + approach_frames):
            t = (frame - frame_start) / fps
            y = start_pos.y + entry_speed * t

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 2: Slide and rotate
        slide_start = frame_start + approach_frames
        slide_frames = 30
        slide_pos = Vector(armature.location)

        for frame in range(slide_start, slide_start + slide_frames):
            progress = (frame - slide_start) / slide_frames
            ease = 0.5 - 0.5 * math.cos(progress * math.pi)

            # Continue forward (slowing)
            y = slide_pos.y + entry_speed * 0.3 * (1 - progress) * (frame - slide_start) / fps

            # Lateral slide
            x = start_pos.x + direction_sign * 5.0 * ease

            # Rotation
            rotation = ease * math.pi * direction_sign

            armature.location = (x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, rotation), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 3: Exit
        exit_start = slide_start + slide_frames
        exit_frames = 30
        exit_pos = Vector(armature.location)

        for frame in range(exit_start, exit_start + exit_frames):
            t = (frame - exit_start) / fps
            # Drive away in new direction
            y = exit_pos.y - 10.0 * t  # Back the way we came

            armature.location = (exit_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((0, 0, math.pi), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": exit_start + exit_frames,
            "direction": direction,
        }

    @staticmethod
    def two_wheel_drive(
        rig: "LaunchControlRig",
        duration: int = 120,
        side: str = "left",
        tilt_angle: float = 35.0,
        speed: float = 12.0,
        frame_start: int = 1,
    ) -> Dict[str, Any]:
        """
        Create two-wheel driving stunt.

        Vehicle drives on two wheels (tilted on side).

        Args:
            rig: LaunchControlRig instance
            duration: Frames on two wheels
            side: Side to tilt on
            tilt_angle: Degrees from horizontal
            speed: Driving speed
            frame_start: Starting frame

        Returns:
            Animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False, "error": "No armature found"}

        fps = bpy.context.scene.render.fps
        start_pos = Vector(armature.location) if hasattr(armature.location, "__iter__") else Vector((0, 0, 0))

        tilt_sign = 1 if side.lower() == "left" else -1
        tilt_rad = math.radians(tilt_angle) * tilt_sign

        # Phase 1: Tilt up
        tilt_up_frames = 30
        for frame in range(frame_start, frame_start + tilt_up_frames):
            t = (frame - frame_start) / fps
            progress = (frame - frame_start) / tilt_up_frames
            ease = 0.5 - 0.5 * math.cos(progress * math.pi)

            y = start_pos.y + speed * t * 0.5
            roll = tilt_rad * ease

            armature.location = (start_pos.x, y, start_pos.z)
            armature.keyframe_insert(data_path="location", frame=frame)
            armature.rotation_euler = Euler((roll, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 2: Drive on two wheels
        tilt_pos = Vector(armature.location)
        two_wheel_start = frame_start + tilt_up_frames

        for frame in range(two_wheel_start, two_wheel_start + duration):
            t = (frame - two_wheel_start) / fps

            # Gentle weave while on two wheels
            weave = math.sin(t * 2) * 0.5

            armature.location = (
                start_pos.x + weave,
                tilt_pos.y + speed * t,
                start_pos.z,
            )
            armature.keyframe_insert(data_path="location", frame=frame)

            # Slight roll variation
            roll = tilt_rad + math.sin(t * 3) * 0.05
            armature.rotation_euler = Euler((roll, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        # Phase 3: Settle down
        end_pos = Vector(armature.location)
        settle_start = two_wheel_start + duration
        settle_frames = 30

        for frame in range(settle_start, settle_start + settle_frames):
            t = (frame - settle_start) / fps
            progress = (frame - settle_start) / settle_frames
            ease = 1 - (0.5 - 0.5 * math.cos(progress * math.pi))

            armature.location = (
                start_pos.x,
                end_pos.y + speed * t,
                start_pos.z,
            )
            armature.keyframe_insert(data_path="location", frame=frame)

            # Return to level
            roll = tilt_rad * (1 - ease)
            armature.rotation_euler = Euler((roll, 0, 0), "XYZ")
            armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": settle_start + settle_frames,
            "side": side,
            "tilt_angle": tilt_angle,
            "duration_on_two_wheels": duration,
        }

    @staticmethod
    def chase_sequence(
        rig: "LaunchControlRig",
        scenario: str = "urban_pursuit",
        duration: int = 600,
        frame_start: int = 1,
    ) -> Dict[str, Any]:
        """
        Create coordinated chase sequence with multiple stunts.

        Args:
            rig: LaunchControlRig instance
            scenario: Predefined chase scenario
            duration: Total sequence duration
            frame_start: Starting frame

        Returns:
            Animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        # Scenario definitions
        scenarios = {
            "urban_pursuit": [
                ("drive", 60),
                ("drift_left", 30),
                ("drive", 60),
                ("near_miss", 20),
                ("drift_right", 30),
                ("drive", 60),
                ("handbrake_turn", 40),
                ("drive", 100),
                ("j_turn", 80),
                ("escape", 120),
            ],
            "highway_chase": [
                ("drive", 80),
                ("weave", 60),
                ("drive", 60),
                ("pit_maneuver", 40),
                ("spin", 60),
                ("recover", 40),
                ("drive", 120),
                ("barrier_dodge", 30),
                ("escape", 70),
            ],
            "parking_garage": [
                ("drive", 40),
                ("tight_turn", 30),
                ("drive", 40),
                ("drift_left", 25),
                ("drive", 40),
                ("bootleg", 50),
                ("drive", 60),
                ("exit_ramp", 40),
                ("jump", 60),
                ("land", 30),
            ],
        }

        actions = scenarios.get(scenario, scenarios["urban_pursuit"])

        # Apply each action
        current_frame = frame_start
        action_results = []

        for action_name, action_frames in actions:
            result = StuntPresets._apply_chase_action(
                rig, action_name, action_frames, current_frame
            )
            action_results.append({
                "action": action_name,
                "frames": action_frames,
                "start_frame": current_frame,
                "end_frame": current_frame + action_frames,
            })
            current_frame += action_frames

        return {
            "success": True,
            "scenario": scenario,
            "frame_start": frame_start,
            "frame_end": current_frame,
            "actions": action_results,
        }

    @staticmethod
    def _apply_chase_action(
        rig: "LaunchControlRig",
        action: str,
        frames: int,
        frame_start: int,
    ) -> Dict[str, Any]:
        """Apply a single chase action."""
        if not BLENDER_AVAILABLE:
            return {"success": False}

        armature = rig.rig_objects.get("armature")
        if not armature:
            return {"success": False}

        fps = bpy.context.scene.render.fps
        start_pos = Vector(armature.location)
        start_rot = Euler(armature.rotation_euler)

        if action == "drive":
            speed = 15.0
            for frame in range(frame_start, frame_start + frames):
                t = (frame - frame_start) / fps
                armature.location = (start_pos.x, start_pos.y + speed * t, start_pos.z)
                armature.keyframe_insert(data_path="location", frame=frame)
                armature.rotation_euler = start_rot
                armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        elif action == "drift_left" or action == "drift_right":
            direction = 1 if "left" in action else -1
            drift_angle = math.radians(25) * direction
            for frame in range(frame_start, frame_start + frames):
                progress = (frame - frame_start) / frames
                t = (frame - frame_start) / fps
                speed = 12.0

                armature.location = (start_pos.x + direction * 3.0 * progress,
                                    start_pos.y + speed * t, start_pos.z)
                armature.keyframe_insert(data_path="location", frame=frame)

                rot = math.atan2(direction * 3.0, speed * frames / fps)
                armature.rotation_euler = Euler((0, 0, rot), "XYZ")
                armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        elif action == "near_miss":
            for frame in range(frame_start, frame_start + frames):
                progress = (frame - frame_start) / frames
                t = (frame - frame_start) / fps
                speed = 15.0

                # Swerve
                swerve = math.sin(progress * math.pi) * 2.0
                armature.location = (start_pos.x + swerve,
                                    start_pos.y + speed * t, start_pos.z)
                armature.keyframe_insert(data_path="location", frame=frame)

                heading = math.atan2(math.cos(progress * math.pi) * 2.0 * math.pi / (frames / fps), speed)
                armature.rotation_euler = Euler((0, 0, heading), "XYZ")
                armature.keyframe_insert(data_path="rotation_euler", frame=frame)

        return {"success": True, "action": action}

    @staticmethod
    def list_stunts() -> List[str]:
        """List available stunt presets."""
        return [
            "barrel_roll",
            "j_turn",
            "bootleg_turn",
            "two_wheel_drive",
            "chase_sequence",
        ]


__all__ = [
    "StuntPresets",
    "StuntType",
    "StuntConfig",
    "BarrelRollConfig",
    "JTurnConfig",
    "BootlegConfig",
    "TwoWheelConfig",
    "ChaseSequenceConfig",
]
