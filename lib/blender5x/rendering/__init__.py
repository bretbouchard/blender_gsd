"""
Rendering Module for Blender 5.0+.

Provides utilities for thin film iridescence, improved subsurface scattering,
NanoVDB integration, and new volume rendering algorithms.

Example:
    >>> from lib.blender5x.rendering import ThinFilmIridescence, SubsurfaceScattering
    >>> ThinFilmIridescence.create_soap_bubble()
    >>> SubsurfaceScattering.configure_skin(material)
"""

from .thin_film import (
    ThinFilmIridescence,
    ThinFilmPreset,
    ThinFilmSettings,
    THIN_FILM_PRESETS,
)

from .sss import (
    SubsurfaceScattering,
    SSSProfile,
    SSSPreset,
    SSSSettings,
    SSS_PRESETS,
)

from .nano_vdb import (
    NanoVDBIntegration,
    NanoVDBGridType,
    NanoVDBStats,
    MemoryInfo,
)

from .volume_render import (
    VolumeRendering,
    VolumeSamplingMethod,
    VolumeInterpolation,
    VolumeRenderSettings,
    VOLUME_QUALITY_PRESETS,
)

__all__ = [
    # Thin Film
    "ThinFilmIridescence",
    "ThinFilmPreset",
    "ThinFilmSettings",
    "THIN_FILM_PRESETS",
    # SSS
    "SubsurfaceScattering",
    "SSSProfile",
    "SSSPreset",
    "SSSSettings",
    "SSS_PRESETS",
    # NanoVDB
    "NanoVDBIntegration",
    "NanoVDBGridType",
    "NanoVDBStats",
    "MemoryInfo",
    # Volume Render
    "VolumeRendering",
    "VolumeSamplingMethod",
    "VolumeInterpolation",
    "VolumeRenderSettings",
    "VOLUME_QUALITY_PRESETS",
]
