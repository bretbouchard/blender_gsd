"""
Cinematic Rendering System Package

A comprehensive system for cinematic camera, lighting, and rendering.

Modules:
- types: Core data structures (ShotState, CameraConfig, etc.)
- enums: Type-safe enumerations
- state_manager: State persistence

Quick Start:
    from lib.cinematic import (
        ShotState, CameraConfig, Transform3D,
        StateManager, FrameStore
    )

    # Create camera config
    camera = CameraConfig(
        name="hero_camera",
        focal_length=85.0,
        f_stop=4.0
    )

    # Create shot state
    state = ShotState(
        shot_name="hero_knob_01",
        camera=camera
    )

    # Save state
    manager = StateManager()
    manager.save(state, Path(".gsd-state/cinematic/sessions/hero.yaml"))
"""

from .types import (
    Transform3D,
    CameraConfig,
    LightConfig,
    BackdropConfig,
    RenderSettings,
    ShotState,
)
from .enums import (
    LensType,
    LightType,
    QualityTier,
    ColorSpace,
    EasingType,
)
from .state_manager import (
    StateManager,
    FrameStore,
)

__all__ = [
    # Core types
    "Transform3D",
    "CameraConfig",
    "LightConfig",
    "BackdropConfig",
    "RenderSettings",
    "ShotState",

    # Enums
    "LensType",
    "LightType",
    "QualityTier",
    "ColorSpace",
    "EasingType",

    # State management
    "StateManager",
    "FrameStore",
]

__version__ = "0.1.0"
