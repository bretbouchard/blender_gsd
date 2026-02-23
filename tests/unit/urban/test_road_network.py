"""
Tests for Road Network Generator

Tests high-level road network generation with presets.
"""

import pytest
from lib.urban.road_network import (
    RoadNetworkPreset,
    ROAD_NETWORK_PRESETS,
    RoadNetworkGenerator,
    generate_grid_network,
    generate_organic_network,
    generate_suburban_network,
    list_network_presets,
    get_network_preset,
)


class TestRoadNetworkPreset:
    """Tests for RoadNetworkPreset dataclass."""

    def test_create_default(self):
        """Test creating RoadNetworkPreset."""
        preset = RoadNetworkPreset(
            name="Test",
            description="Test preset",
            pattern="grid",
            dimensions=(100, 100),
            iterations=2,
            style="modern_urban",
            default_lanes=2,
            has_sidewalks=True,
            has_bike_lanes=True,
        )
        assert preset.name == "Test"
        assert preset.pattern == "grid"
        assert preset.default_lanes == 2


class TestRoadNetworkPresets:
    """Tests for predefined road network presets."""

    def test_presets_exist(self):
        """Test that ROAD_NETWORK_PRESETS is populated."""
        assert isinstance(ROAD_NETWORK_PRESETS, dict)
        assert len(ROAD_NETWORK_PRESETS) > 0

    def test_small_grid_preset(self):
        """Test small grid preset."""
        preset = ROAD_NETWORK_PRESETS.get("small_grid")
        assert preset is not None
        assert preset.pattern == "grid"
        assert preset.dimensions == (200.0, 200.0)

    def test_medium_grid_preset(self):
        """Test medium grid preset."""
        preset = ROAD_NETWORK_PRESETS.get("medium_grid")
        assert preset is not None
        assert preset.iterations == 3

    def test_large_grid_preset(self):
        """Test large grid preset."""
        preset = ROAD_NETWORK_PRESETS.get("large_grid")
        assert preset is not None
        assert preset.dimensions == (800.0, 800.0)

    def test_organic_presets(self):
        """Test organic presets."""
        small = ROAD_NETWORK_PRESETS.get("organic_small")
        large = ROAD_NETWORK_PRESETS.get("organic_large")
        assert small is not None
        assert large is not None
        assert small.pattern == "organic"

    def test_suburban_presets(self):
        """Test suburban presets."""
        small = ROAD_NETWORK_PRESETS.get("suburban_small")
        large = ROAD_NETWORK_PRESETS.get("suburban_large")
        assert small is not None
        assert large is not None
        assert small.style == "suburban"

    def test_highway_preset(self):
        """Test highway preset."""
        preset = ROAD_NETWORK_PRESETS.get("highway_interchange")
        assert preset is not None
        assert preset.pattern == "highway"
        assert preset.has_sidewalks is False

    def test_downtown_preset(self):
        """Test downtown preset."""
        preset = ROAD_NETWORK_PRESETS.get("downtown_core")
        assert preset is not None
        assert preset.style == "downtown"

    def test_village_preset(self):
        """Test village preset."""
        preset = ROAD_NETWORK_PRESETS.get("village")
        assert preset is not None
        assert preset.style == "village"
        assert preset.default_lanes == 1

    def test_industrial_preset(self):
        """Test industrial preset."""
        preset = ROAD_NETWORK_PRESETS.get("industrial_park")
        assert preset is not None
        assert preset.style == "industrial"

    def test_campus_preset(self):
        """Test campus preset."""
        preset = ROAD_NETWORK_PRESETS.get("campus")
        assert preset is not None
        assert preset.style == "campus"


