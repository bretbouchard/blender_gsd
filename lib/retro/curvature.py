"""
Screen Curvature Module

Implements authentic CRT screen curvature effects, including barrel distortion
and vignette effects from curved CRT glass.

Older CRTs had more pronounced curvature, while later models (especially
Trinitron) were flatter. The curvature creates characteristic edge distortion
and vignetting.

Example Usage:
    from lib.retro.curvature import apply_curvature, apply_vignette
    from lib.retro.crt_types import CurvatureConfig

    config = CurvatureConfig(enabled=True, amount=0.1, vignette_amount=0.2)
    result = apply_curvature(image, config)
"""

from typing import Tuple, Optional, Any
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

from lib.retro.crt_types import CurvatureConfig


# =============================================================================
# UV Coordinate Transformation
# =============================================================================

def calculate_curved_uv(
    u: float,
    v: float,
    amount: float,
    aspect_ratio: float = 1.0
) -> Tuple[float, float]:
    """
    Calculate curved screen UV coordinates using barrel distortion.

    Barrel distortion pushes the corners outward, simulating the
    curved glass surface of CRT displays.

    Args:
        u: Horizontal coordinate (0-1, center = 0.5)
        v: Vertical coordinate (0-1, center = 0.5)
        amount: Distortion amount (0-1)
        aspect_ratio: Width/height ratio for proper distortion

    Returns:
        Tuple of (new_u, new_v) coordinates
    """
    if amount == 0:
        return u, v

    # Convert to centered coordinates (-1 to 1)
    x = (u - 0.5) * 2.0
    y = (v - 0.5) * 2.0

    # Apply aspect ratio correction
    x = x * aspect_ratio

    # Calculate distance from center
    r = math.sqrt(x * x + y * y)

    if r == 0:
        return u, v

    # Barrel distortion formula
    # r' = r * (1 + k * r^2)
    # where k is the distortion coefficient
    k = amount * 0.5  # Scale to reasonable range

    # Apply barrel distortion
    r_distorted = r * (1.0 + k * r * r)

    # Normalize back to unit circle
    if r_distorted > 0:
        factor = r_distorted / r
        x_distorted = x * factor
        y_distorted = y * factor
    else:
        x_distorted = x
        y_distorted = y

    # Correct aspect ratio
    x_distorted = x_distorted / aspect_ratio

    # Convert back to 0-1 range
    new_u = (x_distorted + 1.0) * 0.5
    new_v = (y_distorted + 1.0) * 0.5

    return new_u, new_v


def calculate_barrel_distortion_grid(
    width: int,
    height: int,
    amount: float
) -> Tuple["np.ndarray", "np.ndarray"]:
    """
    Calculate full grid of UV distortion offsets.

    Pre-computes the distortion mapping for the entire image,
    useful for efficient image transformation.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        amount: Distortion amount (0-1)

    Returns:
        Tuple of (u_map, v_map) coordinate arrays
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for curvature effects")

    aspect_ratio = width / height if height > 0 else 1.0

    # Create coordinate grids
    y_coords, x_coords = np.mgrid[0:height, 0:width]

    # Normalize to 0-1
    u = x_coords / (width - 1) if width > 1 else np.zeros_like(x_coords)
    v = y_coords / (height - 1) if height > 1 else np.zeros_like(y_coords)

    # Convert to centered coordinates (-1 to 1)
    x = (u - 0.5) * 2.0
    y = (v - 0.5) * 2.0

    # Apply aspect ratio
    x = x * aspect_ratio

    # Calculate distance from center
    r = np.sqrt(x * x + y * y)

    # Barrel distortion
    k = amount * 0.5
    r_distorted = r * (1.0 + k * r * r)

    # Apply distortion
    with np.errstate(invalid='ignore', divide='ignore'):
        factor = np.where(r > 0, r_distorted / r, 1.0)
    x_distorted = x * factor
    y_distorted = y * factor

    # Correct aspect ratio
    x_distorted = x_distorted / aspect_ratio

    # Convert back to 0-1 range
    u_map = (x_distorted + 1.0) * 0.5
    v_map = (y_distorted + 1.0) * 0.5

    return u_map, v_map


# =============================================================================
# Vignette Effect
# =============================================================================

def create_vignette_mask(
    width: int,
    height: int,
    amount: float,
    corner_radius: int = 0
) -> "np.ndarray":
    """
    Create vignette (edge darkening) mask.

    Vignetting simulates the natural darkening at the edges
    of curved CRT displays due to viewing angle.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        amount: Vignette intensity (0-1)
        corner_radius: Rounded corner radius in pixels

    Returns:
        2D numpy array of brightness multipliers
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for vignette effects")

    if amount == 0:
        return np.ones((height, width), dtype=np.float32)

    # Create coordinate grids (0 to 1)
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    y_norm = y_coords / (height - 1) if height > 1 else np.zeros_like(y_coords)
    x_norm = x_coords / (width - 1) if width > 1 else np.zeros_like(x_coords)

    # Distance from center (0 to ~0.7 for corners)
    x_centered = x_norm - 0.5
    y_centered = y_norm - 0.5
    distance = np.sqrt(x_centered * x_centered + y_centered * y_centered)

    # Apply vignette falloff
    # Start darkening from center, increase toward edges
    # Use smooth falloff curve
    vignette = 1.0 - (distance * 2.0 * amount) ** 2
    vignette = np.clip(vignette, 0.0, 1.0)

    # Apply rounded corners if specified
    if corner_radius > 0:
        corner_mask = create_corner_mask(width, height, corner_radius)
        vignette = vignette * corner_mask

    return vignette.astype(np.float32)


