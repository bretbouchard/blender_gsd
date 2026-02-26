"""Multi-tentacle array generation for zombie mouths."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np

try:
    import bpy
    from bpy.types import Object
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None

from ..types import TentacleConfig, ZombieMouthConfig
from ..geometry import TentacleBodyGenerator, TentacleResult
from .mouth_attach import (
    calculate_mouth_distribution,
    angle_to_position,
    attach_tentacle_to_socket,
)


@dataclass
class SizeMixConfig:
    """Configuration for mixing tentacle sizes."""

    main_ratio: float = 0.5         # Ratio of main tentacles
    main_config: Optional[TentacleConfig] = None
    feeler_config: Optional[TentacleConfig] = None

    def get_config_for_index(self, index: int, total: int) -> TentacleConfig:
        """
        Get tentacle config for a specific index based on size mix.

        Args:
            index: Tentacle index
            total: Total number of tentacles

        Returns:
            TentacleConfig for this tentacle
        """
        # Determine if this is a main or feeler tentacle
        main_count = max(1, int(total * self.main_ratio))

        if index < main_count:
            return self.main_config or TentacleConfig()
        else:
            return self.feeler_config or self._default_feeler_config()

    def _default_feeler_config(self) -> TentacleConfig:
        """Create default feeler configuration."""
        return TentacleConfig(
            length=0.5,
            base_diameter=0.04,
            tip_diameter=0.01,
            segments=12,
            name="Feeler",
        )


@dataclass
class MultiTentacleResult:
    """Result of multi-tentacle generation."""

    tentacles: List[TentacleResult] = field(default_factory=list)
    positions: List[Tuple[float, float, float]] = field(default_factory=list)
    socket_name: Optional[str] = None

    @property
    def count(self) -> int:
        """Number of tentacles generated."""
        return len(self.tentacles)

    @property
    def total_vertices(self) -> int:
        """Total vertex count across all tentacles."""
        return sum(t.vertex_count for t in self.tentacles)

    @property
    def total_faces(self) -> int:
        """Total face count across all tentacles."""
        return sum(t.face_count for t in self.tentacles)


class MultiTentacleArray:
    """Generate and manage multiple tentacles for zombie mouth."""

    def __init__(self, config: ZombieMouthConfig):
        """
        Initialize array generator.

        Args:
            config: Zombie mouth configuration
        """
        self.config = config
        self._size_mix = SizeMixConfig(
            main_ratio=1.0 - config.size_mix,  # size_mix=0 means all main
            main_config=config.main_tentacle,
            feeler_config=config.feeler_tentacle,
        )

    def generate(self, name_prefix: str = "ZombieTentacle") -> MultiTentacleResult:
        """
        Generate all tentacles in the array.

        Args:
            name_prefix: Prefix for tentacle names

        Returns:
            MultiTentacleResult with all tentacles
        """
        result = MultiTentacleResult()

        # Calculate distribution
        positions = calculate_mouth_distribution(
            self.config.tentacle_count,
            self.config.spread_angle,
            self.config.distribution,
        )

        # Generate each tentacle
        for i in range(self.config.tentacle_count):
            # Get config for this tentacle
            tentacle_config = self._size_mix.get_config_for_index(
                i, self.config.tentacle_count
            )

            # Generate tentacle
            generator = TentacleBodyGenerator(tentacle_config)
            tentacle_result = generator.generate(name=f"{name_prefix}_{i:02d}")
            result.tentacles.append(tentacle_result)

            # Calculate position
            angle, z_offset = positions[i]
            pos = angle_to_position(angle, z_offset)
            result.positions.append(pos)

        return result

    def attach_to_character(
        self,
        result: MultiTentacleResult,
        jaw_bone_name: str,
        socket_name: str = "Mouth_Inside",
    ) -> Optional[str]:
        """
        Attach generated tentacles to character face rig.

        Args:
            result: Multi-tentacle generation result
            jaw_bone_name: Name of jaw bone
            socket_name: Name for mouth socket

        Returns:
            Socket name if successful, None otherwise
        """
        if not BLENDER_AVAILABLE:
            return None

        from .mouth_attach import create_mouth_socket, attach_tentacle_to_socket

        # Create mouth socket
        socket = create_mouth_socket(jaw_bone_name, socket_name)
        if not socket:
            return None

        # Attach each tentacle
        for i, tentacle_result in enumerate(result.tentacles):
            if tentacle_result.object:
                attach_tentacle_to_socket(
                    tentacle_result.object,
                    socket_name,
                    index=i,
                )
                # Set position
                pos = result.positions[i]
                tentacle_result.object.location = pos

        return socket_name


def create_zombie_mouth(
    config: ZombieMouthConfig,
    name_prefix: str = "ZombieTentacle",
) -> MultiTentacleResult:
    """
    Convenience function to create zombie mouth tentacles.

    Args:
        config: Zombie mouth configuration
        name_prefix: Prefix for tentacle names

    Returns:
        MultiTentacleResult with all tentacles
    """
    array = MultiTentacleArray(config)
    return array.generate(name_prefix)
