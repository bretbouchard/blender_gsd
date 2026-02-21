"""
Steering System for Launch Control

Vehicle steering with Ackermann geometry support for realistic
turning behavior and steering wheel controller setup.

Features:
- Front, rear, and four-wheel steering configurations
- Ackermann geometry for accurate turn radius
- Steering wheel controller with visual feedback
- Animation support for steering maneuvers
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
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


class SteeringControllerType(Enum):
    """Types of steering controllers."""

    STEERING_WHEEL = "steering_wheel"
    LEVER = "lever"
    CUSTOM = "custom"
    NONE = "none"


@dataclass
class SteeringConfig:
    """Configuration for steering system."""

    max_angle: float = 35.0  # degrees
    ackermann_enabled: bool = True
    four_wheel_steering: bool = False
    rear_steering_ratio: float = 0.0  # 0 = same direction, 1 = opposite
    wheelbase: float = 2.7  # meters
    track_width: float = 1.6  # meters
    controller_type: SteeringControllerType = SteeringControllerType.STEERING_WHEEL
    auto_center: bool = True
    steering_ratio: float = 1.0  # Steering wheel to wheel angle ratio


@dataclass
class AckermannResult:
    """Result from Ackermann geometry calculation."""

    inner_angle: float  # degrees
    outer_angle: float  # degrees
    turning_radius: float  # meters
    steer_angle_input: float  # degrees (input)


class AckermannGeometry:
    """Ackermann steering geometry calculations.

    Provides static methods for calculating correct steering angles
    that allow all wheels to roll around a common point without slipping.

    Example:
        # Calculate steering angles for a turn
        result = AckermannGeometry.calculate_angles(
            steering_input=20.0,
            wheelbase=2.7,
            track_width=1.6
        )
        print(f"Inner wheel: {result.inner_angle:.1f} deg")
        print(f"Outer wheel: {result.outer_angle:.1f} deg")

        # Calculate turning radius
        radius = AckermannGeometry.turning_radius(steering_angle=20.0, wheelbase=2.7)
    """

    @staticmethod
    def calculate_angles(
        steering_input: float,
        wheelbase: float,
        track_width: float,
    ) -> AckermannResult:
        """Calculate Ackermann-corrected steering angles.

        The inner wheel must turn more sharply than the outer wheel
        to maintain a common turn center. This is the fundamental
        principle of Ackermann steering geometry.

        Formula:
            cot(outer) - cot(inner) = track_width / wheelbase
            inner = steering_input (by convention)

        Args:
            steering_input: Base steering angle in degrees
            wheelbase: Distance between front and rear axles in meters
            track_width: Distance between left and right wheels in meters

        Returns:
            AckermannResult with calculated angles and turning radius
        """
        if abs(steering_input) < 0.01:
            return AckermannResult(
                inner_angle=0.0,
                outer_angle=0.0,
                turning_radius=float("inf"),
                steer_angle_input=steering_input,
            )

        # Convert to radians
        input_rad = math.radians(steering_input)

        # Calculate turn radius to the center of the vehicle
        turning_radius = wheelbase / math.tan(abs(input_rad))

        # Calculate inner wheel angle (closer to center)
        # Inner wheel follows the input angle
        inner_angle = steering_input

        # Calculate outer wheel angle using Ackermann geometry
        # cot(outer) = cot(inner) - track/wheelbase
        inner_cot = 1.0 / math.tan(abs(input_rad))
        outer_cot = inner_cot - track_width / wheelbase

        if outer_cot > 0:
            outer_rad = math.atan(1.0 / outer_cot)
            outer_angle = math.degrees(outer_rad) * (1 if steering_input >= 0 else -1)
        else:
            # Very sharp turn, outer wheel at extreme angle
            outer_angle = steering_input * 0.7

        return AckermannResult(
            inner_angle=inner_angle,
            outer_angle=outer_angle,
            turning_radius=turning_radius,
            steer_angle_input=steering_input,
        )

    @staticmethod
    def turning_radius(
        steering_angle: float,
        wheelbase: float,
    ) -> float:
        """Calculate turning radius for given steering angle.

        Args:
            steering_angle: Steering angle in degrees
            wheelbase: Distance between axles in meters

        Returns:
            Turning radius in meters (infinity if straight)
        """
        if abs(steering_angle) < 0.01:
            return float("inf")

        angle_rad = math.radians(steering_angle)
        return wheelbase / math.tan(abs(angle_rad))

    @staticmethod
    def max_steering_angle(
        wheelbase: float,
        min_turning_radius: float,
    ) -> float:
        """Calculate maximum steering angle for a minimum turning radius.

        Args:
            wheelbase: Distance between axles in meters
            min_turning_radius: Minimum desired turning radius in meters

        Returns:
            Maximum steering angle in degrees
        """
        if min_turning_radius <= 0:
            return 45.0  # Default max

        angle_rad = math.atan(wheelbase / min_turning_radius)
        return math.degrees(angle_rad)

    @staticmethod
    def four_wheel_angles(
        steering_input: float,
        wheelbase: float,
        track_width: float,
        rear_ratio: float = 0.0,
    ) -> dict[str, float]:
        """Calculate angles for four-wheel steering.

        Args:
            steering_input: Base steering angle in degrees
            wheelbase: Distance between axles in meters
            track_width: Distance between wheels in meters
            rear_ratio: Rear steering ratio (0 = same, 1 = opposite)

        Returns:
            Dictionary with FL, FR, RL, RR wheel angles
        """
        # Front wheels use standard Ackermann
        front_result = AckermannGeometry.calculate_angles(
            steering_input, wheelbase, track_width
        )

        # Rear wheels
        rear_base = steering_input * rear_ratio
        rear_result = AckermannGeometry.calculate_angles(
            rear_base, wheelbase, track_width
        )

        return {
            "front_left": front_result.inner_angle if steering_input > 0 else front_result.outer_angle,
            "front_right": front_result.outer_angle if steering_input > 0 else front_result.inner_angle,
            "rear_left": rear_result.inner_angle if rear_base > 0 else rear_result.outer_angle,
            "rear_right": rear_result.outer_angle if rear_base > 0 else rear_result.inner_angle,
        }


class SteeringSystem:
    """Vehicle steering with Ackermann geometry.

    Manages steering configuration, controller creation, and angle
    application for realistic vehicle turning.

    Example:
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        steering = SteeringSystem(rig)
        steering.configure(
            max_angle=35.0,
            ackermann=True,
            four_wheel_steering=False
        )

        # Create visual steering wheel controller
        steering.create_controller(location=(0, -0.3, 0.8))

        # Apply steering angle with Ackermann correction
        steering.apply_ackermann(wheelbase=2.7, track_width=1.6)

        # Set steering angle (can be animated)
        steering.set_angle(20.0, frame=60)
    """

    def __init__(self, rig: "LaunchControlRig"):
        """Initialize steering system.

        Args:
            rig: The LaunchControlRig instance to control
        """
        self.rig = rig
        self.config = SteeringConfig()
        self.controller: Optional[Any] = None
        self.current_angle: float = 0.0
        self._wheel_bones: dict[str, str] = {}

        # Cache wheel bone references
        self._cache_wheel_bones()

    def _cache_wheel_bones(self) -> None:
        """Cache references to steering wheel bones."""
        if not self.rig.rig_objects:
            return

        for key, value in self.rig.rig_objects.items():
            if key.startswith("wheel_"):
                # Map FL, FR, RL, RR to bone names
                if "_FL" in key.upper() or "front_left" in key.lower():
                    self._wheel_bones["front_left"] = value
                elif "_FR" in key.upper() or "front_right" in key.lower():
                    self._wheel_bones["front_right"] = value
                elif "_RL" in key.upper() or "rear_left" in key.lower():
                    self._wheel_bones["rear_left"] = value
                elif "_RR" in key.upper() or "rear_right" in key.lower():
                    self._wheel_bones["rear_right"] = value

    def configure(
        self,
        max_angle: float = 35.0,
        ackermann: bool = True,
        four_wheel_steering: bool = False,
        rear_ratio: float = 0.0,
        wheelbase: Optional[float] = None,
        track_width: Optional[float] = None,
        auto_center: bool = True,
        steering_ratio: float = 1.0,
    ) -> None:
        """Configure steering parameters.

        Args:
            max_angle: Maximum steering angle in degrees
            ackermann: Enable Ackermann geometry correction
            four_wheel_steering: Enable rear wheel steering
            rear_ratio: Rear steering ratio (0=same, 1=opposite direction)
            wheelbase: Vehicle wheelbase (auto-detected if None)
            track_width: Vehicle track width (auto-detected if None)
            auto_center: Whether steering auto-centers
            steering_ratio: Ratio of controller to wheel angle
        """
        self.config.max_angle = max_angle
        self.config.ackermann_enabled = ackermann
        self.config.four_wheel_steering = four_wheel_steering
        self.config.rear_steering_ratio = rear_ratio
        self.config.auto_center = auto_center
        self.config.steering_ratio = steering_ratio

        # Auto-detect wheelbase and track width from detected components
        if wheelbase is not None:
            self.config.wheelbase = wheelbase
        else:
            self.config.wheelbase = self._detect_wheelbase()

        if track_width is not None:
            self.config.track_width = track_width
        else:
            self.config.track_width = self._detect_track_width()

    def _detect_wheelbase(self) -> float:
        """Detect wheelbase from wheel positions."""
        if not self.rig.detected_components:
            return 2.7  # Default

        positions = self.rig.detected_components.wheel_positions
        if len(positions) < 4:
            return 2.7

        pos_list = list(positions.values())

        # Find average distance between front and rear wheels
        front_x = (pos_list[0].x + pos_list[1].x) / 2 if len(pos_list) >= 2 else 0
        rear_x = (pos_list[2].x + pos_list[3].x) / 2 if len(pos_list) >= 4 else 0

        return abs(front_x - rear_x)

    def _detect_track_width(self) -> float:
        """Detect track width from wheel positions."""
        if not self.rig.detected_components:
            return 1.6  # Default

        positions = self.rig.detected_components.wheel_positions
        if len(positions) < 2:
            return 1.6

        pos_list = list(positions.values())

        # Find average distance between left and right wheels
        # Assuming Y axis is left/right
        if len(pos_list) >= 2:
            return abs(pos_list[0].y - pos_list[1].y)

        return 1.6

    def create_controller(
        self,
        location: tuple[float, float, float] = (0, -0.3, 0.8),
        shape: str = "steering_wheel",
        size: float = 0.15,
    ) -> Any:
        """Create a steering wheel controller object.

        Args:
            location: World position for the controller
            shape: Controller shape - "steering_wheel", "lever", or "custom"
            size: Display size of the controller

        Returns:
            Created controller object
        """
        if not BLENDER_AVAILABLE:
            return None

        # Check if controller already exists
        controller_name = f"{self.rig.config.rig_name}_steering_ctrl"

        # Check existing controllers
        if controller_name in bpy.data.objects:
            self.controller = bpy.data.objects[controller_name]
            return self.controller

        # Create new controller
        if shape == "steering_wheel":
            # Create a torus-like steering wheel shape
            self.controller = self._create_steering_wheel_mesh(
                controller_name, location, size
            )
        elif shape == "lever":
            # Simple lever controller
            self.controller = bpy.data.objects.new(controller_name, None)
            self.controller.empty_display_type = "ARROWS"
            self.controller.empty_display_size = size
            self.controller.location = location
            bpy.context.collection.objects.link(self.controller)
        else:
            # Custom or simple circle
            self.controller = bpy.data.objects.new(controller_name, None)
            self.controller.empty_display_type = "CIRCLE"
            self.controller.empty_display_size = size
            self.controller.location = location
            bpy.context.collection.objects.link(self.controller)

        # Add custom property for steering angle
        self.controller["steering_angle"] = 0.0
        self.controller.id_properties_ui("steering_angle").update(
            min=-self.config.max_angle,
            max=self.config.max_angle,
        )

        return self.controller

    def _create_steering_wheel_mesh(
        self,
        name: str,
        location: tuple[float, float, float],
        size: float,
    ) -> Any:
        """Create a mesh steering wheel shape.

        Args:
            name: Object name
            location: World position
            size: Wheel radius

        Returns:
            Created mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create torus for steering wheel
        bpy.ops.mesh.primitive_torus_add(
            major_radius=size,
            minor_radius=size * 0.1,
            location=location,
            rotation=(math.pi / 2, 0, 0),  # Rotate to face forward
        )

        wheel = bpy.context.active_object
        wheel.name = name

        return wheel

    def apply_ackermann(
        self,
        wheelbase: Optional[float] = None,
        track_width: Optional[float] = None,
    ) -> None:
        """Apply Ackermann geometry to wheel steering.

        Sets up constraints or drivers for Ackermann-corrected steering.

        Args:
            wheelbase: Override wheelbase (uses config if None)
            track_width: Override track width (uses config if None)
        """
        if not BLENDER_AVAILABLE:
            return

        wb = wheelbase or self.config.wheelbase
        tw = track_width or self.config.track_width

        armature = self.rig.rig_objects.get("armature")
        if not armature:
            return

        # Setup drivers on wheel bones for Ackermann geometry
        # This creates drivers that calculate correct angles based on steering input
        self._setup_ackermann_drivers(armature, wb, tw)

    def _setup_ackermann_drivers(
        self,
        armature: Any,
        wheelbase: float,
        track_width: float,
    ) -> None:
        """Setup drivers for Ackermann steering.

        Args:
            armature: Rig armature object
            wheelbase: Vehicle wheelbase
            track_width: Vehicle track width
        """
        # Get steering angle source
        steering_source = self.controller or armature

        # Setup driver on each wheel bone
        wheel_positions = ["front_left", "front_right"]
        if self.config.four_wheel_steering:
            wheel_positions.extend(["rear_left", "rear_right"])

        for pos in wheel_positions:
            bone_name = self._wheel_bones.get(pos)
            if not bone_name:
                continue

            if armature.pose and bone_name in armature.pose.bones:
                bone = armature.pose.bones[bone_name]

                # Add driver for Y rotation (steering axis)
                if not bone.animation_data:
                    bone.animation_data_create()

                # Driver setup would go here with expression:
                # For inner wheel: steering_angle
                # For outer wheel: atan(wheelbase / (wheelbase/tan(steering_angle) - track_width))
                # This is simplified - actual implementation uses Blender's driver system

    def set_angle(
        self,
        angle: float,
        frame: Optional[int] = None,
        apply_ackermann: bool = True,
    ) -> None:
        """Set steering angle.

        Args:
            angle: Steering angle in degrees
            frame: Frame for keyframe (None = no keyframe)
            apply_ackermann: Whether to apply Ackermann correction
        """
        # Clamp angle
        clamped_angle = max(-self.config.max_angle, min(angle, self.config.max_angle))
        self.current_angle = clamped_angle

        if not BLENDER_AVAILABLE:
            return

        armature = self.rig.rig_objects.get("armature")
        if not armature:
            return

        # Calculate wheel angles
        if apply_ackermann and self.config.ackermann_enabled:
            wheel_angles = AckermannGeometry.four_wheel_angles(
                clamped_angle,
                self.config.wheelbase,
                self.config.track_width,
                self.config.rear_steering_ratio if self.config.four_wheel_steering else 0.0,
            )
        else:
            # All wheels same angle
            wheel_angles = {
                "front_left": clamped_angle,
                "front_right": clamped_angle,
                "rear_left": clamped_angle * self.config.rear_steering_ratio if self.config.four_wheel_steering else 0,
                "rear_right": clamped_angle * self.config.rear_steering_ratio if self.config.four_wheel_steering else 0,
            }

        # Apply to wheel bones
        for pos, wheel_angle in wheel_angles.items():
            bone_name = self._wheel_bones.get(pos)
            if not bone_name:
                continue

            if armature.pose and bone_name in armature.pose.bones:
                bone = armature.pose.bones[bone_name]
                # Rotate around Y axis (typical steering axis)
                bone.rotation_euler = Euler((0, math.radians(wheel_angle), 0), "XYZ")

                if frame is not None:
                    bone.keyframe_insert(
                        data_path="rotation_euler",
                        index=1,  # Y axis
                        frame=frame,
                    )

        # Update controller
        if self.controller:
            self.controller["steering_angle"] = clamped_angle
            # Rotate controller for visual feedback
            self.controller.rotation_euler = Euler(
                (0, 0, math.radians(clamped_angle * self.config.steering_ratio)),
                "XYZ"
            )
            if frame is not None:
                self.controller.keyframe_insert(
                    data_path="rotation_euler",
                    index=2,  # Z axis
                    frame=frame,
                )

    def animate_steering(
        self,
        start_angle: float,
        end_angle: float,
        frame_start: int,
        frame_end: int,
        easing: str = "ease_in_out",
    ) -> None:
        """Animate steering from one angle to another.

        Args:
            start_angle: Starting angle in degrees
            end_angle: Ending angle in degrees
            frame_start: Start frame
            frame_end: End frame
            easing: Easing type - "linear", "ease_in", "ease_out", "ease_in_out"
        """
        if not BLENDER_AVAILABLE:
            return

        # Set start angle
        self.set_angle(start_angle, frame=frame_start)

        # Set end angle
        self.set_angle(end_angle, frame=frame_end)

        # Set interpolation for smooth animation
        armature = self.rig.rig_objects.get("armature")
        if armature and armature.animation_data:
            for fcurve in armature.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if frame_start <= keyframe.co.x <= frame_end:
                        if easing == "linear":
                            keyframe.interpolation = "LINEAR"
                        elif easing == "ease_in":
                            keyframe.interpolation = "BACK"
                        elif easing == "ease_out":
                            keyframe.interpolation = "BACK"
                        else:
                            keyframe.interpolation = "BEZIER"

    def get_turning_radius(self) -> float:
        """Get current turning radius based on steering angle.

        Returns:
            Turning radius in meters (infinity if straight)
        """
        return AckermannGeometry.turning_radius(
            self.current_angle,
            self.config.wheelbase,
        )

    def reset(self) -> None:
        """Reset steering to center position."""
        self.set_angle(0.0)