def create_corner_mask(
    width: int,
    height: int,
    corner_radius: int
) -> "np.ndarray":
    """
    Create rounded corner mask.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        corner_radius: Corner radius in pixels

    Returns:
        2D numpy array (1 inside corners, 0 outside)
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for corner mask")

    if corner_radius <= 0:
        return np.ones((height, width), dtype=np.float32)

    mask = np.ones((height, width), dtype=np.float32)

    # Use vectorized approach for efficiency
    y_coords, x_coords = np.ogrid[:height, :width]
    r = corner_radius
    r_sq = r * r

    # Top-left corner (only in the r x r region)
    tl_region = (x_coords < r) & (y_coords < r)
    tl_dist_sq = x_coords * x_coords + y_coords * y_coords
    mask = np.where(tl_region & (tl_dist_sq > r_sq), 0.0, mask)

    # Top-right corner
    tr_x = width - 1 - x_coords
    tr_region = (tr_x < r) & (y_coords < r)
    tr_dist_sq = tr_x * tr_x + y_coords * y_coords
    mask = np.where(tr_region & (tr_dist_sq > r_sq), 0.0, mask)

    # Bottom-left corner
    bl_y = height - 1 - y_coords
    bl_region = (x_coords < r) & (bl_y < r)
    bl_dist_sq = x_coords * x_coords + bl_y * bl_y
    mask = np.where(bl_region & (bl_dist_sq > r_sq), 0.0, mask)

    # Bottom-right corner
    br_region = (tr_x < r) & (bl_y < r)
    br_dist_sq = tr_x * tr_x + bl_y * bl_y
    mask = np.where(br_region & (br_dist_sq > r_sq), 0.0, mask)

    return mask.astype(np.float32)


def apply_vignette(image: Any, amount: float, corner_radius: int = 0) -> Any:
    """
    Apply vignette effect to image.

    Args:
        image: PIL Image or numpy array
        amount: Vignette intensity (0-1)
        corner_radius: Rounded corner radius

    Returns:
        Image with vignette applied
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for vignette effects")

    if amount == 0 and corner_radius == 0:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()

    height, width = arr.shape[:2]

    # Create vignette mask
    vignette = create_vignette_mask(width, height, amount, corner_radius)

    # Apply to image
    if len(arr.shape) == 3:
        arr = arr * vignette[:, :, np.newaxis]
    else:
        arr = arr * vignette

    arr = np.clip(arr, 0, 1)

    if is_pil:
        return Image.fromarray((arr * 255).astype(np.uint8))
    return arr


# =============================================================================
# Main Curvature Application
# =============================================================================

def apply_curvature(image: Any, config: CurvatureConfig) -> Any:
    """
    Apply screen curvature distortion to image.

    Applies barrel distortion and optional vignette effect
    to simulate curved CRT display.

    Args:
        image: PIL Image or numpy array
        config: Curvature configuration

    Returns:
        Image with curvature applied
    """
    if not HAS_PIL:
        raise ImportError("PIL and numpy required for curvature effects")

    if not config.enabled:
        return image

    is_pil = isinstance(image, Image.Image)
    if is_pil:
        arr = np.array(image).astype(np.float32) / 255.0
    else:
        arr = image.astype(np.float32) if image.dtype != np.float32 else image.copy()
        if arr.max() > 1.0:
            arr = arr / 255.0

    height, width = arr.shape[:2]

    # Calculate distortion grid
    u_map, v_map = calculate_barrel_distortion_grid(width, height, config.amount)

    # Sample from original image using distorted coordinates
    # Convert to pixel indices
    u_pixels = np.clip(u_map * (width - 1), 0, width - 1).astype(np.float32)
    v_pixels = np.clip(v_map * (height - 1), 0, height - 1).astype(np.float32)

    # Bilinear interpolation sampling
    result = bilinear_sample(arr, u_pixels, v_pixels)

    # Apply vignette
    if config.vignette_amount > 0 or config.corner_radius > 0:
        vignette = create_vignette_mask(width, height, config.vignette_amount, config.corner_radius)
        if len(result.shape) == 3:
            result = result * vignette[:, :, np.newaxis]
        else:
            result = result * vignette

    # Apply border
    if config.border_size > 0:
        result = apply_border(result, config.border_size)

    result = np.clip(result, 0, 1)

    if is_pil:
        return Image.fromarray((result * 255).astype(np.uint8))
    return result


