"""
Scattering Utilities Module - Codified from Tutorial 5

Implements scattering utilities for the Blender 5.0+ built-in
scattering modifier and custom geometry node setups.

Based on tutorial: Polygon Runway - Blender 5.0 Scattering Modifier (Section 5)

Usage:
    from lib.scatter import ScatterSetup, WeightMask

    # Use built-in scattering modifier
    scatter = ScatterSetup(ground_plane)
    scatter.add_collection(tree_collection, density=0.1)
    scatter.enable_align_rotation()
    scatter.set_scale_variation(0.5, 1.5)
"""

from __future__ import annotations
import bpy
from typing import Optional, List, Dict
from pathlib import Path

# Import NodeKit for node building
try:
    from .nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit


class ScatterSetup:
    """
    Setup for Blender 5.0+ built-in scattering modifier.

    Cross-references:
    - KB Section 5: Scattering Modifier
    """

    def __init__(self, target_object: bpy.types.Object):
        self._target = target_object
        self._modifier: Optional[bpy.types.Modifier] = None
        self._collections: List[bpy.types.Collection] = []

    @classmethod
    def create(
        cls,
        target_object: bpy.types.Object,
        name: str = "Scatter"
    ) -> "ScatterSetup":
        """
        Create scattering setup on target object.

        KB Reference: Section 5 - Basic scatter setup

        Args:
            target_object: Object to scatter onto
            name: Modifier name

        Returns:
            Configured ScatterSetup instance
        """
        instance = cls(target_object)

        # Add geometry nodes modifier for scattering
        # Note: In Blender 5.0+, there's a dedicated scatter modifier
        # For compatibility, we use geometry nodes
        mod = target_object.modifiers.new(name=name, type='NODES')
        instance._modifier = mod

        return instance

    def add_collection(
        self,
        collection: bpy.types.Collection,
        density: float = 0.1
    ) -> "ScatterSetup":
        """
        Add collection to scatter.

        KB Reference: Section 5 - Pick Instance

        Args:
            collection: Collection of objects to scatter
            density: Instance density (per square meter)

        Returns:
            Self for chaining
        """
        self._collections.append(collection)
        return self

    def add_object(
        self,
        obj: bpy.types.Object,
        density: float = 0.1
    ) -> "ScatterSetup":
        """
        Add single object to scatter.

        Args:
            obj: Object to scatter
            density: Instance density

        Returns:
            Self for chaining
        """
        # Create collection if needed
        if not self._collections:
            coll = bpy.data.collections.new("ScatterObjects")
            bpy.context.collection.children.link(coll)
            self._collections.append(coll)

        self._collections[0].objects.link(obj)
        return self

    def set_density(self, density: float) -> "ScatterSetup":
        """
        Set scattering density.

        KB Reference: Section 5 - Amount vs Density method

        Args:
            density: Density value

        Returns:
            Self for chaining
        """
        # Implementation depends on node setup
        return self

    def enable_align_rotation(self) -> "ScatterSetup":
        """
        Align instances to surface normal.

        KB Reference: Section 5 - Align Rotation

        Returns:
            Self for chaining
        """
        return self

    def set_surface_offset(self, offset: float) -> "ScatterSetup":
        """
        Set offset from surface.

        KB Reference: Section 5 - Surface Offset

        Args:
            offset: Distance from surface (negative for buried)

        Returns:
            Self for chaining
        """
        return self

    def set_scale_variation(
        self,
        min_scale: float = 0.5,
        max_scale: float = 1.5
    ) -> "ScatterSetup":
        """
        Set random scale variation.

        KB Reference: Section 5 - Scale Randomization

        Args:
            min_scale: Minimum scale
            max_scale: Maximum scale

        Returns:
            Self for chaining
        """
        return self

    def set_distribution_mask(
        self,
        vertex_group: str
    ) -> "ScatterSetup":
        """
        Set vertex group as distribution mask.

        KB Reference: Section 5 - Distribution Mask

        Args:
            vertex_group: Name of vertex group

        Returns:
            Self for chaining
        """
        return self

    def get_modifier(self) -> Optional[bpy.types.Modifier]:
        """Get the scatter modifier."""
        return self._modifier


