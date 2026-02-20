"""
Unit tests for Side-Scroller module
"""

import pytest
import math
from lib.retro.side_scroller import (
    ParallaxLayer,
    SideScrollerCameraConfig,
    create_side_scroller_camera_config,
    get_camera_rotation_for_view,
    calculate_parallax_offset,
    calculate_layer_scroll_speed,
    get_parallax_positions,
    assign_depth_by_z,
    assign_depth_by_name_pattern,
    get_layer_visibility_at_depth,
    calculate_optimal_layer_count,
    generate_layer_depths,
)
from lib.retro.isometric_types import SideScrollerConfig


class TestParallaxLayer:
    """Tests for ParallaxLayer dataclass."""

    def test_default_values(self):
        """Test default values."""
        layer = ParallaxLayer()
        assert layer.index == 0
        assert layer.depth == 1.0
        assert layer.visible is True

    def test_to_dict(self):
        """Test serialization."""
        layer = ParallaxLayer(index=1, name="mid", depth=0.5)
        data = layer.to_dict()
        assert data["index"] == 1
        assert data["name"] == "mid"
        assert data["depth"] == 0.5


class TestSideScrollerCameraConfig:
    """Tests for SideScrollerCameraConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = SideScrollerCameraConfig()
        assert config.name == "SideScrollerCamera"
        assert config.view_direction == "side"
        assert config.orthographic is True

    def test_to_dict(self):
        """Test serialization."""
        config = SideScrollerCameraConfig()
        data = config.to_dict()
        assert data["name"] == "SideScrollerCamera"


class TestCreateSideScrollerCameraConfig:
    """Tests for create_side_scroller_camera_config function."""

    def test_returns_config(self):
        """Test returns config instance."""
        ss_config = SideScrollerConfig()
        cam_config = create_side_scroller_camera_config(ss_config)
        assert isinstance(cam_config, SideScrollerCameraConfig)

    def test_side_view(self):
        """Test side view camera position."""
        ss_config = SideScrollerConfig(view_direction="side")
        cam_config = create_side_scroller_camera_config(ss_config)
        # Side view should have negative Y
        assert cam_config.location[1] < 0

    def test_top_view(self):
        """Test top view camera position."""
        ss_config = SideScrollerConfig(view_direction="top")
        cam_config = create_side_scroller_camera_config(ss_config)
        # Top view should have positive Z
        assert cam_config.location[2] > 0

    def test_front_view(self):
        """Test front view camera position."""
        ss_config = SideScrollerConfig(view_direction="front")
        cam_config = create_side_scroller_camera_config(ss_config)
        # Front view should have negative X
        assert cam_config.location[0] < 0


class TestGetCameraRotationForView:
    """Tests for get_camera_rotation_for_view function."""

    def test_side_rotation(self):
        """Test side view rotation."""
        rotation = get_camera_rotation_for_view("side")
        assert len(rotation) == 3

    def test_top_rotation(self):
        """Test top view rotation."""
        rotation = get_camera_rotation_for_view("top")
        # Top view looks straight down
        assert rotation[0] == 0  # No pitch

    def test_unknown_returns_side(self):
        """Test unknown view returns side rotation."""
        rotation = get_camera_rotation_for_view("unknown")
        side_rotation = get_camera_rotation_for_view("side")
        assert rotation == side_rotation


class TestCalculateParallaxOffset:
    """Tests for calculate_parallax_offset function."""

    def test_no_movement(self):
        """Test no camera movement."""
        offset = calculate_parallax_offset(1.0, 0.0)
        assert offset == 0.0

    def test_depth_1(self):
        """Test depth 1 (full movement)."""
        offset = calculate_parallax_offset(1.0, 10.0)
        assert offset == 10.0

    def test_depth_2(self):
        """Test depth 2 (half movement)."""
        offset = calculate_parallax_offset(2.0, 10.0)
        assert offset == 5.0

    def test_depth_05(self):
        """Test depth 0.5 (double movement)."""
        offset = calculate_parallax_offset(0.5, 10.0)
        assert offset == 20.0


class TestCalculateLayerScrollSpeed:
    """Tests for calculate_layer_scroll_speed function."""

    def test_depth_1(self):
        """Test depth 1 (full speed)."""
        speed = calculate_layer_scroll_speed(1.0, 1.0)
        assert speed == 1.0

    def test_depth_05(self):
        """Test depth 0.5 (half speed)."""
        speed = calculate_layer_scroll_speed(0.5, 1.0)
        assert speed == 0.5

    def test_base_speed(self):
        """Test base speed affects result."""
        speed1 = calculate_layer_scroll_speed(1.0, 1.0)
        speed2 = calculate_layer_scroll_speed(1.0, 2.0)
        assert speed2 == speed1 * 2


class TestGetParallaxPositions:
    """Tests for get_parallax_positions function."""

    def test_returns_dict(self):
        """Test returns dict."""
        layers = [ParallaxLayer(name="bg", depth=0.5)]
        positions = get_parallax_positions(layers, 0.0, 0, 10)
        assert isinstance(positions, dict)
        assert "bg" in positions

    def test_different_depths_different_speeds(self):
        """Test different depths produce different offsets."""
        layers = [
            ParallaxLayer(name="far", depth=0.5),
            ParallaxLayer(name="near", depth=2.0),
        ]
        positions = get_parallax_positions(layers, 10.0, 0, 10)
        # Far layer should have larger offset (moves faster visually)
        assert positions["far"] > positions["near"]


class TestAssignDepthByZ:
    """Tests for assign_depth_by_z function."""

    def test_empty_list(self):
        """Test empty list returns empty dict."""
        result = assign_depth_by_z([], SideScrollerConfig())
        assert result == {}

    def test_assigns_based_on_z(self):
        """Test assigns based on Z position."""
        class MockObj:
            def __init__(self, name, z):
                self.name = name
                self.location = type('Location', (), {'z': z})()

        config = SideScrollerConfig(parallax_layers=3)
        objects = [
            MockObj("low", 0),
            MockObj("high", 10),
        ]
        result = assign_depth_by_z(objects, config)
        assert "low" in result
        assert "high" in result


class TestAssignDepthByNamePattern:
    """Tests for assign_depth_by_name_pattern function."""

    def test_empty_list(self):
        """Test empty list returns empty dict."""
        result = assign_depth_by_name_pattern([], {"bg": 0})
        assert result == {}

    def test_matches_pattern(self):
        """Test matches name patterns."""
        class MockObj:
            def __init__(self, name):
                self.name = name

        objects = [
            MockObj("background_sky"),
            MockObj("foreground_tree"),
        ]
        patterns = {"background": 0, "foreground": 2}
        result = assign_depth_by_name_pattern(objects, patterns)
        assert result["background_sky"] == 0
        assert result["foreground_tree"] == 2

    def test_case_insensitive(self):
        """Test pattern matching is case insensitive."""
        class MockObj:
            def __init__(self, name):
                self.name = name

        objects = [MockObj("BACKGROUND_SKY")]
        patterns = {"background": 0}
        result = assign_depth_by_name_pattern(objects, patterns)
        assert result["BACKGROUND_SKY"] == 0


class TestGetLayerVisibilityAtDepth:
    """Tests for get_layer_visibility_at_depth function."""

    def test_visible_in_range(self):
        """Test visible when in clipping range."""
        visible = get_layer_visibility_at_depth(5.0, 0.0, 0.1, 100.0)
        assert visible is True

    def test_hidden_too_close(self):
        """Test hidden when too close."""
        visible = get_layer_visibility_at_depth(0.05, 0.0, 0.1, 100.0)
        assert visible is False

    def test_hidden_too_far(self):
        """Test hidden when too far."""
        visible = get_layer_visibility_at_depth(200.0, 0.0, 0.1, 100.0)
        assert visible is False


class TestCalculateOptimalLayerCount:
    """Tests for calculate_optimal_layer_count function."""

    def test_minimum_2(self):
        """Test minimum is 2 layers."""
        count = calculate_optimal_layer_count(0.5)
        assert count >= 2

    def test_maximum_8(self):
        """Test maximum is 8 layers."""
        count = calculate_optimal_layer_count(100.0, 0.1)
        assert count <= 8

    def test_depth_affects_count(self):
        """Test depth affects layer count."""
        count1 = calculate_optimal_layer_count(5.0)
        count2 = calculate_optimal_layer_count(20.0)
        assert count2 >= count1


class TestGenerateLayerDepths:
    """Tests for generate_layer_depths function."""

    def test_linear(self):
        """Test linear distribution."""
        depths = generate_layer_depths(4, "linear")
        assert len(depths) == 4
        # Linear: 1/1, 1/2, 1/3, 1/4
        assert depths[0] == 1.0

    def test_exponential(self):
        """Test exponential distribution."""
        depths = generate_layer_depths(4, "exponential")
        assert len(depths) == 4
        # Exponential: 0.5^0, 0.5^1, 0.5^2, 0.5^3
        assert depths[0] == 1.0
        assert depths[1] == 0.5

    def test_uniform(self):
        """Test uniform distribution."""
        depths = generate_layer_depths(4, "uniform")
        assert len(depths) == 4
        # Uniform: 1/4, 2/4, 3/4, 4/4
        assert depths[-1] == 1.0

    def test_unknown_returns_linear(self):
        """Test unknown distribution returns linear."""
        depths = generate_layer_depths(4, "unknown")
        linear_depths = generate_layer_depths(4, "linear")
        assert depths == linear_depths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
