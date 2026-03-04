"""
Light Dispersion Module - Codified from Tutorials 2, 3

Implements chromatic aberration, light splitting, and dispersion effects
for both shader and compositor workflows.

Based on tutorials:
- Default Cube: Geometric Minimalism (Section 2)
- Polygon Runway: Isometric/RTS (Section 3)

Usage:
    from lib.dispersion import ChromaticAberration, GlassDispersion, LightSplitter

    # Shader-based dispersion
    glass = GlassDispersion.create("PrismGlass")
    glass.set_ior(1.52)  # Crown glass
    glass.set_dispersion(0.02)
    mat = glass.build()

    # Compositor chromatic aberration
    aberration = ChromaticAberration()
    aberration.set_strength(0.01)
    aberration.apply()

    # Geometry nodes light splitter
    splitter = LightSplitter.create("PrismSplit")
    splitter.set_splits(7)
    splitter.set_spread(2.0)
    tree = splitter.build()
"""

from __future__ import annotations
import bpy
import math
from typing import Optional, Tuple, Dict
from pathlib import Path

# Import NodeKit for node building
try:
    from .nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit


class ChromaticAberration:
    """
    Compositor-based chromatic aberration effect.

    Cross-references:
    - KB Section 2: Chromatic aberration for geometric minimalism
    - KB Section 22: Compositor effects
    """

    def __init__(self):
        self._scene = bpy.context.scene
        self._strength = 0.01
        self._use_jitter = True
        self._nodes: dict = {}

    def set_strength(self, strength: float) -> "ChromaticAberration":
        """
        Set aberration strength.

        KB Reference: Section 2 - Subtle chromatic effect

        Args:
            strength: Aberration amount (0.0-0.1 typical)

        Returns:
            Self for chaining
        """
        self._strength = strength
        return self

    def enable_jitter(self, enable: bool = True) -> "ChromaticAberration":
        """
        Enable jittered sampling for smoother results.

        Args:
            enable: Whether to use jitter

        Returns:
            Self for chaining
        """
        self._use_jitter = enable
        return self

    def apply(self) -> "ChromaticAberration":
        """
        Apply chromatic aberration to compositor.

        KB Reference: Section 2 - Bonus lines effect

        Returns:
            Self for chaining
        """
        self._scene.use_nodes = True
        tree = self._scene.node_tree

        # Create lens distortion node
        lens = tree.nodes.new('CompositorNodeLensdist')
        lens.use_jitter = self._use_jitter
        lens.dispersion = self._strength

        self._nodes['lens'] = lens
        return self

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._nodes.get(name)


