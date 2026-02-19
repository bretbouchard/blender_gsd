"""
Input Node Group Builder - Organized

Creates a geometry node group with:
1. ALL parameters exposed as inputs
2. Logical frame hierarchy for readability
3. Clean value routing

Frame Structure:
├── GLOBAL INPUTS (input gathering, no frame needed)
├── UNIT CONVERSION (mm → m conversions)
├── POSITION CALC (dynamic Z positions based on heights)
├── ZONE B
│   ├── B_BOT_CAP
│   └── B_MID
├── ZONE A
│   ├── A_MID
│   └── A_TOP_CAP
└── OUTPUT
    └── Join, Merge, Material
"""

from __future__ import annotations
import bpy
import math
from typing import Dict, Any, Optional, Tuple, List

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


class InputNodeGroupBuilder:
    """Builds organized geometry node groups with exposed inputs."""

    def __init__(self):
        self.tree: Optional[bpy.types.NodeTree] = None
        self.nk: Optional[NodeKit] = None
        self.gi: Optional[bpy.types.Node] = None
        self.created_nodes: List[bpy.types.Node] = []
        self.frames: Dict[str, bpy.types.Node] = {}

    def build(self, name: str = "Input_ZoneBased") -> bpy.types.NodeTree:
        """Build the complete node group."""
        if name in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups[name])

        self.tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.nk = NodeKit(self.tree)
        self.nk.clear()
        self.created_nodes = []
        self.frames = {}

        self._create_interface()

        self.gi = self.nk.group_input(0, 0)
        go = self.nk.group_output(2400, 0)

        final_geo = self._build_geometry()

        if final_geo:
            self.nk.link(final_geo, go.inputs["Geometry"])

        return self.tree

    # =========================================================================
    # INTERFACE CREATION
    # =========================================================================

    def _create_interface(self):
        """Create all input sockets."""
        t = self.tree

        # GLOBAL
        self._float("Height_mm", 20.0, 1, 100)
        self._float("Width_mm", 14.0, 1, 100)
        self._int("Segments", 64, 8, 256)

        # ZONE A (TOP)
        self._float("A_Height", 12.0, 0, 50)
        self._float("A_Width_Top", 14.0, 1, 50)
        self._float("A_Width_Bot", 14.0, 1, 50)
        self._float("A_Top_Height", 3.0, 0, 20)
        self._int("A_Top_Style", 2, 0, 2)
        self._float("A_Mid_Height", 6.0, 0, 30)
        self._bool("A_Knurl", False)
        self._int("A_Knurl_Count", 30, 0, 100)
        self._float("A_Knurl_Depth", 0.5, 0, 2)
        self._float("A_Bot_Height", 2.0, 0, 10)  # Default 2mm for transition section

        # ZONE B (BOTTOM)
        self._float("B_Height", 8.0, 0, 50)
        self._float("B_Width_Top", 14.0, 1, 50)
        self._float("B_Width_Bot", 16.0, 1, 50)
        self._float("B_Top_Height", 2.0, 0, 10)  # Default 2mm for transition section
        self._float("B_Mid_Height", 6.0, 0, 30)
        self._bool("B_Knurl", True)
        self._int("B_Knurl_Count", 30, 0, 100)
        self._float("B_Knurl_Depth", 0.5, 0, 2)
        self._float("B_Bot_Height", 2.0, 0, 10)
        self._int("B_Bot_Style", 2, 0, 2)

        # MATERIAL
        self._color("Color", (0.5, 0.5, 0.5))
        self._float("Metallic", 0.0, 0, 1)
        self._float("Roughness", 0.3, 0, 1)

        # DEBUG MODE
        self._bool("Debug_Mode", False)
        self._material("Debug_A_Top_Material")
        self._material("Debug_A_Mid_Material")
        self._material("Debug_A_Bot_Material")
        self._material("Debug_B_Top_Material")
        self._material("Debug_B_Mid_Material")
        self._material("Debug_B_Bot_Material")

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

    def _material(self, name: str, default: bpy.types.Material = None):
        """Create a material input socket."""
        s = self.tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketMaterial")
        s.default_value = default

    # =========================================================================
    # GEOMETRY BUILDING
    # =========================================================================

    def _build_geometry(self):
        """Build geometry with organized frames."""
        gi = self.gi
        MM = 0.001

        # =========================================
        # FRAME: UNIT CONVERSION
        # =========================================
        frame_convert = self._frame("UNIT CONVERSION", 100, 400)

        # Global conversions
        height_m = self._math("*", gi.outputs["Height_mm"], MM, 150, 450, "Height_M")
        width_m = self._math("*", gi.outputs["Width_mm"], MM, 150, 420, "Width_M")

        # Zone A conversions
        a_height_m = self._math("*", gi.outputs["A_Height"], MM, 250, 450, "A_Height_M")
        a_width_top_m = self._math("*", gi.outputs["A_Width_Top"], MM, 250, 420, "A_WidthTop_M")
        a_width_bot_m = self._math("*", gi.outputs["A_Width_Bot"], MM, 250, 390, "A_WidthBot_M")
        a_top_h_m = self._math("*", gi.outputs["A_Top_Height"], MM, 250, 360, "A_TopH_M")
        a_mid_h_m = self._math("*", gi.outputs["A_Mid_Height"], MM, 250, 330, "A_MidH_M")
        a_bot_h_m = self._math("*", gi.outputs["A_Bot_Height"], MM, 250, 300, "A_BotH_M")
        a_knurl_d_m = self._math("*", gi.outputs["A_Knurl_Depth"], MM, 250, 270, "A_KnurlD_M")

        # Zone B conversions
        b_height_m = self._math("*", gi.outputs["B_Height"], MM, 350, 450, "B_Height_M")
        b_width_top_m = self._math("*", gi.outputs["B_Width_Top"], MM, 350, 420, "B_WidthTop_M")
        b_width_bot_m = self._math("*", gi.outputs["B_Width_Bot"], MM, 350, 390, "B_WidthBot_M")
        b_top_h_m = self._math("*", gi.outputs["B_Top_Height"], MM, 350, 360, "B_TopH_M")
        b_mid_h_m = self._math("*", gi.outputs["B_Mid_Height"], MM, 350, 330, "B_MidH_M")
        b_bot_h_m = self._math("*", gi.outputs["B_Bot_Height"], MM, 350, 300, "B_BotH_M")
        b_knurl_d_m = self._math("*", gi.outputs["B_Knurl_Depth"], MM, 350, 270, "B_KnurlD_M")

        # Parent conversion nodes to frame
        self._parent_nodes(self.created_nodes[-14:], frame_convert)

        # =========================================
        # FRAME: POSITION CALCULATIONS
        # =========================================
        # IMPORTANT: Blender 5.0 cones are positioned by their BASE (Z=0 to Z=depth),
        # while cylinders and spheres are centered at origin (Z=-depth/2 to Z=+depth/2).
        # We calculate BASE positions for all sections, then adjust for centered primitives.
        frame_pos = self._frame("POSITION CALC", 450, 400)

        # B_Bot base Z = 0 (bottom of knob)
        # But cylinder is centered, so we translate by: base + depth/2 = 0 + B_Bot_H/2
        b_bot_half = self._math("*", b_bot_h_m, 0.5, 500, 450, "B_Bot_Half")
        b_bot_z = b_bot_half  # Cylinder center = 0 + half

        # B_Mid base Z = B_Bot_H (sits on top of B_Bot)
        # Cone base is at 0, so we translate by: B_Bot_H
        b_mid_z = b_bot_h_m  # Cone base = B_Bot_Height (no need for separate node)

        # B_Top base Z = B_Bot_H + B_Mid_H
        b_bot_plus_mid = self._math("+", b_bot_h_m, b_mid_h_m, 500, 390, "B_Bot+Mid")
        b_top_z = b_bot_plus_mid  # Cone base

        # A_Bot base Z = B_Bot_H + B_Mid_H + B_Top_H
        b_total = self._math("+", b_bot_plus_mid, b_top_h_m, 500, 360, "B_Total")
        a_bot_z = b_total  # Cone base

        # A_Mid base Z = B_Bot_H + B_Mid_H + B_Top_H + A_Bot_H
        b_plus_a_bot = self._math("+", b_total, a_bot_h_m, 500, 330, "B+A_Bot")
        a_mid_z = b_plus_a_bot  # Cone base

        # A_Top base Z = B_Bot_H + B_Mid_H + B_Top_H + A_Bot_H + A_Mid_H
        # But A_Top uses cylinder (centered), so: base + depth/2
        b_plus_a_mid = self._math("+", b_plus_a_bot, a_mid_h_m, 500, 300, "B+A_Mid")
        a_top_half = self._math("*", a_top_h_m, 0.5, 650, 300, "A_Top_Half")
        a_top_z = self._math("+", b_plus_a_mid, a_top_half, 800, 300, "A_Top_Z")

        # Parent position calc nodes to frame
        self._parent_nodes(self.created_nodes[-18:], frame_pos)

        # =========================================
        # FRAME: ZONE B (BOTTOM) - 3 sections
        # =========================================
        frame_b = self._frame("ZONE B", 100, -100)

        # Sub-frame: B_BOT_CAP (cap at bottom)
        frame_b_bot = self._frame("B_BOT_CAP", 150, -200)

        b_bot_radius = self._math("/", b_width_bot_m, 2, 200, -250, "B_Bot_Radius")

        # Build cap with style switching
        b_bot_cap = self._build_cap(
            gi.outputs["B_Bot_Style"],
            b_bot_radius,
            b_bot_h_m,
            gi.outputs["Segments"],
            250, -280, "B_Bot_Cap"
        )

        # Dynamic translation using calculated Z position
        b_bot_pos = self._combine_xyz(0, 0, b_bot_z, 850, -280, "B_Bot_Pos")
        b_bot_xform = self.nk.n("GeometryNodeTransform", "B_Bot_Xform", 1000, -250)
        self.nk.link(b_bot_cap.outputs["Output"], b_bot_xform.inputs["Geometry"])
        self.nk.link(b_bot_pos.outputs["Vector"], b_bot_xform.inputs["Translation"])

        self._parent_nodes([b_bot_cap, b_bot_pos, b_bot_xform], frame_b_bot)

        # Sub-frame: B_MID (cone middle section)
        frame_b_mid = self._frame("B_MID", 150, -400)

        b_mid_radius_top = self._math("/", b_width_top_m, 2, 200, -450, "B_Mid_RadiusTop")
        b_mid_radius_bot = self._math("/", b_width_bot_m, 2, 200, -480, "B_Mid_RadiusBot")

        b_mid_cone = self.nk.n("GeometryNodeMeshCone", "B_Mid_Cone", 300, -460)
        self.nk.link(gi.outputs["Segments"], b_mid_cone.inputs["Vertices"])
        self.nk.link(b_mid_radius_top, b_mid_cone.inputs["Radius Top"])
        self.nk.link(b_mid_radius_bot, b_mid_cone.inputs["Radius Bottom"])
        self.nk.link(b_mid_h_m, b_mid_cone.inputs["Depth"])

        # Apply knurling to B_MID
        b_mid_knurl = self._build_knurling(
            b_mid_cone.outputs["Mesh"],
            gi.outputs["B_Knurl"],
            gi.outputs["B_Knurl_Count"],
            b_knurl_d_m,
            b_mid_radius_bot,  # Use bottom radius as reference
            400, -550, "B_Mid_Knurl"
        )

        # Dynamic translation using calculated Z position
        b_mid_pos = self._combine_xyz(0, 0, b_mid_z, 1150, -490, "B_Mid_Pos")
        b_mid_xform = self.nk.n("GeometryNodeTransform", "B_Mid_Xform", 1300, -460)
        self.nk.link(b_mid_knurl.outputs["Geometry"], b_mid_xform.inputs["Geometry"])
        self.nk.link(b_mid_pos.outputs["Vector"], b_mid_xform.inputs["Translation"])

        self._parent_nodes([b_mid_cone, b_mid_pos, b_mid_xform, b_mid_knurl], frame_b_mid)

        # Sub-frame: B_TOP (cone at top of Zone B)
        frame_b_top = self._frame("B_TOP", 150, -600)

        b_top_radius_bot = self._math("/", b_width_top_m, 2, 200, -650, "B_Top_RadiusBot")
        b_top_radius_top = self._math("/", a_width_bot_m, 2, 200, -680, "B_Top_RadiusTop")  # Use A's bottom width for transition

        b_top_cone = self.nk.n("GeometryNodeMeshCone", "B_Top_Cone", 300, -660)
        self.nk.link(gi.outputs["Segments"], b_top_cone.inputs["Vertices"])
        self.nk.link(b_top_radius_top, b_top_cone.inputs["Radius Top"])
        self.nk.link(b_top_radius_bot, b_top_cone.inputs["Radius Bottom"])
        self.nk.link(b_top_h_m, b_top_cone.inputs["Depth"])

        # Dynamic translation using calculated Z position
        b_top_pos = self._combine_xyz(0, 0, b_top_z, 1150, -690, "B_Top_Pos")
        b_top_xform = self.nk.n("GeometryNodeTransform", "B_Top_Xform", 1300, -660)
        self.nk.link(b_top_cone.outputs["Mesh"], b_top_xform.inputs["Geometry"])
        self.nk.link(b_top_pos.outputs["Vector"], b_top_xform.inputs["Translation"])

        self._parent_nodes([b_top_cone, b_top_pos, b_top_xform], frame_b_top)

        # Parent sub-frames to Zone B frame
        frame_b_bot.parent = frame_b
        frame_b_mid.parent = frame_b
        frame_b_top.parent = frame_b

        # =========================================
        # FRAME: ZONE A (TOP) - 3 sections
        # =========================================
        frame_a = self._frame("ZONE A", 100, 100)

        # Sub-frame: A_BOT (cone at bottom of Zone A)
        frame_a_bot = self._frame("A_BOT", 150, -50)

        # A_Bot is a transition cone from Zone B width to Zone A width
        # Bottom radius = B width (to connect to B_Top)
        # Top radius = A mid radius (to connect to A_Mid)
        a_bot_radius_bot = self._math("/", b_width_top_m, 2, 200, -80, "A_Bot_RadiusBot")  # Use B width
        a_bot_radius_top = self._math("/", a_width_top_m, 2, 200, -110, "A_Bot_RadiusTop")  # Use A top width

        a_bot_cone = self.nk.n("GeometryNodeMeshCone", "A_Bot_Cone", 300, -90)
        self.nk.link(gi.outputs["Segments"], a_bot_cone.inputs["Vertices"])
        self.nk.link(a_bot_radius_top, a_bot_cone.inputs["Radius Top"])
        self.nk.link(a_bot_radius_bot, a_bot_cone.inputs["Radius Bottom"])
        self.nk.link(a_bot_h_m, a_bot_cone.inputs["Depth"])

        # Dynamic translation using calculated Z position
        a_bot_pos = self._combine_xyz(0, 0, a_bot_z, 1150, -120, "A_Bot_Pos")
        a_bot_xform = self.nk.n("GeometryNodeTransform", "A_Bot_Xform", 1300, -90)
        self.nk.link(a_bot_cone.outputs["Mesh"], a_bot_xform.inputs["Geometry"])
        self.nk.link(a_bot_pos.outputs["Vector"], a_bot_xform.inputs["Translation"])

        self._parent_nodes([a_bot_cone, a_bot_pos, a_bot_xform], frame_a_bot)

        # Sub-frame: A_MID (cone middle section)
        frame_a_mid = self._frame("A_MID", 150, 50)

        a_mid_radius_top = self._math("/", a_width_top_m, 2, 200, 20, "A_Mid_RadiusTop")
        a_mid_radius_bot = self._math("/", a_width_bot_m, 2, 200, -10, "A_Mid_RadiusBot")

        a_mid_cone = self.nk.n("GeometryNodeMeshCone", "A_Mid_Cone", 300, 10)
        self.nk.link(gi.outputs["Segments"], a_mid_cone.inputs["Vertices"])
        self.nk.link(a_mid_radius_top, a_mid_cone.inputs["Radius Top"])
        self.nk.link(a_mid_radius_bot, a_mid_cone.inputs["Radius Bottom"])
        self.nk.link(a_mid_h_m, a_mid_cone.inputs["Depth"])

        # Apply knurling to A_MID
        a_mid_knurl = self._build_knurling(
            a_mid_cone.outputs["Mesh"],
            gi.outputs["A_Knurl"],
            gi.outputs["A_Knurl_Count"],
            a_knurl_d_m,
            a_mid_radius_bot,  # Use bottom radius as reference
            400, -80, "A_Mid_Knurl"
        )

        # Dynamic translation using calculated Z position
        a_mid_pos = self._combine_xyz(0, 0, a_mid_z, 1150, -20, "A_Mid_Pos")
        a_mid_xform = self.nk.n("GeometryNodeTransform", "A_Mid_Xform", 1300, 10)
        self.nk.link(a_mid_knurl.outputs["Geometry"], a_mid_xform.inputs["Geometry"])
        self.nk.link(a_mid_pos.outputs["Vector"], a_mid_xform.inputs["Translation"])

        self._parent_nodes([a_mid_cone, a_mid_pos, a_mid_xform, a_mid_knurl], frame_a_mid)

        # Sub-frame: A_TOP_CAP (cap at top)
        frame_a_top = self._frame("A_TOP_CAP", 150, 200)

        a_top_radius = self._math("/", a_width_top_m, 2, 200, 180, "A_Top_Radius")

        # Build cap with style switching
        a_top_cap = self._build_cap(
            gi.outputs["A_Top_Style"],
            a_top_radius,
            a_top_h_m,
            gi.outputs["Segments"],
            250, 150, "A_Top_Cap"
        )

        # Dynamic translation using calculated Z position
        a_top_pos = self._combine_xyz(0, 0, a_top_z, 850, 150, "A_Top_Pos")
        a_top_xform = self.nk.n("GeometryNodeTransform", "A_Top_Xform", 1000, 180)
        self.nk.link(a_top_cap.outputs["Output"], a_top_xform.inputs["Geometry"])
        self.nk.link(a_top_pos.outputs["Vector"], a_top_xform.inputs["Translation"])

        self._parent_nodes([a_top_cap, a_top_pos, a_top_xform], frame_a_top)

        # Parent sub-frames to Zone A frame
        frame_a_bot.parent = frame_a
        frame_a_mid.parent = frame_a
        frame_a_top.parent = frame_a

        # =========================================
        # FRAME: OUTPUT (with per-section materials)
        # =========================================
        frame_output = self._frame("OUTPUT", 600, -100)

        # Create the production material once
        mat = self._create_material()

        # Apply materials to each section BEFORE join (6 sections total)
        # This allows debug mode to show distinct colors per section

        # B_Bot material
        b_bot_set_mat = self._set_section_material(
            b_bot_xform.outputs["Geometry"],
            "B_Bot",
            mat,
            1400, -250
        )

        # B_Mid material
        b_mid_set_mat = self._set_section_material(
            b_mid_xform.outputs["Geometry"],
            "B_Mid",
            mat,
            1400, -460
        )

        # B_Top material
        b_top_set_mat = self._set_section_material(
            b_top_xform.outputs["Geometry"],
            "B_Top",
            mat,
            1400, -660
        )

        # A_Bot material
        a_bot_set_mat = self._set_section_material(
            a_bot_xform.outputs["Geometry"],
            "A_Bot",
            mat,
            1400, -90
        )

        # A_Mid material
        a_mid_set_mat = self._set_section_material(
            a_mid_xform.outputs["Geometry"],
            "A_Mid",
            mat,
            1400, 10
        )

        # A_Top material
        a_top_set_mat = self._set_section_material(
            a_top_xform.outputs["Geometry"],
            "A_Top",
            mat,
            1400, 180
        )

        # Join all 6 sections (now with materials already applied)
        join = self.nk.n("GeometryNodeJoinGeometry", "Join_All", 1650, -50)
        self.nk.link(b_bot_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(b_mid_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(b_top_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(a_bot_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(a_mid_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(a_top_set_mat.outputs["Geometry"], join.inputs["Geometry"])

        # NOTE: Removed MergeByDistance for debug mode to preserve section colors
        # When sections are adjacent with the same radius, MergeByDistance would merge them
        # into a single mesh, losing the per-section material assignments.
        # For production, MergeByDistance can be re-enabled but should be done BEFORE
        # material assignment, not after.

        self._parent_nodes([join], frame_output)

        return join.outputs["Geometry"]

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _math(self, op: str, a, b, x: float, y: float, name: str = "") -> bpy.types.NodeSocket:
        """
        Create a math node and return its output socket.

        NOTE: Blender 5.0's ShaderNodeMath has 3 inputs (all default to 0.5).
        For 2-input operations (MULTIPLY, ADD, etc.), we explicitly clear the
        3rd input to 0.0 to ensure predictable behavior.
        """
        node = self.nk.n("ShaderNodeMath", name or f"Math_{op}", x, y)

        ops = {"*": "MULTIPLY", "/": "DIVIDE", "+": "ADD", "-": "SUBTRACT"}
        node.operation = ops.get(op, op)

        if isinstance(a, bpy.types.NodeSocket):
            self.nk.link(a, node.inputs[0])
        elif isinstance(a, bpy.types.Node):
            self.nk.link(a.outputs[0], node.inputs[0])
        else:
            node.inputs[0].default_value = a

        if isinstance(b, bpy.types.NodeSocket):
            self.nk.link(b, node.inputs[1])
        elif isinstance(b, bpy.types.Node):
            self.nk.link(b.outputs[0], node.inputs[1])
        else:
            node.inputs[1].default_value = b

        # Blender 5.0: Clear 3rd input (default is 0.5, which could affect some operations)
        if len(node.inputs) > 2:
            node.inputs[2].default_value = 0.0

        self.created_nodes.append(node)
        return node.outputs[0]

    def _combine_xyz(self, x, y, z, pos_x: float, pos_y: float, name: str = "") -> bpy.types.Node:
        """Create a Combine XYZ node and return the node (not socket)."""
        node = self.nk.n("ShaderNodeCombineXYZ", name or "CombineXYZ", pos_x, pos_y)

        # Handle X input
        if isinstance(x, bpy.types.NodeSocket):
            self.nk.link(x, node.inputs["X"])
        elif x is not None:
            node.inputs["X"].default_value = x

        # Handle Y input
        if isinstance(y, bpy.types.NodeSocket):
            self.nk.link(y, node.inputs["Y"])
        elif y is not None:
            node.inputs["Y"].default_value = y

        # Handle Z input
        if isinstance(z, bpy.types.NodeSocket):
            self.nk.link(z, node.inputs["Z"])
        elif z is not None:
            node.inputs["Z"].default_value = z

        self.created_nodes.append(node)
        return node

    def _frame(self, label: str, x: float, y: float) -> bpy.types.Node:
        """Create a frame for organization."""
        frame = self.nk.n("NodeFrame", f"Frame_{label}", x, y)
        frame.label = label
        self.frames[label] = frame
        self.created_nodes.append(frame)
        return frame

    def _parent_nodes(self, nodes: list, frame: bpy.types.Node):
        """Parent nodes to a frame."""
        for node in nodes:
            if node and hasattr(node, 'parent'):
                node.parent = frame

    def _build_knurling(
        self,
        geo_socket,
        enable_socket,
        count_socket,
        depth_socket,
        base_radius_socket,
        x: float,
        y: float,
        name_prefix: str
    ) -> bpy.types.Node:
        """
        Build knurling displacement for a geometry.

        Knurling creates ridges by displacing vertices radially based on angle.
        The displacement is purely horizontal (XY plane) to avoid issues with
        cone-shaped geometry.

        Uses: Position → Separate XYZ → Math(arctan2) → Sine → Normalize XY → Multiply by depth
        """
        # Get position
        pos = self.nk.n("GeometryNodeInputPosition", f"{name_prefix}_Pos", x, y)
        sep = self.nk.n("ShaderNodeSeparateXYZ", f"{name_prefix}_SepXYZ", x + 150, y)
        self.nk.link(pos.outputs["Position"], sep.inputs["Vector"])

        # Calculate angle using arctan2(y, x)
        angle = self.nk.n("ShaderNodeMath", f"{name_prefix}_Angle", x + 300, y)
        angle.operation = "ARCTAN2"
        self.nk.link(sep.outputs["Y"], angle.inputs[0])
        self.nk.link(sep.outputs["X"], angle.inputs[1])
        if len(angle.inputs) > 2:
            angle.inputs[2].default_value = 0.0  # Blender 5.0: Clear 3rd input

        # Multiply angle by knurl count to create ridges
        # angle * count * 2 = frequency of ridges
        count_as_float = self.nk.n("ShaderNodeMath", f"{name_prefix}_CountF", x + 450, y + 30)
        count_as_float.operation = "MULTIPLY"
        self.nk.link(count_socket, count_as_float.inputs[0])
        count_as_float.inputs[1].default_value = 2.0  # Double frequency for V-shape
        if len(count_as_float.inputs) > 2:
            count_as_float.inputs[2].default_value = 0.0  # Blender 5.0: Clear 3rd input

        freq = self.nk.n("ShaderNodeMath", f"{name_prefix}_Freq", x + 600, y)
        freq.operation = "MULTIPLY"
        self.nk.link(angle.outputs[0], freq.inputs[0])
        self.nk.link(count_as_float.outputs[0], freq.inputs[1])
        if len(freq.inputs) > 2:
            freq.inputs[2].default_value = 0.0  # Blender 5.0: Clear 3rd input

        # Sine wave for displacement pattern
        sine = self.nk.n("ShaderNodeMath", f"{name_prefix}_Sine", x + 750, y)
        sine.operation = "SINE"
        self.nk.link(freq.outputs[0], sine.inputs[0])
        if len(sine.inputs) > 2:
            sine.inputs[2].default_value = 0.0  # Blender 5.0: Clear 3rd input

        # Scale sine output by depth
        displ = self.nk.n("ShaderNodeMath", f"{name_prefix}_Displ", x + 900, y)
        displ.operation = "MULTIPLY"
        self.nk.link(sine.outputs[0], displ.inputs[0])
        self.nk.link(depth_socket, displ.inputs[1])
        if len(displ.inputs) > 2:
            displ.inputs[2].default_value = 0.0  # Blender 5.0: Clear 3rd input

        # Multiply by enable flag (0 or 1)
        enabled = self.nk.n("ShaderNodeMath", f"{name_prefix}_Enabled", x + 1050, y)
        enabled.operation = "MULTIPLY"
        self.nk.link(displ.outputs[0], enabled.inputs[0])
        # Convert bool to float
        self.nk.link(enable_socket, enabled.inputs[1])
        if len(enabled.inputs) > 2:
            enabled.inputs[2].default_value = 0.0  # Blender 5.0: Clear 3rd input

        # Create horizontal direction vector from X and Y components
        # Normalize the XY position to get radial direction (ignoring Z)
        xy_vec = self.nk.n("ShaderNodeCombineXYZ", f"{name_prefix}_XYVec", x, y - 100)
        self.nk.link(sep.outputs["X"], xy_vec.inputs["X"])
        self.nk.link(sep.outputs["Y"], xy_vec.inputs["Y"])
        xy_vec.inputs["Z"].default_value = 0.0

        # Normalize the XY vector to get pure radial direction
        normalize = self.nk.n("ShaderNodeVectorMath", f"{name_prefix}_Normalize", x + 150, y - 100)
        normalize.operation = "NORMALIZE"
        self.nk.link(xy_vec.outputs["Vector"], normalize.inputs["Vector"])

        # Scale normalized direction by displacement amount
        displace_vec = self.nk.n("ShaderNodeVectorMath", f"{name_prefix}_DispVec", x + 300, y - 100)
        displace_vec.operation = "SCALE"
        self.nk.link(normalize.outputs["Vector"], displace_vec.inputs["Vector"])
        self.nk.link(enabled.outputs[0], displace_vec.inputs["Scale"])

        # Set position to apply knurling
        set_pos = self.nk.n("GeometryNodeSetPosition", f"{name_prefix}_SetPos", x + 500, y - 100)
        self.nk.link(geo_socket, set_pos.inputs["Geometry"])
        self.nk.link(displace_vec.outputs["Vector"], set_pos.inputs["Offset"])

        # Track all knurling nodes
        self.created_nodes.extend([
            pos, sep, angle, count_as_float, freq, sine,
            displ, enabled, xy_vec, normalize, displace_vec, set_pos
        ])

        return set_pos

    def _build_cap(
        self,
        style_socket,
        radius_socket,
        height_socket,
        segments_socket,
        x: float,
        y: float,
        name_prefix: str
    ) -> bpy.types.Node:
        """
        Build a cap with switchable style.

        Styles:
        0: Flat (cylinder)
        1: Beveled (cone with flat top, depth = height, radius_top = radius * 0.8)
        2: Rounded (UV sphere)

        Returns a Switch node that outputs the selected geometry.
        """
        # Style 0: Flat cap (cylinder)
        flat = self.nk.n("GeometryNodeMeshCylinder", f"{name_prefix}_Flat", x, y)
        self.nk.link(segments_socket, flat.inputs["Vertices"])
        self.nk.link(radius_socket, flat.inputs["Radius"])
        self.nk.link(height_socket, flat.inputs["Depth"])

        # Style 1: Beveled cap (cone with reduced top radius)
        bevel = self.nk.n("GeometryNodeMeshCone", f"{name_prefix}_Bevel", x + 180, y)
        self.nk.link(segments_socket, bevel.inputs["Vertices"])
        # Top radius is 80% of bottom for beveled look
        bevel_top_r = self._math("*", radius_socket, 0.8, x + 180, y + 50, f"{name_prefix}_BevelTopR")
        self.nk.link(bevel_top_r, bevel.inputs["Radius Top"])
        self.nk.link(radius_socket, bevel.inputs["Radius Bottom"])
        self.nk.link(height_socket, bevel.inputs["Depth"])

        # Style 2: Rounded cap (UV sphere)
        rounded = self.nk.n("GeometryNodeMeshUVSphere", f"{name_prefix}_Rounded", x + 360, y)
        self.nk.link(segments_socket, rounded.inputs["Segments"])
        self.nk.link(radius_socket, rounded.inputs["Radius"])
        rounded.inputs["Rings"].default_value = 8

        # Create switch nodes for each style option
        # Blender's Index Switch node selects based on integer index
        switch = self.nk.n("GeometryNodeIndexSwitch", f"{name_prefix}_Switch", x + 540, y)
        self.nk.link(style_socket, switch.inputs["Index"])

        # Connect each geometry to its switch input
        self.nk.link(flat.outputs["Mesh"], switch.inputs[0])
        self.nk.link(bevel.outputs["Mesh"], switch.inputs[1])
        self.nk.link(rounded.outputs["Mesh"], switch.inputs[2])

        # Track nodes
        self.created_nodes.extend([flat, bevel, rounded, switch])
        # Also track the bevel_top_r math node that was created
        if bevel_top_r and hasattr(bevel_top_r, 'node'):
            pass  # Already tracked in _math

        return switch

    def _create_material(self) -> bpy.types.Material:
        """Create a simple material."""
        mat = bpy.data.materials.new("Input_Material")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()

        nk = NodeKit(nt)

        bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", -200, 0)
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.3

        out = nk.n("ShaderNodeOutputMaterial", "Output", 0, 0)
        nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

        return mat

    def _create_material_switch(
        self,
        debug_mode_socket,
        debug_mat_socket,
        production_mat: bpy.types.Material,
        x: float,
        y: float,
        name: str
    ) -> bpy.types.Node:
        """
        Create a Switch node to select between debug and production materials.

        Args:
            debug_mode_socket: Boolean socket controlling the switch
            debug_mat_socket: Material socket for debug material
            production_mat: Production material (set as default)
            x: X position in node editor
            y: Y position in node editor
            name: Node name

        Returns:
            The Switch node
        """
        switch = self.nk.n("GeometryNodeSwitch", name, x, y)
        switch.input_type = 'MATERIAL'

        # Connect debug mode boolean to switch selection
        # The "Switch" input is the boolean selector
        self.nk.link(debug_mode_socket, switch.inputs["Switch"])

        # False input = production material
        switch.inputs["False"].default_value = production_mat

        # True input = debug material from input socket
        self.nk.link(debug_mat_socket, switch.inputs["True"])

        self.created_nodes.append(switch)
        return switch

    def _set_section_material(
        self,
        geo_socket,
        section_name: str,
        production_mat: bpy.types.Material,
        x: float,
        y: float
    ) -> bpy.types.Node:
        """
        Apply material to a section.

        NOTE: Due to a Blender 5.0 bug where Switch nodes don't properly evaluate
        boolean inputs from Group Input, we cannot use the debug mode switch.
        For now, we simply apply the production material directly.

        TODO: Re-enable debug mode switching when Blender fixes the Switch node issue.

        Args:
            geo_socket: Geometry socket to apply material to
            section_name: Section name (A_Top, A_Mid, B_Mid, B_Bot)
            production_mat: Production material to use
            x: X position in node editor
            y: Y position in node editor

        Returns:
            The Set Material node
        """
        # Create Set Material node - apply production material directly
        # (Switch node workaround: skip the debug mode switching entirely)
        set_mat = self.nk.n("GeometryNodeSetMaterial", f"Set_{section_name}_Mat", x, y)
        set_mat.inputs["Material"].default_value = production_mat
        self.nk.link(geo_socket, set_mat.inputs["Geometry"])

        self.created_nodes.append(set_mat)
        return set_mat


def create_input_node_group(name: str = "Input_ZoneBased") -> bpy.types.NodeTree:
    """Create the input geometry node group with exposed parameters."""
    builder = InputNodeGroupBuilder()
    return builder.build(name)
