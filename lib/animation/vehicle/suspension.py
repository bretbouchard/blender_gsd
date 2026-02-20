"""
Suspension System Module

Manages vehicle suspension for terrain following and
realistic vehicle motion.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SuspensionData:
    """Data for a single suspension unit."""
    arm: Any                                  # Suspension arm object
    wheel: Any                                # Connected wheel
    travel: float = 0.15                      # Travel distance (meters)
    stiffness: float = 1.0                    # Spring stiffness
    damping: float = 0.5                      # Damping coefficient
    rest_height: float = 0.0                  # Rest position
    velocity: float = 0.0                     # Current velocity (for damping)
    terrain_constraint: Optional[Any] = None  # Shrinkwrap constraint


class SuspensionSystem:
    """Manage vehicle suspension for terrain following."""

    def __init__(self):
        self._suspensions: Dict[str, SuspensionData] = {}

    @staticmethod
    def create_suspension(
        wheel_object: Any,
        travel: float = 0.15,
        stiffness: float = 1.0,
        damping: float = 0.5
    ) -> SuspensionData:
        """
        Create suspension system for a wheel.

        Args:
            wheel_object: The wheel to suspend
            travel: Suspension travel distance in meters
            stiffness: Spring stiffness coefficient
            damping: Damping coefficient (prevents oscillation)

        Returns:
            SuspensionData containing all suspension components
        """
        # Create suspension arm (mock for testing)
        arm = {
            'name': f"{getattr(wheel_object, 'name', 'wheel')}_suspension",
            'location': getattr(wheel_object, 'location', [0, 0, 0])[:],
            'type': 'SUSPENSION_ARM',
        }

        # Get initial height as rest position
        rest_height = arm['location'][2] if isinstance(arm.get('location'), list) else 0.0

        return SuspensionData(
            arm=arm,
            wheel=wheel_object,
            travel=travel,
            stiffness=stiffness,
            damping=damping,
            rest_height=rest_height,
            velocity=0.0,
        )

    def add_suspension(
        self,
        wheel_id: str,
        wheel_object: Any,
        travel: float = 0.15,
        stiffness: float = 1.0,
        damping: float = 0.5
    ) -> SuspensionData:
        """
        Add suspension for a wheel.

        Args:
            wheel_id: Unique identifier for the wheel
            wheel_object: The wheel object
            travel: Suspension travel distance
            stiffness: Spring stiffness
            damping: Damping coefficient

        Returns:
            The created SuspensionData
        """
        data = self.create_suspension(wheel_object, travel, stiffness, damping)
        self._suspensions[wheel_id] = data
        return data

    def get_suspension(self, wheel_id: str) -> Optional[SuspensionData]:
        """Get suspension data for a wheel."""
        return self._suspensions.get(wheel_id)

    def get_all_suspensions(self) -> List[SuspensionData]:
        """Get all suspension data."""
        return list(self._suspensions.values())

    @staticmethod
    def add_terrain_following(
        suspension_data: SuspensionData,
        terrain_object: Any,
        ray_length: float = 1.0
    ) -> None:
        """
        Add terrain following constraint to suspension.

        This creates a shrinkwrap constraint that projects the
        suspension arm onto the terrain surface.

        Args:
            suspension_data: The suspension to modify
            terrain_object: The terrain mesh to follow
            ray_length: Maximum ray projection distance
        """
        constraint = {
            'type': 'SHRINKWRAP',
            'target': terrain_object,
            'shrinkwrap_type': 'PROJECT',
            'distance': ray_length,
            'project_axis': 'NEG_Z',
            'use_project_z': True,
        }
        suspension_data.terrain_constraint = constraint

    @staticmethod
    def simulate_suspension(
        suspension_data: SuspensionData,
        terrain_height: float,
        dt: float = 1/24
    ) -> float:
        """
        Simulate spring-damper suspension for one time step.

        Implements proper spring-damper physics:
        force = stiffness * displacement - damping * velocity

        Args:
            suspension_data: The suspension to simulate
            terrain_height: Target height from terrain
            dt: Time step in seconds

        Returns:
            New suspension height
        """
        arm = suspension_data.arm
        travel = suspension_data.travel
        stiffness = suspension_data.stiffness
        damping = suspension_data.damping

        # Get current height
        current_height = arm['location'][2] if isinstance(arm.get('location'), list) else 0.0
        rest_height = suspension_data.rest_height

        # Calculate spring displacement
        target_height = terrain_height
        displacement = target_height - current_height

        # Spring force: F = k * x
        spring_force = stiffness * displacement

        # Damping force: F = -c * v
        damping_force = -damping * suspension_data.velocity

        # Total force
        total_force = spring_force + damping_force

        # Update velocity (simple Euler integration)
        suspension_data.velocity += total_force * dt

        # Calculate new height
        new_height = current_height + suspension_data.velocity * dt

        # Clamp to travel limits
        min_height = rest_height - travel
        max_height = rest_height + travel
        new_height = max(min_height, min(max_height, new_height))

        # If clamped, also clamp velocity to prevent energy buildup
        if new_height <= min_height or new_height >= max_height:
            suspension_data.velocity = 0.0

        # Update arm location
        arm['location'] = [
            arm['location'][0] if isinstance(arm.get('location'), list) else 0,
            arm['location'][1] if isinstance(arm.get('location'), list) else 0,
            new_height,
        ]

        return new_height

    def update_all_suspensions(
        self,
        terrain_heights: Dict[str, float],
        dt: float = 1/24
    ) -> Dict[str, float]:
        """
        Update all suspensions with new terrain heights.

        Args:
            terrain_heights: Dictionary of wheel_id -> terrain_height
            dt: Time step in seconds

        Returns:
            Dictionary of wheel_id -> new_height
        """
        results = {}
        for wheel_id, terrain_height in terrain_heights.items():
            suspension = self.get_suspension(wheel_id)
            if suspension:
                new_height = self.simulate_suspension(suspension, terrain_height, dt)
                results[wheel_id] = new_height
        return results

    def reset_all_velocities(self) -> None:
        """Reset all suspension velocities to zero."""
        for suspension in self._suspensions.values():
            suspension.velocity = 0.0

    def get_compression_ratio(self, wheel_id: str) -> float:
        """
        Get suspension compression ratio (0 = extended, 1 = fully compressed).

        Args:
            wheel_id: The wheel to check

        Returns:
            Compression ratio from 0 to 1
        """
        suspension = self.get_suspension(wheel_id)
        if not suspension:
            return 0.0

        current_height = suspension.arm['location'][2] if isinstance(suspension.arm.get('location'), list) else 0.0
        rest_height = suspension.rest_height
        travel = suspension.travel

        # Compression is how much we're above rest position
        compression = (rest_height - current_height + travel) / (2 * travel)
        return max(0.0, min(1.0, compression))


def setup_vehicle_suspension(
    wheels: List[Any],
    travel: float = 0.15,
    stiffness: float = 1.0,
    damping: float = 0.5
) -> Dict[str, SuspensionData]:
    """
    Setup suspension for all wheels.

    Args:
        wheels: List of wheel objects
        travel: Suspension travel for all wheels
        stiffness: Spring stiffness for all wheels
        damping: Damping coefficient for all wheels

    Returns:
        Dictionary of wheel_name -> SuspensionData
    """
    system = SuspensionSystem()
    suspensions = {}

    wheel_ids = ['FL', 'FR', 'RL', 'RR']

    for i, wheel in enumerate(wheels):
        wheel_id = wheel_ids[i] if i < len(wheel_ids) else f'W{i}'
        suspension = system.add_suspension(
            wheel_id=wheel_id,
            wheel_object=wheel,
            travel=travel,
            stiffness=stiffness,
            damping=damping
        )
        suspensions[wheel_id] = suspension

    return suspensions
