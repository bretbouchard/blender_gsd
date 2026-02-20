"""
Pattern Dithering Module

Implements pattern-based dithering using predefined and custom patterns.
Pattern dithering applies a repeating texture to simulate gradients.

Patterns include:
- Diagonal lines
- Horizontal/vertical lines
- Crosshatch
- Dots
- Custom patterns loaded from images
"""

from __future__ import annotations
from typing import Tuple, List, Optional, Any, Dict
import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from lib.retro.dither_types import DitherMatrix
from lib.retro.dither_ordered import ordered_dither


# =============================================================================
# Pre-defined Pattern Matrices
# =============================================================================

# Diagonal lines pattern (45 degrees)
DIAGONAL_LINES: List[List[float]] = [
    [0.0, 1.0],
    [1.0, 0.0]
]

# Horizontal lines
HORIZONTAL_LINES: List[List[float]] = [
    [0.0],
    [1.0]
]

# Vertical lines
VERTICAL_LINES: List[List[float]] = [
    [0.0, 1.0]
]

# Crosshatch pattern
CROSSHATCH: List[List[float]] = [
    [0.0, 1.0, 0.0],
    [1.0, 1.0, 1.0],
    [0.0, 1.0, 0.0]
]

# Diamond pattern
DIAMOND: List[List[float]] = [
    [0.5, 0.0, 0.5],
    [0.0, 1.0, 0.0],
    [0.5, 0.0, 0.5]
]

# Dots pattern (2x2)
DOTS_2X2: List[List[float]] = [
    [0.0, 0.5],
    [0.5, 1.0]
]

# Dots pattern (3x3)
DOTS_3X3: List[List[float]] = [
    [0.5, 0.0, 0.5],
    [0.0, 0.0, 0.0],
    [0.5, 0.0, 0.5]
]

# Circles pattern (4x4)
CIRCLES_4X4: List[List[float]] = [
    [0.5, 0.25, 0.25, 0.5],
    [0.25, 0.0, 0.0, 0.25],
    [0.25, 0.0, 0.0, 0.25],
    [0.5, 0.25, 0.25, 0.5]
]

# Herringbone pattern
HERRINGBONE: List[List[float]] = [
    [0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0]
]

# Brick pattern
BRICK: List[List[float]] = [
    [0.0, 0.5, 0.0, 0.5],
    [0.5, 0.0, 0.5, 0.0]
]

# Weave pattern
WEAVE: List[List[float]] = [
    [0.0, 0.5, 0.0],
    [0.5, 1.0, 0.5],
    [0.0, 0.5, 0.0],
    [0.5, 1.0, 0.5]
]

# Dictionary of built-in patterns
PATTERNS: Dict[str, List[List[float]]] = {
    "diagonal_lines": DIAGONAL_LINES,
    "horizontal_lines": HORIZONTAL_LINES,
    "vertical_lines": VERTICAL_LINES,
    "crosshatch": CROSSHATCH,
    "diamond": DIAMOND,
    "dots_2x2": DOTS_2X2,
    "dots_3x3": DOTS_3X3,
    "circles_4x4": CIRCLES_4X4,
    "herringbone": HERRINGBONE,
    "brick": BRICK,
    "weave": WEAVE,
}


# =============================================================================
# Pattern Generation Functions
# =============================================================================

def generate_diagonal_pattern(spacing: int = 2, angle: int = 45) -> List[List[float]]:
    """
    Generate diagonal line pattern with specified spacing.

    Args:
        spacing: Line spacing in pixels
        angle: Line angle in degrees (0, 45, 90, or 135)

    Returns:
        2D threshold pattern
    """
    size = spacing * 2
    matrix = [[1.0 for _ in range(size)] for _ in range(size)]

    if angle == 0:
        # Horizontal lines
        for y in range(size):
            if y % spacing == 0:
                for x in range(size):
                    matrix[y][x] = 0.0
    elif angle == 90:
        # Vertical lines
        for x in range(size):
            if x % spacing == 0:
                for y in range(size):
                    matrix[y][x] = 0.0
    elif angle == 45:
        # Diagonal (top-left to bottom-right)
        for y in range(size):
            for x in range(size):
                if (x + y) % spacing == 0:
                    matrix[y][x] = 0.0
    elif angle == 135:
        # Anti-diagonal (top-right to bottom-left)
        for y in range(size):
            for x in range(size):
                if (x - y) % spacing == 0:
                    matrix[y][x] = 0.0

    return matrix


