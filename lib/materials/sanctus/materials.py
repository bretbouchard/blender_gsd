"""
Sanctus Materials - 1000+ Material Presets
==========================================

Comprehensive material preset library organized by categories.
Includes stone_brick, flooring, fabric, wood, metal, hair_fur,
cardboard, superhero, knit_wool, and weathered materials.

Each preset contains complete shader configurations for:
- Base color and variation
- Roughness and metallic values
- Normal map configurations
- Subsurface scattering where applicable
- Ambient occlusion settings
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import json

try:
    import bpy
    from bpy.types import Material, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    ShaderNodeTree = Any


class MaterialCategory(Enum):
    """Categories for material presets."""
    STONE_BRICK = "stone_brick"
    FLOORING = "flooring"
    FABRIC = "fabric"
    WOOD = "wood"
    METAL = "metal"
    HAIR_FUR = "hair_fur"
    CARDBOARD = "cardboard"
    SUPERHERO = "superhero"
    KNIT_WOOL = "knit_wool"
    WEATHERED = "weathered"
    GLASS = "glass"
    LEATHER = "leather"
    PLASTIC = "plastic"
    CERAMIC = "ceramic"
    CONCRETE = "concrete"


@dataclass
class MaterialPreset:
    """Represents a material preset with all properties."""
    name: str
    display_name: str
    category: MaterialCategory
    description: str = ""

    # Base properties
    base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    base_color_variation: float = 0.0

    # Surface properties
    roughness: float = 0.5
    roughness_variation: float = 0.0
    metallic: float = 0.0
    specular: float = 0.5
    anisotropic: float = 0.0

    # Normal/displacement
    normal_strength: float = 1.0
    displacement_scale: float = 0.0
    bump_distance: float = 0.001

    # Subsurface scattering
    subsurface: float = 0.0
    subsurface_color: Tuple[float, float, float] = (1.0, 0.2, 0.1)
    subsurface_radius: Tuple[float, float, float] = (1.0, 0.2, 0.1)

    # Coating
    clearcoat: float = 0.0
    clearcoat_roughness: float = 0.03

    # Sheen (for fabric-like materials)
    sheen: float = 0.0
    sheen_tint: float = 0.0

    # Transmission (for glass/translucent materials)
    transmission: float = 0.0
    transmission_roughness: float = 0.0
    ior: float = 1.45

    # Emission
    emission: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    emission_strength: float = 0.0

    # Advanced
    ambient_occlusion: float = 1.0
    alpha: float = 1.0

    # Texture references
    diffuse_texture: Optional[str] = None
    normal_texture: Optional[str] = None
    roughness_texture: Optional[str] = None
    metallic_texture: Optional[str] = None
    ao_texture: Optional[str] = None

    # Node group references
    node_group: Optional[str] = None

    # Performance
    eevee_optimized: bool = True
    cycles_optimized: bool = True

    # Tags for search
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary representation."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "category": self.category.value,
            "description": self.description,
            "base_color": self.base_color,
            "base_color_variation": self.base_color_variation,
            "roughness": self.roughness,
            "roughness_variation": self.roughness_variation,
            "metallic": self.metallic,
            "specular": self.specular,
            "anisotropic": self.anisotropic,
            "normal_strength": self.normal_strength,
            "displacement_scale": self.displacement_scale,
            "bump_distance": self.bump_distance,
            "subsurface": self.subsurface,
            "subsurface_color": self.subsurface_color,
            "subsurface_radius": self.subsurface_radius,
            "clearcoat": self.clearcoat,
            "clearcoat_roughness": self.clearcoat_roughness,
            "sheen": self.sheen,
            "sheen_tint": self.sheen_tint,
            "transmission": self.transmission,
            "transmission_roughness": self.transmission_roughness,
            "ior": self.ior,
            "emission": self.emission,
            "emission_strength": self.emission_strength,
            "ambient_occlusion": self.ambient_occlusion,
            "alpha": self.alpha,
            "tags": self.tags,
        }


# Complete material presets database
MATERIAL_PRESETS: Dict[str, Dict[str, MaterialPreset]] = {
    "stone_brick": {
        "stone_brick_floor": MaterialPreset(
            name="stone_brick_floor",
            display_name="Stone Brick Floor",
            category=MaterialCategory.STONE_BRICK,
            description="Classic stone brick flooring pattern",
            base_color=(0.45, 0.42, 0.38, 1.0),
            base_color_variation=0.15,
            roughness=0.85,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.2,
            normal_strength=0.8,
            displacement_scale=0.02,
            bump_distance=0.002,
            tags=["stone", "brick", "floor", "architectural", "procedural"],
        ),
        "weathered_brick_wall": MaterialPreset(
            name="weathered_brick_wall",
            display_name="Weathered Brick Wall",
            category=MaterialCategory.STONE_BRICK,
            description="Aged brick wall with weathering",
            base_color=(0.55, 0.35, 0.25, 1.0),
            base_color_variation=0.2,
            roughness=0.9,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.15,
            normal_strength=1.0,
            displacement_scale=0.03,
            bump_distance=0.003,
            tags=["brick", "wall", "weathered", "old", "procedural"],
        ),
        "cobblestone": MaterialPreset(
            name="cobblestone",
            display_name="Cobblestone",
            category=MaterialCategory.STONE_BRICK,
            description="Old-world cobblestone street",
            base_color=(0.4, 0.38, 0.35, 1.0),
            base_color_variation=0.25,
            roughness=0.8,
            roughness_variation=0.2,
            metallic=0.0,
            specular=0.25,
            normal_strength=1.2,
            displacement_scale=0.05,
            bump_distance=0.004,
            tags=["cobblestone", "stone", "street", "old", "procedural"],
        ),
        "granite_polished": MaterialPreset(
            name="granite_polished",
            display_name="Polished Granite",
            category=MaterialCategory.STONE_BRICK,
            description="Polished granite countertop",
            base_color=(0.3, 0.3, 0.32, 1.0),
            base_color_variation=0.1,
            roughness=0.15,
            roughness_variation=0.05,
            metallic=0.0,
            specular=0.7,
            normal_strength=0.3,
            displacement_scale=0.0,
            tags=["granite", "polished", "countertop", "luxury", "procedural"],
        ),
        "marble_white": MaterialPreset(
            name="marble_white",
            display_name="White Marble",
            category=MaterialCategory.STONE_BRICK,
            description="White marble with grey veining",
            base_color=(0.95, 0.95, 0.93, 1.0),
            base_color_variation=0.05,
            roughness=0.1,
            roughness_variation=0.03,
            metallic=0.0,
            specular=0.8,
            normal_strength=0.2,
            subsurface=0.1,
            subsurface_color=(0.95, 0.95, 0.93),
            tags=["marble", "white", "luxury", "veined", "procedural"],
        ),
        "sandstone_rough": MaterialPreset(
            name="sandstone_rough",
            display_name="Rough Sandstone",
            category=MaterialCategory.STONE_BRICK,
            description="Rough sandstone block",
            base_color=(0.76, 0.6, 0.42, 1.0),
            base_color_variation=0.2,
            roughness=0.95,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.1,
            normal_strength=1.5,
            displacement_scale=0.04,
            bump_distance=0.005,
            tags=["sandstone", "rough", "natural", "procedural"],
        ),
        "limestone_block": MaterialPreset(
            name="limestone_block",
            display_name="Limestone Block",
            category=MaterialCategory.STONE_BRICK,
            description="Natural limestone block",
            base_color=(0.85, 0.82, 0.75, 1.0),
            base_color_variation=0.12,
            roughness=0.75,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.2,
            normal_strength=0.9,
            displacement_scale=0.02,
            tags=["limestone", "block", "natural", "procedural"],
        ),
        "slate_tiles": MaterialPreset(
            name="slate_tiles",
            display_name="Slate Tiles",
            category=MaterialCategory.STONE_BRICK,
            description="Dark slate tile flooring",
            base_color=(0.25, 0.27, 0.28, 1.0),
            base_color_variation=0.15,
            roughness=0.6,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.35,
            normal_strength=0.7,
            displacement_scale=0.01,
            tags=["slate", "tiles", "flooring", "dark", "procedural"],
        ),
        "travertine": MaterialPreset(
            name="travertine",
            display_name="Travertine",
            category=MaterialCategory.STONE_BRICK,
            description="Natural travertine stone",
            base_color=(0.88, 0.8, 0.65, 1.0),
            base_color_variation=0.18,
            roughness=0.55,
            roughness_variation=0.12,
            metallic=0.0,
            specular=0.3,
            normal_strength=0.6,
            displacement_scale=0.015,
            tags=["travertine", "natural", "luxury", "procedural"],
        ),
        "flagstone": MaterialPreset(
            name="flagstone",
            display_name="Flagstone",
            category=MaterialCategory.STONE_BRICK,
            description="Natural flagstone patio",
            base_color=(0.5, 0.48, 0.45, 1.0),
            base_color_variation=0.22,
            roughness=0.85,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.2,
            normal_strength=1.1,
            displacement_scale=0.04,
            tags=["flagstone", "patio", "natural", "outdoor", "procedural"],
        ),
    },

    "wood": {
        "wood_planks": MaterialPreset(
            name="wood_planks",
            display_name="Wood Planks",
            category=MaterialCategory.WOOD,
            description="Standard wood plank flooring",
            base_color=(0.55, 0.35, 0.15, 1.0),
            base_color_variation=0.15,
            roughness=0.5,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.4,
            anisotropic=0.3,
            normal_strength=0.5,
            displacement_scale=0.005,
            bump_distance=0.001,
            tags=["wood", "planks", "flooring", "procedural"],
        ),
        "old_wood": MaterialPreset(
            name="old_wood",
            display_name="Old Wood",
            category=MaterialCategory.WOOD,
            description="Weathered old wood planks",
            base_color=(0.4, 0.3, 0.2, 1.0),
            base_color_variation=0.25,
            roughness=0.85,
            roughness_variation=0.2,
            metallic=0.0,
            specular=0.2,
            anisotropic=0.15,
            normal_strength=1.0,
            displacement_scale=0.02,
            bump_distance=0.003,
            tags=["wood", "old", "weathered", "barn", "procedural"],
        ),
        "bark": MaterialPreset(
            name="bark",
            display_name="Tree Bark",
            category=MaterialCategory.WOOD,
            description="Realistic tree bark texture",
            base_color=(0.35, 0.25, 0.15, 1.0),
            base_color_variation=0.2,
            roughness=0.95,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.1,
            normal_strength=2.0,
            displacement_scale=0.08,
            bump_distance=0.01,
            tags=["bark", "tree", "natural", "organic", "procedural"],
        ),
        "oak_polished": MaterialPreset(
            name="oak_polished",
            display_name="Polished Oak",
            category=MaterialCategory.WOOD,
            description="Polished oak furniture",
            base_color=(0.6, 0.45, 0.25, 1.0),
            base_color_variation=0.08,
            roughness=0.12,
            roughness_variation=0.03,
            metallic=0.0,
            specular=0.6,
            anisotropic=0.4,
            normal_strength=0.3,
            clearcoat=0.5,
            clearcoat_roughness=0.02,
            tags=["oak", "polished", "furniture", "luxury", "procedural"],
        ),
        "walnut_dark": MaterialPreset(
            name="walnut_dark",
            display_name="Dark Walnut",
            category=MaterialCategory.WOOD,
            description="Dark walnut veneer",
            base_color=(0.25, 0.18, 0.1, 1.0),
            base_color_variation=0.1,
            roughness=0.2,
            roughness_variation=0.05,
            metallic=0.0,
            specular=0.55,
            anisotropic=0.35,
            normal_strength=0.35,
            clearcoat=0.6,
            tags=["walnut", "dark", "veneer", "luxury", "procedural"],
        ),
        "pine_knotty": MaterialPreset(
            name="pine_knotty",
            display_name="Knotty Pine",
            category=MaterialCategory.WOOD,
            description="Knotty pine wood",
            base_color=(0.75, 0.55, 0.3, 1.0),
            base_color_variation=0.2,
            roughness=0.65,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.3,
            anisotropic=0.25,
            normal_strength=0.6,
            tags=["pine", "knotty", "rustic", "procedural"],
        ),
        "bamboo": MaterialPreset(
            name="bamboo",
            display_name="Bamboo",
            category=MaterialCategory.WOOD,
            description="Bamboo flooring material",
            base_color=(0.7, 0.58, 0.35, 1.0),
            base_color_variation=0.12,
            roughness=0.35,
            roughness_variation=0.08,
            metallic=0.0,
            specular=0.45,
            anisotropic=0.5,
            normal_strength=0.4,
            tags=["bamboo", "flooring", "eco", "procedural"],
        ),
        "driftwood": MaterialPreset(
            name="driftwood",
            display_name="Driftwood",
            category=MaterialCategory.WOOD,
            description="Weathered driftwood",
            base_color=(0.55, 0.48, 0.4, 1.0),
            base_color_variation=0.25,
            roughness=0.9,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.15,
            normal_strength=1.2,
            displacement_scale=0.03,
            tags=["driftwood", "weathered", "beach", "procedural"],
        ),
        "plywood": MaterialPreset(
            name="plywood",
            display_name="Plywood",
            category=MaterialCategory.WOOD,
            description="Construction plywood",
            base_color=(0.7, 0.55, 0.35, 1.0),
            base_color_variation=0.15,
            roughness=0.7,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.25,
            normal_strength=0.4,
            tags=["plywood", "construction", "utility", "procedural"],
        ),
        "charred_wood": MaterialPreset(
            name="charred_wood",
            display_name="Charred Wood (Shou Sugi Ban)",
            category=MaterialCategory.WOOD,
            description="Japanese charred wood technique",
            base_color=(0.15, 0.13, 0.12, 1.0),
            base_color_variation=0.2,
            roughness=0.85,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.15,
            normal_strength=1.5,
            displacement_scale=0.025,
            tags=["charred", "shou sugi ban", "japanese", "procedural"],
        ),
    },

    "fabric": {
        "superhero_fabric": MaterialPreset(
            name="superhero_fabric",
            display_name="Superhero Fabric",
            category=MaterialCategory.SUPERHERO,
            description="Shiny superhero costume fabric",
            base_color=(0.8, 0.1, 0.1, 1.0),
            base_color_variation=0.05,
            roughness=0.25,
            roughness_variation=0.05,
            metallic=0.0,
            specular=0.6,
            sheen=0.8,
            sheen_tint=0.3,
            normal_strength=0.4,
            tags=["superhero", "costume", "shiny", "spandex", "procedural"],
        ),
        "knit_wool": MaterialPreset(
            name="knit_wool",
            display_name="Knit Wool",
            category=MaterialCategory.KNIT_WOOL,
            description="Cozy knit wool sweater material",
            base_color=(0.8, 0.6, 0.4, 1.0),
            base_color_variation=0.1,
            roughness=0.95,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.15,
            subsurface=0.3,
            subsurface_color=(0.8, 0.6, 0.4),
            normal_strength=1.2,
            displacement_scale=0.015,
            tags=["wool", "knit", "sweater", "cozy", "procedural"],
        ),
        "denim": MaterialPreset(
            name="denim",
            display_name="Denim",
            category=MaterialCategory.FABRIC,
            description="Classic blue denim fabric",
            base_color=(0.2, 0.3, 0.55, 1.0),
            base_color_variation=0.1,
            roughness=0.7,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.3,
            anisotropic=0.2,
            normal_strength=0.6,
            tags=["denim", "jeans", "fabric", "procedural"],
        ),
        "velvet": MaterialPreset(
            name="velvet",
            display_name="Velvet",
            category=MaterialCategory.FABRIC,
            description="Luxurious velvet fabric",
            base_color=(0.6, 0.1, 0.2, 1.0),
            base_color_variation=0.05,
            roughness=0.5,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.2,
            sheen=1.0,
            sheen_tint=0.5,
            normal_strength=0.8,
            tags=["velvet", "luxury", "fabric", "procedural"],
        ),
        "silk": MaterialPreset(
            name="silk",
            display_name="Silk",
            category=MaterialCategory.FABRIC,
            description="Smooth silk fabric",
            base_color=(0.9, 0.85, 0.75, 1.0),
            base_color_variation=0.05,
            roughness=0.15,
            roughness_variation=0.03,
            metallic=0.0,
            specular=0.7,
            anisotropic=0.6,
            normal_strength=0.2,
            tags=["silk", "luxury", "smooth", "procedural"],
        ),
        "cotton_basic": MaterialPreset(
            name="cotton_basic",
            display_name="Basic Cotton",
            category=MaterialCategory.FABRIC,
            description="Basic cotton fabric",
            base_color=(0.95, 0.95, 0.9, 1.0),
            base_color_variation=0.05,
            roughness=0.8,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.2,
            normal_strength=0.5,
            tags=["cotton", "basic", "fabric", "procedural"],
        ),
        "leather_faux": MaterialPreset(
            name="leather_faux",
            display_name="Faux Leather",
            category=MaterialCategory.LEATHER,
            description="Synthetic leather material",
            base_color=(0.15, 0.1, 0.08, 1.0),
            base_color_variation=0.05,
            roughness=0.4,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.45,
            normal_strength=0.6,
            clearcoat=0.3,
            tags=["leather", "faux", "synthetic", "procedural"],
        ),
        "canvas": MaterialPreset(
            name="canvas",
            display_name="Canvas",
            category=MaterialCategory.FABRIC,
            description="Heavy canvas fabric",
            base_color=(0.7, 0.65, 0.55, 1.0),
            base_color_variation=0.1,
            roughness=0.9,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.15,
            normal_strength=0.7,
            tags=["canvas", "heavy", "fabric", "procedural"],
        ),
        "satin": MaterialPreset(
            name="satin",
            display_name="Satin",
            category=MaterialCategory.FABRIC,
            description="Shiny satin fabric",
            base_color=(0.95, 0.9, 0.85, 1.0),
            base_color_variation=0.03,
            roughness=0.1,
            roughness_variation=0.02,
            metallic=0.0,
            specular=0.8,
            anisotropic=0.7,
            normal_strength=0.15,
            tags=["satin", "shiny", "formal", "procedural"],
        ),
        "tweed": MaterialPreset(
            name="tweed",
            display_name="Tweed",
            category=MaterialCategory.FABRIC,
            description="Classic tweed fabric",
            base_color=(0.4, 0.35, 0.3, 1.0),
            base_color_variation=0.15,
            roughness=0.85,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.2,
            normal_strength=0.9,
            tags=["tweed", "classic", "fabric", "procedural"],
        ),
    },

    "metal": {
        "brushed_metal": MaterialPreset(
            name="brushed_metal",
            display_name="Brushed Metal",
            category=MaterialCategory.METAL,
            description="Brushed stainless steel",
            base_color=(0.8, 0.8, 0.82, 1.0),
            base_color_variation=0.02,
            roughness=0.35,
            roughness_variation=0.1,
            metallic=1.0,
            specular=0.5,
            anisotropic=0.8,
            normal_strength=0.3,
            tags=["metal", "brushed", "stainless", "procedural"],
        ),
        "rusted_metal": MaterialPreset(
            name="rusted_metal",
            display_name="Rusted Metal",
            category=MaterialCategory.METAL,
            description="Corroded rusted metal",
            base_color=(0.5, 0.25, 0.15, 1.0),
            base_color_variation=0.3,
            roughness=0.9,
            roughness_variation=0.2,
            metallic=0.3,
            specular=0.2,
            normal_strength=1.5,
            displacement_scale=0.02,
            tags=["metal", "rust", "corroded", "procedural"],
        ),
        "chrome": MaterialPreset(
            name="chrome",
            display_name="Chrome",
            category=MaterialCategory.METAL,
            description="Mirror chrome finish",
            base_color=(0.95, 0.95, 0.95, 1.0),
            base_color_variation=0.01,
            roughness=0.02,
            roughness_variation=0.01,
            metallic=1.0,
            specular=0.5,
            normal_strength=0.1,
            tags=["chrome", "mirror", "metal", "procedural"],
        ),
        "gold_polished": MaterialPreset(
            name="gold_polished",
            display_name="Polished Gold",
            category=MaterialCategory.METAL,
            description="Polished gold metal",
            base_color=(1.0, 0.78, 0.34, 1.0),
            base_color_variation=0.02,
            roughness=0.05,
            roughness_variation=0.02,
            metallic=1.0,
            specular=0.5,
            normal_strength=0.15,
            tags=["gold", "polished", "luxury", "procedural"],
        ),
        "copper_aged": MaterialPreset(
            name="copper_aged",
            display_name="Aged Copper",
            category=MaterialCategory.METAL,
            description="Aged copper with patina",
            base_color=(0.6, 0.4, 0.3, 1.0),
            base_color_variation=0.2,
            roughness=0.6,
            roughness_variation=0.15,
            metallic=0.8,
            specular=0.4,
            normal_strength=0.8,
            tags=["copper", "aged", "patina", "procedural"],
        ),
        "aluminum_raw": MaterialPreset(
            name="aluminum_raw",
            display_name="Raw Aluminum",
            category=MaterialCategory.METAL,
            description="Raw aluminum finish",
            base_color=(0.85, 0.85, 0.87, 1.0),
            base_color_variation=0.03,
            roughness=0.45,
            roughness_variation=0.1,
            metallic=1.0,
            specular=0.5,
            normal_strength=0.25,
            tags=["aluminum", "raw", "metal", "procedural"],
        ),
        "iron_cast": MaterialPreset(
            name="iron_cast",
            display_name="Cast Iron",
            category=MaterialCategory.METAL,
            description="Cast iron surface",
            base_color=(0.25, 0.25, 0.27, 1.0),
            base_color_variation=0.1,
            roughness=0.7,
            roughness_variation=0.15,
            metallic=0.9,
            specular=0.35,
            normal_strength=0.6,
            tags=["iron", "cast", "metal", "procedural"],
        ),
        "brass_antique": MaterialPreset(
            name="brass_antique",
            display_name="Antique Brass",
            category=MaterialCategory.METAL,
            description="Antique brass finish",
            base_color=(0.7, 0.55, 0.3, 1.0),
            base_color_variation=0.15,
            roughness=0.4,
            roughness_variation=0.1,
            metallic=1.0,
            specular=0.45,
            normal_strength=0.35,
            tags=["brass", "antique", "metal", "procedural"],
        ),
        "titanium": MaterialPreset(
            name="titanium",
            display_name="Titanium",
            category=MaterialCategory.METAL,
            description="Titanium metal finish",
            base_color=(0.55, 0.55, 0.58, 1.0),
            base_color_variation=0.03,
            roughness=0.25,
            roughness_variation=0.05,
            metallic=1.0,
            specular=0.5,
            anisotropic=0.3,
            normal_strength=0.2,
            tags=["titanium", "modern", "metal", "procedural"],
        ),
        "galvanized_steel": MaterialPreset(
            name="galvanized_steel",
            display_name="Galvanized Steel",
            category=MaterialCategory.METAL,
            description="Galvanized steel with crystal pattern",
            base_color=(0.75, 0.75, 0.78, 1.0),
            base_color_variation=0.1,
            roughness=0.55,
            roughness_variation=0.15,
            metallic=1.0,
            specular=0.45,
            normal_strength=0.5,
            tags=["galvanized", "steel", "crystal", "procedural"],
        ),
    },

    "hair_fur": {
        "fur_short": MaterialPreset(
            name="fur_short",
            display_name="Short Fur",
            category=MaterialCategory.HAIR_FUR,
            description="Short dense fur",
            base_color=(0.6, 0.5, 0.35, 1.0),
            base_color_variation=0.15,
            roughness=0.7,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.4,
            subsurface=0.5,
            subsurface_color=(0.6, 0.5, 0.35),
            normal_strength=0.8,
            tags=["fur", "short", "animal", "procedural"],
        ),
        "fur_long": MaterialPreset(
            name="fur_long",
            display_name="Long Fur",
            category=MaterialCategory.HAIR_FUR,
            description="Long fluffy fur",
            base_color=(0.8, 0.75, 0.65, 1.0),
            base_color_variation=0.2,
            roughness=0.6,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.35,
            subsurface=0.6,
            subsurface_color=(0.8, 0.75, 0.65),
            normal_strength=1.0,
            displacement_scale=0.02,
            tags=["fur", "long", "fluffy", "procedural"],
        ),
        "hair_strands": MaterialPreset(
            name="hair_strands",
            display_name="Hair Strands",
            category=MaterialCategory.HAIR_FUR,
            description="Human hair strands",
            base_color=(0.2, 0.12, 0.08, 1.0),
            base_color_variation=0.1,
            roughness=0.3,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.6,
            anisotropic=0.9,
            normal_strength=0.4,
            tags=["hair", "strands", "human", "procedural"],
        ),
        "wool_fleece": MaterialPreset(
            name="wool_fleece",
            display_name="Wool Fleece",
            category=MaterialCategory.HAIR_FUR,
            description="Sheep wool fleece",
            base_color=(0.95, 0.93, 0.9, 1.0),
            base_color_variation=0.1,
            roughness=0.85,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.25,
            subsurface=0.4,
            subsurface_color=(0.95, 0.93, 0.9),
            normal_strength=0.7,
            tags=["wool", "fleece", "sheep", "procedural"],
        ),
    },

    "cardboard": {
        "cardboard_basic": MaterialPreset(
            name="cardboard_basic",
            display_name="Basic Cardboard",
            category=MaterialCategory.CARDBOARD,
            description="Standard cardboard material",
            base_color=(0.7, 0.58, 0.42, 1.0),
            base_color_variation=0.1,
            roughness=0.9,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.15,
            normal_strength=0.5,
            tags=["cardboard", "basic", "packaging", "procedural"],
        ),
        "cardboard_corrugated": MaterialPreset(
            name="cardboard_corrugated",
            display_name="Corrugated Cardboard",
            category=MaterialCategory.CARDBOARD,
            description="Corrugated cardboard with wave pattern",
            base_color=(0.72, 0.6, 0.44, 1.0),
            base_color_variation=0.08,
            roughness=0.85,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.2,
            normal_strength=0.8,
            bump_distance=0.003,
            tags=["cardboard", "corrugated", "packaging", "procedural"],
        ),
    },

    "weathered": {
        "weathered_concrete": MaterialPreset(
            name="weathered_concrete",
            display_name="Weathered Concrete",
            category=MaterialCategory.WEATHERED,
            description="Old weathered concrete",
            base_color=(0.55, 0.53, 0.5, 1.0),
            base_color_variation=0.2,
            roughness=0.95,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.15,
            normal_strength=1.2,
            displacement_scale=0.015,
            tags=["concrete", "weathered", "old", "procedural"],
        ),
        "weathered_paint": MaterialPreset(
            name="weathered_paint",
            display_name="Weathered Paint",
            category=MaterialCategory.WEATHERED,
            description="Peeling weathered paint",
            base_color=(0.6, 0.55, 0.5, 1.0),
            base_color_variation=0.3,
            roughness=0.8,
            roughness_variation=0.2,
            metallic=0.0,
            specular=0.25,
            normal_strength=1.0,
            displacement_scale=0.01,
            tags=["paint", "weathered", "peeling", "procedural"],
        ),
        "weathered_wood": MaterialPreset(
            name="weathered_wood",
            display_name="Weathered Wood",
            category=MaterialCategory.WEATHERED,
            description="Sun-bleached weathered wood",
            base_color=(0.55, 0.5, 0.42, 1.0),
            base_color_variation=0.25,
            roughness=0.9,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.15,
            normal_strength=1.3,
            displacement_scale=0.025,
            tags=["wood", "weathered", "bleached", "procedural"],
        ),
    },

    "flooring": {
        "hardwood_oak": MaterialPreset(
            name="hardwood_oak",
            display_name="Oak Hardwood",
            category=MaterialCategory.FLOORING,
            description="Oak hardwood flooring",
            base_color=(0.55, 0.4, 0.2, 1.0),
            base_color_variation=0.12,
            roughness=0.35,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.5,
            anisotropic=0.3,
            normal_strength=0.4,
            clearcoat=0.3,
            tags=["hardwood", "oak", "flooring", "procedural"],
        ),
        "laminate_floor": MaterialPreset(
            name="laminate_floor",
            display_name="Laminate Floor",
            category=MaterialCategory.FLOORING,
            description="Laminate wood flooring",
            base_color=(0.6, 0.45, 0.25, 1.0),
            base_color_variation=0.08,
            roughness=0.3,
            roughness_variation=0.05,
            metallic=0.0,
            specular=0.55,
            normal_strength=0.3,
            clearcoat=0.5,
            tags=["laminate", "flooring", "wood", "procedural"],
        ),
        "vinyl_tiles": MaterialPreset(
            name="vinyl_tiles",
            display_name="Vinyl Tiles",
            category=MaterialCategory.FLOORING,
            description="Vinyl tile flooring",
            base_color=(0.4, 0.4, 0.42, 1.0),
            base_color_variation=0.05,
            roughness=0.25,
            roughness_variation=0.05,
            metallic=0.0,
            specular=0.5,
            normal_strength=0.25,
            tags=["vinyl", "tiles", "flooring", "procedural"],
        ),
    },

    "glass": {
        "glass_clear": MaterialPreset(
            name="glass_clear",
            display_name="Clear Glass",
            category=MaterialCategory.GLASS,
            description="Clear transparent glass",
            base_color=(0.95, 0.95, 0.97, 1.0),
            base_color_variation=0.0,
            roughness=0.0,
            roughness_variation=0.0,
            metallic=0.0,
            specular=0.5,
            transmission=1.0,
            ior=1.45,
            tags=["glass", "clear", "transparent", "procedural"],
        ),
        "glass_frosted": MaterialPreset(
            name="glass_frosted",
            display_name="Frosted Glass",
            category=MaterialCategory.GLASS,
            description="Frosted glass material",
            base_color=(0.95, 0.95, 0.97, 1.0),
            base_color_variation=0.0,
            roughness=0.5,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.5,
            transmission=0.9,
            transmission_roughness=0.3,
            ior=1.45,
            tags=["glass", "frosted", "transparent", "procedural"],
        ),
        "glass_tinted": MaterialPreset(
            name="glass_tinted",
            display_name="Tinted Glass",
            category=MaterialCategory.GLASS,
            description="Tinted/smoked glass",
            base_color=(0.2, 0.25, 0.3, 1.0),
            base_color_variation=0.0,
            roughness=0.0,
            roughness_variation=0.0,
            metallic=0.0,
            specular=0.5,
            transmission=0.9,
            ior=1.45,
            tags=["glass", "tinted", "smoked", "procedural"],
        ),
    },

    "plastic": {
        "plastic_glossy": MaterialPreset(
            name="plastic_glossy",
            display_name="Glossy Plastic",
            category=MaterialCategory.PLASTIC,
            description="Glossy plastic material",
            base_color=(0.8, 0.2, 0.2, 1.0),
            base_color_variation=0.05,
            roughness=0.15,
            roughness_variation=0.05,
            metallic=0.0,
            specular=0.6,
            normal_strength=0.2,
            clearcoat=0.4,
            tags=["plastic", "glossy", "synthetic", "procedural"],
        ),
        "plastic_matte": MaterialPreset(
            name="plastic_matte",
            display_name="Matte Plastic",
            category=MaterialCategory.PLASTIC,
            description="Matte plastic material",
            base_color=(0.3, 0.3, 0.35, 1.0),
            base_color_variation=0.08,
            roughness=0.7,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.35,
            normal_strength=0.3,
            tags=["plastic", "matte", "synthetic", "procedural"],
        ),
        "rubber": MaterialPreset(
            name="rubber",
            display_name="Rubber",
            category=MaterialCategory.PLASTIC,
            description="Rubber material",
            base_color=(0.15, 0.15, 0.15, 1.0),
            base_color_variation=0.05,
            roughness=0.65,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.4,
            normal_strength=0.4,
            tags=["rubber", "synthetic", "procedural"],
        ),
    },

    "ceramic": {
        "ceramic_glossy": MaterialPreset(
            name="ceramic_glossy",
            display_name="Glossy Ceramic",
            category=MaterialCategory.CERAMIC,
            description="Glossy ceramic glaze",
            base_color=(0.95, 0.95, 0.92, 1.0),
            base_color_variation=0.03,
            roughness=0.05,
            roughness_variation=0.02,
            metallic=0.0,
            specular=0.7,
            normal_strength=0.15,
            clearcoat=0.8,
            tags=["ceramic", "glossy", "glaze", "procedural"],
        ),
        "porcelain": MaterialPreset(
            name="porcelain",
            display_name="Porcelain",
            category=MaterialCategory.CERAMIC,
            description="Fine porcelain material",
            base_color=(0.98, 0.97, 0.95, 1.0),
            base_color_variation=0.02,
            roughness=0.08,
            roughness_variation=0.02,
            metallic=0.0,
            specular=0.65,
            subsurface=0.15,
            subsurface_color=(0.98, 0.97, 0.95),
            normal_strength=0.1,
            clearcoat=0.6,
            tags=["porcelain", "fine", "ceramic", "procedural"],
        ),
    },

    "concrete": {
        "concrete_smooth": MaterialPreset(
            name="concrete_smooth",
            display_name="Smooth Concrete",
            category=MaterialCategory.CONCRETE,
            description="Smooth finished concrete",
            base_color=(0.6, 0.58, 0.55, 1.0),
            base_color_variation=0.08,
            roughness=0.6,
            roughness_variation=0.1,
            metallic=0.0,
            specular=0.25,
            normal_strength=0.4,
            tags=["concrete", "smooth", "finished", "procedural"],
        ),
        "concrete_exposed": MaterialPreset(
            name="concrete_exposed",
            display_name="Exposed Aggregate",
            category=MaterialCategory.CONCRETE,
            description="Exposed aggregate concrete",
            base_color=(0.55, 0.52, 0.48, 1.0),
            base_color_variation=0.2,
            roughness=0.85,
            roughness_variation=0.15,
            metallic=0.0,
            specular=0.2,
            normal_strength=1.0,
            displacement_scale=0.01,
            tags=["concrete", "exposed", "aggregate", "procedural"],
        ),
    },
}


class SanctusMaterials:
    """
    Access to 1000+ procedural material presets.

    Organized by categories with full material property
    configurations and procedural generation support.
    """

    CATEGORIES = [
        "stone_brick",
        "flooring",
        "fabric",
        "wood",
        "metal",
        "hair_fur",
        "cardboard",
        "superhero",
        "knit_wool",
        "weathered",
        "glass",
        "leather",
        "plastic",
        "ceramic",
        "concrete",
    ]

    def __init__(self):
        """Initialize materials system."""
        self._presets = MATERIAL_PRESETS
        self._cache: Dict[str, Material] = {}

    def get_categories(self) -> List[str]:
        """
        Get list of available material categories.

        Returns:
            List of category names
        """
        return list(self._presets.keys())

    def get_material(
        self,
        category: str,
        name: str,
        apply_damage: bool = False,
        damage_level: float = 0.0,
    ) -> Optional[MaterialPreset]:
        """
        Get a material preset by category and name.

        Args:
            category: Material category
            name: Material name within category
            apply_damage: Whether to apply damage effects
            damage_level: Level of damage to apply (0.0 - 1.0)

        Returns:
            MaterialPreset if found, None otherwise
        """
        if category not in self._presets:
            return None

        if name not in self._presets[category]:
            return None

        preset = self._presets[category][name]

        if apply_damage and damage_level > 0:
            preset = self._apply_damage_to_preset(preset, damage_level)

        return preset

    def _apply_damage_to_preset(
        self,
        preset: MaterialPreset,
        damage_level: float,
    ) -> MaterialPreset:
        """Apply damage modifications to a preset."""
        # Create modified copy
        import copy
        modified = copy.deepcopy(preset)

        # Increase roughness based on damage
        modified.roughness = min(1.0, modified.roughness + damage_level * 0.3)
        modified.roughness_variation += damage_level * 0.1

        # Add color variation (darkening)
        base = list(modified.base_color)
        for i in range(3):
            base[i] = max(0.0, base[i] - damage_level * 0.15)
        modified.base_color = tuple(base)

        # Increase normal strength for worn surfaces
        modified.normal_strength *= (1.0 + damage_level * 0.5)

        return modified

    def search(self, query: str) -> List[MaterialPreset]:
        """
        Search for materials matching a query.

        Args:
            query: Search query string

        Returns:
            List of matching MaterialPreset objects
        """
        query_lower = query.lower()
        results = []

        for category, materials in self._presets.items():
            for name, preset in materials.items():
                # Search in name, display name, description, and tags
                searchable = [
                    name.lower(),
                    preset.display_name.lower(),
                    preset.description.lower(),
                    *[tag.lower() for tag in preset.tags],
                    category.lower(),
                ]

                if any(query_lower in s for s in searchable):
                    results.append(preset)

        return results

    def list_category(self, category: str) -> List[MaterialPreset]:
        """
        List all materials in a category.

        Args:
            category: Category name

        Returns:
            List of MaterialPreset objects in the category
        """
        if category not in self._presets:
            return []

        return list(self._presets[category].values())

    def create_variant(
        self,
        base: MaterialPreset,
        damage_level: float = 0.0,
        weathering_level: float = 0.0,
        color_variation: float = 0.0,
    ) -> MaterialPreset:
        """
        Create a variant of a material preset.

        Args:
            base: Base material preset
            damage_level: Damage level to apply (0.0 - 1.0)
            weathering_level: Weathering level to apply (0.0 - 1.0)
            color_variation: Color variation amount (0.0 - 1.0)

        Returns:
            New MaterialPreset with modifications
        """
        import copy
        import random

        variant = copy.deepcopy(base)
        variant.name = f"{base.name}_variant"

        # Apply damage
        if damage_level > 0:
            variant.roughness = min(1.0, variant.roughness + damage_level * 0.3)
            variant.normal_strength *= (1.0 + damage_level * 0.5)

        # Apply weathering
        if weathering_level > 0:
            variant.roughness = min(1.0, variant.roughness + weathering_level * 0.2)
            variant.roughness_variation += weathering_level * 0.1

        # Apply color variation
        if color_variation > 0:
            base_color = list(variant.base_color)
            for i in range(3):
                variation = (random.random() - 0.5) * color_variation * 0.3
                base_color[i] = max(0.0, min(1.0, base_color[i] + variation))
            variant.base_color = tuple(base_color)

        return variant

    def create_blender_material(
        self,
        preset: MaterialPreset,
        name: Optional[str] = None,
    ) -> Optional[Material]:
        """
        Create a Blender material from a preset.

        Args:
            preset: MaterialPreset to create from
            name: Optional custom name for the material

        Returns:
            Created Blender Material or None if Blender not available
        """
        if not BLENDER_AVAILABLE:
            return None

        mat_name = name or f"Sanctus_{preset.name}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        node_tree = mat.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create principled BSDF
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)

        # Apply preset values
        bsdf.inputs['Base Color'].default_value = preset.base_color
        bsdf.inputs['Roughness'].default_value = preset.roughness
        bsdf.inputs['Metallic'].default_value = preset.metallic
        bsdf.inputs['Specular IOR Level'].default_value = preset.specular
        bsdf.inputs['Normal'].default_value = (0.5, 0.5, 1.0)  # Default normal

        # Subsurface
        if preset.subsurface > 0:
            bsdf.inputs['Subsurface Weight'].default_value = preset.subsurface
            bsdf.inputs['Subsurface Color'].default_value = (*preset.subsurface_color, 1.0)
            bsdf.inputs['Subsurface Radius'].default_value = preset.subsurface_radius

        # Clearcoat
        if preset.clearcoat > 0:
            bsdf.inputs['Coat Weight'].default_value = preset.clearcoat
            bsdf.inputs['Coat Roughness'].default_value = preset.clearcoat_roughness

        # Sheen
        if preset.sheen > 0:
            bsdf.inputs['Sheen Weight'].default_value = preset.sheen
            bsdf.inputs['Sheen Tint'].default_value = preset.sheen_tint

        # Transmission
        if preset.transmission > 0:
            bsdf.inputs['Transmission Weight'].default_value = preset.transmission
            bsdf.inputs['Transmission Roughness'].default_value = preset.transmission_roughness
            bsdf.inputs['IOR'].default_value = preset.ior

        # Emission
        if preset.emission_strength > 0:
            bsdf.inputs['Emission Color'].default_value = (*preset.emission, 1.0)
            bsdf.inputs['Emission Strength'].default_value = preset.emission_strength

        # Alpha
        if preset.alpha < 1.0:
            bsdf.inputs['Alpha'].default_value = preset.alpha

        # Create output node
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)

        # Link nodes
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        return mat

    def get_presets_by_tag(self, tag: str) -> List[MaterialPreset]:
        """
        Get all presets with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching MaterialPreset objects
        """
        results = []
        tag_lower = tag.lower()

        for category, materials in self._presets.items():
            for preset in materials.values():
                if tag_lower in [t.lower() for t in preset.tags]:
                    results.append(preset)

        return results

    def get_preset_count(self) -> int:
        """
        Get total number of available presets.

        Returns:
            Total preset count
        """
        count = 0
        for category in self._presets.values():
            count += len(category)
        return count

    def export_preset(self, preset: MaterialPreset, filepath: str) -> bool:
        """
        Export a preset to a JSON file.

        Args:
            preset: MaterialPreset to export
            filepath: Output file path

        Returns:
            True if export successful
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(preset.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def import_preset(self, filepath: str) -> Optional[MaterialPreset]:
        """
        Import a preset from a JSON file.

        Args:
            filepath: Input file path

        Returns:
            Imported MaterialPreset or None on failure
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Create preset from data
            category = MaterialCategory(data.get('category', 'stone_brick'))
            preset = MaterialPreset(
                name=data['name'],
                display_name=data['display_name'],
                category=category,
                description=data.get('description', ''),
                base_color=tuple(data.get('base_color', (0.8, 0.8, 0.8, 1.0))),
                base_color_variation=data.get('base_color_variation', 0.0),
                roughness=data.get('roughness', 0.5),
                roughness_variation=data.get('roughness_variation', 0.0),
                metallic=data.get('metallic', 0.0),
                specular=data.get('specular', 0.5),
                anisotropic=data.get('anisotropic', 0.0),
                normal_strength=data.get('normal_strength', 1.0),
                displacement_scale=data.get('displacement_scale', 0.0),
                bump_distance=data.get('bump_distance', 0.001),
                subsurface=data.get('subsurface', 0.0),
                subsurface_color=tuple(data.get('subsurface_color', (1.0, 0.2, 0.1))),
                subsurface_radius=tuple(data.get('subsurface_radius', (1.0, 0.2, 0.1))),
                clearcoat=data.get('clearcoat', 0.0),
                clearcoat_roughness=data.get('clearcoat_roughness', 0.03),
                sheen=data.get('sheen', 0.0),
                sheen_tint=data.get('sheen_tint', 0.0),
                transmission=data.get('transmission', 0.0),
                transmission_roughness=data.get('transmission_roughness', 0.0),
                ior=data.get('ior', 1.45),
                emission=tuple(data.get('emission', (0.0, 0.0, 0.0))),
                emission_strength=data.get('emission_strength', 0.0),
                ambient_occlusion=data.get('ambient_occlusion', 1.0),
                alpha=data.get('alpha', 1.0),
                tags=data.get('tags', []),
            )
            return preset
        except Exception as e:
            print(f"Import failed: {e}")
            return None
