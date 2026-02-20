"""
Stunt Coordination Module

Plans and animates stunt sequences for multiple vehicles.
Supports drifts, jumps, barrel rolls, and formations.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging
import math

from ..types import StuntType

logger = logging.getLogger(__name__)

# Physics constants
GRAVITY = 9.81  # m/s²
FRAME_RATE = 24


@dataclass
class StuntMarkerData:
    """Internal data for a planned stunt."""
    frame: int
    stunt_type: StuntType
    vehicles: List[Any]
    duration_frames: int
    intensity: float
    notes: str
    start_position: Optional[Tuple[float, float, float]]
    end_position: Optional[Tuple[float, float, float]]
    keyframes: List[Dict[str, Any]] = field(default_factory=list)
    camera_suggestion: Optional[str] = None


class StuntCoordinator:
    """
    Coordinates stunt sequences for multiple vehicles.

    Supports planning and animating:
    - Jumps with parabolic trajectories
    - Drifts with body roll
    - Barrel rolls
    - Formation driving
    - Chase sequences
    """

    def __init__(self, frame_rate: int = FRAME_RATE):
        """
        Initialize stunt coordinator.

        Args:
            frame_rate: Frames per second
        """
        self.frame_rate = frame_rate
        self.markers: List[StuntMarkerData] = []
        self.safety_check_enabled: bool = True
        self._shot_list: List[Dict[str, Any]] = []

    def plan_stunt(
        self,
        stunt_type: StuntType,
        vehicles: List[Any],
        start_frame: int,
        duration_frames: int = 24,
        intensity: float = 1.0,
        notes: str = ""
    ) -> StuntMarkerData:
        """
        Plan a stunt sequence.

        Args:
            stunt_type: Type of stunt to perform
            vehicles: List of vehicle objects
            start_frame: Starting frame
            duration_frames: Duration in frames
            intensity: Stunt intensity 0-1 (affects extremity)
            notes: Optional notes for the stunt

        Returns:
            Created StuntMarkerData
        """
        # Clamp intensity
        intensity = max(0.0, min(1.0, intensity))

        # Get start position from first vehicle
        start_pos = None
        if vehicles:
            v = vehicles[0]
            if hasattr(v, 'get'):
                start_pos = tuple(v.get('location', [0, 0, 0]))

        marker = StuntMarkerData(
            frame=start_frame,
            stunt_type=stunt_type,
            vehicles=vehicles,
            duration_frames=duration_frames,
            intensity=intensity,
            notes=notes,
            start_position=start_pos,
            end_position=None,
            keyframes=[],
            camera_suggestion=self._get_camera_suggestion(stunt_type),
        )

        # Generate animation based on stunt type
        if stunt_type == StuntType.DRIFT:
            self._animate_drift(vehicles, marker)
        elif stunt_type == StuntType.JUMP:
            self._animate_jump(vehicles, marker)
        elif stunt_type == StuntType.BARREL_ROLL:
            self._animate_barrel_roll(vehicles, marker)
        elif stunt_type == StuntType.FORMATION:
            self._animate_formation(vehicles, marker)

        self.markers.append(marker)
        logger.info(f"Planned {stunt_type.value} stunt at frame {start_frame}")

        return marker

    def _get_camera_suggestion(self, stunt_type: StuntType) -> str:
        """Get suggested camera setup for a stunt type."""
        suggestions = {
            StuntType.JUMP: "Wide shot from side, low angle to emphasize height",
            StuntType.DRIFT: "Tracking shot following drift arc",
            StuntType.BARREL_ROLL: "Wide shot, center frame on rotation axis",
            StuntType.J_TURN: "Overhead or high angle for 180 visibility",
            StuntType.BOOTLEG: "Low angle from rear quarter",
            StuntType.T_BONE: "Wide intersection shot",
            StuntType.PURSUIT: "Multiple cameras, tracking shots",
            StuntType.FORMATION: "High angle or helicopter shot",
        }
        return suggestions.get(stunt_type, "Standard coverage")

    def _animate_drift(self, vehicles: List[Any], marker: StuntMarkerData) -> None:
        """
        Animate a drift maneuver.

        Drift involves:
        - Lateral slide
        - Body roll (tilt)
        - Counter-steering
        - Optional tire smoke
        """
        for vehicle in vehicles:
            start_frame = marker.frame
            duration = marker.duration_frames
            intensity = marker.intensity

            # Drift angle based on intensity (15-45 degrees)
            drift_angle = 15 + intensity * 30

            # Body roll based on intensity (3-10 degrees)
            body_roll = 3 + intensity * 7

            # Create drift keyframes
            keyframes = [
                {
                    'frame': start_frame,
                    'location': [0, 0, 0],
                    'rotation': [0, 0, 0],
                    'phase': 'entry',
                },
                {
                    'frame': start_frame + duration // 4,
                    'location': [5, 1 * intensity, 0],
                    'rotation': [math.radians(body_roll), 0, math.radians(drift_angle / 2)],
                    'phase': 'initiation',
                },
                {
                    'frame': start_frame + duration // 2,
                    'location': [15, 3 * intensity, 0],
                    'rotation': [math.radians(body_roll * 1.2), 0, math.radians(drift_angle)],
                    'phase': 'hold',
                },
                {
                    'frame': start_frame + 3 * duration // 4,
                    'location': [25, 2 * intensity, 0],
                    'rotation': [math.radians(body_roll * 0.5), 0, math.radians(drift_angle / 2)],
                    'phase': 'exit',
                },
                {
                    'frame': start_frame + duration,
                    'location': [35, 0, 0],
                    'rotation': [0, 0, 0],
                    'phase': 'recovery',
                },
            ]

            marker.keyframes = keyframes
            vehicle['drift_keyframes'] = keyframes

    def _animate_jump(self, vehicles: List[Any], marker: StuntMarkerData) -> None:
        """
        Animate a vehicle jump with parabolic trajectory.

        Uses projectile motion physics:
        - Ramp angle affects trajectory
        - Gravity constant for arc calculation
        - Landing compression on suspension
        """
        for vehicle in vehicles:
            start_frame = marker.frame
            duration = marker.duration_frames
            intensity = marker.intensity

            # Jump parameters based on intensity
            ramp_angle = 20 + intensity * 25  # 20-45 degrees
            takeoff_speed = 15 + intensity * 20  # m/s

            # Calculate trajectory
            ramp_rad = math.radians(ramp_angle)
            v_vertical = takeoff_speed * math.sin(ramp_rad)
            v_horizontal = takeoff_speed * math.cos(ramp_rad)

            # Time in air: t = 2 * v_y / g
            air_time = 2 * v_vertical / GRAVITY
            air_frames = int(air_time * self.frame_rate)

            # Peak height: h = v_y² / (2g)
            peak_height = (v_vertical ** 2) / (2 * GRAVITY)

            # Horizontal distance
            jump_distance = v_horizontal * air_time

            # Suspension compression on landing (10-15% of typical 0.15m travel)
            landing_compression = 0.015 + intensity * 0.0075

            keyframes = []

            # Pre-jump approach
            keyframes.append({
                'frame': start_frame,
                'location': [-10, 0, 0],
                'rotation': [0, 0, 0],
                'phase': 'approach',
            })

            # Takeoff
            keyframes.append({
                'frame': start_frame + duration // 4,
                'location': [0, 0, 0.1],
                'rotation': [0, math.radians(ramp_angle), 0],
                'phase': 'takeoff',
            })

            # Peak of jump (midpoint)
            peak_frame = start_frame + duration // 2
            keyframes.append({
                'frame': peak_frame,
                'location': [jump_distance / 2, 0, peak_height],
                'rotation': [0, 0, 0],
                'phase': 'apex',
            })

            # Landing
            landing_frame = start_frame + 3 * duration // 4
            keyframes.append({
                'frame': landing_frame,
                'location': [jump_distance, 0, landing_compression],
                'rotation': [math.radians(-ramp_angle / 3), 0, 0],
                'phase': 'landing',
            })

            # Recovery
            keyframes.append({
                'frame': start_frame + duration,
                'location': [jump_distance + 10, 0, 0],
                'rotation': [0, 0, 0],
                'phase': 'recovery',
            })

            marker.keyframes = keyframes
            marker.end_position = (jump_distance + 10, 0, 0)
            vehicle['jump_keyframes'] = keyframes

    def _animate_barrel_roll(self, vehicles: List[Any], marker: StuntMarkerData) -> None:
        """
        Animate a 360° barrel roll.

        Roll axis is typically local X for forward-moving car.
        Includes suspension preload before takeoff.
        """
        for vehicle in vehicles:
            start_frame = marker.frame
            duration = marker.duration_frames
            intensity = marker.intensity

            # Roll speed based on intensity
            roll_frames = int(duration * 0.6)  # Roll takes 60% of stunt duration

            keyframes = [
                {
                    'frame': start_frame,
                    'location': [0, 0, 0],
                    'rotation': [0, 0, 0],
                    'phase': 'approach',
                },
                # Suspension preload
                {
                    'frame': start_frame + duration // 8,
                    'location': [5, 0, -0.05],
                    'rotation': [0, 0, 0],
                    'phase': 'preload',
                },
                # Takeoff
                {
                    'frame': start_frame + duration // 4,
                    'location': [10, 0, 0.2],
                    'rotation': [math.radians(45), 0, 0],
                    'phase': 'takeoff',
                },
                # Mid-roll
                {
                    'frame': start_frame + duration // 2,
                    'location': [25, 0, peak_height := 0.8 + intensity * 0.5],
                    'rotation': [math.radians(180), 0, 0],
                    'phase': 'inverted',
                },
                # Coming around
                {
                    'frame': start_frame + 3 * duration // 4,
                    'location': [40, 0, 0.3],
                    'rotation': [math.radians(315), 0, 0],
                    'phase': 'rotation_complete',
                },
                # Landing
                {
                    'frame': start_frame + duration,
                    'location': [50, 0, 0],
                    'rotation': [0, 0, 0],
                    'phase': 'landing',
                },
            ]

            marker.keyframes = keyframes
            vehicle['barrel_roll_keyframes'] = keyframes

    def _animate_formation(self, vehicles: List[Any], marker: StuntMarkerData) -> None:
        """
        Animate vehicles into formation (wedge, v-shape, line).

        Args:
            vehicles: List of vehicles
            marker: Stunt marker for the formation
        """
        if len(vehicles) < 2:
            logger.warning("Formation requires at least 2 vehicles")
            return

        intensity = marker.intensity
        duration = marker.duration_frames
        start_frame = marker.frame

        # Formation offset patterns
        formations = {
            'wedge': [(0, 0), (-5, 3), (-5, -3), (-10, 6), (-10, -6)],
            'v_shape': [(-5, 0), (0, 4), (0, -4), (5, 8), (5, -8)],
            'line': [(0, 0), (0, 4), (0, -4), (0, 8), (0, -8)],
        }

        # Use wedge as default
        pattern = formations['wedge']

        for i, vehicle in enumerate(vehicles):
            if i >= len(pattern):
                break

            offset_x, offset_y = pattern[i]

            keyframes = [
                {
                    'frame': start_frame,
                    'location': [i * 10, 0, 0],  # Start in line
                    'phase': 'start',
                },
                {
                    'frame': start_frame + duration // 2,
                    'location': [50 + offset_x, offset_y, 0],
                    'phase': 'forming',
                },
                {
                    'frame': start_frame + duration,
                    'location': [100 + offset_x, offset_y, 0],
                    'phase': 'hold',
                },
            ]

            vehicle['formation_keyframes'] = keyframes

    def safety_check(self, frame_range: Tuple[int, int]) -> List[str]:
        """
        Check for potential collisions in frame range.

        Args:
            frame_range: (start_frame, end_frame) to check

        Returns:
            List of warning messages about potential collisions
        """
        warnings = []

        if not self.safety_check_enabled:
            return warnings

        # Simple overlap check between stunts
        for i, marker1 in enumerate(self.markers):
            for marker2 in self.markers[i + 1:]:
                # Check frame overlap
                end1 = marker1.frame + marker1.duration_frames
                end2 = marker2.frame + marker2.duration_frames

                if (marker1.frame <= marker2.frame < end1 or
                    marker2.frame <= marker1.frame < end2):
                    # Check if same vehicles involved
                    common_vehicles = set(id(v) for v in marker1.vehicles) & set(id(v) for v in marker2.vehicles)
                    if common_vehicles:
                        warnings.append(
                            f"Vehicle overlap between {marker1.stunt_type.value} "
                            f"(frame {marker1.frame}) and {marker2.stunt_type.value} "
                            f"(frame {marker2.frame})"
                        )

        return warnings

    def generate_shot_list(self) -> List[Dict[str, Any]]:
        """
        Generate shot list from stunt markers with camera suggestions.

        Returns:
            List of shot dictionaries with frame, type, and camera info
        """
        shot_list = []

        for marker in self.markers:
            shot = {
                'frame': marker.frame,
                'end_frame': marker.frame + marker.duration_frames,
                'stunt_type': marker.stunt_type.value,
                'vehicles': [getattr(v, 'name', f'vehicle_{i}') for i, v in enumerate(marker.vehicles)],
                'camera_suggestion': marker.camera_suggestion,
                'intensity': marker.intensity,
                'notes': marker.notes,
                'duration_seconds': marker.duration_frames / self.frame_rate,
            }
            shot_list.append(shot)

        self._shot_list = shot_list
        return shot_list


def create_stunt_coordinator(frame_rate: int = FRAME_RATE) -> StuntCoordinator:
    """
    Factory function for stunt coordinator.

    Args:
        frame_rate: Frames per second

    Returns:
        New StuntCoordinator instance
    """
    return StuntCoordinator(frame_rate=frame_rate)


# Alias for backward compatibility
StuntMarker = StuntMarkerData
