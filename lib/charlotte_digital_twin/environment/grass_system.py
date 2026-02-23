"""
Grass Ground Cover System

Creates realistic grass coverage:
- Particle system grass
- Multiple blade variations
- Wind animation
- Distance-based density optimization

Designed for large-scale ground cover along highways.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random

try:
    import bpy
    import bmesh
    from bpy.types import Object, Collection, ParticleSettings, ParticleSystem
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Collection = Any
    ParticleSettings = Any
    ParticleSystem = Any


class GrassType(Enum):
    """Types of grass coverage."""
    LAWN = "lawn"                 # Short, manicured
    MEADOW = "meadow"             # Tall, wild
    HIGHWAY_VERGE = "verge"       # Roadside grass
    PASTURE = "pasture"           # Grazed field
    WETLAND = "wetland"           # Marsh grass


@dataclass
class GrassConfig:
    """Configuration for grass particle system."""
    # Blade dimensions (meters)
    blade_length_min: float = 0.15
    blade_length_max: float = 0.35
    blade_width_base: float = 0.005
    blade_segments: int = 4

    # Particle settings
    particle_count: int = 50000
    emission_shape: str = "HEX"  # Distribution pattern

    # Density (particles per square meter)
    density: float = 100.0

    # Color
    base_color: Tuple[float, float, float] = (0.2, 0.45, 0.15)
    tip_color: Tuple[float, float, float] = (0.35, 0.55, 0.2)
    dead_color: Tuple[float, float, float] = (0.45, 0.4, 0.25)

    # Variation
    color_variation: float = 0.15
    length_variation: float = 0.3

    # Physics/Wind
    use_wind: bool = True
    wind_strength: float = 0.5
    wind_direction: Tuple[float, float] = (1.0, 0.0)  # X, Y

    # Clumping
    clump_factor: float = 0.3
    clump_shape: float = 0.5

    # Performance
    child_particles: int = 10  # Children per parent
    use_children: bool = True


# Preset configurations for different grass types
GRASS_CONFIGS = {
    GrassType.LAWN: GrassConfig(
        blade_length_min=0.05,
        blade_length_max=0.12,
        density=200.0,
        base_color=(0.15, 0.5, 0.15),
        tip_color=(0.25, 0.6, 0.2),
        clump_factor=0.1,
    ),
    GrassType.MEADOW: GrassConfig(
        blade_length_min=0.3,
        blade_length_max=0.6,
        density=60.0,
        base_color=(0.25, 0.4, 0.1),
        tip_color=(0.35, 0.5, 0.15),
        color_variation=0.25,
        wind_strength=0.7,
    ),
    GrassType.HIGHWAY_VERGE: GrassConfig(
        blade_length_min=0.1,
        blade_length_max=0.25,
        density=80.0,
        base_color=(0.2, 0.42, 0.12),
        tip_color=(0.28, 0.48, 0.15),
        color_variation=0.2,
        clump_factor=0.2,
    ),
    GrassType.PASTURE: GrassConfig(
        blade_length_min=0.08,
        blade_length_max=0.2,
        density=120.0,
        base_color=(0.22, 0.45, 0.15),
        tip_color=(0.3, 0.5, 0.18),
        clump_factor=0.15,
    ),
    GrassType.WETLAND: GrassConfig(
        blade_length_min=0.4,
        blade_length_max=0.8,
        density=40.0,
        base_color=(0.18, 0.38, 0.12),
        tip_color=(0.25, 0.42, 0.15),
        blade_width_base=0.008,
        color_variation=0.3,
    ),
}


class GrassSystem:
    """
    Creates and manages grass particle systems.

    Generates realistic grass coverage using Blender's
    particle hair system with custom settings.
    """

    def __init__(self):
        """Initialize the grass system."""
        self._material_cache: Dict[str, Any] = {}
        self._blade_cache: Dict[str, Object] = {}

    def create_grass_blade(
        self,
        config: GrassConfig,
        name: str = "Grass_Blade",
    ) -> Optional[Object]:
        """
        Create a single grass blade mesh for use as particle.

        Args:
            config: Grass configuration
            name: Object name

        Returns:
            Blender mesh object
        """
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"blade_{config.blade_segments}_{config.blade_width_base}"
        if cache_key in self._blade_cache:
            return self._blade_cache[cache_key]

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()

        segments = config.blade_segments
        half_width = config.blade_width_base / 2

        # Create blade as curved mesh
        for i in range(segments + 1):
            t = i / segments
            z = t  # Height from 0 to 1
            width = half_width * (1 - t * 0.9)  # Taper to tip

            # Slight curve
            curve = math.sin(t * math.pi * 0.3) * 0.1

            # Create two vertices for this segment
            v1 = bm.verts.new((-width, curve, z))
            v2 = bm.verts.new((width, curve, z))

        bm.verts.ensure_lookup_table()

        # Create faces connecting segments
        for i in range(segments):
            v1 = bm.verts[i * 2]
            v2 = bm.verts[i * 2 + 1]
            v3 = bm.verts[(i + 1) * 2 + 1]
            v4 = bm.verts[(i + 1) * 2]
            bm.faces.new([v1, v2, v3, v4])

        # Tip point
        tip = bm.verts.new((0, 0.1, 1.05))
        bm.verts.ensure_lookup_table()

        last_idx = segments * 2
        bm.faces.new([bm.verts[last_idx], bm.verts[last_idx + 1], tip])

        bm.to_mesh(mesh)
        bm.free()

        # Scale down to realistic size
        obj.scale = (1, 1, 0.3)

        self._blade_cache[cache_key] = obj
        return obj

    def add_grass_to_surface(
        self,
        surface_obj: Object,
        grass_type: GrassType = GrassType.HIGHWAY_VERGE,
        config: Optional[GrassConfig] = None,
        name: str = "Grass",
    ) -> Optional[ParticleSystem]:
        """
        Add grass particle system to a surface object.

        Args:
            surface_obj: Ground/plane object to add grass to
            grass_type: Type of grass
            config: Custom configuration
            name: Particle system name

        Returns:
            Created particle system
        """
        if not BLENDER_AVAILABLE or surface_obj is None:
            return None

        config = config or GRASS_CONFIGS.get(grass_type, GrassConfig())

        # Create grass blade object
        blade = self.create_grass_blade(config)
        if blade is None:
            return None

        # Add particle system modifier
        ps_mod = surface_obj.modifiers.new(name=name, type='PARTICLE_SYSTEM')
        ps = ps_mod.particle_system

        # Configure particle settings
        settings = ps.settings
        settings.type = 'HAIR'
        settings.use_advanced_hair = True
        settings.emit_from = 'FACE'
        settings.use_emit_random = True
        settings.distribution = config.emission_shape

        # Count
        settings.count = config.particle_count

        # Hair length
        settings.hair_length = config.blade_length_max
        settings.hair_step = config.blade_segments

        # Rendering
        settings.render_type = 'OBJECT'
        settings.instance_object = blade

        # Physics
        if config.use_wind:
            settings.use_hair_bspline = True
            settings.cloth_stiffness = 5.0
            settings.cloth_mass = 0.1

        # Clumping
        settings.use_clump_curve = True
        settings.clump_factor = config.clump_factor
        settings.clump_shape = config.clump_shape

        # Children for density
        if config.use_children:
            settings.child_type = 'INTERPOLATED'
            settings.child_nbr = config.child_particles
            settings.rendered_child_count = config.child_particles * 2

        # Apply grass material
        mat = self._get_grass_material(config)
        if mat:
            if len(surface_obj.data.materials) == 0:
                surface_obj.data.materials.append(mat)
            else:
                surface_obj.data.materials[0] = mat

        return ps

    def create_grass_plane(
        self,
        size: Tuple[float, float] = (100.0, 100.0),
        location: Tuple[float, float, float] = (0, 0, 0),
        grass_type: GrassType = GrassType.HIGHWAY_VERGE,
        config: Optional[GrassConfig] = None,
        name: str = "Grass_Field",
        collection: Optional[Collection] = None,
    ) -> Optional[Object]:
        """
        Create a grass-covered plane.

        Args:
            size: (width, height) of plane in meters
            location: World position
            grass_type: Type of grass
            config: Custom configuration
            name: Object name
            collection: Collection to add to

        Returns:
            Blender mesh object with grass particles
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or GRASS_CONFIGS.get(grass_type, GrassConfig())

        # Create plane
        bpy.ops.mesh.primitive_plane_add(
            size=1.0,
            location=location,
        )
        plane = bpy.context.active_object
        plane.name = name
        plane.scale = (size[0], size[1], 1.0)

        # Calculate particle count based on density
        area = size[0] * size[1]
        config.particle_count = int(config.density * area / config.child_particles if config.use_children else config.density * area)

        # Add grass
        self.add_grass_to_surface(plane, grass_type, config, f"{name}_Particles")

        if collection:
            collection.objects.link(plane)

        return plane

    def _get_grass_material(self, config: GrassConfig) -> Optional[Any]:
        """Get or create grass material."""
        if not BLENDER_AVAILABLE:
            return None

        cache_key = f"grass_{config.base_color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        mat = bpy.data.materials.new("Grass_Material")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, 0)

        # Separate for random
        separate = nodes.new("ShaderNodeSeparateXYZ")
        separate.location = (-600, 0)
        links.new(tex_coord.outputs["Object"], separate.inputs["Vector"])

        # Random for color variation
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-600, 200)
        noise.inputs["Scale"].default_value = 10.0
        links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

        # Color ramp for base-to-tip gradient
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-400, 200)
        color_ramp.color_ramp.elements[0].color = (*config.base_color, 1.0)
        color_ramp.color_ramp.elements[1].color = (*config.tip_color, 1.0)
        links.new(separate.outputs["Z"], color_ramp.inputs["Fac"])

        # Mix with noise for variation
        mix_color = nodes.new("ShaderNodeMixRGB")
        mix_color.location = (-200, 200)
        mix_color.inputs["Fac"].default_value = config.color_variation
        mix_color.inputs["Color1"].default_value = (*config.base_color, 1.0)
        links.new(color_ramp.outputs["Color"], mix_color.inputs["Color2"])
        links.new(noise.outputs["Fac"], mix_color.inputs["Fac"])

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.6
        bsdf.inputs["Metallic"].default_value = 0.0

        links.new(mix_color.outputs["Color"], bsdf.inputs["Base Color"])

        # Subsurface for translucency
        bsdf.inputs["Subsurface Weight"].default_value = 0.1
        bsdf.inputs["Subsurface Color"].default_value = (*config.tip_color, 1.0)

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._material_cache[cache_key] = mat
        return mat


