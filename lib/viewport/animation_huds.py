"""
Animation & Rigging HUD Widgets

Provides HUD controls for animation and rigging workflows:
- Bone transform controls
- IK/FK blend sliders
- Constraint influence controls
- Pose library picker
- Timeline/scrubbing controls
- Shape key sliders
- Animation layer controls

Usage:
    from lib.viewport.animation_huds import (
        RigHUD,
        BoneHUD,
        IKFKBlendHUD,
        ShapeKeyHUD,
        TimelineHUD,
    )

    # Create rig HUD for armature
    rig_hud = RigHUD("Character")
    rig_hud.setup()
    rig_hud.show()
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
)

# Blender guards
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

if TYPE_CHECKING:
    from bpy.types import Context, Object, PoseBone


# =============================================================================
# THEMES
# =============================================================================

RIG_THEME = WidgetTheme(
    primary=(0.3, 0.8, 1.0, 0.9),
    highlight=(0.5, 0.95, 1.0, 1.0),
    background=(0.08, 0.12, 0.18, 0.9),
)

BONE_THEME = WidgetTheme(
    primary=(0.4, 1.0, 0.6, 0.9),
    highlight=(0.6, 1.0, 0.8, 1.0),
    background=(0.1, 0.15, 0.12, 0.9),
)

IK_THEME = WidgetTheme(
    primary=(1.0, 0.5, 0.2, 0.9),
    highlight=(1.0, 0.7, 0.4, 1.0),
    background=(0.15, 0.1, 0.08, 0.9),
)

FK_THEME = WidgetTheme(
    primary=(0.5, 0.8, 1.0, 0.9),
    highlight=(0.7, 0.9, 1.0, 1.0),
    background=(0.1, 0.12, 0.15, 0.9),
)

SHAPE_KEY_THEME = WidgetTheme(
    primary=(0.9, 0.5, 0.9, 0.9),
    highlight=(1.0, 0.7, 1.0, 1.0),
    background=(0.12, 0.08, 0.12, 0.9),
)

TIMELINE_THEME = WidgetTheme(
    primary=(0.7, 0.7, 0.7, 0.9),
    highlight=(1.0, 1.0, 1.0, 1.0),
    background=(0.12, 0.12, 0.12, 0.9),
)


# =============================================================================
# BONE TRANSFORM HUD
# =============================================================================

class BoneHUD:
    """HUD for controlling a single bone's transforms."""

    def __init__(self, armature_name: str, bone_name: str, x: int = 20, y: int = 200):
        self.armature_name = armature_name
        self.bone_name = bone_name
        self.x = x
        self.y = y
        self.panel_name = f"bone_{armature_name}_{bone_name}"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create bone control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        current_y = self.y

        # Build property paths
        base = f"pose.bones['{self.bone_name}']"

        # Location X
        loc_x = HUDSlider(
            name=f"{self.bone_name}_loc_x",
            label="Loc X",
            target_object=self.armature_name,
            target_property=f"{base}.location[0]",
            min_value=-10.0,
            max_value=10.0,
            format_string="{:.2f}",
            x=self.x,
            y=current_y,
            theme=BONE_THEME,
        )
        hud.add_widget(loc_x, self.panel_name)
        self._widgets.append(loc_x)
        current_y -= 40

        # Location Y
        loc_y = HUDSlider(
            name=f"{self.bone_name}_loc_y",
            label="Loc Y",
            target_object=self.armature_name,
            target_property=f"{base}.location[1]",
            min_value=-10.0,
            max_value=10.0,
            format_string="{:.2f}",
            x=self.x,
            y=current_y,
            theme=BONE_THEME,
        )
        hud.add_widget(loc_y, self.panel_name)
        self._widgets.append(loc_y)
        current_y -= 40

        # Location Z
        loc_z = HUDSlider(
            name=f"{self.bone_name}_loc_z",
            label="Loc Z",
            target_object=self.armature_name,
            target_property=f"{base}.location[2]",
            min_value=-10.0,
            max_value=10.0,
            format_string="{:.2f}",
            x=self.x,
            y=current_y,
            theme=BONE_THEME,
        )
        hud.add_widget(loc_z, self.panel_name)
        self._widgets.append(loc_z)
        current_y -= 45

        # Rotation (Euler) - we'll just show X for simplicity
        rot_x = HUDSlider(
            name=f"{self.bone_name}_rot_x",
            label="Rot X",
            target_object=self.armature_name,
            target_property=f"{base}.rotation_euler[0]",
            min_value=-3.14159,
            max_value=3.14159,
            format_string="{:.0f}°",
            x=self.x,
            y=current_y,
            theme=BONE_THEME,
        )
        hud.add_widget(rot_x, self.panel_name)
        self._widgets.append(rot_x)
        current_y -= 40

        # Scale
        scale = HUDSlider(
            name=f"{self.bone_name}_scale",
            label="Scale",
            target_object=self.armature_name,
            target_property=f"{base}.scale[0]",
            min_value=0.1,
            max_value=5.0,
            format_string="{:.2f}x",
            x=self.x,
            y=current_y,
            theme=BONE_THEME,
        )
        hud.add_widget(scale, self.panel_name)
        self._widgets.append(scale)

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
# IK/FK BLEND HUD
# =============================================================================

