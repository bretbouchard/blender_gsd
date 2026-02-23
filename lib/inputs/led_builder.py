"""
LED/Indicator Element Builder - Geometry Nodes for procedural LED generation.

Supports multiple LED styles:
- 0: Single LED (round or square)
- 1: LED Bar (horizontal or vertical strip)
- 2: VU Meter (analog-style meter with needle - simplified)
- 3: 7-Segment Display (numeric)

All parameters exposed via node group inputs for real-time adjustment.
"""

import bpy
from typing import Tuple
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


class LEDBuilder:
    """Builds procedural LED/indicator geometry using Geometry Nodes."""

    def __init__(self, node_group_name: str = "LED_Element"):
        self.tree = bpy.data.node_groups.new(node_group_name, "GeometryNodeTree")
        self.nk = NodeKit(self.tree)
        self.created_nodes = []
        self.frames = {}

        self._create_interface()
        go = self.nk.group_output(1800, 0)
        final_geo = self._build_geometry()
        if final_geo:
            self.nk.link(final_geo, go.inputs["Geometry"])

    def _create_interface(self):
        """Create all input sockets for the LED."""
        t = self.tree

        # TYPE
        # 0=Single, 1=Bar, 2=VU Meter, 3=7-Segment
        self._int("Type", 0, 0, 3)

        # SINGLE LED
        self._float("Size", 5.0, 2, 15)               # LED diameter/size in mm
        self._int("Shape", 0, 0, 1)                  # 0=Round, 1=Square
        self._float("Height", 2.0, 0.5, 5)           # Height above panel

        # LED BAR
        self._int("Segments", 10, 2, 50)             # Number of segments
        self._float("Segment_Width", 3.0, 1, 8)      # Width of each segment
        self._float("Segment_Height", 8.0, 3, 20)    # Height of each segment
        self._float("Segment_Spacing", 1.0, 0, 4)    # Gap between segments
        self._int("Direction", 0, 0, 1)              # 0=Vertical, 1=Horizontal

        # BEZEL
        self._bool("Bezel_Enabled", True)
        self._float("Bezel_Width", 1.0, 0, 3)        # Bezel ring width
        self._color("Bezel_Color", (0.7, 0.7, 0.7))
        self._int("Bezel_Shape", 0, 0, 2)            # 0=Round, 1=Square, 2=Flanged

        # COLOR SYSTEM
        self._color("Color_Off", (0.1, 0.1, 0.1))    # Off state color
        self._color("Color_On", (0.0, 1.0, 0.0))     # On state color (green)
        self._color("Color_Warning", (1.0, 1.0, 0.0)) # Warning color (yellow)
        self._color("Color_Danger", (1.0, 0.0, 0.0))  # Danger color (red)

        # STATE
        self._float("Value", 0.5, 0, 1)              # Current value (0-1)
        self._bool("State", True)                    # On/Off for single LED
        self._float("Warning_Threshold", 0.7, 0, 1)  # When to show warning color
        self._float("Danger_Threshold", 0.9, 0, 1)   # When to show danger color

        # GLOW
        self._bool("Glow_Enabled", True)
        self._float("Glow_Intensity", 2.0, 0, 10)
        self._float("Glow_Radius", 5.0, 0, 20)

        # MATERIAL PROPERTIES
        self._float("Roughness", 0.2, 0, 1)
        self._float("Transmission", 0.5, 0, 1)       # For LED lens effect

        t.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    def _float(self, name: str, default: float, min: float, max: float):
        s = self.tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = default
        s.min_value = min
        s.max_value = max

    def _int(self, name: str, default: int, min: int, max: int):
        s = self.tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketInt")
        s.default_value = default
        s.min_value = min
        s.max_value = max

    def _bool(self, name: str, default: bool):
        s = self.tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketBool")
        s.default_value = default

    def _color(self, name: str, default: Tuple[float, float, float]):
        s = self.tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketColor")
        s.default_value = (*default, 1.0)

    def _math(self, op: str, a, b, x: float, y: float, name: str = None):
        node = self.nk.n("ShaderNodeMath", name or f"Math_{op}", x, y)
        op_map = {
            "+": "ADD",
            "-": "SUBTRACT",
            "*": "MULTIPLY",
            "/": "DIVIDE",
        }
        node.operation = op_map.get(op, op)

        if a is not None:
            if isinstance(a, bpy.types.Node):
                self.nk.link(a.outputs[0], node.inputs[0])
            elif isinstance(a, bpy.types.NodeSocket):
                self.nk.link(a, node.inputs[0])
            else:
                node.inputs[0].default_value = a

        if b is not None:
            if isinstance(b, bpy.types.Node):
                self.nk.link(b.outputs[0], node.inputs[1])
            elif isinstance(b, bpy.types.NodeSocket):
                self.nk.link(b, node.inputs[1])
            else:
                node.inputs[1].default_value = b

        self.created_nodes.append(node)
        return node

    def _link(self, source, target_input):
        """Helper to link a source (node or socket) to a target input."""
        if isinstance(source, bpy.types.Node):
            self.nk.link(source.outputs[0], target_input)
        else:
            self.nk.link(source, target_input)

    def _combine_xyz(self, x, y, z, pos_x: float, pos_y: float, name: str = None):
        node = self.nk.n("ShaderNodeCombineXYZ", name or "CombineXYZ", pos_x, pos_y)
        for i, val in enumerate([x, y, z]):
            if isinstance(val, bpy.types.Node):
                self.nk.link(val.outputs[0], node.inputs[i])
            elif isinstance(val, bpy.types.NodeSocket):
                self.nk.link(val, node.inputs[i])
            elif val is not None:
                node.inputs[i].default_value = val
        self.created_nodes.append(node)
        return node

    def _build_geometry(self):
        """Build the LED geometry."""
        gi = self.nk.group_input()
        MM = 0.001

        # Unit conversions
        size_m = self._math("*", gi.outputs["Size"], MM, 100, 200, "Size_M")
        height_m = self._math("*", gi.outputs["Height"], MM, 100, 180, "Height_M")
        seg_w_m = self._math("*", gi.outputs["Segment_Width"], MM, 100, 160, "SegW_M")
        seg_h_m = self._math("*", gi.outputs["Segment_Height"], MM, 100, 140, "SegH_M")
        spacing_m = self._math("*", gi.outputs["Segment_Spacing"], MM, 100, 120, "Spacing_M")

        # Type 0: Single LED (cylinder for round, cube for square)
        # Round LED
        round_led = self.nk.n("GeometryNodeMeshCylinder", "Round_LED", 300, 200)
        round_led.inputs["Vertices"].default_value = 16
        self._link(size_m, round_led.inputs["Radius"])
        self._link(height_m, round_led.inputs["Depth"])

        # Square LED - Blender 5.0 MeshCube uses single "Size" vector
        square_led = self.nk.n("GeometryNodeMeshCube", "Square_LED", 300, 150)
        square_size = self._combine_xyz(size_m, size_m, height_m, 350, 150, "SquareSize")
        self._link(square_size, square_led.inputs["Size"])
        square_led.inputs["Vertices X"].default_value = 2
        square_led.inputs["Vertices Y"].default_value = 2
        square_led.inputs["Vertices Z"].default_value = 2

        # Shape switch for single LED
        shape_switch = self.nk.n("GeometryNodeSwitch", "Shape_Switch", 450, 180)
        shape_switch.input_type = 'GEOMETRY'
        self.nk.link(gi.outputs["Shape"], shape_switch.inputs[0])
        self.nk.link(round_led.outputs["Mesh"], shape_switch.inputs[1])
        self.nk.link(square_led.outputs["Mesh"], shape_switch.inputs[2])

        # Type 1: LED Bar (array of segments)
        # Create a grid of segment positions
        # Calculate total bar dimensions
        # For simplicity, create a single elongated shape
        bar_width = self._math("*", seg_w_m, 1, 300, 100, "BarWidth")
        # Total height = segments * height + spacing
        seg_count = gi.outputs["Segments"]
        # Simplified: create a bar representing the lit portion
        led_bar = self.nk.n("GeometryNodeMeshCube", "LED_Bar", 300, 50)
        # Height proportional to value
        bar_height = self._math("*", seg_h_m, gi.outputs["Value"], 350, 50, "BarHeight")
        bar_size = self._combine_xyz(seg_w_m, 0.005, bar_height, 380, 50, "BarSize")
        self._link(bar_size, led_bar.inputs["Size"])
        led_bar.inputs["Vertices X"].default_value = 2
        led_bar.inputs["Vertices Y"].default_value = 2
        led_bar.inputs["Vertices Z"].default_value = 2

        # Type 2 & 3: VU Meter and 7-Segment (simplified as boxes for now)
        vu_meter = self.nk.n("GeometryNodeMeshCube", "VU_Meter", 300, 0)
        vu_meter.inputs["Size"].default_value = (0.025, 0.005, 0.030)
        vu_meter.inputs["Vertices X"].default_value = 2
        vu_meter.inputs["Vertices Y"].default_value = 2
        vu_meter.inputs["Vertices Z"].default_value = 2

        seven_seg = self.nk.n("GeometryNodeMeshCube", "7Segment", 300, -50)
        seven_seg.inputs["Size"].default_value = (0.015, 0.005, 0.025)
        seven_seg.inputs["Vertices X"].default_value = 2
        seven_seg.inputs["Vertices Y"].default_value = 2
        seven_seg.inputs["Vertices Z"].default_value = 2

        # Type switch
        type_switch = self.nk.n("GeometryNodeIndexSwitch", "Type_Switch", 600, 150)
        type_switch.data_type = 'GEOMETRY'
        type_switch.index_switch_items.new()
        type_switch.index_switch_items.new()

        self.nk.link(gi.outputs["Type"], type_switch.inputs["Index"])
        self.nk.link(shape_switch.outputs["Output"], type_switch.inputs[1])  # Single LED
        self.nk.link(led_bar.outputs["Mesh"], type_switch.inputs[2])          # LED Bar
        self.nk.link(vu_meter.outputs["Mesh"], type_switch.inputs[3])         # VU Meter
        self.nk.link(seven_seg.outputs["Mesh"], type_switch.inputs[4])        # 7-Segment

        # Create and apply emissive material
        mat = self._create_material()
        set_mat = self.nk.n("GeometryNodeSetMaterial", "Set_LED_Mat", 1400, 150)
        self.nk.link(type_switch.outputs["Output"], set_mat.inputs["Geometry"])
        set_mat.inputs["Material"].default_value = mat

        self.created_nodes.extend([round_led, square_led, shape_switch, led_bar, vu_meter, seven_seg, type_switch, set_mat])

        return set_mat.outputs["Geometry"]

    def _create_material(self) -> bpy.types.Material:
        """Create emissive LED material."""
        mat = bpy.data.materials.new("LED_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        # Material Output node (required for materials)
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        mix = nodes.new("ShaderNodeMixShader")
        mix.location = (200, 0)

        diffuse = nodes.new("ShaderNodeBsdfDiffuse")
        diffuse.location = (0, 50)

        emission = nodes.new("ShaderNodeEmission")
        emission.location = (0, -50)
        emission.inputs["Strength"].default_value = 2.0

        links.new(diffuse.outputs["BSDF"], mix.inputs[1])
        links.new(emission.outputs["Emission"], mix.inputs[2])
        links.new(mix.outputs["Shader"], output.inputs["Surface"])

        return mat


def create_led_node_group(name: str = "LED_Element") -> bpy.types.NodeTree:
    """Create and return an LED element node group."""
    builder = LEDBuilder(name)
    return builder.tree
