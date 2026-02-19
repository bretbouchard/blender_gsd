"""
Follow Camera Mode Transitions

Implements smooth transitions between camera modes:
- Cut: Instant transition (no interpolation)
- Blend: Smooth blend between positions
- Orbit: Orbit transition around subject
- Dolly: Physical dolly-like movement

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-56
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Callable, Dict, Any

from .types import (
    TransitionType,
    FollowCameraConfig,
    CameraState,
    FollowMode,
)

# Blender API guard for testing outside Blender
try:
    import mathutils
    from mathutils import Vector, Matrix, Euler
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Import fallback Vector from follow_modes
    from .follow_modes import Vector


class TransitionState:
    """
    Tracks the state of an active transition.

    Attributes:
        start_position: Camera position at transition start
        start_rotation: Camera rotation at transition start (yaw, pitch, roll)
        start_mode: Mode at transition start
        target_position: Target camera position
        target_rotation: Target camera rotation
        target_mode: Target mode
        progress: Current progress (0-1)
        duration: Total transition duration in seconds
        transition_type: Type of transition being performed
    """
    def __init__(
        self,
        start_position: Tuple[float, float, float],
        start_rotation: Tuple[float, float, float],
        start_mode: FollowMode,
        target_position: Tuple[float, float, float],
        target_rotation: Tuple[float, float, float],
        target_mode: FollowMode,
        duration: float,
        transition_type: TransitionType = TransitionType.BLEND,
    ):
        self.start_position = start_position
        self.start_rotation = start_rotation
        self.start_mode = start_mode
        self.target_position = target_position
        self.target_rotation = target_rotation
        self.target_mode = target_mode
        self.progress = 0.0
        self.duration = duration
        self.transition_type = transition_type
        self._elapsed_time = 0.0
        self._is_complete = False

    def update(self, delta_time: float) -> float:
        """
        Update transition progress.

        Args:
            delta_time: Time since last update in seconds

        Returns:
            New progress value (0-1)
        """
        if self._is_complete:
            return 1.0

        self._elapsed_time += delta_time
        self.progress = min(self._elapsed_time / self.duration, 1.0)

        if self.progress >= 1.0:
            self._is_complete = True

        return self.progress

    def is_complete(self) -> bool:
        """Check if transition is complete."""
        return self._is_complete


def calculate_transition_position(
    transition: TransitionState,
    subject_position: Tuple[float, float, float],
) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Calculate camera position during transition.

    Routes to appropriate transition type handler.

    Args:
        transition: Current transition state
        subject_position: Current subject position for orbit transitions

    Returns:
        Tuple of (camera_position, camera_rotation)
    """
    if transition.transition_type == TransitionType.CUT:
        return _transition_cut(transition)
    elif transition.transition_type == TransitionType.BLEND:
        return _transition_blend(transition)
    elif transition.transition_type == TransitionType.ORBIT:
        return _transition_orbit(transition, subject_position)
    elif transition.transition_type == TransitionType.DOLLY:
        return _transition_dolly(transition)
    else:
        # Default to blend
        return _transition_blend(transition)


def _transition_cut(transition: TransitionState) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Instant cut transition - no interpolation.

    Returns target position immediately when progress > 0.
    """
    if transition.progress >= 1.0:
        return (
            Vector(transition.target_position),
            transition.target_rotation,
        )
    else:
        return (
            Vector(transition.start_position),
            transition.start_rotation,
        )


def _transition_blend(transition: TransitionState) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Smooth blend transition between positions.

    Uses smooth interpolation for natural camera movement.
    """
    # Use smooth ease function
    t = _ease_in_out_smoother(transition.progress)

    start_pos = Vector(transition.start_position)
    target_pos = Vector(transition.target_position)

    # Interpolate position
    current_pos = start_pos.lerp(target_pos, t)

    # Interpolate rotation with angle wrapping
    current_rot = _interpolate_rotation(
        transition.start_rotation,
        transition.target_rotation,
        t,
    )

    return current_pos, current_rot


