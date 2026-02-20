"""
Script Analysis - Comprehensive analysis tools for screenplays.

Implements REQ-SCRIPT-05
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

from .script_types import Script, Scene, Character, Location, ScriptAnalysis
from .beat_generator import calculate_pacing, identify_emotional_peaks


def analyze_script(script: Script) -> ScriptAnalysis:
    """Generate comprehensive script analysis.

    Args:
        script: Parsed Script object

    Returns:
        ScriptAnalysis with statistics and recommendations
    """
    if not script.scenes:
        return ScriptAnalysis()

    analysis = ScriptAnalysis()

    # Basic counts
    analysis.total_scenes = len(script.scenes)
    analysis.character_count = len(script.characters)
    analysis.location_count = len(script.locations)

    # Page and runtime estimates
    analysis.total_pages = script.total_pages
    analysis.estimated_runtime = script.estimated_runtime

    # Dialogue vs Action analysis
    dialogue_words = 0
    action_words = 0

    for scene in script.scenes:
        for dialogue in scene.dialogue:
            dialogue_words += len(dialogue.text.split())
        for action in scene.action:
            action_words += len(action.text.split())

    total_words = dialogue_words + action_words
    if total_words > 0:
        analysis.dialogue_percentage = (dialogue_words / total_words) * 100
        analysis.action_percentage = (action_words / total_words) * 100

    # Day/Night ratio
    day_count = len(script.get_day_scenes())
    night_count = len(script.get_night_scenes())
    if night_count > 0:
        analysis.day_night_ratio = day_count / night_count
    else:
        analysis.day_night_ratio = float(day_count) if day_count > 0 else 1.0

    # Interior/Exterior ratio
    interior_count = len(script.get_interior_scenes())
    exterior_count = len(script.get_exterior_scenes())
    if exterior_count > 0:
        analysis.interior_exterior_ratio = interior_count / exterior_count
    else:
        analysis.interior_exterior_ratio = float(interior_count) if interior_count > 0 else 1.0

    # Longest and shortest scenes
    if script.scenes:
        scene_durations = [(s.number, s.estimate_duration()) for s in script.scenes]

        longest = max(scene_durations, key=lambda x: x[1])
        shortest = min(scene_durations, key=lambda x: x[1])

        analysis.longest_scene = longest[0]
        analysis.shortest_scene = shortest[0]

    # Character with most dialogue
    if script.characters:
        most_dialogue_char = max(script.characters, key=lambda c: c.dialogue_count)
        analysis.most_dialogue = most_dialogue_char.name

    # Pacing curve
    analysis.pacing = calculate_pacing(script)

    # Generate recommendations
    analysis.recommendations = generate_recommendations(script, analysis)

    return analysis


def generate_recommendations(script: Script, analysis: ScriptAnalysis) -> List[str]:
    """Generate actionable recommendations for script improvement.

    Args:
        script: Parsed Script object
        analysis: ScriptAnalysis results

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Runtime recommendations
    if analysis.estimated_runtime < 85:
        recommendations.append(
            f"Script is short ({analysis.estimated_runtime:.0f} min). "
            "Consider expanding character development or subplots."
        )
    elif analysis.estimated_runtime > 130:
        recommendations.append(
            f"Script is long ({analysis.estimated_runtime:.0f} min). "
            "Consider trimming scenes or tightening dialogue."
        )

    # Dialogue/Action balance
    if analysis.dialogue_percentage > 70:
        recommendations.append(
            f"Heavy on dialogue ({analysis.dialogue_percentage:.0f}%). "
            "Consider adding more visual storytelling."
        )
    elif analysis.action_percentage > 80:
        recommendations.append(
            f"Heavy on action ({analysis.action_percentage:.0f}%). "
            "Consider adding dialogue to develop characters."
        )

    # Scene count recommendations
    if analysis.total_scenes > 80:
        recommendations.append(
            f"Many scenes ({analysis.total_scenes}). "
            "Consider combining similar scenes for better flow."
        )

    # Day/Night balance
    if analysis.day_night_ratio > 5:
        recommendations.append(
            "Heavily weighted toward day scenes. "
            "Consider night scenes for visual variety and mood."
        )
    elif analysis.day_night_ratio < 0.2:
        recommendations.append(
            "Heavily weighted toward night scenes. "
            "Consider day scenes for contrast and energy."
        )

    # Interior/Exterior balance
    if analysis.interior_exterior_ratio > 10:
        recommendations.append(
            "Mostly interior locations. "
            "Consider exterior scenes for visual scope and production value."
        )

    # Character distribution
    if script.characters:
        top_char = script.characters[0]
        if len(script.characters) > 1:
            second_char = script.characters[1]
            ratio = top_char.dialogue_count / max(second_char.dialogue_count, 1)
            if ratio > 5:
                recommendations.append(
                    f"'{top_char.name}' dominates dialogue ({ratio:.1f}x more than second lead). "
                    "Consider balancing character voices."
                )

        # Many minor characters
        minor_chars = [c for c in script.characters if c.dialogue_count < 3]
        if len(minor_chars) > len(script.characters) * 0.6:
            recommendations.append(
                f"Many minor characters ({len(minor_chars)} with <3 lines). "
                "Consider consolidating or cutting."
            )

    # Location variety
    if script.locations:
        single_scene_locations = [l for l in script.locations if l.scene_count == 1]
        if len(single_scene_locations) > len(script.locations) * 0.5:
            recommendations.append(
                f"Many single-use locations ({len(single_scene_locations)}). "
                "Consider consolidating locations for production efficiency."
            )

    # Scene length variance
    if script.scenes:
        durations = [s.estimate_duration() for s in script.scenes]
        avg_duration = sum(durations) / len(durations)

        very_long = [s for s in script.scenes if s.estimate_duration() > avg_duration * 3]
        if very_long:
            recommendations.append(
                f"{len(very_long)} very long scene(s) (>3x average). "
                "Consider breaking up for better pacing."
            )

    # Pacing issues
    if analysis.pacing:
        # Check for monotonous pacing
        pacing_variance = sum(
            (p - sum(analysis.pacing) / len(analysis.pacing)) ** 2
            for p in analysis.pacing
        ) / len(analysis.pacing)

        if pacing_variance < 0.01:
            recommendations.append(
                "Pacing appears flat throughout. "
                "Consider varying scene lengths and intensity."
            )

    # Emotional peaks
    peaks = identify_emotional_peaks(script)
    if len(peaks) < 3:
        recommendations.append(
            f"Few emotional peaks ({len(peaks)} identified). "
            "Consider heightening key dramatic moments."
        )

    return recommendations


