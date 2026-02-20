"""
Unit tests for Light Rigs Module

Tests for lib/cinematic/light_rigs.py - Lighting rig presets and positioning.
All tests run without Blender (mocked) for CI compatibility.
"""

import pytest
import math
from unittest.mock import patch, MagicMock

from lib.cinematic.light_rigs import (
    position_key_light,
    position_fill_light,
    position_back_light,
    create_three_point_soft,
    create_three_point_hard,
    create_product_hero,
    create_studio_high_key,
    create_studio_low_key,
    create_light_rig,
    list_light_rig_presets,
    DEFAULT_KEY_ANGLE,
    DEFAULT_KEY_ELEVATION,
    DEFAULT_KEY_DISTANCE,
    DEFAULT_FILL_RATIO,
    DEFAULT_BACK_ELEVATION,
)
from lib.cinematic.types import LightConfig, Transform3D


class TestPositionKeyLight:
    """Tests for key light positioning."""

    def test_default_positioning(self):
        """Test key light with default parameters."""
        base_config = LightConfig(name="key", intensity=1000.0)
        result = position_key_light(base_config, (0, 0, 0))

        # Check that position is calculated
        pos = result.transform.position
        assert pos[2] > 0  # Should be elevated

    def test_custom_angle(self):
        """Test key light with custom angle."""
        base_config = LightConfig(name="key", intensity=1000.0)
        result = position_key_light(
            base_config,
            (0, 0, 0),
            angle=90.0,  # Side light
            elevation=45.0
        )

        # At 90 degrees, should be on the side
        pos = result.transform.position
        assert abs(pos[0]) > 0  # X offset

    def test_custom_distance(self):
        """Test key light with custom distance."""
        base_config = LightConfig(name="key", intensity=1000.0)
        result = position_key_light(
            base_config,
            (0, 0, 0),
            distance=3.0
        )

        # Distance should affect position magnitude
        pos = result.transform.position
        magnitude = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
        assert magnitude > 2.5  # Roughly 3m away

    def test_subject_offset(self):
        """Test key light with offset subject position."""
        base_config = LightConfig(name="key", intensity=1000.0)
        result = position_key_light(
            base_config,
            (5.0, 5.0, 1.0),  # Subject at (5, 5, 1)
            distance=1.0
        )

        # Position should be relative to subject
        pos = result.transform.position
        assert pos[0] != 0  # Not at origin
        assert pos[1] != 0

    def test_preserves_intensity(self):
        """Test that intensity is preserved."""
        base_config = LightConfig(name="key", intensity=1500.0)
        result = position_key_light(base_config, (0, 0, 0))

        assert result.intensity == 1500.0


class TestPositionFillLight:
    """Tests for fill light positioning."""

    def test_fill_relative_to_key(self):
        """Test fill light positioned relative to key."""
        key_config = position_key_light(
            LightConfig(name="key", intensity=1000.0),
            (0, 0, 0),
            angle=45.0
        )

        fill_config = LightConfig(name="fill", intensity=400.0)
        result = position_fill_light(fill_config, key_config)

        # Fill should be on opposite side
        key_pos = key_config.transform.position
        fill_pos = result.transform.position

        # Signs should be opposite or similar distance away
        assert key_pos != fill_pos

    def test_fill_intensity_ratio(self):
        """Test fill light intensity ratio."""
        key_config = LightConfig(
            name="key",
            intensity=1000.0,
            transform=Transform3D(position=(1.0, -1.0, 1.0))
        )

        fill_config = LightConfig(name="fill", intensity=400.0)
        result = position_fill_light(fill_config, key_config, ratio=0.4)

        # Intensity should be scaled by ratio
        assert result.intensity == 1000.0 * 0.4

    def test_fill_larger_size(self):
        """Test that fill light has larger size for softer light."""
        key_config = LightConfig(
            name="key",
            intensity=1000.0,
            transform=Transform3D(position=(1.0, -1.0, 1.0))
        )

        fill_config = LightConfig(
            name="fill",
            intensity=400.0,
            size=1.0,
            size_y=1.0
        )
        result = position_fill_light(fill_config, key_config)

        # Fill should be larger for softer shadows
        assert result.size > fill_config.size
        assert result.size_y > fill_config.size_y


