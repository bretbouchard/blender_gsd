"""
LED/Indicator Configuration System

Configuration dataclasses for LED and indicator elements.

LED Types:
- Single LED: Individual indicator lights
- LED Bar: Multi-segment level meters
- VU Meter: Analog-style needle meters
- 7-Segment: Numeric displays

Features:
- Multiple LED sizes (3mm, 5mm, 10mm)
- Lens types (clear, diffused, water clear)
- Bezel styles (chrome, black, flanged)
- Color zones for level meters
- Animation support
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, Dict, Any, List


class LEDType(Enum):
    """LED/indicator type classification."""
    SINGLE = "single"           # Single LED indicator
    LED_BAR = "led_bar"         # Multi-segment bar
    VU_METER = "vu_meter"       # Analog needle meter
    SEVEN_SEGMENT = "7_segment" # Numeric display
    BI_COLOR = "bi_color"       # Two-color LED
    RGB = "rgb"                 # RGB LED


class LEDShape(Enum):
    """LED shape options."""
    ROUND = "round"
    SQUARE = "square"
    RECTANGULAR = "rectangular"
    OVAL = "oval"


class LEDLens(Enum):
    """LED lens type."""
    CLEAR = "clear"             # Focused, bright
    DIFFUSED = "diffused"       # Soft glow
    WATER_CLEAR = "water_clear" # Transparent when off
    TINTED = "tinted"           # Slightly colored


class BezelStyle(Enum):
    """LED bezel/mounting style."""
    NONE = "none"               # Flush mount
    CHROME = "chrome"           # Chrome bezel ring
    BLACK = "black"             # Black bezel ring
    FLANGED = "flanged"         # Wide flange mount
    RECESSED = "recessed"       # Set into panel


class LEDSize(Enum):
    """Standard LED sizes."""
    T1 = 3       # 3mm (T1)
    T1_3_4 = 5   # 5mm (T1-3/4) - most common
    T1_1_4 = 8   # 8mm (T1-1/4)
    T3_4 = 10    # 10mm (T3/4)


class BarDirection(Enum):
    """LED bar orientation."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class VUNeedleStyle(Enum):
    """VU meter needle style."""
    CLASSIC = "classic"         # Traditional black needle
    MODERN = "modern"           # Slim red needle
    MINIMAL = "minimal"         # Thin line


class VUScaleStyle(Enum):
    """VU meter scale style."""
    IEC = "iec"                 # Standard IEC scale
    DIN = "din"                 # German DIN scale
    CUSTOM = "custom"           # Custom scale


class VUResponse(Enum):
    """VU meter response speed."""
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"


class SegmentStyle(Enum):
    """7-segment display style."""
    CLASSIC = "classic"         # Traditional LED segments
    MODERN = "modern"           # Slim segments
    DOT_MATRIX = "dot_matrix"   # Dot-based display


class AnimationType(Enum):
    """LED animation types."""
    NONE = "none"
    PULSE = "pulse"             # Slow brightness pulse
    FLASH = "flash"             # Fast on/off
    FADE = "fade"               # Fade in/out
    CHASE = "chase"             # Sequential chase
    RANDOM = "random"           # Random flicker


@dataclass
class BezelConfig:
    """Configuration for LED bezel."""
    style: BezelStyle = BezelStyle.NONE
    diameter: float = 0.008     # 8mm bezel diameter
    height: float = 0.002       # 2mm bezel height
    color: Tuple[float, float, float] = (0.8, 0.8, 0.82)  # Chrome

    def to_params(self) -> Dict[str, Any]:
        return {
            "bezel_style": self.style.value,
            "bezel_diameter": self.diameter,
            "bezel_height": self.height,
            "bezel_color": list(self.color),
        }


@dataclass
class ColorZone:
    """Color zone for LED bar threshold."""
    threshold: float            # 0-100 percentage
    color: Tuple[float, float, float]

    def to_params(self) -> Dict[str, Any]:
        return {
            "threshold": self.threshold,
            "color": list(self.color),
        }


