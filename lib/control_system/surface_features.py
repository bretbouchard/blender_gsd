"""
Surface Features Module

Provides surface modification systems for control surfaces:
- Knurling (vertical ridges for grip)
- Ribbing (horizontal rings)
- Grooves (channels)
- Indicators (position markers)
- Collet/Cap systems
- Backlight support

All features are designed to work with Geometry Nodes for procedural generation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class KnurlPattern(Enum):
    """Knurling pattern types."""
    STRAIGHT = "straight"      # Vertical lines
    DIAMOND = "diamond"        # Cross-hatched diamond pattern
    HELICAL = "helical"        # Spiral pattern


class IndicatorType(Enum):
    """Indicator/pointer types."""
    LINE = "line"              # Simple line marker
    DOT = "dot"                # Single dot marker
    POINTER = "pointer"        # Extended pointer (chicken head style)
    SKIRT = "skirt"            # Marker on skirt edge
    ENGRAVED = "engraved"      # Recessed indicator
    BACKLIT = "backlit"        # Illuminated indicator


class GroovePattern(Enum):
    """Groove pattern types."""
    SINGLE = "single"          # Single ring
    MULTI = "multi"            # Multiple parallel rings
    SPIRAL = "spiral"          # Helical groove


# =============================================================================
# KNURLING SYSTEM
# =============================================================================

@dataclass
class KnurlingConfig:
    """
    Configuration for knurling surface feature.

    Knurling creates vertical ridges around the circumference of a knob
    for improved grip and tactile feedback.
    """
    # Enable/disable
    enabled: bool = False

    # Pattern
    pattern: KnurlPattern = KnurlPattern.STRAIGHT

    # Dimensions
    count: int = 30            # Number of ridges around circumference
    depth: float = 0.0008      # Depth of ridges (meters)

    # Zone control (normalized 0-1 where 0=bottom, 1=top)
    z_start: float = 0.0       # Where knurling begins
    z_end: float = 1.0         # Where knurling ends
    fade: float = 0.0          # Smooth transition at zone edges

    # Profile shape (0=flat/trapezoid, 0.5=round/sinusoidal, 1=sharp/V)
    profile: float = 0.5

    # Diamond/Helical specific
    cross_angle: float = 0.0   # Angle for diamond pattern (radians, 0 = straight)
    helix_pitch: float = 0.0   # Vertical rise per rotation for helical

    # Advanced
    randomize: float = 0.0     # Random variation in depth (0-1)
    chamfer: float = 0.0       # Edge chamfer amount

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "knurl_enabled": self.enabled,
            "knurl_pattern": self.pattern.value,
            "knurl_count": self.count,
            "knurl_depth": self.depth,
            "knurl_z_start": self.z_start,
            "knurl_z_end": self.z_end,
            "knurl_fade": self.fade,
            "knurl_profile": self.profile,
            "knurl_cross_angle": self.cross_angle,
            "knurl_helix_pitch": self.helix_pitch,
            "knurl_randomize": self.randomize,
            "knurl_chamfer": self.chamfer,
        }


# =============================================================================
# RIBBING SYSTEM
# =============================================================================

@dataclass
class RibbingConfig:
    """
    Configuration for ribbing surface feature.

    Ribbing creates horizontal rings around a knob, common on
    vintage equipment and premium controls.
    """
    # Enable/disable
    enabled: bool = False

    # Dimensions
    count: int = 5             # Number of ribs
    depth: float = 0.0006      # Depth of each rib (meters)
    width: float = 0.001       # Width of each rib (meters)
    spacing: float = 0.002     # Space between ribs (meters)

    # Zone control (normalized 0-1)
    z_start: float = 0.1       # Where ribbing begins
    z_end: float = 0.9         # Where ribbing ends

    # Profile
    profile: float = 0.5       # 0=flat, 0.5=round, 1=sharp
    edge_radius: float = 0.0   # Rounding on rib edges

    # Pattern variation
    variable_spacing: bool = False  # Enable variable spacing
    spacing_curve: List[float] = field(default_factory=lambda: [])  # Spacing multipliers

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "rib_enabled": self.enabled,
            "rib_count": self.count,
            "rib_depth": self.depth,
            "rib_width": self.width,
            "rib_spacing": self.spacing,
            "rib_z_start": self.z_start,
            "rib_z_end": self.z_end,
            "rib_profile": self.profile,
            "rib_edge_radius": self.edge_radius,
            "rib_variable_spacing": self.variable_spacing,
            "rib_spacing_curve": self.spacing_curve,
        }


# =============================================================================
# GROOVE SYSTEM
# =============================================================================

@dataclass
class GrooveConfig:
    """
    Configuration for groove surface feature.

    Grooves create channels in the knob surface, often used
    for decorative or functional purposes.
    """
    # Enable/disable
    enabled: bool = False

    # Pattern
    pattern: GroovePattern = GroovePattern.SINGLE

    # Dimensions
    depth: float = 0.001       # Depth of groove (meters)
    width: float = 0.002       # Width of groove (meters)

    # Position (normalized 0-1)
    z_position: float = 0.5    # Vertical position of groove center

    # Multi-groove specific
    count: int = 1             # Number of grooves
    spacing: float = 0.003     # Spacing between grooves (meters)

    # Spiral specific
    spiral_turns: float = 2.0  # Number of full rotations

    # Profile
    profile: float = 0.3       # 0=flat bottom, 0.5=round, 1=V-shape
    edge_radius: float = 0.0   # Rounding on groove edges

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "groove_enabled": self.enabled,
            "groove_pattern": self.pattern.value,
            "groove_depth": self.depth,
            "groove_width": self.width,
            "groove_z_position": self.z_position,
            "groove_count": self.count,
            "groove_spacing": self.spacing,
            "groove_spiral_turns": self.spiral_turns,
            "groove_profile": self.profile,
            "groove_edge_radius": self.edge_radius,
        }


# =============================================================================
# INDICATOR SYSTEM
# =============================================================================

@dataclass
class IndicatorConfig:
    """
    Configuration for position indicator/pointer.

    Indicators show the current position of a knob on its scale.
    """
    # Enable/disable
    enabled: bool = True

    # Type
    indicator_type: IndicatorType = IndicatorType.LINE

    # Dimensions
    length: float = 0.012      # Length of indicator (meters)
    width: float = 0.08        # Angular width (radians)
    height: float = 0.0005     # Height above surface (meters)

    # Position
    z_offset: float = 0.0      # Vertical offset from top (meters)
    radial_offset: float = 0.0 # Radial offset from edge (meters, negative = inward)

    # Colors
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    emissive: bool = False
    emissive_strength: float = 1.0

    # Engraved specific
    engrave_depth: float = 0.0005  # Depth for engraved type

    # Backlit specific
    backlight_color: Tuple[float, float, float] = (0.2, 0.8, 1.0)
    backlight_intensity: float = 2.0
    backlight_spread: float = 0.002  # Glow spread (meters)

    # Dot specific
    dot_diameter: float = 0.003   # Diameter for dot type

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "indicator_enabled": self.enabled,
            "indicator_type": self.indicator_type.value,
            "indicator_length": self.length,
            "indicator_width": self.width,
            "indicator_height": self.height,
            "indicator_z_offset": self.z_offset,
            "indicator_radial_offset": self.radial_offset,
            "indicator_color": list(self.color),
            "indicator_emissive": self.emissive,
            "indicator_emissive_strength": self.emissive_strength,
            "indicator_engrave_depth": self.engrave_depth,
            "indicator_backlight_color": list(self.backlight_color),
            "indicator_backlight_intensity": self.backlight_intensity,
            "indicator_backlight_spread": self.backlight_spread,
            "indicator_dot_diameter": self.dot_diameter,
        }


# =============================================================================
# COLLET & CAP SYSTEM
# =============================================================================

@dataclass
class ColletConfig:
    """
    Configuration for collet (metal ring) feature.

    Collets are decorative or functional metal rings around knobs,
    common on Neve 88RS and other premium consoles.
    """
    # Enable/disable
    enabled: bool = False

    # Dimensions
    height: float = 0.010      # Height of collet (meters)
    diameter: float = 0.020    # Outer diameter (meters)
    thickness: float = 0.002   # Wall thickness (meters)

    # Position
    z_position: float = 0.0    # Bottom position (meters)
    gap: float = 0.001         # Gap above collet (meters)

    # Material
    metallic: float = 0.9
    roughness: float = 0.2
    color: Tuple[float, float, float] = (0.7, 0.7, 0.72)  # Silver

    # Style
    knurled: bool = False      # Add knurling to collet surface
    knurl_count: int = 40

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "collet_enabled": self.enabled,
            "collet_height": self.height,
            "collet_diameter": self.diameter,
            "collet_thickness": self.thickness,
            "collet_z_position": self.z_position,
            "collet_gap": self.gap,
            "collet_metallic": self.metallic,
            "collet_roughness": self.roughness,
            "collet_color": list(self.color),
            "collet_knurled": self.knurled,
            "collet_knurl_count": self.knurl_count,
        }


@dataclass
class CapConfig:
    """
    Configuration for cap/insert feature.

    Caps are inset or overlay elements on knob tops,
    often with different colors or materials.
    """
    # Enable/disable
    enabled: bool = False

    # Dimensions
    diameter: float = 0.012    # Cap diameter (meters)
    height: float = 0.003      # Cap height (meters)
    inset: float = 0.001       # Inset from top surface (meters)

    # Style
    domed: bool = False        # Domed vs flat top
    dome_radius: float = 0.006

    # Material
    metallic: float = 0.0
    roughness: float = 0.3
    color: Tuple[float, float, float] = (0.2, 0.2, 0.2)

    # Indicator integration
    has_indicator: bool = False  # Cap has its own indicator
    indicator_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "cap_enabled": self.enabled,
            "cap_diameter": self.diameter,
            "cap_height": self.height,
            "cap_inset": self.inset,
            "cap_domed": self.domed,
            "cap_dome_radius": self.dome_radius,
            "cap_metallic": self.metallic,
            "cap_roughness": self.roughness,
            "cap_color": list(self.color),
            "cap_has_indicator": self.has_indicator,
            "cap_indicator_color": list(self.indicator_color),
        }


# =============================================================================
# BACKLIGHT SYSTEM
# =============================================================================

@dataclass
class BacklightConfig:
    """
    Configuration for backlit indicator feature.

    Backlights provide illumination for indicators or entire knobs,
    common on modern digital consoles and DJ equipment.
    """
    # Enable/disable
    enabled: bool = False

    # Light properties
    color: Tuple[float, float, float] = (0.2, 0.8, 1.0)  # Cyan default
    intensity: float = 2.0
    spread: float = 0.003      # Glow spread distance (meters)

    # Animation
    animated: bool = False
    animation_type: str = "static"  # static, pulse, breath, chase

    # Zone (for ring backlights)
    z_start: float = 0.0
    z_end: float = 1.0

    # Ring specific
    ring_angle_start: float = 0.0    # Start angle (radians)
    ring_angle_end: float = 6.28318  # End angle (radians, 2*pi = full ring)
    ring_segments: int = 16          # Number of LED segments

    # Value response
    responds_to_value: bool = False  # Light responds to knob position
    value_min: float = 0.0
    value_max: float = 1.0

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary."""
        return {
            "backlight_enabled": self.enabled,
            "backlight_color": list(self.color),
            "backlight_intensity": self.intensity,
            "backlight_spread": self.spread,
            "backlight_animated": self.animated,
            "backlight_animation_type": self.animation_type,
            "backlight_z_start": self.z_start,
            "backlight_z_end": self.z_end,
            "backlight_ring_angle_start": self.ring_angle_start,
            "backlight_ring_angle_end": self.ring_angle_end,
            "backlight_ring_segments": self.ring_segments,
            "backlight_responds_to_value": self.responds_to_value,
            "backlight_value_min": self.value_min,
            "backlight_value_max": self.value_max,
        }


