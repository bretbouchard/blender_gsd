"""
Main Dithering Module

Provides a unified interface for all dithering algorithms.
Supports ordered dithering (Bayer), error diffusion (Floyd-Steinberg, Atkinson),
pattern-based dithering, and custom patterns.

Example Usage:
    from lib.retro import dither, DitherConfig

    # Using preset
    config = DitherConfig(mode="atkinson", strength=1.0)
    result = dither(image, config)

    # Bayer dithering
    config = DitherConfig(mode="bayer_4x4", levels=4)
    result = dither(image, config, palette=my_palette)

    # Custom pattern
    custom_pattern = [[0, 0.5], [1, 0.5]]
    config = DitherConfig(mode="custom", custom_pattern=custom_pattern)
    result = dither(image, config)
"""

from __future__ import annotations
from typing import Tuple, List, Optional, Any, Dict
import time

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

from lib.retro.dither_types import (
    DitherConfig,
    DitherMatrix,
    DitherMode,
    DitherColorSpace,
    BUILTIN_MATRICES,
    get_matrix,
    list_matrices,
)

from lib.retro.dither_ordered import (
    ordered_dither,
    bayer_dither,
    checkerboard_dither,
    halftone_dither,
    diagonal_dither,
    blue_noise_dither,
    generate_bayer_matrix,
    normalize_matrix,
)

from lib.retro.dither_error import (
    error_diffusion_dither,
    floyd_steinberg_dither,
    atkinson_dither,
    sierra_dither,
    jarvis_judice_ninke_dither,
    stucki_dither,
    burkes_dither,
    find_nearest_color,
    get_kernel,
    get_kernel_names,
    ERROR_DIFFUSION_KERNELS,
)

from lib.retro.dither_patterns import (
    pattern_dither,
    custom_pattern_dither,
    custom_matrix_dither,
    stipple_dither,
    newsprint_dither,
    woodcut_dither,
    list_patterns,
    get_pattern,
    tile_pattern,
    PATTERNS,
)


# =============================================================================
# Main Dithering Function
# =============================================================================

def dither(
    image: Any,
    config: DitherConfig,
    palette: Optional[List[Tuple[int, int, int]]] = None
) -> Any:
    """
    Main dithering function.

    Applies the specified dithering algorithm to the image.

    Args:
        image: Input image (PIL Image or numpy array)
        config: Dither configuration
        palette: Target color palette (optional, uses levels quantization if None)

    Returns:
        Dithered PIL Image

    Raises:
        ValueError: If configuration is invalid
        ImportError: If required dependencies are missing
    """
    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

    # Handle none mode (no dithering)
    if config.mode == "none":
        return _convert_to_pil(image)

    # Convert input to PIL Image
    pil_image = _convert_to_pil(image)

    # Route to appropriate dithering method
    mode = config.mode.lower()

    # Ordered dithering (Bayer matrices)
    if mode in ("bayer_2x2", "bayer_4x4", "bayer_8x8"):
        size = int(mode.split("_")[1][0])  # Extract size from mode name
        return bayer_dither(
            pil_image,
            size=size,
            levels=config.levels,
            strength=config.strength
        )

    if mode in ("ordered_2x2", "ordered_4x4", "ordered_8x8"):
        size = int(mode.split("_")[1][0])
        return bayer_dither(
            pil_image,
            size=size,
            levels=config.levels,
            strength=config.strength
        )

    # Checkerboard
    if mode == "checkerboard":
        return checkerboard_dither(
            pil_image,
            levels=config.levels,
            strength=config.strength
        )

    # Halftone
    if mode == "halftone":
        return halftone_dither(
            pil_image,
            dot_size=config.matrix_size,
            levels=config.levels,
            strength=config.strength
        )

    # Error diffusion algorithms
    if mode == "error_diffusion" or mode == "floyd_steinberg":
        return floyd_steinberg_dither(
            pil_image,
            palette=palette,
            levels=config.levels,
            serpentine=config.serpentine,
            color_space=config.color_space,
            strength=config.strength
        )

    if mode == "atkinson":
        return atkinson_dither(
            pil_image,
            palette=palette,
            levels=config.levels,
            serpentine=config.serpentine,
            color_space=config.color_space,
            strength=config.strength
        )

    if mode == "sierra" or mode == "sierra_lite":
        return sierra_dither(
            pil_image,
            palette=palette,
            levels=config.levels,
            serpentine=config.serpentine,
            color_space=config.color_space,
            strength=config.strength,
            variant="lite"
        )

    if mode == "jarvis_judice_ninke" or mode == "jjn":
        return jarvis_judice_ninke_dither(
            pil_image,
            palette=palette,
            levels=config.levels,
            serpentine=config.serpentine,
            color_space=config.color_space,
            strength=config.strength
        )

    # Random dithering
    if mode == "random":
        return stipple_dither(
            pil_image,
            density=config.strength,
            seed=config.seed
        )

    # Custom pattern
    if mode == "custom":
        if config.custom_pattern is None:
            raise ValueError("custom_pattern is required for custom mode")
        return custom_matrix_dither(
            pil_image,
            config.custom_pattern,
            levels=config.levels,
            strength=config.strength
        )

    # Built-in patterns
    if mode in PATTERNS:
        return pattern_dither(
            pil_image,
            pattern=mode,
            levels=config.levels,
            strength=config.strength
        )

    # Default: try to match a kernel name
    kernel = get_kernel(mode)
    if kernel:
        return error_diffusion_dither(
            pil_image,
            kernel,
            palette=palette,
            levels=config.levels,
            serpentine=config.serpentine,
            color_space=config.color_space,
            strength=config.strength
        )

    raise ValueError(f"Unknown dithering mode: {mode}")