def get_character_network(script: Script) -> Dict[str, List[str]]:
    """Build character interaction network.

    Characters who appear in the same scene are considered connected.

    Args:
        script: Parsed Script object

    Returns:
        Dict mapping character names to list of characters they share scenes with
    """
    network: Dict[str, set] = {}

    for scene in script.scenes:
        characters_in_scene = scene.get_characters_in_scene()

        for char in characters_in_scene:
            if char not in network:
                network[char] = set()

            # Add all other characters in this scene
            for other in characters_in_scene:
                if other != char:
                    network[char].add(other)

    # Convert sets to sorted lists
    return {char: sorted(list(connections)) for char, connections in network.items()}


def get_location_schedule(script: Script) -> Dict[str, List[int]]:
    """Get scene schedule organized by location.

    Useful for production scheduling (shooting by location).

    Args:
        script: Parsed Script object

    Returns:
        Dict mapping location names to list of scene numbers
    """
    schedule: Dict[str, List[int]] = {}

    for scene in script.scenes:
        loc = scene.location
        if loc not in schedule:
            schedule[loc] = []
        schedule[loc].append(scene.number)

    return schedule


def get_cast_list(script: Script) -> List[Dict]:
    """Generate cast list with scene appearances.

    Args:
        script: Parsed Script object

    Returns:
        List of dicts with character info and appearance list
    """
    cast = []

    for char in script.characters:
        cast.append({
            "name": char.name,
            "dialogue_count": char.dialogue_count,
            "scenes": sorted(char.scenes_appearing),
            "first_appearance": char.first_appearance,
            "last_appearance": char.last_appearance,
        })

    return cast


def get_daily_breakdown(script: Script, pages_per_day: float = 5.0) -> List[Dict]:
    """Break down script into shooting days.

    Args:
        script: Parsed Script object
        pages_per_day: Target pages to shoot per day (default 5)

    Returns:
        List of shooting day breakdowns with scenes and locations
    """
    if not script.scenes:
        return []

    days = []
    current_day_pages = 0.0
    current_day_scenes: List[int] = []
    current_day_locations: List[str] = []

    for scene in script.scenes:
        scene_pages = scene.page_end - scene.page_start + 1

        # Check if adding this scene would exceed daily target
        if current_day_pages + scene_pages > pages_per_day and current_day_scenes:
            # Save current day
            days.append({
                "day": len(days) + 1,
                "scenes": current_day_scenes,
                "locations": list(set(current_day_locations)),
                "pages": current_day_pages,
            })

            # Start new day
            current_day_pages = 0.0
            current_day_scenes = []
            current_day_locations = []

        current_day_pages += scene_pages
        current_day_scenes.append(scene.number)
        current_day_locations.append(scene.location)

    # Don't forget the last day
    if current_day_scenes:
        days.append({
            "day": len(days) + 1,
            "scenes": current_day_scenes,
            "locations": list(set(current_day_locations)),
            "pages": current_day_pages,
        })

    return days


