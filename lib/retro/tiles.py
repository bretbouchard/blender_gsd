"""
Tile System

Provides tile set generation, tile map creation, and export
for game asset tile-based rendering.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING
import math
import csv
import json

from lib.retro.isometric_types import (
    TileConfig,
    TileSetResult,
    IsometricConfig,
    get_tile_size,
    TILE_SIZES,
)

if TYPE_CHECKING:
    try:
        from PIL import Image as PILImage
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False

    try:
        import numpy as np
        HAS_NUMPY = True
    except ImportError:
        HAS_NUMPY = False


# =============================================================================
# TILE DATA STRUCTURES
# =============================================================================

@dataclass
class Tile:
    """
    Single tile data.

    Attributes:
        id: Tile ID (index in tile set)
        image: Tile image data
        name: Tile name
        collision: Whether tile has collision
        properties: Additional tile properties
    """
    id: int = 0
    image: Any = None
    name: str = ""
    collision: bool = False
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "collision": self.collision,
            "properties": self.properties,
        }


@dataclass
class TileSet:
    """
    Tile set containing multiple tiles.

    Attributes:
        tiles: List of tiles
        tile_width: Tile width in pixels
        tile_height: Tile height in pixels
        tile_count: Number of unique tiles
        image: Combined tile set image
    """
    tiles: List[Tile] = field(default_factory=list)
    tile_width: int = 32
    tile_height: int = 32
    tile_count: int = 0
    image: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tile_width": self.tile_width,
            "tile_height": self.tile_height,
            "tile_count": self.tile_count,
            "tiles": [t.to_dict() for t in self.tiles],
        }


# =============================================================================
# TILE SET GENERATION
# =============================================================================

def render_tile_set(
    objects: List[Any],
    isometric_config: IsometricConfig,
    tile_config: TileConfig,
    output_path: Optional[str] = None
) -> TileSetResult:
    """
    Render all objects as tile set.

    Args:
        objects: List of Blender objects
        isometric_config: Isometric configuration
        tile_config: Tile configuration
        output_path: Optional output path

    Returns:
        TileSetResult with tile set image
    """
    result = TileSetResult()
    result.tile_count = 0
    warnings = []

    try:
        from PIL import Image as PILImage
        import bpy
        import tempfile
        import os

        tile_width, tile_height = tile_config.tile_size

        # Calculate tile set dimensions
        tile_count = len(objects)
        cols = math.ceil(math.sqrt(tile_count))
        rows = math.ceil(tile_count / cols)

        set_width = cols * tile_width + (cols - 1) * tile_config.spacing + 2 * tile_config.padding
        set_height = rows * tile_height + (rows - 1) * tile_config.spacing + 2 * tile_config.padding

        # Create tile set image
        tile_set = PILImage.new('RGBA', (set_width, set_height), (0, 0, 0, 0))

        # Store original state
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.active_object
        scene = bpy.context.scene

        temp_dir = tempfile.mkdtemp()

        try:
            for i, obj in enumerate(objects):
                col = i % cols
                row = i // cols

                # Deselect all
                bpy.ops.object.select_all(action='DESELECT')

                # Select this object
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                # Hide other objects
                for other in bpy.data.objects:
                    if other != obj and other.type != 'CAMERA':
                        other.hide_render = True

                # Set render size
                scene.render.resolution_x = tile_width
                scene.render.resolution_y = tile_height
                scene.render.resolution_percentage = 100
                scene.render.image_settings.file_format = 'PNG'
                scene.render.image_settings.color_mode = 'RGBA'

                # Render
                tile_path = os.path.join(temp_dir, f"tile_{i}.png")
                scene.render.filepath = tile_path
                bpy.ops.render.render(write_still=True)

                # Load and place in tile set
                if os.path.exists(tile_path):
                    tile_img = PILImage.open(tile_path)
                    x = tile_config.padding + col * (tile_width + tile_config.spacing)
                    y = tile_config.padding + row * (tile_height + tile_config.spacing)
                    tile_set.paste(tile_img, (x, y))
                    result.tile_count += 1

                # Unhide objects
                for other in bpy.data.objects:
                    if other != obj and other.type != 'CAMERA':
                        other.hide_render = False

        finally:
            # Restore state
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = original_active

            # Clean up temp files
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

        result.image = tile_set

        if output_path:
            tile_set.save(output_path)

    except ImportError:
        warnings.append("PIL or Blender not available for tile set rendering")
    except Exception as e:
        warnings.append(f"Tile set rendering error: {str(e)}")

    result.warnings = warnings
    return result


def create_tile_set_from_images(
    images: List[Any],
    tile_config: TileConfig
) -> TileSetResult:
    """
    Create tile set from list of images.

    Args:
        images: List of tile images
        tile_config: Tile configuration

    Returns:
        TileSetResult with tile set image
    """
    result = TileSetResult()
    result.tile_count = 0
    warnings = []

    try:
        from PIL import Image as PILImage
        import numpy as np

        if not images:
            warnings.append("No images provided")
            result.warnings = warnings
            return result

        tile_width, tile_height = tile_config.tile_size

        # Calculate dimensions
        tile_count = len(images)
        cols = math.ceil(math.sqrt(tile_count))
        rows = math.ceil(tile_count / cols)

        set_width = cols * tile_width + (cols - 1) * tile_config.spacing + 2 * tile_config.padding
        set_height = rows * tile_height + (rows - 1) * tile_config.spacing + 2 * tile_config.padding

        # Create tile set
        tile_set = PILImage.new('RGBA', (set_width, set_height), (0, 0, 0, 0))

        for i, img in enumerate(images):
            col = i % cols
            row = i // cols

            # Convert to PIL if needed
            if isinstance(img, np.ndarray):
                if img.shape[-1] == 4:
                    pil_img = PILImage.fromarray(img, 'RGBA')
                else:
                    pil_img = PILImage.fromarray(img).convert('RGBA')
            else:
                pil_img = img.convert('RGBA') if img.mode != 'RGBA' else img

            # Resize to tile size if needed
            if pil_img.size != (tile_width, tile_height):
                pil_img = pil_img.resize((tile_width, tile_height), PILImage.NEAREST)

            # Place in tile set
            x = tile_config.padding + col * (tile_width + tile_config.spacing)
            y = tile_config.padding + row * (tile_height + tile_config.spacing)
            tile_set.paste(pil_img, (x, y))
            result.tile_count += 1

        result.image = tile_set

    except ImportError:
        warnings.append("PIL or numpy not available for tile set creation")
    except Exception as e:
        warnings.append(f"Tile set creation error: {str(e)}")

    result.warnings = warnings
    return result


# =============================================================================
# TILE MAP GENERATION
# =============================================================================

def generate_tile_map(
    scene: Any,
    config: IsometricConfig,
    tile_size: Tuple[int, int] = (32, 32)
) -> List[List[int]]:
    """
    Generate tile map indices from scene.

    Args:
        scene: Blender scene
        config: Isometric configuration
        tile_size: Tile dimensions

    Returns:
        2D array of tile indices
    """
    tile_map = []

    try:
        import bpy

        # Get scene bounds
        objects_3d = [obj for obj in scene.objects if obj.type == 'MESH']

        if not objects_3d:
            return [[]]

        # Calculate scene bounds
        min_x = min(obj.location.x for obj in objects_3d)
        max_x = max(obj.location.x for obj in objects_3d)
        min_y = min(obj.location.y for obj in objects_3d)
        max_y = max(obj.location.y for obj in objects_3d)

        # Calculate tile dimensions
        tile_w, tile_h = tile_size
        scene_width = max_x - min_x
        scene_height = max_y - min_y

        cols = max(1, int(scene_width / tile_w) + 1)
        rows = max(1, int(scene_height / tile_h) + 1)

        # Initialize empty map
        tile_map = [[0 for _ in range(cols)] for _ in range(rows)]

        # Map objects to tiles
        for obj in objects_3d:
            # Convert world position to tile coordinates
            tile_x = int((obj.location.x - min_x) / tile_w)
            tile_y = int((obj.location.y - min_y) / tile_h)

            # Clamp to bounds
            tile_x = max(0, min(tile_x, cols - 1))
            tile_y = max(0, min(tile_y, rows - 1))

            # Assign tile ID based on object name or property
            tile_id = hash(obj.name) % 256  # Simple hash for demo
            tile_map[tile_y][tile_x] = tile_id

    except ImportError:
        tile_map = [[]]
    except Exception:
        tile_map = [[]]

    return tile_map


def generate_tile_map_from_positions(
    positions: List[Tuple[float, float, int]],
    grid_size: Tuple[int, int],
    tile_size: Tuple[int, int] = (1, 1)
) -> List[List[int]]:
    """
    Generate tile map from list of positions.

    Args:
        positions: List of (x, y, tile_id) tuples
        grid_size: (width, height) in tiles
        tile_size: Tile dimensions

    Returns:
        2D array of tile indices
    """
    cols, rows = grid_size

    # Initialize empty map
    tile_map = [[0 for _ in range(cols)] for _ in range(rows)]

    for x, y, tile_id in positions:
        # Convert world position to tile
        tile_x = int(x / tile_size[0])
        tile_y = int(y / tile_size[1])

        # Clamp to bounds
        if 0 <= tile_x < cols and 0 <= tile_y < rows:
            tile_map[tile_y][tile_x] = tile_id

    return tile_map


# =============================================================================
# TILE MAP EXPORT
# =============================================================================

def export_tile_map(
    tile_map: List[List[int]],
    path: str,
    format: str = "csv"
) -> bool:
    """
    Export tile map data.

    Args:
        tile_map: 2D array of tile indices
        path: Output file path
        format: Export format (csv, json, tmx)

    Returns:
        True if export successful
    """
    try:
        if format == "csv":
            return export_tile_map_csv(tile_map, path)
        elif format == "json":
            return export_tile_map_json(tile_map, path)
        elif format == "tmx":
            return export_tile_map_tmx(tile_map, path)
        else:
            return False
    except Exception:
        return False


def export_tile_map_csv(tile_map: List[List[int]], path: str) -> bool:
    """
    Export tile map as CSV.

    Args:
        tile_map: 2D array of tile indices
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in tile_map:
                writer.writerow(row)
        return True
    except Exception:
        return False


