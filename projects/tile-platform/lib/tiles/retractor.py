"""
TileRetractor for determining tile removal logic.

This module provides the TileRetractor class for determining which tiles
can be safely removed based on the current position and keep distance.
"""

from typing import TYPE_CHECKING, List, Tuple

from .registry import TileRegistry, TileState

if TYPE_CHECKING:
    from ..foundation import Platform


class TileRetractor:
    """Determines tile removal based on current position and keep distance.

    The TileRetractor identifies tiles that are behind the current position
    (beyond keep_distance) and can be safely removed.

    Attributes:
        platform: Platform instance for tile removal
        registry: TileRegistry for state management
        keep_distance: How far behind current position to keep tiles (default 3)
    """

    def __init__(
        self,
        platform: "Platform",
        registry: TileRegistry,
        keep_distance: int = 3,
    ) -> None:
        """Initialize the tile retractor.

        Args:
            platform: Platform instance for removing tiles
            registry: TileRegistry for tracking tile states
            keep_distance: How far behind current position to keep tiles (default 3)
        """
        self.platform = platform
        self.registry = registry
        self.keep_distance = keep_distance

    def update_removals(self, current_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Update tile removals based on current position.

        Determines which tiles should be removed based on keep_distance
        from current position along the target path.

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            List of positions that should have tiles removed
        """
        target_path = self.registry.target_path
        if not target_path:
            return []

        # Find current position in path
        try:
            current_index = target_path.index(current_pos)
        except ValueError:
            # Current position not in path, nothing to remove
            return []

        # Get positions that are beyond keep_distance behind current position
        positions_to_remove = []

        for i in range(max(0, current_index - self.keep_distance - 1)):
            pos = target_path[i]
            state = self.registry.get_state(pos)

            # Remove tiles that are placed but beyond keep distance
            if state == TileState.PLACED:
                if self.can_remove_at(pos):
                    positions_to_remove.append(pos)
                    # Mark as removing in registry
                    self.registry.mark_removing(pos)

        # Also check for tiles not on the path
        off_path_candidates = self.registry.get_removal_candidates()
        for pos in off_path_candidates:
            if self.can_remove_at(pos):
                positions_to_remove.append(pos)
                self.registry.mark_removing(pos)

        return positions_to_remove

    def can_remove_at(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is safe to remove.

        Args:
            pos: (x, y) grid position to check

        Returns:
            True if position is safe to remove, False otherwise
        """
        # Check if position has a placed tile
        state = self.registry.get_state(pos)
        if state != TileState.PLACED:
            return False

        # Check if position is currently being removed
        if state == TileState.REMOVING:
            return False

        # Additional safety checks could be added here:
        # - Check if arm is available for removal
        # - Check if removal would strand other tiles
        # - Check if tile is needed for structural integrity

        return True

    def get_next_removals(self, n: int) -> List[Tuple[int, int]]:
        """Get the next N positions scheduled for removal.

        Returns positions prioritized by distance from current position
        (furthest first for efficient cleanup).

        Args:
            n: Maximum number of positions to return

        Returns:
            List of up to N positions scheduled for removal
        """
        removal_candidates = []

        # Get all tiles in REMOVING state
        for pos, state in self.registry.tile_states.items():
            if state == TileState.REMOVING:
                removal_candidates.append(pos)

        if not removal_candidates:
            return []

        # Sort by distance from origin (furthest first)
        # This ensures we remove tiles from the edges inward
        target_path = self.registry.target_path
        if target_path:
            # Sort by position in path (earliest positions are furthest behind)
            path_order = {pos: i for i, pos in enumerate(target_path)}
            removal_candidates.sort(key=lambda p: path_order.get(p, float("inf")))
        else:
            # Sort by distance from origin
            removal_candidates.sort(key=lambda p: p[0] ** 2 + p[1] ** 2, reverse=True)

        return removal_candidates[:n]

    def get_removal_count(self) -> int:
        """Get the number of tiles pending removal.

        Returns:
            Count of positions scheduled for tile removal
        """
        count = 0
        for state in self.registry.tile_states.values():
            if state == TileState.REMOVING:
                count += 1
        return count

    def remove_tiles(self, positions: List[Tuple[int, int]]) -> int:
        """Remove tiles at the specified positions.

        Calls the platform's remove_tile method for each position.

        Args:
            positions: List of (x, y) grid positions to remove tiles

        Returns:
            Number of tiles successfully removed
        """
        removed_count = 0
        for pos in positions:
            if self.platform.remove_tile(pos):
                self.registry.mark_removed(pos)
                removed_count += 1

        return removed_count

    def get_tiles_to_keep(self, current_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get positions of tiles that should be kept (within keep_distance).

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            List of positions that should retain their tiles
        """
        target_path = self.registry.target_path
        if not target_path:
            return list(self.registry.placed_tiles)

        try:
            current_index = target_path.index(current_pos)
        except ValueError:
            return list(self.registry.placed_tiles)

        # Keep tiles from current position back to keep_distance
        start_index = max(0, current_index - self.keep_distance)
        end_index = min(current_index + self.lookahead_if_applicable(), len(target_path))

        keep_positions = []
        for i in range(start_index, end_index):
            pos = target_path[i]
            if self.registry.is_placed(pos):
                keep_positions.append(pos)

        return keep_positions

    def lookahead_if_applicable(self) -> int:
        """Get lookahead distance if available from placer (for context).

        Returns:
            Lookahead distance or 0 if not applicable
        """
        # This method provides context for what tiles should be kept
        # The actual lookahead is managed by TilePlacer
        return 0
