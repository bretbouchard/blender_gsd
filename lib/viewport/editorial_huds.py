"""
Editorial/Timeline HUD Controls

Heads-up display controls for timeline editing, clip management,
and editorial operations.

Part of Bret's AI Stack 2.0 - Viewport Control System
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy import types as bpy_types

from .viewport_widgets import (
    HUDManager,
    HUDWidget,
    HUDSlider,
    HUDToggle,
    HUDDial,
    HUDButton,
    WidgetTheme,
    HUDPanelConfig,
)


# ==================== Editorial Theme ====================

EDITORIAL_THEME = WidgetTheme(
    primary=(0.2, 0.6, 0.9, 0.9),      # Blue - editorial/timeline
    secondary=(0.15, 0.45, 0.7, 0.7),
    text=(1.0, 1.0, 1.0, 1.0),
    background=(0.08, 0.12, 0.18, 0.85),
    highlight=(0.3, 0.7, 1.0, 1.0),
    accent=(0.25, 0.65, 0.95, 1.0),
)

VIDEO_TRACK_THEME = WidgetTheme(
    primary=(0.3, 0.7, 0.4, 0.9),      # Green - video tracks
    secondary=(0.2, 0.5, 0.3, 0.7),
    text=(1.0, 1.0, 1.0, 1.0),
    background=(0.08, 0.12, 0.18, 0.85),
    highlight=(0.4, 0.8, 0.5, 1.0),
    accent=(0.35, 0.75, 0.45, 1.0),
)

AUDIO_TRACK_THEME = WidgetTheme(
    primary=(0.7, 0.5, 0.8, 0.9),      # Purple - audio tracks
    secondary=(0.5, 0.35, 0.6, 0.7),
    text=(1.0, 1.0, 1.0, 1.0),
    background=(0.08, 0.12, 0.18, 0.85),
    highlight=(0.8, 0.6, 0.9, 1.0),
    accent=(0.75, 0.55, 0.85, 1.0),
)


# ==================== Playback HUD ====================

class PlaybackHUD:
    """
    HUD for playback controls.

    Provides:
    - Play/Pause toggle
    - Frame slider
    - Start/End frame controls
    - Playback speed
    - Loop mode
    """

    def __init__(
        self,
        scene_name: str = "",
        panel_name: str = "Playback",
        position: Tuple[int, int] = (20, 100),
    ):
        self.scene_name = scene_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create playback control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="PLAYBACK",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Transport controls row
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_start",
            label="⏮",
            x=x,
            y=y,
            width=40,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._go_to_start,
        ))
        self.widgets.append(f"{self.panel_name}_start")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_prev",
            label="◀",
            x=x + 44,
            y=y,
            width=40,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._prev_frame,
        ))
        self.widgets.append(f"{self.panel_name}_prev")

        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_play",
            label="▶",
            target_object="",
            target_property="",
            x=x + 88,
            y=y,
            width=40,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_toggle=self._toggle_play,
        ))
        self.widgets.append(f"{self.panel_name}_play")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_next",
            label="▶",
            x=x + 132,
            y=y,
            width=40,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._next_frame,
        ))
        self.widgets.append(f"{self.panel_name}_next")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_end",
            label="⏭",
            x=x + 176,
            y=y,
            width=40,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._go_to_end,
        ))
        self.widgets.append(f"{self.panel_name}_end")
        y -= spacing

        # Current frame slider
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_frame",
            label="Frame",
            target_object="Scene",
            target_property="frame_current",
            min_value=1,
            max_value=250,
            default_value=1,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_frame")
        y -= spacing

        # Frame range
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_start_frame",
            label="Start",
            target_object="Scene",
            target_property="frame_start",
            min_value=1,
            max_value=10000,
            default_value=1,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_start_frame")
        y -= spacing

        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_end_frame",
            label="End",
            target_object="Scene",
            target_property="frame_end",
            min_value=1,
            max_value=10000,
            default_value=250,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_end_frame")
        y -= spacing

        # Playback speed
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_speed",
            label="Speed",
            target_object="Screen",
            target_property="animation_playback_speed",
            min_value=0.1,
            max_value=4.0,
            default_value=1.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_speed")
        y -= spacing

        # Loop mode
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_loop",
            label="🔁 Loop",
            target_object="Screen",
            target_property="use_animation_loop",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_loop")

    def _go_to_start(self) -> None:
        """Jump to start frame."""
        try:
            import bpy
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        except:
            pass

    def _go_to_end(self) -> None:
        """Jump to end frame."""
        try:
            import bpy
            bpy.context.scene.frame_set(bpy.context.scene.frame_end)
        except:
            pass

    def _prev_frame(self) -> None:
        """Go to previous frame."""
        try:
            import bpy
            bpy.context.scene.frame_set(bpy.context.scene.frame_current - 1)
        except:
            pass

    def _next_frame(self) -> None:
        """Go to next frame."""
        try:
            import bpy
            bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
        except:
            pass

    def _toggle_play(self) -> None:
        """Toggle playback."""
        try:
            import bpy
            if bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel()
            else:
                bpy.ops.screen.animation_play()
        except:
            pass

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Track Control HUD ====================

class TrackControlHUD:
    """
    HUD for timeline track controls.

    Provides:
    - Track visibility toggles
    - Mute/Solo buttons
    - Lock controls
    - Volume/Opacity (for audio/video)
    """

    def __init__(
        self,
        panel_name: str = "Tracks",
        position: Tuple[int, int] = (20, 400),
    ):
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False
        self._video_tracks: List[str] = []
        self._audio_tracks: List[str] = []

    def _detect_tracks(self) -> None:
        """Detect tracks from VSE or timeline data."""
        try:
            import bpy
            scene = bpy.context.scene

            # Check for VSE
            if scene.sequence_editor:
                # Get unique channel numbers
                channels = set()
                for strip in scene.sequence_editor.sequences_all:
                    channels.add(strip.channel)

                self._video_tracks = []
                self._audio_tracks = []

                for ch in sorted(channels):
                    # Check if channel has video or audio
                    has_video = False
                    has_audio = False
                    for strip in scene.sequence_editor.sequences_all:
                        if strip.channel == ch:
                            if strip.type in {'MOVIE', 'IMAGE'}:
                                has_video = True
                            elif strip.type in {'SOUND'}:
                                has_audio = True

                    if has_video:
                        self._video_tracks.append(f"V{ch}")
                    if has_audio:
                        self._audio_tracks.append(f"A{ch}")
        except:
            # Default tracks if detection fails
            self._video_tracks = ["V1", "V2", "V3"]
            self._audio_tracks = ["A1", "A2"]

    def setup(self) -> None:
        """Create track control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        self._detect_tracks()

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="TRACKS",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Refresh button
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_refresh",
            label="↻ Refresh",
            x=x,
            y=y,
            width=95,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._refresh_tracks,
        ))
        self.widgets.append(f"{self.panel_name}_refresh")

        # All mute toggle
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_all_mute",
            label="🔇 Mute All",
            x=x + 105,
            y=y,
            width=95,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._toggle_all_mute,
        ))
        self.widgets.append(f"{self.panel_name}_all_mute")
        y -= spacing + 10

        # Video tracks
        if self._video_tracks:
            hud.add_widget(HUDToggle(
                name=f"{self.panel_name}_video_label",
                label="VIDEO TRACKS",
                target_object="",
                target_property="",
                x=x,
                y=y,
                width=200,
                height=widget_height - 4,
                theme=VIDEO_TRACK_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_video_label")
            y -= spacing - 4

            for track_name in self._video_tracks[:6]:
                safe_name = track_name.replace(" ", "_")

                # Track mute toggle
                hud.add_widget(HUDToggle(
                    name=f"{self.panel_name}_mute_{safe_name}",
                    label=f"👁 {track_name}",
                    target_object="",
                    target_property="",
                    x=x,
                    y=y,
                    width=130,
                    height=widget_height,
                    theme=VIDEO_TRACK_THEME,
                ))
                self.widgets.append(f"{self.panel_name}_mute_{safe_name}")

                # Solo button
                hud.add_widget(HUDButton(
                    name=f"{self.panel_name}_solo_{safe_name}",
                    label="S",
                    x=x + 134,
                    y=y,
                    width=30,
                    height=widget_height,
                    theme=VIDEO_TRACK_THEME,
                    on_click=lambda t=track_name: self._solo_track(t),
                ))
                self.widgets.append(f"{self.panel_name}_solo_{safe_name}")

                # Lock button
                hud.add_widget(HUDButton(
                    name=f"{self.panel_name}_lock_{safe_name}",
                    label="🔒",
                    x=x + 168,
                    y=y,
                    width=30,
                    height=widget_height,
                    theme=VIDEO_TRACK_THEME,
                    on_click=lambda t=track_name: self._lock_track(t),
                ))
                self.widgets.append(f"{self.panel_name}_lock_{safe_name}")
                y -= spacing
            y -= 10

        # Audio tracks
        if self._audio_tracks:
            hud.add_widget(HUDToggle(
                name=f"{self.panel_name}_audio_label",
                label="AUDIO TRACKS",
                target_object="",
                target_property="",
                x=x,
                y=y,
                width=200,
                height=widget_height - 4,
                theme=AUDIO_TRACK_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_audio_label")
            y -= spacing - 4

            for track_name in self._audio_tracks[:4]:
                safe_name = track_name.replace(" ", "_")

                # Track mute toggle
                hud.add_widget(HUDToggle(
                    name=f"{self.panel_name}_mute_{safe_name}",
                    label=f"🔊 {track_name}",
                    target_object="",
                    target_property="",
                    x=x,
                    y=y,
                    width=130,
                    height=widget_height,
                    theme=AUDIO_TRACK_THEME,
                ))
                self.widgets.append(f"{self.panel_name}_mute_{safe_name}")

                # Volume slider would need separate row
                hud.add_widget(HUDSlider(
                    name=f"{self.panel_name}_vol_{safe_name}",
                    label="Vol",
                    target_object="",
                    target_property="",
                    min_value=0.0,
                    max_value=2.0,
                    default_value=1.0,
                    x=x + 134,
                    y=y,
                    width=64,
                    height=widget_height,
                    theme=AUDIO_TRACK_THEME,
                ))
                self.widgets.append(f"{self.panel_name}_vol_{safe_name}")
                y -= spacing

    def _refresh_tracks(self) -> None:
        """Refresh track list."""
        self.teardown()
        self.setup()

    def _toggle_all_mute(self) -> None:
        """Toggle mute for all tracks."""
        pass  # Implementation would toggle all tracks

    def _solo_track(self, track_name: str) -> None:
        """Solo a track."""
        pass  # Implementation would solo track

    def _lock_track(self, track_name: str) -> None:
        """Lock a track."""
        pass  # Implementation would lock track

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Clip Edit HUD ====================

class ClipEditHUD:
    """
    HUD for clip editing operations.

    Provides:
    - Clip info display
    - Trim controls
    - Slip/slide controls
    - Speed adjustment
    - Opacity/volume
    """

    def __init__(
        self,
        clip_name: str = "",
        panel_name: str = "ClipEdit",
        position: Tuple[int, int] = (20, 600),
    ):
        self.clip_name = clip_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create clip editing widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header with clip name
        display_name = self.clip_name[:16] if self.clip_name else "No Clip"
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label=f"CLIP: {display_name}",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Clip operations
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_split",
            label="✂ Split",
            x=x,
            y=y,
            width=65,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._split_clip,
        ))
        self.widgets.append(f"{self.panel_name}_split")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_delete",
            label="🗑 Delete",
            x=x + 69,
            y=y,
            width=65,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._delete_clip,
        ))
        self.widgets.append(f"{self.panel_name}_delete")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_duplicate",
            label="📋 Dup",
            x=x + 138,
            y=y,
            width=60,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._duplicate_clip,
        ))
        self.widgets.append(f"{self.panel_name}_duplicate")
        y -= spacing + 5

        # Trim controls
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_trim_in",
            label="Trim In",
            target_object="",
            target_property="",
            min_value=0,
            max_value=1000,
            default_value=0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_trim_in")
        y -= spacing

        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_trim_out",
            label="Trim Out",
            target_object="",
            target_property="",
            min_value=0,
            max_value=1000,
            default_value=100,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_trim_out")
        y -= spacing

        # Slip control
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_slip",
            label="Slip",
            target_object="",
            target_property="",
            min_value=-100,
            max_value=100,
            default_value=0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_slip")
        y -= spacing

        # Speed control
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_speed",
            label="Speed %",
            target_object="",
            target_property="",
            min_value=10,
            max_value=400,
            default_value=100,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_speed")
        y -= spacing

        # Opacity
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_opacity",
            label="Opacity",
            target_object="",
            target_property="",
            min_value=0.0,
            max_value=1.0,
            default_value=1.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_opacity")

    def _split_clip(self) -> None:
        """Split clip at current frame."""
        try:
            import bpy
            bpy.ops.sequencer.cut(
                frame=bpy.context.scene.frame_current,
                type='SOFT',
                side='BOTH'
            )
        except:
            pass

    def _delete_clip(self) -> None:
        """Delete selected clip."""
        try:
            import bpy
            bpy.ops.sequencer.delete()
        except:
            pass

    def _duplicate_clip(self) -> None:
        """Duplicate selected clip."""
        try:
            import bpy
            bpy.ops.sequencer.duplicate_move()
        except:
            pass

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Transition HUD ====================

