"""
CRT & Display Effects Types

Data structures and type definitions for authentic retro display simulation.
Supports CRT, LCD, and other vintage display technologies.

Modules:
- ScanlineConfig: Scanline effect configuration
- PhosphorConfig: Phosphor mask configuration
- CurvatureConfig: Screen curvature configuration
- CRTConfig: Complete CRT effect configuration
- CRT_PRESETS: Built-in presets for various display types

Example Usage:
    from lib.retro.crt_types import CRTConfig, CRT_PRESETS

    # Use preset
    config = CRT_PRESETS["crt_arcade"]

    # Custom configuration
    from lib.retro.crt_types import ScanlineConfig, CRTConfig
    config = CRTConfig(
        name="custom",
        scanlines=ScanlineConfig(enabled=True, intensity=0.3),
    )
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import math


# =============================================================================
# Enums
# =============================================================================

class ScanlineMode(Enum):
    """Scanline rendering mode."""
    ALTERNATE = "alternate"  # Dark/light/dark/light pattern
    EVERY_LINE = "every_line"  # Every line has scanline
    RANDOM = "random"  # Random variation


class PhosphorPattern(Enum):
    """Phosphor mask pattern types."""
    RGB = "rgb"  # Standard RGB stripe
    BGR = "bgr"  # BGR stripe
    APERTURE_GRILLE = "aperture_grille"  # Sony Trinitron style
    SLOT_MASK = "slot_mask"  # Standard CRT slot mask
    SHADOW_MASK = "shadow_mask"  # Delta pattern shadow mask


class DisplayType(Enum):
    """Display technology types."""
    CRT_ARCADE = "crt_arcade"
    CRT_TV = "crt_tv"
    CRT_PVM = "crt_pvm"  # Sony PVM professional monitor
    LCD_GAMEBOY = "lcd_gameboy"
    LCD_GENERIC = "lcd_generic"
    OLED = "oled"


# =============================================================================
# Dataclasses
# =============================================================================

@dataclass
class ScanlineConfig:
    """
    Scanline effect configuration.

    Scanlines simulate the horizontal dark lines visible on CRT displays,
    caused by the gaps between scan lines during electron beam sweep.

    Attributes:
        enabled: Whether scanlines are enabled
        intensity: Darkness of scanlines (0-1, higher = darker)
        spacing: Pixels per scanline group (1 = every line, 2 = every other line)
        thickness: How much of each line is dark (0-1, 0.5 = half the line)
        mode: Scanline rendering mode
        brightness_compensation: Compensate brightness loss from scanlines
    """
    enabled: bool = True
    intensity: float = 0.3
    spacing: int = 2
    thickness: float = 0.5
    mode: str = "alternate"
    brightness_compensation: float = 1.1

    def __post_init__(self):
        """Validate configuration."""
        if not 0 <= self.intensity <= 1:
            raise ValueError(f"intensity must be 0-1, got {self.intensity}")
        if self.spacing < 1:
            raise ValueError(f"spacing must be >= 1, got {self.spacing}")
        if not 0 <= self.thickness <= 1:
            raise ValueError(f"thickness must be 0-1, got {self.thickness}")
        if self.mode not in ("alternate", "every_line", "random"):
            raise ValueError(f"mode must be 'alternate', 'every_line', or 'random', got {self.mode}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanlineConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PhosphorConfig:
    """
    Phosphor mask configuration.

    Phosphor masks simulate the RGB dot/stripe patterns visible on
    close inspection of CRT displays. Different CRT technologies used
    different mask patterns.

    Attributes:
        enabled: Whether phosphor mask is enabled
        pattern: Phosphor pattern type
        intensity: Visibility of the mask pattern (0-1)
        scale: Scale of the phosphor pattern (1.0 = normal)
        slot_width: Width of slots in slot mask mode
        slot_height: Height of slots in slot mask mode
    """
    enabled: bool = False
    pattern: str = "rgb"
    intensity: float = 0.5
    scale: float = 1.0
    slot_width: int = 2
    slot_height: int = 4

    def __post_init__(self):
        """Validate configuration."""
        valid_patterns = ("rgb", "bgr", "aperture_grille", "slot_mask", "shadow_mask")
        if self.pattern not in valid_patterns:
            raise ValueError(f"pattern must be one of {valid_patterns}, got {self.pattern}")
        if not 0 <= self.intensity <= 1:
            raise ValueError(f"intensity must be 0-1, got {self.intensity}")
        if self.scale <= 0:
            raise ValueError(f"scale must be > 0, got {self.scale}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhosphorConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CurvatureConfig:
    """
    Screen curvature configuration.

    Simulates the curved glass surface of CRT displays. Older CRTs had
    more pronounced curvature, while later models (especially Trinitron)
    were flatter.

    Attributes:
        enabled: Whether curvature is enabled
        amount: Amount of barrel distortion (0-1)
        vignette_amount: Edge darkening from curved glass (0-1)
        corner_radius: Rounded corner radius in pixels (0 = square)
        border_size: Black border size in pixels
    """
    enabled: bool = False
    amount: float = 0.1
    vignette_amount: float = 0.2
    corner_radius: int = 0
    border_size: int = 0

    def __post_init__(self):
        """Validate configuration."""
        if not 0 <= self.amount <= 1:
            raise ValueError(f"amount must be 0-1, got {self.amount}")
        if not 0 <= self.vignette_amount <= 1:
            raise ValueError(f"vignette_amount must be 0-1, got {self.vignette_amount}")
        if self.corner_radius < 0:
            raise ValueError(f"corner_radius must be >= 0, got {self.corner_radius}")
        if self.border_size < 0:
            raise ValueError(f"border_size must be >= 0, got {self.border_size}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurvatureConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CRTConfig:
    """
    Complete CRT effect configuration.

    Combines all effect settings into a single configuration for
    authentic retro display simulation.

    Attributes:
        name: Preset name
        scanlines: Scanline effect settings
        phosphor: Phosphor mask settings
        curvature: Screen curvature settings

        Additional effects:
        bloom: Glow effect around bright areas (0-1)
        chromatic_aberration: RGB channel separation (0-0.1)
        flicker: Brightness variation between frames (0-1)
        interlace: Enable interlacing effect
        pixel_jitter: Horizontal pixel instability (0-1)
        noise: Analog static noise (0-1)
        ghosting: Image persistence/ghosting (0-1)

        Color adjustments:
        brightness: Brightness multiplier
        contrast: Contrast multiplier
        saturation: Saturation multiplier
        gamma: Gamma correction value
    """
    name: str = "custom"

    # Sub-configurations
    scanlines: ScanlineConfig = field(default_factory=ScanlineConfig)
    phosphor: PhosphorConfig = field(default_factory=PhosphorConfig)
    curvature: CurvatureConfig = field(default_factory=CurvatureConfig)

    # Additional effects
    bloom: float = 0.0
    chromatic_aberration: float = 0.0
    flicker: float = 0.0
    interlace: bool = False
    pixel_jitter: float = 0.0
    noise: float = 0.0
    ghosting: float = 0.0

    # Color adjustments
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 2.2

    def __post_init__(self):
        """Validate configuration."""
        # Validate ranges
        if not 0 <= self.bloom <= 1:
            raise ValueError(f"bloom must be 0-1, got {self.bloom}")
        if not 0 <= self.chromatic_aberration <= 0.1:
            raise ValueError(f"chromatic_aberration must be 0-0.1, got {self.chromatic_aberration}")
        if not 0 <= self.flicker <= 1:
            raise ValueError(f"flicker must be 0-1, got {self.flicker}")
        if not 0 <= self.pixel_jitter <= 1:
            raise ValueError(f"pixel_jitter must be 0-1, got {self.pixel_jitter}")
        if not 0 <= self.noise <= 1:
            raise ValueError(f"noise must be 0-1, got {self.noise}")
        if not 0 <= self.ghosting <= 1:
            raise ValueError(f"ghosting must be 0-1, got {self.ghosting}")

        if self.brightness <= 0:
            raise ValueError(f"brightness must be > 0, got {self.brightness}")
        if self.contrast <= 0:
            raise ValueError(f"contrast must be > 0, got {self.contrast}")
        if self.saturation < 0:
            raise ValueError(f"saturation must be >= 0, got {self.saturation}")
        if self.gamma <= 0:
            raise ValueError(f"gamma must be > 0, got {self.gamma}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "scanlines": self.scanlines.to_dict(),
            "phosphor": self.phosphor.to_dict(),
            "curvature": self.curvature.to_dict(),
            "bloom": self.bloom,
            "chromatic_aberration": self.chromatic_aberration,
            "flicker": self.flicker,
            "interlace": self.interlace,
            "pixel_jitter": self.pixel_jitter,
            "noise": self.noise,
            "ghosting": self.ghosting,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "gamma": self.gamma,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CRTConfig":
        """Create from dictionary."""
        # Handle nested configs
        if "scanlines" in data and isinstance(data["scanlines"], dict):
            data["scanlines"] = ScanlineConfig.from_dict(data["scanlines"])
        if "phosphor" in data and isinstance(data["phosphor"], dict):
            data["phosphor"] = PhosphorConfig.from_dict(data["phosphor"])
        if "curvature" in data and isinstance(data["curvature"], dict):
            data["curvature"] = CurvatureConfig.from_dict(data["curvature"])
        return cls(**data)


# =============================================================================
# Built-in Presets
# =============================================================================

CRT_PRESETS: Dict[str, CRTConfig] = {
    # 80s Arcade monitor - bright, visible scanlines, slight curvature
    "crt_arcade": CRTConfig(
        name="crt_arcade",
        scanlines=ScanlineConfig(enabled=True, intensity=0.25, spacing=2),
        phosphor=PhosphorConfig(enabled=True, pattern="aperture_grille", intensity=0.4),
        curvature=CurvatureConfig(enabled=True, amount=0.08, vignette_amount=0.15),
        bloom=0.15,
        chromatic_aberration=0.002,
    ),

    # Home CRT TV 90s - softer, more noticeable scanlines
    "crt_tv": CRTConfig(
        name="crt_tv",
        scanlines=ScanlineConfig(enabled=True, intensity=0.4, spacing=1),
        phosphor=PhosphorConfig(enabled=True, pattern="slot_mask", intensity=0.5),
        curvature=CurvatureConfig(enabled=True, amount=0.12, vignette_amount=0.2),
        noise=0.05,
        flicker=0.02,
    ),

    # Sony PVM professional monitor - high quality, minimal artifacts
    "pvm": CRTConfig(
        name="pvm",
        scanlines=ScanlineConfig(enabled=True, intensity=0.15, spacing=1, thickness=0.3),
        phosphor=PhosphorConfig(enabled=True, pattern="aperture_grille", intensity=0.25),
        curvature=CurvatureConfig(enabled=False),
        bloom=0.05,
    ),

    # Game Boy LCD - no scanlines, ghosting, low contrast
    "lcd_gameboy": CRTConfig(
        name="lcd_gameboy",
        scanlines=ScanlineConfig(enabled=False),
        phosphor=PhosphorConfig(enabled=False),
        curvature=CurvatureConfig(enabled=False),
        pixel_jitter=0.02,
        ghosting=0.3,
        contrast=1.2,
        saturation=0.8,
        gamma=2.4,
    ),

    # CGA Monitor - harsh scanlines, visible phosphor
    "cga_monitor": CRTConfig(
        name="cga_monitor",
        scanlines=ScanlineConfig(enabled=True, intensity=0.5, spacing=1),
        phosphor=PhosphorConfig(enabled=True, pattern="rgb", intensity=0.6),
        curvature=CurvatureConfig(enabled=True, amount=0.05),
        flicker=0.03,
    ),

    # Modern LCD (clean) - minimal effects
    "modern_lcd": CRTConfig(
        name="modern_lcd",
        scanlines=ScanlineConfig(enabled=False),
        phosphor=PhosphorConfig(enabled=False),
        curvature=CurvatureConfig(enabled=False),
        chromatic_aberration=0.001,
    ),

    # Trinitron - Sony's famous flat CRT
    "trinitron": CRTConfig(
        name="trinitron",
        scanlines=ScanlineConfig(enabled=True, intensity=0.2, spacing=1, thickness=0.4),
        phosphor=PhosphorConfig(enabled=True, pattern="aperture_grille", intensity=0.35, scale=1.2),
        curvature=CurvatureConfig(enabled=True, amount=0.03, vignette_amount=0.1),
        bloom=0.1,
        brightness=1.1,
    ),

    # Vintage TV 70s - high curvature, noise, warm colors
    "vintage_tv": CRTConfig(
        name="vintage_tv",
        scanlines=ScanlineConfig(enabled=True, intensity=0.35, spacing=2, thickness=0.6),
        phosphor=PhosphorConfig(enabled=True, pattern="slot_mask", intensity=0.55),
        curvature=CurvatureConfig(enabled=True, amount=0.15, vignette_amount=0.25),
        noise=0.08,
        flicker=0.04,
        bloom=0.2,
        saturation=1.1,
        gamma=2.0,
    ),

    # Portable LCD (like Tiger handhelds)
    "portable_lcd": CRTConfig(
        name="portable_lcd",
        scanlines=ScanlineConfig(enabled=False),
        phosphor=PhosphorConfig(enabled=False),
        curvature=CurvatureConfig(enabled=False),
        ghosting=0.4,
        contrast=1.4,
        saturation=0.6,
        brightness=0.9,
    ),

    # NES on CRT
    "nes_crt": CRTConfig(
        name="nes_crt",
        scanlines=ScanlineConfig(enabled=True, intensity=0.3, spacing=1),
        phosphor=PhosphorConfig(enabled=True, pattern="slot_mask", intensity=0.45),
        curvature=CurvatureConfig(enabled=True, amount=0.1, vignette_amount=0.18),
        bloom=0.12,
        chromatic_aberration=0.003,
    ),

    # Sharp vibrant arcade
    "arcade_sharp": CRTConfig(
        name="arcade_sharp",
        scanlines=ScanlineConfig(enabled=True, intensity=0.2, spacing=1, thickness=0.35),
        phosphor=PhosphorConfig(enabled=True, pattern="aperture_grille", intensity=0.3),
        curvature=CurvatureConfig(enabled=False),
        bloom=0.08,
        brightness=1.15,
        saturation=1.1,
    ),

    # B&W CRT (like old Mac)
    "bw_crt": CRTConfig(
        name="bw_crt",
        scanlines=ScanlineConfig(enabled=True, intensity=0.25, spacing=2),
        phosphor=PhosphorConfig(enabled=False),
        curvature=CurvatureConfig(enabled=True, amount=0.08),
        bloom=0.1,
        saturation=0.0,  # Force grayscale
        gamma=2.3,
    ),
}


# =============================================================================
# Utility Functions
# =============================================================================

def get_preset(name: str) -> CRTConfig:
    """
    Get a CRT preset by name.

    Args:
        name: Preset name

    Returns:
        CRTConfig for the preset

    Raises:
        KeyError: If preset not found
    """
    if name not in CRT_PRESETS:
        available = list(CRT_PRESETS.keys())
        raise KeyError(f"Preset '{name}' not found. Available: {available}")
    return CRT_PRESETS[name]


def list_presets() -> List[str]:
    """
    List available CRT presets.

    Returns:
        List of preset names
    """
    return list(CRT_PRESETS.keys())


def get_preset_description(name: str) -> str:
    """
    Get description for a preset.

    Args:
        name: Preset name

    Returns:
        Human-readable description
    """
    descriptions = {
        "crt_arcade": "80s arcade monitor - bright, visible scanlines, slight curvature",
        "crt_tv": "90s home CRT TV - softer image, noticeable scanlines",
        "pvm": "Sony PVM professional monitor - high quality, minimal artifacts",
        "lcd_gameboy": "Nintendo Game Boy LCD - ghosting, low contrast",
        "cga_monitor": "IBM CGA monitor - harsh scanlines, visible phosphor",
        "modern_lcd": "Modern LCD display - clean, minimal effects",
        "trinitron": "Sony Trinitron - flat CRT with aperture grille",
        "vintage_tv": "70s vintage TV - high curvature, noise, warm colors",
        "portable_lcd": "Portable LCD (Tiger handhelds) - heavy ghosting",
        "nes_crt": "NES on CRT TV - classic 8-bit console look",
        "arcade_sharp": "Sharp vibrant arcade - clean, bright colors",
        "bw_crt": "Black and white CRT - like old Macintosh",
    }
    return descriptions.get(name, "No description available")


def create_custom_preset(
    base: str = "modern_lcd",
    **overrides
) -> CRTConfig:
    """
    Create a custom preset by overriding base preset values.

    Args:
        base: Base preset name to start from
        **overrides: Values to override

    Returns:
        New CRTConfig with overrides applied
    """
    base_config = get_preset(base)
    base_dict = base_config.to_dict()

    # Handle nested overrides
    for key, value in overrides.items():
        if "." in key:
            # Nested override like "scanlines.intensity"
            parts = key.split(".", 1)
            if parts[0] in base_dict and isinstance(base_dict[parts[0]], dict):
                base_dict[parts[0]][parts[1]] = value
        else:
            base_dict[key] = value

    base_dict["name"] = overrides.get("name", "custom")
    return CRTConfig.from_dict(base_dict)


def validate_config(config: CRTConfig) -> List[str]:
    """
    Validate a CRT configuration and return any issues.

    Args:
        config: Configuration to validate

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    # Check for conflicting settings
    if config.scanlines.enabled and config.scanlines.intensity > 0.7:
        issues.append("High scanline intensity (>0.7) may cause very dark image")

    if config.curvature.enabled and config.curvature.amount > 0.2:
        issues.append("High curvature (>0.2) may cause significant distortion")

    if config.noise > 0.1:
        issues.append("High noise (>0.1) may overwhelm image content")

    if config.ghosting > 0.5 and config.bloom > 0.3:
        issues.append("High ghosting and bloom together may cause blurry image")

    # Check for performance concerns
    effect_count = sum([
        config.scanlines.enabled,
        config.phosphor.enabled,
        config.curvature.enabled,
        config.bloom > 0,
        config.chromatic_aberration > 0,
        config.flicker > 0,
        config.noise > 0,
        config.ghosting > 0,
    ])

    if effect_count > 5:
        issues.append(f"Many effects enabled ({effect_count}) may impact performance")

    return issues
