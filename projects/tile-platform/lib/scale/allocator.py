"""
Tile allocation with object pooling for efficient memory management.

This module provides the TileAllocator class for managing tile IDs
with a pool-based allocation strategy for optimal memory reuse.
"""

from typing import Dict, Set


class TileAllocator:
    """Efficient tile ID allocator with object pooling.

    Manages tile IDs using a pool-based allocation strategy that
    pre-allocates IDs and reuses released IDs for better performance.

    Attributes:
        pool_size: Initial pool size (default 100)
        allocated: Set of currently allocated tile IDs
        free: Set of available tile IDs
        _next_id: Next ID to allocate when pool is exhausted
    """

    def __init__(self, pool_size: int = 100) -> None:
        """Initialize the tile allocator.

        Args:
            pool_size: Initial number of tile IDs to pre-allocate
        """
        self.pool_size = pool_size
        self.allocated: Set[int] = set()
        self.free: Set[int] = set()
        self._next_id = 0

        # Pre-allocate initial pool
        self._expand_pool(pool_size)

    def _expand_pool(self, count: int) -> None:
        """Expand the free pool by adding more tile IDs.

        Args:
            count: Number of new IDs to add to the pool
        """
        for _ in range(count):
            self.free.add(self._next_id)
            self._next_id += 1

    def allocate(self) -> int:
        """Allocate a tile ID from the pool.

        Returns:
            A free tile ID

        Raises:
            RuntimeError: If pool is exhausted (shouldn't happen with auto-expansion)
        """
        if not self.free:
            # Auto-expand pool when exhausted
            self._expand_pool(self.pool_size)

        tile_id = self.free.pop()
        self.allocated.add(tile_id)
        return tile_id

    def release(self, tile_id: int) -> None:
        """Release a tile ID back to the pool.

        Args:
            tile_id: The tile ID to release

        Raises:
            ValueError: If tile_id is not currently allocated
        """
        if tile_id not in self.allocated:
            raise ValueError(
                f"Tile ID {tile_id} is not allocated"
            )

        self.allocated.remove(tile_id)
        self.free.add(tile_id)

    def get_stats(self) -> Dict[str, int]:
        """Get allocation statistics.

        Returns:
            Dictionary with allocation stats:
            - allocated: Number of currently allocated IDs
            - free: Number of available IDs
            - total: Total IDs in the system
        """
        return {
            'allocated': len(self.allocated),
            'free': len(self.free),
            'total': self._next_id
        }

    def is_allocated(self, tile_id: int) -> bool:
        """Check if a tile ID is currently allocated.

        Args:
            tile_id: The tile ID to check

        Returns:
            True if allocated, False otherwise
        """
        return tile_id in self.allocated

    def clear(self) -> None:
        """Clear all allocations and reset the pool.

        Releases all allocated IDs back to the free pool.
        """
        self.free.update(self.allocated)
        self.allocated.clear()
