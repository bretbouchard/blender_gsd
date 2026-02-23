"""
Unit tests for Charlotte Digital Twin scale module.

Tests scale management and unit conversion without Blender dependencies.

Note: bpy and mathutils are mocked in conftest.py before any imports.
"""

import pytest

from lib.charlotte_digital_twin.geometry.scale import (
    ScalePreset,
    ScaleConfig,
    ScaleManager,
    ROAD_WIDTHS_METERS,
    BUILDING_HEIGHTS_METERS,
    CHARLOTTE_BUILDING_HEIGHTS,
)


class TestScalePreset:
    """Tests for ScalePreset enum."""

    def test_preset_values(self):
        """Test scale preset values."""
        assert ScalePreset.REALISTIC.value == "realistic"
        assert ScalePreset.HALF.value == "half"
        assert ScalePreset.DOUBLE.value == "double"
        assert ScalePreset.DECIMETER.value == "decimeter"
        assert ScalePreset.CENTIMETER.value == "centimeter"
        assert ScalePreset.KILOMETER.value == "kilometer"


class TestScaleConfig:
    """Tests for ScaleConfig dataclass."""

    def test_default_values(self):
        """Test default configuration."""
        config = ScaleConfig()

        assert config.meters_per_blender_unit == 1.0
        assert config.name == "Realistic"
        assert "1 meter" in config.description

    def test_from_preset_realistic(self):
        """Test creating config from REALISTIC preset."""
        config = ScaleConfig.from_preset(ScalePreset.REALISTIC)

        assert config.meters_per_blender_unit == 1.0
        assert config.name == "Realistic"

    def test_from_preset_half(self):
        """Test creating config from HALF preset."""
        config = ScaleConfig.from_preset(ScalePreset.HALF)

        assert config.meters_per_blender_unit == 2.0
        assert "Half" in config.name

    def test_from_preset_double(self):
        """Test creating config from DOUBLE preset."""
        config = ScaleConfig.from_preset(ScalePreset.DOUBLE)

        assert config.meters_per_blender_unit == 0.5
        assert "Double" in config.name

    def test_from_preset_decimeter(self):
        """Test creating config from DECIMETER preset."""
        config = ScaleConfig.from_preset(ScalePreset.DECIMETER)

        assert config.meters_per_blender_unit == 0.1

    def test_from_preset_centimeter(self):
        """Test creating config from CENTIMETER preset."""
        config = ScaleConfig.from_preset(ScalePreset.CENTIMETER)

        assert config.meters_per_blender_unit == 0.01

    def test_from_preset_kilometer(self):
        """Test creating config from KILOMETER preset."""
        config = ScaleConfig.from_preset(ScalePreset.KILOMETER)

        assert config.meters_per_blender_unit == 1000.0


