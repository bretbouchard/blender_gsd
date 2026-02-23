"""
LOD (Level of Detail) System

Manages level-of-detail switching for scene optimization.
Supports distance-based, percentage-based, and custom LOD strategies.

Implements REQ-GN-07: LOD System (NEW - Council).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
from enum import Enum
import math


class LODStrategy(Enum):
    """LOD selection strategy."""
    DISTANCE = "distance"
    SCREEN_SIZE = "screen_size"
    INSTANCE_COUNT = "instance_count"
    MANUAL = "manual"


class LODQuality(Enum):
    """LOD quality level."""
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    IMPOSTOR = 3


@dataclass
class LODLevel:
    """
    Single LOD level specification.

    Attributes:
        level: LOD level (0 = highest detail)
        distance_min: Minimum distance for this LOD
        distance_max: Maximum distance for this LOD
        screen_size_min: Minimum screen size percentage
        decimation_ratio: Geometry reduction ratio
        texture_resolution: Texture resolution divisor
        use_impostor: Whether to use billboard impostor
        material_simplification: Material complexity reduction
    """
    level: int = 0
    distance_min: float = 0.0
    distance_max: float = 100.0
    screen_size_min: float = 0.0
    decimation_ratio: float = 1.0
    texture_resolution: float = 1.0
    use_impostor: bool = False
    material_simplification: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level,
            "distance_min": self.distance_min,
            "distance_max": self.distance_max,
            "screen_size_min": self.screen_size_min,
            "decimation_ratio": self.decimation_ratio,
            "texture_resolution": self.texture_resolution,
            "use_impostor": self.use_impostor,
            "material_simplification": self.material_simplification,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LODLevel":
        """Create from dictionary."""
        return cls(
            level=data.get("level", 0),
            distance_min=data.get("distance_min", 0.0),
            distance_max=data.get("distance_max", 100.0),
            screen_size_min=data.get("screen_size_min", 0.0),
            decimation_ratio=data.get("decimation_ratio", 1.0),
            texture_resolution=data.get("texture_resolution", 1.0),
            use_impostor=data.get("use_impostor", False),
            material_simplification=data.get("material_simplification", 0),
        )


@dataclass
class LODConfig:
    """
    LOD configuration for an asset or group.

    Attributes:
        config_id: Unique configuration identifier
        strategy: LOD selection strategy
        levels: LOD levels in order (highest to lowest detail)
        hysteresis: Distance hysteresis to prevent LOD flickering
        transition_speed: LOD transition animation speed
    """
    config_id: str = "default"
    strategy: str = "distance"
    levels: List[LODLevel] = field(default_factory=list)
    hysteresis: float = 2.0
    transition_speed: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "strategy": self.strategy,
            "levels": [l.to_dict() for l in self.levels],
            "hysteresis": self.hysteresis,
            "transition_speed": self.transition_speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LODConfig":
        """Create from dictionary."""
        return cls(
            config_id=data.get("config_id", "default"),
            strategy=data.get("strategy", "distance"),
            levels=[LODLevel.from_dict(l) for l in data.get("levels", [])],
            hysteresis=data.get("hysteresis", 2.0),
            transition_speed=data.get("transition_speed", 0.1),
        )

    def get_level_for_distance(self, distance: float, previous_level: int = 0) -> int:
        """
        Get appropriate LOD level for distance.

        Uses hysteresis to prevent rapid switching.

        Args:
            distance: Distance to camera
            previous_level: Previous LOD level (for hysteresis)

        Returns:
            LOD level index
        """
        for i, level in enumerate(self.levels):
            # Apply hysteresis
            if previous_level > i:
                # Going to higher detail - require closer distance
                min_dist = level.distance_min + self.hysteresis
            else:
                min_dist = level.distance_min

            if min_dist <= distance < level.distance_max:
                return level.level

        # Return lowest detail if nothing matches
        return self.levels[-1].level if self.levels else 0


@dataclass
class LODState:
    """
    Current LOD state for an instance.

    Attributes:
        instance_id: Instance identifier
        current_level: Current LOD level
        target_level: Target LOD level (for transitions)
        transition_progress: Transition progress (0-1)
        last_distance: Last calculated distance
    """
    instance_id: str = ""
    current_level: int = 0
    target_level: int = 0
    transition_progress: float = 1.0
    last_distance: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "current_level": self.current_level,
            "target_level": self.target_level,
            "transition_progress": self.transition_progress,
            "last_distance": self.last_distance,
        }


# =============================================================================
# PRESET LOD CONFIGURATIONS
# =============================================================================

DEFAULT_LOD_CONFIGS: Dict[str, LODConfig] = {
    "default": LODConfig(
        config_id="default",
        strategy="distance",
        levels=[
            LODLevel(level=0, distance_min=0.0, distance_max=20.0, decimation_ratio=1.0, texture_resolution=1.0),
            LODLevel(level=1, distance_min=20.0, distance_max=50.0, decimation_ratio=0.5, texture_resolution=0.5),
            LODLevel(level=2, distance_min=50.0, distance_max=100.0, decimation_ratio=0.25, texture_resolution=0.25),
            LODLevel(level=3, distance_min=100.0, distance_max=1000.0, decimation_ratio=0.1, texture_resolution=0.125, use_impostor=True),
        ],
        hysteresis=2.0,
    ),

    "high_quality": LODConfig(
        config_id="high_quality",
        strategy="distance",
        levels=[
            LODLevel(level=0, distance_min=0.0, distance_max=50.0, decimation_ratio=1.0, texture_resolution=1.0),
            LODLevel(level=1, distance_min=50.0, distance_max=100.0, decimation_ratio=0.75, texture_resolution=0.75),
            LODLevel(level=2, distance_min=100.0, distance_max=200.0, decimation_ratio=0.5, texture_resolution=0.5),
            LODLevel(level=3, distance_min=200.0, distance_max=1000.0, decimation_ratio=0.25, texture_resolution=0.25),
        ],
        hysteresis=5.0,
    ),

    "performance": LODConfig(
        config_id="performance",
        strategy="distance",
        levels=[
            LODLevel(level=0, distance_min=0.0, distance_max=10.0, decimation_ratio=1.0, texture_resolution=1.0),
            LODLevel(level=1, distance_min=10.0, distance_max=25.0, decimation_ratio=0.5, texture_resolution=0.5),
            LODLevel(level=2, distance_min=25.0, distance_max=50.0, decimation_ratio=0.25, texture_resolution=0.25, use_impostor=True),
            LODLevel(level=3, distance_min=50.0, distance_max=1000.0, decimation_ratio=0.1, texture_resolution=0.125, use_impostor=True),
        ],
        hysteresis=1.0,
    ),

    "foliage": LODConfig(
        config_id="foliage",
        strategy="distance",
        levels=[
            LODLevel(level=0, distance_min=0.0, distance_max=15.0, decimation_ratio=1.0, texture_resolution=1.0),
            LODLevel(level=1, distance_min=15.0, distance_max=30.0, decimation_ratio=0.5, texture_resolution=0.5),
            LODLevel(level=2, distance_min=30.0, distance_max=60.0, decimation_ratio=0.25, texture_resolution=0.25, use_impostor=False),
            LODLevel(level=3, distance_min=60.0, distance_max=1000.0, decimation_ratio=0.1, texture_resolution=0.125, use_impostor=True),
        ],
        hysteresis=3.0,
    ),

    "characters": LODConfig(
        config_id="characters",
        strategy="screen_size",
        levels=[
            LODLevel(level=0, distance_min=0.0, distance_max=30.0, screen_size_min=0.1, decimation_ratio=1.0, texture_resolution=1.0),
            LODLevel(level=1, distance_min=30.0, distance_max=60.0, screen_size_min=0.05, decimation_ratio=0.5, texture_resolution=0.5),
            LODLevel(level=2, distance_min=60.0, distance_max=120.0, screen_size_min=0.02, decimation_ratio=0.25, texture_resolution=0.25),
            LODLevel(level=3, distance_min=120.0, distance_max=1000.0, screen_size_min=0.0, decimation_ratio=0.1, texture_resolution=0.125, use_impostor=True),
        ],
        hysteresis=4.0,
    ),
}


class LODManager:
    """
    Manages LOD for scene instances.

    Tracks instance states, calculates LOD transitions, and
    provides GN-compatible output.

    Usage:
        manager = LODManager()
        manager.set_camera_position((0, 0, 0))
        manager.update_instances(instances)
        gn_data = manager.to_gn_input()
    """

    def __init__(self, config: Optional[LODConfig] = None):
        """
        Initialize LOD manager.

        Args:
            config: Default LOD configuration
        """
        self.config = config or DEFAULT_LOD_CONFIGS["default"]
        self.configs: Dict[str, LODConfig] = dict(DEFAULT_LOD_CONFIGS)
        self.states: Dict[str, LODState] = {}
        self.camera_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._update_count = 0

    def set_config(self, config_id: str, config: LODConfig) -> None:
        """Set LOD configuration."""
        self.configs[config_id] = config

    def get_config(self, config_id: str) -> LODConfig:
        """Get LOD configuration."""
        return self.configs.get(config_id, self.config)

    def set_camera_position(self, position: Tuple[float, float, float]) -> None:
        """Set camera position for distance calculations."""
        self.camera_position = position

    def calculate_distance(self, instance_position: Tuple[float, float, float]) -> float:
        """Calculate distance from camera to instance."""
        dx = instance_position[0] - self.camera_position[0]
        dy = instance_position[1] - self.camera_position[1]
        dz = instance_position[2] - self.camera_position[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def update_instance(
        self,
        instance_id: str,
        position: Tuple[float, float, float],
        config_id: str = "default",
    ) -> LODState:
        """
        Update LOD state for single instance.

        Args:
            instance_id: Instance identifier
            position: Instance world position
            config_id: LOD configuration to use

        Returns:
            Updated LOD state
        """
        config = self.get_config(config_id)
        distance = self.calculate_distance(position)

        # Get or create state
        state = self.states.get(instance_id)
        if not state:
            state = LODState(instance_id=instance_id)
            self.states[instance_id] = state

        # Calculate new LOD level
        new_level = config.get_level_for_distance(distance, state.current_level)

        # Update state
        state.last_distance = distance
        state.target_level = new_level

        # Handle transition
        if state.target_level != state.current_level:
            state.transition_progress = 0.0
        else:
            # Continue transition
            if state.transition_progress < 1.0:
                state.transition_progress = min(
                    1.0,
                    state.transition_progress + config.transition_speed
                )
            if state.transition_progress >= 0.5:
                # Switch at halfway point
                state.current_level = state.target_level

        return state

    def update_instances(
        self,
        instances: List[Dict[str, Any]],
        config_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, LODState]:
        """
        Update LOD for multiple instances.

        Args:
            instances: List of instance dictionaries with 'instance_id' and 'position'
            config_map: Map of instance_id to config_id

        Returns:
            Dictionary of instance states
        """
        config_map = config_map or {}
        results = {}

        for instance in instances:
            instance_id = instance.get("instance_id", "")
            position = instance.get("position", (0.0, 0.0, 0.0))
            config_id = config_map.get(instance_id, "default")

            if instance_id:
                results[instance_id] = self.update_instance(
                    instance_id,
                    tuple(position),
                    config_id
                )

        self._update_count += 1
        return results

    def get_instance_state(self, instance_id: str) -> Optional[LODState]:
        """Get LOD state for instance."""
        return self.states.get(instance_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get LOD statistics."""
        level_counts: Dict[int, int] = {}
        for state in self.states.values():
            level = state.current_level
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "total_instances": len(self.states),
            "level_distribution": level_counts,
            "update_count": self._update_count,
            "camera_position": list(self.camera_position),
        }

    def to_gn_input(self) -> Dict[str, Any]:
        """
        Convert to GN input format.

        Returns:
            GN-compatible dictionary
        """
        return {
            "version": "1.0",
            "states": {k: v.to_dict() for k, v in self.states.items()},
            "statistics": self.get_statistics(),
            "configs": {k: v.to_dict() for k, v in self.configs.items()},
        }

    def reset(self) -> None:
        """Reset all LOD states."""
        self.states.clear()
        self._update_count = 0


