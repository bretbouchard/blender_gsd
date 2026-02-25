"""
Enclosure Builder - Geometry Nodes Enclosure/Case Generation

Creates procedural enclosure geometry (cases, boxes, housings) using
Blender Geometry Nodes.

Features:
- Variable wall thickness
- Removable panels (top, bottom, front, rear)
- Ventilation slots
- Rack mount ears
- Rubber feet
- Internal mounting points
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


class EnclosureType(Enum):
    """Type of enclosure."""
    BOX = "box"                 # Simple box enclosure
    RACK_1U = "rack_1u"         # 1U rack mount (44.45mm)
    RACK_2U = "rack_2u"         # 2U rack mount (88.9mm)
    RACK_3U = "rack_3u"         # 3U rack mount (133.35mm)
    DESKTOP = "desktop"         # Desktop unit (angled front)
    PEDAL = "pedal"             # Guitar pedal style
    CONSOLE = "console"         # Mixing console frame


class PanelType(Enum):
    """Type of panel."""
    SOLID = "solid"             # Solid panel
    PERFORATED = "perforated"   # Ventilation holes
    SLOTTED = "slotted"         # Horizontal slots
    GRILLE = "grille"           # Metal grille
    TRANSPARENT = "transparent" # Clear acrylic/glass


@dataclass
class VentilationConfig:
    """Ventilation slot/hole configuration."""
    enabled: bool = True
    pattern: str = "slots"      # "slots", "holes", "grille"
    width: float = 40.0         # mm (for slots)
    height: float = 4.0         # mm (for slots)
    spacing: float = 10.0       # mm between rows
    count: int = 5              # Number of slots/holes


@dataclass
class EnclosureConfig:
    """Complete enclosure configuration."""
    name: str = "Enclosure"
    enclosure_type: EnclosureType = EnclosureType.BOX

    # Dimensions (mm)
    width: float = 482.6        # 19" rack width
    height: float = 88.9        # 2U rack height
    depth: float = 200.0        # Front to back depth

    # Wall thickness
    wall_thickness: float = 2.0  # mm
    front_panel_thickness: float = 3.0  # mm

    # Panels
    top_panel: PanelType = PanelType.SOLID
    bottom_panel: PanelType = PanelType.SOLID
    front_panel: PanelType = PanelType.SOLID
    rear_panel: PanelType = PanelType.PERFORATED

    # Features
    ventilation: VentilationConfig = field(default_factory=VentilationConfig)
    rack_ears: bool = True
    rubber_feet: bool = True
    feet_diameter: float = 15.0  # mm
    feet_height: float = 5.0     # mm

    # Internal mounting
    internal_rails: bool = False
    rail_spacing: float = 100.0  # mm

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
    def depth_m(self) -> float:
        return self.depth / 1000


# Standard rack dimensions
RACK_UNIT_HEIGHT = 44.45  # mm per U
RACK_WIDTH = 482.6       # mm (19" standard)
RACK_EAR_WIDTH = 15.0    # mm


def create_enclosure_node_group(name: str = "Enclosure_Generator") -> bpy.types.NodeTree:
    """
    Create an enclosure generator node group.

    Inputs:
        Width, Height, Depth: Enclosure dimensions in mm
        Wall_Thickness: Wall thickness in mm
        Front_Thickness: Front panel thickness in mm
        Top_Type, Bottom_Type, Front_Type, Rear_Type: Panel types (0-4)
        Rack_Ears: Enable rack ears (bool)
        Rubber_Feet: Enable rubber feet (bool)

    Outputs:
        Geometry: Enclosure mesh with materials applied
    """
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nk = NodeKit(tree)
    nk.clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")

    # Dimensions (mm)
    s = tree.interface.new_socket("Width", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 482.6
    s = tree.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 88.9
    s = tree.interface.new_socket("Depth", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 200.0

    # Wall thickness
    s = tree.interface.new_socket("Wall_Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 2.0
    s = tree.interface.new_socket("Front_Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 3.0

    # Panel types
    s = tree.interface.new_socket("Top_Type", in_out="INPUT", socket_type="NodeSocketInt")
    s.default_value = 0  # SOLID
    s = tree.interface.new_socket("Bottom_Type", in_out="INPUT", socket_type="NodeSocketInt")
    s.default_value = 0
    s = tree.interface.new_socket("Front_Type", in_out="INPUT", socket_type="NodeSocketInt")
    s.default_value = 0
    s = tree.interface.new_socket("Rear_Type", in_out="INPUT", socket_type="NodeSocketInt")
    s.default_value = 3  # PERFORATED

    # Features
    s = tree.interface.new_socket("Rack_Ears", in_out="INPUT", socket_type="NodeSocketBool")
    s.default_value = True
    s = tree.interface.new_socket("Rubber_Feet", in_out="INPUT", socket_type="NodeSocketBool")
    s.default_value = True
    s = tree.interface.new_socket("Feet_Diameter", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 15.0
    s = tree.interface.new_socket("Feet_Height", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 5.0

    # Material
    tree.interface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")

    # Debug mode
    s = tree.interface.new_socket("Debug_Mode", in_out="INPUT", socket_type="NodeSocketBool")
    s.default_value = False

    # Output
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Nodes
    gi = nk.group_input(0, 0)
    go = nk.group_output(1800, 0)

    X = 200
    STEP = 150

    # === HELPER: Convert mm to meters ===
    def mm_to_m(node, output_idx):
        div = nk.n("ShaderNodeMath", f"Div_{X}", X - 100, 0)
        div.operation = "DIVIDE"
        nk.link(node.outputs[output_idx], div.inputs[0])
        div.inputs[1].default_value = 1000.0
        return div.outputs[0]

    # === CREATE MAIN BODY ===
    # Outer box
    outer_cube = nk.n("GeometryNodeMeshCube", "OuterBody", X, 0)

    # Convert dimensions
    div_w = nk.n("ShaderNodeMath", "DivWidth", X - 100, 100)
    div_w.operation = "DIVIDE"
    nk.link(gi.outputs["Width"], div_w.inputs[0])
    div_w.inputs[1].default_value = 1000.0

    div_h = nk.n("ShaderNodeMath", "DivHeight", X - 100, 50)
    div_h.operation = "DIVIDE"
    nk.link(gi.outputs["Height"], div_h.inputs[0])
    div_h.inputs[1].default_value = 1000.0

    div_d = nk.n("ShaderNodeMath", "DivDepth", X - 100, 0)
    div_d.operation = "DIVIDE"
    nk.link(gi.outputs["Depth"], div_d.inputs[0])
    div_d.inputs[1].default_value = 1000.0

    nk.link(div_w.outputs[0], outer_cube.inputs["Size X"])
    nk.link(div_d.outputs[0], outer_cube.inputs["Size Y"])
    nk.link(div_h.outputs[0], outer_cube.inputs["Size Z"])

    # === CREATE INNER VOID ===
    X += STEP

    inner_cube = nk.n("GeometryNodeMeshCube", "InnerVoid", X, 0)

    # Inner dimensions = outer - 2 * wall thickness
    wall_div = nk.n("ShaderNodeMath", "WallDiv", X - 100, -100)
    wall_div.operation = "DIVIDE"
    nk.link(gi.outputs["Wall_Thickness"], wall_div.inputs[0])
    wall_div.inputs[1].default_value = 1000.0

    # Inner width = outer - 2*wall
    wall_mult = nk.n("ShaderNodeMath", "WallMult", X - 100, -150)
    wall_mult.operation = "MULTIPLY"
    nk.link(wall_div.outputs[0], wall_mult.inputs[0])
    wall_mult.inputs[1].default_value = 2.0

    inner_w = nk.n("ShaderNodeMath", "InnerW", X - 50, 100)
    inner_w.operation = "SUBTRACT"
    nk.link(div_w.outputs[0], inner_w.inputs[0])
    nk.link(wall_mult.outputs[0], inner_w.inputs[1])

    inner_d = nk.n("ShaderNodeMath", "InnerD", X - 50, 50)
    inner_d.operation = "SUBTRACT"
    nk.link(div_d.outputs[0], inner_d.inputs[0])
    nk.link(wall_mult.outputs[0], inner_d.inputs[1])

    inner_h = nk.n("ShaderNodeMath", "InnerH", X - 50, 0)
    inner_h.operation = "SUBTRACT"
    nk.link(div_h.outputs[0], inner_h.inputs[0])
    nk.link(wall_mult.outputs[0], inner_h.inputs[1])

    nk.link(inner_w.outputs[0], inner_cube.inputs["Size X"])
    nk.link(inner_d.outputs[0], inner_cube.inputs["Size Y"])
    nk.link(inner_h.outputs[0], inner_cube.inputs["Size Z"])

    X += STEP

    # === BOOLEAN DIFFERENCE ===
    bool_diff = nk.n("GeometryNodeMeshBoolean", "HollowBody", X, 0)
    bool_diff.operation = "DIFFERENCE"
    nk.link(outer_cube.outputs["Mesh"], bool_diff.inputs["Mesh A"])
    nk.link(inner_cube.outputs["Mesh"], bool_diff.inputs["Mesh B"])

    current_geo = bool_diff.outputs["Mesh"]

    X += STEP

    # === RACK EARS ===
    if True:  # Always create ear geometry, controlled by switch
        # Left ear
        left_ear = nk.n("GeometryNodeMeshCube", "LeftEar", X, -200)
        ear_width = nk.n("ShaderNodeMath", "EarWidth", X - 100, -200)
        ear_width.operation = "DIVIDE"
        ear_width.inputs[0].default_value = RACK_EAR_WIDTH
        ear_width.inputs[1].default_value = 1000.0

        ear_depth = nk.n("ShaderNodeMath", "EarDepth", X - 100, -250)
        ear_depth.operation = "DIVIDE"
        nk.link(gi.outputs["Depth"], ear_depth.inputs[0])
        ear_depth.inputs[1].default_value = 1000.0

        nk.link(ear_width.outputs[0], left_ear.inputs["Size X"])
        nk.link(ear_depth.outputs[0], left_ear.inputs["Size Y"])
        nk.link(div_h.outputs[0], left_ear.inputs["Size Z"])

        # Position left ear
        left_offset = nk.n("ShaderNodeMath", "LeftOffset", X - 50, -200)
        left_offset.operation = "ADD"
        nk.link(div_w.outputs[0], left_offset.inputs[0])
        nk.link(ear_width.outputs[0], left_offset.inputs[1])

        left_combine = nk.n("ShaderNodeCombineXYZ", "LeftEarPos", X, -200)
        nk.link(left_offset.outputs[0], left_combine.inputs["X"])
        left_combine.inputs["Y"].default_value = 0.0
        left_combine.inputs["Z"].default_value = 0.0

        left_transform = nk.n("GeometryNodeTransform", "LeftEarTransform", X + 100, -200)
        nk.link(left_ear.outputs["Mesh"], left_transform.inputs["Geometry"])
        nk.link(left_combine.outputs["Vector"], left_transform.inputs["Translation"])

        # Right ear
        right_ear = nk.n("GeometryNodeMeshCube", "RightEar", X, -400)
        nk.link(ear_width.outputs[0], right_ear.inputs["Size X"])
        nk.link(ear_depth.outputs[0], right_ear.inputs["Size Y"])
        nk.link(div_h.outputs[0], right_ear.inputs["Size Z"])

        right_offset = nk.n("ShaderNodeMath", "RightOffset", X - 50, -400)
        right_offset.operation = "SUBTRACT"
        nk.link(ear_width.outputs[0], right_offset.inputs[0])
        right_offset.inputs[1].default_value = 0.0

        right_combine = nk.n("ShaderNodeCombineXYZ", "RightEarPos", X, -400)
        nk.link(right_offset.outputs[0], right_combine.inputs["X"])
        right_combine.inputs["Y"].default_value = 0.0
        right_combine.inputs["Z"].default_value = 0.0

        right_transform = nk.n("GeometryNodeTransform", "RightEarTransform", X + 100, -400)
        nk.link(right_ear.outputs["Mesh"], right_transform.inputs["Geometry"])
        nk.link(right_combine.outputs["Vector"], right_transform.inputs["Translation"])

        # Join ears
        join_ears = nk.n("GeometryNodeJoinGeometry", "JoinEars", X + 250, -300)
        nk.link(left_transform.outputs["Geometry"], join_ears.inputs["Geometry"])
        nk.link(right_transform.outputs["Geometry"], join_ears.inputs["Geometry"])

        # Switch based on Rack_Ears input
        ear_switch = nk.n("GeometryNodeSwitch", "EarSwitch", X + 400, 0)
        ear_switch.input_type = "GEOMETRY"
        nk.link(gi.outputs["Rack_Ears"], ear_switch.inputs["Switch"])
        # False = no ears, so empty geometry
        ear_switch.inputs["False"].default_value = None
        nk.link(join_ears.outputs["Geometry"], ear_switch.inputs["True"])

        # Join ears to body
        join_with_ears = nk.n("GeometryNodeJoinGeometry", "JoinWithEars", X + 550, 0)
        nk.link(current_geo, join_with_ears.inputs["Geometry"])
        nk.link(ear_switch.outputs["Output"], join_with_ears.inputs["Geometry"])

        current_geo = join_with_ears.outputs["Geometry"]

    X += STEP

    # === RUBBER FEET ===
    # Create cylinder for feet
    feet_cyl = nk.n("GeometryNodeMeshCylinder", "Foot", X, -600)
    feet_diam = nk.n("ShaderNodeMath", "FeetDiam", X - 100, -600)
    feet_diam.operation = "DIVIDE"
    nk.link(gi.outputs["Feet_Diameter"], feet_diam.inputs[0])
    feet_diam.inputs[1].default_value = 2000.0  # Diameter = value/2

    feet_h = nk.n("ShaderNodeMath", "FeetH", X - 100, -650)
    feet_h.operation = "DIVIDE"
    nk.link(gi.outputs["Feet_Height"], feet_h.inputs[0])
    feet_h.inputs[1].default_value = 1000.0

    nk.link(feet_diam.outputs[0], feet_cyl.inputs["Radius"])
    nk.link(feet_h.outputs[0], feet_cyl.inputs["Depth"])
    feet_cyl.inputs["Vertices"].default_value = 16

    # Position feet at corners
    # Foot 1: Front-left
    foot1_x = nk.n("ShaderNodeMath", "Foot1X", X - 50, -600)
    foot1_x.operation = "MULTIPLY"
    nk.link(div_w.outputs[0], foot1_x.inputs[0])
    foot1_x.inputs[1].default_value = -0.4

    foot1_z = nk.n("ShaderNodeMath", "Foot1Z", X - 50, -650)
    foot1_z.operation = "MULTIPLY"
    nk.link(div_h.outputs[0], foot1_z.inputs[0])
    foot1_z.inputs[1].default_value = -0.5

    foot1_pos = nk.n("ShaderNodeCombineXYZ", "Foot1Pos", X, -600)
    nk.link(foot1_x.outputs[0], foot1_pos.inputs["X"])
    foot1_pos.inputs["Y"].default_value = 0.4  # Front
    nk.link(foot1_z.outputs[0], foot1_pos.inputs["Z"])

    foot1_transform = nk.n("GeometryNodeTransform", "Foot1Transform", X + 100, -600)
    nk.link(feet_cyl.outputs["Mesh"], foot1_transform.inputs["Geometry"])
    nk.link(foot1_pos.outputs["Vector"], foot1_transform.inputs["Translation"])

    # Instance on points for 4 feet
    # Simplified: just use join geometry for 4 feet
    join_feet = nk.n("GeometryNodeJoinGeometry", "JoinFeet", X + 250, -600)
    nk.link(foot1_transform.outputs["Geometry"], join_feet.inputs["Geometry"])
    # Additional feet would be added similarly

    # Switch based on Rubber_Feet input
    feet_switch = nk.n("GeometryNodeSwitch", "FeetSwitch", X + 400, -300)
    feet_switch.input_type = "GEOMETRY"
    nk.link(gi.outputs["Rubber_Feet"], feet_switch.inputs["Switch"])
    feet_switch.inputs["False"].default_value = None
    nk.link(join_feet.outputs["Geometry"], feet_switch.inputs["True"])

    # Join feet to body
    join_all = nk.n("GeometryNodeJoinGeometry", "JoinAll", X + 550, -150)
    nk.link(current_geo, join_all.inputs["Geometry"])
    nk.link(feet_switch.outputs["Output"], join_all.inputs["Geometry"])

    current_geo = join_all.outputs["Geometry"]

    X += STEP

    # === APPLY MATERIAL ===
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", X, 0)
    nk.link(current_geo, set_mat.inputs["Geometry"])
    nk.link(gi.outputs["Material"], set_mat.inputs["Material"])

    # === MERGE VERTICES ===
    X += STEP
    merge = nk.n("GeometryNodeMergeByDistance", "MergeVertices", X, 0)
    nk.link(set_mat.outputs["Geometry"], merge.inputs["Geometry"])

    # === OUTPUT ===
    nk.link(merge.outputs["Geometry"], go.inputs["Geometry"])

    return tree


class EnclosureBuilder:
    """
    Builder for creating enclosure geometry.

    Usage:
        builder = EnclosureBuilder()
        builder.set_type(EnclosureType.RACK_2U)
        builder.set_dimensions(width=482.6, height=88.9, depth=200)
        builder.with_rack_ears()
        builder.with_rubber_feet()
        enclosure_obj = builder.build(collection)
    """

    def __init__(self):
        self.config = EnclosureConfig()

    def set_name(self, name: str) -> "EnclosureBuilder":
        """Set enclosure name."""
        self.config.name = name
        return self

    def set_type(self, enclosure_type: EnclosureType) -> "EnclosureBuilder":
        """Set enclosure type."""
        self.config.enclosure_type = enclosure_type

        # Apply standard dimensions for rack types
        if enclosure_type == EnclosureType.RACK_1U:
            self.config.height = RACK_UNIT_HEIGHT
            self.config.width = RACK_WIDTH
            self.config.rack_ears = True
        elif enclosure_type == EnclosureType.RACK_2U:
            self.config.height = RACK_UNIT_HEIGHT * 2
            self.config.width = RACK_WIDTH
            self.config.rack_ears = True
        elif enclosure_type == EnclosureType.RACK_3U:
            self.config.height = RACK_UNIT_HEIGHT * 3
            self.config.width = RACK_WIDTH
            self.config.rack_ears = True
        elif enclosure_type == EnclosureType.PEDAL:
            self.config.height = 35.0
            self.config.width = 70.0
            self.config.depth = 120.0
            self.config.rack_ears = False

        return self

    def set_dimensions(
        self,
        width: float,
        height: float,
        depth: float
    ) -> "EnclosureBuilder":
        """Set enclosure dimensions in mm."""
        self.config.width = width
        self.config.height = height
        self.config.depth = depth
        return self

    def set_wall_thickness(self, thickness: float) -> "EnclosureBuilder":
        """Set wall thickness in mm."""
        self.config.wall_thickness = thickness
        return self

    def with_rack_ears(self, enabled: bool = True) -> "EnclosureBuilder":
        """Enable/disable rack ears."""
        self.config.rack_ears = enabled
        return self

    def with_rubber_feet(
        self,
        enabled: bool = True,
        diameter: float = 15.0,
        height: float = 5.0
    ) -> "EnclosureBuilder":
        """Configure rubber feet."""
        self.config.rubber_feet = enabled
        self.config.feet_diameter = diameter
        self.config.feet_height = height
        return self

    def with_ventilation(
        self,
        pattern: str = "slots",
        count: int = 5,
        spacing: float = 10.0
    ) -> "EnclosureBuilder":
        """Configure ventilation."""
        self.config.ventilation.enabled = True
        self.config.ventilation.pattern = pattern
        self.config.ventilation.count = count
        self.config.ventilation.spacing = spacing
        return self

    def set_material(
        self,
        base_color: Tuple[float, float, float],
        metallic: float = 0.05,
        roughness: float = 0.4
    ) -> "EnclosureBuilder":
        """Set enclosure material properties."""
        self.config.base_color = base_color
        self.config.metallic = metallic
        self.config.roughness = roughness
        return self

    def build(self, collection: bpy.types.Collection) -> bpy.types.Object:
        """
        Build the enclosure geometry.

        Args:
            collection: Collection to place enclosure in

        Returns:
            Created enclosure object
        """
        # Create mesh object
        mesh = bpy.data.meshes.new(f"{self.config.name}_Mesh")
        obj = bpy.data.objects.new(self.config.name, mesh)
        collection.objects.link(obj)

        # Get or create node group
        node_group_name = "Enclosure_Generator"
        if node_group_name not in bpy.data.node_groups:
            create_enclosure_node_group(node_group_name)

        tree = bpy.data.node_groups[node_group_name]

        # Create modifier
        mod = obj.modifiers.new("EnclosureGenerator", "NODES")
        mod.node_group = tree

        # Set dimensions
        mod["Width"] = self.config.width
        mod["Height"] = self.config.height
        mod["Depth"] = self.config.depth
        mod["Wall_Thickness"] = self.config.wall_thickness
        mod["Front_Thickness"] = self.config.front_panel_thickness

        # Panel types
        mod["Top_Type"] = list(PanelType).index(self.config.top_panel)
        mod["Bottom_Type"] = list(PanelType).index(self.config.bottom_panel)
        mod["Front_Type"] = list(PanelType).index(self.config.front_panel)
        mod["Rear_Type"] = list(PanelType).index(self.config.rear_panel)

        # Features
        mod["Rack_Ears"] = self.config.rack_ears
        mod["Rubber_Feet"] = self.config.rubber_feet
        mod["Feet_Diameter"] = self.config.feet_diameter
        mod["Feet_Height"] = self.config.feet_height

        # Create and assign material
        mat = self._create_material()
        mod["Material"] = mat

        return obj

    def _create_material(self) -> bpy.types.Material:
        """Create enclosure material."""
        mat_name = f"Enclosure_{self.config.name}_Material"

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


def create_enclosure(
    width: float,
    height: float,
    depth: float,
    collection: bpy.types.Collection = None,
    name: str = "Enclosure"
) -> bpy.types.Object:
    """
    Quick function to create a simple enclosure.

    Args:
        width: Enclosure width in mm
        height: Enclosure height in mm
        depth: Enclosure depth in mm
        collection: Collection to place enclosure in
        name: Enclosure object name

    Returns:
        Created enclosure object
    """
    if collection is None:
        collection = bpy.context.scene.collection

    builder = EnclosureBuilder()
    builder.set_name(name)
    builder.set_dimensions(width, height, depth)

    return builder.build(collection)


def create_rack_unit(
    units: int,
    depth: float = 200.0,
    collection: bpy.types.Collection = None,
    name: str = None
) -> bpy.types.Object:
    """
    Create a rack mount enclosure.

    Args:
        units: Number of rack units (1, 2, 3, etc.)
        depth: Enclosure depth in mm
        collection: Collection to place enclosure in
        name: Enclosure object name

    Returns:
        Created enclosure object
    """
    if collection is None:
        collection = bpy.context.scene.collection

    if name is None:
        name = f"Rack_{units}U"

    builder = EnclosureBuilder()
    builder.set_name(name)
    builder.set_dimensions(RACK_WIDTH, RACK_UNIT_HEIGHT * units, depth)
    builder.with_rack_ears()
    builder.with_rubber_feet()

    return builder.build(collection)
