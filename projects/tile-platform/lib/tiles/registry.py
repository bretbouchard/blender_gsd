"""
TileRegistry for tracking tile state in the platform system.

This module provides the TileRegistry class for tracking tile states
(PENDING, PLACED, REMOVING, REMOVED) and managing the target path
for automated following.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class TileState(Enum):
    """Enumeration of tile lifecycle states."""
    PENDING = "pending"      # Tile needs to be placed
    PLACED = "placed"        # Tile is currently placed
    REMOVING = "removing"    # Tile is scheduled for removal
    REMOVED = "removed"      # Tile has been removed


class TileRegistry:
    """Registry for tracking tile states and target path.

    The TileRegistry maintains the state of all tiles in the system
    and tracks the target path for automated following behavior.

    Attributes:
        tile_states: Dictionary mapping positions to their current state
        target_path: Optional list of positions forming the target path
        placed_tiles: Set of positions that currently have tiles placed
    """

    def __init__(self) -> None:
        """Initialize an empty tile registry."""
        self._tile_states: Dict[Tuple[int, int], TileState] = {}
        self._target_path: Optional[List[Tuple[int, int]]] = None
        self._placed_tiles: Set[Tuple[int, int]] = set()

    @property
    def tile_states(self) -> Dict[Tuple[int, int], TileState]:
        """Return a copy of the tile states dictionary."""
        return self._tile_states.copy()

    @property
    def target_path(self) -> Optional[List[Tuple[int, int]]]:
        """Return the current target path."""
        return self._target_path.copy() if self._target_path else None

    @property
    def placed_tiles(self) -> Set[Tuple[int, int]]:
        """Return a copy of the placed tiles set."""
        return self._placed_tiles.copy()

    def set_target_path(self, path: List[Tuple[int, int]]) -> None:
        """Set the target path for the platform to follow.

        Args:
            path: List of (x, y) grid positions forming the path
        """
        self._target_path = list(path)

    def get_placement_candidates(self) -> List[Tuple[int, int]]:
        """Get positions along target path that need tiles placed.

        Returns positions in the target path that are not currently
        in the PLACED state.

        Returns:
            List of (x, y) positions needing tile placement
        """
        if not self._target_path:
            return []

        candidates = []
        for pos in self._target_path:
            state = self._tile_states.get(pos)
            if state != TileState.PLACED:
                candidates.append(pos)

        return candidates

    def get_removal_candidates(self) -> List[Tuple[int, int]]:
        """Get placed positions that are not on the target path.

        Returns positions that have PLACED tiles but are not part
        of the current target path.

        Returns:
            List of (x, y) positions scheduled for removal
        """
        if not self._target_path:
            # If no target path, all placed tiles are removal candidates
            return list(self._placed_tiles)

        path_set = set(self._target_path)
        candidates = []
        for pos in self._placed_tiles:
            if pos not in path_set:
                candidates.append(pos)

        return candidates

    def mark_placed(self, pos: Tuple[int, int]) -> None:
        """Mark a tile as placed at the given position.

        Args:
            pos: (x, y) grid position of the placed tile
        """
        self._tile_states[pos] = TileState.PLACED
        self._placed_tiles.add(pos)

    def mark_removing(self, pos: Tuple[int, int]) -> None:
        """Mark a tile as being removed at the given position.

        Args:
            pos: (x, y) grid position of the tile being removed
        """
        self._tile_states[pos] = TileState.REMOVING

    def mark_removed(self, pos: Tuple[int, int]) -> None:
        """Mark a tile as removed at the given position.

        Args:
            pos: (x, y) grid position of the removed tile
        """
        self._tile_states[pos] = TileState.REMOVED
        self._placed_tiles.discard(pos)

    def get_state(self, pos: Tuple[int, int]) -> Optional[TileState]:
        """Get the current state of a tile at the given position.

        Args:
            pos: (x, y) grid position to query

        Returns:
            Current TileState, or None if position has no recorded state
        """
        return self._tile_states.get(pos)

    def is_placed(self, pos: Tuple[int, int]) -> bool:
        """Check if a tile is placed at the given position.

        Args:
            pos: (x, y) grid position to check

        Returns:
            True if tile is in PLACED state, False otherwise
        """
        return self._tile_states.get(pos) == TileState.PLACED

    def clear(self) -> None:
        """Clear all registry state."""
        self._tile_states.clear()
        self._target_path = None
        self._placed_tiles.clear()

    def __len__(self) -> int:
        """Return the number of tracked tile positions."""
        return len(self._tile_states)

    def __contains__(self, pos: Tuple[int, int]) -> bool:
        """Check if a position has a recorded state."""
        return pos in self._tile_states
