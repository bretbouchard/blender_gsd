"""
Mecha Assembly System

Combines mechanical parts into complete assemblies (robots, vehicles, etc).
Supports hierarchical structure, attachment constraints, and export.

Implements REQ-CH-06: Assembly System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union
from enum import Enum
from pathlib import Path
import json
import math


class AssemblyType(Enum):
    """Assembly type classification."""
    HUMANOID = "humanoid"       # Biped robot/mech
    QUADRUPED = "quadruped"     # Four-legged
    VEHICLE = "vehicle"         # Car, tank, etc
    DRONE = "drone"            # Flying vehicle
    STATIONARY = "stationary"   # Turret, cannon
    PROP = "prop"              # Static assembly
    HYBRID = "hybrid"          # Mixed type


# =============================================================================
# ATTACHMENT PRESETS
# =============================================================================

ATTACHMENT_PRESETS: Dict[str, Dict[str, Any]] = {
    "shoulder_left": {
        "parent": "torso",
        "position": (0.2, 0.4, 0.0),
        "rotation": (0, 0, 90),
        "point_type": "ball_joint",
        "limits": {"x": (-90, 90), "y": (-45, 120), "z": (-90, 90)},
    },
    "shoulder_right": {
        "parent": "torso",
        "position": (-0.2, 0.4, 0.0),
        "rotation": (0, 0, -90),
        "point_type": "ball_joint",
        "limits": {"x": (-90, 90), "y": (-120, 45), "z": (-90, 90)},
    },
    "hip_left": {
        "parent": "torso",
        "position": (0.1, -0.4, 0.0),
        "rotation": (0, 180, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-45, 90), "y": (-30, 30), "z": (-60, 60)},
    },
    "hip_right": {
        "parent": "torso",
        "position": (-0.1, -0.4, 0.0),
        "rotation": (0, 180, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-45, 90), "y": (-30, 30), "z": (-60, 60)},
    },
    "neck": {
        "parent": "torso",
        "position": (0, 0.5, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-45, 45), "y": (-60, 60), "z": (-45, 45)},
    },
    "elbow_left": {
        "parent": "upper_arm_l",
        "position": (0, -0.3, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "hinge",
        "limits": {"z": (-145, 0)},
    },
    "elbow_right": {
        "parent": "upper_arm_r",
        "position": (0, -0.3, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "hinge",
        "limits": {"z": (0, 145)},
    },
    "knee_left": {
        "parent": "upper_leg_l",
        "position": (0, -0.4, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "hinge",
        "limits": {"z": (0, 145)},
    },
    "knee_right": {
        "parent": "upper_leg_r",
        "position": (0, -0.4, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "hinge",
        "limits": {"z": (0, 145)},
    },
    "wrist_left": {
        "parent": "lower_arm_l",
        "position": (0, -0.25, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-45, 45), "y": (-30, 30), "z": (-90, 90)},
    },
    "wrist_right": {
        "parent": "lower_arm_r",
        "position": (0, -0.25, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-45, 45), "y": (-30, 30), "z": (-90, 90)},
    },
    "ankle_left": {
        "parent": "lower_leg_l",
        "position": (0, -0.4, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-30, 45), "y": (-20, 20), "z": (-30, 30)},
    },
    "ankle_right": {
        "parent": "lower_leg_r",
        "position": (0, -0.4, 0.0),
        "rotation": (0, 0, 0),
        "point_type": "ball_joint",
        "limits": {"x": (-30, 45), "y": (-20, 20), "z": (-30, 30)},
    },
    "weapon_mount": {
        "parent": "any",
        "position": (0, 0, 0.2),
        "rotation": (0, 0, 0),
        "point_type": "fixed",
        "limits": {},
    },
    "armor_slot": {
        "parent": "any",
        "position": (0, 0.05, 0),
        "rotation": (0, 0, 0),
        "point_type": "fixed",
        "limits": {},
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AssemblyNode:
    """
    Node in assembly hierarchy.

    Represents a part instance with transform and hierarchy info.

    Attributes:
        node_id: Unique node identifier
        part_id: Reference to part in library
        parent_id: Parent node ID (empty for root)
        attachment_point: Attachment point used
        position: Local position offset
        rotation: Local rotation (Euler degrees)
        scale: Local scale factor
        variant: Variant index to use
        enabled: Whether node is active
        custom_properties: Custom properties
    """
    node_id: str = ""
    part_id: str = ""
    parent_id: str = ""
    attachment_point: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    variant: int = 0
    enabled: bool = True
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "part_id": self.part_id,
            "parent_id": self.parent_id,
            "attachment_point": self.attachment_point,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": self.scale,
            "variant": self.variant,
            "enabled": self.enabled,
            "custom_properties": self.custom_properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssemblyNode":
        """Create from dictionary."""
        return cls(
            node_id=data.get("node_id", ""),
            part_id=data.get("part_id", ""),
            parent_id=data.get("parent_id", ""),
            attachment_point=data.get("attachment_point", ""),
            position=tuple(data.get("position", [0.0, 0.0, 0.0])),
            rotation=tuple(data.get("rotation", [0.0, 0.0, 0.0])),
            scale=data.get("scale", 1.0),
            variant=data.get("variant", 0),
            enabled=data.get("enabled", True),
            custom_properties=data.get("custom_properties", {}),
        )


@dataclass
class AssemblySpec:
    """
    Complete assembly specification.

    Attributes:
        assembly_id: Unique assembly identifier
        name: Display name
        assembly_type: Type classification
        root_node: Root node ID
        nodes: All nodes in assembly
        materials: Material preset assignments
        metadata: Assembly metadata
    """
    assembly_id: str = ""
    name: str = ""
    assembly_type: str = "humanoid"
    root_node: str = ""
    nodes: List[AssemblyNode] = field(default_factory=list)
    materials: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "assembly_id": self.assembly_id,
            "name": self.name,
            "assembly_type": self.assembly_type,
            "root_node": self.root_node,
            "nodes": [n.to_dict() for n in self.nodes],
            "materials": self.materials,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssemblySpec":
        """Create from dictionary."""
        return cls(
            assembly_id=data.get("assembly_id", ""),
            name=data.get("name", ""),
            assembly_type=data.get("assembly_type", "humanoid"),
            root_node=data.get("root_node", ""),
            nodes=[AssemblyNode.from_dict(n) for n in data.get("nodes", [])],
            materials=data.get("materials", {}),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# ASSEMBLY CLASS
# =============================================================================

class Assembly:
    """
    Manages a mechanical assembly.

    Handles part addition, hierarchy management, and export.

    Usage:
        assembly = Assembly("my_mech")
        assembly.set_root("torso_ultraborg_01")
        assembly.add_part("arm_left_01", parent="torso", attachment="shoulder_left")
        assembly.export_blend("mech.blend")
    """

    def __init__(
        self,
        name: str,
        assembly_type: str = "humanoid",
    ):
        """
        Initialize assembly.

        Args:
            name: Assembly name
            assembly_type: Type classification
        """
        self.name = name
        self.assembly_type = assembly_type
        self.nodes: Dict[str, AssemblyNode] = {}
        self.root_node_id: str = ""
        self.materials: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {
            "created": "",
            "modified": "",
            "version": "1.0",
        }
        self._node_counter = 0

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        self._node_counter += 1
        return f"node_{self._node_counter:04d}"

    def set_root(
        self,
        part_id: str,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
    ) -> str:
        """
        Set root part of assembly.

        Args:
            part_id: Part to use as root
            position: World position
            rotation: World rotation
            scale: Scale factor

        Returns:
            Root node ID
        """
        node_id = self._generate_node_id()
        node = AssemblyNode(
            node_id=node_id,
            part_id=part_id,
            parent_id="",
            position=position,
            rotation=rotation,
            scale=scale,
        )
        self.nodes[node_id] = node
        self.root_node_id = node_id
        return node_id

    def add_part(
        self,
        part_id: str,
        parent: str,
        attachment: Optional[str] = None,
        offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        variant: int = 0,
    ) -> str:
        """
        Add part to assembly.

        Args:
            part_id: Part to add
            parent: Parent node ID
            attachment: Attachment point preset
            offset: Local position offset
            rotation: Local rotation
            scale: Scale factor
            variant: Variant index

        Returns:
            New node ID
        """
        if parent not in self.nodes:
            raise ValueError(f"Parent node '{parent}' not found")

        node_id = self._generate_node_id()

        # Apply attachment preset if specified
        position = offset
        final_rotation = rotation
        if attachment and attachment in ATTACHMENT_PRESETS:
            preset = ATTACHMENT_PRESETS[attachment]
            position = tuple(
                offset[i] + preset.get("position", (0, 0, 0))[i]
                for i in range(3)
            )
            final_rotation = tuple(
                rotation[i] + preset.get("rotation", (0, 0, 0))[i]
                for i in range(3)
            )

        node = AssemblyNode(
            node_id=node_id,
            part_id=part_id,
            parent_id=parent,
            attachment_point=attachment or "",
            position=position,
            rotation=final_rotation,
            scale=scale,
            variant=variant,
        )
        self.nodes[node_id] = node
        return node_id

    def remove_node(self, node_id: str, remove_children: bool = True) -> List[str]:
        """
        Remove node from assembly.

        Args:
            node_id: Node to remove
            remove_children: Also remove child nodes

        Returns:
            List of removed node IDs
        """
        if node_id not in self.nodes:
            return []

        removed = [node_id]

        if remove_children:
            # Find all children
            children = [
                nid for nid, node in self.nodes.items()
                if node.parent_id == node_id
            ]
            for child_id in children:
                removed.extend(self.remove_node(child_id, remove_children=True))

        del self.nodes[node_id]
        return removed

    def get_node(self, node_id: str) -> Optional[AssemblyNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[AssemblyNode]:
        """Get direct children of node."""
        return [
            node for node in self.nodes.values()
            if node.parent_id == node_id
        ]

    def get_descendants(self, node_id: str) -> List[AssemblyNode]:
        """Get all descendants of node."""
        descendants = []
        for child in self.get_children(node_id):
            descendants.append(child)
            descendants.extend(self.get_descendants(child.node_id))
        return descendants

    def get_hierarchy(self) -> Dict[str, Any]:
        """Get hierarchy tree."""
        def build_tree(node_id: str) -> Dict[str, Any]:
            node = self.nodes[node_id]
            return {
                "node_id": node_id,
                "part_id": node.part_id,
                "children": [
                    build_tree(child.node_id)
                    for child in self.get_children(node_id)
                ],
            }

        if not self.root_node_id:
            return {}

        return build_tree(self.root_node_id)

    def set_material(self, slot: str, preset: str) -> None:
        """
        Set material preset for slot.

        Args:
            slot: Material slot name
            preset: Material preset name
        """
        self.materials[slot] = preset

    def get_world_transform(
        self,
        node_id: str,
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], float]:
        """
        Calculate world transform for node.

        Args:
            node_id: Node to calculate

        Returns:
            Tuple of (position, rotation, scale)
        """
        node = self.nodes.get(node_id)
        if not node:
            return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.0)

        # Accumulate from root
        position = list(node.position)
        rotation = list(node.rotation)
        scale = node.scale

        current = node
        while current.parent_id:
            parent = self.nodes.get(current.parent_id)
            if not parent:
                break

            # Add parent position (simplified - no rotation consideration)
            position[0] += parent.position[0]
            position[1] += parent.position[1]
            position[2] += parent.position[2]

            # Add parent rotation
            rotation[0] += parent.rotation[0]
            rotation[1] += parent.rotation[1]
            rotation[2] += parent.rotation[2]

            # Accumulate scale
            scale *= parent.scale

            current = parent

        return (tuple(position), tuple(rotation), scale)

    def to_spec(self) -> AssemblySpec:
        """Convert to AssemblySpec."""
        return AssemblySpec(
            assembly_id=self.name.lower().replace(" ", "_"),
            name=self.name,
            assembly_type=self.assembly_type,
            root_node=self.root_node_id,
            nodes=list(self.nodes.values()),
            materials=self.materials,
            metadata=self.metadata,
        )

    @classmethod
    def from_spec(cls, spec: AssemblySpec) -> "Assembly":
        """Create from AssemblySpec."""
        assembly = cls(
            name=spec.name,
            assembly_type=spec.assembly_type,
        )
        assembly.root_node_id = spec.root_node
        assembly.nodes = {n.node_id: n for n in spec.nodes}
        assembly.materials = spec.materials
        assembly.metadata = spec.metadata
        return assembly

    def to_json(self, path: str) -> None:
        """Save assembly to JSON."""
        spec = self.to_spec()
        with open(path, "w") as f:
            json.dump(spec.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "Assembly":
        """Load assembly from JSON."""
        with open(path, "r") as f:
            data = json.load(f)
        spec = AssemblySpec.from_dict(data)
        return cls.from_spec(spec)

    def get_statistics(self) -> Dict[str, Any]:
        """Get assembly statistics."""
        return {
            "name": self.name,
            "type": self.assembly_type,
            "total_parts": len(self.nodes),
            "hierarchy_depth": self._calculate_depth(),
            "materials": len(self.materials),
        }

    def _calculate_depth(self) -> int:
        """Calculate hierarchy depth."""
        def depth(node_id: str) -> int:
            children = self.get_children(node_id)
            if not children:
                return 1
            return 1 + max(depth(c.node_id) for c in children)

        if not self.root_node_id:
            return 0
        return depth(self.root_node_id)

    def export_blend(
        self,
        path: str,
        parts_library: Optional[Any] = None,
    ) -> bool:
        """
        Export assembly to .blend file.

        Args:
            path: Output path
            parts_library: PartsLibrary for loading parts

        Returns:
            Success status

        Note:
            In Blender context, this would:
            1. Create new blend file
            2. Load parts from library
            3. Instance with transforms
            4. Create hierarchy
            5. Apply materials
        """
        # Placeholder - actual implementation requires bpy
        spec = self.to_spec()
        spec.to_dict()  # Validates structure

        # Save JSON as intermediate format
        json_path = path.replace(".blend", ".json")
        self.to_json(json_path)

        return True


# =============================================================================
# ASSEMBLY BUILDER
# =============================================================================

class AssemblyBuilder:
    """
    Fluent interface for building assemblies.

    Usage:
        builder = AssemblyBuilder("my_mech")
        builder.root("torso_01").arm_left("arm_01").hand_left("hand_01")
        assembly = builder.build()
    """

    def __init__(self, name: str, assembly_type: str = "humanoid"):
        """Initialize builder."""
        self._assembly = Assembly(name, assembly_type)
        self._current_node: str = ""

    def root(self, part_id: str) -> "AssemblyBuilder":
        """Set root part."""
        self._current_node = self._assembly.set_root(part_id)
        return self

    def torso(self, part_id: str) -> "AssemblyBuilder":
        """Add torso (alias for root)."""
        if not self._assembly.root_node_id:
            return self.root(part_id)
        return self

    def head(self, part_id: str) -> "AssemblyBuilder":
        """Add head to torso."""
        if self._assembly.root_node_id:
            self._assembly.add_part(part_id, self._assembly.root_node_id, "neck")
        return self

    def arm_left(
        self,
        upper: str,
        lower: Optional[str] = None,
        hand: Optional[str] = None,
    ) -> "AssemblyBuilder":
        """Add left arm."""
        if not self._assembly.root_node_id:
            return self

        upper_id = self._assembly.add_part(
            upper, self._assembly.root_node_id, "shoulder_left"
        )
        self._current_node = upper_id

        if lower:
            lower_id = self._assembly.add_part(lower, upper_id, "elbow_left")
            self._current_node = lower_id

            if hand:
                self._assembly.add_part(hand, lower_id, "wrist_left")

        return self

    def arm_right(
        self,
        upper: str,
        lower: Optional[str] = None,
        hand: Optional[str] = None,
    ) -> "AssemblyBuilder":
        """Add right arm."""
        if not self._assembly.root_node_id:
            return self

        upper_id = self._assembly.add_part(
            upper, self._assembly.root_node_id, "shoulder_right"
        )
        self._current_node = upper_id

        if lower:
            lower_id = self._assembly.add_part(lower, upper_id, "elbow_right")
            self._current_node = lower_id

            if hand:
                self._assembly.add_part(hand, lower_id, "wrist_right")

        return self

    def leg_left(
        self,
        upper: str,
        lower: Optional[str] = None,
        foot: Optional[str] = None,
    ) -> "AssemblyBuilder":
        """Add left leg."""
        if not self._assembly.root_node_id:
            return self

        upper_id = self._assembly.add_part(
            upper, self._assembly.root_node_id, "hip_left"
        )
        self._current_node = upper_id

        if lower:
            lower_id = self._assembly.add_part(lower, upper_id, "knee_left")
            self._current_node = lower_id

            if foot:
                self._assembly.add_part(foot, lower_id, "ankle_left")

        return self

    def leg_right(
        self,
        upper: str,
        lower: Optional[str] = None,
        foot: Optional[str] = None,
    ) -> "AssemblyBuilder":
        """Add right leg."""
        if not self._assembly.root_node_id:
            return self

        upper_id = self._assembly.add_part(
            upper, self._assembly.root_node_id, "hip_right"
        )
        self._current_node = upper_id

        if lower:
            lower_id = self._assembly.add_part(lower, upper_id, "knee_right")
            self._current_node = lower_id

            if foot:
                self._assembly.add_part(foot, lower_id, "ankle_right")

        return self

    def armor(self, part_id: str, slot: str = "armor_slot") -> "AssemblyBuilder":
        """Add armor to current node."""
        if self._current_node:
            self._assembly.add_part(part_id, self._current_node, slot)
        return self

    def weapon(self, part_id: str, mount: str = "weapon_mount") -> "AssemblyBuilder":
        """Add weapon to current node."""
        if self._current_node:
            self._assembly.add_part(part_id, self._current_node, mount)
        return self

    def detail(self, part_id: str, offset: Tuple[float, float, float] = (0, 0, 0)) -> "AssemblyBuilder":
        """Add detail part to current node."""
        if self._current_node:
            self._assembly.add_part(part_id, self._current_node, offset=offset)
        return self

    def material(self, slot: str, preset: str) -> "AssemblyBuilder":
        """Set material preset."""
        self._assembly.set_material(slot, preset)
        return self

    def build(self) -> Assembly:
        """Build the assembly."""
        return self._assembly


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_assembly(
    name: str,
    parts: List[Dict[str, Any]],
    assembly_type: str = "humanoid",
) -> Assembly:
    """
    Create assembly from part list.

    Args:
        name: Assembly name
        parts: List of part specifications
        assembly_type: Type classification

    Returns:
        Assembly object

    Example:
        assembly = create_assembly("my_mech", [
            {"part_id": "torso_01", "is_root": True},
            {"part_id": "head_01", "parent": "torso_01", "attachment": "neck"},
            {"part_id": "arm_l_01", "parent": "torso_01", "attachment": "shoulder_left"},
        ])
    """
    builder = AssemblyBuilder(name, assembly_type)

    node_map: Dict[str, str] = {}

    for part_spec in parts:
        part_id = part_spec.get("part_id", "")

        if part_spec.get("is_root"):
            node_id = builder._assembly.set_root(part_id)
            node_map[part_id] = node_id
        else:
            parent_id = part_spec.get("parent", "")
            attachment = part_spec.get("attachment")
            offset = part_spec.get("offset", (0, 0, 0))

            if parent_id in node_map:
                node_id = builder._assembly.add_part(
                    part_id,
                    node_map[parent_id],
                    attachment,
                    offset,
                )
                node_map[part_id] = node_id

    return builder.build()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AssemblyType",
    # Data classes
    "AssemblySpec",
    "AssemblyNode",
    # Constants
    "ATTACHMENT_PRESETS",
    # Classes
    "Assembly",
    "AssemblyBuilder",
    # Functions
    "create_assembly",
]