@dataclass
class LEDConfig:
    """
    Configuration for single LED indicator.

    Default values represent a standard 5mm panel-mount LED.
    """
    name: str = "LED"

    # Type and shape
    led_type: LEDType = LEDType.SINGLE
    shape: LEDShape = LEDShape.ROUND
    size: LEDSize = LEDSize.T1_3_4    # 5mm

    # Custom dimensions (overrides size)
    diameter: Optional[float] = None  # Custom diameter in meters
    height: Optional[float] = None    # Custom height

    # Lens
    lens: LEDLens = LEDLens.DIFFUSED
    diffusion: float = 0.3            # 0=sharp, 1=soft

    # Color
    color: Tuple[float, float, float] = (0.0, 1.0, 0.0)  # Green
    color_off: Tuple[float, float, float] = (0.1, 0.1, 0.1)
    brightness: float = 1.0           # 0-2 multiplier

    # State
    active: bool = True               # On/off state
    value: float = 1.0                # Brightness value 0-1

    # Bezel
    bezel: BezelConfig = field(default_factory=BezelConfig)

    # Animation
    animation: AnimationType = AnimationType.NONE
    animation_speed: float = 1.0      # Hz

    def get_diameter(self) -> float:
        """Get LED diameter in meters."""
        if self.diameter is not None:
            return self.diameter
        # Convert mm to meters
        return self.size.value / 1000.0

    def get_height(self) -> float:
        """Get LED height in meters."""
        if self.height is not None:
            return self.height
        # Height is typically 0.6x diameter
        return self.get_diameter() * 0.6

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        params = {
            "led_name": self.name,
            "led_type": self.led_type.value,
            "led_shape": self.shape.value,
            "led_size": self.size.value,
            "led_diameter": self.get_diameter(),
            "led_height": self.get_height(),
            "led_lens": self.lens.value,
            "led_diffusion": self.diffusion,
            "led_color": list(self.color),
            "led_color_off": list(self.color_off),
            "led_brightness": self.brightness,
            "led_active": self.active,
            "led_value": self.value,
            "led_animation": self.animation.value,
            "led_animation_speed": self.animation_speed,
        }
        params.update(self.bezel.to_params())
        return params


@dataclass
class LEDBarConfig:
    """
    Configuration for LED bar/level meter.

    Default values represent a 10-segment stereo level meter.
    """
    name: str = "LEDBar"

    # Orientation
    direction: BarDirection = BarDirection.VERTICAL
    segments: int = 10
    segment_spacing: float = 0.002    # 2mm between segments

    # Segment dimensions
    segment_width: float = 0.004      # 4mm wide
    segment_height: float = 0.008     # 8mm tall
    segment_depth: float = 0.003      # 3mm thick

    # Colors with zones
    color_zones: List[ColorZone] = field(default_factory=lambda: [
        ColorZone(0, (0.0, 0.8, 0.0)),      # Green: 0-60%
        ColorZone(60, (1.0, 1.0, 0.0)),     # Yellow: 60-85%
        ColorZone(85, (1.0, 0.0, 0.0)),     # Red: 85%+
    ])

    # Global
    brightness: float = 1.0
    color_off: Tuple[float, float, float] = (0.05, 0.05, 0.05)

    # Value
    value: float = 0.0                # 0-1 level
    peak_value: float = 0.0           # Peak hold indicator

    # Bezel/frame
    bezel: BezelConfig = field(default_factory=BezelConfig)
    frame_enabled: bool = True
    frame_color: Tuple[float, float, float] = (0.15, 0.15, 0.15)

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        params = {
            "ledbar_name": self.name,
            "ledbar_direction": self.direction.value,
            "ledbar_segments": self.segments,
            "ledbar_spacing": self.segment_spacing,
            "ledbar_segment_width": self.segment_width,
            "ledbar_segment_height": self.segment_height,
            "ledbar_segment_depth": self.segment_depth,
            "ledbar_brightness": self.brightness,
            "ledbar_color_off": list(self.color_off),
            "ledbar_value": self.value,
            "ledbar_peak_value": self.peak_value,
            "ledbar_frame_enabled": self.frame_enabled,
            "ledbar_frame_color": list(self.frame_color),
        }
        params.update(self.bezel.to_params())
        params["color_zones"] = [z.to_params() for z in self.color_zones]
        return params


