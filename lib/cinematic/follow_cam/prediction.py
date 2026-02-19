"""
Follow Camera Motion Prediction

Implements motion prediction for smoother camera following:
- Velocity-based trajectory prediction
- Animation-based prediction (read keyframes ahead)
- Look-ahead system
- Speed anticipation
- Corner prediction for vehicles

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-59
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass, field

from .types import (
    FollowCameraConfig,
    FollowTarget,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Import fallback Vector from follow_modes
    from .follow_modes import Vector


@dataclass
class PredictionResult:
    """
    Result of motion prediction calculation.

    Attributes:
        predicted_position: Predicted target position
        predicted_velocity: Predicted target velocity
        predicted_forward: Predicted forward direction
        confidence: Confidence level (0-1)
        time_horizon: How far ahead the prediction is (seconds)
        is_corner: Whether a corner/turn is predicted
        corner_direction: Direction of predicted corner (1=right, -1=left, 0=straight)
    """
    predicted_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    predicted_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    predicted_forward: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    confidence: float = 0.5
    time_horizon: float = 0.5
    is_corner: bool = False
    corner_direction: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "predicted_position": list(self.predicted_position),
            "predicted_velocity": list(self.predicted_velocity),
            "predicted_forward": list(self.predicted_forward),
            "confidence": self.confidence,
            "time_horizon": self.time_horizon,
            "is_corner": self.is_corner,
            "corner_direction": self.corner_direction,
        }


class MotionPredictor:
    """
    Predicts future target position for smoother camera following.

    Uses multiple prediction methods:
    1. Velocity-based: Extrapolate from current velocity
    2. Animation-based: Read keyframes ahead
    3. Corner detection: Predict turns based on velocity changes

    Usage:
        predictor = MotionPredictor()

        # Record history each frame
        predictor.record_position(current_position, current_time)

        # Get prediction
        prediction = predictor.predict(
            target=target,
            config=config,
            time_ahead=0.5,  # Predict 0.5 seconds ahead
        )
    """

    def __init__(self, history_size: int = 60):
        """
        Initialize motion predictor.

        Args:
            history_size: Number of frames to keep in history
        """
        self._position_history: List[Tuple[float, float, float]] = []
        self._time_history: List[float] = []
        self._velocity_history: List[Tuple[float, float, float]] = []
        self._history_size = history_size
        self._last_velocity = Vector((0.0, 0.0, 0.0))
        self._smoothed_velocity = Vector((0.0, 0.0, 0.0))

    def record_position(
        self,
        position: Tuple[float, float, float],
        time: float,
    ) -> None:
        """
        Record position for velocity calculation.

        Call this every frame to build up velocity history.

        Args:
            position: Current target position
            time: Current time (seconds)
        """
        self._position_history.append(position)
        self._time_history.append(time)

        # Calculate instantaneous velocity
        if len(self._position_history) >= 2:
            last_pos = Vector(self._position_history[-2])
            curr_pos = Vector(position)
            last_time = self._time_history[-2]
            curr_time = time

            if curr_time > last_time:
                dt = curr_time - last_time
                velocity = (curr_pos - last_pos) / dt
                self._velocity_history.append(tuple(velocity._values))

                # Smooth velocity
                smoothing = 0.1
                self._smoothed_velocity = self._smoothed_velocity.lerp(velocity, smoothing)
                self._last_velocity = velocity

        # Trim history
        if len(self._position_history) > self._history_size:
            self._position_history = self._position_history[-self._history_size:]
            self._time_history = self._time_history[-self._history_size:]
            self._velocity_history = self._velocity_history[-self._history_size:]

    def predict(
        self,
        target: FollowTarget,
        config: FollowCameraConfig,
        time_ahead: Optional[float] = None,
    ) -> PredictionResult:
        """
        Predict future target position.

        Args:
            target: Follow target with prediction settings
            config: Camera configuration
            time_ahead: How far ahead to predict (uses config if not provided)

        Returns:
            PredictionResult with predicted position and metadata
        """
        if time_ahead is None:
            time_ahead = target.prediction_frames / 60.0  # Assume 60fps

        if not config.prediction_enabled:
            # Return current position with no prediction
            if self._position_history:
                return PredictionResult(
                    predicted_position=self._position_history[-1],
                    predicted_velocity=tuple(self._last_velocity._values),
                    confidence=1.0,
                    time_horizon=0.0,
                )
            return PredictionResult()

        # Start with velocity-based prediction
        result = self._predict_velocity_based(time_ahead, target.velocity_smoothing)

        # Enhance with animation-based prediction if available
        if target.use_animation_prediction and HAS_BLENDER:
            anim_result = self._predict_animation_based(target, time_ahead)
            if anim_result:
                # Blend predictions
                result = self._blend_predictions(result, anim_result, 0.5)

        # Detect corners
        result.is_corner, result.corner_direction = self._detect_corner()

        return result

    def _predict_velocity_based(
        self,
        time_ahead: float,
        smoothing: float,
    ) -> PredictionResult:
        """
        Predict based on velocity extrapolation.

        Uses smoothed velocity to predict future position.
        """
        if not self._position_history:
            return PredictionResult()

        current_pos = Vector(self._position_history[-1])
        velocity = self._smoothed_velocity

        # Simple linear prediction
        predicted_pos = current_pos + velocity * time_ahead

        # Calculate confidence based on velocity stability
        confidence = self._calculate_velocity_confidence()

        # Predict forward direction
        predicted_forward = velocity.normalized() if velocity.length() > 0.1 else Vector((0.0, 1.0, 0.0))

        return PredictionResult(
            predicted_position=tuple(predicted_pos._values),
            predicted_velocity=tuple(velocity._values),
            predicted_forward=tuple(predicted_forward._values),
            confidence=confidence,
            time_horizon=time_ahead,
        )

    def _predict_animation_based(
        self,
        target: FollowTarget,
        time_ahead: float,
    ) -> Optional[PredictionResult]:
        """
        Predict by reading animation keyframes.

        Only available in Blender with animated objects.
        """
        if not HAS_BLENDER:
            return None

        # Get the target object
        obj = bpy.data.objects.get(target.object_name)
        if obj is None:
            return None

        # Check if object has animation
        if obj.animation_data is None or obj.animation_data.action is None:
            return None

        # Get current frame
        current_frame = bpy.context.scene.frame_current
        frames_ahead = int(time_ahead * 24)  # Assume 24fps

        # Store current frame
        stored_frame = current_frame

        try:
            # Jump to future frame
            future_frame = current_frame + frames_ahead
            bpy.context.scene.frame_set(future_frame)

            # Read position at future frame
            predicted_pos = tuple(obj.matrix_world.translation)

            # Calculate predicted velocity
            current_pos = tuple(obj.matrix_world.translation)
            if time_ahead > 0:
                predicted_vel = tuple(
                    (p - c) / time_ahead
                    for p, c in zip(predicted_pos, current_pos)
                )
            else:
                predicted_vel = (0.0, 0.0, 0.0)

            return PredictionResult(
                predicted_position=predicted_pos,
                predicted_velocity=predicted_vel,
                confidence=0.9,  # High confidence for animation
                time_horizon=time_ahead,
            )

        finally:
            # Restore frame
            bpy.context.scene.frame_set(stored_frame)

    def _blend_predictions(
        self,
        pred1: PredictionResult,
        pred2: PredictionResult,
        blend_factor: float,
    ) -> PredictionResult:
        """
        Blend two predictions together.
        """
        pos1 = Vector(pred1.predicted_position)
        pos2 = Vector(pred2.predicted_position)
        blended_pos = pos1.lerp(pos2, blend_factor)

        vel1 = Vector(pred1.predicted_velocity)
        vel2 = Vector(pred2.predicted_velocity)
        blended_vel = vel1.lerp(vel2, blend_factor)

        fwd1 = Vector(pred1.predicted_forward)
        fwd2 = Vector(pred2.predicted_forward)
        blended_fwd = fwd1.lerp(fwd2, blend_factor).normalized()

        return PredictionResult(
            predicted_position=tuple(blended_pos._values),
            predicted_velocity=tuple(blended_vel._values),
            predicted_forward=tuple(blended_fwd._values),
            confidence=(pred1.confidence + pred2.confidence) / 2,
            time_horizon=pred1.time_horizon,
        )

    def _calculate_velocity_confidence(self) -> float:
        """
        Calculate confidence based on velocity stability.

        More consistent velocity = higher confidence.
        """
        if len(self._velocity_history) < 3:
            return 0.5

        # Calculate velocity variance
        recent_vels = [Vector(v) for v in self._velocity_history[-10:]]
        avg_vel = sum(recent_vels, Vector((0.0, 0.0, 0.0))) / len(recent_vels)

        # Calculate variance
        variance = 0.0
        for v in recent_vels:
            diff = (v - avg_vel).length()
            variance += diff * diff
        variance /= len(recent_vels)

        # Convert variance to confidence (less variance = more confidence)
        # Variance of 0 = confidence 1.0
        # Variance of 10+ = confidence 0.0
        confidence = max(0.0, 1.0 - variance / 10.0)

        return confidence

    def _detect_corner(self) -> Tuple[bool, float]:
        """
        Detect if target is approaching a corner/turn.

        Returns:
            Tuple of (is_corner, direction)
            direction: 1 = right turn, -1 = left turn, 0 = straight
        """
        if len(self._velocity_history) < 5:
            return False, 0.0

        # Look at velocity direction changes
        recent_vels = [Vector(v) for v in self._velocity_history[-5:]]

        # Calculate angular velocity
        angles = []
        for v in recent_vels:
            if v.length() > 0.1:
                angles.append(math.atan2(v.x, v.y))

        if len(angles) < 2:
            return False, 0.0

        # Calculate total angular change
        total_angle_change = 0.0
        for i in range(1, len(angles)):
            diff = angles[i] - angles[i-1]
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            total_angle_change += diff

        # Detect significant turn rate
        turn_rate = abs(total_angle_change)

        # Corner threshold: 30 degrees total in 5 frames
        if turn_rate > math.radians(30):
            direction = 1.0 if total_angle_change > 0 else -1.0
            return True, direction

        return False, 0.0

    def reset(self) -> None:
        """Clear prediction history."""
        self._position_history.clear()
        self._time_history.clear()
        self._velocity_history.clear()
        self._last_velocity = Vector((0.0, 0.0, 0.0))
        self._smoothed_velocity = Vector((0.0, 0.0, 0.0))


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def predict_look_ahead(
    current_position: Tuple[float, float, float],
    current_velocity: Tuple[float, float, float],
    look_ahead_distance: float,
    smoothing: float = 0.5,
) -> Tuple[float, float, float]:
    """
    Calculate look-ahead position for camera targeting.

    Simple utility for basic look-ahead without full prediction system.

    Args:
        current_position: Current target position
        current_velocity: Current target velocity
        look_ahead_distance: How far ahead to look
        smoothing: Smoothing factor for velocity

    Returns:
        Look-ahead position
    """
    pos = Vector(current_position)
    vel = Vector(current_velocity)

    if vel.length() < 0.01:
        return current_position

    # Normalize velocity and apply look-ahead distance
    direction = vel.normalized()
    look_ahead_pos = pos + direction * look_ahead_distance

    return tuple(look_ahead_pos._values)


def calculate_anticipation_offset(
    speed: float,
    max_speed: float,
    anticipation_distance: float,
) -> float:
    """
    Calculate anticipation offset based on speed.

    Higher speed = more anticipation.

    Args:
        speed: Current speed
        max_speed: Reference maximum speed
        anticipation_distance: Maximum anticipation distance

    Returns:
        Anticipation offset distance
    """
    if max_speed <= 0:
        return 0.0

    speed_ratio = min(speed / max_speed, 1.0)
    return anticipation_distance * speed_ratio
