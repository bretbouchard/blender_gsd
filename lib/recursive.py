"""
Recursive Instancing Module - Codified from Tutorial 11

Implements Doctor Strange-style recursive instancing where objects
spawn smaller copies at specific points (e.g., fingertips), with
smooth blending at intersection points.

Based on CGMatter tutorial: https://www.youtube.com/watch?v=DYMEQuYVUAs

Usage:
    from lib.recursive import RecursiveInstance

    # Create recursive hand rig effect
    recursive = RecursiveInstance.create("RecursiveHands")
    recursive.set_tip_collection(tips_collection)
    recursive.set_instance_collection(hands_collection)
    recursive.set_scale(0.3)  # 30% scale for child hands
    recursive.enable_position_blending(blend_distance=0.025)
    recursive.enable_normal_blending(blend_distance=0.025)
    tree = recursive.build()
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


class RecursiveInstance:
    """
    Recursive instancing with position and normal blending.

    Creates a node tree that:
    - Fetches tip markers from a collection
    - Separates children into individual instances
    - Stores transform for each instance
    - Instances geometry at each tip position
    - Blends positions/normals near parent surface

    Cross-references:
    - KB Section 11: Recursive Hand Rig System (CGMatter)
    - KB Section 12: Effector (similar proximity patterns)
    - lib/nodekit.py: For node tree building patterns
    """

    def __init__(self, node_tree: Optional[bpy.types.NodeTree] = None):
        self.node_tree = node_tree
        self.nk: Optional[NodeKit] = None
        self._tip_collection: Optional[bpy.types.Collection] = None
        self._instance_collection: Optional[bpy.types.Collection] = None
        self._scale = 0.3
        self._position_blend_enabled = False
        self._position_blend_dist = 0.025
        self._normal_blend_enabled = False
        self._normal_blend_dist = 0.025
        self._parent_geometry: Optional[bpy.types.Object] = None
        self._created_nodes: dict = {}

    @classmethod
    def create(cls, name: str = "RecursiveInstance") -> "RecursiveInstance":
        """
        Create a new geometry node tree for recursive instancing.

        Args:
            name: Name for the node group

        Returns:
            Configured RecursiveInstance instance
        """
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        instance = cls(tree)
        instance._setup_interface()
        return instance

    @classmethod
    def from_object(
        cls,
        obj: bpy.types.Object,
        name: str = "RecursiveInstance"
    ) -> "RecursiveInstance":
        """
        Create and attach to an object via geometry nodes modifier.

        Args:
            obj: Blender object to attach effect to
            name: Name for the node group

        Returns:
            Configured RecursiveInstance instance
        """
        mod = obj.modifiers.new(name=name, type='NODES')
        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        mod.node_group = tree

        instance = cls(tree)
        instance._setup_interface()
        instance._parent_geometry = obj
        return instance

    def _setup_interface(self) -> None:
        """Set up the node group interface (inputs/outputs)."""
        # Create interface inputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self.node_tree.interface.new_socket(
            name="Tip Collection", in_out='INPUT', socket_type='NodeSocketCollection'
        )
        self.node_tree.interface.new_socket(
            name="Instance Collection", in_out='INPUT', socket_type='NodeSocketCollection'
        )
        self.node_tree.interface.new_socket(
            name="Scale", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._scale, min_value=0.01, max_value=2.0
        )
        self.node_tree.interface.new_socket(
            name="Position Blend Distance", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._position_blend_dist, min_value=0.001, max_value=1.0
        )
        self.node_tree.interface.new_socket(
            name="Normal Blend Distance", in_out='INPUT', socket_type='NodeSocketFloat',
            default_value=self._normal_blend_dist, min_value=0.001, max_value=1.0
        )

        # Create interface outputs
        self.node_tree.interface.new_socket(
            name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )

        self.nk = NodeKit(self.node_tree)

    def set_tip_collection(self, collection: bpy.types.Collection) -> "RecursiveInstance":
        """
        Set the collection containing tip marker objects.

        Args:
            collection: Collection with empties/objects at tip positions
        """
        self._tip_collection = collection
        return self

    def set_instance_collection(self, collection: bpy.types.Collection) -> "RecursiveInstance":
        """
        Set the collection to instance at each tip.

        Args:
            collection: Collection containing geometry to instance
        """
        self._instance_collection = collection
        return self

    def set_scale(self, scale: float) -> "RecursiveInstance":
        """
        Set uniform scale for child instances.

        Args:
            scale: Scale factor (0.3 = 30% size)
        """
        self._scale = scale
        return self

    def enable_position_blending(self, blend_distance: float = 0.025) -> "RecursiveInstance":
        """
        Enable smooth position blending at intersections.

        Args:
            blend_distance: Distance for blend effect (0.01-0.025 typical)
        """
        self._position_blend_enabled = True
        self._position_blend_dist = blend_distance
        return self

    def enable_normal_blending(self, blend_distance: float = 0.025) -> "RecursiveInstance":
        """
        Enable smooth normal blending for seamless shading.

        Args:
            blend_distance: Distance for normal blend (match position blend)
        """
        self._normal_blend_enabled = True
        self._normal_blend_dist = blend_distance
        return self

    def set_parent_geometry(self, obj: bpy.types.Object) -> "RecursiveInstance":
        """Set parent geometry for proximity-based blending."""
        self._parent_geometry = obj
        return self

    def build(self) -> bpy.types.NodeTree:
        """
        Build the complete node tree for recursive instancing.

        KB Reference: Section 11 - Recursive Hand Rig System

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

        # === COLLECTION INFO FOR TIPS ===
        # KB Reference: Section 11 - Collection Info + Separate Children
        tip_info = nk.n(
            "GeometryNodeCollectionInfo",
            "Tip Collection Info",
            x=x, y=100
        )
        tip_info.inputs["Separate Children"].default_value = True  # CRITICAL!
        tip_info.inputs["Reset Children"].default_value = True
        nk.link(group_in.outputs["Tip Collection"], tip_info.inputs["Collection"])
        self._created_nodes['tip_info'] = tip_info

        x += 250

        # === POINTS FROM INSTANCES ===
        # Convert instances to points for processing
        to_points = nk.n(
            "GeometryNodeInstancesToPoints",
            "To Points",
            x=x, y=100
        )
        nk.link(tip_info.outputs["Instances"], to_points.inputs["Instances"])
        self._created_nodes['to_points'] = to_points

        x += 200

        # === INSTANCE TRANSFORM ===
        # KB Reference: Section 11 - Store transform for later use
        instance_transform = nk.n(
            "GeometryNodeInstanceTransform",
            "Get Transform",
            x=x, y=100
        )
        nk.link(to_points.outputs["Points"], instance_transform.inputs["Geometry"])
        self._created_nodes['instance_transform'] = instance_transform

        x += 200

        # === STORE NAMED ATTRIBUTE (TRANSFORM) ===
        store_transform = nk.n(
            "GeometryNodeStoreNamedAttribute",
            "Store Transform",
            x=x, y=100
        )
        store_transform.inputs["Name"].default_value = "finger_transform"
        store_transform.inputs["Data Type"].default_value = 'ROTATION'
        nk.link(instance_transform.outputs["Geometry"], store_transform.inputs["Geometry"])
        nk.link(instance_transform.outputs["Rotation"], store_transform.inputs["Value"])
        self._created_nodes['store_transform'] = store_transform

        x += 200

        # === OPTIONAL: POSITION BLENDING ===
        if self._position_blend_enabled and self._parent_geometry:
            # KB Reference: Section 11 - Position Blending at Intersections
            # Geometry Proximity for distance to parent
            proximity = nk.n(
                "GeometryNodeProximity",
                "Proximity",
                x=x, y=-100
            )
            proximity.target_element = 'POINTS'
            # Parent object info
            parent_info = nk.n(
                "GeometryNodeObjectInfo",
                "Parent Info",
                x=x, y=-250
            )
            parent_info.transform_space = 'RELATIVE'
            # Note: Would need to connect parent object
            self._created_nodes['proximity'] = proximity
            self._created_nodes['parent_info'] = parent_info

            # Map Range (inverted) for blend factor
            map_range = nk.n(
                "ShaderNodeMapRange",
                "Blend Factor",
                x=x + 200, y=-100
            )
            map_range.inputs["From Min"].default_value = 0.0
            nk.link(group_in.outputs["Position Blend Distance"], map_range.inputs["From Max"])
            map_range.inputs["To Min"].default_value = 1.0  # Close = full blend
            map_range.inputs["To Max"].default_value = 0.0  # Far = no blend
            self._created_nodes['map_range'] = map_range

            # Get snapped position from nearest surface
            sample_pos = nk.n(
                "GeometryNodeSampleNearestSurface",
                "Sample Position",
                x=x + 200, y=-250
            )
            self._created_nodes['sample_pos'] = sample_pos

            # Mix original and snapped positions
            mix_pos = nk.n(
                "ShaderNodeMixVector",
                "Blend Position",
                x=x + 400, y=100
            )
            # A = original position, B = snapped position
            nk.link(map_range.outputs[0], mix_pos.inputs["Factor"])
            self._created_nodes['mix_pos'] = mix_pos

            x += 600
        else:
            mix_pos = None

        self._created_nodes['mix_pos'] = mix_pos

        # === COLLECTION INFO FOR INSTANCES ===
        instance_info = nk.n(
            "GeometryNodeCollectionInfo",
            "Instance Collection",
            x=x, y=200
        )
        instance_info.inputs["Separate Children"].default_value = False
        nk.link(group_in.outputs["Instance Collection"], instance_info.inputs["Collection"])
        self._created_nodes['instance_info'] = instance_info

        x += 250

        # === INSTANCE ON POINTS ===
        # KB Reference: Section 11 - Instance on Points
        instance_on_points = nk.n(
            "GeometryNodeInstanceOnPoints",
            "Instance at Tips",
            x=x, y=100
        )
        nk.link(store_transform.outputs["Geometry"], instance_on_points.inputs["Points"])
        nk.link(instance_info.outputs["Instances"], instance_on_points.inputs["Instance"])
        self._created_nodes['instance_on_points'] = instance_on_points

        x += 200

        # === SCALE INSTANCES ===
        scale_instances = nk.n(
            "GeometryNodeScaleInstances",
            "Scale Children",
            x=x, y=100
        )
        scale_instances.inputs["Local Space"].default_value = True
        nk.link(instance_on_points.outputs["Instances"], scale_instances.inputs["Instances"])

        # Create uniform scale vector
        scale_vec = nk.n("ShaderNodeCombineXYZ", "Scale Vec", x=x - 100, y=-50)
        nk.link(group_in.outputs["Scale"], scale_vec.inputs["X"])
        nk.link(group_in.outputs["Scale"], scale_vec.inputs["Y"])
        nk.link(group_in.outputs["Scale"], scale_vec.inputs["Z"])
        nk.link(scale_vec.outputs["Vector"], scale_instances.inputs["Scale"])
        self._created_nodes['scale_instances'] = scale_instances
        self._created_nodes['scale_vec'] = scale_vec

        x += 250

        # === OPTIONAL: NORMAL BLENDING ===
        if self._normal_blend_enabled and self._parent_geometry:
            # KB Reference: Section 11 - Normal Blending for Seamless Shading
            # Get original normal
            input_normal = nk.n(
                "GeometryNodeInputNormal",
                "Original Normal",
                x=x, y=-100
            )
            self._created_nodes['input_normal'] = input_normal

            # Sample normal from parent surface
            sample_normal = nk.n(
                "GeometryNodeSampleNearestSurface",
                "Sample Normal",
                x=x, y=-250
            )
            self._created_nodes['sample_normal'] = sample_normal

            # Map range for normal blend factor
            normal_map = nk.n(
                "ShaderNodeMapRange",
                "Normal Blend Factor",
                x=x + 200, y=-150
            )
            normal_map.inputs["From Min"].default_value = 0.0
            nk.link(group_in.outputs["Normal Blend Distance"], normal_map.inputs["From Max"])
            normal_map.inputs["To Min"].default_value = 1.0
            normal_map.inputs["To Max"].default_value = 0.0
            self._created_nodes['normal_map'] = normal_map

            # Mix normals
            mix_normal = nk.n(
                "ShaderNodeMixVector",
                "Blend Normal",
                x=x + 400, y=-100
            )
            nk.link(normal_map.outputs[0], mix_normal.inputs["Factor"])
            self._created_nodes['mix_normal'] = mix_normal

            # Set mesh normal
            set_normal = nk.n(
                "GeometryNodeSetMeshNormal",
                "Set Blended Normal",
                x=x + 600, y=100
            )
            set_normal.mode = 'FREE'
            nk.link(scale_instances.outputs["Instances"], set_normal.inputs["Geometry"])
            nk.link(mix_normal.outputs["Vector"], set_normal.inputs["Custom Normal"])
            self._created_nodes['set_normal'] = set_normal

            x += 800
            final_geo = set_normal
        else:
            final_geo = scale_instances

        self._created_nodes['final_geo'] = final_geo

        # === JOIN WITH PARENT (optional) ===
        join = nk.n(
            "GeometryNodeJoinGeometry",
            "Join",
            x=x, y=100
        )
        nk.link(group_in.outputs["Geometry"], join.inputs[0])
        nk.link(final_geo.outputs["Instances"] if hasattr(final_geo, 'outputs') and "Instances" in final_geo.outputs else final_geo.outputs["Geometry"], join.inputs[1])
        self._created_nodes['join'] = join

        x += 200

        # === OUTPUT ===
        group_out = nk.group_output(x=x, y=100)
        nk.link(join.outputs["Geometry"], group_out.inputs["Geometry"])
        self._created_nodes['group_output'] = group_out

        return self.node_tree

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._created_nodes.get(name)


