"""Unit tests for tentacle geometry generation."""

import pytest
import numpy as np

from lib.tentacle import TentacleConfig
from lib.tentacle.geometry import (
    TentacleBodyGenerator,
    TentacleResult,
    create_tentacle,
    calculate_taper_radii,
    distribute_segment_points,
)


class TestTaperCalculations:
    """Test taper profile calculations."""

    def test_linear_taper(self):
        """Test linear taper profile."""
        radii = calculate_taper_radii(5, 0.04, 0.01, "linear")
        assert len(radii) == 5
        assert radii[0] == pytest.approx(0.04)  # Base
        assert radii[-1] == pytest.approx(0.01)  # Tip

    def test_organic_taper(self):
        """Test organic taper profile."""
        radii = calculate_taper_radii(20, 0.04, 0.01, "organic")
        assert len(radii) == 20
        assert radii[0] > radii[-1]  # Base larger than tip

    def test_radii_decrease(self):
        """Test that radii decrease from base to tip."""
        radii = calculate_taper_radii(10, 0.04, 0.01, "smooth")
        for i in range(len(radii) - 1):
            assert radii[i] >= radii[i + 1]


class TestSegmentDistribution:
    """Test segment point distribution."""

    def test_uniform_distribution(self):
        """Test uniform segment distribution."""
        positions = distribute_segment_points(10, 1.0, uniform=True)
        assert len(positions) == 11  # n+1 points for n segments
        assert positions[0] == 0.0
        assert positions[-1] == 1.0

    def test_deterministic_variation(self):
        """Test that variation is deterministic with seed."""
        p1 = distribute_segment_points(10, 1.0, variation=0.1, seed=42)
        p2 = distribute_segment_points(10, 1.0, variation=0.1, seed=42)
        np.testing.assert_array_equal(p1, p2)

    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        p1 = distribute_segment_points(10, 1.0, variation=0.1, seed=42)
        p2 = distribute_segment_points(10, 1.0, variation=0.1, seed=43)
        assert not np.array_equal(p1, p2)


class TestTentacleBodyGenerator:
    """Test tentacle body generation."""

    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid length
        with pytest.raises(ValueError):
            TentacleBodyGenerator(TentacleConfig(length=5.0))

        # Invalid segments
        with pytest.raises(ValueError):
            TentacleBodyGenerator(TentacleConfig(segments=100))

    def test_numpy_generation(self):
        """Test generation without Blender."""
        config = TentacleConfig(
            length=1.0,
            base_diameter=0.08,
            tip_diameter=0.02,
            segments=10,
        )
        generator = TentacleBodyGenerator(config)
        result = generator.generate()

        assert isinstance(result, TentacleResult)
        assert result.vertex_count > 0
        assert result.face_count > 0
        assert result.length == 1.0

    def test_vertex_count_matches_segments(self):
        """Test that vertex count matches expected for segments."""
        config = TentacleConfig(segments=10, curve_resolution=16)
        generator = TentacleBodyGenerator(config)
        result = generator.generate()

        # Expected: (segments + 1) * resolution
        expected = (10 + 1) * 16
        assert result.vertex_count == expected

    def test_deterministic_output(self):
        """Test that same config produces same mesh."""
        config = TentacleConfig(seed=42)

        gen1 = TentacleBodyGenerator(config)
        result1 = gen1.generate()

        gen2 = TentacleBodyGenerator(config)
        result2 = gen2.generate()

        np.testing.assert_array_equal(result1.vertices, result2.vertices)


class TestCreateTentacleConvenience:
    """Test convenience function."""

    def test_create_tentacle(self):
        """Test create_tentacle convenience function."""
        config = TentacleConfig()
        result = create_tentacle(config)

        assert isinstance(result, TentacleResult)
        assert result.vertex_count > 0
