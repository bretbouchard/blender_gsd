"""
Rotation Limits Module

Joint rotation limit enforcement for bones.

Phase 13.1: IK/FK System (REQ-ANIM-02)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math
from pathlib import Path

from .types import RotationLimits

if TYPE_CHECKING:
    import bpy


class RotationLimitEnforcer:
    """
    Enforces rotation limits on armature bones.

    Uses Blender's limit rotation constraints to prevent
    bones from rotating beyond anatomical limits.
    """

    def __init__(self, armature: Any = None):
        """
        Initialize rotation limit enforcer.

        Args:
            armature: Blender armature object (optional)
        """
        self.armature = armature
        self._limits: Dict[str, RotationLimits] = {}
        self._presets: Dict[str, Dict[str, RotationLimits]] = {}

    def apply_limits(
        self,
        armature: Any,
        bone_name: str,
        limits: RotationLimits
    ) -> Any:
        """
        Apply rotation limits to a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
            limits: Rotation limits configuration

        Returns:
            Created limit constraint
        """
        self.armature = armature

        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            raise ValueError(f"Bone '{bone_name}' not found in armature")

        # Find existing limit constraint
        limit_constraint = None
        for constraint in pose_bone.constraints:
            if constraint.type == 'LIMIT_ROTATION':
                limit_constraint = constraint
                break

        # Create new if not exists
        if limit_constraint is None:
            limit_constraint = pose_bone.constraints.new('LIMIT_ROTATION')

        # Configure limits (convert degrees to radians)
        limit_constraint.use_limit_x = limits.use_limits_x
        limit_constraint.use_limit_y = limits.use_limits_y
        limit_constraint.use_limit_z = limits.use_limits_z

        limit_constraint.min_x = math.radians(limits.x_min)
        limit_constraint.max_x = math.radians(limits.x_max)
        limit_constraint.min_y = math.radians(limits.y_min)
        limit_constraint.max_y = math.radians(limits.y_max)
        limit_constraint.min_z = math.radians(limits.z_min)
        limit_constraint.max_z = math.radians(limits.z_max)

        limit_constraint.owner_space = 'LOCAL'

        # Store limits
        self._limits[bone_name] = limits

        return limit_constraint

    def remove_limits(
        self,
        armature: Any,
        bone_name: str
    ) -> None:
        """
        Remove rotation limits from a bone.

        Args:
            armature: Blender armature object
            bone_name: Name of bone
        """
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            return

        # Find and remove limit constraint
        for constraint in list(pose_bone.constraints):
            if constraint.type == 'LIMIT_ROTATION':
                pose_bone.constraints.remove(constraint)

        # Remove from storage
        if bone_name in self._limits:
            del self._limits[bone_name]

    def get_limits(
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

        return self._limits.get(bone_name)

    def enforce_limits(
        self,
        armature: Any,
        bone_name: str
    ) -> Tuple[float, float, float]:
        """
        Enforce rotation limits on a bone's current rotation.

        Clamps the current rotation to be within limits.

        Args:
            armature: Blender armature object
            bone_name: Name of bone

        Returns:
            Clamped rotation (x, y, z) in radians
        """
        limits = self.get_limits(armature, bone_name)
        if limits is None:
            return (0.0, 0.0, 0.0)

        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            return (0.0, 0.0, 0.0)

        rot = pose_bone.rotation_euler
        clamped = list(rot)

        if limits.use_limits_x:
            clamped[0] = max(
                math.radians(limits.x_min),
                min(math.radians(limits.x_max), rot[0])
            )
        if limits.use_limits_y:
            clamped[1] = max(
                math.radians(limits.y_min),
                min(math.radians(limits.y_max), rot[1])
            )
        if limits.use_limits_z:
            clamped[2] = max(
                math.radians(limits.z_min),
                min(math.radians(limits.z_max), rot[2])
            )

        pose_bone.rotation_euler = clamped
        return tuple(clamped)

    def enforce_all_limits(self, armature: Any) -> None:
        """
        Enforce rotation limits on all bones.

        Args:
            armature: Blender armature object
        """
        for bone_name in self._limits:
            self.enforce_limits(armature, bone_name)

    def load_limits_preset(
        self,
        preset_name: str
    ) -> Dict[str, RotationLimits]:
        """
        Load rotation limits preset.

        Args:
            preset_name: Name of preset

        Returns:
            Dictionary of bone name to limits
        """
        # Check built-in presets first
        if preset_name in self._presets:
            return self._presets[preset_name]

        # Try to load from file
        preset_path = Path(__file__).parent.parent.parent / "configs" / "animation" / "ik" / "rotation_limits.yaml"

        if preset_path.exists():
            try:
                import yaml
                with open(preset_path) as f:
                    data = yaml.safe_load(f)

                if preset_name in data:
                    preset = {}
                    for bone_name, limits_data in data[preset_name].items():
                        preset[bone_name] = RotationLimits.from_dict(limits_data)

                    self._presets[preset_name] = preset
                    return preset
            except Exception:
                pass

        # Fall back to built-in presets
        return self._get_builtin_preset(preset_name)

    def _get_builtin_preset(self, name: str) -> Dict[str, RotationLimits]:
        """Get built-in rotation limits preset."""
        presets = {
            'human_arm_left': {
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
                'hand_L': RotationLimits(
                    x_min=-90, x_max=90,
                    y_min=-45, y_max=45,
                    z_min=-90, z_max=90,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
            },
            'human_arm_right': {
                'upper_arm_R': RotationLimits(
                    x_min=-90, x_max=90,
                    y_min=-90, y_max=90,
                    z_min=-60, z_max=90,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
                'lower_arm_R': RotationLimits(
                    x_min=0, x_max=145,
                    y_min=0, y_max=0,
                    z_min=0, z_max=0,
                    use_limits_x=True, use_limits_y=False, use_limits_z=False,
                ),
                'hand_R': RotationLimits(
                    x_min=-90, x_max=90,
                    y_min=-45, y_max=45,
                    z_min=-90, z_max=90,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
            },
            'human_leg_left': {
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
                'foot_L': RotationLimits(
                    x_min=-50, x_max=50,
                    y_min=-25, y_max=25,
                    z_min=-45, z_max=45,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
            },
            'human_leg_right': {
                'thigh_R': RotationLimits(
                    x_min=-120, x_max=45,
                    y_min=-45, y_max=45,
                    z_min=-60, z_max=45,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
                'shin_R': RotationLimits(
                    x_min=0, x_max=150,
                    y_min=0, y_max=0,
                    z_min=0, z_max=0,
                    use_limits_x=True, use_limits_y=False, use_limits_z=False,
                ),
                'foot_R': RotationLimits(
                    x_min=-50, x_max=50,
                    y_min=-25, y_max=25,
                    z_min=-45, z_max=45,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
            },
            'human_spine': {
                'spine_01': RotationLimits(
                    x_min=-30, x_max=30,
                    y_min=-30, y_max=30,
                    z_min=-30, z_max=30,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
                'spine_02': RotationLimits(
                    x_min=-30, x_max=30,
                    y_min=-30, y_max=30,
                    z_min=-30, z_max=30,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
                'spine_03': RotationLimits(
                    x_min=-30, x_max=30,
                    y_min=-45, y_max=45,
                    z_min=-30, z_max=30,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
            },
            'human_neck': {
                'neck': RotationLimits(
                    x_min=-45, x_max=45,
                    y_min=-60, y_max=60,
                    z_min=-45, z_max=45,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
                'head': RotationLimits(
                    x_min=-45, x_max=45,
                    y_min=-75, y_max=75,
                    z_min=-45, z_max=45,
                    use_limits_x=True, use_limits_y=True, use_limits_z=True,
                ),
            },
        }

        return presets.get(name, {})

    def apply_preset(
        self,
        armature: Any,
        preset_name: str
    ) -> Dict[str, Any]:
        """
        Apply rotation limits preset to armature.

        Args:
            armature: Blender armature object
            preset_name: Name of preset

        Returns:
            Dictionary of created constraints
        """
        preset = self.load_limits_preset(preset_name)

        constraints = {}
        for bone_name, limits in preset.items():
            if bone_name in armature.pose.bones:
                constraint = self.apply_limits(armature, bone_name, limits)
                constraints[bone_name] = constraint

        return constraints

    def save_custom_preset(
        self,
        preset_name: str,
        bone_limits: Dict[str, RotationLimits]
    ) -> None:
        """
        Save custom rotation limits preset.

        Args:
            preset_name: Name for preset
            bone_limits: Dictionary of bone name to limits
        """
        self._presets[preset_name] = bone_limits

    def list_presets(self) -> List[str]:
        """
        List available rotation limit presets.

        Returns:
            List of preset names
        """
        built_in = [
            'human_arm_left',
            'human_arm_right',
            'human_leg_left',
            'human_leg_right',
            'human_spine',
            'human_neck',
        ]

        return built_in + list(self._presets.keys())


def apply_joint_limits(
    armature: Any,
    joint_type: str,
    side: str = "L"
) -> Dict[str, Any]:
    """
    Convenience function to apply standard joint limits.

    Args:
        armature: Blender armature object
        joint_type: "arm", "leg", "spine", "neck"
        side: "L" or "R" (for arm/leg)

    Returns:
        Dictionary of created constraints
    """
    enforcer = RotationLimitEnforcer()

    # Map to preset name
    preset_map = {
        ('arm', 'L'): 'human_arm_left',
        ('arm', 'R'): 'human_arm_right',
        ('leg', 'L'): 'human_leg_left',
        ('leg', 'R'): 'human_leg_right',
        ('spine', ''): 'human_spine',
        ('neck', ''): 'human_neck',
    }

    preset_name = preset_map.get((joint_type, side))
    if preset_name is None:
        raise ValueError(f"Unknown joint type: {joint_type} {side}")

    return enforcer.apply_preset(armature, preset_name)


def clamp_rotation(
    rotation: Tuple[float, float, float],
    limits: RotationLimits
) -> Tuple[float, float, float]:
    """
    Clamp rotation to limits.

    Args:
        rotation: Euler rotation (x, y, z) in radians
        limits: Rotation limits

    Returns:
        Clamped rotation in radians
    """
    clamped = list(rotation)

    if limits.use_limits_x:
        clamped[0] = max(math.radians(limits.x_min),
                        min(math.radians(limits.x_max), rotation[0]))
    if limits.use_limits_y:
        clamped[1] = max(math.radians(limits.y_min),
                        min(math.radians(limits.y_max), rotation[1]))
    if limits.use_limits_z:
        clamped[2] = max(math.radians(limits.z_min),
                        min(math.radians(limits.z_max), rotation[2]))

    return tuple(clamped)


# Convenience exports
__all__ = [
    'RotationLimitEnforcer',
    'RotationLimits',
    'apply_joint_limits',
    'clamp_rotation',
]
