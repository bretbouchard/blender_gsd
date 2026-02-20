"""
Pixel Art Types for Retro Style Conversion

Defines dataclasses for pixel art conversion, color quantization,
and retro console style emulation.

All classes designed for YAML serialization via to_dict() and
deserialization via from_dict() class methods.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import time


class PixelMode(str, Enum):
    """Pixel art style modes."""
    PHOTOREALISTIC = "photorealistic"  # High color, smooth
    STYLIZED = "stylized"              # Artistically modified
    BIT_32 = "32bit"                   # Modern pixel art
    BIT_16 = "16bit"                   # SNES/Genesis era
    BIT_8 = "8bit"                     # NES/Master System
    BIT_4 = "4bit"                     # Game Boy era
    BIT_2 = "2bit"                     # Early LCD
    BIT_1 = "1bit"                     # Pure black/white


class AspectRatioMode(str, Enum):
    """Aspect ratio handling modes."""
    PRESERVE = "preserve"    # Maintain original aspect ratio
    STRETCH = "stretch"      # Stretch to fill target
    CROP = "crop"            # Crop to fit target


class ScalingFilter(str, Enum):
    """Image scaling filter types."""
    NEAREST = "nearest"      # Pixel-perfect (no interpolation)
    BILINEAR = "bilinear"    # Smooth linear interpolation
    LANCZOS = "lanczos"      # High-quality resampling
    BOX = "box"              # Area average (good for downscaling


class DitherMode(str, Enum):
    """Dithering modes for color reduction."""
    NONE = "none"                    # No dithering
    ORDERED = "ordered"              # Bayer matrix dithering
    FLOYD_STEINBERG = "floyd_steinberg"  # Error diffusion
    ATKINSON = "atkinson"            # Bill Atkinson dithering
    RANDOM = "random"                # Random noise dithering


class SubPixelLayout(str, Enum):
    """LCD sub-pixel layouts for simulation."""
    RGB = "rgb"      # Standard LCD
    BGR = "bgr"      # Some LCD panels
    NONE = "none"    # No sub-pixel simulation


@dataclass
class PixelStyle:
    """
    Pixel art style configuration.

    Defines the visual characteristics of pixel art output including
    color depth, pixel size, edge handling, and posterization.

    Attributes:
        mode: Pixel style mode (photorealistic, stylized, 32bit, 16bit, 8bit, 4bit, 2bit, 1bit)
        pixel_size: Size of each pixel in output (1 = 1:1, 2 = 2x2 blocks)
        color_limit: Maximum number of colors in output
        preserve_edges: Whether to detect and enhance edges
        posterize_levels: Number of color levels per channel (0 = disabled)
        sub_pixel_layout: LCD sub-pixel layout for simulation
        dither_mode: Dithering mode for color reduction
        dither_strength: Dithering intensity (0.0-1.0)
    """
    mode: str = "16bit"
    pixel_size: int = 1
    color_limit: int = 256
    preserve_edges: bool = True
    posterize_levels: int = 0  # 0 = disabled
    sub_pixel_layout: str = "none"
    dither_mode: str = "none"
    dither_strength: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "pixel_size": self.pixel_size,
            "color_limit": self.color_limit,
            "preserve_edges": self.preserve_edges,
            "posterize_levels": self.posterize_levels,
            "sub_pixel_layout": self.sub_pixel_layout,
            "dither_mode": self.dither_mode,
            "dither_strength": self.dither_strength,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PixelStyle:
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "16bit"),
            pixel_size=data.get("pixel_size", 1),
            color_limit=data.get("color_limit", 256),
            preserve_edges=data.get("preserve_edges", True),
            posterize_levels=data.get("posterize_levels", 0),
            sub_pixel_layout=data.get("sub_pixel_layout", "none"),
            dither_mode=data.get("dither_mode", "none"),
            dither_strength=data.get("dither_strength", 1.0),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        valid_modes = ["photorealistic", "stylized", "32bit", "16bit", "8bit", "4bit", "2bit", "1bit"]
        if self.mode not in valid_modes:
            errors.append(f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}")

        if self.pixel_size < 1:
            errors.append(f"pixel_size must be >= 1, got {self.pixel_size}")

        if self.color_limit < 2:
            errors.append(f"color_limit must be >= 2, got {self.color_limit}")

        if self.posterize_levels < 0 or self.posterize_levels > 256:
            errors.append(f"posterize_levels must be 0-256, got {self.posterize_levels}")

        if self.dither_strength < 0 or self.dither_strength > 1:
            errors.append(f"dither_strength must be 0.0-1.0, got {self.dither_strength}")

        valid_dither = ["none", "ordered", "floyd_steinberg", "atkinson", "random"]
        if self.dither_mode not in valid_dither:
            errors.append(f"Invalid dither_mode '{self.dither_mode}'. Must be one of: {valid_dither}")

        valid_layouts = ["rgb", "bgr", "none"]
        if self.sub_pixel_layout not in valid_layouts:
            errors.append(f"Invalid sub_pixel_layout '{self.sub_pixel_layout}'. Must be one of: {valid_layouts}")

        return errors


@dataclass
class PixelationConfig:
    """
    Complete pixelation configuration.

    Brings together style settings, resolution handling, edge detection,
    and output scaling for the pixelation process.

    Attributes:
        style: Pixel style configuration
        target_resolution: Target resolution (width, height) - set to (0, 0) for auto
        aspect_ratio_mode: How to handle aspect ratio differences
        scaling_filter: Filter to use when scaling
        edge_detection: Whether to detect edges before pixelation
        edge_threshold: Edge detection sensitivity (0.0-1.0)
        edge_enhancement: Edge enhancement strength (0.0-1.0)
        output_scale: Integer scale multiplier for final output
        custom_palette: Optional custom color palette (list of RGB tuples)
        palette_name: Named preset palette to use
    """
    style: PixelStyle = field(default_factory=PixelStyle)
    target_resolution: Tuple[int, int] = (0, 0)  # (0, 0) = auto
    aspect_ratio_mode: str = "preserve"
    scaling_filter: str = "nearest"
    edge_detection: bool = True
    edge_threshold: float = 0.1
    edge_enhancement: float = 0.0
    output_scale: int = 1
    custom_palette: List[Tuple[int, int, int]] = field(default_factory=list)
    palette_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "style": self.style.to_dict(),
            "target_resolution": list(self.target_resolution),
            "aspect_ratio_mode": self.aspect_ratio_mode,
            "scaling_filter": self.scaling_filter,
            "edge_detection": self.edge_detection,
            "edge_threshold": self.edge_threshold,
            "edge_enhancement": self.edge_enhancement,
            "output_scale": self.output_scale,
            "custom_palette": [list(c) for c in self.custom_palette],
            "palette_name": self.palette_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PixelationConfig:
        """Create from dictionary."""
        style_data = data.get("style", {})
        palette_data = data.get("custom_palette", [])
        custom_palette = [tuple(c) for c in palette_data] if palette_data else []

        return cls(
            style=PixelStyle.from_dict(style_data),
            target_resolution=tuple(data.get("target_resolution", (0, 0))),
            aspect_ratio_mode=data.get("aspect_ratio_mode", "preserve"),
            scaling_filter=data.get("scaling_filter", "nearest"),
            edge_detection=data.get("edge_detection", True),
            edge_threshold=data.get("edge_threshold", 0.1),
            edge_enhancement=data.get("edge_enhancement", 0.0),
            output_scale=data.get("output_scale", 1),
            custom_palette=custom_palette,
            palette_name=data.get("palette_name", ""),
        )

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Validate style
        errors.extend(self.style.validate())

        # Validate resolution
        if self.target_resolution[0] < 0 or self.target_resolution[1] < 0:
            errors.append(f"target_resolution must be >= (0, 0), got {self.target_resolution}")

        # Validate aspect ratio mode
        valid_aspect = ["preserve", "stretch", "crop"]
        if self.aspect_ratio_mode not in valid_aspect:
            errors.append(f"Invalid aspect_ratio_mode '{self.aspect_ratio_mode}'. Must be one of: {valid_aspect}")

        # Validate scaling filter
        valid_filters = ["nearest", "bilinear", "lanczos", "box"]
        if self.scaling_filter not in valid_filters:
            errors.append(f"Invalid scaling_filter '{self.scaling_filter}'. Must be one of: {valid_filters}")

        # Validate edge settings
        if self.edge_threshold < 0 or self.edge_threshold > 1:
            errors.append(f"edge_threshold must be 0.0-1.0, got {self.edge_threshold}")

        if self.edge_enhancement < 0 or self.edge_enhancement > 1:
            errors.append(f"edge_enhancement must be 0.0-1.0, got {self.edge_enhancement}")

        # Validate output scale
        if self.output_scale < 1:
            errors.append(f"output_scale must be >= 1, got {self.output_scale}")

        return errors

    @classmethod
    def for_console(cls, console: str) -> PixelationConfig:
        """
        Create configuration preset for a specific console.

        Args:
            console: Console name (snes, nes, gameboy, pico8, mac_plus, genesis)

        Returns:
            PixelationConfig configured for that console
        """
        presets = {
            "snes": cls(
                style=PixelStyle(mode="16bit", pixel_size=2, color_limit=256, preserve_edges=True),
                target_resolution=(256, 224),
                scaling_filter="nearest",
            ),
            "nes": cls(
                style=PixelStyle(mode="8bit", pixel_size=2, color_limit=54, preserve_edges=True, posterize_levels=4),
                target_resolution=(256, 240),
                scaling_filter="nearest",
            ),
            "gameboy": cls(
                style=PixelStyle(mode="4bit", pixel_size=3, color_limit=4, preserve_edges=True),
                target_resolution=(160, 144),
                scaling_filter="nearest",
            ),
            "pico8": cls(
                style=PixelStyle(mode="8bit", pixel_size=4, color_limit=16, preserve_edges=True),
                target_resolution=(128, 128),
                scaling_filter="nearest",
            ),
            "mac_plus": cls(
                style=PixelStyle(mode="1bit", pixel_size=1, color_limit=2, preserve_edges=False),
                target_resolution=(512, 342),
                scaling_filter="nearest",
            ),
            "genesis": cls(
                style=PixelStyle(mode="16bit", pixel_size=2, color_limit=512, preserve_edges=True),
                target_resolution=(320, 224),
                scaling_filter="nearest",
            ),
            "c64": cls(
                style=PixelStyle(mode="8bit", pixel_size=2, color_limit=16, preserve_edges=True),
                target_resolution=(320, 200),
                scaling_filter="nearest",
            ),
        }
        return presets.get(console.lower(), cls())


@dataclass
class PixelationResult:
    """
    Result of pixelation process.

    Contains the processed image and metadata about the transformation.

    Attributes:
        image: Processed image (PIL Image or numpy array)
        original_resolution: Original image resolution (width, height)
        pixel_resolution: Resolution after pixelation (before output scaling)
        output_resolution: Final output resolution (after output scaling)
        color_count: Number of unique colors in output
        processing_time: Time taken for processing in seconds
        palette_used: Color palette used (if quantization applied)
        config: Configuration used for pixelation
        warnings: Any warnings generated during processing
    """
    image: Any = None
    original_resolution: Tuple[int, int] = (0, 0)
    pixel_resolution: Tuple[int, int] = (0, 0)
    output_resolution: Tuple[int, int] = (0, 0)
    color_count: int = 0
    processing_time: float = 0.0
    palette_used: List[Tuple[int, int, int]] = field(default_factory=list)
    config: Optional[PixelationConfig] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (without image data)."""
        return {
            "original_resolution": list(self.original_resolution),
            "pixel_resolution": list(self.pixel_resolution),
            "output_resolution": list(self.output_resolution),
            "color_count": self.color_count,
            "processing_time": self.processing_time,
            "palette_used": [list(c) for c in self.palette_used],
            "warnings": self.warnings,
        }


