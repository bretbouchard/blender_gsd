"""
Tests for Interior Details

Tests moldings, fixtures, and interior detail generation.
"""

import pytest
from lib.interiors.details import (
    MoldingType,
    FixtureType,
    MoldingConfig,
    FixtureConfig,
    RoomDetails,
    InteriorDetails,
    DEFAULT_MOLDING_CONFIGS,
    ROOM_MOLDING_REQUIREMENTS,
    LIGHT_FIXTURE_REQUIREMENTS,
    add_interior_details,
)
from lib.interiors.types import FloorPlan, Room


class TestMoldingType:
    """Tests for MoldingType enum."""

    def test_molding_type_values(self):
        """Test MoldingType enum values."""
        assert MoldingType.BASEBOARD.value == "baseboard"
        assert MoldingType.CROWN.value == "crown"
        assert MoldingType.CHAIR_RAIL.value == "chair_rail"
        assert MoldingType.WAINSCOTING.value == "wainscoting"


class TestFixtureType:
    """Tests for FixtureType enum."""

    def test_fixture_type_values(self):
        """Test FixtureType enum values."""
        assert FixtureType.CEILING_LIGHT.value == "ceiling_light"
        assert FixtureType.WALL_SCONCE.value == "wall_sconce"
        assert FixtureType.RECESSED_LIGHT.value == "recessed_light"
        assert FixtureType.CEILING_FAN.value == "ceiling_fan"


class TestMoldingConfig:
    """Tests for MoldingConfig dataclass."""

    def test_create_default(self):
        """Test creating MoldingConfig with defaults."""
        config = MoldingConfig()
        assert config.molding_type == "baseboard"
        assert config.height == 0.1
        assert config.depth == 0.02
        assert config.material == "wood_white"

    def test_create_with_values(self):
        """Test creating MoldingConfig with values."""
        config = MoldingConfig(
            molding_type="crown",
            height=0.15,
            depth=0.1,
            material="wood_oak",
            style="colonial",
        )
        assert config.molding_type == "crown"
        assert config.style == "colonial"

    def test_to_dict(self):
        """Test MoldingConfig serialization."""
        config = MoldingConfig(molding_type="chair_rail", height=0.9)
        result = config.to_dict()
        assert result["molding_type"] == "chair_rail"
        assert result["height"] == 0.9


class TestFixtureConfig:
    """Tests for FixtureConfig dataclass."""

    def test_create_default(self):
        """Test creating FixtureConfig with defaults."""
        config = FixtureConfig()
        assert config.fixture_type == "ceiling_light"
        assert config.position == (0.0, 0.0, 2.8)
        assert config.size == 0.3

    def test_create_with_values(self):
        """Test creating FixtureConfig with values."""
        config = FixtureConfig(
            fixture_type="wall_sconce",
            position=(1.0, 2.0, 1.8),
            rotation=90.0,
            size=0.15,
            material="brass",
        )
        assert config.fixture_type == "wall_sconce"
        assert config.rotation == 90.0

    def test_to_dict(self):
        """Test FixtureConfig serialization."""
        config = FixtureConfig(fixture_type="recessed_light", size=0.15)
        result = config.to_dict()
        assert result["fixture_type"] == "recessed_light"
        assert result["size"] == 0.15


class TestRoomDetails:
    """Tests for RoomDetails dataclass."""

    def test_create_default(self):
        """Test creating RoomDetails with defaults."""
        details = RoomDetails()
        assert details.room_id == ""
        assert details.moldings == []
        assert details.fixtures == []
        assert details.has_baseboard is True

    def test_create_with_values(self):
        """Test creating RoomDetails with values."""
        moldings = [MoldingConfig(molding_type="baseboard")]
        fixtures = [FixtureConfig(fixture_type="ceiling_light")]
        details = RoomDetails(
            room_id="r1",
            moldings=moldings,
            fixtures=fixtures,
            has_crown_molding=True,
        )
        assert details.room_id == "r1"
        assert details.has_crown_molding is True

    def test_to_dict(self):
        """Test RoomDetails serialization."""
        details = RoomDetails(room_id="test", has_baseboard=True)
        result = details.to_dict()
        assert result["room_id"] == "test"
        assert result["has_baseboard"] is True


