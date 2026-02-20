"""
Ordered Dithering Module

Implements ordered dithering algorithms including Bayer matrices,
checkerboard patterns, and halftone effects.

Ordered dithering uses a threshold matrix that is tiled across the image.
Each pixel's value is compared against its corresponding threshold to
determine the output value.
"""

from __future__ import annotations
from typing import Tuple, List, Optional, Any, Union
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

from lib.retro.dither_types import DitherMatrix, DitherConfig


# =============================================================================
# Bayer Matrix Constants
# =============================================================================

# Pre-defined Bayer matrices (integer values, 0 to N^2-1)
BAYER_2X2_INT = [
    [0, 2],
    [3, 1]
]

BAYER_4X4_INT = [
    [ 0,  8,  2, 10],
    [12,  4, 14,  6],
    [ 3, 11,  1,  9],
    [15,  7, 13,  5]
]

BAYER_8X8_INT = [
    [ 0, 32,  8, 40,  2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44,  4, 36, 14, 46,  6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [ 3, 35, 11, 43,  1, 33,  9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47,  7, 39, 13, 45,  5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21]
]


# =============================================================================
# Matrix Generation Functions
# =============================================================================

def generate_bayer_matrix(size: int) -> List[List[int]]:
    """
    Generate Bayer matrix of any size (power of 2).

    Uses recursive definition to generate threshold values.

    Args:
        size: Matrix size (must be power of 2: 2, 4, 8, 16, etc.)

    Returns:
        2D list of integers from 0 to size^2 - 1

    Raises:
        ValueError: If size is not a power of 2
    """
    if size == 2:
        return [row[:] for row in BAYER_2X2_INT]

    if size == 4:
        return [row[:] for row in BAYER_4X4_INT]

    if size == 8:
        return [row[:] for row in BAYER_8X8_INT]

    # Check power of 2
    if size & (size - 1) != 0:
        raise ValueError(f"Bayer matrix size must be power of 2, got {size}")

    # Recursive generation
    return _generate_bayer_recursive(size)


def _generate_bayer_recursive(size: int) -> List[List[int]]:
    """
    Recursively generate Bayer matrix.

    Formula:
    B(2n) = | 4*B(n)      4*B(n) + 2 |
            | 4*B(n) + 3  4*B(n) + 1 |
    """
    if size == 2:
        return [row[:] for row in BAYER_2X2_INT]

    half = size // 2
    smaller = _generate_bayer_recursive(half)

    result = [[0 for _ in range(size)] for _ in range(size)]

    for y in range(half):
        for x in range(half):
            val = smaller[y][x]
            result[y][x] = 4 * val
            result[y][x + half] = 4 * val + 2
            result[y + half][x] = 4 * val + 3
            result[y + half][x + half] = 4 * val + 1

    return result


def normalize_matrix(matrix: List[List[int]]) -> List[List[float]]:
    """
    Normalize integer matrix to 0.0-1.0 range.

    Args:
        matrix: 2D list of integers

    Returns:
        2D list of floats normalized to 0.0-1.0
    """
    if not matrix or not matrix[0]:
        return [[0.0]]

    max_val = max(max(row) for row in matrix)
    if max_val == 0:
        return [[0.0 for _ in row] for row in matrix]

    return [[val / max_val for val in row] for row in matrix]


def get_bayer_threshold(x: int, y: int, size: int) -> float:
    """
    Get Bayer threshold value at position (with wrapping).

    Args:
        x: X coordinate
        y: Y coordinate
        size: Bayer matrix size

    Returns:
        Threshold value (0.0-1.0)
    """
    if size == 2:
        matrix = BAYER_2X2_INT
    elif size == 4:
        matrix = BAYER_4X4_INT
    elif size == 8:
        matrix = BAYER_8X8_INT
    else:
        matrix = generate_bayer_matrix(size)

    x_mod = x % size
    y_mod = y % size
    max_val = size * size - 1
    return matrix[y_mod][x_mod] / max_val


# =============================================================================
# Ordered Dithering Functions
# =============================================================================

def ordered_dither(
    image: Any,
    matrix: DitherMatrix,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply ordered dithering using a threshold matrix.

    Args:
        image: PIL Image (RGB or L mode)
        matrix: DitherMatrix with threshold values
        levels: Number of output levels per channel (2 for binary, etc.)
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if not HAS_NUMPY:
        return _ordered_dither_slow(image, matrix, levels, strength)

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode == "1":
        return image
    if image.mode == "P":
        image = image.convert("RGB")
    if image.mode == "L":
        image = image.convert("RGB")

    # Get image dimensions
    width, height = image.size
    img_array = np.array(image, dtype=np.float32)

    # Calculate quantization step
    step = 255.0 / (levels - 1) if levels > 1 else 255.0

    # Create threshold map
    threshold_map = _create_threshold_map(matrix, width, height)

    # Apply dithering
    if strength < 1.0:
        # Blend threshold with 0.5 for partial strength
        threshold_map = 0.5 + (threshold_map - 0.5) * strength

    # Scale threshold to match quantization range
    threshold_scaled = threshold_map * step

    # Add threshold, quantize, clip
    dithered = img_array + threshold_scaled - (step / 2)
    quantized = np.round(dithered / step) * step
    result = np.clip(quantized, 0, 255).astype(np.uint8)

    return Image.fromarray(result)


def _ordered_dither_slow(
    image: Any,
    matrix: DitherMatrix,
    levels: int,
    strength: float
) -> Any:
    """
    Slow ordered dithering without numpy.

    Falls back to pixel-by-pixel processing.
    """
    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    pixels = image.load()

    result = Image.new("RGB", (width, height))
    result_pixels = result.load()

    step = 255.0 / (levels - 1) if levels > 1 else 255.0

    for y in range(height):
        for x in range(width):
            # Get threshold from matrix
            threshold = matrix.get_threshold(x, y)

            # Apply strength
            if strength < 1.0:
                threshold = 0.5 + (threshold - 0.5) * strength

            pixel = pixels[x, y]

            # Process each channel
            new_pixel = []
            for channel in pixel[:3]:
                # Add threshold offset
                val = channel + (threshold - 0.5) * step
                # Quantize
                quantized = round(val / step) * step
                # Clip
                new_pixel.append(int(max(0, min(255, quantized))))

            result_pixels[x, y] = tuple(new_pixel)

    return result


def _create_threshold_map(
    matrix: DitherMatrix,
    width: int,
    height: int
) -> np.ndarray:
    """
    Create full-size threshold map by tiling matrix.

    Args:
        matrix: DitherMatrix to tile
        width: Output width
        height: Output height

    Returns:
        numpy array of shape (height, width, 1) with threshold values
    """
    # Get matrix as numpy array
    matrix_array = np.array(matrix.matrix, dtype=np.float32)

    # Calculate tiles needed
    tiles_y = (height + matrix.size - 1) // matrix.size
    tiles_x = (width + matrix.size - 1) // matrix.size

    # Tile the matrix
    tiled = np.tile(matrix_array, (tiles_y, tiles_x))

    # Crop to exact size
    threshold_map = tiled[:height, :width]

    # Add channel dimension for broadcasting
    return threshold_map[:, :, np.newaxis]


def bayer_dither(
    image: Any,
    size: int = 4,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply Bayer matrix dithering.

    Convenience function that generates Bayer matrix and applies dithering.

    Args:
        image: PIL Image
        size: Bayer matrix size (2, 4, or 8)
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    matrix = DitherMatrix.bayer(size)
    return ordered_dither(image, matrix, levels, strength)


def checkerboard_dither(
    image: Any,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply checkerboard pattern dithering.

    Simple 2x2 alternating pattern that creates a checkerboard effect.

    Args:
        image: PIL Image
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    matrix = DitherMatrix.checkerboard()
    return ordered_dither(image, matrix, levels, strength)


def halftone_dither(
    image: Any,
    dot_size: int = 2,
    angle: float = 45.0,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply halftone pattern dithering.

    Creates a halftone printing effect with dots arranged at the specified angle.

    Args:
        image: PIL Image
        dot_size: Size of each halftone dot in pixels
        angle: Rotation angle in degrees (default 45 degrees)
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to grayscale for halftone
    if image.mode != "L":
        gray_image = image.convert("L")
    else:
        gray_image = image

    # Generate halftone matrix
    matrix = DitherMatrix.halftone(dot_size)

    # Apply angle rotation if not 0
    if angle != 0:
        gray_image = _rotate_for_halftone(gray_image, angle)

    # Apply dithering
    result = ordered_dither(gray_image.convert("RGB"), matrix, levels, strength)

    # Rotate back if needed
    if angle != 0:
        result = _rotate_for_halftone(result, -angle)
        # Crop to original size
        result = _center_crop(result, image.size)

    return result


def _rotate_for_halftone(image: Any, angle: float) -> Any:
    """Rotate image for halftone angle."""
    from PIL import Image as PILImage

    # Expand canvas to avoid clipping
    width, height = image.size
    diagonal = int(math.sqrt(width**2 + height**2))
    expanded = PILImage.new(image.mode, (diagonal, diagonal), 255)

    # Paste centered
    paste_x = (diagonal - width) // 2
    paste_y = (diagonal - height) // 2
    expanded.paste(image, (paste_x, paste_y))

    # Rotate
    return expanded.rotate(-angle, expand=False, fillcolor=255)


def _center_crop(image: Any, target_size: Tuple[int, int]) -> Any:
    """Crop image to target size from center."""
    width, height = image.size
    target_width, target_height = target_size

    left = (width - target_width) // 2
    top = (height - target_height) // 2

    return image.crop((left, top, left + target_width, top + target_height))


# =============================================================================
# Additional Pattern Dithering
# =============================================================================

def diagonal_dither(
    image: Any,
    spacing: int = 2,
    levels: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Apply diagonal line pattern dithering.

    Args:
        image: PIL Image
        spacing: Line spacing in pixels
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    matrix = DitherMatrix.diagonal_lines(spacing)
    return ordered_dither(image, matrix, levels, strength)


def blue_noise_dither(
    image: Any,
    levels: int = 2,
    strength: float = 1.0,
    seed: Optional[int] = None
) -> Any:
    """
    Apply blue noise pattern dithering.

    Uses a simulated blue noise distribution for more natural-looking dithering.

    Note: This is a simplified approximation. True blue noise requires
    pre-computed noise textures.

    Args:
        image: PIL Image
        levels: Number of output levels per channel
        strength: Dithering strength (0.0-1.0)
        seed: Random seed for reproducibility

    Returns:
        Dithered PIL Image
    """
    if not HAS_NUMPY:
        raise ImportError("NumPy is required for blue noise dithering")

    if isinstance(image, str):
        image = Image.open(image)

    # Set random seed
    if seed is not None:
        np.random.seed(seed)

    width, height = image.size

    # Generate blue noise approximation using low-pass filtered white noise
    # This is a simplified approach - true blue noise is more complex
    noise = np.random.rand(height, width).astype(np.float32)

    # Apply simple low-pass filter to reduce high-frequency content
    # (approximates blue noise distribution)
    kernel_size = 3
    kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)

    # Simple convolution approximation
    from numpy.lib.stride_tricks import as_strided
    padded = np.pad(noise, kernel_size // 2, mode='wrap')

    # Create view for convolution
    shape = (height, width, kernel_size, kernel_size)
    strides = padded.strides + padded.strides
    windows = as_strided(padded, shape=shape, strides=strides)
    filtered = np.einsum('ijkl,kl->ij', windows, kernel)

    # Normalize to 0-1
    filtered = (filtered - filtered.min()) / (filtered.max() - filtered.min() + 1e-10)

    # Create DitherMatrix from filtered noise
    # Use a small tile size for efficiency
    tile_size = 64
    tile = filtered[:tile_size, :tile_size].tolist()

    matrix = DitherMatrix(
        size=tile_size,
        matrix=tile,
        name="blue_noise",
        description="Blue noise approximation pattern"
    )

    return ordered_dither(image, matrix, levels, strength)
