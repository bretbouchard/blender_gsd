"""
Quetzalcoatl Spine Generator

Procedural spine curve generation with wave deformation and taper profiles.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass

from .types import SpineConfig


@dataclass
class SpineResult:
    """Result of spine generation."""
    points: np.ndarray  # (N, 3) array of spine points
    tangents: np.ndarray  # (N, 3) tangent vectors (normalized)
    normals: np.ndarray  # (N, 3) normal vectors (perpendicular to tangent)
    binormals: np.ndarray  # (N, 3) binormal vectors (cross product)
    radii: np.ndarray  # (N,) radius at each point (normalized 0-1)
    spine_positions: np.ndarray  # (N,) normalized position along spine (0-1)

    @property
    def point_count(self) -> int:
        """Number of points in the spine."""
        return len(self.points)

    @property
    def length(self) -> float:
        """Approximate length of the spine curve."""
        # Sum of distances between consecutive points
        diffs = np.diff(self.points, axis=0)
        return np.sum(np.linalg.norm(diffs, axis=1))


class SpineGenerator:
    """Generate procedural spine curves for creature bodies."""

    def __init__(self, config: SpineConfig, seed: Optional[int] = None):
        """
        Initialize spine generator.

        Args:
            config: Spine configuration
            seed: Random seed for reproducibility
        """
        self.config = config
        self.rng = np.random.default_rng(seed)

    def generate(self) -> SpineResult:
        """
        Generate spine curve with all attributes.

        Returns:
            SpineResult containing points, vectors, and radii
        """
        n = self.config.segments
        length = self.config.length

        # Create parameter along spine (0 to 1)
        t = np.linspace(0, 1, n)

        # Create base line along X axis
        x = t * length

        # Apply primary wave deformation
        wave_amp = self.config.wave_amplitude
        wave_freq = self.config.wave_frequency
        y = wave_amp * np.sin(2 * np.pi * wave_freq * t)

        # Z variation for 3D wave (slight phase offset)
        z = wave_amp * 0.3 * np.cos(2 * np.pi * wave_freq * t + np.pi / 4)

        # Add slight noise for organic feel (deterministic via seed)
        noise_scale = wave_amp * 0.1
        y += noise_scale * self.rng.standard_normal(n) * 0.5
        z += noise_scale * self.rng.standard_normal(n) * 0.3

        # Combine into points array
        points = np.column_stack([x, y, z])

        # Calculate frame vectors
        tangents = self._calculate_tangents(points)
        normals, binormals = self._calculate_frame(tangents)

        # Calculate radii with taper profile
        radii = self._calculate_radii(t)

        return SpineResult(
            points=points,
            tangents=tangents,
            normals=normals,
            binormals=binormals,
            radii=radii,
            spine_positions=t,
        )

    def _calculate_tangents(self, points: np.ndarray) -> np.ndarray:
        """
        Calculate tangent vectors via finite differences.

        Uses central difference for interior points and
        forward/backward difference for endpoints.
        """
        n = len(points)
        tangents = np.zeros_like(points)

        # Central difference for interior points
        tangents[1:-1] = points[2:] - points[:-2]

        # Forward/backward difference for endpoints
        tangents[0] = points[1] - points[0]
        tangents[-1] = points[-1] - points[-2]

        # Normalize
        lengths = np.linalg.norm(tangents, axis=1, keepdims=True)
        tangents = tangents / np.maximum(lengths, 1e-8)

        return tangents

    def _calculate_frame(
        self, tangents: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate normal and binormal vectors for the spine frame.

        Uses the rotation-minimizing frame approach for smooth transitions.
        """
        n = len(tangents)
        normals = np.zeros_like(tangents)
        binormals = np.zeros_like(tangents)

        # Initial frame using up vector
        up = np.array([0.0, 0.0, 1.0])

        # First normal: perpendicular to tangent and up
        first_normal = np.cross(tangents[0], up)
        first_normal_len = np.linalg.norm(first_normal)
        if first_normal_len > 1e-8:
            normals[0] = first_normal / first_normal_len
        else:
            # Tangent is parallel to up, use different reference
            normals[0] = np.array([0.0, 1.0, 0.0])

        # First binormal
        binormals[0] = np.cross(tangents[0], normals[0])
        binormals[0] = binormals[0] / np.linalg.norm(binormals[0])

        # Propagate frame along curve (rotation-minimizing)
        for i in range(1, n):
            # Vector from previous to current tangent
            t_diff = tangents[i] - tangents[i - 1]

            # Reflection of normal
            n_prev = normals[i - 1]
            t_proj = np.dot(n_prev, tangents[i - 1])

            # Rotate normal to remain perpendicular
            normals[i] = n_prev - 2 * t_proj * tangents[i - 1]
            normals[i] = normals[i] / np.linalg.norm(normals[i])

            # Recalculate binormal
            binormals[i] = np.cross(tangents[i], normals[i])
            b_len = np.linalg.norm(binormals[i])
            if b_len > 1e-8:
                binormals[i] = binormals[i] / b_len

        return normals, binormals

    def _calculate_radii(self, t: np.ndarray) -> np.ndarray:
        """
        Calculate radius along spine with head/tail taper.

        Args:
            t: Normalized position along spine (0=head, 1=tail)

        Returns:
            Normalized radii (0-1 scale, to be multiplied by body.radius)
        """
        base_radius = 1.0

        # Head taper region (first 20% of spine)
        head_region = 0.2
        head_mask = t < head_region
        head_taper = np.ones_like(t)
        head_taper[head_mask] = t[head_mask] / head_region
        # Apply head taper multiplier
        head_taper = head_taper ** (1.0 / max(self.config.taper_head, 0.1))
        head_taper = np.clip(head_taper, 0.1, 1.0)

        # Tail taper region (last 30% of spine)
        tail_region = 0.3
        tail_start = 1.0 - tail_region
        tail_mask = t > tail_start
        tail_taper = np.ones_like(t)
        tail_taper[tail_mask] = (1.0 - t[tail_mask]) / tail_region
        # Apply tail taper multiplier
        tail_taper = tail_taper ** (1.0 / max(self.config.taper_tail, 0.1))
        tail_taper = np.clip(tail_taper, 0.05, 1.0)

        # Combine tapers (use minimum for smooth transition)
        radii = base_radius * np.minimum(head_taper, tail_taper)

        # Add slight bulge in middle body region
        body_bulge = 1.0 + 0.2 * np.sin(np.pi * t)
        radii = radii * body_bulge

        return radii


def generate_spine(
    length: float = 10.0,
    segments: int = 64,
    taper_head: float = 0.3,
    taper_tail: float = 0.2,
    wave_amplitude: float = 0.5,
    wave_frequency: int = 3,
    seed: Optional[int] = None,
) -> SpineResult:
    """
    Convenience function to generate a spine curve.

    Args:
        length: Total spine length (1-100 meters)
        segments: Number of points in curve
        taper_head: Head taper factor (0-1)
        taper_tail: Tail taper factor (0-1)
        wave_amplitude: Wave amplitude in meters
        wave_frequency: Number of wave cycles
        seed: Random seed for reproducibility

    Returns:
        SpineResult with generated spine data
    """
    config = SpineConfig(
        length=length,
        segments=segments,
        taper_head=taper_head,
        taper_tail=taper_tail,
        wave_amplitude=wave_amplitude,
        wave_frequency=wave_frequency,
    )
    generator = SpineGenerator(config, seed=seed)
    return generator.generate()