class LODSelector:
    """
    Selects appropriate LOD variant from asset.

    Used by GN to choose between pre-baked LOD meshes.
    """

    @staticmethod
    def select_lod_variant(
        lod_level: int,
        available_variants: List[int],
    ) -> int:
        """
        Select best available variant for LOD level.

        Args:
            lod_level: Required LOD level
            available_variants: Available variant indices

        Returns:
            Best matching variant index
        """
        if not available_variants:
            return 0

        # Find exact match or closest higher detail
        for v in available_variants:
            if v == lod_level:
                return v

        # Find closest match
        closest = min(available_variants, key=lambda x: abs(x - lod_level))

        # Prefer higher detail if within 1 level
        higher = [v for v in available_variants if v < lod_level]
        if higher and (lod_level - min(higher)) <= 1:
            return min(higher)

        return closest


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_lod_config(
    levels: int = 4,
    max_distance: float = 100.0,
    decimation_start: float = 0.5,
    hysteresis: float = 2.0,
) -> LODConfig:
    """
    Create LOD configuration with evenly spaced levels.

    Args:
        levels: Number of LOD levels
        max_distance: Maximum view distance
        decimation_start: Decimation ratio for first LOD
        hysteresis: Distance hysteresis

    Returns:
        LODConfig
    """
    distance_step = max_distance / levels
    decimation_step = (1.0 - decimation_start) / (levels - 1) if levels > 1 else 0

    lod_levels = []
    for i in range(levels):
        lod_levels.append(LODLevel(
            level=i,
            distance_min=i * distance_step,
            distance_max=(i + 1) * distance_step,
            decimation_ratio=max(0.1, 1.0 - i * decimation_step),
            texture_resolution=max(0.125, 1.0 / (i + 1)),
            use_impostor=(i == levels - 1),
        ))

    return LODConfig(
        config_id="custom",
        strategy="distance",
        levels=lod_levels,
        hysteresis=hysteresis,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "LODStrategy",
    "LODQuality",
    # Data classes
    "LODLevel",
    "LODConfig",
    "LODState",
    # Constants
    "DEFAULT_LOD_CONFIGS",
    # Classes
    "LODManager",
    "LODSelector",
    # Functions
    "create_lod_config",
]
