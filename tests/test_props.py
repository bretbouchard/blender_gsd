"""
Unit Tests for Props System

Tests prop library loading, placement, and dressing styles.
"""

import pytest
from lib.art.props import (
    DEFAULT_PROP_LIBRARY,
    load_prop_library,
    get_prop_config,
    find_props_by_category,
    find_props_by_tag,
    find_props_by_style,
    DRESSING_STYLES,
)
from lib.art.set_types import (
    PropConfig,
    PropPlacement,
    RoomConfig,
)


class TestDefaultPropLibrary:
    """Tests for default prop library."""

    def test_library_not_empty(self):
        """Test that default library contains props."""
        assert len(DEFAULT_PROP_LIBRARY) > 0

    def test_furniture_props_exist(self):
        """Test that furniture props are defined."""
        furniture_props = ["sofa_modern", "armchair_modern", "coffee_table_wood"]
        for name in furniture_props:
            assert name in DEFAULT_PROP_LIBRARY

    def test_electronics_props_exist(self):
        """Test that electronics props are defined."""
        electronics_props = ["tv_55inch", "laptop", "keyboard"]
        for name in electronics_props:
            assert name in DEFAULT_PROP_LIBRARY

    def test_decor_props_exist(self):
        """Test that decor props are defined."""
        decor_props = ["lamp_floor", "vase_modern", "plant_potted"]
        for name in decor_props:
            assert name in DEFAULT_PROP_LIBRARY

    def test_prop_has_required_fields(self):
        """Test that props have all required fields."""
        for name, config in DEFAULT_PROP_LIBRARY.items():
            assert config.name == name
            assert config.category is not None
            assert config.dimensions is not None
            assert len(config.dimensions) == 3

    def test_prop_dimensions_positive(self):
        """Test that prop dimensions are positive."""
        for name, config in DEFAULT_PROP_LIBRARY.items():
            assert all(d > 0 for d in config.dimensions), f"Prop {name} has non-positive dimensions"


class TestGetPropConfig:
    """Tests for get_prop_config function."""

    def test_get_existing_prop(self):
        """Test retrieving an existing prop."""
        config = get_prop_config("sofa_modern")
        assert config is not None
        assert config.name == "sofa_modern"
        assert config.category == "furniture"

    def test_get_nonexistent_prop(self):
        """Test retrieving a non-existent prop."""
        config = get_prop_config("nonexistent_prop")
        assert config is None

    def test_get_with_custom_library(self):
        """Test retrieving prop from custom library."""
        custom_lib = {
            "custom_item": PropConfig(
                name="custom_item",
                category="decor",
                style="custom",
            )
        }
        config = get_prop_config("custom_item", custom_lib)
        assert config is not None
        assert config.name == "custom_item"


class TestFindPropsByCategory:
    """Tests for find_props_by_category function."""

    def test_find_furniture(self):
        """Test finding furniture props."""
        props = find_props_by_category("furniture")
        assert len(props) > 0
        for p in props:
            assert p.category == "furniture"

    def test_find_electronics(self):
        """Test finding electronics props."""
        props = find_props_by_category("electronics")
        assert len(props) > 0
        for p in props:
            assert p.category == "electronics"

    def test_find_decor(self):
        """Test finding decor props."""
        props = find_props_by_category("decor")
        assert len(props) > 0
        for p in props:
            assert p.category == "decor"

    def test_find_nonexistent_category(self):
        """Test finding props in non-existent category."""
        props = find_props_by_category("nonexistent")
        assert len(props) == 0


class TestFindPropsByTag:
    """Tests for find_props_by_tag function."""

    def test_find_by_tag_seating(self):
        """Test finding props with 'seating' tag."""
        props = find_props_by_tag("seating")
        assert len(props) > 0
        for p in props:
            assert "seating" in p.tags

    def test_find_by_tag_living_room(self):
        """Test finding props for living room."""
        props = find_props_by_tag("living_room")
        assert len(props) > 0
        for p in props:
            assert "living_room" in p.tags

    def test_find_by_nonexistent_tag(self):
        """Test finding props with non-existent tag."""
        props = find_props_by_tag("nonexistent_tag")
        assert len(props) == 0


