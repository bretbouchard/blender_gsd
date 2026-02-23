"""
Atmospherics Module

Provides atmospheric effects for photoshoots and scenes including:
- Haze and fog simulation
- Volumetric lighting
- Dust particles
- Rain and weather effects
- Lens effects (bloom, glare)

Usage:
    from lib.cinematic.atmospherics import (
        AtmosphereConfig,
        VolumetricConfig,
        create_fog_effect,
        create_dust_motes,
        create_rain_effect,
    )

    # Create fog effect
    fog = create_fog_effect("morning_mist", density=0.3)

    # Create volumetric light beam
    beam = create_volumetric_beam("god_rays", direction=(45, 30))
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math


class AtmosphereType(Enum):
    """Types of atmospheric effects."""
    FOG = "fog"
    HAZE = "haze"
    MIST = "mist"
    SMOKE = "smoke"
    DUST = "dust"
    RAIN = "rain"
    SNOW = "snow"
    STEAM = "steam"


class VolumetricType(Enum):
    """Types of volumetric effects."""
    GOD_RAYS = "god_rays"
    LIGHT_BEAM = "light_beam"
    SHAFT = "shaft"
    AMBIENT = "ambient"


class ParticleType(Enum):
    """Types of particle effects."""
    DUST_MOTES = "dust_motes"
    POLLEN = "pollen"
    SPARKS = "sparks"
    EMBERS = "embers"
    BUBBLES = "bubbles"


@dataclass
class AtmosphereConfig:
    """Configuration for atmospheric effects."""
    name: str
    atmosphere_type: AtmosphereType
    density: float = 0.5  # 0.0 to 1.0
    height: float = 5.0  # Effect height in meters
    anisotropy: float = 0.0  # -1 to 1 (forward/backward scattering)
    color: Tuple[float, float, float] = (0.9, 0.9, 0.95)
    absorption_color: Tuple[float, float, float] = (0.1, 0.1, 0.15)
    emission_strength: float = 0.0
    emission_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    noise_scale: float = 1.0
    noise_detail: int = 2
    animation_speed: float = 0.0  # m/s for moving fog
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "atmosphere_type": self.atmosphere_type.value,
            "density": self.density,
            "height": self.height,
            "anisotropy": self.anisotropy,
            "color": self.color,
            "absorption_color": self.absorption_color,
            "emission_strength": self.emission_strength,
            "emission_color": self.emission_color,
            "noise_scale": self.noise_scale,
            "noise_detail": self.noise_detail,
            "animation_speed": self.animation_speed,
            "properties": self.properties,
        }


@dataclass
class VolumetricConfig:
    """Configuration for volumetric lighting."""
    name: str
    volumetric_type: VolumetricType
    direction: Tuple[float, float] = (0.0, 45.0)  # azimuth, elevation
    cone_angle: float = 30.0  # degrees
    intensity: float = 1.0
    color: Tuple[float, float, float] = (1.0, 0.98, 0.95)
    scattering: float = 0.5
    absorption: float = 0.1
    distance: float = 10.0  # Effect range in meters
    noise_amount: float = 0.2
    source_position: Optional[Tuple[float, float, float]] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "volumetric_type": self.volumetric_type.value,
            "direction": self.direction,
            "cone_angle": self.cone_angle,
            "intensity": self.intensity,
            "color": self.color,
            "scattering": self.scattering,
            "absorption": self.absorption,
            "distance": self.distance,
            "noise_amount": self.noise_amount,
            "source_position": self.source_position,
            "properties": self.properties,
        }


@dataclass
class ParticleConfig:
    """Configuration for particle effects."""
    name: str
    particle_type: ParticleType
    count: int = 1000
    size_min: float = 0.01
    size_max: float = 0.05
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.1)  # m/s
    lifetime: float = 10.0  # seconds
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.8)
    emission_box: Tuple[float, float, float] = (10.0, 10.0, 5.0)  # x, y, z size
    gravity: float = 0.0  # m/s^2
    turbulence: float = 0.1
    glow: float = 0.0  # Particle glow intensity
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "particle_type": self.particle_type.value,
            "count": self.count,
            "size_min": self.size_min,
            "size_max": self.size_max,
            "velocity": self.velocity,
            "lifetime": self.lifetime,
            "color": self.color,
            "emission_box": self.emission_box,
            "gravity": self.gravity,
            "turbulence": self.turbulence,
            "glow": self.glow,
            "properties": self.properties,
        }


@dataclass
class LensEffectConfig:
    """Configuration for lens/post-processing effects."""
    name: str
    bloom_intensity: float = 0.0
    bloom_threshold: float = 0.8
    bloom_radius: float = 6.5
    glare_type: str = "streaks"  # streaks, ghosts, frosty
    glare_intensity: float = 0.0
    chromatic_aberration: float = 0.0
    vignette_intensity: float = 0.0
    film_grain: float = 0.0
    color_correction: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "bloom_intensity": self.bloom_intensity,
            "bloom_threshold": self.bloom_threshold,
            "bloom_radius": self.bloom_radius,
            "glare_type": self.glare_type,
            "glare_intensity": self.glare_intensity,
            "chromatic_aberration": self.chromatic_aberration,
            "vignette_intensity": self.vignette_intensity,
            "film_grain": self.film_grain,
            "color_correction": self.color_correction,
        }


# =============================================================================
# FOG AND HAZE PRESETS
# =============================================================================

def create_fog_effect(
    preset: str = "standard",
    density: float = 0.5
) -> AtmosphereConfig:
    """
    Create a fog effect configuration.

    Args:
        preset: Fog type (standard, morning_mist, dense, ground_fog)
        density: Density multiplier (0.0 to 1.0)

    Returns:
        AtmosphereConfig
    """
    presets = {
        "standard": AtmosphereConfig(
            name="standard_fog",
            atmosphere_type=AtmosphereType.FOG,
            density=density,
            height=5.0,
            anisotropy=0.2,
            color=(0.9, 0.9, 0.95),
            noise_scale=2.0,
        ),
        "morning_mist": AtmosphereConfig(
            name="morning_mist",
            atmosphere_type=AtmosphereType.MIST,
            density=density * 0.3,
            height=2.0,
            anisotropy=0.5,
            color=(0.95, 0.95, 1.0),
            noise_scale=3.0,
            noise_detail=3,
        ),
        "dense": AtmosphereConfig(
            name="dense_fog",
            atmosphere_type=AtmosphereType.FOG,
            density=density * 1.5,
            height=3.0,
            anisotropy=0.0,
            color=(0.85, 0.85, 0.9),
            absorption_color=(0.15, 0.15, 0.2),
            noise_scale=1.5,
        ),
        "ground_fog": AtmosphereConfig(
            name="ground_fog",
            atmosphere_type=AtmosphereType.FOG,
            density=density,
            height=1.0,
            anisotropy=0.3,
            color=(0.9, 0.9, 0.93),
            noise_scale=4.0,
            noise_detail=4,
            properties={"ground_falloff": True},
        ),
    }

    return presets.get(preset, presets["standard"])


def create_haze_effect(
    preset: str = "standard",
    density: float = 0.3
) -> AtmosphereConfig:
    """
    Create a haze effect configuration.

    Args:
        preset: Haze type (standard, atmospheric, heat_haze)
        density: Density multiplier

    Returns:
        AtmosphereConfig
    """
    presets = {
        "standard": AtmosphereConfig(
            name="standard_haze",
            atmosphere_type=AtmosphereType.HAZE,
            density=density * 0.3,
            height=20.0,
            anisotropy=0.7,
            color=(0.95, 0.95, 0.98),
            absorption_color=(0.02, 0.02, 0.03),
        ),
        "atmospheric": AtmosphereConfig(
            name="atmospheric_haze",
            atmosphere_type=AtmosphereType.HAZE,
            density=density * 0.2,
            height=50.0,
            anisotropy=0.8,
            color=(0.9, 0.92, 1.0),
            absorption_color=(0.01, 0.01, 0.02),
        ),
        "heat_haze": AtmosphereConfig(
            name="heat_haze",
            atmosphere_type=AtmosphereType.HAZE,
            density=density * 0.15,
            height=2.0,
            anisotropy=0.5,
            color=(0.98, 0.96, 0.9),
            noise_scale=0.5,
            animation_speed=2.0,
        ),
    }

    return presets.get(preset, presets["standard"])


def create_smoke_effect(
    preset: str = "standard",
    density: float = 0.5
) -> AtmosphereConfig:
    """
    Create a smoke effect configuration.

    Args:
        preset: Smoke type (standard, cigarette, chimney, steam)
        density: Density multiplier

    Returns:
        AtmosphereConfig
    """
    presets = {
        "standard": AtmosphereConfig(
            name="standard_smoke",
            atmosphere_type=AtmosphereType.SMOKE,
            density=density,
            height=3.0,
            anisotropy=-0.3,
            color=(0.4, 0.4, 0.45),
            absorption_color=(0.3, 0.3, 0.35),
            noise_scale=1.0,
            noise_detail=5,
            animation_speed=0.5,
        ),
        "cigarette": AtmosphereConfig(
            name="cigarette_smoke",
            atmosphere_type=AtmosphereType.SMOKE,
            density=density * 0.2,
            height=1.5,
            anisotropy=0.0,
            color=(0.9, 0.9, 0.9),
            noise_scale=0.3,
            noise_detail=6,
            animation_speed=0.3,
        ),
        "chimney": AtmosphereConfig(
            name="chimney_smoke",
            atmosphere_type=AtmosphereType.SMOKE,
            density=density * 1.2,
            height=10.0,
            anisotropy=-0.2,
            color=(0.35, 0.35, 0.4),
            noise_scale=2.0,
            noise_detail=4,
            animation_speed=1.0,
        ),
        "steam": AtmosphereConfig(
            name="steam",
            atmosphere_type=AtmosphereType.STEAM,
            density=density * 0.5,
            height=2.0,
            anisotropy=0.6,
            color=(0.98, 0.98, 1.0),
            emission_strength=0.1,
            emission_color=(1.0, 1.0, 1.0),
            noise_scale=0.5,
            animation_speed=0.8,
        ),
    }

    return presets.get(preset, presets["standard"])


# =============================================================================
# VOLUMETRIC LIGHTING
# =============================================================================

def create_volumetric_beam(
    preset: str = "god_rays",
    direction: Tuple[float, float] = (0.0, 45.0),
    intensity: float = 1.0
) -> VolumetricConfig:
    """
    Create a volumetric light beam configuration.

    Args:
        preset: Beam type (god_rays, spotlight, window_light)
        direction: (azimuth, elevation) in degrees
        intensity: Intensity multiplier

    Returns:
        VolumetricConfig
    """
    presets = {
        "god_rays": VolumetricConfig(
            name="god_rays",
            volumetric_type=VolumetricType.GOD_RAYS,
            direction=direction,
            cone_angle=45.0,
            intensity=intensity,
            color=(1.0, 0.98, 0.9),
            scattering=0.8,
            absorption=0.05,
            distance=20.0,
            noise_amount=0.3,
        ),
        "spotlight": VolumetricConfig(
            name="spotlight_beam",
            volumetric_type=VolumetricType.LIGHT_BEAM,
            direction=direction,
            cone_angle=15.0,
            intensity=intensity * 1.5,
            color=(1.0, 1.0, 1.0),
            scattering=1.0,
            absorption=0.1,
            distance=8.0,
            noise_amount=0.1,
        ),
        "window_light": VolumetricConfig(
            name="window_light",
            volumetric_type=VolumetricType.SHAFT,
            direction=direction,
            cone_angle=60.0,
            intensity=intensity * 0.8,
            color=(1.0, 0.97, 0.9),
            scattering=0.5,
            absorption=0.02,
            distance=15.0,
            noise_amount=0.4,
        ),
        "ambient": VolumetricConfig(
            name="ambient_volumetric",
            volumetric_type=VolumetricType.AMBIENT,
            direction=(0.0, 0.0),
            cone_angle=180.0,
            intensity=intensity * 0.3,
            color=(0.95, 0.95, 1.0),
            scattering=0.3,
            absorption=0.01,
            distance=50.0,
            noise_amount=0.2,
        ),
    }

    return presets.get(preset, presets["god_rays"])


# =============================================================================
# PARTICLE EFFECTS
# =============================================================================

def create_dust_motes(
    count: int = 500,
    animated: bool = True
) -> ParticleConfig:
    """
    Create floating dust motes effect.

    Args:
        count: Number of particles
        animated: Whether particles should drift

    Returns:
        ParticleConfig
    """
    return ParticleConfig(
        name="dust_motes",
        particle_type=ParticleType.DUST_MOTES,
        count=count,
        size_min=0.005,
        size_max=0.02,
        velocity=(0.02, 0.02, 0.03) if animated else (0, 0, 0),
        lifetime=30.0,
        color=(1.0, 1.0, 0.98, 0.3),
        emission_box=(10.0, 10.0, 4.0),
        turbulence=0.05 if animated else 0.0,
        glow=0.1,
        properties={
            "catch_light": True,
            "slow_drift": animated,
        },
    )


def create_rain_effect(
    intensity: str = "medium",
    wind_speed: float = 0.0
) -> ParticleConfig:
    """
    Create rain particle effect.

    Args:
        intensity: Rain intensity (light, medium, heavy)
        wind_speed: Horizontal wind speed in m/s

    Returns:
        ParticleConfig
    """
    intensity_params = {
        "light": {"count": 2000, "velocity": (0, 0, -4)},
        "medium": {"count": 5000, "velocity": (0, 0, -6)},
        "heavy": {"count": 10000, "velocity": (0, 0, -8)},
    }

    params = intensity_params.get(intensity, intensity_params["medium"])

    # Apply wind to velocity
    velocity = (
        wind_speed * 0.1,
        wind_speed * 0.1,
        params["velocity"][2]
    )

    return ParticleConfig(
        name=f"rain_{intensity}",
        particle_type=ParticleType.DUST_MOTES,  # Using same type with different params
        count=params["count"],
        size_min=0.002,
        size_max=0.005,
        velocity=velocity,
        lifetime=2.0,
        color=(0.8, 0.85, 0.9, 0.4),
        emission_box=(20.0, 20.0, 10.0),
        gravity=9.8,
        turbulence=0.02,
        properties={
            "streak_length": 0.1,
            "splash": True,
        },
    )


def create_snow_effect(
    intensity: str = "medium",
    wind_speed: float = 0.0
) -> ParticleConfig:
    """
    Create snow particle effect.

    Args:
        intensity: Snow intensity (light, medium, heavy)
        wind_speed: Horizontal wind speed

    Returns:
        ParticleConfig
    """
    intensity_params = {
        "light": {"count": 1000, "velocity": (0, 0, -0.5)},
        "medium": {"count": 3000, "velocity": (0, 0, -0.8)},
        "heavy": {"count": 6000, "velocity": (0, 0, -1.0)},
    }

    params = intensity_params.get(intensity, intensity_params["medium"])

    return ParticleConfig(
        name=f"snow_{intensity}",
        particle_type=ParticleType.DUST_MOTES,
        count=params["count"],
        size_min=0.01,
        size_max=0.04,
        velocity=params["velocity"],
        lifetime=15.0,
        color=(1.0, 1.0, 1.0, 0.9),
        emission_box=(15.0, 15.0, 8.0),
        gravity=0.5,
        turbulence=0.3,
        properties={
            "flutter": True,
            "accumulate": False,
        },
    )


def create_sparks_effect(
    preset: str = "welding",
    count: int = 200
) -> ParticleConfig:
    """
    Create sparks particle effect.

    Args:
        preset: Spark type (welding, fire, magic)
        count: Number of particles

    Returns:
        ParticleConfig
    """
    presets = {
        "welding": ParticleConfig(
            name="welding_sparks",
            particle_type=ParticleType.SPARKS,
            count=count,
            size_min=0.005,
            size_max=0.02,
            velocity=(0, 0, 3),
            lifetime=1.0,
            color=(1.0, 0.8, 0.2, 1.0),
            emission_box=(0.2, 0.2, 0.1),
            gravity=9.8,
            turbulence=0.1,
            glow=2.0,
        ),
        "fire": ParticleConfig(
            name="fire_sparks",
            particle_type=ParticleType.EMBERS,
            count=count,
            size_min=0.01,
            size_max=0.03,
            velocity=(0, 0, 2),
            lifetime=2.0,
            color=(1.0, 0.5, 0.1, 1.0),
            emission_box=(0.5, 0.5, 0.1),
            gravity=2.0,
            turbulence=0.5,
            glow=1.5,
        ),
        "magic": ParticleConfig(
            name="magic_sparks",
            particle_type=ParticleType.SPARKS,
            count=count,
            size_min=0.01,
            size_max=0.02,
            velocity=(0, 0, 1),
            lifetime=3.0,
            color=(0.5, 0.8, 1.0, 1.0),
            emission_box=(1.0, 1.0, 1.0),
            gravity=-0.5,
            turbulence=0.8,
            glow=3.0,
        ),
    }

    return presets.get(preset, presets["welding"])


# =============================================================================
# LENS EFFECTS
# =============================================================================

def create_lens_effect(preset: str = "cinematic") -> LensEffectConfig:
    """
    Create lens/post-processing effect configuration.

    Args:
        preset: Effect style (cinematic, dreamy, vintage, sharp)

    Returns:
        LensEffectConfig
    """
    presets = {
        "cinematic": LensEffectConfig(
            name="cinematic",
            bloom_intensity=0.15,
            bloom_threshold=0.9,
            bloom_radius=5.0,
            glare_type="streaks",
            glare_intensity=0.1,
            vignette_intensity=0.3,
        ),
        "dreamy": LensEffectConfig(
            name="dreamy",
            bloom_intensity=0.4,
            bloom_threshold=0.6,
            bloom_radius=8.0,
            glare_type="ghosts",
            glare_intensity=0.2,
            chromatic_aberration=0.002,
            vignette_intensity=0.2,
        ),
        "vintage": LensEffectConfig(
            name="vintage",
            bloom_intensity=0.1,
            bloom_threshold=0.85,
            bloom_radius=4.0,
            glare_type="frosty",
            glare_intensity=0.15,
            chromatic_aberration=0.003,
            vignette_intensity=0.5,
            film_grain=0.15,
            color_correction={
                "contrast": 1.1,
                "saturation": 0.9,
                "warmth": 0.1,
            },
        ),
        "sharp": LensEffectConfig(
            name="sharp",
            bloom_intensity=0.05,
            bloom_threshold=0.95,
            bloom_radius=3.0,
            vignette_intensity=0.1,
            color_correction={
                "contrast": 1.15,
                "saturation": 1.05,
            },
        ),
        "commercial": LensEffectConfig(
            name="commercial",
            bloom_intensity=0.1,
            bloom_threshold=0.92,
            bloom_radius=4.5,
            vignette_intensity=0.15,
            color_correction={
                "contrast": 1.05,
                "saturation": 1.1,
            },
        ),
    }

    return presets.get(preset, presets["cinematic"])


# =============================================================================
# COMBINED ATMOSPHERE PRESETS
# =============================================================================

@dataclass
class AtmospherePreset:
    """Complete atmosphere preset combining multiple effects."""
    name: str
    description: str
    atmosphere: Optional[AtmosphereConfig] = None
    volumetric: Optional[VolumetricConfig] = None
    particles: Optional[ParticleConfig] = None
    lens_effects: Optional[LensEffectConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "atmosphere": self.atmosphere.to_dict() if self.atmosphere else None,
            "volumetric": self.volumetric.to_dict() if self.volumetric else None,
            "particles": self.particles.to_dict() if self.particles else None,
            "lens_effects": self.lens_effects.to_dict() if self.lens_effects else None,
        }


def get_atmosphere_preset(preset_name: str) -> AtmospherePreset:
    """
    Get a complete atmosphere preset.

    Args:
        preset_name: Preset name

    Returns:
        AtmospherePreset with combined effects
    """
    presets = {
        "morning_studio": AtmospherePreset(
            name="morning_studio",
            description="Soft morning light with subtle haze",
            atmosphere=create_fog_effect("morning_mist", 0.2),
            particles=create_dust_motes(300, True),
            lens_effects=create_lens_effect("dreamy"),
        ),
        "dramatic_studio": AtmospherePreset(
            name="dramatic_studio",
            description="Dramatic lighting with volumetric beams",
            volumetric=create_volumetric_beam("god_rays", (45, 30), 1.2),
            particles=create_dust_motes(500, True),
            lens_effects=create_lens_effect("cinematic"),
        ),
        "vintage_portrait": AtmospherePreset(
            name="vintage_portrait",
            description="Vintage film look with soft glow",
            atmosphere=create_haze_effect("standard", 0.1),
            lens_effects=create_lens_effect("vintage"),
        ),
        "product_clean": AtmospherePreset(
            name="product_clean",
            description="Clean, sharp product photography",
            particles=create_dust_motes(100, False),
            lens_effects=create_lens_effect("sharp"),
        ),
        "atmospheric_exterior": AtmospherePreset(
            name="atmospheric_exterior",
            description="Atmospheric outdoor lighting",
            atmosphere=create_haze_effect("atmospheric", 0.3),
            volumetric=create_volumetric_beam("god_rays", (30, 45), 0.8),
            lens_effects=create_lens_effect("cinematic"),
        ),
        "rainy_mood": AtmospherePreset(
            name="rainy_mood",
            description="Rainy atmospheric mood",
            atmosphere=create_fog_effect("standard", 0.4),
            particles=create_rain_effect("medium", 2.0),
            lens_effects=create_lens_effect("cinematic"),
        ),
        "snowy_scene": AtmospherePreset(
            name="snowy_scene",
            description="Gentle snowfall",
            atmosphere=create_fog_effect("morning_mist", 0.2),
            particles=create_snow_effect("light", 0.5),
            lens_effects=create_lens_effect("dreamy"),
        ),
        "smoky_bar": AtmospherePreset(
            name="smoky_bar",
            description="Atmospheric bar/club lighting",
            atmosphere=create_smoke_effect("standard", 0.5),
            volumetric=create_volumetric_beam("spotlight", (0, 60), 1.5),
            lens_effects=create_lens_effect("vintage"),
        ),
    }

    if preset_name not in presets:
        available = list(presets.keys())
        raise ValueError(f"Unknown preset: {preset_name}. Available: {available}")

    return presets[preset_name]


def list_atmosphere_presets() -> List[str]:
    """List available atmosphere presets."""
    return [
        "morning_studio",
        "dramatic_studio",
        "vintage_portrait",
        "product_clean",
        "atmospheric_exterior",
        "rainy_mood",
        "snowy_scene",
        "smoky_bar",
    ]
