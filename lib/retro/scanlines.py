"""
Scanline Effect Module

Implements authentic CRT scanline effects with multiple patterns and modes.
Scanlines simulate the horizontal dark lines visible on CRT displays,
caused by the gaps between scan lines during electron beam sweep.

Modules:
- apply_scanlines: Main scanline effect function
- create_scanline_overlay: Generate scanline overlay mask
- alternate_scanlines: Alternate line pattern
- every_line_scanlines: Every line pattern
- random_scanlines: Random variation pattern

Example Usage:
    from lib.retro.scanlines import apply_scanlines
    from lib.retro.crt_types import ScanlineConfig

    config = ScanlineConfig(intensity=0.3, spacing=2)
    result = apply_scanlines(image, config)
"""

from typing import List, Tuple, Optional, Any, Union
import math
import random

# Handle PIL import for image processing
try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    np = None

from lib.retro.crt_types import ScanlineConfig


# =============================================================================
# Scanline Pattern Generators
# =============================================================================

def alternate_scanlines(height: int, config: ScanlineConfig) -> List[float]:
    """
    Generate alternate line pattern (dark/light/dark/light).

    This is the classic CRT scanline pattern where every other line
    appears darker due to the electron beam sweep pattern.

    Args:
        height: Image height in pixels
        config: Scanline configuration

    Returns:
        List of brightness multipliers (0-1) for each row
    """
    pattern = []
    spacing = config.spacing
    intensity = config.intensity
    thickness = config.thickness

    for y in range(height):
        group_position = y % spacing
        line_position = group_position / spacing if spacing > 0 else 0

        # Darken the first 'thickness' portion of each group
        if line_position < thickness:
            # Dark line
            multiplier = 1.0 - intensity
        else:
            # Light line
            multiplier = 1.0

        pattern.append(multiplier)

    return pattern


def every_line_scanlines(height: int, config: ScanlineConfig) -> List[float]:
    """
    Generate every-line pattern with varying intensity.

    Every line has some scanline effect, creating a more uniform
    darkening effect across the entire image.

    Args:
        height: Image height in pixels
        config: Scanline configuration

    Returns:
        List of brightness multipliers (0-1) for each row
    """
    pattern = []
    intensity = config.intensity
    thickness = config.thickness

    for y in range(height):
        # Calculate position within line (0 to 1)
        # Use sub-pixel variation for smoother effect
        line_progress = (y % 2) / 2.0 + 0.25

        if line_progress < thickness:
            # Apply scanline darkness
            fade = 1.0 - (line_progress / thickness) if thickness > 0 else 0
            multiplier = 1.0 - (intensity * fade)
        else:
            # Less affected area
            multiplier = 1.0 - (intensity * 0.1)

        pattern.append(multiplier)

    return pattern


def random_scanlines(height: int, config: ScanlineConfig, seed: int = None) -> List[float]:
    """
    Generate scanline pattern with random variation.

    Adds slight random variation to scanline intensity, simulating
    analog CRT irregularities.

    Args:
        height: Image height in pixels
        config: Scanline configuration
        seed: Random seed for reproducibility

    Returns:
        List of brightness multipliers (0-1) for each row
    """
    if seed is not None:
        random.seed(seed)

    pattern = []
    spacing = config.spacing
    intensity = config.intensity
    thickness = config.thickness

    for y in range(height):
        group_position = y % spacing
        line_position = group_position / spacing if spacing > 0 else 0

        # Base multiplier
        if line_position < thickness:
            base_multiplier = 1.0 - intensity
        else:
            base_multiplier = 1.0

        # Add random variation (up to +/- 10%)
        variation = random.uniform(-0.1, 0.1) * intensity
        multiplier = max(0.1, min(1.0, base_multiplier + variation))

        pattern.append(multiplier)

    return pattern


# =============================================================================
# Scanline Overlay Generation
# =============================================================================

