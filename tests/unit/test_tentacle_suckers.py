"""Unit tests for sucker system."""

import pytest
import numpy as np

from lib.tentacle.suckers import (
    SuckerConfig,
    SuckerInstance,
    SuckerResult,
    SuckerGenerator,
    generate_suckers,
    calculate_sucker_positions,
    calculate_sucker_mesh_size,
)


class TestSuckerConfig:
    """Test sucker configuration."""

    def test_default_config(self):
        """Test default configuration is valid."""
        config = SuckerConfig()
        assert config.enabled is True
        assert config.rows == 6
        assert config.columns == 8
        assert config.base_size == 0.015
        assert config.tip_size == 0.003

    def test_config_validation_rows(self):
        """Test row count validation."""
        with pytest.raises(ValueError):
            SuckerConfig(rows=1)
        with pytest.raises(ValueError):
            SuckerConfig(rows=10)

    def test_config_validation_columns(self):
        """Test column count validation."""
        with pytest.raises(ValueError):
            SuckerConfig(columns=3)
        with pytest.raises(ValueError):
            SuckerConfig(columns=15)

    def test_config_validation_size(self):
        """Test size validation."""
        with pytest.raises(ValueError):
            SuckerConfig(base_size=0.01, tip_size=0.02)

    def test_get_size_at_position(self):
        """Test size interpolation."""
        config = SuckerConfig(base_size=0.02, tip_size=0.004)

        # At base (t=0)
        assert config.get_size_at_position(0.0) == pytest.approx(0.02)

        # At tip (t=1)
        assert config.get_size_at_position(1.0) == pytest.approx(0.004)

        # At middle (t=0.5)
        mid_size = config.get_size_at_position(0.5)
        assert 0.004 < mid_size < 0.02


class TestSuckerPlacement:
    """Test sucker placement calculations."""

    def test_disabled_suckers(self):
        """Test that disabled config returns empty list."""
        config = SuckerConfig(enabled=False)

        def radius_func(t):
            return 0.04

        positions = calculate_sucker_positions(config, 1.0, radius_func)
        assert positions == []

    def test_uniform_placement_count(self):
        """Test uniform placement generates correct count."""
        config = SuckerConfig(rows=4, columns=6, placement="uniform")

        def radius_func(t):
            return 0.04

        positions = calculate_sucker_positions(config, 1.0, radius_func)
        assert len(positions) == 4 * 6  # rows * columns

    def test_alternating_placement(self):
        """Test alternating placement has offset rows."""
        config = SuckerConfig(rows=4, columns=6, placement="alternating")

        def radius_func(t):
            return 1.04

        positions = calculate_sucker_positions(config, 1.0, radius_func)
        assert len(positions) == 4 * 6

    def test_random_placement_deterministic(self):
        """Test random placement is deterministic with seed."""
        config = SuckerConfig(rows=4, columns=6, placement="random", seed=42)

        def radius_func(t):
            return 1.04

        p1 = calculate_sucker_positions(config, 1.0, radius_func)
        p2 = calculate_sucker_positions(config, 1.0, radius_func)

        assert len(p1) == len(p2)
        for s1, s2 in zip(p1, p2):
            assert s1.position == pytest.approx(s2.position)

    def test_sucker_instance_data(self):
        """Test sucker instance has correct data."""
        config = SuckerConfig(rows=2, columns=4)

        def radius_func(t):
            return 1.04

        positions = calculate_sucker_positions(config, 1.0, radius_func)

        for sucker in positions:
            assert isinstance(sucker, SuckerInstance)
            assert len(sucker.position) == 3
            assert len(sucker.normal) == 3
            assert sucker.size > 0

    def test_size_gradient(self):
        """Test that suckers are larger at base than tip."""
        config = SuckerConfig(rows=4, columns=4, size_variation=0.0)

        def radius_func(t):
            return 1.04

        positions = calculate_sucker_positions(config, 1.0, radius_func)

        # First row (base) should have larger suckers than last row (tip)
        base_sizes = [s.size for s in positions if s.row_index == 0]
        tip_sizes = [s.size for s in positions if s.row_index == 3]

        assert min(base_sizes) > max(tip_sizes)


class TestSuckerGenerator:
    """Test sucker geometry generation."""

    def test_generator_creation(self):
        """Test generator can be created."""
        config = SuckerConfig()
        generator = SuckerGenerator(config)
        assert generator.config == config

    def test_generate_for_tentacle(self):
        """Test generating suckers for a tentacle."""
        config = SuckerConfig(rows=3, columns=4)
        generator = SuckerGenerator(config)

        def radius_func(t):
            return 1.04 - 0.02 * t

        result = generator.generate_for_tentacle(1.0, radius_func)

        assert isinstance(result, SuckerResult)
        assert result.count == 12  # 3 rows * 4 columns
        assert result.total_count == 12

    def test_generate_disabled(self):
        """Test generating with suckers disabled."""
        config = SuckerConfig(enabled=False)
        generator = SuckerGenerator(config)

        def radius_func(t):
            return 1.04

        result = generator.generate_for_tentacle(1.0, radius_func)

        assert result.count == 0

    def test_generate_with_geometry(self):
        """Test that geometry is generated."""
        config = SuckerConfig(rows=2, columns=4)
        generator = SuckerGenerator(config)

        def radius_func(t):
            return 1.04

        result = generator.generate_for_tentacle(1.0, radius_func)

        # Should have vertex and face counts
        assert result.vertex_count > 0
        assert result.face_count > 0


class TestGenerateSuckersConvenience:
    """Test convenience function."""

    def test_generate_suckers(self):
        """Test generate_suckers convenience function."""
        config = SuckerConfig(rows=2, columns=4)

        def radius_func(t):
            return 1.04

        result = generate_suckers(config, 1.0, radius_func)

        assert isinstance(result, SuckerResult)
        assert result.count == 8


class TestSuckerMeshSize:
    """Test sucker mesh size calculations."""

    def test_mesh_size_calculation(self):
        """Test mesh size estimation."""
        verts, faces = calculate_sucker_mesh_size(0.015, 0.005, 0.002, resolution=16)

        assert verts > 0
        assert faces > 0
        assert isinstance(verts, int)
        assert isinstance(faces, int)
