"""
Phosphor Mask Module

Implements authentic CRT phosphor mask effects, simulating the RGB
dot/stripe patterns visible on close inspection of CRT displays.

Different CRT technologies used different mask patterns:
- RGB/BGR: Standard stripe patterns
- Aperture Grille: Sony Trinitron style vertical stripes
- Slot Mask: Standard CRT with slots
- Shadow Mask: Delta pattern shadow mask

Example Usage:
    from lib.retro.phosphor import apply_phosphor_mask, create_phosphor_mask
    from lib.retro.crt_types import PhosphorConfig

    config = PhosphorConfig(pattern="aperture_grille", intensity=0.5)
    result = apply_phosphor_mask(image, config)
"""

from typing import List, Tuple, Optional, Any, Dict
import math

# Handle PIL import for image processing
try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    np = None

from lib.retro.crt_types import PhosphorConfig


# =============================================================================
# Phosphor Pattern Definitions
# =============================================================================

# Basic RGB patterns (normalized 0-1 values)
PHOSPHOR_PATTERNS: Dict[str, List[List[float]]] = {
    # Standard RGB stripe - alternating R, G, B vertical stripes
    "rgb": [
        [1.0, 0.0, 0.0],  # Red
        [0.0, 1.0, 0.0],  # Green
        [0.0, 0.0, 1.0],  # Blue
    ],
    # BGR stripe - opposite order
    "bgr": [
        [0.0, 0.0, 1.0],  # Blue
        [0.0, 1.0, 0.0],  # Green
        [1.0, 0.0, 0.0],  # Red
    ],
}

# Aperture grille pattern dimensions (Sony Trinitron style)
# Vertical RGB stripes with fine spacing
APERTURE_GRILLE_PATTERN = {
    "stripe_width": 1,  # Each RGB stripe is 1 pixel
    "gap_width": 0,     # No gap between stripes (continuous)
    "support_lines": 2,  # Damper wire positions (horizontal)
}


# =============================================================================
# Mask Generation Functions
# =============================================================================

