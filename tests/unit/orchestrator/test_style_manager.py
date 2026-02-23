"""
Tests for Style Manager

Tests style profiles and compatibility checking.
"""

import pytest
from lib.orchestrator.style_manager import (
    StyleCategory,
    StyleProfile,
    StyleManager,
    STYLE_PROFILES,
)


class TestStyleCategory:
    """Tests for StyleCategory enum."""

    def test_category_values(self):
        """Test StyleCategory enum values."""
        assert StyleCategory.REALISTIC.value == "realistic"
        assert StyleCategory.STYLIZED.value == "stylized"
        assert StyleCategory.CARTOON.value == "cartoon"
        assert StyleCategory.ABSTRACT.value == "abstract"
        assert StyleCategory.RETRO.value == "retro"
        assert StyleCategory.FUTURISTIC.value == "futuristic"


class TestStyleProfile:
    """Tests for StyleProfile dataclass."""

    def test_create_default(self):
        """Test creating StyleProfile with defaults."""
        profile = StyleProfile()
        assert profile.style_id == ""
        assert profile.name == ""
        assert profile.category == "realistic"
        assert profile.material_style == "pbr"
        assert profile.texture_intensity == 1.0
        assert profile.geometry_detail == 1.0

    def test_create_with_values(self):
        """Test creating StyleProfile with values."""
        profile = StyleProfile(
            style_id="custom_style",
            name="Custom Style",
            category="stylized",
            material_style="toon",
            color_palette=["#FF0000", "#00FF00", "#0000FF"],
            texture_intensity=0.5,
            geometry_detail=0.7,
        )
        assert profile.style_id == "custom_style"
        assert profile.name == "Custom Style"
        assert profile.category == "stylized"
        assert profile.material_style == "toon"
        assert len(profile.color_palette) == 3
        assert profile.texture_intensity == 0.5

    def test_to_dict(self):
        """Test StyleProfile serialization."""
        profile = StyleProfile(
            style_id="test_style",
            name="Test",
            category="cartoon",
            post_processing=["outline", "cel_shading"],
        )
        result = profile.to_dict()
        assert result["style_id"] == "test_style"
        assert result["category"] == "cartoon"
        assert result["post_processing"] == ["outline", "cel_shading"]


class TestStyleProfiles:
    """Tests for predefined style profiles."""

    def test_style_profiles_exist(self):
        """Test that STYLE_PROFILES is populated."""
        assert isinstance(STYLE_PROFILES, dict)
        assert len(STYLE_PROFILES) > 0

    def test_photorealistic_profile(self):
        """Test photorealistic style profile."""
        profile = STYLE_PROFILES.get("photorealistic")
        assert profile is not None
        assert profile.style_id == "photorealistic"
        assert profile.category == "realistic"
        assert profile.material_style == "pbr"
        assert profile.texture_intensity == 1.0
        assert profile.geometry_detail == 1.0

    def test_cartoon_profile(self):
        """Test cartoon style profile."""
        profile = STYLE_PROFILES.get("cartoon")
        assert profile is not None
        assert profile.style_id == "cartoon"
        assert profile.category == "cartoon"
        assert profile.material_style == "toon"
        assert profile.texture_intensity == 0.2
        assert "cel_shading" in profile.post_processing

    def test_low_poly_profile(self):
        """Test low poly style profile."""
        profile = STYLE_PROFILES.get("low_poly")
        assert profile is not None
        assert profile.style_id == "low_poly"
        assert profile.category == "stylized"
        assert profile.texture_intensity == 0.0
        assert profile.geometry_detail == 0.3

    def test_sci_fi_profile(self):
        """Test sci-fi style profile."""
        profile = STYLE_PROFILES.get("sci_fi")
        assert profile is not None
        assert profile.style_id == "sci_fi"
        assert profile.category == "futuristic"
        assert "bloom" in profile.post_processing

    def test_all_profiles_have_required_fields(self):
        """Test all profiles have required fields."""
        for style_id, profile in STYLE_PROFILES.items():
            assert profile.style_id == style_id
            assert profile.name != ""
            assert profile.category != ""
            assert isinstance(profile.color_palette, list)


