"""
Generative Geometry Patterns Module - Codified from Tutorials 2, 15

Implements generative art patterns using geometry nodes including
radial arrays, wave fields, and procedural patterns.

Based on tutorials:
- Ducky 3D: Geometric Minimalism (Section 2)
- RADIUM: Complete Geometry Nodes Reference (Section 15)

Usage:
    from lib.geometry import RadialArray, WaveField, IndexAnimation

    # Create radial cube rotation
    radial = RadialArray.create("RadialPattern")
    radial.set_count(80)
    radial.set_radius(7.0)
    radial.animate_by_index(factor=3)
    tree = radial.build()
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


class RadialArray:
    """
    Radial array with index-based animation.

    Creates patterns like the cube rotation from geometric minimalism tutorials.

    Cross-references:
    - KB Section 2: Radial Cube Rotation
    - KB Section 15: Geometry nodes patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._count = 80
        self._radius = 7.0
        self._instance_type = 'CUBE'
        self._instance_size = (32.0, 3.3, 3.3)
        self._rotation_factor = 3  # Index multiplier
        self._animate_rotation = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "RadialArray") -> "RadialArray":
        """
        Create radial array node tree.

        KB Reference: Section 2 - Tutorial 1: Radial Cube Rotation

        Args:
            name: Node tree name

        Returns:
            Configured RadialArray instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "RadialArray"
    ) -> "RadialArray":
        """
        Create and attach to object via modifier.

        Args:
            obj: Object to attach to
            name: Node tree name

        Returns:
            Configured RadialArray instance
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
            name="Count", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._count, min_value=2
        )
        self.node_tree.interface.new_socket(
            name="Radius", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._radius, min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Rotation Factor", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._rotation_factor
        )

        # Outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_count(self, count: int) -> "RadialArray":
        """Set number of instances."""
        self._count = count
        return self

    def set_radius(self, radius: float) -> "RadialArray":
        """Set circle radius."""
        self._radius = radius
        return self

    def set_instance_size(self, x: float, y: float, z: float) -> "RadialArray":
        """Set instance dimensions."""
        self._instance_size = (x, y, z)
        return self

    def animate_by_index(self, factor: int = 3) -> "RadialArray":
        """
        Enable index-based rotation animation.

        KB Reference: Section 2 - Index Math for rotation

        Args:
            factor: Index multiplier (3 = spiral, 5 = more rotations)

        Returns:
            Self for chaining
        """
        self._animate_rotation = True
        self._rotation_factor = factor
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the radial array node tree.

        KB Reference: Section 2 - Radial Cube Rotation setup

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

        # === CURVE CIRCLE ===
        circle = nk.n("GeometryNodeCurvePrimitiveCircle", "Circle", x=x, y=100)
        circle.mode = 'POINTS'
        nk.link(group_in.outputs["Radius"], circle.inputs["Radius"])
        nk.link(group_in.outputs["Count"], circle.inputs["Points"])
        self._created_nodes['circle'] = circle

        x += 250

        # === CURVE TO POINTS (for proper tangent/normal) ===
        # KB Reference: Section 2 - Curve tangent alignment
        curve_to_points = nk.n(
            "GeometryNodeCurveToPoints",
            "Curve to Points",
            x=x, y=100
        )
        curve_to_points.mode = 'COUNT'
        nk.link(group_in.outputs["Count"], curve_to_points.inputs["Count"])
        nk.link(circle.outputs["Curve"], curve_to_points.inputs["Curve"])
        self._created_nodes['curve_to_points'] = curve_to_points

        x += 250

        # === CUBE INSTANCE ===
        cube = nk.n("GeometryNodeMeshCube", "Cube", x=x, y=200)
        cube.inputs["Size X"].default_value = self._instance_size[0]
        cube.inputs["Size Y"].default_value = self._instance_size[1]
        cube.inputs["Size Z"].default_value = self._instance_size[2]
        self._created_nodes['cube'] = cube

        x += 200

        # === ALIGN ROTATION TO VECTOR (using tangent) ===
        # KB Reference: Section 2 - Align Rotation to Vector
        align = nk.n(
            "FunctionNodeAlignRotationToVector",
            "Align to Tangent",
            x=x, y=100
        )
        align.axis = 'Y'
        align.factor = 1.0
        nk.link(curve_to_points.outputs["Tangent"], align.inputs["Vector"])
        self._created_nodes['align'] = align

        x += 250

        # === INDEX-BASED ROTATION ===
        if self._animate_rotation:
            # Get index
            index = nk.n("GeometryNodeInputIndex", "Index", x=x, y=200)
            self._created_nodes['index'] = index

            x += 150

            # Multiply by factor
            multiply = nk.n("ShaderNodeMath", "× Factor", x=x, y=200)
            multiply.operation = 'MULTIPLY'
            multiply.inputs[1].default_value = float(self._rotation_factor)
            nk.link(index.outputs["Index"], multiply.inputs[0])
            self._created_nodes['multiply'] = multiply

            x += 150

            # Add to alignment rotation (combine rotations)
            # Use vector math to add rotation around X axis
            combine = nk.n("ShaderNodeCombineXYZ", "Index Rotation", x=x, y=150)
            nk.link(multiply.outputs[0], combine.inputs["X"])
            self._created_nodes['combine_rot'] = combine

            # Rotate Euler to add index rotation
            rotate = nk.n("FunctionNodeRotateEuler", "Add Rotation", x=x + 200, y=100)
            rotate.type = 'EULER'
            nk.link(align.outputs["Rotation"], rotate.inputs["Rotation"])
            nk.link(combine.outputs["Vector"], rotate.inputs["Rotate By"])
            self._created_nodes['rotate'] = rotate

            rotation_source = rotate
        else:
            rotation_source = align

        x += 400

        # === INSTANCE ON POINTS ===
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance on Points",
            x=x, y=0
        )
        nk.link(curve_to_points.outputs["Points"], instance.inputs["Points"])
        nk.link(cube.outputs["Mesh"], instance.inputs["Instance"])
        nk.link(rotation_source.outputs["Rotation"], instance.inputs["Rotation"])
        self._created_nodes['instance'] = instance

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=0)
        nk.link(instance.outputs["Instances"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class WaveField:
    """
    Cylindrical wave field with gradient scale control.

    Cross-references:
    - KB Section 2: Tutorial 2: Cylindrical Wave Field
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._count = 21
        self._cylinder_vertices = 80
        self._cylinder_radius = 2.0
        self._cylinder_depth = 0.7
        self._gradient_scale = 2.0
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "WaveField") -> "WaveField":
        """
        Create wave field node tree.

        KB Reference: Section 2 - Cylindrical Wave Field

        Args:
            name: Node tree name

        Returns:
            Configured WaveField instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
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
            name="Count", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._count, min_value=1
        )
        self.node_tree.interface.new_socket(
            name="Gradient Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._gradient_scale
        )

        # Outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_count(self, count: int) -> "WaveField":
        """Set number of cylinders."""
        self._count = count
        return self

    def set_cylinder_params(
        self,
        vertices: int = 80,
        radius: float = 2.0,
        depth: float = 0.7
    ) -> "WaveField":
        """Set cylinder parameters."""
        self._cylinder_vertices = vertices
        self._cylinder_radius = radius
        self._cylinder_depth = depth
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the wave field node tree.

        KB Reference: Section 2 - Gradient Texture Scale Control

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() first")

        nk = self.nk
        x = 0

        # === INPUT ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === MESH LINE ===
        mesh_line = nk.n("GeometryNodeMeshLine", "Mesh Line", x=x, y=100)
        mesh_line.count_mode = 'TOTAL'
        nk.link(group_in.outputs["Count"], mesh_line.inputs["Count"])
        self._created_nodes['mesh_line'] = mesh_line

        x += 250

        # === CYLINDER INSTANCE ===
        cylinder = nk.n("GeometryNodeMeshCylinder", "Cylinder", x=x, y=200)
        cylinder.inputs["Vertices"].default_value = self._cylinder_vertices
        cylinder.inputs["Radius"].default_value = self._cylinder_radius
        cylinder.inputs["Depth"].default_value = self._cylinder_depth
        # Note: fill_type would need to be set via enum
        self._created_nodes['cylinder'] = cylinder

        x += 200

        # === POSITION → GRADIENT ===
        # Position input
        position = nk.n("GeometryNodeInputPosition", "Position", x=x, y=100)
        self._created_nodes['position'] = position

        x += 150

        # Multiply for scale control
        scale_mult = nk.n("ShaderNodeMath", "Scale", x=x, y=100)
        scale_mult.operation = 'MULTIPLY'
        nk.link(group_in.outputs["Gradient Scale"], scale_mult.inputs[0])
        self._created_nodes['scale_mult'] = scale_mult

        x += 150

        # Gradient texture (spherical)
        gradient = nk.n("ShaderNodeTexGradient", "Gradient", x=x, y=100)
        gradient.gradient_type = 'SPHERICAL'
        self._created_nodes['gradient'] = gradient

        x += 200

        # Float curve for shaping
        float_curve = nk.n("ShaderNodeFloatCurve", "Shape", x=x, y=100)
        self._created_nodes['float_curve'] = float_curve

        x += 200

        # Map range for scale
        map_range = nk.n("ShaderNodeMapRange", "Map Range", x=x, y=100)
        self._created_nodes['map_range'] = map_range

        x += 200

        # Combine XYZ for scale (X and Y only)
        combine = nk.n("ShaderNodeCombineXYZ", "Scale", x=x, y=100)
        self._created_nodes['combine_scale'] = combine

        x += 200

        # === INSTANCE ON POINTS ===
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance on Points",
            x=x, y=0
        )
        nk.link(mesh_line.outputs["Mesh"], instance.inputs["Points"])
        nk.link(cylinder.outputs["Mesh"], instance.inputs["Instance"])
        nk.link(combine.outputs["Vector"], instance.inputs["Scale"])
        self._created_nodes['instance'] = instance

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=0)
        nk.link(instance.outputs["Instances"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class IndexAnimation:
    """
    Utilities for index-based animation patterns.

    Cross-references:
    - KB Section 2: Index Math
    """

    @staticmethod
    def get_rotation_formula() -> dict:
        """
        Get index-based rotation formulas.

        KB Reference: Section 2 - Index Math

        Returns:
            Dictionary with formulas and explanations
        """
        return {
            "spiral": {
                "formula": "Index × Factor → Rotation X",
                "factor_3": "Clean spiral pattern",
                "factor_5": "More rotations, tighter spiral"
            },
            "wave": {
                "formula": "sin(Index × Factor) → Scale",
                "use": "Creates wave-like patterns"
            },
            "offset": {
                "formula": "Index × Offset → Position Y",
                "use": "Staggered animation timing"
            }
        }

    @staticmethod
    def get_interpolation_tip() -> str:
        """
        Get interpolation tip for looping animations.

        KB Reference: Section 2 - Linear Interpolation

        Returns:
            Tip text
        """
        return "Set Preferences → Animation → Default Interpolation → LINEAR for perfect loops"


class PatternPresets:
    """
    Preset configurations for generative patterns.

    Cross-references:
    - KB Section 2: Geometric minimalism styles
    """

    @staticmethod
    def radial_spiral() -> dict:
        """Radial spiral preset."""
        return {
            "count": 80,
            "radius": 7.0,
            "rotation_factor": 3,
            "description": "Classic spiral pattern"
        }

    @staticmethod
    def radial_starburst() -> dict:
        """Radial starburst preset."""
        return {
            "count": 36,
            "radius": 5.0,
            "rotation_factor": 5,
            "description": "Star-like pattern"
        }

    @staticmethod
    def wave_cylinder() -> dict:
        """Wave cylinder preset."""
        return {
            "count": 21,
            "gradient_scale": 2.0,
            "cylinder_radius": 2.0,
            "description": "Cylindrical wave field"
        }

    @staticmethod
    def dense_radial() -> dict:
        """Dense radial pattern."""
        return {
            "count": 120,
            "radius": 10.0,
            "rotation_factor": 7,
            "description": "Dense, complex spiral"
        }


# Convenience functions
def create_radial_array(
    count: int = 80,
    radius: float = 7.0,
    rotation_factor: int = 3
) -> bpy.types.NodeTree:
    """Quick setup for radial array."""
    radial = RadialArray.create()
    radial.set_count(count)
    radial.set_radius(radius)
    radial.animate_by_index(rotation_factor)
    return radial.build()


def create_wave_field(count: int = 21) -> bpy.types.NodeTree:
    """Quick setup for wave field."""
    wave = WaveField.create()
    wave.set_count(count)
    return wave.build()


def get_quick_reference() -> dict:
    """Get quick reference for generative geometry."""
    return {
        "rotation_formula": "Index × Factor → Rotation (use integers)",
        "loop_rotation": "2 × π = perfect 360° loop",
        "linear_interpolation": "Required for seamless loops",
        "emission_material": "Standard for geometric minimalism",
        "wireframe_trick": "Mesh → Curve → Mesh with profile"
    }


class PatternHUD:
    """
    Heads-Up Display for generative geometry patterns.

    Cross-references:
    - KB Section 2: Geometric Minimalism
    - KB Section 15: Geometry Nodes Patterns
    """

    @staticmethod
    def display_radial_settings(
        count: int = 80,
        radius: float = 7.0,
        rotation_factor: int = 3,
        instance_size: tuple = (32.0, 3.3, 3.3)
    ) -> str:
        """Display radial array settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        RADIAL ARRAY SETTINGS         ║",
            "╠══════════════════════════════════════╣",
            f"║ Count:         {count:>20} ║",
            f"║ Radius:        {radius:>20.1f} ║",
            f"║ Rot Factor:    {rotation_factor:>20} ║",
            "╠══════════════════════════════════════╣",
            "║ INSTANCE SIZE                        ║",
            f"║   X:           {instance_size[0]:>20.1f} ║",
            f"║   Y:           {instance_size[1]:>20.1f} ║",
            f"║   Z:           {instance_size[2]:>20.1f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_wave_settings(
        count: int = 21,
        gradient_scale: float = 2.0,
        cylinder_radius: float = 2.0
    ) -> str:
        """Display wave field settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        WAVE FIELD SETTINGS           ║",
            "╠══════════════════════════════════════╣",
            f"║ Count:         {count:>20} ║",
            f"║ Gradient Scale:{gradient_scale:>20.1f} ║",
            f"║ Cylinder R:    {cylinder_radius:>20.1f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_index_formulas() -> str:
        """Display index-based animation formulas."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        INDEX ANIMATION FORMULAS      ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  SPIRAL ROTATION:                    ║",
            "║    rotation = Index × Factor         ║",
            "║    Factor 3 = clean spiral           ║",
            "║    Factor 5 = tighter spiral         ║",
            "║    Factor 7 = very tight             ║",
            "║                                      ║",
            "║  WAVE SCALE:                         ║",
            "║    scale = sin(Index × Factor)       ║",
            "║    Creates wave-like patterns        ║",
            "║                                      ║",
            "║  STAGGERED OFFSET:                   ║",
            "║    offset = Index × Spacing          ║",
            "║    Creates cascade timing            ║",
            "║                                      ║",
            "║  PERFECT LOOP:                       ║",
            "║    2 × π = 360° (full rotation)      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for radial array."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       RADIAL ARRAY NODE FLOW         ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       └──→ [Curve Circle]            ║",
            "║             (points mode)            ║",
            "║                 │                    ║",
            "║       [Curve to Points]              ║",
            "║                 │                    ║",
            "║  ┌──────────────┼──────────────┐     ║",
            "║  │              │              │     ║",
            "║  ↓              ↓              ↓     ║",
            "║ [Mesh       [Index]      [Align     ║",
            "║  Cube]        │          Rotation]  ║",
            "║  │         [× Factor]        │       ║",
            "║  │              │            │       ║",
            "║  │        [Combine XYZ]      │       ║",
            "║  │              │            │       ║",
            "║  │        [Add Rotation]     │       ║",
            "║  │              │            │       ║",
            "║  └──────────────┼────────────┘       ║",
            "║                 │                    ║",
            "║       [Instance on Points]           ║",
            "║                 │                    ║",
            "║       [Group Output]                 ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for generative patterns."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║    PATTERN PRE-FLIGHT CHECKLIST      ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Count set appropriately           ║",
            "║    (20-120 depending on density)     ║",
            "║                                      ║",
            "□  □ Radius configured                 ║",
            "║    (5-10 for typical patterns)       ║",
            "║                                      ║",
            "□  □ Rotation factor chosen            ║",
            "║    (3, 5, 7 for different effects)   ║",
            "║                                      ║",
            "□  □ Instance geometry ready           ║",
            "║    (cube, custom mesh, etc.)         ║",
            "║                                      ║",
            "□  □ Emission material applied         ║",
            "║    (for geometric minimalism)        ║",
            "║                                      ║",
            "□  □ Animation interpolation LINEAR   ║",
            "║    (for perfect loops)               ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_presets() -> str:
        """Display pattern presets."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        PATTERN PRESETS               ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  RADIAL SPIRAL (classic):            ║",
            "║    count=80, radius=7, factor=3      ║",
            "║                                      ║",
            "║  RADIAL STARBURST:                   ║",
            "║    count=36, radius=5, factor=5      ║",
            "║                                      ║",
            "║  DENSE RADIAL:                       ║",
            "║    count=120, radius=10, factor=7    ║",
            "║                                      ║",
            "║  WAVE CYLINDER:                      ║",
            "║    count=21, gradient_scale=2.0      ║",
            "║                                      ║",
            "║  TIP: Use integer factors for        ║",
            "║       predictable spiral patterns    ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_pattern_settings(pattern_type: str = "radial", **kwargs) -> None:
    """Print pattern settings to console."""
    if pattern_type == "radial":
        print(PatternHUD.display_radial_settings(**kwargs))
    elif pattern_type == "wave":
        print(PatternHUD.display_wave_settings(**kwargs))
