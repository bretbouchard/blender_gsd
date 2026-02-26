"""
Tests for projection shader system.
"""

import pytest
from dataclasses import asdict

from lib.cinematic.projection.physical.shaders.types import (
    ProjectionMode,
    BlendMode,
    TextureFilter,
    TextureExtension,
    ProjectionShaderConfig,
    ProjectionShaderResult,
    ProxyGeometryConfig,
    ProxyGeometryResult,
)
from lib.cinematic.projection.physical.shaders.proxy_geometry import (
    create_planar_proxy_vertices,
    compute_uv_for_calibration_points,
    subdivide_quad,
    subdivide_uv,
    create_proxy_geometry_for_surface,
)


class TestProjectionMode:
    """Tests for ProjectionMode enum."""

    def test_mode_values(self):
        """Test enum values."""
        assert ProjectionMode.CAMERA.value == "camera"
        assert ProjectionMode.UV.value == "uv"
        assert ProjectionMode.TRIPLANAR.value == "triplanar"

    def test_all_modes_defined(self):
        """Test all modes are defined."""
        modes = list(ProjectionMode)
        assert len(modes) == 3


class TestBlendMode:
    """Tests for BlendMode enum."""

    def test_blend_values(self):
        """Test blend mode values."""
        assert BlendMode.MIX.value == "mix"
        assert BlendMode.ADD.value == "add"
        assert BlendMode.MULTIPLY.value == "multiply"
        assert BlendMode.OVERLAY.value == "overlay"
        assert BlendMode.SCREEN.value == "screen"


