"""
Button Configuration System

Configuration dataclasses for button control elements.

Button Types:
- Momentary: Press and hold (transport controls)
- Latching: Press to toggle (channel selects)
- Illuminated: LED integrated
- Cap Switch: Removable cap (SSL, Neve)
- Membrane: Flat sealed
- Rubber: Soft silicone (Roland TR-8)
- Metal Dome: Clicky metal (industrial)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, Dict, Any, List


class ButtonType(Enum):
    """Button type classification."""
    MOMENTARY = "momentary"      # Press and hold
    LATCHING = "latching"        # Press to toggle
    ILLUMINATED = "illuminated"  # LED integrated
    CAP_SWITCH = "cap_switch"    # Removable cap
    MEMBRANE = "membrane"        # Flat sealed
    RUBBER = "rubber"            # Soft silicone
    METAL_DOME = "metal_dome"    # Clicky metal
    PUSH_ROTARY = "push_rotary"  # Encoder with switch


class ButtonShape(Enum):
    """Button shape options."""
    SQUARE = "square"
    ROUND = "round"
    RECTANGULAR = "rectangular"
    CUSTOM = "custom"


class ButtonSurface(Enum):
    """Button surface texture."""
    FLAT = "flat"
    DOMED = "domed"
    CONCAVE = "concave"
    TEXTURED = "textured"


class TexturePattern(Enum):
    """Texture pattern for button surface."""
    NONE = "none"
    LINES = "lines"
    DOTS = "dots"
    CROSSHATCH = "crosshatch"
    KNURL = "knurl"


class IlluminationType(Enum):
    """LED illumination style."""
    NONE = "none"
    RING = "ring"          # LED ring around button
    BACKLIT = "backlit"    # Entire surface glows
    ICON = "icon"          # Icon/symbol illumination
    EDGE = "edge"          # Edge lighting
    SPOT = "spot"          # Single LED spot


class TactileFeedback(Enum):
    """Tactile feedback level."""
    NONE = "none"
    SOFT = "soft"
    MEDIUM = "medium"
    FIRM = "firm"


class ActuationForce(Enum):
    """Button actuation force."""
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class CapShape(Enum):
    """Button cap shape options."""
    SQUARE = "square"
    ROUND = "round"
    RECTANGULAR = "rectangular"
    FLAT = "flat"
    RAISED = "raised"


@dataclass
class ButtonCapConfig:
    """Configuration for removable button cap system."""
    enabled: bool = False
    shape: CapShape = CapShape.SQUARE
    color: Tuple[float, float, float] = (0.1, 0.1, 0.1)
    height: float = 0.004          # 4mm cap height
    removable: bool = True
    inset: float = 0.001           # How deep cap sits in base

    # Material
    metallic: float = 0.0
    roughness: float = 0.5

    def to_params(self) -> Dict[str, Any]:
        return {
            "cap_enabled": self.enabled,
            "cap_shape": self.shape.value,
            "cap_color": list(self.color),
            "cap_height": self.height,
            "cap_removable": self.removable,
            "cap_inset": self.inset,
            "cap_metallic": self.metallic,
            "cap_roughness": self.roughness,
        }


@dataclass
class IlluminationConfig:
    """Configuration for button LED illumination."""
    enabled: bool = False
    type: IlluminationType = IlluminationType.BACKLIT

    # Colors per state
    color_off: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    color_on: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    color_active: Tuple[float, float, float] = (1.0, 0.0, 0.0)

    # Intensity
    brightness: float = 1.0
    diffusion: float = 0.3          # 0=sharp, 1=soft glow

    # Animation
    animation: str = "none"         # none, pulse, flash, fade
    animation_speed: float = 1.0    # Hz for pulse/flash

    # Ring-specific
    ring_width: float = 0.002       # 2mm ring width

    def to_params(self) -> Dict[str, Any]:
        return {
            "illum_enabled": self.enabled,
            "illum_type": self.type.value,
            "illum_color_off": list(self.color_off),
            "illum_color_on": list(self.color_on),
            "illum_color_active": list(self.color_active),
            "illum_brightness": self.brightness,
            "illum_diffusion": self.diffusion,
            "illum_animation": self.animation,
            "illum_animation_speed": self.animation_speed,
            "illum_ring_width": self.ring_width,
        }


@dataclass
class ButtonConfig:
    """
    Complete button configuration.

    Default values represent a generic console button.
    """
    name: str = "Button"

    # Type
    button_type: ButtonType = ButtonType.MOMENTARY

    # Geometry
    shape: ButtonShape = ButtonShape.SQUARE
    width: float = 0.010             # 10mm width
    length: float = 0.010            # 10mm length (for rectangular)
    depth_unpressed: float = 0.005   # 5mm height when unpressed
    travel: float = 0.001            # 1mm travel depth

    # Surface
    surface: ButtonSurface = ButtonSurface.FLAT
    texture_pattern: TexturePattern = TexturePattern.NONE
    texture_depth: float = 0.0002    # 0.2mm texture depth

    # Colors/Material
    color: Tuple[float, float, float] = (0.15, 0.15, 0.15)
    metallic: float = 0.0
    roughness: float = 0.4

    # Cap system
    cap: ButtonCapConfig = field(default_factory=ButtonCapConfig)

    # Illumination
    illumination: IlluminationConfig = field(default_factory=IlluminationConfig)

    # Feedback
    tactile_feedback: TactileFeedback = TactileFeedback.MEDIUM
    audible_click: bool = False
    actuation_force: ActuationForce = ActuationForce.MEDIUM

    # State (for visualization)
    pressed: bool = False
    active: bool = False

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        params = {
            "button_name": self.name,
            "button_type": self.button_type.value,
            "button_shape": self.shape.value,
            "button_width": self.width,
            "button_length": self.length,
            "button_depth": self.depth_unpressed,
            "button_travel": self.travel,
            "button_surface": self.surface.value,
            "button_texture": self.texture_pattern.value,
            "button_texture_depth": self.texture_depth,
            "button_color": list(self.color),
            "button_metallic": self.metallic,
            "button_roughness": self.roughness,
            "tactile_feedback": self.tactile_feedback.value,
            "audible_click": self.audible_click,
            "actuation_force": self.actuation_force.value,
            "pressed": self.pressed,
            "active": self.active,
        }
        params.update(self.cap.to_params())
        params.update(self.illumination.to_params())
        return params


# =============================================================================
# PRESETS
# =============================================================================

BUTTON_PRESETS: Dict[str, ButtonConfig] = {}


def _register_preset(name: str, config: ButtonConfig) -> None:
    """Register a button preset."""
    BUTTON_PRESETS[name] = config


# -----------------------------------------------------------------------------
# Console Buttons
# -----------------------------------------------------------------------------

# Neve 1073 style - colored cap push buttons
_register_preset("neve_1073_momentary", ButtonConfig(
    name="Neve 1073 Momentary",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.SQUARE,
    width=0.010,
    length=0.010,
    depth_unpressed=0.006,
    travel=0.0015,
    surface=ButtonSurface.FLAT,
    color=(0.15, 0.15, 0.15),
    cap=ButtonCapConfig(
        enabled=True,
        shape=CapShape.SQUARE,
        color=(0.9, 0.2, 0.15),  # Red cap
        height=0.004,
        metallic=0.0,
        roughness=0.3,
    ),
    tactile_feedback=TactileFeedback.FIRM,
    actuation_force=ActuationForce.MEDIUM,
))

_register_preset("neve_1073_cap_blue", ButtonConfig(
    name="Neve 1073 Blue Cap",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.SQUARE,
    width=0.010,
    length=0.010,
    depth_unpressed=0.006,
    travel=0.0015,
    surface=ButtonSurface.FLAT,
    color=(0.15, 0.15, 0.15),
    cap=ButtonCapConfig(
        enabled=True,
        shape=CapShape.SQUARE,
        color=(0.15, 0.35, 0.85),  # Blue cap
        height=0.004,
    ),
    tactile_feedback=TactileFeedback.FIRM,
))

_register_preset("neve_1073_cap_green", ButtonConfig(
    name="Neve 1073 Green Cap",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.SQUARE,
    width=0.010,
    length=0.010,
    depth_unpressed=0.006,
    travel=0.0015,
    surface=ButtonSurface.FLAT,
    color=(0.15, 0.15, 0.15),
    cap=ButtonCapConfig(
        enabled=True,
        shape=CapShape.SQUARE,
        color=(0.15, 0.75, 0.25),  # Green cap
        height=0.004,
    ),
    tactile_feedback=TactileFeedback.FIRM,
))

# SSL 4000 style - square buttons with built-in LEDs
_register_preset("ssl_4000_square", ButtonConfig(
    name="SSL 4000 Square",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.SQUARE,
    width=0.012,
    length=0.012,
    depth_unpressed=0.004,
    travel=0.001,
    surface=ButtonSurface.FLAT,
    color=(0.25, 0.25, 0.27),
    cap=ButtonCapConfig(enabled=False),
    illumination=IlluminationConfig(
        enabled=True,
        type=IlluminationType.SPOT,
        color_off=(0.0, 0.0, 0.0),
        color_on=(0.0, 0.9, 0.1),
        brightness=0.8,
        diffusion=0.2,
    ),
    tactile_feedback=TactileFeedback.MEDIUM,
))

# API 2500 style - Carling toggle switch style
_register_preset("api_toggle", ButtonConfig(
    name="API Toggle",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.RECTANGULAR,
    width=0.008,
    length=0.015,
    depth_unpressed=0.010,
    travel=0.003,
    surface=ButtonSurface.FLAT,
    color=(0.1, 0.1, 0.1),
    metallic=0.3,
    roughness=0.3,
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.FIRM,
    audible_click=True,
))

# -----------------------------------------------------------------------------
# Synth Buttons
# -----------------------------------------------------------------------------

# Roland TR-808 style - rubber buttons
_register_preset("roland_808_rubber", ButtonConfig(
    name="Roland TR-808 Rubber",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.ROUND,
    width=0.012,
    length=0.012,
    depth_unpressed=0.005,
    travel=0.002,
    surface=ButtonSurface.DOMED,
    texture_pattern=TexturePattern.NONE,
    color=(0.15, 0.15, 0.15),
    roughness=0.7,
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.SOFT,
    actuation_force=ActuationForce.LIGHT,
))

# Moog style - premium rubberized
_register_preset("moog_premium", ButtonConfig(
    name="Moog Premium",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.ROUND,
    width=0.010,
    length=0.010,
    depth_unpressed=0.004,
    travel=0.0015,
    surface=ButtonSurface.FLAT,
    color=(0.08, 0.08, 0.08),
    roughness=0.6,
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.MEDIUM,
))

# Sequential Prophet style
_register_preset("sequential_prophet", ButtonConfig(
    name="Sequential Prophet",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.SQUARE,
    width=0.010,
    length=0.010,
    depth_unpressed=0.003,
    travel=0.001,
    surface=ButtonSurface.FLAT,
    color=(0.12, 0.12, 0.12),
    illumination=IlluminationConfig(
        enabled=True,
        type=IlluminationType.BACKLIT,
        color_off=(0.0, 0.0, 0.0),
        color_on=(0.2, 0.6, 1.0),
        brightness=0.6,
    ),
    cap=ButtonCapConfig(enabled=False),
))

# -----------------------------------------------------------------------------
# Pedal Buttons (Footswitches)
# -----------------------------------------------------------------------------

# Boss style - metal dome footswitch
_register_preset("boss_footswitch", ButtonConfig(
    name="Boss Footswitch",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.ROUND,
    width=0.025,
    length=0.025,
    depth_unpressed=0.008,
    travel=0.003,
    surface=ButtonSurface.DOMED,
    color=(0.7, 0.7, 0.72),
    metallic=0.9,
    roughness=0.2,
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.FIRM,
    audible_click=True,
))

# MXR style - smaller round button
_register_preset("mxr_button", ButtonConfig(
    name="MXR Button",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.ROUND,
    width=0.018,
    length=0.018,
    depth_unpressed=0.006,
    travel=0.002,
    surface=ButtonSurface.DOMED,
    color=(0.2, 0.2, 0.2),
    metallic=0.7,
    roughness=0.3,
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.FIRM,
))

# Electro-Harmonix style
_register_preset("ehx_footswitch", ButtonConfig(
    name="EHX Footswitch",
    button_type=ButtonType.LATCHING,
    shape=ButtonShape.ROUND,
    width=0.020,
    length=0.020,
    depth_unpressed=0.007,
    travel=0.003,
    surface=ButtonSurface.DOMED,
    color=(0.6, 0.6, 0.62),
    metallic=0.8,
    roughness=0.25,
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.FIRM,
    audible_click=True,
))

# -----------------------------------------------------------------------------
# Modern Digital / Illuminated
# -----------------------------------------------------------------------------

# Modern LED ring button
_register_preset("modern_led_ring", ButtonConfig(
    name="Modern LED Ring",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.ROUND,
    width=0.012,
    length=0.012,
    depth_unpressed=0.004,
    travel=0.001,
    surface=ButtonSurface.FLAT,
    color=(0.1, 0.1, 0.1),
    cap=ButtonCapConfig(enabled=False),
    illumination=IlluminationConfig(
        enabled=True,
        type=IlluminationType.RING,
        color_off=(0.1, 0.1, 0.1),
        color_on=(0.0, 0.8, 1.0),
        color_active=(1.0, 0.5, 0.0),
        brightness=1.0,
        ring_width=0.002,
    ),
    tactile_feedback=TactileFeedback.MEDIUM,
))

# Membrane button (budget gear)
_register_preset("membrane_button", ButtonConfig(
    name="Membrane Button",
    button_type=ButtonType.MEMBRANE,
    shape=ButtonShape.SQUARE,
    width=0.010,
    length=0.010,
    depth_unpressed=0.002,
    travel=0.0005,
    surface=ButtonSurface.FLAT,
    color=(0.2, 0.2, 0.22),
    cap=ButtonCapConfig(enabled=False),
    tactile_feedback=TactileFeedback.SOFT,
))

# Transport button (Play/Record)
_register_preset("transport_play", ButtonConfig(
    name="Transport Play",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.ROUND,
    width=0.015,
    length=0.015,
    depth_unpressed=0.005,
    travel=0.0015,
    surface=ButtonSurface.CONCAVE,
    color=(0.1, 0.1, 0.1),
    cap=ButtonCapConfig(enabled=False),
    illumination=IlluminationConfig(
        enabled=True,
        type=IlluminationType.BACKLIT,
        color_off=(0.05, 0.05, 0.05),
        color_on=(0.1, 0.9, 0.1),
        brightness=0.8,
    ),
    tactile_feedback=TactileFeedback.MEDIUM,
))

_register_preset("transport_record", ButtonConfig(
    name="Transport Record",
    button_type=ButtonType.MOMENTARY,
    shape=ButtonShape.ROUND,
    width=0.015,
    length=0.015,
    depth_unpressed=0.005,
    travel=0.0015,
    surface=ButtonSurface.CONCAVE,
    color=(0.1, 0.1, 0.1),
    cap=ButtonCapConfig(enabled=False),
    illumination=IlluminationConfig(
        enabled=True,
        type=IlluminationType.BACKLIT,
        color_off=(0.05, 0.05, 0.05),
        color_on=(0.9, 0.1, 0.1),
        animation="pulse",
        animation_speed=2.0,
        brightness=0.9,
    ),
    tactile_feedback=TactileFeedback.MEDIUM,
))


def list_button_presets() -> List[str]:
    """List all available button preset names."""
    return list(BUTTON_PRESETS.keys())


def get_button_preset(name: str) -> ButtonConfig:
    """Get a button preset by name.

    Args:
        name: Preset name

    Returns:
        ButtonConfig instance

    Raises:
        KeyError: If preset not found
    """
    if name not in BUTTON_PRESETS:
        available = ", ".join(list_button_presets())
        raise KeyError(f"Button preset '{name}' not found. Available: {available}")
    return BUTTON_PRESETS[name]
