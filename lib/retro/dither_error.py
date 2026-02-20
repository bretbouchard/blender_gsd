"""
Error Diffusion Dithering Module

Implements error diffusion dithering algorithms that distribute
quantization error to neighboring pixels. This creates smooth
gradients when reducing colors.

Popular algorithms include:
- Floyd-Steinberg (most common)
- Atkinson (Macintosh style, preserves detail)
- Sierra (balanced quality/speed)
- Jarvis-Judice-Ninke (high quality, slower)
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


# =============================================================================
# Error Diffusion Kernels
# =============================================================================

# Floyd-Steinberg kernel (classic error diffusion)
# Distributes error to 4 neighboring pixels
FLOYD_STEINBERG: Dict[str, Any] = {
    "name": "Floyd-Steinberg",
    "description": "Classic error diffusion algorithm, good balance of quality and speed",
    "kernel": [
        (1, 0, 7 / 16),
        (-1, 1, 3 / 16),
        (0, 1, 5 / 16),
        (1, 1, 1 / 16)
    ],
    "divisor": 16,
}

# Atkinson dithering (Macintosh style)
# Only distributes 75% of error, creating more contrast
ATKINSON: Dict[str, Any] = {
    "name": "Atkinson",
    "description": "Bill Atkinson's algorithm for Macintosh, high contrast, detail-preserving",
    "kernel": [
        (1, 0, 1 / 8),
        (2, 0, 1 / 8),
        (-1, 1, 1 / 8),
        (0, 1, 1 / 8),
        (1, 1, 1 / 8),
        (0, 2, 1 / 8)
    ],
    "divisor": 8,
}

# Sierra Lite (simplified Sierra)
# Faster than Sierra-3, good quality
SIERRA_LITE: Dict[str, Any] = {
    "name": "Sierra Lite",
    "description": "Simplified Sierra algorithm, fast with good quality",
    "kernel": [
        (1, 0, 2 / 4),
        (-1, 1, 1 / 4),
        (0, 1, 1 / 4)
    ],
    "divisor": 4,
}

# Sierra-3 (also known as Filter Lite)
# Better quality than Sierra Lite
SIERRA_3: Dict[str, Any] = {
    "name": "Sierra-3",
    "description": "Three-line filter, better quality than Sierra Lite",
    "kernel": [
        (1, 0, 5 / 32),
        (2, 0, 3 / 32),
        (-2, 1, 2 / 32),
        (-1, 1, 4 / 32),
        (0, 1, 5 / 32),
        (1, 1, 4 / 32),
        (2, 1, 2 / 32),
        (-1, 2, 2 / 32),
        (0, 2, 3 / 32),
        (1, 2, 2 / 32)
    ],
    "divisor": 32,
}

# Jarvis-Judice-Ninke (JJN)
# Distributes error to 12 neighbors, very smooth but slow
JARVIS_JUDICE_NINKE: Dict[str, Any] = {
    "name": "Jarvis-Judice-Ninke",
    "description": "Distributes error to 12 neighbors, very smooth gradients",
    "kernel": [
        (1, 0, 7 / 48), (2, 0, 5 / 48),
        (-2, 1, 3 / 48), (-1, 1, 5 / 48), (0, 1, 7 / 48), (1, 1, 5 / 48), (2, 1, 3 / 48),
        (-2, 2, 1 / 48), (-1, 2, 3 / 48), (0, 2, 5 / 48), (1, 2, 3 / 48), (2, 2, 1 / 48)
    ],
    "divisor": 48,
}

# Stucki (similar to JJN but more error diffusion)
STUCKI: Dict[str, Any] = {
    "name": "Stucki",
    "description": "Extended JJN with more error distribution",
    "kernel": [
        (1, 0, 8 / 42), (2, 0, 4 / 42),
        (-2, 1, 2 / 42), (-1, 1, 4 / 42), (0, 1, 8 / 42), (1, 1, 4 / 42), (2, 1, 2 / 42),
        (-2, 2, 1 / 42), (-1, 2, 2 / 42), (0, 2, 4 / 42), (1, 2, 2 / 42), (2, 2, 1 / 42)
    ],
    "divisor": 42,
}

# Burkes (compromise between speed and quality)
BURKES: Dict[str, Any] = {
    "name": "Burkes",
    "description": "Compromise between Floyd-Steinberg and JJN",
    "kernel": [
        (1, 0, 8 / 32), (2, 0, 4 / 32),
        (-2, 1, 2 / 32), (-1, 1, 4 / 32), (0, 1, 8 / 32), (1, 1, 4 / 32), (2, 1, 2 / 32)
    ],
    "divisor": 32,
}

# Dictionary of all kernels
ERROR_DIFFUSION_KERNELS: Dict[str, Dict[str, Any]] = {
    "floyd_steinberg": FLOYD_STEINBERG,
    "atkinson": ATKINSON,
    "sierra_lite": SIERRA_LITE,
    "sierra_3": SIERRA_3,
    "sierra": SIERRA_3,  # Alias
    "jarvis_judice_ninke": JARVIS_JUDICE_NINKE,
    "jjn": JARVIS_JUDICE_NINKE,  # Alias
    "stucki": STUCKI,
    "burkes": BURKES,
}


# =============================================================================
# Color Distance Functions
# =============================================================================

def rgb_distance(c1: Tuple[float, ...], c2: Tuple[float, ...]) -> float:
    """
    Calculate Euclidean distance in RGB space.

    Args:
        c1: First color (R, G, B)
        c2: Second color (R, G, B)

    Returns:
        Distance value
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))


