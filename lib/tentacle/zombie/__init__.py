"""Zombie mouth tentacle integration package."""

from .mouth_attach import (
    MouthAttachmentPoint,
    MouthSocketResult,
    create_mouth_socket,
    attach_tentacle_to_socket,
    calculate_mouth_distribution,
    angle_to_position,
)
from .multi_array import (
    SizeMixConfig,
    MultiTentacleResult,
    MultiTentacleArray,
    create_zombie_mouth,
)

__all__ = [
    # Mouth attachment
    "MouthAttachmentPoint",
    "MouthSocketResult",
    "create_mouth_socket",
    "attach_tentacle_to_socket",
    "calculate_mouth_distribution",
    "angle_to_position",

    # Multi-array
    "SizeMixConfig",
    "MultiTentacleResult",
    "MultiTentacleArray",
    "create_zombie_mouth",
]
