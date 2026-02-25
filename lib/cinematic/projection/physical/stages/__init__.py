"""Pipeline stage functions for physical projector mapping.

This module implements the 5-stage GSD pipeline for projection mapping:

Stage 0 (Normalize): Profile validation, seed hashing for determinism
Stage 1 (Primary): Base frustum setup, projector camera creation
Stage 2 (Secondary): Calibration/alignment, keystone correction
Stage 3 (Detail): Content mapping, UV projection
Stage 4 (Output): Render configuration, export

Pipeline Rick: "Each stage should be a pure function that takes
state and context, returns new state. Deterministic execution
is critical for reproducible calibration."

Note: Stage implementations are added in Phase 18.1 (calibration)
and Phase 18.2 (content mapping). This module provides the stage
interface and utilities.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable


@dataclass
class StageContext:
    """Context passed to all stage functions."""
    parameters: Dict[str, Any]
    profile_name: str
    target_id: Optional[str] = None
    seed: Optional[int] = None


@dataclass
class StageState:
    """State accumulated through pipeline stages."""
    stage: int
    profile: Any  # ProjectorProfile
    camera: Any   # bpy.types.Object (camera)
    target_checksum: Optional[str] = None
    calibration_points: Optional[list] = None
    errors: list = field(default_factory=list)


# Stage function signature
StageFunction = Callable  # (state: StageState, context: StageContext) -> StageState


def stage_normalize(state: StageState, context: StageContext) -> StageState:
    """Stage 0: Normalize parameters and validate profile.

    This stage:
    - Loads projector profile
    - Computes deterministic seed from inputs
    - Validates all required parameters

    Args:
        state: Current pipeline state
        context: Stage context with parameters

    Returns:
        Updated state with profile loaded
    """
    from ..projector import get_profile
    import hashlib

    # Load profile
    profile = get_profile(context.profile_name)

    # Compute deterministic seed (Pipeline Rick requirement)
    if context.seed is None:
        seed_input = (
            context.profile_name,
            str(context.parameters.get('position', [])),
            context.target_id or '',
        )
        context.seed = int(hashlib.md5('|'.join(seed_input).encode()).hexdigest()[:8], 16)

    return StageState(
        stage=0,
        profile=profile,
        camera=None,
        target_checksum=context.parameters.get('target_checksum'),
        errors=[],
    )


def stage_primary(state: StageState, context: StageContext) -> StageState:
    """Stage 1: Create base projector camera.

    This stage:
    - Creates Blender camera from profile
    - Sets render resolution to projector native
    - Positions camera if position provided

    Args:
        state: Current pipeline state (must have profile)
        context: Stage context with parameters

    Returns:
        Updated state with camera created
    """
    from ..projector import create_projector_camera

    if state.profile is None:
        raise ValueError("Profile required - run stage_normalize first")

    # Create camera from profile
    camera = create_projector_camera(state.profile)

    # Position if provided
    position = context.parameters.get('position')
    if position:
        camera.location = position

    rotation = context.parameters.get('rotation')
    if rotation:
        import math
        camera.rotation_euler = [math.radians(r) for r in rotation]

    return StageState(
        stage=1,
        profile=state.profile,
        camera=camera,
        target_checksum=state.target_checksum,
        errors=state.errors,
    )


# Stages 2-4 implemented in Phase 18.1 and 18.2
# stage_secondary = ...  # Phase 18.1: Calibration
# stage_detail = ...     # Phase 18.2: Content mapping
# stage_output = ...     # Phase 18.2: Render/export


__all__ = [
    'StageContext',
    'StageState',
    'stage_normalize',
    'stage_primary',
]