def export_tile_map_json(tile_map: List[List[int]], path: str) -> bool:
    """
    Export tile map as JSON.

    Args:
        tile_map: 2D array of tile indices
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        data = {
            "width": len(tile_map[0]) if tile_map else 0,
            "height": len(tile_map),
            "data": tile_map,
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def export_tile_map_tmx(tile_map: List[List[int]], path: str) -> bool:
    """
    Export tile map as Tiled TMX format.

    Args:
        tile_map: 2D array of tile indices
        path: Output file path

    Returns:
        True if export successful
    """
    try:
        width = len(tile_map[0]) if tile_map else 0
        height = len(tile_map)

        # Flatten tile data
        tile_data = []
        for row in tile_map:
            tile_data.extend(row)

        # Create TMX XML
        tmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.5" tiledversion="1.7.2" orientation="orthogonal"
     renderorder="right-down" width="{width}" height="{height}"
     tilewidth="32" tileheight="32" infinite="0" nextlayerid="2" nextobjectid="1">
 <tileset firstgid="1" source="tileset.tsx"/>
 <layer id="1" name="Tile Layer 1" width="{width}" height="{height}">
  <data encoding="csv">
{','.join(str(t) for t in tile_data)}
  </data>
 </layer>
</map>
'''
        with open(path, 'w') as f:
            f.write(tmx)
        return True
    except Exception:
        return False


# =============================================================================
# AUTOTILE SYSTEM
# =============================================================================

# Autotile bitmasks for blob tiles
# Each direction corresponds to a bit:
# 1=up, 2=right, 4=down, 8=left, 16=up-right, 32=right-down, 64=down-left, 128=left-up

AUTOTILE_MASKS = {
    # Center tile (all neighbors same)
    "center": 0b11111111,
    # Edge tiles (one side different)
    "top": 0b11101111,
    "right": 0b11111101,
    "bottom": 0b11111011,
    "left": 0b01111111,
    # Corner tiles
    "top_left": 0b01100111,
    "top_right": 0b11101110,
    "bottom_right": 0b11111000,
    "bottom_left": 0b01011011,
    # Single tiles
    "isolated": 0b00000000,
    # Line tiles
    "horizontal": 0b10101010,
    "vertical": 0b01010101,
}


def calculate_autotile_index(neighbors: Dict[str, bool]) -> int:
    """
    Calculate autotile index from neighbor states.

    Args:
        neighbors: Dict with keys 'up', 'right', 'down', 'left',
                   'up_right', 'right_down', 'down_left', 'left_up'

    Returns:
        Autotile index (0-47 for 48-tile autotile set)
    """
    # Bit positions
    #  16  1  32
    #   \ | /
    #  8 -+- 2
    #   / | \
    # 128 4  64

    index = 0

    if neighbors.get('up', False):
        index |= 1
    if neighbors.get('right', False):
        index |= 2
    if neighbors.get('down', False):
        index |= 4
    if neighbors.get('left', False):
        index |= 8
    if neighbors.get('up_right', False):
        index |= 16
    if neighbors.get('right_down', False):
        index |= 32
    if neighbors.get('down_left', False):
        index |= 64
    if neighbors.get('left_up', False):
        index |= 128

    return index


def get_autotile_neighbors(
    tile_map: List[List[int]],
    x: int,
    y: int,
    target_id: int
) -> Dict[str, bool]:
    """
    Get neighbor states for autotile calculation.

    Args:
        tile_map: 2D tile map
        x: Tile X coordinate
        y: Tile Y coordinate
        target_id: Tile ID to match

    Returns:
        Dict of neighbor directions and whether they match
    """
    neighbors = {
        'up': False,
        'right': False,
        'down': False,
        'left': False,
        'up_right': False,
        'right_down': False,
        'down_left': False,
        'left_up': False,
    }

    if not tile_map:
        return neighbors

    height = len(tile_map)
    width = len(tile_map[0]) if height > 0 else 0

    def get_tile(px: int, py: int) -> int:
        if 0 <= px < width and 0 <= py < height:
            return tile_map[py][px]
        return -1

    neighbors['up'] = get_tile(x, y - 1) == target_id
    neighbors['right'] = get_tile(x + 1, y) == target_id
    neighbors['down'] = get_tile(x, y + 1) == target_id
    neighbors['left'] = get_tile(x - 1, y) == target_id
    neighbors['up_right'] = get_tile(x + 1, y - 1) == target_id
    neighbors['right_down'] = get_tile(x + 1, y + 1) == target_id
    neighbors['down_left'] = get_tile(x - 1, y + 1) == target_id
    neighbors['left_up'] = get_tile(x - 1, y - 1) == target_id

    return neighbors


def create_autotile_template(config: IsometricConfig) -> Dict[int, int]:
    """
    Create autotile (blob tile) template mapping.

    Args:
        config: Isometric configuration

    Returns:
        Dict mapping bitmask to tile index
    """
    # Standard 48-tile autotile template
    # This maps bitmask combinations to tile positions in a 48-tile set

    template = {}

    # Simple 16-tile template (4x4)
    # 0: isolated
    template[0] = 0

    # 1-4: single direction
    template[1] = 1   # up
    template[2] = 2   # right
    template[4] = 3   # down
    template[8] = 4   # left

    # Combinations of 2 directions (edges and corners)
    template[1 | 2] = 5     # up + right
    template[2 | 4] = 6     # right + down
    template[4 | 8] = 7     # down + left
    template[8 | 1] = 8     # left + up

    # Opposite directions (horizontal/vertical lines)
    template[1 | 4] = 9     # up + down (vertical)
    template[2 | 8] = 10    # right + left (horizontal)

    # Three directions (T-junctions)
    template[1 | 2 | 4] = 11
    template[2 | 4 | 8] = 12
    template[4 | 8 | 1] = 13
    template[8 | 1 | 2] = 14

    # All four directions (center)
    template[1 | 2 | 4 | 8] = 15

    return template


def apply_autotile(
    tile_map: List[List[int]],
    target_id: int
) -> List[List[int]]:
    """
    Apply autotile rules to a tile map.

    Args:
        tile_map: Original tile map
        target_id: Tile ID to apply autotiling to

    Returns:
        Updated tile map with autotile indices
    """
    if not tile_map:
        return tile_map

    template = create_autotile_template(IsometricConfig())

    height = len(tile_map)
    width = len(tile_map[0])

    # Create result map
    result = [row[:] for row in tile_map]

    for y in range(height):
        for x in range(width):
            if tile_map[y][x] == target_id:
                neighbors = get_autotile_neighbors(tile_map, x, y, target_id)
                bitmask = calculate_autotile_index(neighbors)

                # Map bitmask to tile index
                # Use high bits to indicate this is an autotile
                if bitmask in template:
                    result[y][x] = target_id * 100 + template[bitmask]

    return result


# =============================================================================
# COLLISION MAP
# =============================================================================

def generate_collision_map(
    tile_map: List[List[int]],
    collision_tiles: List[int]
) -> List[List[int]]:
    """
    Generate collision layer from tile map.

    Args:
        tile_map: 2D tile map
        collision_tiles: List of tile IDs that have collision

    Returns:
        Collision map (1 = collision, 0 = no collision)
    """
    if not tile_map:
        return []

    collision_set = set(collision_tiles)

    return [
        [1 if tile in collision_set else 0 for tile in row]
        for row in tile_map
    ]


def export_collision_map(
    collision_map: List[List[int]],
    path: str,
    format: str = "json"
) -> bool:
    """
    Export collision map data.

    Args:
        collision_map: 2D collision array
        path: Output file path
        format: Export format (json, csv)

    Returns:
        True if export successful
    """
    try:
        if format == "json":
            data = {
                "width": len(collision_map[0]) if collision_map else 0,
                "height": len(collision_map),
                "data": collision_map,
            }
            with open(path, 'w') as f:
                json.dump(data, f)
            return True
        elif format == "csv":
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                for row in collision_map:
                    writer.writerow(row)
            return True
        return False
    except Exception:
        return False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_tile_at_position(
    tile_map: List[List[int]],
    world_x: float,
    world_y: float,
    tile_size: Tuple[int, int]
) -> int:
    """
    Get tile ID at world position.

    Args:
        tile_map: 2D tile map
        world_x: World X coordinate
        world_y: World Y coordinate
        tile_size: Tile dimensions

    Returns:
        Tile ID or -1 if out of bounds
    """
    if not tile_map:
        return -1

    tile_x = int(world_x / tile_size[0])
    tile_y = int(world_y / tile_size[1])

    if 0 <= tile_y < len(tile_map) and 0 <= tile_x < len(tile_map[0]):
        return tile_map[tile_y][tile_x]

    return -1


def world_to_tile(
    world_x: float,
    world_y: float,
    tile_size: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Convert world coordinates to tile coordinates.

    Args:
        world_x: World X coordinate
        world_y: World Y coordinate
        tile_size: Tile dimensions

    Returns:
        (tile_x, tile_y) tuple
    """
    return (
        int(world_x / tile_size[0]),
        int(world_y / tile_size[1])
    )


