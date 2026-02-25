"""
Geometry Nodes HUD Controls

Heads-up display controls for Geometry Nodes modifiers,
node tree parameters, and procedural modeling controls.

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


# ==================== Geometry Nodes Theme ====================

GEOMETRY_THEME = WidgetTheme(
    primary=(0.4, 0.8, 0.4, 0.9),      # Green - geometry/procedural
    secondary=(0.3, 0.6, 0.3, 0.7),
    text=(1.0, 1.0, 1.0, 1.0),
    background=(0.08, 0.12, 0.08, 0.85),
    highlight=(0.5, 0.9, 0.5, 1.0),
    accent=(0.45, 0.85, 0.45, 1.0),
)

SIMULATION_THEME = WidgetTheme(
    primary=(0.6, 0.4, 0.9, 0.9),      # Purple - simulation
    secondary=(0.45, 0.3, 0.7, 0.7),
    text=(1.0, 1.0, 1.0, 1.0),
    background=(0.1, 0.08, 0.14, 0.85),
    highlight=(0.7, 0.5, 1.0, 1.0),
    accent=(0.65, 0.45, 0.95, 1.0),
)


# ==================== GN Modifier HUD ====================

class GNModifierHUD:
    """
    HUD for Geometry Nodes modifier controls.

    Provides:
    - Auto-detection of GN modifiers on selected object
    - Input socket sliders
    - Toggle for named attributes
    - Reset to defaults
    """

    def __init__(
        self,
        object_name: str = "",
        modifier_name: str = "",
        panel_name: str = "GNModifier",
        position: Tuple[int, int] = (20, 700),
    ):
        self.object_name = object_name
        self.modifier_name = modifier_name
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False
        self._inputs: List[Dict[str, Any]] = []

    def _detect_gn_modifier(self) -> Tuple[str, str]:
        """Detect GN modifier from selected object."""
        try:
            import bpy
            obj = bpy.context.active_object
            if not obj:
                return "", ""

            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group:
                    self.object_name = obj.name
                    self.modifier_name = mod.name
                    return obj.name, mod.name
        except:
            pass
        return "", ""

    def _get_modifier_inputs(self) -> List[Dict[str, Any]]:
        """Get input sockets from the GN modifier."""
        inputs = []
        try:
            import bpy
            obj = bpy.data.objects.get(self.object_name)
            if not obj:
                return []

            mod = obj.modifiers.get(self.modifier_name)
            if not mod or not mod.node_group:
                return []

            # Get interface inputs from the node group
            for item in mod.node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                    # Determine socket type and range
                    socket_type = item.bl_socket_idname
                    min_val, max_val, default_val = self._get_socket_range(socket_type, mod, item.identifier)

                    inputs.append({
                        "identifier": item.identifier,
                        "name": item.name,
                        "type": socket_type,
                        "min": min_val,
                        "max": max_val,
                        "default": default_val,
                    })
        except Exception as e:
            print(f"Error getting GN inputs: {e}")
        return inputs

    def _get_socket_range(self, socket_type: str, mod: Any, identifier: str) -> Tuple[float, float, Any]:
        """Get appropriate range for socket type."""
        try:
            current_val = mod[identifier]
        except:
            current_val = None

        if socket_type in {'NodeSocketFloat', 'NodeSocketFloatAngle', 'NodeSocketFloatPercentage'}:
            return 0.0, 100.0, current_val if current_val is not None else 1.0
        elif socket_type == 'NodeSocketInt':
            return 0, 100, current_val if current_val is not None else 1
        elif socket_type == 'NodeSocketVector':
            return -100.0, 100.0, current_val if current_val is not None else (0, 0, 0)
        elif socket_type == 'NodeSocketBool':
            return 0, 1, current_val if current_val is not None else False
        else:
            return 0.0, 1.0, current_val

    def setup(self) -> None:
        """Create GN modifier control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Auto-detect if not specified
        if not self.object_name:
            self._detect_gn_modifier()

        self._inputs = self._get_modifier_inputs()

        # Panel header
        display_name = self.modifier_name[:14] if self.modifier_name else "No GN Modifier"
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label=f"GN: {display_name}",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=GEOMETRY_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Refresh button
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_refresh",
            label="↻ Refresh Inputs",
            x=x,
            y=y,
            width=95,
            height=widget_height,
            theme=GEOMETRY_THEME,
            on_click=self._refresh,
        ))
        self.widgets.append(f"{self.panel_name}_refresh")

        # Reset button
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_reset",
            label="↺ Reset",
            x=x + 105,
            y=y,
            width=95,
            height=widget_height,
            theme=GEOMETRY_THEME,
            on_click=self._reset_to_defaults,
        ))
        self.widgets.append(f"{self.panel_name}_reset")
        y -= spacing + 5

        # Create sliders for each input
        for i, input_info in enumerate(self._inputs[:12]):  # Limit to 12 inputs
            safe_name = input_info["identifier"].replace(" ", "_")
            input_type = input_info["type"]

            if input_type == 'NodeSocketBool':
                # Boolean - use toggle
                hud.add_widget(HUDToggle(
                    name=f"{self.panel_name}_input_{safe_name}",
                    label=f"{input_info['name'][:12]}",
                    target_object=f"{self.object_name}.modifiers['{self.modifier_name}']",
                    target_property=f"[\"{input_info['identifier']}\"]",
                    x=x,
                    y=y,
                    width=200,
                    height=widget_height,
                    theme=GEOMETRY_THEME,
                ))
            elif input_type == 'NodeSocketVector':
                # Vector - create X, Y, Z sliders
                hud.add_widget(HUDToggle(
                    name=f"{self.panel_name}_vec_{safe_name}",
                    label=f"▶ {input_info['name'][:10]}",
                    target_object="",
                    target_property="",
                    x=x,
                    y=y,
                    width=200,
                    height=widget_height - 4,
                    theme=GEOMETRY_THEME,
                ))
                y -= spacing - 4

                for axis, color in [("X", (1, 0.4, 0.4)), ("Y", (0.4, 1, 0.4)), ("Z", (0.4, 0.6, 1))]:
                    hud.add_widget(HUDSlider(
                        name=f"{self.panel_name}_input_{safe_name}_{axis}",
                        label=f"  {axis}",
                        target_object=f"{self.object_name}.modifiers['{self.modifier_name}']",
                        target_property=f"[\"{input_info['identifier']}\"][{['X', 'Y', 'Z'].index(axis)}]",
                        min_value=input_info["min"],
                        max_value=input_info["max"],
                        default_value=0.0,
                        x=x,
                        y=y,
                        width=200,
                        height=widget_height,
                        theme=WidgetTheme(
                            primary=(*color, 0.9),
                            secondary=(*color, 0.7),
                            text=(1.0, 1.0, 1.0, 1.0),
                            background=(0.08, 0.12, 0.08, 0.85),
                            highlight=(*color, 1.0),
                            accent=(*color, 1.0),
                        ),
                    ))
                    self.widgets.append(f"{self.panel_name}_input_{safe_name}_{axis}")
                    y -= spacing
                continue
            else:
                # Float or Int - use slider
                hud.add_widget(HUDSlider(
                    name=f"{self.panel_name}_input_{safe_name}",
                    label=input_info["name"][:12],
                    target_object=f"{self.object_name}.modifiers['{self.modifier_name}']",
                    target_property=f"[\"{input_info['identifier']}\"]",
                    min_value=input_info["min"],
                    max_value=input_info["max"],
                    default_value=input_info["default"],
                    x=x,
                    y=y,
                    width=200,
                    height=widget_height,
                    theme=GEOMETRY_THEME,
                ))
            self.widgets.append(f"{self.panel_name}_input_{safe_name}")
            y -= spacing

    def _refresh(self) -> None:
        """Refresh the input list."""
        self.teardown()
        self._detect_gn_modifier()
        self.setup()

    def _reset_to_defaults(self) -> None:
        """Reset all inputs to default values."""
        try:
            import bpy
            obj = bpy.data.objects.get(self.object_name)
            if not obj:
                return

            mod = obj.modifiers.get(self.modifier_name)
            if not mod or not mod.node_group:
                return

            # Reset each input to its default
            for item in mod.node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                    if hasattr(item, 'default_value'):
                        try:
                            mod[item.identifier] = item.default_value
                        except:
                            pass
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


