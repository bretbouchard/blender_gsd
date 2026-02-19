"""
Conditional Visibility System for Anamorphic Projection

Implements camera-triggered visibility with smooth transitions.
Works with animated cameras and zone boundaries.

Part of Phase 9.5 - Conditional Visibility (REQ-ANAM-06)
Beads: blender_gsd-39
"""

from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .zones import (
    CameraZone,
    ZoneManager,
    ZoneState,
    ZoneTransition,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    Vector = None


class VisibilityTransition:
    """Types of visibility transitions."""
    INSTANT = "instant"         # Immediate on/off
    FADE = "fade"               # Alpha fade
    SCALE = "scale"             # Scale up/down
    TRANSLATE = "translate"     # Slide in/out
    CUSTOM = "custom"           # Custom animation


@dataclass
class VisibilityTarget:
    """
    Target object for visibility control.

    Defines how an object's visibility should respond to
    camera position changes.
    """
    # Object name in Blender
    object_name: str

    # Transition type
    transition_type: str = VisibilityTransition.FADE

    # Transition duration (seconds)
    transition_duration: float = 0.5

    # Delay before transition starts (seconds)
    transition_delay: float = 0.0

    # Easing function for transition ("linear", "ease_in", "ease_out", "ease_in_out")
    easing: str = "ease_in_out"

    # Minimum visibility (0.0 = fully hidden, 1.0 = fully visible)
    min_visibility: float = 0.0

    # Maximum visibility
    max_visibility: float = 1.0

    # Whether to use material alpha for fade
    use_material_alpha: bool = True

    # Whether to use object hide for instant transition
    use_object_hide: bool = False

    # Custom property name to drive (if not using defaults)
    custom_property: str = ""

    # Optional: Animation data path (for animation-based transitions)
    animation_data_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_name": self.object_name,
            "transition_type": self.transition_type,
            "transition_duration": self.transition_duration,
            "transition_delay": self.transition_delay,
            "easing": self.easing,
            "min_visibility": self.min_visibility,
            "max_visibility": self.max_visibility,
            "use_material_alpha": self.use_material_alpha,
            "use_object_hide": self.use_object_hide,
            "custom_property": self.custom_property,
            "animation_data_path": self.animation_data_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VisibilityTarget:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object_name", ""),
            transition_type=data.get("transition_type", VisibilityTransition.FADE),
            transition_duration=data.get("transition_duration", 0.5),
            transition_delay=data.get("transition_delay", 0.0),
            easing=data.get("easing", "ease_in_out"),
            min_visibility=data.get("min_visibility", 0.0),
            max_visibility=data.get("max_visibility", 1.0),
            use_material_alpha=data.get("use_material_alpha", True),
            use_object_hide=data.get("use_object_hide", False),
            custom_property=data.get("custom_property", ""),
            animation_data_path=data.get("animation_data_path", ""),
        )


@dataclass
class VisibilityState:
    """Current visibility state for an object."""
    object_name: str
    current_visibility: float  # 0.0 to 1.0
    target_visibility: float   # Where we're transitioning to
    transition_progress: float  # 0.0 to 1.0 (1.0 = complete)
    is_transitioning: bool
    transition_start_time: float = 0.0
    start_visibility: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "object_name": self.object_name,
            "current_visibility": self.current_visibility,
            "target_visibility": self.target_visibility,
            "transition_progress": self.transition_progress,
            "is_transitioning": self.is_transitioning,
            "transition_start_time": self.transition_start_time,
            "start_visibility": self.start_visibility,
        }


@dataclass
class VisibilityConfig:
    """Configuration for visibility system."""
    # Update rate (times per second)
    update_rate: float = 60.0

    # Whether to use frame-based timing
    use_frame_timing: bool = True

    # Default transition duration
    default_duration: float = 0.5

    # Default easing
    default_easing: str = "ease_in_out"

    # Whether to animate in viewport
    animate_viewport: bool = True

    # Whether to keyframe visibility changes
    keyframe_changes: bool = False

    # Frame range for keyframes (start, end)
    keyframe_range: Tuple[int, int] = (1, 250)


