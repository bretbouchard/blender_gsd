"""
Folding controller for automated arm management.

This module provides automated folding control that integrates
with the tile placement system.
"""

from typing import Dict, List, Optional, Tuple
from .animator import FoldingAnimator
from .pose import FoldingPose, FoldingPoseState


class FoldingController:
    """
    Controls arm folding based on tile placement state.

    Integrates FoldingAnimator with TileRegistry to automate
    arm folding and deployment based on tile events.
    """

    def __init__(
        self,
        animator: FoldingAnimator,
        arm_status: Optional[Dict[int, str]] = None
    ):
        """
        Initialize the folding controller.

        Args:
            animator: FoldingAnimator instance for animation control
            arm_status: Optional initial arm status mapping
        """
        self.animator = animator
        self._arm_status: Dict[int, str] = arm_status or {}

        # Mapping of tile positions to arms
        self._tile_to_arm: Dict[Tuple[int, int], int] = {}
        self._arm_to_tile: Dict[int, Tuple[int, int]] = {}

        # Initialize arm status for all configured arms
        for arm_index in animator.folding_configs.keys():
            if arm_index not in self._arm_status:
                self._arm_status[arm_index] = "idle"

    def on_tile_placed(
        self,
        tile_pos: Tuple[int, int],
        arm_index: int
    ) -> None:
        """
        Handle tile placement event.

        Deploys arm if folded and updates status.

        Args:
            tile_pos: (x, y) position of placed tile
            arm_index: Index of arm that placed the tile
        """
        # Update mappings
        self._tile_to_arm[tile_pos] = arm_index
        self._arm_to_tile[arm_index] = tile_pos

        # Get current status
        current_status = self._arm_status.get(arm_index, "idle")

        # Validate state transition
        if current_status == "busy":
            # Arm is currently placing a tile, transition to idle after
            self._arm_status[arm_index] = "idle"
            return

        # Deploy arm if folded
        pose = self.animator.get_pose(arm_index)
        if pose and pose.current_pose == FoldingPoseState.FOLDED:
            self._arm_status[arm_index] = "deploying"
            self.animator.deploy_arm(arm_index)
        else:
            # Arm already deployed or deploying
            self._arm_status[arm_index] = "busy"

    def on_tile_removed(
        self,
        tile_pos: Tuple[int, int],
        arm_index: int
    ) -> None:
        """
        Handle tile removal event.

        Folds arm if idle and updates status.

        Args:
            tile_pos: (x, y) position of removed tile
            arm_index: Index of arm that removed the tile
        """
        # Remove from mappings
        if tile_pos in self._tile_to_arm:
            del self._tile_to_arm[tile_pos]
        if arm_index in self._arm_to_tile:
            del self._arm_to_tile[arm_index]

        # Get current status
        current_status = self._arm_status.get(arm_index, "idle")

        # Validate state transition
        if current_status == "busy":
            # Arm just finished removing, transition to idle
            self._arm_status[arm_index] = "idle"
            current_status = "idle"

        # Fold arm if idle
        if current_status == "idle":
            self._arm_status[arm_index] = "folding"
            self.animator.fold_arm(arm_index)

    def update(self, dt: float) -> Dict[int, FoldingPose]:
        """
        Update animations and transition states.

        Args:
            dt: Time delta in seconds

        Returns:
            Dictionary of arm_index to current FoldingPose
        """
        # Update all animations
        poses = self.animator.update(dt)

        # Transition states based on animation completion
        for arm_index, pose in poses.items():
            if not pose.is_complete():
                continue

            current_status = self._arm_status.get(arm_index, "idle")

            # Transition from deploying to busy when deployed
            if (
                current_status == "deploying"
                and pose.current_pose == FoldingPoseState.DEPLOYED
            ):
                self._arm_status[arm_index] = "busy"

            # Transition from folding to idle when folded
            elif (
                current_status == "folding"
                and pose.current_pose == FoldingPoseState.FOLDED
            ):
                self._arm_status[arm_index] = "idle"

        return poses

    def get_arm_for_tile(self, tile_pos: Tuple[int, int]) -> Optional[int]:
        """
        Find the arm responsible for a tile position.

        Args:
            tile_pos: (x, y) position to query

        Returns:
            Arm index, or None if no arm assigned
        """
        return self._tile_to_arm.get(tile_pos)

    def assign_arm_to_position(
        self,
        arm_index: int,
        tile_pos: Tuple[int, int]
    ) -> None:
        """
        Assign an arm to a tile position.

        Args:
            arm_index: Index of arm to assign
            tile_pos: (x, y) position to assign arm to
        """
        # Remove old mapping if exists
        if arm_index in self._arm_to_tile:
            old_pos = self._arm_to_tile[arm_index]
            if old_pos in self._tile_to_arm:
                del self._tile_to_arm[old_pos]

        # Create new mapping
        self._tile_to_arm[tile_pos] = arm_index
        self._arm_to_tile[arm_index] = tile_pos

    def get_arm_status(self, arm_index: int) -> str:
        """
        Get the current status of an arm.

        Args:
            arm_index: Index of arm to query

        Returns:
            Status string: "idle", "busy", "folding", or "deploying"
        """
        return self._arm_status.get(arm_index, "idle")

    def get_all_status(self) -> Dict[int, str]:
        """
        Get status of all arms.

        Returns:
            Dictionary mapping arm_index to status
        """
        return self._arm_status.copy()

    def is_arm_available(self, arm_index: int) -> bool:
        """
        Check if an arm is available for tile operations.

        Args:
            arm_index: Index of arm to check

        Returns:
            True if arm is idle (available), False otherwise
        """
        return self._arm_status.get(arm_index, "idle") == "idle"

    def get_available_arms(self) -> List[int]:
        """
        Get list of arms that are available (idle).

        Returns:
            List of arm indices that are idle
        """
        return [
            idx for idx, status in self._arm_status.items()
            if status == "idle"
        ]

    def __repr__(self) -> str:
        idle = len(self.get_available_arms())
        total = len(self._arm_status)
        return (
            f"FoldingController(arms={total}, "
            f"available={idle})"
        )
