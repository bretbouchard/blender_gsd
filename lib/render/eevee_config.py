"""
EEVEE Next Configuration System

Provides configuration utilities for EEVEE Next render engine in Blender 5.x.

Features:
- Raytracing configuration (screen-space probes)
- TAA (Temporal Anti-Aliasing) configuration
- Quality presets for different use cases
- Volumetric and shadow configuration

Blender 5.x EEVEE Next Features:
- Hardware raytracing (RTX, Metal)
- Screen-space global illumination via probes
- Improved shadow system
- Better subsurface scattering

Usage:
    from lib.render.eevee_config import apply_eevee_config, get_eevee_preset

    # Apply a preset
    config = get_eevee_preset('production')
    apply_eevee_config(config)

    # Configure raytracing
    configure_raytracing(samples=4)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class RaytracingMethod(Enum):
    """Raytracing methods for EEVEE Next."""
    PROBE = "PROBE"  # Screen-space probes (faster, good quality)
    RAYTRACED = "RAYTRACED"  # Full raytracing (slower, best quality)


class ShadowMethod(Enum):
    """Shadow methods."""
    ESIM = "ESIM"  # Evolutionary shadow Improvement
    SHADOW_MAP = "SHADOW_MAP"  # Traditional shadow maps


@dataclass
class EEVEENextConfig:
    """
    EEVEE Next render configuration for Blender 5.x.

    Attributes:
        name: Configuration name
        taa_samples: TAA render samples
        taa_reprojection: Enable TAA reprojection
        use_raytracing: Enable raytracing
        raytracing_method: Raytracing method (PROBE or RAYTRACED)
        raytracing_samples: Raytracing samples per pixel
        raytracing_resolution: Raytracing resolution scale (0.25-1.0)
        use_gtao: Enable ground-truth ambient occlusion
        gtao_quality: GTAO quality (0-1)
        use_sss: Enable subsurface scattering
        sss_samples: SSS samples
        sss_jitter_threshold: SSS jitter threshold
        use_volumetric: Enable volumetrics
        volumetric_samples: Volumetric samples
        volumetric_tile_size: Volumetric tile size
        shadow_method: Shadow method
        shadow_resolution: Shadow map resolution
        use_soft_shadows: Enable soft shadows
        light_threshold: Light culling threshold
        gi_distance: Global illumination distance
        gi_cubemap_resolution: Cubemap resolution for GI
        gi_visibility_samples: GI visibility samples
        use_fast_gi: Enable fast GI approximation
        overscan: Overscan percentage
    """
    name: str
    taa_samples: int = 32
    taa_reprojection: bool = True
    use_raytracing: bool = True
    raytracing_method: str = "PROBE"
    raytracing_samples: int = 3
    raytracing_resolution: float = 0.5
    use_gtao: bool = True
    gtao_quality: float = 0.5
    use_sss: bool = True
    sss_samples: int = 16
    sss_jitter_threshold: float = 0.3
    use_volumetric: bool = True
    volumetric_samples: int = 64
    volumetric_tile_size: int = 4
    shadow_method: str = "ESIM"
    shadow_resolution: int = 2048
    use_soft_shadows: bool = True
    light_threshold: float = 0.01
    gi_distance: float = 100.0
    gi_cubemap_resolution: int = 512
    gi_visibility_samples: int = 32
    use_fast_gi: bool = False
    overscan: float = 3.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "taa_samples": self.taa_samples,
            "taa_reprojection": self.taa_reprojection,
            "use_raytracing": self.use_raytracing,
            "raytracing_method": self.raytracing_method,
            "raytracing_samples": self.raytracing_samples,
            "raytracing_resolution": self.raytracing_resolution,
            "use_gtao": self.use_gtao,
            "gtao_quality": self.gtao_quality,
            "use_sss": self.use_sss,
            "sss_samples": self.sss_samples,
            "sss_jitter_threshold": self.sss_jitter_threshold,
            "use_volumetric": self.use_volumetric,
            "volumetric_samples": self.volumetric_samples,
            "volumetric_tile_size": self.volumetric_tile_size,
            "shadow_method": self.shadow_method,
            "shadow_resolution": self.shadow_resolution,
            "use_soft_shadows": self.use_soft_shadows,
            "light_threshold": self.light_threshold,
            "gi_distance": self.gi_distance,
            "gi_cubemap_resolution": self.gi_cubemap_resolution,
            "gi_visibility_samples": self.gi_visibility_samples,
            "use_fast_gi": self.use_fast_gi,
            "overscan": self.overscan,
        }


# =============================================================================
# EEVEE NEXT PRESETS
# =============================================================================

EEVEE_PRESETS: Dict[str, EEVEENextConfig] = {
    "viewport": EEVEENextConfig(
        name="viewport",
        taa_samples=8,
        taa_reprojection=True,
        use_raytracing=False,
        use_gtao=True,
        gtao_quality=0.25,
        use_sss=True,
        sss_samples=8,
        use_volumetric=False,
        shadow_method="SHADOW_MAP",
        shadow_resolution=512,
        use_soft_shadows=False,
        overscan=0.0,
    ),
    "preview": EEVEENextConfig(
        name="preview",
        taa_samples=16,
        taa_reprojection=True,
        use_raytracing=True,
        raytracing_method="PROBE",
        raytracing_samples=1,
        raytracing_resolution=0.25,
        use_gtao=True,
        gtao_quality=0.25,
        use_sss=True,
        sss_samples=8,
        use_volumetric=True,
        volumetric_samples=32,
        volumetric_tile_size=8,
        shadow_method="SHADOW_MAP",
        shadow_resolution=1024,
        use_soft_shadows=False,
        overscan=0.0,
    ),
    "draft": EEVEENextConfig(
        name="draft",
        taa_samples=32,
        taa_reprojection=True,
        use_raytracing=True,
        raytracing_method="PROBE",
        raytracing_samples=2,
        raytracing_resolution=0.5,
        use_gtao=True,
        gtao_quality=0.5,
        use_sss=True,
        sss_samples=16,
        use_volumetric=True,
        volumetric_samples=64,
        volumetric_tile_size=4,
        shadow_method="ESIM",
        shadow_resolution=2048,
        use_soft_shadows=True,
        overscan=3.0,
    ),
    "production": EEVEENextConfig(
        name="production",
        taa_samples=64,
        taa_reprojection=True,
        use_raytracing=True,
        raytracing_method="PROBE",
        raytracing_samples=4,
        raytracing_resolution=0.5,
        use_gtao=True,
        gtao_quality=0.75,
        use_sss=True,
        sss_samples=32,
        sss_jitter_threshold=0.3,
        use_volumetric=True,
        volumetric_samples=128,
        volumetric_tile_size=2,
        shadow_method="ESIM",
        shadow_resolution=4096,
        use_soft_shadows=True,
        gi_cubemap_resolution=512,
        gi_visibility_samples=64,
        overscan=3.0,
    ),
    "high_quality": EEVEENextConfig(
        name="high_quality",
        taa_samples=128,
        taa_reprojection=True,
        use_raytracing=True,
        raytracing_method="RAYTRACED",
        raytracing_samples=6,
        raytracing_resolution=1.0,
        use_gtao=True,
        gtao_quality=1.0,
        use_sss=True,
        sss_samples=64,
        sss_jitter_threshold=0.25,
        use_volumetric=True,
        volumetric_samples=256,
        volumetric_tile_size=1,
        shadow_method="ESIM",
        shadow_resolution=8192,
        use_soft_shadows=True,
        gi_cubemap_resolution=1024,
        gi_visibility_samples=128,
        overscan=5.0,
    ),
    "animation": EEVEENextConfig(
        name="animation",
        taa_samples=32,
        taa_reprojection=False,  # Disabled for animation stability
        use_raytracing=True,
        raytracing_method="PROBE",
        raytracing_samples=2,
        raytracing_resolution=0.5,
        use_gtao=True,
        gtao_quality=0.5,
        use_sss=True,
        sss_samples=16,
        use_volumetric=True,
        volumetric_samples=64,
        volumetric_tile_size=4,
        shadow_method="ESIM",
        shadow_resolution=2048,
        use_soft_shadows=True,
        overscan=3.0,
    ),
    "product": EEVEENextConfig(
        name="product",
        taa_samples=64,
        taa_reprojection=True,
        use_raytracing=True,
        raytracing_method="RAYTRACED",
        raytracing_samples=4,
        raytracing_resolution=1.0,
        use_gtao=True,
        gtao_quality=0.75,
        use_sss=True,
        sss_samples=32,
        use_volumetric=False,
        shadow_method="ESIM",
        shadow_resolution=4096,
        use_soft_shadows=True,
        overscan=3.0,
    ),
    "interior": EEVEENextConfig(
        name="interior",
        taa_samples=64,
        taa_reprojection=True,
        use_raytracing=True,
        raytracing_method="PROBE",
        raytracing_samples=4,
        raytracing_resolution=0.5,
        use_gtao=True,
        gtao_quality=1.0,
        use_sss=True,
        sss_samples=32,
        use_volumetric=True,
        volumetric_samples=128,
        volumetric_tile_size=2,
        shadow_method="ESIM",
        shadow_resolution=4096,
        use_soft_shadows=True,
        gi_distance=200.0,
        gi_cubemap_resolution=1024,
        gi_visibility_samples=64,
        use_fast_gi=True,
        overscan=3.0,
    ),
}


# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================

def get_eevee_preset(name: str) -> EEVEENextConfig:
    """
    Get an EEVEE Next preset by name.

    Args:
        name: Preset name

    Returns:
        EEVEENextConfig instance

    Raises:
        KeyError: If preset not found
    """
    if name not in EEVEE_PRESETS:
        available = list(EEVEE_PRESETS.keys())
        raise KeyError(f"EEVEE preset '{name}' not found. Available: {available}")
    return EEVEE_PRESETS[name]


def apply_eevee_config(config: EEVEENextConfig) -> bool:
    """
    Apply EEVEE Next configuration to current scene.

    Args:
        config: EEVEENextConfig instance

    Returns:
        True on success

    Raises:
        RuntimeError: If Blender not available
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene

    if scene.render.engine != "BLENDER_EEVEE_NEXT":
        scene.render.engine = "BLENDER_EEVEE_NEXT"

    eevee = scene.eevee

    # TAA
    eevee.taa_render_samples = config.taa_samples
    eevee.use_taa_reprojection = config.taa_reprojection

    # Raytracing
    eevee.use_raytracing = config.use_raytracing
    if config.use_raytracing:
        eevee.raytracing_method = config.raytracing_method
        eevee.raytracing_samples = config.raytracing_samples
        eevee.raytracing_resolution = config.raytracing_resolution

    # GTAO
    eevee.use_gtao = config.use_gtao
    if config.use_gtao:
        eevee.gtao_quality = config.gtao_quality

    # SSS
    eevee.use_sss = config.use_sss
    if config.use_sss:
        eevee.sss_samples = config.sss_samples
        eevee.sss_jitter_threshold = config.sss_jitter_threshold

    # Volumetrics
    eevee.use_volumetric = config.use_volumetric
    if config.use_volumetric:
        eevee.volumetric_samples = config.volumetric_samples
        eevee.volumetric_tile_size = config.volumetric_tile_size

    # Shadows
    eevee.shadow_method = config.shadow_method
    eevee.shadow_resolution = config.shadow_resolution
    eevee.use_soft_shadows = config.use_soft_shadows

    # GI
    eevee.gi_distance = config.gi_distance
    eevee.gi_cubemap_resolution = config.gi_cubemap_resolution
    eevee.gi_visibility_samples = config.gi_visibility_samples
    eevee.use_fast_gi = config.use_fast_gi

    # Light threshold
    eevee.light_threshold = config.light_threshold

    # Overscan
    eevee.overscan_size = config.overscan

    return True