def lab_distance(c1: Tuple[float, ...], c2: Tuple[float, ...]) -> float:
    """
    Calculate distance in CIE Lab color space.

    More perceptually uniform than RGB distance.

    Args:
        c1: First color (R, G, B) - will be converted to Lab
        c2: Second color (R, G, B) - will be converted to Lab

    Returns:
        Distance value
    """
    # Convert RGB to Lab (simplified approximation)
    lab1 = _rgb_to_lab(c1[:3])
    lab2 = _rgb_to_lab(c2[:3])

    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def _rgb_to_lab(rgb: Tuple[float, ...]) -> Tuple[float, float, float]:
    """
    Convert RGB to CIE Lab color space.

    Simplified conversion assuming sRGB color space.
    """
    # Normalize to 0-1
    r = rgb[0] / 255.0
    g = rgb[1] / 255.0
    b = rgb[2] / 255.0

    # Apply gamma correction (sRGB to linear)
    r = _gamma_expand(r)
    g = _gamma_expand(g)
    b = _gamma_expand(b)

    # Convert to XYZ (sRGB D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    # Convert XYZ to Lab
    # Reference white D65
    x /= 0.95047
    y /= 1.0
    z /= 1.08883

    x = _lab_f(x)
    y = _lab_f(y)
    z = _lab_f(z)

    L = 116 * y - 16
    a = 500 * (x - y)
    b_val = 200 * (y - z)

    return (L, a, b_val)


def _gamma_expand(c: float) -> float:
    """sRGB gamma expansion."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _lab_f(t: float) -> float:
    """Lab conversion helper function."""
    delta = 6 / 29
    if t > delta:
        return t ** (1 / 3)
    return t / (3 * delta ** 2) + 4 / 29


def find_nearest_color(
    color: Tuple[float, ...],
    palette: List[Tuple[int, int, int]],
    color_space: str = "rgb"
) -> Tuple[int, int, int]:
    """
    Find nearest color in palette.

    Args:
        color: Source color (R, G, B)
        palette: List of palette colors
        color_space: Color space for distance calculation (rgb, lab, luma)

    Returns:
        Nearest palette color
    """
    if not palette:
        return (int(color[0]), int(color[1]), int(color[2]))

    min_dist = float('inf')
    nearest = palette[0]

    distance_func = rgb_distance if color_space == "rgb" else lab_distance

    for palette_color in palette:
        dist = distance_func(color, palette_color)
        if dist < min_dist:
            min_dist = dist
            nearest = palette_color

    return nearest


def quantize_to_level(value: float, levels: int) -> float:
    """
    Quantize a value to specified number of levels.

    Args:
        value: Input value (0-255)
        levels: Number of output levels

    Returns:
        Quantized value (0-255)
    """
    if levels <= 1:
        return 0

    step = 255.0 / (levels - 1)
    return round(value / step) * step


# =============================================================================
# Error Diffusion Implementation
# =============================================================================

def error_diffusion_dither(
    image: Any,
    kernel: Dict[str, Any],
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0
) -> Any:
    """
    Apply error diffusion dithering.

    Args:
        image: PIL Image (RGB or L mode)
        kernel: Error diffusion kernel dictionary
        palette: Target color palette (optional, uses levels quantization if None)
        levels: Number of output levels per channel (ignored if palette provided)
        serpentine: Alternate direction each row (reduces directional artifacts)
        color_space: Color space for distance calculation (rgb, lab, luma)
        strength: Error distribution strength (0.0-1.0)

    Returns:
        Dithered PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode == "L":
        image = image.convert("RGB")
    elif image.mode == "P":
        image = image.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    if HAS_NUMPY:
        return _error_diffusion_numpy(image, kernel, palette, levels, serpentine, color_space, strength)
    else:
        return _error_diffusion_slow(image, kernel, palette, levels, serpentine, color_space, strength)


