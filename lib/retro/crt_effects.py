"""
CRT Additional Effects Module

Implements additional CRT effects: bloom, chromatic aberration, flicker,
interlace, pixel jitter, noise, and ghosting.

Combined with scanlines, phosphor, and curvature, these complete the
authentic retro display simulation.

Example Usage:
    from lib.retro.crt_effects import apply_all_effects
    from lib.retro.crt_types import CRTConfig

    config = CRTConfig(bloom=0.15, chromatic_aberration=0.003)
    result = apply_all_effects(image, config, frame=0)
"""

from typing import Tuple, Optional, Any
import math
import random

# Handle PIL import for image processing
try:
    from PIL import Image, ImageFilter
    import numpy as np
    from scipy import ndimage
    HAS_PIL = True
    HAS_SCIPY = True
except ImportError:
    HAS_PIL = False
    HAS_SCIPY = False
    Image = None
    np = None

from lib.retro.crt_types import CRTConfig


# =============================================================================
# Bloom Effect
# =============================================================================

def apply_bloom(image: Any, amount: float, threshold: float = 0.8) -> Any:
    """
    Apply bloom/glow effect to bright areas.

    Bloom simulates the light bleed from very bright areas
    on phosphor-based displays.

    Args:
        image: PIL Image or numpy array
        amount: Bloom intensity (0-1)
        threshold: Brightness threshold for bloom (0-1)

    Returns:
        Image with bloom applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for bloom effects")

    if amount <= 0:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    # Calculate luminance
    if len(arr.shape) == 3:
        luminance = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    else:
        luminance = arr

    # Create bloom mask for bright areas
    bright_mask = luminance > threshold

    # Extract bright areas
    if len(arr.shape) == 3:
        bright_areas = np.zeros_like(arr)
        for c in range(3):
            bright_areas[:, :, c] = arr[:, :, c] * bright_mask
    else:
        bright_areas = arr * bright_mask

    # Apply Gaussian blur for glow
    if HAS_SCIPY:
        # Use scipy for Gaussian blur
        sigma = 5 * amount
        if len(arr.shape) == 3:
            bloom_layer = np.zeros_like(arr)
            for c in range(3):
                bloom_layer[:, :, c] = ndimage.gaussian_filter(bright_areas[:, :, c], sigma=sigma)
        else:
            bloom_layer = ndimage.gaussian_filter(bright_areas, sigma=sigma)
    else:
        # Fallback: simple box blur
        bloom_layer = simple_blur(bright_areas, radius=int(5 * amount))

    # Blend bloom layer with original
    result = arr + bloom_layer * amount
    result = np.clip(result, 0, 1)

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


def simple_blur(arr: "np.ndarray", radius: int = 3) -> "np.ndarray":
    """Simple box blur fallback when scipy not available."""
    if radius < 1:
        return arr.copy()

    kernel_size = radius * 2 + 1
    result = arr.copy()

    # Simple averaging blur
    padded = np.pad(arr, ((radius, radius), (radius, radius), (0, 0)) if len(arr.shape) == 3 else radius, mode='edge')

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if len(arr.shape) == 3:
                result[i, j] = padded[i:i+kernel_size, j:j+kernel_size].mean(axis=(0, 1))
            else:
                result[i, j] = padded[i:i+kernel_size, j:j+kernel_size].mean()

    return result


# =============================================================================
# Chromatic Aberration
# =============================================================================

def apply_chromatic_aberration(image: Any, amount: float) -> Any:
    """
    Apply RGB channel separation effect.

    Chromatic aberration simulates the color fringing from
    lens imperfections and CRT electron beam misalignment.

    Args:
        image: PIL Image or numpy array
        amount: Separation amount in pixels (0-0.1 normalized)

    Returns:
        Image with chromatic aberration applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for chromatic aberration")

    if amount <= 0:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    if len(arr.shape) != 3:
        return image  # Grayscale, no effect

    height, width = arr.shape[:2]

    # Calculate pixel offset
    offset = int(amount * width)

    if offset == 0:
        return image

    # Shift red channel left, blue channel right
    result = arr.copy()

    # Red channel shift left
    if offset > 0:
        result[offset:, :, 0] = arr[:-offset, :, 0]
        result[:offset, :, 0] = arr[0, :, 0]
    else:
        result[:offset, :, 0] = arr[-offset:, :, 0]

    # Blue channel shift right
    if offset > 0:
        result[:-offset, :, 2] = arr[offset:, :, 2]
        result[-offset:, :, 2] = arr[-1, :, 2]
    else:
        result[-offset:, :, 2] = arr[:offset, :, 2]

    result = np.clip(result, 0, 1)

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


# =============================================================================
# Flicker Effect
# =============================================================================

