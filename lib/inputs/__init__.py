"""
Console UI Elements - Procedural Geometry Nodes for music console controls.

This package provides procedural element builders following the same methodology:
- All parameters exposed as node group inputs
- Real-time adjustable in Blender UI
- Style switching via index switches
- Material integration

Available Elements:
- Knob: Rotary controls with knurling, multiple profiles
- Button: Momentary/latching buttons with illumination
- Fader: Linear sliders with track and knob
- LED: Single indicators, bars, VU meters, displays
"""

from .node_group_builder import create_input_node_group as create_knob_node_group
from .button_builder import create_button_node_group
from .fader_builder import create_fader_node_group
from .led_builder import create_led_node_group

__all__ = [
    "create_knob_node_group",
    "create_button_node_group",
    "create_fader_node_group",
    "create_led_node_group",
]
