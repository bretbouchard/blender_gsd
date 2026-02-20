"""
Wheel System Module

Manages wheel rotation and steering for vehicles.
Includes Ackermann steering geometry support.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from math import pi, degrees, radians, tan, atan
import logging

logger = logging.getLogger(__name__)


@dataclass
class WheelRig:
    """Represents a rigged wheel with its components."""
    wheel: Any                                 # The wheel object
    pivot: Optional[Any] = None                # Steering pivot (empty)
    rotation_driver: Optional[Any] = None      # Rotation driver data
    steering_constraint: Optional[Any] = None  # Steering constraint
    radius: float = 0.35
    is_steering: bool = False
    is_driven: bool = False


class WheelSystem:
    """Manage wheel rotation and steering for vehicles."""

    # Small angle threshold for Ackermann (prevents jitter)
    ACKERMANN_THRESHOLD = 0.5  # degrees

    @staticmethod
    def create_emitter(name: str, location: Tuple[float, float, float] = (0, 0, 0),
                       size: float = 10.0) -> Dict[str, Any]:
        """
        Create an emitter object for wheel systems.

        This is a mock implementation for testing. In Blender,
        this would create an actual empty object.

        Args:
            name: Name for the emitter
            location: World position
            size: Size of the emitter

        Returns:
            Dictionary representing the emitter
        """
        return {
            'name': name,
            'location': list(location),
            'size': size,
            'type': 'EMITTER',
            'wheels': [],
        }

    @staticmethod
    def create_wheel_rig(
        wheel_object: Any,
        radius: float = 0.35,
        steering_pivot: Optional[Any] = None
    ) -> WheelRig:
        """
        Create wheel rig with rotation and steering controls.

        Args:
            wheel_object: The wheel mesh/object
            radius: Wheel radius in meters
            steering_pivot: Optional existing pivot for steering

        Returns:
            WheelRig containing all rig components
        """
        rig = WheelRig(
            wheel=wheel_object,
            radius=radius,
        )

        # Create or use existing pivot for steering
        if steering_pivot:
            rig.pivot = steering_pivot
            rig.is_steering = True

        return rig

    @staticmethod
    def create_boids_system(
        emitter: Dict[str, Any],
        name: str,
        particle_count: int = 100
    ) -> Dict[str, Any]:
        """
        Create a wheel system from an emitter (for compatibility).

        Args:
            emitter: Emitter object
            name: Name for the system
            particle_count: Number of particles

        Returns:
            Dictionary representing the wheel system
        """
        return {
            'name': name,
            'emitter': emitter,
            'particle_count': particle_count,
            'rules': [],
            'settings': {},
        }

    def __init__(self, vehicle: Optional[Any] = None):
        """
        Initialize wheel system.

        Args:
            vehicle: Optional vehicle object this system belongs to
        """
        self.vehicle = vehicle
        self._wheels: Dict[str, WheelRig] = {}
        self._steering_angle: float = 0.0

    def add_wheel(self, wheel_id: str, wheel_object: Any,
                  radius: float = 0.35, steering: bool = False,
                  driven: bool = False) -> WheelRig:
        """
        Add a wheel to the system.

        Args:
            wheel_id: Unique identifier for the wheel
            wheel_object: The wheel object
            radius: Wheel radius
            steering: Whether this wheel can steer
            driven: Whether this wheel is powered

        Returns:
            The created WheelRig
        """
        rig = self.create_wheel_rig(wheel_object, radius)
        rig.is_steering = steering
        rig.is_driven = driven

        self._wheels[wheel_id] = rig
        return rig

    def get_wheel(self, wheel_id: str) -> Optional[WheelRig]:
        """Get a wheel by its ID."""
        return self._wheels.get(wheel_id)

    def get_all_wheels(self) -> List[WheelRig]:
        """Get all wheels in the system."""
        return list(self._wheels.values())

    def get_steering_wheels(self) -> List[WheelRig]:
        """Get all wheels that can steer."""
        return [w for w in self._wheels.values() if w.is_steering]

    def get_driven_wheels(self) -> List[WheelRig]:
        """Get all wheels that are powered."""
        return [w for w in self._wheels.values() if w.is_driven]

    def add_rotation_driver(
        self,
        wheel_id: str,
        speed_source: Any,
        speed_property: str = "location",
        axis: str = 'Y'
    ) -> None:
        """
        Add driver to rotate wheel based on vehicle speed.

        Args:
            wheel_id: ID of the wheel
            speed_source: Object whose movement drives rotation
            speed_property: Property to use for speed (default: location)
            axis: Rotation axis (default: Y for typical wheel spin)
        """
        wheel = self.get_wheel(wheel_id)
        if wheel:
            wheel.rotation_driver = {
                'source': speed_source,
                'property': speed_property,
                'axis': axis,
                'expression': f'distance / (2 * {pi} * {wheel.radius})',
            }

    def add_simple_rotation_driver(
        self,
        wheel_id: str,
        distance_object: Any,
        radius: Optional[float] = None
    ) -> None:
        """
        Add simple driver based on object X movement.

        Args:
            wheel_id: ID of the wheel
            distance_object: Object whose X location drives rotation
            radius: Optional override for wheel radius
        """
        wheel = self.get_wheel(wheel_id)
        if wheel:
            wheel.rotation_driver = {
                'source': distance_object,
                'property': 'location[0]',
                'axis': 'Y',
                'expression': f'dist / (2 * {pi} * {radius or wheel.radius})',
            }

    def set_behavior_rules(self, rules: List[Tuple[str, float]]) -> None:
        """
        Set behavior rules (compatibility method).

        Args:
            rules: List of (rule_name, weight) tuples

        Note: This is for compatibility with boids-style systems.
        For vehicles, use steering methods instead.
        """
        logger.warning("set_behavior_rules is for compatibility only")

    def get_rules(self) -> List[Any]:
        """Get current rules (compatibility method)."""
        return []

    def set_steering_angle(
        self,
        angle_degrees: float,
        wheel_id: Optional[str] = None
    ) -> None:
        """
        Set steering angle for steering wheels.

        Args:
            angle_degrees: Steering angle in degrees
            wheel_id: Optional specific wheel, or all steering wheels
        """
        self._steering_angle = angle_degrees

        if wheel_id:
            wheel = self.get_wheel(wheel_id)
            if wheel and wheel.pivot:
                wheel.pivot['rotation_z'] = radians(angle_degrees)
        else:
            for wheel in self.get_steering_wheels():
                if wheel.pivot:
                    wheel.pivot['rotation_z'] = radians(angle_degrees)

    @staticmethod
    def apply_ackermann_steering(
        front_left: Any,
        front_right: Any,
        wheelbase: float,
        track_width: float,
        steering_angle: float
    ) -> Tuple[float, float]:
        """
        Apply Ackermann steering geometry.

        The Ackermann principle ensures that during turns, the inner wheel
        follows a tighter radius than the outer wheel, reducing tire scrub.

        Args:
            front_left: Front left wheel pivot
            front_right: Front right wheel pivot
            wheelbase: Distance between front and rear axles (meters)
            track_width: Distance between left and right wheels (meters)
            steering_angle: Desired steering angle in degrees

        Returns:
            Tuple of (inner_angle, outer_angle) in degrees
        """
        # Use smooth threshold instead of hard cutoff
        if abs(steering_angle) < WheelSystem.ACKERMANN_THRESHOLD:
            return (steering_angle, steering_angle)

        steer_rad = radians(steering_angle)

        # Calculate turn radius from steering angle
        # turn_radius = wheelbase / tan(steering_angle)
        try:
            turn_radius = wheelbase / tan(steer_rad)
        except ZeroDivisionError:
            return (steering_angle, steering_angle)

        # Inner wheel angle (tighter turn)
        inner_rad = atan(wheelbase / (turn_radius - track_width / 2))
        inner_angle = degrees(inner_rad)

        # Outer wheel angle (wider turn)
        outer_rad = atan(wheelbase / (turn_radius + track_width / 2))
        outer_angle = degrees(outer_rad)

        # Apply to pivots (in a real Blender implementation)
        if steering_angle > 0:
            # Turning left - left wheel is inner
            if front_left is not None:
                front_left['steering_angle'] = inner_angle
            if front_right is not None:
                front_right['steering_angle'] = outer_angle
        else:
            # Turning right - right wheel is inner
            if front_left is not None:
                front_left['steering_angle'] = -outer_angle
            if front_right is not None:
                front_right['steering_angle'] = -inner_angle

        return (inner_angle, outer_angle)

    def apply_ackermann_to_vehicle(
        self,
        steering_angle: float,
        wheelbase: float,
        track_width: float
    ) -> Tuple[float, float]:
        """
        Apply Ackermann steering to all steering wheels.

        Args:
            steering_angle: Desired steering angle in degrees
            wheelbase: Distance between front and rear axles
            track_width: Distance between left and right wheels

        Returns:
            Tuple of (inner_angle, outer_angle) in degrees
        """
        steering_wheels = self.get_steering_wheels()
        if len(steering_wheels) < 2:
            # Single or no steering wheels - just apply directly
            self.set_steering_angle(steering_angle)
            return (steering_angle, steering_angle)

        # Assume first two are left/right pair
        left = steering_wheels[0].pivot if steering_wheels[0] else None
        right = steering_wheels[1].pivot if len(steering_wheels) > 1 else None

        return self.apply_ackermann_steering(
            left, right, wheelbase, track_width, steering_angle
        )


def setup_car_wheels(
    vehicle: Any,
    wheels: List[Any],
    radius: float = 0.35,
    steering_indices: Optional[List[int]] = None,
    driven_indices: Optional[List[int]] = None
) -> Dict[str, WheelRig]:
    """
    Setup wheel system for a car with common defaults.

    Args:
        vehicle: The vehicle object
        wheels: List of wheel objects (typically FL, FR, RL, RR)
        radius: Wheel radius
        steering_indices: Indices of steering wheels (default: [0, 1] for front)
        driven_indices: Indices of driven wheels (default: [2, 3] for rear)

    Returns:
        Dictionary of wheel_id -> WheelRig
    """
    system = WheelSystem(vehicle)

    if steering_indices is None:
        steering_indices = [0, 1]  # Front wheels steer by default

    if driven_indices is None:
        driven_indices = [2, 3]  # Rear wheels driven by default

    wheel_ids = ['FL', 'FR', 'RL', 'RR']

    rigs = {}
    for i, wheel in enumerate(wheels):
        is_steering = i in steering_indices
        is_driven = i in driven_indices

        wheel_id = wheel_ids[i] if i < len(wheel_ids) else f'W{i}'
        rig = system.add_wheel(
            wheel_id=wheel_id,
            wheel_object=wheel,
            radius=radius,
            steering=is_steering,
            driven=is_driven
        )

        # Add rotation driver for all wheels
        system.add_simple_rotation_driver(wheel_id, vehicle, radius)

        rigs[wheel_id] = rig

    return rigs
