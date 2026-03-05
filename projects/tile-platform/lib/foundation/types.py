"""
Foundation type definitions for the tile platform system.

This module defines the core data types, enums, and configuration classes
used throughout the platform system. It is designed to be pure Python
without Blender dependencies for maximum testability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Tuple, Optional


class TileShape(Enum):
    """Enumeration of supported tile shapes."""
    SQUARE = "square"
    OCTAGONAL = "octagonal"
    HEXAGONAL = "hexagonal"


@dataclass
class TileConfig:
    """Configuration for a single tile in the platform.

    Attributes:
        position: (x, y) coordinates in world space
        shape: The geometric shape of the tile
        size: The size of the tile (default 1.0)
        material_settings: Optional material properties for rendering
    """
    position: Tuple[float, float]
    shape: TileShape = TileShape.SQUARE
    size: float = 1.0
    material_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate tile configuration after initialization."""
        if self.size <= 0:
            raise ValueError(f"Tile size must be positive, got {self.size}")


@dataclass
class PlatformConfig:
    """Configuration for the overall platform system.

    Attributes:
        initial_size: (width, height) in number of tiles
        tile_size: Size of each tile in world units (default 1.0)
        tile_shape: Default shape for tiles (default SQUARE)
        arm_count: Number of mechanical arms (default 4)
    """
    initial_size: Tuple[int, int] = (1, 1)
    tile_size: float = 1.0
    tile_shape: TileShape = TileShape.SQUARE
    arm_count: int = 4

    def __post_init__(self) -> None:
        """Validate platform configuration after initialization."""
        if self.tile_size <= 0:
            raise ValueError(f"Tile size must be positive, got {self.tile_size}")
        if self.arm_count < 1:
            raise ValueError(f"Arm count must be at least 1, got {self.arm_count}")
        if self.initial_size[0] < 0 or self.initial_size[1] < 0:
            raise ValueError(
                f"Initial size dimensions must be non-negative, got {self.initial_size}"
            )


@dataclass
class ArmConfig:
    """Placeholder configuration for mechanical arms.

    This is a simplified configuration for Phase 1. Full arm mechanics
    will be implemented in Phase 3.

    Attributes:
        position: Grid position where the arm is mounted
        status: Current status of the arm (default "idle")
    """
    position: Tuple[int, int]
    status: str = "idle"

    def __post_init__(self) -> None:
        """Validate arm configuration after initialization."""
        valid_statuses = {"idle", "extending", "retracting", "placing", "removing"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid arm status '{self.status}'. Must be one of: {valid_statuses}"
            )
