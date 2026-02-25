"""
Tool HUD Widgets - Pre-built HUD configurations for all existing tools

Provides ready-to-use HUD panels for:
- Camera controls
- Light controls (intensity, color, temperature)
- HDRI environment controls
- Material controls
- Render settings
- Animation controls

Usage:
    from lib.viewport.tool_huds import (
        CameraHUD,
        LightHUD,
        HDRIHUD,
        MaterialHUD,
        setup_active_tool_hud,
    )

    # Setup HUD for selected object
    setup_active_tool_hud()

    # Or create specific HUD
    light_hud = LightHUD("KeyLight")
    light_hud.show()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, List, Tuple, Dict, TYPE_CHECKING
import math

# Import base widgets
from .viewport_widgets import (
    HUDManager,
    HUDSlider,
    HUDToggle,
    HUDDial,
    HUDWidget,
    WidgetTheme,
    HUDControlConfig,
)

# Blender guards
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

if TYPE_CHECKING:
    from bpy.types import Context, Object


# =============================================================================
# THEMES
# =============================================================================

CAMERA_THEME = WidgetTheme(
    primary=(1.0, 0.7, 0.2, 0.9),
    highlight=(1.0, 0.9, 0.5, 1.0),
    background=(0.15, 0.12, 0.08, 0.9),
)

LIGHT_THEME = WidgetTheme(
    primary=(1.0, 0.95, 0.6, 0.9),
    highlight=(1.0, 1.0, 0.8, 1.0),
    background=(0.12, 0.12, 0.08, 0.9),
)

HDRI_THEME = WidgetTheme(
    primary=(0.4, 0.7, 1.0, 0.9),
    highlight=(0.6, 0.85, 1.0, 1.0),
    background=(0.08, 0.1, 0.15, 0.9),
)

MATERIAL_THEME = WidgetTheme(
    primary=(0.8, 0.4, 0.9, 0.9),
    highlight=(1.0, 0.6, 1.0, 1.0),
    background=(0.12, 0.08, 0.15, 0.9),
)

RENDER_THEME = WidgetTheme(
    primary=(0.3, 0.9, 0.5, 0.9),
    highlight=(0.5, 1.0, 0.7, 1.0),
    background=(0.08, 0.12, 0.1, 0.9),
)


# =============================================================================
# CAMERA HUD
# =============================================================================

class CameraHUD:
    """HUD panel for camera controls."""

    def __init__(self, camera_name: str, x: int = 20, y: int = 200):
        self.camera_name = camera_name
        self.x = x
        self.y = y
        self.panel_name = f"camera_{camera_name}"
        self._widgets: List[HUDWidget] = []
        self._visible = True

    def setup(self) -> None:
        """Create and add widgets to HUD manager."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        current_y = self.y

        # Focal Length
        focal = HUDSlider(
            name=f"{self.camera_name}_focal",
            label="Focal Length",
            target_object=self.camera_name,
            target_property="data.lens",
            min_value=10.0,
            max_value=400.0,
            format_string="{:.0f}mm",
            x=self.x,
            y=current_y,
            theme=CAMERA_THEME,
        )
        hud.add_widget(focal, self.panel_name)
        self._widgets.append(focal)
        current_y -= 45

        # Aperture
        aperture = HUDSlider(
            name=f"{self.camera_name}_aperture",
            label="Aperture",
            target_object=self.camera_name,
            target_property="data.dof.aperture_fstop",
            min_value=1.0,
            max_value=22.0,
            format_string="f/{:.1f}",
            x=self.x,
            y=current_y,
            theme=CAMERA_THEME,
        )
        hud.add_widget(aperture, self.panel_name)
        self._widgets.append(aperture)
        current_y -= 45

        # Focus Distance
        focus = HUDSlider(
            name=f"{self.camera_name}_focus",
            label="Focus Distance",
            target_object=self.camera_name,
            target_property="data.dof.focus_distance",
            min_value=0.1,
            max_value=100.0,
            format_string="{:.2f}m",
            x=self.x,
            y=current_y,
            theme=CAMERA_THEME,
        )
        hud.add_widget(focus, self.panel_name)
        self._widgets.append(focus)
        current_y -= 45

        # DOF Toggle
        dof = HUDToggle(
            name=f"{self.camera_name}_dof",
            label="DOF",
            target_object=self.camera_name,
            target_property="data.dof.use_dof",
            x=self.x,
            y=current_y,
            theme=CAMERA_THEME,
        )
        hud.add_widget(dof, self.panel_name)
        self._widgets.append(dof)

    def show(self) -> None:
        """Show the HUD panel."""
        self._visible = True
        for w in self._widgets:
            w.visible = True

    def hide(self) -> None:
        """Hide the HUD panel."""
        self._visible = False
        for w in self._widgets:
            w.visible = False

    def remove(self) -> None:
        """Remove from HUD manager."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)
        self._widgets.clear()


# =============================================================================
# LIGHT HUD
# =============================================================================

class LightHUD:
    """HUD panel for light controls."""

    def __init__(self, light_name: str, x: int = 20, y: int = 200):
        self.light_name = light_name
        self.x = x
        self.y = y
        self.panel_name = f"light_{light_name}"
        self._widgets: List[HUDWidget] = []
        self._light_type: str = ""

    def setup(self) -> None:
        """Create and add widgets to HUD manager."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        # Detect light type
        self._detect_light_type()

        current_y = self.y

        # Intensity (all lights)
        intensity = HUDSlider(
            name=f"{self.light_name}_intensity",
            label="Intensity",
            target_object=self.light_name,
            target_property="data.energy",
            min_value=0.0,
            max_value=10000.0,
            format_string="{:.0f}W",
            x=self.x,
            y=current_y,
            theme=LIGHT_THEME,
        )
        hud.add_widget(intensity, self.panel_name)
        self._widgets.append(intensity)
        current_y -= 45

        # Color Temperature (if supported)
        temp = HUDSlider(
            name=f"{self.light_name}_temp",
            label="Temperature",
            target_object=self.light_name,
            target_property="data.temperature",
            min_value=1000.0,
            max_value=20000.0,
            format_string="{:.0f}K",
            x=self.x,
            y=current_y,
            theme=LIGHT_THEME,
        )
        hud.add_widget(temp, self.panel_name)
        self._widgets.append(temp)
        current_y -= 45

        # Use Temperature Toggle
        use_temp = HUDToggle(
            name=f"{self.light_name}_usetemp",
            label="Use Temp",
            target_object=self.light_name,
            target_property="data.use_temperature",
            x=self.x,
            y=current_y,
            theme=LIGHT_THEME,
        )
        hud.add_widget(use_temp, self.panel_name)
        self._widgets.append(use_temp)
        current_y -= 40

        # Shadow Toggle
        shadow = HUDToggle(
            name=f"{self.light_name}_shadow",
            label="Shadow",
            target_object=self.light_name,
            target_property="data.use_shadow",
            x=self.x,
            y=current_y,
            theme=LIGHT_THEME,
        )
        hud.add_widget(shadow, self.panel_name)
        self._widgets.append(shadow)
        current_y -= 40

        # Area/Spot specific controls
        if self._light_type in ("AREA", "SPOT"):
            size = HUDSlider(
                name=f"{self.light_name}_size",
                label="Size",
                target_object=self.light_name,
                target_property="data.size",
                min_value=0.01,
                max_value=10.0,
                format_string="{:.2f}m",
                x=self.x,
                y=current_y,
                theme=LIGHT_THEME,
            )
            hud.add_widget(size, self.panel_name)
            self._widgets.append(size)
            current_y -= 45

        # Spot specific
        if self._light_type == "SPOT":
            spot_size = HUDSlider(
                name=f"{self.light_name}_spotsize",
                label="Cone Angle",
                target_object=self.light_name,
                target_property="data.spot_size",
                min_value=0.0,
                max_value=3.14159,
                format_string="{:.0f}°",
                x=self.x,
                y=current_y,
                theme=LIGHT_THEME,
            )
            hud.add_widget(spot_size, self.panel_name)
            self._widgets.append(spot_size)

    def _detect_light_type(self) -> None:
        """Detect the type of light."""
        if not BLENDER_AVAILABLE:
            return

        obj = bpy.data.objects.get(self.light_name)
        if obj and obj.type == "LIGHT" and obj.data:
            self._light_type = obj.data.type

    def show(self) -> None:
        for w in self._widgets:
            w.visible = True

    def hide(self) -> None:
        for w in self._widgets:
            w.visible = False

    def remove(self) -> None:
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)
        self._widgets.clear()


