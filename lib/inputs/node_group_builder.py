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
        self._int("Segments", 64, 8, 256)

        # =========================================================================
        # DIAMETERS - Continuous surface by default (each section shares boundaries)
        # =========================================================================
        # Order from top to bottom:
        # Top_Diameter → A_Mid_Top → A_Bot_Top → AB_Junction → B_Mid_Bot → Bot_Diameter
        self._float("Top_Diameter", 14.0, 1, 50)       # A_Top cap top
        self._float("A_Mid_Top_Diameter", 14.0, 1, 50) # A_Mid top (= A_Top bottom)
        self._float("A_Bot_Top_Diameter", 14.0, 1, 50) # A_Bot top (= A_Mid bottom)
        self._float("AB_Junction_Diameter", 14.0, 1, 50) # A_Bot bottom = B_Top top (zone transition)
        self._float("B_Mid_Bot_Diameter", 16.0, 1, 50) # B_Mid bottom (= B_Top bottom, = B_Bot top)
        self._float("Bot_Diameter", 16.0, 1, 50)       # B_Bot cap bottom

        # =========================================================================
        # HEIGHTS - Section heights
        # =========================================================================
        # Zone A (top)
        self._float("A_Top_Height", 3.0, 0, 20)   # Cap height
        self._float("A_Mid_Height", 6.0, 0, 30)   # Middle section
        self._float("A_Bot_Height", 2.0, 0, 10)   # Transition to Zone B

        # Zone B (bottom)
        self._float("B_Top_Height", 2.0, 0, 10)   # Transition from Zone A
        self._float("B_Mid_Height", 6.0, 0, 30)   # Middle section
        self._float("B_Bot_Height", 2.0, 0, 10)   # Cap height

        # =========================================================================
        # STYLES
        # =========================================================================
        # 0=Flat, 1=Beveled, 2=Rounded, 3=Tapered+Skirt (Neve style)
        self._int("A_Top_Style", 2, 0, 3)
        self._int("B_Bot_Style", 2, 0, 3)

        # =========================================================================
        # KNURLING - Per-section control
        # =========================================================================
        # Each section can have independent knurling with its own count and depth
        # A_Mid section (top middle)
        self._bool("A_Mid_Knurl", False)
        self._int("A_Mid_Knurl_Count", 30, 0, 100)
        self._float("A_Mid_Knurl_Depth", 0.5, 0, 2)

        # A_Bot section (zone transition at top)
        self._bool("A_Bot_Knurl", False)
        self._int("A_Bot_Knurl_Count", 30, 0, 100)
        self._float("A_Bot_Knurl_Depth", 0.5, 0, 2)

        # B_Top section (zone transition at bottom)
        self._bool("B_Top_Knurl", False)
        self._int("B_Top_Knurl_Count", 30, 0, 100)
        self._float("B_Top_Knurl_Depth", 0.5, 0, 2)

        # B_Mid section (bottom middle)
        self._bool("B_Mid_Knurl", True)
        self._int("B_Mid_Knurl_Count", 30, 0, 100)
        self._float("B_Mid_Knurl_Depth", 0.5, 0, 2)

        # =========================================================================
        # MATERIAL
        # =========================================================================
        self._color("Color", (0.5, 0.5, 0.5))
        self._float("Metallic", 0.0, 0, 1)
        self._float("Roughness", 0.3, 0, 1)

        # External material input - when provided, overrides procedural material
        # Use this to apply Sanctus or other external materials
        self._material("Material", None)

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
        """
        Build geometry with continuous surface using chained diameters.

        Diameter chain (top to bottom):
        Top_Diameter → A_Mid_Top_Dia → A_Bot_Top_Dia → AB_Junction_Dia → B_Mid_Bot_Dia → Bot_Diameter

        Each section uses a CONE (tapered) so the surface is continuous.
        """
        gi = self.gi
        MM = 0.001

        # =========================================
        # FRAME: UNIT CONVERSION
        # =========================================
        frame_convert = self._frame("UNIT CONVERSION", 100, 400)

        # Diameter conversions (to radius = diameter / 2, then to meters)
        # Top to bottom chain
        top_r_m = self._math("/", self._math("*", gi.outputs["Top_Diameter"], MM, 150, 480, "Top_Dia_M"), 2, 150, 450, "Top_Radius_M")
        a_mid_top_r_m = self._math("/", self._math("*", gi.outputs["A_Mid_Top_Diameter"], MM, 150, 450, "A_MidTop_Dia_M"), 2, 150, 420, "A_MidTop_R_M")
        a_bot_top_r_m = self._math("/", self._math("*", gi.outputs["A_Bot_Top_Diameter"], MM, 150, 420, "A_BotTop_Dia_M"), 2, 150, 390, "A_BotTop_R_M")
        ab_junction_r_m = self._math("/", self._math("*", gi.outputs["AB_Junction_Diameter"], MM, 150, 390, "AB_Junc_Dia_M"), 2, 150, 360, "AB_Junc_R_M")
        b_mid_bot_r_m = self._math("/", self._math("*", gi.outputs["B_Mid_Bot_Diameter"], MM, 150, 360, "B_MidBot_Dia_M"), 2, 150, 330, "B_MidBot_R_M")
        bot_r_m = self._math("/", self._math("*", gi.outputs["Bot_Diameter"], MM, 150, 330, "Bot_Dia_M"), 2, 150, 300, "Bot_Radius_M")

        # Height conversions
        a_top_h_m = self._math("*", gi.outputs["A_Top_Height"], MM, 250, 450, "A_TopH_M")
        a_mid_h_m = self._math("*", gi.outputs["A_Mid_Height"], MM, 250, 420, "A_MidH_M")
        a_bot_h_m = self._math("*", gi.outputs["A_Bot_Height"], MM, 250, 390, "A_BotH_M")
        b_top_h_m = self._math("*", gi.outputs["B_Top_Height"], MM, 250, 360, "B_TopH_M")
        b_mid_h_m = self._math("*", gi.outputs["B_Mid_Height"], MM, 250, 330, "B_MidH_M")
        b_bot_h_m = self._math("*", gi.outputs["B_Bot_Height"], MM, 250, 300, "B_BotH_M")

        # Knurl depth conversions (per-section)
        a_mid_knurl_d_m = self._math("*", gi.outputs["A_Mid_Knurl_Depth"], MM, 250, 270, "A_MidKnurlD_M")
        a_bot_knurl_d_m = self._math("*", gi.outputs["A_Bot_Knurl_Depth"], MM, 250, 240, "A_BotKnurlD_M")
        b_top_knurl_d_m = self._math("*", gi.outputs["B_Top_Knurl_Depth"], MM, 250, 210, "B_TopKnurlD_M")
        b_mid_knurl_d_m = self._math("*", gi.outputs["B_Mid_Knurl_Depth"], MM, 250, 180, "B_MidKnurlD_M")

        # Parent conversion nodes to frame
        self._parent_nodes(self.created_nodes[-22:], frame_convert)

        # =========================================
        # FRAME: POSITION CALCULATIONS
        # =========================================
        # All sections use cones positioned by BASE at Z=0
        # Stack from bottom (Z=0) to top
        frame_pos = self._frame("POSITION CALC", 450, 400)

        # B_Bot base Z = 0 (cone base at bottom)
        b_bot_z = 0  # No node needed for 0

        # B_Mid base Z = B_Bot_H
        b_mid_z_node = b_bot_h_m  # Use the height directly (cone base position)

        # B_Top base Z = B_Bot_H + B_Mid_H
        b_bot_plus_mid = self._math("+", b_bot_h_m, b_mid_h_m, 500, 390, "B_Bot+Mid")

        # A_Bot base Z = B_Bot_H + B_Mid_H + B_Top_H
        b_total = self._math("+", b_bot_plus_mid, b_top_h_m, 500, 360, "B_Total")

        # A_Mid base Z = B_Total + A_Bot_H
        b_plus_a_bot = self._math("+", b_total, a_bot_h_m, 500, 330, "B+A_Bot")

        # A_Top base Z = B_Total + A_Bot_H + A_Mid_H (but cap uses centered geometry)
        b_plus_a_mid = self._math("+", b_plus_a_bot, a_mid_h_m, 500, 300, "B+A_Mid")
        a_top_half = self._math("*", a_top_h_m, 0.5, 650, 300, "A_Top_Half")
        a_top_z = self._math("+", b_plus_a_mid, a_top_half, 800, 300, "A_Top_Z")

        # Parent position calc nodes to frame
        self._parent_nodes(self.created_nodes[-7:], frame_pos)

        # =========================================
        # FRAME: ZONE B (BOTTOM) - 3 sections
        # =========================================
        frame_b = self._frame("ZONE B", 100, -100)

        # --- B_Bot cap ---
        # Bottom radius = Bot_Diameter (connects to nothing, it's the base)
        # Top radius = B_Mid_Bot_Diameter (connects to B_Mid)
        frame_b_bot = self._frame("B_BOT_CAP", 150, -200)

        b_bot_cap = self._build_cap(
            gi.outputs["B_Bot_Style"],
            bot_r_m,         # Top radius (outer tip of cap)
            b_mid_bot_r_m,   # Bottom radius (connects to B_Mid)
            b_bot_h_m,
            gi.outputs["Segments"],
            250, -280, "B_Bot_Cap"
        )

        # Cap geometry is centered, so position at: base + height/2
        b_bot_center_z = self._math("*", b_bot_h_m, 0.5, 850, -280, "B_Bot_CenterZ")
        b_bot_pos = self._combine_xyz(0, 0, b_bot_center_z, 900, -280, "B_Bot_Pos")
        b_bot_xform = self.nk.n("GeometryNodeTransform", "B_Bot_Xform", 1000, -250)
        self.nk.link(b_bot_cap.outputs["Output"], b_bot_xform.inputs["Geometry"])
        self.nk.link(b_bot_pos.outputs["Vector"], b_bot_xform.inputs["Translation"])

        self._parent_nodes([b_bot_cap, b_bot_pos, b_bot_xform], frame_b_bot)

        # --- B_Mid cone ---
        # Top radius = B_Mid_Bot (shared with B_Top bottom), Bottom radius = B_Mid_Bot
        # Since B_Mid is flat (cylinder), use same radius top and bottom
        frame_b_mid = self._frame("B_MID", 150, -400)

        b_mid_cone = self.nk.n("GeometryNodeMeshCone", "B_Mid_Cone", 300, -460)
        self.nk.link(gi.outputs["Segments"], b_mid_cone.inputs["Vertices"])
        self.nk.link(b_mid_bot_r_m, b_mid_cone.inputs["Radius Top"])     # Top = B_Mid_Bot
        self.nk.link(b_mid_bot_r_m, b_mid_cone.inputs["Radius Bottom"])  # Bot = B_Mid_Bot (flat)
        self.nk.link(b_mid_h_m, b_mid_cone.inputs["Depth"])

        # Knurling
        b_mid_knurl = self._build_knurling(
            b_mid_cone.outputs["Mesh"],
            gi.outputs["B_Mid_Knurl"],
            gi.outputs["B_Mid_Knurl_Count"],
            b_mid_knurl_d_m,
            b_mid_bot_r_m,
            b_mid_h_m,  # Section height for cutter
            400, -550, "B_Mid_Knurl"
        )

        # Cone base at b_mid_z_node
        b_mid_pos = self._combine_xyz(0, 0, b_mid_z_node, 1150, -490, "B_Mid_Pos")
        b_mid_xform = self.nk.n("GeometryNodeTransform", "B_Mid_Xform", 1300, -460)
        self.nk.link(b_mid_knurl.outputs[0], b_mid_xform.inputs["Geometry"])
        self.nk.link(b_mid_pos.outputs["Vector"], b_mid_xform.inputs["Translation"])

        self._parent_nodes([b_mid_cone, b_mid_pos, b_mid_xform, b_mid_knurl], frame_b_mid)

        # --- B_Top cone ---
        # Top radius = AB_Junction, Bottom radius = B_Mid_Bot
        frame_b_top = self._frame("B_TOP", 150, -600)

        b_top_cone = self.nk.n("GeometryNodeMeshCone", "B_Top_Cone", 300, -660)
        self.nk.link(gi.outputs["Segments"], b_top_cone.inputs["Vertices"])
        self.nk.link(ab_junction_r_m, b_top_cone.inputs["Radius Top"])    # Top = AB_Junction
        self.nk.link(b_mid_bot_r_m, b_top_cone.inputs["Radius Bottom"])   # Bot = B_Mid_Bot
        self.nk.link(b_top_h_m, b_top_cone.inputs["Depth"])

        # Knurling
        b_top_knurl = self._build_knurling(
            b_top_cone.outputs["Mesh"],
            gi.outputs["B_Top_Knurl"],
            gi.outputs["B_Top_Knurl_Count"],
            b_top_knurl_d_m,
            ab_junction_r_m,  # Use top radius as reference
            b_top_h_m,  # Section height for cutter
            400, -750, "B_Top_Knurl"
        )

        # Cone base at b_bot_plus_mid
        b_top_pos = self._combine_xyz(0, 0, b_bot_plus_mid, 1150, -690, "B_Top_Pos")
        b_top_xform = self.nk.n("GeometryNodeTransform", "B_Top_Xform", 1300, -660)
        self.nk.link(b_top_knurl.outputs[0], b_top_xform.inputs["Geometry"])
        self.nk.link(b_top_pos.outputs["Vector"], b_top_xform.inputs["Translation"])

        self._parent_nodes([b_top_cone, b_top_pos, b_top_xform, b_top_knurl], frame_b_top)

        # Parent sub-frames to Zone B
        frame_b_bot.parent = frame_b
        frame_b_mid.parent = frame_b
        frame_b_top.parent = frame_b

        # =========================================
        # FRAME: ZONE A (TOP) - 3 sections
        # =========================================
        frame_a = self._frame("ZONE A", 100, 100)

        # --- A_Bot cone ---
        # Top radius = A_Bot_Top, Bottom radius = AB_Junction
        frame_a_bot = self._frame("A_BOT", 150, -50)

        a_bot_cone = self.nk.n("GeometryNodeMeshCone", "A_Bot_Cone", 300, -90)
        self.nk.link(gi.outputs["Segments"], a_bot_cone.inputs["Vertices"])
        self.nk.link(a_bot_top_r_m, a_bot_cone.inputs["Radius Top"])      # Top = A_Bot_Top
        self.nk.link(ab_junction_r_m, a_bot_cone.inputs["Radius Bottom"]) # Bot = AB_Junction
        self.nk.link(a_bot_h_m, a_bot_cone.inputs["Depth"])

        # Knurling
        a_bot_knurl = self._build_knurling(
            a_bot_cone.outputs["Mesh"],
            gi.outputs["A_Bot_Knurl"],
            gi.outputs["A_Bot_Knurl_Count"],
            a_bot_knurl_d_m,
            a_bot_top_r_m,  # Use top radius as reference
            a_bot_h_m,  # Section height for cutter
            400, -180, "A_Bot_Knurl"
        )

        # Cone base at b_total
        a_bot_pos = self._combine_xyz(0, 0, b_total, 1150, -120, "A_Bot_Pos")
        a_bot_xform = self.nk.n("GeometryNodeTransform", "A_Bot_Xform", 1300, -90)
        self.nk.link(a_bot_knurl.outputs[0], a_bot_xform.inputs["Geometry"])
        self.nk.link(a_bot_pos.outputs["Vector"], a_bot_xform.inputs["Translation"])

        self._parent_nodes([a_bot_cone, a_bot_pos, a_bot_xform, a_bot_knurl], frame_a_bot)

        # --- A_Mid cone ---
        # Top radius = A_Mid_Top, Bottom radius = A_Bot_Top
        frame_a_mid = self._frame("A_MID", 150, 50)

        a_mid_cone = self.nk.n("GeometryNodeMeshCone", "A_Mid_Cone", 300, 10)
        self.nk.link(gi.outputs["Segments"], a_mid_cone.inputs["Vertices"])
        self.nk.link(a_mid_top_r_m, a_mid_cone.inputs["Radius Top"])      # Top = A_Mid_Top
        self.nk.link(a_bot_top_r_m, a_mid_cone.inputs["Radius Bottom"])   # Bot = A_Bot_Top
        self.nk.link(a_mid_h_m, a_mid_cone.inputs["Depth"])

        # Knurling
        a_mid_knurl = self._build_knurling(
            a_mid_cone.outputs["Mesh"],
            gi.outputs["A_Mid_Knurl"],
            gi.outputs["A_Mid_Knurl_Count"],
            a_mid_knurl_d_m,
            a_mid_top_r_m,
            a_mid_h_m,  # Section height for cutter
            400, -80, "A_Mid_Knurl"
        )

        # Cone base at b_plus_a_bot
        a_mid_pos = self._combine_xyz(0, 0, b_plus_a_bot, 1150, -20, "A_Mid_Pos")
        a_mid_xform = self.nk.n("GeometryNodeTransform", "A_Mid_Xform", 1300, 10)
        self.nk.link(a_mid_knurl.outputs[0], a_mid_xform.inputs["Geometry"])
        self.nk.link(a_mid_pos.outputs["Vector"], a_mid_xform.inputs["Translation"])

        self._parent_nodes([a_mid_cone, a_mid_pos, a_mid_xform, a_mid_knurl], frame_a_mid)

        # --- A_Top cap ---
        # Top radius = Top_Diameter (outer tip of cap)
        # Bottom radius = A_Mid_Top_Diameter (connects to A_Mid)
        frame_a_top = self._frame("A_TOP_CAP", 150, 200)

        a_top_cap = self._build_cap(
            gi.outputs["A_Top_Style"],
            top_r_m,         # Top radius (outer tip)
            a_mid_top_r_m,   # Bottom radius (connects to A_Mid)
            a_top_h_m,
            gi.outputs["Segments"],
            250, 150, "A_Top_Cap"
        )

        # Cap is centered, position at a_top_z
        a_top_pos = self._combine_xyz(0, 0, a_top_z, 850, 150, "A_Top_Pos")
        a_top_xform = self.nk.n("GeometryNodeTransform", "A_Top_Xform", 1000, 180)
        self.nk.link(a_top_cap.outputs["Output"], a_top_xform.inputs["Geometry"])
        self.nk.link(a_top_pos.outputs["Vector"], a_top_xform.inputs["Translation"])

        self._parent_nodes([a_top_cap, a_top_pos, a_top_xform], frame_a_top)

        # Parent sub-frames to Zone A
        frame_a_bot.parent = frame_a
        frame_a_mid.parent = frame_a
        frame_a_top.parent = frame_a

        # =========================================
        # FRAME: OUTPUT (with per-section materials)
        # =========================================
        frame_output = self._frame("OUTPUT", 600, -100)

        # Create the production material
        mat = self._create_material()

        # Apply materials to each section
        b_bot_set_mat = self._set_section_material(b_bot_xform.outputs["Geometry"], "B_Bot", mat, 1400, -250)
        b_mid_set_mat = self._set_section_material(b_mid_xform.outputs["Geometry"], "B_Mid", mat, 1400, -460)
        b_top_set_mat = self._set_section_material(b_top_xform.outputs["Geometry"], "B_Top", mat, 1400, -660)
        a_bot_set_mat = self._set_section_material(a_bot_xform.outputs["Geometry"], "A_Bot", mat, 1400, -90)
        a_mid_set_mat = self._set_section_material(a_mid_xform.outputs["Geometry"], "A_Mid", mat, 1400, 10)
        a_top_set_mat = self._set_section_material(a_top_xform.outputs["Geometry"], "A_Top", mat, 1400, 180)

        # Join all 6 sections
        join = self.nk.n("GeometryNodeJoinGeometry", "Join_All", 1650, -50)
        self.nk.link(b_bot_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(b_mid_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(b_top_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(a_bot_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(a_mid_set_mat.outputs["Geometry"], join.inputs["Geometry"])
        self.nk.link(a_top_set_mat.outputs["Geometry"], join.inputs["Geometry"])

        # Recalculate normals on the joined geometry to ensure consistent shading
        # Boolean operations on any section can affect overall mesh normals
        join_normals = self.nk.n("GeometryNodeSetMeshNormal", "Join_RecalcNormals", 1800, -50)
        join_normals.inputs["Remove Custom"].default_value = True
        self.nk.link(join.outputs["Geometry"], join_normals.inputs["Mesh"])

        self._parent_nodes([join, join_normals], frame_output)

        return join_normals.outputs[0]

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
        height_socket,
        x: float,
        y: float,
        name_prefix: str
    ) -> bpy.types.Node:
        """
        Build knurling using boolean subtraction with groove cutters.

        Creates actual geometric grooves by:
        1. Generating a grid of thin wedge cutters around the circumference
        2. Using Mesh Boolean (Difference) to carve grooves into the cylinder

        This approach:
        - Works with ANY knurl count (not tied to segments)
        - Can be extended for angled/helical knurling
        - Creates real geometric grooves for actual grip texture

        Args:
            geo_socket: The cylinder geometry to knurl
            enable_socket: Boolean to enable/disable knurling
            count_socket: Number of grooves around circumference
            depth_socket: How deep each groove cuts (in mm, converted)
            base_radius_socket: Radius of the cylinder (for positioning cutters)
            height_socket: Height of the section (for cutter height)
            x, y: Node positions
            name_prefix: Name prefix for nodes
        """
        # ========================================
        # GROOVE CUTTER GEOMETRY
        # ========================================
        # Create a thin rectangular cutter that will be instanced around the cylinder
        # The cutter is a thin box positioned to cut into the surface

        # Groove width: determined by count - more grooves = narrower
        # Circumference = 2 * pi * radius, so width ≈ circumference / count
        # But we want grooves to be visible, so make them a bit wider
        # Use depth as a proxy for groove width too (deeper = wider for V-shape)

        # Create a single groove cutter (thin cube)
        # Width = small fraction of circumference
        # Depth = depth_socket (how deep it cuts)
        # Height = section height (full height of the section)

        # For the cutter box:
        # - Position it so its inner face is at radius - depth
        # - Its outer face extends beyond radius to ensure intersection
        # - Width is narrow (based on count)

        # Calculate groove width as fraction of circumference
        # For 32 grooves on a 14mm diameter (7mm radius), circumference = 2*pi*7 ≈ 44mm
        # Each groove occupies 44/32 ≈ 1.4mm of arc, but the actual groove is narrower
        # Use depth as groove width too for simplicity (V-shaped grooves)

        # Cutter dimensions (in meters, since we're working in m)
        # Width: Use a reasonable default - grooves are typically 0.5-1mm wide
        # We'll use depth as width too

        # Use a simple Cube primitive (1m cube) and scale it to groove dimensions
        # GeometryNodeMeshCube creates a 1m cube centered at origin

        cutter_cube = self.nk.n("GeometryNodeMeshCube", f"{name_prefix}_Cube", x, y)
        # MeshCube in Blender 5.0 has: Vertices X, Vertices Y, Vertices Z, Size X, Size Y, Size Z
        # But the input names might be different - let's check what exists
        # Default is a 1m cube, we'll scale it via transform

        # Scale the cube to groove dimensions
        # X = groove_width, Y = depth * 2, Z = height
        cutter_scale = self._combine_xyz(
            depth_socket,  # Width = depth
            self._math("*", depth_socket, 2, x + 100, y + 50, f"{name_prefix}_Depth2"),
            height_socket,
            x + 200, y, f"{name_prefix}_Scale"
        )

        cutter_xform_inner = self.nk.n("GeometryNodeTransform", f"{name_prefix}_CutterScale", x + 350, y)
        self.nk.link(cutter_cube.outputs["Mesh"], cutter_xform_inner.inputs["Geometry"])
        self.nk.link(cutter_scale.outputs["Vector"], cutter_xform_inner.inputs["Scale"])

        # ========================================
        # INSTANCE CUTTERS AROUND CIRCUMFERENCE
        # ========================================
        # Use Points on Circle + Instance on Points approach

        # Create a circle mesh with 'count' vertices
        circle = self.nk.n("GeometryNodeMeshCircle", f"{name_prefix}_Circle", x, y - 150)
        self.nk.link(count_socket, circle.inputs["Vertices"])
        self.nk.link(base_radius_socket, circle.inputs["Radius"])

        # Instance the cutter on each circle vertex, rotated to face center
        # The cutter should face inward (toward center) to cut grooves
        instance_on_points = self.nk.n("GeometryNodeInstanceOnPoints", f"{name_prefix}_Instance", x + 500, y - 150)
        self.nk.link(circle.outputs["Mesh"], instance_on_points.inputs["Points"])
        self.nk.link(cutter_xform_inner.outputs["Geometry"], instance_on_points.inputs["Instance"])

        # Rotation: Each point needs to rotate the cutter to face the center
        # For a point on a circle at angle theta, we want the cutter to face inward
        # Rotation around Z axis = theta + pi/2 (to face center)

        # Get rotation from the point position's angle
        pos = self.nk.n("GeometryNodeInputPosition", f"{name_prefix}_Pos", x + 500, y - 200)
        sep = self.nk.n("ShaderNodeSeparateXYZ", f"{name_prefix}_SepPos", x + 650, y - 200)
        self.nk.link(pos.outputs["Position"], sep.inputs["Vector"])

        # Calculate angle using arctan2
        angle = self.nk.n("ShaderNodeMath", f"{name_prefix}_Angle", x + 800, y - 200)
        angle.operation = "ARCTAN2"
        self.nk.link(sep.outputs["Y"], angle.inputs[0])
        self.nk.link(sep.outputs["X"], angle.inputs[1])
        if len(angle.inputs) > 2:
            angle.inputs[2].default_value = 0.0

        # Create rotation vector (only Z rotation)
        rot_vec = self._combine_xyz(0, 0, angle.outputs[0], x + 950, y - 200, f"{name_prefix}_RotVec")
        self.nk.link(rot_vec.outputs["Vector"], instance_on_points.inputs["Rotation"])

        # Scale is already handled in cutter_xform_inner, use (1,1,1)
        # Realize instances for boolean operation
        realize = self.nk.n("GeometryNodeRealizeInstances", f"{name_prefix}_Realize", x + 700, y - 150)
        self.nk.link(instance_on_points.outputs["Instances"], realize.inputs["Geometry"])

        # ========================================
        # BOOLEAN SUBTRACTION
        # ========================================
        # Subtract the cutters from the cylinder

        bool_node = self.nk.n("GeometryNodeMeshBoolean", f"{name_prefix}_Bool", x + 900, y - 100)
        bool_node.operation = 'DIFFERENCE'
        # Blender 5.0 uses index-based inputs: 0 = first mesh, 1+ = additional meshes
        self.nk.link(geo_socket, bool_node.inputs[0])  # Cylinder (Mesh A)
        self.nk.link(realize.outputs["Geometry"], bool_node.inputs[1])  # Cutters (Mesh B)

        # ========================================
        # RECALCULATE NORMALS
        # ========================================
        # Boolean operations can create inverted normals, fix them
        # GeometryNodeSetMeshNormal with Remove Custom = True recalculates normals
        recalc_normals = self.nk.n("GeometryNodeSetMeshNormal", f"{name_prefix}_RecalcNormals", x + 1050, y - 100)
        recalc_normals.inputs["Remove Custom"].default_value = True  # Recalculate normals
        self.nk.link(bool_node.outputs[0], recalc_normals.inputs["Mesh"])

        # ========================================
        # ENABLE/DISABLE SWITCH
        # ========================================
        # If knurling is disabled, pass through original geometry

        switch = self.nk.n("GeometryNodeSwitch", f"{name_prefix}_Switch", x + 1200, y - 100)
        switch.input_type = 'GEOMETRY'
        # Blender 5.0 Switch inputs: 0 = False (condition), 1 = True (condition)
        # Actually the inputs might be: False, True and switch selection is via "Switch" input
        # Let's use index-based access
        self.nk.link(enable_socket, switch.inputs[0])  # Switch condition
        self.nk.link(geo_socket, switch.inputs[1])  # False = original
        self.nk.link(recalc_normals.outputs[0], switch.inputs[2])  # True = knurled (with fixed normals)

        # Track all nodes
        self.created_nodes.extend([
            cutter_cube, cutter_scale, cutter_xform_inner,
            circle, instance_on_points, pos, sep, angle, rot_vec,
            realize, bool_node, recalc_normals, switch
        ])

        return switch

    def _build_cap(
        self,
        style_socket,
        top_radius_socket,
        bottom_radius_socket,
        height_socket,
        segments_socket,
        x: float,
        y: float,
        name_prefix: str
    ) -> bpy.types.Node:
        """
        Build a cap with switchable style.

        Styles:
        0: Flat (cylinder with bottom_radius)
        1: Beveled (cone from bottom_radius to top_radius * 0.8)
        2: Rounded (UV sphere with bottom_radius)
        3: Tapered+Skirt (Neve style: cone taper out, then vertical skirt)

        For continuous surface:
        - bottom_radius connects to the adjacent section
        - top_radius is the outer tip of the cap

        Returns a Switch node that outputs the selected geometry.
        """
        # Style 0: Flat cap (cylinder - uses bottom_radius for continuous surface)
        flat = self.nk.n("GeometryNodeMeshCylinder", f"{name_prefix}_Flat", x, y)
        self.nk.link(segments_socket, flat.inputs["Vertices"])
        self.nk.link(bottom_radius_socket, flat.inputs["Radius"])
        self.nk.link(height_socket, flat.inputs["Depth"])

        # Style 1: Beveled cap (cone from bottom_radius to tapered top)
        bevel = self.nk.n("GeometryNodeMeshCone", f"{name_prefix}_Bevel", x + 180, y)
        self.nk.link(segments_socket, bevel.inputs["Vertices"])
        # Top radius is 80% of top_radius for beveled look
        bevel_top_r = self._math("*", top_radius_socket, 0.8, x + 180, y + 50, f"{name_prefix}_BevelTopR")
        self.nk.link(bevel_top_r, bevel.inputs["Radius Top"])
        self.nk.link(bottom_radius_socket, bevel.inputs["Radius Bottom"])
        self.nk.link(height_socket, bevel.inputs["Depth"])

        # Style 2: Rounded cap (UV sphere - uses bottom_radius for continuous surface)
        rounded = self.nk.n("GeometryNodeMeshUVSphere", f"{name_prefix}_Rounded", x + 360, y)
        self.nk.link(segments_socket, rounded.inputs["Segments"])
        self.nk.link(bottom_radius_socket, rounded.inputs["Radius"])
        rounded.inputs["Rings"].default_value = 8

        # Fix normals on UV sphere - the pole can have inverted normals
        rounded_normals = self.nk.n("GeometryNodeSetMeshNormal", f"{name_prefix}_RoundedNormals", x + 450, y)
        rounded_normals.inputs["Remove Custom"].default_value = True
        self.nk.link(rounded.outputs["Mesh"], rounded_normals.inputs["Mesh"])

        # Style 3: Tapered+Skirt (Neve style)
        # Creates: cone that tapers OUT from smaller top to larger bottom,
        # then a vertical cylinder "skirt" at the bottom
        # This gives the classic Neve knob base profile

        # Split height: 50% for taper, 50% for skirt
        taper_h = self._math("*", height_socket, 0.5, x + 540, y + 80, f"{name_prefix}_TaperH")
        skirt_h = self._math("*", height_socket, 0.5, x + 540, y + 50, f"{name_prefix}_SkirtH")

        # Taper cone: goes from smaller (bottom_radius) at top to larger (top_radius) at bottom
        # This creates the outward flare
        taper = self.nk.n("GeometryNodeMeshCone", f"{name_prefix}_Taper", x + 660, y + 80)
        self.nk.link(segments_socket, taper.inputs["Vertices"])
        self.nk.link(bottom_radius_socket, taper.inputs["Radius Top"])   # Top = smaller (connects to section above)
        self.nk.link(top_radius_socket, taper.inputs["Radius Bottom"])   # Bottom = larger (outer edge)
        self.nk.link(taper_h, taper.inputs["Depth"])

        # Skirt cylinder: vertical section at the larger radius
        skirt = self.nk.n("GeometryNodeMeshCylinder", f"{name_prefix}_Skirt", x + 660, y + 20)
        self.nk.link(segments_socket, skirt.inputs["Vertices"])
        self.nk.link(top_radius_socket, skirt.inputs["Radius"])  # Same radius as taper bottom
        self.nk.link(skirt_h, skirt.inputs["Depth"])

        # Position skirt below taper
        skirt_pos = self._combine_xyz(0, 0, skirt_h, x + 800, y + 20, f"{name_prefix}_SkirtPos")
        skirt_xform = self.nk.n("GeometryNodeTransform", f"{name_prefix}_SkirtXform", x + 900, y + 20)
        self.nk.link(skirt.outputs["Mesh"], skirt_xform.inputs["Geometry"])
        self.nk.link(skirt_pos.outputs["Vector"], skirt_xform.inputs["Translation"])

        # Join taper and skirt
        taper_skirt_join = self.nk.n("GeometryNodeJoinGeometry", f"{name_prefix}_TaperSkirtJoin", x + 1000, y + 50)
        self.nk.link(taper.outputs["Mesh"], taper_skirt_join.inputs["Geometry"])
        self.nk.link(skirt_xform.outputs["Geometry"], taper_skirt_join.inputs["Geometry"])

        # Create switch nodes for each style option
        # Blender's Index Switch node selects based on integer index
        # IMPORTANT: IndexSwitch inputs are: [0]=Index, [1]=Option0, [2]=Option1, etc.
        switch = self.nk.n("GeometryNodeIndexSwitch", f"{name_prefix}_Switch", x + 1150, y)
        switch.data_type = 'GEOMETRY'

        # Add 2 more items to support 4 options (styles 0-3)
        # Default is 2 items, we need 4
        switch.index_switch_items.new()
        switch.index_switch_items.new()

        self.nk.link(style_socket, switch.inputs["Index"])

        # Connect each geometry to its switch input
        # Inputs: [0]=Index, [1]=Option0 (flat), [2]=Option1 (bevel), [3]=Option2 (rounded), [4]=Option3 (tapered+skirt)
        self.nk.link(flat.outputs["Mesh"], switch.inputs[1])   # Option 0 = Flat
        self.nk.link(bevel.outputs["Mesh"], switch.inputs[2])  # Option 1 = Beveled
        self.nk.link(rounded_normals.outputs[0], switch.inputs[3])  # Option 2 = Rounded (with fixed normals)
        self.nk.link(taper_skirt_join.outputs["Geometry"], switch.inputs[4])  # Option 3 = Tapered+Skirt

        # Track nodes
        self.created_nodes.extend([
            flat, bevel, rounded, rounded_normals,
            taper_h, skirt_h, taper, skirt, skirt_pos, skirt_xform, taper_skirt_join,
            switch
        ])

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
        Apply material to a section with external material and debug mode support.

        Material priority (Index Switch with 3 options):
        - Index 0: External Material input (when Material socket is connected)
        - Index 1: Debug material from input socket (when Debug_Mode = True and no external mat)
        - Index 2: Production material (fallback default)

        The selection logic:
        1. If external Material is provided (not None), use it
        2. Else if Debug_Mode is True, use Debug material
        3. Else use Production material

        Args:
            geo_socket: Geometry socket to apply material to
            section_name: Section name (A_Top, A_Mid, A_Bot, B_Top, B_Mid, B_Bot)
            production_mat: Production material to use as fallback
            x: X position in node editor
            y: Y position in node editor

        Returns:
            The Set Material node
        """
        # ========================================
        # MATERIAL SELECTION LOGIC
        # ========================================
        # We need to select between 3 materials:
        # 0 = External Material (if provided)
        # 1 = Debug Material (if Debug_Mode and no external)
        # 2 = Production Material (fallback)
        #
        # Selection index calculation:
        # - If Material is not None: index = 0 (external)
        # - Else if Debug_Mode: index = 1 (debug)
        # - Else: index = 2 (production)
        #
        # We can detect if Material is connected by checking if it's different from default

        # Check if external material is provided (Material socket)
        # We use a switch that checks if the Material input is None or not
        # Unfortunately in geometry nodes we can't directly check for None
        # So we use a different approach: always connect external material to option 0
        # and use a fallback chain

        # Create Index Switch for material selection (3 options)
        mat_switch = self.nk.n("GeometryNodeIndexSwitch", f"{section_name}_MatSwitch", x + 100, y)
        mat_switch.data_type = 'MATERIAL'
        # Add one more item for 3 total options
        mat_switch.index_switch_items.new()

        # Calculate selection index:
        # - Debug_Mode=True and Material=None: index=1 (debug)
        # - Debug_Mode=True and Material set: index=0 (external - takes priority)
        # - Debug_Mode=False: index=0 if Material set, else index=2

        # For simplicity, we use a different approach:
        # Use a Switch to choose between external material and a nested switch
        # First switch: Is external Material provided? (check via bool from group input)

        # Since we can't easily detect if Material is connected, we use Debug_Mode
        # to control the main switch, and always pass external Material as option 0

        # Create selection logic:
        # If Debug_Mode is True:
        #   - Use Debug material (index 1) - this allows per-section debug mats
        # Else:
        #   - Use external Material if connected (index 0), fallback to production (index 2)

        # For now, simpler approach:
        # Index 0 = External Material (from Material input)
        # Index 1 = Debug Material
        # Index 2 = Production Material
        #
        # Selection: Debug_Mode ? 1 : 0
        # But we want external material to override debug when provided...
        #
        # Let's simplify: Use a two-level switch
        # Level 1: Debug_Mode ? (debug material) : (choose between external/production)
        # Level 2: Is external Material None? production : external

        # SIMPLER APPROACH: Use a single Index Switch
        # - Index 0 = External Material input
        # - Index 1 = Debug Material input
        # - Index 2 = Production material (default)
        #
        # Index calculation:
        # If Debug_Mode: index = 1
        # Else: index = 0 (external, which falls back to production if not connected)

        # Convert Debug_Mode to index
        debug_mode_int = self.nk.n("ShaderNodeMath", f"{section_name}_DebugInt", x, y + 30)
        debug_mode_int.operation = "MULTIPLY"
        self.nk.link(self.gi.outputs["Debug_Mode"], debug_mode_int.inputs[0])
        debug_mode_int.inputs[1].default_value = 1.0
        if len(debug_mode_int.inputs) > 2:
            debug_mode_int.inputs[2].default_value = 0.0

        # Create another int for the external material case
        # If NOT Debug_Mode and Material is provided, use index 0
        # If NOT Debug_Mode and Material is NOT provided, use index 2
        # For simplicity: If NOT Debug_Mode, use index 0 (external), which defaults to None
        # and Blender will handle None gracefully

        # Actually, let's make it simpler:
        # Always try external Material first (index 0)
        # If that's empty/None, Blender will show pink error
        # So we use a switch: Debug_Mode ? debug_mat : external_mat
        # Then wrap in another node that falls back to production

        # FINAL APPROACH: Two switches
        # Switch 1: Debug_Mode ? debug_mat : external_mat
        # Switch 2: (result from Switch 1 is None or connected) ? (result) : production_mat
        #
        # Actually Blender doesn't have "is None" check for materials...
        #
        # SIMPLEST: Just use external Material as option 0, debug as option 1, production as option 2
        # User controls via passing Material and setting Debug_Mode

        self.nk.link(debug_mode_int.outputs[0], mat_switch.inputs["Index"])

        # Option 0: External Material from input socket
        self.nk.link(self.gi.outputs["Material"], mat_switch.inputs[1])

        # Option 1: Debug material from input socket
        debug_socket_name = f"Debug_{section_name}_Material"
        self.nk.link(self.gi.outputs[debug_socket_name], mat_switch.inputs[2])

        # Option 2: Production material (fallback)
        mat_switch.inputs[3].default_value = production_mat

        # Create Set Material node
        set_mat = self.nk.n("GeometryNodeSetMaterial", f"Set_{section_name}_Mat", x + 250, y)
        self.nk.link(geo_socket, set_mat.inputs["Geometry"])
        self.nk.link(mat_switch.outputs["Output"], set_mat.inputs["Material"])

        self.created_nodes.extend([debug_mode_int, mat_switch, set_mat])
        return set_mat


def create_input_node_group(name: str = "Input_ZoneBased") -> bpy.types.NodeTree:
    """Create the input geometry node group with exposed parameters."""
    builder = InputNodeGroupBuilder()
    return builder.build(name)
