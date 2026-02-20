"""
Unit tests for Lighting System Module

Tests for lib/cinematic/lighting.py - Light creation, configuration, and management.
All tests run without Blender (mocked) for CI compatibility.
"""

import pytest
import math
from dataclasses import asdict
from unittest.mock import patch, MagicMock

from lib.cinematic.lighting import (
    create_light,
    create_area_light,
    create_spot_light,
    create_point_light,
    create_sun_light,
    setup_light_linking,
    delete_light,
    list_lights,
    get_light,
    set_light_intensity,
    set_light_color,
    set_light_temperature,
    apply_lighting_rig,
    _validate_area_shape,
    _build_light_config,
    _load_preset_with_inheritance,
    AREA_SHAPES,
    BLENDER_AVAILABLE,
    BLENDER_40_MIN,
)
from lib.cinematic.types import LightConfig, Transform3D


class TestValidateAreaShape:
    """Tests for area light shape validation."""

    def test_valid_shapes(self):
        """Test that valid shapes pass validation."""
        for shape in AREA_SHAPES:
            assert _validate_area_shape(shape) is True
            assert _validate_area_shape(shape.lower()) is True

    def test_invalid_shape(self):
        """Test that invalid shapes raise ValueError."""
        with pytest.raises(ValueError, match="Invalid area light shape"):
            _validate_area_shape("TRIANGLE")

        with pytest.raises(ValueError, match="Invalid area light shape"):
            _validate_area_shape("star")

    def test_case_insensitive(self):
        """Test that shape validation is case insensitive."""
        assert _validate_area_shape("rectangle") is True
        assert _validate_area_shape("RECTANGLE") is True
        assert _validate_area_shape("Rectangle") is True


class TestCreateLight:
    """Tests for create_light function."""

    def test_create_area_light_config(self):
        """Test creating area light from config."""
        config = LightConfig(
            name="test_area",
            light_type="area",
            intensity=1000.0,
            color=(1.0, 0.9, 0.8),
            transform=Transform3D(
                position=(1.0, 2.0, 3.0),
                rotation=(45.0, 0.0, 0.0)
            ),
            shape="RECTANGLE",
            size=2.0,
            size_y=1.0
        )

        # When Blender not available, returns None
        result = create_light(config)
        assert result is None

    def test_create_spot_light_config(self):
        """Test creating spot light from config."""
        config = LightConfig(
            name="test_spot",
            light_type="spot",
            intensity=2000.0,
            spot_size=0.785,  # 45 degrees
            spot_blend=0.5
        )

        result = create_light(config)
        assert result is None  # Blender not available

    def test_create_point_light_config(self):
        """Test creating point light from config."""
        config = LightConfig(
            name="test_point",
            light_type="point",
            intensity=500.0,
            shadow_soft_size=0.2
        )

        result = create_light(config)
        assert result is None  # Blender not available

    def test_create_sun_light_config(self):
        """Test creating sun light from config."""
        config = LightConfig(
            name="test_sun",
            light_type="sun",
            intensity=1.0,
            transform=Transform3D(
                rotation=(45.0, 0.0, 90.0)
            )
        )

        result = create_light(config)
        assert result is None  # Blender not available


class TestConvenienceFunctions:
    """Tests for convenience light creation functions."""

    def test_create_area_light_default(self):
        """Test area light with default parameters."""
        result = create_area_light(
            name="test_light",
            position=(0, 0, 2),
            size=1.0
        )
        assert result is None  # Blender not available

    def test_create_area_light_rectangle(self):
        """Test rectangular area light."""
        result = create_area_light(
            name="rect_light",
            position=(0, 0, 2),
            size=2.0,
            shape="RECTANGLE",
            size_y=1.0
        )
        assert result is None

    def test_create_spot_light_degrees(self):
        """Test spot light with degrees conversion."""
        result = create_spot_light(
            name="spot_light",
            position=(0, -2, 2),
            spot_size=45.0,  # degrees
            spot_blend=0.5
        )
        assert result is None

    def test_create_point_light(self):
        """Test point light creation."""
        result = create_point_light(
            name="point_light",
            position=(1, 1, 1),
            intensity=800.0
        )
        assert result is None

    def test_create_sun_light(self):
        """Test sun light creation."""
        result = create_sun_light(
            name="sun_light",
            rotation=(45, 0, 0)
        )
        assert result is None

    def test_create_area_light_with_temperature(self):
        """Test area light with color temperature."""
        result = create_area_light(
            name="warm_light",
            position=(0, 0, 2),
            size=1.0,
            use_temperature=True,
            temperature=3200.0
        )
        assert result is None


class TestLightLinking:
    """Tests for light linking functionality."""

    def test_setup_light_linking_basic(self):
        """Test basic light linking setup."""
        result = setup_light_linking(
            "test_light",
            ["object1", "object2"]
        )
        assert result is False  # Blender not available

    def test_setup_light_linking_with_blockers(self):
        """Test light linking with blocker objects."""
        result = setup_light_linking(
            "test_light",
            ["object1"],
            blocker_objects=["blocker1"]
        )
        assert result is False


