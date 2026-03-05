"""
ArmController for managing multiple mechanical arms.

This module provides the ArmController class for coordinating multiple
arms, assigning targets, and handling collision detection.
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from .types import ArmPhysicsConfig, PhysicsMode
from .arm import Arm
from .physics import PhysicsSimulator


@dataclass
class ArmController:
    """Controller for managing multiple mechanical arms.

    The ArmController handles coordination of multiple arms, including
    target assignment, physics simulation, and collision detection.

    Attributes:
        arms: List of arms under control
        physics_simulator: Shared physics simulator configuration
        target_assignments: Map of arm index to target position
    """
    arms: List[Arm] = field(default_factory=list)
    physics_simulator: Optional[PhysicsSimulator] = None
    target_assignments: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize default physics simulator if not provided."""
        if self.physics_simulator is None:
            config = ArmPhysicsConfig(mode=PhysicsMode.HYBRID)
            self.physics_simulator = PhysicsSimulator(config=config)

    def add_arm(self, arm: Arm) -> int:
        """Add an arm to the controller.

        Args:
            arm: Arm instance to add

        Returns:
            Index of the added arm
        """
        self.arms.append(arm)
        return len(self.arms) - 1

    def remove_arm(self, arm_index: int) -> bool:
        """Remove an arm from the controller.

        Args:
            arm_index: Index of arm to remove

        Returns:
            True if arm was removed, False if index invalid
        """
        if 0 <= arm_index < len(self.arms):
            self.arms.pop(arm_index)
            # Update target assignments for shifted indices
            new_assignments = {}
            for idx, target in self.target_assignments.items():
                if idx > arm_index:
                    new_assignments[idx - 1] = target
                elif idx < arm_index:
                    new_assignments[idx] = target
            self.target_assignments = new_assignments
            return True
        return False

    def assign_target(
        self,
        arm_index: int,
        target_pos: Tuple[float, float, float]
    ) -> bool:
        """Assign a target position to a specific arm.

        Args:
            arm_index: Index of arm to assign target to
            target_pos: Target world position (x, y, z)

        Returns:
            True if assignment successful, False if arm index invalid
        """
        if 0 <= arm_index < len(self.arms):
            self.target_assignments[arm_index] = target_pos
            return True
        return False

    def clear_target(self, arm_index: int) -> bool:
        """Clear target assignment for an arm.

        Args:
            arm_index: Index of arm to clear target for

        Returns:
            True if cleared, False if arm index invalid
        """
        if 0 <= arm_index < len(self.arms):
            if arm_index in self.target_assignments:
                del self.target_assignments[arm_index]
            return True
        return False

    def update_all(self, dt: float) -> Dict[int, Tuple[float, float, float]]:
        """Update all arms towards their targets.

        Performs physics simulation for all arms with assigned targets.

        Args:
            dt: Time step in seconds

        Returns:
            Dictionary mapping arm index to end effector position
        """
        positions: Dict[int, Tuple[float, float, float]] = {}

        for i, arm in enumerate(self.arms):
            if i in self.target_assignments:
                target = self.target_assignments[i]
                new_pos = arm.update(dt, target)
                positions[i] = new_pos
            else:
                # Arm has no target, just record current position
                positions[i] = arm.end_effector_position

        return positions

    def get_arm_positions(self) -> Dict[int, Tuple[float, float, float]]:
        """Get current end effector positions for all arms.

        Returns:
            Dictionary mapping arm index to end effector position
        """
        return {
            i: arm.end_effector_position
            for i, arm in enumerate(self.arms)
        }

    def get_available_arm(
        self,
        target_pos: Tuple[float, float, float]
    ) -> Optional[int]:
        """Find arm closest to target that can reach it.

        Searches for an arm that:
        1. Can reach the target position
        2. Does not currently have a target assigned
        3. Is closest to the target (for efficiency)

        Args:
            target_pos: Target world position (x, y, z)

        Returns:
            Index of available arm, or None if no arm available
        """
        best_arm: Optional[int] = None
        best_distance = float('inf')

        for i, arm in enumerate(self.arms):
            # Skip arms that already have targets
            if i in self.target_assignments:
                continue

            # Check if arm can reach target
            if not arm.can_reach(target_pos):
                continue

            # Calculate distance to target
            current_pos = arm.end_effector_position
            distance = math.sqrt(
                (current_pos[0] - target_pos[0]) ** 2 +
                (current_pos[1] - target_pos[1]) ** 2 +
                (current_pos[2] - target_pos[2]) ** 2
            )

            if distance < best_distance:
                best_distance = distance
                best_arm = i

        return best_arm

    def check_arm_collisions(self) -> List[Tuple[int, int]]:
        """Check for collisions between arms.

        Uses bounding box intersection to detect potential collisions
        between arms. Returns pairs of arm indices that are colliding.

        Returns:
            List of (arm_index_1, arm_index_2) tuples for colliding arms
        """
        collisions: List[Tuple[int, int]] = []

        for i in range(len(self.arms)):
            for j in range(i + 1, len(self.arms)):
                if self._arms_collide(self.arms[i], self.arms[j]):
                    collisions.append((i, j))

        return collisions

    def _arms_collide(self, arm1: Arm, arm2: Arm) -> bool:
        """Check if two arms are colliding using bounding boxes.

        Args:
            arm1: First arm
            arm2: Second arm

        Returns:
            True if arms' bounding boxes intersect
        """
        bounds1 = arm1.get_bounds()
        bounds2 = arm2.get_bounds()

        # Check AABB intersection
        # bounds format: (min_x, min_y, min_z, max_x, max_y, max_z)
        no_overlap = (
            bounds1[3] < bounds2[0] or  # arm1.max_x < arm2.min_x
            bounds1[0] > bounds2[3] or  # arm1.min_x > arm2.max_x
            bounds1[4] < bounds2[1] or  # arm1.max_y < arm2.min_y
            bounds1[1] > bounds2[4] or  # arm1.min_y > arm2.max_y
            bounds1[5] < bounds2[2] or  # arm1.max_z < arm2.min_z
            bounds1[2] > bounds2[5]     # arm1.min_z > arm2.max_z
        )

        return not no_overlap

    def get_arm_states(self) -> Dict[int, str]:
        """Get operational states of all arms.

        Returns:
            Dictionary mapping arm index to state name
        """
        return {
            i: arm.state.value
            for i, arm in enumerate(self.arms)
        }

    def get_idle_arms(self) -> List[int]:
        """Get indices of all arms in IDLE state.

        Returns:
            List of arm indices that are idle
        """
        from .types import ArmState
        return [
            i for i, arm in enumerate(self.arms)
            if arm.state == ArmState.IDLE
        ]

    def get_busy_arms(self) -> List[int]:
        """Get indices of all arms that are not IDLE.

        Returns:
            List of arm indices that are busy
        """
        from .types import ArmState
        return [
            i for i, arm in enumerate(self.arms)
            if arm.state != ArmState.IDLE
        ]

    def reset_all(self) -> None:
        """Reset all arms to their initial state."""
        self.target_assignments.clear()
        for arm in self.arms:
            arm.reset()

    def get_total_reach(self) -> float:
        """Calculate combined reach of all arms.

        Returns:
            Sum of maximum reach of all arms
        """
        return sum(arm.get_reach() for arm in self.arms)

    def get_coverage_radius(self) -> float:
        """Calculate approximate coverage radius from arm bases.

        Returns:
            Maximum distance from origin covered by any arm
        """
        max_coverage = 0.0
        for arm in self.arms:
            base = arm.base_position
            reach = arm.get_reach()
            distance_from_origin = math.sqrt(
                base[0] ** 2 + base[1] ** 2 + base[2] ** 2
            )
            coverage = distance_from_origin + reach
            max_coverage = max(max_coverage, coverage)
        return max_coverage
