"""
Seamless Animation Loop Module - Codified from Tutorial 2

Implements perfect animation loops using 4D noise and temporal offsets.
Based on Default Cube tutorial: https://youtu.be/ZWEdWkYPzvU

Usage:
    from lib.loop import SeamlessLoop, LoopPresets

    # Create seamless animation
    loop = SeamlessLoop.create("PerfectLoop")
    loop.set_duration(250)  # Frame count
    loop.use_4d_noise(scale=2.0, speed=0.5)
    loop.add_to_attribute(position_attr)
    tree = loop.build()
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


class SeamlessLoop:
    """
    Creates seamless animation loops using 4D noise.

    THE SECRET: 4D Noise with W = Frame/Duration × 2π
    - At frame 0: W = 0
    - At frame Duration: W = 2π (same as 0)
    - Result: Perfectly seamless loop

    Cross-references:
    - KB Section 2: Geometric Minimalism (Default Cube)
    - KB Section 2: Perfect Loops with 4D Noise
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._duration = 250
        self._noise_scale = 2.0
        self._noise_speed = 0.5
        self._noise_dimensions = 4
        self._position_offset = (0.0, 0.0, 0.0)
        self._rotation_offset = 0.0
        self._scale_variation = 0.0
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "SeamlessLoop") -> "SeamlessLoop":
        """
        Create a new geometry node tree for seamless looping.

        Args:
            name: Name for the node group

        Returns:
            Configured SeamlessLoop instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "SeamlessLoop"
    ) -> "SeamlessLoop":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach to
            name: Name for the node group

        Returns:
            Configured SeamlessLoop instance
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
            name="Duration", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._duration, min_value=1
        )
        self.node_tree.interface.new_socket(
            name="Noise Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_scale, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Noise Speed", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_speed, min_value=0.01
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

    def set_duration(self, frames: int) -> "SeamlessLoop":
        """
        Set loop duration in frames.

        Args:
            frames: Number of frames for complete loop
        """
        self._duration = frames
        return self

    def use_4d_noise(
        self,
        scale: float = 2.0,
        speed: float = 0.5
    ) -> "SeamlessLoop":
        """
        Enable 4D noise for seamless looping.

        KB Reference: Section 2 - 4D Noise for Perfect Loops

        Args:
            scale: Noise texture scale
            speed: Animation speed multiplier
        """
        self._noise_scale = scale
        self._noise_speed = speed
        return self

    def set_position_offset(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0
    ) -> "SeamlessLoop":
        """Set position offset based on noise."""
        self._position_offset = (x, y, z)
        return self

    def set_rotation_offset(self, max_rotation: float = 0.0) -> "SeamlessLoop":
        """Set rotation offset based on noise."""
        self._rotation_offset = max_rotation
        return self

    def set_scale_variation(self, variation: float = 0.0) -> "SeamlessLoop":
        """Set scale variation based on noise."""
        self._scale_variation = variation
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for seamless animation loop.

        KB Reference: Section 2 - The 4D Noise Formula

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

        # === SCENE TIME ===
        # KB Reference: Section 2 - Frame-based animation
        scene_time = nk.n(
            "GeometryNodeInputSceneTime",
            "Scene Time",
            x=x, y=200
        )
        self._created_nodes['scene_time'] = scene_time

        x += 200

        # === CALCULATE W (4TH DIMENSION) ===
        # KB Reference: Section 2 - W = Frame/Duration × 2π
        # This creates the seamless loop!

        # Divide frame by duration
        frame_div = nk.n("ShaderNodeMath", "Frame/Duration", x=x, y=200)
        frame_div.operation = 'DIVIDE'
        nk.link(scene_time.outputs["Frame"], frame_div.inputs[0])
        nk.link(group_in.outputs["Duration"], frame_div.inputs[1])
        self._created_nodes['frame_div'] = frame_div

        # Multiply by 2π (6.28318...)
        tau = 6.28318530718
        w_calc = nk.n("ShaderNodeMath", "× 2π", x=x + 200, y=200)
        w_calc.operation = 'MULTIPLY'
        w_calc.inputs[1].default_value = tau
        nk.link(frame_div.outputs[0], w_calc.inputs[0])
        self._created_nodes['w_calc'] = w_calc

        # Multiply by speed
        w_speed = nk.n("ShaderNodeMath", "W × Speed", x=x + 400, y=200)
        w_speed.operation = 'MULTIPLY'
        nk.link(w_calc.outputs[0], w_speed.inputs[0])
        nk.link(group_in.outputs["Noise Speed"], w_speed.inputs[1])
        self._created_nodes['w_speed'] = w_speed

        x += 650

        # === 4D NOISE TEXTURE ===
        # KB Reference: Section 2 - 4D Noise is the key
        noise = nk.n(
            "ShaderNodeTexNoise",
            "4D Noise",
            x=x, y=100
        )
        noise.inputs["Scale"].default_value = self._noise_scale
        noise.noise_dimensions = '4D'
        nk.link(group_in.outputs["Noise Scale"], noise.inputs["Scale"])
        nk.link(group_in.outputs["Seed"], noise.inputs["Seed"])
        nk.link(w_speed.outputs[0], noise.inputs["W"])
        self._created_nodes['noise'] = noise

        x += 300

        # === POSITION OFFSET ===
        # KB Reference: Section 2 - Position animation
        if self._position_offset != (0.0, 0.0, 0.0):
            # Multiply noise by offset amounts
            offset_x = nk.n("ShaderNodeMath", "Offset X", x=x, y=200)
            offset_x.operation = 'MULTIPLY'
            offset_x.inputs[1].default_value = self._position_offset[0]
            nk.link(noise.outputs["Fac"], offset_x.inputs[0])

            offset_y = nk.n("ShaderNodeMath", "Offset Y", x=x, y=100)
            offset_y.operation = 'MULTIPLY'
            offset_y.inputs[1].default_value = self._position_offset[1]
            nk.link(noise.outputs["Fac"], offset_y.inputs[0])

            offset_z = nk.n("ShaderNodeMath", "Offset Z", x=x, y=0)
            offset_z.operation = 'MULTIPLY'
            offset_z.inputs[1].default_value = self._position_offset[2]
            nk.link(noise.outputs["Fac"], offset_z.inputs[0])

            self._created_nodes['offset_x'] = offset_x
            self._created_nodes['offset_y'] = offset_y
            self._created_nodes['offset_z'] = offset_z

            # Combine offset
            combine_offset = nk.n("ShaderNodeCombineXYZ", "Offset", x=x + 200, y=100)
            nk.link(offset_x.outputs[0], combine_offset.inputs["X"])
            nk.link(offset_y.outputs[0], combine_offset.inputs["Y"])
            nk.link(offset_z.outputs[0], combine_offset.inputs["Z"])
            self._created_nodes['combine_offset'] = combine_offset

            x += 400

        # === SET POSITION ===
        set_pos = nk.n(
            "GeometryNodeSetPosition",
            "Animate Position",
            x=x, y=0
        )
        nk.link(group_in.outputs["Geometry"], set_pos.inputs["Geometry"])

        if self._position_offset != (0.0, 0.0, 0.0):
            nk.link(combine_offset.outputs["Vector"], set_pos.inputs["Offset"])

        self._created_nodes['set_pos'] = set_pos

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=0)
        nk.link(set_pos.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class LoopUtilities:
    """
    Utilities for calculating loop parameters.

    Cross-references:
    - KB Section 2: Loop Math
    """

    @staticmethod
    def calculate_w_value(frame: int, duration: int) -> float:
        """
        Calculate the W value for 4D noise at a given frame.

        KB Reference: Section 2 - W = Frame/Duration × 2π

        Args:
            frame: Current frame number
            duration: Total loop duration in frames

        Returns:
            W value for 4D noise input
        """
        return (frame / duration) * 2 * math.pi

    @staticmethod
    def get_loop_formula() -> dict:
        """Get the seamless loop formula."""
        return {
            "formula": "W = Frame / Duration × 2π",
            "explanation": [
                "At frame 0: W = 0",
                "At frame Duration: W = 2π (equivalent to 0)",
                "Result: Seamless transition from end to start"
            ],
            "key_insight": "4D noise with W coordinate creates temporal dimension",
            "why_4d": "3D noise would require manual blending; 4D handles it automatically"
        }

    @staticmethod
    def get_common_durations() -> dict:
        """Get common loop durations and their use cases."""
        return {
            "short": {"frames": 60, "use": "Quick loops, GIFs"},
            "medium": {"frames": 120, "use": "Social media, presentations"},
            "standard": {"frames": 250, "use": "Default Blender, general use"},
            "long": {"frames": 500, "use": "Subtle motion, backgrounds"}
        }


class LoopPresets:
    """
    Preset configurations for common loop styles.

    Cross-references:
    - KB Section 2: Geometric Minimalism
    """

    @staticmethod
    def subtle_float() -> dict:
        """Configuration for subtle floating motion."""
        return {
            "noise_scale": 1.5,
            "noise_speed": 0.3,
            "position_offset": (0.0, 0.0, 0.2),
            "rotation_offset": 0.0,
            "scale_variation": 0.0,
            "description": "Gentle up/down floating"
        }

    @staticmethod
    def organic_movement() -> dict:
        """Configuration for organic, breathing-like motion."""
        return {
            "noise_scale": 2.0,
            "noise_speed": 0.5,
            "position_offset": (0.1, 0.1, 0.1),
            "rotation_offset": 0.1,
            "scale_variation": 0.05,
            "description": "Natural, organic motion"
        }

    @staticmethod
    def energetic() -> dict:
        """Configuration for energetic, dynamic motion."""
        return {
            "noise_scale": 3.0,
            "noise_speed": 1.0,
            "position_offset": (0.3, 0.3, 0.3),
            "rotation_offset": 0.3,
            "scale_variation": 0.1,
            "description": "Fast, dynamic movement"
        }

    @staticmethod
    def geometric_pulse() -> dict:
        """Configuration for geometric pulsing."""
        return {
            "noise_scale": 1.0,
            "noise_speed": 0.8,
            "position_offset": (0.0, 0.0, 0.0),
            "rotation_offset": 0.0,
            "scale_variation": 0.15,
            "description": "Scale-based pulsing"
        }


class EmissionLoop:
    """
    Emission-based looping animations.

    Cross-references:
    - KB Section 2: Emission-only rendering
    """

    @staticmethod
    def create_emission_material(
        name: str = "LoopEmission",
        color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        strength: float = 1.0
    ) -> bpy.types.Material:
        """
        Create emission material for loop animation.

        KB Reference: Section 2 - Emission-only workflow

        Args:
            name: Material name
            color: RGBA emission color
            strength: Emission strength

        Returns:
            Configured emission material
        """
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Output
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (400, 0)

        # Emission
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (200, 0)
        emission.inputs["Color"].default_value = color
        emission.inputs["Strength"].default_value = strength

        # Link
        links.new(emission.outputs["Emission"], output.inputs["Surface"])

        return mat


# Convenience functions
def create_seamless_loop(
    obj: bpy.types.Object,
    duration: int = 250,
    noise_scale: float = 2.0,
    noise_speed: float = 0.5
) -> SeamlessLoop:
    """
    Quick setup for seamless animation loop.

    Args:
        obj: Object to animate
        duration: Loop duration in frames
        noise_scale: Noise texture scale
        noise_speed: Animation speed

    Returns:
        Configured SeamlessLoop with built node tree
    """
    loop = SeamlessLoop.from_object(obj)
    loop.set_duration(duration)
    loop.use_4d_noise(scale=noise_scale, speed=noise_speed)
    loop.build()
    return loop


def get_loop_workflow() -> list:
    """Get the seamless loop creation workflow."""
    return [
        "1. Add Noise Texture node",
        "2. Set dimensions to 4D",
        "3. Connect Scene Time → Frame",
        "4. Divide Frame by Duration",
        "5. Multiply by 2π (6.28318)",
        "6. Connect to Noise W input",
        "7. Use noise output for position/rotation/scale",
        "8. Render frames 0 to Duration-1"
    ]


def get_quick_reference() -> dict:
    """Get quick reference for loop creation."""
    return {
        "formula": "W = Frame / Duration × 2π",
        "noise_dimensions": "4D",
        "key_outputs": ["Position offset", "Rotation", "Scale"],
        "render_range": "Frame 0 to Duration-1"
    }


class LoopHUD:
    """
    Heads-Up Display for loop timing and visualization.

    Cross-references:
    - KB Section 2: Loop timing visualization
    """

    @staticmethod
    def display_timeline(duration: int, current_frame: int = 0) -> str:
        """
        Display loop timeline with current position.

        KB Reference: Section 2 - Timeline visualization

        Args:
            duration: Total loop duration in frames
            current_frame: Current frame position

        Returns:
            Formatted timeline display
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'LOOP TIMELINE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        # Calculate progress
        progress = current_frame / duration if duration > 0 else 0
        progress = min(1.0, max(0.0, progress))

        # Timeline bar
        bar_width = 40
        filled = int(progress * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        lines.append(f"│ Duration: {duration} frames")
        lines.append(f"│ Frame: {current_frame} / {duration}")
        lines.append(f"│ Progress: {progress * 100:.1f}%")
        lines.append(f"│ [{bar}] {progress * 360:.0f}°")
        lines.append("│")

        # W value display
        w_value = (current_frame / duration) * 2 * math.pi if duration > 0 else 0
        lines.append(f"│ W Value: {w_value:.4f} rad ({w_value * 180 / math.pi:.1f}°)")

        # Loop status
        if current_frame == 0:
            lines.append("│ Status: START (W = 0)")
        elif current_frame >= duration:
            lines.append("│ Status: END (W = 2π = 0) ✓ SEAMLESS")
        else:
            lines.append("│ Status: IN PROGRESS")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_formula_breakdown() -> str:
        """
        Display the seamless loop formula breakdown.

        KB Reference: Section 2 - Formula explanation

        Returns:
            Formatted formula breakdown
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'SEAMLESS LOOP FORMULA':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        lines.append("║")
        lines.append("║   W = Frame / Duration × 2π")
        lines.append("║")
        lines.append("╠" + "─" * 48 + "╣")

        breakdown = [
            ("Frame", "Current animation frame (0 to Duration)"),
            ("Duration", "Total loop length in frames"),
            ("2π", "6.28318... (full rotation in radians)"),
            ("W", "4th dimension input for noise texture"),
        ]

        for var, desc in breakdown:
            lines.append(f"║   {var:<10} = {desc:<34}│")

        lines.append("╠" + "─" * 48 + "╣")

        lines.append("║ WHY IT WORKS:")
        lines.append("║   • At Frame 0:     W = 0/Duration × 2π = 0")
        lines.append("║   • At Frame Duration: W = D/D × 2π = 2π")
        lines.append("║   • 2π radians = 0 radians (same position!)")
        lines.append("║   • Result: Perfect seamless loop")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_duration_guide() -> str:
        """
        Display duration selection guide.

        KB Reference: Section 2 - Duration selection

        Returns:
            Formatted duration guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'DURATION SELECTION GUIDE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        durations = [
            (60, "Short", "Quick loops, GIFs, social media"),
            (120, "Medium", "Presentations, web embeds"),
            (250, "Standard", "Default Blender, general use"),
            (500, "Long", "Subtle motion, ambient displays"),
            (750, "Very Long", "Slow, meditative animations"),
        ]

        for frames, name, use in durations:
            fps = 30  # Assumed
            seconds = frames / fps
            lines.append(f"│ {frames:>4} frames ({seconds:>4.1f}s) - {name:<10}: {use:<18}│")

        lines.append("├" + "─" * 48 + "┤")
        lines.append("│ Tips:")
        lines.append("│   • Match frame rate: 30fps × seconds = frames")
        lines.append("│   • Longer = more subtle motion")
        lines.append("│   • Shorter = more energetic feel")
        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """
        Display node flow diagram.

        KB Reference: Section 2 - Node setup

        Returns:
            Formatted node flow diagram
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'LOOP NODE FLOW':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        lines.append("║")
        lines.append("║   [Scene Time] ──→ [Frame]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Math: ÷ Duration]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Math: × 2π] ──→ W Value")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Math: × Speed]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Noise 4D] ←── [Scale, Seed]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Position/Rotation/Scale]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Set Position] → Output")
        lines.append("║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """
        Display loop creation checklist.

        KB Reference: Section 2 - Checklist

        Returns:
            Formatted checklist
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'SEAMLESS LOOP CHECKLIST':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        checklist = [
            ("Setup", [
                "☐ Create geometry node tree",
                "☐ Add Scene Time node",
                "☐ Add Noise Texture (set to 4D)",
            ]),
            ("Math", [
                "☐ Frame ÷ Duration",
                "☐ Result × 2π (6.28318)",
                "☐ Result × Speed",
                "☐ Connect to Noise W input",
            ]),
            ("Animation", [
                "☐ Add position offset (optional)",
                "☐ Add rotation (optional)",
                "☐ Add scale variation (optional)",
            ]),
            ("Render", [
                "☐ Set start frame to 0",
                "☐ Set end frame to Duration-1",
                "☐ Use LINEAR interpolation",
                "☐ Test loop in preview",
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
    def display_w_table(duration: int) -> str:
        """
        Display W values for key frames.

        KB Reference: Section 2 - W value table

        Args:
            duration: Loop duration in frames

        Returns:
            Formatted W value table
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'W VALUES TABLE (Duration=' + str(duration) + ')':^48}│")
        lines.append("├" + "─" * 48 + "┤")
        lines.append("│ Frame    │ W (rad)   │ W (deg)   │ Note     │")

        key_frames = [
            0,
            duration // 4,
            duration // 2,
            3 * duration // 4,
            duration
        ]

        for frame in key_frames:
            w_rad = (frame / duration) * 2 * math.pi if duration > 0 else 0
            w_deg = w_rad * 180 / math.pi

            if frame == 0:
                note = "START"
            elif frame == duration:
                note = "END (same as 0)"
            else:
                note = ""

            lines.append(f"│ {frame:>8} │ {w_rad:>9.4f} │ {w_deg:>9.1f}° │ {note:<8} │")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)


def print_loop_timeline(duration: int, current_frame: int = 0) -> None:
    """Print loop timeline to console."""
    print(LoopHUD.display_timeline(duration, current_frame))


def print_loop_formula() -> None:
    """Print loop formula breakdown to console."""
    print(LoopHUD.display_formula_breakdown())
