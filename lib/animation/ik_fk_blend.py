"""
IK/FK Blend Module

Seamless blending between IK and FK modes for limbs.

Phase 13.1: IK/FK System (REQ-ANIM-02, REQ-ANIM-03)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from .types import IKFKBlendConfig, IKConfig, FKConfig

if TYPE_CHECKING:
    import bpy


class IKFKBlender:
    """
    Manages seamless blending between IK and FK modes.

    Provides methods for:
    - Blending between IK and FK control
    - Snapping IK to FK position and vice versa
    - Keyframing blend transitions
    """

    def __init__(self, armature: Any, config: Optional[IKFKBlendConfig] = None):
        """
        Initialize IK/FK blender.

        Args:
            armature: Blender armature object
            config: Optional blend configuration
        """
        self.armature = armature
        self.config = config
        self._blend_factor = config.default_blend if config else 1.0

        # Store bone rotation data for snapping
        self._fk_rotations: Dict[str, Tuple[float, float, float]] = {}
        self._ik_rotations: Dict[str, Tuple[float, float, float]] = {}

    def set_blend_factor(self, factor: float) -> None:
        """
        Set blend factor between IK and FK.

        Args:
            factor: Blend factor (0.0 = FK, 1.0 = IK)
        """
        self._blend_factor = max(0.0, min(1.0, factor))

        if self.config is None:
            return

        # Update IK constraint influence
        from .ik_system import IKSystem
        ik_system = IKSystem(self.armature)

        # Get the IK bone (last in chain)
        if self.config.ik_chain:
            ik_bone = self.config.ik_chain[-1]
            constraint = ik_system.get_ik_constraint(self.armature, ik_bone)

            if constraint:
                constraint.influence = self._blend_factor

        # Update any copy rotation constraints on FK bones
        # that copy from IK bones
        self._update_copy_constraints()

    def get_blend_factor(self) -> float:
        """
        Get current blend factor.

        Returns:
            Blend factor (0.0 = FK, 1.0 = IK)
        """
        return self._blend_factor

    def _update_copy_constraints(self) -> None:
        """Update copy constraint influences based on blend factor."""
        if self.config is None:
            return

        # For each bone in the FK chain, update any copy rotation constraints
        # from IK bones
        for i, fk_bone_name in enumerate(self.config.fk_chain):
            if i >= len(self.config.ik_chain):
                break

            ik_bone_name = self.config.ik_chain[i]
            fk_bone = self.armature.pose.bones.get(fk_bone_name)

            if fk_bone is None:
                continue

            # Find copy rotation constraints from IK bones
            for constraint in fk_bone.constraints:
                if constraint.type == 'COPY_ROTATION':
                    if constraint.subtarget == ik_bone_name:
                        # Blend factor controls constraint influence
                        constraint.influence = self._blend_factor

    def snap_to_ik(self) -> None:
        """
        Snap FK bones to match IK bone positions.

        This is used when switching from FK to IK mode.
        """
        if self.config is None:
            return

        from .fk_system import FKSystem
        fk_system = FKSystem(self.armature)

        # Get IK bone rotations and apply to FK bones
        for i, fk_bone_name in enumerate(self.config.fk_chain):
            if i >= len(self.config.ik_chain):
                break

            ik_bone_name = self.config.ik_chain[i]
            ik_bone = self.armature.pose.bones.get(ik_bone_name)
            fk_bone = self.armature.pose.bones.get(fk_bone_name)

            if ik_bone is None or fk_bone is None:
                continue

            # Store FK rotation before snap
            self._fk_rotations[fk_bone_name] = tuple(fk_bone.rotation_euler)

            # Copy IK rotation to FK
            fk_system.set_rotation(
                self.armature,
                fk_bone_name,
                tuple(ik_bone.rotation_euler)
            )

    def snap_to_fk(self) -> None:
        """
        Snap IK target to match FK bone positions.

        This is used when switching from IK to FK mode.
        """
        if self.config is None:
            return

        import bpy

        # Get the end effector position from FK chain
        if not self.config.fk_chain:
            return

        # Get last FK bone world position
        last_fk_bone = self.config.fk_chain[-1]
        fk_bone = self.armature.pose.bones.get(last_fk_bone)

        if fk_bone is None:
            return

        # Calculate world position of bone tail
        world_matrix = self.armature.matrix_world @ fk_bone.matrix
        tail_world = world_matrix @ bpy.mathutils.Vector((0, fk_bone.length, 0))

        # Move IK target to this position
        if self.config.ik_target:
            ik_target = bpy.data.objects.get(self.config.ik_target)
            if ik_target:
                ik_target.location = tail_world
            elif self.config.ik_target in self.armature.pose.bones:
                # It's a bone - create or find control object
                control_bone = self.armature.pose.bones.get(self.config.ik_target)
                if control_bone:
                    control_bone.location = fk_bone.tail

    def store_current_state(self) -> Dict[str, Any]:
        """
        Store current bone states for later restoration.

        Returns:
            Dictionary of bone states
        """
        if self.config is None:
            return {}

        state = {
            'blend_factor': self._blend_factor,
            'ik_rotations': {},
            'fk_rotations': {},
        }

        # Store IK bone rotations
        for bone_name in self.config.ik_chain:
            bone = self.armature.pose.bones.get(bone_name)
            if bone:
                state['ik_rotations'][bone_name] = tuple(bone.rotation_euler)

        # Store FK bone rotations
        for bone_name in self.config.fk_chain:
            bone = self.armature.pose.bones.get(bone_name)
            if bone:
                state['fk_rotations'][bone_name] = tuple(bone.rotation_euler)

        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore bone states from stored data.

        Args:
            state: Dictionary of bone states from store_current_state()
        """
        if not state:
            return

        from .fk_system import FKSystem
        fk_system = FKSystem(self.armature)

        # Restore blend factor
        if 'blend_factor' in state:
            self.set_blend_factor(state['blend_factor'])

        # Restore IK rotations
        for bone_name, rotation in state.get('ik_rotations', {}).items():
            bone = self.armature.pose.bones.get(bone_name)
            if bone:
                bone.rotation_euler = rotation

        # Restore FK rotations
        for bone_name, rotation in state.get('fk_rotations', {}).items():
            fk_system.set_rotation(self.armature, bone_name, rotation)

    def keyframe_blend(
        self,
        frame: int,
        factor: float,
        add_snap_keyframes: bool = True
    ) -> None:
        """
        Keyframe blend factor change at a specific frame.

        Optionally adds snap keyframes to prevent jumping.

        Args:
            frame: Frame number
            factor: Target blend factor
            add_snap_keyframes: Add snap keyframes to prevent jumps
        """
        if self.config is None:
            return

        import bpy

        # If transitioning between modes, snap first
        current_is_ik = self._blend_factor > 0.5
        target_is_ik = factor > 0.5

        if add_snap_keyframes and current_is_ik != target_is_ik:
            # Snap to target mode first
            if target_is_ik:
                self.snap_to_ik()
            else:
                self.snap_to_fk()

            # Keyframe all bone rotations at this frame
            bpy.context.scene.frame_set(frame - 1)

            for bone_name in self.config.fk_chain:
                bone = self.armature.pose.bones.get(bone_name)
                if bone:
                    bone.keyframe_insert(data_path="rotation_euler", frame=frame - 1)

            for bone_name in self.config.ik_chain:
                bone = self.armature.pose.bones.get(bone_name)
                if bone:
                    bone.keyframe_insert(data_path="rotation_euler", frame=frame - 1)

        # Set blend factor
        self.set_blend_factor(factor)

        # Keyframe IK constraint influence
        bpy.context.scene.frame_set(frame)

        from .ik_system import IKSystem
        ik_system = IKSystem(self.armature)

        if self.config.ik_chain:
            ik_bone = self.config.ik_chain[-1]
            constraint = ik_system.get_ik_constraint(self.armature, ik_bone)

            if constraint:
                # Keyframe constraint influence
                constraint.keyframe_insert(data_path="influence", frame=frame)

    def create_blend_property(self) -> None:
        """
        Create custom property on armature for blend factor.

        This creates a slider property that can be animated.
        """
        if self.config is None:
            return

        prop_name = self.config.blend_property

        # Create custom property
        self.armature[prop_name] = self._blend_factor

        # Add property with UI limits
        import bpy

        # Using RNA properties for better UI
        if not hasattr(self.armature, 'rna_type'):
            return

        # Set min/max via ID property
        self.armature.id_properties_ui(prop_name).update(
            min=0.0,
            max=1.0,
            soft_min=0.0,
            soft_max=1.0,
            step=0.1,
            default=self._blend_factor,
        )


