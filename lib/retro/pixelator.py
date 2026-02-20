"""
Pixelation Engine for Retro Style Conversion

Core pixelation functions that transform images into pixel art
with various retro console styles.
"""

from __future__ import annotations
from typing import Tuple, List, Optional, Any, Union
import time

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from lib.retro.pixel_types import (
    PixelationConfig,
    PixelationResult,
    PixelStyle,
    ColorPalette,
    get_palette,
)


def pixelate(
    image: Any,
    config: PixelationConfig
) -> PixelationResult:
    """
    Main pixelation function.

    Transforms an image into pixel art according to the configuration.

    Args:
        image: Input image (PIL Image, numpy array, or file path)
        config: Pixelation configuration

    Returns:
        PixelationResult with processed image and metadata
    """
    start_time = time.time()
    warnings = []

    # Validate configuration
    errors = config.validate()
    if errors:
        return PixelationResult(
            image=None,
            warnings=[f"Configuration error: {e}" for e in errors],
        )

    # Convert input to PIL Image
    pil_image = _to_pil_image(image)
    if pil_image is None:
        return PixelationResult(
            image=None,
            warnings=["Could not convert input to image"],
        )

    original_resolution = pil_image.size  # (width, height)

    # Step 1: Calculate target resolution
    target_res = _calculate_target_resolution(pil_image.size, config)
    pixel_resolution = target_res

    # Step 2: Apply edge detection if enabled
    if config.edge_detection and config.style.preserve_edges:
        pil_image = enhance_edges(
            pil_image,
            threshold=config.edge_threshold,
            strength=config.edge_enhancement
        )

    # Step 3: Downscale to target resolution
    if target_res != pil_image.size:
        pil_image = downscale_image(
            pil_image,
            target_res,
            filter_name=config.scaling_filter
        )

    # Step 4: Apply posterization if configured
    if config.style.posterize_levels > 0:
        pil_image = posterize(pil_image, config.style.posterize_levels)

    # Step 5: Apply pixelation based on mode
    if config.style.pixel_size > 1:
        pil_image = pixelate_block(pil_image, config.style.pixel_size)

    # Step 6: Apply color quantization
    palette_used = []
    if config.custom_palette:
        pil_image = quantize_to_palette(pil_image, config.custom_palette)
        palette_used = config.custom_palette
    elif config.palette_name:
        palette = get_palette(config.palette_name)
        if palette:
            pil_image = quantize_to_palette(pil_image, palette.colors)
            palette_used = palette.colors

    # Step 7: Apply mode-specific processing
    pil_image = _apply_mode_processing(pil_image, config.style)

    # Step 8: Count colors
    color_count = _count_colors(pil_image)

    # Step 9: Upscale for output if needed
    output_resolution = pil_image.size
    if config.output_scale > 1:
        output_resolution = (
            pil_image.size[0] * config.output_scale,
            pil_image.size[1] * config.output_scale
        )
        pil_image = pil_image.resize(
            output_resolution,
            Image.NEAREST if HAS_PIL else None
        )

    processing_time = time.time() - start_time

    return PixelationResult(
        image=pil_image,
        original_resolution=original_resolution,
        pixel_resolution=pixel_resolution,
        output_resolution=output_resolution,
        color_count=color_count,
        processing_time=processing_time,
        palette_used=palette_used,
        config=config,
        warnings=warnings,
    )


def downscale_image(
    image: Any,
    target_size: Tuple[int, int],
    filter_name: str = "nearest"
) -> Any:
    """
    Downscale image to target resolution.

    Args:
        image: PIL Image to downscale
        target_size: Target size as (width, height)
        filter_name: Scaling filter (nearest, bilinear, lanczos, box)

    Returns:
        Downscaled PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    filter_map = {
        "nearest": Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "lanczos": Image.LANCZOS,
        "box": Image.BOX,
    }

    resample = filter_map.get(filter_name, Image.NEAREST)
    return image.resize(target_size, resample=resample)


def pixelate_block(image: Any, block_size: int) -> Any:
    """
    Apply block pixelation (average color per block).

    Creates chunky pixels by averaging colors in each block.

    Args:
        image: PIL Image to pixelate
        block_size: Size of each pixel block

    Returns:
        Pixelated PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    width, height = image.size

    # Calculate new size (smaller for block sampling)
    new_width = width // block_size
    new_height = height // block_size

    if new_width == 0 or new_height == 0:
        return image

    # Downscale using BOX filter (area averaging)
    small = image.resize((new_width, new_height), Image.BOX)

    # Upscale using NEAREST (no interpolation)
    return small.resize((new_width * block_size, new_height * block_size), Image.NEAREST)