def generate_dot_pattern(dot_size: int = 2, spacing: int = 2) -> List[List[float]]:
    """
    Generate dot pattern with specified size and spacing.

    Args:
        dot_size: Size of each dot
        spacing: Space between dots

    Returns:
        2D threshold pattern
    """
    size = dot_size + spacing
    matrix = [[1.0 for _ in range(size)] for _ in range(size)]

    # Create dot in center
    half_dot = dot_size // 2
    center = size // 2

    for y in range(size):
        for x in range(size):
            dist = math.sqrt((x - center) ** 2 + (y - center) ** 2)
            if dist <= half_dot:
                # Gradient from center
                matrix[y][x] = dist / (half_dot + 1)

    return matrix


def generate_circle_pattern(radius: int = 2) -> List[List[float]]:
    """
    Generate circular pattern.

    Args:
        radius: Circle radius

    Returns:
        2D threshold pattern with circular gradient
    """
    size = radius * 2 + 2
    matrix = [[1.0 for _ in range(size)] for _ in range(size)]
    center = size // 2

    for y in range(size):
        for x in range(size):
            dist = math.sqrt((x - center) ** 2 + (y - center) ** 2)
            matrix[y][x] = min(1.0, dist / (radius + 1))

    return matrix


def generate_crosshatch_pattern(line_width: int = 1, spacing: int = 2) -> List[List[float]]:
    """
    Generate crosshatch pattern.

    Args:
        line_width: Width of lines
        spacing: Space between lines

    Returns:
        2D threshold pattern
    """
    size = spacing + line_width
    matrix = [[1.0 for _ in range(size)] for _ in range(size)]

    # Create both diagonal directions
    for y in range(size):
        for x in range(size):
            # Check if on diagonal line
            if (x + y) % size < line_width or (x - y + size) % size < line_width:
                matrix[y][x] = 0.0

    return matrix


def tile_pattern(
    pattern: List[List[float]],
    width: int,
    height: int
) -> List[List[float]]:
    """
    Tile pattern to image size.

    Args:
        pattern: 2D threshold pattern
        width: Target width
        height: Target height

    Returns:
        Pattern tiled to target dimensions
    """
    if not pattern or not pattern[0]:
        return [[0.5 for _ in range(width)] for _ in range(height)]

    pattern_height = len(pattern)
    pattern_width = len(pattern[0])

    result = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(pattern[y % pattern_height][x % pattern_width])
        result.append(row)

    return result


# =============================================================================
# Pattern Dithering Functions
# =============================================================================

