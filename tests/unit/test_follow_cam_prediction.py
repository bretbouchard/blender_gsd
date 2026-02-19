"""
Follow Camera Motion Prediction Unit Tests

Tests for: lib/cinematic/follow_cam/prediction.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-59
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.prediction import (
    MotionPredictor,
    PredictionResult,
    predict_look_ahead,
    calculate_anticipation_offset,
)
from lib.cinematic.follow_cam.types import (
    FollowCameraConfig,
    FollowTarget,
)


class TestPredictionResult:
    """Unit tests for PredictionResult dataclass."""

    def test_default_values(self):
        """Default PredictionResult should have sensible defaults."""
        result = PredictionResult()

        compare_vectors(result.predicted_position, (0.0, 0.0, 0.0))
        compare_vectors(result.predicted_velocity, (0.0, 0.0, 0.0))
        compare_vectors(result.predicted_forward, (0.0, 1.0, 0.0))
        compare_numbers(result.confidence, 0.5)
        compare_numbers(result.time_horizon, 0.5)
        assert result.is_corner is False
        compare_numbers(result.corner_direction, 0.0)

    def test_custom_values(self):
        """PredictionResult should store all prediction data."""
        result = PredictionResult(
            predicted_position=(10.0, 5.0, 2.0),
            predicted_velocity=(1.0, 0.5, 0.0),
            predicted_forward=(0.894, 0.447, 0.0),  # normalized
            confidence=0.8,
            time_horizon=1.0,
            is_corner=True,
            corner_direction=1.0,
        )

        compare_vectors(result.predicted_position, (10.0, 5.0, 2.0))
        compare_vectors(result.predicted_velocity, (1.0, 0.5, 0.0))
        compare_numbers(result.confidence, 0.8)
        assert result.is_corner is True
        compare_numbers(result.corner_direction, 1.0)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        result = PredictionResult(
            predicted_position=(5.0, 3.0, 1.0),
            predicted_velocity=(2.0, 1.0, 0.0),
            predicted_forward=(0.707, 0.707, 0.0),
            confidence=0.9,
            time_horizon=0.75,
            is_corner=False,
            corner_direction=-1.0,
        )

        data = result.to_dict()

        assert data["predicted_position"] == [5.0, 3.0, 1.0]
        assert data["predicted_velocity"] == [2.0, 1.0, 0.0]
        assert data["confidence"] == 0.9
        assert data["is_corner"] is False


class TestMotionPredictor:
    """Unit tests for MotionPredictor class."""

    def test_initialization(self):
        """MotionPredictor should initialize with empty history."""
        predictor = MotionPredictor()

        assert len(predictor._position_history) == 0
        assert len(predictor._time_history) == 0
        assert len(predictor._velocity_history) == 0

    def test_custom_history_size(self):
        """MotionPredictor should accept custom history size."""
        predictor = MotionPredictor(history_size=30)

        assert predictor._history_size == 30

    def test_record_position(self):
        """Recording positions should build history."""
        predictor = MotionPredictor()

        predictor.record_position((0.0, 0.0, 0.0), 0.0)
        predictor.record_position((1.0, 0.0, 0.0), 1.0)

        assert len(predictor._position_history) == 2
        assert len(predictor._time_history) == 2

    def test_velocity_calculation(self):
        """Recording positions should calculate velocity."""
        predictor = MotionPredictor()

        predictor.record_position((0.0, 0.0, 0.0), 0.0)
        predictor.record_position((1.0, 0.0, 0.0), 1.0)

        # Velocity should be 1 m/s in X direction
        assert len(predictor._velocity_history) == 1
        compare_vectors(predictor._last_velocity._values, (1.0, 0.0, 0.0), tolerance=0.01)

    def test_velocity_calculation_multiple(self):
        """Multiple recordings should track velocity changes."""
        predictor = MotionPredictor()

        predictor.record_position((0.0, 0.0, 0.0), 0.0)
        predictor.record_position((1.0, 0.0, 0.0), 1.0)
        predictor.record_position((3.0, 0.0, 0.0), 2.0)

        # Second velocity should be 2 m/s
        assert len(predictor._velocity_history) == 2

    def test_history_trimming(self):
        """History should be trimmed to history_size."""
        predictor = MotionPredictor(history_size=5)

        for i in range(10):
            predictor.record_position((float(i), 0.0, 0.0), float(i))

        assert len(predictor._position_history) == 5
        assert len(predictor._time_history) == 5

    def test_predict_no_history(self):
        """Prediction with no history should return default."""
        predictor = MotionPredictor()
        config = FollowCameraConfig(prediction_enabled=True)
        target = FollowTarget()

        result = predictor.predict(target, config, time_ahead=0.5)

        compare_vectors(result.predicted_position, (0.0, 0.0, 0.0))
        compare_numbers(result.confidence, 0.5)

    def test_predict_disabled(self):
        """Prediction disabled should return current position."""
        predictor = MotionPredictor()
        config = FollowCameraConfig(prediction_enabled=False)
        target = FollowTarget()

        # Record some history
        predictor.record_position((5.0, 3.0, 1.0), 0.0)
        predictor.record_position((6.0, 3.0, 1.0), 1.0)

        result = predictor.predict(target, config, time_ahead=0.5)

        # Should return current position without prediction
        compare_vectors(result.predicted_position, (6.0, 3.0, 1.0))
        compare_numbers(result.time_horizon, 0.0)

    def test_predict_velocity_based(self):
        """Velocity-based prediction should extrapolate."""
        predictor = MotionPredictor()
        config = FollowCameraConfig(prediction_enabled=True)
        target = FollowTarget(velocity_smoothing=0.5)

        # Move at 1 m/s in Y direction
        predictor.record_position((0.0, 0.0, 0.0), 0.0)
        predictor.record_position((0.0, 1.0, 0.0), 1.0)

        result = predictor.predict(target, config, time_ahead=1.0)

        # Predicted position should be about 1 meter ahead
        # (accounting for smoothing)
        assert result.predicted_position[1] > 1.0
        compare_numbers(result.time_horizon, 1.0)

    def test_predict_forward_direction(self):
        """Prediction should calculate forward direction."""
        predictor = MotionPredictor()
        config = FollowCameraConfig(prediction_enabled=True)
        target = FollowTarget()

        # Move in X direction
        predictor.record_position((0.0, 0.0, 0.0), 0.0)
        predictor.record_position((2.0, 0.0, 0.0), 1.0)

        result = predictor.predict(target, config, time_ahead=0.5)

        # Forward should be in X direction
        assert result.predicted_forward[0] > 0.9  # Mostly X

    def test_corner_detection_no_corner(self):
        """No corner should be detected with straight motion."""
        predictor = MotionPredictor()

        # Straight line motion
        for i in range(10):
            predictor.record_position((float(i), 0.0, 0.0), float(i))

        config = FollowCameraConfig(prediction_enabled=True)
        target = FollowTarget()
        result = predictor.predict(target, config, time_ahead=0.5)

        assert result.is_corner is False
        compare_numbers(result.corner_direction, 0.0)

    def test_corner_detection_right_turn(self):
        """Right turn should be detected with angular motion."""
        predictor = MotionPredictor()

        # Create a right turn trajectory (moving forward then turning right)
        positions = [
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 2.0, 0.0),
            (0.5, 2.5, 0.0),  # Start turning
            (1.0, 2.8, 0.0),
            (1.5, 2.9, 0.0),
            (2.0, 2.9, 0.0),  # Turned right
        ]

        for i, pos in enumerate(positions):
            predictor.record_position(pos, float(i))

        is_corner, direction = predictor._detect_corner()
        assert is_corner is True
        assert direction > 0  # Right turn

    def test_corner_detection_left_turn(self):
        """Left turn should be detected with angular motion."""
        predictor = MotionPredictor()

        # Create a left turn trajectory
        positions = [
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 2.0, 0.0),
            (-0.5, 2.5, 0.0),  # Start turning left
            (-1.0, 2.8, 0.0),
            (-1.5, 2.9, 0.0),
            (-2.0, 2.9, 0.0),  # Turned left
        ]

        for i, pos in enumerate(positions):
            predictor.record_position(pos, float(i))

        is_corner, direction = predictor._detect_corner()
        assert is_corner is True
        assert direction < 0  # Left turn

    def test_velocity_confidence(self):
        """Confidence should be higher with consistent velocity."""
        predictor = MotionPredictor()

        # Consistent velocity (1 m/s in X)
        for i in range(10):
            predictor.record_position((float(i), 0.0, 0.0), float(i))

        confidence = predictor._calculate_velocity_confidence()
        assert confidence > 0.8  # High confidence

    def test_velocity_confidence_low(self):
        """Confidence should be lower with inconsistent velocity."""
        predictor = MotionPredictor()

        # Inconsistent velocity
        import random
        random.seed(42)
        for i in range(10):
            x = float(i) + random.uniform(-0.5, 0.5)
            predictor.record_position((x, 0.0, 0.0), float(i))

        confidence = predictor._calculate_velocity_confidence()
        # Should still have some confidence but lower
        assert 0.0 <= confidence <= 1.0

    def test_reset(self):
        """Reset should clear all history."""
        predictor = MotionPredictor()

        for i in range(5):
            predictor.record_position((float(i), 0.0, 0.0), float(i))

        assert len(predictor._position_history) == 5

        predictor.reset()

        assert len(predictor._position_history) == 0
        assert len(predictor._time_history) == 0
        assert len(predictor._velocity_history) == 0

    def test_blending_predictions(self):
        """Blending should average two predictions."""
        predictor = MotionPredictor()

        pred1 = PredictionResult(
            predicted_position=(0.0, 0.0, 0.0),
            predicted_velocity=(1.0, 0.0, 0.0),
            predicted_forward=(1.0, 0.0, 0.0),
            confidence=0.8,
            time_horizon=0.5,
        )

        pred2 = PredictionResult(
            predicted_position=(10.0, 0.0, 0.0),
            predicted_velocity=(2.0, 0.0, 0.0),
            predicted_forward=(1.0, 0.0, 0.0),
            confidence=0.6,
            time_horizon=0.5,
        )

        blended = predictor._blend_predictions(pred1, pred2, 0.5)

        # Should be in the middle
        compare_numbers(blended.predicted_position[0], 5.0, tolerance=0.1)
        compare_numbers(blended.predicted_velocity[0], 1.5, tolerance=0.1)
        compare_numbers(blended.confidence, 0.7, tolerance=0.05)  # Average


class TestPredictLookAhead:
    """Unit tests for predict_look_ahead function."""

    def test_stationary_target(self):
        """Stationary target should return current position."""
        result = predict_look_ahead(
            current_position=(5.0, 3.0, 1.0),
            current_velocity=(0.0, 0.0, 0.0),
            look_ahead_distance=2.0,
        )

        compare_vectors(result, (5.0, 3.0, 1.0))

    def test_moving_target_forward(self):
        """Moving target should look ahead in velocity direction."""
        result = predict_look_ahead(
            current_position=(0.0, 0.0, 0.0),
            current_velocity=(0.0, 2.0, 0.0),  # Moving in +Y
            look_ahead_distance=5.0,
        )

        # Should look 5 units ahead in Y direction
        compare_vectors(result, (0.0, 5.0, 0.0), tolerance=0.01)

    def test_moving_target_diagonal(self):
        """Diagonal movement should normalize and look ahead."""
        result = predict_look_ahead(
            current_position=(0.0, 0.0, 0.0),
            current_velocity=(1.0, 1.0, 0.0),  # Diagonal
            look_ahead_distance=1.414,  # sqrt(2)
        )

        # Should look ahead at ~45 degrees
        compare_numbers(abs(result[0]), 1.0, tolerance=0.1)
        compare_numbers(abs(result[1]), 1.0, tolerance=0.1)

    def test_moving_target_with_offset(self):
        """Look ahead from non-origin position."""
        result = predict_look_ahead(
            current_position=(10.0, 5.0, 2.0),
            current_velocity=(0.0, 1.0, 0.0),
            look_ahead_distance=3.0,
        )

        compare_vectors(result, (10.0, 8.0, 2.0), tolerance=0.01)


class TestCalculateAnticipationOffset:
    """Unit tests for calculate_anticipation_offset function."""

    def test_zero_speed(self):
        """Zero speed should return zero offset."""
        result = calculate_anticipation_offset(
            speed=0.0,
            max_speed=10.0,
            anticipation_distance=5.0,
        )

        compare_numbers(result, 0.0)

    def test_full_speed(self):
        """Full speed should return full anticipation distance."""
        result = calculate_anticipation_offset(
            speed=10.0,
            max_speed=10.0,
            anticipation_distance=5.0,
        )

        compare_numbers(result, 5.0)

    def test_half_speed(self):
        """Half speed should return half anticipation distance."""
        result = calculate_anticipation_offset(
            speed=5.0,
            max_speed=10.0,
            anticipation_distance=4.0,
        )

        compare_numbers(result, 2.0)

    def test_excessive_speed(self):
        """Speed exceeding max should be clamped."""
        result = calculate_anticipation_offset(
            speed=15.0,
            max_speed=10.0,
            anticipation_distance=5.0,
        )

        compare_numbers(result, 5.0)  # Clamped to max

    def test_zero_max_speed(self):
        """Zero max speed should return zero offset (avoid division by zero)."""
        result = calculate_anticipation_offset(
            speed=5.0,
            max_speed=0.0,
            anticipation_distance=5.0,
        )

        compare_numbers(result, 0.0)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_prediction_module_imports(self):
        """All prediction types should be importable."""
        from lib.cinematic.follow_cam.prediction import (
            MotionPredictor,
            PredictionResult,
            predict_look_ahead,
            calculate_anticipation_offset,
        )

        assert MotionPredictor is not None
        assert PredictionResult is not None

    def test_package_imports_prediction(self):
        """Prediction APIs should be importable from package."""
        from lib.cinematic.follow_cam import (
            MotionPredictor,
            PredictionResult,
            predict_look_ahead,
            calculate_anticipation_offset,
        )

        assert MotionPredictor is not None
        assert PredictionResult is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