def create_rgb_stripe_mask(
    width: int,
    height: int,
    pattern: str = "rgb",
    scale: float = 1.0
) -> "np.ndarray":
    """
    Create RGB stripe phosphor mask.

    Generates a mask representing RGB or BGR vertical stripes,
    the most common phosphor pattern in consumer CRTs.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        pattern: "rgb" or "bgr"
        scale: Scale factor for stripe width

    Returns:
        3D numpy array (H, W, 3) with mask multipliers
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask generation")

    # Get pattern definition
    if pattern not in PHOSPHOR_PATTERNS:
        pattern = "rgb"

    stripe_pattern = PHOSPHOR_PATTERNS[pattern]
    pattern_length = len(stripe_pattern)
    stripe_width = max(1, int(scale))

    # Create mask array
    mask = np.ones((height, width, 3), dtype=np.float32)

    for x in range(width):
        # Determine which stripe we're on
        stripe_index = (x // stripe_width) % pattern_length
        stripe_color = stripe_pattern[stripe_index]

        # Apply color multipliers
        mask[:, x, 0] = stripe_color[0]
        mask[:, x, 1] = stripe_color[1]
        mask[:, x, 2] = stripe_color[2]

    return mask


def create_aperture_grille_mask(
    width: int,
    height: int,
    scale: float = 1.0
) -> "np.ndarray":
    """
    Create Trinitron-style aperture grille mask.

    Sony's aperture grille uses continuous vertical RGB stripes
    without the horizontal gaps of traditional shadow masks.
    This produces a brighter, sharper image with visible
    horizontal "damper wires" that support the grille.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        scale: Scale factor for stripe width

    Returns:
        3D numpy array (H, W, 3) with mask multipliers
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask generation")

    stripe_width = max(1, int(scale))

    # Create base RGB stripe pattern
    mask = np.ones((height, width, 3), dtype=np.float32)

    for x in range(width):
        # Aperture grille uses continuous RGB stripes
        stripe_index = (x // stripe_width) % 3

        # Slightly more visible gaps than simple stripes
        if (x // stripe_width) % 3 == 0:
            mask[:, x, 0] = 1.0
            mask[:, x, 1] = 0.1
            mask[:, x, 2] = 0.1
        elif (x // stripe_width) % 3 == 1:
            mask[:, x, 0] = 0.1
            mask[:, x, 1] = 1.0
            mask[:, x, 2] = 0.1
        else:
            mask[:, x, 0] = 0.1
            mask[:, x, 1] = 0.1
            mask[:, x, 2] = 1.0

    # Add horizontal damper wire lines (subtle)
    # Trinitrons typically have 1-2 damper wires
    num_damper_wires = 2
    wire_positions = [height // 3, 2 * height // 3]
    wire_width = max(1, int(scale * 0.5))

    for pos in wire_positions:
        if 0 <= pos < height:
            # Damper wires appear as very subtle horizontal lines
            start = max(0, pos - wire_width // 2)
            end = min(height, pos + wire_width // 2 + 1)
            mask[start:end, :, :] *= 0.95

    return mask


def create_slot_mask(
    width: int,
    height: int,
    scale: float = 1.0,
    slot_width: int = 2,
    slot_height: int = 4
) -> "np.ndarray":
    """
    Create standard CRT slot mask.

    Slot masks use rectangular slots arranged in a pattern that
    allows more light through than shadow masks while still
    separating the RGB phosphors. Common in later CRT televisions.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        scale: Scale factor for overall pattern
        slot_width: Width of each slot
        slot_height: Height of each slot

    Returns:
        3D numpy array (H, W, 3) with mask multipliers
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask generation")

    # Scale slot dimensions
    sw = max(1, int(slot_width * scale))
    sh = max(1, int(slot_height * scale))

    # Create mask
    mask = np.ones((height, width, 3), dtype=np.float32)

    # Slot mask pattern: rectangular slots in staggered rows
    # Each slot group contains R, G, B slots
    group_width = sw * 3
    group_height = sh

    for y in range(height):
        for x in range(width):
            # Position within group
            gx = x % group_width
            gy = y % group_height

            # Determine which color slot
            color_index = (gx // sw) % 3

            # Check if we're in a slot or mask area
            # Slots are slightly smaller than full area
            slot_margin_x = sw // 4
            slot_margin_y = sh // 4

            in_slot_x = slot_margin_x < (gx % sw) < sw - slot_margin_x
            in_slot_y = slot_margin_y < gy < sh - slot_margin_y

            if in_slot_x and in_slot_y:
                # Inside slot - full color for this channel
                if color_index == 0:
                    mask[y, x, :] = [1.0, 0.1, 0.1]
                elif color_index == 1:
                    mask[y, x, :] = [0.1, 1.0, 0.1]
                else:
                    mask[y, x, :] = [0.1, 0.1, 1.0]
            else:
                # In mask area - dark
                mask[y, x, :] = 0.15

    return mask


def create_shadow_mask(
    width: int,
    height: int,
    scale: float = 1.0
) -> "np.ndarray":
    """
    Create delta pattern shadow mask.

    Shadow masks use a triangular/delta pattern of round holes,
    common in older and professional CRT monitors. The delta
    arrangement provides good color convergence.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        scale: Scale factor for hole size

    Returns:
        3D numpy array (H, W, 3) with mask multipliers
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask generation")

    # Delta pattern parameters
    hole_spacing = max(3, int(6 * scale))
    hole_radius = max(1, int(2 * scale))

    # Create mask
    mask = np.ones((height, width, 3), dtype=np.float32)

    # Generate delta pattern positions
    # Delta pattern has staggered rows
    for row in range(-1, height // hole_spacing + 2):
        y_center = row * hole_spacing
        x_offset = (row % 2) * (hole_spacing // 2)  # Stagger

        for col in range(-1, width // hole_spacing + 2):
            x_center = col * hole_spacing + x_offset

            # Draw circular hole
            for dy in range(-hole_radius, hole_radius + 1):
                for dx in range(-hole_radius, hole_radius + 1):
                    if dx * dx + dy * dy <= hole_radius * hole_radius:
                        x = x_center + dx
                        y = y_center + dy

                        if 0 <= x < width and 0 <= y < height:
                            # Determine color based on position in trio
                            # Delta pattern groups holes in triangles
                            group_y = row // 2
                            group_x = col // 3
                            pos_in_group = col % 3

                            if pos_in_group == 0:
                                mask[y, x, :] = [1.0, 0.15, 0.15]
                            elif pos_in_group == 1:
                                mask[y, x, :] = [0.15, 1.0, 0.15]
                            else:
                                mask[y, x, :] = [0.15, 0.15, 1.0]

    # Invert - holes should be bright, mask should be dark
    mask = np.where(mask > 0.5, 1.0, 0.2).astype(np.float32)

    return mask


def create_phosphor_mask(
    width: int,
    height: int,
    config: PhosphorConfig
) -> "np.ndarray":
    """
    Create phosphor mask based on configuration.

    Main entry point for phosphor mask generation. Selects
    appropriate mask function based on pattern type.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        config: Phosphor configuration

    Returns:
        3D numpy array (H, W, 3) with mask multipliers
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask generation")

    if not config.enabled:
        return np.ones((height, width, 3), dtype=np.float32)

    pattern = config.pattern
    scale = config.scale

    if pattern in ("rgb", "bgr"):
        mask = create_rgb_stripe_mask(width, height, pattern, scale)
    elif pattern == "aperture_grille":
        mask = create_aperture_grille_mask(width, height, scale)
    elif pattern == "slot_mask":
        mask = create_slot_mask(
            width, height, scale,
            config.slot_width, config.slot_height
        )
    elif pattern == "shadow_mask":
        mask = create_shadow_mask(width, height, scale)
    else:
        # Default to RGB stripe
        mask = create_rgb_stripe_mask(width, height, "rgb", scale)

    return mask


# =============================================================================
# Phosphor Mask Application
# =============================================================================

def apply_phosphor_mask(image: Any, config: PhosphorConfig) -> Any:
    """
    Apply phosphor mask effect to image.

    Takes an image and applies the phosphor mask pattern,
    simulating the RGB subpixel structure of CRT displays.

    Args:
        image: PIL Image or numpy array (H, W, C)
        config: Phosphor configuration

    Returns:
        Image with phosphor mask applied (same type as input)
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask effects")

    if not config.enabled:
        return image

    # Convert PIL Image to numpy if needed
    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()
        if arr.max() > 1.0:
            arr = arr / 255.0

    height, width = arr.shape[:2]

    # Create phosphor mask
    mask = create_phosphor_mask(width, height, config)

    # Apply intensity blending
    intensity = config.intensity
    blended_mask = (1.0 - intensity) + mask * intensity

    # Apply mask to image
    if len(arr.shape) == 3:
        arr = arr * blended_mask
    else:
        # Grayscale - apply to all channels
        arr = arr[:, :, np.newaxis] * blended_mask
        arr = arr[:, :, 0]  # Back to grayscale

    # Clip to valid range
    arr = np.clip(arr, 0, 1)

    # Convert back to PIL if needed
    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    return arr


def apply_phosphor_mask_fast(image: Any, config: PhosphorConfig) -> Any:
    """
    Fast phosphor mask application using simplified pattern.

    A faster approximation that creates a simpler pattern,
    useful for real-time or batch processing.

    Args:
        image: PIL Image or numpy array
        config: Phosphor configuration

    Returns:
        Image with phosphor mask applied
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for phosphor mask effects")

    if not config.enabled:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    height, width = arr.shape[:2]
    scale = max(1, int(config.scale))

    # Fast pattern: simple RGB stripe modulation
    intensity = config.intensity

    # Create column pattern
    if config.pattern in ("rgb", "aperture_grille"):
        # R, G, B, R, G, B...
        pattern = np.array([
            [1.0, 0.15, 0.15],
            [0.15, 1.0, 0.15],
            [0.15, 0.15, 1.0],
        ])
    elif config.pattern == "bgr":
        pattern = np.array([
            [0.15, 0.15, 1.0],
            [0.15, 1.0, 0.15],
            [1.0, 0.15, 0.15],
        ])
    else:
        # Default pattern
        pattern = np.array([
            [1.0, 0.2, 0.2],
            [0.2, 1.0, 0.2],
            [0.2, 0.2, 1.0],
        ])

    # Tile pattern across width
    num_repeats = (width // scale) + 1
    row_mask = np.tile(pattern, (num_repeats, 1))[:width]
    row_mask = np.repeat(row_mask, scale, axis=0)[:width]

    # Blend with intensity
    blended_mask = (1.0 - intensity) + row_mask * intensity

    # Apply to image
    if len(arr.shape) == 3:
        arr = arr * blended_mask[np.newaxis, :, :]
    else:
        arr = arr * blended_mask[:, 0][:, np.newaxis]

    arr = np.clip(arr, 0, 1)

    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    return arr


# =============================================================================
# Utility Functions
# =============================================================================

def get_phosphor_brightness_factor(config: PhosphorConfig) -> float:
    """
    Calculate the brightness factor from phosphor mask.

    Phosphor masks reduce overall brightness because they
    block some light. This calculates the approximate factor.

    Args:
        config: Phosphor configuration

    Returns:
        Brightness factor (0-1)
    """
    if not config.enabled:
        return 1.0

    intensity = config.intensity
    pattern = config.pattern

    # Approximate brightness loss per pattern
    # These are estimates based on typical mask designs
    pattern_factors = {
        "rgb": 0.7,      # ~70% light passes
        "bgr": 0.7,
        "aperture_grille": 0.8,  # More efficient
        "slot_mask": 0.75,
        "shadow_mask": 0.65,  # Least efficient
    }

    base_factor = pattern_factors.get(pattern, 0.7)

    # Blend with intensity
    return (1.0 - intensity) + intensity * base_factor


def list_phosphor_patterns() -> List[str]:
    """
    List available phosphor patterns.

    Returns:
        List of pattern names
    """
    return ["rgb", "bgr", "aperture_grille", "slot_mask", "shadow_mask"]


def get_pattern_description(pattern: str) -> str:
    """
    Get description for a phosphor pattern.

    Args:
        pattern: Pattern name

    Returns:
        Human-readable description
    """
    descriptions = {
        "rgb": "Standard RGB vertical stripe pattern",
        "bgr": "BGR vertical stripe pattern (reversed)",
        "aperture_grille": "Sony Trinitron style continuous vertical stripes",
        "slot_mask": "Rectangular slots in staggered pattern",
        "shadow_mask": "Delta pattern with circular holes",
    }
    return descriptions.get(pattern, "Unknown pattern")


def estimate_mask_visibility(
    config: PhosphorConfig,
    resolution: Tuple[int, int],
    view_distance: float = 1.0
) -> float:
    """
    Estimate how visible the phosphor mask will be.

    Args:
        config: Phosphor configuration
        resolution: Screen resolution (width, height)
        view_distance: Viewing distance relative to screen height

    Returns:
        Visibility score (0-1, higher = more visible)
    """
    if not config.enabled:
        return 0.0

    # Scale affects visibility at same resolution
    scale_factor = min(1.0, config.scale / 2.0)

    # Higher resolution = less visible at same size
    resolution_factor = min(1.0, 1080 / max(resolution[1], 480))

    # Distance affects visibility
    distance_factor = min(1.0, 1.0 / max(view_distance, 0.1))

    # Intensity obviously affects visibility
    intensity_factor = config.intensity

    # Combine factors
    visibility = (
        scale_factor * 0.2 +
        resolution_factor * 0.2 +
        distance_factor * 0.3 +
        intensity_factor * 0.3
    )

    return min(1.0, visibility)
