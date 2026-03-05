"""
TilePlacer for determining tile placement logic.

This module provides the TilePlacer class for determining which tiles
need to be placed based on the current position and target path.
"""

from typing import TYPE_CHECKING, List, Optional, Tuple

from .registry import TileRegistry, TileState

if TYPE_CHECKING:
    from ..foundation import Platform


class TilePlacer:
    """Determines tile placement based on current position and target path.

    The TilePlacer uses lookahead to place tiles ahead of the current
    position, ensuring smooth platform extension.

    Attributes:
        platform: Platform instance for tile placement
        registry: TileRegistry for state management
        lookahead_distance: How far ahead to place tiles (default 5)
    """

    def __init__(
        self,
        platform: "Platform",
        registry: TileRegistry,
        lookahead_distance: int = 5,
    ) -> None:
        """Initialize the tile placer.

        Args:
            platform: Platform instance for placing tiles
            registry: TileRegistry for tracking tile states
            lookahead_distance: How far ahead to place tiles (default 5)
        """
        self.platform = platform
        self.registry = registry
        self.lookahead_distance = lookahead_distance

    def update_placements(
        self, current_pos: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Update tile placements based on current position.

        Determines which tiles should be placed based on lookahead
        from current position along the target path.

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            List of positions that should have tiles placed
        """
        target_path = self.registry.target_path
        if not target_path:
            return []

        # Find current position in path
        try:
            current_index = target_path.index(current_pos)
        except ValueError:
            # Current position not in path, start from beginning
            current_index = 0

        # Get positions within lookahead distance
        end_index = min(current_index + self.lookahead_distance + 1, len(target_path))
        positions_to_place = []

        for i in range(current_index, end_index):
            pos = target_path[i]
            state = self.registry.get_state(pos)

            # Place tiles that are not yet placed
            if state != TileState.PLACED:
                if self.can_place_at(pos):
                    positions_to_place.append(pos)
                    # Mark as pending in registry
                    self.registry.mark_placed(pos)

        return positions_to_place

    def can_place_at(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is valid for tile placement.

        Args:
            pos: (x, y) grid position to check

        Returns:
            True if position is valid for placement, False otherwise
        """
        # Check if position is already placed
        if self.registry.is_placed(pos):
            return False

        # Check if position is within platform bounds
        bounds = self.platform.get_bounds()
        # Allow placement anywhere (unlimited scale)
        # Only check if the position makes sense (not too far from existing tiles)

        # For now, we allow placement anywhere
        # The platform handles unlimited scale
        return True

    def get_next_placements(self, n: int) -> List[Tuple[int, int]]:
        """Get the next N positions that need placement.

        Returns positions prioritized by proximity to the target path.

        Args:
            n: Maximum number of positions to return

        Returns:
            List of up to N positions needing placement
        """
        candidates = self.registry.get_placement_candidates()
        if not candidates:
            return []

        # Filter to only valid placement positions
        valid_candidates = [p for p in candidates if self.can_place_at(p)]

        # Sort by position order in target path (prioritize earlier positions)
        target_path = self.registry.target_path
        if target_path:
            path_order = {pos: i for i, pos in enumerate(target_path)}
            valid_candidates.sort(key=lambda p: path_order.get(p, float("inf")))

        return valid_candidates[:n]

    def get_placement_count(self) -> int:
        """Get the number of tiles pending placement.

        Returns:
            Count of positions needing tile placement
        """
        return len(self.registry.get_placement_candidates())

    def place_tiles(self, positions: List[Tuple[int, int]]) -> int:
        """Place tiles at the specified positions.

        Calls the platform's place_tile method for each position.

        Args:
            positions: List of (x, y) grid positions to place tiles

        Returns:
            Number of tiles successfully placed
        """
        placed_count = 0
        for pos in positions:
            if self.platform.place_tile(pos):
                self.registry.mark_placed(pos)
                placed_count += 1

        return placed_count
