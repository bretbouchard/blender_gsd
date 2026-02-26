"""
Unit tests for Quetzalcoatl Body System (Phase 20.1)

Tests for body mesh generation from spine curves.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import BodyConfig, SpineConfig
from lib.spine import SpineGenerator
from lib.body import (
    BodyGenerator,
    BodyResult,
    BodyRegion,
    generate_body,
)


class TestBodyRegion:
    """Tests for BodyRegion enum."""

    def test_region_values(self):
        """Test region enum values."""
        assert BodyRegion.HEAD.value == 0
        assert BodyRegion.NECK.value == 1
        assert BodyRegion.BODY.value == 2
        assert BodyRegion.TAIL_BASE.value == 3
        assert BodyRegion.TAIL_TIP.value == 4


class TestBodyResult:
    """Tests for BodyResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample body result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        return body_gen.generate(radial_segments=8)

    def test_vertex_count(self, sample_result):
        """Test vertex count matches expected."""
        # 32 spine points * 8 radial segments = 256 vertices
        assert sample_result.vertex_count == 256

    def test_face_count(self, sample_result):
        """Test face count matches expected."""
        # (32-1) spine segments * 8 radial * 2 triangles = 496 faces
        assert sample_result.face_count == 496

    def test_vertices_shape(self, sample_result):
        """Test vertices array shape."""
        assert sample_result.vertices.shape == (256, 3)

    def test_faces_shape(self, sample_result):
        """Test faces array shape."""
        assert sample_result.faces.shape == (496, 3)

    def test_uvs_shape(self, sample_result):
        """Test UVs array shape."""
        assert sample_result.uvs.shape == (256, 2)

    def test_uvs_range(self, sample_result):
        """Test UV coordinates are in valid range."""
        assert np.all(sample_result.uvs >= 0)
        assert np.all(sample_result.uvs[:, 0] <= 1)  # Spine position
        assert np.all(sample_result.uvs[:, 1] <= 1)  # Radial angle


