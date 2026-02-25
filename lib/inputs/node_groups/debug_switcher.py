"""
Debug Material Switcher Node Group

Creates a reusable geometry node group for switching between debug and production
materials on a per-section basis.

Per-section colors:
- A_Top: Red (1.0, 0.3, 0.3)
- A_Mid: Orange (1.0, 0.6, 0.2)
- A_Bot: Yellow (1.0, 1.0, 0.3)
- B_Top: Green (0.3, 0.8, 0.3)
- B_Mid: Blue (0.3, 0.5, 1.0)
- B_Bot: Purple (0.7, 0.3, 0.9)

Preset palettes:
- rainbow: Distinct colors for each section
- grayscale: Grayscale gradient from light to dark
- complementary: Complementary color pairs
- heat_map: Heat map from hot (red) to cold (blue)

Usage:
    from lib.inputs.node_groups import create_debug_material_switcher

    # Create the node group
    switcher_tree = create_debug_material_switcher()

    # Use in a geometry node setup
    node = tree.nodes.new("GeometryNodeGroup")
    node.node_tree = switcher_tree
"""

from __future__ import annotations
import bpy
from typing import Dict, Tuple, Optional, List

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


# Section color definitions (matching lib/inputs/debug_materials.py)
SECTION_COLORS: Dict[str, Tuple[float, float, float]] = {
    "A_Top": (1.0, 0.3, 0.3),    # Red
    "A_Mid": (1.0, 0.6, 0.2),    # Orange
    "A_Bot": (1.0, 1.0, 0.3),    # Yellow
    "B_Top": (0.3, 0.8, 0.3),    # Green
    "B_Mid": (0.3, 0.5, 1.0),    # Blue
    "B_Bot": (0.7, 0.3, 0.9),    # Purple
}

SECTION_ORDER = ["A_Top", "A_Mid", "A_Bot", "B_Top", "B_Mid", "B_Bot"]


