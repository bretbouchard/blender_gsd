"""
3-Point alignment algorithm for planar surface calibration.

Adapted from Compify's camera_align.py technique for physical projector mapping.
Computes transform from 3 track points to 3 scene points using orthonormal bases.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Use pure Python/math for alignment math (no Blender dependency for core algorithm)
# mathutils is Blender-specific, so we implement our own Vector/Matrix operations


@dataclass
class Vector3:
    """Simple 3D vector for alignment calculations."""
    x: float
    y: float
    z: float

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> 'Vector3':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> 'Vector3':
        return Vector3(-self.x, -self.y, -self.z)

    def dot(self, other: 'Vector3') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        """Cross product."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def length(self) -> float:
        """Vector magnitude."""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self) -> 'Vector3':
        """Return normalized vector."""
        length = self.length()
        if length < 1e-10:
            return Vector3(0, 0, 0)
        return self / length

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)

    @staticmethod
    def from_tuple(t: Tuple[float, float, float]) -> 'Vector3':
        """Create from tuple."""
        return Vector3(t[0], t[1], t[2])


@dataclass
class Matrix3x3:
    """Simple 3x3 matrix for rotation calculations."""
    data: List[List[float]]  # 3x3 list of lists

    def __init__(self, data: Optional[List[List[float]]] = None):
        if data is None:
            self.data = [[0.0] * 3 for _ in range(3)]
        else:
            self.data = data

    @staticmethod
    def identity() -> 'Matrix3x3':
        """Create identity matrix."""
        return Matrix3x3([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])

    @staticmethod
    def from_columns(col0: Vector3, col1: Vector3, col2: Vector3) -> 'Matrix3x3':
        """Create matrix from column vectors."""
        return Matrix3x3([
            [col0.x, col1.x, col2.x],
            [col0.y, col1.y, col2.y],
            [col0.z, col1.z, col2.z]
        ])

    def __mul__(self, other: 'Matrix3x3') -> 'Matrix3x3':
        """Matrix multiplication."""
        result = Matrix3x3()
        for i in range(3):
            for j in range(3):
                result.data[i][j] = sum(
                    self.data[i][k] * other.data[k][j] for k in range(3)
                )
        return result

    def transpose(self) -> 'Matrix3x3':
        """Transpose matrix."""
        return Matrix3x3([
            [self.data[j][i] for j in range(3)]
            for i in range(3)
        ])

    def transform_vector(self, v: Vector3) -> Vector3:
        """Transform vector by matrix."""
        return Vector3(
            sum(self.data[i][0] * v.x + self.data[i][1] * v.y + self.data[i][2] * v.z for i in range(0, 1)),
            sum(self.data[i][0] * v.x + self.data[i][1] * v.y + self.data[i][2] * v.z for i in range(1, 2)),
            self.data[2][0] * v.x + self.data[2][1] * v.y + self.data[2][2] * v.z
        )

    def to_4x4(self) -> 'Matrix4x4':
        """Convert to 4x4 matrix."""
        return Matrix4x4([
            [self.data[0][0], self.data[0][1], self.data[0][2], 0.0],
            [self.data[1][0], self.data[1][1], self.data[1][2], 0.0],
            [self.data[2][0], self.data[2][1], self.data[2][2], 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])


@dataclass
class Matrix4x4:
    """Simple 4x4 matrix for transform calculations."""
    data: List[List[float]]  # 4x4 list of lists

    def __init__(self, data: Optional[List[List[float]]] = None):
        if data is None:
            self.data = [[0.0] * 4 for _ in range(4)]
        else:
            self.data = data

    @staticmethod
    def identity() -> 'Matrix4x4':
        """Create identity matrix."""
        return Matrix4x4([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def translation(v: Vector3) -> 'Matrix4x4':
        """Create translation matrix."""
        return Matrix4x4([
            [1.0, 0.0, 0.0, v.x],
            [0.0, 1.0, 0.0, v.y],
            [0.0, 0.0, 1.0, v.z],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @staticmethod
    def scale(s: float) -> 'Matrix4x4':
        """Create uniform scale matrix."""
        return Matrix4x4([
            [s, 0.0, 0.0, 0.0],
            [0.0, s, 0.0, 0.0],
            [0.0, 0.0, s, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    def __mul__(self, other: 'Matrix4x4') -> 'Matrix4x4':
        """Matrix multiplication."""
        result = Matrix4x4()
        for i in range(4):
            for j in range(4):
                result.data[i][j] = sum(
                    self.data[i][k] * other.data[k][j] for k in range(4)
                )
        return result

    def transform_point(self, v: Vector3) -> Vector3:
        """Transform 3D point by matrix (with translation)."""
        x = self.data[0][0] * v.x + self.data[0][1] * v.y + self.data[0][2] * v.z + self.data[0][3]
        y = self.data[1][0] * v.x + self.data[1][1] * v.y + self.data[1][2] * v.z + self.data[1][3]
        z = self.data[2][0] * v.x + self.data[2][1] * v.y + self.data[2][2] * v.z + self.data[2][3]
        w = self.data[3][0] * v.x + self.data[3][1] * v.y + self.data[3][2] * v.z + self.data[3][3]

        if abs(w) > 1e-10:
            return Vector3(x / w, y / w, z / w)
        return Vector3(x, y, z)

    def to_list(self) -> List[List[float]]:
        """Convert to list of lists."""
        return [row[:] for row in self.data]


@dataclass
class AlignmentResult:
    """Result of alignment computation."""
    transform: Matrix4x4          # 4x4 transform matrix
    scale: float                  # Computed scale factor
    rotation: Matrix3x3           # Computed rotation matrix
    translation: Vector3          # Computed translation vector
    error: float                  # RMS alignment error in world units
    error_normalized: float       # RMS error as fraction of surface size


def build_orthonormal_basis(p1: Vector3, p2: Vector3, p3: Vector3) -> Tuple[Vector3, Vector3, Vector3, Vector3]:
    """
    Build orthonormal basis from 3 points.

    Args:
        p1, p2, p3: Three non-collinear points

    Returns:
        (origin, x_axis, y_axis, z_axis) - Orthonormal basis vectors
    """
    # Origin at first point
    origin = p1

    # X-axis: p1 -> p2 direction
    x_axis = (p2 - p1).normalized()

    # Y-axis: perpendicular to x, in plane of p1, p2, p3
    v = p3 - p1
    # Project v onto plane perpendicular to x_axis
    y_temp = v - x_axis * v.dot(x_axis)
    y_axis = y_temp.normalized()

    # Z-axis: perpendicular to x and y (right-hand rule)
    z_axis = x_axis.cross(y_axis).normalized()

    return origin, x_axis, y_axis, z_axis


def are_collinear(p1: Vector3, p2: Vector3, p3: Vector3, tolerance: float = 1e-6) -> bool:
    """
    Check if three points are collinear.

    Args:
        p1, p2, p3: Three points
        tolerance: Maximum cross product magnitude for collinearity

    Returns:
        True if points are collinear (degenerate)
    """
    v1 = p2 - p1
    v2 = p3 - p1
    cross = v1.cross(v2)
    return cross.length() < tolerance


def _to_vector3(p, z_default: float = 0.0) -> Vector3:
    """Convert point to Vector3, handling Vector3, tuple, or list inputs."""
    if isinstance(p, Vector3):
        return p
    elif hasattr(p, '__len__'):
        if len(p) == 3:
            return Vector3(p[0], p[1], p[2])
        elif len(p) == 2:
            return Vector3(p[0], p[1], z_default)
    raise ValueError(f"Cannot convert {type(p)} to Vector3")


def compute_alignment_transform(
    projector_points: List,
    world_points: List
) -> AlignmentResult:
    """
    Compute transform from projector space to world space using 3-point alignment.

    This algorithm:
    1. Builds orthonormal bases from both point sets
    2. Computes rotation from basis alignment
    3. Computes scale from average distances
    4. Computes translation from origin offset

    Args:
        projector_points: 3 points in projector UV space (0-1 range).
                         Can be Vector3, tuples (x, y), or tuples (x, y, z).
        world_points: 3 corresponding points in world space (meters).
                     Can be Vector3 or tuples (x, y, z).

    Returns:
        AlignmentResult with transform matrix and error metrics

    Raises:
        ValueError: If not exactly 3 points provided or points are collinear
    """
    if len(projector_points) != 3 or len(world_points) != 3:
        raise ValueError("Exactly 3 points required for 3-point alignment")

    # Convert to Vector3 (projector points get Z=0 since they're 2D UV)
    proj_pts = [
        _to_vector3(p, z_default=0.0)
        for p in projector_points
    ]
    world_pts = [
        _to_vector3(p, z_default=0.0)
        for p in world_points
    ]

    # Check for collinear points
    if are_collinear(proj_pts[0], proj_pts[1], proj_pts[2]):
        raise ValueError("Projector points are collinear (degenerate configuration)")
    if are_collinear(world_pts[0], world_pts[1], world_pts[2]):
        raise ValueError("World points are collinear (degenerate configuration)")

    # Build orthonormal bases
    proj_origin, proj_x, proj_y, proj_z = build_orthonormal_basis(
        proj_pts[0], proj_pts[1], proj_pts[2]
    )
    world_origin, world_x, world_y, world_z = build_orthonormal_basis(
        world_pts[0], world_pts[1], world_pts[2]
    )

    # Build rotation matrices from bases
    # Each basis matrix transforms from that basis to identity
    proj_basis = Matrix3x3.from_columns(proj_x, proj_y, proj_z)
    world_basis = Matrix3x3.from_columns(world_x, world_y, world_z)

    # Rotation: transforms from projector basis to world basis
    # R = world_basis @ proj_basis.transpose()
    proj_basis_t = proj_basis.transpose()
    rotation = world_basis * proj_basis_t

    # Compute scale from average distances between points
    proj_distances = [
        (proj_pts[1] - proj_pts[0]).length(),
        (proj_pts[2] - proj_pts[0]).length(),
        (proj_pts[2] - proj_pts[1]).length(),
    ]
    world_distances = [
        (world_pts[1] - world_pts[0]).length(),
        (world_pts[2] - world_pts[0]).length(),
        (world_pts[2] - world_pts[1]).length(),
    ]

    # Avoid division by zero
    proj_total = sum(proj_distances)
    if proj_total < 1e-10:
        raise ValueError("Projector points are too close together")

    scale = sum(world_distances) / proj_total

    # Compute translation
    # Transform projector origin to world space and find offset
    # t = world_origin - scale * (rotation @ proj_origin)
    rotated_proj_origin = rotation.transform_vector(proj_origin)
    translation = world_origin - rotated_proj_origin * scale

    # Build 4x4 transform matrix: T * S * R
    # Order: first scale, then rotate, then translate
    scale_matrix = Matrix4x4.scale(scale)
    rotation_4x4 = rotation.to_4x4()
    translation_matrix = Matrix4x4.translation(translation)

    # Transform = Translation * (Scale * Rotation)
    transform = translation_matrix * (scale_matrix * rotation_4x4)

    # Compute alignment error
    error, error_normalized = compute_alignment_error(
        proj_pts, world_pts, transform, scale
    )

    return AlignmentResult(
        transform=transform,
        scale=scale,
        rotation=rotation,
        translation=translation,
        error=error,
        error_normalized=error_normalized
    )


def compute_alignment_error(
    projector_points: List[Vector3],
    world_points: List[Vector3],
    transform: Matrix4x4,
    scale: float
) -> Tuple[float, float]:
    """
    Compute RMS alignment error.

    Args:
        projector_points: Points in projector space
        world_points: Corresponding points in world space
        transform: Computed transform matrix
        scale: Computed scale factor

    Returns:
        (absolute_error, normalized_error) in meters and as fraction
    """
    errors = []

    for proj_pt, world_pt in zip(projector_points, world_points):
        # Transform projector point to world space
        transformed = transform.transform_point(proj_pt)

        # Compute distance error
        error = (transformed - world_pt).length()
        errors.append(error)

    # RMS error
    rms_error = math.sqrt(sum(e ** 2 for e in errors) / len(errors))

    # Normalized error (as fraction of scale)
    normalized_error = rms_error / scale if scale > 1e-10 else rms_error

    return rms_error, normalized_error


def align_surface(
    projector_points: List[Tuple[float, float]],
    world_points: List[Tuple[float, float, float]]
) -> AlignmentResult:
    """
    Main entry point for 3-point surface alignment.

    Convenience wrapper around compute_alignment_transform.

    Args:
        projector_points: 3 points in projector UV space (0-1 range)
        world_points: 3 corresponding points in world space (meters)

    Returns:
        AlignmentResult ready to apply to projector camera
    """
    return compute_alignment_transform(projector_points, world_points)