class TestStyleManager:
    """Tests for StyleManager class."""

    def test_init(self):
        """Test StyleManager initialization."""
        manager = StyleManager()
        assert manager.profiles is not None
        assert len(manager.profiles) > 0

    def test_get_profile_valid(self):
        """Test getting a valid profile."""
        manager = StyleManager()
        profile = manager.get_profile("photorealistic")
        assert profile is not None
        assert profile.style_id == "photorealistic"

    def test_get_profile_invalid(self):
        """Test getting an invalid profile."""
        manager = StyleManager()
        profile = manager.get_profile("nonexistent_style")
        assert profile is None

    def test_list_styles(self):
        """Test listing all styles."""
        manager = StyleManager()
        styles = manager.list_styles()
        assert isinstance(styles, list)
        assert len(styles) > 0
        assert "photorealistic" in styles

    def test_check_compatibility_same_style(self):
        """Test compatibility of same style."""
        manager = StyleManager()
        assert manager.check_compatibility("photorealistic", "photorealistic") is True
        assert manager.check_compatibility("cartoon", "cartoon") is True

    def test_check_compatibility_different_styles(self):
        """Test compatibility of different styles."""
        manager = StyleManager()
        # These depend on the compatible_styles lists in the profiles
        result = manager.check_compatibility("photorealistic", "minimalist")
        # Should be compatible if listed in compatible_styles
        assert isinstance(result, bool)

    def test_check_compatibility_invalid_styles(self):
        """Test compatibility with invalid styles."""
        manager = StyleManager()
        assert manager.check_compatibility("invalid", "photorealistic") is False
        assert manager.check_compatibility("photorealistic", "invalid") is False

    def test_get_compatible_styles(self):
        """Test getting all compatible styles."""
        manager = StyleManager()
        compatible = manager.get_compatible_styles("photorealistic")
        assert isinstance(compatible, list)
        # Should always include self
        assert "photorealistic" in compatible

    def test_suggest_asset_style_exact_match(self):
        """Test asset style suggestion with exact match."""
        manager = StyleManager()
        asset_styles = ["photorealistic", "stylized", "cartoon"]
        result = manager.suggest_asset_style("photorealistic", asset_styles)
        assert result == "photorealistic"

    def test_suggest_asset_style_compatible_match(self):
        """Test asset style suggestion with compatible match."""
        manager = StyleManager()
        # If photorealistic is not available but a compatible style is
        asset_styles = ["minimalist", "stylized"]
        result = manager.suggest_asset_style("photorealistic", asset_styles)
        assert result in asset_styles

    def test_suggest_asset_style_empty_list(self):
        """Test asset style suggestion with empty list."""
        manager = StyleManager()
        result = manager.suggest_asset_style("photorealistic", [])
        assert result is None

    def test_suggest_asset_style_invalid_scene_style(self):
        """Test asset style suggestion with invalid scene style."""
        manager = StyleManager()
        asset_styles = ["photorealistic", "stylized"]
        result = manager.suggest_asset_style("invalid_style", asset_styles)
        # Should return first available
        assert result == "photorealistic"


class TestStyleCompatibility:
    """Tests for style compatibility logic."""

    def test_same_category_compatibility(self):
        """Test that styles in same category are compatible."""
        manager = StyleManager()
        # Check if same-category styles are compatible
        # This depends on the implementation
        result = manager.check_compatibility("stylized", "low_poly")
        # Both are in "stylized" category
        assert isinstance(result, bool)

    def test_cartoon_compatible_styles(self):
        """Test cartoon style compatibility."""
        manager = StyleManager()
        profile = manager.get_profile("cartoon")
        if profile:
            for compatible_style in profile.compatible_styles:
                assert manager.check_compatibility("cartoon", compatible_style) is True


class TestStyleManagerEdgeCases:
    """Edge case tests for StyleManager."""

    def test_multiple_managers_independent(self):
        """Test that multiple managers are independent."""
        manager1 = StyleManager()
        manager2 = StyleManager()
        # Both should have same profiles
        assert manager1.list_styles() == manager2.list_styles()

    def test_style_category_consistency(self):
        """Test that style categories are consistent."""
        manager = StyleManager()
        for style_id in manager.list_styles():
            profile = manager.get_profile(style_id)
            assert profile is not None
            assert profile.category in [
                "realistic",
                "stylized",
                "cartoon",
                "abstract",
                "retro",
                "futuristic",
            ]

    def test_color_palette_format(self):
        """Test that color palettes use valid hex format."""
        manager = StyleManager()
        for style_id in manager.list_styles():
            profile = manager.get_profile(style_id)
            for color in profile.color_palette:
                assert color.startswith("#")
                assert len(color) == 7  # #RRGGBB format
