"""
Intersection Builder

Creates intersection geometry for road networks.
Handles 4-way, 3-way, and roundabout intersections.

Implements REQ-UR-03: Intersection System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math

from .types import RoadNetwork, RoadNode, IntersectionType


class IntersectionShape(Enum):
    """Intersection shape types."""
    SQUARE = "square"
    CIRCULAR = "circular"
    OCTAGONAL = "octagonal"
    CUSTOM = "custom"


@dataclass
class IntersectionConfig:
    """
    Intersection configuration.

    Attributes:
        intersection_type: Type of intersection
        radius: Radius for circular intersections
        has_crosswalks: Whether intersection has crosswalks
        has_traffic_signals: Whether intersection has traffic signals
        has_stop_signs: Whether intersection has stop signs
        crosswalk_width: Crosswalk width in meters
        island_radius: Central island radius for roundabouts
    """
    intersection_type: str = "four_way"
    radius: float = 8.0
    has_crosswalks: bool = True
    has_traffic_signals: bool = False
    has_stop_signs: bool = False
    crosswalk_width: float = 3.0
    island_radius: float = 5.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intersection_type": self.intersection_type,
            "radius": self.radius,
            "has_crosswalks": self.has_crosswalks,
            "has_traffic_signals": self.has_traffic_signals,
            "has_stop_signs": self.has_stop_signs,
            "crosswalk_width": self.crosswalk_width,
            "island_radius": self.island_radius,
        }


@dataclass
class IntersectionGeometry:
    """
    Generated intersection geometry.

    Attributes:
        node_id: Source node ID
        position: Center position (x, y, z)
        config: Intersection configuration
        crosswalk_positions: Positions for crosswalks
        signal_positions: Positions for traffic signals
    """
    node_id: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    config: Optional[IntersectionConfig] = None
    crosswalk_positions: List[Tuple[float, float, float, float]] = field(default_factory=list)  # x, y, z, rotation
    signal_positions: List[Tuple[float, float, float, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "position": list(self.position),
            "config": self.config.to_dict() if self.config else None,
            "crosswalk_positions": [list(p) for p in self.crosswalk_positions],
            "signal_positions": [list(p) for p in self.signal_positions],
        }


class IntersectionBuilder:
    """
    Creates intersection geometry from road network nodes.

    Usage:
        builder = IntersectionBuilder()
        intersections = builder.build_from_network(network)
    """

    def __init__(self, default_radius: float = 8.0):
        """
        Initialize intersection builder.

        Args:
            default_radius: Default intersection radius
        """
        self.default_radius = default_radius

    def build_from_network(self, network: RoadNetwork) -> List[IntersectionGeometry]:
        """
        Build intersections from network.

        Args:
            network: RoadNetwork to process

        Returns:
            List of IntersectionGeometry
        """
        intersections = []

        for node in network.nodes:
            if node.node_type in ["intersection_4way", "intersection_3way", "roundabout"]:
                intersection = self._create_intersection(node, network)
                if intersection:
                    intersections.append(intersection)

        return intersections

    def _create_intersection(
        self,
        node: RoadNode,
        network: RoadNetwork
    ) -> Optional[IntersectionGeometry]:
        """Create intersection geometry from node."""
        config = IntersectionConfig(
            intersection_type=node.node_type,
            has_crosswalks=node.has_crosswalk,
            has_traffic_signals=node.has_traffic_light,
        )

        geometry = IntersectionGeometry(
            node_id=node.id,
            position=(node.position[0], node.position[1], node.elevation),
            config=config,
        )

        # Add crosswalks and signals based on intersection type
        if node.node_type == "intersection_4way":
            geometry = self._configure_four_way(geometry, node, network)
        elif node.node_type == "intersection_3way":
            geometry = self._configure_three_way(geometry, node, network)
        elif node.node_type == "roundabout":
            geometry = self._configure_roundabout(geometry, node, network)

        return geometry

    def _configure_four_way(
        self,
        geometry: IntersectionGeometry,
        node: RoadNode,
        network: RoadNetwork
    ) -> IntersectionGeometry:
        """Configure 4-way intersection."""
        x, y, z = geometry.position
        radius = geometry.config.radius if geometry.config else self.default_radius

        # Crosswalks at all four approaches
        if geometry.config and geometry.config.has_crosswalks:
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                cx = x + (radius + 2) * math.cos(rad)
                cy = y + (radius + 2) * math.sin(rad)
                geometry.crosswalk_positions.append((cx, cy, z, angle))

        # Traffic signals at corners
        if geometry.config and geometry.config.has_traffic_signals:
            for angle in [45, 135, 225, 315]:
                rad = math.radians(angle)
                sx = x + (radius - 1) * math.cos(rad)
                sy = y + (radius - 1) * math.sin(rad)
                geometry.signal_positions.append((sx, sy, z + 0.5, angle))

        return geometry

    def _configure_three_way(
        self,
        geometry: IntersectionGeometry,
        node: RoadNode,
        network: RoadNetwork
    ) -> IntersectionGeometry:
        """Configure 3-way (T) intersection."""
        x, y, z = geometry.position
        radius = geometry.config.radius if geometry.config else self.default_radius

        # Three crosswalks
        if geometry.config and geometry.config.has_crosswalks:
            for angle in [0, 120, 240]:
                rad = math.radians(angle)
                cx = x + (radius + 2) * math.cos(rad)
                cy = y + (radius + 2) * math.sin(rad)
                geometry.crosswalk_positions.append((cx, cy, z, angle))

        # Stop signs or signals
        if geometry.config and geometry.config.has_stop_signs:
            for angle in [60, 180, 300]:
                rad = math.radians(angle)
                sx = x + (radius - 0.5) * math.cos(rad)
                sy = y + (radius - 0.5) * math.sin(rad)
                geometry.signal_positions.append((sx, sy, z + 0.3, angle))

        return geometry

    def _configure_roundabout(
        self,
        geometry: IntersectionGeometry,
        node: RoadNode,
        network: RoadNetwork
    ) -> IntersectionGeometry:
        """Configure roundabout intersection."""
        x, y, z = geometry.position

        if geometry.config:
            geometry.config.island_radius = self.default_radius * 0.6
            geometry.config.has_crosswalks = True
            geometry.config.has_traffic_signals = False

            # Crosswalks at approaches
            radius = geometry.config.radius
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                cx = x + (radius + 3) * math.cos(rad)
                cy = y + (radius + 3) * math.sin(rad)
                geometry.crosswalk_positions.append((cx, cy, z, angle))

        return geometry


def create_intersection_geometry(network: RoadNetwork) -> List[IntersectionGeometry]:
    """
    Convenience function to create intersection geometry.

    Args:
        network: RoadNetwork to process

    Returns:
        List of IntersectionGeometry
    """
    builder = IntersectionBuilder()
    return builder.build_from_network(network)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "IntersectionShape",
    "IntersectionConfig",
    "IntersectionGeometry",
    "IntersectionBuilder",
    "create_intersection_geometry",
]
