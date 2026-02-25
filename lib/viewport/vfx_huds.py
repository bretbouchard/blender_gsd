"""
VFX/Compositor HUD Controls

Heads-up display controls for compositor, color grading, and VFX operations.

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


# ==================== VFX Theme ====================

VFX_THEME = WidgetTheme(
    primary=(0.9, 0.5, 0.1, 0.9),      # Orange - creative/post
    secondary=(0.7, 0.4, 0.1, 0.7),
    text=(1.0, 1.0, 1.0, 1.0),
    background=(0.15, 0.1, 0.05, 0.85),
    highlight=(1.0, 0.6, 0.2, 1.0),
    accent=(0.95, 0.55, 0.15, 1.0),
)


# ==================== Color Correction HUD ====================

class ColorCorrectionHUD:
    """
    HUD for color correction controls.

    Provides sliders for:
    - Exposure
    - Contrast
    - Saturation
    - Gamma
    - Temperature
    - Tint
    - Highlights/Shadows
    - Lift/Gamma/Gain (per channel)
    """

    def __init__(
        self,
        target_node: str = "",
        panel_name: str = "ColorCorrection",
        position: Tuple[int, int] = (20, 400),
    ):
        """
        Initialize color correction HUD.

        Args:
            target_node: Name of the color correction node
            panel_name: Unique panel identifier
            position: Screen position (x, y)
        """
        self.target_node = target_node
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[HUDWidget] = []
        self._visible = False
        self._expanded_sections: Dict[str, bool] = {
            "basic": True,
            "lgg": False,
            "tonal": False,
        }

    def setup(self) -> None:
        """Create the color correction HUD widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28
        section_gap = 40

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="COLOR CORRECTION",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        y -= spacing

        # === Basic Adjustments ===
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_basic_toggle",
            label="▼ Basic",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
            on_toggle=lambda: self._toggle_section("basic"),
        ))
        y -= spacing

        if self._expanded_sections["basic"]:
            # Exposure
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_exposure",
                label="Exposure",
                target_object=self.target_node,
                target_property="exposure",
                min_value=-3.0,
                max_value=3.0,
                default_value=0.0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_exposure")
            y -= spacing

            # Contrast
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_contrast",
                label="Contrast",
                target_object=self.target_node,
                target_property="contrast",
                min_value=0.0,
                max_value=2.0,
                default_value=1.0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_contrast")
            y -= spacing

            # Saturation
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_saturation",
                label="Saturation",
                target_object=self.target_node,
                target_property="saturation",
                min_value=0.0,
                max_value=2.0,
                default_value=1.0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_saturation")
            y -= spacing

            # Gamma
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_gamma",
                label="Gamma",
                target_object=self.target_node,
                target_property="gamma",
                min_value=0.2,
                max_value=3.0,
                default_value=1.0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_gamma")
            y -= spacing

            # Temperature
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_temperature",
                label="Temperature",
                target_object=self.target_node,
                target_property="temperature",
                min_value=-100,
                max_value=100,
                default_value=0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_temperature")
            y -= spacing

            # Tint
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_tint",
                label="Tint",
                target_object=self.target_node,
                target_property="tint",
                min_value=-100,
                max_value=100,
                default_value=0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_tint")
            y -= section_gap

        # === Lift/Gamma/Gain ===
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_lgg_toggle",
            label="▶ Lift/Gamma/Gain",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
            on_toggle=lambda: self._toggle_section("lgg"),
        ))
        y -= spacing

        if self._expanded_sections["lgg"]:
            # Lift R, G, B
            for channel, color in [("R", (1, 0.3, 0.3)), ("G", (0.3, 1, 0.3)), ("B", (0.3, 0.5, 1))]:
                hud.add_widget(HUDSlider(
                    name=f"{self.panel_name}_lift_{channel.lower()}",
                    label=f"  Lift {channel}",
                    target_object=self.target_node,
                    target_property=f"lift_{channel.lower()}",
                    min_value=-0.5,
                    max_value=0.5,
                    default_value=0.0,
                    x=x,
                    y=y,
                    width=200,
                    height=widget_height,
                    theme=WidgetTheme(
                        primary=(*color, 0.9),
                        secondary=(*color, 0.7),
                        text=(1.0, 1.0, 1.0, 1.0),
                        background=(0.15, 0.1, 0.05, 0.85),
                        highlight=(*color, 1.0),
                        accent=(*color, 1.0),
                    ),
                ))
                self.widgets.append(f"{self.panel_name}_lift_{channel.lower()}")
                y -= spacing

            # Gain R, G, B
            for channel, color in [("R", (1, 0.3, 0.3)), ("G", (0.3, 1, 0.3)), ("B", (0.3, 0.5, 1))]:
                hud.add_widget(HUDSlider(
                    name=f"{self.panel_name}_gain_{channel.lower()}",
                    label=f"  Gain {channel}",
                    target_object=self.target_node,
                    target_property=f"gain_{channel.lower()}",
                    min_value=0.0,
                    max_value=3.0,
                    default_value=1.0,
                    x=x,
                    y=y,
                    width=200,
                    height=widget_height,
                    theme=WidgetTheme(
                        primary=(*color, 0.9),
                        secondary=(*color, 0.7),
                        text=(1.0, 1.0, 1.0, 1.0),
                        background=(0.15, 0.1, 0.05, 0.85),
                        highlight=(*color, 1.0),
                        accent=(*color, 1.0),
                    ),
                ))
                self.widgets.append(f"{self.panel_name}_gain_{channel.lower()}")
                y -= spacing
            y -= section_gap

        # === Tonal Controls ===
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_tonal_toggle",
            label="▶ Highlights/Shadows",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
            on_toggle=lambda: self._toggle_section("tonal"),
        ))
        y -= spacing

        if self._expanded_sections["tonal"]:
            # Highlights
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_highlights",
                label="  Highlights",
                target_object=self.target_node,
                target_property="highlights",
                min_value=-100,
                max_value=100,
                default_value=0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_highlights")
            y -= spacing

            # Shadows
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_shadows",
                label="  Shadows",
                target_object=self.target_node,
                target_property="shadows",
                min_value=-100,
                max_value=100,
                default_value=0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_shadows")
            y -= spacing

            # Whites
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_whites",
                label="  Whites",
                target_object=self.target_node,
                target_property="whites",
                min_value=-100,
                max_value=100,
                default_value=0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_whites")
            y -= spacing

            # Blacks
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_blacks",
                label="  Blacks",
                target_object=self.target_node,
                target_property="blacks",
                min_value=-100,
                max_value=100,
                default_value=0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_blacks")

    def _toggle_section(self, section: str) -> None:
        """Toggle a section's expanded state."""
        self._expanded_sections[section] = not self._expanded_sections[section]
        # Rebuild HUD
        self.teardown()
        self.setup()

    def show(self) -> None:
        """Show the color correction HUD."""
        self._visible = True
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            widget = hud.get_widget(widget_name)
            if widget:
                widget.visible = True

    def hide(self) -> None:
        """Hide the color correction HUD."""
        self._visible = False
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            widget = hud.get_widget(widget_name)
            if widget:
                widget.visible = False

    def teardown(self) -> None:
        """Remove all widgets."""
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Compositor Layer HUD ====================

