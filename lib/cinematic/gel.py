"""
Gel/Color Filter System Module

Provides gel and color filter functionality for cinematic lighting.
Gels are used to modify light color, temperature, softness, and character.

Common gel types:
- CTO (Color Temperature Orange): Warming gels to convert daylight to tungsten
- CTB (Color Temperature Blue): Cooling gels to convert tungsten to daylight
- Diffusion: Softens light quality
- Creative colors: Dramatic accent lighting

Usage:
    from lib.cinematic.gel import apply_gel, create_gel_from_preset, combine_gels
    from lib.cinematic.types import GelConfig

    # Apply gel from preset
    gel = create_gel_from_preset("cto_full")
    apply_gel(light_object, gel)

    # Combine multiple gels
    combined = combine_gels(["cto_quarter", "diffusion_half"])
    apply_gel(light_object, combined)

    # Convert color temperature to RGB
    rgb = kelvin_to_rgb(3200)  # Tungsten
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List
import math

from .types import GelConfig
from .preset_loader import get_gel_preset

# Guarded bpy import
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


# Constants
KELVIN_MIN = 1000
KELVIN_MAX = 40000
BLENDER_40_MIN = (4, 0, 0)


def _get_blender_version() -> Tuple[int, int, int]:
    """
    Get Blender version as tuple.

    Returns:
        Version tuple (major, minor, patch) or (0, 0, 0) if not available
    """
    if not BLENDER_AVAILABLE:
        return (0, 0, 0)

    try:
        return bpy.app.version
    except Exception:
        return (0, 0, 0)


def kelvin_to_rgb(kelvin: float) -> Tuple[float, float, float]:
    """
    Convert color temperature in Kelvin to RGB.

    Uses Tanner Helland algorithm for accurate color temperature conversion.
    Valid range: 1000K to 40000K.

    Common color temperature values:
    - Candle: 1900K
    - Tungsten: 3200K
    - Daylight: 5500K-6500K
    - Overcast: 7000K
    - Blue sky: 10000K+

    Args:
        kelvin: Color temperature in Kelvin

    Returns:
        RGB tuple with values in 0.0-1.0 range
    """
    # Clamp to valid range
    kelvin = max(KELVIN_MIN, min(KELVIN_MAX, kelvin))

    # Convert to hundreds of kelvin
    temp = kelvin / 100.0

    # Calculate red
    if temp <= 66:
        red = 255.0
    else:
        red = temp - 60.0
        red = 329.698727446 * (red ** -0.1332047592)
        red = max(0.0, min(255.0, red))

    # Calculate green
    if temp <= 66:
        green = temp
        green = 99.4708025861 * math.log(green) - 161.1195681661
    else:
        green = temp - 60.0
        green = 288.1221695283 * (green ** -0.0755148492)
    green = max(0.0, min(255.0, green))

    # Calculate blue
    if temp >= 66:
        blue = 255.0
    elif temp <= 19:
        blue = 0.0
    else:
        blue = temp - 10.0
        blue = 138.5177312231 * math.log(blue) - 305.0447927307
        blue = max(0.0, min(255.0, blue))

    # Normalize to 0-1 range
    return (red / 255.0, green / 255.0, blue / 255.0)


def apply_gel(light_obj: Any, gel_config: GelConfig) -> bool:
    """
    Apply gel/color filter to a light.

    Modifies light color, softness, and optionally uses native
    temperature mode on Blender 4.0+.

    Args:
        light_obj: Blender light object
        gel_config: GelConfig with color, temperature_shift, softness settings

    Returns:
        True if successful, False if Blender not available or error occurred
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Get light data
        if light_obj is None or not hasattr(light_obj, "data"):
            return False

        light = light_obj.data
        if light is None:
            return False

        # Apply color if specified (not default white)
        if gel_config.color != (1.0, 1.0, 1.0):
            # Multiply existing color with gel color
            current_color = tuple(light.color)
            new_color = (
                current_color[0] * gel_config.color[0],
                current_color[1] * gel_config.color[1],
                current_color[2] * gel_config.color[2],
            )
            light.color = new_color

        # Apply temperature shift
        if gel_config.temperature_shift != 0:
            version = _get_blender_version()

            # Blender 4.0+ has native temperature support
            if version >= BLENDER_40_MIN:
                # Use native temperature mode
                if hasattr(light, "use_temperature"):
                    light.use_temperature = True
                    if hasattr(light, "temperature"):
                        # Base temperature is typically 6500K (daylight)
                        base_temp = 6500.0
                        light.temperature = base_temp + gel_config.temperature_shift
            else:
                # Fallback: convert temperature shift to color
                base_temp = 6500.0
                target_temp = base_temp + gel_config.temperature_shift
                temp_color = kelvin_to_rgb(target_temp)

                # Multiply with existing color
                current_color = tuple(light.color)
                new_color = (
                    current_color[0] * temp_color[0],
                    current_color[1] * temp_color[1],
                    current_color[2] * temp_color[2],
                )
                light.color = new_color

        # Apply softness (shadow soft size)
        if gel_config.softness > 0:
            if hasattr(light, "shadow_soft_size"):
                # Add softness to existing value
                light.shadow_soft_size = max(
                    light.shadow_soft_size,
                    gel_config.softness
                )

        return True

    except Exception:
        return False


