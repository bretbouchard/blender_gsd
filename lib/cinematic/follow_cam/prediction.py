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


# =============================================================================
# OSCILLATION PREVENTION (Phase 8.2)
# =============================================================================

class OscillationPreventer:
    """
    Prevents camera position oscillation and jitter.

    Detects rapid direction changes in camera movement and applies
    damping to stabilize the camera. Part of the operator behavior
    simulation that makes camera movement feel natural.

    Configuration is typically sourced from:
    - OperatorBehavior dataclass (reaction_delay, oscillation_threshold, etc.)
    - prediction_settings.yaml (oscillation_prevention section)

    Usage:
        preventer = OscillationPreventer()

        # Each frame, check if movement should be damped
        new_pos, damping = preventer.filter_position(
            target_pos,
            current_pos,
            dt,
            threshold=0.1,
            max_direction_changes=3,
        )
        # Apply damping factor to movement
        filtered_pos = current_pos.lerp(target_pos, 1.0 - damping)

    Part of Phase 8.2 - Obstacle Avoidance
    Beads: blender_gsd-58
    """

    def __init__(
        self,
        history_size: int = 10,
        threshold: float = 0.1,
        max_direction_changes: int = 3,
        damping_strength: float = 0.5,
        min_damping_factor: float = 0.3,
        recovery_rate: float = 0.1,
    ):
        """
        Initialize oscillation preventer.

        Args:
            history_size: Number of positions to track
            threshold: Minimum distance change before response (meters)
            max_direction_changes: Max direction changes per second before damping
            damping_strength: How strongly to damp when oscillation detected (0-1)
            min_damping_factor: Minimum damping factor (prevents complete freeze)
            recovery_rate: How fast damping decreases when stable (0-1)
        """
        self._position_history: List[Tuple[float, float, float]] = []
        self._time_history: List[float] = []
        self._direction_changes: List[float] = []  # Timestamps of direction changes
        self._current_damping: float = 0.0
        self._last_direction: Optional[Vector] = None

        self.history_size = history_size
        self.threshold = threshold
        self.max_direction_changes = max_direction_changes
        self.damping_strength = damping_strength
        self.min_damping_factor = min_damping_factor
        self.recovery_rate = recovery_rate

    def record_position(
        self,
        position: Tuple[float, float, float],
        time: float,
    ) -> None:
        """
        Record camera position for oscillation analysis.

        Args:
            position: Current camera position
            time: Current time (seconds)
        """
        self._position_history.append(position)
        self._time_history.append(time)

        # Trim history
        if len(self._position_history) > self.history_size:
            self._position_history = self._position_history[-self.history_size:]
            self._time_history = self._time_history[-self.history_size:]

    def filter_position(
        self,
        target_position: Tuple[float, float, float],
        current_position: Tuple[float, float, float],
        time: float,
        dt: float = 1.0 / 60.0,
    ) -> Tuple[Tuple[float, float, float], float]:
        """
        Filter target position to prevent oscillation.

        Args:
            target_position: Desired camera position
            current_position: Current camera position
            time: Current time (seconds)
            dt: Delta time since last frame

        Returns:
            Tuple of (filtered_position, damping_factor)
            damping_factor: 0 = no damping, 1 = maximum damping
        """
        target = Vector(target_position)
        current = Vector(current_position)

        # Calculate movement delta
        delta = target - current
        delta_length = delta.length()

        # Check if movement is below threshold
        if delta_length < self.threshold:
            # Below threshold - no movement needed
            self._reduce_damping(dt)
            return current_position, self._current_damping

        # Calculate movement direction
        direction = delta.normalized()

        # Track direction changes
        if self._last_direction is not None:
            # Dot product to detect direction change
            dot = direction.dot(self._last_direction)
            if dot < 0:  # Direction reversed
                self._direction_changes.append(time)

        self._last_direction = direction

        # Clean up old direction changes (older than 1 second)
        self._direction_changes = [t for t in self._direction_changes if time - t < 1.0]

        # Check for oscillation
        num_changes = len(self._direction_changes)
        if num_changes >= self.max_direction_changes:
            # Oscillation detected - increase damping
            self._increase_damping(dt, num_changes)
        else:
            # Stable - reduce damping
            self._reduce_damping(dt)

        # Apply damping
        if self._current_damping > 0:
            # Interpolate between current and target based on damping
            damping_blend = 1.0 - (self._current_damping * self.damping_strength)
            damping_blend = max(self.min_damping_factor, damping_blend)
            filtered = current.lerp(target, damping_blend)
            return tuple(filtered._values), self._current_damping

        return target_position, 0.0

    def _increase_damping(self, dt: float, num_changes: int) -> None:
        """
        Increase damping when oscillation detected.

        Args:
            dt: Delta time
            num_changes: Number of recent direction changes
        """
        # Scale damping based on how many direction changes
        excess = num_changes - self.max_direction_changes
        increase_rate = 0.5 + (excess * 0.2)  # Faster increase for more changes
        self._current_damping = min(1.0, self._current_damping + increase_rate * dt)

    def _reduce_damping(self, dt: float) -> None:
        """
        Reduce damping when movement is stable.

        Args:
            dt: Delta time
        """
        self._current_damping = max(0.0, self._current_damping - self.recovery_rate * dt)

    def get_stability_score(self) -> float:
        """
        Get current stability score.

        Returns:
            Stability score from 0 (oscillating) to 1 (stable)
        """
        return 1.0 - self._current_damping

    def is_oscillating(self) -> bool:
        """
        Check if camera is currently oscillating.

        Returns:
            True if oscillation is detected
        """
        return self._current_damping > 0.1

    def reset(self) -> None:
        """Reset oscillation preventer state."""
        self._position_history.clear()
        self._time_history.clear()
        self._direction_changes.clear()
        self._current_damping = 0.0
        self._last_direction = None

    @classmethod
    def from_operator_behavior(
        cls,
        operator_behavior: "OperatorBehavior",
    ) -> "OscillationPreventer":
        """
        Create OscillationPreventer from OperatorBehavior config.

        Args:
            operator_behavior: OperatorBehavior dataclass instance

        Returns:
            Configured OscillationPreventer instance
        """
        return cls(
            history_size=operator_behavior.position_history_size,
            threshold=operator_behavior.oscillation_threshold,
            max_direction_changes=operator_behavior.max_direction_changes,
            damping_strength=0.5,
            min_damping_factor=0.3,
            recovery_rate=0.1,
        )


