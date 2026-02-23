"""
Unit tests for lib/geometry_nodes/room_builder.py

Tests the room builder system including:
- WallType enum
- OpeningType enum
- WallSpec dataclass
- OpeningSpec dataclass
- RoomGeometry dataclass
- STANDARD_DOORS
- STANDARD_WINDOWS
- WALL_MATERIALS
- RoomBuilder class
- RoomBuilderGN class
- build_rooms function
- rooms_to_gn_format function
"""

import pytest
import json
import math

from lib.geometry_nodes.room_builder import (
    WallType,
    OpeningType,
    WallSpec,
    OpeningSpec,
    RoomGeometry,
    STANDARD_DOORS,
    STANDARD_WINDOWS,
    WALL_MATERIALS,
    RoomBuilder,
    RoomBuilderGN,
    build_rooms,
    rooms_to_gn_format,
)


class TestWallType:
    """Tests for WallType enum."""

    def test_wall_type_values(self):
        """Test that WallType enum has expected values."""
        assert WallType.EXTERIOR.value == "exterior"
        assert WallType.INTERIOR.value == "interior"
        assert WallType.PARTITION.value == "partition"
        assert WallType.LOAD_BEARING.value == "load_bearing"

    def test_wall_type_count(self):
        """Test that all expected wall types exist."""
        assert len(WallType) == 4


class TestOpeningType:
    """Tests for OpeningType enum."""

    def test_opening_type_values(self):
        """Test that OpeningType enum has expected values."""
        assert OpeningType.DOOR.value == "door"
        assert OpeningType.WINDOW.value == "window"
        assert OpeningType.ARCHWAY.value == "archway"
        assert OpeningType.PASSAGE.value == "passage"

    def test_opening_type_count(self):
        """Test that all expected opening types exist."""
        assert len(OpeningType) == 4


class TestWallSpec:
    """Tests for WallSpec dataclass."""

    def test_default_values(self):
        """Test WallSpec default values."""
        wall = WallSpec()
        assert wall.wall_id == ""
        assert wall.start == (0.0, 0.0)
        assert wall.end == (1.0, 0.0)
        assert wall.height == 3.0
        assert wall.thickness == 0.15
        assert wall.wall_type == "interior"
        assert wall.openings == []
        assert wall.material == "drywall"

    def test_custom_values(self):
        """Test WallSpec with custom values."""
        wall = WallSpec(
            wall_id="wall_001",
            start=(0.0, 0.0),
            end=(5.0, 0.0),
            height=3.5,
            thickness=0.2,
            wall_type="exterior",
            material="brick",
        )
        assert wall.wall_id == "wall_001"
        assert wall.start == (0.0, 0.0)
        assert wall.end == (5.0, 0.0)
        assert wall.height == 3.5
        assert wall.thickness == 0.2
        assert wall.wall_type == "exterior"

    def test_length_horizontal(self):
        """Test WallSpec.length for horizontal wall."""
        wall = WallSpec(start=(0.0, 0.0), end=(10.0, 0.0))
        assert wall.length == pytest.approx(10.0, rel=0.01)

    def test_length_vertical(self):
        """Test WallSpec.length for vertical wall."""
        wall = WallSpec(start=(0.0, 0.0), end=(0.0, 5.0))
        assert wall.length == pytest.approx(5.0, rel=0.01)

    def test_length_diagonal(self):
        """Test WallSpec.length for diagonal wall."""
        wall = WallSpec(start=(0.0, 0.0), end=(3.0, 4.0))
        assert wall.length == pytest.approx(5.0, rel=0.01)

    def test_angle_horizontal(self):
        """Test WallSpec.angle for horizontal wall."""
        wall = WallSpec(start=(0.0, 0.0), end=(10.0, 0.0))
        assert wall.angle == pytest.approx(0.0, rel=0.01)

    def test_angle_vertical(self):
        """Test WallSpec.angle for vertical wall."""
        wall = WallSpec(start=(0.0, 0.0), end=(0.0, 10.0))
        assert wall.angle == pytest.approx(math.pi / 2, rel=0.01)

    def test_angle_diagonal(self):
        """Test WallSpec.angle for diagonal wall."""
        wall = WallSpec(start=(0.0, 0.0), end=(1.0, 1.0))
        assert wall.angle == pytest.approx(math.pi / 4, rel=0.01)

    def test_to_dict(self):
        """Test WallSpec.to_dict() serialization."""
        wall = WallSpec(
            wall_id="wall_001",
            start=(0.0, 0.0),
            end=(5.0, 0.0),
            openings=[{"opening_type": "door"}],
        )
        data = wall.to_dict()
        assert data["wall_id"] == "wall_001"
        assert data["start"] == [0.0, 0.0]
        assert data["end"] == [5.0, 0.0]
        assert len(data["openings"]) == 1


