"""
Input Types and Configurations

Defines the core types and dataclasses for the Universal Input System.

All dimensions are in MILLIMETERS at the user level,
converted to meters internally for Blender.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


# =============================================================================
# CONVERSION
# =============================================================================

MM_TO_M = 0.001


def mm(value: float) -> float:
    """Convert millimeters to meters."""
    return value * MM_TO_M


# =============================================================================
# ENUMS
# =============================================================================

class InputType(Enum):
    """Type of input control."""
    ROTARY = "rotary"       # Knobs - rotate around axis
    LINEAR = "linear"       # Faders/sliders - move along track
    MOMENTARY = "momentary" # Buttons - press and release


class BaseShape(Enum):
    """Base geometry shape."""
    CYLINDER = "cylinder"   # Rotary knobs, round buttons
    CUBE = "cube"           # Slider knobs, square buttons
    CONE = "cone"           # Tapered knobs


class CapStyle(Enum):
    """Cap edge/transition style."""
    FLAT = "flat"           # Flat edge, 90 degrees
    BEVEL = "bevel"         # Angled chamfer (45 degrees)
    ROUNDED = "rounded"     # Smooth fillet/radius


class KnurlProfile(Enum):
    """Knurl groove cross-section shape."""
    V_SHAPED = "v"          # Sharp V-groove
    U_SHAPED = "u"          # Rounded U-groove
    FLAT = "flat"           # Flat-bottom groove


class RotationMode(Enum):
    """How zones rotate relative to each other."""
    LOCKED = "locked"           # Zones rotate together
    INDEPENDENT = "independent" # Zones can rotate separately
    DETENT = "detent"           # Zone clicks into positions


# =============================================================================
# CONFIG DATACLASSES
# =============================================================================

@dataclass
class CapConfig:
    """
    Configuration for a zone cap (top or bottom).

    All dimensions in MILLIMETERS.
    """
    style: CapStyle = CapStyle.FLAT
    height_mm: float = 0.0         # 0 = no cap
    bevel_angle_deg: float = 45.0  # For bevel style
    radius_mm: float = 0.0         # For rounded style (0 = auto from height)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "style": self.style.value,
            "height_mm": self.height_mm,
            "bevel_angle_deg": self.bevel_angle_deg,
            "radius_mm": self.radius_mm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapConfig":
        return cls(
            style=CapStyle(data.get("style", "flat")),
            height_mm=data.get("height_mm", 0.0),
            bevel_angle_deg=data.get("bevel_angle_deg", 45.0),
            radius_mm=data.get("radius_mm", 0.0),
        )

    @property
    def height_m(self) -> float:
        """Height in meters."""
        return mm(self.height_mm)


@dataclass
class KnurlConfig:
    """
    Configuration for knurling (grip grooves).

    All dimensions in MILLIMETERS.
    """
    enabled: bool = False
    count: int = 0                 # Number of grooves (0 = no knurling)
    depth_mm: float = 0.5          # How deep grooves go
    width_fraction: float = 0.5    # Groove width as fraction of spacing (0.0-1.0)
    profile: KnurlProfile = KnurlProfile.V_SHAPED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "count": self.count,
            "depth_mm": self.depth_mm,
            "width_fraction": self.width_fraction,
            "profile": self.profile.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnurlConfig":
        return cls(
            enabled=data.get("enabled", False),
            count=data.get("count", 0),
            depth_mm=data.get("depth_mm", 0.5),
            width_fraction=data.get("width_fraction", 0.5),
            profile=KnurlProfile(data.get("profile", "v")),
        )

    @property
    def depth_m(self) -> float:
        """Depth in meters."""
        return mm(self.depth_mm)


@dataclass
class ZoneConfig:
    """
    Configuration for a single zone (A or B).

    Each zone has 3 sections: top_cap, middle, bottom_cap.

    All dimensions in MILLIMETERS.
    """
    height_mm: float = 10.0        # Total zone height
    width_top_mm: float = 14.0     # Width at top of zone
    width_bottom_mm: float = 14.0  # Width at bottom of zone

    top_cap: CapConfig = field(default_factory=CapConfig)
    middle_knurl: KnurlConfig = field(default_factory=KnurlConfig)
    bottom_cap: CapConfig = field(default_factory=CapConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "height_mm": self.height_mm,
            "width_top_mm": self.width_top_mm,
            "width_bottom_mm": self.width_bottom_mm,
            "top_cap": self.top_cap.to_dict(),
            "middle_knurl": self.middle_knurl.to_dict(),
            "bottom_cap": self.bottom_cap.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ZoneConfig":
        return cls(
            height_mm=data.get("height_mm", 10.0),
            width_top_mm=data.get("width_top_mm", 14.0),
            width_bottom_mm=data.get("width_bottom_mm", 14.0),
            top_cap=CapConfig.from_dict(data.get("top_cap", {})),
            middle_knurl=KnurlConfig.from_dict(data.get("middle_knurl", {})),
            bottom_cap=CapConfig.from_dict(data.get("bottom_cap", {})),
        )

    @property
    def height_m(self) -> float:
        """Height in meters."""
        return mm(self.height_mm)

    @property
    def width_top_m(self) -> float:
        """Width at top in meters."""
        return mm(self.width_top_mm)

    @property
    def width_bottom_m(self) -> float:
        """Width at bottom in meters."""
        return mm(self.width_bottom_mm)


@dataclass
class RotationConfig:
    """
    Configuration for rotation behavior.

    Applies to rotary inputs (knobs).
    """
    mode: RotationMode = RotationMode.LOCKED
    min_angle_deg: float = -150.0   # Minimum rotation angle
    max_angle_deg: float = 150.0    # Maximum rotation angle
    detent_count: int = 0           # Number of detent positions (0 = continuous)
    detent_force: float = 0.0       # Detent click force (0-1)

    # For independent rotation (zone B rotates separately)
    zone_b_independent: bool = False
    zone_b_ratio: float = 1.0       # Zone B rotation ratio (1.0 = 1:1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "min_angle_deg": self.min_angle_deg,
            "max_angle_deg": self.max_angle_deg,
            "detent_count": self.detent_count,
            "detent_force": self.detent_force,
            "zone_b_independent": self.zone_b_independent,
            "zone_b_ratio": self.zone_b_ratio,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RotationConfig":
        return cls(
            mode=RotationMode(data.get("mode", "locked")),
            min_angle_deg=data.get("min_angle_deg", -150.0),
            max_angle_deg=data.get("max_angle_deg", 150.0),
            detent_count=data.get("detent_count", 0),
            detent_force=data.get("detent_force", 0.0),
            zone_b_independent=data.get("zone_b_independent", False),
            zone_b_ratio=data.get("zone_b_ratio", 1.0),
        )


@dataclass
class InputConfig:
    """
    Complete configuration for an input control.

    This is the top-level config that defines everything needed
    to build an input (knob, fader, button).
    """
    # Identity
    name: str = "Input"
    input_type: InputType = InputType.ROTARY
    base_shape: BaseShape = BaseShape.CYLINDER

    # Overall dimensions
    total_height_mm: float = 20.0
    total_width_mm: float = 14.0

    # Zones (A = top/upper, B = bottom/lower)
    zone_a: ZoneConfig = field(default_factory=ZoneConfig)
    zone_b: ZoneConfig = field(default_factory=ZoneConfig)

    # Rotation (for rotary inputs)
    rotation: RotationConfig = field(default_factory=RotationConfig)

    # Mesh quality
    segments: int = 64              # Circumference segments
    cap_segments: int = 8           # Radial segments for rounded caps

    # Material defaults
    base_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    metallic: float = 0.0
    roughness: float = 0.3

    # Tags for categorization
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "input_type": self.input_type.value,
            "base_shape": self.base_shape.value,
            "total_height_mm": self.total_height_mm,
            "total_width_mm": self.total_width_mm,
            "zones": {
                "a": self.zone_a.to_dict(),
                "b": self.zone_b.to_dict(),
            },
            "rotation": self.rotation.to_dict(),
            "mesh": {
                "segments": self.segments,
                "cap_segments": self.cap_segments,
            },
            "material": {
                "base_color": list(self.base_color),
                "metallic": self.metallic,
                "roughness": self.roughness,
            },
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputConfig":
        zones = data.get("zones", {})
        mesh = data.get("mesh", {})
        material = data.get("material", {})

        return cls(
            name=data.get("name", "Input"),
            input_type=InputType(data.get("input_type", "rotary")),
            base_shape=BaseShape(data.get("base_shape", "cylinder")),
            total_height_mm=data.get("total_height_mm", 20.0),
            total_width_mm=data.get("total_width_mm", 14.0),
            zone_a=ZoneConfig.from_dict(zones.get("a", {})),
            zone_b=ZoneConfig.from_dict(zones.get("b", {})),
            rotation=RotationConfig.from_dict(data.get("rotation", {})),
            segments=mesh.get("segments", 64),
            cap_segments=mesh.get("cap_segments", 8),
            base_color=tuple(material.get("base_color", [0.5, 0.5, 0.5])),
            metallic=material.get("metallic", 0.0),
            roughness=material.get("roughness", 0.3),
            tags=data.get("tags", []),
        )

    @property
    def total_height_m(self) -> float:
        """Total height in meters."""
        return mm(self.total_height_mm)

    @property
    def total_width_m(self) -> float:
        """Total width in meters."""
        return mm(self.total_width_mm)
