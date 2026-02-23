"""
Unit tests for MSG 1998 prompts module.

Tests prompt building and SD prompt configuration without SD pipeline.
"""

import pytest

from lib.msg1998.prompts_1998 import (
    POSITIVE_BASE,
    NEGATIVE_BASE,
    SCENE_PROMPTS,
    LAYER_PROMPTS,
    PERIOD_NEGATIVE_ADDITIONS,
    TIME_MODIFIERS,
    WEATHER_MODIFIERS,
    build_prompt,
    get_prompt_variations,
    create_negative_prompt,
    get_period_negative_prompt,
    add_time_modifier,
    add_weather_modifier,
)


class TestPositiveBase:
    """Tests for POSITIVE_BASE constant."""

    def test_contains_film_stock_reference(self):
        """Test that film stock is mentioned."""
        assert "film" in POSITIVE_BASE.lower()
        assert "kodak" in POSITIVE_BASE.lower()

    def test_contains_year_reference(self):
        """Test that 1998 is mentioned."""
        assert "1998" in POSITIVE_BASE

    def test_contains_lens_reference(self):
        """Test that lens type is mentioned."""
        assert "anamorphic" in POSITIVE_BASE.lower() or "lens" in POSITIVE_BASE.lower()

    def test_contains_aspect_ratio(self):
        """Test that aspect ratio is mentioned."""
        assert "2.39" in POSITIVE_BASE or "aspect" in POSITIVE_BASE.lower()

    def test_contains_nyc_reference(self):
        """Test that NYC is mentioned."""
        assert "new york" in POSITIVE_BASE.lower() or "nyc" in POSITIVE_BASE.lower()


class TestNegativeBase:
    """Tests for NEGATIVE_BASE constant."""

    def test_contains_digital_keywords(self):
        """Test that digital is mentioned as negative."""
        assert "digital" in NEGATIVE_BASE.lower()

    def test_contains_modern_keywords(self):
        """Test that modern is mentioned as negative."""
        assert "modern" in NEGATIVE_BASE.lower()

    def test_contains_smartphone_keyword(self):
        """Test that smartphone is mentioned as negative."""
        assert "smartphone" in NEGATIVE_BASE.lower()

    def test_contains_year_keywords(self):
        """Test that wrong years are mentioned."""
        assert "2020" in NEGATIVE_BASE


class TestScenePrompts:
    """Tests for SCENE_PROMPTS dictionary."""

    def test_has_exterior_scenes(self):
        """Test that exterior scenes are defined."""
        assert "msg_exterior" in SCENE_PROMPTS
        assert "street_day" in SCENE_PROMPTS

    def test_has_interior_scenes(self):
        """Test that interior scenes are defined."""
        assert "msg_interior" in SCENE_PROMPTS
        assert "office" in SCENE_PROMPTS

    def test_has_subway_scenes(self):
        """Test that subway scenes are defined."""
        assert "subway_platform" in SCENE_PROMPTS
        assert "subway_car" in SCENE_PROMPTS

    def test_has_night_scenes(self):
        """Test that night scenes are defined."""
        assert "night_exterior" in SCENE_PROMPTS

    def test_scene_prompts_are_strings(self):
        """Test that all scene prompts are strings."""
        for key, value in SCENE_PROMPTS.items():
            assert isinstance(value, str), f"Scene prompt {key} should be string"


class TestLayerPrompts:
    """Tests for LAYER_PROMPTS dictionary."""

    def test_has_background_layer(self):
        """Test that background layer is defined."""
        assert "background" in LAYER_PROMPTS

    def test_has_midground_layer(self):
        """Test that midground layer is defined."""
        assert "midground" in LAYER_PROMPTS

    def test_has_foreground_layer(self):
        """Test that foreground layer is defined."""
        assert "foreground" in LAYER_PROMPTS

    def test_all_layers_are_strings(self):
        """Test that all layer prompts are strings."""
        for key, value in LAYER_PROMPTS.items():
            assert isinstance(value, str)


