"""
Product Morph Effect Module - Codified from Tutorial 24

Implements real-time morphing effect controlled by an empty object.
Objects transform based on proximity to controller - no simulations needed.

Based on Default Cube tutorial: https://www.youtube.com/watch?v=aWYiW-LSso0

Usage:
    from lib.morphing import ProductMorph

    # Create morph effect
    morph = ProductMorph.create("ProductMorph")
    morph.set_controller(empty_object)
    morph.set_threshold(0.5)
    morph.set_morph_offset(z=0.5)  # Morph upward
    morph.pass_to_shader("morph_mask")  # For material changes
    tree = morph.build()
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple
from pathlib import Path

# Import NodeKit for node building
try:
    from .nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit


class ProductMorph:
    """
    Real-time product morphing effect controlled by empty.

    Creates a node tree that:
    - Calculates distance from controller empty
    - Creates morph mask based on threshold
    - Blends between original and morphed positions
    - Stores mask for shader access

    Cross-references:
    - KB Section 24: Morphing Product Effect (Default Cube)
    - KB Section 12: Effector (similar distance pattern)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._controller: Optional[bpy.types.Object] = None
        self._threshold = 0.5
        self._morph_offset = (0.0, 0.0, 0.5)
        self._morph_scale = (1.0, 1.0, 1.0)
        self._morph_rotation = (0.0, 0.0, 0.0)
        self._shader_attribute = "morph_mask"
        self._use_shader_output = True
        self._smooth_falloff = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "ProductMorph") -> "ProductMorph":
        """
        Create a new geometry node tree for morph effect.

        Args:
            name: Name for the node group

        Returns:
            Configured ProductMorph instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "ProductMorph"
    ) -> "ProductMorph":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to apply morph to
            name: Name for the node group

        Returns:
            Configured ProductMorph instance
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
            name="Controller", in_out='INPUT', socket_type='NodeSocketObject'
        )
        self.node_tree.interface.new_socket(
            name="Threshold", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._threshold, min_value=0.01, max_value=10.0
        )
        self.node_tree.interface.new_socket(
            name="Morph Offset X", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._morph_offset[0]
        )
        self.node_tree.interface.new_socket(
            name="Morph Offset Y", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._morph_offset[1]
        )
        self.node_tree.interface.new_socket(
            name="Morph Offset Z", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._morph_offset[2]
        )
        self.node_tree.interface.new_socket(
            name="Morph Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=1.0, min_value=0.0
        )
        self.node_tree.interface.new_socket(
            name="Smooth Falloff", in_out='INPUT', socket_type='NodeSocketBool',
            default_value=self._smooth_falloff
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_controller(self, empty: bpy.types.Object) -> "ProductMorph":
        """
        Set the controller empty that drives the morph.

        Args:
            empty: Empty object to use as controller
        """
        self._controller = empty
        return self

    def set_threshold(self, distance: float) -> "ProductMorph":
        """
        Set the distance threshold for morph region.

        Args:
            distance: Distance within which morph occurs
        """
        self._threshold = distance
        return self

    def set_morph_offset(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.5
    ) -> "ProductMorph":
        """Set the position offset for morphed vertices."""
        self._morph_offset = (x, y, z)
        return self

    def set_morph_scale(self, uniform: float = 1.0) -> "ProductMorph":
        """Set scale for morphed geometry."""
        self._morph_scale = (uniform, uniform, uniform)
        return self

    def set_morph_rotation(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> "ProductMorph":
        """Set rotation for morphed geometry (radians)."""
        self._morph_rotation = (x, y, z)
        return self

    def pass_to_shader(self, attribute_name: str = "morph_mask") -> "ProductMorph":
        """
        Enable passing morph mask to shader via named attribute.

        Args:
            attribute_name: Name for the attribute (use in shader Attribute node)
        """
        self._use_shader_output = True
        self._shader_attribute = attribute_name
        return self

    def use_smooth_falloff(self, smooth: bool = True) -> "ProductMorph":
        """Enable/disable smooth falloff at morph boundary."""
        self._smooth_falloff = smooth
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for product morph effect.

        KB Reference: Section 24 - Morphing Product Effect

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

        # === OBJECT INFO FOR CONTROLLER ===
        # KB Reference: Section 24 - Controller Empty
        obj_info = nk.n(
            "GeometryNodeObjectInfo",
            "Controller Info",
            x=x, y=-100
        )
        obj_info.transform_space = 'RELATIVE'
        nk.link(group_in.outputs["Controller"], obj_info.inputs["Object"])
        self._created_nodes['object_info'] = obj_info

        x += 200

        # === INPUT POSITION ===
        position = nk.n(
            "GeometryNodeInputPosition",
            "Position",
            x=x, y=200
        )
        self._created_nodes['position'] = position

        x += 200

        # === VECTOR DISTANCE ===
        # KB Reference: Section 24 - Distance mask calculation
        distance = nk.n(
            "ShaderNodeVectorMath",
            "Distance",
            x=x, y=100
        )
        distance.operation = 'DISTANCE'
        nk.link(obj_info.outputs["Location"], distance.inputs[0])
        nk.link(position.outputs["Position"], distance.inputs[1])
        self._created_nodes['distance'] = distance

        x += 200

        # === COMPARE (LESS THAN) ===
        # KB Reference: Section 24 - Threshold creates morph region
        compare = nk.n(
            "FunctionNodeCompare",
            "Is In Range",
            x=x, y=100
        )
        compare.operation = 'LESS_THAN'
        nk.link(distance.outputs[0], compare.inputs[0])
        nk.link(group_in.outputs["Threshold"], compare.inputs[1])
        self._created_nodes['compare'] = compare

        x += 200

        # === SMOOTH FALLOFF (OPTIONAL) ===
        if self._smooth_falloff:
            # Map range for smooth transition
            # KB Reference: Section 24 - Smooth falloff
            map_range = nk.n(
                "ShaderNodeMapRange",
                "Smooth Mask",
                x=x, y=100
            )
            # From distance to 0-1 factor
            nk.link(distance.outputs[0], map_range.inputs["Value"])
            map_range.inputs["From Min"].default_value = 0.0
            nk.link(group_in.outputs["Threshold"], map_range.inputs["From Max"])
            map_range.inputs["To Min"].default_value = 1.0  # Full at center
            map_range.inputs["To Max"].default_value = 0.0  # None at edge
            self._created_nodes['map_range'] = map_range

            # Float curve for falloff shape
            float_curve = nk.n(
                "ShaderNodeFloatCurve",
                "Falloff Shape",
                x=x + 200, y=100
            )
            nk.link(map_range.outputs[0], float_curve.inputs["Value"])
            self._created_nodes['float_curve'] = float_curve

            mask_value = float_curve
            x += 400
        else:
            mask_value = compare
            x += 200

        self._created_nodes['mask_value'] = mask_value

        # === STORE NAMED ATTRIBUTE (MASK FOR SHADER) ===
        if self._use_shader_output:
            # KB Reference: Section 24 - Pass mask to shader
            store_mask = nk.n(
                "GeometryNodeStoreNamedAttribute",
                "Store Mask",
                x=x, y=200
            )
            store_mask.inputs["Name"].default_value = self._shader_attribute
            store_mask.domain = 'POINT'
            nk.link(group_in.outputs["Geometry"], store_mask.inputs["Geometry"])
            if self._smooth_falloff:
                nk.link(mask_value.outputs[0], store_mask.inputs["Value"])
            else:
                # Convert boolean to float
                bool_to_float = nk.n("ShaderNodeMath", "Bool to Float", x=x - 100, y=0)
                bool_to_float.operation = 'ADD'
                bool_to_float.inputs[1].default_value = 0.0
                nk.link(compare.outputs[0], bool_to_float.inputs[0])
                nk.link(bool_to_float.outputs[0], store_mask.inputs["Value"])
                self._created_nodes['bool_to_float'] = bool_to_float

            geo_input = store_mask
            self._created_nodes['store_mask'] = store_mask
            x += 200
        else:
            geo_input = group_in

        # === BUILD MORPH OFFSET VECTOR ===
        offset_x = nk.n("ShaderNodeMath", "Offset X", x=x, y=200)
        offset_x.operation = 'MULTIPLY'
        nk.link(mask_value.outputs[0], offset_x.inputs[0])
        nk.link(group_in.outputs["Morph Offset X"], offset_x.inputs[1])

        offset_y = nk.n("ShaderNodeMath", "Offset Y", x=x, y=100)
        offset_y.operation = 'MULTIPLY'
        nk.link(mask_value.outputs[0], offset_y.inputs[0])
        nk.link(group_in.outputs["Morph Offset Y"], offset_y.inputs[1])

        offset_z = nk.n("ShaderNodeMath", "Offset Z", x=x, y=0)
        offset_z.operation = 'MULTIPLY'
        nk.link(mask_value.outputs[0], offset_z.inputs[0])
        nk.link(group_in.outputs["Morph Offset Z"], offset_z.inputs[1])

        self._created_nodes['offset_math'] = (offset_x, offset_y, offset_z)

        x += 200

        # === COMBINE OFFSET VECTOR ===
        combine_offset = nk.n(
            "ShaderNodeCombineXYZ",
            "Morph Offset",
            x=x, y=100
        )
        nk.link(offset_x.outputs[0], combine_offset.inputs["X"])
        nk.link(offset_y.outputs[0], combine_offset.inputs["Y"])
        nk.link(offset_z.outputs[0], combine_offset.inputs["Z"])
        self._created_nodes['combine_offset'] = combine_offset

        x += 200

        # === SET POSITION ===
        # KB Reference: Section 24 - Mix original and morphed positions
        set_position = nk.n(
            "GeometryNodeSetPosition",
            "Set Position",
            x=x, y=200
        )
        if self._use_shader_output:
            nk.link(store_mask.outputs["Geometry"], set_position.inputs["Geometry"])
        else:
            nk.link(group_in.outputs["Geometry"], set_position.inputs["Geometry"])
        nk.link(combine_offset.outputs["Vector"], set_position.inputs["Offset"])
        self._created_nodes['set_position'] = set_position

        x += 250

        # === OPTIONAL: SCALE TRANSFORM ===
        # Add scale based on mask if scale is not 1.0
        scale_geo = nk.n(
            "GeometryNodeScaleElements",
            "Scale Morphed",
            x=x, y=200
        )
        scale_geo.domain = 'POINT'
        # Use morph scale input
        nk.link(set_position.outputs["Geometry"], scale_geo.inputs["Geometry"])
        nk.link(group_in.outputs["Morph Scale"], scale_geo.inputs["Scale"])
        # Mask controls which elements are scaled
        nk.link(mask_value.outputs[0], scale_geo.inputs["Selection"])
        self._created_nodes['scale_geo'] = scale_geo

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=200)
        nk.link(scale_geo.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class MorphTarget:
    """
    Alternative morph using a target mesh instead of offset.

    Cross-references:
    - KB Section 24: Morph target concept
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._target_mesh: Optional[bpy.types.Object] = None
        self._created_nodes: dict = {}

    def set_target(self, obj: bpy.types.Object) -> "MorphTarget":
        """Set target mesh for morphing."""
        self._target_mesh = obj
        return self