class TransitionHUD:
    """
    HUD for transition controls.

    Provides:
    - Transition type selector
    - Duration control
    - Ease in/out
    - Direction controls (for wipes)
    """

    TRANSITION_TYPES = [
        ("Cut", "✂"),
        ("Dissolve", "◐"),
        ("Wipe", "▶"),
        ("Fade To Black", "◼"),
        ("Fade From Black", "◻"),
        ("Dip To Color", "🎨"),
    ]

    def __init__(
        self,
        panel_name: str = "Transition",
        position: Tuple[int, int] = (20, 350),
    ):
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False
        self._current_type: str = "Dissolve"

    def setup(self) -> None:
        """Create transition control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="TRANSITIONS",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Transition type buttons
        for i, (trans_type, icon) in enumerate(self.TRANSITION_TYPES[:3]):
            hud.add_widget(HUDButton(
                name=f"{self.panel_name}_type_{trans_type.lower().replace(' ', '_')}",
                label=f"{icon} {trans_type[:6]}",
                x=x + (i * 68),
                y=y,
                width=65,
                height=widget_height,
                theme=EDITORIAL_THEME,
                on_click=lambda t=trans_type: self._set_transition_type(t),
            ))
            self.widgets.append(f"{self.panel_name}_type_{trans_type.lower().replace(' ', '_')}")
        y -= spacing

        for i, (trans_type, icon) in enumerate(self.TRANSITION_TYPES[3:6]):
            hud.add_widget(HUDButton(
                name=f"{self.panel_name}_type_{trans_type.lower().replace(' ', '_')}",
                label=f"{icon} {trans_type[:6]}",
                x=x + (i * 68),
                y=y,
                width=65,
                height=widget_height,
                theme=EDITORIAL_THEME,
                on_click=lambda t=trans_type: self._set_transition_type(t),
            ))
            self.widgets.append(f"{self.panel_name}_type_{trans_type.lower().replace(' ', '_')}")
        y -= spacing

        # Duration
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_duration",
            label="Duration (frames)",
            target_object="",
            target_property="",
            min_value=1,
            max_value=120,
            default_value=12,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_duration")
        y -= spacing

        # Ease type
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_ease",
            label="Ease",
            target_object="",
            target_property="",
            min_value=0,
            max_value=100,
            default_value=50,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_ease")
        y -= spacing

        # Wipe direction (conditional)
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_wipe_left",
            label="◀ Left",
            x=x,
            y=y,
            width=50,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=lambda: self._set_wipe_direction("LEFT"),
        ))
        self.widgets.append(f"{self.panel_name}_wipe_left")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_wipe_right",
            label="Right ▶",
            x=x + 54,
            y=y,
            width=50,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=lambda: self._set_wipe_direction("RIGHT"),
        ))
        self.widgets.append(f"{self.panel_name}_wipe_right")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_wipe_up",
            label="▲ Up",
            x=x + 108,
            y=y,
            width=45,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=lambda: self._set_wipe_direction("UP"),
        ))
        self.widgets.append(f"{self.panel_name}_wipe_up")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_wipe_down",
            label="Down ▼",
            x=x + 157,
            y=y,
            width=45,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=lambda: self._set_wipe_direction("DOWN"),
        ))
        self.widgets.append(f"{self.panel_name}_wipe_down")
        y -= spacing

        # Apply button
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_apply",
            label="✓ Apply Transition",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._apply_transition,
        ))
        self.widgets.append(f"{self.panel_name}_apply")

    def _set_transition_type(self, trans_type: str) -> None:
        """Set the transition type."""
        self._current_type = trans_type

    def _set_wipe_direction(self, direction: str) -> None:
        """Set wipe direction."""
        pass  # Would store direction for wipe

    def _apply_transition(self) -> None:
        """Apply transition between selected clips."""
        try:
            import bpy
            # Would add cross, gamma cross, or wipe effect strip
            if self._current_type == "Dissolve":
                bpy.ops.sequencer.crossfade_sounds()  # or add GAMMA_CROSS
            elif self._current_type == "Wipe":
                bpy.ops.sequencer.effect_strip_add(type='WIPE')
        except:
            pass

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Marker HUD ====================

class MarkerHUD:
    """
    HUD for timeline marker controls.

    Provides:
    - Add marker button
    - Marker list
    - Go to marker
    - Delete marker
    """

    def __init__(
        self,
        panel_name: str = "Markers",
        position: Tuple[int, int] = (20, 250),
    ):
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False
        self._markers: List[str] = []

    def _detect_markers(self) -> None:
        """Detect timeline markers."""
        try:
            import bpy
            self._markers = [m.name for m in bpy.context.scene.timeline_markers[:8]]
        except:
            self._markers = []

    def setup(self) -> None:
        """Create marker control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        self._detect_markers()

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="MARKERS",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Add marker
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_add",
            label="+ Add Marker",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._add_marker,
        ))
        self.widgets.append(f"{self.panel_name}_add")
        y -= spacing

        # Marker list
        for marker_name in self._markers[:6]:
            safe_name = marker_name.replace(" ", "_")

            # Go to marker button
            hud.add_widget(HUDButton(
                name=f"{self.panel_name}_goto_{safe_name}",
                label=f"📍 {marker_name[:12]}",
                x=x,
                y=y,
                width=160,
                height=widget_height,
                theme=EDITORIAL_THEME,
                on_click=lambda m=marker_name: self._go_to_marker(m),
            ))
            self.widgets.append(f"{self.panel_name}_goto_{safe_name}")

            # Delete marker button
            hud.add_widget(HUDButton(
                name=f"{self.panel_name}_del_{safe_name}",
                label="✕",
                x=x + 164,
                y=y,
                width=34,
                height=widget_height,
                theme=EDITORIAL_THEME,
                on_click=lambda m=marker_name: self._delete_marker(m),
            ))
            self.widgets.append(f"{self.panel_name}_del_{safe_name}")
            y -= spacing

        # Prev/Next marker buttons
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_prev",
            label="◀ Prev",
            x=x,
            y=y,
            width=95,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._prev_marker,
        ))
        self.widgets.append(f"{self.panel_name}_prev")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_next",
            label="Next ▶",
            x=x + 105,
            y=y,
            width=95,
            height=widget_height,
            theme=EDITORIAL_THEME,
            on_click=self._next_marker,
        ))
        self.widgets.append(f"{self.panel_name}_next")

    def _add_marker(self) -> None:
        """Add marker at current frame."""
        try:
            import bpy
            bpy.ops.marker.add()
        except:
            pass

    def _go_to_marker(self, marker_name: str) -> None:
        """Go to a specific marker."""
        try:
            import bpy
            for marker in bpy.context.scene.timeline_markers:
                if marker.name == marker_name:
                    bpy.context.scene.frame_set(marker.frame)
                    break
        except:
            pass

    def _delete_marker(self, marker_name: str) -> None:
        """Delete a marker."""
        try:
            import bpy
            for marker in bpy.context.scene.timeline_markers:
                if marker.name == marker_name:
                    bpy.context.scene.timeline_markers.remove(marker)
                    break
            self._refresh()
        except:
            pass

    def _prev_marker(self) -> None:
        """Go to previous marker."""
        try:
            import bpy
            bpy.ops.marker.move_to_previous()
        except:
            pass

    def _next_marker(self) -> None:
        """Go to next marker."""
        try:
            import bpy
            bpy.ops.marker.move_to_next()
        except:
            pass

    def _refresh(self) -> None:
        """Refresh the marker list."""
        self.teardown()
        self.setup()

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Editorial Master HUD ====================

