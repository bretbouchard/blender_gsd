"""
Lighting Setup Utilities

Combines HDRI/procedural sky with proper Cycles shadow configuration
for realistic outdoor rendering.
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .hdri_setup import HDRISetup, HDRIPreset, HDRIConfig
from .procedural_sky import ProceduralSky, TimeOfDay, SkyConfig
from .atmosphere import AtmosphericEffects, AtmosphereConfig


@dataclass
class ShadowConfig:
    """Configuration for shadow rendering."""
    # Soft shadows
    soft_size: float = 0.1  # Sun soft size

    # Contact shadows (EEVEE)
    use_contact_shadows: bool = True
    contact_thickness: float = 0.2

    # Shadow buffer (Cycles)
    use_transparent_shadows: bool = True
    max_bounces: int = 4


@dataclass
class LightingConfig:
    """Complete lighting configuration."""
    # Use HDRI or procedural sky
    use_hdri: bool = False
    hdri_preset: HDRIPreset = HDRIPreset.SUNNY_AFTERNOON
    hdri_path: Optional[str] = None

    # Or use procedural
    time_of_day: TimeOfDay = TimeOfDay.AFTERNOON
    custom_hour: Optional[int] = None

    # Atmosphere
    atmosphere_preset: str = "light_haze"

    # Shadows
    shadow_config: ShadowConfig = None

    # Render engine
    render_engine: str = "CYCLES"
    cycles_samples: int = 64

    def __post_init__(self):
        if self.shadow_config is None:
            self.shadow_config = ShadowConfig()


def setup_realistic_lighting(
    config: Optional[LightingConfig] = None,
) -> bool:
    """
    Setup complete realistic lighting for a scene.

    Args:
        config: Lighting configuration

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    config = config or LightingConfig()
    success = True

    # Setup sky/environment
    if config.use_hdri:
        hdri = HDRISetup()
        if config.hdri_path:
            success = hdri.load_from_file(config.hdri_path)
        else:
            success = hdri.load_from_preset(config.hdri_preset)
    else:
        sky = ProceduralSky()
        if config.custom_hour is not None:
            success = sky.set_time_of_day(config.custom_hour)
        else:
            success = sky.set_preset_time(config.time_of_day)

    # Setup atmosphere
    if config.atmosphere_preset:
        atmosphere = AtmosphericEffects()
        atmosphere.apply_preset(config.atmosphere_preset)

    # Configure shadows
    configure_cycles_shadows(config.shadow_config)

    # Set render engine
    bpy.context.scene.render.engine = config.render_engine
    if config.render_engine == "CYCLES":
        bpy.context.scene.cycles.samples = config.cycles_samples

    return success


def configure_cycles_shadows(config: Optional[ShadowConfig] = None) -> bool:
    """
    Configure Cycles shadow settings for realistic shadows.

    Args:
        config: Shadow configuration

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    config = config or ShadowConfig()
    scene = bpy.context.scene

    # Cycles settings
    if scene.render.engine == "CYCLES":
        cycles = scene.cycles

        # Transparent shadows
        cycles.transparent_max_bounces = config.max_bounces

        # Light sampling
        cycles.use_direct_light = True

        # Ambient occlusion for contact shadows
        cycles.use_fast_gi = False

    # Configure sun light if present
    for obj in scene.objects:
        if obj.type == "LIGHT" and obj.data.type == "SUN":
            light = obj.data

            # Soft shadows
            light.shadow_soft_size = config.soft_size

            # Contact shadows (Blender 4.0+)
            if hasattr(light, "use_contact_shadow"):
                light.use_contact_shadow = config.use_contact_shadows
            if hasattr(light, "contact_shadow_thickness"):
                light.contact_shadow_thickness = config.contact_thickness

    return True


def setup_charlotte_afternoon() -> bool:
    """
    Setup lighting for Charlotte afternoon scene.

    Preset configuration for typical I-277 car chase lighting.

    Returns:
        True if successful
    """
    config = LightingConfig(
        use_hdri=False,
        time_of_day=TimeOfDay.AFTERNOON,
        atmosphere_preset="light_haze",
        render_engine="CYCLES",
        cycles_samples=128,
        shadow_config=ShadowConfig(
            soft_size=0.15,
            use_contact_shadows=True,
        ),
    )
    return setup_realistic_lighting(config)


def setup_charlotte_golden_hour() -> bool:
    """
    Setup lighting for Charlotte golden hour scene.

    Dramatic sunset lighting for cinematic shots.

    Returns:
        True if successful
    """
    config = LightingConfig(
        use_hdri=False,
        time_of_day=TimeOfDay.GOLDEN_HOUR,
        atmosphere_preset="light_haze",
        render_engine="CYCLES",
        cycles_samples=128,
        shadow_config=ShadowConfig(
            soft_size=0.2,
            use_contact_shadows=True,
        ),
    )
    return setup_realistic_lighting(config)


def setup_charlotte_overcast() -> bool:
    """
    Setup lighting for Charlotte overcast day.

    Soft, diffuse lighting.

    Returns:
        True if successful
    """
    config = LightingConfig(
        use_hdri=True,
        hdri_preset=HDRIPreset.OVERCAST,
        atmosphere_preset="hazy",
        render_engine="CYCLES",
        cycles_samples=64,  # Lower samples OK for diffuse
    )
    return setup_realistic_lighting(config)


__all__ = [
    "ShadowConfig",
    "LightingConfig",
    "setup_realistic_lighting",
    "configure_cycles_shadows",
    "setup_charlotte_afternoon",
    "setup_charlotte_golden_hour",
    "setup_charlotte_overcast",
]