def bilinear_sample(
    image: "np.ndarray",
    u_pixels: "np.ndarray",
    v_pixels: "np.ndarray"
) -> "np.ndarray":
    """
    Bilinear interpolation sampling from image.

    Args:
        image: Source image array
        u_pixels: X coordinate array
        v_pixels: Y coordinate array

    Returns:
        Sampled image array
    """
    height, width = image.shape[:2]

    # Get integer and fractional parts
    u0 = np.floor(u_pixels).astype(np.int32)
    v0 = np.floor(v_pixels).astype(np.int32)
    u1 = np.minimum(u0 + 1, width - 1)
    v1 = np.minimum(v0 + 1, height - 1)

    # Clamp to valid range
    u0 = np.clip(u0, 0, width - 1)
    v0 = np.clip(v0, 0, height - 1)

    # Fractional parts
    fu = u_pixels - u0
    fv = v_pixels - v0

    # Sample four corners
    if len(image.shape) == 3:
        # Color image
        p00 = image[v0, u0, :]
        p01 = image[v0, u1, :]
        p10 = image[v1, u0, :]
        p11 = image[v1, u1, :]

        # Bilinear interpolation
        fu = fu[:, :, np.newaxis]
        fv = fv[:, :, np.newaxis]

        result = (
            p00 * (1 - fu) * (1 - fv) +
            p01 * fu * (1 - fv) +
            p10 * (1 - fu) * fv +
            p11 * fu * fv
        )
    else:
        # Grayscale
        p00 = image[v0, u0]
        p01 = image[v0, u1]
        p10 = image[v1, u0]
        p11 = image[v1, u1]

        result = (
            p00 * (1 - fu) * (1 - fv) +
            p01 * fu * (1 - fv) +
            p10 * (1 - fu) * fv +
            p11 * fu * fv
        )

    return result


def apply_border(image: "np.ndarray", border_size: int) -> "np.ndarray":
    """
    Apply black border around image.

    Args:
        image: Image array
        border_size: Border size in pixels

    Returns:
        Image with border applied
    """
    if border_size <= 0:
        return image

    height, width = image.shape[:2]

    # Create mask for border
    border_mask = np.ones((height, width), dtype=np.float32)
    border_mask[:border_size, :] = 0
    border_mask[-border_size:, :] = 0
    border_mask[:, :border_size] = 0
    border_mask[:, -border_size:] = 0

    # Apply border
    if len(image.shape) == 3:
        image = image * border_mask[:, :, np.newaxis]
    else:
        image = image * border_mask

    return image


def combine_curvature_vignette(
    image: Any,
    curvature: float,
    vignette: float
) -> Any:
    """
    Apply both curvature and vignette in one pass.

    Optimized function that applies both effects together.

    Args:
        image: PIL Image or numpy array
        curvature: Curvature amount (0-1)
        vignette: Vignette amount (0-1)

    Returns:
        Image with both effects applied
    """
    config = CurvatureConfig(
        enabled=True,
        amount=curvature,
        vignette_amount=vignette
    )
    return apply_curvature(image, config)


# =============================================================================
# Utility Functions
# =============================================================================

def calculate_edge_stretch(amount: float, aspect_ratio: float = 1.0) -> float:
    """
    Calculate the maximum edge stretching from curvature.

    Args:
        amount: Curvature amount (0-1)
        aspect_ratio: Image aspect ratio

    Returns:
        Maximum stretch factor at corners
    """
    if amount == 0:
        return 1.0

    # Maximum distortion at corners (r = sqrt(2) / 2)
    r = math.sqrt(2) / 2
    k = amount * 0.5
    r_distorted = r * (1.0 + k * r * r)

    return r_distorted / r if r > 0 else 1.0


def estimate_content_loss(amount: float) -> float:
    """
    Estimate percentage of content lost at edges due to curvature.

    Args:
        amount: Curvature amount (0-1)

    Returns:
        Fraction of content that falls outside frame (0-1)
    """
    if amount == 0:
        return 0.0

    # Approximate content loss based on corner displacement
    # At max curvature (~0.3), about 10-15% is lost
    # Use exponential approximation
    return min(1.0, amount * 0.5)


def recommend_border_size(
    width: int,
    height: int,
    amount: float
) -> int:
    """
    Recommend border size to hide edge artifacts from curvature.

    Args:
        width: Image width
        height: Image height
        amount: Curvature amount

    Returns:
        Recommended border size in pixels
    """
    if amount == 0:
        return 0

    # Border should be proportional to image size and curvature
    min_dim = min(width, height)
    border = int(min_dim * amount * 0.05)

    return max(0, min(border, min_dim // 10))