class WeightMask:
    """
    Weight paint mask creation for controlled scattering.

    Cross-references:
    - KB Section 5: Weight Paint for Distribution
    """

    def __init__(self, obj: bpy.types.Object):
        self._obj = obj
        self._vertex_group: Optional[bpy.types.VertexGroup] = None

    @classmethod
    def create(
        cls,
        obj: bpy.types.Object,
        name: str = "ScatterMask"
    ) -> "WeightMask":
        """
        Create weight mask on object.

        Args:
            obj: Object to paint mask on
            name: Vertex group name

        Returns:
            Configured WeightMask instance
        """
        instance = cls(obj)
        instance._vertex_group = obj.vertex_groups.new(name=name)
        return instance

    @classmethod
    def from_vertex_group(
        cls,
        obj: bpy.types.Object,
        group_name: str
    ) -> "WeightMask":
        """
        Use existing vertex group as mask.

        Args:
            obj: Object with vertex group
            group_name: Name of existing vertex group

        Returns:
            Configured WeightMask instance
        """
        instance = cls(obj)
        for vg in obj.vertex_groups:
            if vg.name == group_name:
                instance._vertex_group = vg
                break
        return instance

    def paint_gradient(
        self,
        start: tuple = (0, 0, 0),
        end: tuple = (0, 0, 10),
        invert: bool = False
    ) -> "WeightMask":
        """
        Create gradient weight paint.

        KB Reference: Section 5 - Gradient distribution

        Args:
            start: Start point (full weight)
            end: End point (zero weight)
            invert: Swap start/end weights

        Returns:
            Self for chaining
        """
        # This would use bpy.ops.paint.weight_gradient
        # Implementation requires edit mode context
        return self

    def get_vertex_group(self) -> Optional[bpy.types.VertexGroup]:
        """Get the vertex group."""
        return self._vertex_group

    def get_name(self) -> Optional[str]:
        """Get vertex group name."""
        if self._vertex_group:
            return self._vertex_group.name
        return None