class TestFindPropsByStyle:
    """Tests for find_props_by_style function."""

    def test_find_modern_style(self):
        """Test finding modern style props."""
        props = find_props_by_style("modern")
        assert len(props) > 0
        for p in props:
            assert p.style == "modern"

    def test_find_nonexistent_style(self):
        """Test finding props with non-existent style."""
        props = find_props_by_style("nonexistent")
        assert len(props) == 0


class TestDressingStyles:
    """Tests for dressing style constants."""

    def test_dressing_styles_exist(self):
        """Test that all expected dressing styles are defined."""
        expected_styles = [
            "minimal",
            "lived_in",
            "cluttered",
            "sterile",
            "eclectic",
            "staged",
            "abandoned",
            "hoarder",
        ]

        for style in expected_styles:
            assert style in DRESSING_STYLES

    def test_dressing_style_density_ranges(self):
        """Test that prop_density is in valid range."""
        for style_name, style_data in DRESSING_STYLES.items():
            assert 0 <= style_data["prop_density"] <= 1

    def test_dressing_style_clutter_ranges(self):
        """Test that clutter is in valid range."""
        for style_name, style_data in DRESSING_STYLES.items():
            assert 0 <= style_data["clutter"] <= 1

    def test_minimal_low_density(self):
        """Test minimal style has low density."""
        assert DRESSING_STYLES["minimal"]["prop_density"] <= 0.3

    def test_cluttered_high_density(self):
        """Test cluttered style has high density."""
        assert DRESSING_STYLES["cluttered"]["prop_density"] >= 0.9

    def test_sterile_no_clutter(self):
        """Test sterile style has no clutter."""
        assert DRESSING_STYLES["sterile"]["clutter"] == 0.0


class TestPropPlacement:
    """Tests for PropPlacement dataclass."""

    def test_default_placement(self):
        """Test default prop placement values."""
        placement = PropPlacement()
        assert placement.prop == ""
        assert placement.position == (0.0, 0.0, 0.0)
        assert placement.rotation == (0.0, 0.0, 0.0)
        assert placement.scale == 1.0
        assert placement.variant == 0

    def test_custom_placement(self):
        """Test custom prop placement."""
        placement = PropPlacement(
            prop="sofa_modern",
            position=(1.5, 2.0, 0.0),
            rotation=(0.0, 0.0, 45.0),
            scale=1.1,
            variant=2,
        )
        assert placement.prop == "sofa_modern"
        assert placement.position == (1.5, 2.0, 0.0)
        assert placement.rotation == (0.0, 0.0, 45.0)

    def test_serialization(self):
        """Test prop placement serialization."""
        placement = PropPlacement(
            prop="chair_office",
            position=(1.0, 2.0, 0.5),
            rotation=(0.0, 0.0, 90.0),
            scale=1.2,
        )

        data = placement.to_dict()
        assert data["prop"] == "chair_office"
        assert data["position"] == [1.0, 2.0, 0.5]
        assert data["scale"] == 1.2

        restored = PropPlacement.from_dict(data)
        assert restored.prop == placement.prop
        assert restored.position == placement.position
        assert restored.scale == placement.scale


class TestPropConfig:
    """Tests for PropConfig dataclass."""

    def test_default_config(self):
        """Test default prop config values."""
        config = PropConfig()
        assert config.name == ""
        assert config.category == "decor"
        assert config.scale == 1.0
        assert config.variations == 1

    def test_custom_config(self):
        """Test custom prop config."""
        config = PropConfig(
            name="test_prop",
            category="furniture",
            style="modern",
            material="wood_oak",
            dimensions=(1.0, 0.5, 0.8),
            variations=3,
            tags=["test", "furniture"],
        )
        assert config.name == "test_prop"
        assert config.category == "furniture"
        assert config.dimensions == (1.0, 0.5, 0.8)
        assert len(config.tags) == 2

    def test_serialization(self):
        """Test prop config serialization."""
        config = PropConfig(
            name="serialize_test",
            category="electronics",
            dimensions=(0.3, 0.2, 0.1),
            tags=["small"],
        )

        data = config.to_dict()
        assert data["name"] == "serialize_test"
        assert data["dimensions"] == [0.3, 0.2, 0.1]

        restored = PropConfig.from_dict(data)
        assert restored.name == config.name
        assert restored.dimensions == config.dimensions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