class TestDefaultMoldingConfigs:
    """Tests for DEFAULT_MOLDING_CONFIGS."""

    def test_configs_exist(self):
        """Test that configs are populated."""
        assert isinstance(DEFAULT_MOLDING_CONFIGS, dict)
        assert len(DEFAULT_MOLDING_CONFIGS) > 0

    def test_modern_style(self):
        """Test modern style molding configs."""
        assert "modern" in DEFAULT_MOLDING_CONFIGS
        modern = DEFAULT_MOLDING_CONFIGS["modern"]
        assert "baseboard" in modern

    def test_traditional_style(self):
        """Test traditional style molding configs."""
        assert "traditional" in DEFAULT_MOLDING_CONFIGS
        traditional = DEFAULT_MOLDING_CONFIGS["traditional"]
        assert "chair_rail" in traditional

    def test_all_styles_have_baseboard(self):
        """Test that all styles have baseboard config."""
        for style_name, style_config in DEFAULT_MOLDING_CONFIGS.items():
            assert "baseboard" in style_config, f"{style_name} missing baseboard"


class TestRoomMoldingRequirements:
    """Tests for ROOM_MOLDING_REQUIREMENTS."""

    def test_requirements_exist(self):
        """Test that requirements are populated."""
        assert isinstance(ROOM_MOLDING_REQUIREMENTS, dict)
        assert len(ROOM_MOLDING_REQUIREMENTS) > 0

    def test_living_room_requirements(self):
        """Test living room requirements."""
        assert "living_room" in ROOM_MOLDING_REQUIREMENTS
        reqs = ROOM_MOLDING_REQUIREMENTS["living_room"]
        assert reqs.get("baseboard") is True

    def test_dining_room_requirements(self):
        """Test dining room has chair rail."""
        assert "dining_room" in ROOM_MOLDING_REQUIREMENTS
        reqs = ROOM_MOLDING_REQUIREMENTS["dining_room"]
        assert reqs.get("chair_rail") is True


class TestLightFixtureRequirements:
    """Tests for LIGHT_FIXTURE_REQUIREMENTS."""

    def test_requirements_exist(self):
        """Test that requirements are populated."""
        assert isinstance(LIGHT_FIXTURE_REQUIREMENTS, dict)
        assert len(LIGHT_FIXTURE_REQUIREMENTS) > 0

    def test_living_room_lights(self):
        """Test living room light requirements."""
        assert "living_room" in LIGHT_FIXTURE_REQUIREMENTS
        reqs = LIGHT_FIXTURE_REQUIREMENTS["living_room"]
        assert "ceiling_light" in reqs

    def test_kitchen_lights(self):
        """Test kitchen has recessed lights."""
        assert "kitchen" in LIGHT_FIXTURE_REQUIREMENTS
        reqs = LIGHT_FIXTURE_REQUIREMENTS["kitchen"]
        assert "recessed_light" in reqs


