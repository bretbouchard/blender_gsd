"""
Launch Control Module

Manages vehicle launch sequences for cinematic scenes.
Supports staging, countdown, and synchronized launches.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging

from ..types import LaunchConfig, LaunchState

logger = logging.getLogger(__name__)


@dataclass
class StagedVehicle:
    """A vehicle staged for launch."""
    vehicle: Any
    config: LaunchConfig
    start_position: Tuple[float, float, float]
    start_rotation: Tuple[float, float, float]
    countdown_markers: List[Dict[str, Any]] = field(default_factory=list)


class LaunchController:
    """
    Manages vehicle launch sequences.

    Supports:
    - Staging multiple vehicles
    - Countdown sequences with audio sync markers
    - Synchronized or staggered launches
    - Emergency abort functionality
    """

    FRAME_RATE = 24  # Default frame rate

    def __init__(self, frame_rate: int = 24):
        """
        Initialize launch controller.

        Args:
            frame_rate: Frames per second for timing calculations
        """
        self.frame_rate = frame_rate
        self._vehicles: Dict[str, StagedVehicle] = {}
        self.state: LaunchState = LaunchState.STAGED
        self.current_frame: int = 0
        self.countdown_start_frame: int = 0
        self._audio_markers: List[Dict[str, Any]] = []

    def stage_vehicle(
        self,
        vehicle: Any,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float] = (0, 0, 0),
        config: Optional[LaunchConfig] = None
    ) -> None:
        """
        Position vehicle at launch staging area.

        Args:
            vehicle: The vehicle object to stage
            position: World position for staging
            rotation: Rotation in degrees (x, y, z)
            config: Launch configuration (uses defaults if None)
        """
        vehicle_id = getattr(vehicle, 'name', f'vehicle_{len(self._vehicles)}')

        if config is None:
            config = LaunchConfig(vehicle_id=vehicle_id)

        staged = StagedVehicle(
            vehicle=vehicle,
            config=config,
            start_position=position,
            start_rotation=rotation,
            countdown_markers=[],
        )

        # Set vehicle position
        if hasattr(vehicle, 'location'):
            vehicle['location'] = list(position)
        if hasattr(vehicle, 'rotation_euler'):
            vehicle['rotation_euler'] = list(rotation)

        self._vehicles[vehicle_id] = staged
        logger.info(f"Staged vehicle: {vehicle_id} at {position}")

    def start_countdown(self, start_frame: int) -> None:
        """
        Begin countdown sequence with audio sync markers.

        Creates countdown markers for each second before launch.

        Args:
            start_frame: Frame to start countdown
        """
        self.countdown_start_frame = start_frame
        self.state = LaunchState.COUNTDOWN

        # Create countdown markers for all staged vehicles
        for vehicle_id, staged in self._vehicles.items():
            countdown_seconds = staged.config.countdown_seconds

            staged.countdown_markers = []
            for i in range(countdown_seconds, 0, -1):
                marker_frame = start_frame + (countdown_seconds - i) * self.frame_rate
                marker = {
                    'frame': marker_frame,
                    'type': 'countdown',
                    'value': i,
                    'audio_sync': f'countdown_{i}',
                }
                staged.countdown_markers.append(marker)
                self._audio_markers.append(marker)

            # Add "GO" marker at launch frame
            go_frame = start_frame + countdown_seconds * self.frame_rate
            go_marker = {
                'frame': go_frame,
                'type': 'launch',
                'value': 'GO',
                'audio_sync': 'launch_go',
            }
            staged.countdown_markers.append(go_marker)
            self._audio_markers.append(go_marker)

        logger.info(f"Started countdown at frame {start_frame}")

    def launch(self, frame: int) -> None:
        """
        Execute launch sequence for all staged vehicles.

        Args:
            frame: Frame to execute launch
        """
        if self.state == LaunchState.ABORTED:
            logger.warning("Cannot launch - sequence was aborted")
            return

        self.state = LaunchState.LAUNCHING

        for vehicle_id, staged in self._vehicles.items():
            self._apply_launch_animation(
                staged.vehicle,
                staged.config,
                frame
            )

        self.state = LaunchState.RUNNING
        logger.info(f"Launched {len(self._vehicles)} vehicles at frame {frame}")

    def _apply_launch_animation(
        self,
        vehicle: Any,
        config: LaunchConfig,
        start_frame: int
    ) -> None:
        """
        Create launch keyframes with proper easing.

        Applies acceleration from 0 to target_speed over
        calculated frames based on acceleration rate.

        Args:
            vehicle: Vehicle to animate
            config: Launch configuration
            start_frame: Starting frame for launch
        """
        # Calculate frames needed to reach target speed
        # v = a * t, so t = v / a
        # Convert km/h to m/s: m/s = km/h / 3.6
        target_speed_ms = config.target_speed / 3.6
        time_to_speed = target_speed_ms / config.acceleration  # seconds
        frames_to_speed = int(time_to_speed * self.frame_rate)

        # Create keyframes (mock for testing)
        keyframes = []

        # Start position
        keyframes.append({
            'frame': start_frame,
            'location': [0, 0, 0],
            'easing': config.easing,
        })

        # Acceleration phase - use ease_out for realistic acceleration feel
        distance_during_accel = 0.5 * config.acceleration * time_to_speed ** 2
        accel_end_frame = start_frame + frames_to_speed

        keyframes.append({
            'frame': accel_end_frame,
            'location': [distance_during_accel, 0, 0],
            'easing': 'linear',  # Constant speed after acceleration
        })

        # If hold_at_end, add final hold position
        if config.hold_at_end:
            hold_distance = distance_during_accel + target_speed_ms * 2  # 2 seconds of travel
            keyframes.append({
                'frame': accel_end_frame + 2 * self.frame_rate,
                'location': [hold_distance, 0, 0],
                'easing': 'linear',
            })

        # Store keyframes on vehicle (mock)
        vehicle['launch_keyframes'] = keyframes

        logger.debug(f"Applied launch animation: {len(keyframes)} keyframes")

    def abort(self, frame: int) -> None:
        """
        Emergency abort - stop all vehicles immediately.

        Args:
            frame: Frame to execute abort
        """
        self.state = LaunchState.ABORTED

        for vehicle_id, staged in self._vehicles.items():
            # Add immediate stop keyframe
            if hasattr(staged.vehicle, 'location'):
                current_loc = staged.vehicle.get('location', [0, 0, 0])
                staged.vehicle['abort_frame'] = frame
                staged.vehicle['abort_location'] = current_loc

        logger.warning(f"Launch aborted at frame {frame}")

    def reset(self) -> None:
        """Reset all vehicles to staged state."""
        for vehicle_id, staged in self._vehicles.items():
            # Reset to start position
            if hasattr(staged.vehicle, 'location'):
                staged.vehicle['location'] = list(staged.start_position)
            if hasattr(staged.vehicle, 'rotation_euler'):
                staged.vehicle['rotation_euler'] = list(staged.start_rotation)

            # Clear markers
            staged.countdown_markers = []

        self._audio_markers = []
        self.state = LaunchState.STAGED
        self.current_frame = 0
        logger.info("Launch controller reset")

    def get_audio_markers(self) -> List[Dict[str, Any]]:
        """
        Get all audio sync markers for the launch sequence.

        Returns:
            List of marker dictionaries with frame and sync info
        """
        return self._audio_markers.copy()

    def get_staged_vehicles(self) -> List[str]:
        """Get list of staged vehicle IDs."""
        return list(self._vehicles.keys())

    def get_countdown_frames(self) -> Dict[str, int]:
        """
        Get countdown frame information.

        Returns:
            Dictionary with countdown_start and launch_frame
        """
        if not self._vehicles:
            return {}

        # Use first vehicle's countdown for timing
        first_staged = next(iter(self._vehicles.values()))
        countdown_seconds = first_staged.config.countdown_seconds

        return {
            'countdown_start': self.countdown_start_frame,
            'launch_frame': self.countdown_start_frame + countdown_seconds * self.frame_rate,
        }


def create_launch_controller(frame_rate: int = 24) -> LaunchController:
    """
    Factory function for launch controller.

    Args:
        frame_rate: Frames per second

    Returns:
        New LaunchController instance
    """
    return LaunchController(frame_rate=frame_rate)
