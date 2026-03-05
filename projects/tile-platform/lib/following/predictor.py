"""
PlacementPredictor for predictive tile placement in the following system.

This module provides the PlacementPredictor class for predicting which
tiles will need to be placed or removed based on target movement patterns.
"""

from typing import List, Optional, Tuple

from .tracker import TargetTracker


class PlacementPredictor:
    """Predicts tile placement needs based on target tracking.

    The PlacementPredictor analyzes target movement patterns to predict
    which tiles will be needed in the future and which can be safely removed.
    This enables smooth following without visual stuttering.

    Attributes:
        tracker: TargetTracker for target position information
        prediction_horizon: How many steps ahead to predict (default 10)
        confidence_threshold: Minimum confidence for predictions (default 0.0)
        placement_history: History of actual placements for learning
    """

    def __init__(
        self,
        tracker: TargetTracker,
        prediction_horizon: int = 10,
        confidence_threshold: float = 0.0,
    ) -> None:
        """Initialize the placement predictor.

        Args:
            tracker: TargetTracker instance for target information
            prediction_horizon: How many steps ahead to predict (default 10)
            confidence_threshold: Minimum confidence for predictions (default 0.0)
        """
        self.tracker = tracker
        self._prediction_horizon = max(1, prediction_horizon)
        self._confidence_threshold = max(0.0, min(1.0, confidence_threshold))

        # Learning data
        self._placement_history: List[List[Tuple[int, int]]] = []
        self._prediction_accuracy: List[float] = []
        self._last_predictions: List[Tuple[int, int]] = []

        # Buffer configuration
        self._buffer_distance = 2  # Extra tiles around predicted path
        self._removal_delay = 3  # Steps to wait before removing tiles

    @property
    def prediction_horizon(self) -> int:
        """Return the prediction horizon."""
        return self._prediction_horizon

    @prediction_horizon.setter
    def prediction_horizon(self, value: int) -> None:
        """Set the prediction horizon."""
        self._prediction_horizon = max(1, value)

    @property
    def confidence_threshold(self) -> float:
        """Return the confidence threshold."""
        return self._confidence_threshold

    @confidence_threshold.setter
    def confidence_threshold(self, value: float) -> None:
        """Set the confidence threshold."""
        self._confidence_threshold = max(0.0, min(1.0, value))

    def predict_placements(
        self, current_pos: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Predict which tiles will need to be placed.

        Uses target velocity, acceleration, and path to predict
        future tile placement needs.

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            List of predicted (x, y) grid positions needing tiles
        """
        predictions: List[Tuple[int, int]] = set()

        # Get predicted positions from tracker
        for steps_ahead in range(1, self._prediction_horizon + 1):
            predicted_world = self.tracker.predict_position(steps_ahead)
            if predicted_world is not None:
                grid_pos = (int(predicted_world[0]), int(predicted_world[1]))
                predictions.add(grid_pos)

                # Add buffer tiles around predicted position
                for dx in range(-self._buffer_distance, self._buffer_distance + 1):
                    for dy in range(-self._buffer_distance, self._buffer_distance + 1):
                        if abs(dx) + abs(dy) <= self._buffer_distance:
                            predictions.add((grid_pos[0] + dx, grid_pos[1] + dy))

        # Get future positions from path
        future_from_path = self.tracker.get_targets_within_distance(
            self.tracker.lookahead_distance * 2
        )

        for pos in future_from_path:
            grid_pos = (int(pos[0]), int(pos[1]))
            predictions.add(grid_pos)

            # Add buffer for path positions too
            for dx in range(-self._buffer_distance, self._buffer_distance + 1):
                for dy in range(-self._buffer_distance, self._buffer_distance + 1):
                    if abs(dx) + abs(dy) <= self._buffer_distance:
                        predictions.add((grid_pos[0] + dx, grid_pos[1] + dy))

        # Remove current position (already placed)
        predictions.discard(current_pos)

        # Store predictions for accuracy tracking
        self._last_predictions = list(predictions)

        return list(predictions)

    def predict_removals(
        self, current_pos: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Predict which tiles can be removed.

        Identifies tiles that are behind the current position
        and can be safely removed.

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            List of (x, y) grid positions that can be removed
        """
        removals: List[Tuple[int, int]] = []

        # Get positions that should be kept
        keep_positions = self._get_keep_positions(current_pos)

        # Get all predicted placements
        predicted_placements = set(self.predict_placements(current_pos))

        # Combine keep and predicted positions
        all_keep = keep_positions | predicted_placements

        # Any tile in last_predictions but not in all_keep can be removed
        for pos in self._last_predictions:
            if pos not in all_keep:
                # Check removal delay
                if self._should_remove_now(pos, current_pos):
                    removals.append(pos)

        return removals

    def _get_keep_positions(self, current_pos: Tuple[int, int]) -> set:
        """Get positions that should definitely be kept.

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            Set of positions to keep
        """
        keep: set = set()

        # Keep current position and nearby
        for dx in range(-self._removal_delay, self._removal_delay + 1):
            for dy in range(-self._removal_delay, self._removal_delay + 1):
                keep.add((current_pos[0] + dx, current_pos[1] + dy))

        # Keep positions from recent history
        for history in self._placement_history[-3:]:
            for pos in history:
                keep.add(pos)

        return keep

    def _should_remove_now(
        self, pos: Tuple[int, int], current_pos: Tuple[int, int]
    ) -> bool:
        """Check if a position should be removed now.

        Args:
            pos: Position to check
            current_pos: Current position

        Returns:
            True if position should be removed
        """
        # Calculate Manhattan distance from current position
        distance = abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1])

        # Only remove if far enough away
        return distance > self._removal_delay + self._buffer_distance

    def update_with_actual(
        self, actual_placements: List[Tuple[int, int]]
    ) -> float:
        """Update prediction model with actual placement data.

        This improves future predictions by learning from actual
        placement patterns.

        Args:
            actual_placements: List of positions that were actually placed

        Returns:
            Accuracy score (0.0 to 1.0) of last prediction
        """
        # Store in history
        self._placement_history.append(actual_placements)

        # Keep history bounded
        if len(self._placement_history) > 100:
            self._placement_history = self._placement_history[-50:]

        # Calculate accuracy
        if self._last_predictions:
            predicted_set = set(self._last_predictions)
            actual_set = set(actual_placements)

            if predicted_set:
                # Calculate intersection over union
                intersection = len(predicted_set & actual_set)
                union = len(predicted_set | actual_set)
                accuracy = intersection / union if union > 0 else 0.0
            else:
                accuracy = 0.0

            self._prediction_accuracy.append(accuracy)

            # Keep accuracy history bounded
            if len(self._prediction_accuracy) > 100:
                self._prediction_accuracy = self._prediction_accuracy[-50:]

            return accuracy

        return 0.0

    def get_prediction_confidence(self) -> float:
        """Get confidence level for current predictions.

        Based on historical accuracy, returns a confidence score
        for the current predictions.

        Returns:
            Confidence score from 0.0 to 1.0
        """
        if not self._prediction_accuracy:
            return 0.5  # Default medium confidence

        # Use recent average accuracy
        recent = self._prediction_accuracy[-10:]
        return sum(recent) / len(recent) if recent else 0.5

    def get_high_confidence_placements(
        self, current_pos: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Get placements with confidence above threshold.

        Filters predictions to only those with sufficient confidence.

        Args:
            current_pos: Current (x, y) grid position

        Returns:
            List of high-confidence placement positions
        """
        all_predictions = self.predict_placements(current_pos)
        confidence = self.get_prediction_confidence()

        if confidence < self._confidence_threshold:
            # Low confidence - only predict very near positions
            return [
                pos
                for pos in all_predictions
                if abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1])
                <= self._buffer_distance + 2
            ]

        return all_predictions

    def get_stats(self) -> dict:
        """Get prediction statistics.

        Returns:
            Dictionary with prediction statistics
        """
        avg_accuracy = 0.0
        if self._prediction_accuracy:
            avg_accuracy = sum(self._prediction_accuracy) / len(
                self._prediction_accuracy
            )

        return {
            "prediction_horizon": self._prediction_horizon,
            "confidence_threshold": self._confidence_threshold,
            "current_confidence": self.get_prediction_confidence(),
            "average_accuracy": avg_accuracy,
            "history_size": len(self._placement_history),
            "last_prediction_count": len(self._last_predictions),
        }

    def reset(self) -> None:
        """Reset prediction state."""
        self._placement_history = []
        self._prediction_accuracy = []
        self._last_predictions = []

    def __repr__(self) -> str:
        """Return string representation of the predictor."""
        return (
            f"PlacementPredictor(horizon={self._prediction_horizon}, "
            f"confidence={self.get_prediction_confidence():.2f})"
        )
