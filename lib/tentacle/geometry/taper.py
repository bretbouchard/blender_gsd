"""Taper profile calculations for tentacle bodies."""

from typing import List, Optional, Tuple
import numpy as np

from ..types import TaperProfile


def calculate_taper_radii(
    point_count: int,
    base_radius: float,
    tip_radius: float,
    profile_type: str = "organic",
    profile: Optional[TaperProfile] = None,
) -> np.ndarray:
    """
    Calculate radius at each point along tentacle length.

    Args:
        point_count: Number of points along tentacle
        base_radius: Radius at base (start)
        tip_radius: Radius at tip (end)
        profile_type: Built-in profile type
        profile: Custom profile (overrides profile_type)

    Returns:
        Array of radii for each point
    """
    t = np.linspace(0, 1, point_count)

    if profile and profile.points:
        # Use custom profile points
        return _interpolate_custom_profile(t, profile, base_radius, tip_radius)

    # Use built-in profile
    if profile_type == "linear":
        factors = _linear_profile(t)
    elif profile_type == "smooth":
        factors = _smooth_profile(t)
    elif profile_type == "organic":
        factors = _organic_profile(t, base_ratio=2.5, mid_point=0.4)
    else:
        factors = _organic_profile(t)  # Default to organic

    # Scale to actual radii
    return tip_radius + (base_radius - tip_radius) * (1 - factors)


def _linear_profile(t: np.ndarray) -> np.ndarray:
    """Linear taper from base to tip."""
    return t


def _smooth_profile(t: np.ndarray) -> np.ndarray:
    """Smooth ease-in-out taper."""
    # Smoothstep function: 3t² - 2t³
    return 3 * t**2 - 2 * t**3


def _organic_profile(
    t: np.ndarray,
    base_ratio: float = 2.5,
    mid_point: float = 0.4,
) -> np.ndarray:
    """
    Organic/natural taper with bulbous base.

    Args:
        t: Normalized position (0-1)
        base_ratio: Ratio of base to tip diameter
        mid_point: Where taper accelerates (0-1)

    Returns:
        Radius factors (0 at base, 1 at tip)
    """
    # Create smooth organic curve
    # Faster taper at base, slower toward tip
    factor = np.zeros_like(t)

    for i, ti in enumerate(t):
        if ti < mid_point:
            # Bulbous base - slower initial taper
            factor[i] = 0.5 * (ti / mid_point) ** 2
        else:
            # Accelerating taper toward tip
            normalized = (ti - mid_point) / (1 - mid_point)
            factor[i] = 0.5 + 0.5 * (2 * normalized - normalized**2)

    return factor


def _interpolate_custom_profile(
    t: np.ndarray,
    profile: TaperProfile,
    base_radius: float,
    tip_radius: float,
) -> np.ndarray:
    """Interpolate custom profile points."""
    points = sorted(profile.points, key=lambda p: p[0])
    positions = np.array([p[0] for p in points])
    factors = np.array([p[1] for p in points])

    # Interpolate
    result = np.interp(t, positions, factors)

    # Scale to radii
    return tip_radius + (base_radius - tip_radius) * (1 - result)


def create_taper_curve(
    base_radius: float,
    tip_radius: float,
    resolution: int = 64,
    profile_type: str = "organic",
) -> List[Tuple[float, float, float]]:
    """
    Create taper curve as list of (x, y, z) points.

    Args:
        base_radius: Radius at base
        tip_radius: Radius at tip
        resolution: Number of points
        profile_type: Profile type

    Returns:
        List of (x, y, z) tuples for curve points
    """
    radii = calculate_taper_radii(resolution, base_radius, tip_radius, profile_type)

    points = []
    for i, radius in enumerate(radii):
        z = i / (resolution - 1)  # Normalized length
        points.append((radius, 0, z))

    return points