class TestInteriorDetails:
    """Tests for InteriorDetails class."""

    def test_init(self):
        """Test InteriorDetails initialization."""
        details = InteriorDetails()
        assert details.style == "modern"

    def test_init_with_style(self):
        """Test InteriorDetails initialization with style."""
        details = InteriorDetails(style="traditional")
        assert details.style == "traditional"

    def test_generate_for_room_living_room(self):
        """Test generating details for living room."""
        generator = InteriorDetails(style="modern")
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        details = generator.generate_for_room(room)

        assert details.room_id == "r1"
        assert details.has_baseboard is True

    def test_generate_for_room_dining_room(self):
        """Test generating details for dining room."""
        generator = InteriorDetails(style="traditional")
        room = Room(
            id="r1",
            room_type="dining_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        details = generator.generate_for_room(room)

        assert details.has_chair_rail is True

    def test_generate_for_room_bathroom(self):
        """Test generating details for bathroom."""
        generator = InteriorDetails(style="modern")
        room = Room(
            id="r1",
            room_type="bathroom",
            polygon=[(0, 0), (2, 0), (2, 2.5), (0, 2.5)],
            height=2.4,
        )
        details = generator.generate_for_room(room)

        assert details.has_baseboard is True

    def test_generate_recessed_lights(self):
        """Test recessed light generation."""
        generator = InteriorDetails()
        lights = generator._generate_recessed_lights(
            bounds=(0, 0, 4, 4),
            height=2.8,
            count=4,
        )

        assert len(lights) == 4
        for light in lights:
            assert light.fixture_type == "recessed_light"

    def test_generate_wall_sconces_two(self):
        """Test wall sconce generation - 2 sconces."""
        generator = InteriorDetails()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        sconces = generator._generate_wall_sconces(room, 2)

        assert len(sconces) == 2
        for sconce in sconces:
            assert sconce.fixture_type == "wall_sconce"

    def test_generate_wall_sconces_four(self):
        """Test wall sconce generation - 4 sconces."""
        generator = InteriorDetails()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        sconces = generator._generate_wall_sconces(room, 4)

        assert len(sconces) == 4

    def test_unknown_room_type(self):
        """Test handling unknown room type."""
        generator = InteriorDetails()
        room = Room(
            id="r1",
            room_type="unknown_type",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        details = generator.generate_for_room(room)

        # Should use default requirements
        assert details.room_id == "r1"


class TestAddInteriorDetails:
    """Tests for add_interior_details function."""

    def test_add_to_plan(self):
        """Test adding details to floor plan."""
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        plan = FloorPlan(style="modern", rooms=[room])
        details = add_interior_details(plan)

        assert len(details) == 1
        assert details[0].room_id == "r1"

    def test_add_multiple_rooms(self):
        """Test adding details to multiple rooms."""
        room1 = Room(id="r1", room_type="living_room", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)], height=2.8)
        room2 = Room(id="r2", room_type="bedroom", polygon=[(5, 0), (10, 0), (10, 4), (5, 4)], height=2.8)
        plan = FloorPlan(rooms=[room1, room2])
        details = add_interior_details(plan)

        assert len(details) == 2

    def test_add_with_style_override(self):
        """Test adding details with style override."""
        room = Room(
            id="r1",
            room_type="dining_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        plan = FloorPlan(style="modern", rooms=[room])
        details = add_interior_details(plan, style="traditional")

        assert len(details) == 1


class TestInteriorDetailsEdgeCases:
    """Edge case tests for interior details."""

    def test_victorian_style(self):
        """Test Victorian style details."""
        generator = InteriorDetails(style="victorian")
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=3.0,
        )
        details = generator.generate_for_room(room)

        assert details.has_crown_molding is True

    def test_minimalist_style(self):
        """Test minimalist style details."""
        generator = InteriorDetails(style="minimalist")
        room = Room(
            id="r1",
            room_type="bedroom",
            polygon=[(0, 0), (4, 0), (4, 3), (0, 3)],
            height=2.4,
        )
        details = generator.generate_for_room(room)

        # Minimalist should have minimal moldings
        assert details.has_baseboard is True

    def test_unknown_style(self):
        """Test unknown style falls back to modern."""
        generator = InteriorDetails(style="unknown_style")
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
            height=2.8,
        )
        details = generator.generate_for_room(room)

        # Should still generate something
        assert details.room_id == "r1"

    def test_large_room(self):
        """Test details for large room."""
        generator = InteriorDetails()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (10, 0), (10, 8), (0, 8)],
            height=2.8,
        )
        details = generator.generate_for_room(room)

        # Should have more recessed lights for larger room
        assert len(details.fixtures) > 0
