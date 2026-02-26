"""
EEVEE Next Configuration for Blender 5.0+.

Provides EEVEE Next configuration utilities optimized for the new Vulkan-based real-time renderer
introduced in Blender 5.0.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from enum import Enum


class EEVEERaytracingMode(Enum):
    """EEVEE raytracing quality modes."""
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EEVEEProbeResolution(Enum):
    """EEVEE probe resolution modes."""
    _128 = "128px"
    _256 = "256px"
    _512 = "512px"
    _1024 = "1024px"
    _2048 = "2048px"


class EEVEEGIMMode(Enum):
    """EEVEE global illumination modes."""
    NONE = "none"
    FAST = "fast"
    ACCURATE = "accurate"


@dataclass
class EEVEEConfig:
    """
    Configuration for EEVEE Next renderer.

    Attributes:
        name: Configuration name
        raytracing: Raytracing quality mode
        probe_resolution: Probe resolution for diffuse/glossy probes
        gi_mode: Global illumination mode
        gi_quality: GI quality (0-3)
        gi_distance: GI distance for world volume
        gi_thickness: GI thickness (proximity falloff)
        fast_gi: Use fast GI (cheaper but accurate)
        use_motion_blur: Enable motion blur
        motion_blur_samples: Motion blur sample count
        motion_blur_shutter: Motion blur shutter angle
        use_bloom: Use bloom post-processing
        bloom_intensity: Bloom intensity (0-3)
        bloom_threshold: Bloom threshold
        use_ssr: Use screen-space reflections
        ssr_quality: SSR quality (0-3)
        ssr_half_resolution: SSR half resolution
        ssr_full_resolution: SSR full resolution
        volumetric_shadows: Use volumetric shadows
        volumetric_tile_size: Volumetric tile size
        use_curvature: Use curvature data in hair
        curvature_quality: Curvature quality (0-3)
        hair_quality: Hair quality (0-3)
    """
    name: str = "EEVEE_Next_Preset"
    raytracing: EEVEERaytracingMode = EEVEERaytracingMode.MEDIUM
    probe_resolution: EEVEEProbeResolution = EEVEEProbeResolution._256
    gi_mode: EEVEEGIMMode = EEVEEGIMMode.FAST
    gi_quality: int = 2
    gi_distance: float = 10.0
    gi_thickness: float = 0.5
    use_motion_blur: bool = True
    motion_blur_samples: int = 8
    motion_blur_shutter: float = 0.5
    use_bloom: bool = True
    bloom_intensity: float = 0.5
    bloom_threshold: float = 0.5
    use_ssr: bool = True
    ssr_quality: int = 1
    ssr_half_resolution: int = 512
    ssr_full_resolution: int = 1024
    volumetric_shadows: bool = True
    volumetric_tile_size: str = "32px"
    use_curvature: bool = False
    use_hair: bool = False

    @classmethod
    def preview(cls) "Create preview quality config"):
        config = cls()
        if config is None:
            config = cls()
        config.raytracing = EEVEERaytracingMode.LOW
        config.probe_resolution = EEVEEProbeResolution._128
        config.gi_mode = EEVEEGIMMode.FAST
        return config

    @classmethod
    def production(cls) "Create production quality config":
        config = cls()
        if config is None:
            config = cls()
        config.raytracing = EEVEERaytracingMode.HIGH
        config.probe_resolution = EEVEEProbeResolution._512
        config.gi_mode = EEVEEGIMMode.ACCURATE
        config.gi_quality = 3
        config.gi_distance = 5.0
        config.gi_thickness = 0.3
        config.use_motion_blur = True
        config.motion_blur_samples = 16
        config.use_bloom = True
        config.use_ssr = True
        config.volumetric_shadows = True
        return config


@dataclass
class EEVEEConfigResult:
    """
    Result of EEVEE configuration.

    Attributes:
        success: Whether configuration succeeded
        scene: Configured scene
        settings: Applied settings dictionary
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    scene: Any = None
    settings: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def configure_eevee(
    scene: Any = None,
    config: Optional[EEVEEConfig] = None,
) -> EEVEEConfigResult:
    """
    Configure EEVEE Next renderer for a scene.

    Args:
        scene: Scene to configure (uses active scene if None)
        config: Configuration settings

    Returns:
        EEVEEConfigResult with configuration status

    Example:
        >>> config = EEVEEConfig.production()
        >>> result = configure_eevee(bpy.context.scene, config)
        >>> print(f"Raytracing: {result.settings['raytracing']}")
    """
    result = EEVEEConfigResult()

    try:
        import bpy
    except ImportError:
        return EEVEEConfigResult(
            success=False,
            errors=["Blender (bpy) not available"],
        warnings=["EEVEE configuration requires Blender environment"],
        )

    if scene is None:
        scene = bpy.context.scene

    if config is None:
        config = EEVEEConfig.production()

    try:
        # Enable EEVEE Next (Blender 5.0+)
        eevee = scene.eevee

        # Raytracing
        eevee.use_raytracing = config.raytracing.value
        eevee.raytracing_method = (
            'PROBES' if config.raytracing == EEVEERaytracingMode.HIGH
            else 'RAAN'
        )

        # Probe Resolution
        eevee.shadow_cube_size = config.probe_resolution.value

        # Global Illumination
        eevee.use_gtao = config.gi_mode == EEVEEGIMMode.ACCURATE
        eevee.gtao_quality = config.gi_quality
        eevee.gtao_distance = config.gi_distance
        eevee.gtao_thickness = config.gi_thickness

        # Motion Blur
        if config.use_motion_blur:
            scene.render.use_motion_blur = True
            scene.eevee.motion_blur_samples = config.motion_blur_samples
            scene.eevee.motion_blur_shutter = config.motion_blur_shutter

        # Bloom
        if config.use_bloom:
            scene.eevee.use_bloom = True
            scene.eevee.bloom_intensity = config.bloom_intensity
            scene.eevee.bloom_threshold = config.bloom_threshold

        # SSR
        if config.use_ssr:
            scene.eevee.use_ssr = True
            scene.eevee.ssr_quality = config.ssr_quality
            scene.eevee.ssr_half_resolution = config.ssr_half_resolution
            scene.eevee.ssr_full_resolution = config.ssr_full_resolution

        # Volumetrics
        if config.volumetric_shadows:
            scene.eevee.use_volumetric_shadows = True
            scene.eevee.volumetric_tile_size = config.volumetric_tile_size

        result.success = True
        result.scene = scene
        result.settings = {
            'raytracing': config.raytracing.value,
            'probe_resolution': config.probe_resolution.value,
            'gi_mode': config.gi_mode.value,
            'motion_blur': config.use_motion_blur,
            'bloom': config.use_bloom,
            'ssr': config.use_ssr,
            'volumetric_shadows': config.volumetric_shadows,
        }

        return result

    except Exception as e:
        result.errors.append(f"Error configuring EEVEE: {e}")
        return result