def create_highway_grass_strip(
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    width: float = 10.0,
    grass_type: GrassType = GrassType.HIGHWAY_VERGE,
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Create a grass strip along a highway section.

    Args:
        start: Start position
        end: End position
        width: Width of grass strip
        grass_type: Type of grass
        collection: Collection to add to

    Returns:
        Grass plane object
    """
    if not BLENDER_AVAILABLE:
        return None

    start_v = Vector(start)
    end_v = Vector(end)
    direction = (end_v - start_v).normalized()
    length = (end_v - start_v).length

    # Calculate center and rotation
    center = (start_v + end_v) / 2
    angle = math.atan2(direction.y, direction.x)

    system = GrassSystem()
    config = GRASS_CONFIGS.get(grass_type, GrassConfig())

    # Reduce particle count for strips (optimized for highway)
    config.particle_count = int(config.density * length * width / 5)

    plane = system.create_grass_plane(
        size=(length, width),
        location=center.to_tuple(),
        grass_type=grass_type,
        config=config,
        name="Highway_Grass",
        collection=collection,
    )

    if plane:
        plane.rotation_euler = (0, 0, angle)

    return plane


def create_grass_field(
    center: Tuple[float, float, float],
    size: float = 50.0,
    grass_type: GrassType = GrassType.MEADOW,
    collection: Optional[Collection] = None,
) -> Optional[Object]:
    """
    Create a square grass field.

    Args:
        center: Center position
        size: Side length in meters
        grass_type: Type of grass
        collection: Collection to add to

    Returns:
        Grass plane object
    """
    system = GrassSystem()
    return system.create_grass_plane(
        size=(size, size),
        location=center,
        grass_type=grass_type,
        name="Grass_Field",
        collection=collection,
    )


__all__ = [
    "GrassType",
    "GrassConfig",
    "GRASS_CONFIGS",
    "GrassSystem",
    "create_highway_grass_strip",
    "create_grass_field",
]
