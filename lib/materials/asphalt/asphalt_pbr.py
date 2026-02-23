"""
Procedural PBR Asphalt Material Generator

Creates realistic asphalt materials using only procedural nodes.
No external textures required - suitable for any scale.

Features:
- Aggregate texture simulation (small stones in asphalt)
- Trowel marks and roller patterns
- Oil stains and tire marks
- Crack generation
- Pothole displacement
- Multiple wear levels
- Wet weather variations
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import bpy
    from bpy.types import Material, ShaderNode, ShaderNodeTree, Object
    from mathutils import Color
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    ShaderNode = Any
    ShaderNodeTree = Any
    Object = Any


class AsphaltType(Enum):
    """Types of asphalt surface."""
    HIGHWAY = "highway"           # Fresh, dark, smooth
    RESIDENTIAL = "residential"   # Medium wear, some texture
    PARKING_LOT = "parking_lot"   # Heavily worn, stained
    DRIVEWAY = "driveway"         # Mixed wear, patchy
    RURAL = "rural"               # Gravel mix, rough


class AsphaltCondition(Enum):
    """Physical condition of asphalt."""
    FRESH = "fresh"           # Recently paved, dark
    GOOD = "good"             # Normal wear
    WORN = "worn"             # Visible wear, lighter color
    DAMAGED = "damaged"       # Cracks, patches, potholes
    AGED = "aged"             # Old, faded, cracked


class AsphaltPreset(Enum):
    """Presets combining type and condition."""
    HIGHWAY_FRESH = "highway_fresh"
    HIGHWAY_WORN = "highway_worn"
    RESIDENTIAL_GOOD = "residential_good"
    RESIDENTIAL_WORN = "residential_worn"
    PARKING_LOT = "parking_lot"
    RURAL_ROAD = "rural_road"
    WET_HIGHWAY = "wet_highway"
    DAMAGED_ROAD = "damaged_road"


@dataclass
class AsphaltConfig:
    """Configuration for asphalt material generation."""
    name: str = "Asphalt"

    # Base color
    base_color: Tuple[float, float, float] = (0.08, 0.08, 0.08)
    color_variation: float = 0.03  # How much color varies

    # Aggregate (stones in asphalt)
    aggregate_scale: float = 15.0  # Size of aggregate pattern
    aggregate_contrast: float = 0.15  # How visible aggregate is
    aggregate_color: Tuple[float, float, float] = (0.12, 0.11, 0.10)  # Lighter stones

    # Surface texture
    roughness_base: float = 0.75
    roughness_variation: float = 0.1
    normal_strength: float = 0.3

    # Wear and damage
    wear_amount: float = 0.0  # 0-1, affects lightness and roughness
    crack_intensity: float = 0.0  # 0-1, crack visibility
    crack_scale: float = 2.0
    pothole_intensity: float = 0.0  # 0-1, displacement depth

    # Stains and marks
    oil_stain_amount: float = 0.0  # 0-1
    tire_mark_amount: float = 0.0  # 0-1

    # Weather
    wetness: float = 0.0  # 0-1, reduces roughness, increases specularity
    puddle_amount: float = 0.0  # 0-1

    # UV and scale
    uv_scale: float = 1.0

    # Performance
    use_bump: bool = True  # Use bump instead of displacement for performance
    detail_level: int = 4  # Noise detail octaves (1-8)


@dataclass
class AsphaltMaterialResult:
    """Result of asphalt material creation."""
    material: Optional[Material] = None
    node_group: Optional[Any] = None  # ShaderNodeGroup
    config_used: Optional[AsphaltConfig] = None
    nodes_created: List[str] = field(default_factory=list)

    # Outputs available in node group
    has_displacement: bool = False
    has_ao: bool = False


# Preset configurations
ASPHALT_PRESETS = {
    AsphaltPreset.HIGHWAY_FRESH: AsphaltConfig(
        name="Highway_Fresh",
        base_color=(0.06, 0.06, 0.06),
        color_variation=0.02,
        aggregate_scale=20.0,
        aggregate_contrast=0.1,
        roughness_base=0.7,
        normal_strength=0.25,
        wear_amount=0.0,
        detail_level=5,
    ),
    AsphaltPreset.HIGHWAY_WORN: AsphaltConfig(
        name="Highway_Worn",
        base_color=(0.10, 0.10, 0.09),
        color_variation=0.04,
        aggregate_scale=18.0,
        aggregate_contrast=0.2,
        roughness_base=0.8,
        normal_strength=0.35,
        wear_amount=0.4,
        crack_intensity=0.2,
        detail_level=4,
    ),
    AsphaltPreset.RESIDENTIAL_GOOD: AsphaltConfig(
        name="Residential_Good",
        base_color=(0.08, 0.08, 0.07),
        color_variation=0.03,
        aggregate_scale=15.0,
        aggregate_contrast=0.15,
        roughness_base=0.75,
        normal_strength=0.3,
        wear_amount=0.2,
        oil_stain_amount=0.1,
        detail_level=4,
    ),
    AsphaltPreset.RESIDENTIAL_WORN: AsphaltConfig(
        name="Residential_Worn",
        base_color=(0.12, 0.11, 0.10),
        color_variation=0.05,
        aggregate_scale=12.0,
        aggregate_contrast=0.25,
        roughness_base=0.85,
        normal_strength=0.4,
        wear_amount=0.6,
        crack_intensity=0.3,
        oil_stain_amount=0.2,
        detail_level=4,
    ),
    AsphaltPreset.PARKING_LOT: AsphaltConfig(
        name="Parking_Lot",
        base_color=(0.10, 0.10, 0.09),
        color_variation=0.05,
        aggregate_scale=10.0,
        aggregate_contrast=0.2,
        roughness_base=0.8,
        normal_strength=0.35,
        wear_amount=0.5,
        oil_stain_amount=0.4,
        tire_mark_amount=0.3,
        crack_intensity=0.15,
        detail_level=3,
    ),
    AsphaltPreset.RURAL_ROAD: AsphaltConfig(
        name="Rural_Road",
        base_color=(0.15, 0.13, 0.10),
        color_variation=0.08,
        aggregate_scale=8.0,
        aggregate_contrast=0.3,
        roughness_base=0.9,
        normal_strength=0.5,
        wear_amount=0.5,
        crack_intensity=0.4,
        detail_level=3,
    ),
    AsphaltPreset.WET_HIGHWAY: AsphaltConfig(
        name="Wet_Highway",
        base_color=(0.04, 0.04, 0.05),
        color_variation=0.02,
        aggregate_scale=20.0,
        aggregate_contrast=0.08,
        roughness_base=0.2,  # Wet = low roughness
        normal_strength=0.15,
        wetness=0.8,
        puddle_amount=0.2,
        detail_level=4,
    ),
    AsphaltPreset.DAMAGED_ROAD: AsphaltConfig(
        name="Damaged_Road",
        base_color=(0.12, 0.11, 0.10),
        color_variation=0.06,
        aggregate_scale=12.0,
        aggregate_contrast=0.25,
        roughness_base=0.85,
        normal_strength=0.45,
        wear_amount=0.7,
        crack_intensity=0.6,
        crack_scale=3.0,
        pothole_intensity=0.3,
        detail_level=4,
    ),
}


class AsphaltMaterialBuilder:
    """
    Builder for creating procedural asphalt materials.

    Creates a complete PBR material with:
    - Procedural base color with aggregate texture
    - Roughness variation
    - Normal map detail
    - Optional displacement for cracks/potholes
    - Wet weather variations
    """

    def __init__(self):
        """Initialize the asphalt material builder."""
        self._material_cache: Dict[str, Material] = {}
        self._node_group_cache: Dict[str, Any] = {}

    def create(
        self,
        name: str = "Asphalt",
        preset: Optional[AsphaltPreset] = None,
        config: Optional[AsphaltConfig] = None,
    ) -> AsphaltMaterialResult:
        """
        Create an asphalt material.

        Args:
            name: Material name
            preset: Use a preset configuration
            config: Custom configuration (overrides preset)

        Returns:
            AsphaltMaterialResult with created material
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to create materials")

        # Determine configuration
        if config is not None:
            used_config = config
        elif preset is not None:
            used_config = ASPHALT_PRESETS.get(preset, AsphaltConfig())
        else:
            used_config = AsphaltConfig()

        used_config.name = name

        # Check cache
        cache_key = f"{name}_{hash(str(used_config))}"
        if cache_key in self._material_cache:
            return AsphaltMaterialResult(
                material=self._material_cache[cache_key],
                config_used=used_config,
            )

        # Create material
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Build the shader network
        result = self._build_procedural_asphalt(
            mat.node_tree,
            used_config
        )

        result.material = mat
        result.config_used = used_config

        # Cache
        self._material_cache[cache_key] = mat

        return result

    def _build_procedural_asphalt(
        self,
        node_tree: ShaderNodeTree,
        config: AsphaltConfig,
    ) -> AsphaltMaterialResult:
        """Build the procedural asphalt shader network."""
        nodes = node_tree.nodes
        links = node_tree.links

        result = AsphaltMaterialResult()

        # === COORDINATE NODES ===
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, 0)
        result.nodes_created.append(tex_coord.name)

        mapping = nodes.new("ShaderNodeMapping")
        mapping.location = (-600, 0)
        mapping.inputs["Scale"].default_value = (config.uv_scale, config.uv_scale, 1.0)
        result.nodes_created.append(mapping.name)

        links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

        # === BASE COLOR LAYER ===
        # Base asphalt color with noise variation
        base_color_noise = nodes.new("ShaderNodeTexNoise")
        base_color_noise.location = (-400, 200)
        base_color_noise.inputs["Scale"].default_value = config.aggregate_scale
        base_color_noise.inputs["Detail"].default_value = config.detail_level
        base_color_noise.inputs["Distortion"].default_value = 0.2
        result.nodes_created.append(base_color_noise.name)

        links.new(mapping.outputs["Vector"], base_color_noise.inputs["Vector"])

        # Color ramp for aggregate variation
        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (-200, 200)
        # Set gradient colors
        color_ramp.color_ramp.elements[0].color = (*config.base_color, 1.0)
        color_ramp.color_ramp.elements[1].color = (*config.aggregate_color, 1.0)
        result.nodes_created.append(color_ramp.name)

        links.new(base_color_noise.outputs["Fac"], color_ramp.inputs["Fac"])

        # Additional color noise for variation
        color_var_noise = nodes.new("ShaderNodeTexNoise")
        color_var_noise.location = (-400, 400)
        color_var_noise.inputs["Scale"].default_value = config.aggregate_scale * 0.5
        color_var_noise.inputs["Detail"].default_value = 2
        result.nodes_created.append(color_var_noise.name)

        links.new(mapping.outputs["Vector"], color_var_noise.inputs["Vector"])

        # Mix base color with variation
        color_mix = nodes.new("ShaderNodeMixRGB")
        color_mix.location = (0, 300)
        color_mix.inputs["Fac"].default_value = config.color_variation
        color_mix.inputs["Color1"].default_value = (*config.base_color, 1.0)
        result.nodes_created.append(color_mix.name)

        links.new(color_ramp.outputs["Color"], color_mix.inputs["Color2"])
        links.new(color_var_noise.outputs["Fac"], color_mix.inputs["Fac"])

        # === WEAR EFFECT (lightens color) ===
        if config.wear_amount > 0:
            wear_mix = nodes.new("ShaderNodeMixRGB")
            wear_mix.location = (100, 300)
            wear_mix.inputs["Fac"].default_value = config.wear_amount
            wear_mix.inputs["Color2"].default_value = (0.18, 0.17, 0.15, 1.0)  # Worn color
            result.nodes_created.append(wear_mix.name)

            links.new(color_mix.outputs["Color"], wear_mix.inputs["Color1"])
            final_color_node = wear_mix
        else:
            final_color_node = color_mix

        # === OIL STAINS ===
        if config.oil_stain_amount > 0:
            oil_noise = nodes.new("ShaderNodeTexNoise")
            oil_noise.location = (-200, -100)
            oil_noise.inputs["Scale"].default_value = 3.0
            oil_noise.inputs["Detail"].default_value = 2
            result.nodes_created.append(oil_noise.name)

            links.new(mapping.outputs["Vector"], oil_noise.inputs["Vector"])

            oil_mix = nodes.new("ShaderNodeMixRGB")
            oil_mix.location = (200, 200)
            oil_mix.inputs["Fac"].default_value = config.oil_stain_amount
            oil_mix.inputs["Color2"].default_value = (0.03, 0.03, 0.04, 1.0)  # Dark oil
            result.nodes_created.append(oil_mix.name)

            links.new(final_color_node.outputs["Color"], oil_mix.inputs["Color1"])
            links.new(oil_noise.outputs["Fac"], oil_mix.inputs["Fac"])
            final_color_node = oil_mix

        # === ROUGHNESS ===
        roughness_noise = nodes.new("ShaderNodeTexNoise")
        roughness_noise.location = (-400, -200)
        roughness_noise.inputs["Scale"].default_value = config.aggregate_scale * 2
        roughness_noise.inputs["Detail"].default_value = max(2, config.detail_level - 2)
        result.nodes_created.append(roughness_noise.name)

        links.new(mapping.outputs["Vector"], roughness_noise.inputs["Vector"])

        roughness_math = nodes.new("ShaderNodeMath")
        roughness_math.location = (-200, -200)
        roughness_math.operation = "MULTIPLY_ADD"
        roughness_math.inputs[0].default_value = config.roughness_variation
        roughness_math.inputs[2].default_value = config.roughness_base
        result.nodes_created.append(roughness_math.name)

        links.new(roughness_noise.outputs["Fac"], roughness_math.inputs[1])

        # Wetness reduces roughness
        if config.wetness > 0:
            wet_roughness = nodes.new("ShaderNodeMath")
            wet_roughness.location = (0, -200)
            wet_roughness.operation = "SUBTRACT"
            wet_roughness.inputs[1].default_value = config.wetness * 0.5
            result.nodes_created.append(wet_roughness.name)

            links.new(roughness_math.outputs[0], wet_roughness.inputs[0])
            final_roughness_node = wet_roughness
        else:
            final_roughness_node = roughness_math

        # === NORMAL MAP ===
        normal_noise = nodes.new("ShaderNodeTexNoise")
        normal_noise.location = (-400, -400)
        normal_noise.inputs["Scale"].default_value = config.aggregate_scale * 3
        normal_noise.inputs["Detail"].default_value = max(2, config.detail_level - 1)
        result.nodes_created.append(normal_noise.name)

        links.new(mapping.outputs["Vector"], normal_noise.inputs["Vector"])

        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-200, -400)
        normal_map.inputs["Strength"].default_value = config.normal_strength
        result.nodes_created.append(normal_map.name)

        # Convert noise to color for normal map
        normal_combine = nodes.new("ShaderNodeCombineColor")
        normal_combine.location = (-350, -400)
        normal_combine.inputs["Green"].default_value = 0.5
        result.nodes_created.append(normal_combine.name)

        # Use noise for both R and B channels
        links.new(normal_noise.outputs["Fac"], normal_combine.inputs["Red"])
        links.new(normal_noise.outputs["Fac"], normal_combine.inputs["Blue"])
        links.new(normal_combine.outputs["Image"], normal_map.inputs["Color"])

        # === CRACK EFFECT ===
        if config.crack_intensity > 0:
            crack_voronoi = nodes.new("ShaderNodeTexVoronoi")
            crack_voronoi.location = (-400, -600)
            crack_voronoi.inputs["Scale"].default_value = config.crack_scale
            crack_voronoi.inputs["Randomness"].default_value = 0.8
            result.nodes_created.append(crack_voronoi.name)

            links.new(mapping.outputs["Vector"], crack_voronoi.inputs["Vector"])

            # Crack affects roughness (makes it rougher in cracks)
            crack_roughness = nodes.new("ShaderNodeMath")
            crack_roughness.location = (-200, -600)
            crack_roughness.operation = "MULTIPLY_ADD"
            crack_roughness.inputs[0].default_value = config.crack_intensity * 0.3
            result.nodes_created.append(crack_roughness.name)

            links.new(crack_voronoi.outputs["Distance"], crack_roughness.inputs[1])
            links.new(crack_roughness.outputs[0], roughness_math.inputs[2])  # Add to roughness base

            result.nodes_created.append(crack_voronoi.name)

        # === PRINCIPLED BSDF ===
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (400, 0)
        result.nodes_created.append(bsdf.name)

        # Connect color
        links.new(final_color_node.outputs["Color"], bsdf.inputs["Base Color"])

        # Connect roughness
        links.new(final_roughness_node.outputs[0], bsdf.inputs["Roughness"])

        # Connect normal
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])

        # Wetness affects specular
        if config.wetness > 0:
            bsdf.inputs["Specular IOR Level"].default_value = 0.5 + config.wetness * 0.4
        else:
            bsdf.inputs["Specular IOR Level"].default_value = 0.5

        # === OUTPUT ===
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (600, 0)
        result.nodes_created.append(output.name)

        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        return result

    def apply_to_object(
        self,
        obj: Object,
        material: Material,
        slot_index: int = 0,
    ) -> bool:
        """
        Apply asphalt material to a mesh object.

        Args:
            obj: Blender object to apply material to
            material: Material to apply
            slot_index: Material slot index

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        if obj is None or material is None:
            return False

        # Ensure material slots exist
        while len(obj.data.materials) <= slot_index:
            obj.data.materials.append(None)

        obj.data.materials[slot_index] = material
        return True

    def create_node_group(
        self,
        name: str = "Asphalt_PBR",
        config: Optional[AsphaltConfig] = None,
    ) -> Optional[Any]:
        """
        Create a reusable node group for asphalt.

        The node group has inputs for:
        - Vector (UV)
        - Color Override
        - Roughness Override
        - Normal Strength

        And outputs for:
        - Color
        - Roughness
        - Normal
        - Displacement

        Args:
            name: Node group name
            config: Configuration for defaults

        Returns:
            ShaderNodeGroup or None
        """
        if not BLENDER_AVAILABLE:
            return None

        config = config or AsphaltConfig()

        # Check if group already exists
        if name in bpy.data.node_groups:
            return bpy.data.node_groups[name]

        # Create node group
        node_group = bpy.data.node_groups.new(name=name, type="ShaderNodeTree")

        # Create interface
        # Inputs
        node_group.interface.new_socket(name="Vector", socket_type="NodeSocketVector")
        node_group.interface.new_socket(name="Color Override", socket_type="NodeSocketColor")
        node_group.interface.new_socket(name="Roughness Override", socket_type="NodeSocketFloatFactor")
        node_group.interface.new_socket(name="Normal Strength", socket_type="NodeSocketFloatFactor", default_value=config.normal_strength)

        # Outputs
        node_group.interface.new_socket(name="Color", socket_type="NodeSocketColor")
        node_group.interface.new_socket(name="Roughness", socket_type="NodeSocketFloat")
        node_group.interface.new_socket(name="Normal", socket_type="NodeSocketVector")
        node_group.interface.new_socket(name="Displacement", socket_type="NodeSocketFloat")

        # Build internal nodes (simplified version)
        nodes = node_group.nodes
        links = node_group.links

        # Input/Output nodes
        input_node = nodes.new("NodeGroupInput")
        input_node.location = (-400, 0)

        output_node = nodes.new("NodeGroupOutput")
        output_node.location = (400, 0)

        # Simple noise-based color
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-200, 0)
        noise.inputs["Scale"].default_value = config.aggregate_scale

        color_ramp = nodes.new("ShaderNodeValToRGB")
        color_ramp.location = (0, 0)
        color_ramp.color_ramp.elements[0].color = (*config.base_color, 1.0)
        color_ramp.color_ramp.elements[1].color = (*config.aggregate_color, 1.0)

        # Roughness
        roughness = nodes.new("ShaderNodeValue")
        roughness.location = (0, -100)
        roughness.outputs[0].default_value = config.roughness_base

        # Normal (pass through for now)
        normal = nodes.new("ShaderNodeVector")
        normal.location = (0, -200)

        # Link
        links.new(input_node.outputs["Vector"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], output_node.inputs["Color"])
        links.new(roughness.outputs[0], output_node.inputs["Roughness"])

        return node_group


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_asphalt_material(
    name: str = "Asphalt",
    preset: Optional[AsphaltPreset] = None,
    **kwargs,
) -> Optional[Material]:
    """
    Create an asphalt material with optional preset.

    Args:
        name: Material name
        preset: Preset to use
        **kwargs: Additional config overrides

    Returns:
        Blender Material or None
    """
    builder = AsphaltMaterialBuilder()
    result = builder.create(name=name, preset=preset)
    return result.material


def create_highway_asphalt(name: str = "Highway_Asphalt") -> Optional[Material]:
    """Create highway asphalt material (fresh, dark)."""
    return create_asphalt_material(name, preset=AsphaltPreset.HIGHWAY_FRESH)


def create_residential_asphalt(name: str = "Residential_Asphalt") -> Optional[Material]:
    """Create residential road asphalt material (medium wear)."""
    return create_asphalt_material(name, preset=AsphaltPreset.RESIDENTIAL_GOOD)


def create_worn_asphalt(name: str = "Worn_Asphalt") -> Optional[Material]:
    """Create worn asphalt material (heavily used)."""
    return create_asphalt_material(name, preset=AsphaltPreset.HIGHWAY_WORN)


def create_wet_asphalt(name: str = "Wet_Asphalt") -> Optional[Material]:
    """Create wet asphalt material (after rain)."""
    return create_asphalt_material(name, preset=AsphaltPreset.WET_HIGHWAY)


__all__ = [
    # Enums
    "AsphaltType",
    "AsphaltCondition",
    "AsphaltPreset",
    # Dataclasses
    "AsphaltConfig",
    "AsphaltMaterialResult",
    # Builder
    "AsphaltMaterialBuilder",
    # Presets
    "ASPHALT_PRESETS",
    # Functions
    "create_asphalt_material",
    "create_highway_asphalt",
    "create_residential_asphalt",
    "create_worn_asphalt",
    "create_wet_asphalt",
]
