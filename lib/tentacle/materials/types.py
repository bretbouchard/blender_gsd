"""
Tentacle Material Types

Data structures for procedural skin materials with horror themes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


class MaterialTheme(Enum):
    """Horror material theme presets."""

    ROTTING = "rotting"          # Gray-green, necrotic
    PARASITIC = "parasitic"      # Flesh pink, infested
    DEMONIC = "demonic"        # Deep red, hellish
    MUTATED = "mutated"        # Pale flesh, alien/radioactive
    DECAYED = "decayed"        # Bone white, skeletal


class WetnessLevel(Enum):
    """Wetness level presets."""

    DRY = "dry"
    MOIST = "moist"
    SLIMY = "slimy"
    DRIPPING = "dripping"


@dataclass
class SSSConfig:
    """Subsurface scattering configuration."""

    radius: float = 1.0
    """SSS radius in millimeters."""

    color: Tuple[float, float, float] = (1.0, 0.2, 0.2)
    """SSS tint color as RGB tuple (0-1 range)."""

    weight: float = 1.0
    """SSS influence weight (0.0-1.0)."""

    anisotropy: float = 0.0
    """Directional SSS (0.0-1.0)."""

    ior: float = 1.4
    """Index of refraction for skin."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "radius": self.radius,
            "color": list(self.color),
            "weight": self.weight,
            "anisotropy": self.anisotropy,
            "ior": self.ior,
        }


@dataclass
class WetnessConfig:
    """Wet/slimy surface configuration."""

    level: WetnessLevel = WetnessLevel.DRY
    """Wetness level preset."""

    intensity: float = 0.5
    """Wetness intensity (0.0-1.0)."""

    roughness_modifier: float = 0.3
    """How much wetness reduces roughness."""

    specular_boost: float = 0.5
    """Additional specular from wetness"""

    clearcoat: float = 0.0
    """Clearcoat layer intensity for slimy look."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "level": self.level.value,
            "intensity": self.intensity,
            "roughness_modifier": self.roughness_modifier,
            "specular_boost": self.specular_boost,
            "clearcoat": self.clearcoat,
        }


@dataclass
class VeinConfig:
    """Vein pattern configuration."""

    enabled: bool = True
    """Whether veins are visible."""

    color: Tuple[float, float, float] = (0.3, 0.0, 0.0)
    """Vein color as RGB tuple (0-1 range)."""

    density: float = 0.5
    """Vein network density (0.0-1.0)."""

    scale: float = 0.1
    """Vein pattern scale in meters."""

    depth: float = 0.02
    """Vein indentation depth."""

    glow: bool = False
    """Bioluminescent glow (for mutated theme)"""

    glow_color: Tuple[float, float, float] = (0.0, 1.0, 0.5)
    """Glow color for bioluminescence"""

    glow_intensity: float = 0.5
    """Glow intensity (0.0-1.0) """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "color": list(self.color),
            "density": self.density,
            "scale": self.scale,
            "depth": self.depth,
            "glow": self.glow,
            "glow_color": list(self.glow_color),
            "glow_intensity": self.glow_intensity,
        }


@dataclass
class RoughnessConfig:
    """Surface roughness configuration."""

    base: float = 0.5
    """Base roughness value."""

    variation: float = 0.1
    """Noise-based roughness variation."""

    metallic: float = 0.0
    """Metallic value (usually 0 for organic)"""

    normal_strength: float = 0.5
    """Normal map strength for surface detail"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "base": self.base,
            "variation": self.variation,
            "metallic": self.metallic,
            "normal_strength": self.normal_strength,
        }