class TestPeriodNegativeAdditions:
    """Tests for PERIOD_NEGATIVE_ADDITIONS list."""

    def test_has_smartphone(self):
        """Test that smartphone is in list."""
        assert "smartphone" in PERIOD_NEGATIVE_ADDITIONS

    def test_has_iphone(self):
        """Test that iphone is in list."""
        assert "iphone" in PERIOD_NEGATIVE_ADDITIONS

    def test_has_tesla(self):
        """Test that Tesla is in list (may be 'Tesla car')."""
        has_tesla = any("tesla" in item.lower() for item in PERIOD_NEGATIVE_ADDITIONS)
        assert has_tesla, "Tesla should be in period negative additions"

    def test_has_led_billboard(self):
        """Test that LED billboard is in list."""
        assert "LED billboard" in PERIOD_NEGATIVE_ADDITIONS

    def test_has_flat_screen(self):
        """Test that flat screen TV is in list."""
        assert "flat screen TV" in PERIOD_NEGATIVE_ADDITIONS

    def test_has_modern_fashion(self):
        """Test that modern fashion references are in list."""
        assert any("fashion" in item for item in PERIOD_NEGATIVE_ADDITIONS)


class TestTimeModifiers:
    """Tests for TIME_MODIFIERS dictionary."""

    def test_has_golden_hour(self):
        """Test that golden hour is defined."""
        assert "golden_hour" in TIME_MODIFIERS

    def test_has_blue_hour(self):
        """Test that blue hour is defined."""
        assert "blue_hour" in TIME_MODIFIERS

    def test_has_midday(self):
        """Test that midday is defined."""
        assert "midday" in TIME_MODIFIERS

    def test_has_night(self):
        """Test that night is defined."""
        assert "night" in TIME_MODIFIERS

    def test_all_modifiers_are_strings(self):
        """Test that all time modifiers are strings."""
        for key, value in TIME_MODIFIERS.items():
            assert isinstance(value, str)


class TestWeatherModifiers:
    """Tests for WEATHER_MODIFIERS dictionary."""

    def test_has_clear(self):
        """Test that clear is defined."""
        assert "clear" in WEATHER_MODIFIERS

    def test_has_rain(self):
        """Test that rain is defined."""
        assert "rain" in WEATHER_MODIFIERS

    def test_has_snow(self):
        """Test that snow is defined."""
        assert "snow" in WEATHER_MODIFIERS

    def test_has_fog(self):
        """Test that fog is defined."""
        assert "fog" in WEATHER_MODIFIERS


class TestBuildPrompt:
    """Tests for build_prompt function."""

    def test_base_only(self):
        """Test with only base prompt."""
        result = build_prompt("test base", None, None)

        assert result == "test base"

    def test_with_scene_type(self):
        """Test with scene type."""
        result = build_prompt("base", "msg_exterior", None)

        assert "base" in result
        assert "Madison Square Garden" in result

    def test_with_layer(self):
        """Test with layer."""
        result = build_prompt("base", None, "background")

        assert "base" in result
        assert "distant buildings" in result

    def test_with_scene_and_layer(self):
        """Test with both scene and layer."""
        result = build_prompt("base", "street_day", "foreground")

        assert "base" in result
        assert "busy NYC street" in result
        assert "street level details" in result

    def test_invalid_scene_type(self):
        """Test with invalid scene type."""
        result = build_prompt("base", "nonexistent_scene", None)

        # Should just return base
        assert result == "base"

    def test_invalid_layer(self):
        """Test with invalid layer."""
        result = build_prompt("base", None, "nonexistent_layer")

        # Should just return base
        assert result == "base"

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        result = build_prompt("  base with spaces  ", None, None)

        # Should strip whitespace
        assert "base with spaces" in result

    def test_all_valid_scenes(self):
        """Test that all scene types work."""
        for scene_type in SCENE_PROMPTS.keys():
            result = build_prompt("test", scene_type, None)
            assert "test" in result

    def test_all_valid_layers(self):
        """Test that all layers work."""
        for layer in LAYER_PROMPTS.keys():
            result = build_prompt("test", None, layer)
            assert "test" in result


class TestGetPromptVariations:
    """Tests for get_prompt_variations function."""

    def test_returns_dict(self):
        """Test that function returns dictionary."""
        result = get_prompt_variations("msg_exterior")

        assert isinstance(result, dict)

    def test_has_all_layers(self):
        """Test that all layers are present."""
        result = get_prompt_variations("msg_exterior")

        assert "background" in result
        assert "midground" in result
        assert "foreground" in result

    def test_layer_prompts_contain_scene(self):
        """Test that layer prompts contain scene description."""
        result = get_prompt_variations("msg_exterior")

        for layer, prompt in result.items():
            assert "Madison Square Garden" in prompt

    def test_layer_prompts_contain_base(self):
        """Test that layer prompts contain positive base."""
        result = get_prompt_variations("street_day")

        for layer, prompt in result.items():
            assert "1998" in prompt  # From POSITIVE_BASE

    def test_all_scene_types(self):
        """Test all scene types generate variations."""
        for scene_type in SCENE_PROMPTS.keys():
            result = get_prompt_variations(scene_type)
            assert len(result) == 3  # 3 layers


