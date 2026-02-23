"""
Environment Ground Materials

Procedural PBR materials for ground surfaces around roads:
- Grass (multiple varieties)
- Dirt/Gravel
- Concrete (sidewalks, under bridges)
- Mulch (landscaping)

Optimized for large-scale ground planes with distance-based LOD.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math
import random

try:
    import bpy
    from bpy.types import Material, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    ShaderNodeTree = Any


class GroundType(Enum):
    """Types of ground surfaces."""
    GRASS_HEALTHY = "grass_healthy"
    GRASS_DRY = "grass_dry"
    GRASS_WILD = "grass_wild"
    DIRT = "dirt"
    GRAVEL = "gravel"
    CONCRETE_NEW = "concrete_new"
    CONCRETE_WEATHERED = "concrete_weathered"
    MULCH = "mulch"
    SAND = "sand"
    MUD = "mud"


@dataclass
class GroundMaterialConfig:
    """Configuration for ground material generation."""
    name: str = "Ground"

    # Primary color
    base_color: Tuple[float, float, float] = (0.2, 0.4, 0.1)  # Green for grass

    # Color variation
    color_variation: float = 0.15
    color_variation_scale: float = 10.0

    # Roughness
    roughness_base: float = 0.8
    roughness_variation: float = 0.1

    # Normal
    normal_strength: float = 0.5

    # Scale
    uv_scale: float = 1.0

    # Secondary details
    detail_scale: float = 50.0
    detail_strength: float = 0.3

    # Distance fade (for LOD)
    fade_distance: float = 500.0  # Distance where detail fades
    fade_color: Tuple[float, float, float] = (0.3, 0.35, 0.3)


# Preset configurations
GROUND_PRESETS = {
    GroundType.GRASS_HEALTHY: GroundMaterialConfig(
        name="Grass_Healthy",
        base_color=(0.15, 0.45, 0.1),
        color_variation=0.15,
        color_variation_scale=15.0,
        roughness_base=0.85,
        normal_strength=0.6,
        detail_scale=60.0,
        detail_strength=0.4,
    ),
    GroundType.GRASS_DRY: GroundMaterialConfig(
        name="Grass_Dry",
        base_color=(0.35, 0.45, 0.15),
        color_variation=0.2,
        color_variation_scale=12.0,
        roughness_base=0.9,
        normal_strength=0.4,
        detail_scale=50.0,
        detail_strength=0.3,
    ),
    GroundType.GRASS_WILD: GroundMaterialConfig(
        name="Grass_Wild",
        base_color=(0.2, 0.4, 0.12),
        color_variation=0.25,
        color_variation_scale=8.0,
        roughness_base=0.88,
        normal_strength=0.5,
        detail_scale=40.0,
        detail_strength=0.5,
    ),
    GroundType.DIRT: GroundMaterialConfig(
        name="Dirt",
        base_color=(0.35, 0.28, 0.18),
        color_variation=0.1,
        color_variation_scale=5.0,
        roughness_base=0.95,
        normal_strength=0.7,
        detail_scale=30.0,
        detail_strength=0.4,
    ),
    GroundType.GRAVEL: GroundMaterialConfig(
        name="Gravel",
        base_color=(0.45, 0.42, 0.38),
        color_variation=0.15,
        color_variation_scale=2.0,
        roughness_base=0.9,
        normal_strength=0.8,
        detail_scale=20.0,
        detail_strength=0.6,
    ),
    GroundType.CONCRETE_NEW: GroundMaterialConfig(
        name="Concrete_New",
        base_color=(0.55, 0.55, 0.52),
        color_variation=0.03,
        color_variation_scale=20.0,
        roughness_base=0.5,
        normal_strength=0.3,
        detail_scale=80.0,
        detail_strength=0.2,
    ),
    GroundType.CONCRETE_WEATHERED: GroundMaterialConfig(
        name="Concrete_Weathered",
        base_color=(0.48, 0.47, 0.44),
        color_variation=0.08,
        color_variation_scale=10.0,
        roughness_base=0.7,
        normal_strength=0.4,
        detail_scale=60.0,
        detail_strength=0.4,
    ),
    GroundType.MULCH: GroundMaterialConfig(
        name="Mulch",
        base_color=(0.25, 0.15, 0.08),
        color_variation=0.15,
        color_variation_scale=3.0,
        roughness_base=0.95,
        normal_strength=0.9,
        detail_scale=15.0,
        detail_strength=0.5,
    ),
    GroundType.SAND: GroundMaterialConfig(
        name="Sand",
        base_color=(0.76, 0.7, 0.5),
        color_variation=0.05,
        color_variation_scale=30.0,
        roughness_base=0.85,
        normal_strength=0.3,
        detail_scale=100.0,
        detail_strength=0.2,
    ),
    GroundType.MUD: GroundMaterialConfig(
        name="Mud",
        base_color=(0.25, 0.18, 0.1),
        color_variation=0.1,
        color_variation_scale=8.0,
        roughness_base=0.3,  # Wet = low roughness
        normal_strength=0.5,
        detail_scale=40.0,
        detail_strength=0.3,
    ),
}


class GroundMaterialBuilder:
    """
    Builder for procedural ground materials.

    Creates optimized PBR materials for large-scale ground planes
    with distance-based detail fading.
    """

    def __init__(self):
        """Initialize the ground material builder."""
        self._material_cache: Dict[str, Material] = {}

    def create(
        self,
        ground_type: GroundType = GroundType.GRASS_HEALTHY,
        config: Optional[GroundMaterialConfig] = None,
    ) -> Optional[Material]:
        """
        Create a ground material.

        Args:
            ground_type: Preset ground type
            config: Custom configuration (overrides preset)

        Returns:
            Blender Material or None
        """
        if not BLENDER_AVAILABLE:
            return None

        # Get configuration
        if config is not None:
            used_config = config
        else:
            used_config = GROUND_PRESETS.get(ground_type, GroundMaterialConfig())

        # Check cache
        cache_key = f"{used_config.name}_{hash(str(used_config))}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        # Create material
        mat = bpy.data.materials.new(name=used_config.name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        self._build_shader_network(nodes, links, used_config)

        self._material_cache[cache_key] = mat
        return mat

    def _build_shader_network(
        self,
        nodes: ShaderNodeTree.nodes,
        links: ShaderNodeTree.links,
        config: GroundMaterialConfig,
    ):
        """Build the procedural shader network for ground."""

        # === COORDINATES ===
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-1200, 0)

        # Separate for potential distance fade
        separate_xyz = nodes.new("ShaderNodeSeparateXYZ")
        separate_xyz.location = (-1000, -200)
        links.new(tex_coord.outputs["Generated"], separate_xyz.inputs["Vector"])

        # === MAIN COLOR NOISE ===
        # Large-scale color variation
        color_noise_large = nodes.new("ShaderNodeTexNoise")
        color_noise_large.location = (-800, 200)
        color_noise_large.inputs["Scale"].default_value = config.color_variation_scale
        color_noise_large.inputs["Detail"].default_value = 2
        color_noise_large.inputs["Distortion"].default_value = 0.3
        links.new(tex_coord.outputs["Generated"], color_noise_large.inputs["Vector"])

        # Color ramp for variation
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-600, 200)
        # Set gradient for grass-like variation
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
        links.new(color_noise_large.outputs["Fac"], color_ramp.inputs["Fac"])

        # === DETAIL NOISE ===
        detail_noise = nodes.new("ShaderNodeTexNoise")
        detail_noise.location = (-800, 0)
        detail_noise.inputs["Scale"].default_value = config.detail_scale
        detail_noise.inputs["Detail"].default_value = 4
        links.new(tex_coord.outputs["Generated"], detail_noise.inputs["Vector"])

        # Mix detail with base color
        detail_mix = nodes.new("ShaderNodeMixRGB")
        detail_mix.location = (-400, 100)
        detail_mix.inputs["Fac"].default_value = config.detail_strength
        detail_mix.inputs["Color1"].default_value = (*config.base_color, 1.0)
        links.new(color_ramp.outputs["Color"], detail_mix.inputs["Color2"])
        links.new(detail_noise.outputs["Fac"], detail_mix.inputs["Fac"])

        # === ROUGHNESS ===
        roughness_noise = nodes.new("ShaderNodeTexNoise")
        roughness_noise.location = (-800, -200)
        roughness_noise.inputs["Scale"].default_value = config.detail_scale * 0.5
        roughness_noise.inputs["Detail"].default_value = 2
        links.new(tex_coord.outputs["Generated"], roughness_noise.inputs["Vector"])

        roughness_math = nodes.new("ShaderNodeMath")
        roughness_math.location = (-600, -200)
        roughness_math.operation = "MULTIPLY_ADD"
        roughness_math.inputs[0].default_value = config.roughness_variation
        roughness_math.inputs[2].default_value = config.roughness_base
        links.new(roughness_noise.outputs["Fac"], roughness_math.inputs[1])

        # === NORMAL ===
        normal_noise = nodes.new("ShaderNodeTexNoise")
        normal_noise.location = (-800, -400)
        normal_noise.inputs["Scale"].default_value = config.detail_scale * 2
        normal_noise.inputs["Detail"].default_value = 3
        links.new(tex_coord.outputs["Generated"], normal_noise.inputs["Vector"])

        # Convert to normal
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-400, -400)
        normal_map.inputs["Strength"].default_value = config.normal_strength

        # Combine for normal input
        normal_combine = nodes.new("ShaderNodeCombineColor")
        normal_combine.location = (-600, -400)
        normal_combine.inputs["Green"].default_value = 0.5
        links.new(normal_noise.outputs["Fac"], normal_combine.inputs["Red"])
        links.new(normal_noise.outputs["Fac"], normal_combine.inputs["Blue"])
        links.new(normal_combine.outputs["Image"], normal_map.inputs["Color"])

        # === BSDF ===
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

        links.new(detail_mix.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(roughness_math.outputs[0], bsdf.inputs["Roughness"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])

        # === OUTPUT ===
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])


def create_grass_material(
    variety: str = "healthy",
    name: str = "Grass",
) -> Optional[Material]:
    """
    Create a grass material.

    Args:
        variety: "healthy", "dry", or "wild"
        name: Material name

    Returns:
        Blender Material or None
    """
    type_map = {
        "healthy": GroundType.GRASS_HEALTHY,
        "dry": GroundType.GRASS_DRY,
        "wild": GroundType.GRASS_WILD,
    }

    builder = GroundMaterialBuilder()
    mat = builder.create(type_map.get(variety, GroundType.GRASS_HEALTHY))

    if mat:
        mat.name = name

    return mat


def create_dirt_material(name: str = "Dirt") -> Optional[Material]:
    """Create a dirt ground material."""
    builder = GroundMaterialBuilder()
    mat = builder.create(GroundType.DIRT)
    if mat:
        mat.name = name
    return mat


def create_gravel_material(name: str = "Gravel") -> Optional[Material]:
    """Create a gravel ground material."""
    builder = GroundMaterialBuilder()
    mat = builder.create(GroundType.GRAVEL)
    if mat:
        mat.name = name
    return mat


def create_concrete_material(
    weathered: bool = True,
    name: str = "Concrete",
) -> Optional[Material]:
    """
    Create a concrete material.

    Args:
        weathered: If True, creates weathered concrete
        name: Material name

    Returns:
        Blender Material or None
    """
    builder = GroundMaterialBuilder()
    ground_type = GroundType.CONCRETE_WEATHERED if weathered else GroundType.CONCRETE_NEW
    mat = builder.create(ground_type)
    if mat:
        mat.name = name
    return mat


__all__ = [
    "GroundType",
    "GroundMaterialConfig",
    "GroundMaterialBuilder",
    "GROUND_PRESETS",
    "create_grass_material",
    "create_dirt_material",
    "create_gravel_material",
    "create_concrete_material",
]
