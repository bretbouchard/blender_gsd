"""
Beat Sheet Generator - Generate beat sheets from parsed scripts.

Implements REQ-SCRIPT-04
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .script_types import Script, Scene, Beat, BeatSheet


# Blake Snyder's Save the Cat beat structure
SAVE_THE_CAT_BEATS = {
    "opening_image": 0.0,        # 0%
    "setup": 0.0,                # 0-10%
    "theme_stated": 0.05,        # 5%
    "catalyst": 0.10,            # 10%
    "debate": 0.10,              # 10-20%
    "break_into_two": 0.25,      # 25%
    "b_story": 0.27,             # 27%
    "fun_and_games": 0.30,       # 30-50%
    "midpoint": 0.50,            # 50%
    "bad_guys_close_in": 0.50,   # 50-62%
    "all_is_lost": 0.62,         # 62%
    "dark_night_of_soul": 0.75,  # 75%
    "break_into_three": 0.80,    # 80%
    "finale": 0.80,              # 80-100%
    "final_image": 1.0,          # 100%
}

# Three-act structure
THREE_ACT_BEATS = {
    "act_1_end": 0.25,           # 25%
    "act_2_midpoint": 0.50,      # 50%
    "act_2_end": 0.75,           # 75%
    "climax": 0.90,              # 90%
}

# Dan Harmon's Story Circle
STORY_CIRCLE_BEATS = {
    "you": 0.0,                  # 0% - Protagonist in comfort zone
    "need": 0.12,                # 12% - They want something
    "go": 0.25,                  # 25% - They enter unfamiliar situation
    "search": 0.37,              # 37% - Adapt to it
    "find": 0.50,                # 50% - Get what they wanted
    "take": 0.62,                # 62% - Pay heavy price
    "return": 0.75,              # 75% - Return to familiar
    "change": 0.87,              # 87% - Having changed
}


def generate_beat_sheet(
    script: Script,
    structure: str = "save_the_cat"
) -> BeatSheet:
    """Generate beat sheet from parsed script.

    Args:
        script: Parsed Script object
        structure: Beat structure to use
            - "save_the_cat": Blake Snyder's 15-beat structure
            - "three_act": Traditional three-act structure
            - "story_circle": Dan Harmon's 8-beat circle

    Returns:
        BeatSheet with identified beats and act breaks
    """
    if not script.scenes:
        return BeatSheet()

    total_scenes = len(script.scenes)

    # Select beat structure
    if structure == "save_the_cat":
        beat_structure = SAVE_THE_CAT_BEATS
    elif structure == "three_act":
        beat_structure = THREE_ACT_BEATS
    elif structure == "story_circle":
        beat_structure = STORY_CIRCLE_BEATS
    else:
        beat_structure = SAVE_THE_CAT_BEATS

    beats = []

    # Map beats to scenes
    for beat_name, position in beat_structure.items():
        scene_number = int(position * total_scenes) + 1
        scene_number = min(scene_number, total_scenes)

        if scene_number >= 1:
            scene = script.get_scene_by_number(scene_number)
            if scene:
                description = _describe_beat(beat_name, scene)
                emotional_value = _calculate_emotional_value(beat_name, position)

                beat = Beat(
                    scene_number=scene_number,
                    beat_type=beat_name,
                    description=description,
                    emotional_value=emotional_value,
                    pages=scene.page_end - scene.page_start + 1
                )
                beats.append(beat)

    # Identify act breaks
    act_breaks = identify_act_breaks(script, structure)

    return BeatSheet(beats=beats, act_breaks=act_breaks)


def identify_act_breaks(
    script: Script,
    structure: str = "save_the_cat"
) -> List[int]:
    """Identify act break scene numbers.

    Args:
        script: Parsed Script object
        structure: Beat structure used

    Returns:
        List of scene numbers where acts end
    """
    if not script.scenes:
        return []

    total_scenes = len(script.scenes)
    act_breaks = []

    if structure == "save_the_cat":
        # Act 1 ends at Break into Two (25%)
        act1_scene = int(0.25 * total_scenes) + 1
        act_breaks.append(min(act1_scene, total_scenes))

        # Act 2 ends at Break into Three (80%)
        act2_scene = int(0.80 * total_scenes) + 1
        act_breaks.append(min(act2_scene, total_scenes))

    elif structure == "three_act":
        # Traditional three-act structure
        act_breaks.append(int(0.25 * total_scenes) + 1)  # End of Act 1
        act_breaks.append(int(0.75 * total_scenes) + 1)  # End of Act 2

    elif structure == "story_circle":
        # Story circle doesn't have traditional acts, but we can mark major shifts
        act_breaks.append(int(0.25 * total_scenes) + 1)  # "Go" - crossing threshold
        act_breaks.append(int(0.75 * total_scenes) + 1)  # "Return" - return home

    return sorted(set(act_breaks))


def calculate_pacing(script: Script) -> List[float]:
    """Calculate pacing curve (tension/intensity over time).

    Uses heuristics based on:
    - Scene length (shorter = faster pacing)
    - Dialogue density (more dialogue = slower pacing)
    - Action density (more action = faster pacing)
    - Scene changes (frequent changes = faster pacing)

    Args:
        script: Parsed Script object

    Returns:
        List of pacing values (0.0 to 1.0) per scene
    """
    if not script.scenes:
        return []

    pacing_values = []
    window_size = 3  # Rolling window for smoothing

    for i, scene in enumerate(script.scenes):
        # Calculate scene pacing factors
        duration = scene.estimated_duration

        # Short scenes = faster pacing
        duration_factor = 1.0 - min(duration / 120.0, 1.0)  # 2 min = slow

        # Dialogue heavy = slower
        dialogue_words = sum(len(d.text.split()) for d in scene.dialogue)
        action_words = sum(len(a.text.split()) for a in scene.action)
        total_words = dialogue_words + action_words

        if total_words > 0:
            dialogue_ratio = dialogue_words / total_words
        else:
            dialogue_ratio = 0.5

        dialogue_factor = 1.0 - dialogue_ratio

        # Multiple characters = more dynamic
        character_count = len(scene.get_characters_in_scene())
        character_factor = min(character_count / 4.0, 1.0)

        # Combine factors
        pacing = (
            duration_factor * 0.4 +
            dialogue_factor * 0.3 +
            character_factor * 0.3
        )

        pacing_values.append(pacing)

    # Apply smoothing with rolling window
    smoothed = []
    for i, pacing in enumerate(pacing_values):
        start = max(0, i - window_size // 2)
        end = min(len(pacing_values), i + window_size // 2 + 1)
        window = pacing_values[start:end]
        smoothed.append(sum(window) / len(window))

    return smoothed


def identify_emotional_peaks(script: Script) -> List[int]:
    """Identify emotional peak scenes.

    Uses heuristics to find scenes with high emotional intensity:
    - Many characters present
    - Long dialogue (revelations, confrontations)
    - Key story beats (act breaks, midpoint)

    Args:
        script: Parsed Script object

    Returns:
        List of scene numbers with emotional peaks
    """
    if not script.scenes:
        return []

    peaks = []
    total_scenes = len(script.scenes)

    # Calculate emotional score for each scene
    for i, scene in enumerate(script.scenes):
        score = 0.0

        # Multiple characters = emotional scene
        char_count = len(scene.get_characters_in_scene())
        score += char_count * 0.15

        # Long dialogue = important scene
        dialogue_lines = len(scene.dialogue)
        score += min(dialogue_lines / 10.0, 0.3)

        # Key structural positions
        position = (i + 1) / total_scenes

        # Midpoint (50%)
        if 0.45 <= position <= 0.55:
            score += 0.3

        # All is Lost (62%)
        if 0.58 <= position <= 0.66:
            score += 0.4

        # Climax (90%)
        if 0.85 <= position <= 0.95:
            score += 0.5

        # Break into Act 2 and 3
        if 0.22 <= position <= 0.28:
            score += 0.25
        if 0.77 <= position <= 0.83:
            score += 0.25

        # Threshold for peak
        if score >= 0.6:
            peaks.append(scene.number)

    return peaks


def _describe_beat(beat_name: str, scene: Scene) -> str:
    """Generate description for a beat based on scene content.

    Args:
        beat_name: Name of the beat
        scene: Scene at this beat position

    Returns:
        Human-readable description
    """
    descriptions = {
        "opening_image": f"Opening image establishes tone at {scene.location}",
        "setup": f"Setup: Introducing characters at {scene.location}",
        "theme_stated": f"Theme stated through dialogue",
        "catalyst": f"Catalyst event: Something happens at {scene.location}",
        "debate": f"Debate: Character weighs options",
        "break_into_two": f"Break into Act 2: Entering new world",
        "b_story": f"B-story begins (secondary relationship)",
        "fun_and_games": f"Fun and games: Core premise explored",
        "midpoint": f"Midpoint: Stakes raised at {scene.location}",
        "bad_guys_close_in": f"Bad guys close in: Pressure mounts",
        "all_is_lost": f"All is lost moment",
        "dark_night_of_soul": f"Dark night of the soul",
        "break_into_three": f"Break into Act 3: Resolution approach",
        "finale": f"Finale: Climactic confrontation",
        "final_image": f"Final image mirrors opening",
        "act_1_end": f"Act 1 ends: Journey begins",
        "act_2_midpoint": f"Act 2 midpoint: Major revelation",
        "act_2_end": f"Act 2 ends: Crisis point",
        "climax": f"Climax: Final showdown",
        "you": f"You: Protagonist in comfort zone",
        "need": f"Need: Character wants something",
        "go": f"Go: Entering unfamiliar territory",
        "search": f"Search: Adapting to new world",
        "find": f"Find: Getting what was wanted",
        "take": f"Take: Paying the price",
        "return": f"Return: Coming back",
        "change": f"Change: Transformed by journey",
    }

    base_description = descriptions.get(beat_name, f"{beat_name.replace('_', ' ').title()}")

    # Add character information if available
    characters = scene.get_characters_in_scene()
    if characters:
        char_str = ", ".join(characters[:3])
        if len(characters) > 3:
            char_str += f" (+{len(characters) - 3})"
        base_description += f" ({char_str})"

    return base_description


def _calculate_emotional_value(beat_name: str, position: float) -> float:
    """Calculate emotional value for a beat.

    Args:
        beat_name: Name of the beat
        position: Position in script (0.0 to 1.0)

    Returns:
        Emotional value (-1.0 to 1.0)
    """
    # Emotional curve mapping
    emotional_values = {
        "opening_image": 0.0,
        "setup": 0.2,
        "theme_stated": 0.3,
        "catalyst": 0.0,
        "debate": -0.2,
        "break_into_two": 0.5,
        "b_story": 0.3,
        "fun_and_games": 0.6,
        "midpoint": 0.8 if position >= 0.5 else 0.6,
        "bad_guys_close_in": -0.4,
        "all_is_lost": -0.8,
        "dark_night_of_soul": -0.6,
        "break_into_three": 0.2,
        "finale": 0.9,
        "final_image": 0.5,
        "act_1_end": 0.3,
        "act_2_midpoint": 0.7,
        "act_2_end": -0.5,
        "climax": 1.0,
        "you": 0.0,
        "need": 0.2,
        "go": 0.4,
        "search": 0.3,
        "find": 0.7,
        "take": -0.7,
        "return": 0.3,
        "change": 0.8,
    }

    return emotional_values.get(beat_name, 0.0)


def create_beat_summary(script: Script, beat_sheet: BeatSheet) -> str:
    """Create a text summary of the beat sheet.

    Args:
        script: Parsed Script object
        beat_sheet: Generated BeatSheet

    Returns:
        Human-readable summary text
    """
    lines = []
    lines.append(f"Beat Sheet for: {script.title or 'Untitled'}")
    lines.append(f"Structure: {len(beat_sheet.beats)} beats, {len(beat_sheet.act_breaks)} act breaks")
    lines.append("")

    current_act = 1

    for beat in beat_sheet.beats:
        # Check for act break
        if beat.scene_number in beat_sheet.act_breaks:
            lines.append(f"--- ACT {current_act} END (Scene {beat.scene_number}) ---")
            current_act += 1

        # Format beat
        emotional = beat.emotional_value
        emotional_str = "+" * int(emotional * 5) if emotional > 0 else "-" * int(abs(emotional) * 5)

        lines.append(
            f"Scene {beat.scene_number:3d} | {beat.beat_type:20s} | {emotional_str:10s} | {beat.description}"
        )

    return "\n".join(lines)


__all__ = [
    "generate_beat_sheet",
    "identify_act_breaks",
    "calculate_pacing",
    "identify_emotional_peaks",
    "create_beat_summary",
    "SAVE_THE_CAT_BEATS",
    "THREE_ACT_BEATS",
    "STORY_CIRCLE_BEATS",
]
