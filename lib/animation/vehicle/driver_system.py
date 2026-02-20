"""
Driver System Module

Applies realistic driving characteristics based on driver profiles.
Affects path smoothing, acceleration, and driving imperfections.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Any, Dict
import logging
import math
import random

from ..types import DriverProfile, DRIVER_PRESETS

logger = logging.getLogger(__name__)


class ExpertDriver:
    """
    Applies expert driving characteristics to vehicle animation.

    Uses driver profiles to modify:
    - Path smoothness
    - Steering response
    - Acceleration/braking curves
    - Driving imperfections (jitter for nervous drivers)
    """

    # Physics constants
    FRAME_RATE = 24
    JITTER_SCALE = 0.02  # Maximum jitter in meters

    @staticmethod
    def smooth_path(
        vehicle: Any,
        frame_range: Tuple[int, int],
        profile: DriverProfile
    ) -> None:
        """
        Smooth vehicle path based on driver skill.

        Higher skill = smoother path with less corner cutting.
        Lower skill = more erratic path with overshoots.

        Args:
            vehicle: Vehicle object with animation data
            frame_range: (start_frame, end_frame) to process
            profile: Driver profile to apply
        """
        start_frame, end_frame = frame_range

        # Get existing keyframes or create mock
        keyframes = vehicle.get('path_keyframes', [])
        if not keyframes:
            # Create mock keyframes for testing
            keyframes = [
                {'frame': start_frame, 'location': [0, 0, 0]},
                {'frame': (start_frame + end_frame) // 2, 'location': [50, 10, 0]},
                {'frame': end_frame, 'location': [100, 0, 0]},
            ]

        # Smooth factor based on skill (higher skill = more smoothing)
        smooth_factor = profile.smoothness

        # Apply smoothing to intermediate positions
        smoothed = []
        for i, kf in enumerate(keyframes):
            if i == 0 or i == len(keyframes) - 1:
                # Keep endpoints unchanged
                smoothed.append(kf.copy())
            else:
                # Interpolate with neighbors based on smoothness
                prev_loc = keyframes[i - 1]['location']
                curr_loc = kf['location']
                next_loc = keyframes[i + 1]['location']

                # Weighted average towards smooth line
                new_loc = [
                    curr_loc[0] * (1 - smooth_factor) +
                    (prev_loc[0] + next_loc[0]) / 2 * smooth_factor,
                    curr_loc[1] * (1 - smooth_factor) +
                    (prev_loc[1] + next_loc[1]) / 2 * smooth_factor,
                    curr_loc[2],
                ]

                smoothed_kf = kf.copy()
                smoothed_kf['location'] = new_loc
                smoothed_kf['smoothed'] = True
                smoothed.append(smoothed_kf)

        vehicle['path_keyframes'] = smoothed
        logger.debug(f"Smoothed path with factor {smooth_factor}")

    @staticmethod
    def add_realism(
        vehicle: Any,
        profile: DriverProfile,
        add_jitter: bool = True
    ) -> None:
        """
        Add realistic driving imperfections based on driver profile.

        Low smoothness = more jitter and corrections
        Low consistency = more random variations

        Args:
            vehicle: Vehicle object
            profile: Driver profile
            add_jitter: Whether to add positional jitter
        """
        keyframes = vehicle.get('path_keyframes', [])
        if not keyframes:
            return

        # Jitter inversely proportional to smoothness
        jitter_amount = (1 - profile.smoothness) * ExpertDriver.JITTER_SCALE

        # Randomness inversely proportional to consistency
        randomness = 1 - profile.consistency

        for kf in keyframes:
            if add_jitter and jitter_amount > 0:
                # Add small random offsets
                jitter_x = random.uniform(-jitter_amount, jitter_amount) * randomness
                jitter_y = random.uniform(-jitter_amount, jitter_amount) * randomness

                kf['location'] = [
                    kf['location'][0] + jitter_x,
                    kf['location'][1] + jitter_y,
                    kf['location'][2],
                ]
                kf['jitter_applied'] = True

        vehicle['path_keyframes'] = keyframes
        logger.debug(f"Added realism with jitter={jitter_amount}")

    @staticmethod
    def apply_racing_line(
        vehicle: Any,
        path_curve: Any,
        profile: DriverProfile,
        frame_range: Tuple[int, int]
    ) -> None:
        """
        Apply racing line optimization to path following.

        Expert drivers take optimal lines through corners:
        - Wider entry
        - Apex at geometric center
        - Wider exit

        Args:
            vehicle: Vehicle object
            path_curve: The path/curve to follow
            profile: Driver profile
            frame_range: Frame range for animation
        """
        # Racing line optimization factor (0 = follow center, 1 = optimal racing line)
        optimization = profile.skill_level * profile.aggression

        # Generate racing line keyframes
        keyframes = []
        start_frame, end_frame = frame_range
        total_frames = end_frame - start_frame

        # Mock path points (in real use, would sample from curve)
        path_points = [
            (0, 0), (20, 5), (40, 15), (60, 10), (80, 0), (100, 0)
        ]

        for i, point in enumerate(path_points):
            frame = start_frame + int(i * total_frames / (len(path_points) - 1))

            # Apply racing line offset based on optimization
            # In corners, move towards outside then apex
            if i > 0 and i < len(path_points) - 1:
                # Calculate curvature direction
                prev = path_points[i - 1]
                curr = point
                next_pt = path_points[i + 1]

                # Cross product to determine inside/outside
                dx1 = curr[0] - prev[0]
                dy1 = curr[1] - prev[1]
                dx2 = next_pt[0] - curr[0]
                dy2 = next_pt[1] - curr[1]

                # Simple curvature estimate
                curvature = (dx1 * dy2 - dy1 * dx2)

                # Offset towards outside of corner (racing line)
                offset = curvature * 0.3 * optimization

                keyframes.append({
                    'frame': frame,
                    'location': [point[0], point[1] + offset, 0],
                    'racing_line': True,
                })
            else:
                keyframes.append({
                    'frame': frame,
                    'location': [point[0], point[1], 0],
                })

        vehicle['path_keyframes'] = keyframes
        logger.debug(f"Applied racing line with optimization={optimization}")

    @staticmethod
    def apply_acceleration_curve(
        vehicle: Any,
        profile: DriverProfile,
        target_speed: float,
        frame_range: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """
        Apply driver-specific acceleration/braking curves.

        Aggressive drivers = harder acceleration/braking
        Smooth drivers = gradual speed changes

        Args:
            vehicle: Vehicle object
            profile: Driver profile
            target_speed: Target speed in m/s
            frame_range: Frame range for acceleration

        Returns:
            List of speed keyframes
        """
        start_frame, end_frame = frame_range
        duration = end_frame - start_frame

        # Aggressive = faster acceleration (fewer frames to reach speed)
        aggression_factor = 0.5 + profile.aggression * 0.5
        accel_frames = int(duration * (1 - aggression_factor * 0.5))

        speed_keyframes = [
            {'frame': start_frame, 'speed': 0},
            {'frame': start_frame + accel_frames, 'speed': target_speed},
            {'frame': end_frame, 'speed': target_speed},
        ]

        vehicle['speed_keyframes'] = speed_keyframes
        return speed_keyframes

    @staticmethod
    def generate_correction_keyframes(
        vehicle: Any,
        profile: DriverProfile,
        frame_range: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """
        Generate steering correction keyframes for nervous/inexperienced drivers.

        Low skill = more corrections needed
        Low consistency = more frequent corrections

        Args:
            vehicle: Vehicle object
            profile: Driver profile
            frame_range: Frame range

        Returns:
            List of correction keyframes
        """
        corrections = []

        # Only add corrections for less skilled drivers
        if profile.skill_level > 0.7:
            return corrections

        start_frame, end_frame = frame_range

        # Correction frequency based on skill and consistency
        correction_chance = (1 - profile.skill_level) * (1 - profile.consistency)
        correction_interval = max(12, int(48 * profile.skill_level))  # Frames between corrections

        current_frame = start_frame + correction_interval
        while current_frame < end_frame:
            if random.random() < correction_chance:
                # Generate small steering correction
                correction_angle = random.uniform(-5, 5) * (1 - profile.skill_level)
                corrections.append({
                    'frame': current_frame,
                    'type': 'steering_correction',
                    'angle': correction_angle,
                    'duration': random.randint(3, 8),
                })

            current_frame += correction_interval

        vehicle['correction_keyframes'] = corrections
        return corrections


def get_driver_profile(preset_name: str) -> DriverProfile:
    """
    Get a driver profile by preset name.

    Args:
        preset_name: Name of preset ('stunt_driver', 'race_driver',
                     'average_driver', 'nervous_driver')

    Returns:
        DriverProfile instance (defaults to 'average_driver' if not found)
    """
    return DRIVER_PRESETS.get(preset_name, DRIVER_PRESETS['average_driver'])


def list_driver_presets() -> List[str]:
    """
    List available driver preset names.

    Returns:
        List of preset names
    """
    return list(DRIVER_PRESETS.keys())


def create_custom_driver_profile(
    name: str,
    skill_level: float = 0.5,
    aggression: float = 0.5,
    smoothness: float = 0.5,
    consistency: float = 0.5
) -> DriverProfile:
    """
    Create a custom driver profile.

    Args:
        name: Profile name
        skill_level: 0 (amateur) to 1 (expert)
        aggression: 0 (cautious) to 1 (aggressive)
        smoothness: 0 (jerky) to 1 (smooth)
        consistency: 0 (variable) to 1 (consistent)

    Returns:
        New DriverProfile instance
    """
    return DriverProfile(
        name=name,
        skill_level=max(0, min(1, skill_level)),
        aggression=max(0, min(1, aggression)),
        smoothness=max(0, min(1, smoothness)),
        consistency=max(0, min(1, consistency)),
    )