# =============================================================================
# COMPOSITE SURFACE FEATURES
# =============================================================================

@dataclass
class SurfaceFeatures:
    """
    Complete surface feature configuration for a control element.

    Combines all surface features into a single configuration object.
    """
    knurling: KnurlingConfig = field(default_factory=KnurlingConfig)
    ribbing: RibbingConfig = field(default_factory=RibbingConfig)
    grooves: GrooveConfig = field(default_factory=GrooveConfig)
    indicator: IndicatorConfig = field(default_factory=IndicatorConfig)
    collet: ColletConfig = field(default_factory=ColletConfig)
    cap: CapConfig = field(default_factory=CapConfig)
    backlight: BacklightConfig = field(default_factory=BacklightConfig)

    def to_params(self) -> Dict[str, Any]:
        """Convert all features to parameter dictionary."""
        params = {}
        params.update(self.knurling.to_params())
        params.update(self.ribbing.to_params())
        params.update(self.grooves.to_params())
        params.update(self.indicator.to_params())
        params.update(self.collet.to_params())
        params.update(self.cap.to_params())
        params.update(self.backlight.to_params())
        return params

    @classmethod
    def from_preset(cls, preset_name: str) -> "SurfaceFeatures":
        """
        Create surface features from a named preset.

        Args:
            preset_name: Name of preset (e.g., "neve_1073", "ssl_4000")

        Returns:
            SurfaceFeatures configured for the preset
        """
        return SURFACE_PRESETS.get(preset_name, cls())


