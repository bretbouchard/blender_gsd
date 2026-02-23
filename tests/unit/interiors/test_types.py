"""
Tests for Interior Layout Types

Tests dataclasses and enums for floor plans, rooms, and connections.
"""

import pytest
import json
from lib.interiors.types import (
    RoomType,
    InteriorStyle,
    DoorType,
    WindowType,
    DoorSpec,
    WindowSpec,
    Room,
    Connection,
    FurniturePlacement,
    FloorPlan,
    validate_room,
    validate_floor_plan,
)


class TestEnums:
    """Tests for enum types."""

    def test_room_type_values(self):
        """Test RoomType enum values."""
        assert RoomType.LIVING_ROOM.value == "living_room"
        assert RoomType.BEDROOM.value == "bedroom"
        assert RoomType.KITCHEN.value == "kitchen"
        assert RoomType.BATHROOM.value == "bathroom"
        assert RoomType.OFFICE.value == "office"

    def test_interior_style_values(self):
        """Test InteriorStyle enum values."""
        assert InteriorStyle.MODERN.value == "modern"
        assert InteriorStyle.CONTEMPORARY.value == "contemporary"
        assert InteriorStyle.MINIMALIST.value == "minimalist"
        assert InteriorStyle.INDUSTRIAL.value == "industrial"
        assert InteriorStyle.TRADITIONAL.value == "traditional"

    def test_door_type_values(self):
        """Test DoorType enum values."""
        assert DoorType.STANDARD.value == "standard"
        assert DoorType.POCKET.value == "pocket"
        assert DoorType.SLIDING.value == "sliding"
        assert DoorType.FRENCH.value == "french"

    def test_window_type_values(self):
        """Test WindowType enum values."""
        assert WindowType.SINGLE_HUNG.value == "single_hung"
        assert WindowType.DOUBLE_HUNG.value == "double_hung"
        assert WindowType.CASEMENT.value == "casement"
        assert WindowType.PICTURE.value == "picture"


class TestDoorSpec:
    """Tests for DoorSpec dataclass."""

    def test_create_default(self):
        """Test creating DoorSpec with defaults."""
        spec = DoorSpec()
        assert spec.wall_index == 0
        assert spec.position == 0.5
        assert spec.width == 0.9
        assert spec.height == 2.1
        assert spec.door_type == "standard"

    def test_create_with_values(self):
        """Test creating DoorSpec with values."""
        spec = DoorSpec(
            wall_index=2,
            position=0.3,
            width=1.0,
            height=2.2,
            door_type="french",
            swing_direction="out_left",
        )
        assert spec.wall_index == 2
        assert spec.position == 0.3
        assert spec.width == 1.0
        assert spec.door_type == "french"

    def test_to_dict(self):
        """Test DoorSpec serialization."""
        spec = DoorSpec(wall_index=1, position=0.5)
        result = spec.to_dict()
        assert result["wall_index"] == 1
        assert result["position"] == 0.5

    def test_from_dict(self):
        """Test DoorSpec deserialization."""
        data = {"wall_index": 2, "position": 0.7, "width": 1.0}
        spec = DoorSpec.from_dict(data)
        assert spec.wall_index == 2
        assert spec.position == 0.7
        assert spec.width == 1.0


class TestWindowSpec:
    """Tests for WindowSpec dataclass."""

    def test_create_default(self):
        """Test creating WindowSpec with defaults."""
        spec = WindowSpec()
        assert spec.wall_index == 0
        assert spec.position == 0.5
        assert spec.width == 1.2
        assert spec.height == 1.4
        assert spec.sill_height == 0.9

    def test_create_with_values(self):
        """Test creating WindowSpec with values."""
        spec = WindowSpec(
            wall_index=1,
            position=0.5,
            width=1.5,
            height=1.8,
            sill_height=1.0,
            window_type="casement",
        )
        assert spec.wall_index == 1
        assert spec.width == 1.5
        assert spec.window_type == "casement"

    def test_to_dict(self):
        """Test WindowSpec serialization."""
        spec = WindowSpec(wall_index=1, width=1.5)
        result = spec.to_dict()
        assert result["wall_index"] == 1
        assert result["width"] == 1.5

    def test_from_dict(self):
        """Test WindowSpec deserialization."""
        data = {"wall_index": 2, "width": 1.8, "sill_height": 1.1}
        spec = WindowSpec.from_dict(data)
        assert spec.wall_index == 2
        assert spec.width == 1.8


