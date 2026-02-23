"""
Building Materials System

Procedural PBR materials for buildings:
- Glass windows (reflective, transparent)
- Concrete walls (weathered, clean)
- Brick facades
- Metal cladding
- Roof materials

Optimized for urban building visualization.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple

try:
    import bpy
    from bpy.types import Material, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    ShaderNodeTree = Any


class FacadeType(Enum):
    """Building facade material types."""
    GLASS_CURTAIN = "glass_curtain"      # Modern glass facade
    CONCRETE_BRUTALIST = "concrete"       # Exposed concrete
    BRICK_TRADITIONAL = "brick"           # Traditional brick
    METAL_PANEL = "metal"                 # Metal cladding
    STUCCO = "stucco"                     # Stucco/plaster
    COMBINED = "combined"                 # Mixed materials


class WindowType(Enum):
    """Window glass types."""
    CLEAR = "clear"           # Standard clear glass
    TINTED = "tinted"         # Tinted glass
    REFLECTIVE = "reflective" # Mirror-like glass
    CURTAIN_WALL = "curtain"  # Full curtain wall


class RoofMaterial(Enum):
    """Roof material types."""
    FLAT_TAR = "tar"          # Flat tar/gravel roof
    METAL = "metal"           # Metal roofing
    SHINGLE = "shingle"       # Asphalt shingles
    TILE = "tile"             # Clay/concrete tiles
    MEMBRANE = "membrane"     # Rubber membrane


@dataclass
class GlassConfig:
    """Configuration for glass material."""
    base_color: Tuple[float, float, float] = (0.6, 0.7, 0.8)
    roughness: float = 0.05
    metallic: float = 0.0
    ior: float = 1.45  # Index of refraction
    transmission: float = 0.9
    reflectivity: float = 0.5
    tint_strength: float = 0.3


@dataclass
class ConcreteConfig:
    """Configuration for concrete material."""
    base_color: Tuple[float, float, float] = (0.55, 0.53, 0.5)
    roughness: float = 0.85
    color_variation: float = 0.1
    crack_amount: float = 0.05
    stain_amount: float = 0.1
    weathering: float = 0.3


@dataclass
class BrickConfig:
    """Configuration for brick material."""
    base_color: Tuple[float, float, float] = (0.6, 0.35, 0.25)
    mortar_color: Tuple[float, float, float] = (0.7, 0.68, 0.65)
    brick_size: Tuple[float, float] = (0.2, 0.065)  # Width, height
    roughness: float = 0.8
    color_variation: float = 0.15


@dataclass
class MetalConfig:
    """Configuration for metal cladding."""
    base_color: Tuple[float, float, float] = (0.6, 0.6, 0.65)
    roughness: float = 0.3
    metallic: float = 0.9
    anisotropic: float = 0.5
    panel_width: float = 0.6


# Preset configurations
GLASS_PRESETS = {
    WindowType.CLEAR: GlassConfig(
        base_color=(0.85, 0.9, 0.95),
        transmission=0.95,
        tint_strength=0.1,
    ),
    WindowType.TINTED: GlassConfig(
        base_color=(0.3, 0.4, 0.5),
        transmission=0.7,
        tint_strength=0.5,
    ),
    WindowType.REFLECTIVE: GlassConfig(
        base_color=(0.5, 0.55, 0.6),
        transmission=0.3,
        reflectivity=0.8,
        metallic=0.2,
    ),
    WindowType.CURTAIN_WALL: GlassConfig(
        base_color=(0.4, 0.5, 0.55),
        transmission=0.6,
        reflectivity=0.6,
        tint_strength=0.4,
    ),
}


class BuildingMaterialBuilder:
    """
    Creates procedural building materials.

    Generates PBR materials optimized for urban visualization
    with weathering and variation.
    """

    def __init__(self):
        """Initialize material builder."""
        self._cache: Dict[str, Material] = {}

    def create_glass_material(
        self,
        window_type: WindowType = WindowType.REFLECTIVE,
        config: Optional[GlassConfig] = None,
        name: str = "Building_Glass",
    ) -> Optional[Material]:
        """
        Create glass material for windows.

        Args:
            window_type: Type of glass
            config: Custom configuration
            name: Material name

        Returns:
            Blender Material
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or GLASS_PRESETS.get(window_type, GlassConfig())

        cache_key = f"glass_{window_type.value}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        mat = bpy.data.materials.new(name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Glass BSDF
        glass = nodes.new("ShaderNodeBsdfGlass")
        glass.location = (0, 0)
        glass.inputs["Color"].default_value = (*config.base_color, 1.0)
        glass.inputs["Roughness"].default_value = config.roughness
        glass.inputs["IOR"].default_value = config.ior

        # Mix with principled for reflectivity
        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, -200)
        principled.inputs["Base Color"].default_value = (*config.base_color, 1.0)
        principled.inputs["Metallic"].default_value = config.metallic
        principled.inputs["Roughness"].default_value = config.roughness

        # Mix shader
        mix = nodes.new("ShaderNodeMixShader")
        mix.location = (200, 0)
        mix.inputs["Fac"].default_value = 1.0 - config.transmission

        links.new(glass.outputs["BSDF"], mix.inputs[1])
        links.new(principled.outputs["BSDF"], mix.inputs[2])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        links.new(mix.outputs["Shader"], output.inputs["Surface"])

        self._cache[cache_key] = mat
        return mat

    def create_concrete_material(
        self,
        config: Optional[ConcreteConfig] = None,
        name: str = "Building_Concrete",
    ) -> Optional[Material]:
        """
        Create concrete material.

        Args:
            config: Concrete configuration
            name: Material name

        Returns:
            Blender Material
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or ConcreteConfig()

        cache_key = f"concrete_{config.weathering}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        mat = bpy.data.materials.new(name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Texture coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-1200, 0)

        # Noise for variation
        noise1 = nodes.new("ShaderNodeTexNoise")
        noise1.location = (-1000, 200)
        noise1.inputs["Scale"].default_value = 20.0
        noise1.inputs["Detail"].default_value = 4
        links.new(tex_coord.outputs["Object"], noise1.inputs["Vector"])

        # Color ramp for variation
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-800, 200)
        color_ramp.color_ramp.elements[0].color = (
            config.base_color[0] - config.color_variation,
            config.base_color[1] - config.color_variation,
            config.base_color[2] - config.color_variation,
            1.0
        )
        color_ramp.color_ramp.elements[1].color = (
            config.base_color[0] + config.color_variation,
            config.base_color[1] + config.color_variation,
            config.base_color[2] + config.color_variation,
            1.0
        )
        links.new(noise1.outputs["Fac"], color_ramp.inputs["Fac"])

        # Detail noise for roughness
        noise2 = nodes.new("ShaderNodeTexNoise")
        noise2.location = (-800, -100)
        noise2.inputs["Scale"].default_value = 100.0
        noise2.inputs["Detail"].default_value = 8
        links.new(tex_coord.outputs["Object"], noise2.inputs["Vector"])

        # Roughness math
        roughness_math = nodes.new("ShaderNodeMath")
        roughness_math.location = (-600, -100)
        roughness_math.operation = "MULTIPLY_ADD"
        roughness_math.inputs[0].default_value = 0.1
        roughness_math.inputs[2].default_value = config.roughness
        links.new(noise2.outputs["Fac"], roughness_math.inputs[1])

        # Normal map noise
        normal_noise = nodes.new("ShaderNodeTexNoise")
        normal_noise.location = (-800, -300)
        normal_noise.inputs["Scale"].default_value = 50.0
        links.new(tex_coord.outputs["Object"], normal_noise.inputs["Vector"])

        # Normal map
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-600, -300)
        normal_map.inputs["Strength"].default_value = 0.3

        # Combine for normal
        combine = nodes.new("ShaderNodeCombineColor")
        combine.location = (-800, -400)
        combine.inputs["Green"].default_value = 0.5
        links.new(normal_noise.outputs["Fac"], combine.inputs["Red"])
        links.new(normal_noise.outputs["Fac"], combine.inputs["Blue"])
        links.new(combine.outputs["Image"], normal_map.inputs["Color"])

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

        links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(roughness_math.outputs[0], bsdf.inputs["Roughness"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._cache[cache_key] = mat
        return mat

    def create_brick_material(
        self,
        config: Optional[BrickConfig] = None,
        name: str = "Building_Brick",
    ) -> Optional[Material]:
        """
        Create brick material with mortar.

        Args:
            config: Brick configuration
            name: Material name

        Returns:
            Blender Material
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or BrickConfig()

        if "brick" in self._cache:
            return self._cache["brick"]

        mat = bpy.data.materials.new(name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Texture coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-1200, 0)

        # Brick texture
        brick = nodes.new("ShaderNodeTexBrick")
        brick.location = (-800, 0)
        brick.inputs["Color1"].default_value = (*config.base_color, 1.0)
        brick.inputs["Color2"].default_value = (
            config.base_color[0] * 0.9,
            config.base_color[1] * 0.9,
            config.base_color[2] * 0.9,
            1.0
        )
        brick.inputs["Mortar"].default_value = (*config.mortar_color, 1.0)
        brick.inputs["Scale"].default_value = 1.0 / config.brick_size[0]
        brick.inputs["Mortar Size"].default_value = 0.03
        brick.inputs["Bias"].default_value = config.color_variation

        links.new(tex_coord.outputs["Object"], brick.inputs["Vector"])

        # Noise for brick variation
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-1000, 200)
        noise.inputs["Scale"].default_value = 30.0
        links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

        # Mix brick with noise
        mix_color = nodes.new("ShaderNodeMixRGB")
        mix_color.location = (-600, 0)
        mix_color.inputs["Fac"].default_value = 0.3
        links.new(brick.outputs["Color"], mix_color.inputs["Color1"])
        links.new(noise.outputs["Fac"], mix_color.inputs["Color2"])

        # Bump for brick relief
        bump = nodes.new("ShaderNodeBump")
        bump.location = (-600, -200)
        bump.inputs["Strength"].default_value = 0.02
        links.new(brick.outputs["Fac"], bump.inputs["Height"])

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = config.roughness

        links.new(mix_color.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._cache["brick"] = mat
        return mat

    def create_metal_material(
        self,
        config: Optional[MetalConfig] = None,
        name: str = "Building_Metal",
    ) -> Optional[Material]:
        """
        Create metal cladding material.

        Args:
            config: Metal configuration
            name: Material name

        Returns:
            Blender Material
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or MetalConfig()

        cache_key = f"metal_{config.anisotropic}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        mat = bpy.data.materials.new(name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Texture coordinate
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, 0)

        # Wave texture for panel lines
        wave = nodes.new("ShaderNodeTexWave")
        wave.location = (-600, 0)
        wave.inputs["Scale"].default_value = 1.0 / config.panel_width
        wave.inputs["Distortion"].default_value = 0.0
        wave.inputs["Detail"].default_value = 0.0
        links.new(tex_coord.outputs["Object"], wave.inputs["Vector"])

        # Color ramp for panel grooves
        groove_ramp = nodes.new("ShaderNodeValToRGB")
        groove_ramp.location = (-400, -100)
        groove_ramp.color_ramp.elements[0].position = 0.45
        groove_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        groove_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        links.new(wave.outputs["Fac"], groove_ramp.inputs["Fac"])

        # BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Base Color"].default_value = (*config.base_color, 1.0)
        bsdf.inputs["Metallic"].default_value = config.metallic
        bsdf.inputs["Roughness"].default_value = config.roughness
        bsdf.inputs["Anisotropic"].default_value = config.anisotropic

        # Use groove for bump
        bump = nodes.new("ShaderNodeBump")
        bump.location = (-200, -200)
        bump.inputs["Strength"].default_value = 0.01
        links.new(groove_ramp.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        self._cache[cache_key] = mat
        return mat


def create_facade_material(
    facade_type: FacadeType = FacadeType.CONCRETE_BRUTALIST,
    name: str = "Building_Facade",
) -> Optional[Material]:
    """
    Create building facade material by type.

    Args:
        facade_type: Type of facade
        name: Material name

    Returns:
        Blender Material
    """
    builder = BuildingMaterialBuilder()

    if facade_type == FacadeType.GLASS_CURTAIN:
        return builder.create_glass_material(WindowType.CURTAIN_WALL, name=name)
    elif facade_type == FacadeType.CONCRETE_BRUTALIST:
        return builder.create_concrete_material(name=name)
    elif facade_type == FacadeType.BRICK_TRADITIONAL:
        return builder.create_brick_material(name=name)
    elif facade_type == FacadeType.METAL_PANEL:
        return builder.create_metal_material(name=name)
    else:
        return builder.create_concrete_material(name=name)


__all__ = [
    "FacadeType",
    "WindowType",
    "RoofMaterial",
    "GlassConfig",
    "ConcreteConfig",
    "BrickConfig",
    "MetalConfig",
    "GLASS_PRESETS",
    "BuildingMaterialBuilder",
    "create_facade_material",
]
