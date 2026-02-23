"""
Unit tests for lib/geometry_nodes/lod_system.py

Tests the LOD (Level of Detail) system including:
- LODStrategy enum
- LODQuality enum
- LODLevel dataclass
- LODConfig dataclass
- LODState dataclass
- DEFAULT_LOD_CONFIGS
- LODManager class
- LODSelector class
- create_lod_config function
"""

import pytest
import math

from lib.geometry_nodes.lod_system import (
    LODStrategy,
    LODQuality,
    LODLevel,
    LODConfig,
    LODState,
    DEFAULT_LOD_CONFIGS,
    LODManager,
    LODSelector,
    create_lod_config,
)


class TestLODStrategy:
    """Tests for LODStrategy enum."""

    def test_lod_strategy_values(self):
        """Test that LODStrategy enum has expected values."""
        assert LODStrategy.DISTANCE.value == "distance"
        assert LODStrategy.SCREEN_SIZE.value == "screen_size"
        assert LODStrategy.INSTANCE_COUNT.value == "instance_count"
        assert LODStrategy.MANUAL.value == "manual"

    def test_lod_strategy_count(self):
        """Test that all expected strategies exist."""
        assert len(LODStrategy) == 4


class TestLODQuality:
    """Tests for LODQuality enum."""

    def test_lod_quality_values(self):
        """Test that LODQuality enum has expected values."""
        assert LODQuality.HIGH.value == 0
        assert LODQuality.MEDIUM.value == 1
        assert LODQuality.LOW.value == 2
        assert LODQuality.IMPOSTOR.value == 3

    def test_lod_quality_order(self):
        """Test that LOD quality levels are ordered."""
        assert LODQuality.HIGH.value < LODQuality.MEDIUM.value
        assert LODQuality.MEDIUM.value < LODQuality.LOW.value
        assert LODQuality.LOW.value < LODQuality.IMPOSTOR.value


class TestLODLevel:
    """Tests for LODLevel dataclass."""

    def test_default_values(self):
        """Test LODLevel default values."""
        level = LODLevel()
        assert level.level == 0
        assert level.distance_min == 0.0
        assert level.distance_max == 100.0
        assert level.screen_size_min == 0.0
        assert level.decimation_ratio == 1.0
        assert level.texture_resolution == 1.0
        assert level.use_impostor is False
        assert level.material_simplification == 0

    def test_custom_values(self):
        """Test LODLevel with custom values."""
        level = LODLevel(
            level=2,
            distance_min=50.0,
            distance_max=100.0,
            decimation_ratio=0.25,
            texture_resolution=0.25,
            use_impostor=True,
        )
        assert level.level == 2
        assert level.distance_min == 50.0
        assert level.decimation_ratio == 0.25
        assert level.use_impostor is True

    def test_to_dict(self):
        """Test LODLevel.to_dict() serialization."""
        level = LODLevel(level=1, distance_min=20.0, distance_max=50.0)
        data = level.to_dict()
        assert data["level"] == 1
        assert data["distance_min"] == 20.0
        assert data["distance_max"] == 50.0

    def test_from_dict(self):
        """Test LODLevel.from_dict() deserialization."""
        data = {
            "level": 2,
            "distance_min": 50.0,
            "distance_max": 100.0,
            "decimation_ratio": 0.5,
        }
        level = LODLevel.from_dict(data)
        assert level.level == 2
        assert level.distance_min == 50.0
        assert level.decimation_ratio == 0.5

    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = LODLevel(
            level=3,
            distance_min=100.0,
            distance_max=500.0,
            use_impostor=True,
        )
        data = original.to_dict()
        restored = LODLevel.from_dict(data)
        assert restored.level == original.level
        assert restored.distance_min == original.distance_min
        assert restored.use_impostor == original.use_impostor


