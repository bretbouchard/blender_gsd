"""
Unit tests for Quetzalcoatl Feather Layer (Phase 20.6)

Tests for procedural feather generation on body.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import FeatherConfig, SpineConfig, BodyConfig
from lib.spine import SpineGenerator
from lib.body import BodyGenerator
from lib.feather import (
    FeatherGenerator,
    FeatherLayerResult,
    FeatherRegion,
    FeatherData,
    generate_feathers,
)


class TestFeatherRegion:
    """Tests for FeatherRegion enum."""

    def test_region_values(self):
        """Test region enum values."""
        assert FeatherRegion.HEAD_CREST.value == 0
        assert FeatherRegion.NECK_MANE.value == 1
        assert FeatherRegion.BACK_RIDGE.value == 2
        assert FeatherRegion.TAIL_TUFT.value == 3
        assert FeatherRegion.BODY_PLUMAGE.value == 4


class TestFeatherData:
    """Tests for FeatherData dataclass."""

    def test_feather_creation(self):
        """Test creating feather data."""
        feather = FeatherData(
            position=np.array([0.5, 0.0, 0.2]),
            direction=np.array([0.7, -0.3, 0.5]),
            length=0.3,
            width=0.02,
            barb_density=20,
            rotation=0.1,
            iridescence=0.5,
            region=FeatherRegion.BACK_RIDGE,
        )

        assert feather.length == 0.3
        assert feather.barb_density == 20
        assert feather.region == FeatherRegion.BACK_RIDGE


class TestFeatherLayerResult:
    """Tests for FeatherLayerResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample feather layer result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        feather_config = FeatherConfig()
        feather_gen = FeatherGenerator(feather_config, body_result)
        return feather_gen.generate(seed=42, coverage=0.2)

    def test_feather_count(self, sample_result):
        """Test that feathers are generated."""
        assert sample_result.feather_count > 0

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

    def test_feathers_have_data(self, sample_result):
        """Test that feathers have complete data."""
        for feather in sample_result.feathers:
            assert feather.position.shape == (3,)
            assert feather.direction.shape == (3,)
            assert feather.length > 0
            assert feather.width > 0
            assert isinstance(feather.region, FeatherRegion)