class TestScaleManager:
    """Tests for ScaleManager class."""

    def test_default_initialization(self):
        """Test default initialization."""
        manager = ScaleManager()

        assert manager.scale == 1.0
        assert manager.blender_units_per_meter == 1.0

    def test_initialization_with_preset(self):
        """Test initialization with preset."""
        manager = ScaleManager(ScalePreset.DOUBLE)

        assert manager.scale == 0.5
        assert manager.blender_units_per_meter == 2.0

    def test_set_scale(self):
        """Test changing scale."""
        manager = ScaleManager()
        manager.set_scale(ScalePreset.HALF)

        assert manager.scale == 2.0

    def test_meters_to_blender_realistic(self):
        """Test meters to Blender conversion with realistic scale."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        assert manager.meters_to_blender(10.0) == 10.0
        assert manager.meters_to_blender(100.0) == 100.0

    def test_meters_to_blender_half(self):
        """Test meters to Blender conversion with half scale."""
        manager = ScaleManager(ScalePreset.HALF)

        assert manager.meters_to_blender(10.0) == 5.0
        assert manager.meters_to_blender(100.0) == 50.0

    def test_meters_to_blender_double(self):
        """Test meters to Blender conversion with double scale."""
        manager = ScaleManager(ScalePreset.DOUBLE)

        assert manager.meters_to_blender(10.0) == 20.0
        assert manager.meters_to_blender(100.0) == 200.0

    def test_meters_to_blender_kilometer(self):
        """Test meters to Blender conversion with kilometer scale."""
        manager = ScaleManager(ScalePreset.KILOMETER)

        assert manager.meters_to_blender(1000.0) == 1.0
        assert manager.meters_to_blender(5000.0) == 5.0

    def test_blender_to_meters_realistic(self):
        """Test Blender to meters conversion with realistic scale."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        assert manager.blender_to_meters(10.0) == 10.0
        assert manager.blender_to_meters(100.0) == 100.0

    def test_blender_to_meters_half(self):
        """Test Blender to meters conversion with half scale."""
        manager = ScaleManager(ScalePreset.HALF)

        assert manager.blender_to_meters(5.0) == 10.0
        assert manager.blender_to_meters(50.0) == 100.0

    def test_blender_to_meters_double(self):
        """Test Blender to meters conversion with double scale."""
        manager = ScaleManager(ScalePreset.DOUBLE)

        assert manager.blender_to_meters(20.0) == 10.0
        assert manager.blender_to_meters(200.0) == 100.0

    def test_kilometers_to_blender(self):
        """Test kilometers to Blender conversion."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        assert manager.kilometers_to_blender(1.0) == 1000.0
        assert manager.kilometers_to_blender(5.0) == 5000.0

    def test_blender_to_kilometers(self):
        """Test Blender to kilometers conversion."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        assert manager.blender_to_kilometers(1000.0) == 1.0
        assert manager.blender_to_kilometers(5000.0) == 5.0

    def test_feet_to_blender(self):
        """Test feet to Blender conversion."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        # 1 foot = 0.3048 meters
        result = manager.feet_to_blender(1.0)
        assert result == pytest.approx(0.3048)

    def test_blender_to_feet(self):
        """Test Blender to feet conversion."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        result = manager.blender_to_feet(0.3048)
        assert result == pytest.approx(1.0)

    def test_scale_vector(self):
        """Test scaling a 3D vector."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        result = manager.scale_vector(10.0, 20.0, 30.0)

        assert result == (10.0, 20.0, 30.0)

    def test_scale_vector_half(self):
        """Test scaling vector with half scale."""
        manager = ScaleManager(ScalePreset.HALF)

        result = manager.scale_vector(10.0, 20.0, 30.0)

        assert result == (5.0, 10.0, 15.0)

    def test_scale_vector_double(self):
        """Test scaling vector with double scale."""
        manager = ScaleManager(ScalePreset.DOUBLE)

        result = manager.scale_vector(10.0, 20.0, 30.0)

        assert result == (20.0, 40.0, 60.0)

    def test_get_blender_unit_settings_realistic(self):
        """Test Blender unit settings for realistic scale."""
        manager = ScaleManager(ScalePreset.REALISTIC)
        settings = manager.get_blender_unit_settings()

        assert settings["system"] == "METRIC"
        assert settings["scale_length"] == 1.0
        assert settings["length_unit"] == "METERS"

    def test_get_blender_unit_settings_half(self):
        """Test Blender unit settings for half scale."""
        manager = ScaleManager(ScalePreset.HALF)
        settings = manager.get_blender_unit_settings()

        assert settings["scale_length"] == 0.5

    def test_get_blender_unit_settings_double(self):
        """Test Blender unit settings for double scale."""
        manager = ScaleManager(ScalePreset.DOUBLE)
        settings = manager.get_blender_unit_settings()

        assert settings["scale_length"] == 2.0

    def test_get_blender_unit_settings_kilometer(self):
        """Test Blender unit settings for kilometer scale."""
        manager = ScaleManager(ScalePreset.KILOMETER)
        settings = manager.get_blender_unit_settings()

        assert settings["scale_length"] == 1000.0
        assert settings["length_unit"] == "KILOMETERS"

    def test_roundtrip_conversion(self):
        """Test that roundtrip conversion is accurate."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        original = 123.456
        blender = manager.meters_to_blender(original)
        back = manager.blender_to_meters(blender)

        assert back == pytest.approx(original)

    def test_roundtrip_conversion_all_presets(self):
        """Test roundtrip conversion for all presets."""
        original = 100.0

        for preset in ScalePreset:
            manager = ScaleManager(preset)
            blender = manager.meters_to_blender(original)
            back = manager.blender_to_meters(blender)

            assert back == pytest.approx(original), f"Failed for {preset}"


class TestRoadWidthsMeters:
    """Tests for ROAD_WIDTHS_METERS constant."""

    def test_has_motorway_lane(self):
        """Test motorway lane width."""
        assert "motorway_lane" in ROAD_WIDTHS_METERS
        assert ROAD_WIDTHS_METERS["motorway_lane"] == 3.75

    def test_has_highway_lane(self):
        """Test highway lane width."""
        assert "highway_lane" in ROAD_WIDTHS_METERS
        assert ROAD_WIDTHS_METERS["highway_lane"] == 3.5

    def test_has_sidewalk(self):
        """Test sidewalk width."""
        assert "sidewalk" in ROAD_WIDTHS_METERS
        assert ROAD_WIDTHS_METERS["sidewalk"] == 1.5

    def test_all_widths_positive(self):
        """Test all widths are positive."""
        for name, width in ROAD_WIDTHS_METERS.items():
            assert width > 0, f"Width for {name} should be positive"

    def test_motorway_wider_than_urban(self):
        """Test that motorway lanes are wider than urban."""
        assert ROAD_WIDTHS_METERS["motorway_lane"] > ROAD_WIDTHS_METERS["urban_lane"]