def _error_diffusion_numpy(
    image: Any,
    kernel: Dict[str, Any],
    palette: Optional[List[Tuple[int, int, int]]],
    levels: int,
    serpentine: bool,
    color_space: str,
    strength: float
) -> Any:
    """
    NumPy-optimized error diffusion dithering.
    """
    img_array = np.array(image, dtype=np.float64)
    height, width = img_array.shape[:2]
    kernel_def = kernel["kernel"]

    # Process each row
    for y in range(height):
        # Determine direction
        x_range = range(width) if (not serpentine or y % 2 == 0) else range(width - 1, -1, -1)

        for x in x_range:
            old_pixel = img_array[y, x].copy()

            # Find new pixel value
            if palette:
                new_pixel = np.array(find_nearest_color(tuple(old_pixel), palette, color_space), dtype=np.float64)
            else:
                new_pixel = np.array([
                    quantize_to_level(old_pixel[0], levels),
                    quantize_to_level(old_pixel[1], levels),
                    quantize_to_level(old_pixel[2], levels)
                ])

            # Update pixel
            img_array[y, x] = new_pixel

            # Calculate error
            error = (old_pixel - new_pixel) * strength

            # Distribute error to neighbors
            for dx, dy, weight in kernel_def:
                # Adjust x offset for serpentine direction
                if serpentine and y % 2 == 1:
                    dx = -dx

                nx = x + dx
                ny = y + dy

                if 0 <= nx < width and 0 <= ny < height:
                    img_array[ny, nx] += error * weight

    # Clip and convert
    result = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(result)


def _error_diffusion_slow(
    image: Any,
    kernel: Dict[str, Any],
    palette: Optional[List[Tuple[int, int, int]]],
    levels: int,
    serpentine: bool,
    color_space: str,
    strength: float
) -> Any:
    """
    Pure Python error diffusion dithering (slower but no numpy dependency).
    """
    width, height = image.size
    pixels = image.load()

    # Create working array as list of lists for error accumulation
    # Use floats for error accumulation
    work_array = [[list(pixels[x, y][:3]) for x in range(width)] for y in range(height)]

    kernel_def = kernel["kernel"]

    for y in range(height):
        x_range = range(width) if (not serpentine or y % 2 == 0) else range(width - 1, -1, -1)

        for x in x_range:
            old_pixel = work_array[y][x]

            # Find new pixel value
            if palette:
                new_pixel = list(find_nearest_color(tuple(old_pixel), palette, color_space))
            else:
                new_pixel = [
                    quantize_to_level(old_pixel[0], levels),
                    quantize_to_level(old_pixel[1], levels),
                    quantize_to_level(old_pixel[2], levels)
                ]

            # Update working array
            work_array[y][x] = new_pixel

            # Calculate error
            error = [(old_pixel[i] - new_pixel[i]) * strength for i in range(3)]

            # Distribute error to neighbors
            for dx, dy, weight in kernel_def:
                if serpentine and y % 2 == 1:
                    dx = -dx

                nx = x + dx
                ny = y + dy

                if 0 <= nx < width and 0 <= ny < height:
                    for i in range(3):
                        work_array[ny][nx][i] += error[i] * weight

    # Create result image
    result = Image.new("RGB", (width, height))
    result_pixels = result.load()

    for y in range(height):
        for x in range(width):
            pixel = work_array[y][x]
            result_pixels[x, y] = (
                int(max(0, min(255, pixel[0]))),
                int(max(0, min(255, pixel[1]))),
                int(max(0, min(255, pixel[2])))
            )

    return result


