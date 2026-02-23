"""
Culling Strategy

Implements frustum, distance, and occlusion culling for scene optimization.
Reduces render load by skipping invisible or distant objects.

Implements REQ-GN-08: Culling Strategy (NEW - Council).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set
from enum import Enum
import math


class CullingType(Enum):
    """Culling type classification."""
    FRUSTUM = "frustum"
    DISTANCE = "distance"
    OCCLUSION = "occlusion"
    SMALL_OBJECT = "small_object"
    BACKFACE = "backface"


@dataclass
class Frustum:
    """
    Camera frustum planes for frustum culling.

    Planes are stored as (normal_x, normal_y, normal_z, distance).
    Points are "inside" if dot(normal, point) + distance > 0 for all planes.
    """
    planes: List[Tuple[float, float, float, float]] = field(default_factory=list)

    @classmethod
    def from_camera(
        cls,
        camera_position: Tuple[float, float, float],
        camera_forward: Tuple[float, float, float],
        camera_up: Tuple[float, float, float],
        camera_right: Tuple[float, float, float],
        fov: float,
        aspect: float,
        near: float,
        far: float,
    ) -> "Frustum":
        """
        Create frustum from camera parameters.

        Args:
            camera_position: Camera world position
            camera_forward: Camera forward direction (normalized)
            camera_up: Camera up direction (normalized)
            camera_right: Camera right direction (normalized)
            fov: Vertical field of view in degrees
            aspect: Aspect ratio (width / height)
            near: Near clip distance
            far: Far clip distance

        Returns:
            Frustum with 6 clipping planes
        """
        planes = []

        # Helper to create plane from point and normal
        def make_plane(point, normal):
            return (
                normal[0], normal[1], normal[2],
                -(normal[0] * point[0] + normal[1] * point[1] + normal[2] * point[2])
            )

        # Near plane
        near_point = (
            camera_position[0] + camera_forward[0] * near,
            camera_position[1] + camera_forward[1] * near,
            camera_position[2] + camera_forward[2] * near,
        )
        planes.append(make_plane(near_point, camera_forward))

        # Far plane
        far_point = (
            camera_position[0] + camera_forward[0] * far,
            camera_position[1] + camera_forward[1] * far,
            camera_position[2] + camera_forward[2] * far,
        )
        planes.append(make_plane(far_point, tuple(-f for f in camera_forward)))

        # Calculate tangent of half FOV
        tan_half_fov = math.tan(math.radians(fov / 2))
        tan_half_fov_h = tan_half_fov * aspect

        # Top plane
        top_normal = (
            camera_forward[0] * tan_half_fov - camera_up[0],
            camera_forward[1] * tan_half_fov - camera_up[1],
            camera_forward[2] * tan_half_fov - camera_up[2],
        )
        top_normal = cls._normalize(top_normal)
        planes.append(make_plane(camera_position, top_normal))

        # Bottom plane
        bottom_normal = (
            camera_forward[0] * tan_half_fov + camera_up[0],
            camera_forward[1] * tan_half_fov + camera_up[1],
            camera_forward[2] * tan_half_fov + camera_up[2],
        )
        bottom_normal = cls._normalize(bottom_normal)
        planes.append(make_plane(camera_position, bottom_normal))

        # Left plane
        left_normal = (
            camera_forward[0] * tan_half_fov_h + camera_right[0],
            camera_forward[1] * tan_half_fov_h + camera_right[1],
            camera_forward[2] * tan_half_fov_h + camera_right[2],
        )
        left_normal = cls._normalize(left_normal)
        planes.append(make_plane(camera_position, left_normal))

        # Right plane
        right_normal = (
            camera_forward[0] * tan_half_fov_h - camera_right[0],
            camera_forward[1] * tan_half_fov_h - camera_right[1],
            camera_forward[2] * tan_half_fov_h - camera_right[2],
        )
        right_normal = cls._normalize(right_normal)
        planes.append(make_plane(camera_position, right_normal))

        return cls(planes=planes)

    @staticmethod
    def _normalize(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Normalize vector."""
        length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        if length == 0:
            return v
        return (v[0] / length, v[1] / length, v[2] / length)

    def is_point_inside(self, point: Tuple[float, float, float]) -> bool:
        """Check if point is inside frustum."""
        for plane in self.planes:
            distance = (
                plane[0] * point[0] +
                plane[1] * point[1] +
                plane[2] * point[2] +
                plane[3]
            )
            if distance < 0:
                return False
        return True

    def is_sphere_inside(
        self,
        center: Tuple[float, float, float],
        radius: float,
    ) -> bool:
        """Check if sphere intersects frustum."""
        for plane in self.planes:
            distance = (
                plane[0] * center[0] +
                plane[1] * center[1] +
                plane[2] * center[2] +
                plane[3]
            )
            if distance < -radius:
                return False
        return True

    def is_box_inside(
        self,
        min_corner: Tuple[float, float, float],
        max_corner: Tuple[float, float, float],
    ) -> bool:
        """Check if axis-aligned box intersects frustum."""
        # Test all 8 corners
        corners = [
            (min_corner[0], min_corner[1], min_corner[2]),
            (max_corner[0], min_corner[1], min_corner[2]),
            (min_corner[0], max_corner[1], min_corner[2]),
            (max_corner[0], max_corner[1], min_corner[2]),
            (min_corner[0], min_corner[1], max_corner[2]),
            (max_corner[0], min_corner[1], max_corner[2]),
            (min_corner[0], max_corner[1], max_corner[2]),
            (max_corner[0], max_corner[1], max_corner[2]),
        ]

        for plane in self.planes:
            all_outside = True
            for corner in corners:
                distance = (
                    plane[0] * corner[0] +
                    plane[1] * corner[1] +
                    plane[2] * corner[2] +
                    plane[3]
                )
                if distance >= 0:
                    all_outside = False
                    break
            if all_outside:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "planes": [list(p) for p in self.planes],
        }


