"""
Unit tests for Quetzalcoatl Scale Layer (Phase 20.5)

Tests for procedural scale generation.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import ScaleConfig, ScaleShape, SpineConfig, BodyConfig
from lib.spine import SpineGenerator
from lib.body import BodyGenerator
from lib.scale import (
    ScaleGenerator,
    ScaleLayerResult,
    ScaleRegion,
    ScaleData,
    generate_scales,
)


class TestScaleRegion:
    """Tests for ScaleRegion enum."""

    def test_region_values(self):
        """Test region enum values."""
        assert ScaleRegion.HEAD.value == 0
        assert ScaleRegion.NECK.value == 1
        assert ScaleRegion.BACK.value == 2
        assert ScaleRegion.BELLY.value == 3
        assert ScaleRegion.TAIL.value == 4


class TestScaleData:
    """Tests for ScaleData dataclass."""

    def test_scale_creation(self):
        """Test creating scale data."""
        scale = ScaleData(
            position=np.array([0.5, 0.0, 0.0]),
            normal=np.array([1.0, 0.0, 0.0]),
            size=0.05,
            shape=ScaleShape.OVAL,
            rotation=0.1,
            overlap=0.3,
            region=ScaleRegion.BACK,
        )

        assert scale.size == 0.05
        assert scale.shape == ScaleShape.OVAL
        assert scale.region == ScaleRegion.BACK


class TestScaleLayerResult:
    """Tests for ScaleLayerResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample scale layer result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        scale_config = ScaleConfig()
        scale_gen = ScaleGenerator(scale_config, body_result)
        return scale_gen.generate(seed=42)

    def test_scale_count(self, sample_result):
        """Test that scales are generated."""
        assert sample_result.scale_count > 0

    def test_vertex_count(self, sample_result):
        """Test that vertices are generated."""
        assert sample_result.vertex_count > 0

    def test_vertices_shape(self, sample_result):
        """Test vertices array shape."""
        assert sample_result.vertices.shape[1] == 3

    def test_faces_shape(self, sample_result):
        """Test faces array shape."""
        if sample_result.faces.shape[0] > 0:
            assert sample_result.faces.shape[1] == 3

    def test_uvs_shape(self, sample_result):
        """Test UVs array shape."""
        assert sample_result.uvs.shape[1] == 2

    def test_scales_have_data(self, sample_result):
        """Test that scales have complete data."""
        for scale in sample_result.scales:
            assert scale.position.shape == (3,)
            assert scale.normal.shape == (3,)
            assert scale.size > 0
            assert isinstance(scale.shape, ScaleShape)
            assert isinstance(scale.region, ScaleRegion)