def create_ikfk_setup(
    armature: Any,
    ik_chain: List[str],
    fk_chain: List[str],
    ik_target: str,
    pole_target: Optional[str] = None,
    name: str = "ikfk_blend"
) -> IKFKBlender:
    """
    Convenience function to create IK/FK blend setup.

    Args:
        armature: Blender armature object
        ik_chain: IK bone chain (e.g., ["upper_arm_L", "lower_arm_L"])
        fk_chain: FK bone chain (e.g., ["upper_arm_fk_L", "lower_arm_fk_L"])
        ik_target: IK target control name
        pole_target: Optional pole target name
        name: Name for this blend setup

    Returns:
        Configured IKFKBlender instance
    """
    config = IKFKBlendConfig(
        name=name,
        ik_chain=ik_chain,
        fk_chain=fk_chain,
        ik_target=ik_target,
        pole_target=pole_target,
    )

    blender = IKFKBlender(armature, config)
    blender.create_blend_property()

    return blender


def blend_to_ik(armature: Any, setup_name: str, duration_frames: int = 10) -> None:
    """
    Animate blend from FK to IK over specified frames.

    Args:
        armature: Blender armature object
        setup_name: Name of IK/FK setup
        duration_frames: Number of frames for transition
    """
    import bpy

    current_frame = bpy.context.scene.frame_current

    # Create blender with config
    config = IKFKBlendConfig(
        name=setup_name,
        ik_chain=[],
        fk_chain=[],
        ik_target="",
    )

    blender = IKFKBlender(armature, config)

    # Snap and keyframe
    blender.keyframe_blend(current_frame, 0.0, add_snap_keyframes=True)  # Start FK
    blender.keyframe_blend(current_frame + duration_frames, 1.0, add_snap_keyframes=False)  # End IK


