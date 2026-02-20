"""
Pose Utilities Module

Mirror, flip, and conversion utilities for poses.

Phase 13.2: Pose Library (REQ-ANIM-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import math

from .types import Pose, BonePose, PoseMirrorAxis, PoseCategory

if TYPE_CHECKING:
    import bpy


class PoseMirror:
    """
    Mirror poses between left and right sides.

    Supports mirroring across X, Y, or Z axis with automatic
    bone name detection for L/R pairs.
    """

    # Common bone name patterns for L/R detection
    LEFT_PATTERNS = ['_L', '.L', '_left', '.left', 'left_', 'left.']
    RIGHT_PATTERNS = ['_R', '.R', '_right', '.right', 'right_', 'right.']

    @staticmethod
    def get_mirror_bone_name(bone_name: str) -> str:
        """
        Get the mirrored bone name.

        Args:
            bone_name: Original bone name

        Returns:
            Mirrored bone name (or original if not L/R pattern)
        """
        for left, right in zip(PoseMirror.LEFT_PATTERNS, PoseMirror.RIGHT_PATTERNS):
            if left in bone_name:
                return bone_name.replace(left, right)
            if right in bone_name:
                return bone_name.replace(right, left)

        return bone_name

    @staticmethod
    def is_left_bone(bone_name: str) -> bool:
        """Check if bone is a left-side bone."""
        for pattern in PoseMirror.LEFT_PATTERNS:
            if pattern in bone_name:
                return True
        return False

    @staticmethod
    def is_right_bone(bone_name: str) -> bool:
        """Check if bone is a right-side bone."""
        for pattern in PoseMirror.RIGHT_PATTERNS:
            if pattern in bone_name:
                return True
        return False

    @staticmethod
    def mirror_rotation(
        rotation: Tuple[float, float, float],
        axis: PoseMirrorAxis = PoseMirrorAxis.X
    ) -> Tuple[float, float, float]:
        """
        Mirror rotation values.

        Args:
            rotation: Euler rotation in degrees
            axis: Mirror axis

        Returns:
            Mirrored rotation
        """
        x, y, z = rotation

        if axis == PoseMirrorAxis.X:
            # Mirror across X (invert X and Z)
            return (-x, y, -z)
        elif axis == PoseMirrorAxis.Y:
            # Mirror across Y (invert Y and Z)
            return (x, -y, -z)
        else:  # Z
            # Mirror across Z (invert X and Y)
            return (-x, -y, z)

    @staticmethod
    def mirror_location(
        location: Tuple[float, float, float],
        axis: PoseMirrorAxis = PoseMirrorAxis.X
    ) -> Tuple[float, float, float]:
        """
        Mirror location values.

        Args:
            location: Location values
            axis: Mirror axis

        Returns:
            Mirrored location
        """
        x, y, z = location
        values = [x, y, z]
        idx = {'x': 0, 'y': 1, 'z': 2}[axis.value]
        values[idx] = -values[idx]
        return tuple(values)

    @staticmethod
    def mirror_pose(
        pose: Pose,
        axis: PoseMirrorAxis = PoseMirrorAxis.X
    ) -> Pose:
        """
        Create a mirrored version of a pose.

        Args:
            pose: Original pose
            axis: Mirror axis

        Returns:
            New mirrored Pose object
        """
        mirrored_bones: Dict[str, BonePose] = {}

        for bone_name, bone_pose in pose.bones.items():
            mirror_name = PoseMirror.get_mirror_bone_name(bone_name)

            mirrored_bones[mirror_name] = BonePose(
                location=PoseMirror.mirror_location(bone_pose.location, axis),
                rotation=PoseMirror.mirror_rotation(bone_pose.rotation, axis),
                rotation_quat=bone_pose.rotation_quat,  # Quaternion mirroring is complex
                scale=bone_pose.scale,
                rotation_mode=bone_pose.rotation_mode
            )

        return Pose(
            id=f"{pose.id}_mirrored",
            name=f"{pose.name} (Mirrored)",
            category=pose.category,
            rig_type=pose.rig_type,
            description=f"Mirrored version of {pose.name}",
            bones=mirrored_bones,
            tags=pose.tags + ['mirrored'],
            metadata={**pose.metadata, 'mirrored_from': pose.id}
        )

    @staticmethod
    def apply_mirrored_pose(
        armature: Any,
        pose: Pose,
        side: str = 'both',
        axis: PoseMirrorAxis = PoseMirrorAxis.X
    ) -> None:
        """
        Apply a pose mirrored to the opposite side.

        Args:
            armature: Blender armature object
            pose: Pose to apply
            side: 'left', 'right', or 'both'
            axis: Mirror axis
        """
        for bone_name, bone_pose in pose.bones.items():
            mirror_name = PoseMirror.get_mirror_bone_name(bone_name)

            # Determine which side to apply to
            apply_bones = []
            if side == 'both':
                apply_bones = [bone_name, mirror_name]
            elif side == 'left' and PoseMirror.is_left_bone(bone_name):
                apply_bones = [bone_name]
            elif side == 'right' and PoseMirror.is_right_bone(bone_name):
                apply_bones = [bone_name]

            for target_bone in apply_bones:
                if target_bone not in armature.pose.bones:
                    continue

                pb = armature.pose.bones[target_bone]

                # Check if this is the mirrored side
                is_mirror = (target_bone != bone_name)

                if is_mirror:
                    # Apply mirrored values
                    pb.location = PoseMirror.mirror_location(bone_pose.location, axis)
                    pb.rotation_euler = [
                        math.radians(a) for a in PoseMirror.mirror_rotation(bone_pose.rotation, axis)
                    ]
                else:
                    # Apply original values
                    pb.location = bone_pose.location
                    pb.rotation_euler = [math.radians(a) for a in bone_pose.rotation]

                pb.scale = bone_pose.scale

    @staticmethod
    def flip_pose(armature: Any) -> None:
        """
        Flip the current pose (L <-> R).

        Swaps left and right side bone transforms.

        Args:
            armature: Blender armature object
        """
        # Store current pose
        current_pose: Dict[str, Dict[str, Any]] = {}
        for bone_name, pb in armature.pose.bones.items():
            current_pose[bone_name] = {
                'location': tuple(pb.location),
                'rotation': tuple(math.degrees(a) for a in pb.rotation_euler),
                'scale': tuple(pb.scale)
            }

        # Track processed bones to avoid double-flipping
        processed = set()

        # Apply mirrored values
        for bone_name, data in current_pose.items():
            if bone_name in processed:
                continue

            mirror_name = PoseMirror.get_mirror_bone_name(bone_name)

            if mirror_name == bone_name:
                # No mirror (center bone), keep as is
                continue

            if mirror_name not in armature.pose.bones:
                continue

            mirror_pb = armature.pose.bones[mirror_name]

            # Apply mirrored values from original bone
            mirror_pb.location = PoseMirror.mirror_location(data['location'])
            mirror_pb.rotation_euler = [
                math.radians(a) for a in PoseMirror.mirror_rotation(data['rotation'])
            ]
            mirror_pb.scale = data['scale']

            processed.add(bone_name)
            processed.add(mirror_name)


class PoseUtils:
    """General pose utility functions."""

    @staticmethod
    def get_pose_difference(
        pose_a: Pose,
        pose_b: Pose,
        bones: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate the difference between two poses.

        Args:
            pose_a: First pose
            pose_b: Second pose
            bones: Specific bones to compare (None = all common)

        Returns:
            Dictionary of bone name -> difference values
        """
        common_bones = set(pose_a.bones.keys()) & set(pose_b.bones.keys())
        if bones:
            common_bones = common_bones & set(bones)

        differences = {}

        for bone_name in common_bones:
            a = pose_a.bones[bone_name]
            b = pose_b.bones[bone_name]

            diff = {
                'location': tuple(
                    abs(a.location[i] - b.location[i]) for i in range(3)
                ),
                'rotation': tuple(
                    abs(a.rotation[i] - b.rotation[i]) for i in range(3)
                ),
                'scale': tuple(
                    abs(a.scale[i] - b.scale[i]) for i in range(3)
                )
            }

            # Calculate overall magnitude
            diff['location_magnitude'] = math.sqrt(sum(d**2 for d in diff['location']))
            diff['rotation_magnitude'] = math.sqrt(sum(d**2 for d in diff['rotation']))
            diff['scale_magnitude'] = math.sqrt(sum(d**2 for d in diff['scale']))

            differences[bone_name] = diff

        return differences

    @staticmethod
    def extract_pose_bones(
        pose: Pose,
        bone_names: List[str]
    ) -> Pose:
        """
        Extract specific bones from a pose.

        Args:
            pose: Original pose
            bone_names: Bones to extract

        Returns:
            New pose with only specified bones
        """
        extracted_bones = {
            name: pose.bones[name]
            for name in bone_names
            if name in pose.bones
        }

        return Pose(
            id=f"{pose.id}_partial",
            name=f"{pose.name} (Partial)",
            category=pose.category,
            rig_type=pose.rig_type,
            description=f"Partial pose: {', '.join(bone_names[:3])}{'...' if len(bone_names) > 3 else ''}",
            bones=extracted_bones,
            tags=pose.tags + ['partial'],
            affected_bones=bone_names
        )

    @staticmethod
    def combine_poses(
        poses: List[Tuple[Pose, float]]
    ) -> Pose:
        """
        Combine multiple poses into one.

        Args:
            poses: List of (pose, weight) tuples

        Returns:
            Combined pose
        """
        if not poses:
            raise ValueError("No poses to combine")

        if len(poses) == 1:
            return poses[0][0]

        combined_bones: Dict[str, BonePose] = {}

        # Get all bone names
        all_bones = set()
        for pose, _ in poses:
            all_bones.update(pose.bones.keys())

        for bone_name in all_bones:
            loc = [0.0, 0.0, 0.0]
            rot = [0.0, 0.0, 0.0]
            scale = [1.0, 1.0, 1.0]
            total_weight = 0.0

            for pose, weight in poses:
                if bone_name not in pose.bones:
                    continue

                bp = pose.bones[bone_name]
                for i in range(3):
                    loc[i] += bp.location[i] * weight
                    rot[i] += bp.rotation[i] * weight
                    scale[i] += (bp.scale[i] - 1.0) * weight

                total_weight += weight

            if total_weight > 0:
                for i in range(3):
                    loc[i] /= total_weight
                    rot[i] /= total_weight
                    scale[i] = 1.0 + (scale[i] / total_weight)

                combined_bones[bone_name] = BonePose(
                    location=tuple(loc),
                    rotation=tuple(rot),
                    scale=tuple(scale)
                )

        return Pose(
            id="combined_pose",
            name="Combined Pose",
            category=PoseCategory.CUSTOM,
            rig_type=poses[0][0].rig_type,
            description=f"Combination of {len(poses)} poses",
            bones=combined_bones,
            tags=['combined']
        )

    @staticmethod
    def flip_rotation_euler(
        rotation: Tuple[float, float, float],
        from_order: str = "XYZ",
        to_order: str = "XYZ"
    ) -> Tuple[float, float, float]:
        """
        Convert rotation between Euler orders.

        Args:
            rotation: Euler rotation in degrees
            from_order: Source rotation order
            to_order: Target rotation order

        Returns:
            Converted rotation in degrees
        """
        if from_order == to_order:
            return rotation

        # This is a simplified conversion - proper conversion
        # requires matrix decomposition
        # For now, just return as-is (same as Blender's default)
        return rotation