class IKFKBlendHUD:
    """HUD for controlling IK/FK blend on a limb."""

    def __init__(self, armature_name: str, x: int = 20, y: int = 200):
        self.armature_name = armature_name
        self.x = x
        self.y = y
        self.panel_name = f"ikfk_{armature_name}"
        self._widgets: List[HUDWidget] = []
        self._ik_chains: Dict[str, Dict] = {}  # Store IK chain info

    def setup(self) -> None:
        """Create IK/FK blend controls."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        # Detect IK chains in armature
        self._detect_ik_chains()

        current_y = self.y

        for chain_name, chain_info in self._ik_chains.items():
            # IK/FK Blend slider
            blend = HUDSlider(
                name=f"{chain_name}_blend",
                label=f"{chain_name} IK/FK",
                target_object=self.armature_name,
                target_property=f"['{chain_info.get('blend_prop', 'ik_fk_blend')}']",
                min_value=0.0,
                max_value=1.0,
                format_string="{:.0%}",
                x=self.x,
                y=current_y,
                theme=IK_THEME,
            )
            hud.add_widget(blend, self.panel_name)
            self._widgets.append(blend)
            current_y -= 45

            # IK Influence
            if chain_info.get('ik_constraint'):
                influence = HUDSlider(
                    name=f"{chain_name}_influence",
                    label="IK Influence",
                    target_object=self.armature_name,
                    target_property=f"pose.bones['{chain_info['tip_bone']}'].constraints['IK'].influence",
                    min_value=0.0,
                    max_value=1.0,
                    format_string="{:.0%}",
                    x=self.x,
                    y=current_y,
                    theme=IK_THEME,
                )
                hud.add_widget(influence, self.panel_name)
                self._widgets.append(influence)
                current_y -= 45

            # Pole angle if pole target exists
            if chain_info.get('pole_target'):
                pole = HUDSlider(
                    name=f"{chain_name}_pole",
                    label="Pole Angle",
                    target_object=self.armature_name,
                    target_property=f"pose.bones['{chain_info['tip_bone']}'].constraints['IK'].pole_angle",
                    min_value=-3.14159,
                    max_value=3.14159,
                    format_string="{:.0f}°",
                    x=self.x,
                    y=current_y,
                    theme=IK_THEME,
                )
                hud.add_widget(pole, self.panel_name)
                self._widgets.append(pole)
                current_y -= 50

    def _detect_ik_chains(self) -> None:
        """Detect IK chains in the armature."""
        if not BLENDER_AVAILABLE:
            return

        obj = bpy.data.objects.get(self.armature_name)
        if not obj or obj.type != "ARMATURE":
            return

        for bone in obj.pose.bones:
            for constraint in bone.constraints:
                if constraint.type == "IK":
                    chain_name = bone.name.replace("_ik", "").replace("_IK", "")
                    self._ik_chains[chain_name] = {
                        "tip_bone": bone.name,
                        "chain_count": constraint.chain_count,
                        "ik_constraint": constraint.name,
                        "target": constraint.target.name if constraint.target else None,
                        "pole_target": constraint.pole_target.name if constraint.pole_target else None,
                    }

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
# CONSTRAINT INFLUENCE HUD
# =============================================================================

class ConstraintHUD:
    """HUD for controlling bone constraint influences."""

    def __init__(self, armature_name: str, x: int = 20, y: int = 200):
        self.armature_name = armature_name
        self.x = x
        self.y = y
        self.panel_name = f"constraints_{armature_name}"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create constraint control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        if not BLENDER_AVAILABLE:
            return

        obj = bpy.data.objects.get(self.armature_name)
        if not obj or obj.type != "ARMATURE":
            return

        current_y = self.y

        for bone in obj.pose.bones:
            for constraint in bone.constraints:
                # Create slider for constraint influence
                slider = HUDSlider(
                    name=f"{bone.name}_{constraint.name}",
                    label=f"{bone.name[:10]}:{constraint.type[:8]}",
                    target_object=self.armature_name,
                    target_property=f"pose.bones['{bone.name}'].constraints['{constraint.name}'].influence",
                    min_value=0.0,
                    max_value=1.0,
                    format_string="{:.0%}",
                    x=self.x,
                    y=current_y,
                    theme=RIG_THEME,
                )
                hud.add_widget(slider, self.panel_name)
                self._widgets.append(slider)
                current_y -= 35

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
# SHAPE KEY HUD
# =============================================================================

class ShapeKeyHUD:
    """HUD for controlling shape keys (morph targets)."""

    def __init__(self, mesh_name: str, x: int = 20, y: int = 200):
        self.mesh_name = mesh_name
        self.x = x
        self.y = y
        self.panel_name = f"shapekeys_{mesh_name}"
        self._widgets: List[HUDWidget] = []
        self._shape_keys: List[str] = []

    def setup(self) -> None:
        """Create shape key control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        if not BLENDER_AVAILABLE:
            return

        obj = bpy.data.objects.get(self.mesh_name)
        if not obj or not obj.data or not hasattr(obj.data, "shape_keys"):
            return

        shape_keys = obj.data.shape_keys
        if not shape_keys:
            return

        current_y = self.y

        for key_block in shape_keys.key_blocks:
            # Skip Basis (first shape key)
            if key_block.name == "Basis":
                continue

            slider = HUDSlider(
                name=f"sk_{key_block.name}",
                label=key_block.name[:15],
                target_object=self.mesh_name,
                target_property=f"data.shape_keys.key_blocks['{key_block.name}'].value",
                min_value=0.0,
                max_value=1.0,
                format_string="{:.0%}",
                x=self.x,
                y=current_y,
                theme=SHAPE_KEY_THEME,
            )
            hud.add_widget(slider, self.panel_name)
            self._widgets.append(slider)
            self._shape_keys.append(key_block.name)
            current_y -= 38

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

    def reset_all(self) -> None:
        """Reset all shape keys to 0."""
        for name in self._shape_keys:
            if BLENDER_AVAILABLE:
                obj = bpy.data.objects.get(self.mesh_name)
                if obj and obj.data and obj.data.shape_keys:
                    key = obj.data.shape_keys.key_blocks.get(name)
                    if key:
                        key.value = 0.0


