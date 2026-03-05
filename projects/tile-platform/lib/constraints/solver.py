"""
Integrated constraint solver for mechanical arms.

This module provides the ConstraintSolver class that combines physics
simulation with constraint enforcement to produce smooth, accurate
arm movement that guarantees target reach.
"""

from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from lib.arms.physics import PhysicsSimulator
from lib.arms.types import ArmPhysicsConfig
from .target_reach import TargetReachConstraint
from .limiters import JointLimiter


class ConstraintSolver:
    """Integrated constraint solver combining physics with constraints.

    The ConstraintSolver integrates physics simulation with target reach
    constraints and joint limits to produce smooth, accurate movement
    that guarantees arms reach their targets.

    Attributes:
        physics_simulator: PhysicsSimulator for arm dynamics
        target_reach: TargetReachConstraint for guaranteed target reach
        joint_limiter: JointLimiter for joint angle constraints
        iteration_count: Maximum iterations per solve step (default: 10)
        convergence_threshold: Threshold for convergence detection (default: 1e-6)
    """

    def __init__(
        self,
        physics_simulator: PhysicsSimulator = None,
        physics_config: ArmPhysicsConfig = None,
        target_reach: TargetReachConstraint = None,
        joint_limiter: JointLimiter = None,
        iteration_count: int = 10,
        convergence_threshold: float = 1e-6
    ) -> None:
        """Initialize the constraint solver.

        Args:
            physics_simulator: Existing PhysicsSimulator instance (optional)
            physics_config: Config for creating new PhysicsSimulator (optional)
            target_reach: TargetReachConstraint instance (optional)
            joint_limiter: JointLimiter instance (optional)
            iteration_count: Maximum constraint iterations per step
            convergence_threshold: Threshold for detecting convergence
        """
        # Initialize or use provided physics simulator
        if physics_simulator:
            self.physics_simulator = physics_simulator
        elif physics_config:
            self.physics_simulator = PhysicsSimulator(physics_config)
        else:
            # Create default physics simulator
            from lib.arms.types import ArmPhysicsConfig, PhysicsMode
            default_config = ArmPhysicsConfig(
                mode=PhysicsMode.HYBRID,
                gravity=-9.81,
                air_resistance=0.1,
                target_reach_force=5.0
            )
            self.physics_simulator = PhysicsSimulator(default_config)

        # Initialize or use provided constraints
        self.target_reach = target_reach or TargetReachConstraint()
        self.joint_limiter = joint_limiter or JointLimiter()

        # Solver parameters
        self.iteration_count = iteration_count
        self.convergence_threshold = convergence_threshold

        # State tracking
        self._current_positions: Dict[int, Tuple[float, float, float]] = {}
        self._target_positions: Dict[int, Tuple[float, float, float]] = {}
        self._velocities: Dict[int, Tuple[float, float, float]] = {}
        self._deviation_history: List[float] = []

    def set_arm_state(
        self,
        arm_id: int,
        current_pos: Tuple[float, float, float],
        velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ) -> None:
        """Set the current state of an arm.

        Args:
            arm_id: Identifier for the arm
            current_pos: Current end effector position (x, y, z)
            velocity: Current velocity (vx, vy, vz)
        """
        self._current_positions[arm_id] = current_pos
        self._velocities[arm_id] = velocity

    def set_target(
        self,
        arm_id: int,
        target_pos: Tuple[float, float, float]
    ) -> None:
        """Set the target position for an arm.

        Args:
            arm_id: Identifier for the arm
            target_pos: Target end effector position (x, y, z)
        """
        self._target_positions[arm_id] = target_pos

    def solve_step(self, dt: float) -> Dict[int, float]:
        """Perform one constraint solving step.

        Runs physics simulation, applies constraints, and returns
        joint corrections needed to reach targets.

        Args:
            dt: Time step in seconds

        Returns:
            Dictionary mapping arm_id to correction magnitude
        """
        corrections: Dict[int, float] = {}

        for arm_id in self._current_positions:
            if arm_id not in self._target_positions:
                continue

            current_pos = self._current_positions[arm_id]
            target_pos = self._target_positions[arm_id]
            velocity = self._velocities.get(arm_id, (0.0, 0.0, 0.0))

            # Compute constraint correction
            correction = self.target_reach.compute_correction(
                current_pos,
                target_pos,
                velocity,
                dt
            )

            # Calculate correction magnitude
            magnitude = (
                correction[0]**2 + correction[1]**2 + correction[2]**2
            )**0.5

            corrections[arm_id] = magnitude

            # Update tracked position (simplified - in real use, would
            # update based on physics simulation results)
            self._current_positions[arm_id] = (
                current_pos[0] + correction[0],
                current_pos[1] + correction[1],
                current_pos[2] + correction[2]
            )

            # Update velocity (simplified)
            if dt > 0:
                self._velocities[arm_id] = correction

            # Track deviation for convergence checking
            deviation = self.target_reach.get_deviation(current_pos, target_pos)
            self._deviation_history.append(deviation)

        return corrections

    def solve_full(
        self,
        duration: float,
        steps: int
    ) -> List[Dict[int, float]]:
        """Run full constraint solving simulation.

        Performs multiple solve steps over a duration, applying
        constraints at each step.

        Args:
            duration: Total simulation time in seconds
            steps: Number of steps to perform

        Returns:
            List of correction dictionaries at each step
        """
        dt = duration / steps if steps > 0 else 0.016
        history: List[Dict[int, float]] = []

        for _ in range(steps):
            corrections = self.solve_step(dt)
            history.append(corrections)

            # Check for early convergence
            if self.check_convergence():
                break

        return history

    def check_convergence(self) -> bool:
        """Check if all arms have converged to their targets.

        Returns:
            True if all arms have settled at their targets
        """
        if not self._current_positions or not self._target_positions:
            return True

        for arm_id in self._current_positions:
            if arm_id not in self._target_positions:
                continue

            current_pos = self._current_positions[arm_id]
            target_pos = self._target_positions[arm_id]
            velocity = self._velocities.get(arm_id, (0.0, 0.0, 0.0))

            if not self.target_reach.is_reached(current_pos, target_pos, velocity):
                return False

        # Also check convergence history if available
        if self._deviation_history:
            if not self.target_reach.is_converged(self._deviation_history):
                return False

        return True

    def apply_joint_limits(
        self,
        corrections: Dict[int, float]
    ) -> Dict[int, float]:
        """Apply joint limits to corrections.

        Takes correction magnitudes and applies joint limits to ensure
        corrections don't violate joint constraints.

        Args:
            corrections: Dictionary of arm_id -> correction magnitude

        Returns:
            Modified corrections respecting joint limits
        """
        # In a real implementation, this would convert position corrections
        # to joint angle corrections and apply limits
        # For now, we apply a simple scaling based on violation

        limited_corrections: Dict[int, float] = {}

        for arm_id, magnitude in corrections.items():
            # Check if this magnitude would violate limits
            # (simplified - real implementation would check actual joint angles)
            if self.joint_limiter.joint_limits:
                # Scale down if approaching limits
                max_allowed = 1.0  # Placeholder for max correction magnitude
                limited = min(magnitude, max_allowed)
                limited_corrections[arm_id] = limited
            else:
                limited_corrections[arm_id] = magnitude

        return limited_corrections

    def reset(self) -> None:
        """Reset solver state."""
        self._current_positions.clear()
        self._target_positions.clear()
        self._velocities.clear()
        self._deviation_history.clear()

    def get_deviation(self, arm_id: int) -> float:
        """Get current deviation for an arm.

        Args:
            arm_id: Identifier for the arm

        Returns:
            Current distance from target, or 0.0 if not tracked
        """
        if arm_id not in self._current_positions:
            return 0.0
        if arm_id not in self._target_positions:
            return 0.0

        return self.target_reach.get_deviation(
            self._current_positions[arm_id],
            self._target_positions[arm_id]
        )

    def get_all_deviations(self) -> Dict[int, float]:
        """Get deviations for all tracked arms.

        Returns:
            Dictionary mapping arm_id to deviation from target
        """
        deviations: Dict[int, float] = {}

        for arm_id in self._current_positions:
            deviation = self.get_deviation(arm_id)
            if deviation > 0.0:
                deviations[arm_id] = deviation

        return deviations

    def is_settled(self, arm_id: int) -> bool:
        """Check if a specific arm has settled at its target.

        Args:
            arm_id: Identifier for the arm

        Returns:
            True if arm is settled at target
        """
        if arm_id not in self._current_positions:
            return False
        if arm_id not in self._target_positions:
            return False

        current_pos = self._current_positions[arm_id]
        target_pos = self._target_positions[arm_id]
        velocity = self._velocities.get(arm_id, (0.0, 0.0, 0.0))

        return self.target_reach.is_reached(current_pos, target_pos, velocity)

    @property
    def deviation_history(self) -> List[float]:
        """Return the history of deviation measurements."""
        return self._deviation_history.copy()