class TestLODConfig:
    """Tests for LODConfig dataclass."""

    def test_default_values(self):
        """Test LODConfig default values."""
        config = LODConfig()
        assert config.config_id == "default"
        assert config.strategy == "distance"
        assert config.levels == []
        assert config.hysteresis == 2.0
        assert config.transition_speed == 0.1

    def test_custom_values(self):
        """Test LODConfig with custom values."""
        config = LODConfig(
            config_id="custom",
            strategy="screen_size",
            levels=[LODLevel(level=0), LODLevel(level=1)],
            hysteresis=5.0,
        )
        assert config.config_id == "custom"
        assert config.strategy == "screen_size"
        assert len(config.levels) == 2
        assert config.hysteresis == 5.0

    def test_to_dict(self):
        """Test LODConfig.to_dict() serialization."""
        config = LODConfig(
            config_id="test",
            levels=[LODLevel(level=0), LODLevel(level=1)],
        )
        data = config.to_dict()
        assert data["config_id"] == "test"
        assert len(data["levels"]) == 2

    def test_from_dict(self):
        """Test LODConfig.from_dict() deserialization."""
        data = {
            "config_id": "from_dict",
            "strategy": "distance",
            "levels": [{"level": 0}, {"level": 1}, {"level": 2}],
            "hysteresis": 3.0,
        }
        config = LODConfig.from_dict(data)
        assert config.config_id == "from_dict"
        assert len(config.levels) == 3
        assert config.hysteresis == 3.0

    def test_get_level_for_distance_no_levels(self):
        """Test get_level_for_distance with no levels."""
        config = LODConfig()
        level = config.get_level_for_distance(50.0)
        assert level == 0

    def test_get_level_for_distance_basic(self):
        """Test basic distance-based LOD selection."""
        config = LODConfig(
            levels=[
                LODLevel(level=0, distance_min=0.0, distance_max=20.0),
                LODLevel(level=1, distance_min=20.0, distance_max=50.0),
                LODLevel(level=2, distance_min=50.0, distance_max=100.0),
            ],
        )

        assert config.get_level_for_distance(10.0) == 0
        assert config.get_level_for_distance(30.0) == 1
        assert config.get_level_for_distance(75.0) == 2

    def test_get_level_for_distance_boundary(self):
        """Test LOD selection at boundaries."""
        config = LODConfig(
            levels=[
                LODLevel(level=0, distance_min=0.0, distance_max=20.0),
                LODLevel(level=1, distance_min=20.0, distance_max=50.0),
            ],
        )

        # At exactly 20.0, should be level 1 (min is inclusive, max is exclusive)
        assert config.get_level_for_distance(20.0) == 1

    def test_get_level_for_distance_hysteresis(self):
        """Test LOD selection with hysteresis."""
        config = LODConfig(
            levels=[
                LODLevel(level=0, distance_min=0.0, distance_max=20.0),
                LODLevel(level=1, distance_min=20.0, distance_max=50.0),
            ],
            hysteresis=5.0,
        )

        # Going from high detail to low detail - no hysteresis
        assert config.get_level_for_distance(25.0, previous_level=0) == 1

        # Test basic distance selection still works
        assert config.get_level_for_distance(10.0) == 0
        assert config.get_level_for_distance(30.0) == 1


class TestLODState:
    """Tests for LODState dataclass."""

    def test_default_values(self):
        """Test LODState default values."""
        state = LODState()
        assert state.instance_id == ""
        assert state.current_level == 0
        assert state.target_level == 0
        assert state.transition_progress == 1.0
        assert state.last_distance == 0.0

    def test_custom_values(self):
        """Test LODState with custom values."""
        state = LODState(
            instance_id="inst_001",
            current_level=1,
            target_level=2,
            transition_progress=0.5,
            last_distance=35.0,
        )
        assert state.instance_id == "inst_001"
        assert state.current_level == 1
        assert state.target_level == 2
        assert state.transition_progress == 0.5

    def test_to_dict(self):
        """Test LODState.to_dict() serialization."""
        state = LODState(instance_id="inst_001", current_level=2)
        data = state.to_dict()
        assert data["instance_id"] == "inst_001"
        assert data["current_level"] == 2