class CompositorLayerHUD:
    """
    HUD for compositor layer controls.

    Provides:
    - Layer visibility toggles
    - Opacity slider
    - Blend mode selector
    - Solo/Mute controls
    """

    BLEND_MODES = [
        "Normal", "Add", "Subtract", "Multiply", "Screen",
        "Overlay", "Soft Light", "Hard Light", "Difference",
        "Darken", "Lighten", "Color", "Hue", "Saturation", "Luminosity"
    ]

    def __init__(
        self,
        scene_name: str = "",
        panel_name: str = "Compositor",
        position: Tuple[int, int] = (20, 600),
    ):
        """
        Initialize compositor layer HUD.

        Args:
            scene_name: Name of the scene with compositor nodes
            panel_name: Unique panel identifier
            position: Screen position (x, y)
        """
        self.scene_name = scene_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False
        self._layers: List[str] = []

    def _detect_layers(self) -> List[str]:
        """Detect compositor layers from the node tree."""
        try:
            import bpy
            scene = bpy.data.scenes.get(self.scene_name, bpy.context.scene)
            if not scene or not scene.use_nodes:
                return []

            tree = scene.node_tree
            layers = []

            # Find all layer-like nodes (image, render layers, etc.)
            for node in tree.nodes:
                if node.type in {'R_LAYERS', 'IMAGE', 'MOVIE'}:
                    layers.append(node.name)
                elif hasattr(node, 'blend_type'):
                    # MixRGB or similar blend nodes
                    layers.append(node.name)

            return layers
        except:
            return []

    def setup(self) -> None:
        """Create the compositor layer HUD widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        self._layers = self._detect_layers()

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="COMPOSITOR LAYERS",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Global controls
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_refresh",
            label="↻ Refresh",
            x=x,
            y=y,
            width=95,
            height=widget_height,
            theme=VFX_THEME,
            on_click=self._refresh_layers,
        ))
        self.widgets.append(f"{self.panel_name}_refresh")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_all_on",
            label="☀ All On",
            x=x + 105,
            y=y,
            width=95,
            height=widget_height,
            theme=VFX_THEME,
            on_click=self._enable_all_layers,
        ))
        self.widgets.append(f"{self.panel_name}_all_on")
        y -= spacing + 10

        # Layer controls
        for layer_name in self._layers[:10]:  # Limit to 10 layers
            safe_name = layer_name.replace(" ", "_").replace(".", "_")

            # Visibility toggle
            hud.add_widget(HUDToggle(
                name=f"{self.panel_name}_vis_{safe_name}",
                label=f"👁 {layer_name[:16]}",
                target_object=layer_name,
                target_property="mute",
                invert_toggle=True,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_vis_{safe_name}")
            y -= spacing

            # Opacity slider (if applicable)
            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_opacity_{safe_name}",
                label=f"  Opacity",
                target_object=layer_name,
                target_property="inputs[0].default_value",  # Fac input
                min_value=0.0,
                max_value=1.0,
                default_value=1.0,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=VFX_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_opacity_{safe_name}")
            y -= spacing + 5

    def _refresh_layers(self) -> None:
        """Refresh the layer list."""
        self.teardown()
        self.setup()

    def _enable_all_layers(self) -> None:
        """Enable all layers."""
        try:
            import bpy
            scene = bpy.data.scenes.get(self.scene_name, bpy.context.scene)
            if scene and scene.node_tree:
                for node in scene.node_tree.nodes:
                    if hasattr(node, 'mute'):
                        node.mute = False
        except:
            pass

    def show(self) -> None:
        """Show the compositor HUD."""
        self._visible = True

    def hide(self) -> None:
        """Hide the compositor HUD."""
        self._visible = False

    def teardown(self) -> None:
        """Remove all widgets."""
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Glare/Bloom HUD ====================

class GlareHUD:
    """
    HUD for glare/bloom effect controls.

    Provides sliders for:
    - Threshold
    - Intensity
    - Size/Spread
    - Mix factor
    - Streaks (for streaks mode)
    """

    def __init__(
        self,
        node_name: str = "",
        panel_name: str = "Glare",
        position: Tuple[int, int] = (20, 350),
    ):
        self.node_name = node_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create glare control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="GLARE / BLOOM",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Threshold
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_threshold",
            label="Threshold",
            target_object=self.node_name,
            target_property="threshold",
            min_value=0.0,
            max_value=5.0,
            default_value=1.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_threshold")
        y -= spacing

        # Intensity
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_intensity",
            label="Intensity",
            target_object=self.node_name,
            target_property="mix",
            min_value=-10.0,
            max_value=10.0,
            default_value=0.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_intensity")
        y -= spacing

        # Size
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_size",
            label="Size",
            target_object=self.node_name,
            target_property="size",
            min_value=1,
            max_value=9,
            default_value=4,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_size")
        y -= spacing

        # Streaks (if applicable)
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_streaks",
            label="Streaks",
            target_object=self.node_name,
            target_property="streaks",
            min_value=1,
            max_value=16,
            default_value=4,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_streaks")
        y -= spacing

        # Color modulation
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_color_mod",
            label="Color Mod",
            target_object=self.node_name,
            target_property="color_modulation",
            min_value=0.0,
            max_value=1.0,
            default_value=0.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_color_mod")

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Lens Distortion HUD ====================

class LensDistortionHUD:
    """
    HUD for lens distortion effect controls.

    Provides sliders for:
    - Dispersion
    - Distortion
    - Jitter
    """

    def __init__(
        self,
        node_name: str = "",
        panel_name: str = "LensDistort",
        position: Tuple[int, int] = (20, 300),
    ):
        self.node_name = node_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create lens distortion control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="LENS DISTORTION",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Dispersion (chromatic aberration)
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_dispersion",
            label="Dispersion",
            target_object=self.node_name,
            target_property="dispersion",
            min_value=0.0,
            max_value=20.0,
            default_value=0.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_dispersion")
        y -= spacing

        # Distortion
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_distortion",
            label="Distortion",
            target_object=self.node_name,
            target_property="distortion",
            min_value=-1.0,
            max_value=1.0,
            default_value=0.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_distortion")
        y -= spacing

        # Jitter
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_jitter",
            label="Jitter",
            target_object=self.node_name,
            target_property="use_jitter",
            min_value=0.0,
            max_value=1.0,
            default_value=0.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_jitter")
        y -= spacing

        # Projector (fit to render)
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_projector",
            label="Fit to Render",
            target_object=self.node_name,
            target_property="use_projector",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_projector")

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Motion Blur HUD ====================

class MotionBlurHUD:
    """
    HUD for motion blur effect controls.

    Provides sliders for:
    - Shutter speed
    - Blur max
    - Steps
    """

    def __init__(
        self,
        node_name: str = "",
        panel_name: str = "MotionBlur",
        position: Tuple[int, int] = (20, 250),
    ):
        self.node_name = node_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create motion blur control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="MOTION BLUR",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Shutter (angle in degrees, 0-360)
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_shutter",
            label="Shutter (°)",
            target_object=self.node_name,
            target_property="shutter",
            min_value=0,
            max_value=360,
            default_value=180,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_shutter")
        y -= spacing

        # Blur max (samples)
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_blur_max",
            label="Blur Max",
            target_object=self.node_name,
            target_property="blur_max",
            min_value=0.0,
            max_value=64.0,
            default_value=16.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_blur_max")
        y -= spacing

        # Steps (sample count)
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_steps",
            label="Steps",
            target_object=self.node_name,
            target_property="steps",
            min_value=1,
            max_value=16,
            default_value=4,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_steps")

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()


# ==================== Cryptomatte HUD ====================

class CryptomatteHUD:
    """
    HUD for Cryptomatte object/material isolation.

    Provides:
    - Object list picker
    - Selection controls
    - Matte preview toggle
    """

    def __init__(
        self,
        node_name: str = "",
        panel_name: str = "Cryptomatte",
        position: Tuple[int, int] = (20, 200),
    ):
        self.node_name = node_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False
        self._available_objects: List[str] = []

    def setup(self) -> None:
        """Create cryptomatte control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="CRYPTOMATTE",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Add button
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_add_pick",
            label="+ Add from Picker",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
            on_click=self._enable_picker_mode,
        ))
        self.widgets.append(f"{self.panel_name}_add_pick")
        y -= spacing

        # Clear selection
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_clear",
            label="✕ Clear Selection",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
            on_click=self._clear_selection,
        ))
        self.widgets.append(f"{self.panel_name}_clear")
        y -= spacing

        # Edge smoothing
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_edge",
            label="Edge Smooth",
            target_object=self.node_name,
            target_property="edge_radius",
            min_value=0.0,
            max_value=20.0,
            default_value=0.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_edge")
        y -= spacing

        # Matte output toggle
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_matte_output",
            label="Output Matte",
            target_object=self.node_name,
            target_property="matte_output",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_matte_output")

    def _enable_picker_mode(self) -> None:
        """Enable cryptomatte picker mode."""
        try:
            import bpy
            # Would activate cryptomatte picker
            bpy.context.scene.cryptomatte_picker = True
        except:
            pass

    def _clear_selection(self) -> None:
        """Clear all selected objects."""
        try:
            import bpy
            node = bpy.context.scene.node_tree.nodes.get(self.node_name)
            if node:
                # Clear the entries
                node.entries.clear()
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