def enhance_edges(
    image: Any,
    threshold: float = 0.1,
    strength: float = 0.0
) -> Any:
    """
    Detect and enhance edges before pixelation.

    Uses PIL's built-in edge detection filter.

    Args:
        image: PIL Image to process
        threshold: Edge detection sensitivity (0.0-1.0)
        strength: Edge enhancement strength (0.0-1.0)

    Returns:
        PIL Image with enhanced edges
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    if strength <= 0:
        return image

    # Find edges using PIL filter
    edges = image.filter(ImageFilter.FIND_EDGES)

    # Blend edges with original based on strength
    return Image.blend(image, edges, strength * 0.5)


def posterize(image: Any, levels: int) -> Any:
    """
    Reduce color levels for posterized look.

    Args:
        image: PIL Image to posterize
        levels: Number of levels per channel (2-256)

    Returns:
        Posterized PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    if levels < 2 or levels >= 256:
        return image

    # PIL's posterize is in the ImageOps module
    from PIL import ImageOps
    return ImageOps.posterize(image, bits=max(1, int(levels).bit_length() - 1))


def quantize_colors(
    image: Any,
    color_count: int,
    method: str = "median_cut"
) -> Any:
    """
    Reduce image to specified number of colors.

    Args:
        image: PIL Image to quantize
        color_count: Maximum number of colors
        method: Quantization method (median_cut, libimagequant, fastoctree)

    Returns:
        Quantized PIL Image in palette mode
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    method_map = {
        "median_cut": Image.MEDIANCUT,
        "libimagequant": Image.LIBIMAGEQUANT,
        "fastoctree": Image.FASTOCTREE,
    }

    quantize_method = method_map.get(method, Image.MEDIANCUT)

    # Convert to RGB if needed
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    return image.quantize(colors=color_count, method=quantize_method)


def quantize_to_palette(
    image: Any,
    palette: List[Tuple[int, int, int]]
) -> Any:
    """
    Reduce image to specific palette.

    Args:
        image: PIL Image to quantize
        palette: List of RGB color tuples

    Returns:
        PIL Image quantized to palette
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    if not palette:
        return image

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    if not HAS_NUMPY:
        # Fallback: create palette image and use quantize
        return _quantize_to_palette_slow(image, palette)

    # Fast numpy-based quantization
    img_array = np.array(image)

    # Reshape for distance calculation
    pixels = img_array.reshape(-1, 3)

    # Create palette array
    palette_array = np.array(palette)

    # Calculate distances to all palette colors for each pixel
    # Using broadcasting for efficiency
    distances = np.sqrt(((pixels[:, np.newaxis] - palette_array) ** 2).sum(axis=2))

    # Find nearest palette index for each pixel
    nearest_indices = np.argmin(distances, axis=1)

    # Map back to colors
    new_pixels = palette_array[nearest_indices]
    new_array = new_pixels.reshape(img_array.shape)

    return Image.fromarray(new_array.astype(np.uint8))


def _quantize_to_palette_slow(
    image: Any,
    palette: List[Tuple[int, int, int]]
) -> Any:
    """
    Slow palette quantization without numpy.

    Falls back to pixel-by-pixel processing.
    """
    width, height = image.size
    pixels = image.load()

    result = Image.new("RGB", (width, height))
    result_pixels = result.load()

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if isinstance(pixel, int):
                # Grayscale
                pixel = (pixel, pixel, pixel)

            # Find nearest palette color
            min_dist = float('inf')
            nearest = palette[0]

            for color in palette:
                dist = sum((a - b) ** 2 for a, b in zip(pixel[:3], color))
                if dist < min_dist:
                    min_dist = dist
                    nearest = color

            result_pixels[x, y] = nearest

    return result