def compare_characters(script: Script, name1: str, name2: str) -> Dict:
    """Compare two characters' dialogue and presence.

    Args:
        script: Parsed Script object
        name1: First character name
        name2: Second character name

    Returns:
        Dict with comparison statistics
    """
    char1 = script.get_character_by_name(name1)
    char2 = script.get_character_by_name(name2)

    if not char1 or not char2:
        return {"error": "Character not found"}

    return {
        "character_1": {
            "name": char1.name,
            "dialogue_lines": char1.dialogue_count,
            "word_count": char1.dialogue_word_count,
            "scenes": len(char1.scenes_appearing),
            "first_appearance": char1.first_appearance,
            "last_appearance": char1.last_appearance,
        },
        "character_2": {
            "name": char2.name,
            "dialogue_lines": char2.dialogue_count,
            "word_count": char2.dialogue_word_count,
            "scenes": len(char2.scenes_appearing),
            "first_appearance": char2.first_appearance,
            "last_appearance": char2.last_appearance,
        },
        "shared_scenes": list(set(char1.scenes_appearing) & set(char2.scenes_appearing)),
    }


def export_analysis_report(script: Script, analysis: ScriptAnalysis) -> str:
    """Export analysis as formatted text report.

    Args:
        script: Parsed Script object
        analysis: ScriptAnalysis results

    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"SCRIPT ANALYSIS: {script.title or 'Untitled'}")
    lines.append("=" * 60)
    lines.append("")

    # Metadata
    if script.author:
        lines.append(f"Author: {script.author}")
    if script.draft:
        lines.append(f"Draft: {script.draft}")
    lines.append("")

    # Overview
    lines.append("OVERVIEW")
    lines.append("-" * 40)
    lines.append(f"Total Scenes: {analysis.total_scenes}")
    lines.append(f"Total Pages: {analysis.total_pages:.1f}")
    lines.append(f"Estimated Runtime: {analysis.estimated_runtime:.0f} minutes")
    lines.append(f"Characters: {analysis.character_count}")
    lines.append(f"Locations: {analysis.location_count}")
    lines.append("")

    # Content Balance
    lines.append("CONTENT BALANCE")
    lines.append("-" * 40)
    lines.append(f"Dialogue: {analysis.dialogue_percentage:.1f}%")
    lines.append(f"Action: {analysis.action_percentage:.1f}%")
    lines.append(f"Day/Night Ratio: {analysis.day_night_ratio:.2f}")
    lines.append(f"Interior/Exterior Ratio: {analysis.interior_exterior_ratio:.2f}")
    lines.append("")

    # Scene Analysis
    lines.append("SCENE ANALYSIS")
    lines.append("-" * 40)
    lines.append(f"Longest Scene: #{analysis.longest_scene}")
    lines.append(f"Shortest Scene: #{analysis.shortest_scene}")
    lines.append(f"Most Dialogue: {analysis.most_dialogue}")
    lines.append("")

    # Top Characters
    lines.append("TOP CHARACTERS BY DIALOGUE")
    lines.append("-" * 40)
    for char in script.characters[:10]:
        lines.append(
            f"  {char.name}: {char.dialogue_count} lines, "
            f"{char.dialogue_word_count} words, "
            f"{len(char.scenes_appearing)} scenes"
        )
    lines.append("")

    # Top Locations
    lines.append("TOP LOCATIONS BY SCENES")
    lines.append("-" * 40)
    for loc in script.locations[:10]:
        lines.append(
            f"  {loc.name}: {loc.scene_count} scenes "
            f"({'/'.join(loc.time_variants)})"
        )
    lines.append("")

    # Recommendations
    if analysis.recommendations:
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 40)
        for i, rec in enumerate(analysis.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


__all__ = [
    "analyze_script",
    "generate_recommendations",
    "get_character_network",
    "get_location_schedule",
    "get_cast_list",
    "get_daily_breakdown",
    "compare_characters",
    "export_analysis_report",
]