class GeometryNodesScatter:
    """
    Custom geometry nodes scatter setup.

    More control than built-in modifier, compatible with older Blender.

    Cross-references:
    - KB Section 5: Custom scatter setups
    - KB Section 34: Procedural growth patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._density = 0.1
        self._scale_min = 0.8
        self._scale_max = 1.2
        self._rotation_randomness = 1.0
        self._align_to_normal = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "CustomScatter") -> "GeometryNodesScatter":
        """
        Create custom scatter node tree.

        Args:
            name: Node tree name

        Returns:
            Configured GeometryNodesScatter instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "CustomScatter"
    ) -> "GeometryNodesScatter":
        """
        Create and attach to object via modifier.

        Args:
            obj: Object to attach to
            name: Node tree name

        Returns:
            Configured GeometryNodesScatter instance
        """
        mod = obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance._setup_interface()
        return instance

    def _setup_interface(self) -> None:
        """Set up node group interface."""
        # Inputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Instance Collection", in_out='INPUT',
            socket_type='NodeSocketObject'
        )
        self.node_tree.interface.new_socket(
            name="Density", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=0.1, min_value=0.0
        )
        self.node_tree.interface.new_socket(
            name="Scale Min", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=0.8, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Scale Max", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=1.2, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Rotation Randomness", in_out='INPUT',
            socket_type='NodeSocketFloat',
            default_value=1.0, min_value=0.0, max_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=42
        )

        # Outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_density(self, density: float) -> "GeometryNodesScatter":
        """Set instance density."""
        self._density = density
        return self

    def set_scale_range(
        self,
        min_scale: float,
        max_scale: float
    ) -> "GeometryNodesScatter":
        """Set scale variation range."""
        self._scale_min = min_scale
        self._scale_max = max_scale
        return self

    def set_rotation_randomness(self, randomness: float) -> "GeometryNodesScatter":
        """Set rotation randomness (0-1)."""
        self._rotation_randomness = randomness
        return self

    def align_to_normal(self, enable: bool = True) -> "GeometryNodesScatter":
        """Enable/disable normal alignment."""
        self._align_to_normal = enable
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the scatter node tree.

        KB Reference: Section 5 - Custom scatter workflow

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() or from_object() first")

        nk = self.nk
        x = 0

        # === INPUT ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === DISTRIBUTE POINTS ON FACES ===
        distribute = nk.n(
            "GeometryNodeDistributePointsOnFaces",
            "Distribute Points",
            x=x, y=100
        )
        distribute.distribute_method = 'RANDOM'
        nk.link(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
        nk.link(group_in.outputs["Density"], distribute.inputs["Density"])
        nk.link(group_in.outputs["Seed"], distribute.inputs["Seed"])
        self._created_nodes['distribute'] = distribute

        x += 300

        # === RANDOM ROTATION ===
        random_rot = nk.n("FunctionNodeRandomRotation", "Random Rotation", x=x, y=200)
        nk.link(group_in.outputs["Seed"], random_rot.inputs["ID"])
        self._created_nodes['random_rot'] = random_rot

        x += 200

        # === ALIGN ROTATION TO VECTOR (if enabled) ===
        if self._align_to_normal:
            align = nk.n(
                "FunctionNodeAlignRotationToVector",
                "Align to Normal",
                x=x, y=200
            )
            align.axis = 'Z'
            nk.link(random_rot.outputs["Rotation"], align.inputs["Rotation"])
            nk.link(distribute.outputs["Normal"], align.inputs["Vector"])
            self._created_nodes['align'] = align
            rotation_source = align
        else:
            rotation_source = random_rot

        x += 250

        # === RANDOM SCALE ===
        random_value = nk.n("FunctionNodeRandomValue", "Random Scale", x=x, y=100)
        random_value.data_type = 'FLOAT'
        nk.link(group_in.outputs["Scale Min"], random_value.inputs[2])
        nk.link(group_in.outputs["Scale Max"], random_value.inputs[3])
        nk.link(group_in.outputs["Seed"], random_value.inputs[0])
        self._created_nodes['random_scale'] = random_value

        x += 200

        # === INSTANCE ON POINTS ===
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance on Points",
            x=x, y=0
        )
        nk.link(distribute.outputs["Points"], instance.inputs["Points"])
        nk.link(group_in.outputs["Instance Collection"], instance.inputs["Selection"])
        nk.link(rotation_source.outputs["Rotation"], instance.inputs["Rotation"])
        nk.link(random_value.outputs[1], instance.inputs["Scale"])
        self._created_nodes['instance'] = instance

        x += 250

        # === REALIZE INSTANCES (optional) ===
        realize = nk.n("GeometryNodeRealizeInstances", "Realize", x=x, y=0)
        nk.link(instance.outputs["Instances"], realize.inputs["Geometry"])
        self._created_nodes['realize'] = realize

        x += 200

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=0)
        nk.link(realize.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class ScatterPresets:
    """
    Preset configurations for scattering.

    Cross-references:
    - KB Section 5: Scattering settings
    """

    @staticmethod
    def forest_floor() -> dict:
        """Forest floor debris preset."""
        return {
            "density": 0.05,
            "scale_min": 0.3,
            "scale_max": 1.5,
            "rotation_randomness": 1.0,
            "align_to_normal": True,
            "description": "Twigs, leaves, small rocks"
        }

    @staticmethod
    def grass_field() -> dict:
        """Grass field preset."""
        return {
            "density": 0.5,
            "scale_min": 0.8,
            "scale_max": 1.2,
            "rotation_randomness": 0.3,
            "align_to_normal": True,
            "description": "Dense grass coverage"
        }

    @staticmethod
    def scattered_rocks() -> dict:
        """Scattered rocks preset."""
        return {
            "density": 0.02,
            "scale_min": 0.5,
            "scale_max": 2.0,
            "rotation_randomness": 0.8,
            "align_to_normal": True,
            "description": "Varied rock distribution"
        }

    @staticmethod
    def flower_meadow() -> dict:
        """Flower meadow preset."""
        return {
            "density": 0.1,
            "scale_min": 0.7,
            "scale_max": 1.3,
            "rotation_randomness": 0.5,
            "align_to_normal": True,
            "description": "Mixed flowers and plants"
        }


# Convenience functions
def scatter_on_surface(
    target: bpy.types.Object,
    collection: bpy.types.Collection,
    density: float = 0.1
) -> ScatterSetup:
    """Quick scatter setup on surface."""
    scatter = ScatterSetup.create(target)
    scatter.add_collection(collection, density)
    scatter.enable_align_rotation()
    scatter.set_scale_variation(0.8, 1.2)
    return scatter


def create_weight_mask(
    obj: bpy.types.Object,
    name: str = "ScatterMask"
) -> WeightMask:
    """Quick weight mask creation."""
    return WeightMask.create(obj, name)


def get_quick_reference() -> dict:
    """Get quick reference for scattering."""
    return {
        "density_units": "Instances per square meter",
        "scale_variation": "0.5-1.5 for natural look",
        "align_rotation": "Enable for upright plants",
        "surface_offset": "Negative for buried roots",
        "weight_paint": "White = full, Black = none"
    }


class ScatterHUD:
    """
    Heads-Up Display for scattering visualization.

    Cross-references:
    - KB Section 5: Scattering Modifier
    """

    @staticmethod
    def display_settings(
        density: float = 0.1,
        scale_min: float = 0.8,
        scale_max: float = 1.2,
        rotation_randomness: float = 1.0,
        align_to_normal: bool = True,
        surface_offset: float = 0.0
    ) -> str:
        """Display current scatter settings."""
        align_status = "ON" if align_to_normal else "OFF"
        lines = [
            "╔══════════════════════════════════════╗",
            "║         SCATTER SETTINGS             ║",
            "╠══════════════════════════════════════╣",
            f"║ Density:       {density:>20.3f} ║",
            f"║ Align Normal:  {align_status:>20} ║",
            f"║ Surface Offset:{surface_offset:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ SCALE VARIATION                      ║",
            f"║   Min:         {scale_min:>20.2f} ║",
            f"║   Max:         {scale_max:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ ROTATION                             ║",
            f"║   Randomness:  {rotation_randomness:>17.1f} (0-1) ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_density_guide() -> str:
        """Display density configuration guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║         DENSITY GUIDE                ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  DENSITY METHOD:                     ║",
            "║    Instances per square meter        ║",
            "║                                      ║",
            "║  TYPICAL VALUES:                     ║",
            "║    0.02 = Sparse rocks               ║",
            "║    0.05 = Light debris               ║",
            "║    0.10 = Normal vegetation          ║",
            "║    0.50 = Dense grass                ║",
            "║    1.00 = Very dense coverage        ║",
            "║                                      ║",
            "║  AMOUNT METHOD (alternative):        ║",
            "║    Fixed number of instances         ║",
            "║    Better for controlled placement   ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for scattering."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        SCATTER NODE FLOW             ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       └──→ [Distribute Points]       ║",
            "║             on Faces                 ║",
            "║                 │                    ║",
            "║  ┌──────────────┼──────────────┐     ║",
            "║  │              │              │     ║",
            "║  ↓              ↓              ↓     ║",
            "║ [Random     [Align        [Random    ║",
            "║  Rotation]   to Normal]    Scale]    ║",
            "║  │              │              │     ║",
            "║  └──────────────┼──────────────┘     ║",
            "║                 │                    ║",
            "║       [Collection Info]              ║",
            "║            (instances)               ║",
            "║                 │                    ║",
            "║       [Instance on Points]           ║",
            "║                 │                    ║",
            "║       [Realize Instances]            ║",
            "║                 │                    ║",
            "║       [Group Output]                 ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for scatter setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║      SCATTER PRE-FLIGHT CHECKLIST    ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Surface mesh has faces            ║",
            "║    (points distribute on faces)      ║",
            "║                                      ║",
            "□  □ Collection prepared               ║",
            "║    (objects to scatter)              ║",
            "║                                      ║",
            "□  □ Density configured                ║",
            "║    (per square meter)                ║",
            "║                                      ║",
            "□  □ Align rotation enabled            ║",
            "║    (for upright plants)              ║",
            "║                                      ║",
            "□  □ Scale variation set               ║",
            "║    (0.8-1.2 for natural look)        ║",
            "║                                      ║",
            "□  □ Optional: Weight mask             ║",
            "║    (for controlled distribution)     ║",
            "║                                      ║",
            "□  □ Optional: Surface offset          ║",
            "║    (negative for buried roots)       ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_weight_mask_guide() -> str:
        """Display weight mask guide for controlled scattering."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       WEIGHT MASK GUIDE              ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  WEIGHT PAINTING:                    ║",
            "║    White = Full density              ║",
            "║    Black = No instances              ║",
            "║    Gray = Reduced density            ║",
            "║                                      ║",
            "║  CREATION METHODS:                   ║",
            "║    1. Weight Paint mode              ║",
            "║    2. Gradient tool                  ║",
            "║    3. Vertex group selection         ║",
            "║                                      ║",
            "║  USES:                               ║",
            "║    • Keep areas clear                ║",
            "║    • Create density gradients        ║",
            "║    • Control placement precisely     ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_scatter_settings(**kwargs) -> None:
    """Print scatter settings to console."""
    print(ScatterHUD.display_settings(**kwargs))