def _transition_orbit(
    transition: TransitionState,
    subject_position: Tuple[float, float, float],
) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Orbit transition around subject.

    Camera orbits around the subject while transitioning,
    creating a cinematic arc movement.
    """
    t = _ease_in_out_smoother(transition.progress)

    start_pos = Vector(transition.start_position)
    target_pos = Vector(transition.target_position)
    subject_pos = Vector(subject_position)

    # Calculate start and target angles relative to subject
    start_offset = start_pos - subject_pos
    target_offset = target_pos - subject_pos

    start_dist = start_offset.length()
    target_dist = target_offset.length()

    # Calculate angles
    start_angle = math.atan2(start_offset.x, start_offset.y)
    target_angle = math.atan2(target_offset.x, target_offset.y)

    # Handle angle wrapping for shortest path
    angle_diff = target_angle - start_angle
    while angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    while angle_diff < -math.pi:
        angle_diff += 2 * math.pi

    # Interpolate angle
    current_angle = start_angle + angle_diff * t

    # Interpolate distance
    current_dist = start_dist + (target_dist - start_dist) * t

    # Interpolate height
    current_height = start_offset.z + (target_offset.z - start_offset.z) * t

    # Calculate new position
    current_pos = Vector((
        subject_pos.x + math.sin(current_angle) * current_dist,
        subject_pos.y + math.cos(current_angle) * current_dist,
        subject_pos.z + current_height,
    ))

    # Calculate rotation to look at subject
    current_rot = _calculate_look_rotation(current_pos, subject_pos)

    return current_pos, current_rot


def _transition_dolly(transition: TransitionState) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Dolly transition - physical camera movement.

    Simulates a physical dolly with acceleration and deceleration.
    """
    # Use custom ease for dolly feel (slow start, fast middle, slow end)
    t = _ease_dolly(transition.progress)

    start_pos = Vector(transition.start_position)
    target_pos = Vector(transition.target_position)

    # Interpolate position
    current_pos = start_pos.lerp(target_pos, t)

    # Interpolate rotation
    current_rot = _interpolate_rotation(
        transition.start_rotation,
        transition.target_rotation,
        t,
    )

    return current_pos, current_rot


# =============================================================================
# EASING FUNCTIONS
# =============================================================================

def _ease_in_out_smoother(t: float) -> float:
    """
    Smoother ease-in-out using cubic interpolation.

    Provides very smooth acceleration and deceleration.
    """
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def _ease_dolly(t: float) -> float:
    """
    Dolly-style easing with distinct acceleration/deceleration phases.

    Mimics physical dolly movement.
    """
    if t < 0.2:
        # Acceleration phase
        return 2.5 * t * t
    elif t < 0.8:
        # Constant speed phase
        return 0.1 + (t - 0.2) * 1.25
    else:
        # Deceleration phase
        dt = t - 0.8
        return 0.85 + 1.25 * dt - 3.125 * dt * dt


def _ease_quadratic_in_out(t: float) -> float:
    """Standard quadratic ease-in-out."""
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - pow(-2 * t + 2, 2) / 2


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _interpolate_rotation(
    start: Tuple[float, float, float],
    target: Tuple[float, float, float],
    t: float,
) -> Tuple[float, float, float]:
    """
    Interpolate between two rotations with angle wrapping.

    Args:
        start: Start rotation (yaw, pitch, roll)
        target: Target rotation
        t: Interpolation factor (0-1)

    Returns:
        Interpolated rotation
    """
    def interp_angle(s: float, tg: float, factor: float) -> float:
        """Interpolate single angle with wrapping."""
        diff = tg - s
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return s + diff * factor

    return (
        interp_angle(start[0], target[0], t),
        interp_angle(start[1], target[1], t),
        interp_angle(start[2], target[2], t),
    )


def _calculate_look_rotation(
    camera_pos: Vector,
    target_pos: Vector,
) -> Tuple[float, float, float]:
    """
    Calculate rotation to look at target.

    Args:
        camera_pos: Camera position
        target_pos: Target position to look at

    Returns:
        Rotation as (yaw, pitch, roll) in degrees
    """
    direction = target_pos - camera_pos
    direction_norm = direction.normalized()

    # Calculate yaw
    yaw = math.degrees(math.atan2(direction_norm.x, direction_norm.y))

    # Calculate pitch
    horizontal_dist = math.sqrt(direction_norm.x ** 2 + direction_norm.y ** 2)
    pitch = math.degrees(math.atan2(direction_norm.z, horizontal_dist))

    # Roll is always 0
    roll = 0.0

    return (yaw, pitch, roll)