class MultiLightHUD:
    """HUD for controlling multiple lights at once."""

    def __init__(self, light_names: List[str], x: int = 20, y: int = 200):
        self.light_names = light_names
        self.x = x
        self.y = y
        self._light_huds: Dict[str, LightHUD] = {}

    def setup(self) -> None:
        """Create HUDs for all lights in a vertical stack."""
        current_y = self.y
        for name in self.light_names:
            hud = LightHUD(name, x=self.x, y=current_y)
            hud.setup()
            self._light_huds[name] = hud
            current_y -= 250  # Spacing between lights

    def show(self) -> None:
        for hud in self._light_huds.values():
            hud.show()

    def hide(self) -> None:
        for hud in self._light_huds.values():
            hud.hide()

    def remove(self) -> None:
        for hud in self._light_huds.values():
            hud.remove()
        self._light_huds.clear()


# =============================================================================
# HDRI HUD
# =============================================================================

class HDRIHUD:
    """HUD for HDRI environment controls."""

    def __init__(self, x: int = 20, y: int = 100):
        self.x = x
        self.y = y
        self.panel_name = "hdri_controls"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create HDRI control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        current_y = self.y

        # HDRI Rotation (requires world node access)
        rotation = HUDSlider(
            name="hdri_rotation",
            label="Rotation",
            target_object="World",  # Special handling needed
            target_property="node_tree.nodes['Mapping'].inputs['Rotation'].default_value[2]",
            min_value=0.0,
            max_value=6.28318,
            format_string="{:.0f}°",
            x=self.x,
            y=current_y,
            theme=HDRI_THEME,
        )
        hud.add_widget(rotation, self.panel_name)
        self._widgets.append(rotation)
        current_y -= 45

        # Exposure
        exposure = HUDSlider(
            name="hdri_exposure",
            label="Exposure",
            target_object="World",
            target_property="node_tree.nodes['Background'].inputs['Strength'].default_value",
            min_value=0.0,
            max_value=10.0,
            format_string="{:.1f}",
            x=self.x,
            y=current_y,
            theme=HDRI_THEME,
        )
        hud.add_widget(exposure, self.panel_name)
        self._widgets.append(exposure)

    def show(self) -> None:
        for w in self._widgets:
            w.visible = True

    def hide(self) -> None:
        for w in self._widgets:
            w.visible = False

    def remove(self) -> None:
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)
        self._widgets.clear()