def _convert_to_pil(image: Any) -> Any:
    """Convert various image formats to PIL Image."""
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, Image.Image):
        return image

    if isinstance(image, str):
        return Image.open(image)

    if HAS_NUMPY and isinstance(image, np.ndarray):
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)

        if len(image.shape) == 2:
            return Image.fromarray(image, mode="L")
        elif len(image.shape) == 3:
            if image.shape[2] == 3:
                return Image.fromarray(image, mode="RGB")
            elif image.shape[2] == 4:
                return Image.fromarray(image, mode="RGBA")

    raise ValueError(f"Cannot convert {type(image)} to PIL Image")


# =============================================================================
# Preset Functions
# =============================================================================

def dither_1bit(
    image: Any,
    mode: str = "atkinson",
    strength: float = 1.0
) -> Any:
    """
    Dither to 1-bit (black and white).

    Convenience function for common 1-bit dithering.

    Args:
        image: Input image
        mode: Dithering mode (atkinson, floyd_steinberg, bayer_4x4)
        strength: Dithering strength

    Returns:
        1-bit PIL Image
    """
    config = DitherConfig(
        mode=mode,
        levels=2,
        strength=strength
    )
    result = dither(image, config)

    # Convert to 1-bit mode
    if result.mode != "1":
        result = result.convert("1")

    return result


def dither_gameboy(
    image: Any,
    mode: str = "ordered_4x4",
    strength: float = 0.8
) -> Any:
    """
    Dither with Game Boy palette.

    Uses the classic Game Boy 4-color green palette.

    Args:
        image: Input image
        mode: Dithering mode
        strength: Dithering strength

    Returns:
        Dithered PIL Image with Game Boy colors
    """
    from lib.retro.pixel_types import GAMEBOY_PALETTE

    config = DitherConfig(
        mode=mode,
        levels=4,
        strength=strength
    )
    return dither(image, config, palette=GAMEBOY_PALETTE.colors)


def dither_macplus(
    image: Any,
    mode: str = "atkinson",
    strength: float = 1.0
) -> Any:
    """
    Dither for Mac Plus style (1-bit with Atkinson dithering).

    Classic Macintosh style with Bill Atkinson's dithering algorithm.

    Args:
        image: Input image
        mode: Dithering mode (default: atkinson)
        strength: Dithering strength

    Returns:
        1-bit PIL Image in Mac Plus style
    """
    return dither_1bit(image, mode, strength)


def dither_newspaper(
    image: Any,
    dot_size: int = 2,
    strength: float = 1.0
) -> Any:
    """
    Dither for newspaper print style.

    Creates halftone effect similar to newspaper printing.

    Args:
        image: Input image
        dot_size: Halftone dot size
        strength: Dithering strength

    Returns:
        Dithered PIL Image with halftone effect
    """
    config = DitherConfig(
        mode="halftone",
        matrix_size=dot_size,
        levels=2,
        strength=strength
    )
    return dither(image, config)


