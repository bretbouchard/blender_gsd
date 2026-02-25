"""
Launch Control Module

Launch speed and angle optimization for stunts.

Phase 17.4: Launch Control & Physics (REQ-STUNT-05)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import math

from .physics import (
    GRAVITY,
    calculate_launch_velocity,
    calculate_air_time,
    calculate_optimal_trajectory,
)


@dataclass
class SpeedRequirement:
    """Speed requirement for a stunt element."""
    element_id: str
    entry_speed: float
    exit_speed: float
    min_safe_speed: float
    max_safe_speed: float
    recommended_speed: float
    speed_margin: float  # % above minimum


class LaunchController:
    """
    Controls launch parameters for stunt sequences.

    Calculates required speeds and angles for various stunt elements
    and ensures continuity between elements.
    """

    def __init__(self, frame_rate: int = 24):
        """
        Initialize launch controller.

        Args:
            frame_rate: Animation frame rate
        """
        self.frame_rate = frame_rate
        self.speed_requirements: Dict[str, SpeedRequirement] = {}

    def calculate_speed_requirement(
        self,
        element_type: str,
        distance: float,
        height_diff: float = 0.0,
        element_id: Optional[str] = None,
    ) -> SpeedRequirement:
        """Calculate speed requirement for a stunt element.

        Args:
            element_type: Type of stunt (jump, loop, turn, etc.)
            distance: Horizontal distance
            height_diff: Height difference
            element_id: Optional element identifier

        Returns:
            SpeedRequirement with calculated values
        """
        if element_id is None:
            element_id = f"element_{len(self.speed_requirements)}"

        # Get optimal trajectory
        trajectory = calculate_optimal_trajectory(distance, height_diff)

        entry_speed = trajectory['required_speed']
        min_safe_speed = entry_speed * 0.9
        max_safe_speed = entry_speed * 1.5
        recommended_speed = entry_speed * 1.15  # 15% margin

        # Exit speed (approximate based on element type)
        if element_type == 'jump':
            exit_speed = entry_speed * 0.85  # 15% loss on landing
        elif element_type == 'loop':
            exit_speed = entry_speed * 0.7   # 30% loss through loop
        elif element_type == 'turn':
            exit_speed = entry_speed * 0.9   # 10% loss in turn
        else:
            exit_speed = entry_speed * 0.9

        speed_margin = ((recommended_speed - min_safe_speed) / min_safe_speed) * 100

        requirement = SpeedRequirement(
            element_id=element_id,
            entry_speed=entry_speed,
            exit_speed=exit_speed,
            min_safe_speed=min_safe_speed,
            max_safe_speed=max_safe_speed,
            recommended_speed=recommended_speed,
            speed_margin=speed_margin,
        )

        self.speed_requirements[element_id] = requirement
        return requirement

    def get_launch_params(
        self,
        distance: float,
        height_diff: float = 0.0,
        target_angle: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Get optimal launch parameters for a jump.

        Args:
            distance: Horizontal distance to travel
            height_diff: Landing height difference
            target_angle: Optional target angle (will optimize if None)

        Returns:
            Dictionary with launch parameters
        """
        trajectory = calculate_optimal_trajectory(
            distance, height_diff, target_angle
        )

        return {
            'speed': trajectory['required_speed'],
            'angle': trajectory['optimal_angle'],
            'air_time': trajectory['air_time'],
            'peak_height': trajectory['peak_height'],
            'landing_speed': trajectory['landing_speed'],
        }

    def check_speed_continuity(
        self,
        prev_element_id: str,
        next_element_id: str,
        run_distance: float = 0.0,
    ) -> Dict[str, Any]:
        """Check if speed is continuous between elements.

        Args:
            prev_element_id: Previous element ID
            next_element_id: Next element ID
            run_distance: Distance between elements

        Returns:
            Dictionary with continuity analysis
        """
        prev_req = self.speed_requirements.get(prev_element_id)
        next_req = self.speed_requirements.get(next_element_id)

        if prev_req is None or next_req is None:
            return {
                'continuous': False,
                'speed_gap': 0,
                'needs_boost': False,
                'needs_brake': False,
            }

        exit_speed = prev_req.exit_speed
        entry_speed = next_req.entry_speed

        # Account for coasting (drag loss)
        if run_distance > 0:
            # Approximate 2% speed loss per 10m
            coast_loss = 0.02 * (run_distance / 10)
            exit_speed = exit_speed * (1 - coast_loss)

        speed_gap = entry_speed - exit_speed

        return {
            'continuous': abs(speed_gap) < 3.0,  # Within 3 m/s
            'speed_gap': speed_gap,
            'exit_speed': exit_speed,
            'required_entry': entry_speed,
            'needs_boost': speed_gap > 3.0,
            'needs_brake': speed_gap < -5.0,
            'boost_distance': self._calculate_boost_distance(speed_gap) if speed_gap > 0 else 0,
        }

    def _calculate_boost_distance(self, speed_needed: float) -> float:
        """Calculate distance needed to gain speed.

        Args:
            speed_needed: Additional speed needed in m/s

        Returns:
            Distance in meters (assuming moderate acceleration)
        """
        # Assume 0.3g average acceleration
        acceleration = 0.3 * GRAVITY

        # v² = 2 * a * d
        # d = v² / (2 * a)
        if acceleration > 0:
            return speed_needed**2 / (2 * acceleration)
        return 0

    def optimize_sequence(
        self,
        elements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Optimize launch speeds for a sequence of elements.

        Args:
            elements: List of element configurations

        Returns:
            List of elements with optimized speeds
        """
        optimized = []

        for i, element in enumerate(elements):
            # Calculate speed requirement
            req = self.calculate_speed_requirement(
                element.get('type', 'jump'),
                element.get('distance', 10.0),
                element.get('height_diff', 0.0),
                element.get('id', f'elem_{i}'),
            )

            # Check continuity with previous
            continuity = {}
            if i > 0:
                prev_id = optimized[i - 1]['id']
                continuity = self.check_speed_continuity(
                    prev_id, element.get('id', f'elem_{i}'),
                    element.get('run_distance', 0),
                )

            optimized.append({
                **element,
                'speed_requirement': req,
                'continuity': continuity,
            })

        return optimized

    def get_run_up_distance(
        self,
        target_speed: float,
        start_speed: float = 0.0,
        acceleration: float = 0.3 * GRAVITY,
    ) -> float:
        """Calculate run-up distance needed to reach target speed.

        Args:
            target_speed: Required entry speed in m/s
            start_speed: Starting speed in m/s
            acceleration: Average acceleration in m/s²

        Returns:
            Distance in meters
        """
        if acceleration <= 0:
            return float('inf')

        # v² = v0² + 2 * a * d
        # d = (v² - v0²) / (2 * a)
        v_diff_sq = target_speed**2 - start_speed**2

        if v_diff_sq <= 0:
            return 0

        return v_diff_sq / (2 * acceleration)


def calculate_speed_requirement(
    distance: float,
    height_diff: float = 0.0,
    angle: Optional[float] = None,
) -> SpeedRequirement:
    """Convenience function to calculate speed requirement.

    Args:
        distance: Horizontal distance
        height_diff: Height difference
        angle: Optional launch angle

    Returns:
        SpeedRequirement
    """
    controller = LaunchController()
    return controller.calculate_speed_requirement(
        'jump', distance, height_diff
    )


def optimize_launch_angle(
    distance: float,
    height_diff: float = 0.0,
    max_height: Optional[float] = None,
) -> float:
    """Find optimal launch angle for given constraints.

    Args:
        distance: Horizontal distance
        height_diff: Height difference
        max_height: Maximum allowed height

    Returns:
        Optimal angle in degrees
    """
    trajectory = calculate_optimal_trajectory(
        distance, height_diff, max_height
    )
    return trajectory['optimal_angle']


def calculate_run_up(
    target_speed: float,
    start_speed: float = 0.0,
    vehicle_acceleration: Optional[float] = None,
) -> float:
    """Calculate run-up distance needed.

    Args:
        target_speed: Target speed in m/s
        start_speed: Starting speed in m/s
        vehicle_acceleration: Vehicle acceleration capability

    Returns:
        Required run-up distance in meters
    """
    # Default: 0.3g (typical car acceleration)
    if vehicle_acceleration is None:
        vehicle_acceleration = 0.3 * GRAVITY

    if vehicle_acceleration <= 0:
        return float('inf')

    v_diff_sq = target_speed**2 - start_speed**2

    if v_diff_sq <= 0:
        return 0

    return v_diff_sq / (2 * vehicle_acceleration)


def calculate_braking_distance(
    current_speed: float,
    target_speed: float,
    friction: float = 0.8,
) -> float:
    """Calculate braking distance needed.

    Args:
        current_speed: Current speed in m/s
        target_speed: Target speed in m/s
        friction: Tire friction coefficient

    Returns:
        Required braking distance in meters
    """
    g = GRAVITY

    # Deceleration = friction * g
    deceleration = friction * g

    if deceleration <= 0:
        return float('inf')

    v_diff_sq = current_speed**2 - target_speed**2

    if v_diff_sq <= 0:
        return 0

    return v_diff_sq / (2 * deceleration)


def suggest_speed_adjustments(
    elements: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Suggest speed adjustments for a stunt sequence.

    Args:
        elements: List of elements with speed requirements

    Returns:
        List of adjustment suggestions
    """
    suggestions = []

    for i in range(len(elements) - 1):
        current = elements[i]
        next_elem = elements[i + 1]

        exit_speed = current.get('exit_speed', current.get('entry_speed', 20))
        next_entry = next_elem.get('entry_speed', 20)
        run_distance = next_elem.get('run_distance', 0)

        # Account for coasting
        coast_loss = 0.02 * (run_distance / 10) if run_distance > 0 else 0
        actual_exit = exit_speed * (1 - coast_loss)

        speed_gap = next_entry - actual_exit

        if abs(speed_gap) > 3.0:
            suggestion = {
                'from_element': current.get('id', f'elem_{i}'),
                'to_element': next_elem.get('id', f'elem_{i+1}'),
                'speed_gap': speed_gap,
                'actual_exit_speed': actual_exit,
                'required_entry_speed': next_entry,
            }

            if speed_gap > 0:
                # Need more speed
                boost_dist = calculate_run_up(next_entry, actual_exit)
                suggestion['action'] = 'boost'
                suggestion['boost_distance'] = boost_dist
                suggestion['message'] = f"Add {boost_dist:.0f}m acceleration zone"
            else:
                # Need less speed
                brake_dist = calculate_braking_distance(actual_exit, next_entry)
                suggestion['action'] = 'brake'
                suggestion['brake_distance'] = brake_dist
                suggestion['message'] = f"Add {brake_dist:.0f}m braking zone"

            suggestions.append(suggestion)

    return suggestions
