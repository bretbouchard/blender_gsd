"""
Magneto-mechanical tile connection system.

This module provides the magneto-mechanical connection logic for tiles,
including visual feedback, connection tracking, and strength calculations.
The system creates a satisfying attachment experience with visual cues.

All code is pure Python - no Blender dependencies for testability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Tuple

from .feedback import (
    FeedbackSequence,
    TileFeedback,
    connection_sequence,
    disconnection_sequence,
)


class ConnectionStyle(Enum):
    """Visual style for magneto-mechanical connections."""

    INDUSTRIAL = "industrial"  # Rough, mechanical look
    HIGH_TECH = "high_tech"  # Sleek, electronic look
    BRUTALIST = "brutalist"  # Bold, geometric look


@dataclass
class MagnetoConfig:
    """
    Configuration for magneto-mechanical connection system.

    Attributes:
        style: Visual style for connections
        feedback: Feedback sequence to play on connections
        connection_strength: Base strength of connections (0.0-1.0)
        magnetic_field_radius: Radius of magnetic field effect
    """

    style: ConnectionStyle = ConnectionStyle.HIGH_TECH
    feedback: FeedbackSequence = field(default_factory=lambda: connection_sequence())
    connection_strength: float = 0.8
    magnetic_field_radius: float = 1.5

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0.0 <= self.connection_strength <= 1.0:
            raise ValueError(
                f"Connection strength must be between 0.0 and 1.0, got {self.connection_strength}"
            )
        if self.magnetic_field_radius < 0:
            raise ValueError(
                f"Magnetic field radius must be non-negative, got {self.magnetic_field_radius}"
            )

        # Update feedback sequence based on style
        style_name = self.style.value
        self.feedback = connection_sequence(style_name)


@dataclass
class MagnetoMechanical:
    """
    Magneto-mechanical tile connection system.

    Manages tile connections with visual feedback and strength tracking.
    Provides satisfying connection/disconnection experience.

    Attributes:
        config: Configuration for the connection system
        connected_tiles: Set of connected tile positions
    """

    config: MagnetoConfig = field(default_factory=MagnetoConfig)
    connected_tiles: Set[Tuple[int, int]] = field(default_factory=set)

    def connect_tile(self, pos: Tuple[int, int]) -> TileFeedback:
        """
        Connect a tile at the given position.

        Args:
            pos: Grid position (x, y) to connect

        Returns:
            TileFeedback to play when tile connects

        Raises:
            ValueError: If position is already connected
        """
        if pos in self.connected_tiles:
            raise ValueError(f"Tile at {pos} is already connected")

        # Track connection
        self.connected_tiles.add(pos)

        # Return first effect from sequence (primary feedback)
        if self.config.feedback.effects:
            return self.config.feedback.effects[0]

        # Default feedback if sequence is empty
        return TileFeedback(
            effect_type=self._get_default_effect(),
            duration=0.3,
            intensity=0.8,
            color=(0.6, 0.8, 1.0, 1.0),
        )

    def disconnect_tile(self, pos: Tuple[int, int]) -> TileFeedback:
        """
        Disconnect a tile at the given position.

        Args:
            pos: Grid position (x, y) to disconnect

        Returns:
            TileFeedback to play when tile disconnects

        Raises:
            ValueError: If position is not connected
        """
        if pos not in self.connected_tiles:
            raise ValueError(f"Tile at {pos} is not connected")

        # Remove connection
        self.connected_tiles.remove(pos)

        # Return disconnection feedback
        style_name = self.config.style.value
        disconnect_seq = disconnection_sequence(style_name)

        if disconnect_seq.effects:
            return disconnect_seq.effects[0]

        # Default feedback if sequence is empty
        return TileFeedback(
            effect_type=self._get_default_effect(),
            duration=0.2,
            intensity=0.6,
            color=(0.5, 0.7, 0.9, 1.0),
        )

    def is_connected(self, pos: Tuple[int, int]) -> bool:
        """
        Check if a tile is connected at the given position.

        Args:
            pos: Grid position (x, y) to check

        Returns:
            True if tile is connected, False otherwise
        """
        return pos in self.connected_tiles

    def get_connection_strength(self, pos: Tuple[int, int]) -> float:
        """
        Get the connection strength at a given position.

        Strength is calculated based on:
        - Base connection strength from config
        - Distance from center (tiles closer to center are stronger)
        - Maximum distance is based on magnetic field radius

        Args:
            pos: Grid position (x, y) to check

        Returns:
            Connection strength (0.0-1.0), or 0.0 if not connected
        """
        if not self.is_connected(pos):
            return 0.0

        # Calculate distance from center (0, 0)
        distance = (pos[0] ** 2 + pos[1] ** 2) ** 0.5

        # Normalize by magnetic field radius
        normalized_distance = distance / self.config.magnetic_field_radius

        # Strength decreases with distance (linear falloff)
        # Tiles at center have full strength, tiles at radius have 50% strength
        distance_factor = max(0.5, 1.0 - normalized_distance * 0.5)

        return self.config.connection_strength * distance_factor

    def get_all_connections(self) -> Set[Tuple[int, int]]:
        """
        Get all connected tile positions.

        Returns:
            Set of connected positions
        """
        return self.connected_tiles.copy()

    def clear_all_connections(self) -> int:
        """
        Clear all connections.

        Returns:
            Number of connections cleared
        """
        count = len(self.connected_tiles)
        self.connected_tiles.clear()
        return count

    def _get_default_effect(self):
        """Get default visual effect based on style."""
        from .feedback import VisualEffect

        style_effects = {
            ConnectionStyle.INDUSTRIAL: VisualEffect.MAGNETIC,
            ConnectionStyle.HIGH_TECH: VisualEffect.GLOW,
            ConnectionStyle.BRUTALIST: VisualEffect.LOCK,
        }
        return style_effects.get(self.config.style, VisualEffect.MAGNETIC)
