"""
Tentacle Animation Package

Animation system for tentacle squeeze/expand effects with shape keys,
spline IK rigging, and state machine for zombie tentacle behavior.
"""

from .types import (
    # Enums
    ShapeKeyPreset,
    AnimationState,
    # Config dataclasses
    ShapeKeyConfig,
    StateTransition,
    AnimationStateConfig,
    SplineIKRig,
    RigConfig,
    # Result dataclasses
    ShapeKeyResult,
    RigResult,
)

from .shape_keys import (
    ShapeKeyGenerator,
    get_preset_config,
    SHAPE_KEY_PRESETS,
)

from .rig import (
    SplineIKRigGenerator,
    generate_spline_ik_rig,
)

from .state_machine import (
    TentacleStateMachine,
    MultiTentacleStateCoordinator,
    DEFAULT_STATE_CONFIGS,
    DEFAULT_TRANSITIONS,
)


__all__ = [
    # Enums
    "ShapeKeyPreset",
    "AnimationState",
    # Config dataclasses
    "ShapeKeyConfig",
    "StateTransition",
    "AnimationStateConfig",
    "SplineIKRig",
    "RigConfig",
    # Result dataclasses
    "ShapeKeyResult",
    "RigResult",
    # Shape key generation
    "ShapeKeyGenerator",
    "get_preset_config",
    "SHAPE_KEY_PRESETS",
    # Rig generation
    "SplineIKRigGenerator",
    "generate_spline_ik_rig",
    # State machine
    "TentacleStateMachine",
    "MultiTentacleStateCoordinator",
    "DEFAULT_STATE_CONFIGS",
    "DEFAULT_TRANSITIONS",
]


# Convenience functions

def create_shape_key_generator() -> ShapeKeyGenerator:
    """Create a new shape key generator."""
    return ShapeKeyGenerator()


def create_state_machine(
    initial_state: AnimationState = AnimationState.HIDDEN,
) -> TentacleStateMachine:
    """Create a new tentacle state machine.

    Args:
        initial_state: Starting animation state

    Returns:
        Configured TentacleStateMachine
    """
    return TentacleStateMachine(initial_state=initial_state)


def create_multi_tentacle_coordinator(
    tentacle_count: int,
    base_delay: float = 0.0,
    stagger_delay: float = 0.1,
) -> MultiTentacleStateCoordinator:
    """Create a coordinator for multiple tentacles.

    Args:
        tentacle_count: Number of tentacles
        base_delay: Base delay before emergence
        stagger_delay: Delay between each tentacle

    Returns:
        Configured MultiTentacleStateCoordinator
    """
    return MultiTentacleStateCoordinator(
        tentacle_count=tentacle_count,
        base_delay=base_delay,
        stagger_delay=stagger_delay,
    )


# Add convenience functions to exports
__all__.extend([
    "create_shape_key_generator",
    "create_state_machine",
    "create_multi_tentacle_coordinator",
])