def extract_palette(image: Any, count: int = 16) -> List[Tuple[int, int, int]]:
    """
    Extract dominant colors from image.

    Args:
        image: PIL Image to analyze
        count: Number of colors to extract

    Returns:
        List of RGB color tuples
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Use quantization to extract colors
    quantized = image.quantize(colors=count, method=Image.MEDIANCUT)

    # Get palette
    palette = quantized.getpalette()
    if palette is None:
        return []

    # Extract RGB triplets
    colors = []
    for i in range(count):
        r = palette[i * 3]
        g = palette[i * 3 + 1]
        b = palette[i * 3 + 2]
        colors.append((r, g, b))

    return colors


# =============================================================================
# Mode-specific pixelation functions
# =============================================================================

def pixelate_32bit(image: Any, config: PixelStyle) -> Any:
    """
    32-bit style (modern pixel art).

    High color count, smooth gradients, visible pixels.
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    if isinstance(image, str):
        image = Image.open(image)

    # Minimal processing - just pixelate if needed
    if config.pixel_size > 1:
        image = pixelate_block(image, config.pixel_size)

    return image


def pixelate_16bit(image: Any, config: PixelStyle) -> Any:
    """
    16-bit style (SNES/Genesis).

    256-512 colors, smooth gradients, visible pixels.
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    if isinstance(image, str):
        image = Image.open(image)

    # Apply pixelation
    if config.pixel_size > 1:
        image = pixelate_block(image, config.pixel_size)

    # Limit colors to 256-512
    if config.color_limit < 512:
        image = quantize_colors(image, min(config.color_limit, 512))

    return image


def pixelate_8bit(image: Any, config: PixelStyle) -> Any:
    """
    8-bit style (NES/Master System).

    Limited colors (16-64), visible pixels, posterized.
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    if isinstance(image, str):
        image = Image.open(image)

    # Apply posterization for 8-bit look
    if config.posterize_levels > 0:
        image = posterize(image, config.posterize_levels)
    else:
        image = posterize(image, 4)  # Default 4 levels per channel

    # Apply pixelation
    if config.pixel_size > 1:
        image = pixelate_block(image, config.pixel_size)

    # Limit colors
    color_limit = min(config.color_limit, 64)
    image = quantize_colors(image, color_limit)

    return image


def pixelate_4bit(image: Any, config: PixelStyle) -> Any:
    """
    4-bit style (Game Boy).

    4-16 colors, chunky pixels.
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    if isinstance(image, str):
        image = Image.open(image)

    # Apply pixelation with larger blocks
    if config.pixel_size > 1:
        image = pixelate_block(image, config.pixel_size)
    else:
        image = pixelate_block(image, 2)  # Default 2x2 blocks

    # Limit to 4-16 colors
    color_limit = min(config.color_limit, 16)
    image = quantize_colors(image, color_limit)

    return image


def pixelate_2bit(image: Any, config: PixelStyle) -> Any:
    """
    2-bit style (early LCD).

    2-4 colors, chunky pixels.
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    if isinstance(image, str):
        image = Image.open(image)

    # Apply pixelation
    if config.pixel_size > 1:
        image = pixelate_block(image, config.pixel_size)

    # Limit to 2-4 colors
    color_limit = min(config.color_limit, 4)
    image = quantize_colors(image, color_limit)

    return image