# =============================================================================
# Convenience Functions
# =============================================================================

def floyd_steinberg_dither(
    image: Any,
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0
) -> Any:
    """
    Apply Floyd-Steinberg dithering.

    Classic error diffusion algorithm with good balance of quality and speed.

    Args:
        image: PIL Image
        palette: Target color palette (optional)
        levels: Number of output levels per channel
        serpentine: Alternate direction each row
        color_space: Color space for distance calculation
        strength: Error distribution strength

    Returns:
        Dithered PIL Image
    """
    return error_diffusion_dither(
        image, FLOYD_STEINBERG, palette, levels, serpentine, color_space, strength
    )


def atkinson_dither(
    image: Any,
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0
) -> Any:
    """
    Apply Atkinson dithering (Macintosh style).

    Preserves detail and creates high contrast. Only distributes 75% of error,
    which creates more defined edges.

    Args:
        image: PIL Image
        palette: Target color palette (optional)
        levels: Number of output levels per channel
        serpentine: Alternate direction each row
        color_space: Color space for distance calculation
        strength: Error distribution strength

    Returns:
        Dithered PIL Image
    """
    return error_diffusion_dither(
        image, ATKINSON, palette, levels, serpentine, color_space, strength
    )


def sierra_dither(
    image: Any,
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0,
    variant: str = "lite"
) -> Any:
    """
    Apply Sierra dithering.

    Args:
        image: PIL Image
        palette: Target color palette (optional)
        levels: Number of output levels per channel
        serpentine: Alternate direction each row
        color_space: Color space for distance calculation
        strength: Error distribution strength
        variant: Sierra variant ("lite" or "3")

    Returns:
        Dithered PIL Image
    """
    kernel = SIERRA_LITE if variant == "lite" else SIERRA_3
    return error_diffusion_dither(
        image, kernel, palette, levels, serpentine, color_space, strength
    )


def jarvis_judice_ninke_dither(
    image: Any,
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0
) -> Any:
    """
    Apply Jarvis-Judice-Ninke dithering.

    Distributes error to 12 neighbors, creating very smooth gradients.
    Slower than Floyd-Steinberg but higher quality.

    Args:
        image: PIL Image
        palette: Target color palette (optional)
        levels: Number of output levels per channel
        serpentine: Alternate direction each row
        color_space: Color space for distance calculation
        strength: Error distribution strength

    Returns:
        Dithered PIL Image
    """
    return error_diffusion_dither(
        image, JARVIS_JUDICE_NINKE, palette, levels, serpentine, color_space, strength
    )


def stucki_dither(
    image: Any,
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0
) -> Any:
    """
    Apply Stucki dithering.

    Extended JJN with more error distribution. Creates very smooth results.

    Args:
        image: PIL Image
        palette: Target color palette (optional)
        levels: Number of output levels per channel
        serpentine: Alternate direction each row
        color_space: Color space for distance calculation
        strength: Error distribution strength

    Returns:
        Dithered PIL Image
    """
    return error_diffusion_dither(
        image, STUCKI, palette, levels, serpentine, color_space, strength
    )


def burkes_dither(
    image: Any,
    palette: Optional[List[Tuple[int, int, int]]] = None,
    levels: int = 2,
    serpentine: bool = True,
    color_space: str = "rgb",
    strength: float = 1.0
) -> Any:
    """
    Apply Burkes dithering.

    Compromise between Floyd-Steinberg speed and JJN quality.

    Args:
        image: PIL Image
        palette: Target color palette (optional)
        levels: Number of output levels per channel
        serpentine: Alternate direction each row
        color_space: Color space for distance calculation
        strength: Error distribution strength

    Returns:
        Dithered PIL Image
    """
    return error_diffusion_dither(
        image, BURKES, palette, levels, serpentine, color_space, strength
    )


def get_kernel_names() -> List[str]:
    """
    Get list of available error diffusion kernel names.

    Returns:
        List of kernel names
    """
    return list(ERROR_DIFFUSION_KERNELS.keys())


def get_kernel(name: str) -> Optional[Dict[str, Any]]:
    """
    Get error diffusion kernel by name.

    Args:
        name: Kernel name (case-insensitive)

    Returns:
        Kernel dictionary or None if not found
    """
    return ERROR_DIFFUSION_KERNELS.get(name.lower())