# =============================================================================
# Convenience Functions
# =============================================================================

def mirror_current_pose(armature: Any) -> None:
    """
    Convenience function to mirror current pose (L <-> R).

    Args:
        armature: Blender armature object
    """
    PoseMirror.flip_pose(armature)


def mirror_pose(pose: Pose, axis: str = "x") -> Pose:
    """
    Create a mirrored version of a pose.

    Args:
        pose: Original pose
        axis: Mirror axis ("x", "y", or "z")

    Returns:
        Mirrored pose
    """
    axis_enum = PoseMirrorAxis(axis.lower())
    return PoseMirror.mirror_pose(pose, axis_enum)


def get_mirror_bone_name(bone_name: str) -> str:
    """
    Get the mirrored bone name.

    Args:
        bone_name: Original bone name

    Returns:
        Mirrored bone name
    """
    return PoseMirror.get_mirror_bone_name(bone_name)


def compare_poses(
    pose_a: Pose,
    pose_b: Pose
) -> Dict[str, Dict[str, float]]:
    """
    Compare two poses and get differences.

    Args:
        pose_a: First pose
        pose_b: Second pose

    Returns:
        Dictionary of differences per bone
    """
    return PoseUtils.get_pose_difference(pose_a, pose_b)


def extract_bones_from_pose(
    pose: Pose,
    bone_names: List[str]
) -> Pose:
    """
    Extract specific bones from a pose.

    Args:
        pose: Original pose
        bone_names: Bones to extract

    Returns:
        Partial pose with only specified bones
    """
    return PoseUtils.extract_pose_bones(pose, bone_names)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'PoseMirror',
    'PoseUtils',
    'mirror_current_pose',
    'mirror_pose',
    'get_mirror_bone_name',
    'compare_poses',
    'extract_bones_from_pose',
]
