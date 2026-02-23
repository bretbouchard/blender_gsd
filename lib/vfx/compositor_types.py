"""
Compositor Types

Data structures for multi-layer compositing system.

Part of Phase 12.1: Compositor (REQ-COMP-01)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class BlendMode(str, Enum):
    """Blend modes for compositing layers."""
    NORMAL = "normal"
    ADD = "add"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    DIFFERENCE = "difference"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    LINEAR_DODGE = "linear_dodge"
    LINEAR_BURN = "linear_burn"
    DARKEN = "darken"
    LIGHTEN = "lighten"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    LUMINOSITY = "luminosity"


class LayerSource(str, Enum):
    """Source types for composite layers."""
    RENDER_PASS = "render_pass"
    IMAGE_SEQUENCE = "image_sequence"
    SOLID = "solid"
    GRADIENT = "gradient"
    VIDEO = "video"
    PROCEDURAL = "procedural"


class OutputFormat(str, Enum):
    """Output format for composite renders."""
    PNG = "png"
    JPEG = "jpeg"
    EXR = "exr"
    TIFF = "tiff"
    WEBM = "webm"
    MP4 = "mp4"
    PRORES = "prores"


@dataclass
class Transform2D:
    """2D transform for layer positioning."""
    position: Tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)
    anchor: Tuple[float, float] = (0.5, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": list(self.position),
            "rotation": self.rotation,
            "scale": list(self.scale),
            "anchor": list(self.anchor),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transform2D":
        return cls(
            position=tuple(data.get("position", [0.0, 0.0])),
            rotation=data.get("rotation", 0.0),
            scale=tuple(data.get("scale", [1.0, 1.0])),
            anchor=tuple(data.get("anchor", [0.5, 0.5])),
        )


@dataclass
class ColorCorrection:
    """Color correction settings for layers."""
    exposure: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 1.0
    lift: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    gain: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    hue_shift: float = 0.0
    temperature: float = 0.0  # -100 to 100
    tint: float = 0.0  # -100 to 100
    highlights: float = 0.0  # -100 to 100
    shadows: float = 0.0  # -100 to 100
    whites: float = 0.0  # -100 to 100
    blacks: float = 0.0  # -100 to 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exposure": self.exposure,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "gamma": self.gamma,
            "lift": list(self.lift),
            "gain": list(self.gain),
            "offset": list(self.offset),
            "hue_shift": self.hue_shift,
            "temperature": self.temperature,
            "tint": self.tint,
            "highlights": self.highlights,
            "shadows": self.shadows,
            "whites": self.whites,
            "blacks": self.blacks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorCorrection":
        return cls(
            exposure=data.get("exposure", 0.0),
            contrast=data.get("contrast", 1.0),
            saturation=data.get("saturation", 1.0),
            gamma=data.get("gamma", 1.0),
            lift=tuple(data.get("lift", [0.0, 0.0, 0.0])),
            gain=tuple(data.get("gain", [1.0, 1.0, 1.0])),
            offset=tuple(data.get("offset", [0.0, 0.0, 0.0])),
            hue_shift=data.get("hue_shift", 0.0),
            temperature=data.get("temperature", 0.0),
            tint=data.get("tint", 0.0),
            highlights=data.get("highlights", 0.0),
            shadows=data.get("shadows", 0.0),
            whites=data.get("whites", 0.0),
            blacks=data.get("blacks", 0.0),
        )


@dataclass
class GradientStop:
    """A single gradient color stop."""
    position: float  # 0.0 to 1.0
    color: Tuple[float, float, float, float]  # RGBA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "color": list(self.color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GradientStop":
        return cls(
            position=data.get("position", 0.0),
            color=tuple(data.get("color", [0, 0, 0, 1])),
        )


@dataclass
class LayerMask:
    """Mask configuration for a layer."""
    source: str  # Path to mask image or "alpha" for self-masking
    invert: bool = False
    feather: float = 0.0  # Feather amount in pixels
    expansion: float = 0.0  # Expand/contract mask

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "invert": self.invert,
            "feather": self.feather,
            "expansion": self.expansion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayerMask":
        return cls(
            source=data.get("source", ""),
            invert=data.get("invert", False),
            feather=data.get("feather", 0.0),
            expansion=data.get("expansion", 0.0),
        )


@dataclass
class CompLayer:
    """A single layer in the composite stack."""
    name: str
    source: str  # Render pass name, image path, or source identifier
    source_type: LayerSource = LayerSource.RENDER_PASS
    blend_mode: BlendMode = BlendMode.NORMAL
    opacity: float = 1.0
    transform: Transform2D = field(default_factory=Transform2D)
    color_correction: ColorCorrection = field(default_factory=ColorCorrection)
    mask: Optional[LayerMask] = None
    enabled: bool = True
    locked: bool = False
    solo: bool = False
    # For solid/gradient sources
    solid_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    gradient_stops: List[GradientStop] = field(default_factory=list)
    gradient_angle: float = 0.0
    # Timing
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    frame_offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "source_type": self.source_type.value,
            "blend_mode": self.blend_mode.value,
            "opacity": self.opacity,
            "transform": self.transform.to_dict(),
            "color_correction": self.color_correction.to_dict(),
            "mask": self.mask.to_dict() if self.mask else None,
            "enabled": self.enabled,
            "locked": self.locked,
            "solo": self.solo,
            "solid_color": list(self.solid_color),
            "gradient_stops": [s.to_dict() for s in self.gradient_stops],
            "gradient_angle": self.gradient_angle,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "frame_offset": self.frame_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompLayer":
        return cls(
            name=data.get("name", "Layer"),
            source=data.get("source", ""),
            source_type=LayerSource(data.get("source_type", "render_pass")),
            blend_mode=BlendMode(data.get("blend_mode", "normal")),
            opacity=data.get("opacity", 1.0),
            transform=Transform2D.from_dict(data.get("transform", {})),
            color_correction=ColorCorrection.from_dict(data.get("color_correction", {})),
            mask=LayerMask.from_dict(data["mask"]) if data.get("mask") else None,
            enabled=data.get("enabled", True),
            locked=data.get("locked", False),
            solo=data.get("solo", False),
            solid_color=tuple(data.get("solid_color", [0, 0, 0, 1])),
            gradient_stops=[GradientStop.from_dict(s) for s in data.get("gradient_stops", [])],
            gradient_angle=data.get("gradient_angle", 0.0),
            start_frame=data.get("start_frame"),
            end_frame=data.get("end_frame"),
            frame_offset=data.get("frame_offset", 0),
        )


@dataclass
class CryptomatteLayer:
    """Cryptomatte layer for object isolation."""
    name: str
    manifest_path: str  # Path to manifest JSON
    exr_path: str  # Path to EXR with cryptomatte
    rank: int = 0  # Cryptomatte rank (0-6 typically)
    objects: List[str] = field(default_factory=list)  # Selected objects

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "manifest_path": self.manifest_path,
            "exr_path": self.exr_path,
            "rank": self.rank,
            "objects": self.objects,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptomatteLayer":
        return cls(
            name=data.get("name", "Cryptomatte"),
            manifest_path=data.get("manifest_path", ""),
            exr_path=data.get("exr_path", ""),
            rank=data.get("rank", 0),
            objects=data.get("objects", []),
        )


@dataclass
class CompositeConfig:
    """Complete composite configuration."""
    name: str
    resolution: Tuple[int, int] = (1920, 1080)
    frame_rate: float = 24.0
    frame_range: Tuple[int, int] = (1, 250)
    layers: List[CompLayer] = field(default_factory=list)
    cryptomatte_layers: List[CryptomatteLayer] = field(default_factory=list)
    output_path: str = ""
    output_format: OutputFormat = OutputFormat.PNG
    output_quality: int = 90  # For JPEG
    output_codec: str = ""  # For video
    output_bit_depth: int = 8  # 8, 16, 32
    background_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    premultiplied_alpha: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "resolution": list(self.resolution),
            "frame_rate": self.frame_rate,
            "frame_range": list(self.frame_range),
            "layers": [l.to_dict() for l in self.layers],
            "cryptomatte_layers": [c.to_dict() for c in self.cryptomatte_layers],
            "output_path": self.output_path,
            "output_format": self.output_format.value,
            "output_quality": self.output_quality,
            "output_codec": self.output_codec,
            "output_bit_depth": self.output_bit_depth,
            "background_color": list(self.background_color),
            "premultiplied_alpha": self.premultiplied_alpha,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositeConfig":
        return cls(
            name=data.get("name", "Composite"),
            resolution=tuple(data.get("resolution", [1920, 1080])),
            frame_rate=data.get("frame_rate", 24.0),
            frame_range=tuple(data.get("frame_range", [1, 250])),
            layers=[CompLayer.from_dict(l) for l in data.get("layers", [])],
            cryptomatte_layers=[CryptomatteLayer.from_dict(c) for c in data.get("cryptomatte_layers", [])],
            output_path=data.get("output_path", ""),
            output_format=OutputFormat(data.get("output_format", "png")),
            output_quality=data.get("output_quality", 90),
            output_codec=data.get("output_codec", ""),
            output_bit_depth=data.get("output_bit_depth", 8),
            background_color=tuple(data.get("background_color", [0, 0, 0, 0])),
            premultiplied_alpha=data.get("premultiplied_alpha", False),
        )

    def add_layer(self, layer: CompLayer) -> None:
        """Add a layer to the composite."""
        self.layers.append(layer)

    def remove_layer(self, name: str) -> bool:
        """Remove a layer by name."""
        for i, layer in enumerate(self.layers):
            if layer.name == name:
                self.layers.pop(i)
                return True
        return False

    def get_layer(self, name: str) -> Optional[CompLayer]:
        """Get a layer by name."""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def get_enabled_layers(self) -> List[CompLayer]:
        """Get all enabled layers."""
        solo_layers = [l for l in self.layers if l.solo and l.enabled]
        if solo_layers:
            return solo_layers
        return [l for l in self.layers if l.enabled]
