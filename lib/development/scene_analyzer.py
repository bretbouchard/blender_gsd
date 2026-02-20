"""
Scene Analyzer - Analyze scenes for shot generation.

Implements REQ-SHOT-01, REQ-SHOT-02
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re

from .script_types import Scene, ActionBlock, DialogueLine
from .shot_gen_types import ShotSuggestion, CoverageEstimate


@dataclass
class SceneAnalysis:
    """Analysis result for a single scene."""
    scene_number: int
    scene_type: str  # dialogue, action, mixed, transition
    character_count: int
    speaking_characters: List[str]
    action_intensity: str  # low, medium, high
    dialogue_intensity: str  # low, medium, high
    key_moments: List[int]  # Line indices of key moments
    emotional_beats: List[Tuple[int, str]]  # (line_index, emotion)
    estimated_duration: float
    suggested_shots: int


def analyze_scene_for_shots(scene: Scene) -> List[ShotSuggestion]:
    """Analyze scene and generate shot suggestions.

    Args:
        scene: Scene object from parsed script

    Returns:
        List of shot suggestions for the scene
    """
    suggestions = []

    # Analyze scene composition
    analysis = analyze_scene_content(scene)
    characters = scene.get_characters_in_scene()

    shot_number = 1

    # Always start with establishing shot for new locations
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="w",
        camera_angle="eye_level",
        subject=scene.location,
        purpose="establishing",
        estimated_duration=4.0,
        priority="essential",
        description=f"Establish {scene.location}",
        camera_move="static",
        notes="Establish scene location and atmosphere"
    ))
    shot_number += 1

    # Generate shots based on scene type
    if analysis.scene_type == "dialogue":
        suggestions.extend(_generate_dialogue_shots(scene, characters, shot_number))
    elif analysis.scene_type == "action":
        suggestions.extend(_generate_action_shots(scene, shot_number))
    else:  # mixed
        suggestions.extend(_generate_mixed_shots(scene, characters, shot_number))

    return suggestions


def _generate_dialogue_shots(
    scene: Scene,
    characters: List[str],
    start_shot: int
) -> List[ShotSuggestion]:
    """Generate shots for dialogue-heavy scenes."""
    suggestions = []
    shot_number = start_shot

    # Master shot for the scene
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="w",
        camera_angle="eye_level",
        subject=", ".join(characters),
        purpose="coverage",
        estimated_duration=scene.estimate_duration(),
        priority="essential",
        description="Master shot - full scene",
        camera_move="static",
        notes="Cover entire dialogue exchange"
    ))
    shot_number += 1

    # Two-person dialogue
    if len(characters) == 2:
        # Over-the-shoulder shots
        for i, char in enumerate(characters):
            suggestions.append(ShotSuggestion(
                scene_number=scene.number,
                shot_number=shot_number,
                shot_size="mcu",
                camera_angle="eye_level",
                subject=char,
                purpose="coverage",
                estimated_duration=scene.estimate_duration() * 0.4,
                priority="essential",
                description=f"OTS on {char}",
                camera_move="static",
                notes=f"Over-the-shoulder on {char}"
            ))
            shot_number += 1

        # Close-ups for key moments
        for char in characters:
            suggestions.append(ShotSuggestion(
                scene_number=scene.number,
                shot_number=shot_number,
                shot_size="cu",
                camera_angle="eye_level",
                subject=char,
                purpose="coverage",
                estimated_duration=5.0,
                priority="recommended",
                description=f"Close-up on {char}",
                camera_move="static",
                notes="For emphasis or emotional moments"
            ))
            shot_number += 1

    # Multi-person dialogue
    elif len(characters) > 2:
        # Individual close-ups
        for char in characters:
            suggestions.append(ShotSuggestion(
                scene_number=scene.number,
                shot_number=shot_number,
                shot_size="cu",
                camera_angle="eye_level",
                subject=char,
                purpose="coverage",
                estimated_duration=5.0,
                priority="essential",
                description=f"Close-up on {char}",
                camera_move="static"
            ))
            shot_number += 1

        # Group shots
        suggestions.append(ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="m",
            camera_angle="eye_level",
            subject="Group",
            purpose="coverage",
            estimated_duration=10.0,
            priority="recommended",
            description="Group shot",
            camera_move="static"
        ))
        shot_number += 1

    # Reaction shots
    for char in characters:
        suggestions.append(ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="cu",
            camera_angle="eye_level",
            subject=char,
            purpose="reaction",
            estimated_duration=3.0,
            priority="recommended",
            description=f"Reaction shot - {char}",
            camera_move="static",
            notes="For listening/reacting moments"
        ))
        shot_number += 1

    return suggestions


def _generate_action_shots(
    scene: Scene,
    start_shot: int
) -> List[ShotSuggestion]:
    """Generate shots for action-heavy scenes."""
    suggestions = []
    shot_number = start_shot
    action_text = scene.get_action_text()

    # Master shot
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="w",
        camera_angle="eye_level",
        subject="Action",
        purpose="coverage",
        estimated_duration=scene.estimate_duration(),
        priority="essential",
        description="Master shot - action sequence",
        camera_move="handheld",
        notes="Capture full action from wide angle"
    ))
    shot_number += 1

    # Key action beats
    key_moments = identify_key_moments(scene)
    for i, moment_idx in enumerate(key_moments[:5]):  # Limit to 5 key moments
        suggestions.append(ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="mcu" if i % 2 == 0 else "cu",
            camera_angle="low" if i % 3 == 0 else "eye_level",
            subject="Action",
            purpose="coverage",
            estimated_duration=3.0,
            priority="essential",
            description=f"Action beat {i + 1}",
            camera_move="handheld",
            notes="Key action moment"
        ))
        shot_number += 1

    # Insert shots for details
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="ecu",
        camera_angle="eye_level",
        subject="Detail",
        purpose="insert",
        estimated_duration=2.0,
        priority="recommended",
        description="Insert - action detail",
        camera_move="static",
        notes="Close-up on important action detail"
    ))
    shot_number += 1

    # Optional: Slow motion suggestion
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="m",
        camera_angle="low",
        subject="Action",
        purpose="coverage",
        estimated_duration=4.0,
        priority="optional",
        description="Slow motion option",
        camera_move="crane",
        notes="High-speed capture for slow-mo effect"
    ))

    return suggestions


def _generate_mixed_shots(
    scene: Scene,
    characters: List[str],
    start_shot: int
) -> List[ShotSuggestion]:
    """Generate shots for mixed dialogue/action scenes."""
    suggestions = []
    shot_number = start_shot

    # Master shot
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="w",
        camera_angle="eye_level",
        subject="Scene",
        purpose="coverage",
        estimated_duration=scene.estimate_duration(),
        priority="essential",
        description="Master shot",
        camera_move="static"
    ))
    shot_number += 1

    # Character coverage
    for char in characters:
        suggestions.append(ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="cu",
            camera_angle="eye_level",
            subject=char,
            purpose="coverage",
            estimated_duration=5.0,
            priority="essential",
            description=f"Close-up on {char}",
            camera_move="static"
        ))
        shot_number += 1

    # Two-shot for dialogue
    if len(characters) >= 2:
        suggestions.append(ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="m",
            camera_angle="eye_level",
            subject=f"{characters[0]} & {characters[1]}",
            purpose="coverage",
            estimated_duration=10.0,
            priority="recommended",
            description="Two-shot",
            camera_move="static"
        ))
        shot_number += 1

    # Action inserts
    suggestions.append(ShotSuggestion(
        scene_number=scene.number,
        shot_number=shot_number,
        shot_size="mcu",
        camera_angle="eye_level",
        subject="Action",
        purpose="insert",
        estimated_duration=3.0,
        priority="recommended",
        description="Action insert",
        camera_move="handheld"
    ))

    return suggestions


def analyze_scene_content(scene: Scene) -> SceneAnalysis:
    """Perform comprehensive scene analysis.

    Args:
        scene: Scene to analyze

    Returns:
        SceneAnalysis with detailed breakdown
    """
    # Count characters
    speaking_characters = scene.get_characters_in_scene()
    character_count = len(speaking_characters)

    # Calculate action/dialogue ratio
    action_words = sum(len(a.text.split()) for a in scene.action)
    dialogue_words = sum(d.word_count() for d in scene.dialogue)
    total_words = action_words + dialogue_words

    if total_words == 0:
        dialogue_ratio = 0.5
    else:
        dialogue_ratio = dialogue_words / total_words

    # Determine scene type
    if dialogue_ratio > 0.7:
        scene_type = "dialogue"
        dialogue_intensity = "high"
        action_intensity = "low"
    elif dialogue_ratio < 0.3:
        scene_type = "action"
        dialogue_intensity = "low"
        action_intensity = "high"
    else:
        scene_type = "mixed"
        if dialogue_ratio > 0.5:
            dialogue_intensity = "medium"
            action_intensity = "low"
        else:
            dialogue_intensity = "low"
            action_intensity = "medium"

    # Estimate duration
    estimated_duration = scene.estimate_duration()

    # Find key moments
    key_moments = identify_key_moments(scene)

    # Detect emotional beats
    emotional_beats = _detect_emotional_beats(scene)

    # Estimate shot count
    suggested_shots = _estimate_shot_count(
        scene_type,
        character_count,
        estimated_duration
    )

    return SceneAnalysis(
        scene_number=scene.number,
        scene_type=scene_type,
        character_count=character_count,
        speaking_characters=speaking_characters,
        action_intensity=action_intensity,
        dialogue_intensity=dialogue_intensity,
        key_moments=key_moments,
        emotional_beats=emotional_beats,
        estimated_duration=estimated_duration,
        suggested_shots=suggested_shots
    )


def count_characters_in_scene(scene: Scene) -> int:
    """Count speaking characters in scene.

    Args:
        scene: Scene to analyze

    Returns:
        Number of unique speaking characters
    """
    return len(scene.get_characters_in_scene())


def identify_scene_type(scene: Scene) -> str:
    """Identify scene type (dialogue, action, mixed, transition).

    Args:
        scene: Scene to analyze

    Returns:
        Scene type string
    """
    analysis = analyze_scene_content(scene)
    return analysis.scene_type


def estimate_scene_duration(scene: Scene) -> float:
    """Estimate scene duration in seconds.

    Args:
        scene: Scene to analyze

    Returns:
        Estimated duration in seconds
    """
    return scene.estimate_duration()


def identify_key_moments(scene: Scene) -> List[int]:
    """Identify key moments that need coverage.

    Analyzes action blocks and dialogue for important beats.

    Args:
        scene: Scene to analyze

    Returns:
        List of line indices for key moments
    """
    key_moments = []

    # Keywords that indicate important moments
    action_keywords = [
        "suddenly", "just then", "at that moment", "crash", "explode",
        "scream", "gunshot", "silence", "beat", "pause", "stare",
        "looks at", "turns", "enters", "exits", "reveals"
    ]

    dialogue_keywords = [
        "what?", "how?", "why?", "no!", "yes!", "really?",
        "i love you", "i hate you", "you're lying", "trust me"
    ]

    # Check action blocks
    for i, action in enumerate(scene.action):
        text_lower = action.text.lower()
        for keyword in action_keywords:
            if keyword in text_lower:
                key_moments.append(i)
                break

    # Check dialogue
    for i, dialogue in enumerate(scene.dialogue):
        text_lower = dialogue.text.lower()
        for keyword in dialogue_keywords:
            if keyword in text_lower:
                # Offset by action count for unique indices
                key_moments.append(len(scene.action) + i)
                break

    return key_moments


def _detect_emotional_beats(scene: Scene) -> List[Tuple[int, str]]:
    """Detect emotional beats in scene.

    Args:
        scene: Scene to analyze

    Returns:
        List of (line_index, emotion) tuples
    """
    emotional_beats = []

    emotion_patterns = {
        "anger": ["angry", "furious", "rage", "scream", "yell", "shout"],
        "fear": ["afraid", "scared", "terrified", "panic", "trembling"],
        "joy": ["happy", "excited", "laugh", "smile", "grin", "delighted"],
        "sadness": ["sad", "cry", "tears", "weep", "sob", "heartbroken"],
        "surprise": ["shock", "surprise", "gasp", "amazed", "stunned"],
        "tension": ["tense", "nervous", "anxious", "worried", "suspense"]
    }

    # Check action blocks
    for i, action in enumerate(scene.action):
        text_lower = action.text.lower()
        for emotion, patterns in emotion_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    emotional_beats.append((i, emotion))
                    break

    return emotional_beats


def _estimate_shot_count(
    scene_type: str,
    character_count: int,
    duration: float
) -> int:
    """Estimate number of shots needed.

    Args:
        scene_type: Type of scene
        character_count: Number of characters
        duration: Scene duration in seconds

    Returns:
        Estimated shot count
    """
    base_shots = 2  # Establishing + master

    if scene_type == "dialogue":
        # Each character needs coverage
        base_shots += character_count * 2  # CU + reaction
        if character_count == 2:
            base_shots += 2  # OTS shots
        elif character_count > 2:
            base_shots += 1  # Group shot

    elif scene_type == "action":
        # More cuts for action
        base_shots += max(5, int(duration / 5))  # ~1 cut per 5 seconds
        base_shots += 2  # Inserts

    else:  # mixed
        base_shots += character_count  # Character coverage
        base_shots += max(3, int(duration / 10))  # Action beats

    return base_shots


def calculate_coverage_estimate(scene: Scene) -> CoverageEstimate:
    """Calculate coverage estimate for a scene.

    Args:
        scene: Scene to analyze

    Returns:
        CoverageEstimate with shot counts
    """
    analysis = analyze_scene_content(scene)
    characters = scene.get_characters_in_scene()

    coverage = CoverageEstimate(scene_number=scene.number)

    # Establishing shot
    coverage.establishing_shots = 1

    # Master shot
    coverage.master_shots = 1

    if analysis.scene_type == "dialogue":
        # Close-ups for each character
        coverage.closeups = len(characters)

        # Two-shots or OTS
        if len(characters) == 2:
            coverage.two_shots = 3  # OTS A, OTS B, two-shot
        else:
            coverage.two_shots = 1  # Group shot

        # Reactions
        coverage.reactions = len(characters)

        # Inserts for important props/actions mentioned
        coverage.inserts = 1

    elif analysis.scene_type == "action":
        # Action beats
        key_moments = identify_key_moments(scene)
        coverage.closeups = min(5, len(key_moments))

        # Inserts for action details
        coverage.inserts = 2

    else:  # mixed
        coverage.closeups = len(characters)
        coverage.two_shots = 1 if len(characters) >= 2 else 0
        coverage.reactions = len(characters)
        coverage.inserts = 2

    # Calculate minimum (essential) and recommended coverage
    coverage.minimum_coverage = (
        coverage.establishing_shots +
        coverage.master_shots +
        coverage.closeups
    )

    coverage.recommended_coverage = (
        coverage.minimum_coverage +
        coverage.two_shots +
        coverage.reactions
    )

    coverage.calculate_totals()

    return coverage


# Export all functions
__all__ = [
    "SceneAnalysis",
    "analyze_scene_for_shots",
    "analyze_scene_content",
    "count_characters_in_scene",
    "identify_scene_type",
    "estimate_scene_duration",
    "identify_key_moments",
    "calculate_coverage_estimate",
]
