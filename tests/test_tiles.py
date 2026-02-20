"""
Unit tests for Tile System module
"""

import pytest
import os
import tempfile
import json
import csv
from lib.retro.tiles import (
    Tile,
    TileSet,
    render_tile_set,
    create_tile_set_from_images,
    generate_tile_map,
    generate_tile_map_from_positions,
    export_tile_map,
    export_tile_map_csv,
    export_tile_map_json,
    export_tile_map_tmx,
    AUTOTILE_MASKS,
    calculate_autotile_index,
    get_autotile_neighbors,
    create_autotile_template,
    apply_autotile,
    generate_collision_map,
    export_collision_map,
    get_tile_at_position,
    world_to_tile,
    tile_to_world,
    resize_tile_map,
    flip_tile_map_horizontal,
    flip_tile_map_vertical,
    rotate_tile_map_90,
)
from lib.retro.isometric_types import TileConfig, IsometricConfig


class TestTile:
    """Tests for Tile dataclass."""

    def test_default_values(self):
        """Test default values."""
        tile = Tile()
        assert tile.id == 0
        assert tile.name == ""
        assert tile.collision is False

    def test_to_dict(self):
        """Test serialization."""
        tile = Tile(id=5, name="grass", collision=True)
        data = tile.to_dict()
        assert data["id"] == 5
        assert data["name"] == "grass"
        assert data["collision"] is True


class TestTileSet:
    """Tests for TileSet dataclass."""

    def test_default_values(self):
        """Test default values."""
        tileset = TileSet()
        assert tileset.tile_count == 0
        assert tileset.tiles == []

    def test_to_dict(self):
        """Test serialization."""
        tileset = TileSet(tile_width=32, tile_height=32)
        data = tileset.to_dict()
        assert data["tile_width"] == 32
        assert data["tile_height"] == 32


class TestCreateTileSetFromImages:
    """Tests for create_tile_set_from_images function."""

    def test_empty_images(self):
        """Test empty image list."""
        config = TileConfig()
        result = create_tile_set_from_images([], config)
        assert result.tile_count == 0
        assert "No images provided" in result.warnings

    def test_returns_result(self):
        """Test returns TileSetResult."""
        config = TileConfig()
        result = create_tile_set_from_images([], config)
        assert hasattr(result, 'tile_count')
        assert hasattr(result, 'warnings')


class TestGenerateTileMap:
    """Tests for generate_tile_map function."""

    def test_empty_scene(self):
        """Test empty scene returns empty map."""
        result = generate_tile_map(None, IsometricConfig())
        assert result == [[]]


class TestGenerateTileMapFromPositions:
    """Tests for generate_tile_map_from_positions function."""

    def test_empty_positions(self):
        """Test empty positions."""
        result = generate_tile_map_from_positions([], (10, 10))
        # Should return 10x10 map filled with 0
        assert len(result) == 10
        assert len(result[0]) == 10
        assert all(cell == 0 for row in result for cell in row)

    def test_with_positions(self):
        """Test with tile positions."""
        positions = [
            (0, 0, 1),
            (1, 0, 2),
            (0, 1, 3),
        ]
        # tile_size defaults to (32, 32), so (0,0) maps to tile (0,0), (1,0) to (0,0) as well
        result = generate_tile_map_from_positions(positions, (2, 2), tile_size=(1, 1))
        assert result[0][0] == 1
        assert result[0][1] == 2
        assert result[1][0] == 3