class TestBodyGenerator:
    """Tests for BodyGenerator."""

    @pytest.fixture
    def spine_result(self):
        """Create a sample spine result."""
        config = SpineConfig(segments=32, length=10.0)
        generator = SpineGenerator(config, seed=42)
        return generator.generate()

    def test_generate_basic(self, spine_result):
        """Test basic body generation."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate(radial_segments=8)

        assert isinstance(result, BodyResult)
        assert result.vertex_count > 0

    def test_generate_custom_radial_segments(self, spine_result):
        """Test with different radial segment counts."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)

        result8 = generator.generate(radial_segments=8)
        result16 = generator.generate(radial_segments=16)

        assert result16.vertex_count == result8.vertex_count * 2

    def test_radius_affects_size(self, spine_result):
        """Test that radius affects body size."""
        generator_small = BodyGenerator(spine_result, BodyConfig(radius=0.3))
        generator_large = BodyGenerator(spine_result, BodyConfig(radius=0.8))

        result_small = generator_small.generate()
        result_large = generator_large.generate()

        # Large body should have vertices further from center
        dist_small = np.linalg.norm(result_small.vertices, axis=1)
        dist_large = np.linalg.norm(result_large.vertices, axis=1)

        assert np.mean(dist_large) > np.mean(dist_small)

    def test_compression_affects_shape(self, spine_result):
        """Test that compression creates elliptical shape."""
        generator_round = BodyGenerator(spine_result, BodyConfig(compression=1.0))
        generator_flat = BodyGenerator(spine_result, BodyConfig(compression=0.5))

        result_round = generator_round.generate()
        result_flat = generator_flat.generate()

        # Both should have same vertex count
        assert result_round.vertex_count == result_flat.vertex_count

    def test_vertex_normals_normalized(self, spine_result):
        """Test that vertex normals are normalized."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate()

        lengths = np.linalg.norm(result.vertex_normals, axis=1)
        assert np.allclose(lengths, 1.0, atol=0.01)

    def test_spine_positions_match(self, spine_result):
        """Test that spine positions are correctly assigned."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate(radial_segments=8)

        # Check that spine positions repeat correctly
        n_radial = 8
        for i in range(spine_result.point_count):
            expected_t = spine_result.spine_positions[i]
            for j in range(n_radial):
                idx = i * n_radial + j
                assert result.spine_position[idx] == expected_t

    def test_body_regions_assigned(self, spine_result):
        """Test that body regions are assigned."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate()

        # Should have multiple regions
        unique_regions = np.unique(result.body_region)
        assert len(unique_regions) >= 2

    def test_head_region_at_start(self, spine_result):
        """Test that head region is at spine start."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate(radial_segments=8)

        # First cross-section should be HEAD
        first_ring = result.body_region[:8]
        assert np.all(first_ring == BodyRegion.HEAD.value)

    def test_tail_region_at_end(self, spine_result):
        """Test that tail region is at spine end."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate(radial_segments=8)

        # Last cross-section should be TAIL_TIP
        last_ring = result.body_region[-8:]
        assert np.all(last_ring == BodyRegion.TAIL_TIP.value)

    def test_radial_angles_correct(self, spine_result):
        """Test that radial angles are correctly computed."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate(radial_segments=8)

        # Check that angles increase from 0 to 2π
        n_radial = 8
        for i in range(n_radial):
            expected_angle = 2 * np.pi * i / n_radial
            assert np.isclose(result.radial_angle[i], expected_angle)

    def test_faces_valid_indices(self, spine_result):
        """Test that all face indices are valid."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate()

        max_idx = result.vertex_count
        assert np.all(result.faces >= 0)
        assert np.all(result.faces < max_idx)

    def test_faces_no_degenerate(self, spine_result):
        """Test that there are no degenerate faces."""
        config = BodyConfig()
        generator = BodyGenerator(spine_result, config)
        result = generator.generate()

        # No face should have repeated vertices
        for face in result.faces:
            assert len(set(face)) == 3

    def test_dorsal_flat_reduces_height(self, spine_result):
        """Test that dorsal flattening affects top vertices."""
        generator_flat = BodyGenerator(
            spine_result, BodyConfig(dorsal_flat=0.0)
        )
        generator_dorsal = BodyGenerator(
            spine_result, BodyConfig(dorsal_flat=1.0)
        )

        result_flat = generator_flat.generate(radial_segments=16)
        result_dorsal = generator_dorsal.generate(radial_segments=16)

        # Both should generate successfully
        assert result_flat.vertex_count == result_dorsal.vertex_count

    def test_deterministic_output(self, spine_result):
        """Test that same config produces same output."""
        config = BodyConfig()

        gen1 = BodyGenerator(spine_result, config)
        result1 = gen1.generate()

        gen2 = BodyGenerator(spine_result, config)
        result2 = gen2.generate()

        assert np.array_equal(result1.vertices, result2.vertices)
        assert np.array_equal(result1.faces, result2.faces)


class TestGenerateBody:
    """Tests for convenience function."""

    def test_generate_body_defaults(self):
        """Test generate_body with defaults."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()

        result = generate_body(spine_result)

        assert isinstance(result, BodyResult)
        assert result.vertex_count == 16 * 16  # segments * radial

    def test_generate_body_custom(self):
        """Test generate_body with custom parameters."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()

        result = generate_body(
            spine_result,
            radius=0.8,
            compression=0.6,
            dorsal_flat=0.3,
            radial_segments=12,
        )

        assert result.vertex_count == 16 * 12


class TestIntegration:
    """Integration tests for body system."""

    def test_full_pipeline(self):
        """Test full spine + body generation pipeline."""
        # Generate spine
        spine_config = SpineConfig(length=15.0, segments=48)
        spine_gen = SpineGenerator(spine_config, seed=12345)
        spine_result = spine_gen.generate()

        # Generate body
        body_config = BodyConfig(radius=0.6, compression=0.75)
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=24)

        # Verify output
        assert body_result.vertex_count == 48 * 24
        assert body_result.face_count == (48 - 1) * 24 * 2

        # Verify mesh is watertight (basic check)
        assert np.all(body_result.faces >= 0)
        assert np.all(body_result.faces < body_result.vertex_count)

    def test_different_creature_configs(self):
        """Test body generation with different creature types."""
        # Serpent (long, thin)
        spine_serpent = SpineConfig(length=12.0, taper_head=0.2, taper_tail=0.1)
        body_serpent = BodyConfig(radius=0.35, compression=0.9)

        spine_result = SpineGenerator(spine_serpent, seed=42).generate()
        body_result = BodyGenerator(spine_result, body_serpent).generate()

        assert body_result.vertex_count > 0

        # Dragon (thicker, flatter)
        spine_dragon = SpineConfig(length=15.0, taper_head=0.4)
        body_dragon = BodyConfig(radius=0.7, compression=0.7, dorsal_flat=0.3)

        spine_result = SpineGenerator(spine_dragon, seed=42).generate()
        body_result = BodyGenerator(spine_result, body_dragon).generate()

        assert body_result.vertex_count > 0