class TestRoom:
    """Tests for Room dataclass."""

    def test_create_default(self):
        """Test creating Room with defaults."""
        room = Room()
        assert room.id == "room_0"
        assert room.room_type == "living_room"
        assert room.polygon == []
        assert room.height == 2.8

    def test_create_with_values(self):
        """Test creating Room with values."""
        polygon = [(0, 0), (5, 0), (5, 4), (0, 4)]
        room = Room(
            id="living_01",
            room_type="living_room",
            polygon=polygon,
            height=3.0,
            floor_material="hardwood_oak",
            wall_material="drywall_white",
        )
        assert room.id == "living_01"
        assert len(room.polygon) == 4
        assert room.height == 3.0

    def test_center_property(self):
        """Test room center calculation."""
        room = Room(polygon=[(0, 0), (4, 0), (4, 4), (0, 4)])
        center = room.center
        assert center == (2.0, 2.0)

    def test_center_empty_polygon(self):
        """Test center with empty polygon."""
        room = Room(polygon=[])
        assert room.center == (0.0, 0.0)

    def test_area_property(self):
        """Test room area calculation using shoelace formula."""
        room = Room(polygon=[(0, 0), (4, 0), (4, 3), (0, 3)])
        assert room.area == 12.0

    def test_area_triangle(self):
        """Test area with triangular room."""
        room = Room(polygon=[(0, 0), (4, 0), (2, 3)])
        assert room.area == 6.0

    def test_area_empty_polygon(self):
        """Test area with empty polygon."""
        room = Room(polygon=[])
        assert room.area == 0.0

    def test_bounds_property(self):
        """Test room bounds calculation."""
        room = Room(polygon=[(1, 2), (5, 2), (5, 6), (1, 6)])
        bounds = room.bounds
        assert bounds == (1.0, 2.0, 5.0, 6.0)

    def test_get_wall_length(self):
        """Test wall length calculation."""
        room = Room(polygon=[(0, 0), (4, 0), (4, 3), (0, 3)])
        assert room.get_wall_length(0) == 4.0  # Bottom wall
        assert room.get_wall_length(1) == 3.0  # Right wall

    def test_name_auto_generation(self):
        """Test automatic name generation from room type."""
        room = Room(room_type="master_bedroom")
        assert room.name == "Master Bedroom"

    def test_to_dict(self):
        """Test Room serialization."""
        room = Room(id="test", room_type="kitchen", polygon=[(0, 0), (1, 0), (1, 1), (0, 1)])
        result = room.to_dict()
        assert result["id"] == "test"
        assert result["room_type"] == "kitchen"
        assert result["area"] == 1.0

    def test_from_dict(self):
        """Test Room deserialization."""
        data = {
            "id": "room_01",
            "room_type": "bedroom",
            "polygon": [[0, 0], [2, 0], [2, 2], [0, 2]],
            "height": 2.8,
        }
        room = Room.from_dict(data)
        assert room.id == "room_01"
        assert room.room_type == "bedroom"
        assert len(room.polygon) == 4


class TestConnection:
    """Tests for Connection dataclass."""

    def test_create_default(self):
        """Test creating Connection with defaults."""
        conn = Connection()
        assert conn.id == "conn_0"
        assert conn.room_a_id == ""
        assert conn.room_b_id == ""
        assert conn.door_spec is None
        assert conn.is_open is False

    def test_create_with_values(self):
        """Test creating Connection with values."""
        door = DoorSpec(width=1.0)
        conn = Connection(
            id="conn_01",
            room_a_id="room_a",
            room_b_id="room_b",
            door_spec=door,
            is_open=False,
        )
        assert conn.id == "conn_01"
        assert conn.room_a_id == "room_a"
        assert conn.door_spec.width == 1.0

    def test_to_dict(self):
        """Test Connection serialization."""
        conn = Connection(id="test", room_a_id="a", room_b_id="b")
        result = conn.to_dict()
        assert result["id"] == "test"
        assert result["room_a_id"] == "a"

    def test_from_dict(self):
        """Test Connection deserialization."""
        data = {"id": "conn_01", "room_a_id": "r1", "room_b_id": "r2"}
        conn = Connection.from_dict(data)
        assert conn.id == "conn_01"
        assert conn.room_a_id == "r1"