class EditorialMasterHUD:
    """
    Master editorial HUD combining all timeline controls.

    Provides unified access to:
    - Playback controls
    - Track controls
    - Clip editing
    - Transitions
    - Markers
    """

    def __init__(
        self,
        scene_name: str = "",
        position: Tuple[int, int] = (20, 900),
    ):
        self.scene_name = scene_name
        self.position = position
        self._sub_huds: Dict[str, Any] = {}
        self._active_hud: Optional[str] = None
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create the master editorial HUD."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name="editorial_master_header",
            label="EDITORIAL",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=EDITORIAL_THEME,
        ))
        self.widgets.append("editorial_master_header")
        y -= spacing

        # Category buttons
        categories = [
            ("playback", "▶ Play"),
            ("tracks", "📊 Tracks"),
            ("clip", "🎬 Clip"),
            ("trans", "⟷ Trans"),
            ("markers", "📍 Marks"),
        ]

        for i, (cat_id, cat_label) in enumerate(categories):
            hud.add_widget(HUDButton(
                name=f"editorial_cat_{cat_id}",
                label=cat_label,
                x=x + (i % 3) * 68,
                y=y - (i // 3) * (widget_height + 5),
                width=65,
                height=widget_height,
                theme=EDITORIAL_THEME,
                on_click=lambda cid=cat_id: self._switch_category(cid),
            ))
            self.widgets.append(f"editorial_cat_{cat_id}")

        y -= ((len(categories) + 2) // 3) * (widget_height + 5) + 10

        # Create sub-HUDs
        self._sub_huds["playback"] = PlaybackHUD(
            scene_name=self.scene_name,
            panel_name="edit_playback",
            position=(x, y),
        )
        self._sub_huds["tracks"] = TrackControlHUD(
            panel_name="edit_tracks",
            position=(x, y),
        )
        self._sub_huds["clip"] = ClipEditHUD(
            clip_name="",
            panel_name="edit_clip",
            position=(x, y),
        )
        self._sub_huds["trans"] = TransitionHUD(
            panel_name="edit_trans",
            position=(x, y),
        )
        self._sub_huds["markers"] = MarkerHUD(
            panel_name="edit_markers",
            position=(x, y),
        )

        # Show playback by default
        self._switch_category("playback")

    def _switch_category(self, category: str) -> None:
        """Switch the active category."""
        # Hide all
        for hud in self._sub_huds.values():
            hud.hide()
            hud.teardown()

        # Show selected
        if category in self._sub_huds:
            self._sub_huds[category].setup()
            self._sub_huds[category].show()
            self._active_hud = category

    def show(self) -> None:
        """Show the editorial HUD."""
        self._visible = True

    def hide(self) -> None:
        """Hide the editorial HUD."""
        self._visible = False
        for hud in self._sub_huds.values():
            hud.hide()

    def teardown(self) -> None:
        """Remove all widgets."""
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()

        for sub_hud in self._sub_huds.values():
            sub_hud.teardown()


# ==================== Convenience Functions ====================

def create_playback_hud(
    scene_name: str = "",
    position: Tuple[int, int] = (20, 100),
) -> PlaybackHUD:
    """Create a playback HUD."""
    hud = PlaybackHUD(scene_name=scene_name, position=position)
    hud.setup()
    return hud


def create_track_control_hud(
    position: Tuple[int, int] = (20, 400),
) -> TrackControlHUD:
    """Create a track control HUD."""
    hud = TrackControlHUD(position=position)
    hud.setup()
    return hud


def create_clip_edit_hud(
    clip_name: str = "",
    position: Tuple[int, int] = (20, 600),
) -> ClipEditHUD:
    """Create a clip editing HUD."""
    hud = ClipEditHUD(clip_name=clip_name, position=position)
    hud.setup()
    return hud


def create_transition_hud(
    position: Tuple[int, int] = (20, 350),
) -> TransitionHUD:
    """Create a transition HUD."""
    hud = TransitionHUD(position=position)
    hud.setup()
    return hud


def create_marker_hud(
    position: Tuple[int, int] = (20, 250),
) -> MarkerHUD:
    """Create a marker HUD."""
    hud = MarkerHUD(position=position)
    hud.setup()
    return hud


def create_editorial_master_hud(
    scene_name: str = "",
    position: Tuple[int, int] = (20, 900),
) -> EditorialMasterHUD:
    """Create a master editorial HUD with all controls."""
    hud = EditorialMasterHUD(scene_name=scene_name, position=position)
    hud.setup()
    return hud