# =============================================================================
# OPERATOR BEHAVIOR SIMULATION (Phase 8.2)
# =============================================================================

def apply_breathing(
    base_position: Tuple[float, float, float],
    time: float,
    amplitude: float = 0.01,
    frequency: float = 0.25,
    enabled: bool = True,
) -> Tuple[float, float, float]:
    """
    Apply subtle breathing motion to camera position.

    Simulates the natural sway of a human camera operator.

    Args:
        base_position: Base camera position
        time: Current time (seconds)
        amplitude: Breathing amplitude in meters
        frequency: Breathing frequency in Hz
        enabled: Whether breathing is enabled

    Returns:
        Position with breathing applied
    """
    if not enabled or amplitude <= 0:
        return base_position

    # Calculate breathing offset (primarily vertical)
    breath_cycle = math.sin(time * frequency * 2 * math.pi)
    vertical_offset = breath_cycle * amplitude

    # Small horizontal sway
    horizontal_sway = math.sin(time * frequency * 1.5 * math.pi) * amplitude * 0.3

    pos = Vector(base_position)
    pos.z += vertical_offset
    pos.x += horizontal_sway

    return tuple(pos._values)


def apply_reaction_delay(
    current_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    reaction_delay: float,
    dt: float,
    smoothing: float = 0.1,
) -> Tuple[float, float, float]:
    """
    Apply human-like reaction delay to camera movement.

    The camera doesn't instantly respond to target movement,
    creating a more natural feel.

    Args:
        current_pos: Current camera position
        target_pos: Target position
        reaction_delay: Reaction time in seconds
        dt: Delta time
        smoothing: Additional smoothing factor

    Returns:
        Filtered position with reaction delay applied
    """
    if reaction_delay <= 0:
        return target_pos

    # Calculate blend based on reaction delay
    # Lower blend = slower reaction
    blend = min(1.0, dt / reaction_delay) * (1.0 - smoothing)

    current = Vector(current_pos)
    target = Vector(target_pos)

    result = current.lerp(target, blend)
    return tuple(result._values)


def calculate_angle_preference(
    current_angles: Tuple[float, float],
    preferred_range_h: Tuple[float, float],
    preferred_range_v: Tuple[float, float],
    weight: float = 0.5,
) -> Tuple[float, float]:
    """
    Calculate angle adjustment based on operator preferences.

    Operators tend to favor certain shooting angles.

    Args:
        current_angles: Current (yaw, pitch) angles in degrees
        preferred_range_h: Preferred horizontal angle range (min, max)
        preferred_range_v: Preferred vertical angle range (min, max)
        weight: How strongly to favor preferred range

    Returns:
        Adjusted (yaw, pitch) angles
    """
    yaw, pitch = current_angles
    min_h, max_h = preferred_range_h
    min_v, max_v = preferred_range_v

    # Calculate how far outside preferred range
    yaw_offset = 0.0
    if yaw < min_h:
        yaw_offset = min_h - yaw
    elif yaw > max_h:
        yaw_offset = max_h - yaw

    pitch_offset = 0.0
    if pitch < min_v:
        pitch_offset = min_v - pitch
    elif pitch > max_v:
        pitch_offset = max_v - pitch

    # Apply weighted adjustment
    adjusted_yaw = yaw + yaw_offset * weight
    adjusted_pitch = pitch + pitch_offset * weight

    return adjusted_yaw, adjusted_pitch
