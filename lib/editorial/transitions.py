"""
Transitions for Editorial System

Provides transition creation and Blender VSE integration:
- Cut, dissolve, wipe, fade transitions
- Blender VSE effect creation
- Transition presets

Part of Phase 11.1: Timeline System (REQ-EDIT-03)
Beads: blender_gsd-41
"""

from __future__ import annotations
from typing import Tuple, Optional, Any
import math

from .timeline_types import Transition, TransitionType, Clip, Timecode

# Blender API guard for testing outside Blender
try:
    import bpy
    from bpy import types as bpy_types
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    bpy = None
    bpy_types = None


# ==================== Transition Creation ====================

def create_cut(from_clip: str = "", to_clip: str = "") -> Transition:
    """
    Create a cut transition (instant).

    A cut has no duration - it's an instantaneous switch.

    Args:
        from_clip: Source clip name
        to_clip: Destination clip name

    Returns:
        Cut transition
    """
    return Transition(
        type=TransitionType.CUT,
        duration=0,
        from_clip=from_clip,
        to_clip=to_clip,
    )


def create_dissolve(
    duration: int = 12,
    from_clip: str = "",
    to_clip: str = "",
) -> Transition:
    """
    Create a dissolve/crossfade transition.

    Args:
        duration: Duration in frames
        from_clip: Source clip name
        to_clip: Destination clip name

    Returns:
        Dissolve transition
    """
    return Transition(
        type=TransitionType.DISSOLVE,
        duration=duration,
        from_clip=from_clip,
        to_clip=to_clip,
    )


def create_wipe(
    direction: str = "left",
    duration: int = 12,
    from_clip: str = "",
    to_clip: str = "",
) -> Transition:
    """
    Create a wipe transition.

    Args:
        direction: Wipe direction (left, right, up, down)
        duration: Duration in frames
        from_clip: Source clip name
        to_clip: Destination clip name

    Returns:
        Wipe transition
    """
    return Transition(
        type=TransitionType.WIPE,
        duration=duration,
        from_clip=from_clip,
        to_clip=to_clip,
        wipe_direction=direction,
    )


def create_fade_to_black(
    duration: int = 24,
    from_clip: str = "",
) -> Transition:
    """
    Create a fade to black.

    Args:
        duration: Duration in frames
        from_clip: Source clip name

    Returns:
        Fade to black transition
    """
    return Transition(
        type=TransitionType.FADE_TO_BLACK,
        duration=duration,
        from_clip=from_clip,
        to_clip="",
        dip_color=(0.0, 0.0, 0.0, 1.0),
    )


def create_fade_from_black(
    duration: int = 24,
    to_clip: str = "",
) -> Transition:
    """
    Create a fade from black.

    Args:
        duration: Duration in frames
        to_clip: Destination clip name

    Returns:
        Fade from black transition
    """
    return Transition(
        type=TransitionType.FADE_FROM_BLACK,
        duration=duration,
        from_clip="",
        to_clip=to_clip,
        dip_color=(0.0, 0.0, 0.0, 1.0),
    )


def create_dip_to_color(
    color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    duration: int = 24,
    from_clip: str = "",
    to_clip: str = "",
) -> Transition:
    """
    Create a dip to color transition.

    Args:
        color: RGBA color tuple (0-1 range)
        duration: Duration in frames
        from_clip: Source clip name
        to_clip: Destination clip name

    Returns:
        Dip to color transition
    """
    return Transition(
        type=TransitionType.DIP_TO_COLOR,
        duration=duration,
        from_clip=from_clip,
        to_clip=to_clip,
        dip_color=color,
    )


# ==================== Blender VSE Integration ====================

def apply_transition_blender(
    transition: Transition,
    from_clip: Clip,
    to_clip: Clip,
    sequence_editor: Optional[Any] = None,
) -> bool:
    """
    Apply a transition in Blender Video Sequence Editor.

    Args:
        transition: Transition to apply
        from_clip: Source clip
        to_clip: Destination clip
        sequence_editor: Blender sequence editor (uses context if None)

    Returns:
        True if successful
    """
    if not HAS_BLENDER:
        return False

    if sequence_editor is None:
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        sequence_editor = bpy.context.scene.sequence_editor

    if transition.type == TransitionType.CUT:
        # Cuts don't need any effect
        return True

    # Find the strips for the clips
    from_strip = None
    to_strip = None

    for strip in sequence_editor.sequences_all:
        if strip.name == from_clip.name:
            from_strip = strip
        elif strip.name == to_clip.name:
            to_strip = strip

    if from_strip is None or to_strip is None:
        return False

    if transition.type == TransitionType.DISSOLVE:
        return _apply_dissolve_blender(sequence_editor, from_strip, to_strip, transition.duration)

    elif transition.type == TransitionType.WIPE:
        return _apply_wipe_blender(sequence_editor, from_strip, to_strip, transition.duration, transition.wipe_direction)

    elif transition.type in (TransitionType.FADE_TO_BLACK, TransitionType.FADE_FROM_BLACK):
        return _apply_fade_blender(sequence_editor, from_strip, to_strip, transition)

    elif transition.type == TransitionType.DIP_TO_COLOR:
        return _apply_dip_blender(sequence_editor, from_strip, to_strip, transition)

    return False