class MorphingMaterial:
    """
    Helper for creating shader that responds to morph mask.

    Cross-references:
    - KB Section 24: Material integration
    """

    @staticmethod
    def create_morph_material(
        name: str = "MorphMaterial",
        original_color: tuple = (0.2, 0.2, 0.8, 1.0),
        morphed_color: tuple = (0.8, 0.2, 0.2, 1.0),
        attribute_name: str = "morph_mask"
    ) -> bpy.types.Material:
        """
        Create a material that changes color based on morph mask.

        Args:
            name: Material name
            original_color: RGBA color when not morphed
            morphed_color: RGBA color when morphed
            attribute_name: Name of the morph mask attribute

        Returns:
            Configured material
        """
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create output
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)

        # Create principled BSDF
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (400, 0)

        # Create attribute node for morph mask
        attr = nodes.new('ShaderNodeAttribute')
        attr.attribute_name = attribute_name
        attr.location = (0, -100)

        # Create color ramp for mask
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (150, -100)

        # Create mix color
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.location = (250, 0)

        # Create two color inputs
        color_a = nodes.new('ShaderNodeRGB')
        color_a.outputs[0].default_value = original_color
        color_a.location = (50, 100)

        color_b = nodes.new('ShaderNodeRGB')
        color_b.outputs[0].default_value = morphed_color
        color_b.location = (50, -200)

        # Link nodes
        links.new(attr.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], mix.inputs["Factor"])
        links.new(color_a.outputs[0], mix.inputs[6])  # A color
        links.new(color_b.outputs[0], mix.inputs[7])  # B color
        links.new(mix.outputs[2], bsdf.inputs["Base Color"])  # Result color
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        return mat


