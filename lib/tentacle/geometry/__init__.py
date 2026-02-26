"""Tentacle geometry generation package."""

from .body import (
    TentacleBodyGenerator,
    TentacleResult,
    create_tentacle,
)
from .taper import (
    calculate_taper_radii,
    create_taper_curve,
)
from .segments import (
    distribute_segment_points,
    calculate_segment_length,
    get_segment_bounds,
)

__all__ = [
    # Body generation
    "TentacleBodyGenerator",
    "TentacleResult",
    "create_tentacle",

    # Taper
    "calculate_taper_radii",
    "create_taper_curve",

    # Segments
    "distribute_segment_points",
    "calculate_segment_length",
    "get_segment_bounds",
]