def _apply_dissolve_blender(
    seq_editor: Any,
    from_strip: Any,
    to_strip: Any,
    duration: int,
) -> bool:
    """Apply cross dissolve effect in Blender VSE."""
    if not HAS_BLENDER:
        return False

    try:
        # Create cross effect
        effect = seq_editor.sequences.new_effect(
            name=f"{from_strip.name}_x_{to_strip.name}",
            type='CROSS',
            channel=max(from_strip.channel, to_strip.channel) + 1,
            frame_start=to_strip.frame_start,
            frame_end=to_strip.frame_start + duration,
            seq1=from_strip,
            seq2=to_strip,
        )
        return True
    except Exception:
        return False


def _apply_wipe_blender(
    seq_editor: Any,
    from_strip: Any,
    to_strip: Any,
    duration: int,
    direction: str,
) -> bool:
    """Apply wipe effect in Blender VSE."""
    if not HAS_BLENDER:
        return False

    # Map direction to Blender wipe types
    wipe_type_map = {
        "left": "SINGLE",
        "right": "SINGLE",
        "up": "SINGLE",
        "down": "SINGLE",
    }

    try:
        effect = seq_editor.sequences.new_effect(
            name=f"{from_strip.name}_wipe_{to_strip.name}",
            type='WIPE',
            channel=max(from_strip.channel, to_strip.channel) + 1,
            frame_start=to_strip.frame_start,
            frame_end=to_strip.frame_start + duration,
            seq1=from_strip,
            seq2=to_strip,
        )

        # Configure wipe direction
        effect.effect_fader = 0.5  # Default blend

        return True
    except Exception:
        return False


def _apply_fade_blender(
    seq_editor: Any,
    from_strip: Any,
    to_strip: Any,
    transition: Transition,
) -> bool:
    """Apply fade effect in Blender VSE using opacity animation."""
    if not HAS_BLENDER:
        return False

    try:
        if transition.type == TransitionType.FADE_TO_BLACK:
            # Animate from_strip opacity from 1 to 0
            from_strip.blend_alpha = 1.0
            from_strip.keyframe_insert(
                "blend_alpha",
                frame=from_strip.frame_final_end - transition.duration,
            )
            from_strip.blend_alpha = 0.0
            from_strip.keyframe_insert(
                "blend_alpha",
                frame=from_strip.frame_final_end,
            )

        elif transition.type == TransitionType.FADE_FROM_BLACK:
            # Animate to_strip opacity from 0 to 1
            to_strip.blend_alpha = 0.0
            to_strip.keyframe_insert(
                "blend_alpha",
                frame=to_strip.frame_final_start,
            )
            to_strip.blend_alpha = 1.0
            to_strip.keyframe_insert(
                "blend_alpha",
                frame=to_strip.frame_final_start + transition.duration,
            )

        return True
    except Exception:
        return False


def _apply_dip_blender(
    seq_editor: Any,
    from_strip: Any,
    to_strip: Any,
    transition: Transition,
) -> bool:
    """Apply dip to color effect in Blender VSE."""
    if not HAS_BLENDER:
        return False

    try:
        # Create a color strip for the dip
        color_strip = seq_editor.sequences.new_effect(
            name=f"dip_{from_strip.name}",
            type='COLOR',
            channel=max(from_strip.channel, to_strip.channel) + 1,
            frame_start=from_strip.frame_final_end - transition.duration,
            frame_end=to_strip.frame_final_start + transition.duration,
        )

        # Set color
        color_strip.color = list(transition.dip_color[:3])

        return True
    except Exception:
        return False


# ==================== Transition Presets ====================

TRANSITION_PRESETS = {
    "cut": {
        "type": "cut",
        "duration": 0,
    },
    "quick_dissolve": {
        "type": "dissolve",
        "duration": 6,
    },
    "standard_dissolve": {
        "type": "dissolve",
        "duration": 12,
    },
    "slow_dissolve": {
        "type": "dissolve",
        "duration": 24,
    },
    "wipe_left": {
        "type": "wipe",
        "duration": 12,
        "wipe_direction": "left",
    },
    "wipe_right": {
        "type": "wipe",
        "duration": 12,
        "wipe_direction": "right",
    },
    "fade_to_black_quick": {
        "type": "fade_to_black",
        "duration": 12,
    },
    "fade_to_black_standard": {
        "type": "fade_to_black",
        "duration": 24,
    },
    "fade_to_black_slow": {
        "type": "fade_to_black",
        "duration": 48,
    },
}


def create_transition_from_preset(
    preset_name: str,
    from_clip: str = "",
    to_clip: str = "",
) -> Optional[Transition]:
    """
    Create a transition from a preset.

    Args:
        preset_name: Name of preset (cut, quick_dissolve, etc.)
        from_clip: Source clip name
        to_clip: Destination clip name

    Returns:
        Transition or None if preset not found
    """
    preset = TRANSITION_PRESETS.get(preset_name)
    if preset is None:
        return None

    trans_type = TransitionType(preset["type"])

    return Transition(
        type=trans_type,
        duration=preset.get("duration", 0),
        from_clip=from_clip,
        to_clip=to_clip,
        wipe_direction=preset.get("wipe_direction", "left"),
        dip_color=tuple(preset.get("dip_color", [0.0, 0.0, 0.0, 1.0])),
    )


def get_transition_presets() -> dict:
    """Get all available transition presets."""
    return TRANSITION_PRESETS.copy()
