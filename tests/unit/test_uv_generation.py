"""
UV Generation Module Unit Tests

Tests for: lib/cinematic/projection/uv_generation.py
Coverage target: 80%+

Part of Phase 9.2 - UV Generation (REQ-ANAM-03)
Beads: blender_gsd-36
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors

from lib.cinematic.projection.uv_generation import (
    UVGenerationResult,
    UVSeamInfo,
    UVLayoutConfig,
    generate_uvs_from_projection,
    generate_uvs_for_surface,
    detect_uv_seams,
    apply_uv_seams,
    optimize_uv_layout,
    validate_uv_layout,
)

from lib.cinematic.projection.types import (
    SurfaceType,
    SurfaceInfo,
    RayHit,
    FrustumConfig,
    ProjectionResult,
)


class TestUVLayoutConfig:
    """Unit tests for UVLayoutConfig dataclass."""

    def test_default_values(self):
        """Default config should have sensible values."""
        config = UVLayoutConfig()

        assert config.uv_layer_name == "ProjectionUV"
        compare_numbers(config.island_padding, 0.02, tolerance=0.001)
        assert config.pack_islands is True
        compare_numbers(config.auto_seam_angle, math.radians(30.0), tolerance=0.01)
        assert config.normalize_uvs is True

    def test_custom_values(self):
        """Custom values should be stored."""
        config = UVLayoutConfig(
            uv_layer_name="CustomUV",
            island_padding=0.05,
            pack_islands=False,
            normalize_uvs=False,
        )

        assert config.uv_layer_name == "CustomUV"
        compare_numbers(config.island_padding, 0.05)
        assert config.pack_islands is False
        assert config.normalize_uvs is False

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        config = UVLayoutConfig(
            uv_layer_name="TestUV",
            island_padding=0.03,
        )

        data = config.to_dict()

        assert data["uv_layer_name"] == "TestUV"
        assert data["island_padding"] == 0.03

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "uv_layer_name": "RestoredUV",
            "island_padding": 0.04,
            "pack_islands": False,
            "normalize_uvs": False,
        }

        config = UVLayoutConfig.from_dict(data)

        assert config.uv_layer_name == "RestoredUV"
        compare_numbers(config.island_padding, 0.04)
        assert config.pack_islands is False

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = UVLayoutConfig(
            uv_layer_name="RoundTrip",
            island_padding=0.07,
            auto_seam_angle=math.radians(45.0),
        )

        restored = UVLayoutConfig.from_dict(original.to_dict())

        assert restored.uv_layer_name == original.uv_layer_name
        compare_numbers(restored.island_padding, original.island_padding)
        compare_numbers(restored.auto_seam_angle, original.auto_seam_angle)


class TestUVGenerationResult:
    """Unit tests for UVGenerationResult dataclass."""

    def test_default_values(self):
        """Default result should have empty values."""
        result = UVGenerationResult()

        assert result.object_name == ""
        assert result.uv_layer_name == ""
        assert result.uv_count == 0
        assert result.face_count == 0
        assert result.coverage == 0.0
        assert result.has_seams is False
        assert result.seam_count == 0

    def test_result_with_values(self):
        """Result should store all generation data."""
        result = UVGenerationResult(
            object_name="Floor",
            uv_layer_name="ProjectionUV",
            uv_count=1000,
            face_count=500,
            coverage=85.5,
            has_seams=True,
            seam_count=42,
            uv_bounds=(0.0, 0.0, 1.0, 1.0),
            warnings=["Some faces not covered"],
        )

        assert result.object_name == "Floor"
        assert result.uv_count == 1000
        compare_numbers(result.coverage, 85.5)
        assert result.has_seams is True
        assert result.seam_count == 42
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        result = UVGenerationResult(
            object_name="Wall",
            uv_count=2000,
            coverage=100.0,
            uv_bounds=(0.1, 0.2, 0.9, 0.8),
        )

        data = result.to_dict()

        assert data["object_name"] == "Wall"
        assert data["uv_count"] == 2000
        assert data["coverage"] == 100.0
        assert data["uv_bounds"] == [0.1, 0.2, 0.9, 0.8]

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "object_name": "Ceiling",
            "uv_layer_name": "TestUV",
            "uv_count": 500,
            "face_count": 250,
            "coverage": 95.0,
            "has_seams": True,
            "seam_count": 10,
            "uv_bounds": [0.0, 0.0, 1.0, 1.0],
            "warnings": ["Warning 1"],
        }

        result = UVGenerationResult.from_dict(data)

        assert result.object_name == "Ceiling"
        assert result.uv_count == 500
        compare_numbers(result.coverage, 95.0)
        assert result.seam_count == 10


class TestUVSeamInfo:
    """Unit tests for UVSeamInfo dataclass."""

    def test_seam_info_creation(self):
        """SeamInfo should store edge data."""
        seam = UVSeamInfo(
            edge_index=42,
            vertices=(10, 20),
            angle=math.radians(75.0),
            reason="Sharp edge (75.0 degrees)",
        )

        assert seam.edge_index == 42
        assert seam.vertices == (10, 20)
        compare_numbers(seam.angle, math.radians(75.0))
        assert "75" in seam.reason

    def test_seam_info_small_angle(self):
        """Small angles should still work."""
        seam = UVSeamInfo(
            edge_index=0,
            vertices=(0, 1),
            angle=math.radians(15.0),
            reason="Smooth edge",
        )

        compare_numbers(seam.angle, math.radians(15.0))


class TestGenerateUVsFromProjection:
    """Unit tests for generate_uvs_from_projection function."""

    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        # Create a mock projection result
        result = ProjectionResult(
            hits_by_object={"Floor": [RayHit(hit=True, object_name="Floor")]},
        )

        with pytest.raises(RuntimeError) as exc_info:
            generate_uvs_from_projection(result)

        assert "Blender required" in str(exc_info.value)


class TestGenerateUVsForSurface:
    """Unit tests for generate_uvs_for_surface function."""

    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        surface = SurfaceInfo(object_name="Floor")
        with pytest.raises(RuntimeError) as exc_info:
            generate_uvs_for_surface(surface, "Camera", FrustumConfig())

        assert "Blender required" in str(exc_info.value)


class TestDetectUVSeams:
    """Unit tests for detect_uv_seams function."""

    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        surface = SurfaceInfo(object_name="Floor")
        with pytest.raises(RuntimeError) as exc_info:
            detect_uv_seams(surface)

        assert "Blender required" in str(exc_info.value)


class TestApplyUVSeams:
    """Unit tests for apply_uv_seams function."""

    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        surface = SurfaceInfo(object_name="Floor")
        seams = [UVSeamInfo(edge_index=0, vertices=(0, 1), angle=1.0, reason="test")]

        with pytest.raises(RuntimeError) as exc_info:
            apply_uv_seams(surface, seams)

        assert "Blender required" in str(exc_info.value)


class TestOptimizeUVLayout:
    """Unit tests for optimize_uv_layout function."""

    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        surface = SurfaceInfo(object_name="Floor")

        with pytest.raises(RuntimeError) as exc_info:
            optimize_uv_layout(surface)

        assert "Blender required" in str(exc_info.value)


class TestValidateUVLayout:
    """Unit tests for validate_uv_layout function."""

    def test_requires_blender(self):
        """Should raise RuntimeError without Blender."""
        surface = SurfaceInfo(object_name="Floor")

        with pytest.raises(RuntimeError) as exc_info:
            validate_uv_layout(surface)

        assert "Blender required" in str(exc_info.value)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_uv_generation_module_imports(self):
        """All UV generation types should be importable."""
        from lib.cinematic.projection.uv_generation import (
            UVGenerationResult,
            UVSeamInfo,
            UVLayoutConfig,
            generate_uvs_from_projection,
            generate_uvs_for_surface,
            detect_uv_seams,
            apply_uv_seams,
            optimize_uv_layout,
            validate_uv_layout,
        )

        assert UVGenerationResult is not None
        assert UVSeamInfo is not None
        assert UVLayoutConfig is not None
        assert callable(generate_uvs_from_projection)
        assert callable(generate_uvs_for_surface)

    def test_package_imports(self):
        """All UV generation APIs should be importable from package."""
        from lib.cinematic.projection import (
            UVGenerationResult,
            UVSeamInfo,
            UVLayoutConfig,
            generate_uvs_from_projection,
            generate_uvs_for_surface,
            detect_uv_seams,
            apply_uv_seams,
            optimize_uv_layout,
            validate_uv_layout,
        )

        assert UVGenerationResult is not None
        assert UVLayoutConfig is not None
        assert callable(generate_uvs_from_projection)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
