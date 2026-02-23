"""
HUD System - Vehicle Telemetry Overlay

Creates in-scene HUD overlays for vehicle telemetry including:
- Steering wheel indicator with live rotation display
- Speed gauge with analog and digital readout
- RPM indicator
- Gear position display
- G-force meter for stunts
- Mini-map/heading indicator

Supports two modes:
1. Screen-space overlay (always visible, follows camera)
2. World-space (attached to vehicle, perspective correct)

Usage:
    from lib.vehicle.launch_control.hud import (
        HUDSystem, HUDConfig, HUDWidget, SteeringWidget,
        SpeedometerWidget, RPMWidget, GearWidget, GForceWidget
    )

    # Create HUD for vehicle
    hud = HUDSystem(vehicle_rig)
    hud.configure(show_steering=True, show_speed=True)
    hud.attach_to_camera(active_camera)  # Screen-space mode
    # OR
    hud.attach_to_vehicle()  # World-space mode

    # Connect to Launch Control telemetry
    hud.connect_telemetry(physics_system, steering_system)

    # Animate HUD
    hud.update(frame)  # Call each frame for animation

    # Create all widgets at once
    hud = create_vehicle_hud(vehicle_rig, camera, preset="racing")
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from math import pi, sin, cos, sqrt
import colorsys

# Blender availability check
try:
    import bpy
    from mathutils import Vector, Matrix, Euler
    import bmesh
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Matrix = None
    Euler = None
    bmesh = None
    BLENDER_AVAILABLE = False


class HUDMode(Enum):
    """HUD display mode."""
    SCREEN_SPACE = "screen_space"  # 2D overlay, always visible
    WORLD_SPACE = "world_space"    # 3D in scene, perspective correct
    DASHBOARD = "dashboard"        # Attached to dashboard, driver POV


class WidgetType(Enum):
    """Types of HUD widgets."""
    STEERING = "steering"
    SPEEDOMETER = "speedometer"
    RPM = "rpm"
    GEAR = "gear"
    GFORCE = "gforce"
    HEADING = "heading"
    LAP_TIMER = "lap_timer"
    FUEL = "fuel"
    TEMPERATURE = "temperature"


@dataclass
class HUDConfig:
    """Configuration for HUD system."""
    mode: HUDMode = HUDMode.SCREEN_SPACE

    # Position (screen-space: 0-1, world-space: meters)
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Scale factor
    scale: float = 1.0

    # Visibility
    show_steering: bool = True
    show_speed: bool = True
    show_rpm: bool = True
    show_gear: bool = True
    show_gforce: bool = False
    show_heading: bool = False

    # Colors
    primary_color: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0)  # Green
    warning_color: Tuple[float, float, float, float] = (1.0, 0.8, 0.0, 1.0)  # Yellow
    danger_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0)    # Red
    background_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.5)  # Semi-transparent black

    # Opacity
    opacity: float = 0.9

    # Animation
    animate_needles: bool = True
    animation_smoothing: float = 0.15  # Lower = snappier, Higher = smoother


@dataclass
class TelemetryData:
    """Real-time vehicle telemetry."""
    speed: float = 0.0           # m/s
    speed_kmh: float = 0.0       # km/h
    speed_mph: float = 0.0       # mph
    rpm: float = 0.0             # RPM
    gear: int = 1                # Current gear (0=R, 1-6=forward)
    steering_angle: float = 0.0  # degrees (-left, +right)
    steering_rotation: float = 0.0  # Steering wheel rotation in degrees
    g_force_x: float = 0.0       # Lateral G
    g_force_y: float = 0.0       # Longitudinal G (acceleration/braking)
    g_force_z: float = 0.0       # Vertical G
    g_force_total: float = 0.0   # Total G magnitude
    heading: float = 0.0         # Degrees (0=North)
    throttle: float = 0.0        # 0-1
    brake: float = 0.0           # 0-1
    clutch: float = 0.0          # 0-1
    handbrake: bool = False
    abs_active: bool = False
    traction_control: bool = False
    drift_mode: bool = False


class HUDWidget:
    """Base class for HUD widgets."""

    def __init__(
        self,
        widget_type: WidgetType,
        config: HUDConfig,
        position_offset: Tuple[float, float, float] = (0, 0, 0),
    ):
        self.widget_type = widget_type
        self.config = config
        self.position_offset = position_offset
        self.objects: Dict[str, Any] = {}
        self.materials: Dict[str, Any] = {}
        self._blender_available = BLENDER_AVAILABLE
        self._bpy = bpy

        # Animation state
        self._current_value: float = 0.0
        self._target_value: float = 0.0

    def create(self, parent: Optional[Any] = None) -> bool:
        """Create widget geometry. Override in subclass."""
        return False

    def update(self, telemetry: TelemetryData) -> None:
        """Update widget with new telemetry. Override in subclass."""
        pass

    def show(self) -> None:
        """Show widget."""
        for obj in self.objects.values():
            if obj:
                obj.hide_viewport = False
                obj.hide_render = False

    def hide(self) -> None:
        """Hide widget."""
        for obj in self.objects.values():
            if obj:
                obj.hide_viewport = True
                obj.hide_render = True

    def delete(self) -> None:
        """Remove widget from scene."""
        if not self._blender_available:
            return

        for obj in self.objects.values():
            if obj:
                self._bpy.data.objects.remove(obj, do_unlink=True)
        self.objects.clear()

        for mat in self.materials.values():
            if mat:
                self._bpy.data.materials.remove(mat, do_unlink=True)
        self.materials.clear()

    def _animate_value(self, target: float) -> float:
        """Smoothly animate to target value."""
        smoothing = self.config.animation_smoothing
        self._target_value = target
        self._current_value += (self._target_value - self._current_value) * smoothing
        return self._current_value

    def _create_material(
        self,
        name: str,
        color: Tuple[float, float, float, float],
        emission: float = 0.0,
    ) -> Any:
        """Create a material for HUD element."""
        if not self._blender_available:
            return None

        if name in self._bpy.data.materials:
            return self._bpy.data.materials[name]

        mat = self._bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Alpha"].default_value = color[3]

            if emission > 0:
                bsdf.inputs["Emission"].default_value = (*color[:3], 1.0)
                bsdf.inputs["Emission Strength"].default_value = emission

        mat.blend_method = 'BLEND'
        mat.shadow_method = 'CLIP'

        self.materials[name] = mat
        return mat


class SteeringWidget(HUDWidget):
    """
    Steering wheel indicator widget.

    Shows a steering wheel graphic that rotates based on
    current steering angle.
    """

    def __init__(self, config: HUDConfig, position_offset: Tuple[float, float, float] = (0, 0, 0)):
        super().__init__(WidgetType.STEERING, config, position_offset)
        self.wheel_diameter = 0.1  # meters
        self.max_rotation = 540.0  # degrees (1.5 turns lock-to-lock)

    def create(self, parent: Optional[Any] = None) -> bool:
        """Create steering wheel indicator."""
        if not self._blender_available:
            return False

        try:
            # Create root empty for the widget
            root_name = "HUD_Steering"
            root = self._bpy.data.objects.new(root_name, None)
            root.empty_display_type = 'ARROWS'

            # Position based on mode
            pos = (
                self.config.position[0] + self.position_offset[0],
                self.config.position[1] + self.position_offset[1],
                self.config.position[2] + self.position_offset[2],
            )
            root.location = pos

            self._bpy.context.collection.objects.link(root)
            self.objects['root'] = root

            # Create steering wheel visual (torus)
            self._create_wheel_visual(root)

            # Create center marker
            self._create_center_marker(root)

            # Create rotation indicator (needle)
            self._create_rotation_indicator(root)

            # Create left/right markers
            self._create_lock_markers(root)

            if parent:
                root.parent = parent

            return True

        except Exception:
            return False

    def _create_wheel_visual(self, parent: Any) -> None:
        """Create the steering wheel ring visual."""
        # Create torus for wheel rim
        mesh = self._bpy.data.meshes.new("HUD_Steering_Rim")
        rim_obj = self._bpy.data.objects.new("HUD_Steering_Rim", mesh)

        bm = bmesh.new()

        # Create torus (rim)
        major_radius = self.wheel_diameter / 2
        minor_radius = 0.008  # Rim thickness

        segments = 32
        ring_segments = 8

        for i in range(segments):
            angle = 2 * pi * i / segments
            for j in range(ring_segments):
                ring_angle = 2 * pi * j / ring_segments

                x = (major_radius + minor_radius * cos(ring_angle)) * cos(angle)
                y = (major_radius + minor_radius * cos(ring_angle)) * sin(angle)
                z = minor_radius * sin(ring_angle)

                bm.verts.new((x, y, z))

        bm.verts.ensure_lookup_table()

        # Create faces
        for i in range(segments):
            for j in range(ring_segments):
                v1 = bm.verts[i * ring_segments + j]
                v2 = bm.verts[i * ring_segments + (j + 1) % ring_segments]
                v3 = bm.verts[((i + 1) % segments) * ring_segments + (j + 1) % ring_segments]
                v4 = bm.verts[((i + 1) % segments) * ring_segments + j]
                bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        rim_obj.parent = parent
        self._bpy.context.collection.objects.link(rim_obj)

        # Material
        mat = self._create_material(
            "HUD_Steering_Rim",
            self.config.primary_color,
            emission=0.5
        )
        rim_obj.data.materials.append(mat)

        self.objects['rim'] = rim_obj

    def _create_center_marker(self, parent: Any) -> None:
        """Create center (12 o'clock) marker on wheel."""
        # Create small triangle at top
        mesh = self._bpy.data.meshes.new("HUD_Steering_CenterMarker")
        marker = self._bpy.data.objects.new("HUD_Steering_CenterMarker", mesh)

        bm = bmesh.new()

        # Triangle at top
        r = self.wheel_diameter / 2
        v1 = bm.verts.new((0, -r + 0.01, 0.015))
        v2 = bm.verts.new((-0.01, -r + 0.025, 0))
        v3 = bm.verts.new((0.01, -r + 0.025, 0))

        bm.faces.new([v1, v2, v3])

        bm.to_mesh(mesh)
        bm.free()

        marker.parent = parent
        self._bpy.context.collection.objects.link(marker)

        mat = self._create_material(
            "HUD_Steering_Marker",
            (1.0, 1.0, 1.0, 1.0),
            emission=1.0
        )
        marker.data.materials.append(mat)

        self.objects['center_marker'] = marker

    def _create_rotation_indicator(self, parent: Any) -> None:
        """Create needle showing actual steering angle."""
        mesh = self._bpy.data.meshes.new("HUD_Steering_Needle")
        needle = self._bpy.data.objects.new("HUD_Steering_Needle", mesh)

        bm = bmesh.new()

        # Arrow/needle shape
        r = self.wheel_diameter / 2 - 0.01
        v1 = bm.verts.new((0, r, 0.02))
        v2 = bm.verts.new((-0.015, r - 0.03, 0.02))
        v3 = bm.verts.new((0.015, r - 0.03, 0.02))

        bm.faces.new([v1, v2, v3])

        bm.to_mesh(mesh)
        bm.free()

        needle.parent = parent
        self._bpy.context.collection.objects.link(needle)

        mat = self._create_material(
            "HUD_Steering_Needle",
            (1.0, 0.3, 0.0, 1.0),  # Orange
            emission=1.0
        )
        needle.data.materials.append(mat)

        self.objects['needle'] = needle

    def _create_lock_markers(self, parent: Any) -> None:
        """Create left/right lock markers."""
        r = self.wheel_diameter / 2 + 0.02

        for side, angle_offset in [("left", -45), ("right", 45)]:
            mesh = self._bpy.data.meshes.new(f"HUD_Steering_Lock_{side}")
            marker = self._bpy.data.objects.new(f"HUD_Steering_Lock_{side}", mesh)

            bm = bmesh.new()

            # Small line marker
            angle = angle_offset * pi / 180
            x = r * sin(angle)
            y = -r * cos(angle)

            v1 = bm.verts.new((x - 0.005, y, 0))
            v2 = bm.verts.new((x + 0.005, y, 0))
            v3 = bm.verts.new((x + 0.005, y + 0.015, 0))
            v4 = bm.verts.new((x - 0.005, y + 0.015, 0))

            bm.faces.new([v1, v2, v3, v4])

            bm.to_mesh(mesh)
            bm.free()

            marker.parent = parent
            self._bpy.context.collection.objects.link(marker)

            mat = self._create_material(
                f"HUD_Steering_Lock_{side}",
                self.config.warning_color,
                emission=0.5
            )
            marker.data.materials.append(mat)

            self.objects[f'lock_{side}'] = marker

    def update(self, telemetry: TelemetryData) -> None:
        """Update steering wheel rotation."""
        if not self._blender_available:
            return

        needle = self.objects.get('needle')
        if not needle:
            return

        # Animate to target rotation
        # Steering wheel rotation = steering angle * steering ratio
        target_rotation = telemetry.steering_rotation

        if self.config.animate_needles:
            current = self._animate_value(target_rotation)
        else:
            current = target_rotation

        # Apply rotation (around Z axis for top-down wheel view)
        needle.rotation_euler = Euler((0, 0, current * pi / 180), 'XYZ')


class SpeedometerWidget(HUDWidget):
    """
    Speedometer widget with analog dial and digital readout.
    """

    def __init__(self, config: HUDConfig, position_offset: Tuple[float, float, float] = (0, 0, 0)):
        super().__init__(WidgetType.SPEEDOMETER, config, position_offset)
        self.max_speed = 320.0  # km/h
        self.dial_radius = 0.08

    def create(self, parent: Optional[Any] = None) -> bool:
        """Create speedometer widget."""
        if not self._blender_available:
            return False

        try:
            root_name = "HUD_Speedometer"
            root = self._bpy.data.objects.new(root_name, None)
            root.empty_display_type = 'ARROWS'

            pos = (
                self.config.position[0] + self.position_offset[0],
                self.config.position[1] + self.position_offset[1],
                self.config.position[2] + self.position_offset[2],
            )
            root.location = pos

            self._bpy.context.collection.objects.link(root)
            self.objects['root'] = root

            # Create dial background
            self._create_dial_background(root)

            # Create speed marks
            self._create_speed_marks(root)

            # Create needle
            self._create_needle(root)

            # Create digital readout placeholder
            self._create_digital_display(root)

            if parent:
                root.parent = parent

            return True

        except Exception:
            return False

    def _create_dial_background(self, parent: Any) -> None:
        """Create the dial face background."""
        mesh = self._bpy.data.meshes.new("HUD_Speedometer_Background")
        bg = self._bpy.data.objects.new("HUD_Speedometer_Background", mesh)

        bm = bmesh.new()
        bmesh.ops.create_circle(bm, radius=self.dial_radius, segments=64)
        bm.to_mesh(mesh)
        bm.free()

        # Extrude to give thickness
        # (simplified - just a flat disc)

        bg.parent = parent
        self._bpy.context.collection.objects.link(bg)

        mat = self._create_material(
            "HUD_Dial_BG",
            self.config.background_color,
            emission=0.1
        )
        bg.data.materials.append(mat)

        self.objects['background'] = bg

    def _create_speed_marks(self, parent: Any) -> None:
        """Create speed marks around dial."""
        marks = []

        # Speed marks every 20 km/h
        for speed in range(0, int(self.max_speed) + 1, 20):
            # Angle: 240 degree sweep (from -120 to +120)
            angle_deg = -120 + (speed / self.max_speed) * 240
            angle_rad = angle_deg * pi / 180

            # Create mark
            mesh = self._bpy.data.meshes.new(f"HUD_Speed_Mark_{speed}")
            mark = self._bpy.data.objects.new(f"HUD_Speed_Mark_{speed}", mesh)

            bm = bmesh.new()

            r_inner = self.dial_radius * 0.75
            r_outer = self.dial_radius * 0.9

            # Line from inner to outer
            thickness = 0.003 if speed % 40 == 0 else 0.0015

            x1 = r_inner * sin(angle_rad)
            y1 = -r_inner * cos(angle_rad)
            x2 = r_outer * sin(angle_rad)
            y2 = -r_outer * cos(angle_rad)

            # Create thin rectangle for mark
            dx = thickness * cos(angle_rad)
            dy = thickness * sin(angle_rad)

            v1 = bm.verts.new((x1 - dx, y1 - dy, 0.01))
            v2 = bm.verts.new((x1 + dx, y1 + dy, 0.01))
            v3 = bm.verts.new((x2 + dx, y2 + dy, 0.01))
            v4 = bm.verts.new((x2 - dx, y2 - dy, 0.01))

            bm.faces.new([v1, v2, v3, v4])

            bm.to_mesh(mesh)
            bm.free()

            mark.parent = parent
            self._bpy.context.collection.objects.link(mark)

            color = self.config.primary_color
            if speed >= self.max_speed * 0.8:
                color = self.config.danger_color
            elif speed >= self.max_speed * 0.6:
                color = self.config.warning_color

            mat = self._create_material(
                f"HUD_Speed_Mark_{speed}",
                color,
                emission=0.8
            )
            mark.data.materials.append(mat)

            marks.append(mark)

        self.objects['marks'] = marks

    def _create_needle(self, parent: Any) -> None:
        """Create speedometer needle."""
        mesh = self._bpy.data.meshes.new("HUD_Speedometer_Needle")
        needle = self._bpy.data.objects.new("HUD_Speedometer_Needle", mesh)

        bm = bmesh.new()

        # Needle shape (arrow)
        r = self.dial_radius * 0.7

        v1 = bm.verts.new((0, -r, 0.02))
        v2 = bm.verts.new((-0.008, -r + 0.02, 0.02))
        v3 = bm.verts.new((0, 0.01, 0.02))
        v4 = bm.verts.new((0.008, -r + 0.02, 0.02))

        bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        needle.parent = parent
        self._bpy.context.collection.objects.link(needle)

        mat = self._create_material(
            "HUD_Speed_Needle",
            (1.0, 0.0, 0.0, 1.0),  # Red needle
            emission=1.0
        )
        needle.data.materials.append(mat)

        self.objects['needle'] = needle

    def _create_digital_display(self, parent: Any) -> None:
        """Create placeholder for digital speed readout."""
        # For now, just create a small box where text would go
        # In full implementation, this would use text objects

        mesh = self._bpy.data.meshes.new("HUD_Speed_Digital")
        digital = self._bpy.data.objects.new("HUD_Speed_Digital", mesh)

        bm = bmesh.new()

        # Small rectangle for digital display
        w, h = 0.04, 0.015

        v1 = bm.verts.new((-w/2, -0.02, 0.03))
        v2 = bm.verts.new((w/2, -0.02, 0.03))
        v3 = bm.verts.new((w/2, -0.02 - h, 0.03))
        v4 = bm.verts.new((-w/2, -0.02 - h, 0.03))

        bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        digital.parent = parent
        self._bpy.context.collection.objects.link(digital)

        mat = self._create_material(
            "HUD_Speed_Digital_BG",
            (0.0, 0.0, 0.0, 0.8),
            emission=0.3
        )
        digital.data.materials.append(mat)

        self.objects['digital'] = digital

    def update(self, telemetry: TelemetryData) -> None:
        """Update speedometer needle."""
        if not self._blender_available:
            return

        needle = self.objects.get('needle')
        if not needle:
            return

        # Calculate angle from speed
        speed = telemetry.speed_kmh
        speed_ratio = min(speed / self.max_speed, 1.0)

        # Angle: 240 degree sweep
        angle_deg = -120 + speed_ratio * 240

        if self.config.animate_needles:
            target = angle_deg
            current = self._animate_value(target)
        else:
            current = angle_deg

        needle.rotation_euler = Euler((0, 0, current * pi / 180), 'XYZ')


class GearWidget(HUDWidget):
    """
    Gear position indicator widget.

    Shows current gear (R, N, 1-6) as large display.
    """

    def __init__(self, config: HUDConfig, position_offset: Tuple[float, float, float] = (0, 0, 0)):
        super().__init__(WidgetType.GEAR, config, position_offset)
        self.current_gear = 1

    def create(self, parent: Optional[Any] = None) -> bool:
        """Create gear indicator."""
        if not self._blender_available:
            return False

        try:
            root_name = "HUD_Gear"
            root = self._bpy.data.objects.new(root_name, None)
            root.empty_display_type = 'ARROWS'

            pos = (
                self.config.position[0] + self.position_offset[0],
                self.config.position[1] + self.position_offset[1],
                self.config.position[2] + self.position_offset[2],
            )
            root.location = pos

            self._bpy.context.collection.objects.link(root)
            self.objects['root'] = root

            # Create background panel
            self._create_background(root)

            # Create gear indicator (will be updated dynamically)
            self._create_gear_display(root)

            if parent:
                root.parent = parent

            return True

        except Exception:
            return False

    def _create_background(self, parent: Any) -> None:
        """Create background panel for gear display."""
        mesh = self._bpy.data.meshes.new("HUD_Gear_BG")
        bg = self._bpy.data.objects.new("HUD_Gear_BG", mesh)

        bm = bmesh.new()

        # Rectangle
        w, h = 0.05, 0.06

        v1 = bm.verts.new((-w/2, h/2, 0))
        v2 = bm.verts.new((w/2, h/2, 0))
        v3 = bm.verts.new((w/2, -h/2, 0))
        v4 = bm.verts.new((-w/2, -h/2, 0))

        bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        bg.parent = parent
        self._bpy.context.collection.objects.link(bg)

        mat = self._create_material(
            "HUD_Gear_BG",
            (0.0, 0.0, 0.0, 0.7),
            emission=0.1
        )
        bg.data.materials.append(mat)

        self.objects['background'] = bg

    def _create_gear_display(self, parent: Any) -> None:
        """Create gear indicator using text or geometry."""
        # For full implementation, would use text objects
        # Here we create a simple indicator

        mesh = self._bpy.data.meshes.new("HUD_Gear_Indicator")
        indicator = self._bpy.data.objects.new("HUD_Gear_Indicator", mesh)

        # Simple block for now
        bm = bmesh.new()

        w, h = 0.035, 0.045

        v1 = bm.verts.new((-w/2, h/2, 0.01))
        v2 = bm.verts.new((w/2, h/2, 0.01))
        v3 = bm.verts.new((w/2, -h/2, 0.01))
        v4 = bm.verts.new((-w/2, -h/2, 0.01))

        bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        indicator.parent = parent
        self._bpy.context.collection.objects.link(indicator)

        mat = self._create_material(
            "HUD_Gear_Indicator",
            self.config.primary_color,
            emission=1.0
        )
        indicator.data.materials.append(mat)

        self.objects['indicator'] = indicator

    def update(self, telemetry: TelemetryData) -> None:
        """Update gear display."""
        # Update gear indicator color based on gear
        indicator = self.objects.get('indicator')
        if not indicator or not indicator.data.materials:
            return

        gear = telemetry.gear

        # Change color based on gear
        if gear == 0:  # Reverse
            color = self.config.danger_color
        elif gear == 1:
            color = self.config.warning_color
        else:
            color = self.config.primary_color

        mat = indicator.data.materials[0]
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = color


class GForceWidget(HUDWidget):
    """
    G-Force meter widget.

    Shows lateral and longitudinal G-forces as a moving dot
    in a circular display.
    """

    def __init__(self, config: HUDConfig, position_offset: Tuple[float, float, float] = (0, 0, 0)):
        super().__init__(WidgetType.GFORCE, config, position_offset)
        self.max_g = 2.0  # G-force display range
        self.display_radius = 0.04

    def create(self, parent: Optional[Any] = None) -> bool:
        """Create G-force meter."""
        if not self._blender_available:
            return False

        try:
            root_name = "HUD_GForce"
            root = self._bpy.data.objects.new(root_name, None)
            root.empty_display_type = 'ARROWS'

            pos = (
                self.config.position[0] + self.position_offset[0],
                self.config.position[1] + self.position_offset[1],
                self.config.position[2] + self.position_offset[2],
            )
            root.location = pos

            self._bpy.context.collection.objects.link(root)
            self.objects['root'] = root

            # Create background circle
            self._create_background(root)

            # Create axis lines
            self._create_axes(root)

            # Create G-force indicator dot
            self._create_indicator(root)

            # Create threshold rings
            self._create_threshold_rings(root)

            if parent:
                root.parent = parent

            return True

        except Exception:
            return False

    def _create_background(self, parent: Any) -> None:
        """Create background circle."""
        mesh = self._bpy.data.meshes.new("HUD_GForce_BG")
        bg = self._bpy.data.objects.new("HUD_GForce_BG", mesh)

        bm = bmesh.new()
        bmesh.ops.create_circle(bm, radius=self.display_radius, segments=32)
        bm.to_mesh(mesh)
        bm.free()

        bg.parent = parent
        self._bpy.context.collection.objects.link(bg)

        mat = self._create_material(
            "HUD_GForce_BG",
            self.config.background_color,
            emission=0.1
        )
        bg.data.materials.append(mat)

        self.objects['background'] = bg

    def _create_axes(self, parent: Any) -> None:
        """Create X and Y axis lines."""
        for axis in ['x', 'y']:
            mesh = self._bpy.data.meshes.new(f"HUD_GForce_Axis_{axis}")
            line = self._bpy.data.objects.new(f"HUD_GForce_Axis_{axis}", mesh)

            bm = bmesh.new()

            r = self.display_radius * 0.9
            thickness = 0.001

            if axis == 'x':
                # Horizontal line
                v1 = bm.verts.new((-r, -thickness, 0.005))
                v2 = bm.verts.new((r, -thickness, 0.005))
                v3 = bm.verts.new((r, thickness, 0.005))
                v4 = bm.verts.new((-r, thickness, 0.005))
            else:
                # Vertical line
                v1 = bm.verts.new((-thickness, -r, 0.005))
                v2 = bm.verts.new((thickness, -r, 0.005))
                v3 = bm.verts.new((thickness, r, 0.005))
                v4 = bm.verts.new((-thickness, r, 0.005))

            bm.faces.new([v1, v2, v3, v4])

            bm.to_mesh(mesh)
            bm.free()

            line.parent = parent
            self._bpy.context.collection.objects.link(line)

            mat = self._create_material(
                f"HUD_GForce_Axis_{axis}",
                (0.3, 0.3, 0.3, 1.0),
                emission=0.3
            )
            line.data.materials.append(mat)

            self.objects[f'axis_{axis}'] = line

    def _create_indicator(self, parent: Any) -> None:
        """Create moving G-force indicator dot."""
        mesh = self._bpy.data.meshes.new("HUD_GForce_Indicator")
        dot = self._bpy.data.objects.new("HUD_GForce_Indicator", mesh)

        bm = bmesh.new()
        bmesh.ops.create_circle(bm, radius=0.005, segments=16)
        bm.to_mesh(mesh)
        bm.free()

        dot.location = (0, 0, 0.01)
        dot.parent = parent
        self._bpy.context.collection.objects.link(dot)

        mat = self._create_material(
            "HUD_GForce_Indicator",
            (1.0, 0.5, 0.0, 1.0),  # Orange
            emission=1.0
        )
        dot.data.materials.append(mat)

        self.objects['indicator'] = dot

    def _create_threshold_rings(self, parent: Any) -> None:
        """Create rings showing G thresholds."""
        for g_threshold, color in [(1.0, self.config.warning_color), (1.5, self.config.danger_color)]:
            radius = (g_threshold / self.max_g) * self.display_radius

            mesh = self._bpy.data.meshes.new(f"HUD_GForce_Ring_{g_threshold}")
            ring = self._bpy.data.objects.new(f"HUD_GForce_Ring_{g_threshold}", mesh)

            bm = bmesh.new()
            bmesh.ops.create_circle(bm, radius=radius, segments=32)
            bm.to_mesh(mesh)
            bm.free()

            ring.parent = parent
            self._bpy.context.collection.objects.link(ring)

            mat = self._create_material(
                f"HUD_GForce_Ring_{g_threshold}",
                (*color[:3], 0.3),
                emission=0.2
            )
            ring.data.materials.append(mat)

            self.objects[f'ring_{g_threshold}'] = ring

    def update(self, telemetry: TelemetryData) -> None:
        """Update G-force indicator position."""
        if not self._blender_available:
            return

        indicator = self.objects.get('indicator')
        if not indicator:
            return

        # Calculate position from G-forces
        gx = telemetry.g_force_x / self.max_g * self.display_radius
        gy = telemetry.g_force_y / self.max_g * self.display_radius

        # Clamp to display
        magnitude = sqrt(gx * gx + gy * gy)
        if magnitude > self.display_radius:
            scale = self.display_radius / magnitude
            gx *= scale
            gy *= scale

        # Animate position
        if self.config.animation_smoothing > 0:
            current_x = indicator.location.x
            current_y = indicator.location.y

            smoothing = self.config.animation_smoothing
            new_x = current_x + (gx - current_x) * smoothing
            new_y = current_y + (gy - current_y) * smoothing

            indicator.location = (new_x, new_y, 0.01)
        else:
            indicator.location = (gx, gy, 0.01)

        # Update color based on G magnitude
        total_g = telemetry.g_force_total
        if total_g > 1.5:
            color = self.config.danger_color
        elif total_g > 1.0:
            color = self.config.warning_color
        else:
            color = self.config.primary_color

        if indicator.data.materials:
            mat = indicator.data.materials[0]
            if mat.use_nodes:
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = color


class HUDSystem:
    """
    Main HUD system that manages all widgets.

    Coordinates telemetry data and distributes to all active widgets.
    """

    def __init__(
        self,
        vehicle_rig: Optional[Any] = None,
        config: Optional[HUDConfig] = None,
    ):
        self.vehicle_rig = vehicle_rig
        self.config = config or HUDConfig()

        self.widgets: Dict[WidgetType, HUDWidget] = {}
        self.telemetry = TelemetryData()

        self._blender_available = BLENDER_AVAILABLE
        self._bpy = bpy

        # Root object for all HUD elements
        self.root: Optional[Any] = None

        # Connected systems
        self._physics_system = None
        self._steering_system = None
        self._vehicle_path_system = None

    def configure(
        self,
        mode: HUDMode = None,
        show_steering: bool = True,
        show_speed: bool = True,
        show_rpm: bool = True,
        show_gear: bool = True,
        show_gforce: bool = False,
        show_heading: bool = False,
        primary_color: Tuple[float, float, float, float] = None,
    ) -> None:
        """Configure HUD settings."""
        if mode:
            self.config.mode = mode

        self.config.show_steering = show_steering
        self.config.show_speed = show_speed
        self.config.show_rpm = show_rpm
        self.config.show_gear = show_gear
        self.config.show_gforce = show_gforce
        self.config.show_heading = show_heading

        if primary_color:
            self.config.primary_color = primary_color

    def create(self) -> bool:
        """Create all HUD widgets."""
        if not self._blender_available:
            return False

        try:
            # Create root object
            root_name = "HUD_System"
            self.root = self._bpy.data.objects.new(root_name, None)
            self.root.empty_display_type = 'ARROWS'
            self._bpy.context.collection.objects.link(self.root)

            # Create widgets based on config
            layout = self._get_layout_positions()

            if self.config.show_steering:
                widget = SteeringWidget(self.config, layout.get('steering', (0, 0, 0)))
                widget.create(self.root)
                self.widgets[WidgetType.STEERING] = widget

            if self.config.show_speed:
                widget = SpeedometerWidget(self.config, layout.get('speedometer', (0, 0, 0)))
                widget.create(self.root)
                self.widgets[WidgetType.SPEEDOMETER] = widget

            if self.config.show_gear:
                widget = GearWidget(self.config, layout.get('gear', (0, 0, 0)))
                widget.create(self.root)
                self.widgets[WidgetType.GEAR] = widget

            if self.config.show_gforce:
                widget = GForceWidget(self.config, layout.get('gforce', (0, 0, 0)))
                widget.create(self.root)
                self.widgets[WidgetType.GFORCE] = widget

            return True

        except Exception:
            return False

    def _get_layout_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """Get widget positions based on HUD mode."""
        if self.config.mode == HUDMode.SCREEN_SPACE:
            # Lower corners and center positions for screen overlay
            return {
                'steering': (-0.15, -0.1, 0),
                'speedometer': (0.15, -0.1, 0),
                'gear': (0.22, -0.1, 0),
                'gforce': (-0.22, -0.1, 0),
                'rpm': (0.0, -0.1, 0),
                'heading': (0.0, 0.12, 0),
            }
        else:
            # Dashboard positions for world space
            return {
                'steering': (-0.3, 0.3, 0.1),
                'speedometer': (0.3, 0.3, 0.1),
                'gear': (0.4, 0.3, 0.1),
                'gforce': (-0.4, 0.3, 0.1),
                'rpm': (0.0, 0.3, 0.1),
                'heading': (0.0, 0.4, 0.1),
            }

    def attach_to_camera(self, camera: Any) -> bool:
        """Attach HUD to camera for screen-space overlay."""
        if not self._blender_available or not self.root:
            return False

        self.root.parent = camera

        # Position in front of camera
        if self.config.mode == HUDMode.SCREEN_SPACE:
            # Position at fixed distance in front of camera
            self.root.location = (0, 0, -1)  # 1 meter in front
            self.root.rotation_euler = (0, 0, 0)

        return True

    def attach_to_vehicle(self) -> bool:
        """Attach HUD to vehicle for dashboard mode."""
        if not self._blender_available or not self.root or not self.vehicle_rig:
            return False

        self.root.parent = self.vehicle_rig

        # Position on dashboard
        self.root.location = (0.5, 0, 1.0)  # Front of vehicle, at dashboard height
        self.root.rotation_euler = (0, 0, 0)

        return True

    def connect_telemetry(
        self,
        physics_system: Any = None,
        steering_system: Any = None,
        vehicle_path_system: Any = None,
    ) -> None:
        """Connect to Launch Control systems for real telemetry."""
        self._physics_system = physics_system
        self._steering_system = steering_system
        self._vehicle_path_system = vehicle_path_system

    def update(self, frame: Optional[int] = None) -> None:
        """
        Update all HUD widgets with current telemetry.

        Should be called every frame for animation.
        """
        # Gather telemetry from connected systems
        self._gather_telemetry()

        # Update all widgets
        for widget in self.widgets.values():
            widget.update(self.telemetry)

    def _gather_telemetry(self) -> None:
        """Gather telemetry from connected systems."""
        # If connected to physics system, get real data
        if self._physics_system:
            # Would extract speed, RPM, gear from physics system
            # This is a placeholder - actual implementation depends on
            # Launch Control's physics system API
            pass

        # If connected to steering system
        if self._steering_system:
            # Would extract steering angle
            pass

        # Otherwise, use placeholder data for testing
        # In real usage, this would be populated from the actual vehicle

    def set_telemetry(self, telemetry: TelemetryData) -> None:
        """Manually set telemetry data."""
        self.telemetry = telemetry

    def set_speed(self, speed_kmh: float) -> None:
        """Set speed telemetry."""
        self.telemetry.speed_kmh = speed_kmh
        self.telemetry.speed = speed_kmh / 3.6  # m/s
        self.telemetry.speed_mph = speed_kmh * 0.621371

    def set_steering(self, angle_deg: float, rotation_deg: float = None) -> None:
        """Set steering telemetry."""
        self.telemetry.steering_angle = angle_deg
        self.telemetry.steering_rotation = rotation_deg if rotation_deg else angle_deg * 15.0

    def set_gear(self, gear: int) -> None:
        """Set gear telemetry."""
        self.telemetry.gear = gear

    def set_gforce(self, gx: float, gy: float, gz: float = 0.0) -> None:
        """Set G-force telemetry."""
        self.telemetry.g_force_x = gx
        self.telemetry.g_force_y = gy
        self.telemetry.g_force_z = gz
        self.telemetry.g_force_total = sqrt(gx*gx + gy*gy + gz*gz)

    def show(self) -> None:
        """Show all HUD elements."""
        if self.root:
            self.root.hide_viewport = False
            self.root.hide_render = False

        for widget in self.widgets.values():
            widget.show()

    def hide(self) -> None:
        """Hide all HUD elements."""
        if self.root:
            self.root.hide_viewport = True
            self.root.hide_render = True

        for widget in self.widgets.values():
            widget.hide()

    def delete(self) -> None:
        """Remove HUD from scene."""
        for widget in self.widgets.values():
            widget.delete()
        self.widgets.clear()

        if self._blender_available and self.root:
            self._bpy.data.objects.remove(self.root, do_unlink=True)
            self.root = None


# === PRESETS ===

HUD_PRESETS = {
    "racing": HUDConfig(
        mode=HUDMode.SCREEN_SPACE,
        show_steering=True,
        show_speed=True,
        show_rpm=True,
        show_gear=True,
        show_gforce=True,
        primary_color=(0.0, 1.0, 0.0, 1.0),  # Green
    ),

    "street": HUDConfig(
        mode=HUDMode.SCREEN_SPACE,
        show_steering=True,
        show_speed=True,
        show_rpm=False,
        show_gear=True,
        show_gforce=False,
        primary_color=(0.0, 0.8, 1.0, 1.0),  # Cyan
    ),

    "minimal": HUDConfig(
        mode=HUDMode.SCREEN_SPACE,
        show_steering=False,
        show_speed=True,
        show_rpm=False,
        show_gear=False,
        show_gforce=False,
        primary_color=(1.0, 1.0, 1.0, 0.8),  # White
    ),

    "dashboard": HUDConfig(
        mode=HUDMode.DASHBOARD,
        show_steering=True,
        show_speed=True,
        show_rpm=True,
        show_gear=True,
        show_gforce=False,
        primary_color=(1.0, 0.3, 0.0, 1.0),  # Orange
    ),

    "stunt": HUDConfig(
        mode=HUDMode.SCREEN_SPACE,
        show_steering=True,
        show_speed=True,
        show_rpm=False,
        show_gear=True,
        show_gforce=True,
        show_heading=True,
        primary_color=(1.0, 0.0, 0.5, 1.0),  # Magenta
    ),
}


# === CONVENIENCE FUNCTIONS ===

def create_vehicle_hud(
    vehicle_rig: Any,
    camera: Any = None,
    preset: str = "racing",
    custom_config: HUDConfig = None,
) -> HUDSystem:
    """
    Convenience function to create a complete vehicle HUD.

    Args:
        vehicle_rig: The vehicle's rig/control object
        camera: Camera for screen-space attachment
        preset: Preset name ("racing", "street", "minimal", "dashboard", "stunt")
        custom_config: Override with custom config

    Returns:
        Configured HUDSystem ready to use
    """
    config = custom_config or HUD_PRESETS.get(preset, HUD_PRESETS["racing"])

    hud = HUDSystem(vehicle_rig, config)
    hud.create()

    if camera and config.mode == HUDMode.SCREEN_SPACE:
        hud.attach_to_camera(camera)
    elif vehicle_rig:
        hud.attach_to_vehicle()

    return hud


def get_hud_presets() -> List[str]:
    """Get list of available HUD presets."""
    return list(HUD_PRESETS.keys())


__all__ = [
    # Core classes
    "HUDSystem",
    "HUDConfig",
    "HUDMode",
    "TelemetryData",

    # Widgets
    "HUDWidget",
    "WidgetType",
    "SteeringWidget",
    "SpeedometerWidget",
    "GearWidget",
    "GForceWidget",

    # Presets
    "HUD_PRESETS",

    # Convenience
    "create_vehicle_hud",
    "get_hud_presets",
]