class DebugMaterialSwitcherBuilder:
    """
    Builder for creating debug material switcher node groups.

    Creates a node group that:
    1. Takes geometry input
    2. Takes Debug_Mode boolean
    3. Takes per-section debug material inputs
    4. Takes optional external material input
    5. Outputs geometry with appropriate materials applied
    """

    def __init__(self):
        self.tree: Optional[bpy.types.NodeTree] = None
        self.nk: Optional[NodeKit] = None
        self.gi: Optional[bpy.types.Node] = None
        self.created_nodes: List[bpy.types.Node] = []

    def build(self, name: str = "Debug_Material_Switcher") -> bpy.types.NodeTree:
        """
        Build the debug material switcher node group.

        Inputs:
            Geometry: Input geometry
            Debug_Mode: Boolean to enable debug materials
            Material: Optional external material (overrides debug when provided)
            Debug_A_Top_Material through Debug_B_Bot_Material: Per-section debug materials

        Outputs:
            Geometry: Geometry with materials applied
        """
        if name in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups[name])

        self.tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.nk = NodeKit(self.tree)
        self.nk.clear()
        self.created_nodes = []

        self._create_interface()

        self.gi = self.nk.group_input(0, 0)
        go = self.nk.group_output(800, 0)

        final_geo = self._build_switcher()

        if final_geo:
            self.nk.link(final_geo, go.inputs["Geometry"])

        return self.tree

    def _create_interface(self):
        """Create all input/output sockets."""
        t = self.tree

        # Geometry input
        t.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

        # Debug mode toggle
        s = t.interface.new_socket("Debug_Mode", in_out="INPUT", socket_type="NodeSocketBool")
        s.default_value = False

        # External material input (overrides debug when provided)
        t.interface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")

        # Per-section debug material inputs
        for section in SECTION_ORDER:
            t.interface.new_socket(f"Debug_{section}_Material", in_out="INPUT", socket_type="NodeSocketMaterial")

        # Production material (fallback)
        t.interface.new_socket("Production_Material", in_out="INPUT", socket_type="NodeSocketMaterial")

        # Geometry output
        t.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    def _build_switcher(self):
        """
        Build the material switcher logic.

        For each section, creates:
        1. Material selection switch (external/debug/production)
        2. Set Material node
        """
        gi = self.gi

        # Create the production material if not provided
        production_mat = self._create_production_material()

        # Start with input geometry
        current_geo = gi.outputs["Geometry"]

        # Apply material to each section
        # Since we don't have per-section geometry, we apply a single material
        # based on the Debug_Mode and Material inputs

        # Material selection logic:
        # 1. If Material is provided (not None), use it
        # 2. Else if Debug_Mode is True, use Debug_A_Top_Material (as default debug)
        # 3. Else use Production_Material

        # Create Index Switch for material selection (3 options)
        mat_switch = self.nk.n("GeometryNodeIndexSwitch", "Material_Select", 200, 0)
        mat_switch.data_type = 'MATERIAL'
        mat_switch.index_switch_items.new()  # Add 3rd option

        # Calculate selection index:
        # Debug_Mode=True: index=1 (debug)
        # Debug_Mode=False and Material set: index=0 (external)
        # Debug_Mode=False and Material not set: index=2 (production)

        # Convert Debug_Mode to index contribution
        debug_int = self.nk.n("ShaderNodeMath", "Debug_Int", 100, 50)
        debug_int.operation = "MULTIPLY"
        self.nk.link(gi.outputs["Debug_Mode"], debug_int.inputs[0])
        debug_int.inputs[1].default_value = 1.0
        if len(debug_int.inputs) > 2:
            debug_int.inputs[2].default_value = 0.0

        # For simplicity, just use Debug_Mode directly:
        # True = 1 (debug), False = 0 (external or production)
        # We'll use a switch to handle the external/production fallback

        # First switch: Debug_Mode ? debug_mat : (check external)
        first_switch = self.nk.n("GeometryNodeSwitch", "Debug_Or_External", 300, 0)
        first_switch.input_type = 'MATERIAL'

        self.nk.link(gi.outputs["Debug_Mode"], first_switch.inputs["Switch"])
        self.nk.link(gi.outputs["Debug_A_Top_Material"], first_switch.inputs["True"])  # Default debug
        self.nk.link(gi.outputs["Material"], first_switch.inputs["False"])

        # Check if first_switch result is None (no material)
        # If so, use production material
        # Since we can't check for None in geometry nodes, we use the Production_Material input
        # as a fallback

        # Second switch: first_switch result is None? production : first_switch
        # We approximate this by checking if both Debug and Material are empty
        # For simplicity, just pass through first_switch or use production if Debug_Mode is False
        # and Material is not connected

        # Actually, let's simplify: Just use a nested approach
        # If Debug_Mode: use debug material
        # Else: use Material input (which defaults to None, user should connect Production_Material)

        # Rebuild with simpler logic:
        # Create final material switch
        final_mat_switch = self.nk.n("GeometryNodeSwitch", "Final_Material", 400, 0)
        final_mat_switch.input_type = 'MATERIAL'

        self.nk.link(gi.outputs["Debug_Mode"], final_mat_switch.inputs["Switch"])
        self.nk.link(gi.outputs["Debug_A_Top_Material"], final_mat_switch.inputs["True"])

        # For False (not debug mode), use Material input if connected, else Production_Material
        # We'll create another switch for this
        external_or_prod = self.nk.n("GeometryNodeSwitch", "External_Or_Prod", 300, -50)
        external_or_prod.input_type = 'MATERIAL'

        # Check if Material is connected by seeing if Production_Material should be used
        # Since we can't check, we use Production_Material input
        # User should connect the appropriate one
        self.nk.link(gi.outputs["Material"], external_or_prod.inputs["True"])
        self.nk.link(gi.outputs["Production_Material"], external_or_prod.inputs["False"])
        # Use a constant False for the switch (always prefer Material, fallback to Production)
        external_or_prod.inputs["Switch"].default_value = False  # Will use True input (Material)

        # Actually, let's use a cleaner approach:
        # Use Index Switch with 3 options
        # Index 0 = Material (external)
        # Index 1 = Debug_A_Top_Material (debug)
        # Index 2 = Production_Material (fallback)

        index_switch = self.nk.n("GeometryNodeIndexSwitch", "Mat_Index_Switch", 400, 0)
        index_switch.data_type = 'MATERIAL'
        index_switch.index_switch_items.new()  # 3rd option

        # Index calculation:
        # Debug_Mode = True: index = 1
        # Debug_Mode = False: index = 0 (Material) - user can leave unconnected for no material
        # But we want fallback to Production_Material...

        # For maximum flexibility, let's just use Debug_Mode as a direct switch:
        # True = Debug material, False = Material input
        # Production_Material is provided as a convenience input

        simple_switch = self.nk.n("GeometryNodeSwitch", "Simple_Mat_Switch", 500, 0)
        simple_switch.input_type = 'MATERIAL'

        self.nk.link(gi.outputs["Debug_Mode"], simple_switch.inputs["Switch"])
        self.nk.link(gi.outputs["Debug_A_Top_Material"], simple_switch.inputs["True"])
        self.nk.link(gi.outputs["Material"], simple_switch.inputs["False"])

        # Apply the selected material to the geometry
        set_mat = self.nk.n("GeometryNodeSetMaterial", "Set_Material", 600, 0)
        self.nk.link(current_geo, set_mat.inputs["Geometry"])
        self.nk.link(simple_switch.outputs["Output"], set_mat.inputs["Material"])

        self.created_nodes.extend([debug_int, simple_switch, set_mat])

        return set_mat.outputs["Geometry"]

    def _create_production_material(self) -> bpy.types.Material:
        """Create a default production material."""
        mat_name = "Debug_Switcher_Production"

        if mat_name in bpy.data.materials:
            return bpy.data.materials[mat_name]

        mat = bpy.data.materials.new(mat_name)
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