class TestProjectionShaderConfig:
    """Tests for ProjectionShaderConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ProjectionShaderConfig()

        assert config.throw_ratio == 1.0
        assert config.sensor_width == 36.0
        assert config.resolution_x == 1920
        assert config.resolution_y == 1080
        assert config.shift_x == 0.0
        assert config.shift_y == 0.0
        assert config.mode == ProjectionMode.CAMERA
        assert config.blend_mode == BlendMode.MIX
        assert config.intensity == 1.0
        assert config.content_image is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ProjectionShaderConfig(
            throw_ratio=1.5,
            resolution_x=3840,
            resolution_y=2160,
            shift_x=0.1,
            shift_y=-0.05,
            mode=ProjectionMode.UV,
            blend_mode=BlendMode.ADD,
            intensity=0.8,
        )

        assert config.throw_ratio == 1.5
        assert config.resolution_x == 3840
        assert config.resolution_y == 2160
        assert config.shift_x == 0.1
        assert config.shift_y == -0.05
        assert config.mode == ProjectionMode.UV
        assert config.blend_mode == BlendMode.ADD
        assert config.intensity == 0.8

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = ProjectionShaderConfig(throw_ratio=2.0)
        data = config.to_dict()

        assert data["throw_ratio"] == 2.0
        assert data["resolution_x"] == 1920
        assert data["mode"] == "camera"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "throw_ratio": 1.8,
            "resolution_x": 1920,
            "resolution_y": 1080,
            "mode": "uv",
            "blend_mode": "overlay",
        }
        config = ProjectionShaderConfig.from_dict(data)

        assert config.throw_ratio == 1.8
        assert config.mode == ProjectionMode.UV
        assert config.blend_mode == BlendMode.OVERLAY

    def test_round_trip(self):
        """Test serialization round trip."""
        original = ProjectionShaderConfig(
            throw_ratio=1.2,
            shift_x=0.15,
            mode=ProjectionMode.TRIPLANAR,
        )
        data = original.to_dict()
        restored = ProjectionShaderConfig.from_dict(data)

        assert restored.throw_ratio == original.throw_ratio
        assert restored.shift_x == original.shift_x
        assert restored.mode == original.mode


class TestProxyGeometryConfig:
    """Tests for ProxyGeometryConfig."""

    def test_default_config(self):
        """Test default proxy geometry config."""
        config = ProxyGeometryConfig()

        assert config.subdivisions == 2
        assert config.margin == 0.1
        assert config.optimize_uv is True
        assert config.smooth_shading is False

    def test_custom_config(self):
        """Test custom proxy geometry config."""
        config = ProxyGeometryConfig(
            subdivisions=4,
            margin=0.2,
            optimize_uv=False,
            smooth_shading=True,
        )

        assert config.subdivisions == 4
        assert config.margin == 0.2
        assert config.optimize_uv is False
        assert config.smooth_shading is True


class TestPlanarProxyVertices:
    """Tests for planar proxy vertex generation."""

    def test_create_quad_vertices(self):
        """Test creating quad vertices from 3 points."""
        # Simple rectangle in XY plane
        p1 = (0, 0, 0)   # Bottom-left
        p2 = (2, 0, 0)   # Bottom-right
        p3 = (0, 1, 0)   # Top-left

        vertices, faces = create_planar_proxy_vertices([p1, p2, p3])

        assert len(vertices) == 4
        assert len(faces) == 1
        assert faces[0] == (0, 1, 2, 3)

        # Check 4th vertex is computed correctly
        p4 = vertices[2]  # Top-right (index 2 in quad order)
        expected_p4 = (2, 1, 0)  # p1 + (p2-p1) + (p3-p1)
        assert p4 == expected_p4

    def test_3d_vertices(self):
        """Test creating vertices in 3D space."""
        p1 = (0, 0, 0)
        p2 = (1, 0, 1)
        p3 = (0, 1, 0)

        vertices, faces = create_planar_proxy_vertices([p1, p2, p3])

        assert len(vertices) == 4
        # 4th point should be p1 + v1 + v2
        # v1 = (1, 0, 1), v2 = (0, 1, 0)
        # p4 = (0+1+0, 0+0+1, 0+1+0) = (1, 1, 1)
        assert vertices[2] == (1, 1, 1)

    def test_requires_3_points(self):
        """Test that 3 points are required."""
        with pytest.raises(ValueError):
            create_planar_proxy_vertices([(0, 0, 0), (1, 0, 0)])

        with pytest.raises(ValueError):
            create_planar_proxy_vertices([
                (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)
            ])


class TestUVComputation:
    """Tests for UV coordinate computation."""

    def test_compute_uv_for_calibration(self):
        """Test UV computation from calibration points."""
        # Simple UV setup
        projector_uvs = [
            (0.0, 0.0),  # Bottom-left
            (1.0, 0.0),  # Bottom-right
            (0.0, 1.0),  # Top-left
        ]

        uvs = compute_uv_for_calibration_points(projector_uvs)

        assert len(uvs) == 4
        assert uvs[0] == (0.0, 0.0)  # BL
        assert uvs[1] == (1.0, 0.0)  # BR
        assert uvs[3] == (0.0, 1.0)  # TL
        assert uvs[2] == (1.0, 1.0)  # TR (computed)

    def test_partial_uv_range(self):
        """Test UV computation with partial projector range."""
        projector_uvs = [
            (0.2, 0.3),
            (0.8, 0.3),
            (0.2, 0.7),
        ]

        uvs = compute_uv_for_calibration_points(projector_uvs)

        assert uvs[0] == (0.2, 0.3)
        assert uvs[1] == (0.8, 0.3)
        assert uvs[3] == (0.2, 0.7)
        assert uvs[2] == (0.8, 0.7)  # Computed top-right

    def test_requires_3_uvs(self):
        """Test that 3 UVs are required."""
        with pytest.raises(ValueError):
            compute_uv_for_calibration_points([(0, 0), (1, 0)])

    def test_requires_3_uvs_too_many(self):
        """Test that exactly 3 UVs are required."""
        with pytest.raises(ValueError):
            compute_uv_for_calibration_points([
                (0, 0), (1, 0), (0, 1), (1, 1)
            ])


class TestSubdivision:
    """Tests for geometry subdivision."""

    def test_no_subdivision(self):
        """Test zero subdivisions returns original geometry."""
        vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]

        new_verts, new_faces = subdivide_quad(vertices, faces, 0)

        assert len(new_verts) == 4
        assert len(new_faces) == 1

    def test_one_subdivision(self):
        """Test single subdivision creates 4 quads."""
        vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]

        new_verts, new_faces = subdivide_quad(vertices, faces, 1)

        # 1 quad -> 4 quads with 9 vertices (3x3 grid)
        assert len(new_verts) == 9
        assert len(new_faces) == 4

    def test_two_subdivisions(self):
        """Test double subdivision creates 16 quads."""
        vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [(0, 1, 2, 3)]

        new_verts, new_faces = subdivide_quad(vertices, faces, 2)

        # 1 quad -> 4 -> 16 quads with 25 vertices (5x5 grid)
        assert len(new_verts) == 25
        assert len(new_faces) == 16


class TestUVSubdivision:
    """Tests for UV subdivision."""

    def test_no_subdivision_uv(self):
        """Test zero subdivisions returns original UVs."""
        uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

        new_uvs = subdivide_uv(uvs, 0)

        assert len(new_uvs) == 4

    def test_one_subdivision_uv(self):
        """Test single subdivision creates 9 UVs."""
        uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

        new_uvs = subdivide_uv(uvs, 1)

        # 2x2 grid + 1 = 9 UVs
        assert len(new_uvs) == 9

    def test_subdivision_values(self):
        """Test UV values are correct after subdivision."""
        uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

        new_uvs = subdivide_uv(uvs, 1)

        # Check corner UVs are preserved
        assert (0.0, 0.0) in new_uvs  # Bottom-left
        assert (1.0, 0.0) in new_uvs  # Bottom-right
        assert (1.0, 1.0) in new_uvs  # Top-right
        assert (0.0, 1.0) in new_uvs  # Top-left

        # Check center
        assert (0.5, 0.5) in new_uvs


class TestProxyGeometryCreation:
    """Tests for proxy geometry creation."""

    def test_create_planar_proxy(self):
        """Test creating planar proxy geometry."""
        calibration_points = [
            (0, 0, 0),
            (2, 0, 0),
            (0, 1, 0),
        ]
        projector_uvs = [
            (0.0, 0.0),
            (1.0, 0.0),
            (0.0, 1.0),
        ]

        result = create_proxy_geometry_for_surface(
            calibration_points,
            projector_uvs,
            ProxyGeometryConfig(subdivisions=0)
        )

        assert result.success
        assert result.vertex_count == 4
        assert result.face_count == 1
        assert result.uv_bounds == (0.0, 1.0, 0.0, 1.0)

    def test_create_proxy_with_subdivision(self):
        """Test creating proxy with subdivisions."""
        calibration_points = [
            (0, 0, 0),
            (2, 0, 0),
            (0, 1, 0),
        ]
        projector_uvs = [
            (0.0, 0.0),
            (1.0, 0.0),
            (0.0, 1.0),
        ]

        result = create_proxy_geometry_for_surface(
            calibration_points,
            projector_uvs,
            ProxyGeometryConfig(subdivisions=1)
        )

        assert result.success
        assert result.vertex_count == 9  # 3x3 grid
        assert result.face_count == 4   # 4 quads

    def test_invalid_point_count(self):
        """Test error handling for wrong point count."""
        result = create_proxy_geometry_for_surface(
            [(0, 0, 0), (1, 0, 0)],  # Only 2 points
            [(0, 0), (1, 0), (0, 1)],
        )

        assert not result.success
        assert len(result.errors) > 0