class TestFurniturePlacement:
    """Tests for FurniturePlacement dataclass."""

    def test_create_default(self):
        """Test creating FurniturePlacement with defaults."""
        placement = FurniturePlacement()
        assert placement.furniture_type == ""
        assert placement.position == (0.0, 0.0, 0.0)
        assert placement.rotation == 0.0
        assert placement.scale == 1.0

    def test_create_with_values(self):
        """Test creating FurniturePlacement with values."""
        placement = FurniturePlacement(
            furniture_type="sofa",
            position=(5.0, 3.0, 0.0),
            rotation=45.0,
            scale=1.2,
            variant=2,
        )
        assert placement.furniture_type == "sofa"
        assert placement.position == (5.0, 3.0, 0.0)
        assert placement.rotation == 45.0

    def test_to_dict(self):
        """Test FurniturePlacement serialization."""
        placement = FurniturePlacement(furniture_type="chair", position=(1, 2, 0))
        result = placement.to_dict()
        assert result["furniture_type"] == "chair"
        assert result["position"] == [1, 2, 0]

    def test_from_dict(self):
        """Test FurniturePlacement deserialization."""
        data = {"furniture_type": "table", "position": [3, 4, 0], "rotation": 90}
        placement = FurniturePlacement.from_dict(data)
        assert placement.furniture_type == "table"
        assert placement.rotation == 90


class TestFloorPlan:
    """Tests for FloorPlan dataclass."""

    def test_create_default(self):
        """Test creating FloorPlan with defaults."""
        plan = FloorPlan()
        assert plan.version == "1.0"
        assert plan.dimensions == (10.0, 8.0)
        assert plan.rooms == []
        assert plan.style == "modern"

    def test_create_with_values(self):
        """Test creating FloorPlan with values."""
        room = Room(id="r1", room_type="living_room", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)])
        plan = FloorPlan(
            dimensions=(10.0, 8.0),
            rooms=[room],
            style="contemporary",
            wall_height=3.0,
            seed=42,
        )
        assert len(plan.rooms) == 1
        assert plan.style == "contemporary"
        assert plan.seed == 42

    def test_total_area_property(self):
        """Test total area calculation."""
        room1 = Room(polygon=[(0, 0), (4, 0), (4, 3), (0, 3)])
        room2 = Room(polygon=[(4, 0), (8, 0), (8, 3), (4, 3)])
        plan = FloorPlan(rooms=[room1, room2])
        assert plan.total_area == 24.0

    def test_get_room_by_id(self):
        """Test getting room by ID."""
        room1 = Room(id="r1")
        room2 = Room(id="r2")
        plan = FloorPlan(rooms=[room1, room2])
        assert plan.get_room_by_id("r1") == room1
        assert plan.get_room_by_id("r2") == room2
        assert plan.get_room_by_id("r3") is None

    def test_get_connected_rooms(self):
        """Test getting connected rooms."""
        plan = FloorPlan(
            rooms=[Room(id="a"), Room(id="b"), Room(id="c")],
            connections=[
                Connection(room_a_id="a", room_b_id="b"),
                Connection(room_a_id="a", room_b_id="c"),
            ],
        )
        connected = plan.get_connected_rooms("a")
        assert "b" in connected
        assert "c" in connected

    def test_is_connected_true(self):
        """Test connectivity check - connected."""
        plan = FloorPlan(
            rooms=[Room(id="a"), Room(id="b")],
            connections=[Connection(room_a_id="a", room_b_id="b")],
        )
        assert plan.is_connected() is True

    def test_is_connected_false(self):
        """Test connectivity check - not connected."""
        plan = FloorPlan(
            rooms=[Room(id="a"), Room(id="b")],
            connections=[],
        )
        assert plan.is_connected() is False

    def test_is_connected_empty(self):
        """Test connectivity check - empty plan."""
        plan = FloorPlan()
        assert plan.is_connected() is True

    def test_to_dict(self):
        """Test FloorPlan serialization."""
        plan = FloorPlan(dimensions=(10, 8), style="modern")
        result = plan.to_dict()
        assert result["dimensions"] == [10, 8]
        assert result["style"] == "modern"

    def test_from_dict(self):
        """Test FloorPlan deserialization."""
        data = {
            "version": "1.0",
            "dimensions": [12, 10],
            "rooms": [],
            "style": "industrial",
        }
        plan = FloorPlan.from_dict(data)
        assert plan.dimensions == (12, 10)
        assert plan.style == "industrial"

    def test_to_json(self):
        """Test JSON export."""
        plan = FloorPlan(dimensions=(10, 8))
        json_str = plan.to_json()
        data = json.loads(json_str)
        assert data["dimensions"] == [10, 8]

    def test_from_json(self):
        """Test JSON import."""
        json_str = '{"version": "1.0", "dimensions": [10, 8], "rooms": [], "style": "modern"}'
        plan = FloorPlan.from_json(json_str)
        assert plan.dimensions == (10, 8)


