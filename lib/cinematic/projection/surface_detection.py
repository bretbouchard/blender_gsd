"""
Surface Detection in Camera Frustum

Detects and classifies surfaces for anamorphic projection within
the camera's view frustum. Handles occlusion, multi-surface detection,
and surface selection masks.

Part of Phase 9.1 - Surface Detection (REQ-ANAM-02)
Beads: blender_gsd-35
"""

from __future__ import annotations
import math
from typing import List, Optional, Set, Dict, Tuple
from dataclasses import dataclass, field

from .types import (
    SurfaceType,
    SurfaceInfo,
    FrustumConfig,
    RayHit,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Fallback Vector implementation for testing
    class Vector:
        """Simple Vector fallback for testing outside Blender."""
        def __init__(self, data):
            if hasattr(data, '__iter__'):
                self._data = list(data)[:3]
                while len(self._data) < 3:
                    self._data.append(0.0)
            else:
                self._data = [float(data), 0.0, 0.0]

        def __getitem__(self, i):
            return self._data[i]

        def __add__(self, other):
            return Vector([self._data[i] + other._data[i] for i in range(3)])

        def __sub__(self, other):
            return Vector([self._data[i] - other._data[i] for i in range(3)])

        def __truediv__(self, scalar):
            return Vector([x / scalar for x in self._data])

        def __mul__(self, scalar):
            return Vector([x * scalar for x in self._data])

        def __rmul__(self, scalar):
            return self.__mul__(scalar)

        def dot(self, other):
            return sum(self._data[i] * other._data[i] for i in range(3))

        def length(self):
            return (sum(x * x for x in self._data)) ** 0.5

        def normalized(self):
            l = self.length()
            if l > 0:
                return Vector([x / l for x in self._data])
            return Vector([0, 0, 0])

        def normalize(self):
            l = self.length()
            if l > 0:
                self._data = [x / l for x in self._data]

        def cross(self, other):
            return Vector([
                self._data[1] * other._data[2] - self._data[2] * other._data[1],
                self._data[2] * other._data[0] - self._data[0] * other._data[2],
                self._data[0] * other._data[1] - self._data[1] * other._data[0],
            ])

        def copy(self):
            return Vector(self._data)

        @property
        def x(self):
            return self._data[0]

        @property
        def y(self):
            return self._data[1]

        @property
        def z(self):
            return self._data[2]

        def __iter__(self):
            return iter(self._data)

        def __repr__(self):
            return f"Vector({self._data})"

    Matrix = None


@dataclass
class OcclusionResult:
    """Result of occlusion detection for a surface."""
    surface: SurfaceInfo
    is_occluded: bool
    occlusion_ratio: float  # 0.0 = fully visible, 1.0 = fully occluded
    occluding_objects: List[str] = field(default_factory=list)
    visible_face_count: int = 0
    total_face_count: int = 0


@dataclass
class MultiSurfaceGroup:
    """Group of surfaces that form a continuous projection area."""
    surfaces: List[SurfaceInfo]
    group_type: str  # "floor", "wall", "corner", "custom"
    total_area: float
    center: Tuple[float, float, float]
    has_uv_continuity: bool


@dataclass
class SurfaceSelectionMask:
    """Mask for selecting specific faces/regions on a surface."""
    object_name: str
    selected_faces: List[int]  # Face indices
    mask_bounds: Tuple[Tuple[float, ...], Tuple[float, ...]]  # (min, max) in local space
    mask_area: float


def detect_surfaces(
    camera_name: str,
    config: FrustumConfig,
    check_occlusion: bool = True,
) -> List[SurfaceInfo]:
    """
    Detect surfaces within camera frustum with optional occlusion checking.

    This is the enhanced version of detect_surfaces_in_frustum with
    proper frustum bounds checking and surface filtering.

    Args:
        camera_name: Name of the camera object
        config: Frustum configuration
        check_occlusion: Whether to check for occlusion

    Returns:
        List of detected SurfaceInfo objects
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for surface detection")

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        raise ValueError(f"Camera '{camera_name}' not found or not a camera")

    surfaces = []

    # Get camera transform
    camera_pos = camera.matrix_world.translation
    camera_rot = camera.matrix_world.to_euler('XYZ')

    # Calculate frustum planes for culling
    frustum_planes = _calculate_frustum_planes(camera_pos, camera_rot, config)

    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue

        # Skip objects in ignore patterns
        if config.ignore_patterns and obj.name in config.ignore_patterns:
            continue

        # Check if object intersects frustum
        if not _object_in_frustum(obj, frustum_planes):
            continue

        # Detect surfaces on this object
        obj_surfaces = _detect_object_surfaces(
            obj, camera_pos, camera_rot, config, check_occlusion
        )
        surfaces.extend(obj_surfaces)

    return surfaces


def detect_occlusion(
    surface: SurfaceInfo,
    camera_name: str,
    config: FrustumConfig,
) -> OcclusionResult:
    """
    Check if a surface is occluded by other objects.

    Casts sample rays from camera to surface faces and counts
    how many are blocked by other objects.

    Args:
        surface: Surface to check
        camera_name: Camera object name
        config: Frustum configuration

    Returns:
        OcclusionResult with occlusion details
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for occlusion detection")

    camera = bpy.data.objects.get(camera_name)
    if camera is None:
        raise ValueError(f"Camera '{camera_name}' not found")

    obj = bpy.data.objects.get(surface.object_name)
    if obj is None:
        return OcclusionResult(
            surface=surface,
            is_occluded=True,
            occlusion_ratio=1.0,
            occluding_objects=[],
        )

    camera_pos = camera.matrix_world.translation

    visible_count = 0
    total_count = 0
    occluders: Set[str] = set()

    # Sample faces for occlusion test
    sample_step = max(1, len(obj.data.polygons) // 100)  # Max 100 samples

    for i, poly in enumerate(obj.data.polygons):
        if i % sample_step != 0:
            continue

        total_count += 1

        # Get face center in world space
        face_center = Vector((0.0, 0.0, 0.0))
        for vert_idx in poly.vertices:
            face_center += obj.matrix_world @ Vector(obj.data.vertices[vert_idx].co)
        face_center /= len(poly.vertices)

        # Cast ray from camera to face
        direction = (face_center - camera_pos).normalized()
        distance = (face_center - camera_pos).length

        # Check for hits before reaching the face
        hit = _cast_occlusion_ray(
            camera_pos, direction, distance * 0.99,
            ignore_objects=[surface.object_name]
        )

        if hit is None:
            visible_count += 1
        else:
            occluders.add(hit.object_name)

    occlusion_ratio = 1.0 - (visible_count / total_count) if total_count > 0 else 1.0

    return OcclusionResult(
        surface=surface,
        is_occluded=occlusion_ratio > 0.9,
        occlusion_ratio=occlusion_ratio,
        occluding_objects=list(occluders),
        visible_face_count=visible_count,
        total_face_count=total_count,
    )


def detect_multi_surface_groups(
    surfaces: List[SurfaceInfo],
    max_gap: float = 0.1,
) -> List[MultiSurfaceGroup]:
    """
    Detect groups of surfaces that form continuous projection areas.

    Finds corners (floor + wall), L-shapes, and other multi-surface
    configurations suitable for anamorphic projection.

    Args:
        surfaces: List of detected surfaces
        max_gap: Maximum gap between surfaces to consider connected

    Returns:
        List of MultiSurfaceGroup objects
    """
    if not surfaces:
        return []

    groups: List[MultiSurfaceGroup] = []

    # Group by proximity and type combination
    floors = [s for s in surfaces if s.surface_type == SurfaceType.FLOOR]
    walls = [s for s in surfaces if s.surface_type == SurfaceType.WALL]
    ceilings = [s for s in surfaces if s.surface_type == SurfaceType.CEILING]

    # Detect corners (floor + adjacent wall)
    for floor in floors:
        for wall in walls:
            gap = _calculate_surface_gap(floor, wall)
            if gap < max_gap:
                # Check if they form a corner (wall should be near floor edge)
                if _forms_corner(floor, wall):
                    group = MultiSurfaceGroup(
                        surfaces=[floor, wall],
                        group_type="corner",
                        total_area=floor.area + wall.area,
                        center=_calculate_group_center([floor, wall]),
                        has_uv_continuity=False,  # Would need UV analysis
                    )
                    groups.append(group)

    # Single surface groups
    for surface in surfaces:
        groups.append(MultiSurfaceGroup(
            surfaces=[surface],
            group_type=surface.surface_type.value,
            total_area=surface.area,
            center=surface.center,
            has_uv_continuity=surface.has_uv,
        ))

    return groups


def create_surface_selection_mask(
    surface: SurfaceInfo,
    camera_name: str,
    config: FrustumConfig,
    expand_margin: float = 0.0,
) -> SurfaceSelectionMask:
    """
    Create a mask for selecting faces within frustum projection area.

    Identifies which faces on a surface will receive the projected
    image based on camera frustum intersection.

    Args:
        surface: Surface to create mask for
        camera_name: Camera object name
        config: Frustum configuration
        expand_margin: Margin to expand selection beyond frustum

    Returns:
        SurfaceSelectionMask with selected face indices
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for mask creation")

    camera = bpy.data.objects.get(camera_name)
    obj = bpy.data.objects.get(surface.object_name)

    if camera is None or obj is None:
        raise ValueError("Camera or object not found")

    camera_pos = camera.matrix_world.translation
    camera_rot = camera.matrix_world.to_euler('XYZ')

    # Calculate frustum bounds at surface distance
    surface_center = Vector(surface.center)
    surface_distance = (surface_center - camera_pos).length

    frustum_corners = _get_frustum_corners_at_distance(
        camera_pos, camera_rot, config, surface_distance
    )

    # Find faces within frustum bounds
    selected_faces = []
    local_min = [float('inf')] * 3
    local_max = [float('-inf')] * 3

    world_to_local = obj.matrix_world.inverted()

    for i, poly in enumerate(obj.data.polygons):
        # Get face center
        face_center = Vector((0.0, 0.0, 0.0))
        for vert_idx in poly.vertices:
            face_center += Vector(obj.data.vertices[vert_idx].co)
        face_center /= len(poly.vertices)

        # Transform to world space
        world_center = obj.matrix_world @ face_center

        # Check if within frustum (simplified - use frustum volume test)
        if _point_in_frustum(world_center, camera_pos, camera_rot, config, expand_margin):
            selected_faces.append(i)

            # Update bounds
            for j in range(3):
                local_min[j] = min(local_min[j], face_center[j])
                local_max[j] = max(local_max[j], face_center[j])

    # Calculate mask area
    mask_area = 0.0
    for face_idx in selected_faces:
        mask_area += obj.data.polygons[face_idx].area

    return SurfaceSelectionMask(
        object_name=surface.object_name,
        selected_faces=selected_faces,
        mask_bounds=(tuple(local_min), tuple(local_max)),
        mask_area=mask_area,
    )


def filter_surfaces_by_type(
    surfaces: List[SurfaceInfo],
    surface_types: List[SurfaceType],
) -> List[SurfaceInfo]:
    """
    Filter surfaces by type.

    Args:
        surfaces: List of surfaces to filter
        surface_types: Allowed surface types

    Returns:
        Filtered list of surfaces
    """
    return [s for s in surfaces if s.surface_type in surface_types]


def get_best_projection_surfaces(
    surfaces: List[SurfaceInfo],
    camera_name: str,
    prefer_type: Optional[SurfaceType] = None,
    min_area: float = 0.1,
) -> List[SurfaceInfo]:
    """
    Get the best surfaces for projection based on area and visibility.

    Args:
        surfaces: List of candidate surfaces
        camera_name: Camera for visibility calculation
        prefer_type: Preferred surface type
        min_area: Minimum surface area

    Returns:
        Sorted list of best surfaces for projection
    """
    # Filter by minimum area
    valid = [s for s in surfaces if s.area >= min_area and s.in_frustum]

    # Sort by preference and area
    def sort_key(s: SurfaceInfo) -> Tuple[int, float]:
        # Prefer specified type (0) over others (1)
        type_priority = 0 if s.surface_type == prefer_type else 1
        # Larger area is better (negative for descending sort)
        return (type_priority, -s.area)

    return sorted(valid, key=sort_key)


# Private helper functions

def _calculate_frustum_planes(
    camera_pos: Vector,
    camera_rot,
    config: FrustumConfig,
) -> List[Tuple[Vector, Vector]]:
    """Calculate the 6 frustum planes as (point, normal) tuples."""
    planes = []

    fov_rad = math.radians(config.fov)
    aspect = config.resolution_x / config.resolution_y

    # Near and far planes
    forward = Vector((0.0, 0.0, -1.0))
    forward.rotate(camera_rot)

    near_point = camera_pos + forward * config.near_clip
    far_point = camera_pos + forward * config.far_clip

    planes.append((near_point, forward))  # Near plane
    planes.append((far_point, -forward))  # Far plane (normal points inward)

    # Left, right, top, bottom planes
    half_fov_h = fov_rad / 2
    half_fov_v = math.atan(math.tan(half_fov_h) / aspect)

    right = Vector((1.0, 0.0, 0.0))
    right.rotate(camera_rot)
    up = Vector((0.0, 1.0, 0.0))
    up.rotate(camera_rot)

    # Left plane
    left_normal = forward.copy()
    left_normal.rotate(mathutils.Euler((0, 0, half_fov_h), 'XYZ'))
    left_normal = left_normal.cross(up).normalized()
    planes.append((camera_pos, left_normal))

    # Right plane
    right_normal = forward.copy()
    right_normal.rotate(mathutils.Euler((0, 0, -half_fov_h), 'XYZ'))
    right_normal = up.cross(right_normal).normalized()
    planes.append((camera_pos, right_normal))

    # Top plane
    top_normal = forward.copy()
    top_normal.rotate(mathutils.Euler((half_fov_v, 0, 0), 'XYZ'))
    top_normal = right.cross(top_normal).normalized()
    planes.append((camera_pos, top_normal))

    # Bottom plane
    bottom_normal = forward.copy()
    bottom_normal.rotate(mathutils.Euler((-half_fov_v, 0, 0), 'XYZ'))
    bottom_normal = bottom_normal.cross(right).normalized()
    planes.append((camera_pos, bottom_normal))

    return planes


def _object_in_frustum(
    obj,
    frustum_planes: List[Tuple[Vector, Vector]],
) -> bool:
    """Check if object bounding box intersects frustum."""
    # Get world-space bounding box corners
    bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    # Check against each plane
    for point, normal in frustum_planes:
        # If all corners are behind a plane, object is outside frustum
        all_behind = all(
            (corner - point).dot(normal) < 0
            for corner in bbox_world
        )
        if all_behind:
            return False

    return True


def _detect_object_surfaces(
    obj,
    camera_pos: Vector,
    camera_rot,
    config: FrustumConfig,
    check_occlusion: bool,
) -> List[SurfaceInfo]:
    """Detect surface regions on a single object."""
    surfaces = []

    # Group faces by normal direction
    face_groups: Dict[SurfaceType, List[int]] = {
        SurfaceType.FLOOR: [],
        SurfaceType.WALL: [],
        SurfaceType.CEILING: [],
        SurfaceType.CUSTOM: [],
    }

    for i, poly in enumerate(obj.data.polygons):
        # Get world-space normal
        world_normal = obj.matrix_world @ poly.normal
        world_normal = Vector(world_normal).normalized()

        # Classify by normal
        if world_normal.z > 0.7:
            face_groups[SurfaceType.FLOOR].append(i)
        elif world_normal.z < -0.7:
            face_groups[SurfaceType.CEILING].append(i)
        elif abs(world_normal.z) < 0.3:
            face_groups[SurfaceType.WALL].append(i)
        else:
            face_groups[SurfaceType.CUSTOM].append(i)

    # Create SurfaceInfo for each non-empty group
    for surface_type, face_indices in face_groups.items():
        if not face_indices:
            continue

        # Filter by surface_type if specified
        if config.surface_filter != SurfaceType.ALL:
            if surface_type != config.surface_filter:
                continue

        # Calculate center and area
        center = Vector((0.0, 0.0, 0.0))
        area = 0.0

        for face_idx in face_indices:
            poly = obj.data.polygons[face_idx]
            area += poly.area

            # Accumulate face center
            face_center = Vector((0.0, 0.0, 0.0))
            for vert_idx in poly.vertices:
                face_center += Vector(obj.data.vertices[vert_idx].co)
            center += face_center / len(poly.vertices)

        center = obj.matrix_world @ (center / len(face_indices))

        # Scale area by object scale
        scale = obj.scale
        area *= (scale.x * scale.y * scale.z) ** (1/3)

        # Get dominant normal
        avg_normal = Vector((0.0, 0.0, 0.0))
        for face_idx in face_indices:
            world_normal = obj.matrix_world @ obj.data.polygons[face_idx].normal
            avg_normal += Vector(world_normal).normalized()
        avg_normal /= len(face_indices)
        avg_normal.normalize()

        # Check UV
        has_uv = len(obj.data.uv_layers) > 0
        uv_layer = obj.data.uv_layers.active.name if has_uv else ""

        surface_info = SurfaceInfo(
            object_name=obj.name,
            surface_type=surface_type,
            center=tuple(center),
            normal=tuple(avg_normal),
            area=area,
            face_count=len(face_indices),
            in_frustum=True,  # Already filtered by frustum check
            has_uv=has_uv,
            uv_layer=uv_layer,
        )

        surfaces.append(surface_info)

    return surfaces


def _cast_occlusion_ray(
    origin: Vector,
    direction: Vector,
    max_distance: float,
    ignore_objects: List[str],
) -> Optional[RayHit]:
    """Cast a ray for occlusion testing."""
    ignore_set = set(ignore_objects)

    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if obj.name in ignore_set:
            continue

        world_matrix = obj.matrix_world
        world_matrix_inv = world_matrix.inverted()

        origin_obj = world_matrix_inv @ origin
        direction_obj = world_matrix_inv @ (origin + direction) - origin_obj
        direction_obj.normalize()

        hit, location, normal, face_index = obj.ray_cast(origin_obj, direction_obj)

        if hit:
            world_location = world_matrix @ location
            distance = (world_location - origin).length

            if distance < max_distance:
                return RayHit(
                    hit=True,
                    position=tuple(world_location),
                    normal=tuple(world_matrix.transposed() @ normal),
                    distance=distance,
                    object_name=obj.name,
                    face_index=face_index,
                )

    return None


def _calculate_surface_gap(s1: SurfaceInfo, s2: SurfaceInfo) -> float:
    """Calculate minimum gap between two surfaces."""
    p1 = Vector(s1.center)
    p2 = Vector(s2.center)
    return (p2 - p1).length()


def _forms_corner(floor: SurfaceInfo, wall: SurfaceInfo) -> bool:
    """Check if floor and wall form a corner."""
    # Wall should be near floor level
    floor_z = floor.center[2]
    wall_z = wall.center[2]

    # Wall center should be within reasonable range of floor
    return abs(wall_z - floor_z) < 2.0


def _calculate_group_center(surfaces: List[SurfaceInfo]) -> Tuple[float, float, float]:
    """Calculate center of a surface group."""
    if not surfaces:
        return (0.0, 0.0, 0.0)

    center = Vector((0.0, 0.0, 0.0))
    for s in surfaces:
        center += Vector(s.center)
    center /= len(surfaces)

    return tuple(center)


def _get_frustum_corners_at_distance(
    camera_pos: Vector,
    camera_rot,
    config: FrustumConfig,
    distance: float,
) -> List[Vector]:
    """Get frustum corner positions at a specific distance from camera."""
    corners = []

    fov_rad = math.radians(config.fov)
    aspect = config.resolution_x / config.resolution_y

    half_h = distance * math.tan(fov_rad / 2)
    half_v = half_h / aspect

    forward = Vector((0.0, 0.0, -1.0))
    forward.rotate(camera_rot)
    right = Vector((1.0, 0.0, 0.0))
    right.rotate(camera_rot)
    up = Vector((0.0, 1.0, 0.0))
    up.rotate(camera_rot)

    center = camera_pos + forward * distance

    # Four corners
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            corner = center + right * (dx * half_h) + up * (dy * half_v)
            corners.append(corner)

    return corners


def _point_in_frustum(
    point: Vector,
    camera_pos: Vector,
    camera_rot,
    config: FrustumConfig,
    margin: float = 0.0,
) -> bool:
    """Check if a point is inside the camera frustum."""
    # Transform point to camera space
    world_to_cam = camera_rot.to_matrix().to_4x4()
    world_to_cam.translation = -camera_pos

    point_cam = world_to_cam @ point

    # Check if behind camera
    if point_cam.z > -config.near_clip:
        return False

    distance = -point_cam.z

    # Calculate frustum bounds at this distance
    fov_rad = math.radians(config.fov)
    aspect = config.resolution_x / config.resolution_y

    half_h = distance * math.tan(fov_rad / 2) + margin
    half_v = half_h / aspect + margin

    # Check if within frustum bounds
    return (abs(point_cam.x) <= half_h and
            abs(point_cam.y) <= half_v and
            distance <= config.far_clip)