class TransformStorage:
    """
    Utilities for storing and applying transforms.

    Cross-references:
    - KB Section 11: Transform storage pattern
    """

    @staticmethod
    def create_transform_storage_config() -> dict:
        """Get configuration for storing 4x4 transform matrices."""
        return {
            "attribute_name": "transform",
            "data_type": "ROTATION",  # or MATRIX if available
            "domain": "INSTANCE",
            "description": "Full position + rotation storage"
        }

    @staticmethod
    def apply_stored_transform(
        nk: NodeKit,
        instances,
        transform_name: str = "finger_transform"
    ) -> bpy.types.Node:
        """
        Apply a previously stored transform to instances.

        Args:
            nk: NodeKit instance
            instances: Instance geometry socket
            transform_name: Name of stored transform attribute

        Returns:
            Node with transformed instances
        """
        # Named attribute to retrieve transform
        named_attr = nk.n(
            "GeometryNodeNamedAttribute",
            "Get Transform",
            x=0, y=0
        )
        named_attr.inputs["Name"].default_value = transform_name
        named_attr.data_type = 'ROTATION'

        # Set instance transform
        set_transform = nk.n(
            "GeometryNodeSetInstanceTransform",
            "Apply Transform",
            x=200, y=0
        )
        nk.link(instances, set_transform.inputs["Geometry"])
        nk.link(named_attr.outputs[0], set_transform.inputs["Transform"])

        return set_transform