# =============================================================================
# TRANSITION MANAGER
# =============================================================================

class TransitionManager:
    """
    Manages active transitions and provides smooth mode switching.

    Usage:
        manager = TransitionManager()

        # Start transition
        manager.start_transition(
            from_state=current_state,
            to_position=target_pos,
            to_rotation=target_rot,
            to_mode=FollowMode.CHASE,
            config=config,
        )

        # Update each frame
        position, rotation, is_complete = manager.update(delta_time, subject_pos)
    """

    def __init__(self):
        self._active_transition: Optional[TransitionState] = None
        self._transition_complete_callback: Optional[Callable] = None

    def is_transitioning(self) -> bool:
        """Check if a transition is in progress."""
        return self._active_transition is not None and not self._active_transition.is_complete()

    def start_transition(
        self,
        from_state: CameraState,
        to_position: Tuple[float, float, float],
        to_rotation: Tuple[float, float, float],
        to_mode: FollowMode,
        config: FollowCameraConfig,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Start a new transition.

        Args:
            from_state: Current camera state
            to_position: Target position
            to_rotation: Target rotation
            to_mode: Target follow mode
            config: Camera configuration for transition settings
            callback: Optional callback when transition completes
        """
        # Cancel any existing transition
        self._active_transition = None

        # Create new transition
        self._active_transition = TransitionState(
            start_position=from_state.position,
            start_rotation=from_state.rotation,
            start_mode=from_state.current_mode,
            target_position=to_position,
            target_rotation=to_rotation,
            target_mode=to_mode,
            duration=config.transition_duration,
            transition_type=config.transition_type,
        )

        self._transition_complete_callback = callback

    def update(
        self,
        delta_time: float,
        subject_position: Tuple[float, float, float],
    ) -> Tuple[Vector, Tuple[float, float, float], bool]:
        """
        Update active transition.

        Args:
            delta_time: Time since last update
            subject_position: Current subject position

        Returns:
            Tuple of (current_position, current_rotation, is_complete)
        """
        if self._active_transition is None:
            return (
                Vector((0.0, 0.0, 0.0)),
                (0.0, 0.0, 0.0),
                True,
            )

        # Update progress
        self._active_transition.update(delta_time)

        # Calculate current position
        position, rotation = calculate_transition_position(
            self._active_transition,
            subject_position,
        )

        is_complete = self._active_transition.is_complete()

        # Call completion callback
        if is_complete and self._transition_complete_callback:
            self._transition_complete_callback()
            self._transition_complete_callback = None

        return position, rotation, is_complete

    def cancel_transition(self) -> None:
        """Cancel the active transition."""
        self._active_transition = None
        self._transition_complete_callback = None

    def get_progress(self) -> float:
        """Get current transition progress (0-1), or 1.0 if no transition."""
        if self._active_transition is None:
            return 1.0
        return self._active_transition.progress

    def get_target_mode(self) -> Optional[FollowMode]:
        """Get target mode of active transition, or None if no transition."""
        if self._active_transition is None:
            return None
        return self._active_transition.target_mode


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_instant_transition() -> FollowCameraConfig:
    """Create config for instant (cut) transition."""
    return FollowCameraConfig(
        transition_type=TransitionType.CUT,
        transition_duration=0.0,
    )


def create_smooth_transition(duration: float = 0.5) -> FollowCameraConfig:
    """Create config for smooth blend transition."""
    return FollowCameraConfig(
        transition_type=TransitionType.BLEND,
        transition_duration=duration,
    )


def create_orbit_transition(duration: float = 0.75) -> FollowCameraConfig:
    """Create config for orbit transition."""
    return FollowCameraConfig(
        transition_type=TransitionType.ORBIT,
        transition_duration=duration,
    )


def create_dolly_transition(duration: float = 1.0) -> FollowCameraConfig:
    """Create config for dolly transition."""
    return FollowCameraConfig(
        transition_type=TransitionType.DOLLY,
        transition_duration=duration,
    )