def apply_flicker(image: Any, amount: float, frame: int = 0, seed: int = None) -> Any:
    """
    Apply brightness flicker effect.

    Simulates the subtle brightness variation of CRT displays
    due to power supply fluctuations and electron beam intensity.

    Args:
        image: PIL Image or numpy array
        amount: Flicker intensity (0-1)
        frame: Frame number for animation
        seed: Random seed for reproducibility

    Returns:
        Image with flicker applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for flicker effects")

    if amount <= 0:
        return image

    if seed is not None:
        random.seed(seed + frame)
    else:
        random.seed(frame)

    # Generate flicker variation
    # Use sine wave for smooth oscillation plus random noise
    base_flicker = math.sin(frame * 0.5) * 0.5 + 0.5  # 0 to 1
    random_flicker = random.uniform(-0.5, 0.5)
    total_flicker = base_flicker * 0.3 + random_flicker * 0.7

    # Calculate brightness adjustment
    adjustment = 1.0 + total_flicker * amount * 0.1  # +/- 10% variation max

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    # Apply brightness adjustment
    result = arr * adjustment
    result = np.clip(result, 0, 1)

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


# =============================================================================
# Interlace Effect
# =============================================================================

def apply_interlace(image: Any, field: int = 0) -> Any:
    """
    Apply interlacing effect.

    Simulates the alternating field display of interlaced CRTs,
    where only odd or even scanlines are shown per frame.

    Args:
        image: PIL Image or numpy array
        field: 0 for even lines darkened, 1 for odd lines darkened

    Returns:
        Image with interlace effect applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for interlace effects")

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    height = arr.shape[0]

    # Darken lines based on field
    # field=0: darken odd lines (1, 3, 5...), keep even (0, 2, 4...)
    # field=1: darken even lines (0, 2, 4...), keep odd (1, 3, 5...)
    if field == 0:
        # Darken odd lines
        for y in range(1, height, 2):
            if len(arr.shape) == 3:
                arr[y, :, :] *= 0.5
            else:
                arr[y, :] *= 0.5
    else:
        # Darken even lines
        for y in range(0, height, 2):
            if len(arr.shape) == 3:
                arr[y, :, :] *= 0.5
            else:
                arr[y, :] *= 0.5

    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    return arr


# =============================================================================
# Pixel Jitter Effect
# =============================================================================

def apply_pixel_jitter(image: Any, amount: float, frame: int = 0, seed: int = None) -> Any:
    """
    Apply subtle pixel movement effect.

    Simulates the horizontal instability of analog signals,
    causing pixels to shift slightly between frames.

    Args:
        image: PIL Image or numpy array
        amount: Jitter intensity (0-1)
        frame: Frame number for animation
        seed: Random seed for reproducibility

    Returns:
        Image with jitter applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for jitter effects")

    if amount <= 0:
        return image

    if seed is not None:
        random.seed(seed + frame)
    else:
        random.seed(frame)

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    height, width = arr.shape[:2]

    # Calculate maximum jitter in pixels
    max_jitter = max(1, int(amount * 3))

    # Generate per-row jitter offsets
    jitter_offsets = [random.randint(-max_jitter, max_jitter) for _ in range(height)]

    # Apply horizontal jitter to each row
    result = np.zeros_like(arr)
    for y in range(height):
        offset = jitter_offsets[y]
        if offset > 0:
            result[y, :width-offset] = arr[y, offset:]
            result[y, width-offset:] = arr[y, -1:] if len(arr.shape) == 3 else arr[y, -1]
        elif offset < 0:
            result[y, -offset:] = arr[y, :width+offset]
            result[y, :-offset] = arr[y, :1] if len(arr.shape) == 3 else arr[y, 0]
        else:
            result[y] = arr[y]

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


# =============================================================================
# Noise Effect
# =============================================================================

def apply_noise(image: Any, amount: float, frame: int = 0, seed: int = None) -> Any:
    """
    Apply analog static noise.

    Simulates the random noise and interference visible
    on analog CRT displays.

    Args:
        image: PIL Image or numpy array
        amount: Noise intensity (0-1)
        frame: Frame number for animation
        seed: Random seed for reproducibility

    Returns:
        Image with noise applied
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for noise effects")

    if amount <= 0:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    # Set random seed
    if seed is not None:
        np.random.seed(seed + frame)
    else:
        np.random.seed(frame)

    # Generate noise
    noise = np.random.uniform(-amount, amount, arr.shape).astype(np.float32)

    # Apply noise
    result = arr + noise
    result = np.clip(result, 0, 1)

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


# =============================================================================
# Ghosting Effect
# =============================================================================

