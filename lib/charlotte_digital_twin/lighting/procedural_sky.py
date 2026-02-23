"""
Procedural Sky System

Creates realistic procedural sky using Blender's built-in Nishita sky model.
No external HDRI files required.

Features:
- Time-of-day simulation
- Sun position calculator
- Sky color variation
- Cloud layer options
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple
import math

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


class TimeOfDay(Enum):
    """Preset times of day."""
    DAWN = "dawn"              # 6:00 AM
    MORNING = "morning"        # 9:00 AM
    NOON = "noon"              # 12:00 PM
    AFTERNOON = "afternoon"    # 3:00 PM
    GOLDEN_HOUR = "golden"     # 5:30 PM
    SUNSET = "sunset"          # 7:00 PM
    DUSK = "dusk"              # 8:00 PM
    NIGHT = "night"            # 10:00 PM


@dataclass
class SkyConfig:
    """Configuration for procedural sky."""
    # Sun position
    sun_elevation: float = 0.5  # 0-1 (0=horizon, 1=overhead)
    sun_rotation: float = 0.0   # Radians (0=east, pi=west)

    # Sun properties
    sun_strength: float = 3.5
    sun_color: Tuple[float, float, float] = (1.0, 0.95, 0.9)

    # Sky properties
    sky_turbidity: float = 2.0  # Atmosphere clarity (1-10)
    sky_ground_albedo: float = 0.3  # Ground reflection

    # Atmosphere
    atmosphere_strength: float = 1.0

    # Sun disc
    sun_disc: bool = True
    sun_size: float = 0.01
    sun_intensity: float = 1.0


# Time of day presets (Charlotte, NC latitude ~35°N)
TIME_PRESETS = {
    TimeOfDay.DAWN: {
        "hour": 6,
        "sun_elevation": 0.1,
        "sun_strength": 1.0,
        "sun_color": (1.0, 0.7, 0.5),
    },
    TimeOfDay.MORNING: {
        "hour": 9,
        "sun_elevation": 0.4,
        "sun_strength": 2.5,
        "sun_color": (1.0, 0.9, 0.8),
    },
    TimeOfDay.NOON: {
        "hour": 12,
        "sun_elevation": 0.85,
        "sun_strength": 4.0,
        "sun_color": (1.0, 1.0, 0.95),
    },
    TimeOfDay.AFTERNOON: {
        "hour": 15,
        "sun_elevation": 0.6,
        "sun_strength": 3.5,
        "sun_color": (1.0, 0.95, 0.9),
    },
    TimeOfDay.GOLDEN_HOUR: {
        "hour": 17.5,
        "sun_elevation": 0.25,
        "sun_strength": 2.0,
        "sun_color": (1.0, 0.7, 0.4),
    },
    TimeOfDay.SUNSET: {
        "hour": 19,
        "sun_elevation": 0.05,
        "sun_strength": 1.5,
        "sun_color": (1.0, 0.5, 0.3),
    },
    TimeOfDay.DUSK: {
        "hour": 20,
        "sun_elevation": 0.0,
        "sun_strength": 0.5,
        "sun_color": (0.5, 0.4, 0.6),
    },
    TimeOfDay.NIGHT: {
        "hour": 22,
        "sun_elevation": -0.2,
        "sun_strength": 0.1,
        "sun_color": (0.2, 0.2, 0.4),
    },
}


class ProceduralSky:
    """
    Creates procedural sky using Blender's Nishita sky model.

    The Nishita model provides physically accurate atmospheric scattering
    for realistic daylight simulation.
    """

    # Charlotte, NC coordinates
    DEFAULT_LATITUDE = 35.227
    DEFAULT_LONGITUDE = -80.843

    def __init__(
        self,
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
    ):
        """
        Initialize procedural sky.

        Args:
            latitude: Location latitude (for sun calculation)
            longitude: Location longitude
        """
        self.latitude = latitude
        self.longitude = longitude
        self._config = SkyConfig()
        self._world = None

    def setup(self, config: Optional[SkyConfig] = None) -> bool:
        """
        Setup the procedural sky.

        Args:
            config: Sky configuration

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        self._config = config or SkyConfig()

        # Get or create world
        if bpy.context.scene.world:
            self._world = bpy.context.scene.world
        else:
            self._world = bpy.data.worlds.new("Procedural_Sky")
            bpy.context.scene.world = self._world

        if not self._world.use_nodes:
            self._world.use_nodes = True

        nodes = self._world.node_tree.nodes
        links = self._world.node_tree.links
        nodes.clear()

        # Sky texture node (Nishita model)
        sky_tex = nodes.new("ShaderNodeTexSky")
        sky_tex.location = (-600, 0)
        sky_tex.sky_type = "NISHITA"

        # Configure sky
        sky_tex.sun_elevation = self._config.sun_elevation * math.pi / 2
        sky_tex.sun_rotation = self._config.sun_rotation
        sky_tex.air_density = self._config.sky_turbidity
        sky_tex.dust_density = self._config.sky_turbidity * 0.5
        sky_tex.ozone_density = 1.0

        # Sun disc
        if hasattr(sky_tex, "sun_disc"):
            sky_tex.sun_disc = self._config.sun_disc
        if hasattr(sky_tex, "sun_size"):
            sky_tex.sun_size = self._config.sun_size
        if hasattr(sky_tex, "sun_intensity"):
            sky_tex.sun_intensity = self._config.sun_intensity

        # Background
        bg = nodes.new("ShaderNodeBackground")
        bg.location = (-200, 0)
        bg.inputs["Strength"].default_value = 1.0

        links.new(sky_tex.outputs["Color"], bg.inputs["Color"])

        # Output
        output = nodes.new("ShaderNodeOutputWorld")
        output.location = (0, 0)

        links.new(bg.outputs["Background"], output.inputs["Surface"])

        # Add sun light
        self._add_sun_light()

        return True

    def set_time_of_day(self, hour: float, minute: float = 0) -> bool:
        """
        Set sky based on time of day.

        Args:
            hour: Hour (0-24)
            minute: Minute (0-59)

        Returns:
            True if successful
        """
        # Calculate sun position based on time
        # Simplified: assume sun rises at 6, sets at 20
        # Peak at noon (12)

        time_decimal = hour + minute / 60

        # Sun elevation (simplified model)
        # Peak at noon (elevation = 1), zero at dawn/dusk
        if 6 <= time_decimal <= 20:
            # Daytime
            normalized_time = (time_decimal - 6) / 14  # 0 to 1 over daylight hours
            # Peak at noon (normalized_time = 6/14 = 0.43)
            elevation = math.sin(normalized_time * math.pi) * 0.9
        else:
            # Night
            elevation = -0.1

        # Sun rotation (east to west)
        # East (morning) = 0, West (evening) = pi
        if 6 <= time_decimal <= 20:
            rotation = ((time_decimal - 6) / 14) * math.pi
        else:
            rotation = 0

        # Update config
        self._config.sun_elevation = max(0, elevation)
        self._config.sun_rotation = rotation

        # Update sun strength based on elevation
        if elevation > 0.7:
            self._config.sun_strength = 4.0
            self._config.sun_color = (1.0, 1.0, 0.95)
        elif elevation > 0.4:
            self._config.sun_strength = 3.0
            self._config.sun_color = (1.0, 0.95, 0.9)
        elif elevation > 0.15:
            self._config.sun_strength = 2.0
            self._config.sun_color = (1.0, 0.85, 0.7)
        elif elevation > 0:
            self._config.sun_strength = 1.0
            self._config.sun_color = (1.0, 0.6, 0.4)
        else:
            self._config.sun_strength = 0.1
            self._config.sun_color = (0.2, 0.2, 0.4)

        return self.setup(self._config)

    def set_preset_time(self, time_of_day: TimeOfDay) -> bool:
        """
        Set sky using a preset time.

        Args:
            time_of_day: Preset to use

        Returns:
            True if successful
        """
        preset = TIME_PRESETS.get(time_of_day, TIME_PRESETS[TimeOfDay.NOON])

        self._config.sun_elevation = preset["sun_elevation"]
        self._config.sun_strength = preset["sun_strength"]
        self._config.sun_color = preset["sun_color"]

        return self.setup(self._config)

    def _add_sun_light(self) -> bool:
        """Add or update sun light in scene."""
        if not BLENDER_AVAILABLE:
            return False

        sun_name = "Procedural_Sun"

        # Check if sun exists
        if sun_name in bpy.data.objects:
            sun_obj = bpy.data.objects[sun_name]
        else:
            sun_data = bpy.data.lights.new(sun_name, type="SUN")
            sun_obj = bpy.data.objects.new(sun_name, sun_data)
            bpy.context.collection.objects.link(sun_obj)

        sun_data = sun_obj.data

        # Set sun properties
        sun_data.energy = self._config.sun_strength
        sun_data.color = self._config.sun_color

        # Set direction based on elevation and rotation
        elevation = self._config.sun_elevation * math.pi / 2
        rotation = self._config.sun_rotation

        # Convert to euler rotation
        # Blender sun points down -Z, we want it pointing toward the ground
        # from the direction specified by elevation and rotation
        sun_obj.rotation_euler = (
            math.pi / 2 - elevation,
            0,
            rotation
        )

        # Shadow settings
        sun_data.shadow_soft_size = 0.1
        if hasattr(sun_data, "use_contact_shadow"):
            sun_data.use_contact_shadow = True

        return True


def create_sky_for_time(
    hour: float,
    minute: float = 0,
    latitude: float = 35.227,
    longitude: float = -80.843,
) -> bool:
    """
    Convenience function to create sky for a specific time.

    Args:
        hour: Hour (0-24)
        minute: Minute (0-59)
        latitude: Location latitude
        longitude: Location longitude

    Returns:
        True if successful
    """
    sky = ProceduralSky(latitude, longitude)
    return sky.set_time_of_day(hour, minute)


__all__ = [
    "TimeOfDay",
    "SkyConfig",
    "TIME_PRESETS",
    "ProceduralSky",
    "create_sky_for_time",
]