# Convenience functions
def create_product_morph(
    obj: bpy.types.Object,
    controller: bpy.types.Object,
    offset_z: float = 0.5,
    threshold: float = 0.5
) -> ProductMorph:
    """
    Quick setup for product morph effect.

    Args:
        obj: Object to morph
        controller: Empty controller object
        offset_z: Z-axis morph offset
        threshold: Distance threshold

    Returns:
        Configured ProductMorph with built node tree
    """
    morph = ProductMorph.from_object(obj)
    morph.set_controller(controller)
    morph.set_morph_offset(z=offset_z)
    morph.set_threshold(threshold)
    morph.pass_to_shader("morph_mask")
    morph.build()
    return morph


def create_ripple_morph(
    obj: bpy.types.Object,
    controller: bpy.types.Object,
    height: float = 0.3
) -> ProductMorph:
    """
    Create a ripple-like morph effect.

    Args:
        obj: Object to morph
        controller: Empty controller object
        height: Ripple height

    Returns:
        Configured ProductMorph with smooth falloff
    """
    morph = ProductMorph.from_object(obj)
    morph.set_controller(controller)
    morph.set_morph_offset(z=height)
    morph.set_threshold(1.0)
    morph.use_smooth_falloff(True)
    morph.pass_to_shader("morph_mask")
    morph.build()
    return morph


