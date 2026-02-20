"""
Pose Blending Module

Multi-pose blending and transitions for character animation.

Phase 13.2: Pose Library (REQ-ANIM-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from .types import Pose, BonePose, PoseBlendMode, PoseBlendConfig
from .pose_library import PoseLibrary

if TYPE_CHECKING:
    import bpy


class PoseBlender:
    """
    Blends multiple poses together for animation.

    Supports REPLACE, ADD, and MIX blend modes for combining
    poses with weighted blending.
    """

    def __init__(self, armature: Any, rig_type: str = "human_biped"):
        """
        Initialize pose blender.

        Args:
            armature: Blender armature object
            rig_type: Type of rig for pose matching
        """
        self.armature = armature
        self.library = PoseLibrary(rig_type)

    def blend_poses(
        self,
        pose_weights: List[Tuple[str, float]],
        blend_mode: PoseBlendMode = PoseBlendMode.MIX,
        bones: Optional[List[str]] = None
    ) -> None:
        """
        Blend multiple poses with weights.

        Args:
            pose_weights: List of (pose_id, weight) tuples
            blend_mode: How to blend poses
            bones: Specific bones to affect (None = all)
        """
        if not pose_weights:
            return

        # Filter valid poses
        valid_poses = []
        for pose_id, weight in pose_weights:
            pose = self.library.load_pose(pose_id)
            if pose:
                valid_poses.append((pose, weight))

        if not valid_poses:
            return

        # Normalize weights
        total_weight = sum(w for _, w in valid_poses)
        if total_weight > 0:
            valid_poses = [(p, w / total_weight) for p, w in valid_poses]

        if blend_mode == PoseBlendMode.REPLACE:
            # Start from rest pose
            self._reset_to_rest(bones)

        # Collect all bones to affect
        all_bone_names = set()
        for pose, _ in valid_poses:
            all_bone_names.update(pose.bones.keys())

        if bones:
            all_bone_names = all_bone_names.intersection(bones)

        # Blend each bone
        for bone_name in all_bone_names:
            if bone_name not in self.armature.pose.bones:
                continue

            blended = self._blend_bone(bone_name, valid_poses, blend_mode)
            if blended:
                self._apply_blended_bone(bone_name, blended)

    def _blend_bone(
        self,
        bone_name: str,
        pose_weights: List[Tuple[Pose, float]],
        blend_mode: PoseBlendMode
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate blended values for a single bone.

        Args:
            bone_name: Name of bone
            pose_weights: List of (pose, weight) tuples
            blend_mode: Blend mode

        Returns:
            Dictionary with blended location, rotation, scale or None
        """
        # Get current bone state for additive blending
        pb = self.armature.pose.bones.get(bone_name)
        if not pb:
            return None

        current = {
            'location': list(pb.location),
            'rotation': list(pb.rotation_euler),
            'scale': list(pb.scale)
        }

        # Initialize blended values
        if blend_mode == PoseBlendMode.ADD:
            blended = current.copy()
        else:
            blended = {
                'location': [0.0, 0.0, 0.0],
                'rotation': [0.0, 0.0, 0.0],
                'scale': [1.0, 1.0, 1.0]
            }

        # Accumulate weighted values
        for pose, weight in pose_weights:
            if bone_name not in pose.bones:
                continue

            bone_pose = pose.bones[bone_name]

            if blend_mode == PoseBlendMode.ADD:
                # Add weighted rotation
                target_rot = [math.radians(a) for a in bone_pose.rotation]
                for i in range(3):
                    blended['rotation'][i] += target_rot[i] * weight
            else:
                # Mix weighted values
                for i in range(3):
                    blended['location'][i] += bone_pose.location[i] * weight
                    target_rot = math.radians(bone_pose.rotation[i])
                    blended['rotation'][i] += target_rot * weight
                    blended['scale'][i] += (bone_pose.scale[i] - 1.0) * weight + (
                        1.0 if blended['scale'][i] == 1.0 else 0
                    )

        return blended

    def _apply_blended_bone(self, bone_name: str, blended: Dict[str, Any]) -> None:
        """Apply blended values to a bone."""
        pb = self.armature.pose.bones.get(bone_name)
        if not pb:
            return

        pb.location = blended['location']
        pb.rotation_euler = blended['rotation']
        pb.scale = blended['scale']

    def _reset_to_rest(self, bones: Optional[List[str]] = None) -> None:
        """Reset bones to rest pose."""
        for bone_name, pb in self.armature.pose.bones.items():
            if bones and bone_name not in bones:
                continue

            pb.location = (0.0, 0.0, 0.0)
            pb.rotation_euler = (0.0, 0.0, 0.0)
            pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            pb.scale = (1.0, 1.0, 1.0)

    def blend_with_current(
        self,
        pose_id: str,
        weight: float,
        bones: Optional[List[str]] = None
    ) -> None:
        """
        Blend a pose with the current pose.

        Args:
            pose_id: Pose to blend
            weight: Blend weight (0 = current, 1 = pose)
            bones: Specific bones to affect
        """
        pose = self.library.load_pose(pose_id)
        if not pose:
            return

        self.library.apply_pose(self.armature, pose, weight, bones)

    def additive_pose(
        self,
        pose_id: str,
        weight: float = 1.0,
        bones: Optional[List[str]] = None
    ) -> None:
        """
        Add pose values on top of current pose.

        Args:
            pose_id: Pose to add
            weight: Additive weight
            bones: Specific bones to affect
        """
        pose = self.library.load_pose(pose_id)
        if not pose:
            return

        target_bones = bones or list(pose.bones.keys())

        for bone_name in target_bones:
            if bone_name not in self.armature.pose.bones:
                continue
            if bone_name not in pose.bones:
                continue

            pb = self.armature.pose.bones[bone_name]
            bone_pose = pose.bones[bone_name]

            # Add rotation
            target_euler = [math.radians(a) for a in bone_pose.rotation]
            pb.rotation_euler = [
                pb.rotation_euler[i] + target_euler[i] * weight
                for i in range(3)
            ]

    def blend_two_poses(
        self,
        pose_a_id: str,
        pose_b_id: str,
        blend: float,
        bones: Optional[List[str]] = None
    ) -> None:
        """
        Blend between two poses.

        Args:
            pose_a_id: First pose (blend = 0)
            pose_b_id: Second pose (blend = 1)
            blend: Blend factor (0-1)
            bones: Specific bones to affect
        """
        self.blend_poses([
            (pose_a_id, 1.0 - blend),
            (pose_b_id, blend)
        ], PoseBlendMode.MIX, bones)

    def create_pose_transition(
        self,
        start_pose_id: str,
        end_pose_id: str,
        start_frame: int,
        end_frame: int,
        bones: Optional[List[str]] = None
    ) -> None:
        """
        Create a pose-to-pose transition with keyframes.

        Args:
            start_pose_id: Starting pose
            end_pose_id: Ending pose
            start_frame: Start frame number
            end_frame: End frame number
            bones: Specific bones to affect
        """
        # Apply start pose and keyframe
        self.blend_poses([(start_pose_id, 1.0)], PoseBlendMode.REPLACE, bones)
        self._keyframe_bones(start_frame, bones)

        # Apply end pose and keyframe
        self.blend_poses([(end_pose_id, 1.0)], PoseBlendMode.REPLACE, bones)
        self._keyframe_bones(end_frame, bones)

    def _keyframe_bones(self, frame: int, bones: Optional[List[str]] = None) -> None:
        """Keyframe bones at the current frame."""
        target_bones = bones or list(self.armature.pose.bones.keys())

        for bone_name in target_bones:
            if bone_name not in self.armature.pose.bones:
                continue

            pb = self.armature.pose.bones[bone_name]
            pb.keyframe_insert(data_path="location", frame=frame)
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)
            pb.keyframe_insert(data_path="scale", frame=frame)

    def apply_blend_config(self, config: PoseBlendConfig) -> None:
        """
        Apply a blend configuration.

        Args:
            config: PoseBlendConfig to apply
        """
        self.blend_poses(
            config.poses,
            config.blend_mode,
            config.affected_bones
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def blend_two_poses(
    armature: Any,
    pose_a: str,
    pose_b: str,
    blend: float
) -> None:
    """
    Blend between two poses (0 = A, 1 = B).

    Args:
        armature: Blender armature object
        pose_a: First pose ID
        pose_b: Second pose ID
        blend: Blend factor (0-1)
    """
    blender = PoseBlender(armature)
    blender.blend_two_poses(pose_a, pose_b, blend)


def blend_multiple_poses(
    armature: Any,
    pose_weights: List[Tuple[str, float]],
    blend_mode: str = "mix"
) -> None:
    """
    Blend multiple poses together.

    Args:
        armature: Blender armature object
        pose_weights: List of (pose_id, weight) tuples
        blend_mode: "mix", "replace", or "add"
    """
    mode = PoseBlendMode(blend_mode) if blend_mode in [m.value for m in PoseBlendMode] else PoseBlendMode.MIX
    blender = PoseBlender(armature)
    blender.blend_poses(pose_weights, mode)


def apply_pose_blend(
    armature: Any,
    pose_id: str,
    weight: float
) -> None:
    """
    Blend a pose with the current pose.

    Args:
        armature: Blender armature object
        pose_id: Pose ID
        weight: Blend weight (0 = current, 1 = pose)
    """
    blender = PoseBlender(armature)
    blender.blend_with_current(pose_id, weight)


def create_pose_transition(
    armature: Any,
    start_pose: str,
    end_pose: str,
    start_frame: int,
    end_frame: int
) -> None:
    """
    Create a pose-to-pose transition with keyframes.

    Args:
        armature: Blender armature object
        start_pose: Starting pose ID
        end_pose: Ending pose ID
        start_frame: Start frame number
        end_frame: End frame number
    """
    blender = PoseBlender(armature)
    blender.create_pose_transition(start_pose, end_pose, start_frame, end_frame)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'PoseBlender',
    'blend_two_poses',
    'blend_multiple_poses',
    'apply_pose_blend',
    'create_pose_transition',
]
