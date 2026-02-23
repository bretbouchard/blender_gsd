"""
HDRI Environment Setup

Loads and configures HDRI sky environments for realistic outdoor lighting.
Supports both file-based HDRI and procedural sky fallback.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import os

try:
    import bpy
    from bpy.types import World, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    World = Any
    ShaderNodeTree = Any


class HDRIPreset(Enum):
    """Built-in HDRI presets for different conditions."""
    SUNNY_AFTERNOON = "sunny_afternoon"
    SUNNY_MORNING = "sunny_morning"
    GOLDEN_HOUR = "golden_hour"
    OVERCAST = "overcast"
    CLOUDY = "cloudy"
    BLUE_SKY = "blue_sky"
    SUNSET = "sunset"
    NIGHT = "night"


@dataclass
class HDRIConfig:
    """Configuration for HDRI environment."""
    # HDRI file path
    hdri_path: Optional[str] = None

    # Rotation (to align sun direction)
    rotation_z: float = 0.0  # Radians

    # Strength/exposure
    strength: float = 1.0

    # Color adjustments
    saturation: float = 1.0
    exposure: float = 0.0

    # Sun direction override (if HDRI doesn't have good sun)
    sun_direction: Optional[Tuple[float, float, float]] = None
    sun_strength: float = 3.0
    sun_color: Tuple[float, float, float] = (1.0, 0.95, 0.9)

    # Background visibility
    background_visible: bool = True


# Preset configurations
HDRI_PRESETS = {
    HDRIPreset.SUNNY_AFTERNOON: HDRIConfig(
        strength=1.0,
        rotation_z=0.0,
        sun_direction=(0.5, 0.5, 0.7),
        sun_strength=3.5,
        sun_color=(1.0, 0.95, 0.9),
    ),
    HDRIPreset.SUNNY_MORNING: HDRIConfig(
        strength=0.9,
        rotation_z=0.0,
        sun_direction=(0.3, 0.7, 0.4),
        sun_strength=2.5,
        sun_color=(1.0, 0.9, 0.8),
    ),
    HDRIPreset.GOLDEN_HOUR: HDRIConfig(
        strength=0.8,
        rotation_z=0.0,
        sun_direction=(0.7, 0.5, 0.2),
        sun_strength=2.0,
        sun_color=(1.0, 0.7, 0.5),
    ),
    HDRIPreset.OVERCAST: HDRIConfig(
        strength=1.2,
        rotation_z=0.0,
        sun_direction=None,  # Diffuse light
        sun_strength=1.5,
        sun_color=(0.9, 0.9, 1.0),
    ),
    HDRIPreset.CLOUDY: HDRIConfig(
        strength=1.0,
        rotation_z=0.0,
        sun_direction=(0.5, 0.5, 0.6),
        sun_strength=2.0,
        sun_color=(0.95, 0.95, 1.0),
    ),
    HDRIPreset.BLUE_SKY: HDRIConfig(
        strength=1.1,
        rotation_z=0.0,
        sun_direction=(0.4, 0.4, 0.8),
        sun_strength=4.0,
        sun_color=(1.0, 1.0, 0.95),
    ),
    HDRIPreset.SUNSET: HDRIConfig(
        strength=0.6,
        rotation_z=0.0,
        sun_direction=(0.9, 0.3, 0.1),
        sun_strength=1.5,
        sun_color=(1.0, 0.5, 0.3),
    ),
    HDRIPreset.NIGHT: HDRIConfig(
        strength=0.1,
        rotation_z=0.0,
        sun_direction=None,
        sun_strength=0.1,
        sun_color=(0.3, 0.3, 0.5),
    ),
}


class HDRISetup:
    """
    Sets up HDRI environment lighting in Blender.

    Features:
    - Load HDRI from file
    - Apply presets for different times/conditions
    - Configure sun direction
    - Adjust exposure and rotation
    - Fallback to procedural sky
    """

    # Default search paths for HDRI files
    HDRI_SEARCH_PATHS = [
        "assets/hdri",
        "assets/textures/hdri",
        "~/hdri_library",
        "~/.blender_assets/hdri",
    ]

    def __init__(self):
        """Initialize HDRI setup."""
        self._world: Optional[World] = None
        self._config: Optional[HDRIConfig] = None

    def setup_world(self) -> Optional[World]:
        """Create or get the world setup."""
        if not BLENDER_AVAILABLE:
            return None

        # Get or create world
        if bpy.context.scene.world:
            self._world = bpy.context.scene.world
        else:
            self._world = bpy.data.worlds.new("HDRI_World")
            bpy.context.scene.world = self._world

        # Enable nodes
        if not self._world.use_nodes:
            self._world.use_nodes = True

        return self._world

    def load_from_file(
        self,
        hdri_path: str,
        config: Optional[HDRIConfig] = None,
    ) -> bool:
        """
        Load HDRI from a file path.

        Args:
            hdri_path: Path to .hdr or .exr file
            config: Optional configuration overrides

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        world = self.setup_world()
        if not world:
            return False

        # Expand path
        hdri_path = os.path.expanduser(hdri_path)

        if not os.path.exists(hdri_path):
            print(f"[HDRI] File not found: {hdri_path}")
            return False

        config = config or HDRIConfig(hdri_path=hdri_path)
        config.hdri_path = hdri_path
        self._config = config

        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Clear existing nodes
        nodes.clear()

        # Create texture coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, 0)

        # Mapping for rotation
        mapping = nodes.new("ShaderNodeMapping")
        mapping.location = (-600, 0)
        mapping.inputs["Rotation"].default_value = (0, 0, config.rotation_z)

        links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])

        # Environment texture
        env_tex = nodes.new("ShaderNodeTexEnvironment")
        env_tex.location = (-400, 0)

        # Load HDRI image
        try:
            img = bpy.data.images.load(hdri_path, check_existing=True)
            env_tex.image = img
        except Exception as e:
            print(f"[HDRI] Failed to load image: {e}")
            return False

        links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])

        # Background node
        bg = nodes.new("ShaderNodeBackground")
        bg.location = (-200, 0)
        bg.inputs["Strength"].default_value = config.strength

        links.new(env_tex.outputs["Color"], bg.inputs["Color"])

        # Output
        output = nodes.new("ShaderNodeOutputWorld")
        output.location = (0, 0)

        links.new(bg.outputs["Background"], output.inputs["Surface"])

        # Add sun if specified
        if config.sun_direction:
            self._add_sun_light(config)

        return True

    def load_from_preset(
        self,
        preset: HDRIPreset,
        hdri_path: Optional[str] = None,
    ) -> bool:
        """
        Load HDRI using a preset configuration.

        Args:
            preset: Preset to use
            hdri_path: Optional HDRI file path (will search if not provided)

        Returns:
            True if successful
        """
        config = HDRI_PRESETS.get(preset, HDRIConfig())

        if hdri_path:
            return self.load_from_file(hdri_path, config)

        # Search for HDRI file matching preset
        search_name = self._get_hdri_name_for_preset(preset)
        found_path = self._find_hdri_file(search_name)

        if found_path:
            return self.load_from_file(found_path, config)

        # Fallback to procedural sky
        print(f"[HDRI] No HDRI file found for {preset.value}, using procedural sky")
        return self._setup_procedural_fallback(config)

    def _get_hdri_name_for_preset(self, preset: HDRIPreset) -> str:
        """Get likely HDRI filename for a preset."""
        # Map to our downloaded Poly Haven files
        name_map = {
            HDRIPreset.SUNNY_AFTERNOON: "blue_lagoon",  # Clear sky
            HDRIPreset.SUNNY_MORNING: "autumn_park",    # Warm morning
            HDRIPreset.GOLDEN_HOUR: "autumn_park",      # Warm tones
            HDRIPreset.OVERCAST: "mossy_forest",        # Diffuse cloudy
            HDRIPreset.CLOUDY: "mossy_forest",          # Diffuse cloudy
            HDRIPreset.BLUE_SKY: "blue_lagoon",         # Clear blue
            HDRIPreset.SUNSET: "autumn_park",           # Warm sunset tones
            HDRIPreset.NIGHT: "music_hall",             # Night ambient
        }
        return name_map.get(preset, "blue_lagoon")

    def _find_hdri_file(self, name_pattern: str) -> Optional[str]:
        """Search for HDRI file matching name pattern."""
        for search_path in self.HDRI_SEARCH_PATHS:
            search_path = os.path.expanduser(search_path)

            if not os.path.exists(search_path):
                continue

            # Search for matching files
            for ext in [".hdr", ".exr", ".hdri"]:
                pattern = os.path.join(search_path, f"*{name_pattern}*{ext}")
                import glob
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]

                # Also try without pattern (any HDRI)
                pattern = os.path.join(search_path, f"*{ext}")
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]

        return None

    def _setup_procedural_fallback(self, config: HDRIConfig) -> bool:
        """Setup procedural sky as fallback when no HDRI available."""
        if not BLENDER_AVAILABLE:
            return False

        world = self.setup_world()
        if not world:
            return False

        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()

        # Sky texture node (Nishita model for realistic sky)
        sky_tex = nodes.new("ShaderNodeTexSky")
        sky_tex.location = (-600, 0)
        sky_tex.sky_type = "NISHITA"

        # Configure based on preset
        if config.sun_direction:
            # Convert direction to sun rotation
            # Nishita uses elevation and rotation
            x, y, z = config.sun_direction
            sky_tex.sun_elevation = max(0.1, z * 1.5)  # Elevation
            sky_tex.sun_rotation = math.atan2(y, x) if hasattr(sky_tex, "sun_rotation") else 0

        # Background
        bg = nodes.new("ShaderNodeBackground")
        bg.location = (-200, 0)
        bg.inputs["Strength"].default_value = config.strength

        links.new(sky_tex.outputs["Color"], bg.inputs["Color"])

        # Output
        output = nodes.new("ShaderNodeOutputWorld")
        output.location = (0, 0)

        links.new(bg.outputs["Background"], output.inputs["Surface"])

        # Add sun light
        if config.sun_direction:
            self._add_sun_light(config)

        return True

    def _add_sun_light(self, config: HDRIConfig) -> bool:
        """Add sun light to scene."""
        if not BLENDER_AVAILABLE or not config.sun_direction:
            return False

        # Check if sun already exists
        sun_name = "HDRI_Sun"
        if sun_name in bpy.data.objects:
            sun_obj = bpy.data.objects[sun_name]
        else:
            # Create sun
            sun_data = bpy.data.lights.new(sun_name, type="SUN")
            sun_obj = bpy.data.objects.new(sun_name, sun_data)
            bpy.context.collection.objects.link(sun_obj)

        # Set sun properties
        sun_data = sun_obj.data
        sun_data.energy = config.sun_strength
        sun_data.color = config.sun_color

        # Set direction (sun points toward scene, so we negate)
        x, y, z = config.sun_direction
        # Convert to rotation (pointing from origin toward direction)
        import math
        # Azimuth and elevation
        length = math.sqrt(x * x + y * y + z * z)
        if length > 0:
            x, y, z = x / length, y / length, z / length

        # Convert direction to euler rotation
        # Sun looks down -Z, so we need to rotate it to point at our direction
        azimuth = math.atan2(y, x)
        elevation = math.asin(z)

        sun_obj.rotation_euler = (
            math.pi / 2 - elevation,  # Pitch
            0,
            azimuth + math.pi / 2    # Yaw
        )

        # Enable shadows
        sun_data.shadow_soft_size = 0.1
        if hasattr(sun_data, "use_contact_shadow"):
            sun_data.use_contact_shadow = True

        return True

    def set_rotation(self, rotation_z: float) -> bool:
        """Set HDRI rotation (for sun direction alignment)."""
        if not BLENDER_AVAILABLE:
            return False

        world = bpy.context.scene.world
        if not world or not world.use_nodes:
            return False

        # Find mapping node
        for node in world.node_tree.nodes:
            if node.type == "MAPPING":
                node.inputs["Rotation"].default_value = (0, 0, rotation_z)
                return True

        return False

    def set_strength(self, strength: float) -> bool:
        """Set HDRI strength/exposure."""
        if not BLENDER_AVAILABLE:
            return False

        world = bpy.context.scene.world
        if not world or not world.use_nodes:
            return False

        # Find background node
        for node in world.node_tree.nodes:
            if node.type == "BACKGROUND":
                node.inputs["Strength"].default_value = strength
                return True

        return False


def load_hdri_from_file(
    hdri_path: str,
    strength: float = 1.0,
    rotation: float = 0.0,
) -> bool:
    """
    Convenience function to load HDRI from file.

    Args:
        hdri_path: Path to HDRI file
        strength: Environment strength
        rotation: Z rotation in radians

    Returns:
        True if successful
    """
    config = HDRIConfig(
        hdri_path=hdri_path,
        strength=strength,
        rotation_z=rotation,
    )
    setup = HDRISetup()
    return setup.load_from_file(hdri_path, config)


def load_hdri_from_preset(preset: HDRIPreset) -> bool:
    """
    Convenience function to load HDRI from preset.

    Args:
        preset: Preset to use

    Returns:
        True if successful
    """
    setup = HDRISetup()
    return setup.load_from_preset(preset)


# Import math for rotation calculations
import math


__all__ = [
    "HDRIPreset",
    "HDRIConfig",
    "HDRI_PRESETS",
    "HDRISetup",
    "load_hdri_from_file",
    "load_hdri_from_preset",
]
