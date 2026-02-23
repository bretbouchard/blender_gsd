"""
Flooring Generator

Procedural flooring generation with patterns and materials.
Creates floor geometry with various pattern options.

Implements REQ-IL-04: Flooring Generator (patterns).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math

from .types import FloorPlan, Room


class FlooringPattern(Enum):
    """Flooring pattern types."""
    # Wood patterns
    HARDWOOD_PLANK = "hardwood_plank"
    HERRINGBONE = "herringbone"
    CHEVRON = "chevron"
    PARQUET = "parquet"
    DIAGONAL_PLANK = "diagonal_plank"

    # Tile patterns
    GRID = "grid"
    BRICK = "brick"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    MOROCCAN = "moroccan"
    SUBWAY = "subway"
    BASKETWEAVE = "basketweave"

    # Stone/Concrete
    FLAGSTONE = "flagstone"
    TERRAZZO = "terrazzo"
    CONCRETE_TILES = "concrete_tiles"

    # Other
    CARPET_TILE = "carpet_tile"
    VINYL_PLANK = "vinyl_plank"
    LAMINATE = "laminate"


@dataclass
class FlooringConfig:
    """
    Flooring configuration.

    Attributes:
        pattern: Pattern type
        material: Material preset
        plank_width: Width of planks/tiles in meters
        plank_length: Length of planks in meters (for rectangular)
        gap_size: Gap between tiles/planks in meters
        rotation: Pattern rotation in degrees
        random_rotation: Apply random rotation to tiles
        random_offset: Apply random offset to tiles
        color_variation: Amount of color variation (0-1)
        uv_scale: UV coordinate scale
    """
    pattern: str = "hardwood_plank"
    material: str = "hardwood_oak"
    plank_width: float = 0.12  # 12cm
    plank_length: float = 1.2  # 1.2m
    gap_size: float = 0.003  # 3mm
    rotation: float = 0.0
    random_rotation: bool = False
    random_offset: float = 0.0
    color_variation: float = 0.1
    uv_scale: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern": self.pattern,
            "material": self.material,
            "plank_width": self.plank_width,
            "plank_length": self.plank_length,
            "gap_size": self.gap_size,
            "rotation": self.rotation,
            "random_rotation": self.random_rotation,
            "random_offset": self.random_offset,
            "color_variation": self.color_variation,
            "uv_scale": self.uv_scale,
        }


# Default flooring configs by room type
DEFAULT_FLOORING: Dict[str, FlooringConfig] = {
    "living_room": FlooringConfig(
        pattern="hardwood_plank",
        material="hardwood_oak",
        plank_width=0.15,
        plank_length=1.5,
    ),
    "bedroom": FlooringConfig(
        pattern="hardwood_plank",
        material="hardwood_maple",
        plank_width=0.12,
        plank_length=1.2,
    ),
    "master_bedroom": FlooringConfig(
        pattern="hardwood_plank",
        material="hardwood_walnut",
        plank_width=0.15,
        plank_length=1.8,
    ),
    "kitchen": FlooringConfig(
        pattern="grid",
        material="tile_ceramic",
        plank_width=0.3,
        plank_length=0.3,
    ),
    "dining_room": FlooringConfig(
        pattern="herringbone",
        material="hardwood_oak",
        plank_width=0.08,
        plank_length=0.4,
    ),
    "bathroom": FlooringConfig(
        pattern="hexagon",
        material="tile_marble",
        plank_width=0.15,
    ),
    "master_bathroom": FlooringConfig(
        pattern="diamond",
        material="tile_marble",
        plank_width=0.4,
    ),
    "half_bath": FlooringConfig(
        pattern="grid",
        material="tile_ceramic",
        plank_width=0.3,
    ),
    "office": FlooringConfig(
        pattern="hardwood_plank",
        material="hardwood_cherry",
        plank_width=0.12,
    ),
    "laundry": FlooringConfig(
        pattern="grid",
        material="tile_ceramic",
        plank_width=0.3,
    ),
    "hallway": FlooringConfig(
        pattern="hardwood_plank",
        material="hardwood_oak",
        plank_width=0.1,
    ),
    "foyer": FlooringConfig(
        pattern="herringbone",
        material="tile_marble",
        plank_width=0.15,
        plank_length=0.3,
    ),
    "closet": FlooringConfig(
        pattern="carpet_tile",
        material="carpet_neutral",
        plank_width=0.5,
    ),
}


@dataclass
class FloorTile:
    """
    Single floor tile/plank data.

    Attributes:
        position: Center position (x, y, z)
        rotation: Rotation in radians
        width: Tile width
        length: Tile length
        material_index: Material variant index
    """
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0
    width: float = 0.3
    length: float = 0.3
    material_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "position": list(self.position),
            "rotation": self.rotation,
            "width": self.width,
            "length": self.length,
            "material_index": self.material_index,
        }


@dataclass
class FlooringLayout:
    """
    Complete flooring layout for a room.

    Attributes:
        room_id: ID of room
        config: Flooring configuration
        tiles: List of tile positions
        total_tiles: Total number of tiles
        bounds: Room bounds (min_x, min_y, max_x, max_y)
    """
    room_id: str = ""
    config: FlooringConfig = field(default_factory=FlooringConfig)
    tiles: List[FloorTile] = field(default_factory=list)
    total_tiles: int = 0
    bounds: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "room_id": self.room_id,
            "config": self.config.to_dict(),
            "tiles": [t.to_dict() for t in self.tiles],
            "total_tiles": self.total_tiles,
            "bounds": list(self.bounds),
        }


class FlooringGenerator:
    """
    Generates procedural flooring layouts.

    Creates tile/plank positions for various flooring patterns.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize flooring generator.

        Args:
            seed: Random seed for variation
        """
        self.seed = seed
        self._tile_counter = 0

    def generate_for_room(
        self,
        room: Room,
        config: Optional[FlooringConfig] = None
    ) -> FlooringLayout:
        """
        Generate flooring layout for a room.

        Args:
            room: Room to generate flooring for
            config: Optional flooring config (uses default if not provided)

        Returns:
            FlooringLayout with tile positions
        """
        # Use default config for room type if not provided
        if config is None:
            config = DEFAULT_FLOORING.get(
                room.room_type,
                FlooringConfig()
            )

        # Get room bounds
        polygon = room.polygon
        if len(polygon) < 3:
            return FlooringLayout(room_id=room.id, config=config)

        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        bounds = (min(xs), min(ys), max(xs), max(ys))

        # Generate tiles based on pattern
        tiles = self._generate_pattern(config, bounds)

        return FlooringLayout(
            room_id=room.id,
            config=config,
            tiles=tiles,
            total_tiles=len(tiles),
            bounds=bounds,
        )

    def _generate_pattern(
        self,
        config: FlooringConfig,
        bounds: Tuple[float, float, float, float]
    ) -> List[FloorTile]:
        """Generate tiles for a pattern."""
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x
        height = max_y - min_y

        tiles = []

        if config.pattern == "hardwood_plank" or config.pattern == "vinyl_plank":
            tiles = self._generate_planks(config, min_x, min_y, width, height)
        elif config.pattern == "herringbone":
            tiles = self._generate_herringbone(config, min_x, min_y, width, height)
        elif config.pattern == "chevron":
            tiles = self._generate_chevron(config, min_x, min_y, width, height)
        elif config.pattern == "grid":
            tiles = self._generate_grid(config, min_x, min_y, width, height)
        elif config.pattern == "brick":
            tiles = self._generate_brick(config, min_x, min_y, width, height)
        elif config.pattern == "diamond":
            tiles = self._generate_diamond(config, min_x, min_y, width, height)
        elif config.pattern == "hexagon":
            tiles = self._generate_hexagon(config, min_x, min_y, width, height)
        else:
            # Default to grid
            tiles = self._generate_grid(config, min_x, min_y, width, height)

        return tiles

    def _generate_planks(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate parallel plank pattern."""
        tiles = []
        plank_width = config.plank_width
        plank_length = config.plank_length
        gap = config.gap_size

        # Calculate number of rows
        num_rows = int(height / (plank_width + gap)) + 1

        # Rotation in radians
        base_rotation = math.radians(config.rotation)

        for row in range(num_rows):
            y = min_y + row * (plank_width + gap) + plank_width / 2

            # Stagger planks in alternating rows
            offset = (row % 3) * (plank_length / 3)

            # Generate planks along width
            x = min_x - offset
            while x < min_x + width + plank_length:
                tiles.append(FloorTile(
                    position=(x + plank_length / 2, y, 0.0),
                    rotation=base_rotation,
                    width=plank_width,
                    length=plank_length,
                    material_index=(row + int(x / plank_length)) % 5,
                ))
                x += plank_length + gap

        return tiles

    def _generate_herringbone(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate herringbone pattern."""
        tiles = []
        plank_width = config.plank_width
        plank_length = config.plank_length
        gap = config.gap_size

        # Herringbone uses 45-degree angle
        angle = math.pi / 4
        diag_length = plank_length / math.sqrt(2)

        # Offset for the pattern repeat
        repeat = plank_width + diag_length + gap

        row = 0
        y = min_y - plank_length
        while y < min_y + height + plank_length:
            col = 0
            x = min_x - plank_length
            while x < min_x + width + plank_length:
                # Two planks per cell, forming V shape
                # Left plank (rotated 45°)
                tiles.append(FloorTile(
                    position=(x + diag_length / 2, y + diag_length / 2, 0.0),
                    rotation=angle,
                    width=plank_width,
                    length=plank_length,
                    material_index=(row + col) % 5,
                ))

                # Right plank (rotated -45°)
                tiles.append(FloorTile(
                    position=(x + diag_length, y + diag_length / 2, 0.0),
                    rotation=-angle,
                    width=plank_width,
                    length=plank_length,
                    material_index=(row + col + 1) % 5,
                ))

                col += 1
                x += diag_length + plank_width + gap

            row += 1
            y += diag_length + gap

        return tiles

    def _generate_chevron(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate chevron pattern (continuous V pattern)."""
        # Similar to herringbone but planks meet at 90° angle
        return self._generate_herringbone(config, min_x, min_y, width, height)

    def _generate_grid(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate simple grid pattern."""
        tiles = []
        tile_size = config.plank_width
        gap = config.gap_size

        num_cols = int(width / (tile_size + gap)) + 1
        num_rows = int(height / (tile_size + gap)) + 1

        base_rotation = math.radians(config.rotation)

        for row in range(num_rows):
            y = min_y + row * (tile_size + gap) + tile_size / 2
            for col in range(num_cols):
                x = min_x + col * (tile_size + gap) + tile_size / 2
                tiles.append(FloorTile(
                    position=(x, y, 0.0),
                    rotation=base_rotation,
                    width=tile_size,
                    length=tile_size,
                    material_index=(row + col) % 3,
                ))

        return tiles

    def _generate_brick(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate brick/offset pattern."""
        tiles = []
        tile_width = config.plank_width
        tile_length = config.plank_length
        gap = config.gap_size

        num_rows = int(height / (tile_width + gap)) + 1

        base_rotation = math.radians(config.rotation)

        for row in range(num_rows):
            y = min_y + row * (tile_width + gap) + tile_width / 2

            # Offset every other row by half tile
            offset = (tile_length / 2) if row % 2 else 0

            x = min_x - offset
            while x < min_x + width + tile_length:
                tiles.append(FloorTile(
                    position=(x + tile_length / 2, y, 0.0),
                    rotation=base_rotation,
                    width=tile_width,
                    length=tile_length,
                    material_index=(row + int(x / tile_length)) % 4,
                ))
                x += tile_length + gap

        return tiles

    def _generate_diamond(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate diamond pattern (squares rotated 45°)."""
        tiles = []
        tile_size = config.plank_width
        gap = config.gap_size

        # Diagonal spacing
        diag = tile_size * math.sqrt(2) / 2 + gap

        num_rows = int((height + width) / diag) + 2

        base_rotation = math.radians(45)

        for row in range(num_rows):
            y = min_y - tile_size + row * diag
            x_start = min_x - tile_size + row * diag

            for col in range(num_rows):
                x = x_start - col * diag * 2

                # Only add tiles within bounds
                if (min_x - tile_size <= x <= min_x + width + tile_size and
                    min_y - tile_size <= y <= min_y + height + tile_size):
                    tiles.append(FloorTile(
                        position=(x, y, 0.0),
                        rotation=base_rotation,
                        width=tile_size,
                        length=tile_size,
                        material_index=(row + col) % 3,
                    ))

        return tiles

    def _generate_hexagon(
        self,
        config: FlooringConfig,
        min_x: float,
        min_y: float,
        width: float,
        height: float
    ) -> List[FloorTile]:
        """Generate hexagonal tile pattern."""
        tiles = []
        tile_size = config.plank_width  # Distance from center to vertex
        gap = config.gap_size

        # Hexagon spacing
        horiz_spacing = tile_size * 1.5 + gap
        vert_spacing = tile_size * math.sqrt(3) + gap

        num_cols = int(width / horiz_spacing) + 2
        num_rows = int(height / vert_spacing) + 2

        for row in range(num_rows):
            y = min_y - tile_size + row * vert_spacing

            # Offset every other row
            x_offset = (horiz_spacing / 1.5) if row % 2 else 0

            for col in range(num_cols):
                x = min_x - tile_size + x_offset + col * horiz_spacing

                tiles.append(FloorTile(
                    position=(x, y, 0.0),
                    rotation=0.0,
                    width=tile_size,
                    length=tile_size,  # Hexagon uses radius
                    material_index=(row + col) % 4,
                ))

        return tiles


def create_flooring_from_plan(
    plan: FloorPlan,
    configs: Optional[Dict[str, FlooringConfig]] = None
) -> List[FlooringLayout]:
    """
    Create flooring layouts for all rooms in a floor plan.

    Args:
        plan: FloorPlan to process
        configs: Optional dict of room_id -> FlooringConfig

    Returns:
        List of FlooringLayout for each room
    """
    generator = FlooringGenerator()
    layouts = []

    for room in plan.rooms:
        config = None
        if configs and room.id in configs:
            config = configs[room.id]

        layout = generator.generate_for_room(room, config)
        layouts.append(layout)

    return layouts


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FlooringPattern",
    "FlooringConfig",
    "FloorTile",
    "FlooringLayout",
    "FlooringGenerator",
    "DEFAULT_FLOORING",
    "create_flooring_from_plan",
]