@dataclass
class CullingConfig:
    """
    Culling configuration.

    Attributes:
        enable_frustum_culling: Enable frustum culling
        enable_distance_culling: Enable distance culling
        enable_small_object_culling: Enable small object culling
        enable_backface_culling: Enable backface culling
        max_distance: Maximum render distance
        min_screen_size: Minimum screen size percentage
        small_object_threshold: Size threshold for small object culling
    """
    enable_frustum_culling: bool = True
    enable_distance_culling: bool = True
    enable_small_object_culling: bool = True
    enable_backface_culling: bool = False
    max_distance: float = 1000.0
    min_screen_size: float = 0.01
    small_object_threshold: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enable_frustum_culling": self.enable_frustum_culling,
            "enable_distance_culling": self.enable_distance_culling,
            "enable_small_object_culling": self.enable_small_object_culling,
            "enable_backface_culling": self.enable_backface_culling,
            "max_distance": self.max_distance,
            "min_screen_size": self.min_screen_size,
            "small_object_threshold": self.small_object_threshold,
        }


@dataclass
class CullingResult:
    """
    Result of culling operation.

    Attributes:
        visible: List of visible instance IDs
        culled: List of culled instance IDs with reason
        statistics: Culling statistics
    """
    visible: List[str] = field(default_factory=list)
    culled: Dict[str, str] = field(default_factory=dict)
    statistics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "visible": self.visible,
            "culled": self.culled,
            "statistics": self.statistics,
        }


@dataclass
class InstanceBounds:
    """
    Bounding information for an instance.

    Attributes:
        instance_id: Instance identifier
        position: World position
        radius: Bounding sphere radius
        min_corner: AABB minimum corner
        max_corner: AABB maximum corner
        screen_size: Estimated screen size percentage
    """
    instance_id: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    radius: float = 1.0
    min_corner: Tuple[float, float, float] = (-0.5, -0.5, -0.5)
    max_corner: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    screen_size: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "position": list(self.position),
            "radius": self.radius,
            "min_corner": list(self.min_corner),
            "max_corner": list(self.max_corner),
            "screen_size": self.screen_size,
        }