# =============================================================================
# Dithering Result
# =============================================================================

@classmethod
def dither_with_result(
    image: Any,
    config: DitherConfig,
    palette: Optional[List[Tuple[int, int, int]]] = None
) -> Dict[str, Any]:
    """
    Dither image and return detailed result.

    Args:
        image: Input image
        config: Dither configuration
        palette: Target palette

    Returns:
        Dictionary with:
        - image: Dithered PIL Image
        - config: Configuration used
        - processing_time: Time in seconds
        - mode: Mode used
        - levels: Levels used
    """
    start_time = time.time()

    result_image = dither(image, config, palette)

    processing_time = time.time() - start_time

    return {
        "image": result_image,
        "config": config.to_dict(),
        "processing_time": processing_time,
        "mode": config.mode,
        "levels": config.levels,
    }


# =============================================================================
# Utility Functions
# =============================================================================

def get_available_modes() -> Dict[str, List[str]]:
    """
    Get all available dithering modes grouped by type.

    Returns:
        Dictionary with mode categories
    """
    return {
        "ordered": [
            "bayer_2x2",
            "bayer_4x4",
            "bayer_8x8",
            "ordered_2x2",
            "ordered_4x4",
            "ordered_8x8",
            "checkerboard",
            "halftone",
        ],
        "error_diffusion": [
            "floyd_steinberg",
            "error_diffusion",
            "atkinson",
            "sierra",
            "sierra_lite",
            "jarvis_judice_ninke",
            "jjn",
        ],
        "pattern": list(PATTERNS.keys()),
        "other": [
            "random",
            "custom",
        ]
    }


def list_all_modes() -> List[str]:
    """
    List all available dithering mode names.

    Returns:
        Flat list of all mode names
    """
    modes = get_available_modes()
    result = []
    for category in modes.values():
        result.extend(category)
    return result


def is_valid_mode(mode: str) -> bool:
    """
    Check if a mode name is valid.

    Args:
        mode: Mode name to check

    Returns:
        True if valid, False otherwise
    """
    return mode.lower() in list_all_modes()


def get_mode_description(mode: str) -> str:
    """
    Get description of a dithering mode.

    Args:
        mode: Mode name

    Returns:
        Human-readable description
    """
    descriptions = {
        "none": "No dithering",
        "bayer_2x2": "2x2 Bayer ordered dithering - coarse pattern",
        "bayer_4x4": "4x4 Bayer ordered dithering - classic look",
        "bayer_8x8": "8x8 Bayer ordered dithering - fine pattern",
        "ordered_2x2": "Same as bayer_2x2",
        "ordered_4x4": "Same as bayer_4x4",
        "ordered_8x8": "Same as bayer_8x8",
        "checkerboard": "Simple 2x2 checkerboard pattern",
        "halftone": "Halftone dot pattern for print simulation",
        "floyd_steinberg": "Floyd-Steinberg error diffusion - smooth gradients",
        "error_diffusion": "Same as floyd_steinberg",
        "atkinson": "Bill Atkinson's algorithm (Macintosh) - high contrast",
        "sierra": "Sierra error diffusion - balanced quality/speed",
        "sierra_lite": "Simplified Sierra - faster processing",
        "jarvis_judice_ninke": "JJN error diffusion - very smooth, slower",
        "jjn": "Same as jarvis_judice_ninke",
        "random": "Random stippling effect",
        "custom": "Custom pattern from config.custom_pattern",
    }

    # Add pattern descriptions
    for pattern_name in PATTERNS:
        descriptions[pattern_name] = f"Pattern-based dithering: {pattern_name.replace('_', ' ')}"

    return descriptions.get(mode.lower(), f"Unknown mode: {mode}")


# =============================================================================
# Module Info
# =============================================================================

def info() -> Dict[str, Any]:
    """
    Get module information.

    Returns:
        Dictionary with module details
    """
    return {
        "name": "dither",
        "description": "Professional dithering algorithms for color-limited output",
        "modes_available": len(list_all_modes()),
        "patterns_available": len(PATTERNS),
        "kernels_available": len(ERROR_DIFFUSION_KERNELS),
        "has_numpy": HAS_NUMPY,
        "has_pil": HAS_PIL,
    }