def configure_raytracing(
    method: str = "PROBE",
    samples: int = 3,
    resolution: float = 0.5
) -> bool:
    """
    Configure EEVEE raytracing settings.

    Args:
        method: Raytracing method ('PROBE' or 'RAYTRACED')
        samples: Samples per pixel
        resolution: Resolution scale (0.25-1.0)

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene
    eevee = scene.eevee

    eevee.use_raytracing = True
    eevee.raytracing_method = method
    eevee.raytracing_samples = samples
    eevee.raytracing_resolution = max(0.25, min(1.0, resolution))

    return True


def configure_taa(
    samples: int = 64,
    reprojection: bool = True
) -> bool:
    """
    Configure EEVEE TAA settings.

    Args:
        samples: TAA render samples
        reprojection: Enable TAA reprojection

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene
    eevee = scene.eevee

    eevee.taa_render_samples = samples
    eevee.use_taa_reprojection = reprojection

    return True


def configure_volumetrics(
    samples: int = 128,
    tile_size: int = 2
) -> bool:
    """
    Configure EEVEE volumetric settings.

    Args:
        samples: Volumetric samples
        tile_size: Tile size (1, 2, 4, 8 - smaller is higher quality)

    Returns:
        True on success
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene
    eevee = scene.eevee

    eevee.use_volumetric = True
    eevee.volumetric_samples = samples
    eevee.volumetric_tile_size = tile_size

    return True


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "EEVEENextConfig",
    "RaytracingMethod",
    "ShadowMethod",
    "get_eevee_preset",
    "apply_eevee_config",
    "configure_raytracing",
    "configure_taa",
    "configure_volumetrics",
    "EEVEE_PRESETS",
]
