"""
Weather Effects System

Dynamic weather effects for scenes:
- Rain particles and splashes
- Wet road materials
- Puddle generation
- Mist and fog
- Cloud cover

Designed for cinematic weather transitions.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection, Material, ParticleSettings
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any
    Material = Any
    ParticleSettings = Any


class WeatherType(Enum):
    """Types of weather conditions."""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    FOG = "fog"
    MIST = "mist"


@dataclass
class RainConfig:
    """Configuration for rain effect."""
    # Intensity (0-1)
    intensity: float = 0.5

    # Particle settings
    drop_count: int = 10000
    drop_size: float = 0.02
    drop_speed: float = 15.0  # m/s

    # Drop appearance
    drop_length: float = 0.3
    drop_color: Tuple[float, float, float] = (0.7, 0.75, 0.8)
    drop_alpha: float = 0.6

    # Splash
    splash_enabled: bool = True
    splash_size: float = 0.05
    splash_lifetime: float = 0.1


@dataclass
class WetSurfaceConfig:
    """Configuration for wet surfaces."""
    # Puddles
    puddle_depth: float = 0.01
    puddle_coverage: float = 0.3  # 0-1

    # Wet material properties
    wetness: float = 0.5  # 0-1
    roughness_reduction: float = 0.4  # How much roughness decreases
    reflection_increase: float = 0.3  # How much reflectivity increases

    # Water color
    water_color: Tuple[float, float, float] = (0.3, 0.35, 0.4)


@dataclass
class WeatherConfig:
    """Complete weather configuration."""
    weather_type: WeatherType = WeatherType.CLEAR
    rain: Optional[RainConfig] = None
    wet_surface: Optional[WetSurfaceConfig] = None

    # Cloud coverage (0-1)
    cloud_coverage: float = 0.0

    # Fog
    fog_density: float = 0.0
    fog_start: float = 100.0
    fog_color: Tuple[float, float, float] = (0.7, 0.7, 0.75)


# Weather presets
WEATHER_PRESETS = {
    WeatherType.CLEAR: WeatherConfig(
        weather_type=WeatherType.CLEAR,
        cloud_coverage=0.0,
        fog_density=0.0,
    ),
    WeatherType.PARTLY_CLOUDY: WeatherConfig(
        weather_type=WeatherType.PARTLY_CLOUDY,
        cloud_coverage=0.4,
        fog_density=0.0001,
    ),
    WeatherType.OVERCAST: WeatherConfig(
        weather_type=WeatherType.OVERCAST,
        cloud_coverage=0.9,
        fog_density=0.0003,
        wet_surface=WetSurfaceConfig(wetness=0.2),
    ),
    WeatherType.LIGHT_RAIN: WeatherConfig(
        weather_type=WeatherType.LIGHT_RAIN,
        cloud_coverage=0.95,
        fog_density=0.0005,
        rain=RainConfig(
            intensity=0.3,
            drop_count=3000,
            drop_speed=12.0,
        ),
        wet_surface=WetSurfaceConfig(
            wetness=0.5,
            puddle_coverage=0.2,
        ),
    ),
    WeatherType.HEAVY_RAIN: WeatherConfig(
        weather_type=WeatherType.HEAVY_RAIN,
        cloud_coverage=1.0,
        fog_density=0.001,
        rain=RainConfig(
            intensity=0.8,
            drop_count=15000,
            drop_speed=18.0,
        ),
        wet_surface=WetSurfaceConfig(
            wetness=0.9,
            puddle_coverage=0.5,
        ),
    ),
    WeatherType.THUNDERSTORM: WeatherConfig(
        weather_type=WeatherType.THUNDERSTORM,
        cloud_coverage=1.0,
        fog_density=0.002,
        rain=RainConfig(
            intensity=1.0,
            drop_count=25000,
            drop_speed=20.0,
        ),
        wet_surface=WetSurfaceConfig(
            wetness=1.0,
            puddle_coverage=0.7,
        ),
    ),
    WeatherType.FOG: WeatherConfig(
        weather_type=WeatherType.FOG,
        cloud_coverage=1.0,
        fog_density=0.01,
        fog_start=20.0,
    ),
    WeatherType.MIST: WeatherConfig(
        weather_type=WeatherType.MIST,
        cloud_coverage=0.7,
        fog_density=0.003,
        fog_start=50.0,
    ),
}


class WeatherSystem:
    """
    Creates and manages weather effects.

    Handles rain, wet surfaces, fog, and atmospheric
    conditions for realistic weather simulation.
    """

    def __init__(self):
        """Initialize weather system."""
        self._rain_particles: Optional[Object] = None
        self._material_cache: Dict[str, Material] = {}

    def apply_weather(
        self,
        weather_type: WeatherType = WeatherType.CLEAR,
        config: Optional[WeatherConfig] = None,
        target_area: Tuple[float, float, float] = (100.0, 100.0, 50.0),
    ) -> bool:
        """
        Apply weather effects to scene.

        Args:
            weather_type: Type of weather
            config: Custom weather configuration
            target_area: (width, depth, height) for effects

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        config = config or WEATHER_PRESETS.get(weather_type, WeatherConfig())

        # Apply fog
        self._apply_fog(config)

        # Apply rain if configured
        if config.rain and config.rain.intensity > 0:
            self._create_rain(config.rain, target_area)

        # Store config for material updates
        self._current_config = config

        return True

    def create_wet_road_material(
        self,
        base_material: Optional[Material] = None,
        config: Optional[WetSurfaceConfig] = None,
        name: str = "Wet_Road",
    ) -> Optional[Material]:
        """
        Create wet road material.

        Args:
            base_material: Original road material to modify
            config: Wet surface configuration
            name: Material name

        Returns:
            Wet road material
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or WetSurfaceConfig()

        mat = bpy.data.materials.new(name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Mix shader between dry and wet
        mix = nodes.new("ShaderNodeMixShader")
        mix.location = (400, 0)
        mix.inputs["Fac"].default_value = config.wetness

        # Dry asphalt
        dry_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        dry_bsdf.location = (100, 200)
        dry_bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
        dry_bsdf.inputs["Roughness"].default_value = 0.8

        # Wet asphalt (more reflective)
        wet_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        wet_bsdf.location = (100, -200)
        wet_bsdf.inputs["Base Color"].default_value = (*config.water_color, 1.0)
        wet_bsdf.inputs["Roughness"].default_value = 0.2
        wet_bsdf.inputs["Metallic"].default_value = 0.1

        # Add gloss
        gloss = nodes.new("ShaderNodeBsdfGlossy")
        gloss.location = (100, -400)
        gloss.inputs["Color"].default_value = (0.5, 0.5, 0.55, 1.0)
        gloss.inputs["Roughness"].default_value = 0.1

        wet_mix = nodes.new("ShaderNodeMixShader")
        wet_mix.location = (250, -300)
        wet_mix.inputs["Fac"].default_value = 0.5

        links.new(dry_bsdf.outputs["BSDF"], mix.inputs[1])
        links.new(wet_bsdf.outputs["BSDF"], wet_mix.inputs[1])
        links.new(gloss.outputs["BSDF"], wet_mix.inputs[2])
        links.new(wet_mix.outputs["Shader"], mix.inputs[2])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (600, 0)

        links.new(mix.outputs["Shader"], output.inputs["Surface"])

        return mat

    def create_puddles(
        self,
        surface_obj: Object,
        config: Optional[WetSurfaceConfig] = None,
        collection: Optional[Collection] = None,
    ) -> List[Object]:
        """
        Create puddles on a surface.

        Args:
            surface_obj: Surface to add puddles to
            config: Wet surface configuration
            collection: Collection for puddle objects

        Returns:
            List of puddle objects
        """
        if not BLENDER_AVAILABLE or surface_obj is None:
            return []

        config = config or WetSurfaceConfig()
        puddles = []

        # Get surface bounds
        bbox = [surface_obj.matrix_world @ Vector(corner) for corner in surface_obj.bound_box]
        min_x = min(v.x for v in bbox)
        max_x = max(v.x for v in bbox)
        min_y = min(v.y for v in bbox)
        max_y = max(v.y for v in bbox)
        z = max(v.z for v in bbox) + 0.001

        # Calculate number of puddles based on coverage
        area = (max_x - min_x) * (max_y - min_y)
        num_puddles = int(area * config.puddle_coverage / 5)  # Rough estimate

        for i in range(num_puddles):
            # Random position within bounds
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)

            # Random puddle size
            size = random.uniform(0.5, 3.0)

            # Create puddle mesh
            puddle = self._create_single_puddle(
                (x, y, z),
                size,
                config.puddle_depth,
                f"Puddle_{i}",
            )

            if puddle:
                if collection:
                    collection.objects.link(puddle)
                puddles.append(puddle)

        return puddles

    def _create_single_puddle(
        self,
        position: Tuple[float, float, float],
        size: float,
        depth: float,
        name: str,
    ) -> Optional[Object]:
        """Create a single puddle mesh."""
        if not BLENDER_AVAILABLE:
            return None

        # Create flat disc
        bpy.ops.mesh.primitive_circle_add(
            radius=size,
            fill_type='NGON',
            location=position,
        )
        puddle = bpy.context.active_object
        puddle.name = name

        # Apply water material
        mat = self._get_puddle_material()
        if mat:
            puddle.data.materials.append(mat)

        return puddle

    def _create_rain(
        self,
        config: RainConfig,
        target_area: Tuple[float, float, float],
    ) -> Optional[Object]:
        """Create rain particle system."""
        if not BLENDER_AVAILABLE:
            return None

        # Create emitter plane
        bpy.ops.mesh.primitive_plane_add(
            size=1.0,
            location=(0, 0, target_area[2]),
        )
        emitter = bpy.context.active_object
        emitter.name = "Rain_Emitter"
        emitter.scale = (target_area[0], target_area[1], 1.0)

        # Add particle system
        ps_mod = emitter.modifiers.new("Rain", type='PARTICLE_SYSTEM')
        ps = ps_mod.particle_system

        settings = ps.settings
        settings.type = 'EMITTER'
        settings.emit_from = 'FACE'
        settings.count = config.drop_count

        # Lifetime and speed
        settings.lifetime = int(target_area[2] / config.drop_speed * 24)  # Frames
        settings.normal_factor = -config.drop_speed

        # Size
        settings.particle_size = config.drop_size
        settings.size_random = 0.5

        # Rendering
        settings.render_type = 'LINE'
        settings.line_length_head = config.drop_length
        settings.line_length_tail = 0.0

        # Material
        mat = self._get_rain_material(config)
        if mat:
            emitter.data.materials.append(mat)

        self._rain_particles = emitter
        return emitter

    def _apply_fog(self, config: WeatherConfig) -> None:
        """Apply fog to world settings."""
        if not BLENDER_AVAILABLE:
            return

        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world

        world.use_nodes = True

        # Find or create volume
        volume_node = None
        for node in world.node_tree.nodes:
            if node.type == "PRINCIPLED_VOLUME":
                volume_node = node
                break

        if config.fog_density > 0:
            if volume_node is None:
                output = world.node_tree.nodes.get("Output")
                if output is None:
                    output = world.node_tree.nodes.new("ShaderNodeOutputWorld")

                volume_node = world.node_tree.nodes.new("ShaderNodeVolumePrincipled")
                world.node_tree.links.new(volume_node.outputs["Volume"], output.inputs["Volume"])

            volume_node.inputs["Density"].default_value = config.fog_density
            volume_node.inputs["Color"].default_value = (*config.fog_color, 1.0)

        elif volume_node:
            volume_node.inputs["Density"].default_value = 0.0

    def _get_rain_material(self, config: RainConfig) -> Optional[Material]:
        """Get or create rain material."""
        if not BLENDER_AVAILABLE:
            return None

        if "rain" in self._material_cache:
            return self._material_cache["rain"]

        mat = bpy.data.materials.new("Rain_Drops")
        mat.use_nodes = True

        # Simple transparent material
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*config.drop_color, config.drop_alpha)
            bsdf.inputs["Alpha"].default_value = config.drop_alpha
            bsdf.inputs["Roughness"].default_value = 0.1

        mat.blend_method = "BLEND"

        self._material_cache["rain"] = mat
        return mat

    def _get_puddle_material(self) -> Optional[Material]:
        """Get or create puddle water material."""
        if not BLENDER_AVAILABLE:
            return None

        if "puddle" in self._material_cache:
            return self._material_cache["puddle"]

        mat = bpy.data.materials.new("Puddle_Water")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Glass-like material
        glass = nodes.new("ShaderNodeBsdfGlass")
        glass.inputs["Color"].default_value = (0.3, 0.35, 0.4, 1.0)
        glass.inputs["Roughness"].default_value = 0.05
        glass.inputs["IOR"].default_value = 1.33

        output = nodes.new("ShaderNodeOutputMaterial")
        links.new(glass.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache["puddle"] = mat
        return mat


def apply_rain_to_scene(
    intensity: float = 0.5,
    target_area: Tuple[float, float, float] = (100.0, 100.0, 50.0),
) -> Optional[Object]:
    """
    Quick function to add rain to scene.

    Args:
        intensity: Rain intensity (0-1)
        target_area: Area for rain effect

    Returns:
        Rain emitter object
    """
    system = WeatherSystem()

    # Map intensity to weather type
    if intensity < 0.3:
        weather = WeatherType.LIGHT_RAIN
    elif intensity < 0.7:
        weather = WeatherType.HEAVY_RAIN
    else:
        weather = WeatherType.THUNDERSTORM

    config = WEATHER_PRESETS[weather]

    if config.rain:
        config.rain.intensity = intensity
        config.rain.drop_count = int(intensity * 20000)

    system.apply_weather(weather, config, target_area)

    return system._rain_particles


def create_wet_road(
    road_obj: Object,
    wetness: float = 0.5,
    puddles: bool = True,
) -> Optional[Material]:
    """
    Apply wet road effect to a road object.

    Args:
        road_obj: Road mesh object
        wetness: How wet (0-1)
        puddles: Add puddles

    Returns:
        Wet road material
    """
    if not BLENDER_AVAILABLE or road_obj is None:
        return None

    system = WeatherSystem()
    config = WetSurfaceConfig(wetness=wetness)

    mat = system.create_wet_road_material(config=config)

    if mat and road_obj.data.materials:
        road_obj.data.materials[0] = mat
    elif mat:
        road_obj.data.materials.append(mat)

    if puddles:
        system.create_puddles(road_obj, config)

    return mat


__all__ = [
    "WeatherType",
    "RainConfig",
    "WetSurfaceConfig",
    "WeatherConfig",
    "WEATHER_PRESETS",
    "WeatherSystem",
    "apply_rain_to_scene",
    "create_wet_road",
]
