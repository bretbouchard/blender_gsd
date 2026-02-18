"""
Fader System Module

Provides configuration and builders for linear controls (faders/sliders):
- Channel faders (100mm travel)
- Short faders (60mm)
- Mini faders (45mm)
- Fader knob styles (square, rounded, angled)
- Track systems
- LED meter integration
- Scale/markings

All features designed for Geometry Nodes procedural generation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class FaderType(Enum):
    """Fader/slider types."""
    CHANNEL = "channel"       # Long travel (100mm), professional
    SHORT = "short"           # Compact (60mm)
    MINI = "mini"             # Very short (45mm)
    MOTORIZE = "motorized"    # Automated movement
    TOUCH = "touch"           # Touch-sensitive


class FaderKnobStyle(Enum):
    """Fader knob/handle styles."""
    SQUARE = "square"         # SSL style
    ROUNDED = "rounded"       # Neve style
    ANGLED = "angled"         # API style
    TAPERED = "tapered"       # Tapered sides
    CUSTOM = "custom"         # Custom profile


class TrackStyle(Enum):
    """Track/guide styles."""
    EXPOSED = "exposed"           # Exposed metal rail
    COVERED_SLOT = "covered_slot" # Covered slot channel
    LED_SLOT = "led_slot"         # LED slot with meter
    PRINTED = "printed"           # Printed scale on panel


class ScaleType(Enum):
    """Scale marking types."""
    DB = "db"               # Decibel scale (-∞ to +10dB)
    ZERO_TEN = "0-10"       # 0 to 10
    PERCENTAGE = "percentage"  # 0-100%
    CUSTOM = "custom"       # Custom markings


class LEDResponse(Enum):
    """LED meter response types."""
    PEAK = "peak"           # Peak holding
    RMS = "rms"             # RMS average
    VU = "vu"               # VU ballistics


class ScalePosition(Enum):
    """Scale position relative to fader."""
    LEFT = "left"
    RIGHT = "right"
    BOTH = "both"
    NONE = "none"


# =============================================================================
# FADER KNOB CONFIG
# =============================================================================

@dataclass
class FaderKnobConfig:
    """
    Configuration for fader knob/handle.
    """
    # Style
    style: FaderKnobStyle = FaderKnobStyle.ROUNDED

    # Dimensions (meters)
    width: float = 0.015         # Knob width (15mm)
    height: float = 0.020        # Knob height (20mm)
    depth: float = 0.010         # Knob depth (10mm)

    # Style-specific
    top_angle: float = 15.0      # Angle for angled style (degrees)
    taper_ratio: float = 0.8     # Top/bottom ratio for tapered style
    corner_radius: float = 0.002 # Corner rounding

    # Grip features
    grip_enabled: bool = False
    grip_pattern: str = "ridges"  # ridges, dots, smooth
    grip_count: int = 5
    grip_depth: float = 0.0005

    # Colors/Materials
    color: Tuple[float, float, float] = (0.15, 0.15, 0.15)
    metallic: float = 0.0
    roughness: float = 0.4

    # Indicator line on knob
    indicator_enabled: bool = True
    indicator_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    indicator_width: float = 0.002

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "fader_knob_style": self.style.value,
            "fader_knob_width": self.width,
            "fader_knob_height": self.height,
            "fader_knob_depth": self.depth,
            "fader_knob_top_angle": self.top_angle,
            "fader_knob_taper_ratio": self.taper_ratio,
            "fader_knob_corner_radius": self.corner_radius,
            "fader_knob_grip_enabled": self.grip_enabled,
            "fader_knob_grip_pattern": self.grip_pattern,
            "fader_knob_grip_count": self.grip_count,
            "fader_knob_grip_depth": self.grip_depth,
            "fader_knob_color": list(self.color),
            "fader_knob_metallic": self.metallic,
            "fader_knob_roughness": self.roughness,
            "fader_knob_indicator_enabled": self.indicator_enabled,
            "fader_knob_indicator_color": list(self.indicator_color),
            "fader_knob_indicator_width": self.indicator_width,
        }


# =============================================================================
# TRACK CONFIG
# =============================================================================

@dataclass
class TrackConfig:
    """
    Configuration for fader track/guide.
    """
    # Style
    style: TrackStyle = TrackStyle.EXPOSED

    # Dimensions
    width: float = 0.006          # Track width (6mm)
    depth: float = 0.003          # Track depth (3mm)

    # Colors/Materials
    color: Tuple[float, float, float] = (0.6, 0.6, 0.62)
    metallic: float = 0.8
    roughness: float = 0.3

    # Covered slot specific
    slot_cover_enabled: bool = False
    slot_cover_color: Tuple[float, float, float] = (0.2, 0.2, 0.2)

    # End caps
    end_caps_enabled: bool = True
    end_cap_height: float = 0.005

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "fader_track_style": self.style.value,
            "fader_track_width": self.width,
            "fader_track_depth": self.depth,
            "fader_track_color": list(self.color),
            "fader_track_metallic": self.metallic,
            "fader_track_roughness": self.roughness,
            "fader_track_slot_cover_enabled": self.slot_cover_enabled,
            "fader_track_slot_cover_color": list(self.slot_cover_color),
            "fader_track_end_caps_enabled": self.end_caps_enabled,
            "fader_track_end_cap_height": self.end_cap_height,
        }


# =============================================================================
# SCALE CONFIG
# =============================================================================

@dataclass
class ScaleConfig:
    """
    Configuration for scale markings.
    """
    # Enable
    enabled: bool = True

    # Position
    position: ScalePosition = ScalePosition.RIGHT

    # Type
    scale_type: ScaleType = ScaleType.DB

    # Dimensions
    tick_height: float = 0.003    # Tick mark height
    tick_width: float = 0.0005    # Tick mark width
    major_tick_height: float = 0.005
    tick_spacing: float = 0.010   # Between ticks

    # Colors
    color: Tuple[float, float, float] = (0.8, 0.8, 0.8)
    major_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    # Labels (for text rendering)
    labels_enabled: bool = False
    label_font_size: float = 0.004
    label_offset: float = 0.003

    # dB scale specific
    db_range: Tuple[float, float] = (-60.0, 10.0)  # dB range
    db_ticks: List[float] = field(default_factory=lambda: [
        -60, -50, -40, -30, -20, -15, -10, -5, 0, 5, 10
    ])

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "fader_scale_enabled": self.enabled,
            "fader_scale_position": self.position.value,
            "fader_scale_type": self.scale_type.value,
            "fader_scale_tick_height": self.tick_height,
            "fader_scale_tick_width": self.tick_width,
            "fader_scale_major_tick_height": self.major_tick_height,
            "fader_scale_tick_spacing": self.tick_spacing,
            "fader_scale_color": list(self.color),
            "fader_scale_major_color": list(self.major_color),
            "fader_scale_labels_enabled": self.labels_enabled,
            "fader_scale_label_font_size": self.label_font_size,
            "fader_scale_label_offset": self.label_offset,
            "fader_scale_db_range": list(self.db_range),
            "fader_scale_db_ticks": self.db_ticks,
        }


# =============================================================================
# LED METER CONFIG
# =============================================================================

@dataclass
class LEDMeterConfig:
    """
    Configuration for LED meter on fader.
    """
    # Enable
    enabled: bool = False

    # Position
    position: str = "beside_track"  # beside_track, in_track

    # Segments
    segment_count: int = 12
    segment_height: float = 0.006
    segment_width: float = 0.003
    segment_spacing: float = 0.001

    # Colors (thresholds from 0-1 normalized)
    color_zones: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"threshold": 0.0, "color": [0.0, 1.0, 0.0]},      # Green (safe)
        {"threshold": 0.7, "color": [1.0, 1.0, 0.0]},      # Yellow (warning)
        {"threshold": 0.9, "color": [1.0, 0.0, 0.0]},      # Red (danger)
    ])

    # Response
    response: LEDResponse = LEDResponse.PEAK
    hold_time: float = 0.5  # Peak hold time (seconds)

    # Emission
    emissive_strength: float = 2.0
    diffusion: float = 0.5  # 0 = clear, 1 = diffused

    # Current value (for rendering at specific position)
    value: float = 0.5  # 0.0 to 1.0

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "fader_led_enabled": self.enabled,
            "fader_led_position": self.position,
            "fader_led_segment_count": self.segment_count,
            "fader_led_segment_height": self.segment_height,
            "fader_led_segment_width": self.segment_width,
            "fader_led_segment_spacing": self.segment_spacing,
            "fader_led_color_zones": self.color_zones,
            "fader_led_response": self.response.value,
            "fader_led_hold_time": self.hold_time,
            "fader_led_emissive_strength": self.emissive_strength,
            "fader_led_diffusion": self.diffusion,
            "fader_led_value": self.value,
        }


# =============================================================================
# COMPLETE FADER CONFIG
# =============================================================================

@dataclass
class FaderConfig:
    """
    Complete configuration for a fader control.
    """
    # Identity
    name: str = "Fader"
    fader_type: FaderType = FaderType.CHANNEL

    # Main dimensions
    travel_length: float = 0.100   # Travel length (100mm = 0.1m)
    width: float = 0.025           # Overall width
    height: float = 0.030          # Overall height (standing)

    # Position (where fader knob currently is, 0-1 normalized)
    position: float = 0.7          # Default to ~0dB position

    # Components
    knob: FaderKnobConfig = field(default_factory=FaderKnobConfig)
    track: TrackConfig = field(default_factory=TrackConfig)
    scale: ScaleConfig = field(default_factory=ScaleConfig)
    led_meter: LEDMeterConfig = field(default_factory=LEDMeterConfig)

    # Mounting
    panel_mount: bool = True
    mount_height: float = 0.002    # Height above panel surface

    def to_params(self) -> Dict[str, Any]:
        """Convert all components to parameter dictionary."""
        params = {
            "fader_name": self.name,
            "fader_type": self.fader_type.value,
            "fader_travel_length": self.travel_length,
            "fader_width": self.width,
            "fader_height": self.height,
            "fader_position": self.position,
            "fader_panel_mount": self.panel_mount,
            "fader_mount_height": self.mount_height,
        }
        params.update(self.knob.to_params())
        params.update(self.track.to_params())
        params.update(self.scale.to_params())
        params.update(self.led_meter.to_params())
        return params

    @classmethod
    def from_preset(cls, preset_name: str) -> "FaderConfig":
        """
        Create fader config from a named preset.
        """
        return FADER_PRESETS.get(preset_name, cls())


# =============================================================================
# FADER PRESETS
# =============================================================================

FADER_PRESETS: Dict[str, FaderConfig] = {

    # -------------------------------------------------------------------------
    # SSL 4000 E - Channel Fader
    # -------------------------------------------------------------------------
    "ssl_4000_channel": FaderConfig(
        name="SSL 4000 Channel",
        fader_type=FaderType.CHANNEL,
        travel_length=0.100,
        width=0.025,
        height=0.030,
        position=0.7,

        knob=FaderKnobConfig(
            style=FaderKnobStyle.SQUARE,
            width=0.015,
            height=0.018,
            depth=0.008,
            corner_radius=0.001,
            color=(0.15, 0.15, 0.15),
            metallic=0.0,
            roughness=0.35,
            indicator_enabled=True,
            indicator_color=(1.0, 1.0, 1.0),
        ),

        track=TrackConfig(
            style=TrackStyle.EXPOSED,
            width=0.006,
            depth=0.003,
            color=(0.6, 0.6, 0.62),
            metallic=0.8,
            roughness=0.25,
        ),

        scale=ScaleConfig(
            enabled=True,
            position=ScalePosition.RIGHT,
            scale_type=ScaleType.DB,
            tick_height=0.003,
            major_tick_height=0.005,
            color=(0.7, 0.7, 0.7),
        ),

        led_meter=LEDMeterConfig(
            enabled=False,
        ),
    ),

    # -------------------------------------------------------------------------
    # Neve 88RS - Channel Fader
    # -------------------------------------------------------------------------
    "neve_88rs_channel": FaderConfig(
        name="Neve 88RS Channel",
        fader_type=FaderType.CHANNEL,
        travel_length=0.100,
        width=0.028,
        height=0.032,
        position=0.7,

        knob=FaderKnobConfig(
            style=FaderKnobStyle.ROUNDED,
            width=0.018,
            height=0.022,
            depth=0.010,
            corner_radius=0.003,
            grip_enabled=True,
            grip_pattern="ridges",
            grip_count=7,
            grip_depth=0.0004,
            color=(0.12, 0.12, 0.12),
            metallic=0.0,
            roughness=0.4,
            indicator_enabled=True,
            indicator_color=(1.0, 1.0, 1.0),
        ),

        track=TrackConfig(
            style=TrackStyle.EXPOSED,
            width=0.007,
            depth=0.004,
            color=(0.55, 0.55, 0.58),
            metallic=0.7,
            roughness=0.3,
        ),

        scale=ScaleConfig(
            enabled=True,
            position=ScalePosition.BOTH,
            scale_type=ScaleType.DB,
            tick_height=0.003,
            major_tick_height=0.005,
            color=(0.75, 0.75, 0.75),
        ),

        led_meter=LEDMeterConfig(
            enabled=False,
        ),
    ),

    # -------------------------------------------------------------------------
    # API Vision - Channel Fader
    # -------------------------------------------------------------------------
    "api_vision_channel": FaderConfig(
        name="API Vision Channel",
        fader_type=FaderType.CHANNEL,
        travel_length=0.100,
        width=0.024,
        height=0.028,
        position=0.7,

        knob=FaderKnobConfig(
            style=FaderKnobStyle.ANGLED,
            width=0.016,
            height=0.020,
            depth=0.009,
            top_angle=20.0,
            corner_radius=0.001,
            color=(0.1, 0.1, 0.1),
            metallic=0.0,
            roughness=0.35,
            indicator_enabled=True,
            indicator_color=(0.9, 0.9, 0.9),
        ),

        track=TrackConfig(
            style=TrackStyle.EXPOSED,
            width=0.005,
            depth=0.003,
            color=(0.65, 0.65, 0.68),
            metallic=0.85,
            roughness=0.2,
        ),

        scale=ScaleConfig(
            enabled=True,
            position=ScalePosition.RIGHT,
            scale_type=ScaleType.DB,
            tick_height=0.002,
            major_tick_height=0.004,
            color=(0.8, 0.8, 0.8),
        ),

        led_meter=LEDMeterConfig(
            enabled=False,
        ),
    ),

    # -------------------------------------------------------------------------
    # Modern Digital Console - With LED Meter
    # -------------------------------------------------------------------------
    "modern_digital": FaderConfig(
        name="Modern Digital Fader",
        fader_type=FaderType.CHANNEL,
        travel_length=0.100,
        width=0.030,
        height=0.030,
        position=0.7,

        knob=FaderKnobConfig(
            style=FaderKnobStyle.TAPERED,
            width=0.016,
            height=0.020,
            depth=0.010,
            taper_ratio=0.85,
            corner_radius=0.002,
            grip_enabled=True,
            grip_pattern="ridges",
            grip_count=5,
            grip_depth=0.0003,
            color=(0.08, 0.08, 0.08),
            metallic=0.0,
            roughness=0.5,
            indicator_enabled=True,
            indicator_color=(0.3, 0.8, 1.0),  # Cyan
        ),

        track=TrackConfig(
            style=TrackStyle.LED_SLOT,
            width=0.008,
            depth=0.004,
            color=(0.2, 0.2, 0.22),
            metallic=0.0,
            roughness=0.6,
        ),

        scale=ScaleConfig(
            enabled=True,
            position=ScalePosition.LEFT,
            scale_type=ScaleType.DB,
            tick_height=0.002,
            major_tick_height=0.004,
            color=(0.6, 0.6, 0.6),
        ),

        led_meter=LEDMeterConfig(
            enabled=True,
            position="beside_track",
            segment_count=12,
            segment_height=0.006,
            segment_width=0.003,
            segment_spacing=0.001,
            color_zones=[
                {"threshold": 0.0, "color": [0.0, 1.0, 0.0]},
                {"threshold": 0.7, "color": [1.0, 1.0, 0.0]},
                {"threshold": 0.9, "color": [1.0, 0.0, 0.0]},
            ],
            response=LEDResponse.PEAK,
            emissive_strength=2.5,
            value=0.65,
        ),
    ),

    # -------------------------------------------------------------------------
    # Short Fader - Compact
    # -------------------------------------------------------------------------
    "short_compact": FaderConfig(
        name="Short Compact Fader",
        fader_type=FaderType.SHORT,
        travel_length=0.060,
        width=0.020,
        height=0.025,
        position=0.6,

        knob=FaderKnobConfig(
            style=FaderKnobStyle.SQUARE,
            width=0.012,
            height=0.015,
            depth=0.006,
            corner_radius=0.001,
            color=(0.2, 0.2, 0.2),
            metallic=0.0,
            roughness=0.4,
            indicator_enabled=True,
            indicator_color=(1.0, 1.0, 1.0),
        ),

        track=TrackConfig(
            style=TrackStyle.COVERED_SLOT,
            width=0.004,
            depth=0.002,
            color=(0.5, 0.5, 0.52),
            metallic=0.6,
            roughness=0.4,
            slot_cover_enabled=True,
            slot_cover_color=(0.15, 0.15, 0.15),
        ),

        scale=ScaleConfig(
            enabled=True,
            position=ScalePosition.RIGHT,
            scale_type=ScaleType.ZERO_TEN,
            tick_height=0.002,
            major_tick_height=0.003,
            color=(0.7, 0.7, 0.7),
        ),

        led_meter=LEDMeterConfig(
            enabled=False,
        ),
    ),

    # -------------------------------------------------------------------------
    # Mini Fader - Pocket Operator Style
    # -------------------------------------------------------------------------
    "mini_pocket": FaderConfig(
        name="Mini Pocket Fader",
        fader_type=FaderType.MINI,
        travel_length=0.045,
        width=0.015,
        height=0.018,
        position=0.5,

        knob=FaderKnobConfig(
            style=FaderKnobStyle.ROUNDED,
            width=0.010,
            height=0.012,
            depth=0.005,
            corner_radius=0.002,
            color=(0.3, 0.3, 0.32),
            metallic=0.0,
            roughness=0.5,
            indicator_enabled=False,
        ),

        track=TrackConfig(
            style=TrackStyle.COVERED_SLOT,
            width=0.003,
            depth=0.002,
            color=(0.4, 0.4, 0.42),
            metallic=0.0,
            roughness=0.6,
            slot_cover_enabled=True,
            slot_cover_color=(0.25, 0.25, 0.25),
        ),

        scale=ScaleConfig(
            enabled=False,
        ),

        led_meter=LEDMeterConfig(
            enabled=False,
        ),
    ),
}


def list_fader_presets() -> List[str]:
    """List available fader presets."""
    return list(FADER_PRESETS.keys())


def get_fader_preset(name: str) -> FaderConfig:
    """
    Get a fader preset by name.

    Args:
        name: Preset name

    Returns:
        FaderConfig instance

    Raises:
        KeyError: If preset not found
    """
    if name not in FADER_PRESETS:
        available = ", ".join(FADER_PRESETS.keys())
        raise KeyError(f"Fader preset '{name}' not found. Available: {available}")
    return FADER_PRESETS[name]