class TestDefaultLODConfigs:
    """Tests for DEFAULT_LOD_CONFIGS dictionary."""

    def test_default_exists(self):
        """Test that 'default' config exists."""
        assert "default" in DEFAULT_LOD_CONFIGS

    def test_high_quality_exists(self):
        """Test that 'high_quality' config exists."""
        assert "high_quality" in DEFAULT_LOD_CONFIGS

    def test_performance_exists(self):
        """Test that 'performance' config exists."""
        assert "performance" in DEFAULT_LOD_CONFIGS

    def test_foliage_exists(self):
        """Test that 'foliage' config exists."""
        assert "foliage" in DEFAULT_LOD_CONFIGS

    def test_characters_exists(self):
        """Test that 'characters' config exists."""
        assert "characters" in DEFAULT_LOD_CONFIGS

    def test_default_has_four_levels(self):
        """Test that default config has 4 LOD levels."""
        config = DEFAULT_LOD_CONFIGS["default"]
        assert len(config.levels) == 4

    def test_default_levels_progression(self):
        """Test that default config levels progress correctly."""
        config = DEFAULT_LOD_CONFIGS["default"]
        for i, level in enumerate(config.levels):
            assert level.level == i

    def test_performance_uses_impostor_sooner(self):
        """Test that performance config uses impostor at closer distances."""
        perf = DEFAULT_LOD_CONFIGS["performance"]
        default = DEFAULT_LOD_CONFIGS["default"]

        # Performance should have impostor at closer distance
        perf_impostor_distance = perf.levels[2].distance_min
        default_impostor_distance = default.levels[3].distance_min

        assert perf_impostor_distance < default_impostor_distance


class TestLODManager:
    """Tests for LODManager class."""

    def test_default_initialization(self):
        """Test LODManager default initialization."""
        manager = LODManager()
        assert manager.config is not None
        assert manager.camera_position == (0.0, 0.0, 0.0)
        assert len(manager.states) == 0

    def test_custom_config(self):
        """Test LODManager with custom config."""
        config = LODConfig(config_id="test")
        manager = LODManager(config)
        assert manager.config.config_id == "test"

    def test_set_config(self):
        """Test setting a config."""
        manager = LODManager()
        config = LODConfig(config_id="custom")
        manager.set_config("custom", config)
        assert "custom" in manager.configs

    def test_get_config(self):
        """Test getting a config."""
        manager = LODManager()
        config = manager.get_config("default")
        assert config.config_id == "default"

    def test_get_config_nonexistent(self):
        """Test getting a nonexistent config returns default."""
        manager = LODManager()
        config = manager.get_config("nonexistent")
        assert config.config_id == "default"

    def test_set_camera_position(self):
        """Test setting camera position."""
        manager = LODManager()
        manager.set_camera_position((10.0, 20.0, 5.0))
        assert manager.camera_position == (10.0, 20.0, 5.0)

    def test_calculate_distance(self):
        """Test distance calculation."""
        manager = LODManager()
        manager.set_camera_position((0.0, 0.0, 0.0))

        distance = manager.calculate_distance((3.0, 4.0, 0.0))
        assert distance == pytest.approx(5.0, rel=0.01)

    def test_calculate_distance_offset(self):
        """Test distance calculation with camera offset."""
        manager = LODManager()
        manager.set_camera_position((10.0, 0.0, 0.0))

        distance = manager.calculate_distance((13.0, 4.0, 0.0))
        assert distance == pytest.approx(5.0, rel=0.01)

    def test_update_instance(self):
        """Test updating a single instance."""
        manager = LODManager()
        manager.set_camera_position((0.0, 0.0, 0.0))

        state = manager.update_instance("inst_001", (0.0, 0.0, -10.0))

        assert state.instance_id == "inst_001"
        assert state.last_distance == pytest.approx(10.0, rel=0.01)
        assert "inst_001" in manager.states

    def test_update_instance_multiple(self):
        """Test updating instance multiple times."""
        manager = LODManager()
        manager.set_camera_position((0.0, 0.0, 0.0))

        # First update at close distance
        state1 = manager.update_instance("inst_001", (0.0, 0.0, -5.0))
        assert state1.current_level == 0  # Should be highest detail

        # Second update at far distance
        state2 = manager.update_instance("inst_001", (0.0, 0.0, -100.0))
        assert state2.last_distance == pytest.approx(100.0, rel=0.01)

    def test_update_instance_transition(self):
        """Test LOD transition."""
        manager = LODManager()
        manager.set_camera_position((0.0, 0.0, 0.0))

        # Start at close distance
        state = manager.update_instance("inst_001", (0.0, 0.0, -5.0))
        assert state.transition_progress == 1.0

        # Move to far distance - should start transition
        state = manager.update_instance("inst_001", (0.0, 0.0, -100.0))
        assert state.target_level != state.current_level or state.transition_progress == 0.0

    def test_update_instances(self):
        """Test updating multiple instances."""
        manager = LODManager()
        manager.set_camera_position((0.0, 0.0, 0.0))

        instances = [
            {"instance_id": "inst_001", "position": (0.0, 0.0, -10.0)},
            {"instance_id": "inst_002", "position": (0.0, 0.0, -50.0)},
        ]

        results = manager.update_instances(instances)

        assert len(results) == 2
        assert "inst_001" in results
        assert "inst_002" in results

    def test_update_instances_with_config_map(self):
        """Test updating instances with config mapping."""
        manager = LODManager()

        instances = [
            {"instance_id": "inst_001", "position": (0.0, 0.0, -10.0)},
        ]

        config_map = {"inst_001": "high_quality"}
        results = manager.update_instances(instances, config_map)

        assert len(results) == 1

    def test_update_instances_empty(self):
        """Test updating empty instance list."""
        manager = LODManager()
        results = manager.update_instances([])
        assert results == {}

    def test_get_instance_state(self):
        """Test getting instance state."""
        manager = LODManager()
        manager.update_instance("inst_001", (0.0, 0.0, -10.0))

        state = manager.get_instance_state("inst_001")
        assert state is not None
        assert state.instance_id == "inst_001"

    def test_get_instance_state_nonexistent(self):
        """Test getting nonexistent instance state."""
        manager = LODManager()
        state = manager.get_instance_state("nonexistent")
        assert state is None

    def test_get_statistics(self):
        """Test getting statistics."""
        manager = LODManager()
        manager.update_instance("inst_001", (0.0, 0.0, -5.0))
        manager.update_instance("inst_002", (0.0, 0.0, -50.0))

        stats = manager.get_statistics()

        assert stats["total_instances"] == 2
        assert "level_distribution" in stats
        assert stats["update_count"] == 0  # Updated via update_instances

    def test_to_gn_input(self):
        """Test converting to GN input format."""
        manager = LODManager()
        manager.update_instance("inst_001", (0.0, 0.0, -10.0))

        gn_data = manager.to_gn_input()

        assert "version" in gn_data
        assert "states" in gn_data
        assert "statistics" in gn_data
        assert "configs" in gn_data
        assert "inst_001" in gn_data["states"]

    def test_reset(self):
        """Test resetting LOD states."""
        manager = LODManager()
        manager.update_instance("inst_001", (0.0, 0.0, -10.0))

        manager.reset()

        assert len(manager.states) == 0
        assert manager._update_count == 0


