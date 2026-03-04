"""
Painterly Brush Stroke Effect Module - Codified from Tutorial 14

Implements non-photorealistic rendering effect that gives 3D renders
a hand-painted appearance using geometry nodes to instance brush
stroke planes on mesh surfaces.

Based on FFuthoni tutorial: https://www.youtube.com/watch?v=Y0zAZnbBcQU

Usage:
    from lib.painterly import BrushStrokeEffect

    # Create painterly effect
    painterly = BrushStrokeEffect.create("PainterlyEffect")
    painterly.set_density(5000)  # High for detailed strokes
    painterly.set_stroke_shape(stretched_plane)
    painterly.add_rotation_variation(randomness=1.0)
    painterly.add_scale_variation(min=0.5, max=1.5)
    painterly.pass_color_to_shader("stroke_color")
    tree = painterly.build()
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


class BrushStrokeEffect:
    """
    Painterly brush stroke effect using geometry nodes.

    Creates a node tree that:
    - Distributes points on mesh faces
    - Instances stretched plane shapes (brush strokes)
    - Aligns strokes to surface normals
    - Adds random rotation and scale variation
    - Passes attributes to shader for color variation

    Cross-references:
    - KB Section 14: Painterly Brush Stroke Effect (FFuthoni)
    - KB Section 2: Geometric Minimalism (similar emission style)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._density = 5000
        self._seed = 42
        self._stroke_scale = 0.05
        self._stroke_stretch = 3.0  # X/Y ratio
        self._rotation_variation = 1.0
        self._scale_min = 0.5
        self._scale_max = 1.5
        self._color_variation = True
        self._color_attribute = "stroke_color"
        self._align_to_normal = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "BrushStrokeEffect") -> "BrushStrokeEffect":
        """
        Create a new geometry node tree for painterly effect.

        Args:
            name: Name for the node group

        Returns:
            Configured BrushStrokeEffect instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "BrushStrokeEffect"
    ) -> "BrushStrokeEffect":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to apply painterly effect to
            name: Name for the node group

        Returns:
            Configured BrushStrokeEffect instance
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
            name="Density", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._density, min_value=100, max_value=50000
        )
        self.node_tree.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._seed
        )
        self.node_tree.interface.new_socket(
            name="Stroke Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._stroke_scale, min_value=0.001, max_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Stroke Stretch", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._stroke_stretch, min_value=1.0, max_value=10.0
        )
        self.node_tree.interface.new_socket(
            name="Rotation Variation", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._rotation_variation, min_value=0.0, max_value=6.28
        )
        self.node_tree.interface.new_socket(
            name="Scale Min", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._scale_min, min_value=0.1, max_value=2.0
        )
        self.node_tree.interface.new_socket(
            name="Scale Max", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._scale_max, min_value=0.1, max_value=3.0
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_density(self, density: float) -> "BrushStrokeEffect":
        """
        Set stroke density.

        Args:
            density: High (5000+) for detailed Van Gogh style,
                     Low (500) for impressionist style
        """
        self._density = density
        return self

    def set_stroke_shape(self, scale: float = 0.05, stretch: float = 3.0) -> "BrushStrokeEffect":
        """
        Set stroke plane dimensions.

        Args:
            scale: Base stroke size
            stretch: X/Y ratio (higher = more stretched brush strokes)
        """
        self._stroke_scale = scale
        self._stroke_stretch = stretch
        return self

    def add_rotation_variation(self, randomness: float = 1.0) -> "BrushStrokeEffect":
        """
        Add random Z-rotation for natural brush direction.

        Args:
            randomness: Rotation variation in radians (pi = 180°)
        """
        self._rotation_variation = randomness
        return self

    def add_scale_variation(self, min_scale: float = 0.5, max_scale: float = 1.5) -> "BrushStrokeEffect":
        """
        Add random scale variation for organic feel.

        Args:
            min_scale: Minimum scale multiplier
            max_scale: Maximum scale multiplier
        """
        self._scale_min = min_scale
        self._scale_max = max_scale
        return self

    def pass_color_to_shader(self, attribute_name: str = "stroke_color") -> "BrushStrokeEffect":
        """
        Enable passing random color to shader via named attribute.

        Args:
            attribute_name: Name for shader Attribute node
        """
        self._color_variation = True
        self._color_attribute = attribute_name
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for painterly brush stroke effect.

        KB Reference: Section 14 - Painterly Brush Stroke Effect

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

        # === DISTRIBUTE POINTS ON FACES ===
        # KB Reference: Section 14 - Distribute Points on Faces
        distribute = nk.n(
            "GeometryNodeDistributePointsOnFaces",
            "Distribute Strokes",
            x=x, y=100
        )
        distribute.distribute_method = 'RANDOM'
        nk.link(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
        nk.link(group_in.outputs["Density"], distribute.inputs["Density"])
        nk.link(group_in.outputs["Seed"], distribute.inputs["Seed"])
        self._created_nodes['distribute'] = distribute

        x += 250

        # === CREATE STROKE PLANE ===
        # KB Reference: Section 14 - Stretched plane for stroke shape
        grid = nk.n(
            "GeometryNodeMeshGrid",
            "Stroke Plane",
            x=x, y=-150
        )
        # Create stretched rectangle
        # Size X = scale * stretch, Size Y = scale
        stretch_mult = nk.n("ShaderNodeMath", "Stretch", x=x + 100, y=-250)
        stretch_mult.operation = 'MULTIPLY'
        nk.link(group_in.outputs["Stroke Scale"], stretch_mult.inputs[0])
        nk.link(group_in.outputs["Stroke Stretch"], stretch_mult.inputs[1])

        nk.link(stretch_mult.outputs[0], grid.inputs["Size X"])
        nk.link(group_in.outputs["Stroke Scale"], grid.inputs["Size Y"])
        grid.inputs["Vertices X"].default_value = 4
        grid.inputs["Vertices Y"].default_value = 2
        self._created_nodes['grid'] = grid
        self._created_nodes['stretch_mult'] = stretch_mult

        x += 300

        # === NORMAL FOR ALIGNMENT ===
        normal = nk.n(
            "GeometryNodeInputNormal",
            "Surface Normal",
            x=x, y=200
        )
        nk.link(distribute.outputs["Points"], normal.inputs["Geometry"])
        self._created_nodes['normal'] = normal

        x += 200

        # === ALIGN ROTATION TO VECTOR ===
        # KB Reference: Section 14 - Align to surface normals
        align = nk.n(
            "GeometryNodeAlignRotationToVector",
            "Align to Normal",
            x=x, y=100
        )
        align.inputs["Axis"].default_value = 'Z'  # Point normal up
        nk.link(normal.outputs["Normal"], align.inputs["Vector"])
        self._created_nodes['align'] = align

        x += 200

        # === RANDOM ROTATION (Z-AXIS) ===
        # KB Reference: Section 14 - Randomize stroke direction
        random_rot = nk.n(
            "FunctionNodeRandomValue",
            "Random Rotation",
            x=x, y=250
        )
        random_rot.data_type = 'FLOAT'
        random_rot.inputs[2].default_value = 0.0  # Min
        nk.link(group_in.outputs["Rotation Variation"], random_rot.inputs[3])  # Max
        nk.link(group_in.outputs["Seed"], random_rot.inputs[4])  # Seed
        self._created_nodes['random_rot'] = random_rot

        # Add rotation to aligned rotation
        add_rot = nk.n("ShaderNodeMath", "Add Rotation", x=x + 150, y=250)
        add_rot.operation = 'ADD'
        nk.link(align.outputs["Rotation"], add_rot.inputs[0])
        nk.link(random_rot.outputs[0], add_rot.inputs[1])
        self._created_nodes['add_rot'] = add_rot

        x += 350

        # === RANDOM SCALE ===
        # KB Reference: Section 14 - Scale variation for natural look
        random_scale = nk.n(
            "FunctionNodeRandomValue",
            "Random Scale",
            x=x, y=350
        )
        random_scale.data_type = 'FLOAT'
        nk.link(group_in.outputs["Scale Min"], random_scale.inputs[2])
        nk.link(group_in.outputs["Scale Max"], random_scale.inputs[3])
        nk.link(group_in.outputs["Seed"], random_scale.inputs[4])
        self._created_nodes['random_scale'] = random_scale

        # Combine into scale vector
        scale_vec = nk.n("ShaderNodeCombineXYZ", "Scale Vec", x=x + 150, y=350)
        nk.link(random_scale.outputs[0], scale_vec.inputs["X"])
        nk.link(random_scale.outputs[0], scale_vec.inputs["Y"])
        scale_vec.inputs["Z"].default_value = 1.0  # Don't scale Z
        self._created_nodes['scale_vec'] = scale_vec

        x += 350

        # === OPTIONAL: STORE COLOR ATTRIBUTE ===
        if self._color_variation:
            # KB Reference: Section 14 - Color variation per stroke
            random_color = nk.n(
                "FunctionNodeRandomValue",
                "Random Color",
                x=x, y=-50
            )
            random_color.data_type = 'FLOAT'
            random_color.inputs[2].default_value = 0.0
            random_color.inputs[3].default_value = 1.0
            nk.link(group_in.outputs["Seed"], random_color.inputs[4])
            self._created_nodes['random_color'] = random_color

            # Store for shader
            store_color = nk.n(
                "GeometryNodeStoreNamedAttribute",
                "Store Color",
                x=x + 150, y=100
            )
            store_color.inputs["Name"].default_value = self._color_attribute
            store_color.domain = 'INSTANCE'
            nk.link(distribute.outputs["Points"], store_color.inputs["Geometry"])
            nk.link(random_color.outputs[0], store_color.inputs["Value"])
            self._created_nodes['store_color'] = store_color

            points_out = store_color
            x += 350
        else:
            points_out = distribute

        self._created_nodes['points_out'] = points_out

        # === INSTANCE ON POINTS ===
        # KB Reference: Section 14 - Instance brush stroke planes
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance Strokes",
            x=x, y=100
        )
        nk.link(points_out.outputs["Points"] if hasattr(points_out, 'outputs') and "Points" in points_out.outputs else points_out.outputs["Geometry"], instance.inputs["Points"])
        nk.link(grid.outputs["Mesh"], instance.inputs["Instance"])
        nk.link(add_rot.outputs[0], instance.inputs["Rotation"])
        nk.link(scale_vec.outputs["Vector"], instance.inputs["Scale"])
        self._created_nodes['instance'] = instance

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(instance.outputs["Instances"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class PainterlyMaterial:
    """
    Helper for creating painterly shader that responds to stroke attributes.

    Cross-references:
    - KB Section 14: Color variation in shader
    - KB Section 2: Emission-only workflow
    """

    @staticmethod
    def create_painterly_material(
        name: str = "PainterlyMaterial",
        base_color: tuple = (0.8, 0.6, 0.2, 1.0),
        color_variation: float = 0.3,
        attribute_name: str = "stroke_color"
    ) -> bpy.types.Material:
        """
        Create a material for painterly effect with color variation.

        Args:
            name: Material name
            base_color: RGBA base color
            color_variation: Amount of color variation (0-1)
            attribute_name: Name of the color attribute from geometry nodes

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

        # Create emission BSDF (painterly style)
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (400, 0)

        # Create attribute node for color variation
        attr = nodes.new('ShaderNodeAttribute')
        attr.attribute_name = attribute_name
        attr.location = (0, -100)

        # Color ramp for variation
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (150, -100)
        # Configure ramp for color variation

        # Mix base color with variation
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.location = (250, 0)

        # Base color input
        color = nodes.new('ShaderNodeRGB')
        color.outputs[0].default_value = base_color
        color.location = (50, 100)

        # Variation color (slightly different)
        var_color = nodes.new('ShaderNodeRGB')
        var_color.outputs[0].default_value = (
            base_color[0] * (1 + color_variation),
            base_color[1] * (1 - color_variation * 0.5),
            base_color[2] * (1 + color_variation * 0.3),
            1.0
        )
        var_color.location = (50, -200)

        # Link nodes
        links.new(attr.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], mix.inputs["Factor"])
        links.new(color.outputs[0], mix.inputs[6])
        links.new(var_color.outputs[0], mix.inputs[7])
        links.new(mix.outputs[2], emission.inputs["Color"])
        links.new(emission.outputs["Emission"], output.inputs["Surface"])

        return mat


