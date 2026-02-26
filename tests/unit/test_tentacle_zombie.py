"""Unit tests for zombie mouth tentacle system."""

import pytest
import numpy as np

from lib.tentacle import (
    TentacleConfig,
    ZombieMouthConfig,
)
from lib.tentacle.zombie import (
    calculate_mouth_distribution,
    angle_to_position,
    SizeMixConfig,
    MultiTentacleArray,
    MultiTentacleResult,
    create_zombie_mouth,
)


class TestMouthDistribution:
    """Test mouth distribution calculations."""

    def test_uniform_distribution(self):
        """Test uniform tentacle distribution."""
        positions = calculate_mouth_distribution(4, 60.0, "uniform")
        assert len(positions) == 4

        # All z_offsets should be 0 for uniform
        for angle, z in positions:
            assert z == 0.0

    def test_staggered_distribution(self):
        """Test staggered tentacle distribution."""
        positions = calculate_mouth_distribution(4, 60.0, "staggered")
        assert len(positions) == 4

        # Alternating z_offsets
        for i, (angle, z) in enumerate(positions):
            if i % 2 == 0:
                assert z > 0
            else:
                assert z < 0

    def test_random_distribution_deterministic(self):
        """Test that random distribution is deterministic."""
        p1 = calculate_mouth_distribution(4, 60.0, "random")
        p2 = calculate_mouth_distribution(4, 60.0, "random")
        assert p1 == p2

    def test_single_tentacle(self):
        """Test single tentacle at center."""
        positions = calculate_mouth_distribution(1, 60.0, "uniform")
        assert len(positions) == 1
        angle, z = positions[0]
        assert angle == pytest.approx(0.0)  # Center


class TestAngleToPosition:
    """Test angle to position conversion."""

    def test_center_position(self):
        """Test position at center (angle=0)."""
        pos = angle_to_position(0.0, 0.0, radius=0.03)
        assert pos[0] == pytest.approx(0.0)
        assert pos[2] == pytest.approx(0.0)

    def test_angle_offset(self):
        """Test position with angle offset."""
        pos = angle_to_position(np.pi / 4, 0.0, radius=0.03)
        assert pos[0] != 0.0  # X should be offset

    def test_z_offset(self):
        """Test z_offset affects z coordinate."""
        pos1 = angle_to_position(0.0, 0.0)
        pos2 = angle_to_position(0.0, 0.01)
        assert pos2[2] > pos1[2]


class TestSizeMixConfig:
    """Test size mix configuration."""

    def test_all_main(self):
        """Test size mix = 0 (all main tentacles)."""
        main_config = TentacleConfig(length=1.0)
        mix = SizeMixConfig(
            main_ratio=1.0,
            main_config=main_config,
        )

        for i in range(4):
            config = mix.get_config_for_index(i, 4)
            assert config.length == 1.0

    def test_mixed_sizes(self):
        """Test mixed main/feeler tentacles."""
        main_config = TentacleConfig(length=1.0, name="Main")
        feeler_config = TentacleConfig(length=0.5, name="Feeler")
        mix = SizeMixConfig(
            main_ratio=0.5,
            main_config=main_config,
            feeler_config=feeler_config,
        )

        # First 2 should be main (50% of 4)
        assert mix.get_config_for_index(0, 4).name == "Main"
        assert mix.get_config_for_index(1, 4).name == "Main"
        # Last 2 should be feelers
        assert mix.get_config_for_index(2, 4).name == "Feeler"
        assert mix.get_config_for_index(3, 4).name == "Feeler"


class TestMultiTentacleArray:
    """Test multi-tentacle array generation."""

    def test_generate_array(self):
        """Test generating tentacle array."""
        config = ZombieMouthConfig(
            tentacle_count=4,
            distribution="uniform",
            size_mix=0.5,
            spread_angle=60.0,
        )

        array = MultiTentacleArray(config)
        result = array.generate()

        assert isinstance(result, MultiTentacleResult)
        assert result.count == 4
        assert len(result.positions) == 4

    def test_total_vertex_count(self):
        """Test total vertex count calculation."""
        config = ZombieMouthConfig(tentacle_count=2)
        array = MultiTentacleArray(config)
        result = array.generate()

        # Should have vertices
        assert result.total_vertices > 0
        # Should be sum of individual tentacles
        assert result.total_vertices == sum(t.vertex_count for t in result.tentacles)

    def test_position_count_matches_tentacles(self):
        """Test that position count matches tentacle count."""
        config = ZombieMouthConfig(tentacle_count=6)
        array = MultiTentacleArray(config)
        result = array.generate()

        assert len(result.positions) == result.count


class TestCreateZombieMouth:
    """Test convenience function."""

    def test_create_zombie_mouth(self):
        """Test create_zombie_mouth convenience function."""
        config = ZombieMouthConfig(
            tentacle_count=4,
            distribution="staggered",
        )

        result = create_zombie_mouth(config)

        assert isinstance(result, MultiTentacleResult)
        assert result.count == 4