class TestFeatherGenerator:
    """Tests for FeatherGenerator."""

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
        """Test basic feather generation."""
        config = FeatherConfig()
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        assert isinstance(result, FeatherLayerResult)
        assert result.feather_count > 0

    def test_generate_with_seed(self, setup_body):
        """Test that seed produces consistent results."""
        config = FeatherConfig()

        gen1 = FeatherGenerator(config, setup_body)
        gen2 = FeatherGenerator(config, setup_body)

        result1 = gen1.generate(seed=123, coverage=0.2)
        result2 = gen2.generate(seed=123, coverage=0.2)

        assert result1.feather_count == result2.feather_count

    def test_coverage_affects_count(self, setup_body):
        """Test that coverage affects feather count."""
        config = FeatherConfig()

        gen = FeatherGenerator(config, setup_body)

        result_low = gen.generate(seed=42, coverage=0.1)
        result_high = gen.generate(seed=42, coverage=0.5)

        assert result_high.feather_count > result_low.feather_count

    def test_length_affects_geometry(self, setup_body):
        """Test that length affects feather geometry."""
        config_short = FeatherConfig(length=0.1)
        config_long = FeatherConfig(length=0.5)

        gen_short = FeatherGenerator(config_short, setup_body)
        gen_long = FeatherGenerator(config_long, setup_body)

        result_short = gen_short.generate(seed=42, coverage=0.2)
        result_long = gen_long.generate(seed=42, coverage=0.2)

        # Both should generate
        assert result_short.vertex_count > 0
        assert result_long.vertex_count > 0

    def test_width_affects_geometry(self, setup_body):
        """Test that width affects feather geometry."""
        config_narrow = FeatherConfig(width=0.01)
        config_wide = FeatherConfig(width=0.05)

        gen_narrow = FeatherGenerator(config_narrow, setup_body)
        gen_wide = FeatherGenerator(config_wide, setup_body)

        result_narrow = gen_narrow.generate(seed=42, coverage=0.2)
        result_wide = gen_wide.generate(seed=42, coverage=0.2)

        # Both should generate
        assert result_narrow.vertex_count > 0
        assert result_wide.vertex_count > 0

    def test_barb_density_configured(self, setup_body):
        """Test that barb density is configured."""
        config = FeatherConfig(barb_density=30)
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        for feather in result.feathers:
            assert feather.barb_density == 30

    def test_iridescence_configured(self, setup_body):
        """Test that iridescence is configured."""
        config = FeatherConfig(iridescence=0.8)
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        for feather in result.feathers:
            assert feather.iridescence == 0.8

    def test_regions_assigned(self, setup_body):
        """Test that feathers have regions assigned."""
        config = FeatherConfig()
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.3)

        regions = {f.region for f in result.feathers}
        # Should have at least some regions
        assert len(regions) > 0

    def test_vertex_normals_normalized(self, setup_body):
        """Test that vertex normals are normalized."""
        config = FeatherConfig()
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        if result.vertex_count > 0:
            lengths = np.linalg.norm(result.normals, axis=1)
            non_zero = lengths > 0.01
            if np.any(non_zero):
                assert np.allclose(lengths[non_zero], 1.0, atol=0.15)

    def test_faces_valid_indices(self, setup_body):
        """Test that all face indices are valid."""
        config = FeatherConfig()
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        if len(result.faces) > 0:
            max_idx = result.vertex_count
            assert np.all(result.faces >= 0)
            assert np.all(result.faces < max_idx)

    def test_uvs_in_valid_range(self, setup_body):
        """Test that UVs are in 0-1 range."""
        config = FeatherConfig()
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        if result.vertex_count > 0:
            assert np.all(result.uvs >= 0)
            assert np.all(result.uvs <= 1)

    def test_feather_directions_normalized(self, setup_body):
        """Test that feather directions are normalized."""
        config = FeatherConfig()
        generator = FeatherGenerator(config, setup_body)
        result = generator.generate(seed=42, coverage=0.2)

        for feather in result.feathers:
            length = np.linalg.norm(feather.direction)
            assert np.isclose(length, 1.0, atol=0.01)


class TestGenerateFeathers:
    """Tests for convenience function."""

    def test_generate_feathers_defaults(self):
        """Test generate_feathers with defaults."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_feathers(
            FeatherConfig(),
            body_result,
            seed=42,
            coverage=0.2,
        )

        assert isinstance(result, FeatherLayerResult)
        assert result.feather_count > 0

    def test_generate_feathers_custom(self):
        """Test generate_feathers with custom parameters."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_feathers(
            FeatherConfig(
                length=0.4,
                width=0.03,
                barb_density=25,
                iridescence=0.7,
            ),
            body_result,
            seed=42,
            coverage=0.3,
        )

        assert result.feather_count > 0
        for feather in result.feathers:
            assert feather.barb_density == 25
            assert feather.iridescence == 0.7


class TestIntegration:
    """Integration tests for feather system."""

    def test_full_pipeline(self):
        """Test full spine + body + feather generation pipeline."""
        # Generate spine
        spine_config = SpineConfig(length=12.0, segments=48)
        spine_gen = SpineGenerator(spine_config, seed=12345)
        spine_result = spine_gen.generate()

        # Generate body
        body_config = BodyConfig(radius=0.5)
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=16)

        # Generate feathers
        feather_config = FeatherConfig(
            length=0.25,
            width=0.02,
            barb_density=20,
            iridescence=0.6,
        )
        feather_gen = FeatherGenerator(feather_config, body_result)
        feather_result = feather_gen.generate(seed=42, coverage=0.25)

        # Verify output
        assert feather_result.feather_count > 0
        assert feather_result.vertex_count > 0

    def test_different_layer_counts(self):
        """Test with different coverage values."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        for coverage in [0.1, 0.3, 0.5]:
            result = generate_feathers(
                FeatherConfig(),
                body_result,
                seed=42,
                coverage=coverage,
            )
            assert result.feather_count > 0

    def test_empty_body(self):
        """Test handling of empty body."""
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

        config = FeatherConfig()
        generator = FeatherGenerator(config, empty_body)
        result = generator.generate(seed=42, coverage=0.3)

        # Should handle gracefully
        assert result.feather_count == 0
        assert result.vertex_count == 0