@dataclass
class VUMeterConfig:
    """
    Configuration for analog VU meter.

    Default values represent a classic console VU meter.
    """
    name: str = "VUMeter"

    # Dimensions
    width: float = 0.040              # 40mm wide
    height: float = 0.030             # 30mm tall
    depth: float = 0.015              # 15mm deep

    # Needle
    needle_style: VUNeedleStyle = VUNeedleStyle.CLASSIC
    needle_color: Tuple[float, float, float] = (0.1, 0.1, 0.1)
    needle_length: float = 0.015      # 15mm needle
    needle_width: float = 0.001       # 1mm wide at base

    # Scale
    scale_style: VUScaleStyle = VUScaleStyle.IEC
    scale_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    scale_font_size: float = 0.003    # 3mm text

    # Response
    response: VUResponse = VUResponse.MEDIUM
    overshoot: float = 1.5            # Needle overshoot factor

    # Background
    background_color: Tuple[float, float, float] = (0.95, 0.95, 0.92)  # Cream

    # Value
    value: float = 0.0                # -20 to +3 dB

    # Frame
    frame_enabled: bool = True
    frame_color: Tuple[float, float, float] = (0.2, 0.2, 0.2)

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "vu_name": self.name,
            "vu_width": self.width,
            "vu_height": self.height,
            "vu_depth": self.depth,
            "vu_needle_style": self.needle_style.value,
            "vu_needle_color": list(self.needle_color),
            "vu_needle_length": self.needle_length,
            "vu_needle_width": self.needle_width,
            "vu_scale_style": self.scale_style.value,
            "vu_scale_color": list(self.scale_color),
            "vu_scale_font_size": self.scale_font_size,
            "vu_response": self.response.value,
            "vu_overshoot": self.overshoot,
            "vu_background_color": list(self.background_color),
            "vu_value": self.value,
            "vu_frame_enabled": self.frame_enabled,
            "vu_frame_color": list(self.frame_color),
        }


@dataclass
class SevenSegmentConfig:
    """
    Configuration for 7-segment numeric display.

    Default values represent a 4-digit LED display.
    """
    name: str = "SevenSegment"

    # Digits
    digits: int = 4
    digit_spacing: float = 0.006      # 6mm between digits

    # Segment dimensions
    segment_width: float = 0.003      # 3mm segment width
    segment_height: float = 0.008     # 8mm segment height
    segment_gap: float = 0.0005       # 0.5mm gap between segments

    # Style
    segment_style: SegmentStyle = SegmentStyle.CLASSIC
    segment_color: Tuple[float, float, float] = (1.0, 0.2, 0.0)  # Red-orange
    segment_color_off: Tuple[float, float, float] = (0.1, 0.02, 0.0)

    # Decimal points
    decimal_points: bool = True
    decimal_size: float = 0.0015      # 1.5mm decimal dot

    # Global
    brightness: float = 1.0
    background_color: Tuple[float, float, float] = (0.05, 0.05, 0.05)

    # Value
    display_value: str = "0.00"

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "seg_name": self.name,
            "seg_digits": self.digits,
            "seg_spacing": self.digit_spacing,
            "seg_width": self.segment_width,
            "seg_height": self.segment_height,
            "seg_gap": self.segment_gap,
            "seg_style": self.segment_style.value,
            "seg_color": list(self.segment_color),
            "seg_color_off": list(self.segment_color_off),
            "seg_decimal_points": self.decimal_points,
            "seg_decimal_size": self.decimal_size,
            "seg_brightness": self.brightness,
            "seg_background": list(self.background_color),
            "seg_value": self.display_value,
        }


# =============================================================================
# PRESETS
# =============================================================================

LED_PRESETS: Dict[str, LEDConfig] = {}
LEDBAR_PRESETS: Dict[str, LEDBarConfig] = {}
VU_PRESETS: Dict[str, VUMeterConfig] = {}
SEGMENT_PRESETS: Dict[str, SevenSegmentConfig] = {}


def _register_led(name: str, config: LEDConfig) -> None:
    LED_PRESETS[name] = config


def _register_ledbar(name: str, config: LEDBarConfig) -> None:
    LEDBAR_PRESETS[name] = config


def _register_vu(name: str, config: VUMeterConfig) -> None:
    VU_PRESETS[name] = config


def _register_segment(name: str, config: SevenSegmentConfig) -> None:
    SEGMENT_PRESETS[name] = config


# -----------------------------------------------------------------------------
# Single LED Presets
# -----------------------------------------------------------------------------

# Console power LED (green)
_register_led("console_power", LEDConfig(
    name="Console Power",
    shape=LEDShape.ROUND,
    size=LEDSize.T1_3_4,
    lens=LEDLens.DIFFUSED,
    color=(0.0, 0.9, 0.1),
    brightness=0.8,
    bezel=BezelConfig(style=BezelStyle.CHROME),
))