# =============================================================================
# MATERIAL HUD
# =============================================================================

class MaterialHUD:
    """HUD for material property controls."""

    def __init__(self, object_name: str, x: int = 20, y: int = 200):
        self.object_name = object_name
        self.x = x
        self.y = y
        self.panel_name = f"material_{object_name}"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create material control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        # Path to active material's principled BSDF
        # This is a simplified approach - real implementation would need node traversal
        base_path = f"active_material.node_tree.nodes['Principled BSDF'].inputs"

        current_y = self.y

        # Roughness
        roughness = HUDSlider(
            name=f"{self.object_name}_roughness",
            label="Roughness",
            target_object=self.object_name,
            target_property=f"{base_path}['Roughness'].default_value",
            min_value=0.0,
            max_value=1.0,
            format_string="{:.2f}",
            x=self.x,
            y=current_y,
            theme=MATERIAL_THEME,
        )
        hud.add_widget(roughness, self.panel_name)
        self._widgets.append(roughness)
        current_y -= 45

        # Metallic
        metallic = HUDSlider(
            name=f"{self.object_name}_metallic",
            label="Metallic",
            target_object=self.object_name,
            target_property=f"{base_path}['Metallic'].default_value",
            min_value=0.0,
            max_value=1.0,
            format_string="{:.2f}",
            x=self.x,
            y=current_y,
            theme=MATERIAL_THEME,
        )
        hud.add_widget(metallic, self.panel_name)
        self._widgets.append(metallic)
        current_y -= 45

        # IOR
        ior = HUDSlider(
            name=f"{self.object_name}_ior",
            label="IOR",
            target_object=self.object_name,
            target_property=f"{base_path}['IOR'].default_value",
            min_value=1.0,
            max_value=3.0,
            format_string="{:.2f}",
            x=self.x,
            y=current_y,
            theme=MATERIAL_THEME,
        )
        hud.add_widget(ior, self.panel_name)
        self._widgets.append(ior)

    def show(self) -> None:
        for w in self._widgets:
            w.visible = True

    def hide(self) -> None:
        for w in self._widgets:
            w.visible = False

    def remove(self) -> None:
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)
        self._widgets.clear()


# =============================================================================
# RENDER HUD
# =============================================================================