# ==================== Simulation HUD ====================

class SimulationHUD:
    """
    HUD for simulation zone controls.

    Provides:
    - Simulation play/pause
    - Reset simulation
    - Frame cache controls
    - Simulation speed
    """

    def __init__(
        self,
        panel_name: str = "Simulation",
        position: Tuple[int, int] = (20, 400),
    ):
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create simulation control widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="SIMULATION",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=SIMULATION_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Simulation controls
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_reset",
            label="⟲ Reset Sim",
            x=x,
            y=y,
            width=95,
            height=widget_height,
            theme=SIMULATION_THEME,
            on_click=self._reset_simulation,
        ))
        self.widgets.append(f"{self.panel_name}_reset")

        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_bake",
            label="▶ Bake",
            x=x + 105,
            y=y,
            width=95,
            height=widget_height,
            theme=SIMULATION_THEME,
            on_click=self._bake_simulation,
        ))
        self.widgets.append(f"{self.panel_name}_bake")
        y -= spacing

        # Simulation speed
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_speed",
            label="Speed",
            target_object="Scene",
            target_property="simulation_speed",
            min_value=0.1,
            max_value=4.0,
            default_value=1.0,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=SIMULATION_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_speed")
        y -= spacing

        # Cache frame range
        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_cache_start",
            label="Cache Start",
            target_object="Scene",
            target_property="frame_start",
            min_value=1,
            max_value=10000,
            default_value=1,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=SIMULATION_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_cache_start")
        y -= spacing

        hud.add_widget(HUDSlider(
            name=f"{self.panel_name}_cache_end",
            label="Cache End",
            target_object="Scene",
            target_property="frame_end",
            min_value=1,
            max_value=10000,
            default_value=250,
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=SIMULATION_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_cache_end")
        y -= spacing

        # Delete cache
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_delete_cache",
            label="🗑 Delete Cache",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=SIMULATION_THEME,
            on_click=self._delete_cache,
        ))
        self.widgets.append(f"{self.panel_name}_delete_cache")

    def _reset_simulation(self) -> None:
        """Reset simulation to frame 1."""
        try:
            import bpy
            bpy.context.scene.frame_set(1)
            # Would trigger simulation reset
        except:
            pass

    def _bake_simulation(self) -> None:
        """Start baking simulation."""
        try:
            import bpy
            bpy.ops.object.geometry_nodes_bake()
        except:
            pass

    def _delete_cache(self) -> None:
        """Delete simulation cache."""
        try:
            import bpy
            bpy.ops.object.geometry_nodes_bake_delete()
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


