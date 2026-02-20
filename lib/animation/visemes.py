"""
Viseme System

Viseme definitions and lip sync functionality.

Phase 13.4: Face Animation (REQ-ANIM-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import re
import math

from .types import (
    VisemeType,
    LipSyncConfig,
    LipSyncFrame,
    ShapeKeyCategory,
)


# Standard phoneme to viseme mapping (Preston Blair system)
PHONEME_TO_VISEME = {
    # Consonants
    "p": VisemeType.M,
    "b": VisemeType.M,
    "m": VisemeType.M,
    "f": VisemeType.F,
    "v": VisemeType.F,
    "th": VisemeType.TH,
    "t": VisemeType.T,
    "d": VisemeType.T,
    "n": VisemeType.N,
    "l": VisemeType.L,
    "s": VisemeType.S,
    "z": VisemeType.S,
    "ch": VisemeType.CH,
    "sh": VisemeType.CH,
    "j": VisemeType.CH,
    "r": VisemeType.R,
    "w": VisemeType.W,
    "k": VisemeType.K,
    "g": VisemeType.K,
    "ng": VisemeType.K,
    "y": VisemeType.I,

    # Vowels
    "aa": VisemeType.A,
    "ae": VisemeType.E,
    "ah": VisemeType.A,
    "ao": VisemeType.O,
    "aw": VisemeType.O,
    "ay": VisemeType.E,
    "eh": VisemeType.E,
    "er": VisemeType.R,
    "ey": VisemeType.E,
    "ih": VisemeType.I,
    "iy": VisemeType.I,
    "ow": VisemeType.O,
    "oy": VisemeType.O,
    "uh": VisemeType.U,
    "uw": VisemeType.U,

    # Diphthongs
    "au": VisemeType.A,
    "ou": VisemeType.O,
    "ai": VisemeType.A,
    "ei": VisemeType.E,
    "oi": VisemeType.O,
    "ui": VisemeType.U,
}


# Default shape key configurations for each viseme
DEFAULT_VISEME_SHAPES = {
    VisemeType.REST: {
        "jaw_open": 0.0,
        "mouth_pucker": 0.0,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.0,
    },
    VisemeType.A: {
        "jaw_open": 0.7,
        "mouth_pucker": 0.0,
        "smile_L": 0.1,
        "smile_R": 0.1,
        "lip_funnel": 0.0,
    },
    VisemeType.E: {
        "jaw_open": 0.3,
        "mouth_pucker": 0.0,
        "smile_L": 0.6,
        "smile_R": 0.6,
        "lip_funnel": 0.0,
    },
    VisemeType.I: {
        "jaw_open": 0.2,
        "mouth_pucker": 0.0,
        "smile_L": 0.8,
        "smile_R": 0.8,
        "lip_funnel": 0.0,
    },
    VisemeType.O: {
        "jaw_open": 0.5,
        "mouth_pucker": 0.5,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.3,
    },
    VisemeType.U: {
        "jaw_open": 0.2,
        "mouth_pucker": 0.7,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.6,
    },
    VisemeType.M: {
        "jaw_open": 0.0,
        "mouth_pucker": 0.0,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.0,
    },
    VisemeType.F: {
        "jaw_open": 0.1,
        "mouth_pucker": 0.0,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.0,
    },
    VisemeType.TH: {
        "jaw_open": 0.15,
        "mouth_pucker": 0.0,
        "smile_L": 0.1,
        "smile_R": 0.1,
        "lip_funnel": 0.0,
    },
    VisemeType.L: {
        "jaw_open": 0.2,
        "mouth_pucker": 0.0,
        "smile_L": 0.2,
        "smile_R": 0.2,
        "lip_funnel": 0.0,
    },
    VisemeType.W: {
        "jaw_open": 0.1,
        "mouth_pucker": 0.6,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.5,
    },
    VisemeType.CH: {
        "jaw_open": 0.15,
        "mouth_pucker": 0.4,
        "smile_L": 0.1,
        "smile_R": 0.1,
        "lip_funnel": 0.3,
    },
    VisemeType.S: {
        "jaw_open": 0.1,
        "mouth_pucker": 0.0,
        "smile_L": 0.4,
        "smile_R": 0.4,
        "lip_funnel": 0.0,
    },
    VisemeType.N: {
        "jaw_open": 0.15,
        "mouth_pucker": 0.0,
        "smile_L": 0.1,
        "smile_R": 0.1,
        "lip_funnel": 0.0,
    },
    VisemeType.K: {
        "jaw_open": 0.4,
        "mouth_pucker": 0.0,
        "smile_L": 0.1,
        "smile_R": 0.1,
        "lip_funnel": 0.0,
    },
    VisemeType.T: {
        "jaw_open": 0.15,
        "mouth_pucker": 0.0,
        "smile_L": 0.2,
        "smile_R": 0.2,
        "lip_funnel": 0.0,
    },
    VisemeType.R: {
        "jaw_open": 0.2,
        "mouth_pucker": 0.4,
        "smile_L": 0.0,
        "smile_R": 0.0,
        "lip_funnel": 0.2,
    },
}


@dataclass
class PhonemeTiming:
    """Timing data for a phoneme in speech."""
    phoneme: str
    start_frame: int
    end_frame: int
    intensity: float = 1.0


class VisemeMapper:
    """Map phonemes to visemes."""

    def __init__(self, custom_mapping: Optional[Dict[str, VisemeType]] = None):
        """Initialize viseme mapper.

        Args:
            custom_mapping: Optional custom phoneme-to-viseme mapping
        """
        self.mapping = dict(PHONEME_TO_VISEME)
        if custom_mapping:
            self.mapping.update(custom_mapping)

    def phoneme_to_viseme(self, phoneme: str) -> VisemeType:
        """Convert a phoneme to a viseme.

        Args:
            phoneme: Phoneme string (IPA or ASCII)

        Returns:
            Corresponding VisemeType
        """
        phoneme_lower = phoneme.lower()

        # Try direct match
        if phoneme_lower in self.mapping:
            return self.mapping[phoneme_lower]

        # Try partial match for multi-character phonemes
        for key in self.mapping:
            if phoneme_lower.startswith(key) or key.startswith(phoneme_lower):
                return self.mapping[key]

        # Default to rest
        return VisemeType.REST

    def get_viseme_shape_keys(
        self,
        viseme: VisemeType,
        intensity: float = 1.0
    ) -> Dict[str, float]:
        """Get shape key values for a viseme.

        Args:
            viseme: Viseme type
            intensity: Intensity multiplier (0.0-1.0)

        Returns:
            Dict of shape key name -> value
        """
        base_shapes = DEFAULT_VISEME_SHAPES.get(viseme, {})
        return {
            name: value * intensity
            for name, value in base_shapes.items()
        }

    def text_to_visemes(self, text: str) -> List[Tuple[str, VisemeType]]:
        """Simple text to viseme conversion.

        This is a basic implementation. For production use,
        integrate a proper speech synthesis library.

        Args:
            text: Text to convert

        Returns:
            List of (character, viseme) tuples
        """
        result = []
        text = text.lower()

        i = 0
        while i < len(text):
            char = text[i]

            # Check for multi-character phonemes first
            if i + 1 < len(text):
                two_char = text[i:i+2]
                if two_char in ["th", "ch", "sh", "ng"]:
                    viseme = self.phoneme_to_viseme(two_char)
                    result.append((two_char, viseme))
                    i += 2
                    continue

            # Single character
            viseme = self.phoneme_to_viseme(char)
            result.append((char, viseme))
            i += 1

        return result


class LipSyncGenerator:
    """Generate lip sync animation data."""

    def __init__(
        self,
        frame_rate: float = 24.0,
        blend_frames: int = 2,
        coarticulation: bool = True
    ):
        """Initialize lip sync generator.

        Args:
            frame_rate: Animation frame rate
            blend_frames: Number of frames for viseme transitions
            coarticulation: Enable coarticulation blending
        """
        self.frame_rate = frame_rate
        self.blend_frames = blend_frames
        self.coarticulation = coarticulation
        self.mapper = VisemeMapper()

    def generate_from_phonemes(
        self,
        name: str,
        phoneme_timings: List[PhonemeTiming]
    ) -> LipSyncConfig:
        """Generate lip sync from phoneme timing data.

        Args:
            name: Configuration name
            phoneme_timings: List of PhonemeTiming objects

        Returns:
            LipSyncConfig with frame data
        """
        frames = []

        for pt in phoneme_timings:
            viseme = self.mapper.phoneme_to_viseme(pt.phoneme)

            # Create frame data
            for frame in range(pt.start_frame, pt.end_frame + 1):
                # Calculate transition progress
                transition_progress = 0.0
                transition_from = None

                if self.coarticulation and frame == pt.start_frame:
                    # Find previous viseme
                    for prev_pt in phoneme_timings:
                        if prev_pt.end_frame == pt.start_frame - 1:
                            transition_from = self.mapper.phoneme_to_viseme(prev_pt.phoneme)
                            transition_progress = 0.5  # Mid-transition
                            break

                lip_frame = LipSyncFrame(
                    frame=frame,
                    viseme=viseme,
                    intensity=pt.intensity,
                    transition_from=transition_from,
                    transition_progress=transition_progress,
                )
                frames.append(lip_frame)

        return LipSyncConfig(
            name=name,
            frames=frames,
            frame_rate=self.frame_rate,
            blend_frames=self.blend_frames,
            coarticulation=self.coarticulation,
        )

    def generate_from_text(
        self,
        name: str,
        text: str,
        words_per_minute: int = 150,
        start_frame: int = 1
    ) -> LipSyncConfig:
        """Generate basic lip sync from text.

        This is a simplified implementation. For accurate lip sync,
        use audio analysis tools.

        Args:
            name: Configuration name
            text: Text to animate
            words_per_minute: Speaking rate
            start_frame: First frame for animation

        Returns:
            LipSyncConfig with frame data
        """
        # Calculate frames per character (rough estimate)
        frames_per_second = self.frame_rate
        chars_per_minute = words_per_minute * 5  # Average 5 chars per word
        frames_per_char = (frames_per_second * 60) / chars_per_minute

        # Convert text to visemes
        visemes = self.mapper.text_to_visemes(text)

        frames = []
        current_frame = start_frame

        for char, viseme in visemes:
            # Skip spaces (rest position)
            if char == " ":
                current_frame += 1
                continue

            frame_duration = max(2, int(frames_per_char))
            end_frame = current_frame + frame_duration

            for frame in range(current_frame, end_frame):
                frames.append(LipSyncFrame(
                    frame=frame,
                    viseme=viseme,
                    intensity=1.0,
                ))

            current_frame = end_frame + 1

        return LipSyncConfig(
            name=name,
            frames=frames,
            frame_rate=self.frame_rate,
            blend_frames=self.blend_frames,
            coarticulation=self.coarticulation,
        )

    def apply_blend_curves(self, config: LipSyncConfig) -> LipSyncConfig:
        """Apply smooth blending to lip sync frames.

        Args:
            config: Original LipSyncConfig

        Returns:
            New LipSyncConfig with smoothed transitions
        """
        if not self.coarticulation or len(config.frames) < 3:
            return config

        blended_frames = []

        for i, frame in enumerate(config.frames):
            # Calculate blend based on position in viseme
            if i > 0 and i < len(config.frames) - 1:
                prev_viseme = config.frames[i - 1].viseme
                next_viseme = config.frames[i + 1].viseme

                if prev_viseme != frame.viseme:
                    # Start of new viseme - ease in
                    progress = 0.5  # Midway through transition
                elif next_viseme != frame.viseme:
                    # End of viseme - ease out
                    progress = 0.5
                else:
                    progress = 1.0

                blended_frames.append(LipSyncFrame(
                    frame=frame.frame,
                    viseme=frame.viseme,
                    intensity=frame.intensity * progress,
                    transition_from=frame.transition_from,
                    transition_progress=progress if progress < 1.0 else 0.0,
                ))
            else:
                blended_frames.append(frame)

        return LipSyncConfig(
            name=config.name,
            frames=blended_frames,
            frame_rate=config.frame_rate,
            audio_file=config.audio_file,
            blend_frames=config.blend_frames,
            coarticulation=config.coarticulation,
            intensity_curve=config.intensity_curve,
        )


class LipSyncPlayer:
    """Play back lip sync animation."""

    def __init__(self, config: LipSyncConfig):
        """Initialize lip sync player.

        Args:
            config: LipSyncConfig to play
        """
        self.config = config
        self.mapper = VisemeMapper()
        self._frame_index: Dict[int, LipSyncFrame] = {
            f.frame: f for f in config.frames
        }
        self._current_frame = 1
        self._playing = False

    def get_frame_data(self, frame: int) -> Optional[LipSyncFrame]:
        """Get frame data for a specific frame.

        Args:
            frame: Frame number

        Returns:
            LipSyncFrame or None
        """
        return self._frame_index.get(frame)

    def get_shape_keys_for_frame(
        self,
        frame: int,
        custom_shapes: Optional[Dict[VisemeType, Dict[str, float]]] = None
    ) -> Dict[str, float]:
        """Get shape key values for a frame.

        Args:
            frame: Frame number
            custom_shapes: Optional custom viseme shape configurations

        Returns:
            Dict of shape key name -> value
        """
        frame_data = self.get_frame_data(frame)
        if not frame_data:
            return {}

        # Get shape keys for current viseme
        shapes = DEFAULT_VISEME_SHAPES.get(frame_data.viseme, {})

        # Apply custom shapes if provided
        if custom_shapes and frame_data.viseme in custom_shapes:
            shapes = custom_shapes[frame_data.viseme]

        # Apply intensity
        shapes = {
            name: value * frame_data.intensity
            for name, value in shapes.items()
        }

        # Blend with transition viseme if applicable
        if frame_data.transition_from and frame_data.transition_progress > 0:
            prev_shapes = DEFAULT_VISEME_SHAPES.get(frame_data.transition_from, {})
            if custom_shapes and frame_data.transition_from in custom_shapes:
                prev_shapes = custom_shapes[frame_data.transition_from]

            blend_factor = frame_data.transition_progress
            for name, value in prev_shapes.items():
                if name in shapes:
                    shapes[name] = shapes[name] * (1 - blend_factor) + value * blend_factor * 0.5
                else:
                    shapes[name] = value * blend_factor * 0.5

        return shapes

    def get_frame_range(self) -> Tuple[int, int]:
        """Get the frame range of the lip sync.

        Returns:
            Tuple of (start_frame, end_frame)
        """
        if not self.config.frames:
            return (1, 1)
        frames = [f.frame for f in self.config.frames]
        return (min(frames), max(frames))

    def get_duration_seconds(self) -> float:
        """Get the duration in seconds.

        Returns:
            Duration in seconds
        """
        start, end = self.get_frame_range()
        frame_count = end - start + 1
        return frame_count / self.config.frame_rate

    def advance_frame(self) -> Optional[Dict[str, float]]:
        """Advance to the next frame and get shape keys.

        Returns:
            Shape key dict or None if at end
        """
        start, end = self.get_frame_range()

        if self._current_frame > end:
            return None

        shapes = self.get_shape_keys_for_frame(self._current_frame)
        self._current_frame += 1
        return shapes

    def reset(self) -> None:
        """Reset to the beginning."""
        start, _ = self.get_frame_range()
        self._current_frame = start

    def seek_to_frame(self, frame: int) -> bool:
        """Seek to a specific frame.

        Args:
            frame: Target frame

        Returns:
            True if frame is in range
        """
        start, end = self.get_frame_range()
        if start <= frame <= end:
            self._current_frame = frame
            return True
        return False


# Convenience functions
def create_viseme_mapper() -> VisemeMapper:
    """Create a default viseme mapper.

    Returns:
        VisemeMapper instance
    """
    return VisemeMapper()


def get_viseme_names() -> List[str]:
    """Get all viseme names.

    Returns:
        List of viseme names
    """
    return [v.value for v in VisemeType]


def get_vowel_visemes() -> List[VisemeType]:
    """Get vowel visemes.

    Returns:
        List of vowel VisemeTypes
    """
    return [
        VisemeType.A, VisemeType.E, VisemeType.I,
        VisemeType.O, VisemeType.U,
    ]


def get_consonant_visemes() -> List[VisemeType]:
    """Get consonant visemes.

    Returns:
        List of consonant VisemeTypes
    """
    return [
        VisemeType.M, VisemeType.F, VisemeType.TH,
        VisemeType.L, VisemeType.W, VisemeType.CH,
        VisemeType.S, VisemeType.N, VisemeType.K,
        VisemeType.T, VisemeType.R,
    ]


def quick_lip_sync(
    text: str,
    name: str = "lip_sync",
    frame_rate: float = 24.0,
    start_frame: int = 1
) -> LipSyncConfig:
    """Generate a quick lip sync from text.

    Args:
        text: Text to animate
        name: Configuration name
        frame_rate: Animation frame rate
        start_frame: First frame

    Returns:
        LipSyncConfig
    """
    generator = LipSyncGenerator(frame_rate=frame_rate)
    return generator.generate_from_text(name, text, start_frame=start_frame)