class TestLODSelector:
    """Tests for LODSelector class."""

    def test_select_lod_variant_exact_match(self):
        """Test selecting exact match variant."""
        variant = LODSelector.select_lod_variant(1, [0, 1, 2])
        assert variant == 1

    def test_select_lod_variant_first_match(self):
        """Test selecting first matching variant."""
        variant = LODSelector.select_lod_variant(0, [0, 1, 2])
        assert variant == 0

    def test_select_lod_variant_closest(self):
        """Test selecting closest variant when no exact match."""
        variant = LODSelector.select_lod_variant(1, [0, 2])
        # Should return 0 or 2, whichever is closest
        assert variant in [0, 2]

    def test_select_lod_variant_empty(self):
        """Test selecting variant with empty list."""
        variant = LODSelector.select_lod_variant(1, [])
        assert variant == 0

    def test_select_lod_variant_prefers_higher_detail(self):
        """Test that higher detail is preferred when within 1 level."""
        variant = LODSelector.select_lod_variant(2, [0, 1, 3])
        # Should prefer 1 (higher detail) over 3 (same distance from target)
        assert variant == 1

    def test_select_lod_variant_single(self):
        """Test selecting with single available variant."""
        variant = LODSelector.select_lod_variant(2, [1])
        assert variant == 1


