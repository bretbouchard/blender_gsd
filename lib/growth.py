"""
Procedural Growth Module - Codified from Tutorial 34

Implements procedural growth patterns using geometry nodes.
Based on Bad Normals tutorial: https://youtu.be/MGxNuS_-bpo

Usage:
    from lib.growth import FernGrower

    # Create procedural fern
    fern = FernGrower.create("MyFern")
    fern.set_leaf_count(20)
    fern.set_taper(1.0, 0.2)  # Large at bottom, small at top
    tree = fern.build()  # Creates the actual node tree
"""

from __future__ import annotations
import bpy
import math
from typing import Optional, Tuple
from pathlib import Path

# Import NodeKit for node building
try:
    from .nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit


class FernGrower:
    """
    Procedural fern/plant growth using geometry nodes.

    Creates a complete node tree with:
    - Mesh Line for stem/point distribution
    - Index-based taper scaling
    - Instance on Points for leaf placement
    - Random rotation variation

    Cross-references:
    - KB Section 34: Blender Growth Tutorial (Bad Normals)
    - lib/nodekit.py: For node tree building
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._leaf_count = 20
        self._taper_start = 1.0
        self._taper_end = 0.2
        self._rotation_variation = 15.0
        self._stem_height = 5.0
        self._leaf_size = 0.5
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "FernGrower") -> "FernGrower":
        """
        Create a new geometry node tree for fern growth.

        Args:
            name: Name for the node group

        Returns:
            Configured FernGrower instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "FernGrower"
    ) -> "FernGrower":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach to
            name: Name for the node group

        Returns:
            Configured FernGrower instance
        """
        mod = obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance._setup_interface()
        return instance

    def _setup_interface(self) -> None:
        """Set up the node group interface (inputs/outputs)."""
        # Create interface inputs
        self.node_tree.interface.new_socket(
            name="Leaf Count", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._leaf_count, min_value=1, max_value=100
        )
        self.node_tree.interface.new_socket(
            name="Stem Height", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._stem_height, min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Taper Start", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._taper_start, min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Taper End", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._taper_end, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Rotation Variation", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._rotation_variation, min_value=0, max_value=90
        )
        self.node_tree.interface.new_socket(
            name="Leaf Size", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._leaf_size, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=42
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_leaf_count(self, count: int) -> "FernGrower":
        """Set number of leaves along stem."""
        self._leaf_count = count
        return self

    def set_taper(self, start_scale: float, end_scale: float) -> "FernGrower":
        """
        Set taper from bottom to top.

        KB Reference: Section 34 - Creates tapered effect
        """
        self._taper_start = start_scale
        self._taper_end = end_scale
        return self

    def set_rotation_variation(self, degrees: float) -> "FernGrower":
        """Set random rotation variation for natural look."""
        self._rotation_variation = degrees
        return self

    def set_stem_height(self, height: float) -> "FernGrower":
        """Set the height of the fern stem."""
        self._stem_height = height
        return self

    def set_leaf_size(self, size: float) -> "FernGrower":
        """Set the base size of leaves."""
        self._leaf_size = size
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for fern growth.

        KB Reference: Section 34 - Fern Creation Process

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() or from_object() first")

        nk = self.nk
        x = 0

        # === INPUT NODES ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === MESH LINE - Foundation for growth ===
        # KB Reference: Section 34 - Mesh Line as Base
        mesh_line = nk.n(
            "GeometryNodeMeshLine",
            "Stem Points",
            x=x, y=100
        )
        mesh_line.inputs["Count"].default_value = self._leaf_count
        # Connect count from input
        nk.link(group_in.outputs["Leaf Count"], mesh_line.inputs["Count"])

        self._created_nodes['mesh_line'] = mesh_line

        x += 250

        # === INDEX FOR TAPER ===
        # KB Reference: Section 34 - Index-Based Scaling
        index = nk.n(
            "GeometryNodeInputIndex",
            "Index",
            x=x, y=-50
        )
        self._created_nodes['index'] = index

        # === MAP RANGE FOR TAPER ===
        # KB Reference: Section 34 - Inverting Range for Taper
        # We need to map 0→1.0 and (count-1)→0.2

        # First, get count-1 for max
        count_minus_1 = nk.n(
            "ShaderNodeMath",
            "Count - 1",
            x=x, y=-150
        )
        count_minus_1.operation = 'SUBTRACT'
        count_minus_1.inputs[1].default_value = 1.0
        nk.link(group_in.outputs["Leaf Count"], count_minus_1.inputs[0])
        self._created_nodes['count_minus_1'] = count_minus_1

        # Map range for taper
        # Note: Blender doesn't have a direct Map Range node in geometry nodes
        # We use math: (index / max) * (end - start) + start
        # = (index / (count-1)) * (taper_end - taper_start) + taper_start

        # Divide index by count-1
        normalize = nk.n("ShaderNodeMath", "Normalize", x=x + 200, y=-50)
        normalize.operation = 'DIVIDE'
        nk.link(index.outputs["Index"], normalize.inputs[0])
        nk.link(count_minus_1.outputs[0], normalize.inputs[1])
        self._created_nodes['normalize'] = normalize

        # Calculate taper range (end - start)
        taper_diff = nk.n("ShaderNodeMath", "Taper Diff", x=x + 200, y=-150)
        taper_diff.operation = 'SUBTRACT'
        nk.link(group_in.outputs["Taper End"], taper_diff.inputs[0])
        nk.link(group_in.outputs["Taper Start"], taper_diff.inputs[1])
        self._created_nodes['taper_diff'] = taper_diff

        # Multiply normalized by range
        scale_mult = nk.n("ShaderNodeMath", "Scale Mult", x=x + 400, y=-100)
        scale_mult.operation = 'MULTIPLY'
        nk.link(normalize.outputs[0], scale_mult.inputs[0])
        nk.link(taper_diff.outputs[0], scale_mult.inputs[1])
        self._created_nodes['scale_mult'] = scale_mult

        # Add start offset
        scale_add = nk.n("ShaderNodeMath", "Scale Add", x=x + 600, y=-100)
        scale_add.operation = 'ADD'
        nk.link(scale_mult.outputs[0], scale_add.inputs[0])
        nk.link(group_in.outputs["Taper Start"], scale_add.inputs[1])
        self._created_nodes['scale_final'] = scale_add

        x += 850

        # === RANDOM ROTATION ===
        # KB Reference: Section 34 - Random rotation for natural look
        random_rot = nk.n(
            "FunctionNodeRandomValue",
            "Random Rotation",
            x=x, y=-200
        )
        random_rot.data_type = 'FLOAT'
        # Convert degrees to radians
        random_rot.inputs["Min"].default_value = -math.radians(self._rotation_variation)
        random_rot.inputs["Max"].default_value = math.radians(self._rotation_variation)
        nk.link(group_in.outputs["Seed"], random_rot.inputs["Seed"])
        self._created_nodes['random_rotation'] = random_rot

        # === COMBINE ROTATION (Z only) ===
        rotation = nk.n(
            "ShaderNodeCombineXYZ",
            "Rotation",
            x=x + 200, y=-200
        )
        rotation.inputs["X"].default_value = 0.0
        rotation.inputs["Y"].default_value = 0.0
        nk.link(random_rot.outputs[0], rotation.inputs["Z"])
        self._created_nodes['rotation'] = rotation

        x += 450

        # === CREATE LEAF GEOMETRY ===
        # KB Reference: Section 34 - Instance on Points
        # Simple quad for leaf
        leaf_quad = nk.n(
            "GeometryNodeMeshGrid",
            "Leaf Shape",
            x=x, y=-150
        )
        leaf_quad.inputs["Vertices X"].default_value = 2
        leaf_quad.inputs["Vertices Y"].default_value = 2
        nk.link(group_in.outputs["Leaf Size"], leaf_quad.inputs["Size X"])
        nk.link(group_in.outputs["Leaf Size"], leaf_quad.inputs["Size Y"])
        self._created_nodes['leaf_shape'] = leaf_quad

        # === INSTANCE ON POINTS ===
        # KB Reference: Section 34 - Instance on Points
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Place Leaves",
            x=x + 250, y=100
        )
        nk.link(mesh_line.outputs["Mesh"], instance.inputs["Points"])
        nk.link(leaf_quad.outputs["Mesh"], instance.inputs["Instance"])
        # Connect scale from taper calculation
        nk.link(scale_add.outputs[0], instance.inputs["Scale"])
        # Connect rotation
        nk.link(rotation.outputs["Vector"], instance.inputs["Rotation"])

        self._created_nodes['instance'] = instance

        x += 500

        # === REALIZE INSTANCES ===
        realize = nk.n(
            "GeometryNodeRealizeInstances",
            "Realize",
            x=x, y=100
        )
        nk.link(instance.outputs["Instances"], realize.inputs["Geometry"])
        self._created_nodes['realize'] = realize

        x += 200

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(realize.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class IndexTaper:
    """
    Index-based scaling for tapered effects.

    Cross-references:
    - KB Section 34: Index-Based Scaling
    """

    @staticmethod
    def add_taper_nodes(
        nk: NodeKit,
        count_input,
        taper_start: float = 1.0,
        taper_end: float = 0.2,
        x: float = 0,
        y: float = 0
    ) -> bpy.types.Node:
        """
        Add index-based taper scaling nodes.

        Args:
            nk: NodeKit instance
            count_input: Socket with point count
            taper_start: Scale at index 0
            taper_end: Scale at last index
            x, y: Position for nodes

        Returns:
            Final scale value node
        """
        # Index
        index = nk.n("GeometryNodeInputIndex", "Index", x=x, y=y)

        # Count - 1
        count_m1 = nk.n("ShaderNodeMath", "Count-1", x=x + 150, y=y + 100)
        count_m1.operation = 'SUBTRACT'
        count_m1.inputs[1].default_value = 1.0
        nk.link(count_input, count_m1.inputs[0])

        # Normalize index
        normalize = nk.n("ShaderNodeMath", "Normalize", x=x + 300, y=y)
        normalize.operation = 'DIVIDE'
        nk.link(index.outputs["Index"], normalize.inputs[0])
        nk.link(count_m1.outputs[0], normalize.inputs[1])

        # Taper range
        taper_range = taper_end - taper_start

        # Multiply
        scale = nk.n("ShaderNodeMath", "Scale", x=x + 450, y=y)
        scale.operation = 'MULTIPLY'
        scale.inputs[1].default_value = taper_range
        nk.link(normalize.outputs[0], scale.inputs[0])

        # Add start
        final = nk.n("ShaderNodeMath", "Final Scale", x=x + 600, y=y)
        final.operation = 'ADD'
        final.inputs[1].default_value = taper_start
        nk.link(scale.outputs[0], final.inputs[0])

        return final

    @staticmethod
    def get_map_range_config(
        point_count: int,
        from_scale: float = 1.0,
        to_scale: float = 0.2,
        inverted: bool = True
    ) -> dict:
        """Get map range configuration for taper."""
        if inverted:
            return {
                "node": "Map Range",
                "input": "Index",
                "from_min": 0,
                "from_max": point_count - 1,
                "to_min": from_scale,
                "to_max": to_scale,
                "result": "Tapered effect"
            }
        else:
            return {
                "node": "Map Range",
                "input": "Index",
                "from_min": 0,
                "from_max": point_count - 1,
                "to_min": to_scale,
                "to_max": from_scale
            }


class RecursiveGrowth:
    """
    Recursive branching patterns for complex plants.

    Cross-references:
    - KB Section 34: Recursive Growth Patterns
    """

    @staticmethod
    def get_recursive_config() -> dict:
        """Get configuration for recursive branching."""
        return {
            "pattern": "For Each Point",
            "process": [
                "Create sub-branches",
                "Apply same scaling logic",
                "Rotate for natural spread"
            ],
            "iteration": "Can use repeat zones",
            "complexity": "Each level adds detail"
        }

    @staticmethod
    def get_branch_levels() -> dict:
        """Get typical branch level configurations."""
        return {
            "level_1": {
                "name": "Primary branches",
                "count": "5-10 per stem",
                "scale": "0.6-0.8 of parent"
            },
            "level_2": {
                "name": "Secondary branches",
                "count": "3-5 per primary",
                "scale": "0.4-0.6 of parent"
            },
            "level_3": {
                "name": "Tertiary (leaves)",
                "count": "2-3 per secondary",
                "scale": "0.2-0.4 of parent"
            }
        }


class NaturalVariation:
    """
    Add natural variation to growth patterns.

    Cross-references:
    - KB Section 34: Pro Tips for Natural Growth
    """

    @staticmethod
    def add_rotation_variation(
        nk: NodeKit,
        seed_input,
        variation_degrees: float = 15.0,
        x: float = 0,
        y: float = 0
    ) -> bpy.types.Node:
        """
        Add random rotation variation.

        Args:
            nk: NodeKit instance
            seed_input: Seed socket
            variation_degrees: Max rotation in degrees
            x, y: Position for nodes

        Returns:
            Combine XYZ node with rotation vector
        """
        rad = math.radians(variation_degrees)

        random = nk.n("FunctionNodeRandomValue", "Random Rot", x=x, y=y)
        random.inputs["Min"].default_value = -rad
        random.inputs["Max"].default_value = rad
        nk.link(seed_input, random.inputs["Seed"])

        combine = nk.n("ShaderNodeCombineXYZ", "Rot Vector", x=x + 200, y=y)
        combine.inputs["X"].default_value = 0.0
        combine.inputs["Y"].default_value = 0.0
        nk.link(random.outputs[0], combine.inputs["Z"])

        return combine

    @staticmethod
    def get_variation_types() -> dict:
        """Get types of natural variation."""
        return {
            "rotation": {
                "method": "Random Value",
                "range": "±15° typical",
                "axes": ["Z (most common)", "X", "Y"]
            },
            "position": {
                "method": "Noise texture",
                "type": "Offset",
                "strength": "0.1-0.3 typical"
            },
            "scale": {
                "method": "Noise texture",
                "type": "Multiply",
                "range": "0.8-1.2 typical"
            }
        }

    @staticmethod
    def get_performance_tips() -> list:
        """Get performance tips for growth systems."""
        return [
            "Start with fewer points",
            "Use realize instances only at end",
            "Keep leaf geometry simple",
            "Avoid excessive recursion levels"
        ]


# Convenience functions
def create_fern(
    leaf_count: int = 20,
    taper_start: float = 1.0,
    taper_end: float = 0.2
) -> FernGrower:
    """
    Quick setup for procedural fern.

    Args:
        leaf_count: Number of leaves
        taper_start: Scale at bottom
        taper_end: Scale at top

    Returns:
        Configured FernGrower with built node tree
    """
    # Create a simple mesh to attach to
    bpy.ops.mesh.primitive_plane_add(size=0.1)
    obj = bpy.context.active_object
    obj.name = "Fern"

    fern = FernGrower.from_object(obj)
    fern.set_leaf_count(leaf_count)
    fern.set_taper(taper_start, taper_end)
    fern.set_rotation_variation(15.0)
    fern.build()
    return fern


def get_fern_workflow() -> list:
    """Get complete fern creation workflow."""
    return [
        "1. Create mesh line (stem base)",
        "2. Add points for leaf positions",
        "3. Create leaf geometry (separate object)",
        "4. Instance leaves on points",
        "5. Map index to scale (tapered)",
        "6. Add rotation variation",
        "7. Subdivide for more detail",
        "8. Add curve to stem for organic feel"
    ]


def get_quick_reference() -> dict:
    """Get quick reference for growth nodes."""
    return {
        "base": {"node": "Mesh Line", "purpose": "Point distribution"},
        "scaling": {"node": "Math (normalize)", "purpose": "Taper effect"},
        "placement": {"node": "Instance on Points", "purpose": "Leaf positioning"},
        "variation": {"node": "Random Value", "purpose": "Natural look"}
    }


class GrowthHUD:
    """
    Heads-Up Display for procedural growth visualization.

    Cross-references:
    - KB Section 34: Blender Growth Tutorial
    """

    @staticmethod
    def display_settings(
        leaf_count: int = 20,
        stem_height: float = 5.0,
        taper_start: float = 1.0,
        taper_end: float = 0.2,
        rotation_variation: float = 15.0,
        leaf_size: float = 0.5,
        seed: int = 42
    ) -> str:
        """Display current growth settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║         FERN GROWTH SETTINGS         ║",
            "╠══════════════════════════════════════╣",
            f"║ Leaf Count:    {leaf_count:>20} ║",
            f"║ Stem Height:   {stem_height:>20.1f} ║",
            f"║ Leaf Size:     {leaf_size:>20.2f} ║",
            f"║ Seed:          {seed:>20} ║",
            "╠══════════════════════════════════════╣",
            "║ TAPER                                ║",
            f"║   Start Scale: {taper_start:>20.2f} ║",
            f"║   End Scale:   {taper_end:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ VARIATION                            ║",
            f"║   Rotation:    {rotation_variation:>17.1f}° ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_taper_formula() -> str:
        """Display the taper calculation formula."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║         TAPER FORMULA                ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  scale = (index / (count - 1))       ║",
            "║         × (end - start) + start      ║",
            "║                                      ║",
            "║  Example (count=20, start=1, end=0.2):",
            "║    index 0:  scale = 1.0             ║",
            "║    index 10: scale = 0.6             ║",
            "║    index 19: scale = 0.2             ║",
            "║                                      ║",
            "║  Result: Leaves get smaller toward   ║",
            "║          the top of the stem         ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for procedural growth."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║         GROWTH NODE FLOW             ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║  [Mesh Line] ← leaf count            ║",
            "║       │                              ║",
            "║  ┌────┴────┐                         ║",
            "║  │         │                         ║",
            "║  ↓         ↓                         ║",
            "║ [Index]  [Count - 1]                 ║",
            "║  │         │                         ║",
            "║  └────┬────┘                         ║",
            "║       ↓                              ║",
            "║  [Math: Divide] ← normalize          ║",
            "║       │                              ║",
            "║  [Math: × (end-start)]               ║",
            "║       │                              ║",
            "║  [Math: + start] → scale             ║",
            "║       │                              ║",
            "║  ┌────┴────────┐                     ║",
            "║  │             │                     ║",
            "║  ↓             ↓                     ║",
            "║ [Leaf Grid]  [Random Rotation]       ║",
            "║  │             │                     ║",
            "║  └──────┬──────┘                     ║",
            "║         ↓                            ║",
            "║  [Instance on Points]                ║",
            "║         │                            ║",
            "║  [Realize Instances]                 ║",
            "║         │                            ║",
            "║  [Group Output]                      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for growth setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║      GROWTH PRE-FLIGHT CHECKLIST     ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Mesh Line created                 ║",
            "║    (provides point distribution)     ║",
            "║                                      ║",
            "║  □ Leaf geometry ready               ║",
            "║    (separate object or grid)         ║",
            "║                                      ║",
            "□  □ Taper values set                  ║",
            "║    (start > end for natural look)    ║",
            "║                                      ║",
            "║  □ Rotation variation configured      ║",
            "║    (10-20° for natural look)         ║",
            "║                                      ║",
            "║  □ Seed set for reproducibility      ║",
            "║                                      ║",
            "║  □ Instance on Points connected       ║",
            "║                                      ║",
            "║  Optional:                            ║",
            "║  □ Add curve to stem                 ║",
            "║  □ Multiple branch levels            ║",
            "║  □ Color variation by index          ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_variation_types() -> str:
        """Display types of natural variation."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       NATURAL VARIATION TYPES        ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  ROTATION (most common):             ║",
            "║    Random Value → Z axis             ║",
            "║    Range: ±15° typical               ║",
            "║                                      ║",
            "║  POSITION:                           ║",
            "║    Noise texture → Offset            ║",
            "║    Strength: 0.1-0.3                 ║",
            "║                                      ║",
            "║  SCALE:                              ║",
            "║    Noise texture → Multiply          ║",
            "║    Range: 0.8-1.2                    ║",
            "║                                      ║",
            "║  TIPS:                               ║",
            "║    • Start with rotation only        ║",
            "║    • Add more for complexity         ║",
            "║    • Keep variation subtle           ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_growth_settings(**kwargs) -> None:
    """Print growth settings to console."""
    print(GrowthHUD.display_settings(**kwargs))
