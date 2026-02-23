"""
Button Element Builder - Geometry Nodes for procedural button generation.

Supports multiple button styles:
- 0: Flat (simple cylinder)
- 1: Domed (spherical cap)
- 2: Concave (depression in center)
- 3: Illuminated (with LED ring/backlight)

All parameters exposed via node group inputs for real-time adjustment.
"""

import bpy
from typing import Tuple
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


class ButtonBuilder:
    """Builds procedural button geometry using Geometry Nodes."""

    def __init__(self, node_group_name: str = "Button_Element"):
        self.tree = bpy.data.node_groups.new(node_group_name, "GeometryNodeTree")
        self.nk = NodeKit(self.tree)
        self.created_nodes = []
        self.frames = {}

        # Build the node group
        self._create_interface()
        go = self.nk.group_output(1800, 0)
        final_geo = self._build_geometry()
        if final_geo:
            self.nk.link(final_geo, go.inputs["Geometry"])

    def _create_interface(self):
        """Create all input sockets for the button."""
        t = self.tree

        # GEOMETRY
        self._float("Diameter", 12.0, 3, 30)       # Button diameter in mm
        self._float("Height", 5.0, 1, 15)          # Unpressed height in mm
        self._float("Travel", 2.0, 0.5, 5)         # Press travel depth in mm
        self._int("Segments", 32, 8, 64)           # Circle segments

        # STYLE
        # 0=Flat, 1=Domed, 2=Concave, 3=Illuminated
        self._int("Style", 1, 0, 3)
        self._float("Dome_Radius", 0.5, 0, 1)      # Dome amount (0=flat, 1=full sphere)
        self._float("Concave_Depth", 1.0, 0, 3)    # Depth of concave depression

        # BEZEL
        self._bool("Bezel_Enabled", True)
        self._float("Bezel_Width", 1.5, 0.5, 5)    # Bezel ring width
        self._float("Bezel_Height", 1.0, 0, 3)     # Bezel height above panel

        # CAP SYSTEM (removable caps like Neve/SSL)
        self._bool("Cap_Enabled", False)
        self._float("Cap_Inset", 0.5, 0, 3)        # How much cap sits inside button
        self._color("Cap_Color", (0.8, 0.2, 0.2))  # Cap color (red default)

        # ILLUMINATION
        self._bool("LED_Enabled", False)
        self._int("LED_Style", 0, 0, 2)            # 0=Ring, 1=Center dot, 2=Full surface
        self._float("LED_Size", 3.0, 1, 10)        # LED element size
        self._color("LED_Color_Off", (0.2, 0.2, 0.2))
        self._color("LED_Color_On", (0.0, 1.0, 0.0))
        self._float("LED_Intensity", 2.0, 0, 10)
        self._bool("LED_State", False)             # Current on/off state

        # MATERIAL
        self._color("Body_Color", (0.15, 0.15, 0.15))
        self._float("Metallic", 0.0, 0, 1)
        self._float("Roughness", 0.4, 0, 1)

        # STATE
        self._float("Press_Amount", 0.0, 0, 1)     # 0=unpressed, 1=fully pressed

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
        """Create a math node."""
        node = self.nk.n("ShaderNodeMath", name or f"Math_{op}", x, y)
        # Map short names to Blender operation names
        op_map = {
            "+": "ADD",
            "-": "SUBTRACT",
            "*": "MULTIPLY",
            "/": "DIVIDE",
        }
        node.operation = op_map.get(op, op)

        # Handle first input - could be socket, node, or value
        if a is not None:
            if isinstance(a, bpy.types.Node):
                self.nk.link(a.outputs[0], node.inputs[0])
            elif isinstance(a, bpy.types.NodeSocket):
                self.nk.link(a, node.inputs[0])
            else:
                node.inputs[0].default_value = a

        # Handle second input - could be socket, node, or value
        if b is not None:
            if isinstance(b, bpy.types.Node):
                self.nk.link(b.outputs[0], node.inputs[1])
            elif isinstance(b, bpy.types.NodeSocket):
                self.nk.link(b, node.inputs[1])
            else:
                node.inputs[1].default_value = b

        self.created_nodes.append(node)
        return node

    def _combine_xyz(self, x, y, z, pos_x: float, pos_y: float, name: str = None):
        """Create a combine XYZ node."""
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

    def _link(self, source, target_input):
        """Helper to link a source (node or socket) to a target input."""
        if isinstance(source, bpy.types.Node):
            self.nk.link(source.outputs[0], target_input)
        else:
            self.nk.link(source, target_input)

    def _build_geometry(self):
        """Build the button geometry with style switching."""
        gi = self.nk.group_input()
        MM = 0.001  # Millimeters to meters

        # Unit conversions
        diameter_m = self._math("*", gi.outputs["Diameter"], MM, 100, 200, "Diameter_M")
        radius_m = self._math("/", diameter_m, 2, 150, 200, "Radius_M")
        height_m = self._math("*", gi.outputs["Height"], MM, 100, 180, "Height_M")
        travel_m = self._math("*", gi.outputs["Travel"], MM, 100, 160, "Travel_M")
        bezel_w_m = self._math("*", gi.outputs["Bezel_Width"], MM, 100, 140, "BezelW_M")

        # Calculate pressed height
        press_offset = self._math("*", travel_m, gi.outputs["Press_Amount"], 200, 180, "PressOffset")
        current_height = self._math("-", height_m, press_offset, 250, 180, "CurrentHeight")

        # Style 0: Flat button (simple cylinder)
        flat = self.nk.n("GeometryNodeMeshCylinder", "Flat_Button", 400, 200)
        self.nk.link(gi.outputs["Segments"], flat.inputs["Vertices"])
        self._link(radius_m, flat.inputs["Radius"])
        self._link(current_height, flat.inputs["Depth"])

        # Style 1: Domed button (UV sphere, half-height)
        domed = self.nk.n("GeometryNodeMeshUVSphere", "Domed_Button", 400, 100)
        self.nk.link(gi.outputs["Segments"], domed.inputs["Segments"])
        self._link(radius_m, domed.inputs["Radius"])
        domed.inputs["Rings"].default_value = 16

        # Scale dome by height
        dome_scale = self.nk.n("GeometryNodeTransform", "Dome_Scale", 500, 100)
        self.nk.link(domed.outputs["Mesh"], dome_scale.inputs["Geometry"])
        dome_scale_z = self._math("*", current_height, gi.outputs["Dome_Radius"], 550, 80, "DomeScaleZ")
        self._link(self._combine_xyz(1, 1, dome_scale_z, 600, 80, "DomeScale"), dome_scale.inputs["Scale"])

        # Style 2: Concave (cylinder with inverted dome on top)
        concave = self.nk.n("GeometryNodeMeshCylinder", "Concave_Button", 400, 0)
        self.nk.link(gi.outputs["Segments"], concave.inputs["Vertices"])
        self._link(radius_m, concave.inputs["Radius"])
        self._link(current_height, concave.inputs["Depth"])

        # Style 3: Illuminated (flat with LED element)
        illuminated = self.nk.n("GeometryNodeMeshCylinder", "Illum_Button", 400, -100)
        self.nk.link(gi.outputs["Segments"], illuminated.inputs["Vertices"])
        self._link(radius_m, illuminated.inputs["Radius"])
        self._link(current_height, illuminated.inputs["Depth"])

        # Style switch
        switch = self.nk.n("GeometryNodeIndexSwitch", "Style_Switch", 600, 100)
        switch.data_type = 'GEOMETRY'
        switch.index_switch_items.new()
        switch.index_switch_items.new()

        self.nk.link(gi.outputs["Style"], switch.inputs["Index"])
        self.nk.link(flat.outputs["Mesh"], switch.inputs[1])
        self.nk.link(dome_scale.outputs["Geometry"], switch.inputs[2])
        self.nk.link(concave.outputs["Mesh"], switch.inputs[3])
        self.nk.link(illuminated.outputs["Mesh"], switch.inputs[4])

        # Add bezel if enabled
        bezel_switch = self.nk.n("GeometryNodeSwitch", "Bezel_Switch", 800, 100)
        bezel_switch.input_type = 'GEOMETRY'
        self.nk.link(gi.outputs["Bezel_Enabled"], bezel_switch.inputs[0])
        self.nk.link(switch.outputs["Output"], bezel_switch.inputs[1])

        # Create bezel ring
        bezel_outer_r = self._math("+", radius_m, bezel_w_m, 700, 50, "BezelOuterR")
        bezel = self.nk.n("GeometryNodeMeshCylinder", "Bezel", 700, 0)
        self.nk.link(gi.outputs["Segments"], bezel.inputs["Vertices"])
        self._link(bezel_outer_r, bezel.inputs["Radius"])
        bezel.inputs["Depth"].default_value = 0.002  # 2mm bezel height

        # Join bezel with button
        join_bezel = self.nk.n("GeometryNodeJoinGeometry", "Join_Bezel", 900, 50)
        self.nk.link(switch.outputs["Output"], join_bezel.inputs["Geometry"])
        self.nk.link(bezel.outputs["Mesh"], join_bezel.inputs["Geometry"])

        self.nk.link(join_bezel.outputs["Geometry"], bezel_switch.inputs[2])

        # Apply material
        mat = self._create_material()
        set_mat = self.nk.n("GeometryNodeSetMaterial", "Set_Material", 1400, 100)
        self.nk.link(bezel_switch.outputs["Output"], set_mat.inputs["Geometry"])
        set_mat.inputs["Material"].default_value = mat

        self.created_nodes.extend([flat, domed, dome_scale, concave, illuminated, switch, bezel_switch, bezel, join_bezel, set_mat])

        return set_mat.outputs["Geometry"]

    def _create_material(self) -> bpy.types.Material:
        """Create button material."""
        mat = bpy.data.materials.new("Button_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes and rebuild
        nodes.clear()

        # Material Output node (required for materials)
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

        # Connect
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        return mat


def create_button_node_group(name: str = "Button_Element") -> bpy.types.NodeTree:
    """Create and return a button element node group."""
    builder = ButtonBuilder(name)
    return builder.tree
