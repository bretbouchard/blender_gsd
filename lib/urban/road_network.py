"""
Road Network Generator

High-level road network generation with presets for different city layouts.
Provides convenient factory functions for common network configurations.

Implements REQ-UR-01: Road Network Generator convenience functions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import random
import math

from .types import (
    RoadNetwork,
    RoadNode,
    RoadEdge,
    LaneConfig,
    NodeType,
    UrbanStyle,
)
from .l_system import LSystemRoads, generate_road_network


# =============================================================================
# ROAD NETWORK PRESETS
# =============================================================================

@dataclass
class RoadNetworkPreset:
    """Road network preset configuration."""
    name: str
    description: str
    pattern: str
    dimensions: Tuple[float, float]
    iterations: int
    style: str
    default_lanes: int
    has_sidewalks: bool
    has_bike_lanes: bool


ROAD_NETWORK_PRESETS: Dict[str, RoadNetworkPreset] = {
    # Urban grids
    "small_grid": RoadNetworkPreset(
        name="Small City Grid",
        description="Small city block grid (4x4 blocks)",
        pattern="grid",
        dimensions=(200.0, 200.0),
        iterations=2,
        style="american_grid",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=True,
    ),
    "medium_grid": RoadNetworkPreset(
        name="Medium City Grid",
        description="Medium city grid (6x6 blocks)",
        pattern="grid",
        dimensions=(400.0, 400.0),
        iterations=3,
        style="modern_urban",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=True,
    ),
    "large_grid": RoadNetworkPreset(
        name="Large City Grid",
        description="Large city grid (10x10 blocks)",
        pattern="grid",
        dimensions=(800.0, 800.0),
        iterations=4,
        style="downtown",
        default_lanes=4,
        has_sidewalks=True,
        has_bike_lanes=True,
    ),

    # Organic layouts
    "organic_small": RoadNetworkPreset(
        name="Small Organic",
        description="Small organic road layout",
        pattern="organic",
        dimensions=(150.0, 150.0),
        iterations=2,
        style="european",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=False,
    ),
    "organic_large": RoadNetworkPreset(
        name="Large Organic",
        description="Large organic city layout",
        pattern="organic",
        dimensions=(500.0, 500.0),
        iterations=3,
        style="historic",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=True,
    ),

    # Suburban
    "suburban_small": RoadNetworkPreset(
        name="Small Subdivision",
        description="Small suburban subdivision",
        pattern="suburban",
        dimensions=(200.0, 200.0),
        iterations=2,
        style="suburban",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=False,
    ),
    "suburban_large": RoadNetworkPreset(
        name="Large Subdivision",
        description="Large suburban subdivision",
        pattern="suburban",
        dimensions=(400.0, 400.0),
        iterations=3,
        style="suburban",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=False,
    ),

    # Highway
    "highway_interchange": RoadNetworkPreset(
        name="Highway Interchange",
        description="Highway with interchange",
        pattern="highway",
        dimensions=(300.0, 300.0),
        iterations=2,
        style="modern_urban",
        default_lanes=4,
        has_sidewalks=False,
        has_bike_lanes=False,
    ),

    # Downtown
    "downtown_core": RoadNetworkPreset(
        name="Downtown Core",
        description="Dense downtown grid",
        pattern="downtown",
        dimensions=(300.0, 300.0),
        iterations=3,
        style="downtown",
        default_lanes=4,
        has_sidewalks=True,
        has_bike_lanes=True,
    ),

    # Village
    "village": RoadNetworkPreset(
        name="Village",
        description="Small village road network",
        pattern="organic",
        dimensions=(100.0, 100.0),
        iterations=1,
        style="village",
        default_lanes=1,
        has_sidewalks=False,
        has_bike_lanes=False,
    ),

    # Industrial
    "industrial_park": RoadNetworkPreset(
        name="Industrial Park",
        description="Industrial area grid",
        pattern="grid",
        dimensions=(400.0, 400.0),
        iterations=2,
        style="industrial",
        default_lanes=2,
        has_sidewalks=False,
        has_bike_lanes=False,
    ),

    # Campus
    "campus": RoadNetworkPreset(
        name="Campus",
        description="University/corporate campus",
        pattern="organic",
        dimensions=(250.0, 250.0),
        iterations=2,
        style="campus",
        default_lanes=2,
        has_sidewalks=True,
        has_bike_lanes=True,
    ),
}


class RoadNetworkGenerator:
    """
    High-level road network generator with presets and customization.

    Usage:
        generator = RoadNetworkGenerator()
        network = generator.generate_preset("medium_grid")
        network = generator.generate_custom(dimensions=(300, 300), pattern="grid")
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed

    def generate_preset(self, preset_name: str) -> RoadNetwork:
        """
        Generate road network from preset.

        Args:
            preset_name: Name of preset to use

        Returns:
            Generated RoadNetwork
        """
        if preset_name not in ROAD_NETWORK_PRESETS:
            available = list(ROAD_NETWORK_PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

        preset = ROAD_NETWORK_PRESETS[preset_name]

        lsystem = LSystemRoads(seed=self.seed or preset_name.__hash__())
        network = lsystem.generate(
            axiom=self._get_axiom_for_pattern(preset.pattern),
            iterations=preset.iterations,
            pattern=preset.pattern,
            dimensions=preset.dimensions,
        )

        network.style = preset.style
        return network

    def generate_custom(
        self,
        dimensions: Tuple[float, float],
        pattern: str = "grid",
        iterations: int = 3,
        style: str = "modern_urban",
        lane_count: int = 2,
    ) -> RoadNetwork:
        """
        Generate custom road network.

        Args:
            dimensions: Network dimensions
            pattern: L-system pattern
            iterations: Number of iterations
            style: Urban style preset
            lane_count: Default lane count

        Returns:
            Generated RoadNetwork
        """
        network = generate_road_network(
            pattern=pattern,
            dimensions=dimensions,
            iterations=iterations,
            seed=self.seed,
        )

        network.style = style

        # Update lane counts
        for edge in network.edges:
            edge.lanes.count = lane_count

        return network

    def _get_axiom_for_pattern(self, pattern: str) -> str:
        """Get starting axiom for a pattern."""
        axioms = {
            "grid": "R+R+R+R",
            "organic": "R~R~R~R",
            "suburban": "R[R]R[R]R",
            "highway": "H+H+H+H",
            "downtown": "R+R+R+R",
        }
        return axioms.get(pattern, "R+R+R+R")

    def list_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list(ROAD_NETWORK_PRESETS.keys())

    def get_preset_info(self, preset_name: str) -> Dict[str, Any]:
        """Get information about a preset."""
        if preset_name not in ROAD_NETWORK_PRESETS:
            raise ValueError(f"Unknown preset '{preset_name}'")

        preset = ROAD_NETWORK_PRESETS[preset_name]
        return {
            "name": preset.name,
            "description": preset.description,
            "dimensions": preset.dimensions,
            "pattern": preset.pattern,
            "iterations": preset.iterations,
            "style": preset.style,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_grid_network(
    size: str = "medium",
    seed: Optional[int] = None,
) -> RoadNetwork:
    """
    Generate grid-based road network.

    Args:
        size: Size preset ("small", "medium", "large")
        seed: Random seed

    Returns:
        Generated RoadNetwork
    """
    preset_map = {
        "small": "small_grid",
        "medium": "medium_grid",
        "large": "large_grid",
    }

    preset_name = preset_map.get(size, "medium_grid")
    generator = RoadNetworkGenerator(seed=seed)
    return generator.generate_preset(preset_name)


def generate_organic_network(
    size: str = "medium",
    seed: Optional[int] = None,
) -> RoadNetwork:
    """
    Generate organic/curved road network.

    Args:
        size: Size preset ("small", "large")
        seed: Random seed

    Returns:
        Generated RoadNetwork
    """
    preset_map = {
        "small": "organic_small",
        "medium": "organic_large",
        "large": "organic_large",
    }

    preset_name = preset_map.get(size, "organic_small")
    generator = RoadNetworkGenerator(seed=seed)
    return generator.generate_preset(preset_name)


def generate_suburban_network(
    size: str = "medium",
    seed: Optional[int] = None,
) -> RoadNetwork:
    """
    Generate suburban subdivision network.

    Args:
        size: Size preset ("small", "large")
        seed: Random seed

    Returns:
        Generated RoadNetwork
    """
    preset_map = {
        "small": "suburban_small",
        "medium": "suburban_large",
        "large": "suburban_large",
    }

    preset_name = preset_map.get(size, "suburban_small")
    generator = RoadNetworkGenerator(seed=seed)
    return generator.generate_preset(preset_name)


def list_network_presets() -> List[str]:
    """Get list of all available network presets."""
    return list(ROAD_NETWORK_PRESETS.keys())


def get_network_preset(preset_name: str) -> RoadNetworkPreset:
    """Get network preset configuration."""
    if preset_name not in ROAD_NETWORK_PRESETS:
        raise ValueError(f"Unknown preset '{preset_name}'")
    return ROAD_NETWORK_PRESETS[preset_name]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RoadNetworkPreset",
    "ROAD_NETWORK_PRESETS",
    "RoadNetworkGenerator",
    "generate_grid_network",
    "generate_organic_network",
    "generate_suburban_network",
    "list_network_presets",
    "get_network_preset",
]
