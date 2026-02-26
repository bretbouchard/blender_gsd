"""
Viewing angle calculator for anamorphic billboard effects.

Calculates optimal viewing positions for anamorphic illusions,
ensuring the 3D effect is visible from the intended location.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import math


@dataclass
class ViewingPosition:
    """
    Optimal viewing position for anamorphic effect.

    Attributes:
        distance: Distance from display center (meters)
        horizontal_angle: Horizontal angle from display center (degrees)
        vertical_angle: Vertical angle from display center (degrees)
        height: Viewer eye height (meters)
        camera_location: 3D location tuple (x, y, z)
        camera_rotation: Euler rotation tuple (x, y, z) in degrees
        fov: Recommended field of view (degrees)
        fov_vertical: Vertical field of view
    """
    distance: float
    horizontal_angle: float
    vertical_angle: float
    height: float
    camera_location: Tuple[float, float, float]
    camera_rotation: Tuple[float, float, float]
    fov: float = 50.0
    fov_vertical: float = 30.0


class ViewingAngleCalculator:
    """
    Calculate optimal viewing positions for anamorphic billboards.

    The anamorphic illusion only works from a specific viewing angle.
    This calculator determines that position based on display geometry.

    Example:
        >>> calc = ViewingAngleCalculator(
        ...     display_width=12.0,
        ...     display_height=9.0,
        ...     display_type="l_shaped",
        ... )
        >>> position = calc.calculate_optimal_position()
        >>> print(f"Stand at: {position.camera_location}")
    """

    def __init__(
        self,
        display_width: float,
        display_height: float,
        display_type: str = "l_shaped",
        display_depth: float = 3.0,
        curve_angle: float = 90.0,
    ):
        """
        Initialize calculator with display dimensions.

        Args:
            display_width: Display width in meters
            display_height: Display height in meters
            display_type: "flat", "l_shaped", or "curved"
            display_depth: Depth for L-shaped displays
            curve_angle: Arc angle for curved displays (degrees)
        """
        self.display_width = display_width
        self.display_height = display_height
        self.display_type = display_type
        self.display_depth = display_depth
        self.curve_angle = curve_angle

    def calculate_optimal_position(
        self,
        eye_height: float = 1.7,
        viewing_distance_factor: float = 2.5,
    ) -> ViewingPosition:
        """
        Calculate optimal viewing position for anamorphic effect.

        Args:
            eye_height: Viewer eye height in meters (default 1.7m average)
            viewing_distance_factor: Distance as multiple of display height

        Returns:
            ViewingPosition with optimal camera settings
        """
        # Calculate optimal distance
        # Rule of thumb: 2-3x display height for comfortable viewing
        optimal_distance = self.display_height * viewing_distance_factor

        # Calculate horizontal angle
        # For L-shaped: optimal is ~45° from corner
        # For curved: optimal is center of arc
        if self.display_type == "l_shaped":
            horizontal_angle = 45.0
        elif self.display_type == "curved":
            horizontal_angle = 0.0  # Center of curve
        else:
            horizontal_angle = 0.0  # Straight on for flat

        # Calculate vertical angle
        # Slightly below center for most natural viewing
        display_center_height = self.display_height / 2
        vertical_offset = eye_height - display_center_height
        vertical_angle = math.degrees(
            math.atan2(vertical_offset, optimal_distance)
        )

        # Calculate camera position
        # L-shaped: position is at 45° from corner
        if self.display_type == "l_shaped":
            cam_x = -optimal_distance * math.cos(math.radians(horizontal_angle))
            cam_y = -optimal_distance * math.sin(math.radians(horizontal_angle))
        else:
            cam_x = 0.0
            cam_y = -optimal_distance

        cam_z = eye_height

        # Calculate camera rotation to look at display center
        # Point at corner for L-shaped, center for others
        if self.display_type == "l_shaped":
            target = (0.0, 0.0, self.display_height / 2)
        else:
            target = (0.0, 0.0, self.display_height / 2)

        # Calculate rotation angles
        dx = target[0] - cam_x
        dy = target[1] - cam_y
        dz = target[2] - cam_z

        # Horizontal rotation (around Z axis)
        rot_z = math.degrees(math.atan2(dx, -dy))

        # Vertical rotation (pitch)
        horizontal_dist = math.sqrt(dx * dx + dy * dy)
        rot_x = math.degrees(math.atan2(dz, horizontal_dist))

        rot_y = 0.0  # No roll

        # Calculate recommended FOV
        # Should encompass entire display
        fov = self._calculate_fov(optimal_distance, self.display_width)

        return ViewingPosition(
            distance=optimal_distance,
            horizontal_angle=horizontal_angle,
            vertical_angle=vertical_angle,
            height=eye_height,
            camera_location=(cam_x, cam_y, cam_z),
            camera_rotation=(rot_x, rot_y, rot_z),
            fov=fov,
            fov_vertical=self._calculate_fov(optimal_distance, self.display_height),
        )

    def calculate_viewing_zone(
        self,
        tolerance_degrees: float = 5.0,
    ) -> Tuple[float, float]:
        """
        Calculate acceptable viewing zone range.

        The illusion is effective within a range around the optimal position.

        Args:
            tolerance_degrees: Acceptable deviation from optimal angle

        Returns:
            Tuple of (min_distance, max_distance) in meters
        """
        optimal = self.calculate_optimal_position()

        # Distance tolerance based on angle tolerance
        # Using tangent: tolerance_dist = distance * tan(tolerance_angle)
        tolerance_factor = math.tan(math.radians(tolerance_degrees))
        distance_tolerance = optimal.distance * tolerance_factor

        min_distance = optimal.distance - distance_tolerance
        max_distance = optimal.distance + distance_tolerance

        return (max(1.0, min_distance), max_distance)

    def calculate_multiple_viewing_positions(
        self,
        num_positions: int = 5,
        spread_degrees: float = 30.0,
    ) -> list[ViewingPosition]:
        """
        Calculate multiple viewing positions across a spread.

        Useful for testing how the effect looks from different angles.

        Args:
            num_positions: Number of positions to calculate
            spread_degrees: Total spread angle (split evenly)

        Returns:
            List of ViewingPosition objects
        """
        positions = []
        angle_step = spread_degrees / (num_positions - 1)
        start_angle = -spread_degrees / 2

        for i in range(num_positions):
            angle = start_angle + i * angle_step
            pos = self.calculate_optimal_position()
            pos.horizontal_angle = angle

            # Recalculate camera position for this angle
            optimal_distance = pos.distance
            pos.camera_location = (
                -optimal_distance * math.sin(math.radians(angle)),
                -optimal_distance * math.cos(math.radians(angle)),
                pos.height,
            )

            positions.append(pos)

        return positions

    def _calculate_fov(self, distance: float, size: float) -> float:
        """Calculate FOV needed to see object of given size at distance."""
        return 2.0 * math.degrees(math.atan2(size / 2, distance))


def calculate_optimal_viewing_angle(
    display_width: float,
    display_height: float,
    display_type: str = "l_shaped",
    **kwargs,
) -> ViewingPosition:
    """
    Convenience function to calculate optimal viewing angle.

    Args:
        display_width: Display width in meters
        display_height: Display height in meters
        display_type: "flat", "l_shaped", or "curved"
        **kwargs: Additional arguments passed to ViewingAngleCalculator

    Returns:
        ViewingPosition with optimal camera settings

    Example:
        >>> pos = calculate_optimal_viewing_angle(12.0, 9.0, "l_shaped")
        >>> print(f"Camera location: {pos.camera_location}")
        >>> print(f"Camera rotation: {pos.camera_rotation}")
        >>> print(f"FOV: {pos.fov}°")
    """
    calc = ViewingAngleCalculator(
        display_width=display_width,
        display_height=display_height,
        display_type=display_type,
        **kwargs,
    )
    return calc.calculate_optimal_position()


def create_viewing_camera(
    position: ViewingPosition,
    name: str = "AnamorphicViewCamera",
) -> any:
    """
    Create camera at optimal viewing position.

    Args:
        position: ViewingPosition from calculator
        name: Camera object name

    Returns:
        Created camera object
    """
    try:
        import bpy
        from math import radians

        # Create camera
        camera = bpy.data.cameras.new(name)
        obj = bpy.data.objects.new(name, camera)

        # Position camera
        obj.location = position.camera_location

        # Set rotation
        obj.rotation_euler = (
            radians(position.camera_rotation[0]),
            radians(position.camera_rotation[1]),
            radians(position.camera_rotation[2]),
        )

        # Set FOV
        camera.lens_unit = 'FOV'
        camera.angle = radians(position.fov)

        # Link to scene
        bpy.context.collection.objects.link(obj)

        return obj

    except ImportError:
        return None
    except Exception:
        return None