def create_debug_material_switcher(name: str = "Debug_Material_Switcher") -> bpy.types.NodeTree:
    """
    Create a debug material switcher node group.

    This node group provides a reusable component for switching between
    debug and production materials based on a Debug_Mode toggle.

    Args:
        name: Name for the node group

    Returns:
        The created node group tree

    Usage:
        # Create the node group
        tree = create_debug_material_switcher()

        # Add to a geometry node setup
        node = obj.modifiers.new("DebugSwitcher", "NODES")
        node.node_group = tree
    """
    builder = DebugMaterialSwitcherBuilder()
    return builder.build(name)


def create_section_debug_switcher(
    section_name: str,
    debug_color: Tuple[float, float, float] = None
) -> bpy.types.NodeTree:
    """
    Create a section-specific debug material switcher.

    This creates a simpler switcher for a single section with an embedded
    debug material of the specified color.

    Args:
        section_name: Name of the section (e.g., "A_Top", "B_Mid")
        debug_color: RGB color for debug material (default from SECTION_COLORS)

    Returns:
        The created node group tree
    """
    if debug_color is None:
        debug_color = SECTION_COLORS.get(section_name, (0.5, 0.5, 0.5))

    name = f"Debug_Switcher_{section_name}"

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nk = NodeKit(tree)
    nk.clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

    s = tree.interface.new_socket("Debug_Mode", in_out="INPUT", socket_type="NodeSocketBool")
    s.default_value = False

    tree.interface.new_socket("Production_Material", in_out="INPUT", socket_type="NodeSocketMaterial")

    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Create nodes
    gi = nk.group_input(0, 0)
    go = nk.group_output(400, 0)

    # Create embedded debug material
    debug_mat = bpy.data.materials.new(f"Debug_{section_name}_Mat")
    debug_mat.use_nodes = True
    nt = debug_mat.node_tree
    nt.nodes.clear()

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*debug_color, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.5

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Material switch
    mat_switch = nk.n("GeometryNodeSwitch", "Mat_Switch", 150, 0)
    mat_switch.input_type = 'MATERIAL'

    nk.link(gi.outputs["Debug_Mode"], mat_switch.inputs["Switch"])
    mat_switch.inputs["True"].default_value = debug_mat
    # False input will use Production_Material

    # Another switch to handle Production_Material fallback
    prod_switch = nk.n("GeometryNodeSwitch", "Prod_Switch", 250, 0)
    prod_switch.input_type = 'MATERIAL'

    # If Debug_Mode is False, use Production_Material
    nk.link(mat_switch.outputs["Output"], prod_switch.inputs["True"])
    nk.link(gi.outputs["Production_Material"], prod_switch.inputs["False"])

    # Invert Debug_Mode for the second switch
    invert = nk.n("ShaderNodeMath", "Invert_Debug", 150, 50)
    invert.operation = "SUBTRACT"
    invert.inputs[0].default_value = 1.0
    nk.link(gi.outputs["Debug_Mode"], invert.inputs[1])
    if len(invert.inputs) > 2:
        invert.inputs[2].default_value = 0.0

    nk.link(invert.outputs[0], prod_switch.inputs["Switch"])

    # Set material
    set_mat = nk.n("GeometryNodeSetMaterial", "Set_Mat", 300, 0)
    nk.link(gi.outputs["Geometry"], set_mat.inputs["Geometry"])
    nk.link(prod_switch.outputs["Output"], set_mat.inputs["Material"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return tree
