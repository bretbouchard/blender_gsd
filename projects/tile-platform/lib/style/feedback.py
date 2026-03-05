"""
Visual feedback system for satisfying mechanical motion.

Provides overshoot, settle, and feedback effects for
motion polish that emphasizes mechanical authenticity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple
import math


class FeedbackType(Enum):
    """Types of visual feedback events."""
    TILE_PLACE = "tile_place"      # Tile placement feedback
    TILE_REMOVE = "tile_remove"    # Tile removal feedback
    ARM_LOCK = "arm_lock"          # Arm locked in position
    ARM_RELEASE = "arm_release"    # Arm released for movement


@dataclass
class VisualFeedback:
    """Visual feedback configuration for an event."""
    feedback_type: FeedbackType
    duration: float      # Duration in seconds
    intensity: float     # Intensity multiplier (0.0-1.0)

    def __post_init__(self):
        """Validate feedback parameters."""
        if self.duration < 0.0:
            raise ValueError(f"Duration must be >= 0.0, got {self.duration}")
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be 0.0-1.0, got {self.intensity}")


class MotionPolish:
    """
    Motion polish system for satisfying mechanical feedback.

    Adds overshoot, settle, and easing effects to arm and tile motion
    to create satisfying weight and mechanical authenticity.
    """

    def __init__(
        self,
        overshoot_amount: float = 0.0,
        settle_time: float = 0.2,
        ease_curve: str = "ease_out_elastic"
    ):
        """
        Initialize motion polish system.

        Args:
            overshoot_amount: How much to overshoot target (0.0-1.0)
            settle_time: Time to settle after overshoot (seconds)
            ease_curve: Easing function name
        """
        self.overshoot_amount = overshoot_amount
        self.settle_time = settle_time
        self.ease_curve = ease_curve
        self._feedback_registry = self._initialize_feedback_registry()

    def _initialize_feedback_registry(self) -> dict:
        """Initialize default feedback configurations."""
        return {
            FeedbackType.TILE_PLACE: VisualFeedback(
                feedback_type=FeedbackType.TILE_PLACE,
                duration=0.3,
                intensity=0.8
            ),
            FeedbackType.TILE_REMOVE: VisualFeedback(
                feedback_type=FeedbackType.TILE_REMOVE,
                duration=0.2,
                intensity=0.5
            ),
            FeedbackType.ARM_LOCK: VisualFeedback(
                feedback_type=FeedbackType.ARM_LOCK,
                duration=0.15,
                intensity=1.0
            ),
            FeedbackType.ARM_RELEASE: VisualFeedback(
                feedback_type=FeedbackType.ARM_RELEASE,
                duration=0.1,
                intensity=0.6
            ),
        }

    def apply_overshoot(
        self,
        target_pos: Tuple[float, float, float],
        direction: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Add overshoot to motion toward target.

        Args:
            target_pos: Target position (x, y, z)
            direction: Direction of motion (normalized vector)

        Returns:
            Position with overshoot applied
        """
        if self.overshoot_amount <= 0.0:
            return target_pos

        # Calculate overshoot offset
        overshoot_distance = self.overshoot_amount
        overshoot_offset = (
            direction[0] * overshoot_distance,
            direction[1] * overshoot_distance,
            direction[2] * overshoot_distance
        )

        # Apply overshoot
        return (
            target_pos[0] + overshoot_offset[0],
            target_pos[1] + overshoot_offset[1],
            target_pos[2] + overshoot_offset[2]
        )

    def apply_settle(
        self,
        current_pos: Tuple[float, float, float],
        target_pos: Tuple[float, float, float],
        progress: float
    ) -> Tuple[float, float, float]:
        """
        Apply settling motion from overshoot back to target.

        Args:
            current_pos: Current position (with overshoot)
            target_pos: Final target position
            progress: Settle progress (0.0-1.0)

        Returns:
            Settled position
        """
        if progress >= 1.0:
            return target_pos

        # Use easing function for smooth settle
        eased_progress = self._ease_out_elastic(progress)

        # Interpolate toward target
        return (
            current_pos[0] + (target_pos[0] - current_pos[0]) * eased_progress,
            current_pos[1] + (target_pos[1] - current_pos[1]) * eased_progress,
            current_pos[2] + (target_pos[2] - current_pos[2]) * eased_progress
        )

    def create_feedback(self, event: FeedbackType) -> VisualFeedback:
        """
        Create visual feedback for an event type.

        Args:
            event: Type of feedback event

        Returns:
            VisualFeedback configuration
        """
        if event in self._feedback_registry:
            return self._feedback_registry[event]

        # Default feedback if not registered
        return VisualFeedback(
            feedback_type=event,
            duration=0.2,
            intensity=0.5
        )

    def register_feedback(
        self,
        event: FeedbackType,
        duration: float,
        intensity: float
    ) -> None:
        """
        Register custom feedback for an event type.

        Args:
            event: Type of feedback event
            duration: Duration in seconds
            intensity: Intensity multiplier (0.0-1.0)
        """
        feedback = VisualFeedback(
            feedback_type=event,
            duration=duration,
            intensity=intensity
        )
        self._feedback_registry[event] = feedback

    def _ease_out_elastic(self, t: float) -> float:
        """
        Elastic easing function for bouncy settle.

        Args:
            t: Progress (0.0-1.0)

        Returns:
            Eased value
        """
        if t == 0.0 or t == 1.0:
            return t

        # Elastic ease out
        p = 0.3  # Period
        s = p / 4.0

        return math.pow(2.0, -10.0 * t) * math.sin((t - s) * (2.0 * math.pi) / p) + 1.0

    def _ease_out_back(self, t: float) -> float:
        """
        Back easing function for overshoot.

        Args:
            t: Progress (0.0-1.0)

        Returns:
            Eased value
        """
        c1 = 1.70158
        c3 = c1 + 1.0

        return 1.0 + c3 * math.pow(t - 1.0, 3.0) + c1 * math.pow(t - 1.0, 2.0)

    def calculate_motion_phase(
        self,
        time_elapsed: float,
        total_duration: float
    ) -> Tuple[str, float]:
        """
        Calculate current motion phase for polish effects.

        Args:
            time_elapsed: Time since motion start (seconds)
            total_duration: Total motion duration (seconds)

        Returns:
            Tuple of (phase_name, phase_progress)
            phase_name: "overshoot" or "settle"
            phase_progress: 0.0-1.0 progress within phase
        """
        if total_duration <= 0.0:
            return ("settle", 1.0)

        # Split time between overshoot and settle
        settle_start = total_duration * (1.0 - self.settle_time)

        if time_elapsed < settle_start:
            # Overshoot phase
            progress = time_elapsed / settle_start
            return ("overshoot", progress)
        else:
            # Settle phase
            settle_elapsed = time_elapsed - settle_start
            progress = min(settle_elapsed / self.settle_time, 1.0)
            return ("settle", progress)