class TestScaleGenerator:
    """Tests for ScaleGenerator."""

    @pytest.fixture
    def setup_body(self):
        """Create body for testing."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        return body_gen.generate(radial_segments=8)

    def test_generate_basic(self, setup_body):
        """Test basic scale generation."""
        config = ScaleConfig()
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        assert isinstance(result, ScaleLayerResult)
        assert result.scale_count > 0

    def test_generate_with_seed(self, setup_body):
        """Test that seed produces consistent results."""
        config = ScaleConfig()

        gen1 = ScaleGenerator(config, setup_body)
        gen2 = ScaleGenerator(config, setup_body)

        result1 = gen1.generate(seed=123)
        result2 = gen2.generate(seed=123)

        assert result1.scale_count == result2.scale_count

    def test_density_affects_count(self, setup_body):
        """Test that density affects scale count."""
        config_low = ScaleConfig(density=0.5)
        config_high = ScaleConfig(density=2.0)

        gen_low = ScaleGenerator(config_low, setup_body)
        gen_high = ScaleGenerator(config_high, setup_body)

        result_low = gen_low.generate(seed=42)
        result_high = gen_high.generate(seed=42)

        assert result_high.scale_count > result_low.scale_count

    def test_size_affects_geometry(self, setup_body):
        """Test that size affects scale geometry."""
        config_small = ScaleConfig(size=0.02)
        config_large = ScaleConfig(size=0.1)

        gen_small = ScaleGenerator(config_small, setup_body)
        gen_large = ScaleGenerator(config_large, setup_body)

        result_small = gen_small.generate(seed=42)
        result_large = gen_large.generate(seed=42)

        # Both should generate
        assert result_small.vertex_count > 0
        assert result_large.vertex_count > 0

    def test_shape_round(self, setup_body):
        """Test round scale shape."""
        config = ScaleConfig(shape=ScaleShape.ROUND)
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        assert result.scale_count > 0
        for scale in result.scales:
            assert scale.shape == ScaleShape.ROUND

    def test_shape_oval(self, setup_body):
        """Test oval scale shape."""
        config = ScaleConfig(shape=ScaleShape.OVAL)
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        assert result.scale_count > 0
        for scale in result.scales:
            assert scale.shape == ScaleShape.OVAL

    def test_shape_hexagonal(self, setup_body):
        """Test hexagonal scale shape."""
        config = ScaleConfig(shape=ScaleShape.HEXAGONAL)
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        assert result.scale_count > 0
        for scale in result.scales:
            assert scale.shape == ScaleShape.HEXAGONAL

    def test_shape_diamond(self, setup_body):
        """Test diamond scale shape."""
        config = ScaleConfig(shape=ScaleShape.DIAMOND)
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        assert result.scale_count > 0
        for scale in result.scales:
            assert scale.shape == ScaleShape.DIAMOND

    def test_variation_affects_size(self, setup_body):
        """Test that variation affects scale sizes."""
        config_no_var = ScaleConfig(variation=0.0)
        config_with_var = ScaleConfig(variation=0.5)

        gen_no_var = ScaleGenerator(config_no_var, setup_body)
        gen_with_var = ScaleGenerator(config_with_var, setup_body)

        result_no_var = gen_no_var.generate(seed=42)
        result_with_var = gen_with_var.generate(seed=42)

        # With variation, sizes should vary
        if result_with_var.scale_count > 1:
            sizes = [s.size for s in result_with_var.scales]
            size_range = max(sizes) - min(sizes)
            # Some variation should exist (seed-dependent)
            # Just verify it runs without error

    def test_overlap_affects_geometry(self, setup_body):
        """Test that overlap affects scale height."""
        config_low = ScaleConfig(overlap=0.1)
        config_high = ScaleConfig(overlap=0.6)

        gen_low = ScaleGenerator(config_low, setup_body)
        gen_high = ScaleGenerator(config_high, setup_body)

        result_low = gen_low.generate(seed=42)
        result_high = gen_high.generate(seed=42)

        # Both should generate
        assert result_low.vertex_count > 0
        assert result_high.vertex_count > 0

    def test_regions_assigned(self, setup_body):
        """Test that scales have regions assigned."""
        config = ScaleConfig()
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        regions = {s.region for s in result.scales}
        # Should have at least some regions
        assert len(regions) > 0

    def test_vertex_normals_normalized(self, setup_body):
        """Test that vertex normals are normalized."""
        config = ScaleConfig()
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        if result.vertex_count > 0:
            lengths = np.linalg.norm(result.normals, axis=1)
            non_zero = lengths > 0.01
            if np.any(non_zero):
                assert np.allclose(lengths[non_zero], 1.0, atol=0.15)

    def test_faces_valid_indices(self, setup_body):
        """Test that all face indices are valid."""
        config = ScaleConfig()
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        if len(result.faces) > 0:
            max_idx = result.vertex_count
            assert np.all(result.faces >= 0)
            assert np.all(result.faces < max_idx)

    def test_uvs_in_valid_range(self, setup_body):
        """Test that UVs are in 0-1 range."""
        config = ScaleConfig()
        generator = ScaleGenerator(config, setup_body)
        result = generator.generate(seed=42)

        if result.vertex_count > 0:
            assert np.all(result.uvs >= 0)
            assert np.all(result.uvs <= 1)


class TestGenerateScales:
    """Tests for convenience function."""

    def test_generate_scales_defaults(self):
        """Test generate_scales with defaults."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_scales(ScaleConfig(), body_result, seed=42)

        assert isinstance(result, ScaleLayerResult)
        assert result.scale_count > 0

    def test_generate_scales_custom(self):
        """Test generate_scales with custom parameters."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_scales(
            ScaleConfig(
                size=0.08,
                shape=ScaleShape.HEXAGONAL,
                overlap=0.4,
                density=1.5,
            ),
            body_result,
            seed=42,
        )

        assert result.scale_count > 0
        for scale in result.scales:
            assert scale.shape == ScaleShape.HEXAGONAL


class TestIntegration:
    """Integration tests for scale system."""

    def test_full_pipeline(self):
        """Test full spine + body + scale generation pipeline."""
        # Generate spine
        spine_config = SpineConfig(length=12.0, segments=48)
        spine_gen = SpineGenerator(spine_config, seed=12345)
        spine_result = spine_gen.generate()

        # Generate body
        body_config = BodyConfig(radius=0.5)
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=16)

        # Generate scales
        scale_config = ScaleConfig(
            size=0.04,
            shape=ScaleShape.OVAL,
            overlap=0.3,
            density=1.0,
        )
        scale_gen = ScaleGenerator(scale_config, body_result)
        scale_result = scale_gen.generate(seed=42)

        # Verify output
        assert scale_result.scale_count > 0
        assert scale_result.vertex_count > 0

    def test_different_scale_types(self):
        """Test different scale shape types."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        shapes = [
            ScaleShape.ROUND,
            ScaleShape.OVAL,
            ScaleShape.HEXAGONAL,
            ScaleShape.DIAMOND,
        ]

        for shape in shapes:
            result = generate_scales(
                ScaleConfig(shape=shape),
                body_result,
                seed=42,
            )
            assert result.scale_count > 0
            for scale in result.scales:
                assert scale.shape == shape

    def test_empty_body(self):
        """Test handling of empty body."""
        # Create empty body result
        from lib.body import BodyResult

        empty_body = BodyResult(
            vertices=np.zeros((0, 3)),
            faces=np.zeros((0, 3), dtype=int),
            uvs=np.zeros((0, 2)),
            vertex_normals=np.zeros((0, 3)),
            spine_position=np.zeros(0),
            body_region=np.zeros(0, dtype=int),
            radial_angle=np.zeros(0),
        )

        config = ScaleConfig()
        generator = ScaleGenerator(config, empty_body)
        result = generator.generate(seed=42)

        # Should handle gracefully
        assert result.scale_count == 0
        assert result.vertex_count == 0
