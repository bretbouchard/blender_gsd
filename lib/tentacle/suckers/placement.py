"""Sucker placement calculations."""

from typing import List, Tuple
import numpy as np

from .types import SuckerConfig, SuckerInstance


def calculate_sucker_positions(
    config: SuckerConfig,
    tentacle_length: float,
    tentacle_radius_func,
) -> List[SuckerInstance]:
    """
    Calculate all sucker positions along a tentacle.

    Args:
        config: Sucker configuration
        tentacle_length: Total tentacle length
        tentacle_radius_func: Function(t) -> radius at position t

    Returns:
        List of SuckerInstance objects
    """
    if not config.enabled:
        return []

    suckers = []
    rng = np.random.default_rng(config.seed)

    # Calculate row positions (along length)
    row_positions = _calculate_row_positions(config, tentacle_length, rng)

    for row_idx, t in enumerate(row_positions):
        # Get radius at this position
        radius = tentacle_radius_func(t)
        sucker_size = config.get_size_at_position(t)

        # Calculate column positions (around circumference)
        column_angles = _calculate_column_angles(config, row_idx, rng)

        for col_idx, angle in enumerate(column_angles):
            # Add size variation
            size = sucker_size * (1.0 + rng.uniform(-config.size_variation, config.size_variation))

            # Calculate position on surface
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = t * tentacle_length + config.vertical_offset

            # Normal points outward
            nx = np.cos(angle)
            ny = np.sin(angle)
            nz = 0.0

            sucker = SuckerInstance(
                position=(x, y, z),
                normal=(nx, ny, nz),
                size=size,
                rotation=0.0,
                row_index=row_idx,
                col_index=col_idx,
            )
            suckers.append(sucker)

    return suckers


def _calculate_row_positions(
    config: SuckerConfig,
    tentacle_length: float,
    rng: np.random.Generator,
) -> List[float]:
    """
    Calculate normalized positions for sucker rows along tentacle length.

    Args:
        config: Sucker configuration
        tentacle_length: Total tentacle length (unused, for reference)
        rng: Random number generator

    Returns:
        List of normalized positions (0-1) for each row
    """
    positions = []

    # Effective range
    t_start = config.start_offset
    t_end = config.end_offset
    t_range = t_end - t_start

    if config.placement == "uniform":
        # Evenly spaced
        for i in range(config.rows):
            t = t_start + (i / (config.rows - 1)) * t_range if config.rows > 1 else t_start
            positions.append(t)

    elif config.placement == "alternating":
        # Evenly spaced (alternation handled in columns)
        for i in range(config.rows):
            t = t_start + (i / (config.rows - 1)) * t_range if config.rows > 1 else t_start
            positions.append(t)

    elif config.placement == "random":
        # Random positions within range
        for i in range(config.rows):
            t = rng.uniform(t_start, t_end)
            positions.append(t)
        positions.sort()

    elif config.placement == "dense_base":
        # More suckers at base, fewer at tip
        for i in range(config.rows):
            # Exponential distribution toward base
            t_normalized = i / (config.rows - 1) if config.rows > 1 else 0.5
            t = t_start + (t_normalized ** 1.5) * t_range
            positions.append(t)

    else:
        # Default to uniform
        for i in range(config.rows):
            t = t_start + (i / (config.rows - 1)) * t_range if config.rows > 1 else t_start
            positions.append(t)

    return positions


def _calculate_column_angles(
    config: SuckerConfig,
    row_index: int,
    rng: np.random.Generator,
) -> List[float]:
    """
    Calculate angles for sucker columns around circumference.

    Args:
        config: Sucker configuration
        row_index: Current row index
        rng: Random number generator

    Returns:
        List of angles (radians) for each column
    """
    angles = []
    base_angle_step = 2 * np.pi / config.columns

    # Offset for alternating rows
    offset = 0.0
    if config.placement == "alternating" and row_index % 2 == 1:
        offset = base_angle_step / 2

    for col in range(config.columns):
        angle = offset + col * base_angle_step
        angles.append(angle)

    return angles


def calculate_sucker_mesh_size(
    sucker_size: float,
    cup_depth: float,
    rim_width: float,
    resolution: int = 16,
) -> Tuple[int, int]:
    """
    Calculate expected vertex and face count for a single sucker mesh.

    Args:
        sucker_size: Sucker diameter
        cup_depth: Cup depth
        rim_width: Rim thickness
        resolution: Mesh resolution

    Returns:
        (vertex_count, face_count) tuple
    """
    # Approximate: cup is a hemisphere-like shape
    # Vertices: rings of resolution points
    rings = max(4, resolution // 4)
    vertices = rings * resolution + 1  # +1 for center
    faces = (rings - 1) * resolution * 2  # Quads + tris

    return vertices, faces