class MorphHUD:
    """
    Heads-Up Display for product morph effect visualization.

    Cross-references:
    - KB Section 24: Morphing Product Effect
    """

    @staticmethod
    def display_settings(
        threshold: float = 0.5,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        offset_z: float = 0.5,
        morph_scale: float = 1.0,
        smooth_falloff: bool = True,
        shader_attribute: str = "morph_mask"
    ) -> str:
        """Display current morph settings."""
        falloff_status = "ON" if smooth_falloff else "OFF"
        lines = [
            "╔══════════════════════════════════════╗",
            "║         PRODUCT MORPH SETTINGS       ║",
            "╠══════════════════════════════════════╣",
            f"║ Threshold:     {threshold:>20.2f} ║",
            f"║ Morph Scale:   {morph_scale:>20.2f} ║",
            f"║ Smooth Falloff:{falloff_status:>20} ║",
            "╠══════════════════════════════════════╣",
            "║ MORPH OFFSET                         ║",
            f"║   X:           {offset_x:>20.2f} ║",
            f"║   Y:           {offset_y:>20.2f} ║",
            f"║   Z:           {offset_z:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ SHADER OUTPUT                        ║",
            f"║   Attribute:   {shader_attribute:>20} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_mask_formula() -> str:
        """Display the morph mask calculation formula."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║         MORPH MASK FORMULA           ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  1. Calculate distance:              ║",
            "║     d = |controller_pos - point_pos| ║",
            "║                                      ║",
            "║  2. Compare to threshold:            ║",
            "║     in_range = (d < threshold)       ║",
            "║                                      ║",
            "║  3. Optional smooth falloff:         ║",
            "║     mask = map_range(d,              ║",
            "║              0→threshold,            ║",
            "║              1→0)                    ║",
            "║                                      ║",
            "║  4. Apply offset:                    ║",
            "║     pos += mask × morph_offset       ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for morph effect."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║          MORPH NODE FLOW             ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       ├──→ [Object Info] ← Controller║",
            "║       │           │                  ║",
            "║       │    [Vector Distance]         ║",
            "║       │           │                  ║",
            "║       │      [Compare]               ║",
            "║       │       (d < threshold)        ║",
            "║       │           │                  ║",
            "║       │   [Map Range] (smooth)       ║",
            "║       │           │                  ║",
            "║       │   [Float Curve]              ║",
            "║       │           │                  ║",
            "║       └──→ [Store Named Attribute]   ║",
            "║                   │                  ║",
            "║          [Math × Offset] (X,Y,Z)     ║",
            "║                   │                  ║",
            "║           [Combine XYZ]              ║",
            "║                   │                  ║",
            "║           [Set Position]             ║",
            "║                   │                  ║",
            "║          [Scale Elements]            ║",
            "║                   │                  ║",
            "║          [Group Output]              ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for morph setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       MORPH PRE-FLIGHT CHECKLIST     ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Controller empty created          ║",
            "║    (will drive morph position)       ║",
            "║                                      ║",
            "║  □ Controller assigned to input      ║",
            "║                                      ║",
            "║  □ Threshold distance set            ║",
            "║    (size of morph region)            ║",
            "║                                      ║",
            "║  □ Morph offset configured           ║",
            "║    (usually Z for lift effect)       ║",
            "║                                      ║",
            "║  □ Smooth falloff enabled            ║",
            "║    (for natural transition)          ║",
            "║                                      ║",
            "║  □ Shader attribute passed           ║",
            "║    (for material color change)       ║",
            "║                                      ║",
            "║  □ Animate controller movement       ║",
            "║    (keyframe position)               ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_shader_integration() -> str:
        """Display shader integration guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       SHADER INTEGRATION             ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  In Shader Editor:                   ║",
            "║                                      ║",
            "║  1. Add Attribute Node               ║",
            "║     Name: morph_mask                 ║",
            "║                                      ║",
            "║  2. Use Fac output (0-1)             ║",
            "║     0 = not morphed                  ║",
            "║     1 = fully morphed                ║",
            "║                                      ║",
            "║  3. Mix colors:                      ║",
            "║     Original ← Factor → Morphed      ║",
            "║                                      ║",
            "║  Result: Color changes where         ║",
            "║          geometry morphs             ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_morph_settings(**kwargs) -> None:
    """Print morph settings to console."""
    print(MorphHUD.display_settings(**kwargs))