class TestOpeningSpec:
    """Tests for OpeningSpec dataclass."""

    def test_default_values(self):
        """Test OpeningSpec default values."""
        opening = OpeningSpec()
        assert opening.opening_type == "door"
        assert opening.position == 0.5
        assert opening.width == 0.9
        assert opening.height == 2.1
        assert opening.sill_height == 0.0
        assert opening.frame_width == 0.05
        assert opening.frame_depth == 0.02

    def test_custom_values(self):
        """Test OpeningSpec with custom values."""
        opening = OpeningSpec(
            opening_type="window",
            position=0.3,
            width=1.5,
            height=1.2,
            sill_height=0.9,
        )
        assert opening.opening_type == "window"
        assert opening.position == 0.3
        assert opening.width == 1.5
        assert opening.height == 1.2
        assert opening.sill_height == 0.9

    def test_to_dict(self):
        """Test OpeningSpec.to_dict() serialization."""
        opening = OpeningSpec(
            opening_type="door",
            width=1.0,
            height=2.2,
        )
        data = opening.to_dict()
        assert data["opening_type"] == "door"
        assert data["width"] == 1.0
        assert data["height"] == 2.2


class TestRoomGeometry:
    """Tests for RoomGeometry dataclass."""

    def test_default_values(self):
        """Test RoomGeometry default values."""
        room = RoomGeometry()
        assert room.room_id == ""
        assert room.walls == []
        assert room.floor == []
        assert room.ceiling == []
        assert room.bounds == (0.0, 0.0, 1.0, 1.0)

    def test_custom_values(self):
        """Test RoomGeometry with custom values."""
        room = RoomGeometry(
            room_id="room_001",
            walls=[WallSpec(wall_id="wall_001")],
            floor=[(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)],
            bounds=(0.0, 0.0, 5.0, 4.0),
        )
        assert room.room_id == "room_001"
        assert len(room.walls) == 1
        assert len(room.floor) == 4
        assert room.bounds == (0.0, 0.0, 5.0, 4.0)

    def test_to_dict(self):
        """Test RoomGeometry.to_dict() serialization."""
        room = RoomGeometry(
            room_id="room_001",
            walls=[WallSpec(wall_id="wall_001")],
            floor=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        )
        data = room.to_dict()
        assert data["room_id"] == "room_001"
        assert len(data["walls"]) == 1
        assert len(data["floor"]) == 4


class TestStandardDoors:
    """Tests for STANDARD_DOORS dictionary."""

    def test_standard_exists(self):
        """Test that standard door exists."""
        assert "standard" in STANDARD_DOORS
        door = STANDARD_DOORS["standard"]
        assert door.width == 0.9
        assert door.height == 2.1

    def test_wide_exists(self):
        """Test that wide door exists."""
        assert "wide" in STANDARD_DOORS
        door = STANDARD_DOORS["wide"]
        assert door.width == 1.2

    def test_double_exists(self):
        """Test that double door exists."""
        assert "double" in STANDARD_DOORS
        door = STANDARD_DOORS["double"]
        assert door.width == 1.8

    def test_sliding_exists(self):
        """Test that sliding door exists."""
        assert "sliding" in STANDARD_DOORS
        door = STANDARD_DOORS["sliding"]
        assert door.width == 2.0

    def test_all_doors_have_no_sill(self):
        """Test that all doors have no sill height."""
        for name, door in STANDARD_DOORS.items():
            assert door.sill_height == 0.0