# ==================== Procedural Parameters HUD ====================

class ProceduralParamsHUD:
    """
    HUD for common procedural modeling parameters.

    Provides commonly used controls:
    - Seed/Randomness
    - Resolution/Subdivision
    - Scale/Size
    - Detail level
    """

    COMMON_PARAMS = [
        ("Seed", 0, 9999, 42),
        ("Resolution", 1, 128, 32),
        ("Scale", 0.01, 100.0, 1.0),
        ("Detail", 0, 10, 4),
        ("Roughness", 0.0, 1.0, 0.5),
        ("Variation", 0.0, 1.0, 0.3),
    ]

    def __init__(
        self,
        target_path: str = "",
        panel_name: str = "Procedural",
        position: Tuple[int, int] = (20, 550),
    ):
        self.target_path = target_path
        self.panel_name = panel_name
        self.position = position
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create procedural parameter widgets."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name=f"{self.panel_name}_header",
            label="PROCEDURAL PARAMS",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=GEOMETRY_THEME,
        ))
        self.widgets.append(f"{self.panel_name}_header")
        y -= spacing

        # Randomize all button
        hud.add_widget(HUDButton(
            name=f"{self.panel_name}_randomize",
            label="🎲 Randomize All",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=GEOMETRY_THEME,
            on_click=self._randomize_all,
        ))
        self.widgets.append(f"{self.panel_name}_randomize")
        y -= spacing + 5

        # Common parameter sliders
        for param_name, min_val, max_val, default in self.COMMON_PARAMS:
            safe_name = param_name.lower().replace(" ", "_")

            hud.add_widget(HUDSlider(
                name=f"{self.panel_name}_param_{safe_name}",
                label=param_name,
                target_object=self.target_path,
                target_property=param_name,
                min_value=min_val,
                max_value=max_val,
                default_value=default,
                x=x,
                y=y,
                width=200,
                height=widget_height,
                theme=GEOMETRY_THEME,
            ))
            self.widgets.append(f"{self.panel_name}_param_{safe_name}")
            y -= spacing

    def _randomize_all(self) -> None:
        """Randomize all parameters."""
        import random
        try:
            import bpy
            if self.target_path:
                # Would set random values for all parameters
                pass
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


