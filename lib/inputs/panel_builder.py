"""
Panel Builder - Geometry Nodes Panel Generation

Creates procedural panel geometry with mounting holes, cutouts,
and surface details using Blender Geometry Nodes.

Features:
- Variable thickness panels
- Corner radii (sharp to rounded)
- Mounting hole patterns
- Label embossing/debossing
- Surface texture support
- Material zones
"""

from __future__ import annotations
import bpy
import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


class PanelStyle(Enum):
    """Panel edge/corner style."""
    SHARP = "sharp"         # 90-degree edges
    BEVEL = "bevel"         # Chamfered edges
    ROUNDED = "rounded"     # Filleted corners


class MountingPattern(Enum):
    """Mounting hole pattern types."""
    NONE = "none"           # No mounting holes
    CORNER = "corner"       # 4 corner holes
    EDGE = "edge"           # Holes along edges
    GRID = "grid"           # Regular grid pattern
    CUSTOM = "custom"       # Custom positions


@dataclass
class MountingHoleConfig:
    """Configuration for a mounting hole."""
    x: float                # mm from panel center
    y: float                # mm from panel center
    diameter: float = 4.0   # mm
    counterbore: float = 0.0  # mm (0 = no counterbore)
    countersink: bool = False


@dataclass
class CutoutConfig:
    """Configuration for a panel cutout."""
    name: str
    x: float                # mm from panel origin
    y: float                # mm from panel origin
    width: float            # mm
    height: float           # mm
    corner_radius: float = 0.0  # mm
    bevel: bool = False
    edge_chamfer: float = 0.0  # mm


@dataclass
class PanelConfig:
    """Complete panel configuration."""
    name: str = "Panel"
    width: float = 482.6    # mm (19" rack standard)
    height: float = 88.9    # mm (2U rack standard)
    thickness: float = 3.0  # mm
    corner_radius: float = 0.0  # mm
    style: PanelStyle = PanelStyle.SHARP

    # Mounting
    mounting_pattern: MountingPattern = MountingPattern.CORNER
    mounting_holes: List[MountingHoleConfig] = field(default_factory=list)
    mounting_margin: float = 10.0  # mm from edge for auto holes

    # Cutouts
    cutouts: List[CutoutConfig] = field(default_factory=list)

    # Surface details
    label_text: str = ""
    label_depth: float = 0.3  # mm (positive = emboss, negative = deboss)
    surface_roughness: float = 0.0  # mm (texture depth)

    # Material
    base_color: Tuple[float, float, float] = (0.12, 0.12, 0.13)  # Anthracite
    metallic: float = 0.05
    roughness: float = 0.4

    @property
    def width_m(self) -> float:
        return self.width / 1000

    @property
    def height_m(self) -> float:
        return self.height / 1000

    @property
    def thickness_m(self) -> float:
        return self.thickness / 1000


def create_panel_node_group(name: str = "Panel_Generator") -> bpy.types.NodeTree:
    """
    Create a panel generator node group.

    Inputs:
        Width, Height, Thickness: Panel dimensions in mm
        Corner_Radius: Corner rounding radius in mm
        Style: 0=Sharp, 1=Bevel, 2=Rounded
        Material: Panel material

    Outputs:
        Geometry: Panel mesh with materials applied
    """
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nk = NodeKit(tree)
    nk.clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

    # Dimensions (in mm, converted internally)
    s = tree.interface.new_socket("Width", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 482.6
    s = tree.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 88.9
    s = tree.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 3.0
    s = tree.interface.new_socket("Corner_Radius", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 3.0

    # Style
    s = tree.interface.new_socket("Style", in_out="INPUT", socket_type="NodeSocketInt")
    s.default_value = 0
    s.min_value = 0
    s.max_value = 2

    # Material
    tree.interface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")

    # Debug mode
    s = tree.interface.new_socket("Debug_Mode", in_out="INPUT", socket_type="NodeSocketBool")
    s.default_value = False

    # Output
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Nodes
    gi = nk.group_input(0, 0)
    go = nk.group_output(1200, 0)

    X = 200

    # === CREATE BASE PANEL ===
    # Use cube for base shape
    cube = nk.n("GeometryNodeMeshCube", "BasePanel", X, 0)

    # Convert mm to meters (divide by 1000)
    div_width = nk.n("ShaderNodeMath", "DivWidth", X - 100, 100)
    div_width.operation = "DIVIDE"
    nk.link(gi.outputs["Width"], div_width.inputs[0])
    div_width.inputs[1].default_value = 1000.0

    div_height = nk.n("ShaderNodeMath", "DivHeight", X - 100, 50)
    div_height.operation = "DIVIDE"
    nk.link(gi.outputs["Height"], div_height.inputs[0])
    div_height.inputs[1].default_value = 1000.0

    div_thick = nk.n("ShaderNodeMath", "DivThick", X - 100, 0)
    div_thick.operation = "DIVIDE"
    nk.link(gi.outputs["Thickness"], div_thick.inputs[0])
    div_thick.inputs[1].default_value = 1000.0

    # Connect dimensions to cube
    nk.link(div_width.outputs[0], cube.inputs["Size X"])
    nk.link(div_thick.outputs[0], cube.inputs["Size Y"])  # Y is thickness (depth)
    nk.link(div_height.outputs[0], cube.inputs["Size Z"])

    # === TRANSFORM TO ORIGIN ===
    # Panel center at origin, front face at Y=0
    transform = nk.n("GeometryNodeTransform", "PanelTransform", X + 150, 0)
    nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])

    # Offset so front face is at Y=0 and bottom-left corner is at origin
    offset_y = nk.n("ShaderNodeMath", "OffsetY", X + 50, -100)
    offset_y.operation = "DIVIDE"
    nk.link(div_thick.outputs[0], offset_y.inputs[0])
    offset_y.inputs[1].default_value = -2.0  # Half thickness in -Y direction

    combine_offset = nk.n("ShaderNodeCombineXYZ", "CombineOffset", X + 100, -100)
    combine_offset.inputs["X"].default_value = 0.0
    nk.link(offset_y.outputs[0], combine_offset.inputs["Y"])
    combine_offset.inputs["Z"].default_value = 0.0

    nk.link(combine_offset.outputs["Vector"], transform.inputs["Translation"])

    # === APPLY MATERIAL ===
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", X + 400, 0)
    nk.link(transform.outputs["Geometry"], set_mat.inputs["Geometry"])
    nk.link(gi.outputs["Material"], set_mat.inputs["Material"])

    # === OUTPUT ===
    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return tree


