"""
Charlotte Digital Twin Lighting System

Comprehensive lighting setup for realistic outdoor scenes:
- HDRI sky environments
- Procedural sky fallback (no HDRI required)
- Shadow configuration
- Atmospheric effects (fog, haze)
- Time-of-day system

Usage:
    from lib.charlotte_digital_twin.lighting import (
        HDRISetup,
        ProceduralSky,
        AtmosphericEffects,
        setup_realistic_lighting,
    )

    # Setup HDRI lighting
    hdri = HDRISetup()
    hdri.load_from_preset("sunny_afternoon")

    # Or use procedural sky
    sky = ProceduralSky()
    sky.set_time_of_day(14, 30)  # 2:30 PM

    # Add atmosphere
    atmosphere = AtmosphericEffects()
    atmosphere.add_distance_fog(density=0.001, start=100)
"""

from .hdri_setup import (
    HDRIConfig,
    HDRIPreset,
    HDRISetup,
    load_hdri_from_file,
    load_hdri_from_preset,
)

from .procedural_sky import (
    SkyConfig,
    TimeOfDay,
    ProceduralSky,
    create_sky_for_time,
)

from .atmosphere import (
    AtmosphereConfig,
    FogType,
    AtmosphericEffects,
    add_distance_haze,
    add_volumetric_fog,
)

from .lighting_setup import (
    LightingConfig,
    ShadowConfig,
    setup_realistic_lighting,
    configure_cycles_shadows,
    setup_charlotte_afternoon,
    setup_charlotte_golden_hour,
    setup_charlotte_overcast,
)

__version__ = "1.0.0"
__all__ = [
    # HDRI
    "HDRIConfig",
    "HDRIPreset",
    "HDRISetup",
    "load_hdri_from_file",
    "load_hdri_from_preset",
    # Procedural Sky
    "SkyConfig",
    "TimeOfDay",
    "ProceduralSky",
    "create_sky_for_time",
    # Atmosphere
    "AtmosphereConfig",
    "FogType",
    "AtmosphericEffects",
    "add_distance_haze",
    "add_volumetric_fog",
    # Lighting Setup
    "LightingConfig",
    "ShadowConfig",
    "setup_realistic_lighting",
    "configure_cycles_shadows",
    "setup_charlotte_afternoon",
    "setup_charlotte_golden_hour",
    "setup_charlotte_overcast",
]
