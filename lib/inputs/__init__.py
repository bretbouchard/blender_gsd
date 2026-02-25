"""
Console UI Elements - Procedural Geometry Nodes for music console controls.

This package provides procedural element builders following the same methodology:
- All parameters exposed as node group inputs
- Real-time adjustable in Blender UI
- Style switching via index switches
- Material integration
- Debug material system for visualization

Available Elements:
- Knob: Rotary controls with knurling, multiple profiles
- Button: Momentary/latching buttons with illumination
- Fader: Linear sliders with track and knob
- LED: Single indicators, bars, VU meters, displays
- Panel: Console panels with cutouts and mounting holes
- Enclosure: Equipment enclosures and cases

Debug Materials:
- create_debug_materials: Create per-section debug materials
- create_debug_palette: Get color palette by preset name
- render_debug_view: Render debug visualization
"""

from .node_group_builder import create_input_node_group as create_knob_node_group
from .button_builder import create_button_node_group
from .fader_builder import create_fader_node_group
from .led_builder import create_led_node_group

# Panel and Enclosure builders
from .panel_builder import (
    create_panel_node_group,
    create_panel_with_cutouts_node_group,
    PanelBuilder,
    PanelConfig,
    PanelStyle,
    MountingPattern,
    MountingHoleConfig,
    CutoutConfig,
    create_panel,
)
from .enclosure_builder import (
    create_enclosure_node_group,
    EnclosureBuilder,
    EnclosureConfig,
    EnclosureType,
    PanelType,
    VentilationConfig,
    create_enclosure,
    create_rack_unit,
    RACK_UNIT_HEIGHT,
    RACK_WIDTH,
    RACK_EAR_WIDTH,
)

# Debug materials
from .debug_materials import (
    create_debug_material,
    create_debug_palette,
    create_all_debug_materials,
    get_debug_color,
    DEBUG_COLORS,
    DEBUG_PRESETS,
    SECTION_NAMES,
)

# Debug render utilities
from .debug_render import (
    DebugRenderConfig,
    DebugRenderResult,
    render_debug_view,
    render_all_debug_presets,
    enable_debug_mode_on_object,
)

__all__ = [
    # Element builders
    "create_knob_node_group",
    "create_button_node_group",
    "create_fader_node_group",
    "create_led_node_group",
    # Panel builders
    "create_panel_node_group",
    "create_panel_with_cutouts_node_group",
    "PanelBuilder",
    "PanelConfig",
    "PanelStyle",
    "MountingPattern",
    "MountingHoleConfig",
    "CutoutConfig",
    "create_panel",
    # Enclosure builders
    "create_enclosure_node_group",
    "EnclosureBuilder",
    "EnclosureConfig",
    "EnclosureType",
    "PanelType",
    "VentilationConfig",
    "create_enclosure",
    "create_rack_unit",
    "RACK_UNIT_HEIGHT",
    "RACK_WIDTH",
    "RACK_EAR_WIDTH",
    # Debug materials
    "create_debug_material",
    "create_debug_palette",
    "create_all_debug_materials",
    "get_debug_color",
    "DEBUG_COLORS",
    "DEBUG_PRESETS",
    "SECTION_NAMES",
    # Debug render
    "DebugRenderConfig",
    "DebugRenderResult",
    "render_debug_view",
    "render_all_debug_presets",
    "enable_debug_mode_on_object",
]