# =============================================================================
# COMPLETE RIG HUD
# =============================================================================

class RigHUD:
    """Complete HUD for controlling a rig."""

    def __init__(self, armature_name: str, x: int = 20, y: int = 400):
        self.armature_name = armature_name
        self.x = x
        self.y = y
        self._bone_huds: Dict[str, BoneHUD] = {}
        self._ikfk_hud: Optional[IKFKBlendHUD] = None
        self._constraint_hud: Optional[ConstraintHUD] = None
        self._selected_bone: Optional[str] = None

    def setup(self) -> None:
        """Create all rig control widgets."""
        # Create IK/FK HUD
        self._ikfk_hud = IKFKBlendHUD(self.armature_name, x=self.x, y=self.y)
        self._ikfk_hud.setup()

        # Create constraint HUD
        self._constraint_hud = ConstraintHUD(
            self.armature_name,
            x=self.x,
            y=self.y - 200
        )
        self._constraint_hud.setup()

    def show_bone_controls(self, bone_name: str) -> None:
        """Show controls for a specific bone."""
        # Hide previous bone HUD
        if self._selected_bone and self._selected_bone in self._bone_huds:
            self._bone_huds[self._selected_bone].hide()

        # Create/show new bone HUD
        if bone_name not in self._bone_huds:
            hud = BoneHUD(self.armature_name, bone_name, x=self.x + 250, y=self.y)
            hud.setup()
            self._bone_huds[bone_name] = hud

        self._bone_huds[bone_name].show()
        self._selected_bone = bone_name

    def hide_bone_controls(self) -> None:
        """Hide bone controls."""
        if self._selected_bone and self._selected_bone in self._bone_huds:
            self._bone_huds[self._selected_bone].hide()
        self._selected_bone = None

    def show(self) -> None:
        if self._ikfk_hud:
            self._ikfk_hud.show()
        if self._constraint_hud:
            self._constraint_hud.show()

    def hide(self) -> None:
        if self._ikfk_hud:
            self._ikfk_hud.hide()
        if self._constraint_hud:
            self._constraint_hud.hide()
        self.hide_bone_controls()

    def remove(self) -> None:
        if self._ikfk_hud:
            self._ikfk_hud.remove()
        if self._constraint_hud:
            self._constraint_hud.remove()
        for hud in self._bone_huds.values():
            hud.remove()
        self._bone_huds.clear()