@dataclass
class MaterialZone:
    """Material zone for varied appearance along tentacle."""

    name: str
    """Zone name (base, mid, tip)"""

    position: float
    """Position along tentacle (0.0-1.0)"""

    width: float = 0.33
    """Zone width (0.0-1.0)"""

    color_tint: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    """Color tint multiplier"""

    roughness_offset: float = 0.0
    """Roughness offset for this zone"""

    sss_offset: float = 0.0
    """SSS radius offset for this zone"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "position": self.position,
            "width": self.width,
            "color_tint": list(self.color_tint),
            "roughness_offset": self.roughness_offset,
            "sss_offset": self.sss_offset,
        }


@dataclass
class ThemePreset:
    """Complete theme preset with all parameters."""

    name: str
    """Theme preset name."""

    theme: MaterialTheme
    """Theme enum value"""

    description: str = ""
    """Human-readable theme description"""

    base_color: Tuple[float, float, float] = (0.5, 0.4, 0.35)
    """Base albedo color as RGB tuple (0-1 range)"""

    sss: SSSConfig = field(default_factory=SSSConfig)
    """Subsurface scattering settings"""

    wetness: WetnessConfig = field(default_factory=WetnessConfig)
    """Wet/slimy surface settings"""

    veins: VeinConfig = field(default_factory=VeinConfig)
    """Vein pattern settings"""

    roughness: RoughnessConfig = field(default_factory=RoughnessConfig)
    """Surface roughness settings"""

    emission_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Emission color for bioluminescence (0-1 range)"""

    emission_strength: float = 0.0
    """Emission strength (0.0-1.0)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "theme": self.theme.value,
            "description": self.description,
            "base_color": list(self.base_color),
            "sss": self.sss.to_dict(),
            "wetness": self.wetness.to_dict(),
            "veins": self.veins.to_dict(),
            "roughness": self.roughness.to_dict(),
            "emission_color": list(self.emission_color),
            "emission_strength": self.emission_strength,
        }


@dataclass
class TentacleMaterialConfig:
    """Complete material configuration for a tentacle."""

    name: str = "TentacleMaterial"
    """Material configuration name"""

    theme_preset: Optional[ThemePreset] = None
    """Selected theme preset (or None for custom)"""

    zones: List[MaterialZone] = field(default_factory=list)
    """Material zones along tentacle length"""

    blend_zones: bool = True
    """Whether to blend zones smoothly"""

    global_wetness_multiplier: float = 1.0
    """Global wetness multiplier applied to all zones"""

    global_sss_multiplier: float = 1.0
    """Global SSS multiplier applied to all zones"""

    noise_scale: float = 1.0
    """Scale for procedural noise detail"""

    noise_detail: int = 4
    """Detail level for procedural noise (2-16)"""

    seed: Optional[int] = None
    """Random seed for deterministic generation"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "theme_preset": self.theme_preset.to_dict() if self.theme_preset else None,
            "zones": [z.to_dict() for z in self.zones],
            "blend_zones": self.blend_zones,
            "global_wetness_multiplier": self.global_wetness_multiplier,
            "global_sss_multiplier": self.global_sss_multiplier,
            "noise_scale": self.noise_scale,
            "noise_detail": self.noise_detail,
            "seed": self.seed,
        }


@dataclass
class BakeConfig:
    """Configuration for texture baking."""

    resolution: int = 2048
    """Bake resolution in pixels (1024, 2048, 4096)"""

    bake_albedo: bool = True
    """Bake base color/albedo map"""

    bake_normal: bool = True
    """Bake normal map"""

    bake_roughness: bool = True
    """Bake roughness map"""

    bake_sss: bool = True
    """Bake SSS color/weight map"""

    bake_emission: bool = False
    """Bake emission map (for bioluminescent)"""

    output_format: str = "PNG"
    """Output image format (PNG, EXR)"""

    output_directory: Optional[str] = None
    """Output directory for baked textures"""

    denoise: bool = True
    """Apply denoising during bake"""

    samples: int = 64
    """Samples for baking (higher = better quality)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resolution": self.resolution,
            "bake_albedo": self.bake_albedo,
            "bake_normal": self.bake_normal,
            "bake_roughness": self.bake_roughness,
            "bake_sss": self.bake_sss,
            "bake_emission": self.bake_emission,
            "output_format": self.output_format,
            "output_directory": self.output_directory,
            "denoise": self.denoise,
            "samples": self.samples,
        }


@dataclass
class BakeResult:
    """Result from texture baking."""

    albedo_path: Optional[str] = None
    """Path to baked albedo texture"""

    normal_path: Optional[str] = None
    """Path to baked normal map"""

    roughness_path: Optional[str] = None
    """Path to baked roughness map"""

    sss_path: Optional[str] = None
    """Path to baked SSS map"""

    emission_path: Optional[str] = None
    """Path to baked emission map"""

    success: bool = True
    """Whether baking was successful"""

    error: Optional[str] = None
    """Error message if failed"""

    resolution: Tuple[int, int] = (2048, 2048)
    """Actual resolution used"""

    bake_time: float = 0.0
    """Time taken to bake in seconds"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "albedo_path": self.albedo_path,
            "normal_path": self.normal_path,
            "roughness_path": self.roughness_path,
            "sss_path": self.sss_path,
            "emission_path": self.emission_path,
            "success": self.success,
            "error": self.error,
            "resolution": list(self.resolution),
            "bake_time": self.bake_time,
        }
