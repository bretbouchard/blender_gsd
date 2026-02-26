"""
Tentacle Vein Pattern Generator

Procedural vein pattern generation for organic tentacle materials.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import VeinConfig


@dataclass
class VeinPatternResult:
    """Result from vein pattern generation."""

    pattern_name: str
    """Name of the generated pattern."""

    success: bool = True
    """Whether generation was successful."""

    texture_size: Tuple[int, int] = (512, 512)
    """Size of the generated texture."""

    vein_count: int = 0
    """Number of veins generated."""

    error: Optional[str] = None
    """Error message if failed."""


class VeinPatternGenerator:
    """Generator for procedural vein patterns."""

    def __init__(self, config: VeinConfig):
        """Initialize the vein pattern generator.

        Args:
            config: Vein configuration
        """
        self.config = config

    def generate_numpy(self, size: Tuple[int, int], seed: Optional[int] = None) -> np.ndarray:
        """
        Generate vein pattern using numpy (for testing).

        Args:
            size: Texture size (width, height)
            seed: Random seed for reproducibility

        Returns:
            Numpy array with vein pattern (0.0-1.0)
        """
        if seed is not None:
            np.random.seed(seed)

        width, height = size

        # Create base noise for vein structure
        # Use Voronoi noise for vein-like patterns
        noise = np.zeros((height, width))

        # Generate vein center points
        num_veins = int(20 * self.config.density)
        for i in range(num_veins):
            # Random center for each vein branch
            cx = np.random.randint(1, width - 2)
            cy = np.random.randint(1, height - 2)

            # Calculate distance from this point
            y_coords, x_coords = np.ogrid[:height, :width]
            dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)

            # Create vein falloff (closer to center = stronger)
            vein_strength = np.exp(-dist ** 2 / (width * self.config.scale * 10))
            noise = np.maximum(noise, vein_strength)

        # Apply vein color
        vein_mask = noise > 0.3
        # Return grayscale intensity map
        pattern = np.where(vein_mask, noise, 0.0)

        # Add glow if enabled (adds glow intensity to the pattern)
        if self.config.glow:
            # Glow adds intensity based on glow_intensity factor
            glow_boost = np.mean(self.config.glow_color) * self.config.glow_intensity
            pattern = pattern * 0.5 + glow_boost

        return np.clip(pattern, 0.0, 1.0)

    def generate_texture(
        self,
        name: str,
        size: Tuple[int, int] = (512, 512),
        seed: Optional[int] = None,
    ) -> VeinPatternResult:
        """
        Generate vein pattern texture.

        Args:
            name: Texture name
            size: Texture size (width, height)
            seed: Random seed for reproducibility

        Returns:
            VeinPatternResult with generation details
        """
        if not self.config.enabled:
            # Return black texture if veins disabled
            return VeinPatternResult(
                pattern_name=name,
                success=True,
                texture_size=size,
                vein_count=0,
            )

        if not BLENDER_AVAILABLE:
            # Use numpy fallback
            pattern = self.generate_numpy(size, seed)
            return VeinPatternResult(
                pattern_name=name,
                success=True,
                texture_size=size,
                vein_count=int(20 * self.config.density),
            )

        try:
            # Generate using numpy first
            pattern = self.generate_numpy(size, seed)

            # Create Blender texture
            texture = bpy.data.images.new(name, width=size[0], height=size[1])
            texture.pixels[:] = pattern

            return VeinPatternResult(
                pattern_name=name,
                success=True,
                texture_size=size,
                vein_count=int(20 * self.config.density),
            )

        except Exception as e:
            return VeinPatternResult(
                pattern_name=name,
                success=False,
                error=str(e),
            )


def generate_vein_pattern(
    config: VeinConfig,
    name: str = "VeinPattern",
    size: Tuple[int, int] = (512, 512),
    seed: Optional[int] = None,
) -> VeinPatternResult:
    """
    Convenience function to generate a vein pattern.

    Args:
        config: Vein configuration
        name: Texture name
        size: Texture size (width, height)
        seed: Random seed

    Returns:
        VeinPatternResult with generation details
    """
    generator = VeinPatternGenerator(config)
    return generator.generate_texture(name, size, seed)


def create_bioluminescent_pattern(
    glow_color: Tuple[float, float, float] = (0.0, 1.0, 0.5),
    intensity: float = 0.5,
    name: str = "BioluminescentVeins",
    size: Tuple[int, int] = (512, 512),
    seed: Optional[int] = None,
) -> VeinPatternResult:
    """
    Convenience function to create bioluminescent vein pattern.

    Args:
        glow_color: Glow color (RGB 0-1)
        intensity: Glow intensity (0-1)
        name: Texture name
        size: Texture size
        seed: Random seed

    Returns:
        VeinPatternResult with generation details
    """
    config = VeinConfig(
        enabled=True,
        color=(0.2, 0.2, 0.2),
        density=0.6,
        scale=0.05,
        depth=0.01,
        glow=True,
        glow_color=glow_color,
        glow_intensity=intensity,
    )
    return generate_vein_pattern(config, name, size, seed)
