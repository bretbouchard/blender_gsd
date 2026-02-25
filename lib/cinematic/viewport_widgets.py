"""
Viewport Camera Widget System

Provides interactive 3D viewport gizmos and HUD controls for camera manipulation.
Creates custom gizmos, handle widgets, and heads-up displays for real-time
camera control without navigating menus.

Architecture:
- GizmoGroup: Collections of gizmos that appear together
- Gizmo: Individual 3D handle (arrow, dial, slider, etc.)
- HUDPanel: 2D overlay panels with controls
- WidgetConfig: Configuration for widget appearance and behavior

Features:
- Interactive focal length dial
- Aperture slider
- Focus distance wheel
- Camera type toggle
- Quick rig presets
- Custom property bindings

Usage:
    from lib.cinematic.viewport_widgets import (
        CameraGizmoGroup,
        CameraHUDPanel,
        register_camera_widgets,
    )

    # Register widgets
    register_camera_widgets()

    # Widgets appear when camera is selected
    # Use preferences to customize which widgets appear
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, List, Tuple, Dict, Callable, TYPE_CHECKING
from enum import Enum
import math

# Blender imports with guards
try:
    import bpy
    import gpu
    import bgl
    from gpu_extras.batch import batch_for_shader
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    gpu = None
    bgl = None
    Vector = None
    Matrix = None
    BLENDER_AVAILABLE = False

# Type checking imports
if TYPE_CHECKING:
    from bpy.types import Gizmo, GizmoGroup, Context, Event


# =============================================================================
# WIDGET TYPES AND CONFIG
# =============================================================================

class GizmoType(Enum):
    """Types of 3D gizmos."""
    ARROW = "ARROW"
    DIAL = "DIAL"
    SLIDER = "SLIDER"
    CUBE = "CUBE"
    SPHERE = "SPHERE"
    CUSTOM = "CUSTOM"


class HUDWidgetType(Enum):
    """Types of 2D HUD widgets."""
    SLIDER = "slider"
    BUTTON = "button"
    TOGGLE = "toggle"
    DIAL = "dial"
    LABEL = "label"
    DROPDOWN = "dropdown"
    COLOR = "color"


@dataclass
class WidgetTheme:
    """Theme configuration for widgets."""
    color_normal: Tuple[float, float, float, float] = (1.0, 0.7, 0.2, 0.8)
    color_hover: Tuple[float, float, float, float] = (1.0, 0.9, 0.5, 1.0)
    color_active: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    color_background: Tuple[float, float, float, float] = (0.1, 0.1, 0.15, 0.85)
    color_text: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    color_border: Tuple[float, float, float, float] = (0.3, 0.3, 0.4, 1.0)
    corner_radius: float = 8.0
    font_size: int = 12


@dataclass
class GizmoConfig:
    """Configuration for a 3D gizmo."""
    name: str
    gizmo_type: GizmoType
    target_property: str
    label: str = ""
    min_value: float = 0.0
    max_value: float = 100.0
    scale: float = 1.0
    offset: Tuple[float, float, float] = (0, 0, 0)
    rotation: Tuple[float, float, float] = (0, 0, 0)
    color: Tuple[float, ...] = (1.0, 0.7, 0.2)
    sensitivity: float = 1.0
    format_string: str = "{:.1f}"


@dataclass
class HUDControlConfig:
    """Configuration for a 2D HUD control."""
    name: str
    widget_type: HUDWidgetType
    label: str
    target_property: str
    x: int = 0
    y: int = 0
    width: int = 150
    height: int = 30
    min_value: float = 0.0
    max_value: float = 100.0
    options: List[str] = field(default_factory=list)
    callback: Optional[str] = None  # Function name to call on change


@dataclass
class HUDPanelConfig:
    """Configuration for a HUD panel containing controls."""
    name: str
    title: str
    x: int = 20
    y: int = 100
    width: int = 200
    padding: int = 10
    controls: List[HUDControlConfig] = field(default_factory=list)
    theme: WidgetTheme = field(default_factory=WidgetTheme)


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

# Standard gizmo configurations for camera
CAMERA_GIZMOS: List[GizmoConfig] = [
    GizmoConfig(
        name="focal_length_dial",
        gizmo_type=GizmoType.DIAL,
        target_property="data.lens",
        label="Focal Length",
        min_value=10.0,
        max_value=400.0,
        offset=(2, 0, 0),
        scale=0.5,
        color=(1.0, 0.7, 0.2),
        format_string="{:.0f}mm",
    ),
    GizmoConfig(
        name="focus_distance_arrow",
        gizmo_type=GizmoType.ARROW,
        target_property="data.dof.focus_distance",
        label="Focus",
        min_value=0.1,
        max_value=100.0,
        offset=(0, 0, -0.5),
        rotation=(1.57, 0, 0),
        scale=0.3,
        color=(0.2, 0.8, 1.0),
    ),
    GizmoConfig(
        name="aperture_slider",
        gizmo_type=GizmoType.SLIDER,
        target_property="data.dof.aperture_fstop",
        label="Aperture",
        min_value=1.0,
        max_value=22.0,
        offset=(-2, 0, 0),
        scale=0.4,
        color=(0.8, 0.4, 0.8),
        format_string="f/{:.1f}",
    ),
]

# Standard HUD panel for camera
CAMERA_HUD_PANEL = HUDPanelConfig(
    name="camera_controls",
    title="Camera Controls",
    x=20,
    y=150,
    width=220,
    controls=[
        HUDControlConfig(
            name="focal_length",
            widget_type=HUDWidgetType.SLIDER,
            label="Focal Length",
            target_property="data.lens",
            min_value=10.0,
            max_value=400.0,
        ),
        HUDControlConfig(
            name="aperture",
            widget_type=HUDWidgetType.SLIDER,
            label="Aperture",
            target_property="data.dof.aperture_fstop",
            min_value=1.0,
            max_value=22.0,
        ),
        HUDControlConfig(
            name="focus_distance",
            widget_type=HUDWidgetType.SLIDER,
            label="Focus Distance",
            target_property="data.dof.focus_distance",
            min_value=0.1,
            max_value=100.0,
        ),
        HUDControlConfig(
            name="camera_type",
            widget_type=HUDWidgetType.TOGGLE,
            label="Persp/Ortho",
            target_property="data.type",
            options=["PERSP", "ORTHO"],
        ),
        HUDControlConfig(
            name="dof_toggle",
            widget_type=HUDWidgetType.TOGGLE,
            label="DOF",
            target_property="data.dof.use_dof",
        ),
    ],
)


# =============================================================================
# 3D GIZMO IMPLEMENTATION
# =============================================================================

class CameraGizmoGroup:
    """
    3D Gizmo group for camera manipulation.

    Creates interactive 3D handles around the camera for:
    - Focal length (dial)
    - Focus distance (arrow)
    - Aperture (slider)
    """

    bl_idname = "OBJECT_GGT_camera_controls"
    bl_label = "Camera Controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "SHOW_MODAL_ALL"}

    # Class-level storage for gizmo configs
    gizmo_configs: List[GizmoConfig] = CAMERA_GIZMOS

    @classmethod
    def poll(cls, context: "Context") -> bool:
        """Show gizmos only when camera is selected."""
        if not BLENDER_AVAILABLE:
            return False
        obj = context.active_object
        return obj is not None and obj.type == "CAMERA"

    def setup(self, context: "Context"):
        """Create gizmos for the camera."""
        if not BLENDER_AVAILABLE:
            return

        # Store gizmo references
        self.gizmos = {}

        for config in self.gizmo_configs:
            gizmo = self.create_gizmo(config)
            if gizmo:
                self.gizmos[config.name] = gizmo

    def create_gizmo(self, config: GizmoConfig) -> Optional["Gizmo"]:
        """Create a single gizmo from configuration."""
        if not BLENDER_AVAILABLE:
            return None

        # Select gizmo type
        if config.gizmo_type == GizmoType.DIAL:
            gz = self.gizmos.new("GIZMO_GT_dial_3d")
            gz.draw_options = {"ANGLE_START_Y"}
        elif config.gizmo_type == GizmoType.ARROW:
            gz = self.gizmos.new("GIZMO_GT_arrow_3d")
            gz.draw_options = {"ORIGIN", "ARROW_HEAD"}
        elif config.gizmo_type == GizmoType.SLIDER:
            gz = self.gizmos.new("GIZMO_GT_primitive_3d")
            gz.draw_style = "BOX"
        else:
            gz = self.gizmos.new("GIZMO_GT_move_3d")

        # Set properties
        gz.target_set_prop("offset", bpy.context.active_object, config.target_property)

        # Set appearance
        gz.color = config.color[:3]
        gz.color_highlight = tuple(min(1.0, c + 0.3) for c in config.color[:3])
        gz.alpha = 0.8
        gz.alpha_highlight = 1.0

        # Set scale
        gz.scale_basis = config.scale

        # Store config for refresh
        gz.config = config

        return gz

    def refresh(self, context: "Context"):
        """Update gizmo positions based on camera transform."""
        if not BLENDER_AVAILABLE:
            return

        obj = context.active_object
        if not obj or obj.type != "CAMERA":
            return

        for name, gz in self.gizmos.items():
            config = getattr(gz, "config", None)
            if not config:
                continue

            # Calculate world position for gizmo
            # Transform local offset to world space
            local_offset = Vector(config.offset)
            world_pos = obj.matrix_world @ local_offset

            # Set gizmo matrix
            gz.matrix_basis = obj.matrix_world
            gz.matrix_basis.translation = world_pos


# =============================================================================
# 2D HUD PANEL IMPLEMENTATION
# =============================================================================

class CameraHUDPanel:
    """
    2D Heads-Up Display panel for camera controls.

    Provides slider, button, and toggle controls overlaid on the viewport.
    Modular design allows adding arbitrary controls.
    """

    bl_idname = "VIEW3D_PT_camera_hud"
    bl_label = "Camera HUD"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HUD"
    bl_options = {"HEADER_LAYOUT_EXPAND"}

    # Class-level configuration
    panel_config: HUDPanelConfig = CAMERA_HUD_PANEL

    def __init__(self):
        self.is_dragging = False
        self.drag_control: Optional[HUDControlConfig] = None
        self.hover_control: Optional[HUDControlConfig] = None
        self.values: Dict[str, float] = {}

    def draw(self, context: "Context"):
        """Draw the HUD panel."""
        if not BLENDER_AVAILABLE:
            return

        obj = context.active_object
        if not obj or obj.type != "CAMERA":
            return

        layout = self.layout
        config = self.panel_config

        # Panel container
        col = layout.column(align=True)
        col.scale_x = config.width / 100  # Approximate scaling

        # Title
        row = col.row()
        row.label(text=config.title, icon="CAMERA_DATA")
        row.separator()

        # Controls
        for ctrl_config in config.controls:
            self.draw_control(col, obj, ctrl_config)

    def draw_control(self, layout, obj, config: HUDControlConfig):
        """Draw a single control."""
        if not BLENDER_AVAILABLE:
            return

        row = layout.row(align=True)

        # Label
        row.label(text=config.label + ":")

        # Widget based on type
        if config.widget_type == HUDWidgetType.SLIDER:
            # Get property value
            try:
                row.prop(obj, config.target_property, text="", slider=True)
            except (TypeError, AttributeError):
                row.label(text="N/A")

        elif config.widget_type == HUDWidgetType.TOGGLE:
            try:
                row.prop(obj, config.target_property, text="", toggle=True)
            except (TypeError, AttributeError):
                row.label(text="N/A")

        elif config.widget_type == HUDWidgetType.DROPDOWN:
            row.prop_enum(obj, config.target_property, text="")

        elif config.widget_type == HUDWidgetType.BUTTON:
            if config.callback:
                row.operator(config.callback, text=config.label)


# =============================================================================
# MODULAR HUD FRAMEWORK
# =============================================================================

class HUDWidget:
    """
    Base class for modular HUD widgets.

    Each widget controls a single property and can be configured
    with label, range, and callback.
    """

    def __init__(
        self,
        name: str,
        label: str,
        target_object: str,
        target_property: str,
        x: int = 0,
        y: int = 0,
        width: int = 180,
        height: int = 32,
        theme: WidgetTheme = None,
    ):
        self.name = name
        self.label = label
        self.target_object = target_object
        self.target_property = target_property
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.theme = theme or WidgetTheme()
        self.visible = True
        self.enabled = True
        self._hover = False
        self._dragging = False
        self._value = None

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Get widget bounds (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within widget bounds."""
        x1, y1, x2, y2 = self.bounds
        return x1 <= x <= x2 and y1 <= y <= y2

    def get_value(self) -> Any:
        """Get current value from target property."""
        if not BLENDER_AVAILABLE:
            return None

        obj = bpy.data.objects.get(self.target_object)
        if not obj:
            return None

        # Navigate property path (e.g., "data.lens")
        parts = self.target_property.split(".")
        value = obj
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        self._value = value
        return value

    def set_value(self, value: Any) -> bool:
        """Set value on target property."""
        if not BLENDER_AVAILABLE or not self.enabled:
            return False

        obj = bpy.data.objects.get(self.target_object)
        if not obj:
            return False

        # Navigate to parent and set final property
        parts = self.target_property.split(".")
        target = obj
        for part in parts[:-1]:
            if hasattr(target, part):
                target = getattr(target, part)
            else:
                return False

        final_prop = parts[-1]
        if hasattr(target, final_prop):
            try:
                setattr(target, final_prop, value)
                self._value = value
                return True
            except (TypeError, AttributeError):
                return False

        return False

    def on_mouse_enter(self):
        """Called when mouse enters widget."""
        self._hover = True

    def on_mouse_leave(self):
        """Called when mouse leaves widget."""
        self._hover = False
        self._dragging = False

    def on_mouse_down(self, x: int, y: int) -> bool:
        """Handle mouse down. Return True if consumed."""
        if self.contains_point(x, y):
            self._dragging = True
            return True
        return False

    def on_mouse_up(self, x: int, y: int):
        """Handle mouse up."""
        self._dragging = False

    def on_mouse_move(self, x: int, y: int, dx: int, dy: int) -> bool:
        """Handle mouse move while dragging. Return True if consumed."""
        return self._dragging

    def draw(self, context: "Context"):
        """Draw the widget. Override in subclasses."""
        pass


