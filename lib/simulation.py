"""
Simulation Nodes Module - Codified from Tutorial 38

Implements simulation node workflows for footprints, tracks, and deformation.
Based on Bad Normals tutorial: https://youtu.be/HMpKmzTGwiE

Usage:
    from lib.simulation import FootprintSimulation

    # Create footprint simulation
    sim = FootprintSimulation.create("MyFootprints")
    sim.set_depth(0.1)
    sim.set_contact_threshold(0.5)
    tree = sim.build()  # Creates the actual simulation node tree
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


class FootprintSimulation:
    """
    Simulation nodes for creating footprints and tracks.

    Creates a complete simulation node tree with:
    - Simulation Input/Output zone
    - Object info for foot position
    - Vector distance for proximity detection
    - Set Position for ground deformation
    - Accumulated displacement over frames

    Cross-references:
    - KB Section 38: Simulation Nodes Beginner Tutorial (Bad Normals)
    - lib/nodekit.py: For node tree building
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self.ground: Optional[bpy.types.Object] = None
        self.animated_object: Optional[bpy.types.Object] = None
        self._depth = 0.1
        self._contact_threshold = 0.5
        self._push_radius = 1.0
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "FootprintSimulation") -> "FootprintSimulation":
        """
        Create a new geometry node tree for footprint simulation.

        Args:
            name: Name for the node group

        Returns:
            Configured FootprintSimulation instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        ground_obj: bpy.types.Object,
        name: str = "FootprintSimulation"
    ) -> "FootprintSimulation":
        """
        Create and attach to ground object via geometry nodes modifier.

        Args:
            ground_obj: Ground plane to deform
            name: Name for the node group

        Returns:
            Configured FootprintSimulation instance
        """
        # Add geometry nodes modifier
        mod = ground_obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance.ground = ground_obj
        instance._setup_interface()
        return instance

    def _setup_interface(self) -> None:
        """Set up the node group interface (inputs/outputs)."""
        # Create interface inputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        # Foot object reference
        self.node_tree.interface.new_socket(
            name="Foot Object", in_out='INPUT', socket_type='NodeSocketObject'
        )
        self.node_tree.interface.new_socket(
            name="Depth", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._depth, min_value=0.0, max_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Contact Threshold", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._contact_threshold, min_value=0.01
        )
        self.node_tree.interface.new_socket(
            name="Push Radius", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._push_radius, min_value=0.1
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_ground(self, ground: bpy.types.Object) -> "FootprintSimulation":
        """Set the ground plane to deform."""
        self.ground = ground
        return self

    def set_animated_object(self, obj: bpy.types.Object) -> "FootprintSimulation":
        """Set the animated foot/boot object."""
        self.animated_object = obj
        return self

    def prepare_ground(self, subdivisions: int = 6) -> "FootprintSimulation":
        """
        Add subdivision to ground for deformation.

        KB Reference: Section 38 - Ground needs resolution for deformation
        """
        if not self.ground:
            raise RuntimeError("Set ground first")

        # Add subdivision surface modifier
        mod = self.ground.modifiers.new(name="Subdivision", type='SUBSURF')
        mod.levels = subdivisions
        mod.render_levels = subdivisions

        return self

    def set_depth(self, depth: float) -> "FootprintSimulation":
        """Set how deep footprints press into ground."""
        self._depth = depth
        return self

    def set_contact_threshold(self, threshold: float) -> "FootprintSimulation":
        """Set distance at which contact is detected."""
        self._contact_threshold = threshold
        return self

    def set_push_radius(self, radius: float) -> "FootprintSimulation":
        """Set radius of push effect around footprint."""
        self._push_radius = radius
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete simulation node tree for footprints.

        KB Reference: Section 38 - Simulation Zone Structure

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

        # === SIMULATION ZONE ===
        # KB Reference: Section 38 - Basic simulation loop
        # Note: Simulation zones require Blender 4.0+

        # Simulation Input
        sim_in = nk.n(
            "GeometryNodeSimulationInput",
            "Sim Input",
            x=x, y=100
        )
        self._created_nodes['simulation_input'] = sim_in

        # Connect input geometry to sim input
        nk.link(group_in.outputs["Geometry"], sim_in.inputs["Geometry"])

        x += 300

        # === OBJECT INFO - Get foot position ===
        # KB Reference: Section 38 - Foot position drives simulation
        object_info = nk.n(
            "GeometryNodeObjectInfo",
            "Foot Info",
            x=x, y=-100
        )
        object_info.transform_space = 'RELATIVE'
        nk.link(group_in.outputs["Foot Object"], object_info.inputs["Object"])
        self._created_nodes['object_info'] = object_info

        x += 250

        # === GET GROUND POSITION ===
        position = nk.n(
            "GeometryNodeInputPosition",
            "Position",
            x=x, y=100
        )
        self._created_nodes['position'] = position

        x += 150

        # === VECTOR DISTANCE - Proximity Detection ===
        # KB Reference: Section 38 - Know when foot hits ground
        distance = nk.n(
            "ShaderNodeVectorMath",
            "Distance",
            x=x, y=0
        )
        distance.operation = 'DISTANCE'
        nk.link(position.outputs["Position"], distance.inputs[0])
        nk.link(object_info.outputs["Location"], distance.inputs[1])
        self._created_nodes['distance'] = distance

        x += 200

        # === COMPARE - Contact threshold ===
        compare = nk.n(
            "FunctionNodeCompare",
            "Is Contact",
            x=x, y=0
        )
        compare.operation = 'LESS_THAN'
        compare.data_type = 'FLOAT'
        nk.link(distance.outputs[0], compare.inputs[0])
        nk.link(group_in.outputs["Contact Threshold"], compare.inputs[1])
        self._created_nodes['compare'] = compare

        x += 200

        # === CALCULATE DISPLACEMENT ===
        # KB Reference: Section 38 - Push ground down where foot hits

        # Create displacement vector (0, 0, -depth) when in contact
        # Multiply depth by contact boolean
        depth_mult = nk.n(
            "ShaderNodeMath",
            "Depth × Contact",
            x=x, y=50
        )
        depth_mult.operation = 'MULTIPLY'
        nk.link(group_in.outputs["Depth"], depth_mult.inputs[0])
        # Convert bool to float
        bool_to_float = nk.n(
            "ShaderNodeMath",
            "Bool to Float",
            x=x - 100, y=-50
        )
        bool_to_float.operation = 'MULTIPLY'
        bool_to_float.inputs[1].default_value = 1.0
        nk.link(compare.outputs[0], bool_to_float.inputs[0])
        nk.link(bool_to_float.outputs[0], depth_mult.inputs[1])
        self._created_nodes['depth_mult'] = depth_mult

        x += 200

        # Combine into offset vector (0, 0, -depth_when_contact)
        offset = nk.n(
            "ShaderNodeCombineXYZ",
            "Displacement",
            x=x, y=100
        )
        offset.inputs["X"].default_value = 0.0
        offset.inputs["Y"].default_value = 0.0
        nk.link(depth_mult.outputs[0], offset.inputs["Z"])
        # Negate for pushing down
        negate = nk.n("ShaderNodeMath", "Negate", x=x - 100, y=150)
        negate.operation = 'MULTIPLY'
        negate.inputs[1].default_value = -1.0
        nk.link(depth_mult.outputs[0], negate.inputs[0])
        nk.link(negate.outputs[0], offset.inputs["Z"])
        self._created_nodes['offset'] = offset

        x += 200

        # === SET POSITION ===
        # KB Reference: Section 38 - Accumulates over frames
        set_pos = nk.n(
            "GeometryNodeSetPosition",
            "Displace Ground",
            x=x, y=100
        )
        nk.link(sim_in.outputs["Geometry"], set_pos.inputs["Geometry"])
        nk.link(offset.outputs["Vector"], set_pos.inputs["Offset"])
        self._created_nodes['set_position'] = set_pos

        x += 300

        # === SIMULATION OUTPUT ===
        sim_out = nk.n(
            "GeometryNodeSimulationOutput",
            "Sim Output",
            x=x, y=100
        )
        nk.link(set_pos.outputs["Geometry"], sim_out.inputs["Geometry"])
        self._created_nodes['simulation_output'] = sim_out

        # Pair the simulation input/output
        sim_in.paired_output = sim_out

        x += 300

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(sim_out.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class ProximityDetector:
    """
    Detect proximity between objects for simulation triggers.

    Cross-references:
    - KB Section 38: Proximity detection
    """

    @staticmethod
    def add_proximity_nodes(
        nk: NodeKit,
        object_socket,
        position_socket,
        threshold: float = 0.5,
        x: float = 0,
        y: float = 0
    ) -> Tuple[bpy.types.Node, bpy.types.Node]:
        """
        Add proximity detection nodes.

        Args:
            nk: NodeKit instance
            object_socket: Socket with object position
            position_socket: Socket with geometry positions
            threshold: Distance threshold
            x, y: Position for nodes

        Returns:
            Tuple of (distance_node, compare_node)
        """
        # Vector Distance
        distance = nk.n("ShaderNodeVectorMath", "Distance", x=x, y=y)
        distance.operation = 'DISTANCE'
        nk.link(position_socket, distance.inputs[0])
        nk.link(object_socket, distance.inputs[1])

        # Compare
        compare = nk.n("FunctionNodeCompare", "Is Contact", x=x + 200, y=y)
        compare.operation = 'LESS_THAN'
        compare.inputs[1].default_value = threshold
        nk.link(distance.outputs[0], compare.inputs[0])

        return distance, compare

    @staticmethod
    def get_detection_config() -> dict:
        """Get configuration for proximity detection node setup."""
        return {
            "node_setup": [
                "Foot Position → Vector Distance",
                "Compare to ground points",
                "Threshold for contact",
                "Boolean output: Is touching?"
            ],
            "triggers": "Deformation when distance < threshold"
        }


class DisplacementApplicator:
    """
    Apply and accumulate displacement in simulation.

    Cross-references:
    - KB Section 38: Displacement application
    """

    @staticmethod
    def add_displacement_nodes(
        nk: NodeKit,
        geometry_socket,
        contact_socket,
        depth: float = 0.1,
        x: float = 0,
        y: float = 0
    ) -> bpy.types.Node:
        """
        Add displacement application nodes.

        Args:
            nk: NodeKit instance
            geometry_socket: Input geometry
            contact_socket: Contact boolean
            depth: Displacement depth
            x, y: Position for nodes

        Returns:
            Set Position node
        """
        # Bool to float
        bool_float = nk.n("ShaderNodeMath", "Bool→Float", x=x, y=y)
        bool_float.operation = 'MULTIPLY'
        bool_float.inputs[1].default_value = 1.0
        nk.link(contact_socket, bool_float.inputs[0])

        # Multiply by depth
        depth_mult = nk.n("ShaderNodeMath", "× Depth", x=x + 150, y=y)
        depth_mult.operation = 'MULTIPLY'
        depth_mult.inputs[1].default_value = depth
        nk.link(bool_float.outputs[0], depth_mult.inputs[0])

        # Negate
        negate = nk.n("ShaderNodeMath", "Negate", x=x + 300, y=y)
        negate.operation = 'MULTIPLY'
        negate.inputs[1].default_value = -1.0
        nk.link(depth_mult.outputs[0], negate.inputs[0])

        # Combine XYZ
        combine = nk.n("ShaderNodeCombineXYZ", "Offset", x=x + 450, y=y + 50)
        combine.inputs["X"].default_value = 0.0
        combine.inputs["Y"].default_value = 0.0
        nk.link(negate.outputs[0], combine.inputs["Z"])

        # Set Position
        set_pos = nk.n("GeometryNodeSetPosition", "Displace", x=x + 600, y=y + 100)
        nk.link(geometry_socket, set_pos.inputs["Geometry"])
        nk.link(combine.outputs["Vector"], set_pos.inputs["Offset"])

        return set_pos


class AnimationSource:
    """
    Sources for foot/character animation.

    Cross-references:
    - KB Section 38: Character/Boot Animation
    """

    @staticmethod
    def get_animation_sources() -> dict:
        """Get available animation source options."""
        return {
            "manual": {
                "description": "Animate manually in Blender",
                "control": "Full control over timing",
                "difficulty": "Medium"
            },
            "mixamo": {
                "description": "Use Mixamo character animations",
                "control": "Pre-made walks/runs",
                "difficulty": "Easy",
                "url": "https://www.mixamo.com"
            },
            "mocap": {
                "description": "Motion capture (Rokoko/video)",
                "control": "Realistic motion",
                "difficulty": "Advanced"
            }
        }


# Convenience functions
def create_footprint_simulation(
    ground: bpy.types.Object,
    depth: float = 0.1,
    subdivisions: int = 6
) -> FootprintSimulation:
    """
    Quick setup for footprint simulation.

    Args:
        ground: Ground plane to deform
        depth: Print depth
        subdivisions: Ground subdivision level

    Returns:
        Configured FootprintSimulation with built node tree
    """
    ground.modifiers.new(name="Subdivision", type='SUBSURF')
    ground.modifiers["Subdivision"].levels = subdivisions

    sim = FootprintSimulation.from_object(ground)
    sim.set_depth(depth)
    sim.build()
    return sim


def get_simulation_applications() -> list:
    """Get list of applications beyond footprints."""
    return [
        "Mud splatter",
        "Snow tracks",
        "Tire marks",
        "Paint brush strokes",
        "Sand drawing",
        "Water ripples"
    ]


class SimulationHUD:
    """
    Heads-Up Display for simulation visualization.

    Cross-references:
    - KB Section 38: Simulation nodes visualization
    """

    @staticmethod
    def display_settings(
        depth: float = 0.1,
        contact_threshold: float = 0.5,
        push_radius: float = 1.0,
        subdivisions: int = 6
    ) -> str:
        """
        Display simulation settings.

        Args:
            depth: Footprint depth
            contact_threshold: Contact detection threshold
            push_radius: Push effect radius
            subdivisions: Ground subdivisions

        Returns:
            Formatted settings display
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'FOOTPRINT SIMULATION SETTINGS':^48}│")
        lines.append("├" + "─" * 48 + "┤")
        lines.append(f"│ Depth:            {depth:>10.3f} units       │")
        lines.append(f"│ Contact Threshold:{contact_threshold:>10.3f} units       │")
        lines.append(f"│ Push Radius:      {push_radius:>10.3f} units       │")
        lines.append(f"│ Subdivisions:     {subdivisions:>10} levels      │")
        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_simulation_flow() -> str:
        """
        Display simulation node flow diagram.

        Returns:
            Formatted node flow diagram
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'SIMULATION NODE FLOW':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        lines.append("║")
        lines.append("║   [Simulation Input] ←── [Geometry]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Object Info] ←── [Foot Object]")
        lines.append("║          │")
        lines.append("║          ↓")
        lines.append("║   [Position] ──→ [Vector Distance]")
        lines.append("║                         │")
        lines.append("║          [Contact] ────→│")
        lines.append("║                         ↓")
        lines.append("║                    [Compare < Threshold]")
        lines.append("║                         │")
        lines.append("║                         ↓")
        lines.append("║                    [Depth × Contact]")
        lines.append("║                         │")
        lines.append("║                         ↓")
        lines.append("║                    [Negate] ──→ [Offset Z]")
        lines.append("║                                        │")
        lines.append("║                                        ↓")
        lines.append("║   [Sim Geo] ──────────────────→ [Set Position]")
        lines.append("║                                        │")
        lines.append("║                                        ↓")
        lines.append("║   [Simulation Output] ←────────────────┘")
        lines.append("║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_depth_guide() -> str:
        """
        Display depth selection guide.

        Returns:
            Formatted depth guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'DEPTH SELECTION GUIDE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        depths = [
            (0.02, "Light", "Footprints on hard ground"),
            (0.05, "Medium", "Normal soil, grass"),
            (0.10, "Deep", "Soft mud, wet sand"),
            (0.20, "Very Deep", "Deep snow, swamp"),
            (0.50, "Extreme", "Exaggerated cartoon effect"),
        ]

        for depth, name, use in depths:
            lines.append(f"│ {depth:>5.2f} - {name:<10}: {use:<26}│")

        lines.append("├" + "─" * 48 + "┤")
        lines.append("│ Tips:")
        lines.append("│   • Match depth to surface material")
        lines.append("│   • Subdivisions control detail level")
        lines.append("│   • Higher subdivisions = smoother deformation")
        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """
        Display simulation setup checklist.

        Returns:
            Formatted checklist
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'FOOTPRINT SIMULATION CHECKLIST':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        checklist = [
            ("Ground Setup", [
                "☐ Create ground plane",
                "☐ Add subdivision modifier",
                "☐ Set subdivision levels (6+)",
            ]),
            ("Simulation Zone", [
                "☐ Add Simulation Input node",
                "☐ Add Simulation Output node",
                "☐ Connect input to output pair",
            ]),
            ("Detection", [
                "☐ Add Object Info for foot",
                "☐ Get position of geometry",
                "☐ Add Vector Distance node",
                "☐ Add Compare (Less Than)",
            ]),
            ("Deformation", [
                "☐ Multiply depth by contact",
                "☐ Negate for downward push",
                "☐ Combine to offset vector",
                "☐ Add Set Position node",
            ]),
            ("Animation", [
                "☐ Animate foot object",
                "☐ Set frame range",
                "☐ Play to see footprints form",
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
    def display_material_effects() -> str:
        """
        Display material effects for footprints.

        Returns:
            Formatted material effects guide
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'FOOTPRINT MATERIAL EFFECTS':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        materials = [
            ("Mud", "Wet, glossy, displaces outward"),
            ("Sand", "Dry, granular, collapses inward"),
            ("Snow", "White, compresses, edges crisp"),
            ("Dirt", "Brown, dusty, subtle ridges"),
            ("Concrete", "Wet footprints, fade over time"),
        ]

        for material, effect in materials:
            lines.append(f"│ {material:<12}: {effect:<32}│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)


def print_simulation_settings(**kwargs) -> None:
    """Print simulation settings to console."""
    print(SimulationHUD.display_settings(**kwargs))