def create_scanline_overlay(
    width: int,
    height: int,
    config: ScanlineConfig,
    seed: int = None
) -> "np.ndarray":
    """
    Create scanline overlay mask as numpy array.

    Generates a 2D array of brightness multipliers that can be
    applied to an image to simulate scanlines.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        config: Scanline configuration
        seed: Random seed for reproducibility (random mode only)

    Returns:
        2D numpy array of brightness multipliers (0-1)
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for scanline overlay generation")

    # Generate scanline pattern based on mode
    if config.mode == "alternate":
        pattern = alternate_scanlines(height, config)
    elif config.mode == "every_line":
        pattern = every_line_scanlines(height, config)
    elif config.mode == "random":
        pattern = random_scanlines(height, config, seed)
    else:
        pattern = alternate_scanlines(height, config)

    # Create 2D array
    overlay = np.array(pattern, dtype=np.float32).reshape(1, height)
    overlay = np.tile(overlay, (width, 1))
    overlay = overlay.T  # Transpose to (height, width)

    return overlay


def create_scanline_texture(width: int, height: int, config: ScanlineConfig) -> "np.ndarray":
    """
    Create a detailed scanline texture with sub-pixel accuracy.

    Generates a more realistic scanline texture that includes
    gradual falloff and realistic CRT characteristics.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        config: Scanline configuration

    Returns:
        2D numpy array of brightness multipliers (0-1)
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for scanline texture generation")

    spacing = config.spacing
    intensity = config.intensity
    thickness = config.thickness

    # Create array with sub-pixel accuracy
    y_coords = np.arange(height, dtype=np.float32)

    # Calculate position within each scanline group
    group_position = y_coords % spacing

    # Create smooth falloff using sine wave for more realistic look
    # Normalized position within group
    normalized_pos = group_position / spacing if spacing > 0 else 0

    # Create scanline effect with smooth edges
    # Use a cosine-based falloff for more authentic CRT look
    scanline_phase = normalized_pos * 2 * np.pi

    # Base scanline darkness
    base_darkness = intensity * 0.5

    # Modulate with sine wave for smooth effect
    wave = np.cos(scanline_phase) * 0.5 + 0.5  # 0 to 1

    # Apply thickness - if within dark portion, apply intensity
    darkness_mask = (normalized_pos < thickness).astype(np.float32)

    # Combine for final multiplier
    multiplier = 1.0 - (darkness_mask * intensity * (0.7 + 0.3 * wave))

    # Expand to 2D
    overlay = np.tile(multiplier.reshape(height, 1), (1, width))

    return overlay


# =============================================================================
# Main Scanline Application Functions
# =============================================================================

def apply_scanlines(image: Any, config: ScanlineConfig, seed: int = None) -> Any:
    """
    Apply scanline effect to image.

    Takes an image (PIL Image or numpy array) and applies the
    scanline effect based on the provided configuration.

    Args:
        image: PIL Image or numpy array (H, W, C) or (H, W)
        config: Scanline configuration
        seed: Random seed for reproducibility (random mode only)

    Returns:
        Image with scanlines applied (same type as input)
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for scanline effects")

    if not config.enabled:
        return image

    # Convert PIL Image to numpy if needed
    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()
        # Normalize if needed
        if arr.max() > 1.0:
            arr = arr / 255.0

    height = arr.shape[0]
    width = arr.shape[1]

    # Create scanline overlay
    overlay = create_scanline_overlay(width, height, config, seed)

    # Apply brightness compensation
    if config.brightness_compensation != 1.0:
        overlay = overlay * config.brightness_compensation

    # Apply overlay to image
    if len(arr.shape) == 3:
        # Color image - apply to all channels
        overlay = overlay[:, :, np.newaxis]
        arr = arr * overlay
    else:
        # Grayscale
        arr = arr * overlay

    # Clip to valid range
    arr = np.clip(arr, 0, 1)

    # Convert back to PIL if needed
    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    else:
        return arr


def apply_scanlines_fast(image: Any, config: ScanlineConfig) -> Any:
    """
    Fast scanline application using simple row multiplication.

    A simpler, faster version of scanline application that works
    directly with row indices without generating a full overlay.

    Args:
        image: PIL Image or numpy array
        config: Scanline configuration

    Returns:
        Image with scanlines applied
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for scanline effects")

    if not config.enabled:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    height = arr.shape[0]
    spacing = config.spacing
    intensity = config.intensity
    thickness = config.thickness

    # Create row multipliers
    row_indices = np.arange(height)
    group_position = row_indices % spacing
    line_position = group_position / spacing if spacing > 0 else 0

    # Calculate multipliers
    multipliers = np.where(
        line_position < thickness,
        1.0 - intensity,
        1.0
    ).astype(np.float32)

    # Apply brightness compensation
    if config.brightness_compensation != 1.0:
        multipliers *= config.brightness_compensation

    # Apply to image
    if len(arr.shape) == 3:
        arr = arr * multipliers[:, np.newaxis, np.newaxis]
    else:
        arr = arr * multipliers[:, np.newaxis]

    arr = np.clip(arr, 0, 1)

    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    return arr


# =============================================================================
# GPU/Blender Compositor Functions
# =============================================================================

