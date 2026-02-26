"""
Calibration pattern generation for physical projector alignment.

Creates test patterns (checkerboard, color bars, grid, etc.) at specified resolutions.
"""

from typing import Tuple, Optional
import math

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .types import CalibrationPattern, PatternType


def generate_checkerboard_pattern(
    resolution: Tuple[int, int],
    grid_size: int = 8,
    primary_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    secondary_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> 'Image':
    """
    Generate checkerboard calibration pattern.

    Args:
        resolution: (width, height) in pixels
        grid_size: Number of squares per row (and column for square cells)
        primary_color: First color (RGB, 0-1 range)
        secondary_color: Second color (RGB, 0-1 range)

    Returns:
        PIL Image object
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow required for pattern generation. Install with: pip install Pillow")

    width, height = resolution

    # Calculate square size (use smaller dimension for square cells)
    square_width = width // grid_size
    square_height = height // grid_size
    square_size = min(square_width, square_height)

    # Create image
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Convert colors to 0-255 range
    color1 = tuple(int(c * 255) for c in primary_color)
    color2 = tuple(int(c * 255) for c in secondary_color)

    # Draw checkerboard
    for row in range(grid_size + 1):
        for col in range(grid_size + 1):
            x = col * square_size
            y = row * square_size

            # Alternate colors
            if (row + col) % 2 == 0:
                color = color1
            else:
                color = color2

            draw.rectangle(
                [x, y, x + square_size, y + square_size],
                fill=color
            )

    return img


def generate_color_bars_pattern(
    resolution: Tuple[int, int],
    smpte: bool = True
) -> 'Image':
    """
    Generate SMPTE or ARIB color bars for color calibration.

    Args:
        resolution: (width, height) in pixels
        smpte: True for SMPTE bars, False for simplified ARIB bars

    Returns:
        PIL Image object
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow required for pattern generation. Install with: pip install Pillow")

    width, height = resolution

    # Create image
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    if smpte:
        # SMPTE color bars (standard 7-color + bottom section)
        # Top section: 7 color bars (75% height)
        top_height = int(height * 0.67)
        bar_width = width // 7

        # SMPTE colors (RGB, 0-255)
        colors = [
            (192, 192, 192),  # 75% White (Gray)
            (192, 192, 0),    # Yellow
            (0, 192, 192),    # Cyan
            (0, 192, 0),      # Green
            (192, 0, 192),    # Magenta
            (192, 0, 0),      # Red
            (0, 0, 192),      # Blue
        ]

        for i, color in enumerate(colors):
            x = i * bar_width
            draw.rectangle([x, 0, x + bar_width, top_height], fill=color)

        # Middle section: -I, white, +Q, black sections
        middle_height = int(height * 0.08)
        middle_y = top_height

        # -I (dark blue-purple)
        draw.rectangle([0, middle_y, width // 4, middle_y + middle_height], fill=(0, 0, 74))
        # White
        draw.rectangle([width // 4, middle_y, width // 2, middle_y + middle_height], fill=(255, 255, 255))
        # +Q (dark purple)
        draw.rectangle([width // 2, middle_y, 3 * width // 4, middle_y + middle_height], fill=(0, 0, 0))
        # Black
        draw.rectangle([3 * width // 4, middle_y, width, middle_y + middle_height], fill=(0, 0, 0))

        # Bottom section: PLUGE (Picture Line Up Generation Equipment)
        bottom_y = middle_y + middle_height
        bottom_height = height - bottom_y

        # -4% black, 0% black, +4% black sections
        pluge_width = width // 3
        draw.rectangle([0, bottom_y, pluge_width, height], fill=(6, 6, 6))       # +4%
        draw.rectangle([pluge_width, bottom_y, 2 * pluge_width, height], fill=(0, 0, 0))  # 0%
        draw.rectangle([2 * pluge_width, bottom_y, width, height], fill=(12, 12, 12))   # +4%

    else:
        # Simplified ARIB color bars (full height)
        bar_width = width // 8
        colors = [
            (255, 255, 255),  # White
            (255, 255, 0),    # Yellow
            (0, 255, 255),    # Cyan
            (0, 255, 0),      # Green
            (255, 0, 255),    # Magenta
            (255, 0, 0),      # Red
            (0, 0, 255),      # Blue
            (0, 0, 0),        # Black
        ]

        for i, color in enumerate(colors):
            x = i * bar_width
            draw.rectangle([x, 0, x + bar_width, height], fill=color)

    return img


def generate_grid_pattern(
    resolution: Tuple[int, int],
    spacing: int = 100,
    line_width: int = 2,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    background: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> 'Image':
    """
    Generate grid pattern for alignment.

    Args:
        resolution: (width, height) in pixels
        spacing: Grid cell spacing in pixels
        line_width: Line width in pixels
        color: Grid line color (RGB, 0-1 range)
        background: Background color (RGB, 0-1 range)

    Returns:
        PIL Image object
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow required for pattern generation. Install with: pip install Pillow")

    width, height = resolution

    # Convert colors to 0-255 range
    line_color = tuple(int(c * 255) for c in color)
    bg_color = tuple(int(c * 255) for c in background)

    # Create image with background
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw vertical lines
    for x in range(0, width, spacing):
        for offset in range(line_width):
            draw.line([(x + offset, 0), (x + offset, height)], fill=line_color)

    # Draw horizontal lines
    for y in range(0, height, spacing):
        for offset in range(line_width):
            draw.line([(0, y + offset), (width, y + offset)], fill=line_color)

    return img


def generate_crosshair_pattern(
    resolution: Tuple[int, int],
    line_width: int = 2,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    background: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> 'Image':
    """
    Generate crosshair pattern for center alignment.

    Args:
        resolution: (width, height) in pixels
        line_width: Line width in pixels
        color: Crosshair color (RGB, 0-1 range)
        background: Background color (RGB, 0-1 range)

    Returns:
        PIL Image object
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow required for pattern generation. Install with: pip install Pillow")

    width, height = resolution
    center_x, center_y = width // 2, height // 2

    # Convert colors to 0-255 range
    line_color = tuple(int(c * 255) for c in color)
    bg_color = tuple(int(c * 255) for c in background)

    # Create image with background
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw horizontal line
    for offset in range(-line_width // 2, line_width // 2 + 1):
        draw.line([(0, center_y + offset), (width, center_y + offset)], fill=line_color)

    # Draw vertical line
    for offset in range(-line_width // 2, line_width // 2 + 1):
        draw.line([(center_x + offset, 0), (center_x + offset, height)], fill=line_color)

    # Draw center circle
    circle_radius = min(width, height) // 20
    draw.ellipse(
        [center_x - circle_radius, center_y - circle_radius,
         center_x + circle_radius, center_y + circle_radius],
        outline=line_color,
        width=line_width
    )

    return img


def generate_gradient_pattern(
    resolution: Tuple[int, int],
    horizontal: bool = True,
    start_color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    end_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> 'Image':
    """
    Generate gradient pattern for brightness/linearity testing.

    Args:
        resolution: (width, height) in pixels
        horizontal: True for horizontal gradient, False for vertical
        start_color: Starting color (RGB, 0-1 range)
        end_color: Ending color (RGB, 0-1 range)

    Returns:
        PIL Image object
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow required for pattern generation. Install with: pip install Pillow")

    width, height = resolution

    # Create image
    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            # Calculate interpolation factor
            if horizontal:
                t = x / (width - 1) if width > 1 else 0
            else:
                t = y / (height - 1) if height > 1 else 0

            # Interpolate colors
            r = int((start_color[0] + t * (end_color[0] - start_color[0])) * 255)
            g = int((start_color[1] + t * (end_color[1] - start_color[1])) * 255)
            b = int((start_color[2] + t * (end_color[2] - start_color[2])) * 255)

            pixels[x, y] = (r, g, b)

    return img


def generate_pattern(config: CalibrationPattern) -> 'Image':
    """
    Generate calibration pattern from configuration.

    Args:
        config: CalibrationPattern configuration

    Returns:
        PIL Image object
    """
    if config.pattern_type == PatternType.CHECKERBOARD:
        return generate_checkerboard_pattern(
            resolution=config.resolution,
            grid_size=config.grid_size,
            primary_color=config.primary_color,
            secondary_color=config.secondary_color,
        )
    elif config.pattern_type == PatternType.COLOR_BARS:
        return generate_color_bars_pattern(
            resolution=config.resolution,
            smpte=config.smpte_standard,
        )
    elif config.pattern_type == PatternType.GRID:
        return generate_grid_pattern(
            resolution=config.resolution,
            spacing=config.spacing,
            line_width=config.line_width,
            color=config.primary_color,
            background=config.secondary_color,
        )
    elif config.pattern_type == PatternType.CROSSHAIR:
        return generate_crosshair_pattern(
            resolution=config.resolution,
            line_width=config.line_width,
            color=config.primary_color,
            background=config.secondary_color,
        )
    elif config.pattern_type == PatternType.GRADIENT:
        return generate_gradient_pattern(
            resolution=config.resolution,
            horizontal=True,
            start_color=config.secondary_color,
            end_color=config.primary_color,
        )
    else:
        raise ValueError(f"Unknown pattern type: {config.pattern_type}")


def save_pattern(image: 'Image', filepath: str, format: str = 'PNG'):
    """
    Save pattern image to file.

    Args:
        image: PIL Image object
        filepath: Output file path
        format: Image format (PNG, JPEG, etc.)
    """
    image.save(filepath, format=format)
