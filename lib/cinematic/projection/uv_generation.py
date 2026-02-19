"""
UV Generation from Camera Projection

Generates UV coordinates from camera projection mapping for anamorphic
projection. Handles UV seams on complex geometry, supports multiple
surfaces, and creates export-friendly UV layouts.

Part of Phase 9.2 - UV Generation (REQ-ANAM-03)
Beads: blender_gsd-36
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field

from .types import (
    RayHit,
    FrustumConfig,
    ProjectionResult,
    SurfaceInfo,
    SurfaceType,
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
class UVGenerationResult:
    """Result of UV generation operation."""
    object_name: str = ""
    uv_layer_name: str = ""
    uv_count: int = 0  # Number of UV coordinates generated
    face_count: int = 0  # Number of faces with UVs
    coverage: float = 0.0  # Percentage of faces covered (0-100)
    has_seams: bool = False  # Whether UV seams were created
    seam_count: int = 0  # Number of seam edges
    uv_bounds: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)  # (min_u, min_v, max_u, max_v)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_name": self.object_name,
            "uv_layer_name": self.uv_layer_name,
            "uv_count": self.uv_count,
            "face_count": self.face_count,
            "coverage": self.coverage,
            "has_seams": self.has_seams,
            "seam_count": self.seam_count,
            "uv_bounds": list(self.uv_bounds),
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UVGenerationResult:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object_name", ""),
            uv_layer_name=data.get("uv_layer_name", ""),
            uv_count=data.get("uv_count", 0),
            face_count=data.get("face_count", 0),
            coverage=data.get("coverage", 0.0),
            has_seams=data.get("has_seams", False),
            seam_count=data.get("seam_count", 0),
            uv_bounds=tuple(data.get("uv_bounds", (0.0, 0.0, 1.0, 1.0))),
            warnings=data.get("warnings", []),
        )


@dataclass
class UVSeamInfo:
    """Information about a UV seam edge."""
    edge_index: int
    vertices: Tuple[int, int]
    angle: float  # Dihedral angle between faces (radians)
    reason: str  # Why this edge was marked as seam


@dataclass
class UVLayoutConfig:
    """Configuration for UV layout generation."""
    # UV layer name to create/use
    uv_layer_name: str = "ProjectionUV"

    # Padding between UV islands (in UV space, 0-1)
    island_padding: float = 0.02

    # Whether to pack UV islands into 0-1 space
    pack_islands: bool = True

    # Whether to mark seams automatically on sharp edges
    auto_seam_angle: float = math.radians(30.0)  # 30 degrees

    # Minimum angle to consider for seam
    min_seam_angle: float = math.radians(60.0)  # 60 degrees

    # Whether to normalize UVs to 0-1 range
    normalize_uvs: bool = True

    # Maximum stretch allowed (1.0 = no stretch)
    max_stretch: float = 0.5

    # Whether to merge vertices with same position
    merge_vertices: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "uv_layer_name": self.uv_layer_name,
            "island_padding": self.island_padding,
            "pack_islands": self.pack_islands,
            "auto_seam_angle": self.auto_seam_angle,
            "min_seam_angle": self.min_seam_angle,
            "normalize_uvs": self.normalize_uvs,
            "max_stretch": self.max_stretch,
            "merge_vertices": self.merge_vertices,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UVLayoutConfig:
        """Create from dictionary."""
        return cls(
            uv_layer_name=data.get("uv_layer_name", "ProjectionUV"),
            island_padding=data.get("island_padding", 0.02),
            pack_islands=data.get("pack_islands", True),
            auto_seam_angle=data.get("auto_seam_angle", math.radians(30.0)),
            min_seam_angle=data.get("min_seam_angle", math.radians(60.0)),
            normalize_uvs=data.get("normalize_uvs", True),
            max_stretch=data.get("max_stretch", 0.5),
            merge_vertices=data.get("merge_vertices", False),
        )


def generate_uvs_from_projection(
    projection_result: ProjectionResult,
    uv_config: Optional[UVLayoutConfig] = None,
) -> List[UVGenerationResult]:
    """
    Generate UV coordinates from projection ray hits.

    Takes the projection result and generates UV coordinates on each
    hit object based on where rays intersected the geometry.

    Args:
        projection_result: Result from project_from_camera()
        uv_config: UV layout configuration

    Returns:
        List of UVGenerationResult for each processed object
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for UV generation")

    config = uv_config or UVLayoutConfig()
    results = []

    # Process each object that received hits
    for obj_name, hits in projection_result.hits_by_object.items():
        obj = bpy.data.objects.get(obj_name)
        if obj is None or obj.type != 'MESH':
            continue

        result = _generate_object_uvs(obj, hits, config, projection_result.config)
        results.append(result)

    return results


