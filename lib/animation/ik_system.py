"""
IK System Module

Inverse kinematics constraint creation and management.

Phase 13.1: IK/FK System (REQ-ANIM-02)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from .types import IKConfig, IKMode, SplineIKConfig

if TYPE_CHECKING:
    import bpy


class IKSystem:
    """
    Manages IK constraints on armature bones.

    Provides methods to add, remove, and configure IK constraints
    for limbs, chains, and spline-based setups.
    """

    def __init__(self, armature: Any = None):
        """
        Initialize IK system.

        Args:
            armature: Blender armature object (optional)
        """
        self.armature = armature
        self._ik_configs: Dict[str, IKConfig] = {}

    def add_ik_constraint(self, armature: Any, config: IKConfig) -> Any:
        """
        Add IK constraint to a bone.

        Args:
            armature: Blender armature object
            config: IK configuration

        Returns:
            The created constraint
        """
        self.armature = armature

        # Get pose bone (last bone in chain gets the constraint)
        if not config.chain:
            raise ValueError("IK chain cannot be empty")

        bone_name = config.chain[-1]
        pose_bone = armature.pose.bones.get(bone_name)

        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        # Remove existing IK constraint if present
        self.remove_ik(armature, bone_name)

        # Create IK constraint
        ik_constraint = pose_bone.constraints.new('IK')

        # Configure basic properties
        ik_constraint.chain_count = config.chain_count
        ik_constraint.iterations = config.iterations
        ik_constraint.use_tail = config.use_tail
        ik_constraint.stretch = config.stretch
        ik_constraint.influence = config.weight

        # Set target (bone or object)
        if config.target:
            # Try to find as object first
            import bpy
            target_obj = bpy.data.objects.get(config.target)
            if target_obj:
                ik_constraint.target = target_obj
            else:
                # Check if it's a bone in the same armature
                if config.target in armature.pose.bones:
                    ik_constraint.target = armature
                    ik_constraint.subtarget = config.target

        # Set pole target
        if config.pole_target:
            pole_obj = bpy.data.objects.get(config.pole_target)
            if pole_obj:
                ik_constraint.pole_target = pole_obj
            else:
                if config.pole_target in armature.pose.bones:
                    ik_constraint.pole_target = armature
                    ik_constraint.pole_subtarget = config.pole_target

            ik_constraint.pole_angle = config.pole_angle

        # Store configuration
        self._ik_configs[config.name] = config

        return ik_constraint

    def remove_ik(self, armature: Any, bone_name: str) -> None:
        """
        Remove IK constraint from a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            return

        # Find and remove IK constraint
        for constraint in list(pose_bone.constraints):
            if constraint.type == 'IK':
                pose_bone.constraints.remove(constraint)

    def get_ik_constraint(self, armature: Any, bone_name: str) -> Optional[Any]:
        """
        Get IK constraint from a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint

        Returns:
            IK constraint or None
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            return None

        for constraint in pose_bone.constraints:
            if constraint.type == 'IK':
                return constraint

        return None

    def get_ik_chain(self, armature: Any, bone_name: str) -> List[str]:
        """
        Get bone chain affected by IK constraint.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint

        Returns:
            List of bone names in the chain (root to tip)
        """
        constraint = self.get_ik_constraint(armature, bone_name)
        if constraint is None:
            return []

        chain = [bone_name]
        pose_bone = armature.pose.bones.get(bone_name)

        if pose_bone is None:
            return chain

        # Walk up parent chain for chain_count bones
        for _ in range(constraint.chain_count - 1):
            parent = pose_bone.parent
            if parent is None:
                break
            chain.insert(0, parent.name)
            pose_bone = parent

        return chain

    def set_ik_target(self, armature: Any, bone_name: str, target: Any) -> None:
        """
        Set IK target for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint
            target: Target object or bone name
        """
        constraint = self.get_ik_constraint(armature, bone_name)
        if constraint is None:
            raise ValueError(f"No IK constraint found on bone '{bone_name}'")

        import bpy

        if isinstance(target, str):
            target_obj = bpy.data.objects.get(target)
            if target_obj:
                constraint.target = target_obj
            elif target in armature.pose.bones:
                constraint.target = armature
                constraint.subtarget = target
        else:
            constraint.target = target

    def set_pole_target(
        self,
        armature: Any,
        bone_name: str,
        pole: Any,
        angle: float = 0.0
    ) -> None:
        """
        Set IK pole target for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone with IK constraint
            pole: Pole target object or bone name
            angle: Pole angle in radians
        """
        constraint = self.get_ik_constraint(armature, bone_name)
        if constraint is None:
            raise ValueError(f"No IK constraint found on bone '{bone_name}'")

        import bpy

        if isinstance(pole, str):
            pole_obj = bpy.data.objects.get(pole)
            if pole_obj:
                constraint.pole_target = pole_obj
            elif pole in armature.pose.bones:
                constraint.pole_target = armature
                constraint.pole_subtarget = pole
        else:
            constraint.pole_target = pole

        constraint.pole_angle = angle

    def add_chain_ik(self, armature: Any, config: IKConfig) -> Any:
        """
        Add chain IK constraint (3+ bones).

        Same as add_ik_constraint but for multi-bone chains.

        Args:
            armature: Blender armature object
            config: IK configuration

        Returns:
            The created constraint
        """
        config.mode = IKMode.CHAIN
        return self.add_ik_constraint(armature, config)

    def add_spline_ik(self, armature: Any, config: SplineIKConfig) -> Any:
        """
        Add spline IK constraint for curves.

        Args:
            armature: Blender armature object
            config: Spline IK configuration

        Returns:
            The created constraint
        """
        self.armature = armature

        if not config.chain:
            raise ValueError("Spline IK chain cannot be empty")

        bone_name = config.chain[-1]
        pose_bone = armature.pose.bones.get(bone_name)

        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        # Get curve object
        import bpy
        curve_obj = bpy.data.objects.get(config.curve_object)
        if curve_obj is None:
            raise ValueError(f"Curve object '{config.curve_object}' not found")

        # Create spline IK constraint
        spline_ik = pose_bone.constraints.new('SPLINE_IK')

        # Configure properties
        spline_ik.chain_count = config.chain_count
        spline_ik.target = curve_obj
        spline_ik.use_curve_radius = config.use_curve_radius
        spline_ik.use_stretch = config.use_stretch
        spline_ik.use_y_stretch = config.use_y_stretch
        spline_ik.even_divisions = config.even_divisions

        # Set bindings if provided
        if config.bindings:
            # Bindings control how bones map to curve
            spline_ik.bindings = config.bindings

        return spline_ik

    def calculate_pole_position(
        self,
        armature: Any,
        chain: List[str],
        distance: float = 1.0,
        axis: str = 'X'
    ) -> Tuple[float, float, float]:
        """
        Calculate optimal pole target position for a chain.

        Args:
            armature: Blender armature object
            chain: List of bone names (root to tip)
            distance: Distance from chain
            axis: Axis to offset ('X', 'Y', 'Z')

        Returns:
            World position for pole target
        """
        if len(chain) < 2:
            raise ValueError("Chain must have at least 2 bones")

        # Get middle bone for pole positioning
        mid_bone_name = chain[len(chain) // 2 - 1] if len(chain) > 2 else chain[0]
        mid_bone = armature.pose.bones.get(mid_bone_name)

        if mid_bone is None:
            raise ValueError(f"Bone '{mid_bone_name}' not found")

        # Get world matrix of middle bone
        world_matrix = armature.matrix_world @ mid_bone.matrix

        # Calculate position with offset
        offset = {
            'X': (distance, 0, 0),
            'Y': (0, distance, 0),
            'Z': (0, 0, distance),
            '-X': (-distance, 0, 0),
            '-Y': (0, -distance, 0),
            '-Z': (0, 0, -distance),
        }.get(axis, (distance, 0, 0))

        pos = world_matrix.translation
        return (pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2])

    def get_config(self, name: str) -> Optional[IKConfig]:
        """Get stored IK configuration by name."""
        return self._ik_configs.get(name)

    def list_configs(self) -> List[str]:
        """List all stored IK configuration names."""
        return list(self._ik_configs.keys())


def add_ik_to_bone(
    armature: Any,
    bone_name: str,
    target: str,
    chain_count: int = 2,
    pole_target: Optional[str] = None,
    pole_angle: float = 0.0
) -> Any:
    """
    Convenience function to add IK to a bone.

    Args:
        armature: Blender armature object
        bone_name: Name of bone to add IK to
        target: Target object/bone name
        chain_count: Number of bones in chain
        pole_target: Optional pole target
        pole_angle: Pole angle in radians

    Returns:
        Created IK constraint
    """
    config = IKConfig(
        name=f"{bone_name}_ik",
        chain=[bone_name],  # Will be expanded by chain_count
        target=target,
        pole_target=pole_target,
        pole_angle=pole_angle,
        chain_count=chain_count,
    )

    system = IKSystem()
    return system.add_ik_constraint(armature, config)


def create_ik_setup(
    armature: Any,
    limb_type: str = "arm",
    side: str = "L",
    ik_target: Optional[str] = None,
    pole_target: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standard IK setup for a limb.

    Args:
        armature: Blender armature object
        limb_type: "arm" or "leg"
        side: "L" or "R"
        ik_target: Custom IK target name
        pole_target: Custom pole target name

    Returns:
        Dictionary with created constraints and objects
    """
    import bpy

    system = IKSystem()
    result = {}

    if limb_type == "arm":
        # Standard arm chain: upper_arm -> lower_arm -> hand
        upper = f"upper_arm_{side}"
        lower = f"lower_arm_{side}"
        hand = f"hand_{side}"
        chain = [upper, lower]

        # Default target name
        target_name = ik_target or f"ik_hand_{side}"
        pole_name = pole_target or f"pole_elbow_{side}"

    elif limb_type == "leg":
        # Standard leg chain: thigh -> shin -> foot
        thigh = f"thigh_{side}"
        shin = f"shin_{side}"
        foot = f"foot_{side}"
        chain = [thigh, shin]

        target_name = ik_target or f"ik_foot_{side}"
        pole_name = pole_target or f"pole_knee_{side}"

    else:
        raise ValueError(f"Unknown limb type: {limb_type}")

    # Create IK config
    config = IKConfig(
        name=f"{limb_type}_{side}_ik",
        chain=chain,
        target=target_name,
        pole_target=pole_name,
        chain_count=2,
    )

    # Add constraint
    constraint = system.add_ik_constraint(armature, config)
    result['constraint'] = constraint
    result['config'] = config

    return result


# Convenience exports
__all__ = [
    'IKSystem',
    'IKConfig',
    'SplineIKConfig',
    'add_ik_to_bone',
    'create_ik_setup',
]
