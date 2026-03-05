"""
Folding pose system for arm articulation.

This module provides pose management for arm folding sequences,
enabling smooth transitions between deployed and folded states.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional


class FoldingPoseState(Enum):
    """States for arm folding sequence."""
    DEPLOYED = "deployed"      # Arm is extended and ready
    FOLDING = "folding"        # Arm is in transition to folded
    FOLDED = "folded"          # Arm is compactly stored
    DEPLOYING = "deploying"    # Arm is extending from folded


@dataclass
class FoldingConfig:
    """Configuration for arm folding behavior."""
    arm_index: int
    folded_angles: Dict[int, float] = field(default_factory=dict)
    deployed_angles: Dict[int, float] = field(default_factory=dict)
    transition_duration: float = 0.0  # seconds

    def get_angle_difference(self, joint_id: int) -> float:
        """Get the angle difference between folded and deployed for a joint."""
        if joint_id in self.folded_angles and joint_id in self.deployed_angles:
            return self.deployed_angles[joint_id] - self.folded_angles[joint_id]
        return 0.0


class FoldingPose:
    """
    Represents the current folding state of an arm.

    Manages joint angles and interpolation between folding poses.
    """

    def __init__(
        self,
        current_pose: FoldingPoseState = FoldingPoseState.DEPLOYED,
        progress: float = 0.0,
        joint_angles: Optional[Dict[int, float]] = None
    ):
        """
        Initialize folding pose.

        Args:
            current_pose: Current folding state
            progress: Animation progress (0.0 to 1.0)
            joint_angles: Current joint angles by joint ID
        """
        self.current_pose = current_pose
        self.progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
        self.joint_angles = joint_angles if joint_angles is not None else {}

    def interpolate_to(
        self,
        target_pose: FoldingPoseState,
        target_angles: Dict[int, float],
        t: float
    ) -> 'FoldingPose':
        """
        Interpolate towards a target pose.

        Args:
            target_pose: Target folding state
            target_angles: Target joint angles
            t: Interpolation parameter (0.0 to 1.0)

        Returns:
            New FoldingPose with interpolated values
        """
        t = max(0.0, min(1.0, t))  # Clamp t

        interpolated_angles = {}
        for joint_id, target_angle in target_angles.items():
            if joint_id in self.joint_angles:
                current_angle = self.joint_angles[joint_id]
                interpolated_angles[joint_id] = (
                    current_angle + (target_angle - current_angle) * t
                )
            else:
                interpolated_angles[joint_id] = target_angle

        # Update state based on target
        new_pose = FoldingPoseState.DEPLOYED
        if target_pose == FoldingPoseState.FOLDED:
            if t < 1.0:
                new_pose = FoldingPoseState.FOLDING
            else:
                new_pose = FoldingPoseState.FOLDED
        elif target_pose == FoldingPoseState.DEPLOYED:
            if t < 1.0:
                new_pose = FoldingPoseState.DEPLOYING
            else:
                new_pose = FoldingPoseState.DEPLOYED

        return FoldingPose(
            current_pose=new_pose,
            progress=t,
            joint_angles=interpolated_angles
        )

    def get_joint_angle(self, joint_id: int) -> float:
        """
        Get the angle for a specific joint.

        Args:
            joint_id: ID of the joint

        Returns:
            Joint angle, or 0.0 if not found
        """
        return self.joint_angles.get(joint_id, 0.0)

    def is_complete(self) -> bool:
        """
        Check if the current pose transition is complete.

        Returns:
            True if in FOLDED or DEPLOYED state (not transitioning)
        """
        return self.current_pose in (
            FoldingPoseState.FOLDED,
            FoldingPoseState.DEPLOYED
        )

    def __repr__(self) -> str:
        return (
            f"FoldingPose(state={self.current_pose.value}, "
            f"progress={self.progress:.2f}, "
            f"joints={len(self.joint_angles)})"
        )
