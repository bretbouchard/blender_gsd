"""
Ground Detection System for Launch Control

Terrain interaction system for realistic vehicle placement
and suspension response to ground surfaces.

Features:
- Automatic height adjustment from ground
- Surface normal detection for wheel orientation
- Surface type detection for physics adjustments
- Contact point management for multiple wheels
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

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


class SurfaceType(Enum):
    """Types of ground surfaces."""

    ASPHALT = "asphalt"
    CONCRETE = "concrete"
    GRAVEL = "gravel"
    DIRT = "dirt"
    SAND = "sand"
    GRASS = "grass"
    MUD = "mud"
    SNOW = "snow"
    ICE = "ice"
    ROCK = "rock"
    METAL = "metal"
    WOOD = "wood"
    UNKNOWN = "unknown"


@dataclass
class GroundConfig:
    """Configuration for ground detection."""

    ground_object: Optional[Any] = None
    offset: float = 0.0  # Additional offset from ground
    ray_direction: tuple[float, float, float] = (0, 0, -1)
    max_distance: float = 10.0  # Max raycast distance
    auto_align: bool = True  # Align to surface normal
    smooth_factor: float = 0.5  # Smoothing for height changes
    wheel_contact_offset: float = 0.0  # Offset for each wheel contact


@dataclass
class SurfaceInfo:
    """Information about a detected surface."""

    position: Vector
    normal: Vector
    distance: float
    surface_type: SurfaceType = SurfaceType.UNKNOWN
    friction_coefficient: float = 1.0
    object_name: str = ""

    def get_tilt_angle(self) -> float:
        """Get surface tilt angle from horizontal.

        Returns:
            Angle in degrees
        """
        # Dot product with up vector
        up = Vector((0, 0, 1))
        if hasattr(self.normal, "dot"):
            cos_angle = self.normal.dot(up)
        else:
            cos_angle = sum(n * u for n, u in zip(self.normal, up))
        return math.degrees(math.acos(min(1, max(-1, cos_angle))))


@dataclass
class ContactPoint:
    """Contact point for a wheel."""

    wheel_name: str
    position: Vector
    normal: Vector
    distance: float
    is_grounded: bool = True
    surface_info: Optional[SurfaceInfo] = None


class GroundDetection:
    """Terrain interaction system.

    Manages ground detection, surface interaction, and automatic
    height adjustment for vehicle rigs.

    Example:
        rig = LaunchControlRig(vehicle_body)
        rig.one_click_rig()

        ground = GroundDetection(rig)

        # Set ground object
        ground.set_ground_object(terrain_mesh, offset=0.0)

        # Enable automatic height adjustment
        ground.enable_auto_height()

        # Get surface info at a position
        info = ground.get_surface_info((0, 0, 0))
        print(f"Surface type: {info.surface_type}")

        # Get current wheel contact points
        contacts = ground.get_all_contact_points()
    """

    # Surface type detection heuristics
    SURFACE_COLORS = {
        SurfaceType.ASPHALT: [(0.1, 0.1, 0.1), (0.2, 0.2, 0.2)],
        SurfaceType.GRASS: [(0.1, 0.4, 0.1), (0.2, 0.6, 0.2)],
        SurfaceType.SAND: [(0.8, 0.7, 0.5), (0.9, 0.8, 0.6)],
        SurfaceType.DIRT: [(0.4, 0.3, 0.2), (0.6, 0.4, 0.3)],
        SurfaceType.SNOW: [(0.9, 0.9, 0.95), (1.0, 1.0, 1.0)],
        SurfaceType.CONCRETE: [(0.5, 0.5, 0.5), (0.7, 0.7, 0.7)],
    }

    FRICTION_COEFFICIENTS = {
        SurfaceType.ASPHALT: 1.0,
        SurfaceType.CONCRETE: 0.9,
        SurfaceType.GRAVEL: 0.6,
        SurfaceType.DIRT: 0.5,
        SurfaceType.SAND: 0.3,
        SurfaceType.GRASS: 0.4,
        SurfaceType.MUD: 0.2,
        SurfaceType.SNOW: 0.2,
        SurfaceType.ICE: 0.1,
        SurfaceType.ROCK: 0.7,
        SurfaceType.METAL: 0.6,
        SurfaceType.WOOD: 0.5,
        SurfaceType.UNKNOWN: 0.5,
    }

    def __init__(self, rig: "LaunchControlRig"):
        """Initialize ground detection system.

        Args:
            rig: The LaunchControlRig instance
        """
        self.rig = rig
        self.config = GroundConfig()
        self.contact_points: dict[str, ContactPoint] = {}
        self._last_heights: dict[str, float] = {}
        self._is_enabled = False
        self._update_handler: Optional[Any] = None

    def set_ground_object(
        self,
        ground: Any,
        offset: float = 0.0,
    ) -> None:
        """Set the ground object for detection.

        Args:
            ground: Blender mesh object to use as ground
            offset: Additional height offset from ground surface
        """
        self.config.ground_object = ground
        self.config.offset = offset

    def enable_auto_height(
        self,
        ray_direction: tuple[float, float, float] = (0, 0, -1),
    ) -> None:
        """Enable automatic height adjustment.

        Args:
            ray_direction: Direction for raycasting (default: down)
        """
        self.config.ray_direction = ray_direction
        self._is_enabled = True

        if BLENDER_AVAILABLE:
            self._setup_frame_handler()

    def disable_auto_height(self) -> None:
        """Disable automatic height adjustment."""
        self._is_enabled = False

        if BLENDER_AVAILABLE and self._update_handler:
            try:
                bpy.app.handlers.frame_change_post.remove(self._update_handler)
            except ValueError:
                pass
            self._update_handler = None

    def _setup_frame_handler(self) -> None:
        """Setup frame change handler for auto height."""
        if not BLENDER_AVAILABLE:
            return

        def update_height(scene: Any) -> None:
            self.update_all_wheels()

        self._update_handler = update_height
        bpy.app.handlers.frame_change_post.append(update_height)

    def set_wheel_contact_points(
        self,
        points: dict[str, tuple[float, float, float]],
    ) -> None:
        """Set contact point positions for wheels.

        Args:
            points: Dictionary mapping wheel names to local positions
        """
        for wheel_name, pos in points.items():
            self.contact_points[wheel_name] = ContactPoint(
                wheel_name=wheel_name,
                position=Vector(pos) if BLENDER_AVAILABLE else pos,
                normal=Vector((0, 0, 1)) if BLENDER_AVAILABLE else (0, 0, 1),
                distance=0.0,
                is_grounded=True,
            )

    def raycast_ground(
        self,
        origin: Vector,
        direction: Optional[Vector] = None,
    ) -> Optional[SurfaceInfo]:
        """Perform raycast to detect ground.

        Args:
            origin: World position to raycast from
            direction: Ray direction (default: config direction)

        Returns:
            SurfaceInfo if hit, None otherwise
        """
        if not BLENDER_AVAILABLE or not self.config.ground_object:
            return None

        direction = direction or Vector(self.config.ray_direction)
        max_dist = self.config.max_distance

        # Perform scene raycast
        hit, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(
            bpy.context.view_layer.depsgraph,
            origin,
            direction,
            distance=max_dist,
        )

        if hit and obj:
            surface_type = self._detect_surface_type(obj, location)

            return SurfaceInfo(
                position=location,
                normal=normal,
                distance=(location - origin).length,
                surface_type=surface_type,
                friction_coefficient=self.FRICTION_COEFFICIENTS.get(surface_type, 0.5),
                object_name=obj.name,
            )

        return None

    def _detect_surface_type(
        self,
        obj: Any,
        location: Vector,
    ) -> SurfaceType:
        """Detect surface type from object properties.

        Args:
            obj: Hit object
            location: Hit location

        Returns:
            Detected SurfaceType
        """
        # Check for custom property
        if hasattr(obj, "get") and obj.get("surface_type"):
            try:
                return SurfaceType(obj["surface_type"])
            except ValueError:
                pass

        # Check material name for hints
        if hasattr(obj, "material_slots"):
            for slot in obj.material_slots:
                if slot.material:
                    mat_name = slot.material.name.lower()
                    for surface_type in SurfaceType:
                        if surface_type.value in mat_name:
                            return surface_type

        # Check material color as heuristic
        if hasattr(obj, "material_slots") and obj.material_slots:
            mat = obj.material_slots[0].material
            if mat and hasattr(mat, "diffuse_color"):
                color = mat.diffuse_color[:3]
                return self._match_color_to_surface(color)

        return SurfaceType.UNKNOWN

    def _match_color_to_surface(
        self,
        color: tuple[float, float, float],
    ) -> SurfaceType:
        """Match a color to a surface type.

        Args:
            color: RGB color tuple

        Returns:
            Best matching SurfaceType
        """
        best_match = SurfaceType.UNKNOWN
        best_distance = float("inf")

        for surface_type, color_ranges in self.SURFACE_COLORS.items():
            for ref_color in color_ranges:
                # Calculate color distance
                distance = math.sqrt(
                    sum((c - rc) ** 2 for c, rc in zip(color, ref_color))
                )
                if distance < best_distance:
                    best_distance = distance
                    best_match = surface_type

        # Only return match if close enough
        if best_distance < 0.3:
            return best_match
        return SurfaceType.UNKNOWN

    def get_surface_normal(self, position: Vector) -> Vector:
        """Get surface normal at a position.

        Args:
            position: World position to check

        Returns:
            Surface normal vector
        """
        info = self.raycast_ground(position)
        if info:
            return info.normal

        # Default: flat ground
        return Vector((0, 0, 1)) if BLENDER_AVAILABLE else (0, 0, 1)

    def get_surface_type(self, position: Vector) -> str:
        """Get surface type at a position.

        Args:
            position: World position to check

        Returns:
            Surface type string
        """
        info = self.raycast_ground(position)
        if info:
            return info.surface_type.value
        return "unknown"

    def get_surface_info(self, position: Vector) -> Optional[SurfaceInfo]:
        """Get complete surface info at a position.

        Args:
            position: World position to check

        Returns:
            SurfaceInfo or None
        """
        return self.raycast_ground(position)

    def update_all_wheels(self) -> None:
        """Update contact points for all wheels."""
        if not self._is_enabled or not self.rig.detected_components:
            return

        armature = self.rig.rig_objects.get("armature")
        if not armature:
            return

        for wheel in self.rig.detected_components.wheels:
            if not hasattr(wheel, "name"):
                continue
            wheel_name = wheel.name

            # Get wheel world position
            if hasattr(wheel, "matrix_world"):
                wheel_pos = wheel.matrix_world.translation.copy()
            else:
                continue

            # Raycast from wheel position
            info = self.raycast_ground(wheel_pos)

            if info:
                # Apply smoothing
                last_height = self._last_heights.get(wheel_name, info.position.z)
                smoothed_z = (
                    last_height * self.config.smooth_factor
                    + info.position.z * (1 - self.config.smooth_factor)
                )
                self._last_heights[wheel_name] = smoothed_z

                # Update contact point
                self.contact_points[wheel_name] = ContactPoint(
                    wheel_name=wheel_name,
                    position=Vector((info.position.x, info.position.y, smoothed_z)),
                    normal=info.normal,
                    distance=info.distance,
                    is_grounded=True,
                    surface_info=info,
                )

    def get_contact_point(self, wheel_name: str) -> Optional[ContactPoint]:
        """Get contact point for a specific wheel.

        Args:
            wheel_name: Name of the wheel

        Returns:
            ContactPoint or None
        """
        return self.contact_points.get(wheel_name)

    def get_all_contact_points(self) -> dict[str, ContactPoint]:
        """Get all contact points.

        Returns:
            Dictionary of wheel names to ContactPoints
        """
        return dict(self.contact_points)

    def get_average_height(self) -> float:
        """Get average ground height from all contact points.

        Returns:
            Average height in world units
        """
        if not self.contact_points:
            return 0.0

        heights = [cp.position.z for cp in self.contact_points.values()]
        return sum(heights) / len(heights)

    def get_terrain_angle(self) -> tuple[float, float]:
        """Get terrain angle from contact points.

        Calculates pitch and roll based on wheel contact positions.

        Returns:
            Tuple of (pitch, roll) in degrees
        """
        if len(self.contact_points) < 2:
            return (0.0, 0.0)

        positions = list(self.contact_points.values())

        if len(positions) >= 4:
            # Use four-wheel configuration
            fl = positions[0].position if "fl" in positions[0].wheel_name.lower() else None
            fr = next((p.position for p in positions if "fr" in p.wheel_name.lower()), None)
            rl = next((p.position for p in positions if "rl" in p.wheel_name.lower()), None)
            rr = next((p.position for p in positions if "rr" in p.wheel_name.lower()), None)

            if fl and fr and rl and rr:
                # Calculate pitch (front to rear)
                front_avg = (fl.z + fr.z) / 2
                rear_avg = (rl.z + rr.z) / 2
                wheelbase = abs(fl.x - rl.x) if hasattr(fl, "x") else 2.7
                pitch = math.degrees(math.atan2(front_avg - rear_avg, wheelbase))

                # Calculate roll (left to right)
                left_avg = (fl.z + rl.z) / 2
                right_avg = (fr.z + rr.z) / 2
                track = abs(fl.y - fr.y) if hasattr(fl, "y") else 1.6
                roll = math.degrees(math.atan2(left_avg - right_avg, track))

                return (pitch, roll)

        # Simple calculation with available points
        z_values = [p.position.z for p in positions]
        if len(z_values) >= 2:
            # Rough estimate
            z_range = max(z_values) - min(z_values)
            return (z_range * 5, z_range * 3)  # Approximate angles

        return (0.0, 0.0)

    def align_to_terrain(
        self,
        armature: Any,
        frame: Optional[int] = None,
    ) -> None:
        """Align vehicle armature to terrain.

        Args:
            armature: Armature object to align
            frame: Frame for keyframe (None = no keyframe)
        """
        pitch, roll = self.get_terrain_angle()

        if BLENDER_AVAILABLE:
            # Convert to radians and set rotation
            armature.rotation_euler = (
                math.radians(roll),  # X rotation (roll)
                math.radians(pitch),  # Y rotation (pitch)
                armature.rotation_euler[2],  # Keep current heading
            )

            if frame is not None:
                armature.keyframe_insert(data_path="rotation_euler", frame=frame)

    def get_friction_coefficient(self) -> float:
        """Get average friction coefficient from contact points.

        Returns:
            Average friction coefficient
        """
        if not self.contact_points:
            return 1.0

        coefficients = [
            cp.surface_info.friction_coefficient
            for cp in self.contact_points.values()
            if cp.surface_info
        ]

        if not coefficients:
            return 1.0

        return sum(coefficients) / len(coefficients)
