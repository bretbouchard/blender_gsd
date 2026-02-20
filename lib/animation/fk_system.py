"""
FK System Module

Forward kinematics bone control and rotation management.

Phase 13.1: IK/FK System (REQ-ANIM-03)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from .types import FKConfig, RotationOrder, RotationLimits

if TYPE_CHECKING:
    import bpy


class FKSystem:
    """
    Manages FK (Forward Kinematics) bone control.

    Provides methods for rotation control, rotation limits,
    and FK bone configuration.
    """

    def __init__(self, armature: Any = None):
        """
        Initialize FK system.

        Args:
            armature: Blender armature object (optional)
        """
        self.armature = armature
        self._fk_configs: Dict[str, FKConfig] = {}
        self._rotation_limits: Dict[str, RotationLimits] = {}

    def set_rotation_order(
        self,
        armature: Any,
        bone_name: str,
        order: RotationOrder
    ) -> None:
        """
        Set rotation order for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            order: Rotation order enum
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        pose_bone.rotation_mode = order.value

    def get_rotation_order(
        self,
        armature: Any,
        bone_name: str
    ) -> RotationOrder:
        """
        Get rotation order for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone

        Returns:
            Rotation order enum
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        return RotationOrder(pose_bone.rotation_mode)

    def get_rotation(
        self,
        armature: Any,
        bone_name: str,
        space: str = 'LOCAL'
    ) -> Tuple[float, float, float]:
        """
        Get Euler rotation of a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            space: 'LOCAL' or 'WORLD'

        Returns:
            Euler rotation (x, y, z) in radians
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        if space == 'WORLD':
            # Get world rotation
            world_matrix = armature.matrix_world @ pose_bone.matrix
            rotation = world_matrix.to_euler()
        else:
            # Use local rotation
            rotation = pose_bone.rotation_euler

        return (rotation.x, rotation.y, rotation.z)

    def set_rotation(
        self,
        armature: Any,
        bone_name: str,
        euler: Tuple[float, float, float],
        space: str = 'LOCAL'
    ) -> None:
        """
        Set Euler rotation of a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            euler: Euler rotation (x, y, z) in radians
            space: 'LOCAL' or 'WORLD'
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        if space == 'WORLD':
            # Convert world rotation to local
            # This is more complex - for now, just use local
            pose_bone.rotation_euler = euler
        else:
            pose_bone.rotation_euler = euler

    def get_quaternion(
        self,
        armature: Any,
        bone_name: str
    ) -> Tuple[float, float, float, float]:
        """
        Get quaternion rotation of a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone

        Returns:
            Quaternion (w, x, y, z)
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        q = pose_bone.rotation_quaternion
        return (q.w, q.x, q.y, q.z)

    def set_quaternion(
        self,
        armature: Any,
        bone_name: str,
        quaternion: Tuple[float, float, float, float]
    ) -> None:
        """
        Set quaternion rotation of a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            quaternion: Quaternion (w, x, y, z)
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        pose_bone.rotation_mode = 'QUATERNION'
        pose_bone.rotation_quaternion = quaternion

    def lock_rotation_axes(
        self,
        armature: Any,
        bone_name: str,
        axes: List[str]
    ) -> None:
        """
        Lock rotation axes for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            axes: List of axes to lock ('X', 'Y', 'Z')
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        pose_bone.lock_rotation = [
            'X' in axes,
            'Y' in axes,
            'Z' in axes
        ]

    def set_inherit_rotation(
        self,
        armature: Any,
        bone_name: str,
        inherit: bool
    ) -> None:
        """
        Set whether bone inherits rotation from parent.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            inherit: True to inherit rotation
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        # Need to access edit bone for this
        import bpy
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bone = armature.data.edit_bones.get(bone_name)
        if edit_bone:
            edit_bone.use_inherit_rotation = inherit

        bpy.ops.object.mode_set(mode='POSE')

    def set_rotation_limits(
        self,
        armature: Any,
        bone_name: str,
        limits: RotationLimits
    ) -> None:
        """
        Set rotation limits for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            limits: Rotation limits configuration
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        # Set limit rotation constraint
        limit_constraint = None

        # Find existing limit constraint
        for constraint in pose_bone.constraints:
            if constraint.type == 'LIMIT_ROTATION':
                limit_constraint = constraint
                break

        # Create new if not exists
        if limit_constraint is None:
            limit_constraint = pose_bone.constraints.new('LIMIT_ROTATION')

        # Configure limits
        limit_constraint.use_limit_x = limits.use_limits_x
        limit_constraint.use_limit_y = limits.use_limits_y
        limit_constraint.use_limit_z = limits.use_limits_z

        limit_constraint.min_x = math.radians(limits.x_min)
        limit_constraint.max_x = math.radians(limits.x_max)
        limit_constraint.min_y = math.radians(limits.y_min)
        limit_constraint.max_y = math.radians(limits.y_max)
        limit_constraint.min_z = math.radians(limits.z_min)
        limit_constraint.max_z = math.radians(limits.z_max)

        # Store limits
        self._rotation_limits[bone_name] = limits

    def get_rotation_limits(
        self,
        armature: Any,
        bone_name: str
    ) -> Optional[RotationLimits]:
        """
        Get rotation limits for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone

        Returns:
            Rotation limits or None
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            return None

        # Find limit constraint
        for constraint in pose_bone.constraints:
            if constraint.type == 'LIMIT_ROTATION':
                return RotationLimits(
                    x_min=math.degrees(constraint.min_x),
                    x_max=math.degrees(constraint.max_x),
                    y_min=math.degrees(constraint.min_y),
                    y_max=math.degrees(constraint.max_y),
                    z_min=math.degrees(constraint.min_z),
                    z_max=math.degrees(constraint.max_z),
                    use_limits_x=constraint.use_limit_x,
                    use_limits_y=constraint.use_limit_y,
                    use_limits_z=constraint.use_limit_z,
                )

        return self._rotation_limits.get(bone_name)

    def enforce_limits(
        self,
        armature: Any,
        bone_name: str
    ) -> None:
        """
        Enforce rotation limits on a bone.

        This ensures the current rotation is within limits.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
        """
        limits = self.get_rotation_limits(armature, bone_name)
        if limits is None:
            return

        rot = self.get_rotation(armature, bone_name)

        # Clamp rotation to limits
        clamped = list(rot)
        if limits.use_limits_x:
            clamped[0] = max(math.radians(limits.x_min),
                           min(math.radians(limits.x_max), rot[0]))
        if limits.use_limits_y:
            clamped[1] = max(math.radians(limits.y_min),
                           min(math.radians(limits.y_max), rot[1]))
        if limits.use_limits_z:
            clamped[2] = max(math.radians(limits.z_min),
                           min(math.radians(limits.z_max), rot[2]))

        self.set_rotation(armature, bone_name, tuple(clamped))

    def configure_bone(
        self,
        armature: Any,
        config: FKConfig
    ) -> None:
        """
        Apply full FK configuration to a bone.

        Args:
            armature: Blender armature object
            config: FK configuration
        """
        self.armature = armature

        # Set rotation order
        self.set_rotation_order(armature, config.bone_name, config.rotation_order)

        # Lock axes
        locked_axes = []
        if config.lock_x:
            locked_axes.append('X')
        if config.lock_y:
            locked_axes.append('Y')
        if config.lock_z:
            locked_axes.append('Z')

        if locked_axes:
            self.lock_rotation_axes(armature, config.bone_name, locked_axes)

        # Set inherit rotation
        self.set_inherit_rotation(armature, config.bone_name, config.inherit_rotation)

        # Store config
        self._fk_configs[config.bone_name] = config

    def get_config(self, bone_name: str) -> Optional[FKConfig]:
        """Get stored FK configuration for a bone."""
        return self._fk_configs.get(bone_name)

    def copy_rotation(
        self,
        armature: Any,
        source_bone: str,
        target_bone: str
    ) -> None:
        """
        Copy rotation from source to target bone.

        Args:
            armature: Blender armature object
            source_bone: Source bone name
            target_bone: Target bone name
        """
        rot = self.get_rotation(armature, source_bone)
        self.set_rotation(armature, target_bone, rot)

    def mirror_rotation(
        self,
        armature: Any,
        bone_name: str,
        axis: str = 'X'
    ) -> Tuple[float, float, float]:
        """
        Get mirrored rotation for a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            axis: Mirror axis ('X', 'Y', 'Z')

        Returns:
            Mirrored Euler rotation
        """
        rot = self.get_rotation(armature, bone_name)

        if axis == 'X':
            return (-rot[0], rot[1], -rot[2])
        elif axis == 'Y':
            return (rot[0], -rot[1], -rot[2])
        elif axis == 'Z':
            return (-rot[0], -rot[1], rot[2])

        return rot


def set_bone_rotation(
    armature: Any,
    bone_name: str,
    rotation: Tuple[float, float, float],
    degrees: bool = False
) -> None:
    """
    Convenience function to set bone rotation.

    Args:
        armature: Blender armature object
        bone_name: Name of bone
        rotation: Euler rotation (x, y, z)
        degrees: True if rotation is in degrees
    """
    system = FKSystem(armature)

    if degrees:
        rotation = tuple(math.radians(r) for r in rotation)

    system.set_rotation(armature, bone_name, rotation)


def get_bone_rotation(
    armature: Any,
    bone_name: str,
    degrees: bool = False
) -> Tuple[float, float, float]:
    """
    Convenience function to get bone rotation.

    Args:
        armature: Blender armature object
        bone_name: Name of bone
        degrees: True to return rotation in degrees

    Returns:
        Euler rotation (x, y, z)
    """
    system = FKSystem()
    rot = system.get_rotation(armature, bone_name)

    if degrees:
        return tuple(math.degrees(r) for r in rot)

    return rot


def apply_rotation_limits_preset(
    armature: Any,
    preset_name: str
) -> Dict[str, RotationLimits]:
    """
    Apply rotation limits preset to armature.

    Args:
        armature: Blender armature object
        preset_name: Name of preset (e.g., 'human_arm', 'human_leg')

    Returns:
        Dictionary of applied limits
    """
    # Standard presets
    presets = {
        'human_arm': {
            'upper_arm_L': RotationLimits(
                x_min=-90, x_max=90,
                y_min=-90, y_max=90,
                z_min=-90, z_max=60,
                use_limits_x=True, use_limits_y=True, use_limits_z=True,
            ),
            'lower_arm_L': RotationLimits(
                x_min=0, x_max=145,
                y_min=0, y_max=0,
                z_min=0, z_max=0,
                use_limits_x=True, use_limits_y=False, use_limits_z=False,
            ),
        },
        'human_leg': {
            'thigh_L': RotationLimits(
                x_min=-120, x_max=45,
                y_min=-45, y_max=45,
                z_min=-45, z_max=60,
                use_limits_x=True, use_limits_y=True, use_limits_z=True,
            ),
            'shin_L': RotationLimits(
                x_min=0, x_max=150,
                y_min=0, y_max=0,
                z_min=0, z_max=0,
                use_limits_x=True, use_limits_y=False, use_limits_z=False,
            ),
        },
    }

    preset = presets.get(preset_name)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_name}")

    system = FKSystem(armature)
    for bone_name, limits in preset.items():
        if bone_name in armature.pose.bones:
            system.set_rotation_limits(armature, bone_name, limits)

    return preset


# Convenience exports
__all__ = [
    'FKSystem',
    'FKConfig',
    'RotationOrder',
    'RotationLimits',
    'set_bone_rotation',
    'get_bone_rotation',
    'apply_rotation_limits_preset',
]