class TestLightManagement:
    """Tests for light management functions."""

    def test_delete_light(self):
        """Test deleting a light."""
        result = delete_light("nonexistent_light")
        assert result is False  # Blender not available

    def test_list_lights(self):
        """Test listing lights."""
        result = list_lights()
        assert result == []  # Blender not available, empty list

    def test_get_light(self):
        """Test getting a light by name."""
        result = get_light("test_light")
        assert result is None  # Blender not available

    def test_set_light_intensity(self):
        """Test setting light intensity."""
        result = set_light_intensity("test_light", 1500.0)
        assert result is False

    def test_set_light_color(self):
        """Test setting light color."""
        result = set_light_color("test_light", (1.0, 0.5, 0.0))
        assert result is False

    def test_set_light_temperature(self):
        """Test setting light temperature."""
        result = set_light_temperature("test_light", 4000.0)
        assert result is False


class TestApplyLightingRig:
    """Tests for apply_lighting_rig function."""

    def test_apply_rig_blender_unavailable(self):
        """Test that apply_lighting_rig handles missing Blender gracefully."""
        result = apply_lighting_rig("three_point_soft")
        assert result == {
            "preset_name": "three_point_soft",
            "lights_created": [],
            "light_objects": {},
            "total_lights": 0
        }

    def test_apply_rig_with_target_position(self):
        """Test applying rig with custom target position."""
        result = apply_lighting_rig(
            "three_point_soft",
            target_position=(0, 0, 1.0)
        )
        assert result["total_lights"] == 0

    def test_apply_rig_with_intensity_scale(self):
        """Test applying rig with intensity scaling."""
        result = apply_lighting_rig(
            "three_point_soft",
            intensity_scale=2.0
        )
        assert result["total_lights"] == 0


class TestBuildLightConfig:
    """Tests for _build_light_config helper function."""

    def test_build_config_angle_distance(self):
        """Test building config with angle_distance positioning."""
        light_data = {
            "light_type": "area",
            "intensity": 1000.0,
            "color": [1.0, 1.0, 1.0],
            "shape": "RECTANGLE",
            "size": 2.0,
            "position": {
                "type": "angle_distance",
                "angle": 45.0,
                "distance": 2.0,
                "height": 1.5
            }
        }

        config = _build_light_config(
            "key_light",
            light_data,
            (0, 0, 0),
            1.0
        )

        assert config.name == "key_light"
        assert config.light_type == "area"
        assert config.intensity == 1000.0
        assert config.shape == "RECTANGLE"
        assert config.size == 2.0

        # Check position was calculated from angle/distance
        # At 45 degrees, 2m distance, 1.5m height from origin
        pos = config.transform.position
        assert abs(pos[0] - 2.0 * math.sin(math.radians(45))) < 0.01
        assert abs(pos[2] - 1.5) < 0.01

    def test_build_config_absolute_position(self):
        """Test building config with absolute positioning."""
        light_data = {
            "light_type": "area",
            "intensity": 500.0,
            "position": {
                "type": "absolute",
                "coordinates": [1.0, 2.0, 3.0]
            },
            "rotation": [90, 0, 0]
        }

        config = _build_light_config(
            "fill_light",
            light_data,
            (0, 0, 0),
            1.0
        )

        assert config.name == "fill_light"
        assert config.transform.position == (1.0, 2.0, 3.0)
        assert config.transform.rotation == (90, 0, 0)

    def test_build_config_intensity_scale(self):
        """Test that intensity scale is applied."""
        light_data = {
            "light_type": "area",
            "intensity": 1000.0
        }

        config = _build_light_config(
            "light",
            light_data,
            (0, 0, 0),
            2.0  # Double intensity
        )

        assert config.intensity == 2000.0


class TestLightConfigDefaults:
    """Tests for LightConfig default values."""

    def test_default_config(self):
        """Test default LightConfig values."""
        config = LightConfig()

        assert config.name == "key_light"
        assert config.light_type == "area"
        assert config.intensity == 1000.0
        assert config.color == (1.0, 1.0, 1.0)
        assert config.shape == "RECTANGLE"
        assert config.size == 1.0
        assert config.size_y == 1.0
        assert config.spread == 1.047  # 60 degrees
        assert config.use_shadow is True
        assert config.use_temperature is False
        assert config.temperature == 6500.0

    def test_config_serialization(self):
        """Test LightConfig to_dict/from_dict roundtrip."""
        original = LightConfig(
            name="test_light",
            light_type="spot",
            intensity=1500.0,
            color=(0.9, 0.9, 1.0),
            spot_size=0.524,
            spot_blend=0.3
        )

        data = original.to_dict()
        restored = LightConfig.from_dict(data)

        assert restored.name == original.name
        assert restored.light_type == original.light_type
        assert restored.intensity == original.intensity
        assert restored.color == original.color
        assert restored.spot_size == original.spot_size
        assert restored.spot_blend == original.spot_blend


class TestConstants:
    """Tests for module constants."""

    def test_area_shapes(self):
        """Test that AREA_SHAPES contains expected values."""
        assert "SQUARE" in AREA_SHAPES
        assert "RECTANGLE" in AREA_SHAPES
        assert "DISK" in AREA_SHAPES
        assert "ELLIPSE" in AREA_SHAPES

    def test_blender_version_constant(self):
        """Test Blender version constant."""
        assert BLENDER_40_MIN == (4, 0, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