class CullingManager:
    """
    Manages culling for scene instances.

    Performs frustum, distance, and small object culling.

    Usage:
        manager = CullingManager()
        manager.set_frustum_from_camera(...)
        result = manager.cull_instances(instances)
    """

    def __init__(self, config: Optional[CullingConfig] = None):
        """
        Initialize culling manager.

        Args:
            config: Culling configuration
        """
        self.config = config or CullingConfig()
        self.frustum: Optional[Frustum] = None
        self.camera_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def set_frustum(self, frustum: Frustum) -> None:
        """Set camera frustum."""
        self.frustum = frustum

    def set_frustum_from_camera(
        self,
        position: Tuple[float, float, float],
        forward: Tuple[float, float, float],
        up: Tuple[float, float, float],
        right: Tuple[float, float, float],
        fov: float,
        aspect: float,
        near: float,
        far: float,
    ) -> None:
        """Set frustum from camera parameters."""
        self.camera_position = position
        self.frustum = Frustum.from_camera(
            position, forward, up, right, fov, aspect, near, far
        )

    def cull_instances(
        self,
        instances: List[InstanceBounds],
    ) -> CullingResult:
        """
        Perform culling on instances.

        Args:
            instances: List of instance bounds

        Returns:
            CullingResult with visible and culled lists
        """
        result = CullingResult()
        stats = {
            "total": len(instances),
            "frustum_culled": 0,
            "distance_culled": 0,
            "small_object_culled": 0,
        }

        for instance in instances:
            should_cull = False
            cull_reason = ""

            # Distance culling
            if self.config.enable_distance_culling:
                distance = self._calculate_distance(instance.position)
                if distance > self.config.max_distance:
                    should_cull = True
                    cull_reason = "distance"
                    stats["distance_culled"] += 1

            # Frustum culling
            if not should_cull and self.config.enable_frustum_culling and self.frustum:
                if not self.frustum.is_sphere_inside(
                    instance.position, instance.radius
                ):
                    should_cull = True
                    cull_reason = "frustum"
                    stats["frustum_culled"] += 1

            # Small object culling
            if not should_cull and self.config.enable_small_object_culling:
                if instance.screen_size < self.config.min_screen_size:
                    should_cull = True
                    cull_reason = "small_object"
                    stats["small_object_culled"] += 1

            if should_cull:
                result.culled[instance.instance_id] = cull_reason
            else:
                result.visible.append(instance.instance_id)

        result.statistics = stats
        return result

    def _calculate_distance(self, position: Tuple[float, float, float]) -> float:
        """Calculate distance from camera to position."""
        dx = position[0] - self.camera_position[0]
        dy = position[1] - self.camera_position[1]
        dz = position[2] - self.camera_position[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def estimate_screen_size(
        self,
        instance: InstanceBounds,
        fov: float,
        screen_height: int,
    ) -> float:
        """
        Estimate screen size percentage.

        Args:
            instance: Instance bounds
            fov: Camera field of view in degrees
            screen_height: Screen height in pixels

        Returns:
            Estimated screen size (0-1)
        """
        distance = self._calculate_distance(instance.position)
        if distance <= 0:
            return 1.0

        # Calculate angular size
        angular_size = 2 * math.atan(instance.radius / distance)
        angular_size_deg = math.degrees(angular_size)

        # Calculate screen size
        screen_pixels = (angular_size_deg / fov) * screen_height
        screen_percentage = screen_pixels / screen_height

        return screen_percentage

    def to_gn_input(self) -> Dict[str, Any]:
        """
        Convert to GN input format.

        Returns:
            GN-compatible dictionary
        """
        return {
            "version": "1.0",
            "config": self.config.to_dict(),
            "frustum": self.frustum.to_dict() if self.frustum else None,
            "camera_position": list(self.camera_position),
        }


class OcclusionCuller:
    """
    Hierarchical Z-Buffer occlusion culling.

    Uses hierarchical depth buffer for efficient occlusion queries.
    This is a Python implementation for pre-calculation; actual
    runtime occlusion should use GPU-based methods in Blender.
    """

    def __init__(self, resolution: int = 256):
        """
        Initialize occlusion culler.

        Args:
            resolution: Hi-Z buffer resolution
        """
        self.resolution = resolution
        self.depth_buffer: Optional[List[List[float]]] = None

    def build_depth_buffer(
        self,
        occluders: List[InstanceBounds],
        camera_position: Tuple[float, float, float],
        camera_forward: Tuple[float, float, float],
    ) -> None:
        """
        Build hierarchical depth buffer from occluders.

        Args:
            occluders: List of potential occluding objects
            camera_position: Camera position
            camera_forward: Camera forward direction
        """
        # Initialize depth buffer with far plane
        self.depth_buffer = [[1.0] * self.resolution for _ in range(self.resolution)]

        # Rasterize occluders (simplified)
        for occluder in occluders:
            self._rasterize_occluder(occluder, camera_position, camera_forward)

    def _rasterize_occluder(
        self,
        occluder: InstanceBounds,
        camera_position: Tuple[float, float, float],
        camera_forward: Tuple[float, float, float],
    ) -> None:
        """Rasterize single occluder to depth buffer."""
        # Simplified: just use bounding sphere
        distance = math.sqrt(
            (occluder.position[0] - camera_position[0]) ** 2 +
            (occluder.position[1] - camera_position[1]) ** 2 +
            (occluder.position[2] - camera_position[2]) ** 2
        )

        # Calculate screen-space bounds (simplified)
        # In reality, would project and rasterize properly
        screen_x = int(self.resolution * 0.5)  # Center
        screen_y = int(self.resolution * 0.5)

        # Update depth at center
        normalized_depth = distance / 1000.0  # Assume 1000m far plane
        if 0 <= screen_x < self.resolution and 0 <= screen_y < self.resolution:
            self.depth_buffer[screen_y][screen_x] = min(
                self.depth_buffer[screen_y][screen_x],
                normalized_depth
            )

    def is_occluded(
        self,
        instance: InstanceBounds,
        camera_position: Tuple[float, float, float],
    ) -> bool:
        """
        Check if instance is occluded.

        Args:
            instance: Instance to test
            camera_position: Camera position

        Returns:
            True if occluded
        """
        if not self.depth_buffer:
            return False

        # Simplified occlusion test
        distance = math.sqrt(
            (instance.position[0] - camera_position[0]) ** 2 +
            (instance.position[1] - camera_position[1]) ** 2 +
            (instance.position[2] - camera_position[2]) ** 2
        )

        normalized_depth = distance / 1000.0
        screen_x = int(self.resolution * 0.5)
        screen_y = int(self.resolution * 0.5)

        if 0 <= screen_x < self.resolution and 0 <= screen_y < self.resolution:
            # If our depth is greater than buffer, we're occluded
            return normalized_depth > self.depth_buffer[screen_y][screen_x]

        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_frustum_from_camera(
    position: Tuple[float, float, float],
    rotation: Tuple[float, float, float],
    fov: float,
    aspect: float,
    near: float,
    far: float,
) -> Frustum:
    """
    Create frustum from camera transform.

    Args:
        position: Camera position
        rotation: Camera Euler rotation in degrees
        fov: Vertical field of view
        aspect: Aspect ratio
        near: Near clip
        far: Far clip

    Returns:
        Frustum planes
    """
    # Convert rotation to direction vectors
    pitch, yaw, roll = math.radians(rotation[0]), math.radians(rotation[1]), math.radians(rotation[2])

    # Forward direction
    forward = (
        math.sin(yaw) * math.cos(pitch),
        -math.sin(pitch),
        -math.cos(yaw) * math.cos(pitch),
    )

    # Right direction
    right = (
        math.cos(yaw) * math.cos(roll) + math.sin(yaw) * math.sin(pitch) * math.sin(roll),
        math.cos(pitch) * math.sin(roll),
        math.sin(yaw) * math.cos(roll) - math.cos(yaw) * math.sin(pitch) * math.sin(roll),
    )

    # Up direction
    up = (
        math.sin(yaw) * math.sin(pitch) * math.cos(roll) - math.cos(yaw) * math.sin(roll),
        math.cos(pitch) * math.cos(roll),
        -math.cos(yaw) * math.sin(pitch) * math.cos(roll) - math.sin(yaw) * math.sin(roll),
    )

    return Frustum.from_camera(
        position, forward, up, right, fov, aspect, near, far
    )


def cull_instances(
    instances: List[InstanceBounds],
    frustum: Optional[Frustum] = None,
    max_distance: float = 1000.0,
    min_screen_size: float = 0.01,
) -> CullingResult:
    """
    Convenience function for instance culling.

    Args:
        instances: Instances to cull
        frustum: Camera frustum
        max_distance: Maximum distance
        min_screen_size: Minimum screen size

    Returns:
        CullingResult
    """
    config = CullingConfig(
        max_distance=max_distance,
        min_screen_size=min_screen_size,
    )
    manager = CullingManager(config)
    if frustum:
        manager.set_frustum(frustum)
    return manager.cull_instances(instances)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "CullingType",
    # Data classes
    "Frustum",
    "CullingConfig",
    "CullingResult",
    "InstanceBounds",
    # Classes
    "CullingManager",
    "OcclusionCuller",
    # Functions
    "create_frustum_from_camera",
    "cull_instances",
]