# ==================== VFX Master HUD ====================

class VFXMasterHUD:
    """
    Master VFX HUD combining all effect controls.

    Provides unified access to:
    - Color correction
    - Compositor layers
    - Glare/Bloom
    - Lens distortion
    - Motion blur
    - Cryptomatte
    """

    def __init__(
        self,
        scene_name: str = "",
        position: Tuple[int, int] = (20, 800),
    ):
        self.scene_name = scene_name
        self.position = position
        self._sub_huds: Dict[str, Any] = {}
        self._active_hud: Optional[str] = None
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create the master VFX HUD."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name="vfx_master_header",
            label="VFX / COMPOSITOR",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=VFX_THEME,
        ))
        self.widgets.append("vfx_master_header")
        y -= spacing

        # Category buttons
        categories = [
            ("color", "🎨 Color"),
            ("layers", "📑 Layers"),
            ("glare", "✨ Glare"),
            ("lens", "🔭 Lens FX"),
            ("blur", "💨 Motion"),
            ("crypto", "🔒 Crypto"),
        ]

        for i, (cat_id, cat_label) in enumerate(categories):
            hud.add_widget(HUDButton(
                name=f"vfx_cat_{cat_id}",
                label=cat_label,
                x=x + (i % 3) * 68,
                y=y - (i // 3) * (widget_height + 5),
                width=65,
                height=widget_height,
                theme=VFX_THEME,
                on_click=lambda cid=cat_id: self._switch_category(cid),
            ))
            self.widgets.append(f"vfx_cat_{cat_id}")

        y -= (len(categories) // 3 + 1) * (widget_height + 5) + 10

        # Create sub-HUDs
        self._sub_huds["color"] = ColorCorrectionHUD(
            target_node="",
            panel_name="vfx_cc",
            position=(x, y),
        )
        self._sub_huds["layers"] = CompositorLayerHUD(
            scene_name=self.scene_name,
            panel_name="vfx_layers",
            position=(x, y),
        )
        self._sub_huds["glare"] = GlareHUD(
            node_name="Glare",
            panel_name="vfx_glare",
            position=(x, y),
        )
        self._sub_huds["lens"] = LensDistortionHUD(
            node_name="LensDistort",
            panel_name="vfx_lens",
            position=(x, y),
        )
        self._sub_huds["blur"] = MotionBlurHUD(
            node_name="VecBlur",
            panel_name="vfx_blur",
            position=(x, y),
        )
        self._sub_huds["crypto"] = CryptomatteHUD(
            node_name="Cryptomatte",
            panel_name="vfx_crypto",
            position=(x, y),
        )

        # Show color by default
        self._switch_category("color")

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
        """Show the VFX HUD."""
        self._visible = True

    def hide(self) -> None:
        """Hide the VFX HUD."""
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

def create_color_correction_hud(
    target_node: str = "",
    position: Tuple[int, int] = (20, 400),
) -> ColorCorrectionHUD:
    """Create a color correction HUD."""
    hud = ColorCorrectionHUD(target_node=target_node, position=position)
    hud.setup()
    return hud


def create_compositor_layer_hud(
    scene_name: str = "",
    position: Tuple[int, int] = (20, 600),
) -> CompositorLayerHUD:
    """Create a compositor layer HUD."""
    hud = CompositorLayerHUD(scene_name=scene_name, position=position)
    hud.setup()
    return hud


def create_vfx_master_hud(
    scene_name: str = "",
    position: Tuple[int, int] = (20, 800),
) -> VFXMasterHUD:
    """Create a master VFX HUD with all controls."""
    hud = VFXMasterHUD(scene_name=scene_name, position=position)
    hud.setup()
    return hud


def create_glare_hud(
    node_name: str = "Glare",
    position: Tuple[int, int] = (20, 350),
) -> GlareHUD:
    """Create a glare/bloom effect HUD."""
    hud = GlareHUD(node_name=node_name, position=position)
    hud.setup()
    return hud


def create_lens_distortion_hud(
    node_name: str = "LensDistort",
    position: Tuple[int, int] = (20, 300),
) -> LensDistortionHUD:
    """Create a lens distortion effect HUD."""
    hud = LensDistortionHUD(node_name=node_name, position=position)
    hud.setup()
    return hud


def create_cryptomatte_hud(
    node_name: str = "Cryptomatte",
    position: Tuple[int, int] = (20, 200),
) -> CryptomatteHUD:
    """Create a cryptomatte HUD."""
    hud = CryptomatteHUD(node_name=node_name, position=position)
    hud.setup()
    return hud