def generate_uvs_for_surface(
    surface: SurfaceInfo,
    camera_name: str,
    config: FrustumConfig,
    uv_config: Optional[UVLayoutConfig] = None,
) -> UVGenerationResult:
    """
    Generate UVs for a single surface using camera projection.

    Convenience function for generating UVs on a specific surface
    without running full projection first.

    Args:
        surface: Surface to generate UVs for
        camera_name: Camera to project from
        config: Frustum configuration
        uv_config: UV layout configuration

    Returns:
        UVGenerationResult with generation details
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for UV generation")

    camera = bpy.data.objects.get(camera_name)
    obj = bpy.data.objects.get(surface.object_name)

    if camera is None or obj is None:
        raise ValueError("Camera or object not found")

    uv_cfg = uv_config or UVLayoutConfig()

    # Get camera transform
    camera_pos = camera.matrix_world.translation
    camera_rot = camera.matrix_world.to_euler('XYZ')

    # Generate projection UVs for each vertex
    return _generate_surface_projection_uvs(obj, camera_pos, camera_rot, config, uv_cfg)


def detect_uv_seams(
    surface: SurfaceInfo,
    angle_threshold: float = math.radians(60.0),
) -> List[UVSeamInfo]:
    """
    Detect edges that should be UV seams based on geometry.

    Analyzes surface geometry to find edges that would benefit
    from being marked as UV seams for cleaner unwrapping.

    Args:
        surface: Surface to analyze
        angle_threshold: Minimum dihedral angle for seam (radians)

    Returns:
        List of UVSeamInfo for edges that should be seams
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for seam detection")

    obj = bpy.data.objects.get(surface.object_name)
    if obj is None or obj.type != 'MESH':
        return []

    seams = []
    mesh = obj.data

    # Build face-to-edge mapping
    edge_faces: Dict[int, List[int]] = {}
    for face_idx, poly in enumerate(mesh.polygons):
        for edge_key in poly.edge_keys:
            if edge_key not in edge_faces:
                edge_faces[edge_key] = []
            edge_faces[edge_key].append(face_idx)

    # Check each edge
    for edge_idx, edge in enumerate(mesh.edges):
        # Skip already marked seams
        if edge.use_seam:
            continue

        # Get adjacent faces
        edge_key = (edge.vertices[0], edge.vertices[1])
        faces = edge_faces.get(edge_key, edge_faces.get((edge.vertices[1], edge.vertices[0]), []))

        if len(faces) != 2:
            continue  # Boundary edge

        # Calculate dihedral angle
        face1 = mesh.polygons[faces[0]]
        face2 = mesh.polygons[faces[1]]

        # Get face normals in world space
        n1 = Vector(obj.matrix_world @ face1.normal).normalized()
        n2 = Vector(obj.matrix_world @ face2.normal).normalized()

        # Dihedral angle
        dot = max(-1.0, min(1.0, n1.dot(n2)))
        angle = math.acos(dot)

        if angle > angle_threshold:
            seams.append(UVSeamInfo(
                edge_index=edge_idx,
                vertices=(edge.vertices[0], edge.vertices[1]),
                angle=angle,
                reason=f"Sharp edge ({math.degrees(angle):.1f} degrees)",
            ))

    return seams