# =============================================================================
# TIMELINE HUD
# =============================================================================

class TimelineHUD:
    """HUD for timeline/animation controls."""

    def __init__(self, x: int = 20, y: int = 40):
        self.x = x
        self.y = y
        self.panel_name = "timeline_controls"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create timeline control widgets."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        current_y = self.y

        # Frame slider (requires special handling)
        frame = HUDSlider(
            name="current_frame",
            label="Frame",
            target_object="Scene",
            target_property="frame_current",
            min_value=1,
            max_value=250,
            format_string="{:.0f}",
            x=self.x,
            y=current_y,
            theme=TIMELINE_THEME,
        )
        hud.add_widget(frame, self.panel_name)
        self._widgets.append(frame)
        current_y -= 40

        # Start frame
        start = HUDSlider(
            name="start_frame",
            label="Start",
            target_object="Scene",
            target_property="frame_start",
            min_value=1,
            max_value=1000,
            format_string="{:.0f}",
            x=self.x,
            y=current_y,
            theme=TIMELINE_THEME,
        )
        hud.add_widget(start, self.panel_name)
        self._widgets.append(start)
        current_y -= 40

        # End frame
        end = HUDSlider(
            name="end_frame",
            label="End",
            target_object="Scene",
            target_property="frame_end",
            min_value=1,
            max_value=5000,
            format_string="{:.0f}",
            x=self.x,
            y=current_y,
            theme=TIMELINE_THEME,
        )
        hud.add_widget(end, self.panel_name)
        self._widgets.append(end)

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
# ANIMATION LAYER HUD
# =============================================================================

class AnimationLayerHUD:
    """HUD for controlling animation layers."""

    def __init__(self, x: int = 20, y: int = 100):
        self.x = x
        self.y = y
        self.panel_name = "animation_layers"
        self._widgets: List[HUDWidget] = []

    def setup(self) -> None:
        """Create animation layer controls."""
        hud = HUDManager.get_instance()
        hud.clear_panel(self.panel_name)

        if not BLENDER_AVAILABLE:
            return

        # Get active action's layers (Blender 4.0+ feature)
        # For now, just create toggles for NLA tracks
        obj = bpy.context.active_object
        if not obj or not obj.animation_data:
            return

        current_y = self.y

        for track in obj.animation_data.nla_tracks:
            toggle = HUDToggle(
                name=f"nla_{track.name}",
                label=track.name[:15],
                target_object=obj.name,
                target_property=f"animation_data.nla_tracks['{track.name}'].mute",
                x=self.x,
                y=current_y,
                theme=RIG_THEME,
            )
            hud.add_widget(toggle, self.panel_name)
            self._widgets.append(toggle)
            current_y -= 35

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
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_rig_hud(armature_name: str) -> RigHUD:
    """Create complete HUD for a rig."""
    hud = RigHUD(armature_name)
    hud.setup()
    return hud


def create_shape_key_hud(mesh_name: str) -> ShapeKeyHUD:
    """Create HUD for shape key controls."""
    hud = ShapeKeyHUD(mesh_name)
    hud.setup()
    return hud


def create_ikfk_hud(armature_name: str) -> IKFKBlendHUD:
    """Create HUD for IK/FK blending."""
    hud = IKFKBlendHUD(armature_name)
    hud.setup()
    return hud


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # HUD classes
    "BoneHUD",
    "IKFKBlendHUD",
    "ConstraintHUD",
    "ShapeKeyHUD",
    "RigHUD",
    "TimelineHUD",
    "AnimationLayerHUD",
    # Convenience
    "create_rig_hud",
    "create_shape_key_hud",
    "create_ikfk_hud",
    # Themes
    "RIG_THEME",
    "BONE_THEME",
    "IK_THEME",
    "FK_THEME",
    "SHAPE_KEY_THEME",
    "TIMELINE_THEME",
]
