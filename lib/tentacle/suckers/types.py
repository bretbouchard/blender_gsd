"""Sucker system types and configuration."""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum


class SuckerStyle(Enum):
    """Visual style of suckers."""
    SMOOTH = "smooth"          # Body horror smooth cups
    REALISTIC = "realistic"    # Realistic papillae texture
    STYLIZED = "stylized"      # Cartoon/exaggerated


class SuckerPlacement(Enum):
    """Placement pattern for suckers."""
    UNIFORM = "uniform"        # Evenly spaced
    ALTERNATING = "alternating"  # Offset odd rows
    RANDOM = "random"          # Randomized positions
    DENSE_BASE = "dense_base"  # More suckers at base


@dataclass
class SuckerConfig:
    """Configuration for sucker generation."""

    # Enable/disable
    enabled: bool = True

    # Count
    rows: int = 6              # 2-8 rows along length
    columns: int = 8           # 4-12 columns around circumference

    # Size
    base_size: float = 0.015   # Size at tentacle base (meters)
    tip_size: float = 0.003    # Size at tentacle tip (meters)
    size_variation: float = 0.1  # Random size variation (0-1)

    # Cup shape
    cup_depth: float = 0.005   # Depth of cup (meters)
    rim_sharpness: float = 0.7  # Edge hardness (0.0-1.0)
    rim_width: float = 0.002   # Rim thickness (meters)

    # Mesh quality
    mesh_resolution: int = 16  # Vertex count for cup mesh (8-32)

    # Style
    style: str = "smooth"      # smooth, realistic, stylized
    placement: str = "alternating"  # uniform, alternating, random, dense_base

    # Placement options
    start_offset: float = 0.1  # Start position along tentacle (0-1)
    end_offset: float = 0.95   # End position along tentacle (0-1)
    vertical_offset: float = 0.0  # Offset from surface (meters)

    # Variation
    seed: int = 42             # Random seed for variation

    def __post_init__(self):
        """Validate configuration."""
        if not 2 <= self.rows <= 8:
            raise ValueError(f"Rows must be 2-8, got {self.rows}")
        if not 4 <= self.columns <= 12:
            raise ValueError(f"Columns must be 4-12, got {self.columns}")
        if self.base_size < self.tip_size:
            raise ValueError("Base size must be >= tip size")
        if not 0.0 <= self.rim_sharpness <= 1.0:
            raise ValueError(f"Rim sharpness must be 0-1, got {self.rim_sharpness}")
        if not 8 <= self.mesh_resolution <= 32:
            raise ValueError(f"Mesh resolution must be 8-32, got {self.mesh_resolution}")

    def get_size_at_position(self, t: float) -> float:
        """
        Get sucker size at normalized position along tentacle.

        Args:
            t: Normalized position (0=base, 1=tip)

        Returns:
            Sucker size at position
        """
        # Linear interpolation from base to tip
        return self.base_size + (self.tip_size - self.base_size) * t


@dataclass
class SuckerInstance:
    """Single sucker instance data."""

    position: Tuple[float, float, float]  # World position
    normal: Tuple[float, float, float]    # Surface normal
    size: float                            # Sucker size
    rotation: float = 0.0                  # Rotation around normal
    row_index: int = 0                     # Row along tentacle
    col_index: int = 0                     # Column around circumference


@dataclass
class SuckerResult:
    """Result of sucker generation."""

    suckers: List[SuckerInstance] = field(default_factory=list)
    total_count: int = 0
    vertex_count: int = 0
    face_count: int = 0

    # For testing without Blender
    vertices: Optional[object] = None  # numpy array
    faces: Optional[object] = None     # numpy array

    @property
    def count(self) -> int:
        """Number of suckers generated."""
        return len(self.suckers)


@dataclass
class SuckerPreset:
    """Named sucker configuration preset."""

    name: str
    config: SuckerConfig
    description: str = ""
    tags: List[str] = field(default_factory=list)