class TestPositionBackLight:
    """Tests for back/rim light positioning."""

    def test_back_light_position(self):
        """Test back light is positioned behind subject."""
        base_config = LightConfig(name="rim", intensity=800.0)
        result = position_back_light(base_config, (0, 0, 0))

        # Should be behind (positive Y in Blender's coordinate system)
        pos = result.transform.position
        assert pos[1] > 0  # Behind subject

    def test_back_light_elevation(self):
        """Test back light elevation affects Z position."""
        low_config = position_back_light(
            LightConfig(name="rim_low"),
            (0, 0, 0),
            elevation=30.0
        )
        high_config = position_back_light(
            LightConfig(name="rim_high"),
            (0, 0, 0),
            elevation=60.0
        )

        # Higher elevation should have higher Z
        assert high_config.transform.position[2] > low_config.transform.position[2]


class TestCreateThreePointSoft:
    """Tests for soft three-point lighting creation."""

    def test_returns_three_lights(self):
        """Test that three lights are created."""
        lights = create_three_point_soft()
        assert len(lights) == 3

    def test_light_names(self):
        """Test that lights have correct names."""
        lights = create_three_point_soft()
        names = [l.name for l in lights]

        assert "key" in names[0].lower()
        assert "fill" in names[1].lower()
        assert "rim" in names[2].lower() or "back" in names[2].lower()

    def test_intensity_ratio(self):
        """Test that fill is softer than key."""
        lights = create_three_point_soft()
        key = lights[0]
        fill = lights[1]

        # Fill should be less intense than key
        assert fill.intensity < key.intensity

    def test_subject_position_affects_lights(self):
        """Test that subject position affects all lights."""
        lights_default = create_three_point_soft((0, 0, 0))
        lights_offset = create_three_point_soft((5, 5, 2))

        # Positions should be different
        for i in range(3):
            assert lights_default[i].transform.position != lights_offset[i].transform.position

    def test_key_intensity_parameter(self):
        """Test that key_intensity parameter works."""
        lights_low = create_three_point_soft(key_intensity=500.0)
        lights_high = create_three_point_soft(key_intensity=2000.0)

        # Key intensity should be scaled
        assert lights_low[0].intensity == 500.0
        assert lights_high[0].intensity == 2000.0


class TestCreateThreePointHard:
    """Tests for hard three-point lighting creation."""

    def test_returns_three_lights(self):
        """Test that three lights are created."""
        lights = create_three_point_hard()
        assert len(lights) == 3

    def test_harder_shadows_than_soft(self):
        """Test that hard lighting has smaller shadow_soft_size."""
        soft_lights = create_three_point_soft()
        hard_lights = create_three_point_hard()

        # Hard lighting should have smaller soft size
        assert hard_lights[0].shadow_soft_size < soft_lights[0].shadow_soft_size

    def test_spot_light_for_hard_key(self):
        """Test that hard key uses spot light."""
        lights = create_three_point_hard()
        key = lights[0]

        assert key.light_type == "spot"


class TestCreateProductHero:
    """Tests for product hero lighting creation."""

    def test_returns_three_lights(self):
        """Test that three lights are created."""
        lights = create_product_hero()
        assert len(lights) == 3

    def test_overhead_light_position(self):
        """Test that overhead light is above subject."""
        lights = create_product_hero()
        overhead = lights[0]

        # Should be directly above (pointing down)
        assert overhead.transform.position[2] > 0
        assert overhead.transform.rotation[0] == -90  # Pointing down

    def test_fill_cards_positioned_sides(self):
        """Test that fill cards are on opposite sides."""
        lights = create_product_hero()

        # Find left and right fill by name
        left_fill = next((l for l in lights if "left" in l.name), None)
        right_fill = next((l for l in lights if "right" in l.name), None)

        assert left_fill is not None
        assert right_fill is not None

        # Should be on opposite X sides
        assert left_fill.transform.position[0] < 0
        assert right_fill.transform.position[0] > 0


