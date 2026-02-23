"""
Charlotte Digital Twin Effects System

Time of day and weather effects:
- Dynamic sun positioning
- Day/night cycle animation
- Rain and wet surfaces
- Fog and atmospheric effects

Usage:
    from lib.charlotte_digital_twin.effects import (
        TimeOfDaySystem,
        WeatherSystem,
        set_scene_time,
        apply_rain_to_scene,
    )

    # Set time of day
    set_scene_time(TimeOfDay.GOLDEN_HOUR)

    # Add rain
    apply_rain_to_scene(intensity=0.6)
"""

from .time_of_day import (
    TimeOfDay,
    SunPosition,
    TimeConfig,
    TIME_PRESETS,
    TimeOfDaySystem,
    set_scene_time,
    animate_sun_movement,
)

from .weather_effects import (
    WeatherType,
    RainConfig,
    WetSurfaceConfig,
    WeatherConfig,
    WEATHER_PRESETS,
    WeatherSystem,
    apply_rain_to_scene,
    create_wet_road,
)

__version__ = "1.0.0"
__all__ = [
    # Time of Day
    "TimeOfDay",
    "SunPosition",
    "TimeConfig",
    "TIME_PRESETS",
    "TimeOfDaySystem",
    "set_scene_time",
    "animate_sun_movement",
    # Weather
    "WeatherType",
    "RainConfig",
    "WetSurfaceConfig",
    "WeatherConfig",
    "WEATHER_PRESETS",
    "WeatherSystem",
    "apply_rain_to_scene",
    "create_wet_road",
]