class TestStandardWindows:
    """Tests for STANDARD_WINDOWS dictionary."""

    def test_standard_exists(self):
        """Test that standard window exists."""
        assert "standard" in STANDARD_WINDOWS
        window = STANDARD_WINDOWS["standard"]
        assert window.width == 1.2
        assert window.height == 1.2

    def test_picture_exists(self):
        """Test that picture window exists."""
        assert "picture" in STANDARD_WINDOWS
        window = STANDARD_WINDOWS["picture"]
        assert window.width == 1.8

    def test_tall_exists(self):
        """Test that tall window exists."""
        assert "tall" in STANDARD_WINDOWS
        window = STANDARD_WINDOWS["tall"]
        assert window.height == 1.8

    def test_skylight_exists(self):
        """Test that skylight exists."""
        assert "skylight" in STANDARD_WINDOWS
        window = STANDARD_WINDOWS["skylight"]
        assert window.sill_height == 0.0

    def test_all_windows_have_sill_height(self):
        """Test that non-skylight windows have sill height."""
        for name, window in STANDARD_WINDOWS.items():
            if name != "skylight":
                assert window.sill_height > 0.0


class TestWallMaterials:
    """Tests for WALL_MATERIALS dictionary."""

    def test_drywall_exists(self):
        """Test that drywall material exists."""
        assert "drywall" in WALL_MATERIALS
        mat = WALL_MATERIALS["drywall"]
        assert "color" in mat
        assert "roughness" in mat

    def test_concrete_exists(self):
        """Test that concrete material exists."""
        assert "concrete" in WALL_MATERIALS

    def test_brick_exists(self):
        """Test that brick material exists."""
        assert "brick" in WALL_MATERIALS
        mat = WALL_MATERIALS["brick"]
        assert "pattern" in mat

    def test_wood_panel_exists(self):
        """Test that wood panel material exists."""
        assert "wood_panel" in WALL_MATERIALS

    def test_glass_exists(self):
        """Test that glass material exists."""
        assert "glass" in WALL_MATERIALS
        mat = WALL_MATERIALS["glass"]
        assert "transmission" in mat

    def test_all_materials_have_required_properties(self):
        """Test that all materials have required properties."""
        required = ["color", "roughness", "specular"]
        for name, mat in WALL_MATERIALS.items():
            for prop in required:
                assert prop in mat, f"Material {name} missing {prop}"


