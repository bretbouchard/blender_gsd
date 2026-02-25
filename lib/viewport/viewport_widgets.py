"""
Viewport Widgets - Re-exported from cinematic module

This module re-exports the viewport widget system from lib.cinematic.viewport_widgets
for convenience and backward compatibility.

Part of Bret's AI Stack 2.0 - Viewport Control System
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Any, List, Dict, Callable, TYPE_CHECKING

# Re-export everything from cinematic.viewport_widgets
from lib.cinematic.viewport_widgets import (
    # Core classes
    HUDManager,
    HUDWidget,
    HUDSlider,
    HUDToggle,
    HUDDial,
    # Configuration
    GizmoConfig,
    HUDControlConfig,
    HUDPanelConfig,
    GizmoType,
    HUDWidgetType,
    # 3D Gizmos
    CameraGizmoGroup,
    # Registration
    register_camera_widgets,
    unregister_camera_widgets,
    # Presets
    CAMERA_GIZMOS,
    CAMERA_HUD_PANEL,
    # Functions
    create_camera_hud,
    setup_camera_hud,
)


@dataclass
class WidgetTheme:
    """
    Theme configuration for HUD widgets.

    This is an extended theme that supports both naming conventions:
    - primary/secondary/text/background (HUD-style)
    - color_normal/color_hover/color_active (cinematic-style)
    """
    # HUD-style naming (primary, secondary, etc.)
    primary: Tuple[float, float, float, float] = (1.0, 0.7, 0.2, 0.8)
    secondary: Tuple[float, float, float, float] = (0.8, 0.5, 0.1, 0.6)
    text: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    background: Tuple[float, float, float, float] = (0.1, 0.1, 0.15, 0.85)
    highlight: Tuple[float, float, float, float] = (1.0, 0.9, 0.5, 1.0)
    accent: Tuple[float, float, float, float] = (1.0, 0.8, 0.3, 1.0)
    corner_radius: float = 8.0
    font_size: int = 12

    @property
    def color_normal(self) -> Tuple[float, float, float, float]:
        """Alias for primary color (cinematic compatibility)."""
        return self.primary

    @property
    def color_hover(self) -> Tuple[float, float, float, float]:
        """Alias for highlight color (cinematic compatibility)."""
        return self.highlight

    @property
    def color_active(self) -> Tuple[float, float, float, float]:
        """Alias for accent color (cinematic compatibility)."""
        return self.accent

    @property
    def color_background(self) -> Tuple[float, float, float, float]:
        """Alias for background color (cinematic compatibility)."""
        return self.background

    @property
    def color_text(self) -> Tuple[float, float, float, float]:
        """Alias for text color (cinematic compatibility)."""
        return self.text

    @property
    def color_border(self) -> Tuple[float, float, float, float]:
        """Alias for secondary color (cinematic compatibility)."""
        return self.secondary


class HUDButton(HUDWidget):
    """
    Button widget for triggering actions.

    Extends HUDWidget with click callback support.
    """

    def __init__(
        self,
        name: str,
        label: str,
        x: int = 0,
        y: int = 0,
        width: int = 100,
        height: int = 32,
        theme: WidgetTheme = None,
        on_click: callable = None,
        **kwargs
    ):
        # Remove on_click from kwargs before passing to parent
        super().__init__(
            name=name,
            label=label,
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=width,
            height=height,
            theme=theme,
            **kwargs
        )
        self.on_click = on_click

    def on_mouse_up(self, x: int, y: int):
        """Handle mouse up - trigger callback if clicked."""
        if self.contains_point(x, y) and self.on_click:
            self.on_click()
        super().on_mouse_up(x, y)

    def draw(self, context):
        """Draw the button."""
        if not self.visible:
            return

        try:
            import gpu
            from gpu_extras.batch import batch_for_shader
            BLENDER_AVAILABLE = True
        except ImportError:
            return

        theme = self.theme or WidgetTheme()

        # Background
        bg_color = theme.highlight if self._hover else theme.background
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", bg_color)

        vertices = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]

        batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
        batch.draw(shader)

        # Label
        try:
            import blf
            font_id = 0
            blf.position(font_id, self.x + 10, self.y + self.height // 3, 0)
            blf.color(font_id, *theme.text)
            blf.size(font_id, theme.font_size)
            blf.draw(font_id, self.label)
        except:
            pass


__all__ = [
    # Core classes
    "HUDManager",
    "HUDWidget",
    "HUDSlider",
    "HUDToggle",
    "HUDDial",
    "HUDButton",
    # Configuration
    "WidgetTheme",
    "GizmoConfig",
    "HUDControlConfig",
    "HUDPanelConfig",
    "GizmoType",
    "HUDWidgetType",
    # 3D Gizmos
    "CameraGizmoGroup",
    # Registration
    "register_camera_widgets",
    "unregister_camera_widgets",
    # Presets
    "CAMERA_GIZMOS",
    "CAMERA_HUD_PANEL",
    # Functions
    "create_camera_hud",
    "setup_camera_hud",
]
