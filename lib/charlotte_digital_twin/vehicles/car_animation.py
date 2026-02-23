"""
Car Animation System

Realistic car physics and animation:
- Vehicle physics simulation
- Suspension response
- Wheel rotation
- Steering animation
- Follow path with banking

Designed for cinematic car chase sequences.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import bpy
    from bpy.types import Object, Collection, FCurve, Action
    from mathutils import Vector, Matrix, Quaternion
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any
    FCurve = Any
    Action = Any


class AnimationStyle(Enum):
    """Animation driving styles."""
    NORMAL = "normal"         # Standard driving
    AGGRESSIVE = "aggressive" # Fast, sharp maneuvers
    PURSUIT = "pursuit"       # Police-style pursuit
    EVASIVE = "evasive"       # Evasive maneuvers


@dataclass
class VehiclePhysics:
    """Physical properties for vehicle animation."""
    mass: float = 1500.0  # kg
    max_speed: float = 60.0  # m/s (~135 mph)
    acceleration: float = 8.0  # m/s²
    braking: float = 12.0  # m/s²
    turning_radius: float = 6.0  # meters

    # Suspension
    suspension_stiffness: float = 30000.0  # N/m
    suspension_damping: float = 4000.0  # Ns/m
    suspension_travel: float = 0.15  # meters

    # Wheel
    wheel_radius: float = 0.35  # meters
    wheelbase: float = 2.8  # meters


@dataclass
class AnimationConfig:
    """Configuration for car animation."""
    style: AnimationStyle = AnimationStyle.NORMAL
    frame_start: int = 1
    frame_end: int = 250
    fps: float = 24.0

    # Motion
    base_speed: float = 25.0  # m/s (~55 mph)
    speed_variation: float = 0.1

    # Steering
    max_steering_angle: float = 35.0  # degrees
    steering_smoothing: float = 0.3

    # Suspension
    enable_suspension: bool = True
    suspension_intensity: float = 0.5

    # Banking
    enable_banking: bool = True
    max_bank_angle: float = 8.0  # degrees


# Physics presets
PHYSICS_PRESETS = {
    "sedan": VehiclePhysics(
        mass=1500.0,
        max_speed=55.0,
        acceleration=7.0,
        turning_radius=6.0,
    ),
    "sports": VehiclePhysics(
        mass=1300.0,
        max_speed=80.0,
        acceleration=12.0,
        turning_radius=5.0,
        suspension_stiffness=40000.0,
    ),
    "suv": VehiclePhysics(
        mass=2200.0,
        max_speed=50.0,
        acceleration=6.0,
        turning_radius=7.0,
        suspension_travel=0.2,
    ),
    "muscle": VehiclePhysics(
        mass=1700.0,
        max_speed=70.0,
        acceleration=10.0,
        turning_radius=6.5,
    ),
    "police": VehiclePhysics(
        mass=1800.0,
        max_speed=65.0,
        acceleration=9.0,
        turning_radius=6.0,
    ),
}


class CarAnimationSystem:
    """
    Creates realistic car animations.

    Handles path following, wheel rotation, steering,
    and suspension response for cinematic sequences.
    """

    def __init__(self):
        """Initialize animation system."""
        self._physics = PHYSICS_PRESETS["sedan"]

    def animate_car_along_path(
        self,
        car_obj: Object,
        path_curve: Object,
        config: Optional[AnimationConfig] = None,
        physics: Optional[VehiclePhysics] = None,
    ) -> bool:
        """
        Animate car following a path curve.

        Args:
            car_obj: Car object to animate
            path_curve: Curve object to follow
            config: Animation configuration
            physics: Vehicle physics settings

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE or car_obj is None or path_curve is None:
            return False

        config = config or AnimationConfig()
        physics = physics or self._physics

        # Add Follow Path constraint
        if "FollowPath" not in car_obj.constraints:
            constraint = car_obj.constraints.new("FOLLOW_PATH")
            constraint.target = path_curve
            constraint.use_curve_follow = True
            constraint.use_curve_radius = False
            constraint.use_fixed_location = True
            constraint.forward_axis = "FORWARD_X"
            constraint.up_axis = "UP_Z"

            # Set animation range
            constraint.offset_factor = 0.0

        # Animate offset factor
        constraint = car_obj.constraints["FollowPath"]

        # Keyframe at start
        constraint.offset_factor = 0.0
        car_obj.keyframe_insert(
            data_path='constraints["FollowPath"].offset_factor',
            frame=config.frame_start,
        )

        # Keyframe at end
        constraint.offset_factor = 1.0
        car_obj.keyframe_insert(
            data_path='constraints["FollowPath"].offset_factor',
            frame=config.frame_end,
        )

        # Animate wheel rotation
        self._animate_wheels(car_obj, config, physics)

        # Add suspension animation
        if config.enable_suspension:
            self._animate_suspension(car_obj, config, physics)

        return True

    def create_path_from_points(
        self,
        points: List[Tuple[float, float, float]],
        name: str = "Car_Path",
        collection: Optional[Collection] = None,
    ) -> Optional[Object]:
        """
        Create a path curve from waypoints.

        Args:
            points: List of (x, y, z) waypoints
            name: Curve name
            collection: Collection to add to

        Returns:
            Curve object
        """
        if not BLENDER_AVAILABLE or len(points) < 2:
            return None

        # Create curve data
        curve_data = bpy.data.curves.new(name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 12
        curve_data.bevel_depth = 0.0

        # Create spline
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(len(points) - 1)

        for i, (x, y, z) in enumerate(points):
            point = spline.bezier_points[i]
            point.co = (x, y, z)
            point.handle_type_left = 'AUTO'
            point.handle_type_right = 'AUTO'

        # Create object
        curve_obj = bpy.data.objects.new(name, curve_data)

        if collection:
            collection.objects.link(curve_obj)

        return curve_obj

    def _animate_wheels(
        self,
        car_obj: Object,
        config: AnimationConfig,
        physics: VehiclePhysics,
    ) -> None:
        """Animate wheel rotation."""
        if not BLENDER_AVAILABLE:
            return

        # Find wheel objects
        wheel_names = ["Wheel_FL", "Wheel_FR", "Wheel_RL", "Wheel_RR"]

        for wheel_name in wheel_names:
            wheel = None
            for child in car_obj.children:
                if wheel_name in child.name:
                    wheel = child
                    break

            if wheel is None:
                continue

            # Calculate rotation speed based on speed and wheel radius
            # rotations/second = speed / (2 * pi * radius)
            speed = config.base_speed
            rotations_per_second = speed / (2 * math.pi * physics.wheel_radius)
            degrees_per_frame = rotations_per_second * 360 / config.fps

            # Determine rotation axis based on wheel position
            is_right = "FR" in wheel_name or "RR" in wheel_name

            # Animate rotation
            for frame in range(config.frame_start, config.frame_end + 1, 5):
                rotation = degrees_per_frame * (frame - config.frame_start)

                # Right side wheels rotate opposite
                if is_right:
                    rotation = -rotation

                wheel.rotation_euler = (math.radians(rotation), 0, wheel.rotation_euler[2])
                wheel.keyframe_insert("rotation_euler", frame=frame)

    def _animate_suspension(
        self,
        car_obj: Object,
        config: AnimationConfig,
        physics: VehiclePhysics,
    ) -> None:
        """Add suspension bounce animation."""
        if not BLENDER_AVAILABLE:
            return

        # Add subtle Z-axis bounce
        import random

        for frame in range(config.frame_start, config.frame_end, 10):
            # Random bounce based on suspension intensity
            bounce = random.uniform(
                -physics.suspension_travel * config.suspension_intensity,
                physics.suspension_travel * config.suspension_intensity,
            )

            # Add noise-based vertical motion
            car_obj.location.z += bounce
            car_obj.keyframe_insert("location", frame=frame, index=2)


def create_chase_path(
    road_points: List[Tuple[float, float, float]],
    offset: float = 0.0,
    lane: int = 0,
    lane_width: float = 3.5,
    name: str = "Chase_Path",
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Create a chase path from road center points.

    Args:
        road_points: Road center line points
        offset: Lateral offset from lane center
        lane: Lane number (0 = rightmost)
        lane_width: Width of each lane
        name: Path name
        collection: Collection to add to

    Returns:
        Path curve object
    """
    if not BLENDER_AVAILABLE or len(road_points) < 2:
        return None

    # Calculate lane offset
    lateral_offset = lane * lane_width + lane_width / 2 + offset

    # Offset points to lane
    path_points = []

    for i, point in enumerate(road_points):
        p = Vector(point)

        # Calculate direction
        if i == 0:
            direction = (Vector(road_points[1]) - p).normalized()
        elif i == len(road_points) - 1:
            direction = (p - Vector(road_points[-2])).normalized()
        else:
            direction = (Vector(road_points[i + 1]) - Vector(road_points[i - 1])).normalized()

        perpendicular = Vector((-direction.y, direction.x, 0))
        offset_point = p + perpendicular * lateral_offset

        path_points.append(offset_point.to_tuple())

    system = CarAnimationSystem()
    return system.create_path_from_points(path_points, name, collection)


def animate_car_chase(
    car_obj: Object,
    road_points: List[Tuple[float, float, float]],
    lane: int = 0,
    style: AnimationStyle = AnimationStyle.AGGRESSIVE,
    frame_start: int = 1,
    duration_seconds: float = 10.0,
    fps: float = 24.0,
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Set up complete car chase animation.

    Args:
        car_obj: Car object to animate
        road_points: Road center line points
        lane: Lane number
        style: Driving style
        frame_start: Starting frame
        duration_seconds: Animation duration in seconds
        fps: Frames per second
        collection: Collection for path

    Returns:
        Path curve object
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create chase path
    path = create_chase_path(
        road_points,
        lane=lane,
        name=f"Chase_Path_{car_obj.name}",
        collection=collection,
    )

    if path is None:
        return None

    # Animation config
    config = AnimationConfig(
        style=style,
        frame_start=frame_start,
        frame_end=frame_start + int(duration_seconds * fps),
        fps=fps,
        base_speed=30.0 if style == AnimationStyle.AGGRESSIVE else 20.0,
        enable_suspension=True,
        enable_banking=True,
    )

    # Style-specific adjustments
    if style == AnimationStyle.AGGRESSIVE:
        config.max_bank_angle = 12.0
        config.suspension_intensity = 0.8
    elif style == AnimationStyle.PURSUIT:
        config.base_speed = 35.0
        config.max_bank_angle = 10.0

    # Animate
    system = CarAnimationSystem()
    system.animate_car_along_path(car_obj, path, config)

    return path


__all__ = [
    "AnimationStyle",
    "VehiclePhysics",
    "AnimationConfig",
    "PHYSICS_PRESETS",
    "CarAnimationSystem",
    "create_chase_path",
    "animate_car_chase",
]