def tile_to_world(
    tile_x: int,
    tile_y: int,
    tile_size: Tuple[int, int]
) -> Tuple[float, float]:
    """
    Convert tile coordinates to world coordinates (tile center).

    Args:
        tile_x: Tile X coordinate
        tile_y: Tile Y coordinate
        tile_size: Tile dimensions

    Returns:
        (world_x, world_y) tuple
    """
    return (
        tile_x * tile_size[0] + tile_size[0] / 2,
        tile_y * tile_size[1] + tile_size[1] / 2
    )


def resize_tile_map(
    tile_map: List[List[int]],
    new_size: Tuple[int, int],
    fill_value: int = 0
) -> List[List[int]]:
    """
    Resize tile map to new dimensions.

    Args:
        tile_map: Original tile map
        new_size: (width, height) in tiles
        fill_value: Value for new tiles

    Returns:
        Resized tile map
    """
    new_width, new_height = new_size

    result = []

    for y in range(new_height):
        row = []
        for x in range(new_width):
            if y < len(tile_map) and x < len(tile_map[0]):
                row.append(tile_map[y][x])
            else:
                row.append(fill_value)
        result.append(row)

    return result


def flip_tile_map_horizontal(tile_map: List[List[int]]) -> List[List[int]]:
    """
    Flip tile map horizontally.

    Args:
        tile_map: Original tile map

    Returns:
        Horizontally flipped tile map
    """
    return [row[::-1] for row in tile_map]


def flip_tile_map_vertical(tile_map: List[List[int]]) -> List[List[int]]:
    """
    Flip tile map vertically.

    Args:
        tile_map: Original tile map

    Returns:
        Vertically flipped tile map
    """
    return tile_map[::-1]


def rotate_tile_map_90(tile_map: List[List[int]], clockwise: bool = True) -> List[List[int]]:
    """
    Rotate tile map 90 degrees.

    Args:
        tile_map: Original tile map
        clockwise: Rotate clockwise (True) or counter-clockwise (False)

    Returns:
        Rotated tile map
    """
    if not tile_map:
        return []

    if clockwise:
        # Rotate 90 degrees clockwise
        return [list(row) for row in zip(*tile_map[::-1])]
    else:
        # Rotate 90 degrees counter-clockwise
        return [list(row) for row in zip(*tile_map)][::-1]