# ==================== GN Master HUD ====================

class GNMasterHUD:
    """
    Master Geometry Nodes HUD combining all GN controls.

    Provides unified access to:
    - Modifier controls
    - Simulation controls
    - Procedural parameters
    """

    def __init__(
        self,
        object_name: str = "",
        position: Tuple[int, int] = (20, 900),
    ):
        self.object_name = object_name
        self.position = position
        self._sub_huds: Dict[str, Any] = {}
        self._active_hud: Optional[str] = None
        self.widgets: List[str] = []
        self._visible = False

    def setup(self) -> None:
        """Create the master GN HUD."""
        hud = HUDManager.get_instance()
        x, y = self.position
        widget_height = 24
        spacing = 28

        # Panel header
        hud.add_widget(HUDToggle(
            name="gn_master_header",
            label="GEOMETRY NODES",
            target_object="",
            target_property="",
            x=x,
            y=y,
            width=200,
            height=widget_height,
            theme=GEOMETRY_THEME,
        ))
        self.widgets.append("gn_master_header")
        y -= spacing

        # Category buttons
        categories = [
            ("modifier", "⚙ Modifier"),
            ("sim", "⟳ Sim"),
            ("params", "📊 Params"),
        ]

        for i, (cat_id, cat_label) in enumerate(categories):
            hud.add_widget(HUDButton(
                name=f"gn_cat_{cat_id}",
                label=cat_label,
                x=x + (i * 68),
                y=y,
                width=65,
                height=widget_height,
                theme=GEOMETRY_THEME,
                on_click=lambda cid=cat_id: self._switch_category(cid),
            ))
            self.widgets.append(f"gn_cat_{cat_id}")

        y -= spacing + 10

        # Create sub-HUDs
        self._sub_huds["modifier"] = GNModifierHUD(
            object_name=self.object_name,
            panel_name="gn_mod",
            position=(x, y),
        )
        self._sub_huds["sim"] = SimulationHUD(
            panel_name="gn_sim",
            position=(x, y),
        )
        self._sub_huds["params"] = ProceduralParamsHUD(
            panel_name="gn_params",
            position=(x, y),
        )

        # Show modifier by default
        self._switch_category("modifier")

    def _switch_category(self, category: str) -> None:
        """Switch the active category."""
        for hud in self._sub_huds.values():
            hud.hide()
            hud.teardown()

        if category in self._sub_huds:
            self._sub_huds[category].setup()
            self._sub_huds[category].show()
            self._active_hud = category

    def show(self) -> None:
        self._visible = True

    def hide(self) -> None:
        self._visible = False
        for hud in self._sub_huds.values():
            hud.hide()

    def teardown(self) -> None:
        hud = HUDManager.get_instance()
        for widget_name in self.widgets:
            hud.remove_widget(widget_name)
        self.widgets.clear()

        for sub_hud in self._sub_huds.values():
            sub_hud.teardown()


# ==================== Convenience Functions ====================

def create_gn_modifier_hud(
    object_name: str = "",
    modifier_name: str = "",
    position: Tuple[int, int] = (20, 700),
) -> GNModifierHUD:
    """Create a GN modifier HUD."""
    hud = GNModifierHUD(
        object_name=object_name,
        modifier_name=modifier_name,
        position=position,
    )
    hud.setup()
    return hud


def create_simulation_hud(
    position: Tuple[int, int] = (20, 400),
) -> SimulationHUD:
    """Create a simulation control HUD."""
    hud = SimulationHUD(position=position)
    hud.setup()
    return hud


def create_procedural_params_hud(
    target_path: str = "",
    position: Tuple[int, int] = (20, 550),
) -> ProceduralParamsHUD:
    """Create a procedural parameters HUD."""
    hud = ProceduralParamsHUD(target_path=target_path, position=position)
    hud.setup()
    return hud


def create_gn_master_hud(
    object_name: str = "",
    position: Tuple[int, int] = (20, 900),
) -> GNMasterHUD:
    """Create a master GN HUD with all controls."""
    hud = GNMasterHUD(object_name=object_name, position=position)
    hud.setup()
    return hud
