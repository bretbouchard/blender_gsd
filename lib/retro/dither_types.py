"""
Dithering Types for Retro Style Conversion

Defines dataclasses for dithering configuration, threshold matrices,
and pattern definitions for various dithering algorithms.

All classes designed for YAML serialization via to_dict() and
deserialization via from_dict() class methods.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import math


class DitherMode(str, Enum):
    """Dithering modes for color reduction."""
    NONE = "none"
    ORDERED_2X2 = "ordered_2x2"
    ORDERED_4X4 = "ordered_4x4"
    ORDERED_8X8 = "ordered_8x8"
    BAYER_2X2 = "bayer_2x2"
    BAYER_4X4 = "bayer_4x4"
    BAYER_8X8 = "bayer_8x8"
    ERROR_DIFFUSION = "error_diffusion"
    FLOYD_STEINBERG = "floyd_steinberg"
    ATKINSON = "atkinson"
    SIERRA = "sierra"
    SIERRA_LITE = "sierra_lite"
    JARVIS_JUDICE_NINKE = "jarvis_judice_ninke"
    CHECKERBOARD = "checkerboard"
    HALFTONE = "halftone"
    RANDOM = "random"
    CUSTOM = "custom"


class DitherColorSpace(str, Enum):
    """Color spaces for dithering calculations."""
    RGB = "rgb"       # Standard RGB
    LAB = "lab"       # Perceptually uniform CIE Lab
    LUMA = "luma"     # Luminance only (grayscale)


@dataclass
class DitherConfig:
    """
    Dithering configuration.

    Defines the parameters for applying dithering to images, including
    mode selection, strength, color space, and custom patterns.

    Attributes:
        mode: Dithering mode (none, ordered_2x2, bayer_4x4, error_diffusion, etc.)
        strength: Dithering intensity (0.0-1.0, where 1.0 is full dithering)
        color_space: Color space for error calculations (rgb, lab, luma)
        serpentine: Alternate direction each row (for error diffusion)
        matrix_size: Size of ordered dither matrix (2, 4, 8)
        custom_pattern: Custom threshold pattern as 2D list of floats (0.0-1.0)
        levels: Number of output levels per channel (2 for 1-bit, 4 for 2-bit, etc.)
        spread: Spread factor for threshold values (adjusts dither intensity)
        seed: Random seed for reproducible random dithering
    """
    mode: str = "none"
    strength: float = 1.0
    color_space: str = "rgb"
    serpentine: bool = True
    matrix_size: int = 4
    custom_pattern: Optional[List[List[float]]] = None
    levels: int = 2
    spread: float = 1.0
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "strength": self.strength,
            "color_space": self.color_space,
            "serpentine": self.serpentine,
            "matrix_size": self.matrix_size,
            "custom_pattern": self.custom_pattern,
            "levels": self.levels,
            "spread": self.spread,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DitherConfig:
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "none"),
            strength=data.get("strength", 1.0),
            color_space=data.get("color_space", "rgb"),
            serpentine=data.get("serpentine", True),
            matrix_size=data.get("matrix_size", 4),
            custom_pattern=data.get("custom_pattern"),
            levels=data.get("levels", 2),
            spread=data.get("spread", 1.0),
            seed=data.get("seed"),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        valid_modes = [
            "none", "ordered_2x2", "ordered_4x4", "ordered_8x8",
            "bayer_2x2", "bayer_4x4", "bayer_8x8",
            "error_diffusion", "floyd_steinberg", "atkinson",
            "sierra", "sierra_lite", "jarvis_judice_ninke",
            "checkerboard", "halftone", "random", "custom"
        ]
        if self.mode not in valid_modes:
            errors.append(f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}")

        if self.strength < 0 or self.strength > 1:
            errors.append(f"strength must be 0.0-1.0, got {self.strength}")

        valid_color_spaces = ["rgb", "lab", "luma"]
        if self.color_space not in valid_color_spaces:
            errors.append(f"Invalid color_space '{self.color_space}'. Must be one of: {valid_color_spaces}")

        if self.matrix_size not in [2, 4, 8, 16]:
            errors.append(f"matrix_size must be 2, 4, 8, or 16, got {self.matrix_size}")

        if self.levels < 2:
            errors.append(f"levels must be >= 2, got {self.levels}")

        if self.spread <= 0:
            errors.append(f"spread must be > 0, got {self.spread}")

        if self.mode == "custom" and self.custom_pattern is None:
            errors.append("custom_pattern is required when mode is 'custom'")

        if self.custom_pattern is not None:
            pattern_errors = self._validate_custom_pattern()
            errors.extend(pattern_errors)

        return errors

    def _validate_custom_pattern(self) -> List[str]:
        """Validate custom pattern structure."""
        errors = []

        if not self.custom_pattern:
            return errors

        # Check it's a 2D list
        if not isinstance(self.custom_pattern, list):
            errors.append("custom_pattern must be a 2D list")
            return errors

        if not self.custom_pattern:
            errors.append("custom_pattern cannot be empty")
            return errors

        # Check all rows have same length
        first_len = len(self.custom_pattern[0])
        for i, row in enumerate(self.custom_pattern):
            if not isinstance(row, list):
                errors.append(f"custom_pattern row {i} must be a list")
                return errors
            if len(row) != first_len:
                errors.append(f"custom_pattern rows must have equal length, row 0 has {first_len}, row {i} has {len(row)}")
                return errors

            # Check values are in range
            for j, val in enumerate(row):
                if not isinstance(val, (int, float)):
                    errors.append(f"custom_pattern[{i}][{j}] must be a number, got {type(val).__name__}")
                elif val < 0 or val > 1:
                    errors.append(f"custom_pattern[{i}][{j}] must be 0.0-1.0, got {val}")

        return errors


@dataclass
class DitherMatrix:
    """
    Dither threshold matrix.

    Represents a threshold matrix for ordered dithering operations.
    Can be generated algorithmically (Bayer matrices) or loaded from
    custom patterns.

    Attributes:
        size: Matrix dimension (NxN matrix)
        matrix: 2D list of threshold values (normalized 0.0-1.0)
        name: Optional name for the matrix
        description: Optional description
    """
    size: int
    matrix: List[List[float]]
    name: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "size": self.size,
            "matrix": self.matrix,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DitherMatrix:
        """Create from dictionary."""
        return cls(
            size=data.get("size", len(data.get("matrix", [[0]]))),
            matrix=data.get("matrix", [[0]]),
            name=data.get("name", ""),
            description=data.get("description", ""),
        )

    @classmethod
    def bayer(cls, size: int) -> DitherMatrix:
        """
        Generate Bayer matrix of specified size.

        Uses recursive definition for power-of-2 sizes (2, 4, 8, 16, etc.).

        Args:
            size: Matrix size (must be power of 2)

        Returns:
            DitherMatrix with Bayer threshold values
        """
        if not cls._is_power_of_two(size):
            raise ValueError(f"Bayer matrix size must be power of 2, got {size}")

        # Generate raw Bayer matrix (0 to size^2 - 1)
        raw_matrix = cls._generate_bayer_raw(size)

        # Normalize to 0.0-1.0 range
        max_val = size * size - 1
        normalized = [[val / max_val for val in row] for row in raw_matrix]

        return cls(
            size=size,
            matrix=normalized,
            name=f"bayer_{size}x{size}",
            description=f"Bayer {size}x{size} ordered dither matrix",
        )

    @classmethod
    def checkerboard(cls) -> DitherMatrix:
        """
        Generate simple checkerboard dither matrix.

        Returns:
            DitherMatrix with checkerboard pattern (0.0 and 1.0 alternating)
        """
        return cls(
            size=2,
            matrix=[[0.0, 1.0], [1.0, 0.0]],
            name="checkerboard",
            description="Simple 2x2 checkerboard dither pattern",
        )

    @classmethod
    def diagonal_lines(cls, spacing: int = 2) -> DitherMatrix:
        """
        Generate diagonal line pattern matrix.

        Args:
            spacing: Line spacing in pixels

        Returns:
            DitherMatrix with diagonal line threshold pattern
        """
        size = spacing * 2
        matrix = [[0.0 for _ in range(size)] for _ in range(size)]

        for y in range(size):
            for x in range(size):
                # Diagonal pattern based on x+y
                if (x + y) % spacing == 0:
                    matrix[y][x] = 0.0
                else:
                    matrix[y][x] = 1.0

        return cls(
            size=size,
            matrix=matrix,
            name=f"diagonal_lines_{spacing}",
            description=f"Diagonal lines with {spacing}px spacing",
        )

    @classmethod
    def halftone(cls, dot_size: int = 2) -> DitherMatrix:
        """
        Generate halftone dot pattern matrix.

        Args:
            dot_size: Size of each dot in pixels

        Returns:
            DitherMatrix with halftone dot threshold pattern
        """
        size = dot_size * 4  # Allow for dot spacing
        matrix = [[0.5 for _ in range(size)] for _ in range(size)]

        center = size // 2
        radius = dot_size

        for y in range(size):
            for x in range(size):
                # Distance from center
                dist = math.sqrt((x - center) ** 2 + (y - center) ** 2)
                # Create radial gradient for dot effect
                matrix[y][x] = min(1.0, max(0.0, dist / (radius * 2)))

        return cls(
            size=size,
            matrix=matrix,
            name=f"halftone_{dot_size}",
            description=f"Halftone dot pattern with {dot_size}px dots",
        )

    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Check if number is power of 2."""
        return n > 0 and (n & (n - 1)) == 0

    @staticmethod
    def _generate_bayer_raw(size: int) -> List[List[int]]:
        """
        Generate raw Bayer matrix with integer values.

        Uses recursive formula:
        B(2n) = | 4*B(n)      4*B(n) + 2 |
        | 4*B(n) + 3  4*B(n) + 1 |

        Args:
            size: Matrix size (must be power of 2)

        Returns:
            2D list of integers from 0 to size^2 - 1
        """
        if size == 2:
            return [[0, 2], [3, 1]]

        # Recursively generate smaller matrix
        half = size // 2
        smaller = DitherMatrix._generate_bayer_raw(half)

        # Build larger matrix
        result = [[0 for _ in range(size)] for _ in range(size)]

        for y in range(half):
            for x in range(half):
                val = smaller[y][x]
                result[y][x] = 4 * val
                result[y][x + half] = 4 * val + 2
                result[y + half][x] = 4 * val + 3
                result[y + half][x + half] = 4 * val + 1

        return result

    @classmethod
    def from_image(cls, path: str) -> DitherMatrix:
        """
        Load custom matrix from image file.

        The image is converted to grayscale and normalized to 0.0-1.0
        threshold values. Image size determines matrix size.

        Args:
            path: Path to image file

        Returns:
            DitherMatrix with values from image
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("PIL/Pillow is required to load images")

        img = Image.open(path)

        # Convert to grayscale
        if img.mode != "L":
            img = img.convert("L")

        width, height = img.size

        # Use smaller dimension for square matrix
        size = min(width, height)

        # Crop to square from center
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))

        # Get pixel values and normalize
        pixels = img.load()
        matrix = []
        for y in range(size):
            row = []
            for x in range(size):
                # Normalize 0-255 to 0.0-1.0
                row.append(pixels[x, y] / 255.0)
            matrix.append(row)

        import os
        name = os.path.splitext(os.path.basename(path))[0]

        return cls(
            size=size,
            matrix=matrix,
            name=name,
            description=f"Custom pattern loaded from {path}",
        )

    def get_threshold(self, x: int, y: int) -> float:
        """
        Get threshold value at position (with wrapping).

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Threshold value (0.0-1.0)
        """
        x_mod = x % self.size
        y_mod = y % self.size
        return self.matrix[y_mod][x_mod]


# =============================================================================
# Pre-defined dither matrices
# =============================================================================

# Standard Bayer matrices
BAYER_2X2 = DitherMatrix.bayer(2)
BAYER_4X4 = DitherMatrix.bayer(4)
BAYER_8X8 = DitherMatrix.bayer(8)

# Special pattern matrices
CHECKERBOARD = DitherMatrix.checkerboard()

# Dictionary of all built-in matrices
BUILTIN_MATRICES: Dict[str, DitherMatrix] = {
    "bayer_2x2": BAYER_2X2,
    "bayer_4x4": BAYER_4X4,
    "bayer_8x8": BAYER_8X8,
    "checkerboard": CHECKERBOARD,
}


def get_matrix(name: str) -> Optional[DitherMatrix]:
    """
    Get a built-in matrix by name.

    Args:
        name: Matrix name (case-insensitive)

    Returns:
        DitherMatrix or None if not found
    """
    return BUILTIN_MATRICES.get(name.lower())


def list_matrices() -> List[str]:
    """
    List all built-in matrix names.

    Returns:
        List of matrix names
    """
    return list(BUILTIN_MATRICES.keys())