class TestBuildingHeightsMeters:
    """Tests for BUILDING_HEIGHTS_METERS constant."""

    def test_has_floor_heights(self):
        """Test floor height values."""
        assert "single_story" in BUILDING_HEIGHTS_METERS
        assert "two_story" in BUILDING_HEIGHTS_METERS
        assert "three_story" in BUILDING_HEIGHTS_METERS

    def test_has_floor_height_average(self):
        """Test average floor height."""
        assert "floor_height" in BUILDING_HEIGHTS_METERS
        assert BUILDING_HEIGHTS_METERS["floor_height"] == 3.5

    def test_has_office_floor(self):
        """Test office floor height."""
        assert "office_floor" in BUILDING_HEIGHTS_METERS
        assert BUILDING_HEIGHTS_METERS["office_floor"] == 4.0

    def test_floor_progression(self):
        """Test floor height progression."""
        single = BUILDING_HEIGHTS_METERS["single_story"]
        double = BUILDING_HEIGHTS_METERS["two_story"]
        triple = BUILDING_HEIGHTS_METERS["three_story"]

        assert double == pytest.approx(single * 2)
        assert triple == pytest.approx(single * 3)

    def test_office_taller_than_residential(self):
        """Test that office floors are taller than residential."""
        assert BUILDING_HEIGHTS_METERS["office_floor"] > BUILDING_HEIGHTS_METERS["residential_floor"]


class TestCharlotteBuildingHeights:
    """Tests for CHARLOTTE_BUILDING_HEIGHTS constant."""

    def test_has_bank_of_america(self):
        """Test Bank of America Corporate Center height."""
        assert "bank_of_america_corporate_center" in CHARLOTTE_BUILDING_HEIGHTS
        assert CHARLOTTE_BUILDING_HEIGHTS["bank_of_america_corporate_center"] == 312.0

    def test_has_duke_energy(self):
        """Test Duke Energy Center height."""
        assert "duke_energy_center" in CHARLOTTE_BUILDING_HEIGHTS
        assert CHARLOTTE_BUILDING_HEIGHTS["duke_energy_center"] == 240.0

    def test_has_wells_fargo(self):
        """Test Wells Fargo Capital Center height."""
        assert "wells_fargo_capital_center" in CHARLOTTE_BUILDING_HEIGHTS

    def test_has_stadium(self):
        """Test Bank of America Stadium height."""
        assert "bank_of_america_stadium" in CHARLOTTE_BUILDING_HEIGHTS

    def test_tallest_is_boa(self):
        """Test that BoA Corporate Center is tallest."""
        boa = CHARLOTTE_BUILDING_HEIGHTS["bank_of_america_corporate_center"]
        for name, height in CHARLOTTE_BUILDING_HEIGHTS.items():
            assert height <= boa, f"{name} should not be taller than BoA"

    def test_all_heights_positive(self):
        """Test all heights are positive."""
        for name, height in CHARLOTTE_BUILDING_HEIGHTS.items():
            assert height > 0, f"Height for {name} should be positive"


class TestScaleManagerIntegration:
    """Integration tests for ScaleManager with real-world values."""

    def test_road_width_conversion(self):
        """Test converting road widths."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        # Standard US highway lane: 12 feet = 3.658 meters
        lane_width_m = 3.658
        lane_width_bu = manager.meters_to_blender(lane_width_m)

        assert lane_width_bu == pytest.approx(3.658)

    def test_building_height_conversion(self):
        """Test converting building heights."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        # BoA tower: 312 meters
        height_m = CHARLOTTE_BUILDING_HEIGHTS["bank_of_america_corporate_center"]
        height_bu = manager.meters_to_blender(height_m)

        assert height_bu == 312.0

    def test_city_block_conversion(self):
        """Test converting city block sizes."""
        manager = ScaleManager(ScalePreset.REALISTIC)

        # Typical Charlotte block: ~100m x 100m
        block_size = 100.0
        block_bu = manager.meters_to_blender(block_size)

        assert block_bu == 100.0

    def test_scale_for_large_scenes(self):
        """Test using kilometer scale for large scenes."""
        manager = ScaleManager(ScalePreset.KILOMETER)

        # 10 km road
        road_km = 10.0
        road_bu = manager.kilometers_to_blender(road_km)

        assert road_bu == 10.0

    def test_scale_for_detail_work(self):
        """Test using centimeter scale for detail work."""
        manager = ScaleManager(ScalePreset.CENTIMETER)

        # 5 cm detail
        detail_m = 0.05
        detail_bu = manager.meters_to_blender(detail_m)

        assert detail_bu == 5.0