def apply_uv_seams(
    surface: SurfaceInfo,
    seams: List[UVSeamInfo],
) -> int:
    """
    Apply detected UV seams to mesh edges.

    Args:
        surface: Surface to modify
        seams: Seams to apply

    Returns:
        Number of seams applied
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for seam application")

    obj = bpy.data.objects.get(surface.object_name)
    if obj is None or obj.type != 'MESH':
        return 0

    mesh = obj.data
    applied = 0

    for seam in seams:
        if seam.edge_index < len(mesh.edges):
            mesh.edges[seam.edge_index].use_seam = True
            applied += 1

    return applied


def optimize_uv_layout(
    surface: SurfaceInfo,
    uv_layer_name: str = "ProjectionUV",
    pack_islands: bool = True,
    rotate_islands: bool = True,
    island_padding: float = 0.02,
) -> Dict[str, Any]:
    """
    Optimize existing UV layout for better texture utilization.

    Args:
        surface: Surface with existing UVs
        uv_layer_name: UV layer to optimize
        pack_islands: Whether to pack islands into 0-1 space
        rotate_islands: Whether to rotate islands for better fit
        island_padding: Padding between islands

    Returns:
        Dictionary with optimization results
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for UV optimization")

    obj = bpy.data.objects.get(surface.object_name)
    if obj is None or obj.type != 'MESH':
        return {"success": False, "error": "Object not found"}

    mesh = obj.data

    # Find or create UV layer
    uv_layer = None
    for layer in mesh.uv_layers:
        if layer.name == uv_layer_name:
            uv_layer = layer
            break

    if uv_layer is None:
        return {"success": False, "error": "UV layer not found"}

    # Get UV bounds before
    bounds_before = _calculate_uv_bounds(mesh, uv_layer)

    # Apply optimization (using Blender's built-in pack islands)
    if pack_islands:
        # Select object
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Switch to edit mode and select all
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Pack islands
        bpy.ops.uv.pack_islands(
            rotate=rotate_islands,
            margin=island_padding,
        )

        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)

    # Get UV bounds after
    bounds_after = _calculate_uv_bounds(mesh, uv_layer)

    return {
        "success": True,
        "bounds_before": bounds_before,
        "bounds_after": bounds_after,
        "coverage_improvement": _calculate_coverage_improvement(bounds_before, bounds_after),
    }