def blend_to_fk(armature: Any, setup_name: str, duration_frames: int = 10) -> None:
    """
    Animate blend from IK to FK over specified frames.

    Args:
        armature: Blender armature object
        setup_name: Name of IK/FK setup
        duration_frames: Number of frames for transition
    """
    import bpy

    current_frame = bpy.context.scene.frame_current

    # Create blender with config
    config = IKFKBlendConfig(
        name=setup_name,
        ik_chain=[],
        fk_chain=[],
        ik_target="",
    )

    blender = IKFKBlender(armature, config)

    # Snap and keyframe
    blender.keyframe_blend(current_frame, 1.0, add_snap_keyframes=True)  # Start IK
    blender.keyframe_blend(current_frame + duration_frames, 0.0, add_snap_keyframes=False)  # End FK


def get_snap_rotation(
    armature: Any,
    source_bone: str,
    target_bone: str
) -> Tuple[float, float, float]:
    """
    Calculate rotation for target bone to match source bone.

    Args:
        armature: Blender armature object
        source_bone: Source bone name
        target_bone: Target bone name

    Returns:
        Euler rotation to apply to target
    """
    source = armature.pose.bones.get(source_bone)
    target = armature.pose.bones.get(target_bone)

    if source is None or target is None:
        return (0.0, 0.0, 0.0)

    # Get world rotations
    source_world = (armature.matrix_world @ source.matrix).to_euler()
    target_world = (armature.matrix_world @ target.matrix).to_euler()

    # Calculate difference
    diff = (
        source_world.x - target_world.x,
        source_world.y - target_world.y,
        source_world.z - target_world.z,
    )

    return diff


# Convenience exports
__all__ = [
    'IKFKBlender',
    'IKFKBlendConfig',
    'create_ikfk_setup',
    'blend_to_ik',
    'blend_to_fk',
    'get_snap_rotation',
]
