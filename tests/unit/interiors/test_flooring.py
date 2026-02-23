"""
Tests for Flooring Generator

Tests flooring patterns and tile generation.
"""

import pytest
from lib.interiors.flooring import (
    FlooringPattern,
    FlooringConfig,
    FloorTile,
    FlooringLayout,
    FlooringGenerator,
    DEFAULT_FLOORING,
    create_flooring_from_plan,
)
from lib.interiors.types import FloorPlan, Room


class TestFlooringPattern:
    """Tests for FlooringPattern enum."""

    def test_wood_patterns(self):
        """Test wood flooring pattern values."""
        assert FlooringPattern.HARDWOOD_PLANK.value == "hardwood_plank"
        assert FlooringPattern.HERRINGBONE.value == "herringbone"
        assert FlooringPattern.CHEVRON.value == "chevron"
        assert FlooringPattern.PARQUET.value == "parquet"

    def test_tile_patterns(self):
        """Test tile flooring pattern values."""
        assert FlooringPattern.GRID.value == "grid"
        assert FlooringPattern.BRICK.value == "brick"
        assert FlooringPattern.DIAMOND.value == "diamond"
        assert FlooringPattern.HEXAGON.value == "hexagon"

    def test_stone_patterns(self):
        """Test stone flooring pattern values."""
        assert FlooringPattern.FLAGSTONE.value == "flagstone"
        assert FlooringPattern.TERRAZZO.value == "terrazzo"


class TestFlooringConfig:
    """Tests for FlooringConfig dataclass."""

    def test_create_default(self):
        """Test creating FlooringConfig with defaults."""
        config = FlooringConfig()
        assert config.pattern == "hardwood_plank"
        assert config.material == "hardwood_oak"
        assert config.plank_width == 0.12
        assert config.plank_length == 1.2

    def test_create_with_values(self):
        """Test creating FlooringConfig with values."""
        config = FlooringConfig(
            pattern="herringbone",
            material="hardwood_walnut",
            plank_width=0.08,
            plank_length=0.4,
            gap_size=0.002,
            rotation=45.0,
        )
        assert config.pattern == "herringbone"
        assert config.plank_width == 0.08
        assert config.rotation == 45.0

    def test_to_dict(self):
        """Test FlooringConfig serialization."""
        config = FlooringConfig(pattern="grid", plank_width=0.3)
        result = config.to_dict()
        assert result["pattern"] == "grid"
        assert result["plank_width"] == 0.3


class TestFloorTile:
    """Tests for FloorTile dataclass."""

    def test_create_default(self):
        """Test creating FloorTile with defaults."""
        tile = FloorTile()
        assert tile.position == (0.0, 0.0, 0.0)
        assert tile.rotation == 0.0
        assert tile.width == 0.3
        assert tile.length == 0.3

    def test_create_with_values(self):
        """Test creating FloorTile with values."""
        tile = FloorTile(
            position=(5.0, 3.0, 0.0),
            rotation=0.785,  # 45 degrees
            width=0.15,
            length=1.2,
            material_index=2,
        )
        assert tile.position == (5.0, 3.0, 0.0)
        assert tile.material_index == 2

    def test_to_dict(self):
        """Test FloorTile serialization."""
        tile = FloorTile(position=(1, 2, 0), width=0.5)
        result = tile.to_dict()
        assert result["position"] == [1, 2, 0]
        assert result["width"] == 0.5


class TestFlooringLayout:
    """Tests for FlooringLayout dataclass."""

    def test_create_default(self):
        """Test creating FlooringLayout with defaults."""
        layout = FlooringLayout()
        assert layout.room_id == ""
        assert layout.tiles == []
        assert layout.total_tiles == 0

    def test_create_with_values(self):
        """Test creating FlooringLayout with values."""
        config = FlooringConfig(pattern="grid")
        tiles = [FloorTile(position=(0, 0, 0)), FloorTile(position=(1, 0, 0))]
        layout = FlooringLayout(
            room_id="r1",
            config=config,
            tiles=tiles,
            total_tiles=2,
            bounds=(0, 0, 5, 5),
        )
        assert layout.room_id == "r1"
        assert layout.total_tiles == 2

    def test_to_dict(self):
        """Test FlooringLayout serialization."""
        layout = FlooringLayout(room_id="test", total_tiles=5)
        result = layout.to_dict()
        assert result["room_id"] == "test"
        assert result["total_tiles"] == 5


class TestDefaultFlooring:
    """Tests for DEFAULT_FLOORING dict."""

    def test_defaults_exist(self):
        """Test that DEFAULT_FLOORING is populated."""
        assert isinstance(DEFAULT_FLOORING, dict)
        assert len(DEFAULT_FLOORING) > 0

    def test_common_room_types(self):
        """Test defaults for common room types."""
        assert "living_room" in DEFAULT_FLOORING
        assert "bedroom" in DEFAULT_FLOORING
        assert "kitchen" in DEFAULT_FLOORING
        assert "bathroom" in DEFAULT_FLOORING

    def test_default_configs_valid(self):
        """Test that default configs have valid patterns."""
        for room_type, config in DEFAULT_FLOORING.items():
            assert config.pattern is not None
            assert config.plank_width > 0