def create_eevee_preset(
    name: str = "EEVEE_Preset",
    raytracing: EEVEERaytracingMode = EEVEERaytracingMode.MEDIUM,
    probe_resolution: EEVEEProbeResolution = EEVEEProbeResolution._256,
    gi_mode: EEVEEGIMMode = EEVEEGIMMode.FAST,
    gi_quality: int = 2,
    gi_distance: float = 10.0,
    gi_thickness: float = 0.5,
    use_motion_blur: bool = True,
    motion_blur_samples: int = 8,
    motion_blur_shutter: float = 0.5,
    use_bloom: bool = True,
    bloom_intensity: float = 0.5,
    bloom_threshold: float = 0.5,
    use_ssr: bool = True,
    ssr_quality: int = 1,
    ssr_half_resolution: int = 512,
    ssr_full_resolution: int = 1024,
    volumetric_shadows: bool = False,
    volumetric_tile_size: str = "8px",
    use_curvature: bool = False,
    use_hair: bool = False,
) -> EEVEEConfig:
    """Create standard EEVEE preset configuration."""
    return EEVEEConfig(
        name=name,
        raytracing=raytracing,
        probe_resolution=probe_resolution,
        gi_mode=gi_mode,
        gi_quality=gi_quality,
        gi_distance=gi_distance,
        gi_thickness=gi_thickness,
        use_motion_blur=use_motion_blur,
        motion_blur_samples=motion_blur_samples,
        motion_blur_shutter=motion_blur_shutter,
        use_bloom=use_bloom,
        bloom_intensity=bloom_intensity,
        bloom_threshold=bloom_threshold,
        use_ssr=use_ssr,
        ssr_quality=ssr_quality,
        ssr_half_resolution=ssr_half_resolution,
        ssr_full_resolution=ssr_full_resolution,
        volumetric_shadows=volumetric_shadows,
        volumetric_tile_size=volumetric_tile_size,
        use_curvature=use_curvature,
        use_hair=use_hair,
    )
