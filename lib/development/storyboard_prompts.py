"""
Storyboard Prompts - Generate prompts for storyboard and AI image generation.

Implements REQ-SHOT-04
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

from .script_types import Scene, DialogueLine, ActionBlock
from .shot_gen_types import ShotSuggestion, StoryboardPrompt


# Style presets for AI image generation
STYLE_PRESETS = {
    "cinematic": {
        "prefix": "cinematic still from a feature film,",
        "suffix": "dramatic lighting, shallow depth of field, film grain, anamorphic",
        "quality_tags": "4k, high quality, professional cinematography"
    },
    "storyboard": {
        "prefix": "rough storyboard sketch,",
        "suffix": "black and white, loose lines, artistic",
        "quality_tags": "pencil drawing, concept art"
    },
    "realistic": {
        "prefix": "photorealistic image,",
        "suffix": "natural lighting, true to life colors",
        "quality_tags": "8k, ultra detailed, photography"
    },
    "noir": {
        "prefix": "film noir style,",
        "suffix": "high contrast, deep shadows, moody",
        "quality_tags": "black and white photography, dramatic"
    },
    "anime": {
        "prefix": "anime style illustration,",
        "suffix": "vibrant colors, expressive",
        "quality_tags": "high quality animation, detailed"
    },
    "concept_art": {
        "prefix": "professional concept art,",
        "suffix": "digital painting, atmospheric",
        "quality_tags": "artstation quality, detailed rendering"
    },
    "comic": {
        "prefix": "comic book style,",
        "suffix": "bold lines, dynamic",
        "quality_tags": "sequential art, graphic novel"
    }
}

# Composition guidelines for prompts
COMPOSITION_GUIDELINES = {
    "rule_of_thirds": "composed using rule of thirds",
    "centered": "centered composition",
    "golden_ratio": "golden ratio composition",
    "symmetrical": "symmetrical framing",
    "diagonal": "diagonal composition",
    "lead_room": "with lead room for subject movement",
    "headroom": "appropriate headroom"
}

# Lighting presets for prompts
LIGHTING_PRESETS = {
    "natural": "natural daylight",
    "golden_hour": "golden hour warm lighting",
    "blue_hour": "blue hour cool lighting",
    "dramatic": "dramatic side lighting",
    "low_key": "low key lighting with deep shadows",
    "high_key": "high key bright lighting",
    "backlit": "backlit silhouette",
    "practical": "practical lighting from lamps"
}


def generate_storyboard_prompt(
    shot: ShotSuggestion,
    scene: Scene,
    style: str = "cinematic"
) -> StoryboardPrompt:
    """Generate text prompt for storyboard generation.

    Args:
        shot: Shot suggestion to visualize
        scene: Scene context
        style: Style preset to use

    Returns:
        StoryboardPrompt with visual description and AI prompt
    """
    # Get style preset or default to cinematic
    style_config = STYLE_PRESETS.get(style, STYLE_PRESETS["cinematic"])

    # Build visual description
    visual_desc = _build_visual_description(shot, scene)

    # Build AI prompt
    ai_prompt = _build_ai_prompt(shot, scene, style_config)

    # Generate composition notes
    comp_notes = _generate_composition_notes(shot)

    return StoryboardPrompt(
        shot=shot,
        visual_description=visual_desc,
        ai_prompt=ai_prompt,
        style_hints=style_config["suffix"],
        composition_notes=comp_notes
    )


def _build_visual_description(shot: ShotSuggestion, scene: Scene) -> str:
    """Build human-readable visual description.

    Args:
        shot: Shot to describe
        scene: Scene context

    Returns:
        Visual description string
    """
    parts = []

    # Scene heading context
    parts.append(f"Scene {shot.scene_number}: {scene.heading}")

    # Shot type and angle
    shot_size_name = shot.get_shot_size_name()
    angle_name = _get_camera_angle_name(shot.camera_angle)
    parts.append(f"\n{shot_size_name} from {angle_name}")

    # Subject
    parts.append(f"\nSubject: {shot.subject}")

    # Action/context from scene
    if scene.action:
        first_action = scene.action[0].text[:100]
        if len(scene.action[0].text) > 100:
            first_action += "..."
        parts.append(f"\nAction: {first_action}")

    # Camera move
    if shot.camera_move:
        move_name = _get_camera_move_name(shot.camera_move)
        parts.append(f"\nCamera: {move_name}")

    # Notes
    if shot.notes:
        parts.append(f"\nNotes: {shot.notes}")

    return "".join(parts)


def _build_ai_prompt(
    shot: ShotSuggestion,
    scene: Scene,
    style_config: Dict[str, str]
) -> str:
    """Build AI image generation prompt.

    Args:
        shot: Shot to visualize
        scene: Scene context
        style_config: Style configuration

    Returns:
        AI prompt string
    """
    parts = []

    # Style prefix
    parts.append(style_config["prefix"])

    # Shot description
    shot_desc = create_shot_description(shot)
    parts.append(shot_desc.lower())

    # Subject details
    parts.append(f"featuring {shot.subject.lower()}")

    # Scene context
    if scene.interior:
        parts.append("interior setting")
    else:
        parts.append("exterior location")

    # Time of day lighting
    lighting = _get_lighting_from_scene(scene)
    parts.append(lighting)

    # Camera angle perspective
    angle_desc = _get_angle_description(shot.camera_angle)
    parts.append(angle_desc)

    # Shot size framing
    framing = _get_framing_description(shot.shot_size)
    parts.append(framing)

    # Style suffix
    parts.append(style_config["suffix"])

    # Quality tags
    parts.append(style_config["quality_tags"])

    return ", ".join(parts)


def generate_ai_image_prompt(
    shot: ShotSuggestion,
    style: str = "cinematic",
    additional_tags: Optional[List[str]] = None
) -> str:
    """Generate prompt for AI image generation.

    Args:
        shot: Shot to visualize
        style: Style preset name
        additional_tags: Extra tags to include

    Returns:
        AI image generation prompt
    """
    style_config = STYLE_PRESETS.get(style, STYLE_PRESETS["cinematic"])

    parts = []

    # Style prefix
    parts.append(style_config["prefix"])

    # Core description
    desc = create_shot_description(shot)
    parts.append(desc.lower())

    # Subject
    parts.append(f"featuring {shot.subject.lower()}")

    # Shot size framing
    framing = _get_framing_description(shot.shot_size)
    parts.append(framing)

    # Camera angle
    angle_desc = _get_angle_description(shot.camera_angle)
    parts.append(angle_desc)

    # Additional tags
    if additional_tags:
        parts.extend(additional_tags)

    # Style suffix
    parts.append(style_config["suffix"])

    # Quality tags
    parts.append(style_config["quality_tags"])

    return ", ".join(parts)


def create_shot_description(shot: ShotSuggestion) -> str:
    """Create human-readable shot description.

    Args:
        shot: Shot to describe

    Returns:
        Description string
    """
    parts = []

    # Shot label (e.g., "1A")
    label = shot.get_shot_label()
    parts.append(f"Shot {label}")

    # Shot size
    size_name = shot.get_shot_size_name()
    parts.append(f"- {size_name}")

    # Camera angle
    angle_name = _get_camera_angle_name(shot.camera_angle)
    parts.append(f"({angle_name})")

    # Subject
    parts.append(f"\n  Subject: {shot.subject}")

    # Purpose
    purpose_name = _get_purpose_name(shot.purpose)
    parts.append(f"\n  Purpose: {purpose_name}")

    # Duration
    parts.append(f"\n  Duration: {shot.estimated_duration:.1f}s")

    # Camera move
    if shot.camera_move:
        move_name = _get_camera_move_name(shot.camera_move)
        parts.append(f"\n  Camera: {move_name}")

    # Custom description or notes
    if shot.description:
        parts.append(f"\n  Description: {shot.description}")

    if shot.notes:
        parts.append(f"\n  Notes: {shot.notes}")

    return "".join(parts)


def _get_camera_angle_name(angle: str) -> str:
    """Get human-readable camera angle name."""
    angle_names = {
        "eye_level": "Eye Level",
        "high": "High Angle",
        "low": "Low Angle",
        "dutch": "Dutch Angle",
        "birds_eye": "Bird's Eye View",
        "worms_eye": "Worm's Eye View"
    }
    return angle_names.get(angle.lower(), angle.title())


def _get_camera_move_name(move: str) -> str:
    """Get human-readable camera move name."""
    move_names = {
        "static": "Static",
        "pan": "Pan",
        "tilt": "Tilt",
        "dolly": "Dolly",
        "crane": "Crane",
        "handheld": "Handheld",
        "steadicam": "Steadicam",
        "zoom": "Zoom"
    }
    return move_names.get(move.lower(), move.title())


def _get_purpose_name(purpose: str) -> str:
    """Get human-readable purpose name."""
    purpose_names = {
        "coverage": "Coverage",
        "reaction": "Reaction Shot",
        "insert": "Insert/Detail",
        "establishing": "Establishing Shot",
        "transition": "Transition",
        "cutaway": "Cutaway",
        "point_of_view": "Point of View",
        "over_shoulder": "Over the Shoulder"
    }
    return purpose_names.get(purpose.lower(), purpose.title())


def _get_lighting_from_scene(scene: Scene) -> str:
    """Determine lighting description from scene context."""
    time_lower = scene.time_of_day.lower()

    if time_lower in ["night", "evening", "midnight"]:
        return "nighttime low key lighting"
    elif time_lower in ["morning", "dawn"]:
        return "morning golden hour lighting"
    elif time_lower in ["afternoon"]:
        return "afternoon natural lighting"
    elif time_lower in ["dusk", "sunset"]:
        return "sunset warm lighting"
    else:  # day, default
        return "daytime natural lighting"


def _get_angle_description(angle: str) -> str:
    """Get descriptive text for camera angle."""
    angle_descs = {
        "eye_level": "eye level perspective",
        "high": "high angle looking down",
        "low": "low angle looking up",
        "dutch": "tilted dutch angle",
        "birds_eye": "overhead birds eye view",
        "worms_eye": "extreme low angle worms eye view"
    }
    return angle_descs.get(angle.lower(), "neutral perspective")


def _get_framing_description(shot_size: str) -> str:
    """Get descriptive text for shot framing."""
    framing_descs = {
        "ecu": "extreme close-up framing showing fine details",
        "cu": "close-up framing face and shoulders",
        "mcu": "medium close-up framing head and chest",
        "m": "medium shot framing waist up",
        "mf": "medium full shot framing knees up",
        "f": "full shot showing entire figure",
        "w": "wide shot showing environment and subject",
        "ew": "extreme wide establishing shot showing full scene"
    }
    return framing_descs.get(shot_size.lower(), "medium framing")


def _generate_composition_notes(shot: ShotSuggestion) -> str:
    """Generate composition notes for the shot."""
    notes = []

    # Shot size determines framing approach
    if shot.shot_size in ["cu", "ecu", "mcu"]:
        notes.append("Center subject in frame with shallow depth of field")
    elif shot.shot_size == "m":
        notes.append("Rule of thirds placement for balanced composition")
    elif shot.shot_size in ["w", "ew"]:
        notes.append("Establish spatial relationships with wide framing")

    # Camera angle considerations
    if shot.camera_angle == "low":
        notes.append("Low angle conveys power or dominance")
    elif shot.camera_angle == "high":
        notes.append("High angle conveys vulnerability or overview")
    elif shot.camera_angle == "dutch":
        notes.append("Dutch angle creates tension or unease")

    # Movement notes
    if shot.camera_move == "handheld":
        notes.append("Allow for organic camera movement")
    elif shot.camera_move == "static":
        notes.append("Maintain steady locked-off frame")

    return "; ".join(notes) if notes else "Standard composition"


def generate_batch_prompts(
    shots: List[ShotSuggestion],
    scene: Scene,
    style: str = "cinematic"
) -> List[StoryboardPrompt]:
    """Generate prompts for multiple shots.

    Args:
        shots: List of shots to generate prompts for
        scene: Scene context
        style: Style preset

    Returns:
        List of StoryboardPrompts
    """
    return [
        generate_storyboard_prompt(shot, scene, style)
        for shot in shots
    ]


def export_prompts_as_text(prompts: List[StoryboardPrompt]) -> str:
    """Export prompts as plain text for easy use.

    Args:
        prompts: List of prompts to export

    Returns:
        Formatted text string
    """
    lines = []

    for i, prompt in enumerate(prompts, 1):
        shot = prompt.shot
        lines.append(f"{'=' * 60}")
        lines.append(f"SHOT {shot.get_shot_label()}")
        lines.append(f"{'=' * 60}")
        lines.append("")
        lines.append("VISUAL DESCRIPTION:")
        lines.append(prompt.visual_description)
        lines.append("")
        lines.append("AI PROMPT:")
        lines.append(prompt.ai_prompt)
        lines.append("")
        lines.append("COMPOSITION NOTES:")
        lines.append(prompt.composition_notes)
        lines.append("")

    return "\n".join(lines)


# Export all
__all__ = [
    "STYLE_PRESETS",
    "COMPOSITION_GUIDELINES",
    "LIGHTING_PRESETS",
    "generate_storyboard_prompt",
    "generate_ai_image_prompt",
    "create_shot_description",
    "generate_batch_prompts",
    "export_prompts_as_text",
]