class TestFlooringGenerator:
    """Tests for FlooringGenerator class."""

    def test_init(self):
        """Test FlooringGenerator initialization."""
        generator = FlooringGenerator()
        assert generator.seed is None

    def test_init_with_seed(self):
        """Test FlooringGenerator initialization with seed."""
        generator = FlooringGenerator(seed=42)
        assert generator.seed == 42

    def test_generate_for_room(self):
        """Test generating flooring for room."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        layout = generator.generate_for_room(room)

        assert layout.room_id == "r1"
        assert len(layout.tiles) > 0

    def test_generate_for_room_with_config(self):
        """Test generating with custom config."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        config = FlooringConfig(pattern="grid", plank_width=0.5)
        layout = generator.generate_for_room(room, config)

        assert layout.config.pattern == "grid"

    def test_generate_for_empty_room(self):
        """Test generating for room with no polygon."""
        generator = FlooringGenerator()
        room = Room(id="r1", polygon=[])
        layout = generator.generate_for_room(room)

        assert layout.room_id == "r1"
        assert len(layout.tiles) == 0

    def test_generate_planks(self):
        """Test generating plank pattern."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        config = FlooringConfig(pattern="hardwood_plank", plank_width=0.15, plank_length=1.0)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_generate_grid(self):
        """Test generating grid pattern."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (3, 0), (3, 3), (0, 3)],
        )
        config = FlooringConfig(pattern="grid", plank_width=0.5)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_generate_brick(self):
        """Test generating brick pattern."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        config = FlooringConfig(pattern="brick", plank_width=0.1, plank_length=0.3)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_generate_herringbone(self):
        """Test generating herringbone pattern."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (5, 0), (5, 5), (0, 5)],
        )
        config = FlooringConfig(pattern="herringbone", plank_width=0.08, plank_length=0.4)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_generate_diamond(self):
        """Test generating diamond pattern."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (4, 0), (4, 4), (0, 4)],
        )
        config = FlooringConfig(pattern="diamond", plank_width=0.3)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_generate_hexagon(self):
        """Test generating hexagon pattern."""
        generator = FlooringGenerator()
        room = Room(
            id="r1",
            polygon=[(0, 0), (4, 0), (4, 4), (0, 4)],
        )
        config = FlooringConfig(pattern="hexagon", plank_width=0.15)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0


class TestCreateFlooringFromPlan:
    """Tests for create_flooring_from_plan function."""

    def test_create(self):
        """Test creating flooring from plan."""
        room = Room(
            id="r1",
            room_type="living_room",
            polygon=[(0, 0), (5, 0), (5, 4), (0, 4)],
        )
        plan = FloorPlan(rooms=[room])
        layouts = create_flooring_from_plan(plan)

        assert len(layouts) == 1
        assert layouts[0].room_id == "r1"

    def test_create_multiple_rooms(self):
        """Test creating flooring for multiple rooms."""
        room1 = Room(id="r1", room_type="living_room", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)])
        room2 = Room(id="r2", room_type="bedroom", polygon=[(5, 0), (10, 0), (10, 4), (5, 4)])
        plan = FloorPlan(rooms=[room1, room2])
        layouts = create_flooring_from_plan(plan)

        assert len(layouts) == 2

    def test_create_with_custom_configs(self):
        """Test creating with custom configs."""
        room = Room(id="r1", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)])
        plan = FloorPlan(rooms=[room])
        configs = {"r1": FlooringConfig(pattern="herringbone")}
        layouts = create_flooring_from_plan(plan, configs)

        assert layouts[0].config.pattern == "herringbone"


class TestFlooringEdgeCases:
    """Edge case tests for flooring."""

    def test_small_room(self):
        """Test flooring for small room."""
        generator = FlooringGenerator()
        room = Room(id="r1", polygon=[(0, 0), (1, 0), (1, 1), (0, 1)])
        config = FlooringConfig(pattern="grid", plank_width=0.3)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_large_room(self):
        """Test flooring for large room."""
        generator = FlooringGenerator()
        room = Room(id="r1", polygon=[(0, 0), (20, 0), (20, 15), (0, 15)])
        layout = generator.generate_for_room(room)

        assert len(layout.tiles) > 0

    def test_unknown_pattern(self):
        """Test handling unknown pattern."""
        generator = FlooringGenerator()
        room = Room(id="r1", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)])
        config = FlooringConfig(pattern="unknown_pattern")
        layout = generator.generate_for_room(room, config)

        # Should fall back to grid pattern
        assert len(layout.tiles) > 0

    def test_very_small_tiles(self):
        """Test with very small tiles."""
        generator = FlooringGenerator()
        room = Room(id="r1", polygon=[(0, 0), (3, 0), (3, 3), (0, 3)])
        config = FlooringConfig(pattern="grid", plank_width=0.05)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0

    def test_rotated_pattern(self):
        """Test with rotated pattern."""
        generator = FlooringGenerator()
        room = Room(id="r1", polygon=[(0, 0), (5, 0), (5, 4), (0, 4)])
        config = FlooringConfig(pattern="hardwood_plank", rotation=45.0)
        layout = generator.generate_for_room(room, config)

        assert len(layout.tiles) > 0