def create_gel_from_preset(preset_name: str) -> GelConfig:
    """
    Create a GelConfig from a preset name.

    Loads preset from configs/cinematic/lighting/gel_presets.yaml.

    Args:
        preset_name: Name of the gel preset (e.g., "cto_full", "diffusion_half")

    Returns:
        GelConfig populated with preset values

    Raises:
        FileNotFoundError: If gel_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    preset = get_gel_preset(preset_name)

    # Extract fields from preset
    name = preset.get("name", preset_name)
    color = tuple(preset.get("color", (1.0, 1.0, 1.0)))
    temperature_shift = float(preset.get("temperature_shift", 0.0))
    softness = float(preset.get("softness", 0.0))
    transmission = float(preset.get("transmission", 1.0))
    combines = preset.get("combines", [])

    return GelConfig(
        name=name,
        color=color,
        temperature_shift=temperature_shift,
        softness=softness,
        transmission=transmission,
        combines=combines,
    )


def combine_gels(gel_names: List[str]) -> GelConfig:
    """
    Combine multiple gels into a single GelConfig.

    Multiplies colors, sums temperature_shifts, averages softness.

    Args:
        gel_names: List of gel preset names to combine

    Returns:
        Combined GelConfig with cumulative effects

    Raises:
        FileNotFoundError: If gel_presets.yaml doesn't exist
        ValueError: If any preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    if not gel_names:
        return GelConfig()

    # Load all gel presets
    gel_configs = [create_gel_from_preset(name) for name in gel_names]

    # Start with neutral values
    combined_color = [1.0, 1.0, 1.0]
    combined_temp_shift = 0.0
    total_softness = 0.0
    min_transmission = 1.0

    for gel in gel_configs:
        # Multiply colors (cumulative filtering effect)
        combined_color[0] *= gel.color[0]
        combined_color[1] *= gel.color[1]
        combined_color[2] *= gel.color[2]

        # Sum temperature shifts
        combined_temp_shift += gel.temperature_shift

        # Accumulate softness (will average)
        total_softness += gel.softness

        # Take minimum transmission (light loss accumulates)
        min_transmission = min(min_transmission, gel.transmission)

    # Average softness
    avg_softness = total_softness / len(gel_names)

    # Build combined name
    combined_name = "+".join(gel_names)

    return GelConfig(
        name=combined_name,
        color=(combined_color[0], combined_color[1], combined_color[2]),
        temperature_shift=combined_temp_shift,
        softness=avg_softness,
        transmission=min_transmission,
        combines=gel_names,
    )


def list_gel_presets() -> List[str]:
    """
    List all available gel preset names.

    Returns:
        Sorted list of gel preset names

    Raises:
        FileNotFoundError: If gel_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    from .preset_loader import list_gel_presets as _list_gel_presets
    return _list_gel_presets()