def pixelate_1bit(image: Any, config: PixelStyle) -> Any:
    """
    1-bit style (Mac Plus, LCD).

    Pure black and white, optionally dithered.
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to grayscale first
    if image.mode != "L":
        image = image.convert("L")

    # Apply dithering based on config
    if config.dither_mode == "ordered":
        # Bayer dithering
        image = _apply_bayer_dither(image)
    elif config.dither_mode == "floyd_steinberg":
        # Error diffusion
        image = _apply_floyd_steinberg_dither(image)
    else:
        # Simple threshold
        image = image.point(lambda x: 255 if x > 128 else 0)

    # Convert to 1-bit
    image = image.convert("1")

    return image


def _apply_bayer_dither(image: Any) -> Any:
    """Apply 4x4 Bayer matrix dithering."""
    if not HAS_PIL or not HAS_NUMPY:
        return image

    # 4x4 Bayer matrix (values 0-15)
    bayer_matrix = np.array([
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5]
    ], dtype=np.float32) / 16.0

    img_array = np.array(image)
    height, width = img_array.shape

    # Normalize to 0-1
    normalized = img_array / 255.0

    # Create threshold map by tiling Bayer matrix
    threshold = np.tile(bayer_matrix, (height // 4 + 1, width // 4 + 1))[:height, :width]

    # Apply dithering
    result = (normalized > threshold).astype(np.uint8) * 255

    return Image.fromarray(result)


def _apply_floyd_steinberg_dither(image: Any) -> Any:
    """Apply Floyd-Steinberg error diffusion dithering."""
    if not HAS_PIL or not HAS_NUMPY:
        return image

    img_array = np.array(image, dtype=np.float32)
    height, width = img_array.shape

    for y in range(height - 1):
        for x in range(1, width - 1):
            old = img_array[y, x]
            new = 255.0 if old > 128 else 0.0
            img_array[y, x] = new
            error = old - new

            # Distribute error to neighbors
            img_array[y, x + 1] += error * 7 / 16
            img_array[y + 1, x - 1] += error * 3 / 16
            img_array[y + 1, x] += error * 5 / 16
            img_array[y + 1, x + 1] += error * 1 / 16

    return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8), mode="L")


# =============================================================================
# Internal helper functions
# =============================================================================

def _to_pil_image(image: Any) -> Optional[Any]:
    """Convert various image formats to PIL Image."""
    if not HAS_PIL:
        return None

    if isinstance(image, Image.Image):
        return image

    if isinstance(image, str):
        try:
            return Image.open(image)
        except Exception:
            return None

    if HAS_NUMPY and isinstance(image, np.ndarray):
        try:
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)

            if len(image.shape) == 2:
                return Image.fromarray(image, mode="L")
            elif len(image.shape) == 3:
                if image.shape[2] == 3:
                    return Image.fromarray(image)
                elif image.shape[2] == 4:
                    return Image.fromarray(image)
        except Exception:
            return None

    return None


def _calculate_target_resolution(
    original_size: Tuple[int, int],
    config: PixelationConfig
) -> Tuple[int, int]:
    """Calculate target resolution respecting aspect ratio mode."""
    orig_width, orig_height = original_size
    target_width, target_height = config.target_resolution

    # If target is (0, 0), use original size
    if target_width == 0 or target_height == 0:
        return original_size

    if config.aspect_ratio_mode == "stretch":
        return (target_width, target_height)

    if config.aspect_ratio_mode == "crop":
        # Crop to fit target aspect ratio
        orig_aspect = orig_width / orig_height
        target_aspect = target_width / target_height

        if orig_aspect > target_aspect:
            # Original is wider - crop width
            new_width = int(orig_height * target_aspect)
            new_height = orig_height
        else:
            # Original is taller - crop height
            new_width = orig_width
            new_height = int(orig_width / target_aspect)

        return (new_width, new_height)

    # preserve (default)
    orig_aspect = orig_width / orig_height
    target_aspect = target_width / target_height

    if orig_aspect > target_aspect:
        # Original is wider - fit to width
        new_width = target_width
        new_height = int(target_width / orig_aspect)
    else:
        # Original is taller - fit to height
        new_height = target_height
        new_width = int(target_height * orig_aspect)

    return (new_width, new_height)


def _apply_mode_processing(image: Any, style: PixelStyle) -> Any:
    """Apply mode-specific processing to image."""
    mode_functions = {
        "32bit": pixelate_32bit,
        "16bit": pixelate_16bit,
        "8bit": pixelate_8bit,
        "4bit": pixelate_4bit,
        "2bit": pixelate_2bit,
        "1bit": pixelate_1bit,
    }

    func = mode_functions.get(style.mode)
    if func:
        return func(image, style)

    # photorealistic and stylized don't need special processing
    return image


def _count_colors(image: Any) -> int:
    """Count unique colors in image."""
    if not HAS_PIL:
        return 0

    if isinstance(image, str):
        image = Image.open(image)

    # Get colors
    colors = image.getcolors(maxcolors=1000000)
    if colors is None:
        # Too many colors to count efficiently
        if HAS_NUMPY:
            arr = np.array(image)
            return len(np.unique(arr.reshape(-1, arr.shape[-1] if len(arr.shape) > 2 else 1), axis=0))
        return 0

    return len(colors)