def pattern_dither(
    image: Any,
    pattern: str = "diagonal_lines",
    threshold: float = 0.5,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply pattern-based dithering.

    Uses a predefined pattern name to create the dither effect.

    Args:
        image: PIL Image
        pattern: Pattern name (diagonal_lines, horizontal_lines, vertical_lines, crosshatch, etc.)
        threshold: Threshold for binary patterns (0.0-1.0)
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    if pattern not in PATTERNS:
        raise ValueError(f"Unknown pattern '{pattern}'. Available: {list(PATTERNS.keys())}")

    pattern_matrix = PATTERNS[pattern]

    # Create DitherMatrix
    size = len(pattern_matrix)
    matrix = DitherMatrix(
        size=size,
        matrix=pattern_matrix,
        name=pattern,
        description=f"Built-in {pattern} pattern"
    )

    return ordered_dither(image, matrix, levels, strength)


def custom_pattern_dither(
    image: Any,
    pattern_image: Any,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply custom pattern dithering using an image as the pattern.

    The pattern image is converted to grayscale and used as the
    threshold matrix.

    Args:
        image: PIL Image to dither
        pattern_image: PIL Image or path to use as pattern
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    # Load pattern from image
    if isinstance(pattern_image, str):
        matrix = DitherMatrix.from_image(pattern_image)
    elif HAS_PIL and isinstance(pattern_image, Image.Image):
        # Save to temp file and load
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            pattern_image.save(f.name)
            temp_path = f.name
        try:
            matrix = DitherMatrix.from_image(temp_path)
        finally:
            os.unlink(temp_path)
    else:
        raise ValueError("pattern_image must be PIL Image or file path")

    return ordered_dither(image, matrix, levels, strength)


def custom_matrix_dither(
    image: Any,
    pattern_matrix: List[List[float]],
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply custom pattern dithering using a matrix.

    Args:
        image: PIL Image to dither
        pattern_matrix: 2D list of threshold values (0.0-1.0)
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    if not pattern_matrix or not pattern_matrix[0]:
        raise ValueError("pattern_matrix cannot be empty")

    size = len(pattern_matrix)
    matrix = DitherMatrix(
        size=size,
        matrix=pattern_matrix,
        name="custom",
        description="Custom pattern matrix"
    )

    return ordered_dither(image, matrix, levels, strength)


# =============================================================================
# Special Pattern Effects
# =============================================================================

def stipple_dither(
    image: Any,
    density: float = 1.0,
    seed: Optional[int] = None
) -> Any:
    """
    Apply stipple (random dot) dithering.

    Creates a pointillist effect with randomly placed dots.

    Args:
        image: PIL Image
        density: Dot density multiplier (0.1-2.0)
        seed: Random seed for reproducibility

    Returns:
        Dithered PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to grayscale
    if image.mode != "L":
        gray = image.convert("L")
    else:
        gray = image

    width, height = gray.size

    if HAS_NUMPY:
        return _stipple_numpy(gray, density, seed)
    else:
        return _stipple_slow(gray, density, seed)


def _stipple_numpy(image: Any, density: float, seed: Optional[int]) -> Any:
    """NumPy-optimized stipple dithering."""
    if seed is not None:
        np.random.seed(seed)

    width, height = image.size
    img_array = np.array(image, dtype=np.float32) / 255.0

    # Generate random thresholds
    thresholds = np.random.rand(height, width)

    # Adjust density
    adjusted_thresholds = 1.0 - (thresholds * density)

    # Compare luminance to random threshold
    result = (img_array > adjusted_thresholds).astype(np.uint8) * 255

    return Image.fromarray(result, mode="L")


def _stipple_slow(image: Any, density: float, seed: Optional[int]) -> Any:
    """Pure Python stipple dithering."""
    import random
    if seed is not None:
        random.seed(seed)

    width, height = image.size
    pixels = image.load()

    result = Image.new("L", (width, height), 255)
    result_pixels = result.load()

    for y in range(height):
        for x in range(width):
            luminance = pixels[x, y] / 255.0
            threshold = random.random()
            adjusted_threshold = 1.0 - (threshold * density)

            if luminance > adjusted_threshold:
                result_pixels[x, y] = 0
            else:
                result_pixels[x, y] = 255

    return result


def newsprint_dither(
    image: Any,
    dot_size: int = 2,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply newsprint-style halftone dithering.

    Simulates the look of newspaper printing with CMYK-style dots.

    Args:
        image: PIL Image
        dot_size: Size of halftone dots
        levels: Number of output levels
        strength: Dithering strength

    Returns:
        Dithered PIL Image with newsprint effect
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Generate halftone pattern
    matrix = DitherMatrix.halftone(dot_size)

    return ordered_dither(image, matrix, levels, strength)


def woodcut_dither(
    image: Any,
    line_spacing: int = 3,
    threshold: float = 0.5,
    strength: float = 1.0
) -> Any:
    """
    Apply woodcut-style line dithering.

    Creates an effect similar to woodcut printing with varying line widths.

    Args:
        image: PIL Image
        line_spacing: Spacing between lines
        threshold: Threshold for line width adjustment
        strength: Dithering strength

    Returns:
        Dithered PIL Image with woodcut effect
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to grayscale
    if image.mode != "L":
        gray = image.convert("L")
    else:
        gray = image

    width, height = gray.size
    pixels = gray.load()

    result = Image.new("L", (width, height), 255)
    result_pixels = result.load()

    for y in range(height):
        for x in range(width):
            luminance = pixels[x, y] / 255.0

            # Modulate based on line position
            line_mod = (y % line_spacing) / line_spacing

            # Adjust threshold based on luminance
            adjusted_threshold = threshold - (1 - luminance) * strength * 0.3

            if line_mod > adjusted_threshold:
                result_pixels[x, y] = 0
            else:
                result_pixels[x, y] = 255

    return result


# =============================================================================
# Utility Functions
# =============================================================================

def list_patterns() -> List[str]:
    """
    List available pattern names.

    Returns:
        List of pattern names
    """
    return list(PATTERNS.keys())


def get_pattern(name: str) -> Optional[List[List[float]]]:
    """
    Get pattern matrix by name.

    Args:
        name: Pattern name

    Returns:
        Pattern matrix or None if not found
    """
    return PATTERNS.get(name)


def create_pattern_matrix(
    pattern_type: str = "diagonal",
    **kwargs
) -> List[List[float]]:
    """
    Create a custom pattern matrix.

    Args:
        pattern_type: Type of pattern (diagonal, dot, circle, crosshatch)
        **kwargs: Pattern-specific parameters

    Returns:
        2D pattern matrix
    """
    if pattern_type == "diagonal":
        spacing = kwargs.get("spacing", 2)
        angle = kwargs.get("angle", 45)
        return generate_diagonal_pattern(spacing, angle)
    elif pattern_type == "dot":
        dot_size = kwargs.get("dot_size", 2)
        spacing = kwargs.get("spacing", 2)
        return generate_dot_pattern(dot_size, spacing)
    elif pattern_type == "circle":
        radius = kwargs.get("radius", 2)
        return generate_circle_pattern(radius)
    elif pattern_type == "crosshatch":
        line_width = kwargs.get("line_width", 1)
        spacing = kwargs.get("spacing", 2)
        return generate_crosshatch_pattern(line_width, spacing)
    else:
        raise ValueError(f"Unknown pattern type: {pattern_type}")
