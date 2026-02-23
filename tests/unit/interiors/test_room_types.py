"""
Tests for Room Types

Tests room type definitions and requirements.
"""

import pytest
from lib.interiors.room_types import (
    RoomRequirements,
    RoomTypeConfig,
    ROOM_TYPE_CONFIGS,
    get_room_requirements,
    get_room_config,
    list_room_types,
    get_adjacent_room_types,
)


class TestRoomRequirements:
    """Tests for RoomRequirements dataclass."""

    def test_create_default(self):
        """Test creating RoomRequirements with defaults."""
        reqs = RoomRequirements()
        assert reqs.min_width == 2.5
        assert reqs.min_depth == 2.5
        assert reqs.min_height == 2.4
        assert reqs.min_area == 6.0
        assert reqs.requires_window is False

    def test_create_with_values(self):
        """Test creating RoomRequirements with values."""
        reqs = RoomRequirements(
            min_width=3.5,
            min_depth=4.0,
            min_height=2.6,
            min_area=14.0,
            requires_window=True,
            requires_closet=True,
            max_doors=4,
            typical_doors=2,
        )
        assert reqs.min_width == 3.5
        assert reqs.requires_window is True
        assert reqs.typical_doors == 2

    def test_to_dict(self):
        """Test RoomRequirements serialization."""
        reqs = RoomRequirements(min_width=3.0, requires_window=True)
        result = reqs.to_dict()
        assert result["min_width"] == 3.0
        assert result["requires_window"] is True


class TestRoomTypeConfig:
    """Tests for RoomTypeConfig dataclass."""

    def test_create_default(self):
        """Test creating RoomTypeConfig with defaults."""
        config = RoomTypeConfig()
        assert config.room_type == "living_room"
        assert config.name == "Living Room"
        assert config.description == "Main living space"

    def test_create_with_values(self):
        """Test creating RoomTypeConfig with values."""
        reqs = RoomRequirements(min_width=3.5)
        config = RoomTypeConfig(
            room_type="master_bedroom",
            name="Master Bedroom",
            description="Primary bedroom",
            requirements=reqs,
            default_materials={"floor": "carpet"},
            typical_placement="rear",
            adjacency_requirements=["master_bathroom"],
        )
        assert config.room_type == "master_bedroom"
        assert config.requirements.min_width == 3.5
        assert "master_bathroom" in config.adjacency_requirements

    def test_to_dict(self):
        """Test RoomTypeConfig serialization."""
        config = RoomTypeConfig(room_type="kitchen", name="Kitchen")
        result = config.to_dict()
        assert result["room_type"] == "kitchen"
        assert result["name"] == "Kitchen"


class TestRoomTypeConfigs:
    """Tests for ROOM_TYPE_CONFIGS dict."""

    def test_configs_exist(self):
        """Test that configs are populated."""
        assert isinstance(ROOM_TYPE_CONFIGS, dict)
        assert len(ROOM_TYPE_CONFIGS) > 0

    def test_living_room_config(self):
        """Test living room configuration."""
        assert "living_room" in ROOM_TYPE_CONFIGS
        config = ROOM_TYPE_CONFIGS["living_room"]
        assert config.name == "Living Room"
        assert config.requirements.requires_window is True

    def test_master_bedroom_config(self):
        """Test master bedroom configuration."""
        assert "master_bedroom" in ROOM_TYPE_CONFIGS
        config = ROOM_TYPE_CONFIGS["master_bedroom"]
        assert config.requirements.requires_closet is True

    def test_bathroom_config(self):
        """Test bathroom configuration."""
        assert "bathroom" in ROOM_TYPE_CONFIGS
        config = ROOM_TYPE_CONFIGS["bathroom"]
        assert config.requirements.requires_window is False

    def test_kitchen_config(self):
        """Test kitchen configuration."""
        assert "kitchen" in ROOM_TYPE_CONFIGS
        config = ROOM_TYPE_CONFIGS["kitchen"]
        assert config.typical_placement == "rear"

    def test_all_configs_have_requirements(self):
        """Test that all configs have requirements."""
        for room_type, config in ROOM_TYPE_CONFIGS.items():
            assert config.requirements is not None
            assert config.requirements.min_width > 0

    def test_all_configs_have_materials(self):
        """Test that all configs have default materials."""
        for room_type, config in ROOM_TYPE_CONFIGS.items():
            assert len(config.default_materials) > 0
            assert "floor" in config.default_materials