def apply_ghosting(image: Any, amount: float, previous_frame: Any = None) -> Any:
    """
    Apply image persistence/ghosting effect.

    Simulates the slow phosphor decay and image retention
    visible on LCDs and some CRTs.

    Args:
        image: Current frame (PIL Image or numpy array)
        amount: Ghosting intensity (0-1)
        previous_frame: Previous frame for ghosting (optional)

    Returns:
        Image with ghosting applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for ghosting effects")

    if amount <= 0 or previous_frame is None:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        current = np.array(image).astype(np.float32) / 255.0
        prev = np.array(previous_frame).astype(np.float32) / 255.0
    else:
        current = image.astype(np.float32) if image.dtype != np.float32 else image.copy()
        prev = previous_frame.astype(np.float32) if previous_frame.dtype != np.float32 else previous_frame.copy()

    # Blend previous frame with current
    result = current * (1 - amount) + prev * amount
    result = np.clip(result, 0, 1)

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


# =============================================================================
# Color Adjustments
# =============================================================================

def apply_color_adjustments(
    image: Any,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    gamma: float = 2.2
) -> Any:
    """
    Apply color adjustments.

    Args:
        image: PIL Image or numpy array
        brightness: Brightness multiplier
        contrast: Contrast multiplier
        saturation: Saturation multiplier
        gamma: Gamma correction value

    Returns:
        Color-adjusted image
    """
    if not HAS_PIL:
        raise ImportError("PIL required for color adjustments")

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    # Apply brightness
    arr = arr * brightness

    # Apply contrast
    arr = (arr - 0.5) * contrast + 0.5

    # Apply saturation
    if len(arr.shape) == 3 and saturation != 1.0:
        # Convert to grayscale
        gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        # Blend with original
        for c in range(3):
            arr[:, :, c] = gray * (1 - saturation) + arr[:, :, c] * saturation

    # Apply gamma correction
    if gamma != 1.0:
        arr = np.power(np.clip(arr, 0, 1), 1.0 / gamma)

    arr = np.clip(arr, 0, 1)

    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    return arr


# =============================================================================
# Main Pipeline
# =============================================================================

def apply_all_effects(
    image: Any,
    config: CRTConfig,
    frame: int = 0,
    previous_frame: Any = None,
    seed: int = None
) -> Any:
    """
    Apply all CRT effects in correct order.

    Order: color adjustments -> curvature -> chromatic aberration ->
           scanlines -> phosphor -> bloom -> noise -> flicker -> jitter -> ghosting

    Args:
        image: Input image
        config: CRT configuration
        frame: Frame number for animated effects
        previous_frame: Previous frame for ghosting
        seed: Random seed for reproducibility

    Returns:
        Image with all effects applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for CRT effects")

    # Import effect modules here to avoid circular imports
    from lib.retro.scanlines import apply_scanlines
    from lib.retro.phosphor import apply_phosphor_mask
    from lib.retro.curvature import apply_curvature

    result = image

    # 1. Color adjustments
    result = apply_color_adjustments(
        result,
        brightness=config.brightness,
        contrast=config.contrast,
        saturation=config.saturation,
        gamma=config.gamma
    )

    # 2. Curvature
    if config.curvature.enabled:
        result = apply_curvature(result, config.curvature)

    # 3. Chromatic aberration
    if config.chromatic_aberration > 0:
        result = apply_chromatic_aberration(result, config.chromatic_aberration)

    # 4. Scanlines
    if config.scanlines.enabled:
        result = apply_scanlines(result, config.scanlines, seed=seed)

    # 5. Phosphor mask
    if config.phosphor.enabled:
        result = apply_phosphor_mask(result, config.phosphor)

    # 6. Bloom
    if config.bloom > 0:
        result = apply_bloom(result, config.bloom)

    # 7. Interlace (if enabled)
    if config.interlace:
        result = apply_interlace(result, frame % 2)

    # 8. Noise
    if config.noise > 0:
        result = apply_noise(result, config.noise, frame=frame, seed=seed)

    # 9. Flicker
    if config.flicker > 0:
        result = apply_flicker(result, config.flicker, frame=frame, seed=seed)

    # 10. Pixel jitter
    if config.pixel_jitter > 0:
        result = apply_pixel_jitter(result, config.pixel_jitter, frame=frame, seed=seed)

    # 11. Ghosting
    if config.ghosting > 0 and previous_frame is not None:
        result = apply_ghosting(result, config.ghosting, previous_frame)

    return result


def apply_effects_fast(
    image: Any,
    config: CRTConfig,
    frame: int = 0
) -> Any:
    """
    Fast effects application using simplified algorithms.

    Skips expensive effects and uses fast approximations.

    Args:
        image: Input image
        config: CRT configuration
        frame: Frame number

    Returns:
        Image with effects applied
    """
    if not HAS_PIL:
        raise ImportError("PIL required for CRT effects")

    from lib.retro.scanlines import apply_scanlines_fast
    from lib.retro.phosphor import apply_phosphor_mask_fast

    result = image

    # Basic color adjustments
    result = apply_color_adjustments(
        result,
        brightness=config.brightness,
        contrast=config.contrast,
        saturation=config.saturation,
        gamma=config.gamma
    )

    # Fast scanlines
    if config.scanlines.enabled:
        result = apply_scanlines_fast(result, config.scanlines)

    # Fast phosphor
    if config.phosphor.enabled:
        result = apply_phosphor_mask_fast(result, config.phosphor)

    # Skip bloom, noise, flicker for speed

    return result