# Record status (red)
_register_led("record_status", LEDConfig(
    name="Record Status",
    shape=LEDShape.ROUND,
    size=LEDSize.T1_3_4,
    lens=LEDLens.DIFFUSED,
    color=(1.0, 0.1, 0.1),
    color_off=(0.15, 0.0, 0.0),
    brightness=1.0,
    animation=AnimationType.PULSE,
    animation_speed=2.0,
    bezel=BezelConfig(style=BezelStyle.NONE),
))

# Signal present (yellow)
_register_led("signal_present", LEDConfig(
    name="Signal Present",
    shape=LEDShape.ROUND,
    size=LEDSize.T1,
    lens=LEDLens.CLEAR,
    color=(1.0, 0.9, 0.0),
    brightness=0.7,
    bezel=BezelConfig(style=BezelStyle.BLACK),
))

# Clip indicator (red)
_register_led("clip_indicator", LEDConfig(
    name="Clip",
    shape=LEDShape.SQUARE,
    size=LEDSize.T1,
    lens=LEDLens.DIFFUSED,
    color=(1.0, 0.0, 0.0),
    color_off=(0.2, 0.0, 0.0),
    brightness=1.2,
    bezel=BezelConfig(style=BezelStyle.NONE),
))

# MIDI activity (blue)
_register_led("midi_activity", LEDConfig(
    name="MIDI Activity",
    shape=LEDShape.ROUND,
    size=LEDSize.T1,
    lens=LEDLens.CLEAR,
    color=(0.0, 0.5, 1.0),
    brightness=0.6,
    bezel=BezelConfig(style=BezelStyle.NONE),
))

# 808 style colored LED
_register_led("roland_808", LEDConfig(
    name="Roland 808 LED",
    shape=LEDShape.ROUND,
    size=LEDSize.T1_3_4,
    lens=LEDLens.DIFFUSED,
    diffusion=0.5,
    color=(1.0, 0.4, 0.0),  # Orange
    brightness=0.9,
    bezel=BezelConfig(style=BezelStyle.NONE),
))

# SSL style LED (rectangular)
_register_led("ssl_status", LEDConfig(
    name="SSL Status",
    shape=LEDShape.RECTANGULAR,
    diameter=0.004,
    height=0.002,
    lens=LEDLens.DIFFUSED,
    color=(0.0, 0.8, 0.0),
    bezel=BezelConfig(style=BezelStyle.NONE),
))

# -----------------------------------------------------------------------------
# LED Bar Presets
# -----------------------------------------------------------------------------

# Console stereo meter
_register_ledbar("console_stereo", LEDBarConfig(
    name="Console Stereo Meter",
    direction=BarDirection.VERTICAL,
    segments=12,
    segment_spacing=0.003,
    segment_width=0.005,
    segment_height=0.010,
    color_zones=[
        ColorZone(0, (0.0, 0.8, 0.0)),      # Green
        ColorZone(60, (0.8, 0.8, 0.0)),     # Yellow
        ColorZone(85, (1.0, 0.0, 0.0)),     # Red
    ],
    bezel=BezelConfig(style=BezelStyle.BLACK),
))

# Compact meter
_register_ledbar("compact_meter", LEDBarConfig(
    name="Compact Meter",
    direction=BarDirection.VERTICAL,
    segments=8,
    segment_spacing=0.002,
    segment_width=0.003,
    segment_height=0.006,
    color_zones=[
        ColorZone(0, (0.0, 0.7, 0.0)),
        ColorZone(70, (1.0, 0.7, 0.0)),
    ],
))

# Horizontal level meter
_register_ledbar("horizontal_level", LEDBarConfig(
    name="Horizontal Level",
    direction=BarDirection.HORIZONTAL,
    segments=20,
    segment_spacing=0.002,
    segment_width=0.006,
    segment_height=0.004,
    color_zones=[
        ColorZone(0, (0.0, 0.6, 0.0)),
        ColorZone(50, (0.0, 0.8, 0.0)),
        ColorZone(75, (1.0, 1.0, 0.0)),
        ColorZone(90, (1.0, 0.0, 0.0)),
    ],
))

