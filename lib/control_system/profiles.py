"""
Knob Geometry Profiles

Defines 10+ knob profile types with complete parameter sets.
Each profile captures the aesthetic of iconic audio equipment.

Profile Types:
1. CHICKEN_HEAD - Neve 1073 style, rounded pointer knob
2. CYLINDRICAL - MXR style, simple knurled cylinder
3. DOMED - SSL style, dome top with colored center
4. FLATTOP - Sequential style, flat top with knurling
5. SOFT_TOUCH - Moog Voyager style, rubberized feel
6. POINTER - Guitar amp style, extended pointer
7. INSTRUMENT - Vintage test equipment, precision look
8. COLLET - Neve 88RS style, metal collet with cap
9. APEX - Budget style, simple cone
10. CUSTOM - User-defined curve
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class KnobProfileType(Enum):
    """Available knob profile types."""
    CHICKEN_HEAD = "chicken_head"
    CYLINDRICAL = "cylindrical"
    DOMED = "domed"
    FLATTOP = "flattop"
    SOFT_TOUCH = "soft_touch"
    POINTER = "pointer"
    INSTRUMENT = "instrument"
    COLLET = "collet"
    APEX = "apex"
    CUSTOM = "custom"


@dataclass
class KnobProfile:
    """
    Complete parameter set for a knob profile.

    All dimensions in meters unless otherwise specified.
    """
    # Identity
    name: str
    profile_type: KnobProfileType
    description: str = ""

    # Geometry - Cap
    cap_height: float = 0.020
    cap_diameter: float = 0.018
    cap_taper: float = 0.0  # Top diameter offset from base

    # Geometry - Skirt
    skirt_height: float = 0.008
    skirt_diameter: float = 0.020
    skirt_style: int = 0  # 0=integrated, 1=separate

    # Geometry - General
    segments: int = 64
    edge_radius_top: float = 0.001
    edge_radius_bottom: float = 0.0005

    # Pointer
    pointer_length: float = 0.012
    pointer_width: float = 0.08  # radians
    pointer_height: float = 0.0005
    pointer_type: str = "line"  # line, dot, pointer, skirt

    # Knurling
    knurl_count: int = 0
    knurl_depth: float = 0.0008
    knurl_z_start: float = 0.0
    knurl_z_end: float = 1.0
    knurl_fade: float = 0.0
    knurl_profile: float = 0.5  # 0=flat, 0.5=round, 1=sharp

    # Material
    metallic: float = 0.0
    roughness: float = 0.3
    clearcoat: float = 0.0
    clearcoat_roughness: float = 0.05

    # Colors
    base_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    pointer_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    accent_color: Optional[Tuple[float, float, float]] = None

    # Tags for categorization
    tags: List[str] = field(default_factory=list)

    def to_params(self) -> Dict[str, Any]:
        """Convert profile to parameter dictionary for build_artifact."""
        params = {
            # Geometry
            "cap_height": self.cap_height,
            "cap_diameter": self.cap_diameter,
            "cap_taper": self.cap_taper,
            "skirt_height": self.skirt_height,
            "skirt_diameter": self.skirt_diameter,
            "skirt_style": self.skirt_style,
            "segments": self.segments,

            # Pointer
            "pointer_length": self.pointer_length,
            "pointer_width": self.pointer_width,
            "pointer_height": self.pointer_height,
            "pointer_type": self.pointer_type,

            # Knurling
            "ridge_count": self.knurl_count,
            "ridge_depth": self.knurl_depth,
            "knurl_z_start": self.knurl_z_start,
            "knurl_z_end": self.knurl_z_end,
            "knurl_fade": self.knurl_fade,
            "knurl_profile": self.knurl_profile,

            # Material
            "metallic": self.metallic,
            "roughness": self.roughness,
            "clearcoat": self.clearcoat,

            # Colors
            "base_color": list(self.base_color),
            "pointer_color": list(self.pointer_color),
        }

        if self.accent_color:
            params["accent_color"] = list(self.accent_color)

        return params


# =============================================================================
# BUILT-IN PROFILES
# =============================================================================

PROFILES: Dict[str, KnobProfile] = {

    # -------------------------------------------------------------------------
    # CHICKEN HEAD - Neve 1073 Style
    # -------------------------------------------------------------------------
    "chicken_head": KnobProfile(
        name="Chicken Head",
        profile_type=KnobProfileType.CHICKEN_HEAD,
        description="Classic Neve 1073 style with rounded pointer",
        tags=["console", "neve", "vintage", "premium"],

        cap_height=0.022,
        cap_diameter=0.018,
        cap_taper=-0.002,  # Slightly wider at bottom

        skirt_height=0.008,
        skirt_diameter=0.020,
        skirt_style=0,

        segments=64,
        edge_radius_top=0.002,
        edge_radius_bottom=0.001,

        pointer_length=0.014,
        pointer_width=0.10,
        pointer_height=0.0008,
        pointer_type="pointer",

        knurl_count=0,

        metallic=0.0,
        roughness=0.25,
        clearcoat=0.6,

        base_color=(0.2, 0.35, 0.75),  # Classic Neve blue
        pointer_color=(1.0, 1.0, 1.0),
    ),

    # -------------------------------------------------------------------------
    # CYLINDRICAL - MXR Style
    # -------------------------------------------------------------------------
    "cylindrical": KnobProfile(
        name="Cylindrical",
        profile_type=KnobProfileType.CYLINDRICAL,
        description="Simple knurled cylinder, MXR pedal style",
        tags=["pedal", "mxr", "compact"],

        cap_height=0.015,
        cap_diameter=0.016,
        cap_taper=0.0,

        skirt_height=0.005,
        skirt_diameter=0.016,
        skirt_style=0,

        segments=48,
        edge_radius_top=0.0005,
        edge_radius_bottom=0.0005,

        pointer_length=0.008,
        pointer_width=0.06,
        pointer_height=0.0003,
        pointer_type="line",

        knurl_count=30,
        knurl_depth=0.0006,
        knurl_z_start=0.0,
        knurl_z_end=1.0,
        knurl_profile=0.7,  # Slightly sharp

        metallic=0.8,
        roughness=0.35,
        clearcoat=0.0,

        base_color=(0.7, 0.7, 0.72),
        pointer_color=(1.0, 1.0, 1.0),
    ),

    # -------------------------------------------------------------------------
    # DOMED - SSL 4000 Style
    # -------------------------------------------------------------------------
    "domed": KnobProfile(
        name="Domed",
        profile_type=KnobProfileType.DOMED,
        description="SSL 4000 style with dome top and colored center",
        tags=["console", "ssl", "professional"],

        cap_height=0.020,
        cap_diameter=0.018,
        cap_taper=-0.003,  # Domed shape

        skirt_height=0.006,
        skirt_diameter=0.019,
        skirt_style=0,

        segments=64,
        edge_radius_top=0.003,
        edge_radius_bottom=0.001,

        pointer_length=0.010,
        pointer_width=0.08,
        pointer_height=0.0004,
        pointer_type="line",

        knurl_count=20,
        knurl_depth=0.0004,
        knurl_z_start=0.0,
        knurl_z_end=0.6,  # Only on lower portion
        knurl_fade=0.1,
        knurl_profile=0.5,

        metallic=0.0,
        roughness=0.3,
        clearcoat=0.4,

        base_color=(0.6, 0.6, 0.62),  # SSL gray
        pointer_color=(0.2, 0.4, 0.8),  # Blue center dot
        accent_color=(0.2, 0.4, 0.8),
    ),

    # -------------------------------------------------------------------------
    # FLATTOP - Sequential Prophet-5 Style
    # -------------------------------------------------------------------------
    "flattop": KnobProfile(
        name="Flattop",
        profile_type=KnobProfileType.FLATTOP,
        description="Sequential Prophet-5 style with flat top",
        tags=["synth", "sequential", "vintage"],

        cap_height=0.018,
        cap_diameter=0.020,
        cap_taper=0.0,

        skirt_height=0.006,
        skirt_diameter=0.022,
        skirt_style=0,

        segments=64,
        edge_radius_top=0.0005,
        edge_radius_bottom=0.001,

        pointer_length=0.012,
        pointer_width=0.07,
        pointer_height=0.0006,
        pointer_type="line",

        knurl_count=36,
        knurl_depth=0.0005,
        knurl_z_start=0.0,
        knurl_z_end=1.0,
        knurl_profile=0.6,

        metallic=0.0,
        roughness=0.4,
        clearcoat=0.0,

        base_color=(0.15, 0.15, 0.15),  # Black
        pointer_color=(1.0, 1.0, 1.0),
    ),

    # -------------------------------------------------------------------------
    # SOFT_TOUCH - Moog Voyager Style
    # -------------------------------------------------------------------------
    "soft_touch": KnobProfile(
        name="Soft Touch",
        profile_type=KnobProfileType.SOFT_TOUCH,
        description="Moog Voyager style with rubberized feel",
        tags=["synth", "moog", "premium"],

        cap_height=0.024,
        cap_diameter=0.022,
        cap_taper=-0.002,

        skirt_height=0.008,
        skirt_diameter=0.024,
        skirt_style=0,

        segments=64,
        edge_radius_top=0.002,
        edge_radius_bottom=0.001,

        pointer_length=0.016,
        pointer_width=0.09,
        pointer_height=0.0006,
        pointer_type="pointer",

        knurl_count=0,  # Smooth rubberized surface

        metallic=0.0,
        roughness=0.7,  # Rubber-like
        clearcoat=0.0,

        base_color=(0.3, 0.3, 0.32),  # Dark gray/blue
        pointer_color=(1.0, 1.0, 1.0),
    ),

    # -------------------------------------------------------------------------
    # POINTER - Guitar Amp Style
    # -------------------------------------------------------------------------
    "pointer": KnobProfile(
        name="Pointer",
        profile_type=KnobProfileType.POINTER,
        description="Extended pointer knob, vintage amp style",
        tags=["amp", "vintage", "chicken-head"],

        cap_height=0.018,
        cap_diameter=0.015,
        cap_taper=0.0,

        skirt_height=0.005,
        skirt_diameter=0.015,
        skirt_style=0,

        segments=48,
        edge_radius_top=0.001,
        edge_radius_bottom=0.0005,

        pointer_length=0.020,  # Extended pointer
        pointer_width=0.12,
        pointer_height=0.001,
        pointer_type="pointer",

        knurl_count=24,
        knurl_depth=0.0004,
        knurl_z_start=0.0,
        knurl_z_end=1.0,
        knurl_profile=0.5,

        metallic=0.0,
        roughness=0.3,
        clearcoat=0.3,

        base_color=(0.9, 0.85, 0.75),  # Cream/ivory
        pointer_color=(0.2, 0.2, 0.2),
    ),

    # -------------------------------------------------------------------------
    # INSTRUMENT - Vintage Test Equipment
    # -------------------------------------------------------------------------
    "instrument": KnobProfile(
        name="Instrument",
        profile_type=KnobProfileType.INSTRUMENT,
        description="Precision instrument knob, vintage test equipment",
        tags=["instrument", "vintage", "precision"],

        cap_height=0.016,
        cap_diameter=0.020,
        cap_taper=0.001,  # Slightly narrower at bottom

        skirt_height=0.004,
        skirt_diameter=0.018,
        skirt_style=0,

        segments=64,
        edge_radius_top=0.0005,
        edge_radius_bottom=0.0003,

        pointer_length=0.010,
        pointer_width=0.05,
        pointer_height=0.0003,
        pointer_type="line",

        knurl_count=48,
        knurl_depth=0.0003,
        knurl_z_start=0.0,
        knurl_z_end=1.0,
        knurl_profile=0.4,  # Shallow knurl

        metallic=0.9,
        roughness=0.2,
        clearcoat=0.0,

        base_color=(0.8, 0.8, 0.82),  # Brushed aluminum
        pointer_color=(0.1, 0.1, 0.1),
    ),

    # -------------------------------------------------------------------------
    # COLLET - Neve 88RS Style
    # -------------------------------------------------------------------------
    "collet": KnobProfile(
        name="Collet",
        profile_type=KnobProfileType.COLLET,
        description="Neve 88RS style with metal collet and cap",
        tags=["console", "neve", "modern", "premium"],

        cap_height=0.018,
        cap_diameter=0.016,
        cap_taper=0.0,

        skirt_height=0.010,
        skirt_diameter=0.020,
        skirt_style=1,  # Separate collet

        segments=64,
        edge_radius_top=0.001,
        edge_radius_bottom=0.001,

        pointer_length=0.012,
        pointer_width=0.08,
        pointer_height=0.0005,
        pointer_type="line",

        knurl_count=0,

        metallic=0.85,
        roughness=0.25,
        clearcoat=0.0,

        base_color=(0.7, 0.7, 0.72),  # Silver collet
        pointer_color=(1.0, 1.0, 1.0),
    ),

    # -------------------------------------------------------------------------
    # APEX - Budget Style
    # -------------------------------------------------------------------------
    "apex": KnobProfile(
        name="Apex",
        profile_type=KnobProfileType.APEX,
        description="Simple budget knob with apex pointer",
        tags=["budget", "simple"],

        cap_height=0.015,
        cap_diameter=0.016,
        cap_taper=0.002,  # Cone shape

        skirt_height=0.004,
        skirt_diameter=0.016,
        skirt_style=0,

        segments=32,
        edge_radius_top=0.0,
        edge_radius_bottom=0.0005,

        pointer_length=0.010,
        pointer_width=0.06,
        pointer_height=0.0004,
        pointer_type="pointer",

        knurl_count=0,

        metallic=0.0,
        roughness=0.5,
        clearcoat=0.0,

        base_color=(0.3, 0.3, 0.3),
        pointer_color=(1.0, 1.0, 1.0),
    ),
}


def get_profile(name: str) -> KnobProfile:
    """
    Get a profile by name.

    Args:
        name: Profile name (e.g., "chicken_head", "cylindrical")

    Returns:
        KnobProfile instance

    Raises:
        KeyError: If profile not found
    """
    if name not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise KeyError(f"Profile '{name}' not found. Available: {available}")
    return PROFILES[name]


def list_profiles(tags: Optional[List[str]] = None) -> List[str]:
    """
    List available profile names, optionally filtered by tags.

    Args:
        tags: Optional list of tags to filter by

    Returns:
        List of profile names
    """
    if tags is None:
        return list(PROFILES.keys())

    return [
        name for name, profile in PROFILES.items()
        if any(tag in profile.tags for tag in tags)
    ]


def create_custom_profile(
    base_profile: str,
    overrides: Dict[str, Any]
) -> KnobProfile:
    """
    Create a custom profile based on an existing one with overrides.

    Args:
        base_profile: Name of base profile to extend
        overrides: Dictionary of parameter overrides

    Returns:
        New KnobProfile with overrides applied
    """
    base = get_profile(base_profile)

    # Create new profile from base
    profile_dict = {
        "name": overrides.get("name", f"Custom {base.name}"),
        "profile_type": KnobProfileType.CUSTOM,
        "description": overrides.get("description", f"Custom profile based on {base.name}"),
    }

    # Copy all base values
    for field_name in [
        "cap_height", "cap_diameter", "cap_taper",
        "skirt_height", "skirt_diameter", "skirt_style",
        "segments", "edge_radius_top", "edge_radius_bottom",
        "pointer_length", "pointer_width", "pointer_height", "pointer_type",
        "knurl_count", "knurl_depth", "knurl_z_start", "knurl_z_end",
        "knurl_fade", "knurl_profile",
        "metallic", "roughness", "clearcoat", "clearcoat_roughness",
        "base_color", "pointer_color", "accent_color", "tags"
    ]:
        profile_dict[field_name] = getattr(base, field_name)

    # Apply overrides
    for key, value in overrides.items():
        if key in profile_dict:
            profile_dict[key] = value

    return KnobProfile(**profile_dict)