class RenderHUD:
    """HUD for render settings controls."""

    def __init__(self, x: int = 20, y: int = 50):
        self.x = x
        self.y = y
        self.panel_name = "render_controls"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create render control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        current_y = self.y

        # Samples
        samples = HUDSlider(
            name="render_samples",
            label="Samples",
            target_object="Scene",  # Special handling
            target_property="cycles.samples",
            min_value=1,
            max_value=4096,
            format_string="{:.0f}",
            x=self.x,
            y=current_y,
            theme=RENDER_THEME,
        )
        hud.add_widget(samples, self.panel_name)
        self._widgets.append(samples)
        current_y -= 45

        # Denoise Toggle
        denoise = HUDToggle(
            name="render_denoise",
            label="Denoise",
            target_object="Scene",
            target_property="cycles.use_denoising",
            x=self.x,
            y=current_y,
            theme=RENDER_THEME,
        )
        hud.add_widget(denoise, self.panel_name)
        self._widgets.append(denoise)

    def show(self) -> None:
        for w in self._widgets:
            w.visible = True

    def hide(self) -> None:
        for w in self._widgets:
            w.visible = False

    def remove(self) -> None:
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)
        self._widgets.clear()


# =============================================================================
# AUTO-HUD MANAGER
# =============================================================================

class AutoHUDManager:
    """
    Automatically shows appropriate HUD based on selection.

    Monitors selection changes and shows relevant controls:
    - Camera selected → Camera HUD
    - Light selected → Light HUD
    - Mesh with material → Material HUD
    """

    def __init__(self):
        self._current_hud: Optional[Any] = None
        self._current_object: Optional[str] = None
        self._enabled = True

    def update_for_selection(self, context: "Context") -> None:
        """Update HUD based on current selection."""
        if not self._enabled or not BLENDER_AVAILABLE:
            return

        obj = context.active_object
        if obj is None:
            self._clear_current()
            return

        # Skip if same object
        if obj.name == self._current_object:
            return

        # Clear previous HUD
        self._clear_current()

        self._current_object = obj.name

        # Create appropriate HUD
        if obj.type == "CAMERA":
            self._current_hud = CameraHUD(obj.name)
            self._current_hud.setup()
            self._current_hud.show()

        elif obj.type == "LIGHT":
            self._current_hud = LightHUD(obj.name)
            self._current_hud.setup()
            self._current_hud.show()

        elif obj.type == "MESH" and obj.active_material:
            self._current_hud = MaterialHUD(obj.name)
            self._current_hud.setup()
            self._current_hud.show()

    def _clear_current(self) -> None:
        """Clear current HUD."""
        if self._current_hud:
            self._current_hud.remove()
            self._current_hud = None
        self._current_object = None

    def enable(self) -> None:
        """Enable auto-HUD."""
        self._enabled = True

    def disable(self) -> None:
        """Disable auto-HUD."""
        self._enabled = False
        self._clear_current()

    @property
    def enabled(self) -> bool:
        return self._enabled


# Singleton instance
_auto_hud: Optional[AutoHUDManager] = None


def get_auto_hud() -> AutoHUDManager:
    """Get the auto-HUD manager singleton."""
    global _auto_hud
    if _auto_hud is None:
        _auto_hud = AutoHUDManager()
    return _auto_hud


def setup_active_tool_hud(context: "Context" = None) -> None:
    """
    Setup HUD for the currently active object.

    Convenience function to call from operators or handlers.
    """
    if not BLENDER_AVAILABLE:
        return

    if context is None:
        context = bpy.context

    auto_hud = get_auto_hud()
    auto_hud.update_for_selection(context)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_lighting_rig_hud(lights: List[str]) -> MultiLightHUD:
    """
    Create HUD for a complete lighting rig.

    Args:
        lights: List of light names to control

    Returns:
        MultiLightHUD instance
    """
    hud = MultiLightHUD(lights)
    hud.setup()
    return hud


def create_camera_hud(camera_name: str) -> CameraHUD:
    """Create HUD for camera controls."""
    hud = CameraHUD(camera_name)
    hud.setup()
    return hud


def create_light_hud(light_name: str) -> LightHUD:
    """Create HUD for light controls."""
    hud = LightHUD(light_name)
    hud.setup()
    return hud


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # HUD classes
    "CameraHUD",
    "LightHUD",
    "MultiLightHUD",
    "HDRIHUD",
    "MaterialHUD",
    "RenderHUD",
    # Auto-HUD
    "AutoHUDManager",
    "get_auto_hud",
    "setup_active_tool_hud",
    # Convenience
    "create_lighting_rig_hud",
    "create_camera_hud",
    "create_light_hud",
    # Themes
    "CAMERA_THEME",
    "LIGHT_THEME",
    "HDRI_THEME",
    "MATERIAL_THEME",
    "RENDER_THEME",
]