class GlassDispersion:
    """
    Physically-based glass with spectral dispersion.

    Creates realistic glass materials that split light into
    component colors based on wavelength-dependent refraction.

    Cross-references:
    - KB Section 21: Glass flowers
    - KB Section 36: Remake glass flowers
    """

    def __init__(self):
        self._material: Optional[bpy.types.Material] = None
        self._ior = 1.45  # Base IOR (glass)
        self._dispersion = 0.01  # Dispersion strength
        self._roughness = 0.0
        self._transmission = 1.0
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "DispersionGlass") -> "GlassDispersion":
        """
        Create new glass material with dispersion.

        Args:
            name: Material name

        Returns:
            Configured GlassDispersion instance
        """
        instance = cls()
        instance._material = bpy.data.materials.new(name=name)
        instance._material.use_nodes = True
        return instance

    @classmethod
    def from_material(
        cls,
        material: bpy.types.Material
    ) -> "GlassDispersion":
        """
        Configure existing material for dispersion.

        Args:
            material: Existing Blender material

        Returns:
            Configured GlassDispersion instance
        """
        instance = cls()
        instance._material = material
        material.use_nodes = True
        return instance

    def set_ior(self, ior: float) -> "GlassDispersion":
        """
        Set base index of refraction.

        KB Reference: Section 21 - IOR values for glass

        Args:
            ior: Index of refraction (1.0-2.5)
                - Air: 1.0
                - Water: 1.33
                - Glass: 1.45-1.52
                - Crystal: 1.55-2.0
                - Diamond: 2.42

        Returns:
            Self for chaining
        """
        self._ior = ior
        return self

    def set_dispersion(self, strength: float) -> "GlassDispersion":
        """
        Set dispersion strength.

        Higher values create more color separation.

        Args:
            strength: Dispersion amount (0.0-0.1)

        Returns:
            Self for chaining
        """
        self._dispersion = strength
        return self

    def set_roughness(self, roughness: float) -> "GlassDispersion":
        """
        Set surface roughness.

        Args:
            roughness: Roughness value (0.0 = perfectly smooth)

        Returns:
            Self for chaining
        """
        self._roughness = roughness
        return self

    def set_transmission(self, transmission: float) -> "GlassDispersion":
        """
        Set transmission amount.

        Args:
            transmission: Transmission (0.0-1.0)

        Returns:
            Self for chaining
        """
        self._transmission = transmission
        return self

    def build(self) -> bpy.types.Material:
        """
        Build the glass material with dispersion.

        KB Reference: Section 21, 36 - Glass material setup

        Returns:
            Configured material
        """
        if not self._material:
            raise RuntimeError("Call create() or from_material() first")

        nodes = self._material.node_tree.nodes
        links = self._material.node_tree.links

        # Clear default nodes
        nodes.clear()

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)
        self._created_nodes['output'] = output

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (300, 0)
        principled.inputs["Roughness"].default_value = self._roughness
        principled.inputs["IOR"].default_value = self._ior
        principled.inputs["Transmission Weight"].default_value = self._transmission

        # Blender 4.0+ uses Transmission Weight
        if "Transmission" in principled.inputs:
            principled.inputs["Transmission"].default_value = self._transmission

        self._created_nodes['principled'] = principled

        # === DISPERSION SETUP ===
        # For true dispersion, we need to vary IOR by wavelength
        # This is a simplified approach using layered glass

        if self._dispersion > 0:
            # Mix node for color separation effect
            mix = nodes.new('ShaderNodeMixShader')
            mix.location = (450, 0)
            self._created_nodes['mix'] = mix

            # Create slight color tint for dispersion simulation
            # Red channel uses base IOR
            # Blue channel uses slightly different IOR
            color_ramp = nodes.new('ShaderNodeValToRGB')
            color_ramp.location = (100, -200)
            color_ramp.color_ramp.elements[0].color = (1.0, 0.9, 0.9, 1.0)  # Warm
            color_ramp.color_ramp.elements[1].color = (0.9, 0.9, 1.0, 1.0)  # Cool
            self._created_nodes['color_ramp'] = color_ramp

            # Fresnel for edge effect
            fresnel = nodes.new('ShaderNodeFresnel')
            fresnel.location = (100, -100)
            fresnel.inputs["IOR"].default_value = self._ior
            self._created_nodes['fresnel'] = fresnel

            # Link fresnel to color ramp
            links.new(fresnel.outputs["Fac"], color_ramp.inputs["Fac"])

            # Link color to base color
            links.new(color_ramp.outputs["Color"], principled.inputs["Base Color"])

        # === LINK TO OUTPUT ===
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        return self._material

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class LightSplitter:
    """
    Prism-like light splitting effect using geometry nodes.

    Creates geometry that splits and spreads into spectrum colors.
    Each split is colored according to the visible spectrum (ROYGBIV).

    Cross-references:
    - KB Section 2: Generative art patterns
    - KB Section 3: Isometric/RTS color techniques
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._splits = 7  # Number of color bands (ROYGBIV)
        self._spread = 2.0  # Angular spread in radians
        self._scale = 1.0  # Instance scale
        self._offset_distance = 0.5  # Distance between splits
        self._use_rainbow_colors = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "LightSplitter") -> "LightSplitter":
        """
        Create a new geometry node tree for light splitting.

        Args:
            name: Name for the node group

        Returns:
            Configured LightSplitter instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "LightSplitter"
    ) -> "LightSplitter":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach to
            name: Name for the node group

        Returns:
            Configured LightSplitter instance
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
            name="Splits", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._splits, min_value=2, max_value=12
        )
        self.node_tree.interface.new_socket(
            name="Spread", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._spread, min_value=0.1, max_value=6.28
        )
        self.node_tree.interface.new_socket(
            name="Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._scale, min_value=0.1, max_value=10.0
        )
        self.node_tree.interface.new_socket(
            name="Offset Distance", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._offset_distance, min_value=0.0, max_value=5.0
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_splits(self, count: int) -> "LightSplitter":
        """
        Set number of color splits (spectral bands).

        Args:
            count: Number of splits (2-12)
                   3 = RGB, 7 = ROYGBIV, 10 = Full spectrum
        """
        self._splits = max(2, min(12, count))
        return self

    def set_spread(self, spread: float) -> "LightSplitter":
        """
        Set angular spread of splits.

        Args:
            spread: Spread angle in radians (pi = 180°)
        """
        self._spread = spread
        return self

    def set_scale(self, scale: float) -> "LightSplitter":
        """Set instance scale for split geometry."""
        self._scale = scale
        return self

    def set_offset_distance(self, distance: float) -> "LightSplitter":
        """Set distance between split instances."""
        self._offset_distance = distance
        return self

    def use_rainbow_colors(self, use: bool = True) -> "LightSplitter":
        """Enable/disable rainbow color output."""
        self._use_rainbow_colors = use
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for light splitting.

        KB Reference: Section 2 - Light splitting patterns

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

        # === MESH LINE FOR SPLITS ===
        # Create points along a line for each split
        mesh_line = nk.n(
            "GeometryNodeMeshLine",
            "Split Line",
            x=x, y=100
        )
        mesh_line.inputs["Count"].default_value = self._splits
        # Bind count input
        nk.link(group_in.outputs["Splits"], mesh_line.inputs["Count"])
        self._created_nodes['mesh_line'] = mesh_line

        x += 200

        # === SPLINE PARAMETER FOR INDEX ===
        spline_param = nk.n(
            "GeometryNodeSplineParameter",
            "Spline Param",
            x=x, y=100
        )
        nk.link(mesh_line.outputs["Mesh"], spline_param.inputs["Geometry"])
        self._created_nodes['spline_param'] = spline_param

        x += 200

        # === INDEX TO SPLIT ===
        # Convert factor to index (0 to splits-1)
        index_mult = nk.n("ShaderNodeMath", "Index Scale", x=x, y=100)
        index_mult.operation = 'MULTIPLY'
        nk.link(spline_param.outputs["Factor"], index_mult.inputs[0])
        nk.link(group_in.outputs["Splits"], index_mult.inputs[1])
        self._created_nodes['index_mult'] = index_mult

        x += 150

        # === CALCULATE ROTATION PER SPLIT ===
        # rotation = (index / (splits-1) - 0.5) × spread
        # This centers the spread around 0

        # First, subtract 1 from splits
        splits_minus_1 = nk.n("ShaderNodeMath", "Splits-1", x=x, y=-50)
        splits_minus_1.operation = 'SUBTRACT'
        splits_minus_1.inputs[1].default_value = 1.0
        nk.link(group_in.outputs["Splits"], splits_minus_1.inputs[0])
        self._created_nodes['splits_minus_1'] = splits_minus_1

        x += 150

        # Divide index by (splits-1)
        index_norm = nk.n("ShaderNodeMath", "Index Norm", x=x, y=100)
        index_norm.operation = 'DIVIDE'
        nk.link(index_mult.outputs[0], index_norm.inputs[0])
        nk.link(splits_minus_1.outputs[0], index_norm.inputs[1])
        self._created_nodes['index_norm'] = index_norm

        x += 150

        # Subtract 0.5 to center
        center_offset = nk.n("ShaderNodeMath", "Center", x=x, y=100)
        center_offset.operation = 'SUBTRACT'
        center_offset.inputs[1].default_value = 0.5
        nk.link(index_norm.outputs[0], center_offset.inputs[0])
        self._created_nodes['center_offset'] = center_offset

        x += 150

        # Multiply by spread
        rotation_calc = nk.n("ShaderNodeMath", "Rotation", x=x, y=100)
        rotation_calc.operation = 'MULTIPLY'
        nk.link(center_offset.outputs[0], rotation_calc.inputs[0])
        nk.link(group_in.outputs["Spread"], rotation_calc.inputs[1])
        self._created_nodes['rotation_calc'] = rotation_calc

        x += 200

        # === COMBINE ROTATION (Z-AXIS) ===
        combine_rot = nk.n(
            "ShaderNodeCombineXYZ",
            "Rotation Vec",
            x=x, y=100
        )
        combine_rot.inputs["X"].default_value = 0.0
        combine_rot.inputs["Y"].default_value = 0.0
        nk.link(rotation_calc.outputs[0], combine_rot.inputs["Z"])
        self._created_nodes['combine_rot'] = combine_rot

        x += 200

        # === OFFSET POSITION ===
        # Offset each split along its direction
        offset_x = nk.n("ShaderNodeMath", "Offset X", x=x, y=200)
        offset_x.operation = 'MULTIPLY'
        nk.link(group_in.outputs["Offset Distance"], offset_x.inputs[0])
        nk.link(center_offset.outputs[0], offset_x.inputs[1])

        offset_z = nk.n("ShaderNodeMath", "Offset Z", x=x, y=100)
        offset_z.operation = 'MULTIPLY'
        offset_z.inputs[1].default_value = 0.0

        self._created_nodes['offset_x'] = offset_x
        self._created_nodes['offset_z'] = offset_z

        x += 150

        combine_offset = nk.n(
            "ShaderNodeCombineXYZ",
            "Offset Vec",
            x=x, y=150
        )
        nk.link(offset_x.outputs[0], combine_offset.inputs["X"])
        combine_offset.inputs["Y"].default_value = 0.0
        nk.link(offset_z.outputs[0], combine_offset.inputs["Z"])
        self._created_nodes['combine_offset'] = combine_offset

        x += 200

        # === INSTANCE GEOMETRY ===
        # Create a simple cube as the instance
        cube = nk.n(
            "GeometryNodeMeshCube",
            "Split Instance",
            x=x, y=-100
        )
        nk.link(group_in.outputs["Scale"], cube.inputs["Size X"])
        nk.link(group_in.outputs["Scale"], cube.inputs["Size Y"])
        nk.link(group_in.outputs["Scale"], cube.inputs["Size Z"])
        self._created_nodes['cube'] = cube

        x += 200

        # === INSTANCE ON POINTS ===
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance Splits",
            x=x, y=100
        )
        nk.link(spline_param.outputs["Geometry"], instance.inputs["Points"])
        nk.link(cube.outputs["Mesh"], instance.inputs["Instance"])
        nk.link(combine_rot.outputs["Vector"], instance.inputs["Rotation"])
        nk.link(combine_offset.outputs["Vector"], instance.inputs["Translation"])
        self._created_nodes['instance'] = instance

        x += 250

        # === OPTIONAL: STORE COLOR ATTRIBUTE ===
        if self._use_rainbow_colors:
            # Use index to create rainbow color
            # Color is based on position in spectrum
            store_color = nk.n(
                "GeometryNodeStoreNamedAttribute",
                "Store Spectrum Color",
                x=x, y=100
            )
            store_color.inputs["Name"].default_value = "spectrum_color"
            store_color.domain = 'INSTANCE'
            nk.link(instance.outputs["Instances"], store_color.inputs["Geometry"])
            # The color will be a gradient from index_norm
            # Use separate RGB from the normalized index for color variation
            nk.link(index_norm.outputs[0], store_color.inputs["Value"])
            self._created_nodes['store_color'] = store_color

            final_geo = store_color
            x += 200
        else:
            final_geo = instance

        self._created_nodes['final_geo'] = final_geo

        # === REALIZE INSTANCES ===
        realize = nk.n(
            "GeometryNodeRealizeInstances",
            "Realize",
            x=x, y=100
        )
        nk.link(final_geo.outputs["Instances"] if hasattr(final_geo, 'outputs') and "Instances" in final_geo.outputs else final_geo.outputs["Geometry"], realize.inputs["Geometry"])
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


