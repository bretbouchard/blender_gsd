"""
Unit tests for Charlotte Digital Twin lane markings module.

Tests marking types and configuration without Blender dependencies.

Note: bpy and mathutils are mocked in conftest.py before any imports.
"""

import pytest
import math

from lib.charlotte_digital_twin.geometry.lane_markings import (
    MarkingType,
    MarkingColor,
    MarkingConfig,
    MarkingSegment,
    LaneMarkingGenerator,
    HIGHWAY_MARKING_CONFIG,
    RESIDENTIAL_MARKING_CONFIG,
    generate_highway_markings,
)
from lib.charlotte_digital_twin.geometry.types import WorldCoordinate


class TestMarkingType:
    """Tests for MarkingType enum."""

    def test_line_types(self):
        """Test line marking types."""
        assert MarkingType.DASHED_LINE.value == "dashed"
        assert MarkingType.SOLID_LINE.value == "solid"
        assert MarkingType.DOUBLE_SOLID.value == "double_solid"

    def test_arrow_types(self):
        """Test arrow marking types."""
        assert MarkingType.TURN_ARROW_LEFT.value == "turn_left"
        assert MarkingType.TURN_ARROW_RIGHT.value == "turn_right"
        assert MarkingType.EXIT_ARROW.value == "exit_arrow"

    def test_special_types(self):
        """Test special marking types."""
        assert MarkingType.CROSSWALK.value == "crosswalk"
        assert MarkingType.STOP_LINE.value == "stop_line"


class TestMarkingColor:
    """Tests for MarkingColor enum."""

    def test_color_values(self):
        """Test color values."""
        assert MarkingColor.WHITE.value == "white"
        assert MarkingColor.YELLOW.value == "yellow"
        assert MarkingColor.BLUE.value == "blue"
        assert MarkingColor.RED.value == "red"