class TestValidateRoom:
    """Tests for room validation."""

    def test_valid_room(self):
        """Test valid room passes validation."""
        room = Room(
            id="r1",
            polygon=[(0, 0), (4, 0), (4, 3), (0, 3)],
            height=2.8,
        )
        errors = validate_room(room)
        assert len(errors) == 0

    def test_invalid_polygon(self):
        """Test room with too few vertices."""
        room = Room(id="r1", polygon=[(0, 0), (1, 0)])
        errors = validate_room(room)
        assert len(errors) > 0
        assert "polygon" in errors[0].lower()

    def test_invalid_height(self):
        """Test room with invalid height."""
        room = Room(id="r1", polygon=[(0, 0), (1, 0), (1, 1), (0, 1)], height=0)
        errors = validate_room(room)
        assert len(errors) > 0
        assert "height" in errors[0].lower()

    def test_invalid_door_width(self):
        """Test door with invalid width."""
        room = Room(
            id="r1",
            polygon=[(0, 0), (4, 0), (4, 3), (0, 3)],
            doors=[DoorSpec(width=0)],
        )
        errors = validate_room(room)
        assert len(errors) > 0
        assert "width" in errors[0].lower()

    def test_invalid_door_position(self):
        """Test door with invalid position."""
        room = Room(
            id="r1",
            polygon=[(0, 0), (4, 0), (4, 3), (0, 3)],
            doors=[DoorSpec(position=1.5)],
        )
        errors = validate_room(room)
        assert len(errors) > 0


class TestValidateFloorPlan:
    """Tests for floor plan validation."""

    def test_valid_plan(self):
        """Test valid floor plan passes validation."""
        room = Room(id="r1", polygon=[(0, 0), (4, 0), (4, 3), (0, 3)])
        plan = FloorPlan(dimensions=(10, 8), rooms=[room])
        errors = validate_floor_plan(plan)
        # May have connectivity error since single room
        assert all("dimensions" not in e.lower() for e in errors)

    def test_invalid_dimensions(self):
        """Test plan with invalid dimensions."""
        plan = FloorPlan(dimensions=(0, 8))
        errors = validate_floor_plan(plan)
        assert len(errors) > 0
        assert "dimensions" in errors[0].lower()

    def test_no_rooms(self):
        """Test plan with no rooms."""
        plan = FloorPlan(dimensions=(10, 8), rooms=[])
        errors = validate_floor_plan(plan)
        assert len(errors) > 0
        assert "room" in errors[0].lower()

    def test_invalid_connection(self):
        """Test connection to non-existent room."""
        room = Room(id="r1", polygon=[(0, 0), (4, 0), (4, 3), (0, 3)])
        conn = Connection(room_a_id="r1", room_b_id="nonexistent")
        plan = FloorPlan(dimensions=(10, 8), rooms=[room], connections=[conn])
        errors = validate_floor_plan(plan)
        assert any("not found" in e.lower() for e in errors)
