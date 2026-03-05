"""
TargetTracker for path and character tracking in the following system.

This module provides the TargetTracker class for tracking target positions
along a path, predicting future positions, and managing target state.
"""

import math
from typing import List, Optional, Tuple


class TargetTracker:
    """Tracks target positions and predicts future positions.

    The TargetTracker manages a target path and provides methods to
    get current and future target positions, as well as predict
    where the target will be based on velocity and acceleration.

    Attributes:
        target_path: List of (x, y, z) world positions forming the path
        current_index: Current position index in the path
        lookahead_distance: Distance to look ahead for predictions
        velocity: Current estimated velocity of the target
        acceleration: Current estimated acceleration of the target
    """

    def __init__(
        self,
        target_path: Optional[List[Tuple[float, float, float]]] = None,
        lookahead_distance: float = 5.0,
    ) -> None:
        """Initialize the target tracker.

        Args:
            target_path: Initial target path (list of 3D positions)
            lookahead_distance: Distance to look ahead for predictions (default 5.0)
        """
        self._target_path: List[Tuple[float, float, float]] = target_path or []
        self._current_index: int = 0
        self._lookahead_distance: float = lookahead_distance

        # Motion estimation
        self._velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._prev_position: Optional[Tuple[float, float, float]] = None
        self._prev_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def target_path(self) -> List[Tuple[float, float, float]]:
        """Return a copy of the target path."""
        return self._target_path.copy()

    @property
    def current_index(self) -> int:
        """Return the current position index."""
        return self._current_index

    @property
    def lookahead_distance(self) -> float:
        """Return the lookahead distance."""
        return self._lookahead_distance

    @lookahead_distance.setter
    def lookahead_distance(self, value: float) -> None:
        """Set the lookahead distance."""
        self._lookahead_distance = max(0.0, value)

    @property
    def velocity(self) -> Tuple[float, float, float]:
        """Return the current estimated velocity."""
        return self._velocity

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """Return the current estimated acceleration."""
        return self._acceleration

    def update_target(self, new_path: List[Tuple[float, float, float]]) -> None:
        """Update the target path and reset position.

        Args:
            new_path: New list of (x, y, z) positions for the target
        """
        self._target_path = list(new_path)
        self._current_index = 0
        self._velocity = (0.0, 0.0, 0.0)
        self._acceleration = (0.0, 0.0, 0.0)
        self._prev_position = None
        self._prev_velocity = (0.0, 0.0, 0.0)

    def advance_to_position(
        self, position: Tuple[float, float, float], dt: float = 1.0
    ) -> None:
        """Advance the tracker to the closest path position.

        Updates the current index to the closest position on the path
        and estimates velocity and acceleration.

        Args:
            position: Current (x, y, z) world position of the target
            dt: Time delta for velocity calculation (default 1.0)
        """
        if not self._target_path:
            return

        # Find closest position on path
        min_dist = float("inf")
        closest_idx = self._current_index

        # Search from current position forward first (more likely)
        for i in range(self._current_index, len(self._target_path)):
            dist = self._distance_3d(position, self._target_path[i])
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        # Also check positions before current (in case of backtracking)
        for i in range(max(0, self._current_index - 5), self._current_index):
            dist = self._distance_3d(position, self._target_path[i])
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        self._current_index = closest_idx
        current_pos = self._target_path[closest_idx]

        # Update velocity estimation
        if self._prev_position is not None and dt > 0:
            new_velocity = (
                (current_pos[0] - self._prev_position[0]) / dt,
                (current_pos[1] - self._prev_position[1]) / dt,
                (current_pos[2] - self._prev_position[2]) / dt,
            )

            # Update acceleration
            self._acceleration = (
                (new_velocity[0] - self._prev_velocity[0]) / dt,
                (new_velocity[1] - self._prev_velocity[1]) / dt,
                (new_velocity[2] - self._prev_velocity[2]) / dt,
            )

            self._prev_velocity = self._velocity
            self._velocity = new_velocity

        self._prev_position = current_pos

    def get_current_target(self) -> Optional[Tuple[float, float, float]]:
        """Get the current target position.

        Returns:
            Current (x, y, z) target position, or None if path is empty
        """
        if not self._target_path or self._current_index >= len(self._target_path):
            return None
        return self._target_path[self._current_index]

    def get_future_targets(self, count: int) -> List[Tuple[float, float, float]]:
        """Get the next N target positions from the path.

        Returns positions ahead of current position in the path.

        Args:
            count: Number of future positions to return

        Returns:
            List of up to count (x, y, z) future positions
        """
        if not self._target_path:
            return []

        start_idx = self._current_index + 1
        end_idx = min(start_idx + count, len(self._target_path))

        return self._target_path[start_idx:end_idx]

    def get_targets_within_distance(
        self, distance: float
    ) -> List[Tuple[float, float, float]]:
        """Get target positions within a distance from current position.

        Uses the lookahead_distance to determine how far ahead to look.

        Args:
            distance: Maximum distance to look ahead

        Returns:
            List of (x, y, z) positions within the distance
        """
        if not self._target_path:
            return []

        current_pos = self.get_current_target()
        if current_pos is None:
            return []

        result = []
        accumulated_distance = 0.0
        prev_pos = current_pos

        for i in range(self._current_index + 1, len(self._target_path)):
            pos = self._target_path[i]
            segment_dist = self._distance_3d(prev_pos, pos)
            accumulated_distance += segment_dist

            if accumulated_distance <= distance:
                result.append(pos)
            else:
                break

            prev_pos = pos

        return result

    def predict_position(self, steps_ahead: int) -> Optional[Tuple[float, float, float]]:
        """Predict future target position using velocity and acceleration.

        Uses current velocity and acceleration to extrapolate where
        the target will be in the future.

        Args:
            steps_ahead: Number of time steps to predict ahead

        Returns:
            Predicted (x, y, z) position, or None if no current position
        """
        current_pos = self.get_current_target()
        if current_pos is None:
            return None

        # Kinematic equation: p = p0 + v*t + 0.5*a*t^2
        t = float(steps_ahead)
        predicted = (
            current_pos[0] + self._velocity[0] * t + 0.5 * self._acceleration[0] * t * t,
            current_pos[1] + self._velocity[1] * t + 0.5 * self._acceleration[1] * t * t,
            current_pos[2] + self._velocity[2] * t + 0.5 * self._acceleration[2] * t * t,
        )

        return predicted

    def predict_path_intersection(
        self, max_steps: int = 20
    ) -> Optional[Tuple[float, float, float]]:
        """Find where predicted trajectory intersects with the path.

        Combines prediction with path following for smoother results.

        Args:
            max_steps: Maximum steps to look ahead

        Returns:
            Predicted intersection point, or None if not found
        """
        if not self._target_path:
            return None

        current_pos = self.get_current_target()
        if current_pos is None:
            return None

        # Get future positions from path
        future_from_path = self.get_targets_within_distance(self._lookahead_distance)

        if not future_from_path:
            # Fall back to pure prediction
            return self.predict_position(min(max_steps, 5))

        # Find closest future path position to predicted position
        min_dist = float("inf")
        best_match = future_from_path[0] if future_from_path else None

        for i in range(1, min(max_steps + 1, 10)):
            predicted = self.predict_position(i)
            if predicted is None:
                break

            for path_pos in future_from_path:
                dist = self._distance_3d(predicted, path_pos)
                if dist < min_dist:
                    min_dist = dist
                    best_match = path_pos

        return best_match

    def get_remaining_path_length(self) -> float:
        """Calculate total remaining path length from current position.

        Returns:
            Total distance remaining in the path
        """
        if not self._target_path or self._current_index >= len(self._target_path) - 1:
            return 0.0

        total_length = 0.0
        prev_pos = self._target_path[self._current_index]

        for i in range(self._current_index + 1, len(self._target_path)):
            pos = self._target_path[i]
            total_length += self._distance_3d(prev_pos, pos)
            prev_pos = pos

        return total_length

    def is_path_complete(self) -> bool:
        """Check if the target has reached the end of the path.

        Returns:
            True if current position is at the end of the path
        """
        if not self._target_path:
            return True
        return self._current_index >= len(self._target_path) - 1

    def get_path_progress(self) -> float:
        """Get the progress along the path as a ratio.

        Returns:
            Progress ratio from 0.0 (start) to 1.0 (end)
        """
        if not self._target_path:
            return 1.0
        return self._current_index / max(1, len(self._target_path) - 1)

    @staticmethod
    def _distance_3d(
        p1: Tuple[float, float, float], p2: Tuple[float, float, float]
    ) -> float:
        """Calculate Euclidean distance between two 3D points.

        Args:
            p1: First point (x, y, z)
            p2: Second point (x, y, z)

        Returns:
            Euclidean distance between points
        """
        return math.sqrt(
            (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2
        )

    def __len__(self) -> int:
        """Return the number of positions in the target path."""
        return len(self._target_path)

    def __repr__(self) -> str:
        """Return string representation of the tracker."""
        return (
            f"TargetTracker(path_length={len(self._target_path)}, "
            f"current_index={self._current_index}, "
            f"lookahead={self._lookahead_distance})"
        )
