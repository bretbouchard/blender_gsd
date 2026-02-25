"""
Charlotte Digital Twin - Building Materials System

Creates comprehensive PBR materials for Charlotte buildings based on
actual architectural styles and materials used in Uptown Charlotte.

Architecture Research Summary:
=============================
1. MODERN GLASS TOWERS (1990s-2020s)
   - Bank of America Corporate Center: Postmodern, glass curtain wall, César Pelli
   - 550 South Tryon: Contemporary, glass curtain wall with LED integration
   - Truist Center: Modern, glass and steel, SOM design
   - Duke Energy Plaza: Contemporary sustainable, glass with daylight louvers

2. POSTMODERN GRANITE/GLASS (1980s-1990s)
   - 301 South College: Granite and glass facade
   - Two/Three Wells Fargo Center: Granite cladding
   - Charlotte Plaza: Granite and glass

3. HISTORIC/LOW-RISE (Pre-1970s)
   - 112 Tryon Plaza: Historic limestone/terracotta (1927)
   - Johnston Building: Historic stone/brick (1924)
   - 200 South Tryon: Early modern (1961)

4. RESIDENTIAL TOWERS (2000s-2020s)
   - The Vue, Catalyst, Ascent: Glass curtain wall, balconies
   - Museum Tower: Glass and precast concrete panels

5. HOTELS
   - Westin, Ritz-Carlton: Glass curtain wall
   - Marriott: Granite/glass combination

Material Categories:
===================
- GLASS_CURTAIN_WALL: Blue/clear tinted glass, metal mullions
- GRANITE_CLADDING: Polished/honed granite panels
- LIMESTONE_FACADE: Natural limestone, cream/gray tones
- PRECAST_CONCRETE: Architectural concrete panels
- BRICK_VENEER: Traditional brick facades
- METAL_PANEL: Aluminum composite panels (ACP)
- TERRACOTTA: Historic glazed terracotta tiles
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass
import random

try:
    import bpy
    from mathutils import Vector, Color
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class BuildingMaterialType(Enum):
    """Building facade material types."""
    # Modern Glass
    GLASS_CURTAIN_BLUE = "glass_curtain_blue"
    GLASS_CURTAIN_CLEAR = "glass_curtain_clear"
    GLASS_CURTAIN_GREEN = "glass_curtain_green"
    GLASS_CURTAIN_MIRRORED = "glass_curtain_mirrored"

    # Stone
    GRANITE_POLISHED = "granite_polished"
    GRANITE_HONED = "granite_honed"
    LIMESTONE_NATURAL = "limestone_natural"
    LIMESTONE_POLISHED = "limestone_polished"
    MARBLE_WHITE = "marble_white"
    SANDSTONE = "sandstone"

    # Concrete/Masonry
    PRECAST_CONCRETE_SMOOTH = "precast_concrete_smooth"
    PRECAST_CONCRETE_TEXTURED = "precast_concrete_textured"
    CONCRETE_EXPOSED_AGGREGATE = "concrete_exposed_aggregate"
    BRICK_RED = "brick_red"
    BRICK_BROWN = "brick_brown"
    BRICK_TAN = "brick_tan"

    # Metal
    METAL_PANEL_ALUMINUM = "metal_panel_aluminum"
    METAL_PANEL_BRONZE = "metal_panel_bronze"
    METAL_PANEL_COPPER = "metal_panel_copper"
    METAL_MULLION_CHROME = "metal_mullion_chrome"
    METAL_MULLION_BRONZE = "metal_mullion_bronze"

    # Historic
    TERRACOTTA_GLAZED = "terracotta_glazed"
    TERRACOTTA_NATURAL = "terracotta_natural"

    # Mixed/Composite
    GLASS_GRANITE_COMBO = "glass_granite_combo"
    GLASS_CONCRETE_COMBO = "glass_concrete_combo"


class BuildingEra(Enum):
    """Architectural era categories."""
    HISTORIC = "historic"          # Pre-1950
    MID_CENTURY = "mid_century"    # 1950-1970
    POSTMODERN = "postmodern"      # 1970-1995
    MODERN = "modern"              # 1995-2010
    CONTEMPORARY = "contemporary"  # 2010-present


class BuildingUse(Enum):
    """Building use categories."""
    OFFICE_TOWER = "office_tower"
    RESIDENTIAL_TOWER = "residential_tower"
    HOTEL = "hotel"
    RETAIL = "retail"
    PARKING = "parking"
    GOVERNMENT = "government"
    MIXED_USE = "mixed_use"


@dataclass
class BuildingMaterialParams:
    """PBR material parameters for building facades."""
    base_color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)
    roughness: float = 0.5
    metallic: float = 0.0
    specular: float = 0.5
    alpha: float = 1.0
    ior: float = 1.5
    transmission: float = 0.0  # For glass
    coating: float = 0.0
    anisotropic: float = 0.0
    normal_strength: float = 1.0
    detail_scale: float = 1.0
    color_variation: float = 0.1
    description: str = ""


# =============================================================================
# MATERIAL DEFINITIONS - Based on Charlotte Architecture Research
# =============================================================================

BUILDING_MATERIAL_DEFINITIONS: Dict[BuildingMaterialType, BuildingMaterialParams] = {
    # =========================================================================
    # GLASS CURTAIN WALL - Modern Towers
    # =========================================================================

    # Blue tinted glass - BOA Corporate Center style
    BuildingMaterialType.GLASS_CURTAIN_BLUE: BuildingMaterialParams(
        base_color=(0.15, 0.25, 0.35, 0.85),
        roughness=0.02,
        metallic=0.1,
        specular=0.9,
        alpha=0.85,
        ior=1.52,
        transmission=0.7,
        coating=0.3,
        detail_scale=2.0,
        description="Blue tinted glass curtain wall - modern office towers",
    ),

    # Clear glass - Contemporary towers
    BuildingMaterialType.GLASS_CURTAIN_CLEAR: BuildingMaterialParams(
        base_color=(0.75, 0.80, 0.85, 0.80),
        roughness=0.01,
        metallic=0.05,
        specular=0.95,
        alpha=0.80,
        ior=1.50,
        transmission=0.85,
        coating=0.2,
        detail_scale=2.0,
        description="Clear glass curtain wall - contemporary design",
    ),

    # Green tinted glass - Some 2000s towers
    BuildingMaterialType.GLASS_CURTAIN_GREEN: BuildingMaterialParams(
        base_color=(0.20, 0.35, 0.30, 0.85),
        roughness=0.02,
        metallic=0.1,
        specular=0.85,
        alpha=0.85,
        ior=1.52,
        transmission=0.65,
        coating=0.25,
        detail_scale=2.0,
        description="Green tinted glass - sustainable design era",
    ),

    # Mirrored/reflective glass - 1980s style
    BuildingMaterialType.GLASS_CURTAIN_MIRRORED: BuildingMaterialParams(
        base_color=(0.30, 0.35, 0.40, 0.95),
        roughness=0.01,
        metallic=0.8,
        specular=1.0,
        alpha=0.95,
        ior=1.52,
        transmission=0.1,
        coating=0.5,
        detail_scale=2.0,
        description="Mirrored glass - 1980s postmodern style",
    ),

    # =========================================================================
    # GRANITE - Postmodern Office Towers
    # =========================================================================

    # Polished black/gray granite - Wells Fargo style
    BuildingMaterialType.GRANITE_POLISHED: BuildingMaterialParams(
        base_color=(0.25, 0.25, 0.27, 1.0),
        roughness=0.15,
        metallic=0.0,
        specular=0.7,
        detail_scale=4.0,
        color_variation=0.15,
        description="Polished granite - Wells Fargo towers style",
    ),

    # Honed granite - matte finish
    BuildingMaterialType.GRANITE_HONED: BuildingMaterialParams(
        base_color=(0.35, 0.33, 0.32, 1.0),
        roughness=0.4,
        metallic=0.0,
        specular=0.4,
        detail_scale=4.0,
        color_variation=0.2,
        description="Honed granite - matte institutional look",
    ),

    # =========================================================================
    # LIMESTONE - Historic Buildings
    # =========================================================================

    # Natural limestone - 112 Tryon Plaza style
    BuildingMaterialType.LIMESTONE_NATURAL: BuildingMaterialParams(
        base_color=(0.85, 0.82, 0.75, 1.0),
        roughness=0.7,
        metallic=0.0,
        specular=0.25,
        detail_scale=3.0,
        color_variation=0.25,
        description="Natural limestone - historic 1920s buildings",
    ),

    # Polished limestone - refined look
    BuildingMaterialType.LIMESTONE_POLISHED: BuildingMaterialParams(
        base_color=(0.90, 0.88, 0.82, 1.0),
        roughness=0.3,
        metallic=0.0,
        specular=0.5,
        detail_scale=3.0,
        color_variation=0.15,
        description="Polished limestone - refined institutional",
    ),

    # =========================================================================
    # CONCRETE/PRECAST - Modern Construction
    # =========================================================================

    # Smooth precast concrete panels
    BuildingMaterialType.PRECAST_CONCRETE_SMOOTH: BuildingMaterialParams(
        base_color=(0.70, 0.68, 0.65, 1.0),
        roughness=0.6,
        metallic=0.0,
        specular=0.3,
        detail_scale=5.0,
        color_variation=0.1,
        description="Smooth precast concrete panels",
    ),

    # Textured precast - Museum Tower style
    BuildingMaterialType.PRECAST_CONCRETE_TEXTURED: BuildingMaterialParams(
        base_color=(0.65, 0.63, 0.60, 1.0),
        roughness=0.8,
        metallic=0.0,
        specular=0.25,
        detail_scale=4.0,
        color_variation=0.2,
        normal_strength=1.5,
        description="Textured architectural concrete",
    ),

    # Exposed aggregate concrete
    BuildingMaterialType.CONCRETE_EXPOSED_AGGREGATE: BuildingMaterialParams(
        base_color=(0.55, 0.52, 0.50, 1.0),
        roughness=0.9,
        metallic=0.0,
        specular=0.2,
        detail_scale=2.0,
        color_variation=0.3,
        normal_strength=2.0,
        description="Exposed aggregate concrete finish",
    ),

    # =========================================================================
    # BRICK - Traditional Buildings
    # =========================================================================

    # Red brick
    BuildingMaterialType.BRICK_RED: BuildingMaterialParams(
        base_color=(0.65, 0.35, 0.30, 1.0),
        roughness=0.85,
        metallic=0.0,
        specular=0.15,
        detail_scale=1.0,
        color_variation=0.3,
        normal_strength=2.0,
        description="Traditional red brick",
    ),

    # Brown brick
    BuildingMaterialType.BRICK_BROWN: BuildingMaterialParams(
        base_color=(0.50, 0.35, 0.28, 1.0),
        roughness=0.85,
        metallic=0.0,
        specular=0.15,
        detail_scale=1.0,
        color_variation=0.3,
        normal_strength=2.0,
        description="Brown brick veneer",
    ),

    # Tan/cream brick
    BuildingMaterialType.BRICK_TAN: BuildingMaterialParams(
        base_color=(0.75, 0.68, 0.55, 1.0),
        roughness=0.8,
        metallic=0.0,
        specular=0.2,
        detail_scale=1.0,
        color_variation=0.25,
        normal_strength=2.0,
        description="Tan/cream brick",
    ),

    # =========================================================================
    # METAL PANELS - Contemporary Construction
    # =========================================================================

    # Aluminum composite panels
    BuildingMaterialType.METAL_PANEL_ALUMINUM: BuildingMaterialParams(
        base_color=(0.75, 0.77, 0.80, 1.0),
        roughness=0.25,
        metallic=0.9,
        specular=0.8,
        detail_scale=6.0,
        color_variation=0.05,
        description="Aluminum composite panels",
    ),

    # Bronze metallic panels
    BuildingMaterialType.METAL_PANEL_BRONZE: BuildingMaterialParams(
        base_color=(0.55, 0.40, 0.25, 1.0),
        roughness=0.3,
        metallic=0.95,
        specular=0.75,
        detail_scale=6.0,
        color_variation=0.1,
        description="Bronze metallic panels",
    ),

    # Copper panels (patina)
    BuildingMaterialType.METAL_PANEL_COPPER: BuildingMaterialParams(
        base_color=(0.40, 0.55, 0.50, 1.0),
        roughness=0.4,
        metallic=0.9,
        specular=0.6,
        detail_scale=6.0,
        color_variation=0.15,
        description="Copper panels with patina",
    ),

    # Chrome mullions
    BuildingMaterialType.METAL_MULLION_CHROME: BuildingMaterialParams(
        base_color=(0.80, 0.82, 0.85, 1.0),
        roughness=0.1,
        metallic=1.0,
        specular=0.95,
        detail_scale=1.0,
        color_variation=0.02,
        description="Chrome window mullions",
    ),

    # Bronze mullions
    BuildingMaterialType.METAL_MULLION_BRONZE: BuildingMaterialParams(
        base_color=(0.60, 0.50, 0.35, 1.0),
        roughness=0.2,
        metallic=0.95,
        specular=0.8,
        detail_scale=1.0,
        color_variation=0.05,
        description="Bronze window mullions",
    ),

    # =========================================================================
    # TERRACOTTA - Historic Buildings
    # =========================================================================

    # Glazed terracotta - Art Deco style
    BuildingMaterialType.TERRACOTTA_GLAZED: BuildingMaterialParams(
        base_color=(0.85, 0.80, 0.72, 1.0),
        roughness=0.2,
        metallic=0.0,
        specular=0.6,
        detail_scale=2.0,
        color_variation=0.1,
        description="Glazed terracotta - Art Deco buildings",
    ),

    # Natural terracotta
    BuildingMaterialType.TERRACOTTA_NATURAL: BuildingMaterialParams(
        base_color=(0.80, 0.60, 0.45, 1.0),
        roughness=0.7,
        metallic=0.0,
        specular=0.25,
        detail_scale=2.0,
        color_variation=0.2,
        description="Natural terracotta",
    ),

    # =========================================================================
    # STONE - Other
    # =========================================================================

    # White marble
    BuildingMaterialType.MARBLE_WHITE: BuildingMaterialParams(
        base_color=(0.92, 0.90, 0.88, 1.0),
        roughness=0.2,
        metallic=0.0,
        specular=0.7,
        detail_scale=3.0,
        color_variation=0.15,
        description="White marble",
    ),

    # Sandstone
    BuildingMaterialType.SANDSTONE: BuildingMaterialParams(
        base_color=(0.75, 0.65, 0.50, 1.0),
        roughness=0.75,
        metallic=0.0,
        specular=0.2,
        detail_scale=2.0,
        color_variation=0.25,
        normal_strength=1.5,
        description="Sandstone facade",
    ),
}


# =============================================================================
# BUILDING STYLE DEFINITIONS
# =============================================================================

@dataclass
class BuildingStyle:
    """Complete material style for a building."""
    name: str
    era: BuildingEra
    use: BuildingUse
    primary_material: BuildingMaterialType
    secondary_material: Optional[BuildingMaterialType]
    window_material: BuildingMaterialType
    mullion_material: BuildingMaterialType
    base_material: Optional[BuildingMaterialType] = None  # Ground floor
    accent_material: Optional[BuildingMaterialType] = None
    description: str = ""


# Pre-defined building styles based on Charlotte architecture
CHARLOTTE_BUILDING_STYLES: Dict[str, BuildingStyle] = {
    # =========================================================================
    # MODERN GLASS TOWERS (Major Skyscrapers)
    # =========================================================================

    "modern_glass_tower": BuildingStyle(
        name="Modern Glass Tower",
        era=BuildingEra.MODERN,
        use=BuildingUse.OFFICE_TOWER,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        secondary_material=BuildingMaterialType.GRANITE_POLISHED,
        window_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        base_material=BuildingMaterialType.GRANITE_POLISHED,
        description="Bank of America Corporate Center style - blue glass with granite base",
    ),

    "contemporary_glass_tower": BuildingStyle(
        name="Contemporary Glass Tower",
        era=BuildingEra.CONTEMPORARY,
        use=BuildingUse.OFFICE_TOWER,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        secondary_material=BuildingMaterialType.METAL_PANEL_ALUMINUM,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        description="Duke Energy Plaza style - clear glass with metal accents",
    ),

    "sustainable_tower": BuildingStyle(
        name="Sustainable Tower",
        era=BuildingEra.CONTEMPORARY,
        use=BuildingUse.OFFICE_TOWER,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_GREEN,
        secondary_material=BuildingMaterialType.PRECAST_CONCRETE_SMOOTH,
        window_material=BuildingMaterialType.GLASS_CURTAIN_GREEN,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        description="LEED-certified style - green glass with concrete",
    ),

    # =========================================================================
    # POSTMODERN GRANITE/GLASS
    # =========================================================================

    "postmodern_granite_office": BuildingStyle(
        name="Postmodern Granite Office",
        era=BuildingEra.POSTMODERN,
        use=BuildingUse.OFFICE_TOWER,
        primary_material=BuildingMaterialType.GRANITE_POLISHED,
        secondary_material=BuildingMaterialType.GLASS_CURTAIN_MIRRORED,
        window_material=BuildingMaterialType.GLASS_CURTAIN_MIRRORED,
        mullion_material=BuildingMaterialType.METAL_MULLION_BRONZE,
        description="Wells Fargo Center style - polished granite with mirrored glass",
    ),

    "postmodern_mixed": BuildingStyle(
        name="Postmodern Mixed Facade",
        era=BuildingEra.POSTMODERN,
        use=BuildingUse.MIXED_USE,
        primary_material=BuildingMaterialType.GRANITE_HONED,
        secondary_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        window_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        mullion_material=BuildingMaterialType.METAL_MULLION_BRONZE,
        description="Charlotte Plaza style - granite and glass combination",
    ),

    # =========================================================================
    # RESIDENTIAL TOWERS
    # =========================================================================

    "modern_residential_tower": BuildingStyle(
        name="Modern Residential Tower",
        era=BuildingEra.MODERN,
        use=BuildingUse.RESIDENTIAL_TOWER,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        secondary_material=BuildingMaterialType.PRECAST_CONCRETE_SMOOTH,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        base_material=BuildingMaterialType.PRECAST_CONCRETE_TEXTURED,
        description="The Vue style - glass curtain wall with balconies",
    ),

    "contemporary_residential": BuildingStyle(
        name="Contemporary Residential",
        era=BuildingEra.CONTEMPORARY,
        use=BuildingUse.RESIDENTIAL_TOWER,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        secondary_material=BuildingMaterialType.METAL_PANEL_ALUMINUM,
        window_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        description="Museum Tower style - glass with metal panel accents",
    ),

    # =========================================================================
    # HOTELS
    # =========================================================================

    "luxury_hotel_glass": BuildingStyle(
        name="Luxury Hotel Glass",
        era=BuildingEra.MODERN,
        use=BuildingUse.HOTEL,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        secondary_material=BuildingMaterialType.GRANITE_POLISHED,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        base_material=BuildingMaterialType.MARBLE_WHITE,
        description="Ritz-Carlton style - clear glass with marble base",
    ),

    "business_hotel": BuildingStyle(
        name="Business Hotel",
        era=BuildingEra.POSTMODERN,
        use=BuildingUse.HOTEL,
        primary_material=BuildingMaterialType.GRANITE_HONED,
        secondary_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        window_material=BuildingMaterialType.GLASS_CURTAIN_BLUE,
        mullion_material=BuildingMaterialType.METAL_MULLION_BRONZE,
        description="Marriott style - granite with blue glass",
    ),

    # =========================================================================
    # HISTORIC BUILDINGS
    # =========================================================================

    "historic_limestone": BuildingStyle(
        name="Historic Limestone",
        era=BuildingEra.HISTORIC,
        use=BuildingUse.OFFICE_TOWER,
        primary_material=BuildingMaterialType.LIMESTONE_NATURAL,
        secondary_material=BuildingMaterialType.TERRACOTTA_GLAZED,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_BRONZE,
        description="112 Tryon Plaza style - 1920s limestone",
    ),

    "historic_brick": BuildingStyle(
        name="Historic Brick",
        era=BuildingEra.HISTORIC,
        use=BuildingUse.RETAIL,
        primary_material=BuildingMaterialType.BRICK_RED,
        secondary_material=BuildingMaterialType.TERRACOTTA_NATURAL,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_BRONZE,
        description="Traditional brick storefront",
    ),

    # =========================================================================
    # MID-CENTURY
    # =========================================================================

    "mid_century_modern": BuildingStyle(
        name="Mid-Century Modern",
        era=BuildingEra.MID_CENTURY,
        use=BuildingUse.OFFICE_TOWER,
        primary_material=BuildingMaterialType.GLASS_CURTAIN_MIRRORED,
        secondary_material=BuildingMaterialType.CONCRETE_EXPOSED_AGGREGATE,
        window_material=BuildingMaterialType.GLASS_CURTAIN_MIRRORED,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        description="200 South Tryon style - 1960s mirrored glass",
    ),

    # =========================================================================
    # PARKING STRUCTURES
    # =========================================================================

    "parking_structure": BuildingStyle(
        name="Parking Structure",
        era=BuildingEra.MODERN,
        use=BuildingUse.PARKING,
        primary_material=BuildingMaterialType.PRECAST_CONCRETE_TEXTURED,
        secondary_material=BuildingMaterialType.METAL_PANEL_ALUMINUM,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_CHROME,
        description="Precast concrete parking structure",
    ),

    # =========================================================================
    # GOVERNMENT/INSTITUTIONAL
    # =========================================================================

    "government_building": BuildingStyle(
        name="Government Building",
        era=BuildingEra.POSTMODERN,
        use=BuildingUse.GOVERNMENT,
        primary_material=BuildingMaterialType.GRANITE_HONED,
        secondary_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        window_material=BuildingMaterialType.GLASS_CURTAIN_CLEAR,
        mullion_material=BuildingMaterialType.METAL_MULLION_BRONZE,
        description="Government center style - honed granite",
    ),
}


# =============================================================================
# MATERIAL CREATION FUNCTIONS
# =============================================================================

def create_building_material(
    material_type: BuildingMaterialType,
    name: Optional[str] = None
) -> Optional[bpy.types.Material]:
    """
    Create a PBR building facade material.

    Args:
        material_type: Type of building material
        name: Optional custom name

    Returns:
        Created material or None
    """
    if not BLENDER_AVAILABLE:
        return None

    params = BUILDING_MATERIAL_DEFINITIONS.get(material_type)
    if not params:
        print(f"Warning: Unknown material type {material_type}")
        return None

    mat_name = name or f"building_{material_type.value}"

    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (1200, 0)

    # Main principled BSDF
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (800, 0)

    # Set base parameters
    principled.inputs["Base Color"].default_value = params.base_color
    principled.inputs["Roughness"].default_value = params.roughness
    principled.inputs["Metallic"].default_value = params.metallic
    principled.inputs["Specular IOR Level"].default_value = params.specular

    # Glass-specific settings
    if params.transmission > 0:
        principled.inputs["Transmission Weight"].default_value = params.transmission
        principled.inputs["IOR"].default_value = params.ior

    # Coating for polished surfaces
    if params.coating > 0:
        if hasattr(principled.inputs, "Coat Weight"):
            principled.inputs["Coat Weight"].default_value = params.coating

    # ========================================
    # Add procedural variation
    # ========================================

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-400, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-200, 0)
    mapping.inputs["Scale"].default_value = (params.detail_scale, params.detail_scale, 1.0)

    # Noise for color variation
    color_noise = nodes.new("ShaderNodeTexNoise")
    color_noise.location = (0, 200)
    color_noise.inputs["Scale"].default_value = 10.0
    color_noise.inputs["Detail"].default_value = 2

    # Color ramp for variation
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (200, 200)
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp.color_ramp.elements[1].color = (params.color_variation,
                                                params.color_variation,
                                                params.color_variation, 1.0)

    # Mix base color with variation
    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.location = (400, 100)
    color_mix.inputs["Color1"].default_value = params.base_color
    color_mix.inputs["Fac"].default_value = 0.3

    # Normal variation
    normal_noise = nodes.new("ShaderNodeTexNoise")
    normal_noise.location = (0, -100)
    normal_noise.inputs["Scale"].default_value = 50.0
    normal_noise.inputs["Detail"].default_value = 4

    bump = nodes.new("ShaderNodeBump")
    bump.location = (200, -100)
    bump.inputs["Strength"].default_value = 0.05 * params.normal_strength
    bump.inputs["Distance"].default_value = 0.01

    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (400, -100)
    normal_map.inputs["Strength"].default_value = params.normal_strength * 0.3

    # Wire connections
    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], color_noise.inputs["Vector"])
    links.new(mapping.outputs["Vector"], normal_noise.inputs["Vector"])

    links.new(color_noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], color_mix.inputs["Color2"])
    links.new(color_mix.outputs["Color"], principled.inputs["Base Color"])

    links.new(normal_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], normal_map.inputs["Normal"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])

    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # Store metadata
    mat["material_type"] = material_type.value
    mat["description"] = params.description

    return mat


def create_all_building_materials() -> Dict[str, bpy.types.Material]:
    """Create all building materials."""
    materials = {}

    print("\n=== Creating Building Materials ===")

    for mat_type in BuildingMaterialType:
        mat = create_building_material(mat_type)
        if mat:
            materials[mat.name] = mat
            print(f"  Created: {mat.name}")

    print(f"\nTotal building materials: {len(materials)}")

    return materials


# =============================================================================
# STYLE ASSIGNMENT FUNCTIONS
# =============================================================================

def get_style_for_building(
    building_name: str,
    height: float,
    building_type: str = "office",
    year_built: int = 2000
) -> BuildingStyle:
    """
    Determine the appropriate style for a building.

    Args:
        building_name: Name of the building
        height: Building height in meters
        building_type: Type of building (office, residential, hotel, etc.)
        use: Building use category
        year_built: Year of construction

    Returns:
        Appropriate BuildingStyle
    """
    # Named building mappings
    name_lower = building_name.lower()

    # Major skyscrapers - specific styles
    if "bank of america" in name_lower and "corporate" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["modern_glass_tower"]

    if "550 south tryon" in name_lower or "duke energy center" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["contemporary_glass_tower"]

    if "duke energy plaza" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["sustainable_tower"]

    if "truist" in name_lower or "hearst tower" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["modern_glass_tower"]

    if "vue" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["modern_residential_tower"]

    if "wells fargo" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["postmodern_granite_office"]

    if "museum tower" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["contemporary_residential"]

    if "ritz" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["luxury_hotel_glass"]

    if "westin" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["luxury_hotel_glass"]

    if "marriott" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["business_hotel"]

    if "hilton" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["business_hotel"]

    if "jw marriott" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["luxury_hotel_glass"]

    if "112 tryon" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["historic_limestone"]

    if "johnston" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["historic_limestone"]

    if "200 south tryon" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["mid_century_modern"]

    if "parking" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["parking_structure"]

    if "government" in name_lower or "charlotte-mecklenburg" in name_lower:
        return CHARLOTTE_BUILDING_STYLES["government_building"]

    # By building type and era
    if building_type == "residential" or "apartment" in name_lower or "condo" in name_lower:
        if year_built >= 2010:
            return CHARLOTTE_BUILDING_STYLES["contemporary_residential"]
        else:
            return CHARLOTTE_BUILDING_STYLES["modern_residential_tower"]

    if building_type == "hotel":
        if height > 80:
            return CHARLOTTE_BUILDING_STYLES["luxury_hotel_glass"]
        else:
            return CHARLOTTE_BUILDING_STYLES["business_hotel"]

    # By era and height
    if year_built < 1950:
        return CHARLOTTE_BUILDING_STYLES["historic_limestone"]

    if year_built < 1970:
        return CHARLOTTE_BUILDING_STYLES["mid_century_modern"]

    if year_built < 1995:
        return CHARLOTTE_BUILDING_STYLES["postmodern_granite_office"]

    if year_built < 2010:
        return CHARLOTTE_BUILDING_STYLES["modern_glass_tower"]

    # Default to contemporary
    return CHARLOTTE_BUILDING_STYLES["contemporary_glass_tower"]


def get_materials_for_style(style: BuildingStyle) -> Dict[str, bpy.types.Material]:
    """
    Get all materials needed for a building style.

    Returns:
        Dict of material role -> material
    """
    materials = {}

    materials["primary"] = create_building_material(style.primary_material)

    if style.secondary_material:
        materials["secondary"] = create_building_material(style.secondary_material)

    materials["window"] = create_building_material(style.window_material)
    materials["mullion"] = create_building_material(style.mullion_material)

    if style.base_material:
        materials["base"] = create_building_material(style.base_material)

    if style.accent_material:
        materials["accent"] = create_building_material(style.accent_material)

    return materials


# =============================================================================
# MAIN
# =============================================================================

def setup_building_materials():
    """Set up all building materials for the Charlotte scene."""
    print("\n" + "=" * 60)
    print("CHARLOTTE BUILDING MATERIALS SETUP")
    print("=" * 60)

    # Create all base materials
    materials = create_all_building_materials()

    # Print style guide
    print("\n" + "=" * 60)
    print("BUILDING STYLE GUIDE")
    print("=" * 60)

    for style_name, style in CHARLOTTE_BUILDING_STYLES.items():
        print(f"\n{style.name}:")
        print(f"  Era: {style.era.value}")
        print(f"  Primary: {style.primary_material.value}")
        print(f"  Secondary: {style.secondary_material.value if style.secondary_material else 'None'}")
        print(f"  Description: {style.description}")

    return materials


if __name__ == '__main__':
    setup_building_materials()
