"""
Time of Day System

Dynamic lighting and environment based on time:
- Sun position calculation
- Sky color transitions
- Shadow animation
- Ambient light changes

Supports animated day/night cycle for cinematic sequences.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
from datetime import datetime, time

try:
    import bpy
    from bpy.types import Object, Sun, Light, World
    from mathutils import Vector, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Sun = Any
    Light = Any
    World = Any


class TimeOfDay(Enum):
    """Preset times of day."""
    DAWN = "dawn"               # 6:00 AM
    MORNING = "morning"         # 8:00 AM
    MIDDAY = "midday"           # 12:00 PM
    AFTERNOON = "afternoon"     # 3:00 PM
    GOLDEN_HOUR = "golden_hour" # 5:00 PM
    SUNSET = "sunset"           # 7:00 PM
    DUSK = "dusk"               # 8:00 PM
    NIGHT = "night"             # 10:00 PM


@dataclass
class SunPosition:
    """Calculated sun position."""
    azimuth: float  # Horizontal angle (degrees)
    elevation: float  # Vertical angle (degrees)
    intensity: float  # Light intensity
    color: Tuple[float, float, float]  # RGB color


@dataclass
class TimeConfig:
    """Configuration for time of day."""
    # Location (Charlotte, NC)
    latitude: float = 35.2271
    longitude: float = -80.8431
    timezone: int = -5  # EST

    # Date
    month: int = 6  # June (summer)
    day: int = 21   # Summer solstice

    # Animation
    frame_start: int = 1
    frame_end: int = 250
    fps: float = 24.0

    # Speed multiplier (1 = real time, 60 = 1 min = 1 hour)
    time_speed: float = 60.0


# Time presets with sun data
TIME_PRESETS = {
    TimeOfDay.DAWN: {
        "hour": 6,
        "sun_elevation": 5,
        "sun_intensity": 0.3,
        "sun_color": (1.0, 0.7, 0.5),
        "sky_color": (0.4, 0.5, 0.7),
        "ambient": 0.2,
    },
    TimeOfDay.MORNING: {
        "hour": 8,
        "sun_elevation": 25,
        "sun_intensity": 0.6,
        "sun_color": (1.0, 0.9, 0.8),
        "sky_color": (0.5, 0.65, 0.9),
        "ambient": 0.3,
    },
    TimeOfDay.MIDDAY: {
        "hour": 12,
        "sun_elevation": 75,
        "sun_intensity": 1.0,
        "sun_color": (1.0, 1.0, 0.95),
        "sky_color": (0.4, 0.6, 0.9),
        "ambient": 0.4,
    },
    TimeOfDay.AFTERNOON: {
        "hour": 15,
        "sun_elevation": 50,
        "sun_intensity": 0.9,
        "sun_color": (1.0, 0.95, 0.85),
        "sky_color": (0.45, 0.6, 0.85),
        "ambient": 0.35,
    },
    TimeOfDay.GOLDEN_HOUR: {
        "hour": 17,
        "sun_elevation": 15,
        "sun_intensity": 0.7,
        "sun_color": (1.0, 0.75, 0.4),
        "sky_color": (0.6, 0.5, 0.7),
        "ambient": 0.25,
    },
    TimeOfDay.SUNSET: {
        "hour": 19,
        "sun_elevation": 2,
        "sun_intensity": 0.4,
        "sun_color": (1.0, 0.5, 0.3),
        "sky_color": (0.7, 0.4, 0.5),
        "ambient": 0.15,
    },
    TimeOfDay.DUSK: {
        "hour": 20,
        "sun_elevation": -5,
        "sun_intensity": 0.1,
        "sun_color": (0.5, 0.4, 0.6),
        "sky_color": (0.2, 0.2, 0.4),
        "ambient": 0.08,
    },
    TimeOfDay.NIGHT: {
        "hour": 22,
        "sun_elevation": -30,
        "sun_intensity": 0.0,
        "sun_color": (0.2, 0.2, 0.3),
        "sky_color": (0.05, 0.05, 0.1),
        "ambient": 0.02,
    },
}


class TimeOfDaySystem:
    """
    Manages time-based lighting and environment.

    Calculates realistic sun positions and sky colors
    for any time of day.
    """

    def __init__(self):
        """Initialize time of day system."""
        self._sun_obj: Optional[Object] = None
        self._world: Optional[World] = None

    def setup_sun(self, name: str = "Sun") -> Optional[Object]:
        """
        Create or get sun light object.

        Args:
            name: Sun object name

        Returns:
            Sun light object
        """
        if not BLENDER_AVAILABLE:
            return None

        # Check if sun exists
        for obj in bpy.context.scene.objects:
            if obj.type == "LIGHT" and obj.data.type == "SUN":
                self._sun_obj = obj
                return obj

        # Create new sun
        light_data = bpy.data.lights.new(name, type='SUN')
        light_data.energy = 5.0
        light_data.shadow_soft_size = 0.1

        sun_obj = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(sun_obj)

        self._sun_obj = sun_obj
        return sun_obj

    def set_time(
        self,
        time_of_day: TimeOfDay,
        animate: bool = False,
        frame: int = 1,
    ) -> bool:
        """
        Set scene to specific time of day.

        Args:
            time_of_day: Preset time
            animate: Insert keyframes
            frame: Frame number for keyframe

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        preset = TIME_PRESETS.get(time_of_day)
        if preset is None:
            return False

        sun = self.setup_sun()
        if sun is None:
            return False

        # Set sun rotation
        azimuth = preset["hour"] * 15 - 90  # Approximate azimuth
        elevation = preset["sun_elevation"]

        # Convert to euler angles
        sun.rotation_euler = Euler((
            math.radians(90 - elevation),
            0,
            math.radians(azimuth),
        ), 'XYZ')

        # Set sun properties
        sun.data.energy = preset["sun_intensity"] * 5.0
        sun.data.color = preset["sun_color"]

        if animate:
            sun.keyframe_insert("rotation_euler", frame=frame)
            sun.data.keyframe_insert("energy", frame=frame)
            sun.data.keyframe_insert("color", frame=frame)

        # Update world/sky
        self._update_sky(preset, animate, frame)

        return True

    def animate_day_cycle(
        self,
        config: Optional[TimeConfig] = None,
        start_time: TimeOfDay = TimeOfDay.MORNING,
        end_time: TimeOfDay = TimeOfDay.SUNSET,
    ) -> bool:
        """
        Animate a full day cycle.

        Args:
            config: Time configuration
            start_time: Starting time
            end_time: Ending time

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        config = config or TimeConfig()

        # Get hour range
        start_hour = TIME_PRESETS[start_time]["hour"]
        end_hour = TIME_PRESETS[end_time]["hour"]

        if end_hour < start_hour:
            end_hour += 24

        # Calculate keyframe intervals
        total_hours = end_hour - start_hour
        frames_per_hour = (config.frame_end - config.frame_start) / total_hours

        # Set up intermediate keyframes
        times = list(TIME_PRESETS.keys())

        for time_preset in times:
            preset = TIME_PRESETS[time_preset]
            hour = preset["hour"]

            # Handle overnight
            if hour < start_hour:
                hour += 24

            if start_hour <= hour <= end_hour:
                frame = config.frame_start + int((hour - start_hour) * frames_per_hour)
                self.set_time(time_preset, animate=True, frame=frame)

        return True

    def calculate_sun_position(
        self,
        hour: float,
        latitude: float = 35.2271,
        day_of_year: int = 172,  # June 21
    ) -> SunPosition:
        """
        Calculate realistic sun position.

        Args:
            hour: Hour of day (0-24)
            latitude: Location latitude
            day_of_year: Day of year (1-365)

        Returns:
            SunPosition with azimuth, elevation, intensity, color
        """
        # Solar declination
        declination = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))

        # Hour angle
        hour_angle = 15 * (hour - 12)  # 15 degrees per hour

        # Calculate elevation
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        hour_rad = math.radians(hour_angle)

        elevation = math.degrees(math.asin(
            math.sin(lat_rad) * math.sin(dec_rad) +
            math.cos(lat_rad) * math.cos(dec_rad) * math.cos(hour_rad)
        ))

        # Calculate azimuth
        azimuth = math.degrees(math.atan2(
            math.sin(hour_rad),
            math.cos(hour_rad) * math.sin(lat_rad) - math.tan(dec_rad) * math.cos(lat_rad)
        ))

        # Normalize azimuth
        azimuth = (azimuth + 180) % 360

        # Calculate intensity based on elevation
        if elevation > 0:
            intensity = min(1.0, elevation / 90 * 1.2)
        else:
            intensity = 0.0

        # Calculate color based on elevation
        if elevation > 30:
            color = (1.0, 1.0, 0.95)  # White/yellow
        elif elevation > 10:
            t = (elevation - 10) / 20
            color = (
                1.0,
                0.75 + t * 0.2,
                0.4 + t * 0.55,
            )
        elif elevation > 0:
            t = elevation / 10
            color = (
                1.0,
                0.5 + t * 0.25,
                0.3 + t * 0.1,
            )
        else:
            color = (0.3, 0.3, 0.4)  # Night

        return SunPosition(
            azimuth=azimuth,
            elevation=elevation,
            intensity=intensity,
            color=color,
        )

    def _update_sky(
        self,
        preset: Dict[str, Any],
        animate: bool = False,
        frame: int = 1,
    ) -> None:
        """Update world sky settings."""
        if not BLENDER_AVAILABLE:
            return

        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world

        world.use_nodes = True

        # Find background node
        bg_node = None
        for node in world.node_tree.nodes:
            if node.type == "BACKGROUND":
                bg_node = node
                break

        if bg_node is None:
            bg_node = world.node_tree.nodes.new("ShaderNodeBackground")

        # Set sky color
        bg_node.inputs["Color"].default_value = (*preset["sky_color"], 1.0)
        bg_node.inputs["Strength"].default_value = preset["ambient"] + 0.3

        if animate:
            bg_node.inputs["Color"].keyframe_insert("default_value", frame=frame)
            bg_node.inputs["Strength"].keyframe_insert("default_value", frame=frame)


def set_scene_time(
    time_of_day: TimeOfDay = TimeOfDay.AFTERNOON,
    animate: bool = False,
    frame: int = 1,
) -> bool:
    """
    Quick function to set scene time.

    Args:
        time_of_day: Preset time
        animate: Insert keyframe
        frame: Frame number

    Returns:
        True if successful
    """
    system = TimeOfDaySystem()
    return system.set_time(time_of_day, animate, frame)


def animate_sun_movement(
    start_hour: float = 8.0,
    end_hour: float = 18.0,
    frame_start: int = 1,
    frame_end: int = 250,
) -> bool:
    """
    Animate sun movement across the sky.

    Args:
        start_hour: Starting hour (24h)
        end_hour: Ending hour (24h)
        frame_start: Start frame
        frame_end: End frame

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    system = TimeOfDaySystem()
    config = TimeConfig(frame_start=frame_start, frame_end=frame_end)

    sun = system.setup_sun()
    if sun is None:
        return False

    total_frames = frame_end - frame_start
    total_hours = end_hour - start_hour
    frames_per_hour = total_frames / total_hours

    # Keyframe every hour
    for hour in range(int(start_hour), int(end_hour) + 1):
        frame = frame_start + int((hour - start_hour) * frames_per_hour)
        pos = system.calculate_sun_position(hour)

        sun.rotation_euler = Euler((
            math.radians(90 - pos.elevation),
            0,
            math.radians(pos.azimuth),
        ), 'XYZ')
        sun.data.energy = pos.intensity * 5.0
        sun.data.color = pos.color

        sun.keyframe_insert("rotation_euler", frame=frame)
        sun.data.keyframe_insert("energy", frame=frame)
        sun.data.keyframe_insert("color", frame=frame)

    return True


__all__ = [
    "TimeOfDay",
    "SunPosition",
    "TimeConfig",
    "TIME_PRESETS",
    "TimeOfDaySystem",
    "set_scene_time",
    "animate_sun_movement",
]