class TestRoomBuilder:
    """Tests for RoomBuilder class."""

    def test_default_initialization(self):
        """Test RoomBuilder default initialization."""
        builder = RoomBuilder()
        assert builder.wall_height == 3.0
        assert builder.wall_thickness == 0.15
        assert builder.floor_thickness == 0.02

    def test_custom_initialization(self):
        """Test RoomBuilder with custom parameters."""
        builder = RoomBuilder(
            wall_height=2.8,
            wall_thickness=0.2,
            floor_thickness=0.03,
        )
        assert builder.wall_height == 2.8
        assert builder.wall_thickness == 0.2
        assert builder.floor_thickness == 0.03

    def test_build_from_dict_empty(self):
        """Test building from empty dictionary."""
        builder = RoomBuilder()
        rooms = builder.build_from_dict({})

        assert rooms == []

    def test_build_from_dict_single_room(self):
        """Test building from dictionary with single room."""
        builder = RoomBuilder()
        data = {
            "rooms": [
                {
                    "id": "room_001",
                    "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]],
                }
            ]
        }

        rooms = builder.build_from_dict(data)

        assert len(rooms) == 1
        assert rooms[0].room_id == "room_001"
        assert len(rooms[0].walls) == 4

    def test_build_from_dict_multiple_rooms(self):
        """Test building from dictionary with multiple rooms."""
        builder = RoomBuilder()
        data = {
            "rooms": [
                {"id": "room_001", "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 5.0]]},
                {"id": "room_002", "polygon": [[5.0, 0.0], [10.0, 0.0], [10.0, 5.0], [5.0, 5.0]]},
            ]
        }

        rooms = builder.build_from_dict(data)

        assert len(rooms) == 2
        assert rooms[0].room_id == "room_001"
        assert rooms[1].room_id == "room_002"

    def test_build_from_json(self):
        """Test building from JSON string."""
        builder = RoomBuilder()
        json_str = json.dumps({
            "rooms": [
                {"id": "room_001", "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]]}
            ]
        })

        rooms = builder.build_from_json(json_str)

        assert len(rooms) == 1
        assert rooms[0].room_id == "room_001"

    def test_build_room_with_doors(self):
        """Test building room with doors."""
        builder = RoomBuilder()
        data = {
            "id": "room_001",
            "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]],
            "doors": [{"wall": 0, "position": 0.5, "type": "standard"}],
        }

        room = builder._build_room(data)

        assert len(room.walls[0].openings) == 1
        assert room.walls[0].openings[0]["opening_type"] == "door"

    def test_build_room_with_windows(self):
        """Test building room with windows."""
        builder = RoomBuilder()
        data = {
            "id": "room_001",
            "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]],
            "windows": [{"wall": 1, "position": 0.5, "type": "standard"}],
        }

        room = builder._build_room(data)

        assert len(room.walls[1].openings) == 1
        assert room.walls[1].openings[0]["opening_type"] == "window"

    def test_build_room_with_multiple_openings(self):
        """Test building room with multiple openings on same wall."""
        builder = RoomBuilder()
        data = {
            "id": "room_001",
            "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]],
            "doors": [
                {"wall": 0, "position": 0.3},
                {"wall": 0, "position": 0.7},
            ],
        }

        room = builder._build_room(data)

        assert len(room.walls[0].openings) == 2

    def test_bounds_calculation(self):
        """Test bounds calculation from polygon."""
        builder = RoomBuilder()
        data = {
            "id": "room_001",
            "polygon": [[2.0, 3.0], [8.0, 3.0], [8.0, 9.0], [2.0, 9.0]],
        }

        room = builder._build_room(data)

        assert room.bounds[0] == pytest.approx(2.0, rel=0.01)  # min_x
        assert room.bounds[1] == pytest.approx(3.0, rel=0.01)  # min_y
        assert room.bounds[2] == pytest.approx(8.0, rel=0.01)  # max_x
        assert room.bounds[3] == pytest.approx(9.0, rel=0.01)  # max_y

    def test_create_door_opening_standard(self):
        """Test creating standard door opening."""
        builder = RoomBuilder()
        data = {"type": "standard", "position": 0.5}

        opening = builder._create_door_opening(data)

        assert opening["opening_type"] == "door"
        assert opening["width"] == 0.9
        assert opening["height"] == 2.1

    def test_create_door_opening_unknown_type(self):
        """Test creating door opening with unknown type."""
        builder = RoomBuilder()
        data = {"type": "nonexistent", "position": 0.5}

        opening = builder._create_door_opening(data)

        # Should fall back to standard
        assert opening["width"] == 0.9

    def test_create_window_opening_standard(self):
        """Test creating standard window opening."""
        builder = RoomBuilder()
        data = {"type": "standard", "position": 0.5}

        opening = builder._create_window_opening(data)

        assert opening["opening_type"] == "window"
        assert opening["width"] == 1.2
        assert opening["height"] == 1.2

    def test_create_window_opening_with_sill(self):
        """Test that window opening includes sill height."""
        builder = RoomBuilder()
        data = {"type": "tall", "position": 0.5}

        opening = builder._create_window_opening(data)

        assert opening["sill_height"] == 0.3

    def test_to_gn_input(self):
        """Test converting to GN input format."""
        builder = RoomBuilder()
        rooms = [RoomGeometry(room_id="room_001")]

        gn_data = builder.to_gn_input(rooms)

        assert "version" in gn_data
        assert "rooms" in gn_data
        assert "global_settings" in gn_data
        assert "materials" in gn_data
        assert gn_data["global_settings"]["wall_height"] == 3.0

    def test_to_gn_input_multiple_rooms(self):
        """Test GN input with multiple rooms."""
        builder = RoomBuilder()
        rooms = [
            RoomGeometry(room_id="room_001"),
            RoomGeometry(room_id="room_002"),
        ]

        gn_data = builder.to_gn_input(rooms)

        assert len(gn_data["rooms"]) == 2


class TestRoomBuilderGN:
    """Tests for RoomBuilderGN class."""

    def test_create_node_group_spec(self):
        """Test creating node group specification."""
        spec = RoomBuilderGN.create_node_group_spec()

        assert spec["name"] == "Room_Builder"
        assert "inputs" in spec
        assert "outputs" in spec
        assert "node_tree" in spec

    def test_node_group_spec_has_required_inputs(self):
        """Test that node group spec has required inputs."""
        spec = RoomBuilderGN.create_node_group_spec()
        required_inputs = ["Room_Data", "Wall_Height", "Wall_Thickness"]

        for input_name in required_inputs:
            assert input_name in spec["inputs"]

    def test_node_group_spec_has_required_outputs(self):
        """Test that node group spec has required outputs."""
        spec = RoomBuilderGN.create_node_group_spec()
        required_outputs = ["Geometry", "Wall_Mesh", "Floor_Mesh"]

        for output_name in required_outputs:
            assert output_name in spec["outputs"]


class TestBuildRooms:
    """Tests for build_rooms convenience function."""

    def test_build_rooms_basic(self):
        """Test basic room building."""
        data = {
            "rooms": [
                {"id": "room_001", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}
            ]
        }

        rooms = build_rooms(data)

        assert len(rooms) == 1
        assert rooms[0].room_id == "room_001"

    def test_build_rooms_with_options(self):
        """Test room building with options."""
        data = {
            "rooms": [
                {"id": "room_001", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]}
            ]
        }

        rooms = build_rooms(data, wall_height=2.8, wall_thickness=0.2)

        assert rooms[0].walls[0].height == 2.8
        assert rooms[0].walls[0].thickness == 0.2


class TestRoomsToGNFormat:
    """Tests for rooms_to_gn_format convenience function."""

    def test_rooms_to_gn_format_basic(self):
        """Test basic rooms to GN format conversion."""
        rooms = [RoomGeometry(room_id="room_001")]

        gn_data = rooms_to_gn_format(rooms)

        assert gn_data["rooms"][0]["room_id"] == "room_001"

    def test_rooms_to_gn_format_with_options(self):
        """Test GN format conversion with options."""
        rooms = [RoomGeometry(room_id="room_001")]

        gn_data = rooms_to_gn_format(rooms, wall_height=2.5)

        assert gn_data["global_settings"]["wall_height"] == 2.5


class TestRoomBuilderEdgeCases:
    """Edge case tests for RoomBuilder."""

    def test_build_room_no_polygon(self):
        """Test building room with no polygon raises error on bounds calculation."""
        builder = RoomBuilder()
        data = {"id": "room_001", "polygon": []}

        # Empty polygon causes ValueError when calculating bounds (min/max on empty list)
        with pytest.raises(ValueError, match="min\\(\\) arg is an empty sequence"):
            builder._build_room(data)

    def test_build_room_single_point(self):
        """Test building room with single point polygon."""
        builder = RoomBuilder()
        data = {"id": "room_001", "polygon": [[0.0, 0.0]]}

        room = builder._build_room(data)

        assert len(room.walls) == 1

    def test_build_room_triangle(self):
        """Test building triangular room."""
        builder = RoomBuilder()
        data = {"id": "room_001", "polygon": [[0.0, 0.0], [5.0, 0.0], [2.5, 4.0]]}

        room = builder._build_room(data)

        assert len(room.walls) == 3

    def test_wall_properties_applied(self):
        """Test that builder properties are applied to walls."""
        builder = RoomBuilder(wall_height=2.5, wall_thickness=0.25)
        data = {
            "id": "room_001",
            "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]],
        }

        room = builder._build_room(data)

        for wall in room.walls:
            assert wall.height == 2.5
            assert wall.thickness == 0.25

    def test_openings_on_correct_walls(self):
        """Test that openings are applied to correct walls."""
        builder = RoomBuilder()
        data = {
            "id": "room_001",
            "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 4.0], [0.0, 4.0]],
            "doors": [
                {"wall": 0, "position": 0.5},
                {"wall": 2, "position": 0.5},
            ],
        }

        room = builder._build_room(data)

        assert len(room.walls[0].openings) == 1
        assert len(room.walls[1].openings) == 0
        assert len(room.walls[2].openings) == 1
        assert len(room.walls[3].openings) == 0
