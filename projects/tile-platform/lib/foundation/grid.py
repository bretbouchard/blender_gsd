"""
Grid tracking system for tile positions.

This module provides the Grid class for tracking tile positions in 2D space.
It supports adding, removing, and querying tiles by grid position.
"""

from typing import Dict, List, Optional, Tuple

from .types import TileConfig


class Grid:
    """Manages tile positions in a 2D grid.

    The grid tracks tiles by their integer grid positions and maintains
    the bounds of the platform as tiles are added and removed.

    Attributes:
        tiles: Dictionary mapping grid positions to tile configurations
        bounds: Current platform extent (min_x, min_y, max_x, max_y)
    """

    def __init__(self) -> None:
        """Initialize an empty grid."""
        self._tiles: Dict[Tuple[int, int], TileConfig] = {}
        self._bounds: Optional[Tuple[int, int, int, int]] = None

    @property
    def tiles(self) -> Dict[Tuple[int, int], TileConfig]:
        """Return the tiles dictionary (read-only access via property)."""
        return self._tiles.copy()

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Return current platform bounds.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y).
            Returns (0, 0, 0, 0) if grid is empty.
        """
        if self._bounds is None:
            return (0, 0, 0, 0)
        return self._bounds

    def add_tile(self, pos: Tuple[int, int], tile: TileConfig) -> bool:
        """Add a tile at the specified grid position.

        Args:
            pos: Grid position (x, y) where tile should be placed
            tile: Tile configuration to add

        Returns:
            True if tile was added, False if position is already occupied
        """
        if pos in self._tiles:
            return False

        self._tiles[pos] = tile
        self._update_bounds(pos)
        return True

    def remove_tile(self, pos: Tuple[int, int]) -> Optional[TileConfig]:
        """Remove a tile from the specified grid position.

        Args:
            pos: Grid position (x, y) of tile to remove

        Returns:
            Removed tile configuration, or None if position was empty
        """
        if pos not in self._tiles:
            return None

        tile = self._tiles.pop(pos)
        self._recalculate_bounds()
        return tile

    def get_tile(self, pos: Tuple[int, int]) -> Optional[TileConfig]:
        """Get the tile at the specified grid position.

        Args:
            pos: Grid position (x, y) to query

        Returns:
            Tile configuration at position, or None if empty
        """
        return self._tiles.get(pos)

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get adjacent grid positions (up, down, left, right).

        Args:
            pos: Grid position (x, y) to find neighbors for

        Returns:
            List of adjacent grid positions (may include empty positions)
        """
        x, y = pos
        return [
            (x, y + 1),  # up
            (x, y - 1),  # down
            (x - 1, y),  # left
            (x + 1, y),  # right
        ]

    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Return current platform extent.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y).
            Returns (0, 0, 0, 0) if grid is empty.
        """
        return self.bounds

    def _update_bounds(self, new_pos: Tuple[int, int]) -> None:
        """Update bounds to include new position.

        Args:
            new_pos: New tile position to include in bounds
        """
        x, y = new_pos
        if self._bounds is None:
            self._bounds = (x, y, x, y)
        else:
            min_x, min_y, max_x, max_y = self._bounds
            self._bounds = (
                min(min_x, x),
                min(min_y, y),
                max(max_x, x),
                max(max_y, y),
            )

    def _recalculate_bounds(self) -> None:
        """Recalculate bounds from scratch after tile removal."""
        if not self._tiles:
            self._bounds = None
            return

        positions = self._tiles.keys()
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        self._bounds = (min(xs), min(ys), max(xs), max(ys))

    def __len__(self) -> int:
        """Return number of tiles in the grid."""
        return len(self._tiles)

    def __contains__(self, pos: Tuple[int, int]) -> bool:
        """Check if a position has a tile."""
        return pos in self._tiles