class PainterlyPresets:
    """
    Preset configurations for different painterly styles.

    Cross-references:
    - KB Section 14: Style variations
    - KB Section 2: Geometric Minimalism
    """

    @staticmethod
    def van_gogh() -> dict:
        """Configuration for detailed Van Gogh style."""
        return {
            "density": 8000,
            "stroke_scale": 0.03,
            "stroke_stretch": 4.0,
            "rotation_variation": 6.28,  # Full rotation
            "scale_min": 0.3,
            "scale_max": 1.5,
            "description": "High detail, swirling strokes"
        }

    @staticmethod
    def impressionist() -> dict:
        """Configuration for loose impressionist style."""
        return {
            "density": 1500,
            "stroke_scale": 0.08,
            "stroke_stretch": 2.5,
            "rotation_variation": 3.14,  # 180°
            "scale_min": 0.6,
            "scale_max": 1.2,
            "description": "Loose, visible brush strokes"
        }

    @staticmethod
    def pointillist() -> dict:
        """Configuration for pointillist style (small dots)."""
        return {
            "density": 10000,
            "stroke_scale": 0.015,
            "stroke_stretch": 1.0,  # Circular
            "rotation_variation": 0.0,  # No rotation needed
            "scale_min": 0.8,
            "scale_max": 1.2,
            "description": "Small dots of color"
        }

    @staticmethod
    def expressive() -> dict:
        """Configuration for expressive, bold strokes."""
        return {
            "density": 2000,
            "stroke_scale": 0.1,
            "stroke_stretch": 5.0,
            "rotation_variation": 1.57,  # 90°
            "scale_min": 0.5,
            "scale_max": 2.0,
            "description": "Bold, expressive brushwork"
        }


