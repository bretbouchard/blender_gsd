"""
Motion Graphics Module - Codified from Tutorial 37

Implements After Effects-style text animation using geometry nodes.
Based on Bad Normals tutorial: https://youtu.be/S-oKPtOG6DA

Usage:
    from lib.mograph import TextAnimator

    # Create animated text
    text = TextAnimator.create("HELLO")
    text.set_font_size(2.0)
    text.add_wave_animation(axis='Y', amplitude=0.5)
    tree = text.build()  # Creates the actual node tree
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


class TextAnimator:
    """
    Motion graphics text animation using geometry nodes.

    THE GOLDEN RULE: Never use text objects for animation.
    Always use String to Curves node in geometry nodes.

    Creates a complete node tree with:
    - String to Curves node for text
    - Fill Curve for solid letters
    - Index-based per-character animation
    - Wave/rotation animation support

    Cross-references:
    - KB Section 37: After Effects Style Text Animation (Bad Normals)
    - lib/nodekit.py: For node tree building
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._text = "TEXT"
        self._font_size = 1.0
        self._character_spacing = 1.0
        self._alignment = 'CENTER'
        self._pivot_mode = 'MIDPOINT'
        self._wave_settings = {
            'axis': 'Y',
            'amplitude': 0.5,
            'frequency': 1.0,
            'speed': 1.0
        }
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "TextAnimator") -> "TextAnimator":
        """
        Create a new geometry node tree for text animation.

        Args:
            name: Name for the node group

        Returns:
            Configured TextAnimator instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "TextAnimator"
    ) -> "TextAnimator":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach to
            name: Name for the node group

        Returns:
            Configured TextAnimator instance
        """
        # Add geometry nodes modifier
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
            name="Text", in_out='INPUT', socket_type='NodeSocketString',
            default_value=self._text
        )
        self.node_tree.interface.new_socket(
            name="Font Size", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._font_size, min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Character Spacing", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._character_spacing, min_value=0.5
        )
        self.node_tree.interface.new_socket(
            name="Wave Amplitude", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._wave_settings['amplitude']
        )
        self.node_tree.interface.new_socket(
            name="Wave Frequency", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._wave_settings['frequency'], min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Wave Speed", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._wave_settings['speed'], min_value=0.01
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_text(self, text: str) -> "TextAnimator":
        """Set the text string."""
        self._text = text
        return self

    def set_font_size(self, size: float) -> "TextAnimator":
        """Set font size in Blender units."""
        self._font_size = size
        return self

    def set_character_spacing(self, spacing: float) -> "TextAnimator":
        """Set spacing between characters."""
        self._character_spacing = spacing
        return self

    def set_alignment(self, alignment: str) -> "TextAnimator":
        """Set text alignment (LEFT, CENTER, RIGHT, JUSTIFY)."""
        self._alignment = alignment
        return self

    def set_pivot(self, mode: str) -> "TextAnimator":
        """Set pivot point for transformations."""
        self._pivot_mode = mode
        return self

    def add_wave_animation(
        self,
        axis: str = 'Y',
        amplitude: float = 0.5,
        frequency: float = 1.0,
        speed: float = 1.0
    ) -> "TextAnimator":
        """Configure wave animation for characters."""
        self._wave_settings = {
            'axis': axis,
            'amplitude': amplitude,
            'frequency': frequency,
            'speed': speed
        }
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for text animation.

        KB Reference: Section 37 - Mograph Text Creation

        Returns:
            The configured node tree
        """
        if not self.nk:
            raise RuntimeError("Call create() or from_object() first")

        nk = self.nk
        x = 0  # X position tracker

        # === INPUT NODES ===
        group_in = nk.group_input(x=0, y=0)
        self._created_nodes['group_input'] = group_in
        x += 200

        # === STRING TO CURVES ===
        # KB Reference: Section 37 - THE GOLDEN RULE: Never use text objects
        string_to_curves = nk.n(
            "GeometryNodeStringToCurves",
            "String to Curves",
            x=x, y=100
        )
        # Connect text and font size
        nk.link(group_in.outputs["Text"], string_to_curves.inputs["String"])
        nk.link(group_in.outputs["Font Size"], string_to_curves.inputs["Size"])
        nk.link(group_in.outputs["Character Spacing"], string_to_curves.inputs["Character Spacing"])

        # Set alignment
        align_map = {'LEFT': 'LEFT', 'CENTER': 'CENTER', 'RIGHT': 'RIGHT', 'JUSTIFY': 'JUSTIFY'}
        string_to_curves.align_x = align_map.get(self._alignment, 'CENTER')
        string_to_curves.pivot_mode = self._pivot_mode

        self._created_nodes['string_to_curves'] = string_to_curves

        x += 300

        # === FILL CURVE ===
        # KB Reference: Section 37 - Fill Curve for solid text
        fill_curve = nk.n(
            "GeometryNodeFillCurve",
            "Fill Curve",
            x=x, y=100
        )
        fill_curve.mode = 'TRIANGLES'
        nk.link(string_to_curves.outputs["Curve"], fill_curve.inputs["Curve"])
        self._created_nodes['fill_curve'] = fill_curve

        x += 250

        # === PER-CHARACTER ANIMATION ===
        # KB Reference: Section 37 - Index-based per-character animation

        # Get index for per-character offset
        index = nk.n(
            "GeometryNodeInputIndex",
            "Index",
            x=x, y=-100
        )
        self._created_nodes['index'] = index

        # Scene time for animation
        scene_time = nk.n(
            "GeometryNodeInputSceneTime",
            "Scene Time",
            x=x, y=-200
        )
        self._created_nodes['scene_time'] = scene_time

        # === WAVE ANIMATION ===
        # KB Reference: Section 37 - Wave: Index × stagger + time

        # Index × frequency (stagger)
        index_mult = nk.n(
            "ShaderNodeMath",
            "Index × Freq",
            x=x + 200, y=-100
        )
        index_mult.operation = 'MULTIPLY'
        nk.link(index.outputs["Index"], index_mult.inputs[0])
        nk.link(group_in.outputs["Wave Frequency"], index_mult.inputs[1])
        self._created_nodes['index_mult'] = index_mult

        # Time × speed
        time_mult = nk.n(
            "ShaderNodeMath",
            "Time × Speed",
            x=x + 200, y=-200
        )
        time_mult.operation = 'MULTIPLY'
        nk.link(scene_time.outputs["Seconds"], time_mult.inputs[0])
        nk.link(group_in.outputs["Wave Speed"], time_mult.inputs[1])
        self._created_nodes['time_mult'] = time_mult

        # Add for phase offset
        phase_add = nk.n(
            "ShaderNodeMath",
            "Phase",
            x=x + 400, y=-150
        )
        phase_add.operation = 'ADD'
        nk.link(index_mult.outputs[0], phase_add.inputs[0])
        nk.link(time_mult.outputs[0], phase_add.inputs[1])
        self._created_nodes['phase_add'] = phase_add

        # Sine wave
        sine = nk.n(
            "ShaderNodeMath",
            "Sin",
            x=x + 600, y=-150
        )
        sine.operation = 'SINE'
        nk.link(phase_add.outputs[0], sine.inputs[0])
        self._created_nodes['sine'] = sine

        # Multiply by amplitude
        amp_mult = nk.n(
            "ShaderNodeMath",
            "× Amplitude",
            x=x + 800, y=-150
        )
        amp_mult.operation = 'MULTIPLY'
        nk.link(sine.outputs[0], amp_mult.inputs[0])
        nk.link(group_in.outputs["Wave Amplitude"], amp_mult.inputs[1])
        self._created_nodes['amp_mult'] = amp_mult

        x += 1050

        # === COMBINE OFFSET ===
        # Create offset vector based on wave axis
        offset = nk.n(
            "ShaderNodeCombineXYZ",
            "Wave Offset",
            x=x, y=100
        )

        axis = self._wave_settings['axis']
        if axis == 'X':
            nk.link(amp_mult.outputs[0], offset.inputs["X"])
            offset.inputs["Y"].default_value = 0.0
            offset.inputs["Z"].default_value = 0.0
        elif axis == 'Y':
            offset.inputs["X"].default_value = 0.0
            nk.link(amp_mult.outputs[0], offset.inputs["Y"])
            offset.inputs["Z"].default_value = 0.0
        else:  # Z
            offset.inputs["X"].default_value = 0.0
            offset.inputs["Y"].default_value = 0.0
            nk.link(amp_mult.outputs[0], offset.inputs["Z"])

        self._created_nodes['offset'] = offset

        x += 200

        # === SET POSITION ===
        set_position = nk.n(
            "GeometryNodeSetPosition",
            "Animate",
            x=x, y=100
        )
        nk.link(fill_curve.outputs["Geometry"], set_position.inputs["Geometry"])
        nk.link(offset.outputs["Vector"], set_position.inputs["Offset"])
        self._created_nodes['set_position'] = set_position

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(set_position.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class TrailEffect:
    """
    Motion trail effect for text/objects.

    Cross-references:
    - KB Section 37: Trail Effect Behind Text
    """

    def __init__(self, count: int = 5):
        self._trail_count = count
        self._fade_factor = 0.8
        self._offset = 0.1

    @staticmethod
    def add_trail_nodes(
        nk: NodeKit,
        geometry_socket,
        count: int = 5,
        offset: Tuple[float, float, float] = (-0.1, 0, 0),
        x: float = 0,
        y: float = 0
    ) -> bpy.types.Node:
        """
        Add trail effect nodes.

        Args:
            nk: NodeKit instance
            geometry_socket: Input geometry
            count: Number of trail copies
            offset: Offset per trail copy
            x, y: Position for nodes

        Returns:
            Join Geometry node with all copies
        """
        # This is simplified - a full implementation would use
        # repeat zones or multiple instance nodes

        # Create mesh line for trail points
        mesh_line = nk.n("GeometryNodeMeshLine", "Trail Points", x=x, y=y - 100)
        mesh_line.inputs["Count"].default_value = count
        mesh_line.inputs["Resolution"].default_value = 1.0

        # Offset based on index
        index = nk.n("GeometryNodeInputIndex", "Trail Index", x=x + 200, y=y - 100)

        # Multiply by offset
        offset_mult = nk.n("ShaderNodeMath", "× Offset", x=x + 400, y=y - 100)
        offset_mult.operation = 'MULTIPLY'
        offset_mult.inputs[1].default_value = offset[0]  # X offset
        nk.link(index.outputs["Index"], offset_mult.inputs[0])

        # Combine offset
        combine = nk.n("ShaderNodeCombineXYZ", "Trail Offset", x=x + 600, y=y - 100)
        nk.link(offset_mult.outputs[0], combine.inputs["X"])
        combine.inputs["Y"].default_value = offset[1]
        combine.inputs["Z"].default_value = offset[2]

        # Instance on points
        instance = nk.n("GeometryNodeInstanceOnPoints", "Trail Instances", x=x + 800, y=y)
        nk.link(mesh_line.outputs["Mesh"], instance.inputs["Points"])
        nk.link(geometry_socket, instance.inputs["Instance"])
        nk.link(combine.outputs["Vector"], instance.inputs["Translation"])

        return instance

    def set_count(self, count: int) -> "TrailEffect":
        """Set number of trail copies."""
        self._trail_count = count
        return self

    def set_fade(self, fade: float) -> "TrailEffect":
        """Set fade factor between copies."""
        self._fade_factor = fade
        return self

    def set_offset(self, offset: float) -> "TrailEffect":
        """Set position offset between copies."""
        self._offset = offset
        return self


class PerCharacterAnimator:
    """
    Animate each character independently.

    Cross-references:
    - KB Section 37: Per-Character Animation
    """

    @staticmethod
    def add_rotation_animation(
        nk: NodeKit,
        geometry_socket,
        axis: str = 'Z',
        stagger: float = 0.1,
        speed: float = 1.0,
        x: float = 0,
        y: float = 0
    ) -> bpy.types.Node:
        """
        Add per-character rotation animation.

        Args:
            nk: NodeKit instance
            geometry_socket: Input geometry
            axis: Rotation axis
            stagger: Delay between characters
            speed: Rotation speed
            x, y: Position for nodes

        Returns:
            Rotate Instances node
        """
        # Get index
        index = nk.n("GeometryNodeInputIndex", "Index", x=x, y=y - 50)

        # Index × stagger
        stagger_mult = nk.n("ShaderNodeMath", "Index × Stagger", x=x + 200, y=y - 50)
        stagger_mult.operation = 'MULTIPLY'
        stagger_mult.inputs[1].default_value = stagger
        nk.link(index.outputs["Index"], stagger_mult.inputs[0])

        # Scene time
        scene_time = nk.n("GeometryNodeInputSceneTime", "Time", x=x + 200, y=y - 150)

        # Time × speed
        time_mult = nk.n("ShaderNodeMath", "Time × Speed", x=x + 400, y=y - 150)
        time_mult.operation = 'MULTIPLY'
        time_mult.inputs[1].default_value = speed
        nk.link(scene_time.outputs["Seconds"], time_mult.inputs[0])

        # Add stagger
        phase = nk.n("ShaderNodeMath", "Phase", x=x + 600, y=y - 100)
        phase.operation = 'ADD'
        nk.link(stagger_mult.outputs[0], phase.inputs[0])
        nk.link(time_mult.outputs[0], phase.inputs[1])

        # Convert to radians for rotation
        rotation = nk.n("ShaderNodeMath", "Rotation", x=x + 800, y=y - 100)
        rotation.operation = 'MULTIPLY'
        rotation.inputs[1].default_value = math.pi * 2  # Full rotation
        nk.link(phase.outputs[0], rotation.inputs[0])

        # Combine rotation axis
        rot_combine = nk.n("ShaderNodeCombineXYZ", "Rot Axis", x=x + 1000, y=y - 100)
        rot_combine.inputs["X"].default_value = math.pi * 2 if axis == 'X' else 0.0
        rot_combine.inputs["Y"].default_value = math.pi * 2 if axis == 'Y' else 0.0
        rot_combine.inputs["Z"].default_value = math.pi * 2 if axis == 'Z' else 0.0

        # Actually link rotation value
        if axis == 'X':
            nk.link(rotation.outputs[0], rot_combine.inputs["X"])
        elif axis == 'Y':
            nk.link(rotation.outputs[0], rot_combine.inputs["Y"])
        else:
            nk.link(rotation.outputs[0], rot_combine.inputs["Z"])

        # Rotate instances
        rotate = nk.n("GeometryNodeRotateInstances", "Rotate Chars", x=x + 1200, y=y)
        nk.link(geometry_socket, rotate.inputs["Instances"])
        nk.link(rot_combine.outputs["Vector"], rotate.inputs["Rotation"])

        return rotate

    @staticmethod
    def get_animation_types() -> dict:
        """Get available per-character animation types."""
        return {
            "wave": {
                "description": "Characters move in wave pattern",
                "axes": ["X", "Y", "Z"]
            },
            "typewriter": {
                "description": "Characters appear one by one",
                "method": "Scale from 0 to 1 by index"
            },
            "explosion": {
                "description": "Characters explode outward",
                "method": "Random direction × force"
            },
            "bounce": {
                "description": "Characters bounce in sequence",
                "method": "Sin wave with index offset"
            },
            "scramble": {
                "description": "Characters shuffle then settle",
                "method": "Random position → target position"
            }
        }


class MographWorkflow:
    """
    Complete motion graphics workflow.

    Cross-references:
    - KB Section 37: Mograph Text Creation
    """

    @staticmethod
    def get_complete_workflow() -> list:
        """Get complete mograph text creation workflow."""
        return [
            "1. Add any mesh object",
            "2. Add geometry nodes modifier",
            "3. Delete group input connection",
            "4. Add String to Curves node",
            "5. Input your text string",
            "6. Add Fill Curve for solid text",
            "7. Add animation nodes (position, rotation)",
            "8. Use index for per-character offset",
            "9. Add trail/delay effects",
            "10. Style with materials"
        ]

    @staticmethod
    def get_pro_tips() -> dict:
        """Get pro tips for mograph animation."""
        return {
            "animation": [
                "Use Scene Time for frame-based animation",
                "Math nodes for wave/sine effects",
                "Random value for organic motion",
                "Mix vectors for smooth transitions"
            ],
            "performance": [
                "Keep point count low",
                "Use instances where possible",
                "Don't over-subdivide curves"
            ]
        }


# Convenience functions
def create_animated_text(
    text: str,
    animation_type: str = "wave",
    font_size: float = 1.0
) -> TextAnimator:
    """
    Quick setup for animated text.

    Args:
        text: Text string
        animation_type: wave, typewriter, explosion, bounce
        font_size: Font size

    Returns:
        Configured TextAnimator with built node tree
    """
    # Create a simple mesh to attach to
    bpy.ops.mesh.primitive_plane_add(size=0.1)
    obj = bpy.context.active_object
    obj.name = "AnimatedText"

    animator = TextAnimator.from_object(obj)
    animator.set_text(text)
    animator.set_font_size(font_size)

    if animation_type == "wave":
        animator.add_wave_animation()

    animator.build()
    return animator


def create_text_with_trail(
    text: str,
    trail_count: int = 5
) -> Tuple[TextAnimator, TrailEffect]:
    """
    Create animated text with trail effect.

    Args:
        text: Text string
        trail_count: Number of trail copies

    Returns:
        Tuple of (TextAnimator, TrailEffect)
    """
    text_anim = create_animated_text(text)
    trail = TrailEffect(count=trail_count)
    trail.set_fade(0.7)

    return text_anim, trail


class MographHUD:
    """
    Heads-Up Display for motion graphics visualization.

    Cross-references:
    - KB Section 37: Motion graphics visualization
    """

    @staticmethod
    def display_settings(
        text: str = "TEXT",
        font_size: float = 1.0,
        character_spacing: float = 1.0,
        wave_amplitude: float = 0.5,
        wave_frequency: float = 1.0,
        wave_speed: float = 1.0
    ) -> str:
        """
        Display mograph text settings.

        Args:
            text: Text string
            font_size: Font size
            character_spacing: Character spacing
            wave_amplitude: Wave amplitude
            wave_frequency: Wave frequency
            wave_speed: Wave speed

        Returns:
            Formatted settings display
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'MOGRAPH TEXT SETTINGS':^48}│")
        lines.append("├" + "─" * 48 + "┤")
        lines.append(f"│ Text:             {text:>20}         │")
        lines.append(f"│ Font Size:        {font_size:>10.2f}              │")
        lines.append(f"│ Char Spacing:     {character_spacing:>10.2f}              │")
        lines.append(f"│ Wave Amplitude:   {wave_amplitude:>10.2f}              │")
        lines.append(f"│ Wave Frequency:   {wave_frequency:>10.2f}              │")
        lines.append(f"│ Wave Speed:       {wave_speed:>10.2f}              │")
        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_animation_types() -> str:
        """
        Display available animation types.

        Returns:
            Formatted animation types guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'ANIMATION TYPES':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        animations = [
            ("Wave", "Characters move in wave pattern", "Index × frequency + time"),
            ("Typewriter", "Characters appear one by one", "Scale 0→1 by index"),
            ("Explosion", "Characters explode outward", "Random direction × force"),
            ("Bounce", "Characters bounce in sequence", "Sin wave with offset"),
            ("Scramble", "Characters shuffle then settle", "Random → target position"),
            ("Rotation", "Per-character rotation", "Index × stagger + time"),
        ]

        for name, desc, method in animations:
            lines.append(f"│ {name:<12}: {desc:<24}│")
            lines.append(f"│              Method: {method:<26}│")
            lines.append("│" + " " * 48 + "│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_wave_formula() -> str:
        """
        Display wave animation formula.

        Returns:
            Formatted formula breakdown
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'WAVE ANIMATION FORMULA':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        lines.append("║")
        lines.append("║   Offset = sin((Index × Frequency) + (Time × Speed))")
        lines.append("║                × Amplitude")
        lines.append("║")
        lines.append("╠" + "─" * 48 + "╣")

        breakdown = [
            ("Index", "Character index (0, 1, 2, ...)"),
            ("Frequency", "How fast wave repeats across chars"),
            ("Time", "Scene time (seconds or frames)"),
            ("Speed", "Animation speed multiplier"),
            ("Amplitude", "Maximum offset distance"),
        ]

        for var, desc in breakdown:
            lines.append(f"║   {var:<12}: {desc:<32}│")

        lines.append("╠" + "─" * 48 + "╣")
        lines.append("║ Effect: Each character moves up/down with offset timing")
        lines.append("║ Result: Wave-like motion across the text")
        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """
        Display mograph node flow diagram.

        Returns:
            Formatted node flow diagram
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'MOGRAPH NODE FLOW':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        lines.append("║")
        lines.append("║   [Group Input] ──→ [String to Curves]")
        lines.append("║          │                 │")
        lines.append("║          │                 ↓")
        lines.append("║          │          [Fill Curve]")
        lines.append("║          │                 │")
        lines.append("║          │                 ↓")
        lines.append("║   [Scene Time] ──→ [× Speed] ──→ Phase")
        lines.append("║          │                 │")
        lines.append("║   [Index] ──→ [× Freq] ────┼──→ [Add]")
        lines.append("║                            │      │")
        lines.append("║                            └──────┤")
        lines.append("║                                   ↓")
        lines.append("║                              [Sin Wave]")
        lines.append("║                                   │")
        lines.append("║   [Amplitude] ────────────────────┼──→ [Multiply]")
        lines.append("║                                   │        │")
        lines.append("║                                   ↓        ↓")
        lines.append("║                            [Combine XYZ] → Offset")
        lines.append("║                                        │")
        lines.append("║                                        ↓")
        lines.append("║   [Fill Curve Geo] ────────────→ [Set Position]")
        lines.append("║                                        │")
        lines.append("║                                        ↓")
        lines.append("║                                     [Output]")
        lines.append("║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """
        Display mograph setup checklist.

        Returns:
            Formatted checklist
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'MOGRAPH TEXT CHECKLIST':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        checklist = [
            ("THE GOLDEN RULE", [
                "☐ NEVER use text objects for animation!",
                "☐ Always use String to Curves node",
            ]),
            ("Setup", [
                "☐ Add any mesh object",
                "☐ Add geometry nodes modifier",
                "☐ Delete group input connection",
            ]),
            ("Text Creation", [
                "☐ Add String to Curves node",
                "☐ Input your text string",
                "☐ Set font size and spacing",
                "☐ Add Fill Curve for solid text",
            ]),
            ("Animation", [
                "☐ Add Index node for per-char offset",
                "☐ Add Scene Time for animation",
                "☐ Create wave/rotation formula",
                "☐ Add Set Position node",
            ]),
        ]

        for category, items in checklist:
            lines.append(f"║ {category}:")
            for item in items:
                lines.append(f"║   {item}")
            lines.append("║" + " " * 50 + "║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_trail_guide() -> str:
        """
        Display trail effect guide.

        Returns:
            Formatted trail guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'TRAIL EFFECT GUIDE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        lines.append("│ Parameters:")
        lines.append("│   Count:     Number of trail copies")
        lines.append("│   Offset:    Distance between copies")
        lines.append("│   Fade:      Opacity reduction per copy")
        lines.append("│")
        lines.append("│ Common Settings:")

        presets = [
            ("Subtle", 3, 0.05, 0.9),
            ("Standard", 5, 0.1, 0.8),
            ("Long", 8, 0.15, 0.7),
            ("Ghost", 12, 0.2, 0.5),
        ]

        for name, count, offset, fade in presets:
            lines.append(f"│   {name:<10}: {count} copies, offset {offset}, fade {fade}")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)


def print_mograph_settings(**kwargs) -> None:
    """Print mograph settings to console."""
    print(MographHUD.display_settings(**kwargs))
