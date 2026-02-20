"""
Template Expansion

Expand shot templates into full shot configurations.

This module provides functions to expand simplified shot definitions
into complete shot configurations by resolving templates, wardrobe
assignments, location setups, and style presets.

Requirements:
- REQ-CONFIG-04: Shot list integration
- Template expansion and resolution

Part of Phase 14.2: Master Production Config
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from copy import deepcopy

from .config_schema import (
    MasterProductionConfig,
    ShotDef,
    CharacterDef,
    LocationDef,
    OutputDef,
    RetroOutputConfig,
)
from .production_types import (
    ShotConfig,
    CharacterConfig,
    LocationConfig,
    StyleConfig,
    RenderSettings,
)


# Standard shot templates
SHOT_TEMPLATES = {
    # Establishing shots
    "establishing_wide": {
        "description": "Wide establishing shot of location",
        "shot_size": "wide",
        "camera_angle": "eye_level",
        "duration": 120,
        "suggested_for": ["location"],
    },
    "establishing_aerial": {
        "description": "Aerial establishing shot",
        "shot_size": "extreme_wide",
        "camera_angle": "high",
        "duration": 150,
        "suggested_for": ["location"],
    },

    # Character shots
    "character_cu": {
        "description": "Close-up on character",
        "shot_size": "close_up",
        "camera_angle": "eye_level",
        "duration": 90,
        "suggested_for": ["character"],
    },
    "character_mcu": {
        "description": "Medium close-up on character",
        "shot_size": "medium_close_up",
        "camera_angle": "eye_level",
        "duration": 90,
        "suggested_for": ["character"],
    },
    "character_ms": {
        "description": "Medium shot of character",
        "shot_size": "medium",
        "camera_angle": "eye_level",
        "duration": 120,
        "suggested_for": ["character"],
    },
    "character_full": {
        "description": "Full body shot of character",
        "shot_size": "full_shot",
        "camera_angle": "eye_level",
        "duration": 120,
        "suggested_for": ["character"],
    },

    # Two-shots
    "two_shot": {
        "description": "Two-shot with two characters",
        "shot_size": "medium",
        "camera_angle": "eye_level",
        "duration": 150,
        "suggested_for": ["character", "character2"],
    },
    "over_shoulder": {
        "description": "Over-the-shoulder shot",
        "shot_size": "medium_close_up",
        "camera_angle": "eye_level",
        "duration": 120,
        "suggested_for": ["character", "character2"],
    },

    # Dialogue
    "cu_dialogue": {
        "description": "Close-up for dialogue",
        "shot_size": "close_up",
        "camera_angle": "eye_level",
        "duration": 90,
        "suggested_for": ["character"],
    },
    "reverse_dialogue": {
        "description": "Reverse angle for dialogue",
        "shot_size": "close_up",
        "camera_angle": "eye_level",
        "duration": 90,
        "suggested_for": ["character"],
    },

    # Action
    "action_wide": {
        "description": "Wide shot for action",
        "shot_size": "wide",
        "camera_angle": "eye_level",
        "duration": 180,
        "suggested_for": ["character", "location"],
    },
    "action_dynamic": {
        "description": "Dynamic action shot with movement",
        "shot_size": "medium",
        "camera_angle": "low",
        "duration": 120,
        "suggested_for": ["character"],
    },

    # Insert/Detail
    "insert": {
        "description": "Insert shot for detail",
        "shot_size": "extreme_close_up",
        "camera_angle": "eye_level",
        "duration": 60,
        "suggested_for": [],
    },
    "detail": {
        "description": "Detail shot",
        "shot_size": "extreme_close_up",
        "camera_angle": "eye_level",
        "duration": 60,
        "suggested_for": [],
    },

    # POV
    "pov": {
        "description": "Point of view shot",
        "shot_size": "medium",
        "camera_angle": "eye_level",
        "duration": 90,
        "suggested_for": ["character"],
    },

    # Creative
    "dutch_angle": {
        "description": "Dutch angle for tension",
        "shot_size": "medium",
        "camera_angle": "dutch",
        "duration": 90,
        "suggested_for": ["character"],
    },
    "low_angle_hero": {
        "description": "Low angle heroic shot",
        "shot_size": "full_shot",
        "camera_angle": "low",
        "duration": 120,
        "suggested_for": ["character"],
    },
}


# Style presets
STYLE_PRESETS = {
    "cinematic": {
        "mood": "dramatic",
        "color_grade": "neutral",
        "contrast": "medium",
    },
    "cinematic_teal_orange": {
        "mood": "dramatic",
        "color_grade": "teal_orange",
        "contrast": "high",
    },
    "cinematic_warm": {
        "mood": "warm",
        "color_grade": "warm",
        "contrast": "medium",
    },
    "cinematic_cold": {
        "mood": "cold",
        "color_grade": "cold",
        "contrast": "medium",
    },
    "product_hero": {
        "mood": "bright",
        "color_grade": "neutral",
        "contrast": "medium",
    },
    "stylized": {
        "mood": "bright",
        "color_grade": "saturated",
        "contrast": "high",
    },
    "documentary": {
        "mood": "neutral",
        "color_grade": "neutral",
        "contrast": "low",
    },
    "noir": {
        "mood": "dramatic",
        "color_grade": "noir",
        "contrast": "very_high",
    },
}


@dataclass
class CompleteShotConfig:
    """
    Fully expanded shot configuration.

    Contains all resolved references and settings for a single shot.
    """
    # Identity
    name: str
    scene: int
    index: int

    # Template info
    template: str
    description: str = ""
    shot_size: str = "medium"
    camera_angle: str = "eye_level"

    # Characters
    character: Optional[CharacterDef] = None
    character2: Optional[CharacterDef] = None
    costume: str = ""
    costume2: str = ""

    # Location
    location: Optional[LocationDef] = None

    # Timing
    duration: int = 120
    frame_range: Tuple[int, int] = (1, 120)

    # Style
    style: Optional[StyleConfig] = None

    # Output
    notes: str = ""
    variations: int = 0

    def to_shot_def(self) -> ShotDef:
        """Convert back to ShotDef."""
        return ShotDef(
            scene=self.scene,
            template=self.template,
            name=self.name,
            character=self.character.name if self.character else "",
            character2=self.character2.name if self.character2 else "",
            location=self.location.name if self.location else "",
            duration=self.duration,
            frame_range=self.frame_range,
            notes=self.notes,
            variations=self.variations,
        )

    def to_shot_config(self) -> ShotConfig:
        """Convert to ShotConfig for execution."""
        return ShotConfig(
            name=self.name,
            template=self.template,
            scene=self.scene,
            character=self.character.name if self.character else "",
            location=self.location.name if self.location else "",
            duration=self.duration,
            frame_range=self.frame_range,
            notes=self.notes,
            variations=self.variations,
        )


def expand_shot_templates(
    config: MasterProductionConfig,
    resolve_wardrobe: bool = True,
    resolve_locations: bool = True,
    apply_style: bool = True
) -> List[CompleteShotConfig]:
    """
    Expand shot templates into full shot configurations.

    Args:
        config: Master production configuration
        resolve_wardrobe: Whether to resolve costume assignments
        resolve_locations: Whether to resolve location references
        apply_style: Whether to apply style preset

    Returns:
        List of CompleteShotConfig instances
    """
    expanded = []
    frame_counter = 1

    # Get style preset
    style = None
    if apply_style and config.source.style_preset:
        style = _get_style_preset(config.source.style_preset)
    if style is None:
        style = config.style

    for i, shot in enumerate(config.shots):
        # Get template info
        template_info = SHOT_TEMPLATES.get(shot.template, {})

        # Resolve characters
        character = None
        character2 = None
        costume = ""
        costume2 = ""

        if shot.character and shot.character in config.characters:
            character = config.characters[shot.character]
            if resolve_wardrobe:
                costume = character.get_costume_for_scene(shot.scene) or character.wardrobe.get("default", "")

        if shot.character2 and shot.character2 in config.characters:
            character2 = config.characters[shot.character2]
            if resolve_wardrobe:
                costume2 = character2.get_costume_for_scene(shot.scene) or character2.wardrobe.get("default", "")

        # Resolve location
        location = None
        if shot.location and shot.location in config.locations:
            location = config.locations[shot.location]

        # Calculate timing
        duration = shot.duration if shot.duration > 0 else template_info.get("duration", 120)
        if shot.frame_range != (0, 0):
            frame_range = shot.frame_range
        else:
            frame_range = (frame_counter, frame_counter + duration - 1)
        frame_counter = frame_range[1] + 1

        # Create complete config
        complete = CompleteShotConfig(
            name=shot.name or f"shot_{i + 1:03d}",
            scene=shot.scene if shot.scene > 0 else 1,
            index=i,
            template=shot.template,
            description=template_info.get("description", ""),
            shot_size=template_info.get("shot_size", "medium"),
            camera_angle=template_info.get("camera_angle", "eye_level"),
            character=character,
            character2=character2,
            costume=costume,
            costume2=costume2,
            location=location,
            duration=duration,
            frame_range=frame_range,
            style=style,
            notes=shot.notes,
            variations=shot.variations,
        )

        expanded.append(complete)

    return expanded


def resolve_character_wardrobe(
    character_name: str,
    scene: int,
    config: MasterProductionConfig
) -> Optional[str]:
    """
    Resolve costume for character in scene.

    Args:
        character_name: Character name
        scene: Scene number
        config: Master production configuration

    Returns:
        Costume name or None
    """
    if character_name not in config.characters:
        return None

    char = config.characters[character_name]
    return char.get_costume_for_scene(scene)


def resolve_location(
    location_name: str,
    config: MasterProductionConfig
) -> Optional[LocationDef]:
    """
    Resolve location to full configuration.

    Args:
        location_name: Location name
        config: Master production configuration

    Returns:
        LocationDef or None
    """
    return config.locations.get(location_name)


def apply_style_preset(
    style_preset: str,
    shot: CompleteShotConfig
) -> CompleteShotConfig:
    """
    Apply style preset to shot.

    Args:
        style_preset: Style preset name
        shot: Complete shot configuration

    Returns:
        Updated CompleteShotConfig with style applied
    """
    style = _get_style_preset(style_preset)
    if style:
        shot = deepcopy(shot)
        shot.style = style
    return shot


def _get_style_preset(name: str) -> Optional[StyleConfig]:
    """Get style preset by name."""
    preset = STYLE_PRESETS.get(name)
    if preset:
        return StyleConfig(
            preset=name,
            mood=preset.get("mood", "dramatic"),
            color_grade=preset.get("color_grade", "neutral"),
            contrast=preset.get("contrast", "medium"),
        )
    return None


def get_shot_template(name: str) -> Optional[Dict[str, Any]]:
    """
    Get shot template by name.

    Args:
        name: Template name

    Returns:
        Template dictionary or None
    """
    return SHOT_TEMPLATES.get(name)


def list_shot_templates() -> List[str]:
    """
    List all available shot templates.

    Returns:
        List of template names
    """
    return list(SHOT_TEMPLATES.keys())


def list_style_presets() -> List[str]:
    """
    List all available style presets.

    Returns:
        List of preset names
    """
    return list(STYLE_PRESETS.keys())


def suggest_shot_for_context(
    has_character: bool = False,
    has_two_characters: bool = False,
    has_location: bool = False,
    is_action: bool = False
) -> List[str]:
    """
    Suggest shot templates based on context.

    Args:
        has_character: Shot involves a character
        has_two_characters: Shot involves two characters
        has_location: Shot involves a location
        is_action: Shot is action-oriented

    Returns:
        List of suggested template names
    """
    suggestions = []

    if has_two_characters:
        suggestions.extend(["two_shot", "over_shoulder", "cu_dialogue", "reverse_dialogue"])
    elif has_character:
        if is_action:
            suggestions.extend(["action_wide", "action_dynamic", "character_full"])
        else:
            suggestions.extend(["character_cu", "character_mcu", "character_ms", "cu_dialogue"])

    if has_location and not has_character:
        suggestions.extend(["establishing_wide", "establishing_aerial"])

    if not suggestions:
        suggestions.extend(["establishing_wide", "character_ms"])

    return suggestions


def generate_shot_list_from_script(
    config: MasterProductionConfig,
    script_path: Optional[str] = None
) -> List[ShotDef]:
    """
    Generate shot list from script file.

    This is a placeholder for future script parsing integration.
    Currently returns empty list.

    Args:
        config: Master production configuration
        script_path: Optional override script path

    Returns:
        List of ShotDef instances
    """
    # This would integrate with lib.script module
    # For now, return empty list
    return []


def expand_output_formats(
    config: MasterProductionConfig
) -> Dict[str, Dict[str, Any]]:
    """
    Expand output formats with full configuration.

    Args:
        config: Master production configuration

    Returns:
        Dictionary of output name to full configuration
    """
    from .production_types import get_output_format_preset

    expanded = {}

    for output in config.outputs:
        output_config = {
            "name": output.name,
            "format": output.format,
            "resolution": output.resolution,
            "frame_rate": output.frame_rate,
            "codec": output.codec,
            "path": output.path,
            "retro": None,
        }

        # Try to get preset defaults
        preset = get_output_format_preset(output.format)
        if preset:
            if not output.resolution or output.resolution == (1920, 1080):
                output_config["resolution"] = preset.resolution
            if not output.frame_rate:
                output_config["frame_rate"] = preset.frame_rate
            if not output.codec:
                output_config["codec"] = preset.codec

        # Add retro configuration
        if output.retro and output.retro.enabled:
            output_config["retro"] = {
                "enabled": True,
                "palette": output.retro.palette,
                "dither": output.retro.dither,
                "pixel_size": output.retro.pixel_size,
                "target_resolution": output.retro.target_resolution,
                "crt_effects": output.retro.crt_effects,
            }

        expanded[output.name] = output_config

    return expanded


def get_production_summary(config: MasterProductionConfig) -> Dict[str, Any]:
    """
    Get summary of production configuration.

    Args:
        config: Master production configuration

    Returns:
        Dictionary with production summary
    """
    expanded_shots = expand_shot_templates(config)

    # Calculate total duration
    total_frames = sum(shot.duration for shot in expanded_shots)
    frame_rate = config.outputs[0].frame_rate if config.outputs else 24
    total_seconds = total_frames / frame_rate if frame_rate > 0 else 0

    # Count retro outputs
    retro_outputs = config.get_retro_outputs()
    cinematic_outputs = config.get_cinematic_outputs()

    return {
        "title": config.meta.title,
        "author": config.meta.author,
        "version": config.meta.version,
        "character_count": len(config.characters),
        "location_count": len(config.locations),
        "shot_count": len(config.shots),
        "total_shot_count": config.get_shot_count(),  # Including variations
        "scene_count": len(config.get_scenes()),
        "scenes": config.get_scenes(),
        "total_frames": total_frames,
        "total_seconds": total_seconds,
        "total_minutes": total_seconds / 60,
        "output_count": len(config.outputs),
        "retro_outputs": len(retro_outputs),
        "cinematic_outputs": len(cinematic_outputs),
        "style_preset": config.source.style_preset,
        "render_engine": config.render.engine,
        "render_samples": config.render.samples,
    }
