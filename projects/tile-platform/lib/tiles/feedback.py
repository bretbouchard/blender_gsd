"""
Visual feedback system for tile connections.

This module provides visual effects and feedback sequences for magneto-mechanical
tile connections. It creates satisfying visual cues when tiles connect to and
disconnect from the platform.

All effects are pure Python data structures - no Blender dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class VisualEffect(Enum):
    """Visual effect types for tile feedback."""

    NONE = "none"  # No effect
    GLOW = "glow"  # Emission glow
    SPARK = "spark"  # Electrical sparks
    MAGNETIC = "magnetic"  # Magnetic field lines
    LOCK = "lock"  # Mechanical lock indicator


@dataclass
class TileFeedback:
    """
    Feedback to play when a tile connects or disconnects.

    Attributes:
        effect_type: Type of visual effect
        duration: Duration in seconds
        intensity: Intensity from 0.0 to 1.0
        color: RGBA color tuple (0.0-1.0 for each channel)
        trigger_time: When to trigger (None for immediate)
    """

    effect_type: VisualEffect
    duration: float
    intensity: float = 1.0
    color: Optional[Tuple[float, float, float, float]] = None
    trigger_time: Optional[float] = None

    def __post_init__(self):
        """Validate feedback parameters."""
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got {self.intensity}")
        if self.duration < 0:
            raise ValueError(f"Duration must be non-negative, got {self.duration}")


@dataclass
class FeedbackSequence:
    """
    A sequence of feedback effects to play in order.

    Attributes:
        effects: List of TileFeedback instances
        total_duration: Total duration of the sequence in seconds
    """

    effects: List[TileFeedback] = field(default_factory=list)
    total_duration: float = 0.0

    def __post_init__(self):
        """Calculate total duration if not provided."""
        if self.effects and self.total_duration == 0.0:
            # Calculate from effects, accounting for trigger times
            max_end_time = 0.0
            for effect in self.effects:
                start = effect.trigger_time if effect.trigger_time else 0.0
                end = start + effect.duration
                max_end_time = max(max_end_time, end)
            self.total_duration = max_end_time

    def add_effect(self, effect: TileFeedback) -> "FeedbackSequence":
        """
        Add an effect to the sequence.

        Args:
            effect: TileFeedback to add

        Returns:
            Self for method chaining
        """
        self.effects.append(effect)
        self.__post_init__()  # Recalculate duration
        return self


def connection_sequence(style: str = "default") -> FeedbackSequence:
    """
    Create a standard connection feedback sequence.

    Args:
        style: Style preset ("default", "industrial", "high_tech", "brutalist")

    Returns:
        FeedbackSequence for tile connection
    """
    if style == "industrial":
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.MAGNETIC,
                    duration=0.3,
                    intensity=0.8,
                    color=(0.8, 0.8, 0.8, 1.0),  # Metallic gray
                    trigger_time=0.0,
                ),
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.2,
                    intensity=1.0,
                    color=(0.6, 0.6, 0.6, 1.0),  # Darker gray
                    trigger_time=0.3,
                ),
            ],
            total_duration=0.5,
        )
    elif style == "high_tech":
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.GLOW,
                    duration=0.2,
                    intensity=0.6,
                    color=(0.2, 0.6, 1.0, 1.0),  # Cyan glow
                    trigger_time=0.0,
                ),
                TileFeedback(
                    effect_type=VisualEffect.SPARK,
                    duration=0.3,
                    intensity=0.9,
                    color=(0.4, 0.8, 1.0, 1.0),  # Bright cyan spark
                    trigger_time=0.2,
                ),
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.2,
                    intensity=1.0,
                    color=(0.2, 0.6, 1.0, 1.0),  # Cyan lock
                    trigger_time=0.5,
                ),
            ],
            total_duration=0.7,
        )
    elif style == "brutalist":
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.4,
                    intensity=1.0,
                    color=(0.9, 0.9, 0.9, 1.0),  # Bright white
                    trigger_time=0.0,
                ),
            ],
            total_duration=0.4,
        )
    else:  # default
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.MAGNETIC,
                    duration=0.2,
                    intensity=0.7,
                    color=(0.5, 0.7, 0.9, 1.0),  # Soft blue
                    trigger_time=0.0,
                ),
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.2,
                    intensity=0.9,
                    color=(0.6, 0.8, 1.0, 1.0),  # Blue lock
                    trigger_time=0.2,
                ),
            ],
            total_duration=0.4,
        )


def disconnection_sequence(style: str = "default") -> FeedbackSequence:
    """
    Create a standard disconnection feedback sequence.

    Args:
        style: Style preset ("default", "industrial", "high_tech", "brutalist")

    Returns:
        FeedbackSequence for tile disconnection
    """
    if style == "industrial":
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.15,
                    intensity=0.8,
                    color=(0.6, 0.6, 0.6, 1.0),  # Gray unlock
                    trigger_time=0.0,
                ),
                TileFeedback(
                    effect_type=VisualEffect.MAGNETIC,
                    duration=0.2,
                    intensity=0.6,
                    color=(0.7, 0.7, 0.7, 1.0),  # Fading magnetic
                    trigger_time=0.15,
                ),
            ],
            total_duration=0.35,
        )
    elif style == "high_tech":
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.1,
                    intensity=0.7,
                    color=(0.2, 0.6, 1.0, 1.0),  # Cyan unlock
                    trigger_time=0.0,
                ),
                TileFeedback(
                    effect_type=VisualEffect.SPARK,
                    duration=0.2,
                    intensity=0.5,
                    color=(0.3, 0.7, 1.0, 1.0),  # Fading spark
                    trigger_time=0.1,
                ),
            ],
            total_duration=0.3,
        )
    elif style == "brutalist":
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.2,
                    intensity=0.9,
                    color=(0.8, 0.8, 0.8, 1.0),  # Bright unlock
                    trigger_time=0.0,
                ),
            ],
            total_duration=0.2,
        )
    else:  # default
        return FeedbackSequence(
            effects=[
                TileFeedback(
                    effect_type=VisualEffect.LOCK,
                    duration=0.1,
                    intensity=0.7,
                    color=(0.6, 0.8, 1.0, 1.0),  # Blue unlock
                    trigger_time=0.0,
                ),
                TileFeedback(
                    effect_type=VisualEffect.MAGNETIC,
                    duration=0.15,
                    intensity=0.5,
                    color=(0.5, 0.7, 0.9, 1.0),  # Fading magnetic
                    trigger_time=0.1,
                ),
            ],
            total_duration=0.25,
        )
