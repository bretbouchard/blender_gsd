"""
Procedural Crystals Module - Codified from Tutorial 23

Implements procedural crystal creation using geometry nodes with
curve profiles, noise displacement, and surface scattering.

Based on Johnny Matthews tutorial: https://www.youtube.com/watch?v=R9G3x6jpTAE

Usage:
    from lib.crystals import CrystalGenerator

    # Create procedural crystals
    crystals = CrystalGenerator.create("MyCrystals")
    crystals.set_sides(6)  # Hexagonal crystals
    crystals.set_height(2.0)
    crystals.set_radius(0.3)
    crystals.add_imperfections(scale=0.5, strength=0.1)
    tree = crystals.build()

    # Or scatter on a surface
    scatter = CrystalScatter.create("CrystalField")
    scatter.set_surface(ground_plane)
    scatter.set_crystal_collection(crystals_collection)
    scatter.set_density(50)
    tree = scatter.build()
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


class CrystalGenerator:
    """
    Procedural crystal creation using geometry nodes.

    Creates a node tree that:
    - Creates curve line for crystal height
    - Converts to mesh with polygon profile (triangle to hexagon)
    - Adds noise displacement for imperfections
    - Optionally adds facet detection for shader

    Cross-references:
    - KB Section 23: Geometry Nodes Crystals (Johnny Matthews)
    - KB Section 36: Glass flowers (similar organic approach)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._sides = 6  # Hexagonal
        self._height = 2.0
        self._radius = 0.3
        self._imperfections_enabled = False
        self._imperfection_scale = 0.5
        self._imperfection_strength = 0.1
        self._imperfection_detail = 2.0
        self._taper_enabled = True
        self._taper_top = 0.0  # Point at top
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "CrystalGenerator") -> "CrystalGenerator":
        """
        Create a new geometry node tree for crystal generation.

        Args:
            name: Name for the node group

        Returns:
            Configured CrystalGenerator instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "CrystalGenerator"
    ) -> "CrystalGenerator":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach to
            name: Name for the node group

        Returns:
            Configured CrystalGenerator instance
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
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Sides", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._sides, min_value=3, max_value=12
        )
        self.node_tree.interface.new_socket(
            name="Height", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._height, min_value=0.1, max_value=20.0
        )
        self.node_tree.interface.new_socket(
            name="Radius", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._radius, min_value=0.01, max_value=5.0
        )
        self.node_tree.interface.new_socket(
            name="Taper", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._taper_top, min_value=0.0, max_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Imperfection Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._imperfection_scale, min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Imperfection Strength", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._imperfection_strength, min_value=0.0, max_value=1.0
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_sides(self, sides: int) -> "CrystalGenerator":
        """
        Set number of sides for crystal profile.

        Args:
            sides: 3=triangle, 4=square, 6=hexagonal
        """
        self._sides = max(3, min(12, sides))
        return self

    def set_height(self, height: float) -> "CrystalGenerator":
        """Set crystal height."""
        self._height = height
        return self

    def set_radius(self, radius: float) -> "CrystalGenerator":
        """Set crystal base radius/thickness."""
        self._radius = radius
        return self

    def add_imperfections(
        self,
        scale: float = 0.5,
        strength: float = 0.1,
        detail: float = 2.0
    ) -> "CrystalGenerator":
        """
        Add noise-based surface imperfections.

        Args:
            scale: Noise scale (lower = larger features)
            strength: Displacement strength
            detail: Noise detail
        """
        self._imperfections_enabled = True
        self._imperfection_scale = scale
        self._imperfection_strength = strength
        self._imperfection_detail = detail
        return self

    def set_taper(self, top_scale: float = 0.0) -> "CrystalGenerator":
        """
        Set taper for crystal (0 = pointed, 1 = uniform).

        Args:
            top_scale: Scale at top (0.0 = sharp point)
        """
        self._taper_enabled = True
        self._taper_top = top_scale
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for crystal generation.

        KB Reference: Section 23 - Geometry Nodes Crystals

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

        # === CURVE LINE FOR CRYSTAL HEIGHT ===
        # KB Reference: Section 23 - Curve Line base
        curve_line = nk.n(
            "GeometryNodeCurveLine",
            "Crystal Height",
            x=x, y=100
        )
        curve_line.inputs["Start"].default_value = (0, 0, 0)
        # End point will be driven by height input
        # We need a combine XYZ for the end point
        end_point = nk.n("ShaderNodeCombineXYZ", "End Point", x=x, y=-50)
        nk.link(group_in.outputs["Height"], end_point.inputs["Z"])
        nk.link(end_point.outputs["Vector"], curve_line.inputs["End"])
        self._created_nodes['curve_line'] = curve_line
        self._created_nodes['end_point'] = end_point

        x += 200

        # === SET CURVE RADIUS (TAPER) ===
        if self._taper_enabled:
            # KB Reference: Section 23 - Taper effect
            # Use spline parameter for taper
            spline_param = nk.n(
                "GeometryNodeSplineParameter",
                "Spline Param",
                x=x, y=0
            )
            self._created_nodes['spline_param'] = spline_param

            # Map parameter to radius (bottom=full, top=taper)
            taper_map = nk.n(
                "ShaderNodeMapRange",
                "Taper Map",
                x=x + 150, y=0
            )
            taper_map.inputs["From Min"].default_value = 0.0
            taper_map.inputs["From Max"].default_value = 1.0
            taper_map.inputs["To Min"].default_value = 1.0  # Full at bottom
            nk.link(group_in.outputs["Taper"], taper_map.inputs["To Max"])  # Taper at top
            nk.link(spline_param.outputs["Factor"], taper_map.inputs["Value"])
            self._created_nodes['taper_map'] = taper_map

            # Multiply by radius
            radius_mult = nk.n("ShaderNodeMath", "Tapered Radius", x=x + 300, y=0)
            radius_mult.operation = 'MULTIPLY'
            nk.link(taper_map.outputs[0], radius_mult.inputs[0])
            nk.link(group_in.outputs["Radius"], radius_mult.inputs[1])
            self._created_nodes['radius_mult'] = radius_mult

            # Set curve radius
            set_radius = nk.n(
                "GeometryNodeSetCurveRadius",
                "Set Radius",
                x=x + 450, y=100
            )
            nk.link(curve_line.outputs["Curve"], set_radius.inputs["Curve"])
            nk.link(radius_mult.outputs[0], set_radius.inputs["Radius"])
            self._created_nodes['set_radius'] = set_radius

            curve_out = set_radius
            x += 650
        else:
            curve_out = curve_line
            x += 200

        self._created_nodes['curve_out'] = curve_out

        # === CREATE PROFILE CURVE ===
        # KB Reference: Section 23 - Curve Circle with low vertices
        profile = nk.n(
            "GeometryNodeCurveCircle",
            "Profile",
            x=x, y=-100
        )
        # Connect sides input
        nk.link(group_in.outputs["Sides"], profile.inputs["Resolution"])
        profile.inputs["Resolution"].default_value = self._sides
        profile.inputs["Radius"].default_value = 1.0
        self._created_nodes['profile'] = profile

        x += 200

        # === CURVE TO MESH ===
        # KB Reference: Section 23 - Convert curve to mesh with profile
        curve_to_mesh = nk.n(
            "GeometryNodeCurveToMesh",
            "Curve to Mesh",
            x=x, y=100
        )
        nk.link(curve_out.outputs["Curve"], curve_to_mesh.inputs["Curve"])
        nk.link(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
        self._created_nodes['curve_to_mesh'] = curve_to_mesh

        x += 250

        # === OPTIONAL: IMPERFECTIONS ===
        if self._imperfections_enabled:
            # KB Reference: Section 23 - Noise displacement
            # Get position for noise input
            position = nk.n(
                "GeometryNodeInputPosition",
                "Position",
                x=x, y=-100
            )
            self._created_nodes['position'] = position

            # Noise texture
            noise = nk.n(
                "ShaderNodeTexNoise",
                "Imperfection Noise",
                x=x + 150, y=0
            )
            noise.inputs["Scale"].default_value = self._imperfection_scale
            noise.inputs["Detail"].default_value = self._imperfection_detail
            nk.link(group_in.outputs["Imperfection Scale"], noise.inputs["Scale"])
            nk.link(position.outputs["Position"], noise.inputs["Vector"])
            self._created_nodes['noise'] = noise

            # Vector math for displacement
            noise_strength = nk.n(
                "ShaderNodeVectorMath",
                "Noise Strength",
                x=x + 350, y=0
            )
            noise_strength.operation = 'SCALE'
            nk.link(noise.outputs["Color"], noise_strength.inputs["Vector"])
            nk.link(group_in.outputs["Imperfection Strength"], noise_strength.inputs["Scale"])
            self._created_nodes['noise_strength'] = noise_strength

            # Set position with noise offset
            set_position = nk.n(
                "GeometryNodeSetPosition",
                "Add Imperfections",
                x=x + 550, y=100
            )
            nk.link(curve_to_mesh.outputs["Mesh"], set_position.inputs["Geometry"])
            nk.link(noise_strength.outputs["Vector"], set_position.inputs["Offset"])
            self._created_nodes['set_position'] = set_position

            crystal_mesh = set_position
            x += 750
        else:
            crystal_mesh = curve_to_mesh
            x += 200

        self._created_nodes['crystal_mesh'] = crystal_mesh

        # === SET SHADE SMOOTH ===
        shade_smooth = nk.n(
            "GeometryNodeSetShadeSmooth",
            "Shade Smooth",
            x=x, y=100
        )
        shade_smooth.inputs["Shade Smooth"].default_value = True
        nk.link(crystal_mesh.outputs["Mesh"] if hasattr(crystal_mesh, 'outputs') and "Mesh" in crystal_mesh.outputs else crystal_mesh.outputs["Geometry"], shade_smooth.inputs["Geometry"])
        self._created_nodes['shade_smooth'] = shade_smooth

        x += 200

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(shade_smooth.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class CrystalScatter:
    """
    Scatter crystals on a surface with variation.

    Cross-references:
    - KB Section 23: Scattering on objects
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._surface: Optional[bpy.types.Object] = None
        self._crystal_collection: Optional[bpy.types.Collection] = None
        self._density = 50
        self._scale_min = 0.5
        self._scale_max = 1.5
        self._rotation_random = True
        self._align_to_normal = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "CrystalScatter") -> "CrystalScatter":
        """Create a new geometry node tree for crystal scattering."""
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "CrystalScatter"
    ) -> "CrystalScatter":
        """Create and attach to a surface object."""
        mod = obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance._setup_interface()
        instance._surface = obj
        return instance

    def _setup_interface(self) -> None:
        """Set up the node group interface."""
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Crystal Collection", in_out='INPUT', socket_type='NodeSocketCollection'
        )
        self.node_tree.interface.new_socket(
            name="Density", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._density, min_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Scale Min", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._scale_min, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Scale Max", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._scale_max, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Random Rotation", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=self._rotation_random
        )
        self.node_tree.interface.new_socket(
            name="Align to Normal", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=self._align_to_normal
        )

        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_surface(self, obj: bpy.types.Object) -> "CrystalScatter":
        """Set the surface mesh to scatter on."""
        self._surface = obj
        return self

    def set_crystal_collection(self, collection: bpy.types.Collection) -> "CrystalScatter":
        """Set the collection containing crystal geometry."""
        self._crystal_collection = collection
        return self

    def set_density(self, density: float) -> "CrystalScatter":
        """Set scatter density."""
        self._density = density
        return self

    def set_scale_range(self, min_scale: float, max_scale: float) -> "CrystalScatter":
        """Set scale variation range."""
        self._scale_min = min_scale
        self._scale_max = max_scale
        return self

    def build(self) -> bpy.types.NodeTree:
        """Build the crystal scatter node tree."""
        if not self.nk:
            raise RuntimeError("Call create() or from_object() first")

        nk = self.nk
        x = 0

        # Input
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # Distribute points on faces
        distribute = nk.n(
            "GeometryNodeDistributePointsOnFaces",
            "Distribute Points",
            x=x, y=100
        )
        nk.link(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
        nk.link(group_in.outputs["Density"], distribute.inputs["Density"])
        self._created_nodes['distribute'] = distribute

        x += 250

        # Collection info for crystals
        crystal_info = nk.n(
            "GeometryNodeCollectionInfo",
            "Crystal Collection",
            x=x, y=200
        )
        nk.link(group_in.outputs["Crystal Collection"], crystal_info.inputs["Collection"])
        self._created_nodes['crystal_info'] = crystal_info

        x += 200

        # Random scale
        random_scale = nk.n(
            "FunctionNodeRandomValue",
            "Random Scale",
            x=x, y=-100
        )
        random_scale.data_type = 'FLOAT'
        nk.link(group_in.outputs["Scale Min"], random_scale.inputs[2])  # Min
        nk.link(group_in.outputs["Scale Max"], random_scale.inputs[3])  # Max
        self._created_nodes['random_scale'] = random_scale

        x += 200

        # Instance on points
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance Crystals",
            x=x, y=100
        )
        nk.link(distribute.outputs["Points"], instance.inputs["Points"])
        nk.link(crystal_info.outputs["Instances"], instance.inputs["Instance"])
        nk.link(random_scale.outputs[0], instance.inputs["Scale"])
        self._created_nodes['instance'] = instance

        x += 250

        # Output
        group_out = nk.group_output(x=x, y=100)
        nk.link(instance.outputs["Instances"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree


class CrystalPresets:
    """
    Preset configurations for common crystal types.

    Cross-references:
    - KB Section 23: Crystal types
    """

    @staticmethod
    def quartz() -> dict:
        """Configuration for quartz crystals."""
        return {
            "sides": 6,  # Hexagonal
            "height": 2.0,
            "radius": 0.3,
            "taper": 0.0,  # Sharp point
            "imperfection_scale": 0.5,
            "imperfection_strength": 0.1,
        }

    @staticmethod
    def amethyst() -> dict:
        """Configuration for amethyst crystals."""
        return {
            "sides": 6,
            "height": 1.5,
            "radius": 0.25,
            "taper": 0.1,
            "imperfection_scale": 0.3,
            "imperfection_strength": 0.15,
        }

    @staticmethod
    def bismuth() -> dict:
        """Configuration for bismuth hopper crystals."""
        return {
            "sides": 4,  # Square
            "height": 1.0,
            "radius": 0.5,
            "taper": 0.3,
            "imperfection_scale": 0.8,
            "imperfection_strength": 0.2,
        }

    @staticmethod
    def ice() -> dict:
        """Configuration for ice crystals."""
        return {
            "sides": 6,
            "height": 3.0,
            "radius": 0.15,
            "taper": 0.0,
            "imperfection_scale": 0.2,
            "imperfection_strength": 0.05,
        }


# Convenience functions
def create_crystal(
    obj: bpy.types.Object,
    sides: int = 6,
    height: float = 2.0,
    radius: float = 0.3
) -> CrystalGenerator:
    """
    Quick setup for procedural crystal.

    Args:
        obj: Object to attach crystal generator to
        sides: Number of sides (3-12)
        height: Crystal height
        radius: Base radius

    Returns:
        Configured CrystalGenerator with built node tree
    """
    crystal = CrystalGenerator.from_object(obj)
    crystal.set_sides(sides)
    crystal.set_height(height)
    crystal.set_radius(radius)
    crystal.set_taper(0.0)
    crystal.add_imperfections(scale=0.5, strength=0.1)
    crystal.build()
    return crystal


def create_crystal_field(
    surface: bpy.types.Object,
    crystal_collection: bpy.types.Collection,
    density: float = 50
) -> CrystalScatter:
    """
    Quick setup for crystal scattering on surface.

    Args:
        surface: Surface mesh to scatter on
        crystal_collection: Collection with crystal geometry
        density: Scatter density

    Returns:
        Configured CrystalScatter with built node tree
    """
    scatter = CrystalScatter.from_object(surface)
    scatter.set_crystal_collection(crystal_collection)
    scatter.set_density(density)
    scatter.set_scale_range(0.5, 1.5)
    scatter.build()
    return scatter


def create_hexagonal_crystal(obj: bpy.types.Object, height: float = 2.0) -> CrystalGenerator:
    """Create a classic hexagonal crystal."""
    return create_crystal(obj, sides=6, height=height, radius=0.3)


def create_triangular_crystal(obj: bpy.types.Object, height: float = 1.5) -> CrystalGenerator:
    """Create a triangular crystal."""
    return create_crystal(obj, sides=3, height=height, radius=0.4)


class CrystalHUD:
    """
    Heads-Up Display for procedural crystal visualization.

    Cross-references:
    - KB Section 23: Geometry Nodes Crystals
    """

    @staticmethod
    def display_settings(
        sides: int = 6,
        height: float = 2.0,
        radius: float = 0.3,
        taper: float = 0.0,
        imperfection_scale: float = 0.5,
        imperfection_strength: float = 0.1
    ) -> str:
        """Display current crystal settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        CRYSTAL GENERATOR             ║",
            "╠══════════════════════════════════════╣",
            f"║ Sides:         {sides:>20} ║",
            f"║ Height:        {height:>20.2f} ║",
            f"║ Radius:        {radius:>20.2f} ║",
            f"║ Taper:         {taper:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ IMPERFECTIONS                        ║",
            f"║   Scale:       {imperfection_scale:>20.2f} ║",
            f"║   Strength:    {imperfection_strength:>20.2f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_sides_guide() -> str:
        """Display crystal sides configuration guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║          CRYSTAL SIDES               ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  3 = Triangle (sharp, pointed)       ║",
            "║  4 = Square (blocky, bismuth-like)   ║",
            "║  5 = Pentagon (rare, unusual)        ║",
            "║  6 = Hexagonal (quartz, amethyst)    ║",
            "║  8 = Octagon (subtle, faceted)       ║",
            "║                                      ║",
            "║  NATURAL CRYSTALS:                   ║",
            "║    Quartz:     6 sides               ║",
            "║    Amethyst:   6 sides               ║",
            "║    Bismuth:    4 sides (hopper)      ║",
            "║    Ice:        6 sides               ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for crystal generation."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        CRYSTAL NODE FLOW             ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║  [Curve Line] ← height (Z end)       ║",
            "║       │                              ║",
            "║  [Spline Parameter]                  ║",
            "║       │                              ║",
            "║  [Map Range] ← taper (0→1)           ║",
            "║       │                              ║",
            "║  [Math × Radius]                     ║",
            "║       │                              ║",
            "║  [Set Curve Radius]                  ║",
            "║       │                              ║",
            "║  ┌────┴────┐                         ║",
            "║  │         │                         ║",
            "║  ↓         ↓                         ║",
            "║ [Curve  [Curve Circle]               ║",
            "║  Line]     (profile)                 ║",
            "║  │         │                         ║",
            "║  └────┬────┘                         ║",
            "║       ↓                              ║",
            "║  [Curve to Mesh]                     ║",
            "║       │                              ║",
            "║  Optional: [Position + Noise]        ║",
            "║       │                              ║",
            "║  [Set Shade Smooth]                  ║",
            "║       │                              ║",
            "║  [Group Output]                      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for crystal setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║      CRYSTAL PRE-FLIGHT CHECKLIST    ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Sides configured (3-12)           ║",
            "║    (6 for natural quartz look)       ║",
            "║                                      ║",
            "║  □ Height set appropriately          ║",
            "║    (1-5 for typical crystals)        ║",
            "║                                      ║",
            "║  □ Radius configured                 ║",
            "║    (0.1-0.5 for slender to thick)    ║",
            "║                                      ║",
            "║  □ Taper set (0 = sharp point)       ║",
            "║    (0.0-0.3 for natural crystals)    ║",
            "║                                      ║",
            "║  □ Optional: Imperfections added     ║",
            "║    (for natural, organic look)       ║",
            "║                                      ║",
            "║  □ Shade smooth enabled              ║",
            "║    (for faceted crystal appearance)  ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_presets() -> str:
        """Display crystal preset options."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        CRYSTAL PRESETS               ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  QUARTZ (default):                   ║",
            "║    sides=6, height=2.0, radius=0.3   ║",
            "║    taper=0.0, sharp point            ║",
            "║                                      ║",
            "║  AMETHYST:                           ║",
            "║    sides=6, height=1.5, radius=0.25  ║",
            "║    taper=0.1, purple material        ║",
            "║                                      ║",
            "║  BISMUTH:                            ║",
            "║    sides=4, height=1.0, radius=0.5   ║",
            "║    taper=0.3, rainbow material       ║",
            "║                                      ║",
            "║  ICE:                                ║",
            "║    sides=6, height=3.0, radius=0.15  ║",
            "║    taper=0.0, transparent material   ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_crystal_settings(**kwargs) -> None:
    """Print crystal settings to console."""
    print(CrystalHUD.display_settings(**kwargs))