class TestCreateStudioHighKey:
    """Tests for high-key studio lighting creation."""

    def test_returns_multiple_lights(self):
        """Test that multiple lights are created."""
        lights = create_studio_high_key()
        assert len(lights) >= 4  # At least overhead, front, left, right

    def test_all_lights_soft(self):
        """Test that all lights have soft shadows."""
        lights = create_studio_high_key()

        for light in lights:
            assert light.shadow_soft_size >= 0.8  # Soft shadows


class TestCreateStudioLowKey:
    """Tests for low-key studio lighting creation."""

    def test_returns_lights(self):
        """Test that lights are created."""
        lights = create_studio_low_key()
        assert len(lights) >= 2

    def test_key_is_narrow_spot(self):
        """Test that key is a narrow spot light."""
        lights = create_studio_low_key()
        key = lights[0]

        assert key.light_type == "spot"
        assert key.spot_size < 0.5  # Narrow beam

    def test_minimal_fill(self):
        """Test that fill is minimal."""
        lights = create_studio_low_key()
        fill = lights[1]

        # Fill should be much less intense than key
        key = lights[0]
        assert fill.intensity < key.intensity * 0.2


class TestCreateLightRig:
    """Tests for create_light_rig function."""

    def test_valid_presets(self):
        """Test that all listed presets work."""
        presets = list_light_rig_presets()

        for preset in presets:
            lights = create_light_rig(preset)
            assert len(lights) > 0, f"Preset {preset} returned no lights"

    def test_invalid_preset(self):
        """Test that invalid preset raises error."""
        with pytest.raises(ValueError, match="Unknown lighting rig preset"):
            create_light_rig("nonexistent_preset")

    def test_intensity_scale(self):
        """Test that intensity scale is applied."""
        lights_normal = create_light_rig("three_point_soft", intensity_scale=1.0)
        lights_double = create_light_rig("three_point_soft", intensity_scale=2.0)

        for normal, double in zip(lights_normal, lights_double):
            assert double.intensity == normal.intensity * 2

    def test_subject_position(self):
        """Test that subject position is used."""
        lights_origin = create_light_rig("three_point_soft", (0, 0, 0))
        lights_offset = create_light_rig("three_point_soft", (10, 10, 5))

        # All light positions should be different
        for origin, offset in zip(lights_origin, lights_offset):
            assert origin.transform.position != offset.transform.position


class TestListLightRigPresets:
    """Tests for list_light_rig_presets function."""

    def test_returns_list(self):
        """Test that a list is returned."""
        presets = list_light_rig_presets()
        assert isinstance(presets, list)

    def test_contains_common_presets(self):
        """Test that common presets are included."""
        presets = list_light_rig_presets()

        assert "three_point_soft" in presets
        assert "three_point_hard" in presets
        assert "product_hero" in presets
        assert "studio_high_key" in presets
        assert "studio_low_key" in presets

    def test_sorted(self):
        """Test that presets are sorted."""
        presets = list_light_rig_presets()
        assert presets == sorted(presets)


class TestConstants:
    """Tests for module constants."""

    def test_default_values(self):
        """Test that default values are reasonable."""
        assert 0 < DEFAULT_KEY_ANGLE < 90
        assert 0 < DEFAULT_KEY_ELEVATION < 90
        assert DEFAULT_KEY_DISTANCE > 0
        assert 0 < DEFAULT_FILL_RATIO < 1
        assert 0 < DEFAULT_BACK_ELEVATION < 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
