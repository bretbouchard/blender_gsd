"""
Shot Rules Engine - Apply coverage rules for shot generation.

Implements REQ-SHOT-02, REQ-SHOT-03
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any

from .script_types import Scene, DialogueLine, ActionBlock
from .shot_gen_types import ShotSuggestion
from .scene_analyzer import (
    analyze_scene_content,
    count_characters_in_scene,
    identify_scene_type
)


# Standard coverage rules by scene type
COVERAGE_RULES = {
    "dialogue_two_person": {
        "essential": ["master", "cu_a", "cu_b"],
        "recommended": ["mcu_a", "mcu_b", "two_shot", "ots_a", "ots_b"],
        "optional": ["inserts", "cutaways", "reaction_a", "reaction_b"]
    },
    "dialogue_multi_person": {
        "essential": ["master", "individual_cus"],
        "recommended": ["two_shots", "group_shots"],
        "optional": ["reaction_shots", "inserts", "cutaways"]
    },
    "action": {
        "essential": ["master", "key_beats"],
        "recommended": ["coverage_angles", "inserts"],
        "optional": ["slow_motion", "specialty", "extreme_angles"]
    },
    "transition": {
        "essential": ["establishing"],
        "recommended": [],
        "optional": ["detail_inserts"]
    },
    "montage": {
        "essential": ["establishing", "key_beats"],
        "recommended": ["variation_shots"],
        "optional": ["transition_shots"]
    }
}

# Shot size recommendations by content type
SHOT_SIZE_RULES = {
    "facial_emotion": "cu",
    "dialogue_speaking": "mcu",
    "dialogue_listening": "cu",
    "action_full": "w",
    "action_detail": "ecu",
    "two_characters": "m",
    "group_small": "mf",
    "group_large": "w",
    "location_context": "ew",
    "hand_action": "cu",
    "object_detail": "ecu",
    "movement_full": "f",
    "reaction": "cu",
    "walking": "mf",
    "running": "w",
    "intimate": "cu",
    "confrontation": "m"
}

# Camera angle suggestions by context
CAMERA_ANGLE_RULES = {
    "power_dominant": "low",
    "power_weak": "high",
    "neutral": "eye_level",
    "tension": "dutch",
    "action_dynamic": "low",
    "establishing_overview": "birds_eye",
    "disorientation": "worms_eye",
    "intimate": "eye_level",
    "confrontation": "eye_level"
}


@dataclass
class ShotRule:
    """A single shot rule with conditions and result."""
    name: str
    condition: str  # Description of when to apply
    shot_size: str
    camera_angle: str
    priority: str
    purpose: str


def apply_coverage_rules(scene: Scene) -> List[ShotSuggestion]:
    """Apply coverage rules to generate shot suggestions.

    Args:
        scene: Scene to analyze

    Returns:
        List of shot suggestions based on coverage rules
    """
    suggestions = []
    characters = scene.get_characters_in_scene()
    scene_type = identify_scene_type(scene)
    shot_number = 1

    # Determine which rule set to use
    if scene_type == "dialogue" and len(characters) == 2:
        rule_set = COVERAGE_RULES["dialogue_two_person"]
    elif scene_type == "dialogue" and len(characters) > 2:
        rule_set = COVERAGE_RULES["dialogue_multi_person"]
    elif scene_type == "action":
        rule_set = COVERAGE_RULES["action"]
    else:
        rule_set = COVERAGE_RULES["transition"]

    # Generate essential shots
    for rule_name in rule_set.get("essential", []):
        shot = _create_shot_from_rule(scene, rule_name, characters, shot_number, "essential")
        if shot:
            suggestions.append(shot)
            shot_number += 1

    # Generate recommended shots
    for rule_name in rule_set.get("recommended", []):
        shot = _create_shot_from_rule(scene, rule_name, characters, shot_number, "recommended")
        if shot:
            suggestions.append(shot)
            shot_number += 1

    # Generate optional shots
    for rule_name in rule_set.get("optional", []):
        shot = _create_shot_from_rule(scene, rule_name, characters, shot_number, "optional")
        if shot:
            suggestions.append(shot)
            shot_number += 1

    return suggestions


def _create_shot_from_rule(
    scene: Scene,
    rule_name: str,
    characters: List[str],
    shot_number: int,
    priority: str
) -> Optional[ShotSuggestion]:
    """Create a shot suggestion from a rule name.

    Args:
        scene: The scene
        rule_name: Name of the rule (e.g., "cu_a", "master")
        characters: List of character names
        shot_number: Shot number for this scene
        priority: Shot priority level

    Returns:
        ShotSuggestion or None if rule doesn't apply
    """
    rule_lower = rule_name.lower()

    # Master shot
    if rule_lower == "master":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="w",
            camera_angle="eye_level",
            subject=", ".join(characters) if characters else scene.location,
            purpose="coverage",
            estimated_duration=scene.estimate_duration(),
            priority=priority,
            description="Master shot",
            camera_move="static"
        )

    # Establishing shot
    if rule_lower == "establishing":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="w",
            camera_angle="eye_level",
            subject=scene.location,
            purpose="establishing",
            estimated_duration=4.0,
            priority=priority,
            description=f"Establish {scene.location}",
            camera_move="static"
        )

    # Character close-ups
    if len(characters) >= 1:
        if rule_lower == "cu_a" or rule_lower == "individual_cus":
            return ShotSuggestion(
                scene_number=scene.number,
                shot_number=shot_number,
                shot_size="cu",
                camera_angle="eye_level",
                subject=characters[0],
                purpose="coverage",
                estimated_duration=10.0,
                priority=priority,
                description=f"Close-up on {characters[0]}",
                camera_move="static"
            )

    if len(characters) >= 2 and rule_lower == "cu_b":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="cu",
            camera_angle="eye_level",
            subject=characters[1],
            purpose="coverage",
            estimated_duration=10.0,
            priority=priority,
            description=f"Close-up on {characters[1]}",
            camera_move="static"
        )

    # MCU variations
    if len(characters) >= 1 and rule_lower == "mcu_a":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="mcu",
            camera_angle="eye_level",
            subject=characters[0],
            purpose="coverage",
            estimated_duration=10.0,
            priority=priority,
            description=f"Medium close-up on {characters[0]}",
            camera_move="static"
        )

    if len(characters) >= 2 and rule_lower == "mcu_b":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="mcu",
            camera_angle="eye_level",
            subject=characters[1],
            purpose="coverage",
            estimated_duration=10.0,
            priority=priority,
            description=f"Medium close-up on {characters[1]}",
            camera_move="static"
        )

    # Two-shot
    if rule_lower == "two_shot" and len(characters) >= 2:
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="m",
            camera_angle="eye_level",
            subject=f"{characters[0]} & {characters[1]}",
            purpose="coverage",
            estimated_duration=15.0,
            priority=priority,
            description="Two-shot",
            camera_move="static"
        )

    # Over-the-shoulder shots
    if len(characters) >= 2:
        if rule_lower == "ots_a":
            return ShotSuggestion(
                scene_number=scene.number,
                shot_number=shot_number,
                shot_size="mcu",
                camera_angle="eye_level",
                subject=characters[0],
                purpose="coverage",
                estimated_duration=10.0,
                priority=priority,
                description=f"OTS on {characters[0]} (over {characters[1]})",
                camera_move="static",
                notes="Over-the-shoulder"
            )

        if rule_lower == "ots_b":
            return ShotSuggestion(
                scene_number=scene.number,
                shot_number=shot_number,
                shot_size="mcu",
                camera_angle="eye_level",
                subject=characters[1],
                purpose="coverage",
                estimated_duration=10.0,
                priority=priority,
                description=f"OTS on {characters[1]} (over {characters[0]})",
                camera_move="static",
                notes="Over-the-shoulder"
            )

    # Group shots
    if rule_lower == "group_shots" and len(characters) > 2:
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="mf",
            camera_angle="eye_level",
            subject="Group",
            purpose="coverage",
            estimated_duration=10.0,
            priority=priority,
            description="Group shot",
            camera_move="static"
        )

    # Reaction shots
    if rule_lower.startswith("reaction"):
        for i, char in enumerate(characters[:2]):  # First 2 characters
            if rule_lower == f"reaction_{chr(97 + i)}" or rule_lower == "reaction_shots":
                return ShotSuggestion(
                    scene_number=scene.number,
                    shot_number=shot_number,
                    shot_size="cu",
                    camera_angle="eye_level",
                    subject=char,
                    purpose="reaction",
                    estimated_duration=3.0,
                    priority=priority,
                    description=f"Reaction - {char}",
                    camera_move="static"
                )

    # Inserts
    if rule_lower in ["inserts", "cutaways", "detail_inserts"]:
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="ecu",
            camera_angle="eye_level",
            subject="Detail",
            purpose="insert",
            estimated_duration=2.0,
            priority=priority,
            description="Insert shot",
            camera_move="static"
        )

    # Key beats (for action)
    if rule_lower == "key_beats":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="mcu",
            camera_angle="low",
            subject="Action",
            purpose="coverage",
            estimated_duration=3.0,
            priority=priority,
            description="Key action beat",
            camera_move="handheld"
        )

    # Coverage angles (for action)
    if rule_lower == "coverage_angles":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="m",
            camera_angle="eye_level",
            subject="Action",
            purpose="coverage",
            estimated_duration=5.0,
            priority=priority,
            description="Action coverage angle",
            camera_move="handheld"
        )

    # Slow motion
    if rule_lower == "slow_motion":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="m",
            camera_angle="low",
            subject="Action",
            purpose="coverage",
            estimated_duration=4.0,
            priority=priority,
            description="Slow motion capture",
            camera_move="crane",
            notes="High-speed for slow-mo effect"
        )

    # Specialty
    if rule_lower == "specialty" or rule_lower == "extreme_angles":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="w",
            camera_angle="birds_eye",
            subject="Scene",
            purpose="coverage",
            estimated_duration=3.0,
            priority=priority,
            description="Specialty angle",
            camera_move="crane"
        )

    # Variation shots (for montage)
    if rule_lower == "variation_shots":
        return ShotSuggestion(
            scene_number=scene.number,
            shot_number=shot_number,
            shot_size="m",
            camera_angle="eye_level",
            subject="Scene",
            purpose="coverage",
            estimated_duration=3.0,
            priority=priority,
            description="Variation shot",
            camera_move="static"
        )

    return None


def suggest_shot_size(subject: str, action: str, context: str) -> str:
    """Suggest appropriate shot size based on content.

    Args:
        subject: What/who is being shot
        action: What action is occurring
        context: Scene context (dialogue, action, etc.)

    Returns:
        Suggested shot size code
    """
    subject_lower = subject.lower()
    action_lower = action.lower()
    context_lower = context.lower()

    # Check for specific subject indicators
    if any(k in subject_lower for k in ["face", "eyes", "expression"]):
        return SHOT_SIZE_RULES["facial_emotion"]

    if any(k in subject_lower for k in ["hand", "finger", "detail", "object"]):
        return SHOT_SIZE_RULES["object_detail"]

    if any(k in subject_lower for k in ["group", "crowd", "audience"]):
        return SHOT_SIZE_RULES["group_large"]

    # Check action indicators
    if any(k in action_lower for k in ["run", "chase", "fight", "chase"]):
        return SHOT_SIZE_RULES["running"]

    if any(k in action_lower for k in ["walk", "approach", "enter"]):
        return SHOT_SIZE_RULES["walking"]

    if any(k in action_lower for k in ["speak", "talk", "say", "whisper"]):
        return SHOT_SIZE_RULES["dialogue_speaking"]

    if any(k in action_lower for k in ["listen", "react", "watch"]):
        return SHOT_SIZE_RULES["dialogue_listening"]

    # Check context
    if context_lower == "action":
        return SHOT_SIZE_RULES["action_full"]

    if context_lower == "dialogue":
        return SHOT_SIZE_RULES["dialogue_speaking"]

    if context_lower == "transition":
        return SHOT_SIZE_RULES["location_context"]

    # Default to medium shot
    return "m"


def suggest_camera_angle(context: str, power_dynamic: str = "neutral") -> str:
    """Suggest camera angle based on context.

    Args:
        context: Scene or shot context
        power_dynamic: Power relationship (dominant, weak, neutral)

    Returns:
        Suggested camera angle
    """
    context_lower = context.lower()

    # Check power dynamics first
    if power_dynamic == "dominant":
        return CAMERA_ANGLE_RULES["power_weak"]  # Low angle = dominant
    if power_dynamic == "weak":
        return CAMERA_ANGLE_RULES["power_dominant"]  # High angle = weak

    # Check context keywords
    if any(k in context_lower for k in ["tension", "suspense", "uncomfortable"]):
        return CAMERA_ANGLE_RULES["tension"]

    if any(k in context_lower for k in ["action", "dynamic", "energetic"]):
        return CAMERA_ANGLE_RULES["action_dynamic"]

    if any(k in context_lower for k in ["establishing", "overview", "aerial"]):
        return CAMERA_ANGLE_RULES["establishing_overview"]

    if any(k in context_lower for k in ["intimate", "personal", "emotional"]):
        return CAMERA_ANGLE_RULES["intimate"]

    if any(k in context_lower for k in ["confrontation", "conflict", "argument"]):
        return CAMERA_ANGLE_RULES["confrontation"]

    # Default to neutral
    return CAMERA_ANGLE_RULES["neutral"]


def calculate_shot_priority(shot: ShotSuggestion, scene: Scene) -> str:
    """Calculate shot priority (essential/recommended/optional).

    Args:
        shot: Shot to evaluate
        scene: Scene context

    Returns:
        Priority level string
    """
    characters = scene.get_characters_in_scene()
    scene_type = identify_scene_type(scene)

    # Essential conditions
    if shot.purpose == "establishing":
        return "essential"

    if shot.purpose == "coverage" and shot.shot_size == "w":
        # Master shot is always essential
        return "essential"

    if scene_type == "dialogue":
        # Character coverage is essential for dialogue scenes
        if shot.subject in characters and shot.shot_size in ["cu", "mcu"]:
            return "essential"

    if scene_type == "action":
        # Key action beats are essential
        if "key" in shot.description.lower() or "beat" in shot.description.lower():
            return "essential"

    # Optional conditions
    if shot.purpose in ["insert", "cutaway"]:
        return "optional"

    if "slow motion" in shot.description.lower():
        return "optional"

    if shot.camera_angle in ["birds_eye", "worms_eye", "dutch"]:
        return "optional"

    # Default to recommended
    return "recommended"


def get_coverage_summary(scene: Scene) -> Dict[str, Any]:
    """Get a summary of coverage requirements for a scene.

    Args:
        scene: Scene to analyze

    Returns:
        Dictionary with coverage summary
    """
    characters = scene.get_characters_in_scene()
    scene_type = identify_scene_type(scene)
    shots = apply_coverage_rules(scene)

    summary = {
        "scene_number": scene.number,
        "scene_type": scene_type,
        "character_count": len(characters),
        "total_shots": len(shots),
        "essential_count": sum(1 for s in shots if s.priority == "essential"),
        "recommended_count": sum(1 for s in shots if s.priority == "recommended"),
        "optional_count": sum(1 for s in shots if s.priority == "optional"),
        "shot_sizes": {},
        "purposes": {}
    }

    # Count shot sizes
    for shot in shots:
        size = shot.shot_size
        summary["shot_sizes"][size] = summary["shot_sizes"].get(size, 0) + 1

        purpose = shot.purpose
        summary["purposes"][purpose] = summary["purposes"].get(purpose, 0) + 1

    return summary


# Export all
__all__ = [
    "COVERAGE_RULES",
    "SHOT_SIZE_RULES",
    "CAMERA_ANGLE_RULES",
    "ShotRule",
    "apply_coverage_rules",
    "suggest_shot_size",
    "suggest_camera_angle",
    "calculate_shot_priority",
    "get_coverage_summary",
]