class TestCreateLODConfig:
    """Tests for create_lod_config function."""

    def test_default_parameters(self):
        """Test create_lod_config with default parameters."""
        config = create_lod_config()

        assert config.config_id == "custom"
        assert config.strategy == "distance"
        assert len(config.levels) == 4
        assert config.hysteresis == 2.0

    def test_custom_levels(self):
        """Test create_lod_config with custom level count."""
        config = create_lod_config(levels=3)

        assert len(config.levels) == 3

    def test_custom_max_distance(self):
        """Test create_lod_config with custom max distance."""
        config = create_lod_config(levels=4, max_distance=200.0)

        # Last level should go to max_distance
        assert config.levels[-1].distance_max == 200.0

    def test_custom_hysteresis(self):
        """Test create_lod_config with custom hysteresis."""
        config = create_lod_config(hysteresis=5.0)

        assert config.hysteresis == 5.0

    def test_levels_evenly_spaced(self):
        """Test that levels are evenly spaced by distance."""
        config = create_lod_config(levels=4, max_distance=100.0)

        # Each level should span 25 units
        for i, level in enumerate(config.levels):
            assert level.distance_min == pytest.approx(i * 25.0, rel=0.01)
            assert level.distance_max == pytest.approx((i + 1) * 25.0, rel=0.01)

    def test_last_level_uses_impostor(self):
        """Test that last level uses impostor."""
        config = create_lod_config(levels=3)

        assert config.levels[0].use_impostor is False
        assert config.levels[1].use_impostor is False
        assert config.levels[2].use_impostor is True

    def test_decimation_progression(self):
        """Test that decimation ratio decreases with level."""
        config = create_lod_config(levels=4, decimation_start=0.5)

        for i in range(len(config.levels) - 1):
            assert config.levels[i].decimation_ratio >= config.levels[i + 1].decimation_ratio

    def test_single_level(self):
        """Test create_lod_config with single level."""
        config = create_lod_config(levels=1)

        assert len(config.levels) == 1
        assert config.levels[0].level == 0
        assert config.levels[0].use_impostor is True


class TestLODManagerIntegration:
    """Integration tests for LODManager."""

    def test_full_workflow(self):
        """Test complete LOD management workflow."""
        manager = LODManager()
        manager.set_camera_position((0.0, 0.0, 0.0))

        # Create multiple instances at various distances
        instances = [
            {"instance_id": "close", "position": (0.0, 0.0, -5.0)},
            {"instance_id": "medium", "position": (0.0, 0.0, -35.0)},
            {"instance_id": "far", "position": (0.0, 0.0, -75.0)},
        ]

        manager.update_instances(instances)

        # Verify states
        close_state = manager.get_instance_state("close")
        medium_state = manager.get_instance_state("medium")
        far_state = manager.get_instance_state("far")

        # Close should be highest detail (level 0)
        assert close_state.current_level == 0

        # Far should be lowest detail
        assert far_state.current_level >= medium_state.current_level

    def test_camera_movement(self):
        """Test LOD changes with camera movement."""
        manager = LODManager()

        # Instance at fixed position
        manager.update_instance("inst_001", (0.0, 0.0, -30.0))

        # Camera at origin - distance is 30.0
        manager.set_camera_position((0.0, 0.0, 0.0))
        state = manager.update_instance("inst_001", (0.0, 0.0, -30.0))
        distance1 = state.last_distance

        # Camera moves closer - distance is now 10.0
        manager.set_camera_position((0.0, 0.0, -20.0))
        state = manager.update_instance("inst_001", (0.0, 0.0, -30.0))
        distance2 = state.last_distance

        # Distance should decrease (from 30 to 10)
        assert distance2 < distance1
        assert distance1 == pytest.approx(30.0, rel=0.01)
        assert distance2 == pytest.approx(10.0, rel=0.01)

    def test_different_configs(self):
        """Test using different LOD configs."""
        manager = LODManager()

        # Add custom config
        custom_config = create_lod_config(levels=2, max_distance=50.0)
        manager.set_config("custom", custom_config)

        # Update instances with different configs
        instances = [
            {"instance_id": "default_inst", "position": (0.0, 0.0, -30.0)},
            {"instance_id": "custom_inst", "position": (0.0, 0.0, -30.0)},
        ]

        config_map = {"custom_inst": "custom"}
        manager.update_instances(instances, config_map)

        # Both should have states
        assert manager.get_instance_state("default_inst") is not None
        assert manager.get_instance_state("custom_inst") is not None