@dataclass
class ColorPalette:
    """
    Named color palette for pixel art.

    Defines a specific set of colors for palette-mapped pixel art.

    Attributes:
        name: Palette name
        colors: List of RGB color tuples
        description: Human-readable description
        source: Original source (e.g., "NES", "Game Boy", "PICO-8")
    """
    name: str = ""
    colors: List[Tuple[int, int, int]] = field(default_factory=list)
    description: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "colors": [list(c) for c in self.colors],
            "description": self.description,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ColorPalette:
        """Create from dictionary."""
        colors_data = data.get("colors", [])
        colors = [tuple(c) for c in colors_data] if colors_data else []
        return cls(
            name=data.get("name", ""),
            colors=colors,
            description=data.get("description", ""),
            source=data.get("source", ""),
        )

    def nearest_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Find nearest color in palette.

        Args:
            color: RGB color tuple to match

        Returns:
            Nearest palette color
        """
        if not self.colors:
            return color

        min_dist = float('inf')
        nearest = self.colors[0]

        for palette_color in self.colors:
            # Euclidean distance in RGB space
            dist = sum((a - b) ** 2 for a, b in zip(color, palette_color))
            if dist < min_dist:
                min_dist = dist
                nearest = palette_color

        return nearest


# =============================================================================
# BUILT-IN PALETTES - Classic console palettes
# =============================================================================

# Game Boy original palette (green monochrome)
GAMEBOY_PALETTE = ColorPalette(
    name="gameboy",
    colors=[
        (15, 56, 15),    # Darkest green
        (48, 98, 48),    # Dark green
        (139, 172, 15),  # Light green
        (155, 188, 15),  # Lightest green
    ],
    description="Original Game Boy green monochrome palette",
    source="Nintendo Game Boy",
)

# NES palette (simplified - actual NES has 54 usable colors)
NES_PALETTE = ColorPalette(
    name="nes",
    colors=[
        # Grayscale
        (0, 0, 0), (255, 255, 255), (124, 124, 124), (188, 188, 188),
        # Reds
        (188, 0, 0), (255, 0, 0), (124, 0, 0), (252, 116, 96),
        # Oranges/Yellows
        (252, 160, 68), (252, 208, 68), (188, 136, 0), (252, 232, 116),
        # Greens
        (0, 188, 0), (0, 252, 0), (0, 124, 0), (136, 252, 136),
        # Cyans
        (0, 136, 136), (0, 188, 188), (0, 88, 88), (136, 252, 232),
        # Blues
        (0, 0, 188), (0, 0, 252), (0, 0, 124), (104, 136, 252),
        # Purples
        (188, 0, 188), (252, 0, 252), (124, 0, 124), (216, 160, 252),
        # Pinks
        (252, 116, 180), (252, 168, 216),
    ],
    description="Simplified NES color palette",
    source="Nintendo Entertainment System",
)

# PICO-8 palette
PICO8_PALETTE = ColorPalette(
    name="pico8",
    colors=[
        (0, 0, 0),       # 0: Black
        (29, 43, 83),    # 1: Dark blue
        (126, 37, 83),   # 2: Dark purple
        (0, 135, 81),    # 3: Dark green
        (171, 82, 54),   # 4: Brown
        (95, 87, 79),    # 5: Dark gray
        (194, 195, 199), # 6: Light gray
        (255, 241, 232), # 7: White
        (255, 0, 77),    # 8: Red
        (255, 163, 0),   # 9: Orange
        (255, 236, 39),  # 10: Yellow
        (0, 228, 54),    # 11: Green
        (41, 173, 255),  # 12: Blue
        (131, 118, 156), # 13: Indigo
        (255, 119, 168), # 14: Pink
        (255, 204, 170), # 15: Peach
    ],
    description="PICO-8 fantasy console palette",
    source="Lexaloffle PICO-8",
)

# CGA Palette (Palette 1 - Low Intensity)
CGA_PALETTE = ColorPalette(
    name="cga",
    colors=[
        (0, 0, 0),       # Black
        (0, 170, 170),   # Cyan
        (170, 0, 170),   # Magenta
        (170, 170, 170), # White/Light Gray
    ],
    description="CGA Palette 1 (cyan/magenta)",
    source="IBM CGA",
)

# Mac Plus 1-bit (black and white only)
MACPLUS_PALETTE = ColorPalette(
    name="mac_plus",
    colors=[
        (0, 0, 0),       # Black
        (255, 255, 255), # White
    ],
    description="Macintosh Plus monochrome",
    source="Apple Macintosh Plus",
)

# EGA Palette
EGA_PALETTE = ColorPalette(
    name="ega",
    colors=[
        (0, 0, 0),       # Black
        (0, 0, 170),     # Blue
        (0, 170, 0),     # Green
        (0, 170, 170),   # Cyan
        (170, 0, 0),     # Red
        (170, 0, 170),   # Magenta
        (170, 85, 0),    # Brown
        (170, 170, 170), # Light Gray
        (85, 85, 85),    # Dark Gray
        (85, 85, 255),   # Light Blue
        (85, 255, 85),   # Light Green
        (85, 255, 255),  # Light Cyan
        (255, 85, 85),   # Light Red
        (255, 85, 255),  # Light Magenta
        (255, 255, 85),  # Yellow
        (255, 255, 255), # White
    ],
    description="EGA 16-color palette",
    source="IBM EGA",
)

# Dictionary of all built-in palettes
BUILTIN_PALETTES: Dict[str, ColorPalette] = {
    "gameboy": GAMEBOY_PALETTE,
    "nes": NES_PALETTE,
    "pico8": PICO8_PALETTE,
    "cga": CGA_PALETTE,
    "mac_plus": MACPLUS_PALETTE,
    "ega": EGA_PALETTE,
}


def get_palette(name: str) -> Optional[ColorPalette]:
    """
    Get a built-in palette by name.

    Args:
        name: Palette name (case-insensitive)

    Returns:
        ColorPalette or None if not found
    """
    return BUILTIN_PALETTES.get(name.lower())


def list_palettes() -> List[str]:
    """
    List all built-in palette names.

    Returns:
        List of palette names
    """
    return list(BUILTIN_PALETTES.keys())
