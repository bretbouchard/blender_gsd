"""
Folding animator for smooth arm transitions.

This module provides animation control for arm folding sequences,
including easing functions and state management.
"""

from typing import Dict, List, Optional, Callable
from .pose import FoldingPose, FoldingPoseState, FoldingConfig


# Easing functions for smooth animations
def ease_linear(t: float) -> float:
    """Linear easing (no easing)."""
    return t


def ease_in_out(t: float) -> float:
    """Smooth ease-in-out using smoothstep."""
    return t * t * (3.0 - 2.0 * t)


def ease_smooth(t: float) -> float:
    """Smoother easing using smootherstep."""
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


# Easing function registry
EASING_FUNCTIONS: Dict[str, Callable[[float], float]] = {
    "linear": ease_linear,
    "ease_in_out": ease_in_out,
    "smooth": ease_smooth,
}


class FoldingAnimator:
    """
    Animates arm folding sequences with smooth transitions.

    Manages multiple arms folding and deploying concurrently.
    """

    def __init__(
        self,
        folding_configs: Optional[Dict[int, FoldingConfig]] = None,
        transition_easing: str = "ease_in_out"
    ):
        """
        Initialize the folding animator.

        Args:
            folding_configs: Mapping of arm_index to FoldingConfig
            transition_easing: Easing function name ("linear", "ease_in_out", "smooth")
        """
        self.folding_configs = folding_configs or {}
        self.transition_easing = transition_easing

        # Current animation states
        self._arm_poses: Dict[int, FoldingPose] = {}
        self._animation_timers: Dict[int, float] = {}

        # Initialize all arms to deployed state
        for arm_index in self.folding_configs:
            config = self.folding_configs[arm_index]
            self._arm_poses[arm_index] = FoldingPose(
                current_pose=FoldingPoseState.DEPLOYED,
                progress=1.0,
                joint_angles=config.deployed_angles.copy()
            )
            self._animation_timers[arm_index] = 0.0

    def fold_arm(self, arm_index: int) -> None:
        """
        Initiate folding animation for an arm.

        Args:
            arm_index: Index of the arm to fold

        Raises:
            KeyError: If arm_index not in folding_configs
        """
        if arm_index not in self.folding_configs:
            raise KeyError(f"No folding config for arm {arm_index}")

        current_pose = self._arm_poses.get(arm_index)
        if current_pose and current_pose.current_pose in (
            FoldingPoseState.FOLDING,
            FoldingPoseState.FOLDED
        ):
            return  # Already folding or folded

        # Start folding animation
        self._arm_poses[arm_index] = FoldingPose(
            current_pose=FoldingPoseState.FOLDING,
            progress=0.0,
            joint_angles=current_pose.joint_angles if current_pose else {}
        )
        self._animation_timers[arm_index] = 0.0

    def deploy_arm(self, arm_index: int) -> None:
        """
        Initiate deployment animation for an arm.

        Args:
            arm_index: Index of the arm to deploy

        Raises:
            KeyError: If arm_index not in folding_configs
        """
        if arm_index not in self.folding_configs:
            raise KeyError(f"No folding config for arm {arm_index}")

        current_pose = self._arm_poses.get(arm_index)
        if current_pose and current_pose.current_pose in (
            FoldingPoseState.DEPLOYING,
            FoldingPoseState.DEPLOYED
        ):
            return  # Already deploying or deployed

        # Start deployment animation
        self._arm_poses[arm_index] = FoldingPose(
            current_pose=FoldingPoseState.DEPLOYING,
            progress=0.0,
            joint_angles=current_pose.joint_angles if current_pose else {}
        )
        self._animation_timers[arm_index] = 0.0

    def update(self, dt: float) -> Dict[int, FoldingPose]:
        """
        Advance all animations by dt seconds.

        Args:
            dt: Time delta in seconds

        Returns:
            Dictionary of arm_index to current FoldingPose
        """
        easing_func = EASING_FUNCTIONS.get(
            self.transition_easing,
            ease_in_out
        )

        for arm_index, config in self.folding_configs.items():
            pose = self._arm_poses.get(arm_index)
            if not pose or pose.is_complete():
                continue

            # Update animation timer
            self._animation_timers[arm_index] += dt

            # Calculate progress
            if config.transition_duration > 0:
                t = self._animation_timers[arm_index] / config.transition_duration
            else:
                t = 1.0  # Instant transition

            # Apply easing
            eased_t = easing_func(min(t, 1.0))

            # Determine target
            if pose.current_pose == FoldingPoseState.FOLDING:
                target_state = FoldingPoseState.FOLDED
                target_angles = config.folded_angles
            else:  # DEPLOYING
                target_state = FoldingPoseState.DEPLOYED
                target_angles = config.deployed_angles

            # Interpolate
            self._arm_poses[arm_index] = pose.interpolate_to(
                target_state,
                target_angles,
                eased_t
            )

        return self._arm_poses.copy()

    def get_folded_positions(self) -> List[int]:
        """
        Get indices of arms in FOLDED state.

        Returns:
            List of arm indices that are fully folded
        """
        return [
            idx for idx, pose in self._arm_poses.items()
            if pose.current_pose == FoldingPoseState.FOLDED
        ]

    def get_deployed_positions(self) -> List[int]:
        """
        Get indices of arms in DEPLOYED state.

        Returns:
            List of arm indices that are fully deployed
        """
        return [
            idx for idx, pose in self._arm_poses.items()
            if pose.current_pose == FoldingPoseState.DEPLOYED
        ]

    def get_pose(self, arm_index: int) -> Optional[FoldingPose]:
        """
        Get the current pose for an arm.

        Args:
            arm_index: Index of the arm

        Returns:
            Current FoldingPose, or None if arm not found
        """
        return self._arm_poses.get(arm_index)

    def is_animating(self, arm_index: int) -> bool:
        """
        Check if an arm is currently animating.

        Args:
            arm_index: Index of the arm

        Returns:
            True if arm is in transition (FOLDING or DEPLOYING)
        """
        pose = self._arm_poses.get(arm_index)
        return pose is not None and not pose.is_complete()

    def __repr__(self) -> str:
        folded = len(self.get_folded_positions())
        deployed = len(self.get_deployed_positions())
        total = len(self.folding_configs)
        return (
            f"FoldingAnimator(arms={total}, "
            f"folded={folded}, deployed={deployed})"
        )
