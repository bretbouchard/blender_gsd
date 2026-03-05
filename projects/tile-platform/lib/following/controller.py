"""
FollowingController for automated platform following.

This module provides the FollowingController class for coordinating
automated platform following of a target, including tile placement
and removal based on target movement.
"""

from typing import TYPE_CHECKING, List, Optional, Tuple

from .tracker import TargetTracker

if TYPE_CHECKING:
    from ..foundation import Platform
    from ..tiles import TilePlacer, TileRetractor


class FollowingController:
    """Coordinates automated platform following of a target.

    The FollowingController integrates with the platform, tracker, and
    tile management systems to automatically follow a target path,
    placing tiles ahead and removing them behind.

    Attributes:
        platform: Platform instance to control
        tracker: TargetTracker for target position tracking
        tile_placer: TilePlacer for placing tiles ahead
        tile_retractor: TileRetractor for removing tiles behind
        follow_distance: Desired distance to maintain from target
        current_position: Current platform position
    """

    def __init__(
        self,
        platform: "Platform",
        tracker: Optional[TargetTracker] = None,
        tile_placer: Optional["TilePlacer"] = None,
        tile_retractor: Optional["TileRetractor"] = None,
        follow_distance: float = 3.0,
    ) -> None:
        """Initialize the following controller.

        Args:
            platform: Platform instance to control
            tracker: TargetTracker for tracking target (created if None)
            tile_placer: TilePlacer for placing tiles (optional)
            tile_retractor: TileRetractor for removing tiles (optional)
            follow_distance: Distance to maintain from target (default 3.0)
        """
        self.platform = platform
        self.tracker = tracker or TargetTracker()
        self.tile_placer = tile_placer
        self.tile_retractor = tile_retractor

        self._follow_distance = follow_distance
        self._current_position: Tuple[float, float] = (0.0, 0.0)
        self._is_following = False
        self._placed_positions: List[Tuple[int, int]] = []
        self._removed_positions: List[Tuple[int, int]] = []

    @property
    def follow_distance(self) -> float:
        """Return the current follow distance."""
        return self._follow_distance

    @follow_distance.setter
    def follow_distance(self, value: float) -> None:
        """Set the follow distance."""
        self._follow_distance = max(0.0, value)

    @property
    def current_position(self) -> Tuple[float, float]:
        """Return the current platform position."""
        return self._current_position

    @property
    def is_following(self) -> bool:
        """Return whether the controller is actively following."""
        return self._is_following

    def set_target_path(
        self, path: List[Tuple[float, float, float]], start_following: bool = True
    ) -> None:
        """Set a new target path for the platform to follow.

        Args:
            path: List of (x, y, z) world positions to follow
            start_following: Whether to start following immediately (default True)
        """
        self.tracker.update_target(path)
        if start_following:
            self._is_following = True

    def start_following(self) -> None:
        """Start or resume following the target."""
        if self.tracker.target_path:
            self._is_following = True

    def stop_following(self) -> None:
        """Stop following the target."""
        self._is_following = False

    def update(self, dt: float = 1.0) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Update platform position and tile placement.

        This is the main update method that should be called each frame.
        It updates the platform position, places tiles ahead of the target,
        and removes tiles behind the target.

        Args:
            dt: Time delta for position updates (default 1.0)

        Returns:
            Tuple of (positions_placed, positions_removed)
        """
        if not self._is_following:
            return ([], [])

        # Get current target
        current_target = self.tracker.get_current_target()
        if current_target is None:
            return ([], [])

        # Update tracker with target movement
        self.tracker.advance_to_position(current_target, dt)

        # Calculate required tile positions
        required_tiles = self.get_required_tiles()

        # Place tiles ahead
        placed = self._place_tiles(required_tiles)

        # Remove tiles behind
        removed = self._remove_tiles()

        # Update platform position to follow target
        self._update_platform_position(current_target, dt)

        self._placed_positions = placed
        self._removed_positions = removed

        return (placed, removed)

    def _update_platform_position(
        self, target_pos: Tuple[float, float, float], dt: float
    ) -> None:
        """Update platform position to follow target.

        Moves the platform towards the target while maintaining
        the configured follow distance.

        Args:
            target_pos: Current target position (x, y, z)
            dt: Time delta for movement
        """
        # Get target position in 2D (ignore z)
        target_2d = (target_pos[0], target_pos[1])

        # Calculate direction to target
        dx = target_2d[0] - self._current_position[0]
        dy = target_2d[1] - self._current_position[1]
        distance = (dx**2 + dy**2) ** 0.5

        if distance <= self._follow_distance:
            # Already at desired distance, no movement needed
            return

        # Move towards target at follow distance
        # Normalize direction and apply movement
        move_speed = min(distance - self._follow_distance, distance)

        if distance > 0:
            self._current_position = (
                self._current_position[0] + (dx / distance) * move_speed,
                self._current_position[1] + (dy / distance) * move_speed,
            )

    def get_required_tiles(self) -> List[Tuple[int, int]]:
        """Calculate which tile positions are needed.

        Uses the target path and lookahead to determine which
        grid positions need tiles.

        Returns:
            List of (x, y) grid positions that need tiles
        """
        required: List[Tuple[int, int]] = []

        # Get current target position
        current_target = self.tracker.get_current_target()
        if current_target is None:
            return required

        # Convert to grid coordinates
        current_grid = (int(current_target[0]), int(current_target[1]))

        # Add current position
        required.append(current_grid)

        # Get future positions within lookahead distance
        future_positions = self.tracker.get_targets_within_distance(
            self.tracker.lookahead_distance
        )

        for pos in future_positions:
            grid_pos = (int(pos[0]), int(pos[1]))
            if grid_pos not in required:
                required.append(grid_pos)

        # Also include positions around the path for stability
        for pos in list(required):  # Copy list to avoid modification during iteration
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (pos[0] + dx, pos[1] + dy)
                if neighbor not in required:
                    required.append(neighbor)

        return required

    def _place_tiles(self, positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Place tiles at specified positions.

        Args:
            positions: List of (x, y) grid positions to place tiles

        Returns:
            List of positions where tiles were actually placed
        """
        placed: List[Tuple[int, int]] = []

        if self.tile_placer is not None:
            # Use tile placer if available
            placed = self.tile_placer.place_tiles(positions)
        else:
            # Direct platform placement
            for pos in positions:
                if self.platform.place_tile(pos):
                    placed.append(pos)

        return placed

    def _remove_tiles(self) -> List[Tuple[int, int]]:
        """Remove tiles that are no longer needed.

        Removes tiles that are behind the current position
        beyond the keep distance.

        Returns:
            List of positions where tiles were removed
        """
        removed: List[Tuple[int, int]] = []

        if self.tile_retractor is not None:
            # Use tile retractor if available
            current_grid = (
                int(self._current_position[0]),
                int(self._current_position[1]),
            )
            positions_to_remove = self.tile_retractor.update_removals(current_grid)
            removed = self.tile_retractor.remove_tiles(positions_to_remove)
        else:
            # Direct platform removal based on distance
            current_grid = (
                int(self._current_position[0]),
                int(self._current_position[1]),
            )

            # Get all current tile positions
            all_tiles = self.platform.get_tile_positions()

            # Remove tiles that are far from current position
            keep_distance = self._follow_distance + self.tracker.lookahead_distance

            for pos in all_tiles:
                dist = ((pos[0] - current_grid[0]) ** 2 + (pos[1] - current_grid[1]) ** 2) ** 0.5
                if dist > keep_distance:
                    if self.platform.remove_tile(pos):
                        removed.append(pos)

        return removed

    def set_follow_distance(self, distance: float) -> None:
        """Configure the distance platform maintains from target.

        Args:
            distance: Desired follow distance
        """
        self.follow_distance = distance

    def get_last_placed(self) -> List[Tuple[int, int]]:
        """Get positions of tiles placed in the last update.

        Returns:
            List of (x, y) positions placed in last update
        """
        return self._placed_positions.copy()

    def get_last_removed(self) -> List[Tuple[int, int]]:
        """Get positions of tiles removed in the last update.

        Returns:
            List of (x, y) positions removed in last update
        """
        return self._removed_positions.copy()

    def get_status(self) -> dict:
        """Get current status of the following controller.

        Returns:
            Dictionary with status information
        """
        return {
            "is_following": self._is_following,
            "current_position": self._current_position,
            "follow_distance": self._follow_distance,
            "path_progress": self.tracker.get_path_progress(),
            "path_complete": self.tracker.is_path_complete(),
            "tiles_placed_last": len(self._placed_positions),
            "tiles_removed_last": len(self._removed_positions),
            "current_target": self.tracker.get_current_target(),
        }

    def reset(self) -> None:
        """Reset the controller to initial state."""
        self._is_following = False
        self._current_position = (0.0, 0.0)
        self._placed_positions = []
        self._removed_positions = []
        self.tracker.update_target([])

    def __repr__(self) -> str:
        """Return string representation of the controller."""
        return (
            f"FollowingController(following={self._is_following}, "
            f"position={self._current_position}, "
            f"distance={self._follow_distance})"
        )