# =============================================================================
# PRESETS
# =============================================================================

SURFACE_PRESETS: Dict[str, SurfaceFeatures] = {

    # -------------------------------------------------------------------------
    # Neve 1073 - Classic Chicken Head
    # -------------------------------------------------------------------------
    "neve_1073": SurfaceFeatures(
        knurling=KnurlingConfig(enabled=False),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.POINTER,
            length=0.014,
            width=0.10,
            height=0.0008,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # Neve 88RS - Modern Collet Style
    # -------------------------------------------------------------------------
    "neve_88rs": SurfaceFeatures(
        knurling=KnurlingConfig(enabled=False),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.LINE,
            length=0.012,
            width=0.08,
            height=0.0005,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(
            enabled=True,
            height=0.010,
            diameter=0.020,
            thickness=0.002,
            metallic=0.9,
            roughness=0.2,
            color=(0.7, 0.7, 0.72),
        ),
        cap=CapConfig(
            enabled=True,
            diameter=0.014,
            height=0.003,
            inset=0.001,
            color=(0.15, 0.15, 0.15),
        ),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # SSL 4000 E - Domed with Center Dot
    # -------------------------------------------------------------------------
    "ssl_4000": SurfaceFeatures(
        knurling=KnurlingConfig(
            enabled=True,
            count=20,
            depth=0.0004,
            z_start=0.0,
            z_end=0.6,
            fade=0.1,
            profile=0.5,
        ),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.DOT,
            dot_diameter=0.004,
            height=0.0003,
            color=(0.2, 0.4, 0.8),  # Blue center
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # API 2500 - American Console
    # -------------------------------------------------------------------------
    "api_2500": SurfaceFeatures(
        knurling=KnurlingConfig(
            enabled=True,
            count=36,
            depth=0.0006,
            z_start=0.0,
            z_end=1.0,
            profile=0.7,  # Slightly sharp
        ),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(
            enabled=True,
            pattern=GroovePattern.SINGLE,
            depth=0.0008,
            width=0.002,
            z_position=0.3,
        ),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.POINTER,
            length=0.016,
            width=0.08,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # Moog Voyager - Soft Touch
    # -------------------------------------------------------------------------
    "moog_voyager": SurfaceFeatures(
        knurling=KnurlingConfig(enabled=False),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.POINTER,
            length=0.016,
            width=0.09,
            color=(1.0, 1.0, 1.0),
            emissive=True,
            emissive_strength=0.5,
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(
            enabled=True,
            color=(0.4, 0.6, 1.0),  # Blue glow
            intensity=1.5,
            spread=0.005,
            z_start=0.0,
            z_end=0.3,
        ),
    ),

    # -------------------------------------------------------------------------
    # Roland TR-808 - Iconic Drum Machine
    # -------------------------------------------------------------------------
    "roland_808": SurfaceFeatures(
        knurling=KnurlingConfig(
            enabled=True,
            count=24,
            depth=0.001,
            z_start=0.0,
            z_end=1.0,
            profile=0.6,
        ),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.LINE,
            length=0.010,
            width=0.07,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # MXR Phase 90 - Simple Pedal
    # -------------------------------------------------------------------------
    "mxr_phase90": SurfaceFeatures(
        knurling=KnurlingConfig(
            enabled=True,
            count=30,
            depth=0.0006,
            z_start=0.0,
            z_end=1.0,
            profile=0.7,
        ),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.LINE,
            length=0.008,
            width=0.06,
            height=0.0003,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # Sequential Prophet-5 - Vintage Synth
    # -------------------------------------------------------------------------
    "sequential_p5": SurfaceFeatures(
        knurling=KnurlingConfig(
            enabled=True,
            count=36,
            depth=0.0005,
            z_start=0.0,
            z_end=1.0,
            profile=0.6,
        ),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.LINE,
            length=0.012,
            width=0.07,
            height=0.0006,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(enabled=False),
        backlight=BacklightConfig(enabled=False),
    ),

    # -------------------------------------------------------------------------
    # Modern LED Ring - Digital Controller
    # -------------------------------------------------------------------------
    "modern_led_ring": SurfaceFeatures(
        knurling=KnurlingConfig(
            enabled=True,
            count=48,
            depth=0.0004,
            z_start=0.0,
            z_end=0.7,
            fade=0.1,
            profile=0.5,
        ),
        ribbing=RibbingConfig(enabled=False),
        grooves=GrooveConfig(enabled=False),
        indicator=IndicatorConfig(
            enabled=True,
            indicator_type=IndicatorType.LINE,
            length=0.010,
            width=0.06,
            color=(1.0, 1.0, 1.0),
        ),
        collet=ColletConfig(enabled=False),
        cap=CapConfig(
            enabled=True,
            diameter=0.012,
            height=0.002,
            color=(0.1, 0.1, 0.1),
        ),
        backlight=BacklightConfig(
            enabled=True,
            color=(0.0, 1.0, 0.5),  # Green
            intensity=3.0,
            spread=0.003,
            z_start=0.8,
            z_end=1.0,
            responds_to_value=True,
        ),
    ),
}


def list_presets() -> List[str]:
    """List available surface feature presets."""
    return list(SURFACE_PRESETS.keys())


def get_preset(name: str) -> SurfaceFeatures:
    """
    Get a surface features preset by name.

    Args:
        name: Preset name

    Returns:
        SurfaceFeatures instance

    Raises:
        KeyError: If preset not found
    """
    if name not in SURFACE_PRESETS:
        available = ", ".join(SURFACE_PRESETS.keys())
        raise KeyError(f"Preset '{name}' not found. Available: {available}")
    return SURFACE_PRESETS[name]
