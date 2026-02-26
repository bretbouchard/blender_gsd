"""
Tests for 3-point alignment algorithm.
"""

import pytest
from lib.cinematic.projection.physical.calibration.alignment import (
    Vector3,
    Matrix3x3,
    Matrix4x4,
    build_orthonormal_basis,
    compute_alignment_transform,
    are_collinear,
    AlignmentResult,
)


class TestVector3:
    """Tests for Vector3 class."""

    def test_vector_creation(self):
        """Test creating vectors."""
        v = Vector3(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_vector_addition(self):
        """Test vector addition."""
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)
        result = v1 + v2
        assert result.x == 5
        assert result.y == 7
        assert result.z == 9

    def test_vector_subtraction(self):
        """Test vector subtraction."""
        v1 = Vector3(4, 5, 6)
        v2 = Vector3(1, 2, 3)
        result = v1 - v2
        assert result.x == 3
        assert result.y == 3
        assert result.z == 3

    def test_vector_dot_product(self):
        """Test dot product."""
        v1 = Vector3(1, 0, 0)
        v2 = Vector3(0, 1, 0)
        assert v1.dot(v2) == 0

        v3 = Vector3(1, 2, 3)
        v4 = Vector3(1, 2, 3)
        assert v3.dot(v4) == 14  # 1+4+9

    def test_vector_cross_product(self):
        """Test cross product."""
        v1 = Vector3(1, 0, 0)
        v2 = Vector3(0, 1, 0)
        result = v1.cross(v2)
        assert result.x == 0
        assert result.y == 0
        assert result.z == 1

    def test_vector_length(self):
        """Test vector length."""
        v = Vector3(3, 4, 0)
        assert v.length() == 5.0

    def test_vector_normalized(self):
        """Test vector normalization."""
        v = Vector3(3, 4, 0)
        n = v.normalized()
        assert abs(n.x - 0.6) < 1e-10
        assert abs(n.y - 0.8) < 1e-10
        assert n.z == 0


class TestBuildOrthonormalBasis:
    """Tests for build_orthonormal_basis function."""

    def test_build_orthonormal_basis_unit_vectors(self):
        """Test building orthonormal basis from unit vectors."""
        p1 = Vector3(0, 0, 0)
        p2 = Vector3(1, 0, 0)
        p3 = Vector3(0, 1, 0)

        origin, x_axis, y_axis, z_axis = build_orthonormal_basis(p1, p2, p3)

        # Check origin
        assert origin.x == 0
        assert origin.y == 0
        assert origin.z == 0

        # Check axes are unit length
        assert abs(x_axis.length() - 1.0) < 1e-10
        assert abs(y_axis.length() - 1.0) < 1e-10
        assert abs(z_axis.length() - 1.0) < 1e-10

        # Check orthogonality
        assert abs(x_axis.dot(y_axis)) < 1e-10
        assert abs(x_axis.dot(z_axis)) < 1e-10
        assert abs(y_axis.dot(z_axis)) < 1e-10

    def test_build_orthonormal_basis_scaled(self):
        """Test building basis from scaled points."""
        p1 = Vector3(0, 0, 0)
        p2 = Vector3(2, 0, 0)
        p3 = Vector3(0, 3, 0)

        origin, x_axis, y_axis, z_axis = build_orthonormal_basis(p1, p2, p3)

        # Axes should still be normalized
        assert abs(x_axis.length() - 1.0) < 1e-10
        assert abs(y_axis.length() - 1.0) < 1e-10


class TestAreCollinear:
    """Tests for are_collinear function."""

    def test_not_collinear(self):
        """Test that non-collinear points return False."""
        p1 = Vector3(0, 0, 0)
        p2 = Vector3(1, 0, 0)
        p3 = Vector3(0, 1, 0)

        assert not are_collinear(p1, p2, p3)

    def test_collinear_x_axis(self):
        """Test that collinear points on X-axis return True."""
        p1 = Vector3(0, 0, 0)
        p2 = Vector3(1, 0, 0)
        p3 = Vector3(2, 0, 0)

        assert are_collinear(p1, p2, p3)

    def test_collinear_y_axis(self):
        """Test that collinear points on Y-axis return True."""
        p1 = Vector3(0, 0, 0)
        p2 = Vector3(0, 1, 0)
        p3 = Vector3(0, 2, 0)

        assert are_collinear(p1, p2, p3)


class TestComputeAlignmentTransform:
    """Tests for compute_alignment_transform function."""

    def test_identity_transform(self):
        """Test that identical points produce identity-like transform."""
        projector_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(0, 1, 0),
        ]
        world_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(0, 1, 0),
        ]

        result = compute_alignment_transform(projector_pts, world_pts)

        # Check that error is zero for identical points
        assert result.error < 1e-10

        # Check translation is near zero
        assert abs(result.translation.x) < 1e-10
        assert abs(result.translation.y) < 1e-10
        assert abs(result.translation.z) < 1e-10

    def test_scaled_transform(self):
        """Test that scaled points produce correct scale."""
        projector_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(0, 1, 0),
        ]
        world_pts = [
            Vector3(0, 0, 0),
            Vector3(2, 0, 0),  # 2x scale in X
            Vector3(0, 2, 0),  # 2x scale in Y
        ]

        result = compute_alignment_transform(projector_pts, world_pts)

        # Scale should be approximately 2
        assert abs(result.scale - 2.0) < 1e-10

        # Error should be minimal
        assert result.error < 1e-10

    def test_translated_transform(self):
        """Test that translated points produce correct translation."""
        projector_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(0, 1, 0),
        ]
        world_pts = [
            Vector3(1, 2, 3),  # Translation offset
            Vector3(2, 2, 3),
            Vector3(1, 3, 3),
        ]

        result = compute_alignment_transform(projector_pts, world_pts)

        # Translation should match offset
        assert abs(result.translation.x - 1.0) < 1e-10
        assert abs(result.translation.y - 2.0) < 1e-10
        assert abs(result.translation.z - 3.0) < 1e-10

    def test_collinear_raises_error(self):
        """Test that collinear points raise ValueError."""
        projector_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(2, 0, 0),  # Collinear
        ]
        world_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(2, 0, 0),  # Collinear
        ]

        with pytest.raises(ValueError, match="collinear"):
            compute_alignment_transform(projector_pts, world_pts)

    def test_wrong_point_count_raises_error(self):
        """Test that wrong number of points raises ValueError."""
        projector_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
        ]
        world_pts = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
        ]

        with pytest.raises(ValueError, match="Exactly 3 points required"):
            compute_alignment_transform(projector_pts, world_pts)


class TestMatrix4x4:
    """Tests for Matrix4x4 class."""

    def test_identity_matrix(self):
        """Test identity matrix creation."""
        m = Matrix4x4.identity()
        assert m.data[0][0] == 1.0
        assert m.data[1][1] == 1.0
        assert m.data[2][2] == 1.0
        assert m.data[3][3] == 1.0

    def test_transform_point(self):
        """Test point transformation."""
        m = Matrix4x4.identity()
        v = Vector3(1, 2, 3)
        result = m.transform_point(v)
        assert result.x == 1
        assert result.y == 2
        assert result.z == 3

    def test_translation_matrix(self):
        """Test translation matrix."""
        m = Matrix4x4.translation(Vector3(1, 2, 3))
        v = Vector3(0, 0, 0)
        result = m.transform_point(v)
        assert result.x == 1
        assert result.y == 2
        assert result.z == 3
