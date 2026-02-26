"""Segmentation utilities for tentacle bodies."""

from typing import List, Tuple
import numpy as np


def distribute_segment_points(
    segment_count: int,
    length: float,
    uniform: bool = True,
    variation: float = 0.0,
    seed: int = 42,
) -> np.ndarray:
    """
    Distribute segment points along tentacle length.

    Args:
        segment_count: Number of segments
        length: Total tentacle length
        uniform: Equal segment lengths
        variation: Random variation (0-0.2)
        seed: Random seed for determinism

    Returns:
        Array of z-positions for segment boundaries
    """
    if uniform and variation == 0:
        # Perfectly uniform distribution
        return np.linspace(0, length, segment_count + 1)

    # Random variation
    rng = np.random.default_rng(seed)

    # Start with uniform
    positions = np.linspace(0, length, segment_count + 1)

    # Apply variation to interior points
    if variation > 0:
        segment_length = length / segment_count
        for i in range(1, segment_count):
            offset = rng.uniform(-variation, variation) * segment_length
            positions[i] = np.clip(
                positions[i] + offset,
                positions[i - 1] + segment_length * 0.1,
                positions[i + 1] - segment_length * 0.1,
            )

    return positions


def calculate_segment_length(
    total_length: float,
    segment_count: int,
    index: int,
) -> float:
    """
    Calculate length of a specific segment.

    Args:
        total_length: Total tentacle length
        segment_count: Number of segments
        index: Segment index (0-based)

    Returns:
        Length of segment
    """
    return total_length / segment_count


def get_segment_bounds(
    total_length: float,
    segment_count: int,
    index: int,
) -> Tuple[float, float]:
    """
    Get start and end z-position of a segment.

    Args:
        total_length: Total tentacle length
        segment_count: Number of segments
        index: Segment index (0-based)

    Returns:
        (start_z, end_z) tuple
    """
    segment_length = total_length / segment_count
    start_z = index * segment_length
    end_z = (index + 1) * segment_length
    return start_z, end_z