class HUDSlider(HUDWidget):
    """Slider widget for numeric values."""

    def __init__(
        self,
        name: str,
        label: str,
        target_object: str,
        target_property: str,
        min_value: float = 0.0,
        max_value: float = 100.0,
        format_string: str = "{:.1f}",
        **kwargs
    ):
        super().__init__(name, label, target_object, target_property, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.format_string = format_string
        self.height = 40  # Slider height

    def on_mouse_move(self, x: int, y: int, dx: int, dy: int) -> bool:
        if not self._dragging:
            return False

        # Calculate new value from x position
        rel_x = x - self.x
        t = max(0, min(1, rel_x / self.width))
        new_value = self.min_value + t * (self.max_value - self.min_value)
        self.set_value(new_value)
        return True

    def draw(self, context: "Context"):
        if not self.visible or not BLENDER_AVAILABLE:
            return

        value = self.get_value()
        if value is None:
            value = self.min_value

        # Calculate normalized value
        t = (value - self.min_value) / (self.max_value - self.min_value)
        t = max(0, min(1, t))

        # Get colors
        theme = self.theme
        bg_color = theme.color_background
        fill_color = theme.color_normal if not self._hover else theme.color_hover
        text_color = theme.color_text

        # Draw background
        self._draw_rect(self.x, self.y, self.width, self.height, bg_color)

        # Draw fill
        fill_width = int(self.width * t)
        self._draw_rect(self.x, self.y, fill_width, self.height, fill_color)

        # Draw label and value
        label_text = f"{self.label}"
        value_text = self.format_string.format(value)
        self._draw_text(self.x + 5, self.y + 22, label_text, text_color)
        self._draw_text(self.x + self.width - 60, self.y + 22, value_text, text_color)

    def _draw_rect(self, x: int, y: int, w: int, h: int, color: Tuple[float, ...]):
        """Draw a filled rectangle."""
        if not BLENDER_AVAILABLE:
            return

        # Use GPU immediate mode for drawing
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", color)

        vertices = [
            (x, y), (x + w, y), (x + w, y + h), (x, y + h)
        ]

        batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
        batch.draw(shader)

    def _draw_text(self, x: int, y: int, text: str, color: Tuple[float, ...]):
        """Draw text at position."""
        if not BLENDER_AVAILABLE:
            return

        # Text drawing in Blender requires font system
        # This is a simplified placeholder - real implementation
        # would use blf module
        import blf
        font_id = 0
        blf.position(font_id, x, y, 0)
        blf.color(font_id, *color)
        blf.size(font_id, self.theme.font_size)
        blf.draw(font_id, text)


class HUDToggle(HUDWidget):
    """Toggle button widget."""

    def __init__(
        self,
        name: str,
        label: str,
        target_object: str,
        target_property: str,
        on_label: str = "ON",
        off_label: str = "OFF",
        **kwargs
    ):
        super().__init__(name, label, target_object, target_property, **kwargs)
        self.on_label = on_label
        self.off_label = off_label
        self.width = 100
        self.height = 32

    def on_mouse_up(self, x: int, y: int):
        if self.contains_point(x, y):
            # Toggle value
            current = self.get_value()
            if isinstance(current, bool):
                self.set_value(not current)
        super().on_mouse_up(x, y)

    def draw(self, context: "Context"):
        if not self.visible or not BLENDER_AVAILABLE:
            return

        value = self.get_value() or False
        theme = self.theme

        # Background
        bg_color = theme.color_background
        self._draw_rect(self.x, self.y, self.width, self.height, bg_color)

        # State indicator
        state_color = (0.3, 0.9, 0.3, 1.0) if value else (0.9, 0.3, 0.3, 1.0)
        indicator_width = 30
        self._draw_rect(
            self.x + self.width - indicator_width - 5,
            self.y + 5,
            indicator_width,
            self.height - 10,
            state_color
        )

        # Label
        import blf
        blf.position(0, self.x + 5, self.y + 10, 0)
        blf.color(0, *theme.color_text)
        blf.size(0, theme.font_size)
        blf.draw(0, self.label)

    def _draw_rect(self, x: int, y: int, w: int, h: int, color: Tuple[float, ...]):
        """Draw a filled rectangle."""
        if not BLENDER_AVAILABLE:
            return

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", color)

        vertices = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
        batch.draw(shader)


class HUDDial(HUDWidget):
    """Rotary dial widget for continuous values."""

    def __init__(
        self,
        name: str,
        label: str,
        target_object: str,
        target_property: str,
        min_value: float = 0.0,
        max_value: float = 100.0,
        radius: int = 40,
        **kwargs
    ):
        super().__init__(name, label, target_object, target_property, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.radius = radius
        self.width = radius * 2
        self.height = radius * 2 + 20
        self._last_angle = 0

    def on_mouse_move(self, x: int, y: int, dx: int, dy: int) -> bool:
        if not self._dragging:
            return False

        # Calculate angle from center
        cx = self.x + self.radius
        cy = self.y + self.radius + 20
        angle = math.atan2(y - cy, x - cx)

        # Calculate angle delta
        delta_angle = angle - self._last_angle

        # Handle wrap-around
        if delta_angle > math.pi:
            delta_angle -= 2 * math.pi
        elif delta_angle < -math.pi:
            delta_angle += 2 * math.pi

        self._last_angle = angle

        # Map angle to value
        value_range = self.max_value - self.min_value
        delta_value = (delta_angle / (2 * math.pi)) * value_range

        new_value = self.get_value() + delta_value
        new_value = max(self.min_value, min(self.max_value, new_value))
        self.set_value(new_value)

        return True

    def draw(self, context: "Context"):
        if not self.visible or not BLENDER_AVAILABLE:
            return

        value = self.get_value() or self.min_value
        t = (value - self.min_value) / (self.max_value - self.min_value)

        cx = self.x + self.radius
        cy = self.y + self.radius + 20

        theme = self.theme

        # Draw dial background
        self._draw_circle(cx, cy, self.radius, theme.color_background)

        # Draw dial arc
        self._draw_arc(cx, cy, self.radius - 5, 0, t * 2 * math.pi, theme.color_normal)

        # Draw knob
        knob_angle = t * 2 * math.pi - math.pi / 2
        knob_x = cx + (self.radius - 15) * math.cos(knob_angle)
        knob_y = cy + (self.radius - 15) * math.sin(knob_angle)
        self._draw_circle(knob_x, knob_y, 8, theme.color_active)

        # Draw label
        import blf
        blf.position(0, self.x, self.y + 5, 0)
        blf.color(0, *theme.color_text)
        blf.size(0, theme.font_size)
        blf.draw(0, f"{self.label}: {value:.1f}")

    def _draw_circle(self, cx: float, cy: float, r: float, color: Tuple[float, ...]):
        """Draw a filled circle."""
        if not BLENDER_AVAILABLE:
            return

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", color)

        # Generate circle vertices
        segments = 32
        vertices = [(cx, cy)]
        for i in range(segments + 1):
            angle = (i / segments) * 2 * math.pi
            vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

        batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
        batch.draw(shader)

    def _draw_arc(self, cx: float, cy: float, r: float, start_angle: float, end_angle: float, color: Tuple[float, ...]):
        """Draw an arc."""
        if not BLENDER_AVAILABLE:
            return

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", color)

        segments = 32
        vertices = [(cx, cy)]
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + t * (end_angle - start_angle) - math.pi / 2
            vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

        batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
        batch.draw(shader)


# =============================================================================
# MODULAR HUD MANAGER
# =============================================================================

class HUDManager:
    """
    Manager for modular HUD widgets.

    Provides a unified system for adding, removing, and rendering
    arbitrary HUD controls. Widgets can be registered dynamically.

    Usage:
        hud = HUDManager.get_instance()
        hud.add_widget(HUDSlider(...))
        hud.add_widget(HUDToggle(...))

        # In draw callback:
        hud.draw(context)

        # In mouse handler:
        hud.handle_mouse_event(event)
    """

    _instance: Optional["HUDManager"] = None

    def __init__(self):
        self.widgets: Dict[str, HUDWidget] = {}
        self.panels: Dict[str, List[str]] = {}  # Panel name -> widget names
        self.theme = WidgetTheme()
        self.visible = True
        self._capture_mouse = False

    @classmethod
    def get_instance(cls) -> "HUDManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_widget(self, widget: HUDWidget, panel: str = "default") -> str:
        """Add a widget to the HUD. Returns widget name."""
        self.widgets[widget.name] = widget

        if panel not in self.panels:
            self.panels[panel] = []
        self.panels[panel].append(widget.name)

        return widget.name

    def remove_widget(self, name: str):
        """Remove a widget by name."""
        if name in self.widgets:
            del self.widgets[name]
            for panel_widgets in self.panels.values():
                if name in panel_widgets:
                    panel_widgets.remove(name)

    def get_widget(self, name: str) -> Optional[HUDWidget]:
        """Get widget by name."""
        return self.widgets.get(name)

    def clear_panel(self, panel: str = "default"):
        """Remove all widgets from a panel."""
        if panel in self.panels:
            for name in self.panels[panel]:
                if name in self.widgets:
                    del self.widgets[name]
            self.panels[panel] = []

    def layout_panel_vertical(
        self,
        panel: str,
        x: int,
        y: int,
        spacing: int = 5,
    ):
        """Auto-layout widgets in a panel vertically."""
        if panel not in self.panels:
            return

        current_y = y
        for name in self.panels[panel]:
            widget = self.widgets.get(name)
            if widget:
                widget.x = x
                widget.y = current_y
                current_y -= widget.height + spacing

    def draw(self, context: "Context"):
        """Draw all visible widgets."""
        if not self.visible or not BLENDER_AVAILABLE:
            return

        for widget in self.widgets.values():
            if widget.visible:
                widget.draw(context)

    def handle_mouse_event(self, event: "Event", context: "Context") -> bool:
        """
        Handle mouse event. Returns True if consumed.

        Call from modal operator or event handler.
        """
        if not self.visible:
            return False

        x, y = event.mouse_x, event.mouse_y

        # Find hovered widget
        hovered = None
        for widget in reversed(list(self.widgets.values())):
            if widget.visible and widget.contains_point(x, y):
                hovered = widget
                break

        # Update hover states
        for widget in self.widgets.values():
            if widget == hovered:
                if not widget._hover:
                    widget.on_mouse_enter()
            else:
                if widget._hover:
                    widget.on_mouse_leave()

        # Handle event type
        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                if hovered:
                    return hovered.on_mouse_down(x, y)
            elif event.value == "RELEASE":
                for widget in self.widgets.values():
                    widget.on_mouse_up(x, y)

        elif event.type == "MOUSEMOVE":
            dx, dy = event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y
            for widget in self.widgets.values():
                if widget.on_mouse_move(x, y, dx, dy):
                    return True

        return hovered is not None


# =============================================================================
# CAMERA HUD PRESETS
# =============================================================================

def create_camera_hud(camera_name: str) -> List[HUDWidget]:
    """
    Create standard HUD widgets for a camera.

    Returns list of widgets ready to add to HUDManager.
    """
    widgets = []

    # Focal length slider
    widgets.append(HUDSlider(
        name=f"{camera_name}_focal_length",
        label="Focal Length",
        target_object=camera_name,
        target_property="data.lens",
        min_value=10.0,
        max_value=400.0,
        format_string="{:.0f}mm",
    ))

    # Aperture slider
    widgets.append(HUDSlider(
        name=f"{camera_name}_aperture",
        label="Aperture",
        target_object=camera_name,
        target_property="data.dof.aperture_fstop",
        min_value=1.0,
        max_value=22.0,
        format_string="f/{:.1f}",
    ))

    # Focus distance slider
    widgets.append(HUDSlider(
        name=f"{camera_name}_focus",
        label="Focus Dist",
        target_object=camera_name,
        target_property="data.dof.focus_distance",
        min_value=0.1,
        max_value=100.0,
        format_string="{:.1f}m",
    ))

    # DOF toggle
    widgets.append(HUDToggle(
        name=f"{camera_name}_dof",
        label="DOF",
        target_object=camera_name,
        target_property="data.dof.use_dof",
    ))

    return widgets


def setup_camera_hud(camera_name: str, x: int = 20, y: int = 200) -> None:
    """
    Setup complete HUD for a camera.

    Creates widgets and adds them to the HUDManager with auto-layout.
    """
    hud = HUDManager.get_instance()

    # Create widgets
    widgets = create_camera_hud(camera_name)

    # Add to HUD manager
    panel_name = f"camera_{camera_name}"
    for widget in widgets:
        hud.add_widget(widget, panel=panel_name)

    # Layout vertically
    hud.layout_panel_vertical(panel_name, x, y)


# =============================================================================
# REGISTRATION
# =============================================================================

# Gizmo classes to register
GIZMO_CLASSES = []

# Panel classes to register
PANEL_CLASSES = []


def register_camera_widgets():
    """Register all camera widget classes with Blender."""
    if not BLENDER_AVAILABLE:
        return

    for cls in GIZMO_CLASSES:
        bpy.utils.register_class(cls)

    for cls in PANEL_CLASSES:
        bpy.utils.register_class(cls)


def unregister_camera_widgets():
    """Unregister all camera widget classes."""
    if not BLENDER_AVAILABLE:
        return

    for cls in reversed(PANEL_CLASSES):
        bpy.utils.unregister_class(cls)

    for cls in reversed(GIZMO_CLASSES):
        bpy.utils.unregister_class(cls)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Gizmo classes
    "CameraGizmoGroup",
    # HUD classes
    "CameraHUDPanel",
    "HUDManager",
    "HUDWidget",
    "HUDSlider",
    "HUDToggle",
    "HUDDial",
    # Configuration
    "GizmoConfig",
    "HUDControlConfig",
    "HUDPanelConfig",
    "WidgetTheme",
    "GizmoType",
    "HUDWidgetType",
    # Presets
    "CAMERA_GIZMOS",
    "CAMERA_HUD_PANEL",
    # Functions
    "create_camera_hud",
    "setup_camera_hud",
    "register_camera_widgets",
    "unregister_camera_widgets",
]