class TestExportTileMap:
    """Tests for export_tile_map functions."""

    def test_export_csv(self):
        """Test CSV export."""
        tile_map = [[1, 2], [3, 4]]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            path = f.name

        try:
            success = export_tile_map_csv(tile_map, path)
            assert success is True

            with open(path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 2
        finally:
            os.unlink(path)

    def test_export_json(self):
        """Test JSON export."""
        tile_map = [[1, 2], [3, 4]]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            success = export_tile_map_json(tile_map, path)
            assert success is True

            with open(path, 'r') as f:
                data = json.load(f)
                assert data["width"] == 2
                assert data["height"] == 2
        finally:
            os.unlink(path)

    def test_export_tmx(self):
        """Test TMX export."""
        tile_map = [[1, 2], [3, 4]]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tmx', delete=False) as f:
            path = f.name

        try:
            success = export_tile_map_tmx(tile_map, path)
            assert success is True

            with open(path, 'r') as f:
                content = f.read()
                assert '<?xml' in content
                assert '<map' in content
        finally:
            os.unlink(path)

    def test_export_generic(self):
        """Test generic export function."""
        tile_map = [[1, 2], [3, 4]]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            assert export_tile_map(tile_map, csv_path, "csv") is True
            assert export_tile_map(tile_map, json_path, "json") is True
            assert export_tile_map(tile_map, "test.xyz", "unknown") is False
        finally:
            os.unlink(csv_path)
            os.unlink(json_path)


class TestAutotileMasks:
    """Tests for AUTOTILE_MASKS."""

    def test_has_common_masks(self):
        """Test common autotile masks exist."""
        assert "center" in AUTOTILE_MASKS
        assert "isolated" in AUTOTILE_MASKS
        assert "top" in AUTOTILE_MASKS
        assert "corner" in AUTOTILE_MASKS or "top_left" in AUTOTILE_MASKS


class TestCalculateAutotileIndex:
    """Tests for calculate_autotile_index function."""

    def test_no_neighbors(self):
        """Test with no neighbors."""
        neighbors = {
            'up': False, 'right': False, 'down': False, 'left': False,
            'up_right': False, 'right_down': False, 'down_left': False, 'left_up': False,
        }
        index = calculate_autotile_index(neighbors)
        assert index == 0

    def test_all_neighbors(self):
        """Test with all neighbors."""
        neighbors = {k: True for k in ['up', 'right', 'down', 'left', 'up_right', 'right_down', 'down_left', 'left_up']}
        index = calculate_autotile_index(neighbors)
        assert index == 0b11111111  # 255

    def test_cardinal_directions(self):
        """Test cardinal directions only."""
        neighbors = {
            'up': True, 'right': True, 'down': True, 'left': True,
            'up_right': False, 'right_down': False, 'down_left': False, 'left_up': False,
        }
        index = calculate_autotile_index(neighbors)
        assert index == 0b00001111  # 15


class TestGetAutotileNeighbors:
    """Tests for get_autotile_neighbors function."""

    def test_center_tile(self):
        """Test center tile with all same neighbors."""
        tile_map = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        neighbors = get_autotile_neighbors(tile_map, 1, 1, 1)
        assert all(neighbors.values())

    def test_isolated_tile(self):
        """Test isolated tile."""
        tile_map = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        neighbors = get_autotile_neighbors(tile_map, 1, 1, 1)
        assert not any(neighbors.values())

    def test_edge_tile(self):
        """Test edge tile."""
        tile_map = [[0, 1, 0], [0, 1, 0], [0, 0, 0]]
        neighbors = get_autotile_neighbors(tile_map, 1, 0, 1)
        # Should have neighbor below
        assert neighbors['down'] is True


class TestCreateAutotileTemplate:
    """Tests for create_autotile_template function."""

    def test_returns_dict(self):
        """Test returns dictionary."""
        config = IsometricConfig()
        template = create_autotile_template(config)
        assert isinstance(template, dict)

    def test_has_isolated(self):
        """Test has isolated tile."""
        config = IsometricConfig()
        template = create_autotile_template(config)
        assert 0 in template  # Isolated tile

    def test_has_center(self):
        """Test has center tile."""
        config = IsometricConfig()
        template = create_autotile_template(config)
        # Full neighbors = 15 (cardinal only)
        assert 15 in template


class TestApplyAutotile:
    """Tests for apply_autotile function."""

    def test_empty_map(self):
        """Test empty map."""
        result = apply_autotile([], 1)
        assert result == []

    def test_isolated_tile(self):
        """Test isolated tile."""
        tile_map = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        result = apply_autotile(tile_map, 1)
        # Isolated tile should get index 0
        assert result[1][1] != 1  # Should be modified

    def test_preserves_other_tiles(self):
        """Test preserves other tile IDs."""
        tile_map = [[2, 2], [2, 1]]
        result = apply_autotile(tile_map, 1)
        # Tile 2 should remain unchanged
        assert result[0][0] == 2
        assert result[0][1] == 2
        assert result[1][0] == 2


class TestGenerateCollisionMap:
    """Tests for generate_collision_map function."""

    def test_empty_map(self):
        """Test empty map."""
        result = generate_collision_map([], [1])
        assert result == []

    def test_marks_collision(self):
        """Test marks collision tiles."""
        tile_map = [[1, 2], [3, 1]]
        collision_tiles = [1, 3]
        result = generate_collision_map(tile_map, collision_tiles)
        assert result[0][0] == 1  # 1 is collision
        assert result[0][1] == 0  # 2 is not
        assert result[1][0] == 1  # 3 is collision
        assert result[1][1] == 1  # 1 is collision


class TestExportCollisionMap:
    """Tests for export_collision_map function."""

    def test_export_json(self):
        """Test JSON export."""
        collision_map = [[1, 0], [0, 1]]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            success = export_collision_map(collision_map, path, "json")
            assert success is True

            with open(path, 'r') as f:
                data = json.load(f)
                assert data["data"] == collision_map
        finally:
            os.unlink(path)

    def test_export_csv(self):
        """Test CSV export."""
        collision_map = [[1, 0], [0, 1]]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            path = f.name

        try:
            success = export_collision_map(collision_map, path, "csv")
            assert success is True
        finally:
            os.unlink(path)


class TestGetTileAtPosition:
    """Tests for get_tile_at_position function."""

    def test_valid_position(self):
        """Test valid position."""
        tile_map = [[1, 2], [3, 4]]
        tile_id = get_tile_at_position(tile_map, 0, 0, (1, 1))
        assert tile_id == 1

    def test_out_of_bounds(self):
        """Test out of bounds position."""
        tile_map = [[1, 2], [3, 4]]
        tile_id = get_tile_at_position(tile_map, 10, 10, (1, 1))
        assert tile_id == -1


class TestWorldToTile:
    """Tests for world_to_tile function."""

    def test_origin(self):
        """Test world origin."""
        tile_x, tile_y = world_to_tile(0, 0, (32, 32))
        assert tile_x == 0
        assert tile_y == 0

    def test_positive_position(self):
        """Test positive position."""
        tile_x, tile_y = world_to_tile(64, 32, (32, 32))
        assert tile_x == 2
        assert tile_y == 1


class TestTileToWorld:
    """Tests for tile_to_world function."""

    def test_origin(self):
        """Test tile 0,0."""
        x, y = tile_to_world(0, 0, (32, 32))
        # Should be center of tile
        assert x == 16
        assert y == 16

    def test_positive_tile(self):
        """Test positive tile."""
        x, y = tile_to_world(2, 1, (32, 32))
        assert x == 80  # 2 * 32 + 16
        assert y == 48  # 1 * 32 + 16


class TestResizeTileMap:
    """Tests for resize_tile_map function."""

    def test_expand(self):
        """Test expanding map."""
        tile_map = [[1, 2], [3, 4]]
        result = resize_tile_map(tile_map, (3, 3), fill_value=0)
        assert len(result) == 3
        assert len(result[0]) == 3
        assert result[2][2] == 0  # New tile

    def test_shrink(self):
        """Test shrinking map."""
        tile_map = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = resize_tile_map(tile_map, (2, 2))
        assert len(result) == 2
        assert len(result[0]) == 2
        assert result[0][0] == 1
        assert result[1][1] == 5


class TestFlipTileMap:
    """Tests for tile map flipping functions."""

    def test_flip_horizontal(self):
        """Test horizontal flip."""
        tile_map = [[1, 2], [3, 4]]
        result = flip_tile_map_horizontal(tile_map)
        assert result[0] == [2, 1]
        assert result[1] == [4, 3]

    def test_flip_vertical(self):
        """Test vertical flip."""
        tile_map = [[1, 2], [3, 4]]
        result = flip_tile_map_vertical(tile_map)
        assert result[0] == [3, 4]
        assert result[1] == [1, 2]

    def test_flip_both(self):
        """Test flipping both ways."""
        tile_map = [[1, 2], [3, 4]]
        h_flipped = flip_tile_map_horizontal(tile_map)
        v_flipped = flip_tile_map_vertical(h_flipped)
        assert v_flipped == [[4, 3], [2, 1]]


class TestRotateTileMap90:
    """Tests for rotate_tile_map_90 function."""

    def test_rotate_clockwise(self):
        """Test clockwise rotation."""
        tile_map = [[1, 2], [3, 4]]
        result = rotate_tile_map_90(tile_map, clockwise=True)
        assert result == [[3, 1], [4, 2]]

    def test_rotate_counter_clockwise(self):
        """Test counter-clockwise rotation."""
        tile_map = [[1, 2], [3, 4]]
        result = rotate_tile_map_90(tile_map, clockwise=False)
        assert result == [[2, 4], [1, 3]]

    def test_rotate_360(self):
        """Test 360 degree rotation."""
        tile_map = [[1, 2], [3, 4]]
        result = rotate_tile_map_90(tile_map, clockwise=True)
        result = rotate_tile_map_90(result, clockwise=True)
        result = rotate_tile_map_90(result, clockwise=True)
        result = rotate_tile_map_90(result, clockwise=True)
        assert result == tile_map


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
