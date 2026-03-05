"""
Platform core class for the tile platform system.

This module provides the Platform class that manages the tile system,
including tile placement, removal, and overall platform state.
"""

from typing import List, Optional, Tuple

from .grid import Grid
from .types import ArmConfig, PlatformConfig, TileConfig, TileShape


class Platform:
    """Core platform class that manages the tile system.

    The Platform class coordinates tiles and arms, providing the primary
    interface for tile placement and removal operations.

    Attributes:
        config: Platform configuration
        grid: Grid tracking system for tile positions
        arms: List of arm configurations (placeholder for Phase 3)
    """

    def __init__(self, config: Optional[PlatformConfig] = None) -> None:
        """Initialize the platform with optional configuration.

        Args:
            config: Platform configuration. Uses defaults if not provided.
        """
        self.config = config or PlatformConfig()
        self.grid = Grid()
        self.arms: List[ArmConfig] = []

        # Initialize arms with placeholder positions
        self._initialize_arms()

        # Initialize grid with initial tiles if configured
        self._initialize_tiles()

    def _initialize_arms(self) -> None:
        """Initialize mechanical arms at default positions."""
        for i in range(self.config.arm_count):
            # Place arms at corners/edges based on count
            # For now, simple placement around origin
            angle = (2 * 3.14159 * i) / self.config.arm_count
            pos_x = int(round(2 * __import__('math').cos(angle)))
            pos_y = int(round(2 * __import__('math').sin(angle)))
            self.arms.append(ArmConfig(position=(pos_x, pos_y)))

    def _initialize_tiles(self) -> None:
        """Initialize grid with tiles based on initial_size configuration."""
        width, height = self.config.initial_size
        for x in range(width):
            for y in range(height):
                tile = TileConfig(
                    position=(float(x), float(y)),
                    shape=self.config.tile_shape,
                    size=self.config.tile_size,
                )
                self.grid.add_tile((x, y), tile)

    def place_tile(
        self,
        grid_pos: Tuple[int, int],
        shape: Optional[TileShape] = None,
    ) -> bool:
        """Place a tile at the specified grid position.

        Args:
            grid_pos: Grid position (x, y) for tile placement
            shape: Tile shape to use. Uses config default if not specified.

        Returns:
            True if tile was placed, False if position was occupied
        """
        tile_shape = shape or self.config.tile_shape
        world_x = float(grid_pos[0]) * self.config.tile_size
        world_y = float(grid_pos[1]) * self.config.tile_size

        tile = TileConfig(
            position=(world_x, world_y),
            shape=tile_shape,
            size=self.config.tile_size,
        )

        return self.grid.add_tile(grid_pos, tile)

    def remove_tile(self, grid_pos: Tuple[int, int]) -> bool:
        """Remove a tile from the specified grid position.

        Args:
            grid_pos: Grid position (x, y) of tile to remove

        Returns:
            True if tile was removed, False if position was empty
        """
        removed = self.grid.remove_tile(grid_pos)
        return removed is not None

    def get_tile_positions(self) -> List[Tuple[int, int]]:
        """Get all current tile positions.

        Returns:
            List of grid positions where tiles exist
        """
        return list(self.grid.tiles.keys())

    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get the current platform extent.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) grid coordinates
        """
        return self.grid.get_bounds()

    def get_tile_count(self) -> int:
        """Get the total number of tiles in the platform.

        Returns:
            Number of tiles currently placed
        """
        return len(self.grid)

    def get_arm_count(self) -> int:
        """Get the number of mechanical arms.

        Returns:
            Number of arms configured
        """
        return len(self.arms)

    def get_arm_positions(self) -> List[Tuple[int, int]]:
        """Get all arm grid positions.

        Returns:
            List of grid positions where arms are mounted
        """
        return [arm.position for arm in self.arms]