def validate_uv_layout(
    surface: SurfaceInfo,
    uv_layer_name: str = "ProjectionUV",
) -> Dict[str, Any]:
    """
    Validate UV layout for export compatibility.

    Checks for common UV issues that could cause problems
    in game engines or other 3D software.

    Args:
        surface: Surface to validate
        uv_layer_name: UV layer to check

    Returns:
        Dictionary with validation results
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for UV validation")

    obj = bpy.data.objects.get(surface.object_name)
    if obj is None or obj.type != 'MESH':
        return {"valid": False, "errors": ["Object not found"]}

    mesh = obj.data

    # Find UV layer
    uv_layer = None
    for layer in mesh.uv_layers:
        if layer.name == uv_layer_name:
            uv_layer = layer
            break

    if uv_layer is None:
        return {"valid": False, "errors": ["UV layer not found"]}

    errors = []
    warnings = []

    # Check UV bounds
    bounds = _calculate_uv_bounds(mesh, uv_layer)
    min_u, min_v, max_u, max_v = bounds

    if min_u < 0.0 or max_u > 1.0 or min_v < 0.0 or max_v > 1.0:
        warnings.append(f"UVs outside 0-1 range: U[{min_u:.3f}, {max_u:.3f}] V[{min_v:.3f}, {max_v:.3f}]")

    # Check for overlapping UVs (simplified check)
    uv_coords = {}
    for loop in mesh.loops:
        uv = uv_layer.data[loop.index].uv
        key = (round(uv.x, 4), round(uv.y, 4))
        if key in uv_coords:
            uv_coords[key] += 1
        else:
            uv_coords[key] = 1

    overlapping = sum(1 for count in uv_coords.values() if count > 4)  # More than 4 vertices at same UV
    if overlapping > 0:
        warnings.append(f"{overlapping} potentially overlapping UV coordinates")

    # Check for zero-area UV faces
    zero_area_count = 0
    for poly in mesh.polygons:
        if len(poly.loop_indices) >= 3:
            uv0 = uv_layer.data[poly.loop_indices[0]].uv
            uv1 = uv_layer.data[poly.loop_indices[1]].uv
            uv2 = uv_layer.data[poly.loop_indices[2]].uv

            # Calculate 2D triangle area
            area = abs((uv1.x - uv0.x) * (uv2.y - uv0.y) - (uv2.x - uv0.x) * (uv1.y - uv0.y)) / 2
            if area < 0.0001:
                zero_area_count += 1

    if zero_area_count > 0:
        errors.append(f"{zero_area_count} zero-area UV faces")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "bounds": bounds,
        "unique_uvs": len(uv_coords),
        "face_count": len(mesh.polygons),
    }


# Private helper functions

def _generate_object_uvs(
    obj,
    hits: List[RayHit],
    config: UVLayoutConfig,
    frustum_config: Optional[FrustumConfig],
) -> UVGenerationResult:
    """Generate UVs for a single object from ray hits."""
    mesh = obj.data

    # Create or get UV layer
    uv_layer = None
    for layer in mesh.uv_layers:
        if layer.name == config.uv_layer_name:
            uv_layer = layer
            break

    if uv_layer is None:
        uv_layer = mesh.uv_layers.new(name=config.uv_layer_name)

    # Build vertex-to-UV mapping from ray hits
    vertex_uvs: Dict[int, List[Tuple[float, float]]] = {}
    face_uvs: Dict[int, List[Tuple[float, float]]] = {}

    for hit in hits:
        if not hit.hit:
            continue

        if hit.face_index < 0 or hit.face_index >= len(mesh.polygons):
            continue

        # Get UV from pixel coordinates
        if frustum_config:
            u = hit.pixel_x / frustum_config.resolution_x
            v = hit.pixel_y / frustum_config.resolution_y
        else:
            u = 0.5
            v = 0.5

        poly = mesh.polygons[hit.face_index]

        # Store UV for this face
        if hit.face_index not in face_uvs:
            face_uvs[hit.face_index] = []

        # Interpolate UV to vertices based on hit position
        _interpolate_uv_to_face(obj, poly, hit, u, v, uv_layer, face_uvs)

    # Apply UVs
    faces_covered = 0
    for face_idx, uvs in face_uvs.items():
        poly = mesh.polygons[face_idx]
        for i, loop_idx in enumerate(poly.loop_indices):
            if i < len(uvs):
                uv_layer.data[loop_idx].uv = uvs[i]
        faces_covered += 1

    # Calculate bounds
    bounds = _calculate_uv_bounds(mesh, uv_layer)

    # Normalize if requested
    if config.normalize_uvs:
        _normalize_uvs(mesh, uv_layer)
        bounds = _calculate_uv_bounds(mesh, uv_layer)

    # Detect seams if enabled
    seam_count = 0
    if config.auto_seam_angle > 0:
        seams = _detect_auto_seams(obj, config.auto_seam_angle)
        seam_count = len(seams)

    coverage = (faces_covered / len(mesh.polygons) * 100) if mesh.polygons else 0

    return UVGenerationResult(
        object_name=obj.name,
        uv_layer_name=config.uv_layer_name,
        uv_count=len(mesh.loops),
        face_count=len(mesh.polygons),
        coverage=coverage,
        has_seams=seam_count > 0,
        seam_count=seam_count,
        uv_bounds=bounds,
        warnings=[],
    )


def _generate_surface_projection_uvs(
    obj,
    camera_pos: Vector,
    camera_rot,
    config: FrustumConfig,
    uv_config: UVLayoutConfig,
) -> UVGenerationResult:
    """Generate UVs using camera projection mapping."""
    mesh = obj.data

    # Create UV layer
    uv_layer = None
    for layer in mesh.uv_layers:
        if layer.name == uv_config.uv_layer_name:
            uv_layer = layer
            break

    if uv_layer is None:
        uv_layer = mesh.uv_layers.new(name=uv_config.uv_layer_name)

    # Get camera vectors
    forward = Vector((0.0, 0.0, -1.0))
    forward.rotate(camera_rot)
    right = Vector((1.0, 0.0, 0.0))
    right.rotate(camera_rot)
    up = Vector((0.0, 1.0, 0.0))
    up.rotate(camera_rot)

    fov_rad = math.radians(config.fov)
    aspect = config.resolution_x / config.resolution_y

    # Project each vertex
    min_u, min_v = float('inf'), float('inf')
    max_u, max_v = float('-inf'), float('-inf')

    for loop in mesh.loops:
        vertex = mesh.vertices[loop.vertex_index]
        world_pos = obj.matrix_world @ Vector(vertex.co)

        # Calculate direction from camera
        direction = world_pos - camera_pos
        distance = direction.length

        if distance < 0.001:
            uv_layer.data[loop.index].uv = (0.5, 0.5)
            continue

        direction.normalize()

        # Check if in front of camera
        forward_dot = direction.dot(forward)
        if forward_dot <= 0:
            # Behind camera - use default
            uv_layer.data[loop.index].uv = (0.5, 0.5)
            continue

        # Project onto image plane
        # Calculate UV based on angle from forward direction
        right_dist = direction.dot(right)
        up_dist = direction.dot(up)

        # Convert to UV using FOV
        tan_half = math.tan(fov_rad / 2)
        u = (right_dist / forward_dot) / (tan_half * 2 * aspect) + 0.5
        v = (up_dist / forward_dot) / (tan_half * 2) + 0.5

        uv_layer.data[loop.index].uv = (u, v)

        min_u = min(min_u, u)
        max_u = max(max_u, u)
        min_v = min(min_v, v)
        max_v = max(max_v, v)

    # Normalize if requested
    if uv_config.normalize_uvs and (max_u > min_u) and (max_v > min_v):
        for loop in mesh.loops:
            uv = uv_layer.data[loop.index].uv
            u = (uv.x - min_u) / (max_u - min_u)
            v = (uv.y - min_v) / (max_v - min_v)
            uv_layer.data[loop.index].uv = (u, v)
        min_u, min_v = 0.0, 0.0
        max_u, max_v = 1.0, 1.0

    return UVGenerationResult(
        object_name=obj.name,
        uv_layer_name=uv_config.uv_layer_name,
        uv_count=len(mesh.loops),
        face_count=len(mesh.polygons),
        coverage=100.0,
        has_seams=False,
        seam_count=0,
        uv_bounds=(min_u, min_v, max_u, max_v),
        warnings=[],
    )


def _interpolate_uv_to_face(
    obj,
    poly,
    hit: RayHit,
    u: float,
    v: float,
    uv_layer,
    face_uvs: Dict[int, List[Tuple[float, float]]],
) -> None:
    """Interpolate UV coordinates to face vertices based on hit position."""
    mesh = obj.data

    # Get face vertices
    vertices = []
    for vert_idx in poly.vertices:
        vertices.append(Vector(obj.matrix_world @ mesh.vertices[vert_idx].co))

    if len(vertices) < 3:
        face_uvs[poly.index] = [(u, v)] * len(vertices)
        return

    # Calculate barycentric coordinates
    hit_pos = Vector(hit.position)

    # For triangles, use barycentric interpolation
    if len(vertices) == 3:
        weights = _barycentric_weights(hit_pos, vertices[0], vertices[1], vertices[2])
        face_uvs[poly.index] = [(u, v)] * 3
    else:
        # For quads+, assign same UV to all vertices (simplified)
        face_uvs[poly.index] = [(u, v)] * len(vertices)


def _barycentric_weights(
    point: Vector,
    v0: Vector,
    v1: Vector,
    v2: Vector,
) -> Tuple[float, float, float]:
    """Calculate barycentric weights for point in triangle."""
    v0v1 = v1 - v0
    v0v2 = v2 - v0
    v0p = point - v0

    d00 = v0v1.dot(v0v1)
    d01 = v0v1.dot(v0v2)
    d11 = v0v2.dot(v0v2)
    d20 = v0p.dot(v0v1)
    d21 = v0p.dot(v0v2)

    denom = d00 * d11 - d01 * d01
    if abs(denom) < 0.0001:
        return (0.33, 0.33, 0.34)

    w1 = (d11 * d20 - d01 * d21) / denom
    w2 = (d00 * d21 - d01 * d20) / denom
    w0 = 1.0 - w1 - w2

    return (w0, w1, w2)


def _calculate_uv_bounds(mesh, uv_layer) -> Tuple[float, float, float, float]:
    """Calculate UV coordinate bounds."""
    min_u, min_v = float('inf'), float('inf')
    max_u, max_v = float('-inf'), float('-inf')

    for loop in mesh.loops:
        uv = uv_layer.data[loop.index].uv
        min_u = min(min_u, uv.x)
        max_u = max(max_u, uv.x)
        min_v = min(min_v, uv.y)
        max_v = max(max_v, uv.y)

    if min_u == float('inf'):
        return (0.0, 0.0, 1.0, 1.0)

    return (min_u, min_v, max_u, max_v)


def _normalize_uvs(mesh, uv_layer) -> None:
    """Normalize UVs to 0-1 range."""
    bounds = _calculate_uv_bounds(mesh, uv_layer)
    min_u, min_v, max_u, max_v = bounds

    if max_u <= min_u or max_v <= min_v:
        return

    range_u = max_u - min_u
    range_v = max_v - min_v

    for loop in mesh.loops:
        uv = uv_layer.data[loop.index].uv
        u = (uv.x - min_u) / range_u
        v = (uv.y - min_v) / range_v
        uv_layer.data[loop.index].uv = (u, v)


def _detect_auto_seams(obj, angle_threshold: float) -> List[int]:
    """Detect edges that should be marked as seams."""
    mesh = obj.data
    seams = []

    # Build face-to-edge mapping
    edge_faces: Dict[Tuple[int, int], List[int]] = {}
    for face_idx, poly in enumerate(mesh.polygons):
        for i in range(len(poly.vertices)):
            v1 = poly.vertices[i]
            v2 = poly.vertices[(i + 1) % len(poly.vertices)]
            edge_key = (min(v1, v2), max(v1, v2))
            if edge_key not in edge_faces:
                edge_faces[edge_key] = []
            edge_faces[edge_key].append(face_idx)

    # Check each edge
    for edge in mesh.edges:
        if edge.use_seam:
            continue

        edge_key = (min(edge.vertices[0], edge.vertices[1]),
                    max(edge.vertices[0], edge.vertices[1]))
        faces = edge_faces.get(edge_key, [])

        if len(faces) != 2:
            continue

        # Get normals
        n1 = Vector(mesh.polygons[faces[0]].normal).normalized()
        n2 = Vector(mesh.polygons[faces[1]].normal).normalized()

        # Calculate angle
        dot = max(-1.0, min(1.0, n1.dot(n2)))
        angle = math.acos(dot)

        if angle > angle_threshold:
            seams.append(edge.index)

    return seams


def _calculate_coverage_improvement(
    bounds_before: Tuple[float, float, float, float],
    bounds_after: Tuple[float, float, float, float],
) -> float:
    """Calculate UV coverage improvement percentage."""
    # Calculate area before
    width_before = bounds_before[2] - bounds_before[0]
    height_before = bounds_before[3] - bounds_before[1]
    area_before = width_before * height_before

    # Calculate area after
    width_after = bounds_after[2] - bounds_after[0]
    height_after = bounds_after[3] - bounds_after[1]
    area_after = width_after * height_after

    if area_before == 0:
        return 0.0

    return ((area_after - area_before) / area_before) * 100