class TestGetRoomRequirements:
    """Tests for get_room_requirements function."""

    def test_get_living_room(self):
        """Test getting living room requirements."""
        reqs = get_room_requirements("living_room")
        assert reqs.min_width == 3.5
        assert reqs.requires_window is True

    def test_get_bedroom(self):
        """Test getting bedroom requirements."""
        reqs = get_room_requirements("bedroom")
        assert reqs.min_width == 3.0
        assert reqs.requires_closet is True

    def test_get_unknown_type(self):
        """Test getting unknown room type returns default."""
        reqs = get_room_requirements("nonexistent_room")
        assert reqs.min_width == 2.5  # Default value


class TestGetRoomConfig:
    """Tests for get_room_config function."""

    def test_get_valid(self):
        """Test getting valid room config."""
        config = get_room_config("living_room")
        assert config is not None
        assert config.name == "Living Room"

    def test_get_invalid(self):
        """Test getting invalid room config."""
        config = get_room_config("nonexistent_room")
        assert config is None


class TestListRoomTypes:
    """Tests for list_room_types function."""

    def test_list(self):
        """Test listing room types."""
        types = list_room_types()
        assert isinstance(types, list)
        assert len(types) > 0

    def test_list_includes_common_types(self):
        """Test that common types are included."""
        types = list_room_types()
        assert "living_room" in types
        assert "bedroom" in types
        assert "kitchen" in types
        assert "bathroom" in types


class TestGetAdjacentRoomTypes:
    """Tests for get_adjacent_room_types function."""

    def test_living_room_adjacent(self):
        """Test living room adjacency."""
        adjacent = get_adjacent_room_types("living_room")
        assert "kitchen" in adjacent
        assert "dining_room" in adjacent

    def test_master_bedroom_adjacent(self):
        """Test master bedroom adjacency."""
        adjacent = get_adjacent_room_types("master_bedroom")
        assert "master_bathroom" in adjacent
        assert "closet" in adjacent

    def test_kitchen_adjacent(self):
        """Test kitchen adjacency."""
        adjacent = get_adjacent_room_types("kitchen")
        assert "dining_room" in adjacent

    def test_unknown_type(self):
        """Test unknown room type adjacency."""
        adjacent = get_adjacent_room_types("nonexistent_room")
        assert adjacent == []


class TestRoomTypeConfigsDetailed:
    """Detailed tests for specific room type configs."""

    def test_dining_room(self):
        """Test dining room config details."""
        config = ROOM_TYPE_CONFIGS["dining_room"]
        assert config.requirements.min_area == 10.0
        assert config.typical_placement == "front"

    def test_office(self):
        """Test office config details."""
        config = ROOM_TYPE_CONFIGS["office"]
        assert config.requirements.requires_window is True
        assert config.requirements.max_doors == 2

    def test_half_bath(self):
        """Test half bath config details."""
        config = ROOM_TYPE_CONFIGS["half_bath"]
        assert config.requirements.min_width == 1.2
        assert config.requirements.min_area == 2.0

    def test_laundry(self):
        """Test laundry room config details."""
        config = ROOM_TYPE_CONFIGS["laundry"]
        assert config.requirements.min_area == 2.5

    def test_hallway(self):
        """Test hallway config details."""
        config = ROOM_TYPE_CONFIGS["hallway"]
        assert config.requirements.max_doors == 10  # Hallways connect many rooms
        assert config.typical_placement == "center"

    def test_foyer(self):
        """Test foyer config details."""
        config = ROOM_TYPE_CONFIGS["foyer"]
        assert config.typical_placement == "front"
        assert "living_room" in config.adjacency_requirements

    def test_walk_in_closet(self):
        """Test walk-in closet config details."""
        config = ROOM_TYPE_CONFIGS["walk_in_closet"]
        assert config.requirements.min_area == 3.0
        assert "master_bedroom" in config.adjacency_requirements


class TestRoomRequirementsValidation:
    """Tests for room requirement validation scenarios."""

    def test_master_bedroom_requirements(self):
        """Test master bedroom has proper requirements."""
        reqs = get_room_requirements("master_bedroom")
        assert reqs.min_width >= 3.5  # Should be larger than regular bedroom
        assert reqs.requires_window is True
        assert reqs.requires_closet is True

    def test_bathroom_requirements(self):
        """Test bathroom has proper requirements."""
        reqs = get_room_requirements("bathroom")
        assert reqs.min_width <= 2.0  # Bathrooms can be smaller
        assert reqs.max_doors == 1  # Usually single door

    def test_master_bathroom_requirements(self):
        """Test master bathroom has larger requirements."""
        master_reqs = get_room_requirements("master_bathroom")
        regular_reqs = get_room_requirements("bathroom")
        assert master_reqs.min_area > regular_reqs.min_area