class IntersectionBlending:
    """
    Utilities for smooth blending at geometry intersections.

    Cross-references:
    - KB Section 11: Position and normal blending
    """

    @staticmethod
    def get_blend_settings() -> dict:
        """Get recommended blend settings for natural intersections."""
        return {
            "position_blend_distance": 0.025,  # Very small for precise intersection
            "normal_blend_distance": 0.025,    # Match position for consistency
            "invert_factor": True,             # Closer = more influence
            "description": "Use very small proximity distances (0.01-0.025)"
        }

    @staticmethod
    def calculate_blend_factor(distance: float, max_distance: float = 0.025) -> float:
        """
        Calculate inverted blend factor for proximity blending.

        Args:
            distance: Current distance from surface
            max_distance: Distance where blend becomes zero

        Returns:
            Blend factor (1.0 at surface, 0.0 at max_distance)
        """
        if distance >= max_distance:
            return 0.0
        return 1.0 - (distance / max_distance)


# Convenience functions
def create_recursive_hands(
    obj: bpy.types.Object,
    tips_collection: bpy.types.Collection,
    hands_collection: bpy.types.Collection,
    scale: float = 0.3
) -> RecursiveInstance:
    """
    Quick setup for recursive hand rig effect.

    Args:
        obj: Parent object (main hand)
        tips_collection: Collection with fingertip empties
        hands_collection: Collection with hand geometry to instance
        scale: Scale for child hands

    Returns:
        Configured RecursiveInstance with built node tree
    """
    recursive = RecursiveInstance.from_object(obj)
    recursive.set_tip_collection(tips_collection)
    recursive.set_instance_collection(hands_collection)
    recursive.set_scale(scale)
    recursive.enable_position_blending(0.025)
    recursive.enable_normal_blending(0.025)
    recursive.build()
    return recursive


