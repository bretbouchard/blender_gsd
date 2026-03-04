"""
Particle Animation Module - Codified from Tutorial 30

Implements seamless looping particle animations using geometry nodes.
Based on Ducky 3D tutorial: https://www.youtube.com/watch?v=5G2lV-pVPD0

Usage:
    from lib.particles import SeamlessParticles

    # Create seamless particle loop
    particles = SeamlessParticles.create("MyParticles")
    particles.set_density(1000)
    particles.add_noise_animation(speed=0.5, scale=2.0)
    particles.set_loop_duration(250)
    tree = particles.build()  # Creates the actual node tree
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


class SeamlessParticles:
    """
    Seamless looping particle animation using geometry nodes.

    Creates a complete node tree with:
    - Distribute Points on Faces
    - 4D Noise texture for animation
    - Set Position for movement
    - Instance on Points for particle geometry

    Cross-references:
    - KB Section 30: Seamless Particle Animation (Ducky 3D)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._density = 1000
        self._seed = 42
        self._noise_settings = {
            'speed': 0.5,
            'scale': 2.0,
            'detail': 2.0,
            'strength': 0.5
        }
        self._loop_duration = 250
        self._surface_factor = 0.5
        self._particle_scale = 0.1
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "SeamlessParticles") -> "SeamlessParticles":
        """
        Create a new geometry node tree for seamless particles.

        Args:
            name: Name for the node group

        Returns:
            Configured SeamlessParticles instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "SeamlessParticles"
    ) -> "SeamlessParticles":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach particles to
            name: Name for the node group

        Returns:
            Configured SeamlessParticles instance
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
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Density", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._density, min_value=1, max_value=100000
        )
        self.node_tree.interface.new_socket(
            name="Seed", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._seed
        )
        self.node_tree.interface.new_socket(
            name="Noise Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['scale'], min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Noise Speed", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['speed'], min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Movement Strength", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['strength'], min_value=0.0, max_value=2.0
        )
        self.node_tree.interface.new_socket(
            name="Surface Lock", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._surface_factor, min_value=0.0, max_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Particle Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._particle_scale, min_value=0.01
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_density(self, density: int) -> "SeamlessParticles":
        """Set particle density (count per unit area)."""
        self._density = density
        return self

    def set_seed(self, seed: int) -> "SeamlessParticles":
        """Set random seed for variation."""
        self._seed = seed
        return self

    def add_noise_animation(
        self,
        speed: float = 0.5,
        scale: float = 2.0,
        detail: float = 2.0,
        strength: float = 0.5
    ) -> "SeamlessParticles":
        """Configure 4D noise animation for seamless motion."""
        self._noise_settings = {
            'speed': speed,
            'scale': scale,
            'detail': detail,
            'strength': strength
        }
        return self

    def set_loop_duration(self, frames: int) -> "SeamlessParticles":
        """Set loop duration for seamless animation (frames)."""
        self._loop_duration = frames
        return self

    def set_surface_lock(self, factor: float) -> "SeamlessParticles":
        """Set how much particles stay on surface (0=locked, 1=free)."""
        self._surface_factor = factor
        return self

    def set_particle_scale(self, scale: float) -> "SeamlessParticles":
        """Set particle instance scale."""
        self._particle_scale = scale
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for seamless particle animation.

        KB Reference: Section 30 - Seamless Particle Animation

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

        # === DISTRIBUTE POINTS ON FACES ===
        # KB Reference: Section 30 - Base particle distribution
        distribute = nk.n(
            "GeometryNodeDistributePointsOnFaces",
            "Distribute Points",
            x=x, y=100
        )
        self._created_nodes['distribute'] = distribute

        # Connect input geometry to distribute
        nk.link(group_in.outputs["Geometry"], distribute.inputs["Mesh"])

        # Connect density and seed from inputs
        nk.link(group_in.outputs["Density"], distribute.inputs["Density"])
        nk.link(group_in.outputs["Seed"], distribute.inputs["Seed"])

        x += 250

        # === SCENE TIME FOR ANIMATION ===
        scene_time = nk.n(
            "GeometryNodeInputSceneTime",
            "Scene Time",
            x=x, y=-100
        )
        self._created_nodes['scene_time'] = scene_time

        # === MULTIPLY TIME BY SPEED ===
        # KB Reference: Section 30 - W: Scene Time → Multiply (speed)
        speed_math = nk.n(
            "ShaderNodeMath",
            "Time × Speed",
            x=x + 200, y=-100
        )
        speed_math.operation = 'MULTIPLY'
        nk.link(group_in.outputs["Noise Speed"], speed_math.inputs[0])
        nk.link(scene_time.outputs["Seconds"], speed_math.inputs[1])
        self._created_nodes['speed_math'] = speed_math

        x += 450

        # === 4D NOISE TEXTURE ===
        # KB Reference: Section 30 - 4D noise for seamless loops
        noise = nk.n(
            "ShaderNodeTexNoise",
            "4D Noise",
            x=x, y=0
        )
        noise.inputs["Dimensions"].default_value = '4D'
        noise.inputs["Detail"].default_value = self._noise_settings['detail']

        # Connect scale from input
        nk.link(group_in.outputs["Noise Scale"], noise.inputs["Scale"])
        # Connect animated W value
        nk.link(speed_math.outputs[0], noise.inputs["W"])

        self._created_nodes['noise'] = noise

        x += 250

        # === SEPARATE NOISE TO XYZ ===
        separate_xyz = nk.n(
            "ShaderNodeSeparateXYZ",
            "Separate Noise",
            x=x, y=0
        )
        nk.link(noise.outputs["Color"], separate_xyz.inputs["Vector"])
        self._created_nodes['separate_xyz'] = separate_xyz

        x += 200

        # === MULTIPLY BY STRENGTH ===
        # KB Reference: Section 30 - Strength controls movement amount
        strength_mult_x = nk.n("ShaderNodeMath", "Strength X", x=x, y=100)
        strength_mult_x.operation = 'MULTIPLY'
        nk.link(separate_xyz.outputs["X"], strength_mult_x.inputs[0])
        nk.link(group_in.outputs["Movement Strength"], strength_mult_x.inputs[1])

        strength_mult_y = nk.n("ShaderNodeMath", "Strength Y", x=x, y=0)
        strength_mult_y.operation = 'MULTIPLY'
        nk.link(separate_xyz.outputs["Y"], strength_mult_y.inputs[0])
        nk.link(group_in.outputs["Movement Strength"], strength_mult_y.inputs[1])

        strength_mult_z = nk.n("ShaderNodeMath", "Strength Z", x=x, y=-100)
        strength_mult_z.operation = 'MULTIPLY'
        nk.link(separate_xyz.outputs["Z"], strength_mult_z.inputs[0])
        nk.link(group_in.outputs["Movement Strength"], strength_mult_z.inputs[1])

        self._created_nodes['strength_mult'] = (strength_mult_x, strength_mult_y, strength_mult_z)

        x += 200

        # === COMBINE XYZ FOR OFFSET ===
        combine_xyz = nk.n(
            "ShaderNodeCombineXYZ",
            "Offset",
            x=x, y=0
        )
        nk.link(strength_mult_x.outputs[0], combine_xyz.inputs["X"])
        nk.link(strength_mult_y.outputs[0], combine_xyz.inputs["Y"])
        nk.link(strength_mult_z.outputs[0], combine_xyz.inputs["Z"])
        self._created_nodes['combine_xyz'] = combine_xyz

        x += 200

        # === SET POSITION ===
        # KB Reference: Section 30 - Surface Locking with Set Position
        set_position = nk.n(
            "GeometryNodeSetPosition",
            "Set Position",
            x=x, y=100
        )
        nk.link(distribute.outputs["Points"], set_position.inputs["Geometry"])
        nk.link(combine_xyz.outputs["Vector"], set_position.inputs["Offset"])

        self._created_nodes['set_position'] = set_position

        x += 250

        # === INSTANCE ON POINTS ===
        # Create a simple icosphere as particle geometry inline
        # KB Reference: Section 30 - Instance on Points
        ico = nk.n(
            "GeometryNodeMeshIcoSphere",
            "Particle Shape",
            x=x, y=-150
        )
        ico.inputs["Radius"].default_value = 0.5
        self._created_nodes['particle_shape'] = ico

        # Scale the particle
        scale_node = nk.n(
            "GeometryNodeTransform",
            "Scale Particle",
            x=x + 200, y=-150
        )
        nk.link(ico.outputs["Mesh"], scale_node.inputs["Geometry"])
        # Create a vector for uniform scale
        scale_vec = nk.n("ShaderNodeCombineXYZ", "Scale Vec", x=x + 100, y=-250)
        nk.link(group_in.outputs["Particle Scale"], scale_vec.inputs["X"])
        nk.link(group_in.outputs["Particle Scale"], scale_vec.inputs["Y"])
        nk.link(group_in.outputs["Particle Scale"], scale_vec.inputs["Z"])
        nk.link(scale_vec.outputs["Vector"], scale_node.inputs["Scale"])
        self._created_nodes['scale_particle'] = scale_node

        # Instance on points
        instance = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance Particles",
            x=x + 450, y=100
        )
        nk.link(set_position.outputs["Geometry"], instance.inputs["Points"])
        nk.link(scale_node.outputs["Geometry"], instance.inputs["Instance"])

        self._created_nodes['instance'] = instance

        x += 650

        # === REALIZE INSTANCES (optional but good for render) ===
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


class NoiseAnimator:
    """
    4D noise animation utilities for seamless loops.

    Cross-references:
    - KB Section 30: Noise texture animation
    """

    @staticmethod
    def calculate_loop_settings(total_frames: int) -> dict:
        """Calculate settings for seamless noise loop."""
        return {
            "frames": total_frames,
            "w_offset_per_frame": (2 * math.pi) / total_frames,
            "speed_multiplier": 1.0 / total_frames,
            "noise_period": total_frames / (2 * math.pi)
        }

    @staticmethod
    def get_noise_params_for_loop(
        loop_frames: int,
        motion_scale: float = 2.0,
        detail: int = 2
    ) -> dict:
        """Get complete noise parameters for seamless loop."""
        settings = NoiseAnimator.calculate_loop_settings(loop_frames)
        return {
            "dimensions": "4D",
            "scale": motion_scale,
            "detail": detail,
            "w_speed": settings["w_offset_per_frame"],
            "frame_0_w": 0.0,
            "frame_n_w": 2 * math.pi
        }


class RepeatZoneBuilder:
    """
    Helper for building repeat zones for fluid particle motion.

    Cross-references:
    - KB Section 30: Repeat zone for continuous flow
    - KB Section 38: Simulation zones (similar concept)
    """

    @staticmethod
    def add_repeat_zone(
        nk: NodeKit,
        input_geo,
        iterations: int = 5,
        offset_per_iteration: Tuple[float, float, float] = (0.1, 0.0, 0.0)
    ) -> Tuple[bpy.types.Node, bpy.types.Node]:
        """
        Add a repeat zone for cumulative particle motion.

        Args:
            nk: NodeKit instance
            input_geo: Input geometry socket
            iterations: Number of repeat iterations
            offset_per_iteration: (X, Y, Z) offset each iteration

        Returns:
            Tuple of (repeat_input_node, repeat_output_node)
        """
        # Note: Repeat zones require Blender 4.0+
        # This creates the structure conceptually

        # Create repeat zone input/output pair
        repeat_in = nk.n("GeometryNodeRepeatInput", "Repeat In", x=0, y=0)
        repeat_out = nk.n("GeometryNodeRepeatOutput", "Repeat Out", x=400, y=0)

        # Set iterations
        repeat_in.inputs["Iterations"].default_value = iterations

        # Connect input geometry
        nk.link(input_geo, repeat_in.inputs["Geometry"])

        return repeat_in, repeat_out

    @staticmethod
    def create_cumulative_offset(
        iterations: int,
        base_offset: tuple = (0.1, 0.0, 0.0)
    ) -> dict:
        """
        Create cumulative offset for repeat zone.

        Args:
            iterations: Number of repeat iterations
            base_offset: Offset per iteration (x, y, z)

        Returns:
            Configuration for repeat zone
        """
        return {
            "iterations": iterations,
            "offset_per_iteration": base_offset,
            "total_offset": tuple(i * iterations for i in base_offset)
        }


# Convenience functions
def create_seamless_particle_loop(
    obj: bpy.types.Object,
    density: int = 1000,
    loop_frames: int = 250,
    noise_scale: float = 2.0
) -> SeamlessParticles:
    """
    Quick setup for seamless particle animation on an object.

    Args:
        obj: Object to add particles to
        density: Number of particles
        loop_frames: Animation loop length
        noise_scale: Noise scale (lower = smoother)

    Returns:
        Configured SeamlessParticles with built node tree
    """
    particles = SeamlessParticles.from_object(obj)
    particles.set_density(density)
    particles.add_noise_animation(speed=0.5, scale=noise_scale)
    particles.set_loop_duration(loop_frames)
    particles.build()
    return particles


def calculate_perfect_loop(total_frames: int) -> dict:
    """Calculate all values needed for perfect seamless loop."""
    return {
        "w_start": 0.0,
        "w_end": 2 * math.pi,
        "w_per_frame": (2 * math.pi) / total_frames,
        "keyframe_interpolation": "LINEAR",
        "verify_frames": [0, total_frames // 2, total_frames]
    }


class ParticleHUD:
    """
    Heads-Up Display for particle system visualization.

    Cross-references:
    - KB Section 30: Particle animation visualization
    """

    @staticmethod
    def display_settings(
        density: int = 1000,
        seed: int = 42,
        noise_scale: float = 2.0,
        noise_speed: float = 0.5,
        strength: float = 0.5,
        loop_duration: int = 250
    ) -> str:
        """
        Display particle system settings.

        Args:
            density: Particle count per unit area
            seed: Random seed
            noise_scale: Noise texture scale
            noise_speed: Animation speed
            strength: Movement strength
            loop_duration: Loop duration in frames

        Returns:
            Formatted settings display
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'PARTICLE SYSTEM SETTINGS':^48}│")
        lines.append("├" + "─" * 48 + "┤")
        lines.append(f"│ Density:        {density:>10} particles     │")
        lines.append(f"│ Seed:           {seed:>10}              │")
        lines.append(f"│ Noise Scale:    {noise_scale:>10.2f}              │")
        lines.append(f"│ Noise Speed:    {noise_speed:>10.2f}              │")
        lines.append(f"│ Strength:       {strength:>10.2f}              │")
        lines.append(f"│ Loop Duration:  {loop_duration:>10} frames      │")
        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_density_guide() -> str:
        """
        Display density selection guide.

        Returns:
            Formatted density guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'DENSITY SELECTION GUIDE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        densities = [
            (100, "Sparse", "Distant stars, dust motes"),
            (500, "Light", "Fireflies, gentle snow"),
            (1000, "Standard", "Default particle field"),
            (2500, "Dense", "Heavy rain, confetti"),
            (5000, "Very Dense", "Fog, heavy snowstorm"),
            (10000, "Extreme", "Galaxy, dense fog"),
        ]

        for count, name, use in densities:
            lines.append(f"│ {count:>5} - {name:<10}: {use:<26}│")

        lines.append("├" + "─" * 48 + "┤")
        lines.append("│ Tips:")
        lines.append("│   • Higher density = slower render")
        lines.append("│   • Use instances for performance")
        lines.append("│   • Surface Lock prevents escaping")
        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_noise_guide() -> str:
        """
        Display noise parameter guide.

        Returns:
            Formatted noise guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'NOISE PARAMETER GUIDE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        lines.append("│ Scale (Noise texture scale):")
        lines.append("│   0.5 - 1.0  : Large, smooth motion")
        lines.append("│   2.0 - 3.0  : Standard, balanced")
        lines.append("│   5.0+       : Small, chaotic motion")
        lines.append("│")
        lines.append("│ Speed (Animation speed):")
        lines.append("│   0.1 - 0.3  : Slow, gentle drift")
        lines.append("│   0.5        : Standard motion")
        lines.append("│   1.0+       : Fast, energetic")
        lines.append("│")
        lines.append("│ Strength (Movement amount):")
        lines.append("│   0.1 - 0.3  : Subtle vibration")
        lines.append("│   0.5        : Normal movement")
        lines.append("│   1.0+       : Wild motion")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """
        Display particle node flow diagram.

        Returns:
            Formatted node flow diagram
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'PARTICLE NODE FLOW':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        lines.append("║")
        lines.append("║   [Group Input] ──→ [Distribute Points on Faces]")
        lines.append("║          │                    │")
        lines.append("║          │                    ↓")
        lines.append("║   [Scene Time] ──→ [× Speed] ──→ [4D Noise W]")
        lines.append("║                               │")
        lines.append("║   [Noise Scale] ──────────────┼──→ [4D Noise]")
        lines.append("║                               │         │")
        lines.append("║                               │         ↓")
        lines.append("║   [Strength] ─────────────────┼──→ [Separate XYZ]")
        lines.append("║                               │         │")
        lines.append("║                               │         ↓")
        lines.append("║                               └──→ [Combine XYZ]")
        lines.append("║                                         │")
        lines.append("║                                         ↓")
        lines.append("║   [Particle Shape] ────────────→ [Instance on Points]")
        lines.append("║                                         │")
        lines.append("║                                         ↓")
        lines.append("║                                    [Realize] → Output")
        lines.append("║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """
        Display particle setup checklist.

        Returns:
            Formatted checklist
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'PARTICLE SETUP CHECKLIST':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        checklist = [
            ("Setup", [
                "☐ Create geometry node tree",
                "☐ Add Distribute Points on Faces",
                "☐ Set density and seed",
            ]),
            ("Animation", [
                "☐ Add Scene Time node",
                "☐ Multiply time by speed",
                "☐ Add 4D Noise texture",
                "☐ Connect W to animated time",
            ]),
            ("Motion", [
                "☐ Separate noise to XYZ",
                "☐ Multiply by strength",
                "☐ Combine to offset vector",
                "☐ Add Set Position node",
            ]),
            ("Instances", [
                "☐ Create particle geometry",
                "☐ Add Instance on Points",
                "☐ Set particle scale",
                "☐ Optional: Realize Instances",
            ]),
        ]

        for category, items in checklist:
            lines.append(f"║ {category}:")
            for item in items:
                lines.append(f"║   {item}")
            lines.append("║" + " " * 50 + "║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)


def print_particle_settings(**kwargs) -> None:
    """Print particle settings to console."""
    print(ParticleHUD.display_settings(**kwargs))