# Vintage LED bar (warm colors)
_register_ledbar("vintage_warm", LEDBarConfig(
    name="Vintage Warm",
    direction=BarDirection.VERTICAL,
    segments=10,
    segment_spacing=0.004,
    segment_width=0.008,
    segment_height=0.012,
    color_zones=[
        ColorZone(0, (0.8, 0.4, 0.0)),      # Amber
        ColorZone(70, (1.0, 0.6, 0.0)),     # Orange
        ColorZone(90, (1.0, 0.2, 0.0)),     # Red-orange
    ],
))

# -----------------------------------------------------------------------------
# VU Meter Presets
# -----------------------------------------------------------------------------

# Classic console VU
_register_vu("classic_console", VUMeterConfig(
    name="Classic Console VU",
    width=0.050,
    height=0.040,
    needle_style=VUNeedleStyle.CLASSIC,
    needle_color=(0.1, 0.1, 0.1),
    scale_style=VUScaleStyle.IEC,
    background_color=(0.98, 0.96, 0.90),  # Cream
))

# Modern slim VU
_register_vu("modern_slim", VUMeterConfig(
    name="Modern Slim VU",
    width=0.035,
    height=0.020,
    needle_style=VUNeedleStyle.MODERN,
    needle_color=(0.9, 0.1, 0.1),
    scale_style=VUScaleStyle.DIN,
    background_color=(0.95, 0.95, 0.95),
))

# Vintage broadcast
_register_vu("vintage_broadcast", VUMeterConfig(
    name="Vintage Broadcast",
    width=0.060,
    height=0.050,
    needle_style=VUNeedleStyle.CLASSIC,
    needle_color=(0.05, 0.05, 0.05),
    scale_style=VUScaleStyle.IEC,
    background_color=(0.85, 0.82, 0.75),  # Aged cream
))

# -----------------------------------------------------------------------------
# 7-Segment Presets
# -----------------------------------------------------------------------------

# Tempo display
_register_segment("tempo_display", SevenSegmentConfig(
    name="Tempo",
    digits=3,
    segment_width=0.003,
    segment_height=0.006,
    segment_color=(1.0, 0.2, 0.0),  # Red-orange
    decimal_points=False,
))

# Frequency readout
_register_segment("frequency_readout", SevenSegmentConfig(
    name="Frequency",
    digits=5,
    segment_width=0.002,
    segment_height=0.005,
    segment_color=(0.0, 0.8, 0.2),  # Green
    decimal_points=True,
))

# Level display (dB)
_register_segment("level_db", SevenSegmentConfig(
    name="Level dB",
    digits=4,
    segment_width=0.004,
    segment_height=0.008,
    segment_color=(0.2, 0.6, 1.0),  # Blue
    decimal_points=True,
))


def list_led_presets() -> List[str]:
    """List all available LED preset names."""
    return list(LED_PRESETS.keys())


def get_led_preset(name: str) -> LEDConfig:
    """Get an LED preset by name."""
    if name not in LED_PRESETS:
        available = ", ".join(list_led_presets())
        raise KeyError(f"LED preset '{name}' not found. Available: {available}")
    return LED_PRESETS[name]


def list_ledbar_presets() -> List[str]:
    """List all available LED bar preset names."""
    return list(LEDBAR_PRESETS.keys())


def get_ledbar_preset(name: str) -> LEDBarConfig:
    """Get an LED bar preset by name."""
    if name not in LEDBAR_PRESETS:
        available = ", ".join(list_ledbar_presets())
        raise KeyError(f"LED bar preset '{name}' not found. Available: {available}")
    return LEDBAR_PRESETS[name]


def list_vu_presets() -> List[str]:
    """List all available VU meter preset names."""
    return list(VU_PRESETS.keys())


def get_vu_preset(name: str) -> VUMeterConfig:
    """Get a VU meter preset by name."""
    if name not in VU_PRESETS:
        available = ", ".join(list_vu_presets())
        raise KeyError(f"VU preset '{name}' not found. Available: {available}")
    return VU_PRESETS[name]


def list_segment_presets() -> List[str]:
    """List all available 7-segment preset names."""
    return list(SEGMENT_PRESETS.keys())


def get_segment_preset(name: str) -> SevenSegmentConfig:
    """Get a 7-segment display preset by name."""
    if name not in SEGMENT_PRESETS:
        available = ", ".join(list_segment_presets())
        raise KeyError(f"7-segment preset '{name}' not found. Available: {available}")
    return SEGMENT_PRESETS[name]
