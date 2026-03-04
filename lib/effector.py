"""
Effector-Based Offset Animation Module - Codified from Tutorial 12

Implements motion graphics effect where objects offset/animate based on
proximity to a moving "effector" object.

Based on Default Cube/CGMatter tutorial:
https://www.youtube.com/watch?v=qKUuTaynxq8

Usage:
    from lib.effector import EffectorOffset

    # Create effector-based animation
    effector = EffectorOffset.create("MyEffect")
    effector.set_effector(empty_object)
    effector.set_falloff(min_dist=0, max_dist=2.0)
    effector.set_offset(z=1.0)  # Z-axis offset
    effector.add_secondary_noise(scale=1.5, speed=0.35)
    tree = effector.build()
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


class EffectorOffset:
    """
    Effector-driven offset animation for motion graphics.

    Creates a node tree that:
    - Calculates distance from effector object
    - Creates inverted mask (1 near effector, 0 far)
    - Applies translation based on mask
    - Optionally adds noise for secondary motion

    Cross-references:
    - KB Section 12: Effector-Based Offset Animation (Default Cube/CGMatter)
    - KB Section 24: Morphing effect (similar distance pattern)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._effector_obj: Optional[bpy.types.Object] = None
        self._falloff_min = 0.0
        self._falloff_max = 1.0
        self._offset = (0.0, 0.0, 1.0)
        self._noise_settings = {
            'enabled': False,
            'scale': 1.5,
            'speed': 0.35,
            'strength': 1.0
        }
        self._instance_count = 20
        self._use_curve_line = True
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "EffectorOffset") -> "EffectorOffset":
        """
        Create a new geometry node tree for effector animation.

        Args:
            name: Name for the node group

        Returns:
            Configured EffectorOffset instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "EffectorOffset"
    ) -> "EffectorOffset":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach effect to
            name: Name for the node group

        Returns:
            Configured EffectorOffset instance
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
            name="Instance Count", in_out='INPUT', socket_type='NodeSocketInt',
            default_value=self._instance_count, min_value=1, max_value=1000
        )
        self.node_tree.interface.new_socket(
            name="Effector", in_out='INPUT', socket_type='NodeSocketObject'
        )
        self.node_tree.interface.new_socket(
            name="Falloff Min", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._falloff_min, min_value=0.0
        )
        self.node_tree.interface.new_socket(
            name="Falloff Max", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._falloff_max, min_value=0.1
        )
        self.node_tree.interface.new_socket(
            name="Offset X", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._offset[0]
        )
        self.node_tree.interface.new_socket(
            name="Offset Y", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._offset[1]
        )
        self.node_tree.interface.new_socket(
            name="Offset Z", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._offset[2]
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
            name="Noise Strength", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._noise_settings['strength'], min_value=0.0
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_effector(self, obj: bpy.types.Object) -> "EffectorOffset":
        """Set the effector object that drives the animation."""
        self._effector_obj = obj
        return self

    def set_falloff(self, min_dist: float = 0.0, max_dist: float = 1.0) -> "EffectorOffset":
        """
        Set the distance falloff range.

        Args:
            min_dist: Distance where effect is full (1.0)
            max_dist: Distance where effect is zero (0.0)
        """
        self._falloff_min = min_dist
        self._falloff_max = max_dist
        return self

    def set_offset(self, x: float = 0.0, y: float = 0.0, z: float = 1.0) -> "EffectorOffset":
        """Set the translation offset for affected instances."""
        self._offset = (x, y, z)
        return self

    def add_secondary_noise(
        self,
        scale: float = 1.5,
        speed: float = 0.35,
        strength: float = 1.0
    ) -> "EffectorOffset":
        """Add organic secondary motion with noise."""
        self._noise_settings = {
            'enabled': True,
            'scale': scale,
            'speed': speed,
            'strength': strength
        }
        return self

    def set_instance_count(self, count: int) -> "EffectorOffset":
        """Set number of instances along the path."""
        self._instance_count = count
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for effector offset animation.

        KB Reference: Section 12 - Effector-Based Offset Animation

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

        # === CURVE LINE FOR INSTANCE BASE ===
        # KB Reference: Section 12 - Curve Line, Resample
        curve_line = nk.n(
            "GeometryNodeCurveLine",
            "Curve Line",
            x=x, y=200
        )
        curve_line.inputs["Start"].default_value = (0, 0, 0)
        curve_line.inputs["End"].default_value = (10, 0, 0)
        self._created_nodes['curve_line'] = curve_line

        x += 200

        # === RESAMPLE CURVE ===
        resample = nk.n(
            "GeometryNodeResampleCurve",
            "Resample",
            x=x, y=200
        )
        resample.mode = 'COUNT'
        nk.link(group_in.outputs["Instance Count"], resample.inputs["Count"])
        nk.link(curve_line.outputs["Curve"], resample.inputs["Curve"])
        self._created_nodes['resample'] = resample

        x += 200

        # === OBJECT INFO FOR EFFECTOR ===
        # KB Reference: Section 12 - Object Info (Effector)
        obj_info = nk.n(
            "GeometryNodeObjectInfo",
            "Effector Info",
            x=x, y=-100
        )
        obj_info.transform_space = 'RELATIVE'
        nk.link(group_in.outputs["Effector"], obj_info.inputs["Object"])
        self._created_nodes['object_info'] = obj_info

        x += 200

        # === VECTOR DISTANCE ===
        # KB Reference: Section 12 - Distance-Based Mask Calculation
        distance = nk.n(
            "ShaderNodeVectorMath",
            "Distance",
            x=x, y=100
        )
        distance.operation = 'DISTANCE'
        # Connect effector location and instance position
        nk.link(obj_info.outputs["Location"], distance.inputs[0])
        # Position will come from resampled curve points
        self._created_nodes['distance'] = distance

        x += 200

        # === MAP RANGE (INVERTED) ===
        # KB Reference: Section 12 - Inverted mask (1 near, 0 far)
        map_range = nk.n(
            "ShaderNodeMapRange",
            "Falloff",
            x=x, y=100
        )
        # Inverted: From 0-1 becomes To 1-0
        nk.link(group_in.outputs["Falloff Min"], map_range.inputs["From Min"])
        nk.link(group_in.outputs["Falloff Max"], map_range.inputs["From Max"])
        map_range.inputs["To Min"].default_value = 1.0  # Full effect at effector
        map_range.inputs["To Max"].default_value = 0.0  # No effect far away
        nk.link(distance.outputs[0], map_range.inputs["Value"])
        self._created_nodes['map_range'] = map_range

        x += 200

        # === FLOAT CURVE FOR FALLOFF SHAPE ===
        float_curve = nk.n(
            "ShaderNodeFloatCurve",
            "Falloff Shape",
            x=x, y=100
        )
        nk.link(map_range.outputs[0], float_curve.inputs["Value"])
        self._created_nodes['float_curve'] = float_curve

        x += 200

        # === STORE NAMED ATTRIBUTE (MASK) ===
        # KB Reference: Section 12 - Store mask for shader access
        store_mask = nk.n(
            "GeometryNodeStoreNamedAttribute",
            "Store Mask",
            x=x, y=200
        )
        store_mask.inputs["Name"].default_value = "effector_mask"
        store_mask.domain = 'INSTANCE'
        nk.link(resample.outputs["Curve"], store_mask.inputs["Geometry"])
        nk.link(float_curve.outputs[0], store_mask.inputs["Value"])
        self._created_nodes['store_mask'] = store_mask

        x += 200

        # === BUILD OFFSET VECTOR ===
        # Combine offset values with mask
        offset_x = nk.n("ShaderNodeMath", "Offset X", x=x, y=200)
        offset_x.operation = 'MULTIPLY'
        nk.link(float_curve.outputs[0], offset_x.inputs[0])
        nk.link(group_in.outputs["Offset X"], offset_x.inputs[1])

        offset_y = nk.n("ShaderNodeMath", "Offset Y", x=x, y=100)
        offset_y.operation = 'MULTIPLY'
        nk.link(float_curve.outputs[0], offset_y.inputs[0])
        nk.link(group_in.outputs["Offset Y"], offset_y.inputs[1])

        offset_z = nk.n("ShaderNodeMath", "Offset Z", x=x, y=0)
        offset_z.operation = 'MULTIPLY'
        nk.link(float_curve.outputs[0], offset_z.inputs[0])
        nk.link(group_in.outputs["Offset Z"], offset_z.inputs[1])

        self._created_nodes['offset_math'] = (offset_x, offset_y, offset_z)

        x += 200

        # === COMBINE OFFSET VECTOR ===
        combine_offset = nk.n(
            "ShaderNodeCombineXYZ",
            "Total Offset",
            x=x, y=100
        )
        nk.link(offset_x.outputs[0], combine_offset.inputs["X"])
        nk.link(offset_y.outputs[0], combine_offset.inputs["Y"])
        nk.link(offset_z.outputs[0], combine_offset.inputs["Z"])
        self._created_nodes['combine_offset'] = combine_offset

        x += 200

        # === ADD NOISE IF ENABLED ===
        if self._noise_settings['enabled']:
            # Scene time for animation
            scene_time = nk.n(
                "GeometryNodeInputSceneTime",
                "Scene Time",
                x=x, y=-150
            )
            self._created_nodes['scene_time'] = scene_time

            # Multiply time by speed
            time_mult = nk.n("ShaderNodeMath", "Time × Speed", x=x + 150, y=-150)
            time_mult.operation = 'MULTIPLY'
            nk.link(group_in.outputs["Noise Speed"], time_mult.inputs[0])
            nk.link(scene_time.outputs["Seconds"], time_mult.inputs[1])

            x_noise = x + 300

            # 4D Noise texture
            noise = nk.n(
                "ShaderNodeTexNoise",
                "Secondary Noise",
                x=x_noise, y=-100
            )
            noise.inputs["Dimensions"].default_value = '4D'
            nk.link(group_in.outputs["Noise Scale"], noise.inputs["Scale"])
            nk.link(time_mult.outputs[0], noise.inputs["W"])
            self._created_nodes['noise'] = noise

            # Scale noise by strength
            noise_strength = nk.n("ShaderNodeMath", "Noise Strength", x=x_noise + 200, y=-100)
            noise_strength.operation = 'MULTIPLY'
            nk.link(noise.outputs["Fac"], noise_strength.inputs[0])
            nk.link(group_in.outputs["Noise Strength"], noise_strength.inputs[1])

            # Add noise to offset (vector add)
            add_noise = nk.n("ShaderNodeVectorMath", "Add Noise", x=x_noise + 400, y=100)
            add_noise.operation = 'ADD'
            nk.link(combine_offset.outputs["Vector"], add_noise.inputs[0])
            # Convert noise scalar to vector
            noise_to_vec = nk.n("ShaderNodeCombineXYZ", "Noise Vec", x=x_noise + 300, y=-100)
            nk.link(noise_strength.outputs[0], noise_to_vec.inputs["X"])
            nk.link(noise_strength.outputs[0], noise_to_vec.inputs["Y"])
            nk.link(noise_strength.outputs[0], noise_to_vec.inputs["Z"])
            nk.link(noise_to_vec.outputs["Vector"], add_noise.inputs[1])

            final_offset = add_noise
            x = x_noise + 600
        else:
            final_offset = combine_offset

        self._created_nodes['final_offset'] = final_offset

        # === TRANSLATE INSTANCES ===
        # KB Reference: Section 12 - Local Space OFF for global offset
        translate = nk.n(
            "GeometryNodeTranslateInstances",
            "Translate",
            x=x, y=200
        )
        translate.inputs["Local Space"].default_value = False
        nk.link(store_mask.outputs["Geometry"], translate.inputs["Instances"])
        nk.link(final_offset.outputs["Vector"] if hasattr(final_offset, 'outputs') and "Vector" in final_offset.outputs else final_offset.outputs[0], translate.inputs["Translation"])
        self._created_nodes['translate'] = translate

        x += 250

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=200)
        nk.link(translate.outputs["Instances"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class DistanceMask:
    """
    Utility class for creating distance-based masks.

    Cross-references:
    - KB Section 12: Distance-based mask calculation
    - KB Section 24: Morphing (similar pattern)
    """

    @staticmethod
    def create_inverted_mask_config(
        near_distance: float = 0.0,
        far_distance: float = 1.0
    ) -> dict:
        """
        Create configuration for inverted distance mask.

        Args:
            near_distance: Distance where mask = 1.0
            far_distance: Distance where mask = 0.0

        Returns:
            Configuration dict for mask setup
        """
        return {
            "from_min": near_distance,
            "from_max": far_distance,
            "to_min": 1.0,  # Full effect near
            "to_max": 0.0,  # No effect far
            "clamp": True
        }

    @staticmethod
    def calculate_falloff_width(density: float = 1.0) -> float:
        """
        Calculate falloff width based on instance density.

        Args:
            density: Instance density (higher = more instances)

        Returns:
            Suggested falloff max distance
        """
        # Empirical formula: more instances = narrower effect
        return max(0.1, 2.0 / (density ** 0.5))


class DynamicLighting:
    """
    Helper for setting up lights that follow the effector.

    Cross-references:
    - KB Section 12: Dynamic lighting setup
    - KB Section 25: Lighting techniques
    """

    @staticmethod
    def create_tracking_light(
        name: str = "EffectorLight",
        power: float = 400.0,
        size: float = 1.0
    ) -> bpy.types.Object:
        """
        Create an area light for tracking with effector.

        Args:
            name: Light object name
            power: Light power in watts
            size: Light size for softness

        Returns:
            The created light object
        """
        # Create light data
        light_data = bpy.data.lights.new(name=f"{name}_data", type='AREA')
        light_data.energy = power
        light_data.size = size

        # Create object with light data
        light_obj = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light_obj)

        return light_obj

    @staticmethod
    def parent_to_effector(light: bpy.types.Object, effector: bpy.types.Object) -> None:
        """Parent a light to follow the effector object."""
        light.parent = effector


# Convenience functions
def create_effector_animation(
    obj: bpy.types.Object,
    effector: bpy.types.Object,
    offset_z: float = 1.0,
    falloff: float = 1.0
) -> EffectorOffset:
    """
    Quick setup for effector-based animation.

    Args:
        obj: Object to add effect to
        effector: Effector control object
        offset_z: Z-axis offset amount
        falloff: Effect falloff distance

    Returns:
        Configured EffectorOffset with built node tree
    """
    effect = EffectorOffset.from_object(obj)
    effect.set_effector(effector)
    effect.set_offset(z=offset_z)
    effect.set_falloff(0, falloff)
    effect.build()
    return effect


def create_wave_effect(
    obj: bpy.types.Object,
    effector: bpy.types.Object,
    wave_height: float = 0.5
) -> EffectorOffset:
    """
    Create a wave-like effect passing through instances.

    Args:
        obj: Object to add effect to
        effector: Moving effector object
        wave_height: Height of the wave

    Returns:
        Configured EffectorOffset
    """
    effect = EffectorOffset.from_object(obj)
    effect.set_effector(effector)
    effect.set_offset(z=wave_height)
    effect.set_falloff(0, 2.0)
    effect.add_secondary_noise(scale=1.5, speed=0.35, strength=0.3)
    effect.build()
    return effect


class EffectorHUD:
    """
    Heads-Up Display for effector-based animation visualization.

    Cross-references:
    - KB Section 12: Effector-Based Offset Animation
    """

    @staticmethod
    def display_settings(
        instance_count: int = 20,
        falloff_min: float = 0.0,
        falloff_max: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        offset_z: float = 1.0,
        noise_scale: float = 1.5,
        noise_speed: float = 0.35,
        noise_strength: float = 1.0
    ) -> str:
        """Display current effector settings."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║     EFFECTOR OFFSET SETTINGS         ║",
            "╠══════════════════════════════════════╣",
            f"║ Instances:     {instance_count:>20} ║",
            f"║ Falloff Min:   {falloff_min:>20.2f} ║",
            f"║ Falloff Max:   {falloff_max:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ OFFSET                               ║",
            f"║   X:           {offset_x:>20.2f} ║",
            f"║   Y:           {offset_y:>20.2f} ║",
            f"║   Z:           {offset_z:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ NOISE                                ║",
            f"║   Scale:       {noise_scale:>20.2f} ║",
            f"║   Speed:       {noise_speed:>20.2f} ║",
            f"║   Strength:    {noise_strength:>20.2f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_falloff_guide() -> str:
        """Display falloff configuration guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║        FALLOFF CONFIGURATION         ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  INVERTED MASK (1 near, 0 far):      ║",
            "║  ┌─────────────────────────────┐     ║",
            "║  │  Distance → Map Range       │     ║",
            "║  │  From: [min, max]           │     ║",
            "║  │  To:   [1.0, 0.0]           │     ║",
            "║  └─────────────────────────────┘     ║",
            "║                                      ║",
            "║  FALLOFF SHAPE (Float Curve):        ║",
            "║  ┌─────────────────────────────┐     ║",
            "║  │  Smooth: Linear curve       │     ║",
            "║  │  Sharp:  Exponential curve  │     ║",
            "║  │  Soft:   Ease in/out        │     ║",
            "║  └─────────────────────────────┘     ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for effector animation."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║          EFFECTOR NODE FLOW          ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       ├──→ [Curve Line]              ║",
            "║       │         │                    ║",
            "║       │    [Resample Curve]          ║",
            "║       │         │                    ║",
            "║       └──→ [Object Info] ← Effector  ║",
            "║                 │                    ║",
            "║          [Vector Distance]           ║",
            "║                 │                    ║",
            "║            [Map Range]               ║",
            "║                 │                    ║",
            "║          [Float Curve]               ║",
            "║                 │                    ║",
            "║        [Store Named Attribute]       ║",
            "║                 │                    ║",
            "║     [Math × Offset] (X, Y, Z)        ║",
            "║                 │                    ║",
            "║         [Combine XYZ]                ║",
            "║                 │                    ║",
            "║    [Optional: + Noise]               ║",
            "║                 │                    ║",
            "║       [Translate Instances]          ║",
            "║                 │                    ║",
            "║          [Group Output]              ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for effector setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║      EFFECTOR PRE-FLIGHT CHECKLIST   ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Effector object created           ║",
            "║    (Empty or simple mesh)            ║",
            "║                                      ║",
            "║  □ Effector assigned to input        ║",
            "║                                      ║",
            "║  □ Falloff range configured          ║",
            "║    (min < max for proper effect)     ║",
            "║                                      ║",
            "║  □ Offset values set                 ║",
            "║    (usually Z for lift effect)       ║",
            "║                                      ║",
            "║  □ Local Space = OFF                 ║",
            "║    (for global offset direction)     ║",
            "║                                      ║",
            "║  □ Animate effector movement         ║",
            "║    (keyframe position)               ║",
            "║                                      ║",
            "║  □ Optional: Add secondary noise     ║",
            "║    (for organic motion)              ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_distance_formula() -> str:
        """Display the distance-based mask formula."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       DISTANCE MASK FORMULA          ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  distance = |effector_pos - point_pos|",
            "║                                      ║",
            "║  mask = map_range(distance,          ║",
            "║          from_min=0, from_max=falloff║",
            "║          to_min=1.0, to_max=0.0)     ║",
            "║                                      ║",
            "║  Result:                             ║",
            "║    • Near effector: mask = 1.0       ║",
            "║    • Far from effector: mask = 0.0   ║",
            "║    • Between: smooth interpolation   ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_effector_settings(**kwargs) -> None:
    """Print effector settings to console."""
    print(EffectorHUD.display_settings(**kwargs))
