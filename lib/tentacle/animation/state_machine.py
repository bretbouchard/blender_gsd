"""
Tentacle Animation State Machine

State machine for zombie tentacle animation behaviors.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import math
import numpy as np

from .types import (
    AnimationState,
    AnimationStateConfig,
    StateTransition,
)


# Default state configurations
DEFAULT_STATE_CONFIGS: Dict[AnimationState, AnimationStateConfig] = {
    AnimationState.HIDDEN: AnimationStateConfig(
        state=AnimationState.HIDDEN,
        shape_keys={"Compress50": 1.0},
        idle_motion=None,
        idle_speed=0.0,
        emergence_delay=0.0,
        loop=False,
    ),
    AnimationState.EMERGING: AnimationStateConfig(
        state=AnimationState.EMERGING,
        shape_keys={"Compress50": 0.0, "Compress75": 0.5},
        idle_motion="wave",
        idle_speed=0.5,
        emergence_delay=0.0,
        loop=False,
    ),
    AnimationState.SEARCHING: AnimationStateConfig(
        state=AnimationState.SEARCHING,
        shape_keys={"Base": 1.0},
        idle_motion="undulate",
        idle_speed=1.0,
        emergence_delay=0.0,
        loop=True,
    ),
    AnimationState.GRABBING: AnimationStateConfig(
        state=AnimationState.GRABBING,
        shape_keys={"CurlTip": 0.3, "Expand125": 0.2},
        idle_motion=None,
        idle_speed=0.0,
        emergence_delay=0.0,
        loop=False,
    ),
    AnimationState.ATTACKING: AnimationStateConfig(
        state=AnimationState.ATTACKING,
        shape_keys={"CurlFull": 0.7, "Compress50": 0.0},
        idle_motion=None,
        idle_speed=2.0,
        emergence_delay=0.0,
        loop=False,
    ),
    AnimationState.RETRACTING: AnimationStateConfig(
        state=AnimationState.RETRACTING,
        shape_keys={"Compress75": 0.8, "Compress50": 1.0},
        idle_motion=None,
        idle_speed=0.0,
        emergence_delay=0.0,
        loop=False,
    ),
}

# Default state transitions
DEFAULT_TRANSITIONS: List[StateTransition] = [
    StateTransition(
        from_state=AnimationState.HIDDEN,
        to_state=AnimationState.EMERGING,
        duration=0.5,
        blend_curve="ease_out",
        shape_key_blend={"Compress50": 1.0, "Compress75": 0.0},
        conditions={},
    ),
    StateTransition(
        from_state=AnimationState.EMERGING,
        to_state=AnimationState.SEARCHING,
        duration=0.3,
        blend_curve="ease_out",
        shape_key_blend={"Compress50": 0.0, "Compress75": 0.0},
        conditions={},
    ),
    StateTransition(
        from_state=AnimationState.SEARCHING,
        to_state=AnimationState.GRABBING,
        duration=0.2,
        blend_curve="linear",
        shape_key_blend={"Base": 0.5, "CurlTip": 0.5},
        conditions={},
    ),
    StateTransition(
        from_state=AnimationState.SEARCHING,
        to_state=AnimationState.ATTACKING,
        duration=0.1,
        blend_curve="linear",
        shape_key_blend={"CurlFull": 0.7},
        conditions={},
    ),
    StateTransition(
        from_state=AnimationState.GRABBING,
        to_state=AnimationState.RETRACTING,
        duration=0.4,
        blend_curve="ease_in",
        shape_key_blend={"Compress75": 0.6},
        conditions={},
    ),
    StateTransition(
        from_state=AnimationState.ATTACKING,
        to_state=AnimationState.RETRACTING,
        duration=0.2,
        blend_curve="linear",
        shape_key_blend={"Compress50": 1.0},
        conditions={},
    ),
    StateTransition(
        from_state=AnimationState.RETRACTING,
        to_state=AnimationState.HIDDEN,
        duration=0.5,
        blend_curve="ease_in",
        shape_key_blend={"Compress50": 1.0},
        conditions={},
    ),
]


class TentacleStateMachine:
    """State machine for tentacle animation."""

    def __init__(
        self,
        initial_state: AnimationState = AnimationState.HIDDEN,
        state_configs: Optional[Dict[AnimationState, AnimationStateConfig]] = None,
        transitions: Optional[List[StateTransition]] = None,
    ):
        """Initialize the state machine.

        Args:
            initial_state: Starting state
            state_configs: Optional custom state configurations
            transitions: Optional custom transitions
        """
        self._current_state = initial_state
        self._previous_state: Optional[AnimationState] = None
        self._transition_time: float = 0.0
        self._total_transition_duration: float = 0.0
        self._state_time: float = 0.0

        # Use provided configs or defaults
        self._state_configs = state_configs or {}
        self._transitions = transitions or []

        # Add default state configs if not provided
        for state, config in DEFAULT_STATE_CONFIGS.items():
            if state not in self._state_configs:
                self._state_configs[state] = config

        # Add default transitions if not provided
        if not self._transitions:
            self._transitions = DEFAULT_TRANSITIONS.copy()

    @property
    def current_state(self) -> AnimationState:
        """Get the current animation state."""
        return self._current_state

    @property
    def previous_state(self) -> Optional[AnimationState]:
        """Get the previous animation state."""
        return self._previous_state

    @property
    def state_time(self) -> float:
        """Get time in current state."""
        return self._state_time

    @property
    def is_transitioning(self) -> bool:
        """Check if currently transitioning between states."""
        return self._transition_time > 0.0

    @property
    def transition_progress(self) -> float:
        """Get transition progress (0.0 to 1.0)."""
        if self._total_transition_duration <= 0:
            return 1.0
        return 1.0 - (self._transition_time / self._total_transition_duration)

    def add_transition(self, transition: StateTransition) -> None:
        """Add a state transition to the machine."""
        self._transitions.append(transition)

    def add_state_config(self, config: AnimationStateConfig) -> None:
        """Add configuration for a state."""
        self._state_configs[config.state] = config

    def get_state_config(self, state: AnimationState) -> Optional[AnimationStateConfig]:
        """Get configuration for a state."""
        return self._state_configs.get(state)

    def get_transition(self, from_state: AnimationState, to_state: AnimationState) -> Optional[StateTransition]:
        """Get transition between two states."""
        for transition in self._transitions:
            if transition.from_state == from_state and transition.to_state == to_state:
                return transition
        return None

    def can_transition_to(self, target_state: AnimationState) -> bool:
        """Check if transition to target state is possible."""
        return self.get_transition(self._current_state, target_state) is not None

    def transition_to(self, target_state: AnimationState, immediate: bool = False) -> bool:
        """
        Transition to a new state.

        Args:
            target_state: The state to transition to
            immediate: If True, skip transition animation

        Returns:
            True if transition started, False if not possible
        """
        transition = self.get_transition(self._current_state, target_state)
        if transition is None:
            return False

        self._previous_state = self._current_state
        self._current_state = target_state
        self._state_time = 0.0

        if immediate:
            self._transition_time = 0.0
            self._total_transition_duration = 0.0
        else:
            self._transition_time = transition.duration
            self._total_transition_duration = transition.duration

        return True

    def update(self, delta_time: float) -> Dict[str, float]:
        """
        Update state machine with time step.

        Args:
            delta_time: Time elapsed since last update (seconds)

        Returns:
            Current shape key values
        """
        # Update state time
        self._state_time += delta_time

        # Update transition time
        if self._transition_time > 0.0:
            self._transition_time = max(0.0, self._transition_time - delta_time)

        return self.get_shape_key_values()

    def get_shape_key_values(self) -> Dict[str, float]:
        """Get interpolated shape key values for current state."""
        # Get current state config
        current_config = self._state_configs.get(self._current_state)
        if not current_config:
            return {}

        result = current_config.shape_keys.copy()

        # If transitioning, blend with previous state
        if self._transition_time > 0.0 and self._previous_state is not None:
            prev_config = self._state_configs.get(self._previous_state)
            if prev_config:
                # Calculate blend factor (0 = prev, 1 = current)
                blend = self.transition_progress

                # Blend shape keys
                for key, value in prev_config.shape_keys.items():
                    if key in result:
                        # Linear interpolation
                        result[key] = value * (1.0 - blend) + result[key] * blend
                    else:
                        # Key only in previous state
                        result[key] = value * (1.0 - blend)

        return result

    def get_idle_motion(self) -> Optional[str]:
        """Get idle motion type for current state."""
        config = self._state_configs.get(self._current_state)
        if config:
            return config.idle_motion
        return None

    def get_idle_speed(self) -> float:
        """Get idle speed multiplier for current state."""
        config = self._state_configs.get(self._current_state)
        if config:
            return config.idle_speed
        return 1.0

    def reset(self) -> None:
        """Reset state machine to initial state."""
        self._current_state = AnimationState.HIDDEN
        self._previous_state = None
        self._transition_time = 0.0
        self._total_transition_duration = 0.0
        self._state_time = 0.0


class MultiTentacleStateCoordinator:
    """Coordinates state across multiple tentacles with staggered emergence."""

    def __init__(
        self,
        tentacle_count: int,
        base_delay: float = 0.0,
        stagger_delay: float = 0.1
    ):
        """
        Initialize coordinator.

        Args:
            tentacle_count: Number of tentacles to coordinate
            base_delay: Base delay before any tentacle starts
            stagger_delay: Additional delay between each tentacle
        """
        self.tentacle_count = tentacle_count
        self.base_delay = base_delay
        self.stagger_delay = stagger_delay
        self._state_machines: List[TentacleStateMachine] = []
        self._time = 0.0
        self._emergence_triggered = False

        # Create state machines for each tentacle
        for i in range(tentacle_count):
            self._state_machines.append(TentacleStateMachine())

    @property
    def state_machines(self) -> List[TentacleStateMachine]:
        """Get all state machines."""
        return self._state_machines

    def get_machine(self, index: int) -> Optional[TentacleStateMachine]:
        """Get state machine for specific tentacle."""
        if 0 <= index < len(self._state_machines):
            return self._state_machines[index]
        return None

    def get_states(self) -> List[AnimationState]:
        """Get current state of all tentacles."""
        return [sm.current_state for sm in self._state_machines]

    def trigger_emergence(self) -> None:
        """Trigger staggered emergence of all tentacles."""
        self._emergence_triggered = True
        # Each tentacle will emerge based on its delay
        for i, sm in enumerate(self._state_machines):
            delay = self.base_delay + (i * self.stagger_delay)
            # Store delay as state time offset
            sm._state_time = -delay  # Negative means not started yet

    def trigger_retraction(self) -> None:
        """Trigger retraction of all tentacles."""
        for sm in self._state_machines:
            sm.transition_to(AnimationState.RETRACTING)

    def trigger_attack(self) -> None:
        """Trigger attack state for all tentacles."""
        for sm in self._state_machines:
            if sm.current_state == AnimationState.SEARCHING:
                sm.transition_to(AnimationState.ATTACKING)

    def update(self, delta_time: float) -> List[Dict[str, float]]:
        """
        Update all state machines.

        Args:
            delta_time: Time elapsed since last update (seconds)

        Returns:
            List of shape key dictionaries for each tentacle
        """
        self._time += delta_time
        results = []

        for i, sm in enumerate(self._state_machines):
            # Check if this tentacle should start emerging
            if self._emergence_triggered and sm.current_state == AnimationState.HIDDEN:
                delay = self.base_delay + (i * self.stagger_delay)
                if self._time >= delay:
                    sm.transition_to(AnimationState.EMERGING)

            results.append(sm.update(delta_time))

        return results

    def all_hidden(self) -> bool:
        """Check if all tentacles are in hidden state."""
        return all(sm.current_state == AnimationState.HIDDEN for sm in self._state_machines)

    def all_searching(self) -> bool:
        """Check if all tentacles are in searching state."""
        return all(sm.current_state == AnimationState.SEARCHING for sm in self._state_machines)

    def reset(self) -> None:
        """Reset all state machines."""
        self._time = 0.0
        self._emergence_triggered = False
        for sm in self._state_machines:
            sm.reset()