class TestRoadNetworkGenerator:
    """Tests for RoadNetworkGenerator class."""

    def test_init(self):
        """Test RoadNetworkGenerator initialization."""
        generator = RoadNetworkGenerator()
        assert generator is not None

    def test_init_with_seed(self):
        """Test initialization with seed."""
        generator = RoadNetworkGenerator(seed=42)
        assert generator.seed == 42

    def test_generate_preset_small_grid(self):
        """Test generating small grid preset."""
        generator = RoadNetworkGenerator(seed=42)
        network = generator.generate_preset("small_grid")
        assert network is not None
        assert network.style == "american_grid"

    def test_generate_preset_medium_grid(self):
        """Test generating medium grid preset."""
        generator = RoadNetworkGenerator(seed=42)
        network = generator.generate_preset("medium_grid")
        assert network is not None

    def test_generate_preset_organic_small(self):
        """Test generating organic small preset."""
        generator = RoadNetworkGenerator(seed=42)
        network = generator.generate_preset("organic_small")
        assert network is not None
        assert network.style == "european"

    def test_generate_preset_invalid(self):
        """Test generating invalid preset."""
        generator = RoadNetworkGenerator()
        with pytest.raises(ValueError):
            generator.generate_preset("nonexistent_preset")

    def test_generate_custom(self):
        """Test generating custom network."""
        generator = RoadNetworkGenerator(seed=42)
        network = generator.generate_custom(
            dimensions=(150, 150),
            pattern="grid",
            iterations=2,
            style="modern_urban",
            lane_count=2,
        )
        assert network is not None
        assert network.dimensions == (150, 150)
        assert network.style == "modern_urban"

    def test_list_presets(self):
        """Test listing presets."""
        generator = RoadNetworkGenerator()
        presets = generator.list_presets()
        assert isinstance(presets, list)
        assert len(presets) > 0
        assert "small_grid" in presets

    def test_get_preset_info(self):
        """Test getting preset info."""
        generator = RoadNetworkGenerator()
        info = generator.get_preset_info("small_grid")
        assert info["name"] == "Small City Grid"
        assert "dimensions" in info
        assert "pattern" in info

    def test_get_preset_info_invalid(self):
        """Test getting info for invalid preset."""
        generator = RoadNetworkGenerator()
        with pytest.raises(ValueError):
            generator.get_preset_info("nonexistent")


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_grid_network_default(self):
        """Test generating grid network with defaults."""
        network = generate_grid_network()
        assert network is not None

    def test_generate_grid_network_small(self):
        """Test generating small grid network."""
        network = generate_grid_network(size="small")
        assert network is not None

    def test_generate_grid_network_large(self):
        """Test generating large grid network."""
        network = generate_grid_network(size="large", seed=42)
        assert network is not None

    def test_generate_organic_network(self):
        """Test generating organic network."""
        network = generate_organic_network()
        assert network is not None

    def test_generate_organic_network_large(self):
        """Test generating large organic network."""
        network = generate_organic_network(size="large")
        assert network is not None

    def test_generate_suburban_network(self):
        """Test generating suburban network."""
        network = generate_suburban_network()
        assert network is not None

    def test_generate_suburban_network_large(self):
        """Test generating large suburban network."""
        network = generate_suburban_network(size="large", seed=42)
        assert network is not None

    def test_list_network_presets(self):
        """Test listing network presets."""
        presets = list_network_presets()
        assert isinstance(presets, list)
        assert len(presets) > 0

    def test_get_network_preset(self):
        """Test getting network preset."""
        preset = get_network_preset("small_grid")
        assert preset is not None
        assert preset.name == "Small City Grid"

    def test_get_network_preset_invalid(self):
        """Test getting invalid network preset."""
        with pytest.raises(ValueError):
            get_network_preset("nonexistent")


class TestRoadNetworkGeneratorEdgeCases:
    """Edge case tests for RoadNetworkGenerator."""

    def test_custom_zero_dimensions(self):
        """Test custom generation with edge dimensions."""
        generator = RoadNetworkGenerator()
        # Very small dimensions should still work
        network = generator.generate_custom(
            dimensions=(50, 50),
            pattern="grid",
            iterations=1,
        )
        assert network is not None

    def test_custom_high_iterations(self):
        """Test custom generation with high iterations."""
        generator = RoadNetworkGenerator(seed=42)
        network = generator.generate_custom(
            dimensions=(500, 500),
            iterations=4,
        )
        assert network is not None

    def test_custom_high_lane_count(self):
        """Test custom generation with high lane count."""
        generator = RoadNetworkGenerator(seed=42)
        network = generator.generate_custom(
            dimensions=(200, 200),
            lane_count=6,
        )
        assert network is not None
        # Check lane counts were applied
        if network.edges:
            assert network.edges[0].lanes.count == 6

    def test_reproducibility(self):
        """Test that same seed produces same output."""
        net1 = generate_grid_network(seed=12345)
        net2 = generate_grid_network(seed=12345)
        assert len(net1.nodes) == len(net2.nodes)
        assert len(net1.edges) == len(net2.edges)
