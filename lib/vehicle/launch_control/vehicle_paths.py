"""
Vehicle Path System - Advanced Path Following for Launch Control

Integrates road network routing with Launch Control's drive_path() system.
Adds speed curves, reverse driving, and stunt capabilities.

Features:
- Road network path generation
- Speed curve (ease-in/out) integration
- Reverse driving support
- Stunt path generation (jumps, drifts, barrel rolls)
- HUD/steering wheel data export

Usage:
    from lib.vehicle.launch_control.vehicle_paths import (
        VehiclePathSystem, SpeedCurve, PathType
    )

    # Create path system
    path_system = VehiclePathSystem()

    # Create path from road network
    path = path_system.create_path_from_route(
        road_network=network,
        start_node="intersection_1",
        end_node="intersection_5"
    )

    # Create path with speed curve
    path = path_system.create_path_with_speed(
        curve_object=my_curve,
        speed_curve=SpeedCurve.ease_in_out(5.0, 20.0, 5.0),
        reverse=False
    )

    # Apply to vehicle
    path_system.apply_to_vehicle(rig, path)

    # Generate stunt paths
    jump_path = path_system.create_jump_path(
        start=(0, 0, 0),
        jump_distance=20.0,
        jump_height=5.0,
        rotation=360  # Barrel roll
    )
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from pathlib import Path

# Type hints for Blender API
try:
    import bpy
    from mathutils import Vector, Matrix, Quaternion, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    bpy = None
    Vector = Any
    Matrix = Any
    Quaternion = Any
    Euler = Any

if TYPE_CHECKING:
    from .auto_rig import LaunchControlRig
    from .physics import VehiclePhysics


class PathType(Enum):
    """Type of vehicle path."""
    STANDARD = "standard"       # Normal driving
    REVERSE = "reverse"         # Backing up
    DRIFT = "drift"             # Drifting curve
    JUMP = "jump"               # Jump trajectory
    STUNT = "stunt"             # Complex stunt
    CHASE = "chase"             # Chase sequence


@dataclass
class SpeedCurve:
    """
    Defines speed variation along a path.

    Speed at position t (0-1) is interpolated between keyframes.
    """
    keyframes: List[Tuple[float, float]]  # (position, speed) pairs
    default_speed: float = 10.0

    @classmethod
    def constant(cls, speed: float) -> "SpeedCurve":
        """Create constant speed curve."""
        return cls(
            keyframes=[(0.0, speed), (1.0, speed)],
            default_speed=speed
        )

    @classmethod
    def ease_in(cls, start_speed: float, end_speed: float) -> "SpeedCurve":
        """Create ease-in speed curve (slow start, fast finish)."""
        return cls(
            keyframes=[
                (0.0, start_speed),
                (0.5, start_speed + (end_speed - start_speed) * 0.25),
                (1.0, end_speed)
            ],
            default_speed=end_speed
        )

    @classmethod
    def ease_out(cls, start_speed: float, end_speed: float) -> "SpeedCurve":
        """Create ease-out speed curve (fast start, slow finish)."""
        return cls(
            keyframes=[
                (0.0, start_speed),
                (0.5, start_speed + (end_speed - start_speed) * 0.75),
                (1.0, end_speed)
            ],
            default_speed=end_speed
        )

    @classmethod
    def ease_in_out(cls, start_speed: float, cruise_speed: float, end_speed: float) -> "SpeedCurve":
        """Create ease-in-out speed curve with cruise phase."""
        return cls(
            keyframes=[
                (0.0, start_speed),
                (0.2, cruise_speed),
                (0.8, cruise_speed),
                (1.0, end_speed)
            ],
            default_speed=cruise_speed
        )

    @classmethod
    def accelerate_brake(cls, max_speed: float, brake_point: float = 0.7) -> "SpeedCurve":
        """Create accelerate then brake curve."""
        return cls(
            keyframes=[
                (0.0, 0.0),
                (brake_point, max_speed),
                (1.0, 0.0)
            ],
            default_speed=max_speed
        )

    @classmethod
    def chicane(cls, base_speed: float, slow_speed: float, chicane_points: List[float]) -> "SpeedCurve":
        """Create speed curve for chicane (slow at corners)."""
        keyframes = [(0.0, base_speed)]
        for point in chicane_points:
            keyframes.append((point - 0.05, base_speed))
            keyframes.append((point, slow_speed))
            keyframes.append((point + 0.05, base_speed))
        keyframes.append((1.0, base_speed))
        return cls(keyframes=keyframes, default_speed=base_speed)

    def get_speed_at(self, t: float) -> float:
        """
        Get speed at position t (0-1) using linear interpolation.

        Args:
            t: Position along path (0-1)

        Returns:
            Speed in m/s
        """
        if not self.keyframes:
            return self.default_speed

        # Clamp t to valid range
        t = max(0.0, min(1.0, t))

        # Find surrounding keyframes
        prev_pos, prev_speed = self.keyframes[0]
        for pos, speed in self.keyframes:
            if pos >= t:
                # Interpolate between prev and current
                if pos == prev_pos:
                    return speed
                ratio = (t - prev_pos) / (pos - prev_pos)
                return prev_speed + ratio * (speed - prev_speed)
            prev_pos, prev_speed = pos, speed

        return self.keyframes[-1][1]

    def get_duration(self, path_length: float) -> float:
        """
        Calculate total duration for path with this speed curve.

        Uses numerical integration for accuracy.

        Args:
            path_length: Total path length in meters

        Returns:
            Duration in seconds
        """
        if path_length <= 0:
            return 0.0

        # Numerical integration
        steps = 100
        total_time = 0.0

        for i in range(steps):
            t = i / steps
            speed = self.get_speed_at(t)
            if speed > 0:
                segment_length = path_length / steps
                total_time += segment_length / speed

        return total_time


@dataclass
class VehiclePath:
    """
    Complete path definition for a vehicle.

    Includes the curve, speed profile, and metadata.
    """
    curve_object: Any  # Blender curve object
    path_type: PathType = PathType.STANDARD
    speed_curve: Optional[SpeedCurve] = None
    reverse: bool = False
    loop: bool = False

    # Path metadata
    name: str = "VehiclePath"
    length: float = 0.0
    duration: float = 0.0

    # Stunt parameters
    jump_height: float = 0.0
    rotation_count: float = 0.0  # Full rotations during path
    drift_angle: float = 0.0

    # Steering data for HUD
    steering_keyframes: List[Tuple[float, float]] = field(default_factory=list)  # (frame, angle)

    def get_frame_count(self, fps: int = 24) -> int:
        """Get total frame count for this path."""
        return int(self.duration * fps)


class VehiclePathSystem:
    """
    Advanced path following system for Launch Control.

    Creates and manages vehicle paths with speed curves, stunts,
    and road network integration.
    """

    def __init__(self):
        self.paths: Dict[str, VehiclePath] = {}
        self._active_path: Optional[VehiclePath] = None

    def create_path_from_curve(
        self,
        curve: Any,
        name: str = "Path",
        path_type: PathType = PathType.STANDARD,
        speed_curve: Optional[SpeedCurve] = None,
        reverse: bool = False,
    ) -> VehiclePath:
        """
        Create vehicle path from existing Blender curve.

        Args:
            curve: Blender curve object
            name: Path name
            path_type: Type of path
            speed_curve: Speed profile
            reverse: Drive in reverse

        Returns:
            VehiclePath object
        """
        if not BLENDER_AVAILABLE:
            return VehiclePath(curve_object=curve, name=name)

        # Calculate path length
        length = self._calculate_curve_length(curve)

        # Default speed curve if not provided
        if speed_curve is None:
            speed_curve = SpeedCurve.constant(10.0)

        # Calculate duration
        duration = speed_curve.get_duration(length)

        path = VehiclePath(
            curve_object=curve,
            path_type=path_type,
            speed_curve=speed_curve,
            reverse=reverse,
            name=name,
            length=length,
            duration=duration,
        )

        self.paths[name] = path
        return path

    def create_path_from_route(
        self,
        road_network: Any,
        start_node: str,
        end_node: str,
        speed_curve: Optional[SpeedCurve] = None,
        name: str = "Route",
    ) -> Optional[VehiclePath]:
        """
        Create path from road network route.

        Args:
            road_network: RoadNetwork object
            start_node: Starting node ID
            end_node: Ending node ID
            speed_curve: Speed profile
            name: Path name

        Returns:
            VehiclePath or None if no route found
        """
        if not BLENDER_AVAILABLE:
            return None

        # Get route from road network
        if hasattr(road_network, 'find_route'):
            route = road_network.find_route(start_node, end_node)
        elif hasattr(road_network, 'get_route'):
            route = road_network.get_route(start_node, end_node)
        else:
            return None

        if not route:
            return None

        # Create curve from route waypoints
        curve = self._create_curve_from_waypoints(route, name)

        if curve is None:
            return None

        return self.create_path_from_curve(
            curve=curve,
            name=name,
            path_type=PathType.STANDARD,
            speed_curve=speed_curve,
        )

    def create_path_with_speed(
        self,
        curve_object: Any,
        speed_curve: SpeedCurve,
        reverse: bool = False,
    ) -> VehiclePath:
        """
        Create path with custom speed curve.

        Args:
            curve_object: Blender curve
            speed_curve: Speed profile
            reverse: Drive in reverse

        Returns:
            VehiclePath with speed profile
        """
        return self.create_path_from_curve(
            curve=curve_object,
            speed_curve=speed_curve,
            reverse=reverse,
        )

    def create_reverse_path(
        self,
        curve: Any,
        speed_curve: Optional[SpeedCurve] = None,
    ) -> VehiclePath:
        """
        Create reverse driving path.

        Args:
            curve: Blender curve (will be reversed)
            speed_curve: Speed profile (typically slower)

        Returns:
            VehiclePath for reverse driving
        """
        if speed_curve is None:
            speed_curve = SpeedCurve.constant(5.0)  # Slower for reverse

        return self.create_path_from_curve(
            curve=curve,
            path_type=PathType.REVERSE,
            speed_curve=speed_curve,
            reverse=True,
        )

    def create_drift_path(
        self,
        curve: Any,
        drift_angle: float = 30.0,
        speed_curve: Optional[SpeedCurve] = None,
    ) -> VehiclePath:
        """
        Create drifting path with sustained slide angle.

        Args:
            curve: Blender curve
            drift_angle: Drift angle in degrees
            speed_curve: Speed profile

        Returns:
            VehiclePath for drifting
        """
        if speed_curve is None:
            speed_curve = SpeedCurve.constant(15.0)

        path = self.create_path_from_curve(
            curve=curve,
            path_type=PathType.DRIFT,
            speed_curve=speed_curve,
        )
        path.drift_angle = drift_angle
        return path

    def create_jump_path(
        self,
        start: Tuple[float, float, float],
        jump_distance: float,
        jump_height: float,
        rotation: float = 0.0,
        approach_speed: float = 15.0,
        name: str = "Jump",
    ) -> VehiclePath:
        """
        Create jump path with ballistic trajectory.

        Args:
            start: Starting position
            jump_distance: Horizontal distance of jump
            jump_height: Maximum height of jump
            rotation: Rotation during jump (degrees)
            approach_speed: Speed approaching jump
            name: Path name

        Returns:
            VehiclePath with jump trajectory
        """
        if not BLENDER_AVAILABLE:
            return VehiclePath(curve_object=None, name=name)

        # Create approach + jump + landing curve
        curve = self._create_jump_curve(
            start=start,
            distance=jump_distance,
            height=jump_height,
        )

        if curve is None:
            return VehiclePath(curve_object=None, name=name)

        # Speed curve: accelerate, maintain through jump, decelerate on landing
        speed_curve = SpeedCurve.ease_in_out(
            start_speed=approach_speed * 0.7,
            cruise_speed=approach_speed,
            end_speed=approach_speed * 0.5
        )

        path = self.create_path_from_curve(
            curve=curve,
            name=name,
            path_type=PathType.JUMP,
            speed_curve=speed_curve,
        )

        path.jump_height = jump_height
        path.rotation_count = rotation / 360.0

        return path

    def create_stunt_path(
        self,
        curve: Any,
        stunts: List[Dict[str, Any]],
        base_speed: float = 15.0,
    ) -> VehiclePath:
        """
        Create path with multiple stunts at specific points.

        Args:
            curve: Base curve
            stunts: List of stunt configs with 'position', 'type', 'params'
            base_speed: Default driving speed

        Returns:
            VehiclePath with stunts
        """
        # Build speed curve from stunt positions
        speed_keyframes = [(0.0, base_speed)]

        for stunt in stunts:
            pos = stunt.get('position', 0.5)
            stunt_type = stunt.get('type', 'slow')

            if stunt_type == 'slow':
                speed_keyframes.append((pos - 0.02, base_speed))
                speed_keyframes.append((pos, base_speed * 0.5))
                speed_keyframes.append((pos + 0.02, base_speed))
            elif stunt_type == 'jump':
                speed_keyframes.append((pos - 0.02, base_speed * 1.2))
                speed_keyframes.append((pos, base_speed))
                speed_keyframes.append((pos + 0.02, base_speed * 0.8))

        speed_keyframes.append((1.0, base_speed))

        speed_curve = SpeedCurve(keyframes=speed_keyframes, default_speed=base_speed)

        path = self.create_path_from_curve(
            curve=curve,
            path_type=PathType.STUNT,
            speed_curve=speed_curve,
        )

        return path

    def create_chase_path(
        self,
        target_path: VehiclePath,
        follow_distance: float = 10.0,
        follow_offset: Tuple[float, float, float] = (0, 0, 0),
        name: str = "Chase",
    ) -> Optional[VehiclePath]:
        """
        Create path that follows another vehicle at a distance.

        Args:
            target_path: Path of vehicle to follow
            follow_distance: Distance to maintain behind target
            follow_offset: Lateral/vertical offset
            name: Path name

        Returns:
            VehiclePath for chase vehicle
        """
        if not BLENDER_AVAILABLE or target_path.curve_object is None:
            return None

        # Offset the target path curve
        chase_curve = self._offset_curve(
            target_path.curve_object,
            offset=follow_offset,
        )

        if chase_curve is None:
            return None

        # Same speed curve but offset in time
        chase_path = self.create_path_from_curve(
            curve=chase_curve,
            name=name,
            path_type=PathType.CHASE,
            speed_curve=target_path.speed_curve,
        )

        return chase_path

    def apply_to_vehicle(
        self,
        rig: "LaunchControlRig",
        path: VehiclePath,
        frame_start: int = 1,
        align_to_path: bool = True,
        follow_terrain: bool = True,
    ) -> Dict[str, Any]:
        """
        Apply path to vehicle with speed curve animation.

        This replaces the basic drive_path() with speed-aware animation.

        Args:
            rig: LaunchControlRig instance
            path: VehiclePath to apply
            frame_start: Starting frame
            align_to_path: Rotate vehicle to path tangent
            follow_terrain: Adjust height to terrain

        Returns:
            Dictionary with animation results
        """
        if not BLENDER_AVAILABLE:
            return {"success": False, "error": "Blender not available"}

        armature = rig.rig_objects.get("armature")
        if armature is None or path.curve_object is None:
            return {"success": False, "error": "Missing armature or path"}

        fps = bpy.context.scene.render.fps
        speed_curve = path.speed_curve or SpeedCurve.constant(10.0)

        # Calculate total frames from speed curve
        total_frames = int(path.duration * fps)
        frame_end = frame_start + total_frames

        # Setup follow path constraint
        constraint = armature.constraints.new("FOLLOW_PATH")
        constraint.target = path.curve_object
        constraint.use_curve_follow = align_to_path
        constraint.use_fixed_location = True

        # Reverse if needed
        if path.reverse:
            constraint.use_fixed_location = True

        # Animate with speed curve
        for frame in range(frame_start, frame_end + 1):
            # Calculate position along path
            frame_offset = frame - frame_start
            t = frame_offset / total_frames

            # Get speed at this position
            speed = speed_curve.get_speed_at(t)

            # Calculate offset factor based on speed
            # Speed affects how fast we move along the path
            if frame == frame_start:
                offset = 0.0
            else:
                # Integrate speed to get position
                dt = 1.0 / fps
                segment_length = speed * dt
                prev_offset = armature.get("path_offset", 0.0)
                offset = prev_offset + segment_length / path.length

            offset = min(1.0, offset)  # Clamp to path end

            # For reverse, invert offset
            if path.reverse:
                offset = 1.0 - offset

            # Set offset
            armature["path_offset"] = offset
            constraint.offset_factor = offset

            # Keyframe the offset
            armature.keyframe_insert('["path_offset"]', frame=frame)

        # Store steering data for HUD
        if path.drift_angle != 0:
            self._generate_drift_steering(path, frame_start, total_frames)

        return {
            "success": True,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "path_length": path.length,
            "duration": path.duration,
            "path_type": path.path_type.value,
        }

    def get_steering_data(self, path_name: str) -> List[Tuple[float, float]]:
        """
        Get steering wheel animation data for HUD display.

        Args:
            path_name: Name of path

        Returns:
            List of (frame, steering_angle) tuples
        """
        path = self.paths.get(path_name)
        if path is None:
            return []
        return path.steering_keyframes

    def export_hud_data(
        self,
        path: VehiclePath,
        output_path: Path,
        format: str = "json",
    ) -> bool:
        """
        Export path data for HUD/overlay system.

        Args:
            path: VehiclePath to export
            output_path: Where to save
            format: Output format (json, csv)

        Returns:
            True if successful
        """
        import json

        data = {
            "name": path.name,
            "type": path.path_type.value,
            "length": path.length,
            "duration": path.duration,
            "reverse": path.reverse,
            "loop": path.loop,
            "steering": path.steering_keyframes,
        }

        if path.speed_curve:
            data["speed_curve"] = {
                "keyframes": path.speed_curve.keyframes,
                "default_speed": path.speed_curve.default_speed,
            }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    # === PRIVATE METHODS ===

    def _calculate_curve_length(self, curve: Any) -> float:
        """Calculate total length of a curve."""
        if not BLENDER_AVAILABLE or curve is None:
            return 0.0

        total_length = 0.0
        for spline in curve.data.splines:
            total_length += self._calculate_spline_length(spline, curve.matrix_world)

        return total_length

    def _calculate_spline_length(self, spline: Any, matrix: Any) -> float:
        """Calculate length of a single spline."""
        if not spline.bezier_points and not spline.points:
            return 0.0

        length = 0.0
        prev_point = None

        if spline.type == 'BEZIER':
            points = spline.bezier_points
            for i, point in enumerate(points):
                if prev_point is not None:
                    # Approximate with line segments
                    length += (point.co - prev_point.co).length
                prev_point = point
        else:
            points = spline.points
            for i, point in enumerate(points):
                if prev_point is not None:
                    length += (point.co - prev_point.co).length
                prev_point = point

        return length * matrix.to_scale().length

    def _create_curve_from_waypoints(
        self,
        waypoints: List[Any],
        name: str,
    ) -> Optional[Any]:
        """Create Blender curve from waypoint list."""
        if not BLENDER_AVAILABLE or len(waypoints) < 2:
            return None

        # Create curve data
        curve_data = bpy.data.curves.new(name=f"{name}_curve", type='CURVE')
        curve_data.dimensions = '3D'

        # Create spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(waypoints) - 1)

        for i, wp in enumerate(waypoints):
            if hasattr(wp, 'position'):
                pos = wp.position
            elif isinstance(wp, (list, tuple)):
                pos = wp
            else:
                continue
            spline.points[i].co = (pos[0], pos[1], pos[2] if len(pos) > 2 else 0, 1)

        # Create object
        curve_obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(curve_obj)

        return curve_obj

    def _create_jump_curve(
        self,
        start: Tuple[float, float, float],
        distance: float,
        height: float,
    ) -> Optional[Any]:
        """Create parabolic jump curve."""
        if not BLENDER_AVAILABLE:
            return None

        # Create curve with approach, jump, landing
        curve_data = bpy.data.curves.new(name="Jump_curve", type='CURVE')
        curve_data.dimensions = '3D'

        spline = curve_data.splines.new('POLY')

        # Points: approach -> ramp -> apex -> landing -> exit
        points = [
            (start[0] - 10, start[1], start[2]),          # Approach
            (start[0], start[1], start[2]),               # Ramp start
            (start[0] + distance * 0.3, start[1], start[2] + height * 0.5),  # Rising
            (start[0] + distance * 0.5, start[1], start[2] + height),        # Apex
            (start[0] + distance * 0.7, start[1], start[2] + height * 0.5),  # Falling
            (start[0] + distance, start[1], start[2]),    # Landing
            (start[0] + distance + 10, start[1], start[2]),  # Exit
        ]

        spline.points.add(len(points) - 1)
        for i, p in enumerate(points):
            spline.points[i].co = (p[0], p[1], p[2], 1)

        curve_obj = bpy.data.objects.new("Jump_Path", curve_data)
        bpy.context.collection.objects.link(curve_obj)

        return curve_obj

    def _offset_curve(
        self,
        curve: Any,
        offset: Tuple[float, float, float],
    ) -> Optional[Any]:
        """Create offset copy of curve."""
        if not BLENDER_AVAILABLE or curve is None:
            return None

        # Copy curve data
        new_curve_data = curve.data.copy()

        # Offset all points
        for spline in new_curve_data.splines:
            if spline.type == 'BEZIER':
                for point in spline.bezier_points:
                    point.co.x += offset[0]
                    point.co.y += offset[1]
                    point.co.z += offset[2]
            else:
                for point in spline.points:
                    point.co.x += offset[0]
                    point.co.y += offset[1]
                    point.co.z += offset[2]

        new_curve_obj = bpy.data.objects.new(f"{curve.name}_offset", new_curve_data)
        bpy.context.collection.objects.link(new_curve_obj)

        return new_curve_obj

    def _generate_drift_steering(
        self,
        path: VehiclePath,
        frame_start: int,
        total_frames: int,
    ) -> None:
        """Generate steering keyframes for drift path."""
        if path.drift_angle == 0:
            return

        # Steering wheel counter-turns during drift
        drift_rad = math.radians(path.drift_angle)

        # Keyframes: counter-steer at start, hold, return
        path.steering_keyframes = [
            (frame_start, 0.0),
            (frame_start + int(total_frames * 0.1), -drift_rad * 0.8),
            (frame_start + int(total_frames * 0.3), -drift_rad),
            (frame_start + int(total_frames * 0.7), -drift_rad),
            (frame_start + int(total_frames * 0.9), -drift_rad * 0.5),
            (frame_start + total_frames, 0.0),
        ]


# === SPEED SEGMENT ADAPTER ===

class SpeedSegmentAdapter:
    """
    Adapts SpeedSegments (from physics.py) to SpeedCurve.

    Allows using SpeedSegments with the new path system.
    """

    @staticmethod
    def from_speed_segments(speed_segments: Any) -> SpeedCurve:
        """
        Convert SpeedSegments to SpeedCurve.

        Args:
            speed_segments: SpeedSegments object from physics module

        Returns:
            SpeedCurve instance
        """
        keyframes = []

        if hasattr(speed_segments, 'segments'):
            for segment in speed_segments.segments:
                keyframes.append((segment.start, segment.speed))
                keyframes.append((segment.end, segment.speed))

        if not keyframes:
            keyframes = [(0.0, 10.0), (1.0, 10.0)]

        return SpeedCurve(keyframes=keyframes)


# === CONVENIENCE FUNCTIONS ===

def create_path(
    curve: Any,
    speed: float = 10.0,
    reverse: bool = False,
) -> VehiclePath:
    """Quick path creation with constant speed."""
    system = VehiclePathSystem()
    return system.create_path_from_curve(
        curve=curve,
        speed_curve=SpeedCurve.constant(speed),
        reverse=reverse,
    )


def create_chase_sequence(
    hero_path: VehiclePath,
    pursuer_count: int = 3,
    spacing: float = 15.0,
) -> List[VehiclePath]:
    """Create multiple pursuer paths for chase scene."""
    system = VehiclePathSystem()
    paths = []

    for i in range(pursuer_count):
        offset = (0, -(i + 1) * spacing, 0)
        chase_path = system.create_chase_path(
            hero_path,
            follow_distance=spacing * (i + 1),
            follow_offset=offset,
            name=f"Pursuer_{i + 1}",
        )
        if chase_path:
            paths.append(chase_path)

    return paths


__all__ = [
    "VehiclePathSystem",
    "VehiclePath",
    "SpeedCurve",
    "PathType",
    "SpeedSegmentAdapter",
    "create_path",
    "create_chase_sequence",
]