if __name__ == "__main__":
    # Test the motion polish system
    print("Testing MotionPolish...")

    polish = MotionPolish(
        overshoot_amount=0.1,
        settle_time=0.2,
        ease_curve="ease_out_elastic"
    )

    # Test overshoot
    print("\nTesting overshoot...")
    target = (5.0, 0.0, 0.0)
    direction = (1.0, 0.0, 0.0)
    overshoot_pos = polish.apply_overshoot(target, direction)
    print(f"  Target: {target}")
    print(f"  Overshoot: {overshoot_pos}")

    # Test settle
    print("\nTesting settle...")
    current = (5.1, 0.0, 0.0)
    target = (5.0, 0.0, 0.0)
    settled = polish.apply_settle(current, target, 0.5)
    print(f"  Current: {current}")
    print(f"  Settled (50%): {settled}")

    # Test feedback
    print("\nTesting feedback...")
    for event in FeedbackType:
        feedback = polish.create_feedback(event)
        print(f"  {event.value}: duration={feedback.duration}s, intensity={feedback.intensity}")

    # Test motion phase calculation
    print("\nTesting motion phases...")
    total_duration = 1.0
    for elapsed in [0.0, 0.4, 0.8, 1.0]:
        phase, progress = polish.calculate_motion_phase(elapsed, total_duration)
        print(f"  {elapsed}s: {phase} @ {progress:.2f}")

    # Test custom feedback registration
    print("\nTesting custom feedback...")
    polish.register_feedback(FeedbackType.TILE_PLACE, duration=0.5, intensity=0.9)
    custom = polish.create_feedback(FeedbackType.TILE_PLACE)
    print(f"  Custom TILE_PLACE: duration={custom.duration}s, intensity={custom.intensity}")

    # Test validation
    try:
        invalid = VisualFeedback(
            feedback_type=FeedbackType.TILE_PLACE,
            duration=-1.0,
            intensity=0.5
        )
    except ValueError as e:
        print(f"\nValidation working: {e}")

    print("\n✓ MotionPolish tests passed")