# Convenience functions
def create_painterly_effect(
    obj: bpy.types.Object,
    style: str = "impressionist"
) -> BrushStrokeEffect:
    """
    Quick setup for painterly effect with preset style.

    Args:
        obj: Object to apply effect to
        style: Preset style ("van_gogh", "impressionist", "pointillist", "expressive")

    Returns:
        Configured BrushStrokeEffect with built node tree
    """
    presets = {
        "van_gogh": PainterlyPresets.van_gogh,
        "impressionist": PainterlyPresets.impressionist,
        "pointillist": PainterlyPresets.pointillist,
        "expressive": PainterlyPresets.expressive,
    }

    preset_func = presets.get(style, PainterlyPresets.impressionist)
    preset = preset_func()

    effect = BrushStrokeEffect.from_object(obj)
    effect.set_density(preset["density"])
    effect.set_stroke_shape(preset["stroke_scale"], preset["stroke_stretch"])
    effect.add_rotation_variation(preset["rotation_variation"])
    effect.add_scale_variation(preset["scale_min"], preset["scale_max"])
    effect.pass_color_to_shader("stroke_color")
    effect.build()
    return effect


def create_van_gogh_style(obj: bpy.types.Object) -> BrushStrokeEffect:
    """Create Van Gogh style painterly effect."""
    return create_painterly_effect(obj, "van_gogh")