def apply_scanlines_gpu(image: Any, config: ScanlineConfig) -> Any:
    """
    GPU-accelerated scanline effect for Blender compositor.

    Creates a scanline effect that can be used in Blender's
    compositor node system. Returns node setup instructions.

    Args:
        image: Blender image or render layer
        config: Scanline configuration

    Returns:
        Dictionary with node setup parameters for Blender compositor
    """
    # This returns parameters for Blender compositor setup
    # The actual implementation would be in crt_compositor.py
    return {
        "type": "scanlines",
        "enabled": config.enabled,
        "intensity": config.intensity,
        "spacing": config.spacing,
        "thickness": config.thickness,
        "mode": config.mode,
        "brightness_compensation": config.brightness_compensation,
    }


def get_scanline_shader_code(config: ScanlineConfig) -> str:
    """
    Generate GLSL shader code for scanline effect.

    Returns GLSL code that can be used in shader-based
    implementations of the scanline effect.

    Args:
        config: Scanline configuration

    Returns:
        GLSL shader code string
    """
    shader = f"""
// Scanline Effect Shader
uniform float scanline_intensity = {config.intensity};
uniform int scanline_spacing = {config.spacing};
uniform float scanline_thickness = {config.thickness};
uniform float brightness_compensation = {config.brightness_compensation};

float scanline_effect(vec2 uv, int mode) {{
    float y_pos = uv.y;
    float group_pos = mod(y_pos * resolution.y, float(scanline_spacing));
    float normalized_pos = group_pos / float(scanline_spacing);

    float multiplier;

    if (mode == 0) {{ // alternate
        multiplier = (normalized_pos < scanline_thickness)
            ? (1.0 - scanline_intensity)
            : 1.0;
    }} else if (mode == 1) {{ // every_line
        float line_progress = mod(floor(y_pos * resolution.y), 2.0) / 2.0 + 0.25;
        float fade = (line_progress < scanline_thickness)
            ? 1.0 - (line_progress / scanline_thickness)
            : 0.0;
        multiplier = 1.0 - (scanline_intensity * (fade * 0.9 + 0.1));
    }} else {{ // random - use noise function
        float noise = fract(sin(dot(vec2(uv.y, 0.0), vec2(12.9898, 78.233))) * 43758.5453);
        float variation = (noise - 0.5) * 0.2 * scanline_intensity;
        multiplier = (normalized_pos < scanline_thickness)
            ? (1.0 - scanline_intensity + variation)
            : (1.0 + variation);
    }}

    return multiplier * brightness_compensation;
}}

vec4 apply_scanlines(vec4 color, vec2 uv) {{
    float scanline_mult = scanline_effect(uv, {"0" if config.mode == "alternate" else "1" if config.mode == "every_line" else "2"});
    return vec4(color.rgb * scanline_mult, color.a);
}}
"""
    return shader


# =============================================================================
# Utility Functions
# =============================================================================

def calculate_brightness_loss(config: ScanlineConfig) -> float:
    """
    Calculate the brightness loss from scanline effect.

    Args:
        config: Scanline configuration

    Returns:
        Average brightness multiplier (0-1)
    """
    if not config.enabled:
        return 1.0

    thickness = config.thickness
    intensity = config.intensity
    spacing = config.spacing

    # Average brightness = weighted average of dark and light portions
    dark_portion = thickness
    light_portion = 1.0 - thickness
    avg_brightness = dark_portion * (1.0 - intensity) + light_portion * 1.0

    # Apply spacing factor (more spacing = less impact)
    spacing_factor = 1.0 / spacing if spacing > 1 else 1.0

    return avg_brightness * spacing_factor


def recommend_brightness_compensation(config: ScanlineConfig) -> float:
    """
    Recommend brightness compensation value for given config.

    Args:
        config: Scanline configuration

    Returns:
        Recommended brightness compensation (typically 1.0-1.5)
    """
    if not config.enabled:
        return 1.0

    brightness_loss = calculate_brightness_loss(config)

    # Compensate to bring average back to ~0.9 (slightly below 1.0 for realism)
    target_brightness = 0.9
    compensation = target_brightness / brightness_loss

    # Clamp to reasonable range
    return min(max(compensation, 1.0), 1.5)


def estimate_scanline_visibility(config: ScanlineConfig, view_distance: float = 1.0) -> float:
    """
    Estimate how visible scanlines will be at a given viewing distance.

    Args:
        config: Scanline configuration
        view_distance: Viewing distance relative to screen height

    Returns:
        Visibility score (0-1, higher = more visible)
    """
    if not config.enabled:
        return 0.0

    # Visibility depends on intensity, spacing, and viewing distance
    intensity_factor = config.intensity
    spacing_factor = config.spacing / 4.0  # Normalize to common spacing
    distance_factor = min(1.0, 1.0 / max(view_distance, 0.1))

    # Combined visibility score
    visibility = intensity_factor * spacing_factor * distance_factor

    return min(1.0, visibility)
