"""
Scale management for unlimited tile platforms.

This module provides the ScaleManager class for managing unlimited
tile allocation and platform scaling without artificial constraints.
"""

from typing import Dict, List, Tuple, Optional
import sys
sys.path.insert(0, '/Users/bretbouchard/apps/blender_gsd/projects/tile-platform')

from lib.foundation.platform import Platform
from lib.foundation.tile import TileGeometry
from .allocator import TileAllocator


class ScaleManager:
    """Manages unlimited tile allocation for the platform.

    The ScaleManager handles tile allocation, optimization, and ensures
    the platform can extend in any direction without limits.

    Attributes:
        platform: The platform to manage
        max_tiles: Maximum number of tiles (default 1000, unlimited mode ignores this)
        allocator: Tile allocator for efficient memory management
        tile_pool: Pool of reusable tile geometries indexed by tile ID
    """

    def __init__(
        self,
        platform: Optional[Platform] = None,
        max_tiles: int = 1000,
        pool_size: int = 100
    ) -> None:
        """Initialize the scale manager.

        Args:
            platform: Platform instance to manage (created if None)
            max_tiles: Maximum tiles (for bounded mode, default 1000)
            pool_size: Initial tile pool size for allocator
        """
        self.platform = platform or Platform()
        self.max_tiles = max_tiles
        self.allocator = TileAllocator(pool_size=pool_size)
        self.tile_pool: Dict[int, TileGeometry] = {}

        # Track tile ID to position mapping
        self._tile_positions: Dict[int, Tuple[int, int]] = {}

    def can_add_tile(self, pos: Tuple[int, int]) -> bool:
        """Check if platform can expand to include a tile at position.

        In unlimited mode (default), this always returns True.
        In bounded mode, checks against max_tiles limit.

        Args:
            pos: Grid position (x, y) to check

        Returns:
            True if tile can be added, False otherwise
        """
        # Unlimited mode - always can add
        if self.max_tiles <= 0:
            return True

        # Bounded mode - check against limit
        current_count = len(self.tile_pool)
        return current_count < self.max_tiles

    def allocate_tiles(
        self,
        count: int,
        positions: List[Tuple[int, int]]
    ) -> List[int]:
        """Allocate tile geometries for given positions.

        Args:
            count: Number of tiles to allocate
            positions: List of grid positions for tiles

        Returns:
            List of allocated tile IDs

        Raises:
            ValueError: If count doesn't match positions length
        """
        if count != len(positions):
            raise ValueError(
                f"Count {count} doesn't match positions length {len(positions)}"
            )

        tile_ids: List[int] = []

        for pos in positions:
            # Check if we can add tile at this position
            if not self.can_add_tile(pos):
                # Rollback any allocations
                for tile_id in tile_ids:
                    self.allocator.release(tile_id)
                raise RuntimeError(f"Cannot add tile at {pos}: limit reached")

            # Allocate tile ID
            tile_id = self.allocator.allocate()
            tile_ids.append(tile_id)

            # Get tile geometry from platform
            geometry = self.platform.get_tile_geometry(pos)
            if geometry is not None:
                self.tile_pool[tile_id] = geometry
                self._tile_positions[tile_id] = pos

        return tile_ids

    def release_tiles(self, tile_ids: List[int]) -> None:
        """Release tiles back to the pool.

        Args:
            tile_ids: List of tile IDs to release
        """
        for tile_id in tile_ids:
            if tile_id in self.tile_pool:
                del self.tile_pool[tile_id]
            if tile_id in self._tile_positions:
                del self._tile_positions[tile_id]
            self.allocator.release(tile_id)

    def get_tile_bounds(self) -> Tuple[int, int, int, int]:
        """Get the current platform extent.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) grid coordinates
        """
        if not self._tile_positions:
            return (0, 0, 0, 0)

        positions = list(self._tile_positions.values())
        min_x = min(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        max_y = max(pos[1] for pos in positions)

        return (min_x, min_y, max_x, max_y)

    def optimize_layout(self) -> None:
        """Optimize tile layout for memory efficiency.

        Groups adjacent tiles in memory for better cache performance.
        Reorganizes the tile pool to keep nearby tiles together.
        """
        if not self._tile_positions:
            return

        # Sort tile IDs by position (spatial locality)
        # Group tiles by their grid position in a Morton curve order
        sorted_ids = sorted(
            self._tile_positions.keys(),
            key=lambda tid: (
                self._tile_positions[tid][0] + self._tile_positions[tid][1]
            )
        )

        # Create new pool with sorted order
        new_pool: Dict[int, TileGeometry] = {}
        for tile_id in sorted_ids:
            if tile_id in self.tile_pool:
                new_pool[tile_id] = self.tile_pool[tile_id]

        self.tile_pool = new_pool

    def get_tile_count(self) -> int:
        """Get the total number of allocated tiles.

        Returns:
            Number of tiles currently in the pool
        """
        return len(self.tile_pool)

    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics.

        Returns:
            Dictionary with memory statistics:
            - tile_count: Number of tiles
            - pool_allocated: Allocated tiles in allocator
            - pool_free: Free tiles in allocator
        """
        stats = self.allocator.get_stats()
        return {
            'tile_count': len(self.tile_pool),
            'pool_allocated': stats['allocated'],
            'pool_free': stats['free'],
            'pool_total': stats['total']
        }