class VisibilityController:
    """
    Controls object visibility based on camera position zones.

    Manages transitions, timing, and applies visibility changes
    to objects in the scene.
    """

    def __init__(self, config: Optional[VisibilityConfig] = None):
        self.config = config or VisibilityConfig()
        self.targets: Dict[str, VisibilityTarget] = {}
        self.states: Dict[str, VisibilityState] = {}
        self._zone_manager: Optional[ZoneManager] = None
        self._last_update_time: float = 0.0
        self._last_frame: int = -1

    def add_target(self, target: VisibilityTarget) -> None:
        """Add a visibility target."""
        self.targets[target.object_name] = target
        # Initialize state
        if target.object_name not in self.states:
            self.states[target.object_name] = VisibilityState(
                object_name=target.object_name,
                current_visibility=target.min_visibility,
                target_visibility=target.min_visibility,
                transition_progress=1.0,
                is_transitioning=False,
            )

    def remove_target(self, object_name: str) -> bool:
        """Remove a visibility target."""
        if object_name in self.targets:
            del self.targets[object_name]
            if object_name in self.states:
                del self.states[object_name]
            return True
        return False

    def get_target(self, object_name: str) -> Optional[VisibilityTarget]:
        """Get a visibility target by object name."""
        return self.targets.get(object_name)

    def set_zone_manager(self, manager: ZoneManager) -> None:
        """Set the zone manager for visibility evaluation."""
        self._zone_manager = manager

    def update(
        self,
        camera_position: Tuple[float, float, float],
        frame: int = 0,
        delta_time: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Update visibility based on camera position.

        Args:
            camera_position: Current camera world position
            frame: Current frame number
            delta_time: Time since last update (auto-calculated if None)

        Returns:
            Dictionary of object_name -> visibility (0.0-1.0)
        """
        current_time = time.time()

        if delta_time is None:
            if self._last_update_time > 0:
                delta_time = current_time - self._last_update_time
            else:
                delta_time = 1.0 / self.config.update_rate

        self._last_update_time = current_time

        # Get zone evaluation
        if self._zone_manager:
            zone_state = self._zone_manager.evaluate(camera_position, frame)
        else:
            zone_state = ZoneState()

        # Update each target
        visibility_results = {}

        for obj_name, target in self.targets.items():
            # Get visibility factor from zone state
            zone_factor = zone_state.object_visibility.get(obj_name, target.min_visibility)

            # Map zone factor to visibility range
            target_visibility = (
                target.min_visibility + zone_factor * (target.max_visibility - target.min_visibility)
            )

            # Update state
            state = self.states.get(obj_name)
            if state is None:
                state = VisibilityState(
                    object_name=obj_name,
                    current_visibility=target_visibility,
                    target_visibility=target_visibility,
                    transition_progress=1.0,
                    is_transitioning=False,
                )
                self.states[obj_name] = state

            # Check if target changed
            if abs(state.target_visibility - target_visibility) > 0.001:
                # Start new transition
                state.target_visibility = target_visibility
                state.start_visibility = state.current_visibility
                state.transition_progress = 0.0
                state.is_transitioning = True
                state.transition_start_time = current_time + target.transition_delay

            # Update ongoing transition
            if state.is_transitioning:
                if current_time >= state.transition_start_time:
                    # Apply delay
                    effective_start = state.transition_start_time
                    elapsed = current_time - effective_start
                    duration = target.transition_duration

                    if duration > 0:
                        progress = min(1.0, elapsed / duration)
                    else:
                        progress = 1.0

                    # Apply easing
                    eased_progress = self._apply_easing(progress, target.easing)

                    # Calculate current visibility
                    state.current_visibility = (
                        state.start_visibility + eased_progress * (state.target_visibility - state.start_visibility)
                    )
                    state.transition_progress = progress

                    if progress >= 1.0:
                        state.is_transitioning = False
                        state.current_visibility = state.target_visibility

            visibility_results[obj_name] = state.current_visibility

            # Apply to Blender if available
            if HAS_BLENDER and self.config.animate_viewport:
                self._apply_visibility(obj_name, state.current_visibility, target)

            # Keyframe if enabled
            if self.config.keyframe_changes and frame != self._last_frame:
                self._keyframe_visibility(obj_name, state.current_visibility, frame)

        self._last_frame = frame
        return visibility_results

    def force_visibility(
        self,
        object_name: str,
        visibility: float,
        immediate: bool = False,
    ) -> None:
        """
        Force a specific visibility value for an object.

        Args:
            object_name: Object to modify
            visibility: Target visibility (0.0-1.0)
            immediate: If True, skip transition
        """
        if object_name not in self.states:
            return

        state = self.states[object_name]
        target = self.targets.get(object_name)

        if immediate:
            state.current_visibility = visibility
            state.target_visibility = visibility
            state.transition_progress = 1.0
            state.is_transitioning = False
        else:
            state.target_visibility = visibility
            state.start_visibility = state.current_visibility
            state.transition_progress = 0.0
            state.is_transitioning = True
            state.transition_start_time = time.time()

        # Apply immediately
        if HAS_BLENDER and target:
            self._apply_visibility(object_name, state.current_visibility, target)

    def get_state(self, object_name: str) -> Optional[VisibilityState]:
        """Get current visibility state for an object."""
        return self.states.get(object_name)

    def get_all_states(self) -> Dict[str, VisibilityState]:
        """Get all visibility states."""
        return dict(self.states)

    def clear(self) -> None:
        """Clear all targets and states."""
        self.targets.clear()
        self.states.clear()

    def _apply_easing(self, t: float, easing: str) -> float:
        """Apply easing function to progress value."""
        t = max(0.0, min(1.0, t))

        if easing == "linear":
            return t
        elif easing == "ease_in":
            return t * t
        elif easing == "ease_out":
            return 1.0 - (1.0 - t) * (1.0 - t)
        elif easing == "ease_in_out":
            if t < 0.5:
                return 2 * t * t
            else:
                return 1.0 - pow(-2 * t + 2, 2) / 2
        else:
            return t

    def _apply_visibility(
        self,
        object_name: str,
        visibility: float,
        target: VisibilityTarget,
    ) -> None:
        """Apply visibility to Blender object."""
        if not HAS_BLENDER:
            return

        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return

        # Handle object hide
        if target.use_object_hide:
            obj.hide_viewport = visibility < 0.01
            obj.hide_render = visibility < 0.01

        # Handle material alpha
        if target.use_material_alpha and visibility < 1.0:
            for mat_slot in obj.material_slots:
                if mat_slot.material and mat_slot.material.use_nodes:
                    self._set_material_alpha(mat_slot.material, visibility)

        # Handle custom property
        if target.custom_property:
            obj[target.custom_property] = visibility

    def _set_material_alpha(self, material, alpha: float) -> None:
        """Set material alpha for fade effect."""
        if not material.use_nodes:
            return

        nodes = material.node_tree.nodes

        # Find principled BSDF or output node
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                if 'Alpha' in node.inputs:
                    node.inputs['Alpha'].default_value = alpha
                break

    def _keyframe_visibility(
        self,
        object_name: str,
        visibility: float,
        frame: int,
    ) -> None:
        """Insert keyframe for visibility."""
        if not HAS_BLENDER:
            return

        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return

        target = self.targets.get(object_name)
        if target is None:
            return

        # Keyframe custom property
        if target.custom_property:
            obj.keyframe_insert(data_path=f'["{target.custom_property}"]', frame=frame)

        # Keyframe hide
        if target.use_object_hide:
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)
            obj.keyframe_insert(data_path="hide_render", frame=frame)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize controller state to dictionary."""
        return {
            "config": {
                "update_rate": self.config.update_rate,
                "use_frame_timing": self.config.use_frame_timing,
                "default_duration": self.config.default_duration,
                "default_easing": self.config.default_easing,
                "animate_viewport": self.config.animate_viewport,
                "keyframe_changes": self.config.keyframe_changes,
                "keyframe_range": list(self.config.keyframe_range),
            },
            "targets": [t.to_dict() for t in self.targets.values()],
            "states": {k: v.to_dict() for k, v in self.states.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VisibilityController:
        """Create controller from dictionary."""
        config_data = data.get("config", {})
        config = VisibilityConfig(
            update_rate=config_data.get("update_rate", 60.0),
            use_frame_timing=config_data.get("use_frame_timing", True),
            default_duration=config_data.get("default_duration", 0.5),
            default_easing=config_data.get("default_easing", "ease_in_out"),
            animate_viewport=config_data.get("animate_viewport", True),
            keyframe_changes=config_data.get("keyframe_changes", False),
            keyframe_range=tuple(config_data.get("keyframe_range", (1, 250))),
        )

        controller = cls(config)

        for target_data in data.get("targets", []):
            target = VisibilityTarget.from_dict(target_data)
            controller.add_target(target)

        return controller


def create_visibility_target(
    object_name: str,
    transition_type: str = VisibilityTransition.FADE,
    duration: float = 0.5,
    easing: str = "ease_in_out",
    min_visibility: float = 0.0,
    max_visibility: float = 1.0,
) -> VisibilityTarget:
    """
    Convenience function to create a visibility target.

    Args:
        object_name: Name of the object in Blender
        transition_type: How the object should appear/disappear
        duration: Transition duration in seconds
        easing: Easing function for smooth transitions
        min_visibility: Visibility when outside zone
        max_visibility: Visibility when inside zone

    Returns:
        VisibilityTarget configured with the given parameters
    """
    return VisibilityTarget(
        object_name=object_name,
        transition_type=transition_type,
        transition_duration=duration,
        easing=easing,
        min_visibility=min_visibility,
        max_visibility=max_visibility,
    )


def setup_visibility_for_projection(
    controller: VisibilityController,
    zone_manager: ZoneManager,
    object_names: List[str],
    transition_duration: float = 0.5,
) -> None:
    """
    Set up visibility control for projection objects.

    Convenience function to quickly configure visibility for
    typical anamorphic projection setups.

    Args:
        controller: VisibilityController to configure
        zone_manager: ZoneManager with defined zones
        object_names: Objects to control visibility for
        transition_duration: Duration for fade transitions
    """
    controller.set_zone_manager(zone_manager)

    for obj_name in object_names:
        target = create_visibility_target(
            object_name=obj_name,
            transition_type=VisibilityTransition.FADE,
            duration=transition_duration,
            min_visibility=0.0,
            max_visibility=1.0,
        )
        controller.add_target(target)


def evaluate_visibility_for_frame(
    controller: VisibilityController,
    zone_manager: ZoneManager,
    camera_position: Tuple[float, float, float],
    frame: int,
) -> Dict[str, float]:
    """
    Evaluate visibility for a specific frame.

    Useful for rendering animations where visibility needs to
    be baked into each frame.

    Args:
        controller: VisibilityController to use
        zone_manager: ZoneManager for zone evaluation
        camera_position: Camera position at this frame
        frame: Frame number to evaluate

    Returns:
        Dictionary of object_name -> visibility (0.0-1.0)
    """
    controller.set_zone_manager(zone_manager)
    return controller.update(camera_position, frame)


def bake_visibility_animation(
    controller: VisibilityController,
    zone_manager: ZoneManager,
    camera_object_name: str,
    frame_start: int,
    frame_end: int,
    object_names: Optional[List[str]] = None,
) -> Dict[str, List[Tuple[int, float]]]:
    """
    Bake visibility animation for a frame range.

    Pre-calculates visibility values for all frames and optionally
    inserts keyframes in Blender.

    Args:
        controller: VisibilityController to use
        zone_manager: ZoneManager for zone evaluation
        camera_object_name: Name of camera object in Blender
        frame_start: First frame to bake
        frame_end: Last frame to bake
        object_names: Specific objects to bake (None = all)

    Returns:
        Dictionary of object_name -> [(frame, visibility), ...]
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for visibility baking")

    camera = bpy.data.objects.get(camera_object_name)
    if camera is None:
        raise ValueError(f"Camera not found: {camera_object_name}")

    controller.set_zone_manager(zone_manager)

    # Get objects to bake
    if object_names is None:
        object_names = list(controller.targets.keys())

    results = {name: [] for name in object_names}

    # Store current frame
    original_frame = bpy.context.scene.frame_current

    try:
        # Iterate through frames
        for frame in range(frame_start, frame_end + 1):
            # Set scene frame (for animated camera)
            bpy.context.scene.frame_set(frame)

            # Get camera position at this frame
            camera_position = tuple(camera.matrix_world.translation)

            # Update visibility
            visibility = controller.update(camera_position, frame)

            # Record results
            for obj_name in object_names:
                if obj_name in visibility:
                    results[obj_name].append((frame, visibility[obj_name]))

    finally:
        # Restore frame
        bpy.context.scene.frame_set(original_frame)

    return results