class TestCreateNegativePrompt:
    """Tests for create_negative_prompt function."""

    def test_base_only(self):
        """Test with only base negative."""
        result = create_negative_prompt(None)

        assert "digital" in result.lower()

    def test_with_additions(self):
        """Test with additional negative terms."""
        result = create_negative_prompt(["extra_term", "another_term"])

        assert "extra_term" in result
        assert "another_term" in result

    def test_empty_additions(self):
        """Test with empty additions list."""
        result = create_negative_prompt([])

        # Should just be the base
        assert "digital" in result.lower()

    def test_multiple_additions(self):
        """Test with multiple additions."""
        additions = ["term1", "term2", "term3"]
        result = create_negative_prompt(additions)

        for term in additions:
            assert term in result


class TestGetPeriodNegativePrompt:
    """Tests for get_period_negative_prompt function."""

    def test_contains_period_additions(self):
        """Test that period additions are included."""
        result = get_period_negative_prompt()

        assert "iphone" in result.lower()
        assert "smartphone" in result.lower()

    def test_contains_base_negative(self):
        """Test that base negative is included."""
        result = get_period_negative_prompt()

        assert "digital" in result.lower()

    def test_is_string(self):
        """Test that result is string."""
        result = get_period_negative_prompt()

        assert isinstance(result, str)


class TestAddTimeModifier:
    """Tests for add_time_modifier function."""

    def test_golden_hour(self):
        """Test golden hour modifier."""
        result = add_time_modifier("test prompt", "golden_hour")

        assert "warm golden light" in result

    def test_blue_hour(self):
        """Test blue hour modifier."""
        result = add_time_modifier("test prompt", "blue_hour")

        assert "cool blue light" in result

    def test_invalid_time(self):
        """Test with invalid time modifier."""
        result = add_time_modifier("test prompt", "nonexistent_time")

        # Should return unchanged
        assert result == "test prompt"

    def test_all_times(self):
        """Test all time modifiers."""
        for time_key in TIME_MODIFIERS.keys():
            result = add_time_modifier("test", time_key)
            assert len(result) > len("test")


class TestAddWeatherModifier:
    """Tests for add_weather_modifier function."""

    def test_rain(self):
        """Test rain modifier."""
        result = add_weather_modifier("test prompt", "rain")

        assert "wet surfaces" in result

    def test_snow(self):
        """Test snow modifier."""
        result = add_weather_modifier("test prompt", "snow")

        assert "snow" in result.lower()

    def test_fog(self):
        """Test fog modifier."""
        result = add_weather_modifier("test prompt", "fog")

        assert "fog" in result.lower()

    def test_invalid_weather(self):
        """Test with invalid weather modifier."""
        result = add_weather_modifier("test prompt", "nonexistent_weather")

        # Should return unchanged
        assert result == "test prompt"

    def test_all_weather(self):
        """Test all weather modifiers."""
        for weather_key in WEATHER_MODIFIERS.keys():
            result = add_weather_modifier("test", weather_key)
            assert len(result) > len("test")


class TestPromptCombinations:
    """Tests for combined prompt building."""

    def test_full_prompt_with_all_modifiers(self):
        """Test building prompt with all modifiers."""
        base = build_prompt(POSITIVE_BASE, "street_day", "midground")
        with_time = add_time_modifier(base, "golden_hour")
        with_weather = add_weather_modifier(with_time, "rain")

        assert "1998" in with_weather
        assert "golden" in with_weather.lower()
        assert "rain" in with_weather.lower()

    def test_negative_with_modifiers(self):
        """Test negative prompt with time context."""
        negative = create_negative_prompt(["night scene"])

        assert "digital" in negative.lower()
        assert "night scene" in negative

    def test_layer_variations_are_unique(self):
        """Test that layer variations have unique content."""
        variations = get_prompt_variations("msg_exterior")

        backgrounds = variations["background"]
        foregrounds = variations["foreground"]

        # Should have different layer-specific content
        assert backgrounds != foregrounds