class DispersionPresets:
    """
    Preset configurations for dispersion effects.

    Cross-references:
    - KB Section 21, 36: Glass types
    """

    @staticmethod
    def crown_glass() -> Dict:
        """Standard crown glass (low dispersion)."""
        return {
            "ior": 1.52,
            "dispersion": 0.005,
            "description": "Standard optical glass, minimal color separation"
        }

    @staticmethod
    def flint_glass() -> Dict:
        """Flint glass (high dispersion)."""
        return {
            "ior": 1.62,
            "dispersion": 0.03,
            "description": "High dispersion, strong color separation"
        }

    @staticmethod
    def crystal() -> Dict:
        """Crystal glass."""
        return {
            "ior": 1.55,
            "dispersion": 0.02,
            "description": "Lead crystal, good dispersion"
        }

    @staticmethod
    def diamond() -> Dict:
        """Diamond (extreme dispersion)."""
        return {
            "ior": 2.42,
            "dispersion": 0.044,
            "description": "Diamond, extreme fire and brilliance"
        }

    @staticmethod
    def water() -> Dict:
        """Water."""
        return {
            "ior": 1.33,
            "dispersion": 0.002,
            "description": "Water, very low dispersion"
        }


class SpectralColors:
    """
    Utilities for working with spectral colors.

    Cross-references:
    - KB Section 2: Color for geometric minimalism
    """

    @staticmethod
    def get_spectrum_rgb() -> list:
        """
        Get RGB values for visible spectrum.

        Returns:
            List of (r, g, b) tuples from red to violet
        """
        return [
            (1.0, 0.0, 0.0),      # Red (700nm)
            (1.0, 0.5, 0.0),      # Orange (620nm)
            (1.0, 1.0, 0.0),      # Yellow (580nm)
            (0.5, 1.0, 0.0),      # Yellow-Green (550nm)
            (0.0, 1.0, 0.0),      # Green (530nm)
            (0.0, 1.0, 0.5),      # Cyan (500nm)
            (0.0, 0.5, 1.0),      # Light Blue (470nm)
            (0.0, 0.0, 1.0),      # Blue (450nm)
            (0.3, 0.0, 0.5),      # Indigo (420nm)
            (0.5, 0.0, 1.0),      # Violet (400nm)
        ]

    @staticmethod
    def wavelength_to_rgb(wavelength: float) -> Tuple[float, float, float]:
        """
        Convert wavelength (nm) to RGB color.

        Args:
            wavelength: Wavelength in nanometers (380-780)

        Returns:
            (r, g, b) tuple
        """
        # Approximate conversion
        if wavelength < 380:
            return (0.0, 0.0, 0.0)
        elif wavelength < 440:
            r = -(wavelength - 440) / (440 - 380)
            g = 0.0
            b = 1.0
        elif wavelength < 490:
            r = 0.0
            g = (wavelength - 440) / (490 - 440)
            b = 1.0
        elif wavelength < 510:
            r = 0.0
            g = 1.0
            b = -(wavelength - 510) / (510 - 490)
        elif wavelength < 580:
            r = (wavelength - 510) / (580 - 510)
            g = 1.0
            b = 0.0
        elif wavelength < 645:
            r = 1.0
            g = -(wavelength - 645) / (645 - 580)
            b = 0.0
        elif wavelength <= 780:
            r = 1.0
            g = 0.0
            b = 0.0
        else:
            return (0.0, 0.0, 0.0)

        return (max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b)))