def create_simple_recursive(
    obj: bpy.types.Object,
    tips_collection: bpy.types.Collection,
    instance_collection: bpy.types.Collection,
    scale: float = 0.3
) -> RecursiveInstance:
    """
    Simple recursive instancing without blending.

    Args:
        obj: Parent object
        tips_collection: Collection with tip markers
        instance_collection: Collection to instance
        scale: Instance scale

    Returns:
        Configured RecursiveInstance (no blending)
    """
    recursive = RecursiveInstance.from_object(obj)
    recursive.set_tip_collection(tips_collection)
    recursive.set_instance_collection(instance_collection)
    recursive.set_scale(scale)
    recursive.build()
    return recursive


class RecursiveHUD:
    """
    Heads-Up Display for recursive instancing visualization.

    Cross-references:
    - KB Section 11: Recursive Hand Rig System
    """

    @staticmethod
    def display_settings(
        scale: float = 0.3,
        position_blend: float = 0.025,
        normal_blend: float = 0.025,
        position_blending: bool = True,
        normal_blending: bool = True
    ) -> str:
        """Display current recursive instance settings."""
        pos_status = "ON" if position_blending else "OFF"
        norm_status = "ON" if normal_blending else "OFF"
        lines = [
            "╔══════════════════════════════════════╗",
            "║      RECURSIVE INSTANCE SETTINGS     ║",
            "╠══════════════════════════════════════╣",
            f"║ Child Scale:   {scale:>20.2f} ║",
            "╠══════════════════════════════════════╣",
            "║ BLENDING                             ║",
            f"║   Position:    {pos_status:>20} ║",
            f"║   Blend Dist:  {position_blend:>20.4f} ║",
            f"║   Normal:      {norm_status:>20} ║",
            f"║   Blend Dist:  {normal_blend:>20.4f} ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_collection_setup() -> str:
        """Display collection setup guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       COLLECTION SETUP               ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  TIP COLLECTION:                     ║",
            "║    • Empty objects at tip positions  ║",
            "║    • One per fingertip (e.g., 5)     ║",
            "║    • Parented to hand rig            ║",
            "║                                      ║",
            "║  INSTANCE COLLECTION:                ║",
            "║    • Geometry to instance at tips    ║",
            "║    • Can be hand, finger, any mesh   ║",
            "║    • Centered at origin              ║",
            "║                                      ║",
            "║  CRITICAL:                            ║",
            "║    Separate Children = TRUE          ║",
            "║    (for individual transforms)       ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_node_flow() -> str:
        """Display the node flow for recursive instancing."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       RECURSIVE NODE FLOW            ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  [Group Input]                       ║",
            "║       │                              ║",
            "║       └──→ [Collection Info] ← Tips  ║",
            "║                 │                    ║",
            "║           [Separate Children]        ║",
            "║                 │                    ║",
            "║           [To Points]                ║",
            "║                 │                    ║",
            "║       [Store Transform]              ║",
            "║                 │                    ║",
            "║  ┌──────────────┴──────────────┐     ║",
            "║  │                             │     ║",
            "║  ↓                             ↓     ║",
            "║ [Proximity] ← Parent    [Collection] ║",
            "║     │                  Info (Hands)  ║",
            "║  [Map Range]                    │     ║",
            "║     │                           │     ║",
            "║  [Mix Position]                 │     ║",
            "║     │                           │     ║",
            "║     └───────────┬───────────────┘     ║",
            "║                 ↓                    ║",
            "║       [Instance on Points]           ║",
            "║                 │                    ║",
            "║       [Scale Instances]              ║",
            "║                 │                    ║",
            "║       [Optional: Blend Normals]      ║",
            "║                 │                    ║",
            "║       [Join with Parent]             ║",
            "║                 │                    ║",
            "║       [Group Output]                 ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """Display pre-flight checklist for recursive setup."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║     RECURSIVE PRE-FLIGHT CHECKLIST   ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  □ Tip collection created            ║",
            "║    (empties at fingertip positions)  ║",
            "║                                      ║",
            "║  □ Instance collection created       ║",
            "║    (geometry to spawn at tips)       ║",
            "║                                      ║",
            "║  □ Separate Children = TRUE          ║",
            "║    (CRITICAL for proper function)    ║",
            "║                                      ║",
            "║  □ Scale set (0.2-0.4 typical)       ║",
            "║                                      ║",
            "║  □ Position blending enabled         ║",
            "║    (for smooth intersections)        ║",
            "║                                      ║",
            "║  □ Normal blending enabled           ║",
            "║    (for seamless shading)            ║",
            "║                                      ║",
            "║  □ Parent geometry referenced        ║",
            "║    (for proximity calculations)      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @staticmethod
    def display_blending_guide() -> str:
        """Display blending distance guide."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       BLENDING DISTANCE GUIDE        ║",
            "╠══════════════════════════════════════╣",
            "║                                      ║",
            "║  TYPICAL VALUES:                     ║",
            "║    0.01  = Very precise intersection ║",
            "║    0.025 = Default (recommended)     ║",
            "║    0.05  = Soft, gradual blend       ║",
            "║                                      ║",
            "║  POSITION BLEND:                     ║",
            "║    Snaps child vertices to parent    ║",
            "║    surface near intersection         ║",
            "║                                      ║",
            "║  NORMAL BLEND:                       ║",
            "║    Smooths shading at intersection   ║",
            "║    Must match position distance      ║",
            "║                                      ║",
            "║  TIP: Start with 0.025 for both      ║",
            "╚══════════════════════════════════════╝"
        ]
        return "\n".join(lines)


def print_recursive_settings(**kwargs) -> None:
    """Print recursive settings to console."""
    print(RecursiveHUD.display_settings(**kwargs))