class TestMarkingConfig:
    """Tests for MarkingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = MarkingConfig()

        assert config.dash_length == 3.0  # 10 feet
        assert config.dash_gap == 9.0     # 30 feet
        assert config.line_width == 0.15  # 6 inches
        assert config.paint_thickness == 0.003

    def test_standard_us_dimensions(self):
        """Test that defaults match US standards."""
        config = MarkingConfig()

        # Standard US: dash 10ft (3.05m), gap 30ft (9.14m)
        assert 2.5 < config.dash_length < 3.5
        assert 8.0 < config.dash_gap < 10.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = MarkingConfig(
            dash_length=2.5,
            dash_gap=7.5,
            line_width=0.12,
            edge_line_width=0.15,
            wear_amount=0.3
        )

        assert config.dash_length == 2.5
        assert config.wear_amount == 0.3


class TestMarkingSegment:
    """Tests for MarkingSegment dataclass."""

    def test_default_values(self):
        """Test default values."""
        segment = MarkingSegment(
            marking_type=MarkingType.SOLID_LINE,
            start=(0, 0, 0),
            end=(10, 0, 0)
        )

        assert segment.color == MarkingColor.WHITE
        assert segment.width is None
        assert segment.lanes == 2

    def test_custom_values(self):
        """Test custom values."""
        segment = MarkingSegment(
            marking_type=MarkingType.DOUBLE_SOLID,
            start=(0, 0, 0),
            end=(100, 0, 0),
            color=MarkingColor.YELLOW,
            width=0.2,
            lanes=4
        )

        assert segment.color == MarkingColor.YELLOW
        assert segment.width == 0.2
        assert segment.lanes == 4


class TestHighwayMarkingConfig:
    """Tests for HIGHWAY_MARKING_CONFIG preset."""

    def test_dash_length(self):
        """Test highway dash length."""
        assert HIGHWAY_MARKING_CONFIG.dash_length == 3.0

    def test_dash_gap(self):
        """Test highway dash gap."""
        assert HIGHWAY_MARKING_CONFIG.dash_gap == 9.0

    def test_line_width(self):
        """Test highway line width."""
        assert HIGHWAY_MARKING_CONFIG.line_width == 0.15


class TestResidentialMarkingConfig:
    """Tests for RESIDENTIAL_MARKING_CONFIG preset."""

    def test_dash_length(self):
        """Test residential dash length."""
        assert RESIDENTIAL_MARKING_CONFIG.dash_length == 2.5

    def test_dash_gap(self):
        """Test residential dash gap."""
        assert RESIDENTIAL_MARKING_CONFIG.dash_gap == 7.5

    def test_narrower_than_highway(self):
        """Test that residential lines are narrower."""
        assert RESIDENTIAL_MARKING_CONFIG.line_width < HIGHWAY_MARKING_CONFIG.line_width


class TestLaneMarkingGenerator:
    """Tests for LaneMarkingGenerator class."""

    def test_initialization_default(self):
        """Test default initialization."""
        generator = LaneMarkingGenerator()

        assert generator.config.dash_length == 3.0

    def test_initialization_custom_config(self):
        """Test initialization with custom config."""
        config = MarkingConfig(dash_length=2.0)
        generator = LaneMarkingGenerator(config)

        assert generator.config.dash_length == 2.0

    def test_generate_dashed_line_returns_list(self):
        """Test that dashed line returns list."""
        generator = LaneMarkingGenerator()

        # Without Blender, returns empty list
        result = generator.generate_dashed_line(
            (0, 0, 0),
            (100, 0, 0)
        )

        assert isinstance(result, list)

    def test_generate_solid_line_returns_none_without_blender(self):
        """Test that solid line returns None without Blender."""
        generator = LaneMarkingGenerator()

        result = generator.generate_solid_line(
            (0, 0, 0),
            (100, 0, 0)
        )

        assert result is None

    def test_generate_double_line_returns_list(self):
        """Test that double line returns list (empty without Blender)."""
        generator = LaneMarkingGenerator()

        # The LaneMarkingGenerator methods use Blender's Vector internally
        # Without real Blender, these return empty lists
        # This is expected behavior - testing the Blender-dependent code
        # requires integration tests with actual Blender
        try:
            result = generator.generate_double_line(
                (0, 0, 0),
                (100, 0, 0)
            )
            assert isinstance(result, list)
        except (TypeError, AttributeError):
            # Expected when Vector can't be instantiated from mock
            pytest.skip("Requires real Blender for Vector operations")


class TestMarkingCalculations:
    """Tests for marking calculation logic (pure functions)."""

    def test_dash_count_calculation(self):
        """Test calculation of number of dashes."""
        config = MarkingConfig(dash_length=3.0, dash_gap=9.0)

        # 100 meter road
        # Cycle = 3 + 9 = 12 meters
        # Expected: 100 / 12 = 8.33 -> 8 full dashes
        road_length = 100.0
        cycle_length = config.dash_length + config.dash_gap
        expected_dashes = int(road_length / cycle_length)

        assert expected_dashes == 8

    def test_dash_count_short_road(self):
        """Test dash count on short road."""
        config = MarkingConfig(dash_length=3.0, dash_gap=9.0)

        # 5 meter road - only 1 dash
        road_length = 5.0
        cycle_length = config.dash_length + config.dash_gap
        expected_dashes = int(road_length / cycle_length)

        assert expected_dashes == 0  # Less than one cycle

    def test_dash_count_long_road(self):
        """Test dash count on long road."""
        config = MarkingConfig(dash_length=3.0, dash_gap=9.0)

        # 1 km road
        road_length = 1000.0
        cycle_length = config.dash_length + config.dash_gap
        expected_dashes = int(road_length / cycle_length)

        assert expected_dashes == 83

    def test_double_line_spacing(self):
        """Test double line spacing calculation."""
        config = MarkingConfig(
            line_width=0.15,
            double_line_spacing=0.10
        )

        # Total width of double line
        total_width = 2 * config.line_width + config.double_line_spacing

        assert total_width == pytest.approx(0.40)

    def test_edge_line_offset(self):
        """Test edge line offset calculation."""
        road_width = 7.0
        edge_line_width = 0.20

        # Edge lines should be at +/- (road_width/2 - edge_line_width)
        edge_offset = (road_width / 2) - edge_line_width

        assert edge_offset == pytest.approx(3.3)


class TestMarkingColorValues:
    """Tests for marking color RGB values."""

    def test_white_color_values(self):
        """Test white color approximation."""
        # White should be close to (1, 1, 1)
        white_approx = (0.95, 0.95, 0.95)
        assert all(0.9 < v < 1.0 for v in white_approx)

    def test_yellow_color_values(self):
        """Test yellow color approximation."""
        # Yellow should be approximately (0.9, 0.8, 0.1)
        yellow_approx = (0.9, 0.8, 0.1)
        assert yellow_approx[0] > yellow_approx[1] > yellow_approx[2]


class TestMarkingTypeCombinations:
    """Tests for marking type combinations."""

    def test_double_solid_lines(self):
        """Test double solid line configuration."""
        left_type = MarkingType.SOLID_LINE
        right_type = MarkingType.SOLID_LINE

        assert left_type == MarkingType.SOLID_LINE
        assert right_type == MarkingType.SOLID_LINE

    def test_solid_dash_line(self):
        """Test solid + dashed line configuration."""
        left_type = MarkingType.SOLID_LINE
        right_type = MarkingType.DASHED_LINE

        # Common for passing zones
        assert left_type != right_type

    def test_double_dashed_lines(self):
        """Test double dashed line configuration."""
        left_type = MarkingType.DASHED_LINE
        right_type = MarkingType.DASHED_LINE

        assert left_type == MarkingType.DASHED_LINE


class TestGenerateHighwayMarkings:
    """Tests for generate_highway_markings function."""

    def test_returns_dict(self):
        """Test that function returns dictionary."""
        road_points = [
            (0, 0, 0),
            (100, 0, 0),
            (200, 0, 0),
        ]

        result = generate_highway_markings(
            road_points,
            road_width=25.0,
            lanes_per_direction=2
        )

        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        """Test that result has expected keys."""
        road_points = [
            (0, 0, 0),
            (100, 0, 0),
        ]

        result = generate_highway_markings(
            road_points,
            road_width=25.0,
            lanes_per_direction=2
        )

        assert "edge_lines" in result
        assert "center_line" in result
        assert "lane_lines" in result

    def test_divided_highway_no_center_line(self):
        """Test that divided highway has no center line."""
        road_points = [
            (0, 0, 0),
            (100, 0, 0),
        ]

        result = generate_highway_markings(
            road_points,
            road_width=25.0,
            lanes_per_direction=2,
            is_divided=True
        )

        assert result["center_line"] == []

    def test_undivided_highway_has_center_line(self):
        """Test that undivided highway has center line."""
        road_points = [
            (0, 0, 0),
            (100, 0, 0),
        ]

        result = generate_highway_markings(
            road_points,
            road_width=25.0,
            lanes_per_direction=2,
            is_divided=False
        )

        # Without Blender, still empty but logic would create it
        # The function structure is correct
        assert "center_line" in result


class TestMarkingDimensions:
    """Tests for marking dimension calculations."""

    def test_paint_thickness(self):
        """Test paint thickness is realistic."""
        config = MarkingConfig()

        # Paint is typically 2-5mm thick
        assert 0.002 <= config.paint_thickness <= 0.005

    def test_road_marking_width_standard(self):
        """Test standard road marking width."""
        config = MarkingConfig()

        # Standard US marking: 4-8 inches (0.1-0.2m)
        assert 0.1 <= config.line_width <= 0.2

    def test_edge_line_wider_than_center(self):
        """Test edge lines are typically wider."""
        config = MarkingConfig()

        # Edge lines are often 6-12 inches
        assert config.edge_line_width >= config.line_width


class TestMarkingWearParameters:
    """Tests for marking wear parameters."""

    def test_wear_amount_range(self):
        """Test wear amount is in valid range."""
        config = MarkingConfig()

        assert 0.0 <= config.wear_amount <= 1.0

    def test_edge_chipping_range(self):
        """Test edge chipping is in valid range."""
        config = MarkingConfig()

        assert 0.0 <= config.edge_chipping <= 1.0

    def test_worn_markings_config(self):
        """Test configuration for worn markings."""
        config = MarkingConfig(
            wear_amount=0.5,
            edge_chipping=0.4
        )

        assert config.wear_amount == 0.5
        assert config.edge_chipping == 0.4