# Convenience functions
def create_chromatic_aberration(strength: float = 0.01) -> ChromaticAberration:
    """Quick setup for chromatic aberration."""
    aberration = ChromaticAberration()
    aberration.set_strength(strength)
    aberration.apply()
    return aberration


def create_glass_material(
    name: str = "Glass",
    ior: float = 1.45,
    dispersion: float = 0.01
) -> bpy.types.Material:
    """Quick setup for glass material with dispersion."""
    glass = GlassDispersion.create(name)
    glass.set_ior(ior)
    glass.set_dispersion(dispersion)
    return glass.build()


def get_quick_reference() -> Dict:
    """Get quick reference for dispersion."""
    return {
        "glass_ior_range": "1.45-1.52",
        "dispersion_range": "0.005-0.04",
        "diamond_ior": 2.42,
        "wavelength_range": "380-780 nm",
        "tip": "Higher dispersion = more rainbow effect"
    }


class DispersionHUD:
    """
    Heads-Up Display for dispersion and light splitting visualization.

    Cross-references:
    - KB Section 2: Geometric Minimalism
    - KB Section 21: Glass flowers
    """

    @staticmethod
    def display_glass_settings(
        ior: float = 1.45,
        dispersion: float = 0.01,
        roughness: float = 0.0,
        transmission: float = 1.0
    ) -> str:
        """Display glass dispersion settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        GLASS DISPERSION SETTINGS     ║",
            "╠══════════════════════════════════════╣",
            f"║ IOR:           {ior:>20.2f} ║",
            f"║ Dispersion:    {dispersion:>20.3f} ║",
            f"║ Roughness:     {roughness:>20.2f} ║",
            f"║ Transmission:  {transmission:>20.2f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_splitter_settings(
        splits: int = 7,
        spread: float = 2.0,
        scale: float = 1.0,
        offset_distance: float = 0.5,
        rainbow_colors: bool = True
    ) -> str:
        """Display light splitter settings."""
        rainbow_status = "ON" if rainbow_colors else "OFF"
        lines = [
            "╔══════════════════════════════════════╗",
            "║       LIGHT SPLITTER SETTINGS        ║",
            "╠══════════════════════════════════════╣",
            f"║ Splits:        {splits:>20} ║",
            f"║ Spread:        {spread:>17.2f} rad ║",
            f"║ Scale:         {scale:>20.2f} ║",
            f"║ Offset Dist:   {offset_distance:>20.2f} ║",
            f"║ Rainbow:       {rainbow_status:>20} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_ior_guide() -> str:
        """Display IOR reference guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        INDEX OF REFRACTION           ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  COMMON MATERIALS:                   ║",
            "║    Air:        1.00                  ║",
            "║    Water:      1.33                  ║",
            "║    Glass:      1.45-1.52             ║",
            "║    Crystal:    1.55-2.0              ║",
            "║    Diamond:    2.42                  ║",
            "║                                      ║",
            "║  DISPERSION (color separation):      ║",
            "║    Low:        0.005                 ║",
            "║    Medium:     0.01-0.02             ║",
            "║    High:       0.03-0.04             ║",
            "║    Diamond:    0.044                 ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_spectrum() -> str:
        """Display visible spectrum reference."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        VISIBLE SPECTRUM              ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  Wavelength    Color                 ║",
            "║  ─────────────────────────────       ║",
            "║  700 nm        Red                   ║",
            "║  620 nm        Orange                ║",
            "║  580 nm        Yellow                ║",
            "║  530 nm        Green                 ║",
            "║  500 nm        Cyan                  ║",
            "║  470 nm        Light Blue            ║",
            "║  450 nm        Blue                  ║",
            "║  400 nm        Violet                ║",
            "║                                      ║",
            "║  ROYGBIV = 7 spectral bands          ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for light splitting."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       LIGHT SPLITTER NODE FLOW       ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       └──→ [Mesh Line] ← Splits      ║",
            "║                 │                    ║",
            "║          [Spline Parameter]          ║",
            "║                 │                    ║",
            "║       [Index × Splits]               ║",
            "║                 │                    ║",
            "║       [Index / (Splits-1)]           ║",
            "║                 │                    ║",
            "║       [- 0.5] (center)               ║",
            "║                 │                    ║",
            "║       [× Spread] → Rotation          ║",
            "║                 │                    ║",
            "║  ┌──────────────┴──────────────┐     ║",
            "║  │                             │     ║",
            "║  ↓                             ↓     ║",
            "║ [Combine                    [Mesh    ║",
            "║  XYZ] (rot)                  Cube]   ║",
            "║  │                             │     ║",
            "║  └──────────────┬──────────────┘     ║",
            "║                 │                    ║",
            "║       [Instance on Points]           ║",
            "║                 │                    ║",
            "║       [Store Spectrum Color]         ║",
            "║                 │                    ║",
            "║       [Realize Instances]            ║",
            "║                 │                    ║",
            "║       [Group Output]                 ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for dispersion setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║    DISPERSION PRE-FLIGHT CHECKLIST   ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  FOR GLASS MATERIAL:                 ║",
            "║  □ IOR set for material type         ║",
            "║    (1.45-1.52 for glass)             ║",
            "║                                      ║",
            "║  □ Dispersion strength set           ║",
            "║    (0.01-0.04 for visible effect)    ║",
            "║                                      ║",
            "║  □ Transmission enabled              ║",
            "║    (1.0 for full glass)              ║",
            "║                                      ║",
            "║  FOR LIGHT SPLITTER:                 ║",
            "║  □ Splits count configured           ║",
            "║    (7 for ROYGBIV)                   ║",
            "║                                      ║",
            "║  □ Spread angle set                  ║",
            "║    (pi/2 = 90° fan)                  ║",
            "║                                      ║",
            "║  □ Rainbow colors enabled            ║",
            "║    (for spectrum output)             ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_dispersion_settings(mode: str = "glass", **kwargs) -> None:
    """Print dispersion settings to console."""
    if mode == "glass":
        print(DispersionHUD.display_glass_settings(**kwargs))
    elif mode == "splitter":
        print(DispersionHUD.display_splitter_settings(**kwargs))


def create_light_splitter(
    obj: bpy.types.Object,
    splits: int = 7,
    spread: float = 2.0
) -> LightSplitter:
    """
    Quick setup for light splitting effect.

    Args:
        obj: Object to attach splitter to
        splits: Number of spectral bands
        spread: Angular spread in radians

    Returns:
        Configured LightSplitter with built node tree
    """
    splitter = LightSplitter.from_object(obj)
    splitter.set_splits(splits)
    splitter.set_spread(spread)
    splitter.set_scale(0.5)
    splitter.set_offset_distance(1.0)
    splitter.use_rainbow_colors(True)
    splitter.build()
    return splitter


def create_rainbow_splitter(obj: bpy.types.Object) -> LightSplitter:
    """Create full ROYGBIV rainbow splitter."""
    return create_light_splitter(obj, splits=7, spread=3.14)  # 180° spread


def create_rgb_splitter(obj: bpy.types.Object) -> LightSplitter:
    """Create simple RGB splitter."""
    return create_light_splitter(obj, splits=3, spread=1.57)  # 90° spread