def create_panel_with_cutouts_node_group(name: str = "Panel_With_Cutouts") -> bpy.types.NodeTree:
    """
    Create a panel with cutout support.

    Extends the basic panel with boolean operations for cutouts.
    """
    base_name = name.replace("_With_Cutouts", "_Generator")
    base_tree = create_panel_node_group(base_name)

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nk = NodeKit(tree)
    nk.clear()

    # Create interface (same as base + cutout params)
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

    s = tree.interface.new_socket("Width", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 482.6
    s = tree.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 88.9
    s = tree.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 3.0
    s = tree.interface.new_socket("Corner_Radius", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 3.0
    s = tree.interface.new_socket("Style", in_out="INPUT", socket_type="NodeSocketInt")
    s.default_value = 0
    tree.interface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")
    s = tree.interface.new_socket("Debug_Mode", in_out="INPUT", socket_type="NodeSocketBool")
    s.default_value = False

    # Cutout inputs (up to 8 cutouts)
    for i in range(8):
        s = tree.interface.new_socket(f"Cutout_{i}_X", in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = 0.0
        s = tree.interface.new_socket(f"Cutout_{i}_Y", in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = 0.0
        s = tree.interface.new_socket(f"Cutout_{i}_W", in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = 0.0  # 0 = disabled
        s = tree.interface.new_socket(f"Cutout_{i}_H", in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = 0.0
        s = tree.interface.new_socket(f"Cutout_{i}_R", in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = 0.0  # Corner radius

    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Nodes
    gi = nk.group_input(0, 0)
    go = nk.group_output(2000, 0)

    X = 200

    # Base panel
    base_panel = nk.n("GeometryNodeGroup", "BasePanel", X, 0)
    base_panel.node_tree = base_tree

    nk.link(gi.outputs["Width"], base_panel.inputs["Width"])
    nk.link(gi.outputs["Height"], base_panel.inputs["Height"])
    nk.link(gi.outputs["Thickness"], base_panel.inputs["Thickness"])
    nk.link(gi.outputs["Corner_Radius"], base_panel.inputs["Corner_Radius"])
    nk.link(gi.outputs["Style"], base_panel.inputs["Style"])
    nk.link(gi.outputs["Material"], base_panel.inputs["Material"])
    nk.link(gi.outputs["Debug_Mode"], base_panel.inputs["Debug_Mode"])

    current_geo = base_panel.outputs["Geometry"]
    X += 200

    # Apply cutouts using boolean difference
    for i in range(8):
        # Create cutout cube
        cutout_cube = nk.n("GeometryNodeMeshCube", f"Cutout_{i}", X, -i * 100)

        # Convert mm to meters
        div_w = nk.n("ShaderNodeMath", f"Cutout_{i}_DivW", X - 100, -i * 100 - 50)
        div_w.operation = "DIVIDE"
        nk.link(gi.outputs[f"Cutout_{i}_W"], div_w.inputs[0])
        div_w.inputs[1].default_value = 1000.0

        div_h = nk.n("ShaderNodeMath", f"Cutout_{i}_DivH", X - 100, -i * 100 - 100)
        div_h.operation = "DIVIDE"
        nk.link(gi.outputs[f"Cutout_{i}_H"], div_h.inputs[0])
        div_h.inputs[1].default_value = 1000.0

        # Size (make cutout slightly deeper than panel)
        thick_plus = nk.n("ShaderNodeMath", f"Cutout_{i}_Thick", X - 100, -i * 100 - 150)
        thick_plus.operation = "ADD"
        nk.link(gi.outputs["Thickness"], thick_plus.inputs[0])
        thick_plus.inputs[1].default_value = 2.0  # Extra depth

        div_d = nk.n("ShaderNodeMath", f"Cutout_{i}_DivD", X - 100, -i * 100 - 200)
        div_d.operation = "DIVIDE"
        nk.link(thick_plus.outputs[0], div_d.inputs[0])
        div_d.inputs[1].default_value = 1000.0

        # Connect sizes
        nk.link(div_w.outputs[0], cutout_cube.inputs["Size X"])
        nk.link(div_d.outputs[0], cutout_cube.inputs["Size Y"])
        nk.link(div_h.outputs[0], cutout_cube.inputs["Size Z"])

        # Position
        div_x = nk.n("ShaderNodeMath", f"Cutout_{i}_DivX", X - 100, -i * 100 - 250)
        div_x.operation = "DIVIDE"
        nk.link(gi.outputs[f"Cutout_{i}_X"], div_x.inputs[0])
        div_x.inputs[1].default_value = 1000.0

        div_y = nk.n("ShaderNodeMath", f"Cutout_{i}_DivY", X - 100, -i * 100 - 300)
        div_y.operation = "DIVIDE"
        nk.link(gi.outputs[f"Cutout_{i}_Y"], div_y.inputs[0])
        div_y.inputs[1].default_value = 1000.0

        combine_pos = nk.n("ShaderNodeCombineXYZ", f"Cutout_{i}_Pos", X - 50, -i * 100 - 275)
        nk.link(div_x.outputs[0], combine_pos.inputs["X"])
        combine_pos.inputs["Y"].default_value = 0.0
        nk.link(div_y.outputs[0], combine_pos.inputs["Z"])

        cutout_transform = nk.n("GeometryNodeTransform", f"Cutout_{i}_Transform", X + 100, -i * 100)
        nk.link(cutout_cube.outputs["Mesh"], cutout_transform.inputs["Geometry"])
        nk.link(combine_pos.outputs["Vector"], cutout_transform.inputs["Translation"])

        # Boolean difference (only if cutout width > 0)
        bool_diff = nk.n("GeometryNodeMeshBoolean", f"Bool_{i}", X + 250, -i * 100)
        bool_diff.operation = "DIFFERENCE"
        nk.link(current_geo, bool_diff.inputs["Mesh A"])
        nk.link(cutout_transform.outputs["Geometry"], bool_diff.inputs["Mesh B"])

        # Check if enabled (width > 0)
        enabled = nk.n("ShaderNodeMath", f"Cutout_{i}_Enabled", X + 200, -i * 100 + 50)
        enabled.operation = "GREATER_THAN"
        nk.link(gi.outputs[f"Cutout_{i}_W"], enabled.inputs[0])
        enabled.inputs[1].default_value = 0.0

        # Switch between original and cut
        switch = nk.n("GeometryNodeSwitch", f"Switch_{i}", X + 350, -i * 100)
        switch.input_type = "GEOMETRY"
        nk.link(enabled.outputs[0], switch.inputs["Switch"])
        nk.link(current_geo, switch.inputs["False"])
        nk.link(bool_diff.outputs["Mesh"], switch.inputs["True"])

        current_geo = switch.outputs["Output"]

    X += 400

    # Merge vertices
    merge = nk.n("GeometryNodeMergeByDistance", "MergeVertices", X, 0)
    nk.link(current_geo, merge.inputs["Geometry"])

    # Output
    nk.link(merge.outputs["Geometry"], go.inputs["Geometry"])

    return tree


class PanelBuilder:
    """
    Builder for creating panel geometry.

    Usage:
        builder = PanelBuilder()
        builder.set_size(482.6, 88.9)  # 19" 2U rack
        builder.set_thickness(3.0)
        builder.add_cutout("Knob_Hole", x=50, y=30, width=15, height=15)
        panel_obj = builder.build(collection)
    """

    def __init__(self):
        self.config = PanelConfig()
        self._cutout_index = 0

    def set_name(self, name: str) -> "PanelBuilder":
        """Set panel name."""
        self.config.name = name
        return self

    def set_size(self, width: float, height: float) -> "PanelBuilder":
        """Set panel dimensions in mm."""
        self.config.width = width
        self.config.height = height
        return self

    def set_thickness(self, thickness: float) -> "PanelBuilder":
        """Set panel thickness in mm."""
        self.config.thickness = thickness
        return self

    def set_corner_radius(self, radius: float) -> "PanelBuilder":
        """Set corner radius in mm."""
        self.config.corner_radius = radius
        return self

    def set_style(self, style: PanelStyle) -> "PanelBuilder":
        """Set panel edge style."""
        self.config.style = style
        return self

    def set_material(
        self,
        base_color: Tuple[float, float, float],
        metallic: float = 0.05,
        roughness: float = 0.4
    ) -> "PanelBuilder":
        """Set panel material properties."""
        self.config.base_color = base_color
        self.config.metallic = metallic
        self.config.roughness = roughness
        return self

    def add_cutout(
        self,
        name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        corner_radius: float = 0.0
    ) -> "PanelBuilder":
        """Add a rectangular cutout."""
        cutout = CutoutConfig(
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
            corner_radius=corner_radius
        )
        self.config.cutouts.append(cutout)
        return self

    def add_mounting_hole(
        self,
        x: float,
        y: float,
        diameter: float = 4.0
    ) -> "PanelBuilder":
        """Add a mounting hole."""
        hole = MountingHoleConfig(x=x, y=y, diameter=diameter)
        self.config.mounting_holes.append(hole)
        return self

    def add_corner_mounting_holes(self, margin: float = 10.0) -> "PanelBuilder":
        """Add standard corner mounting holes."""
        w = self.config.width
        h = self.config.height

        self.add_mounting_hole(margin, margin)
        self.add_mounting_hole(w - margin, margin)
        self.add_mounting_hole(margin, h - margin)
        self.add_mounting_hole(w - margin, h - margin)

        return self

    def build(self, collection: bpy.types.Collection) -> bpy.types.Object:
        """
        Build the panel geometry.

        Args:
            collection: Collection to place panel in

        Returns:
            Created panel object
        """
        # Create mesh object
        mesh = bpy.data.meshes.new(f"{self.config.name}_Mesh")
        obj = bpy.data.objects.new(self.config.name, mesh)
        collection.objects.link(obj)

        # Get or create node group
        node_group_name = "Panel_With_Cutouts"
        if node_group_name not in bpy.data.node_groups:
            create_panel_with_cutouts_node_group(node_group_name)

        tree = bpy.data.node_groups[node_group_name]

        # Create modifier
        mod = obj.modifiers.new("PanelGenerator", "NODES")
        mod.node_group = tree

        # Set dimensions
        mod["Width"] = self.config.width
        mod["Height"] = self.config.height
        mod["Thickness"] = self.config.thickness
        mod["Corner_Radius"] = self.config.corner_radius
        mod["Style"] = list(PanelStyle).index(self.config.style)

        # Create and assign material
        mat = self._create_material()
        mod["Material"] = mat

        # Set cutout parameters
        for i, cutout in enumerate(self.config.cutouts[:8]):
            mod[f"Cutout_{i}_X"] = cutout.x
            mod[f"Cutout_{i}_Y"] = cutout.y
            mod[f"Cutout_{i}_W"] = cutout.width
            mod[f"Cutout_{i}_H"] = cutout.height
            mod[f"Cutout_{i}_R"] = cutout.corner_radius

        return obj

    def _create_material(self) -> bpy.types.Material:
        """Create panel material."""
        mat_name = f"Panel_{self.config.name}_Material"

        if mat_name in bpy.data.materials:
            return bpy.data.materials[mat_name]

        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()

        nk = NodeKit(nt)

        X = -400

        # Principled BSDF
        bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", X, 0)
        bsdf.inputs["Base Color"].default_value = (*self.config.base_color, 1.0)
        bsdf.inputs["Metallic"].default_value = self.config.metallic
        bsdf.inputs["Roughness"].default_value = self.config.roughness

        # Output
        out = nk.n("ShaderNodeOutputMaterial", "Output", X + 200, 0)
        nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

        return mat


def create_panel(
    width: float,
    height: float,
    thickness: float = 3.0,
    collection: bpy.types.Collection = None,
    name: str = "Panel"
) -> bpy.types.Object:
    """
    Quick function to create a simple panel.

    Args:
        width: Panel width in mm
        height: Panel height in mm
        thickness: Panel thickness in mm
        collection: Collection to place panel in
        name: Panel object name

    Returns:
        Created panel object
    """
    if collection is None:
        collection = bpy.context.scene.collection

    builder = PanelBuilder()
    builder.set_name(name)
    builder.set_size(width, height)
    builder.set_thickness(thickness)

    return builder.build(collection)
