"""
PBR Materials & Visual Realism System

Creates comprehensive PBR materials for driving game with:
- Asphalt variants (fresh, worn, wet)
- Road markings (reflective paint)
- Weather effects (rain, puddles)
- Road wear (cracks, patches, oil stains)

Usage:
    from lib.materials_pbr import (
        create_asphalt_material,
        create_road_marking_material,
        create_weather_material,
        MaterialZone,
        WeatherCondition,
    )
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import math
import random

# Add lib to path for blender_gsd tools
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))

try:
    import bpy
    from mathutils import Vector, Color
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class MaterialZone(Enum):
    """Material zones stored as mesh attributes."""
    ROAD_SURFACE = 0
    CURB = 1
    ROAD_MARKING = 2
    CROSSWALK = 3
    SIDEWALK = 5
    TERRAIN = 10
    BUILDING = 20
    METAL = 30
    GLASS = 31
    VEGETATION = 40


class AsphaltType(Enum):
    """Asphalt condition types."""
    FRESH = "fresh"           # Dark, uniform, new
    NORMAL = "normal"         # Standard wear
    WORN = "worn"             # Lighter, cracked
    PATCHED = "patched"       # With repair patches
    AGED = "aged"             # Heavy wear, faded


class WeatherCondition(Enum):
    """Weather conditions for materials."""
    DRY = "dry"
    WET = "wet"
    RAINING = "raining"
    SNOW = "snow"
    FROZEN = "frozen"


class MarkingColor(Enum):
    """Road marking colors."""
    WHITE = "white"
    YELLOW = "yellow"
    RED = "red"               # Bus lanes, special zones
    BLUE = "blue"             # Handicap parking


@dataclass
class PBRMaterialParams:
    """PBR material parameters."""
    base_color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)
    roughness: float = 0.5
    metallic: float = 0.0
    specular: float = 0.5
    normal_strength: float = 1.0
    emission_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    emission_strength: float = 0.0
    alpha: float = 1.0


@dataclass
class AsphaltParams:
    """Asphalt-specific parameters."""
    condition: AsphaltType = AsphaltType.NORMAL
    crack_density: float = 0.3
    patch_coverage: float = 0.1
    oil_stain_intensity: float = 0.2
    color_variation: float = 0.1


@dataclass
class WeatherParams:
    """Weather effect parameters."""
    condition: WeatherCondition = WeatherCondition.DRY
    wetness: float = 0.0           # 0-1, how wet the surface is
    puddle_depth: float = 0.0      # Meters
    reflection_intensity: float = 0.0
    frost_coverage: float = 0.0


# =============================================================================
# MATERIAL DEFINITIONS
# =============================================================================

ASPHALT_DEFINITIONS = {
    AsphaltType.FRESH: PBRMaterialParams(
        base_color=(0.08, 0.08, 0.10, 1.0),
        roughness=0.85,
        specular=0.3,
    ),
    AsphaltType.NORMAL: PBRMaterialParams(
        base_color=(0.12, 0.12, 0.14, 1.0),
        roughness=0.9,
        specular=0.25,
    ),
    AsphaltType.WORN: PBRMaterialParams(
        base_color=(0.18, 0.18, 0.20, 1.0),
        roughness=0.95,
        specular=0.2,
    ),
    AsphaltType.PATCHED: PBRMaterialParams(
        base_color=(0.15, 0.15, 0.17, 1.0),
        roughness=0.88,
        specular=0.28,
    ),
    AsphaltType.AGED: PBRMaterialParams(
        base_color=(0.22, 0.22, 0.24, 1.0),
        roughness=0.95,
        specular=0.15,
    ),
}

MARKING_DEFINITIONS = {
    MarkingColor.WHITE: PBRMaterialParams(
        base_color=(0.95, 0.95, 0.95, 1.0),
        roughness=0.3,
        specular=0.8,
        emission_color=(0.3, 0.3, 0.3, 1.0),
        emission_strength=0.5,
    ),
    MarkingColor.YELLOW: PBRMaterialParams(
        base_color=(0.95, 0.80, 0.10, 1.0),
        roughness=0.35,
        specular=0.7,
        emission_color=(0.25, 0.20, 0.0, 1.0),
        emission_strength=0.4,
    ),
    MarkingColor.RED: PBRMaterialParams(
        base_color=(0.85, 0.15, 0.10, 1.0),
        roughness=0.4,
        specular=0.6,
    ),
    MarkingColor.BLUE: PBRMaterialParams(
        base_color=(0.15, 0.30, 0.85, 1.0),
        roughness=0.4,
        specular=0.6,
    ),
}


# =============================================================================
# ASPHALT MATERIAL CREATOR
# =============================================================================

def create_asphalt_material(
    name: str = "asphalt_road",
    asphalt_type: AsphaltType = AsphaltType.NORMAL,
    asphalt_params: Optional[AsphaltParams] = None,
    weather_params: Optional[WeatherParams] = None
) -> Optional[bpy.types.Material]:
    """
    Create a PBR asphalt material with optional wear and weather effects.

    Args:
        name: Material name
        asphalt_type: Type of asphalt condition
        asphalt_params: Asphalt-specific parameters
        weather_params: Weather effect parameters

    Returns:
        Created material or None
    """
    if not BLENDER_AVAILABLE:
        return None

    if asphalt_params is None:
        asphalt_params = AsphaltParams(condition=asphalt_type)

    if weather_params is None:
        weather_params = WeatherParams()

    # Get base parameters
    base_params = ASPHALT_DEFINITIONS.get(asphalt_type, ASPHALT_DEFINITIONS[AsphaltType.NORMAL])

    # Create or get material
    if name in bpy.data.materials:
        mat = bpy.data.materials[name]
    else:
        mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # ========================================
    # Build node tree
    # ========================================

    # Output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (1200, 0)

    # Mix shader for weather effects
    mix_shader = nodes.new("ShaderNodeMixShader")
    mix_shader.location = (1000, 0)

    # Base principled BSDF
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (600, 100)

    # Wet/glossy layer for weather
    wet_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    wet_bsdf.location = (600, -200)
    wet_bsdf.inputs["Roughness"].default_value = 0.05
    wet_bsdf.inputs["Specular IOR Level"].default_value = 0.9

    # ========================================
    # Texture coordinates and mapping
    # ========================================
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-400, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-200, 0)
    mapping.inputs["Scale"].default_value = (50.0, 50.0, 1.0)  # UV scale for road

    # ========================================
    # Noise for color variation
    # ========================================
    color_noise = nodes.new("ShaderNodeTexNoise")
    color_noise.location = (0, 200)
    color_noise.inputs["Scale"].default_value = 20.0
    color_noise.inputs["Detail"].default_value = 2
    color_noise.inputs["Distortion"].default_value = 0.5

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (200, 200)
    # Set ramp for subtle color variation
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp.color_ramp.elements[1].color = (0.05, 0.05, 0.05, 1.0)

    # Mix base color with noise
    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.location = (400, 100)
    color_mix.inputs["Color1"].default_value = base_params.base_color
    color_mix.inputs["Fac"].default_value = asphalt_params.color_variation

    # ========================================
    # Crack pattern
    # ========================================
    crack_noise = nodes.new("ShaderNodeTexNoise")
    crack_noise.location = (0, -100)
    crack_noise.inputs["Scale"].default_value = 100.0
    crack_noise.inputs["Detail"].default_value = 8
    crack_noise.inputs["Distortion"].default_value = 2.0

    # Normal map for cracks
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (400, -100)
    normal_map.inputs["Strength"].default_value = 0.3

    bump_node = nodes.new("ShaderNodeBump")
    bump_node.location = (200, -100)
    bump_node.inputs["Strength"].default_value = 0.1
    bump_node.inputs["Distance"].default_value = 0.01

    # ========================================
    # Roughness variation
    # ========================================
    roughness_noise = nodes.new("ShaderNodeTexNoise")
    roughness_noise.location = (0, 0)
    roughness_noise.inputs["Scale"].default_value = 10.0
    roughness_noise.inputs["Detail"].default_value = 1

    roughness_mix = nodes.new("ShaderNodeMix")
    roughness_mix.location = (200, 0)
    roughness_mix.data_type = "FLOAT"
    roughness_mix.inputs[0].default_value = 0.3
    roughness_mix.inputs[1].default_value = base_params.roughness - 0.1
    roughness_mix.inputs[2].default_value = base_params.roughness + 0.1

    # ========================================
    # Weather wetness layer
    # ========================================
    wet_mix = nodes.new("ShaderNodeMix")
    wet_mix.location = (800, -100)
    wet_mix.data_type = "FLOAT"
    wet_mix.inputs[0].default_value = weather_params.wetness

    # ========================================
    # Wire connections
    # ========================================
    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], color_noise.inputs["Vector"])
    links.new(mapping.outputs["Vector"], crack_noise.inputs["Vector"])
    links.new(mapping.outputs["Vector"], roughness_noise.inputs["Vector"])

    links.new(color_noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], color_mix.inputs["Color2"])
    links.new(color_mix.outputs["Color"], principled.inputs["Base Color"])

    links.new(crack_noise.outputs["Fac"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], normal_map.inputs["Normal"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])

    links.new(roughness_noise.outputs["Fac"], roughness_mix.inputs[0])
    links.new(roughness_mix.outputs[0], principled.inputs["Roughness"])

    # Base color for wet layer
    wet_bsdf.inputs["Base Color"].default_value = (
        base_params.base_color[0] * 0.6,
        base_params.base_color[1] * 0.6,
        base_params.base_color[2] * 0.6,
        1.0
    )

    # Weather mixing
    links.new(principled.outputs["BSDF"], mix_shader.inputs[1])
    links.new(wet_bsdf.outputs["BSDF"], mix_shader.inputs[2])
    links.new(wet_mix.outputs[0], mix_shader.inputs["Fac"])

    links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])

    # ========================================
    # Set material properties
    # ========================================
    mat["asphalt_type"] = asphalt_type.value
    mat["crack_density"] = asphalt_params.crack_density
    mat["weather_condition"] = weather_params.condition.value
    mat["wetness"] = weather_params.wetness

    return mat


def create_asphalt_material_variants(base_name: str = "asphalt") -> Dict[str, bpy.types.Material]:
    """
    Create all asphalt material variants.

    Returns:
        Dict of material name -> material
    """
    materials = {}

    # Create each condition type
    for asphalt_type in AsphaltType:
        name = f"{base_name}_{asphalt_type.value}"
        params = AsphaltParams(condition=asphalt_type)

        mat = create_asphalt_material(name, asphalt_type, params)
        if mat:
            materials[name] = mat
            print(f"  Created: {name}")

    # Create wet variants
    for asphalt_type in [AsphaltType.NORMAL, AsphaltType.WORN]:
        name = f"{base_name}_{asphalt_type.value}_wet"
        params = AsphaltParams(condition=asphalt_type)
        weather = WeatherParams(condition=WeatherCondition.WET, wetness=0.7)

        mat = create_asphalt_material(name, asphalt_type, params, weather)
        if mat:
            materials[name] = mat
            print(f"  Created: {name}")

    return materials


# =============================================================================
# ROAD MARKING MATERIAL CREATOR
# =============================================================================

def create_road_marking_material(
    color: MarkingColor = MarkingColor.WHITE,
    worn_amount: float = 0.0,
    retroreflective: bool = True
) -> Optional[bpy.types.Material]:
    """
    Create a road marking paint material.

    Args:
        color: Marking color
        worn_amount: How worn the paint is (0-1)
        retroreflective: Whether paint is reflective

    Returns:
        Created material or None
    """
    if not BLENDER_AVAILABLE:
        return None

    name = f"marking_{color.value}"
    if worn_amount > 0:
        name += f"_worn{int(worn_amount * 100)}"

    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Get base parameters
    params = MARKING_DEFINITIONS.get(color, MARKING_DEFINITIONS[MarkingColor.WHITE])

    # Adjust for wear
    base_color = params.base_color
    if worn_amount > 0:
        # Fade color towards asphalt
        fade = worn_amount * 0.5
        base_color = (
            base_color[0] * (1 - fade) + 0.15 * fade,
            base_color[1] * (1 - fade) + 0.15 * fade,
            base_color[2] * (1 - fade) + 0.15 * fade,
            1.0
        )

    # Output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    # Principled BSDF
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (400, 0)
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Roughness"].default_value = params.roughness
    principled.inputs["Specular IOR Level"].default_value = params.specular

    if retroreflective:
        principled.inputs["Emission Color"].default_value = params.emission_color
        principled.inputs["Emission Strength"].default_value = params.emission_strength

    # Add slight bump for paint thickness
    bump = nodes.new("ShaderNodeBump")
    bump.location = (200, -100)
    bump.inputs["Strength"].default_value = 0.05
    bump.inputs["Distance"].default_value = 0.002

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (0, -100)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (0, -200)
    noise.inputs["Scale"].default_value = 100.0

    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (400, -100)

    # Wire
    links.new(tex_coord.outputs["UV"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], normal_map.inputs["Normal"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # Store metadata
    mat["marking_color"] = color.value
    mat["worn_amount"] = worn_amount
    mat["retroreflective"] = retroreflective

    return mat


def create_all_marking_materials() -> Dict[str, bpy.types.Material]:
    """Create all road marking material variants."""
    materials = {}

    for color in MarkingColor:
        # Fresh paint
        mat = create_road_marking_material(color, worn_amount=0.0)
        if mat:
            materials[mat.name] = mat
            print(f"  Created: {mat.name}")

        # Worn variants
        for worn in [0.3, 0.6]:
            mat = create_road_marking_material(color, worn_amount=worn)
            if mat:
                materials[mat.name] = mat
                print(f"  Created: {mat.name}")

    return materials


# =============================================================================
# WEATHER EFFECT SYSTEM
# =============================================================================

def create_wet_road_material(
    base_material: bpy.types.Material,
    wetness: float = 0.7,
    puddle_mask: Optional[str] = None
) -> Optional[bpy.types.Material]:
    """
    Create wet road variant of an existing material.

    Args:
        base_material: Source asphalt material
        wetness: Wetness level (0-1)
        puddle_mask: Optional puddle mask texture name

    Returns:
        New wet variant material
    """
    if not BLENDER_AVAILABLE:
        return None

    name = f"{base_material.name}_wet"
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    # Copy base material
    mat = base_material.copy()
    mat.name = name

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Find principled BSDF
    principled = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            principled = node
            break

    if not principled:
        return mat

    # Darken base color for wet look
    base_color = principled.inputs["Base Color"].default_value
    wet_color = (
        base_color[0] * 0.6,
        base_color[1] * 0.6,
        base_color[2] * 0.6,
        base_color[3]
    )
    principled.inputs["Base Color"].default_value = wet_color

    # Reduce roughness for wet surface
    current_roughness = principled.inputs["Roughness"].default_value
    principled.inputs["Roughness"].default_value = max(0.05, current_roughness - 0.6 * wetness)

    # Increase specular for reflections
    principled.inputs["Specular IOR Level"].default_value = min(0.9, 0.5 + wetness * 0.4)

    # Add clearcoat for water layer effect
    if hasattr(principled.inputs, "Coat Weight"):
        principled.inputs["Coat Weight"].default_value = wetness * 0.5

    mat["wetness"] = wetness

    return mat


def create_puddle_material(
    depth: float = 0.01,
    ripple_scale: float = 50.0
) -> Optional[bpy.types.Material]:
    """
    Create a puddle material with water surface.

    Args:
        depth: Puddle depth in meters
        ripple_scale: Scale of water ripples

    Returns:
        Puddle material
    """
    if not BLENDER_AVAILABLE:
        return None

    name = "puddle_water"
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    # Glass BSDF for water
    glass = nodes.new("ShaderNodeBsdfGlass")
    glass.location = (400, 0)
    glass.inputs["Color"].default_value = (0.4, 0.45, 0.5, 1.0)
    glass.inputs["Roughness"].default_value = 0.02
    glass.inputs["IOR"].default_value = 1.33

    # Wave texture for ripples
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (0, -100)
    wave.inputs["Scale"].default_value = ripple_scale
    wave.inputs["Distortion"].default_value = 1.0
    wave.inputs["Detail"].default_value = 2

    # Normal map for ripples
    normal = nodes.new("ShaderNodeNormalMap")
    normal.location = (200, -100)
    normal.inputs["Strength"].default_value = 0.3

    bump = nodes.new("ShaderNodeBump")
    bump.location = (0, -200)
    bump.inputs["Strength"].default_value = 0.1

    # Texture coords
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-200, -100)

    # Wire
    links.new(tex_coord.outputs["UV"], wave.inputs["Vector"])
    links.new(wave.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], normal.inputs["Normal"])
    links.new(normal.outputs["Normal"], glass.inputs["Normal"])
    links.new(glass.outputs["BSDF"], output.inputs["Surface"])

    mat["depth"] = depth
    mat["ripple_scale"] = ripple_scale

    return mat


# =============================================================================
# ROAD WEAR SYSTEM
# =============================================================================

def add_crack_pattern_to_material(
    material: bpy.types.Material,
    crack_density: float = 0.3,
    crack_depth: float = 0.005
) -> bpy.types.Material:
    """
    Add crack pattern to existing asphalt material.

    Args:
        material: Material to modify
        crack_density: How many cracks (0-1)
        crack_depth: Depth of cracks in meters

    Returns:
        Modified material
    """
    if not BLENDER_AVAILABLE or not material.use_nodes:
        return material

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Find existing normal map or add one
    normal_map = None
    principled = None

    for node in nodes:
        if node.type == 'NORMAL_MAP':
            normal_map = node
        elif node.type == 'BSDF_PRINCIPLED':
            principled = node

    if not principled:
        return material

    # Add crack texture
    crack_noise = nodes.new("ShaderNodeTexNoise")
    crack_noise.location = (-200, -300)
    crack_noise.inputs["Scale"].default_value = 150.0
    crack_noise.inputs["Detail"].default_value = 10
    crack_noise.inputs["Distortion"].default_value = 3.0

    # Voronoi for crack edges
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.location = (0, -300)
    voronoi.inputs["Scale"].default_value = 80.0

    # Mix cracks
    crack_mix = nodes.new("ShaderNodeMix")
    crack_mix.location = (200, -300)
    crack_mix.data_type = "FLOAT"
    crack_mix.inputs[0].default_value = crack_density

    # Bump for crack depth
    crack_bump = nodes.new("ShaderNodeBump")
    crack_bump.location = (400, -300)
    crack_bump.inputs["Strength"].default_value = crack_depth * 20

    # Add new normal map if needed
    if not normal_map:
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (600, -200)

    # Wire
    links.new(crack_noise.outputs["Fac"], crack_mix.inputs[1])
    links.new(voronoi.outputs["Distance"], crack_mix.inputs[2])
    links.new(crack_mix.outputs[0], crack_bump.inputs["Height"])
    links.new(crack_bump.outputs["Normal"], normal_map.inputs["Normal"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])

    material["crack_density"] = crack_density
    material["crack_depth"] = crack_depth

    return material


def add_patch_overlay_to_material(
    material: bpy.types.Material,
    patch_coverage: float = 0.2,
    patch_color_variance: float = 0.1
) -> bpy.types.Material:
    """
    Add repair patches to asphalt material.

    Args:
        material: Material to modify
        patch_coverage: How much area is patched (0-1)
        patch_color_variance: Color difference from base

    Returns:
        Modified material
    """
    if not BLENDER_AVAILABLE or not material.use_nodes:
        return material

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Find principled BSDF
    principled = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            principled = node
            break

    if not principled:
        return material

    # Add patch mask
    patch_voronoi = nodes.new("ShaderNodeTexVoronoi")
    patch_voronoi.location = (-400, 200)
    patch_voronoi.inputs["Scale"].default_value = 5.0
    patch_voronoi.inputs["Randomness"].default_value = 0.8

    # Threshold for patch locations
    threshold = 1.0 - patch_coverage
    math_node = nodes.new("ShaderNodeMath")
    math_node.location = (-200, 200)
    math_node.operation = 'GREATER_THAN'
    math_node.inputs[1].default_value = threshold

    # Patch color (slightly different asphalt)
    patch_color = nodes.new("ShaderNodeRGB")
    patch_color.location = (-200, 100)
    patch_color.outputs[0].default_value = (0.10, 0.10, 0.12, 1.0)

    # Mix base color with patch
    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.location = (0, 200)

    # Get current base color
    base_color_socket = principled.inputs["Base Color"]

    # Store original links
    base_color_links = list(base_color_socket.links)

    # Wire
    links.new(patch_voronoi.outputs["Distance"], math_node.inputs[0])
    links.new(math_node.outputs[0], color_mix.inputs["Fac"])
    links.new(patch_color.outputs[0], color_mix.inputs["Color1"])

    # Reconnect existing color
    if base_color_links:
        links.new(base_color_links[0].from_socket, color_mix.inputs["Color2"])
    else:
        color_mix.inputs["Color2"].default_value = base_color_socket.default_value

    links.new(color_mix.outputs["Color"], base_color_socket)

    material["patch_coverage"] = patch_coverage

    return material


# =============================================================================
# MATERIAL ZONE ASSIGNMENT
# =============================================================================

def assign_materials_by_zone(
    objects: List[bpy.types.Object],
    material_map: Dict[int, bpy.types.Material]
) -> Dict[str, int]:
    """
    Assign materials to objects based on their material_zone attribute.

    Args:
        objects: Objects to process
        material_map: Dict of zone ID -> material

    Returns:
        Stats dict with assignment counts
    """
    if not BLENDER_AVAILABLE:
        return {}

    stats = {
        'assigned': 0,
        'skipped': 0,
        'errors': 0,
    }

    for obj in objects:
        try:
            zone = obj.get('material_zone', None)

            if zone is None:
                stats['skipped'] += 1
                continue

            material = material_map.get(zone)
            if material:
                # Clear existing materials
                obj.data.materials.clear()
                obj.data.materials.append(material)
                stats['assigned'] += 1
            else:
                stats['skipped'] += 1

        except Exception as e:
            stats['errors'] += 1

    return stats


def create_material_zone_map() -> Dict[int, bpy.types.Material]:
    """
    Create mapping from material zones to materials.

    Returns:
        Dict mapping zone ID to material
    """
    zone_map = {}

    # Road surface
    zone_map[MaterialZone.ROAD_SURFACE.value] = create_asphalt_material(
        "asphalt_road", AsphaltType.NORMAL
    )

    # Curb
    zone_map[MaterialZone.CURB.value] = create_concrete_material("concrete_curb")

    # Road markings
    zone_map[MaterialZone.ROAD_MARKING.value] = create_road_marking_material(
        MarkingColor.WHITE
    )

    # Crosswalk
    zone_map[MaterialZone.CROSSWALK.value] = create_road_marking_material(
        MarkingColor.WHITE, worn_amount=0.2
    )

    # Sidewalk
    zone_map[MaterialZone.SIDEWALK.value] = create_concrete_material(
        "sidewalk_concrete", roughness=0.85
    )

    # Terrain
    zone_map[MaterialZone.TERRAIN.value] = create_grass_material("terrain_grass")

    return zone_map


# =============================================================================
# HELPER MATERIALS
# =============================================================================

def create_concrete_material(
    name: str = "concrete",
    color: Tuple[float, float, float, float] = (0.6, 0.58, 0.55, 1.0),
    roughness: float = 0.85
) -> Optional[bpy.types.Material]:
    """Create a basic concrete material."""
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness

    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    return mat


def create_grass_material(name: str = "grass") -> Optional[bpy.types.Material]:
    """Create a grass/terrain material."""
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (200, 0)
    principled.inputs["Base Color"].default_value = (0.2, 0.4, 0.15, 1.0)
    principled.inputs["Roughness"].default_value = 0.95
    principled.inputs["Specular IOR Level"].default_value = 0.1

    # Add variation
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (0, 100)
    noise.inputs["Scale"].default_value = 20.0

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (0, -100)
    color_ramp.color_ramp.elements[0].color = (0.15, 0.35, 0.10, 1.0)
    color_ramp.color_ramp.elements[1].color = (0.25, 0.45, 0.18, 1.0)

    mix = nodes.new("ShaderNodeMixRGB")
    mix.location = (0, 0)
    mix.inputs["Fac"].default_value = 0.5

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-200, 0)

    links.new(tex_coord.outputs["UV"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    return mat


# =============================================================================
# MAIN
# =============================================================================

def create_all_pbr_materials() -> Dict[str, bpy.types.Material]:
    """Create all PBR materials for the driving game."""
    print("\n=== Creating PBR Materials ===")

    materials = {}

    # Asphalt variants
    print("\nAsphalt materials:")
    materials.update(create_asphalt_material_variants())

    # Road markings
    print("\nRoad marking materials:")
    materials.update(create_all_marking_materials())

    # Helper materials
    print("\nHelper materials:")
    concrete = create_concrete_material()
    if concrete:
        materials[concrete.name] = concrete
        print(f"  Created: {concrete.name}")

    grass = create_grass_material()
    if grass:
        materials[grass.name] = grass
        print(f"  Created: {grass.name}")

    # Weather materials
    print("\nWeather materials:")
    puddle = create_puddle_material()
    if puddle:
        materials[puddle.name] = puddle
        print(f"  Created: {puddle.name}")

    print(f"\nTotal materials created: {len(materials)}")

    return materials


if __name__ == '__main__':
    create_all_pbr_materials()