def create_impressionist_style(obj: bpy.types.Object) -> BrushStrokeEffect:
    """Create impressionist style painterly effect."""
    return create_painterly_effect(obj, "impressionist")


class PainterlyHUD:
    """
    Heads-Up Display for painterly brush stroke visualization.

    Cross-references:
    - KB Section 14: Painterly Brush Stroke Effect
    """

    @staticmethod
    def display_settings(
        density: float = 5000,
        stroke_scale: float = 0.05,
        stroke_stretch: float = 3.0,
        rotation_variation: float = 1.0,
        scale_min: float = 0.5,
        scale_max: float = 1.5,
        color_variation: bool = True
    ) -> str:
        """Display current painterly settings."""
        color_status = "ON" if color_variation else "OFF"
        lines = [
            "╔══════════════════════════════════════╗",
            "║       PAINTERLY EFFECT SETTINGS      ║",
            "╠══════════════════════════════════════╣",
            f"║ Density:       {density:>20.0f} ║",
            f"║ Color Var:     {color_status:>20} ║",
            "╠══════════════════════════════════════╣",
            "║ STROKE SHAPE                         ║",
            f"║   Scale:       {stroke_scale:>20.3f} ║",
            f"║   Stretch:     {stroke_stretch:>20.1f} ║",
            "╠══════════════════════════════════════╣",
            "║ VARIATION                            ║",
            f"║   Rotation:    {rotation_variation:>17.2f} rad ║",
            f"║   Scale Min:   {scale_min:>20.2f} ║",
            f"║   Scale Max:   {scale_max:>20.2f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_style_presets() -> str:
        """Display painterly style presets."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        STYLE PRESETS                 ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  VAN GOGH (detailed, swirling):      ║",
            "║    density=8000, scale=0.03          ║",
            "║    stretch=4.0, rot=6.28 (360°)      ║",
            "║                                      ║",
            "║  IMPRESSIONIST (loose, visible):     ║",
            "║    density=1500, scale=0.08          ║",
            "║    stretch=2.5, rot=3.14 (180°)      ║",
            "║                                      ║",
            "║  POINTILLIST (dots):                 ║",
            "║    density=10000, scale=0.015        ║",
            "║    stretch=1.0, rot=0                ║",
            "║                                      ║",
            "║  EXPRESSIVE (bold strokes):          ║",
            "║    density=2000, scale=0.1           ║",
            "║    stretch=5.0, rot=1.57 (90°)       ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for painterly effect."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       PAINTERLY NODE FLOW            ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       └──→ [Distribute Points]       ║",
            "║                 │                    ║",
            "║  ┌──────────────┴──────────────┐     ║",
            "║  │                             │     ║",
            "║  ↓                             ↓     ║",
            "║ [Input     [Mesh Grid]               ║",
            "║  Normal]   (stroke plane)            ║",
            "║  │         │                         ║",
            "║  ↓         │                         ║",
            "║ [Align    │                         ║",
            "║  Rotation]│                         ║",
            "║  │         │                         ║",
            "║  ↓         │                         ║",
            "║ [Random  │                         ║",
            "║  Rotation]│                         ║",
            "║  │         │                         ║",
            "║  └────┬────┘                         ║",
            "║       ↓                              ║",
            "║  [Random Scale]                      ║",
            "║       │                              ║",
            "║       ↓                              ║",
            "║  [Instance on Points]                ║",
            "║       │                              ║",
            "║  [Group Output]                      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for painterly setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║    PAINTERLY PRE-FLIGHT CHECKLIST    ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Base mesh has surface area        ║",
            "║    (points distribute on faces)      ║",
            "║                                      ║",
            "□  □ Density set for style             ║",
            "║    (500-10000 depending on look)     ║",
            "║                                      ║",
            "║  □ Stroke shape configured           ║",
            "║    (scale + stretch ratio)           ║",
            "║                                      ║",
            "□  □ Rotation variation enabled        ║",
            "║    (for natural brush direction)     ║",
            "║                                      ║",
            "□  □ Scale variation added             ║",
            "║    (0.5-1.5 for organic feel)        ║",
            "║                                      ║",
            "□  □ Material with emission           ║",
            "║    (for painterly style)             ║",
            "║                                      ║",
            "□  □ Optional: Color variation         ║",
            "║    (via shader attribute)            ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_material_tips() -> str:
        """Display material tips for painterly style."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       MATERIAL TIPS                  ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  EMISSION-ONLY (recommended):        ║",
            "║    • No shadows or highlights        ║",
            "║    • Pure flat color per stroke      ║",
            "║    • True painterly look             ║",
            "║                                      ║",
            "║  WITH LIGHTING:                      ║",
            "║    • Use Color Attribute node        ║",
            "║    • Mix with base color             ║",
            "║    • Add subtle roughness            ║",
            "║                                      ║",
            "║  COLOR VARIATION:                    ║",
            "║    • Attribute: stroke_color         ║",
            "║    • Use Color Ramp for palette      ║",
            "║    • Random per instance             ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_painterly_settings(**kwargs) -> None:
    """Print painterly settings to console."""
    print(PainterlyHUD.display_settings(**kwargs))
