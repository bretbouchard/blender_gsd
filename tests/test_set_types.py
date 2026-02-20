"""
Unit Tests for Set Builder Types

Tests dataclasses, validation, and serialization for set construction types.
"""

import pytest
from lib.art.set_types import (
    # Dataclasses
    WallConfig,
    DoorConfig,
    DoorPlacement,
    WindowConfig,
    WindowPlacement,
    RoomConfig,
    PropConfig,
    PropPlacement,
    SetConfig,
    StylePreset,
    # Enums
    WallOrientation,
    DoorStyle,
    WindowStyle,
    SwingDirection,
    SetStyle,
    Period,
    PropCategory,
    DressingStyle,
    # Constants
    DRESSING_STYLES,
    # Validation
    validate_wall_config,
    validate_door_config,
    validate_window_config,
    validate_room_config,
)


class TestWallConfig:
    """Tests for WallConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WallConfig()
        assert config.width == 4.0
        assert config.height == 2.8
        assert config.thickness == 0.15
        assert config.material == "drywall_white"
        assert config.baseboard_height == 0.1
        assert config.crown_molding == False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = WallConfig(
            width=5.0,
            height=3.0,
            thickness=0.2,
            material="brick_exposed",
            crown_molding=True,
        )
        assert config.width == 5.0
        assert config.height == 3.0
        assert config.thickness == 0.2
        assert config.material == "brick_exposed"
        assert config.crown_molding == True

    def test_serialization(self):
        """Test to_dict and from_dict serialization."""
        config = WallConfig(
            width=3.5,
            height=2.5,
            material="wallpaper_floral",
            color=(0.9, 0.85, 0.8),
        )

        data = config.to_dict()
        assert data["width"] == 3.5
        assert data["height"] == 2.5
        assert data["material"] == "wallpaper_floral"
        assert data["color"] == [0.9, 0.85, 0.8]

        restored = WallConfig.from_dict(data)
        assert restored.width == config.width
        assert restored.height == config.height
        assert restored.material == config.material
        assert restored.color == config.color


class TestDoorConfig:
    """Tests for DoorConfig dataclass."""

    def test_default_values(self):
        """Test default door configuration."""
        config = DoorConfig()
        assert config.width == 0.9
        assert config.height == 2.1
        assert config.style == "panel_6"
        assert config.swing_direction == "in_left"

    def test_custom_values(self):
        """Test custom door configuration."""
        config = DoorConfig(
            width=0.8,
            height=2.0,
            style="french",
            swing_direction="out_right",
            has_sidelights=True,
        )
        assert config.width == 0.8
        assert config.style == "french"
        assert config.has_sidelights == True

    def test_serialization(self):
        """Test door config serialization."""
        config = DoorConfig(
            width=1.0,
            style="barn",
            handle_material="iron",
        )

        data = config.to_dict()
        assert data["width"] == 1.0
        assert data["style"] == "barn"
        assert data["handle_material"] == "iron"

        restored = DoorConfig.from_dict(data)
        assert restored.width == config.width
        assert restored.style == config.style


class TestWindowConfig:
    """Tests for WindowConfig dataclass."""

    def test_default_values(self):
        """Test default window configuration."""
        config = WindowConfig()
        assert config.width == 1.2
        assert config.height == 1.4
        assert config.sill_height == 0.9
        assert config.style == "double_hung"
        assert config.has_curtains == False

    def test_custom_values(self):
        """Test custom window configuration."""
        config = WindowConfig(
            width=1.5,
            height=1.8,
            style="casement",
            has_curtains=True,
            curtain_style="drapes_heavy",
        )
        assert config.width == 1.5
        assert config.style == "casement"
        assert config.has_curtains == True

    def test_serialization(self):
        """Test window config serialization."""
        config = WindowConfig(
            width=2.0,
            style="picture",
            has_blinds=True,
            blind_type="roller",
        )

        data = config.to_dict()
        assert data["width"] == 2.0
        assert data["style"] == "picture"
        assert data["has_blinds"] == True

        restored = WindowConfig.from_dict(data)
        assert restored.width == config.width
        assert restored.style == config.style


class TestRoomConfig:
    """Tests for RoomConfig dataclass."""

    def test_default_values(self):
        """Test default room configuration."""
        config = RoomConfig(name="test_room")
        assert config.name == "test_room"
        assert config.width == 5.0
        assert config.depth == 4.0
        assert config.height == 2.8
        assert config.floor_material == "hardwood_oak"

    def test_auto_wall_generation(self):
        """Test automatic wall configuration generation."""
        config = RoomConfig(name="auto_room", width=6.0, depth=5.0)

        assert "north" in config.walls
        assert "south" in config.walls
        assert "east" in config.walls
        assert "west" in config.walls

        # North/South walls should have room width
        assert config.walls["north"].width == 6.0
        assert config.walls["south"].width == 6.0

        # East/West walls should have room depth
        assert config.walls["east"].width == 5.0
        assert config.walls["west"].width == 5.0

    def test_with_doors_and_windows(self):
        """Test room with doors and windows."""
        door = DoorPlacement(
            wall="north",
            position=0.5,
            config=DoorConfig(style="flush"),
        )
        window = WindowPlacement(
            wall="south",
            position=0.3,
            config=WindowConfig(style="casement"),
        )

        config = RoomConfig(
            name="room_with_openings",
            doors=[door],
            windows=[window],
        )

        assert len(config.doors) == 1
        assert len(config.windows) == 1
        assert config.doors[0].wall == "north"
        assert config.windows[0].wall == "south"

    def test_serialization(self):
        """Test room config serialization."""
        config = RoomConfig(
            name="serialize_test",
            width=7.0,
            depth=6.0,
            height=3.0,
            doors=[DoorPlacement(wall="east", position=0.7)],
        )

        data = config.to_dict()
        assert data["name"] == "serialize_test"
        assert data["width"] == 7.0
        assert len(data["doors"]) == 1

        restored = RoomConfig.from_dict(data)
        assert restored.name == config.name
        assert restored.width == config.width
        assert len(restored.doors) == 1


class TestPropConfig:
    """Tests for PropConfig dataclass."""

    def test_default_values(self):
        """Test default prop configuration."""
        config = PropConfig()
        assert config.scale == 1.0
        assert config.variations == 1

    def test_custom_values(self):
        """Test custom prop configuration."""
        config = PropConfig(
            name="sofa_modern",
            category="furniture",
            style="modern",
            dimensions=(2.0, 0.9, 0.8),
            tags=["seating", "living_room"],
            variations=3,
        )
        assert config.name == "sofa_modern"
        assert config.category == "furniture"
        assert config.dimensions == (2.0, 0.9, 0.8)
        assert len(config.tags) == 2

    def test_serialization(self):
        """Test prop config serialization."""
        config = PropConfig(
            name="lamp_floor",
            dimensions=(0.4, 0.4, 1.6),
            tags=["lighting", "lamp"],
        )

        data = config.to_dict()
        assert data["name"] == "lamp_floor"
        assert data["dimensions"] == [0.4, 0.4, 1.6]

        restored = PropConfig.from_dict(data)
        assert restored.name == config.name
        assert restored.dimensions == config.dimensions


class TestPropPlacement:
    """Tests for PropPlacement dataclass."""

    def test_default_values(self):
        """Test default prop placement."""
        placement = PropPlacement()
        assert placement.position == (0.0, 0.0, 0.0)
        assert placement.rotation == (0.0, 0.0, 0.0)
        assert placement.scale == 1.0
        assert placement.variant == 0

    def test_custom_values(self):
        """Test custom prop placement."""
        placement = PropPlacement(
            prop="chair_office",
            position=(1.5, 2.0, 0.0),
            rotation=(0.0, 0.0, 45.0),
            scale=1.1,
            variant=2,
        )
        assert placement.prop == "chair_office"
        assert placement.position == (1.5, 2.0, 0.0)
        assert placement.rotation == (0.0, 0.0, 45.0)

    def test_serialization(self):
        """Test prop placement serialization."""
        placement = PropPlacement(
            prop="vase_modern",
            position=(0.5, 0.3, 0.8),
            variant=3,
        )

        data = placement.to_dict()
        assert data["prop"] == "vase_modern"
        assert data["position"] == [0.5, 0.3, 0.8]
        assert data["variant"] == 3

        restored = PropPlacement.from_dict(data)
        assert restored.prop == placement.prop
        assert restored.position == placement.position


class TestSetConfig:
    """Tests for SetConfig dataclass."""

    def test_default_values(self):
        """Test default set configuration."""
        config = SetConfig()
        assert config.name == "set_01"
        assert config.style == "modern_residential"
        assert config.period == "present"
        assert config.lighting_type == "natural"

    def test_with_rooms_and_props(self):
        """Test set with rooms and props."""
        room = RoomConfig(name="living_room")
        prop = PropPlacement(prop="sofa_modern", position=(0, 0, 0))

        config = SetConfig(
            name="test_set",
            rooms=[room],
            props=[prop],
            lighting_type="mixed",
            time_of_day="golden_hour",
        )

        assert len(config.rooms) == 1
        assert len(config.props) == 1
        assert config.lighting_type == "mixed"
        assert config.time_of_day == "golden_hour"

    def test_serialization(self):
        """Test set config serialization."""
        config = SetConfig(
            name="full_set",
            style="victorian",
            period="1890s",
            rooms=[
                RoomConfig(name="parlor"),
                RoomConfig(name="study"),
            ],
        )

        data = config.to_dict()
        assert data["name"] == "full_set"
        assert data["style"] == "victorian"
        assert len(data["rooms"]) == 2

        restored = SetConfig.from_dict(data)
        assert restored.name == config.name
        assert len(restored.rooms) == 2


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
            assert "prop_density" in DRESSING_STYLES[style]
            assert "clutter" in DRESSING_STYLES[style]
            assert "description" in DRESSING_STYLES[style]

    def test_dressing_style_ranges(self):
        """Test that dressing style values are in valid ranges."""
        for style_name, style_data in DRESSING_STYLES.items():
            assert 0 <= style_data["prop_density"] <= 1
            assert 0 <= style_data["clutter"] <= 1


class TestValidation:
    """Tests for validation functions."""

    def test_validate_wall_config_valid(self):
        """Test validation of valid wall config."""
        config = WallConfig(width=4.0, height=2.8, thickness=0.15)
        errors = validate_wall_config(config)
        assert len(errors) == 0

    def test_validate_wall_config_invalid(self):
        """Test validation of invalid wall config."""
        config = WallConfig(width=-1.0, height=0, thickness=-0.1)
        errors = validate_wall_config(config)
        assert len(errors) == 3
        assert any("width" in e for e in errors)
        assert any("height" in e for e in errors)
        assert any("thickness" in e for e in errors)

    def test_validate_door_config_valid(self):
        """Test validation of valid door config."""
        config = DoorConfig(width=0.9, height=2.1)
        errors = validate_door_config(config)
        assert len(errors) == 0

    def test_validate_door_config_invalid_style(self):
        """Test validation catches invalid door style."""
        config = DoorConfig(style="invalid_style")
        errors = validate_door_config(config)
        assert any("style" in e for e in errors)

    def test_validate_window_config_valid(self):
        """Test validation of valid window config."""
        config = WindowConfig(width=1.2, height=1.4, sill_height=0.9)
        errors = validate_window_config(config)
        assert len(errors) == 0

    def test_validate_window_config_invalid(self):
        """Test validation of invalid window config."""
        config = WindowConfig(width=0, num_panes=0)
        errors = validate_window_config(config)
        assert len(errors) >= 2

    def test_validate_room_config(self):
        """Test room validation."""
        config = RoomConfig(
            name="test",
            width=5.0,
            depth=4.0,
            height=2.8,
        )
        errors = validate_room_config(config)
        assert len(errors) == 0


class TestEnums:
    """Tests for enum types."""

    def test_wall_orientation_values(self):
        """Test WallOrientation enum values."""
        assert WallOrientation.NORTH.value == "north"
        assert WallOrientation.SOUTH.value == "south"
        assert WallOrientation.EAST.value == "east"
        assert WallOrientation.WEST.value == "west"

    def test_door_style_values(self):
        """Test DoorStyle enum values."""
        assert DoorStyle.PANEL_6.value == "panel_6"
        assert DoorStyle.FRENCH.value == "french"
        assert DoorStyle.BARN.value == "barn"

    def test_window_style_values(self):
        """Test WindowStyle enum values."""
        assert WindowStyle.DOUBLE_HUNG.value == "double_hung"
        assert WindowStyle.CASEMENT.value == "casement"
        assert WindowStyle.PICTURE.value == "picture"

    def test_set_style_values(self):
        """Test SetStyle enum values."""
        assert SetStyle.MODERN_RESIDENTIAL.value == "modern_residential"
        assert SetStyle.VICTORIAN.value == "victorian"
        assert SetStyle.INDUSTRIAL.value == "industrial"

    def test_period_values(self):
        """Test Period enum values."""
        assert Period.PRESENT.value == "present"
        assert Period.VICTORIAN_1890S.value == "1890s"
        assert Period.CYBERPUNK.value == "cyberpunk"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
