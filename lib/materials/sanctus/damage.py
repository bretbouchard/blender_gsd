"""
Sanctus Damage Tools - Extended Damage Generation
==================================================

Extended damage generation tools for creating realistic
damage effects including scratches, dents, paint chips,
burn marks, water damage, and more.
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
import math
import random

try:
    import bpy
    from bpy.types import Image, Material, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Image = Any
    Material = Any
    ShaderNodeTree = Any


class DamageType(Enum):
    """Types of damage effects."""
    SCRATCHES = "scratches"
    DENTS = "dents"
    PAINT_CHIPS = "paint_chips"
    CRACKS = "cracks"
    BURN_MARKS = "burn_marks"
    WATER_DAMAGE = "water_damage"
    BULLET_HOLES = "bullet_holes"
    IMPACT_DAMAGE = "impact_damage"
    ABRASION = "abrasion"
    CORROSION = "corrosion"
    RUST = "rust"
    PEELING = "peeling"


@dataclass
class DamageParameters:
    """Parameters for damage generation."""
    damage_type: DamageType = DamageType.SCRATCHES
    intensity: float = 0.5
    scale: float = 1.0
    seed: int = 0

    # Scratches
    scratch_length: float = 0.1
    scratch_width: float = 0.002
    scratch_depth: float = 0.001
    scratch_density: float = 50.0
    scratch_direction: Tuple[float, float, float] = (1, 0, 0)

    # Dents
    dent_size: float = 0.05
    dent_depth: float = 0.01
    dent_density: float = 20.0
    dent_sharpness: float = 0.5

    # Paint chips
    chip_size_min: float = 0.01
    chip_size_max: float = 0.05
    chip_edge_sharpness: float = 0.8
    chip_coverage: float = 0.3

    # Cracks
    crack_width: float = 0.005
    crack_branching: int = 3
    crack_depth: float = 0.02
    crack_length: float = 0.5

    # Burns
    burn_intensity: float = 0.5
    burn_size: float = 0.1
    burn_edge_softness: float = 0.3

    # Water damage
    water_stain_intensity: float = 0.3
    water_spread: float = 0.5
    water_color: Tuple[float, float, float] = (0.8, 0.75, 0.7)


class DamageTools:
    """
    Extended damage generation tools.

    Provides static methods for creating various types of
    damage patterns as materials, textures, and normal maps.
    """

    @staticmethod
    def create_scratch_material(
        length: float = 0.1,
        depth: float = 0.001,
        density: float = 50,
        width: float = 0.002,
        direction: Tuple[float, float, float] = (1, 0, 0),
        seed: int = 0,
        color: Tuple[float, float, float] = (0.3, 0.3, 0.35),
    ) -> Dict[str, Any]:
        """
        Create a procedural scratch material configuration.

        Args:
            length: Average scratch length (0.001 - 1.0)
            depth: Scratch depth for normal/bump (0.0001 - 0.1)
            density: Number of scratches per unit area (1.0 - 500.0)
            width: Scratch width (0.0001 - 0.1)
            direction: Primary scratch direction vector
            seed: Random seed for reproducibility
            color: Scratch base color

        Returns:
            Dictionary containing scratch material node configuration
        """
        return {
            "type": "scratch_material",
            "parameters": {
                "length": max(0.001, min(1.0, length)),
                "depth": max(0.0001, min(0.1, depth)),
                "density": max(1.0, min(500.0, density)),
                "width": max(0.0001, min(0.1, width)),
                "direction": direction,
                "seed": seed,
                "color": color,
            },
            "node_config": {
                "wave_texture_scale": 1.0 / length,
                "noise_distortion": 0.5,
                "voronoi_randomness": 0.8,
                "mix_factor": depth * 10,
                "normal_strength": depth * 100,
                "color_ramp_positions": [0.0, width, width * 2, 1.0],
                "color_ramp_colors": [color, (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0)],
            },
            "shader_setup": {
                "diffuse_color": color,
                "roughness": 0.7 + depth * 0.2,
                "normal_map_strength": depth * 50,
            }
        }

    @staticmethod
    def create_dent_normal_map(
        size: float = 0.05,
        depth: float = 0.01,
        density: float = 20,
        sharpness: float = 0.5,
        seed: int = 0,
        resolution: int = 1024,
    ) -> Dict[str, Any]:
        """
        Create a procedural dent normal map configuration.

        Args:
            size: Average dent size (0.01 - 0.5)
            depth: Dent depth (0.001 - 0.1)
            density: Number of dents per unit area (1.0 - 200.0)
            sharpness: Edge sharpness of dents (0.0 - 1.0)
            seed: Random seed for reproducibility
            resolution: Texture resolution for baked output

        Returns:
            Dictionary containing dent normal map configuration
        """
        return {
            "type": "dent_normal_map",
            "parameters": {
                "size": max(0.01, min(0.5, size)),
                "depth": max(0.001, min(0.1, depth)),
                "density": max(1.0, min(200.0, density)),
                "sharpness": max(0.0, min(1.0, sharpness)),
                "seed": seed,
                "resolution": resolution,
            },
            "node_config": {
                "voronoi_scale": 1.0 / size,
                "voronoi_randomness": 0.7,
                "smooth_radius": size * (1.0 - sharpness) * 0.5,
                "height_multiplier": depth * 100,
                "invert_height": True,
                "normal_strength": depth * 80,
            },
            "generation_steps": [
                "Create Voronoi texture for dent positions",
                "Apply Gaussian blur for smoothness",
                "Invert for concave effect",
                "Convert height to normal map",
            ]
        }

    @staticmethod
    def create_peeling_paint(
        base_color: Tuple[float, float, float] = (0.8, 0.2, 0.1),
        under_color: Tuple[float, float, float] = (0.5, 0.5, 0.55),
        peel_amount: float = 0.3,
        chip_size_min: float = 0.02,
        chip_size_max: float = 0.1,
        edge_roughness: float = 0.8,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a peeling paint material configuration.

        Args:
            base_color: Top layer paint color
            under_color: Underlying surface color
            peel_amount: Amount of paint peeled (0.0 - 1.0)
            chip_size_min: Minimum chip size
            chip_size_max: Maximum chip size
            edge_roughness: Roughness of chip edges
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing peeling paint material configuration
        """
        return {
            "type": "peeling_paint",
            "parameters": {
                "base_color": base_color,
                "under_color": under_color,
                "peel_amount": max(0.0, min(1.0, peel_amount)),
                "chip_size_min": max(0.005, min(0.1, chip_size_min)),
                "chip_size_max": max(chip_size_min, min(0.2, chip_size_max)),
                "edge_roughness": max(0.0, min(1.0, edge_roughness)),
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": 1.0 / chip_size_max,
                "voronoi_randomness": 0.6,
                "threshold": 1.0 - peel_amount,
                "edge_feather": edge_roughness * 0.3,
                "bump_height": 0.005,
            },
            "layer_setup": {
                "base_layer": {
                    "color": base_color,
                    "roughness": 0.3,
                    "metallic": 0.0,
                },
                "under_layer": {
                    "color": under_color,
                    "roughness": 0.6,
                    "metallic": 0.1,
                },
            }
        }

    @staticmethod
    def create_burn_marks(
        intensity: float = 0.5,
        size: float = 0.1,
        edge_softness: float = 0.3,
        center_color: Tuple[float, float, float] = (0.1, 0.08, 0.05),
        edge_color: Tuple[float, float, float] = (0.3, 0.15, 0.05),
        outer_color: Tuple[float, float, float] = (0.5, 0.35, 0.25),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a burn marks material configuration.

        Args:
            intensity: Burn intensity (0.0 - 1.0)
            size: Average burn mark size (0.01 - 0.5)
            edge_softness: Softness of burn edges (0.0 - 1.0)
            center_color: Color at burn center (charred)
            edge_color: Color at burn edge
            outer_color: Color of surrounding heat damage
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing burn marks material configuration
        """
        return {
            "type": "burn_marks",
            "parameters": {
                "intensity": max(0.0, min(1.0, intensity)),
                "size": max(0.01, min(0.5, size)),
                "edge_softness": max(0.0, min(1.0, edge_softness)),
                "center_color": center_color,
                "edge_color": edge_color,
                "outer_color": outer_color,
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": 1.0 / size,
                "noise_distortion": edge_softness,
                "color_ramp_positions": [0.0, 0.3, 0.6, 1.0],
                "color_ramp_colors": [center_color, edge_color, outer_color, (1, 1, 1)],
                "roughness_variation": intensity * 0.4,
            },
            "shader_setup": {
                "center_roughness": 0.95,
                "edge_roughness": 0.7,
                "normal_intensity": intensity * 0.3,
            }
        }

    @staticmethod
    def create_water_damage(
        stain_color: Tuple[float, float, float] = (0.8, 0.75, 0.7),
        intensity: float = 0.3,
        spread: float = 0.5,
        streak_length: float = 0.3,
        ring_effect: bool = True,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a water damage material configuration.

        Args:
            stain_color: Color of water stains
            intensity: Damage intensity (0.0 - 1.0)
            spread: How much stains spread (0.0 - 1.0)
            streak_length: Length of water streaks
            ring_effect: Include concentric ring effect
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing water damage material configuration
        """
        return {
            "type": "water_damage",
            "parameters": {
                "stain_color": stain_color,
                "intensity": max(0.0, min(1.0, intensity)),
                "spread": max(0.0, min(1.0, spread)),
                "streak_length": max(0.1, min(1.0, streak_length)),
                "ring_effect": ring_effect,
                "seed": seed,
            },
            "node_config": {
                "noise_scale": 10.0,
                "wave_scale": streak_length * 5,
                "spread_distortion": spread * 2,
                "ring_frequency": 15 if ring_effect else 0,
                "color_intensity": intensity,
            },
            "shader_setup": {
                "stain_roughness": 0.4,
                "base_roughness": 0.6,
                "normal_subtlety": 0.2,
            }
        }

    @staticmethod
    def create_crack_network(
        width: float = 0.005,
        branching: int = 3,
        length: float = 0.5,
        depth: float = 0.02,
        color: Tuple[float, float, float] = (0.15, 0.12, 0.1),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a crack network material configuration.

        Args:
            width: Crack width (0.001 - 0.05)
            branching: Number of branch points (1 - 10)
            length: Average crack length (0.1 - 2.0)
            depth: Crack depth (0.001 - 0.1)
            color: Crack interior color
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing crack network configuration
        """
        return {
            "type": "crack_network",
            "parameters": {
                "width": max(0.001, min(0.05, width)),
                "branching": max(1, min(10, branching)),
                "length": max(0.1, min(2.0, length)),
                "depth": max(0.001, min(0.1, depth)),
                "color": color,
                "seed": seed,
            },
            "node_config": {
                "voronoi_edge_mode": True,
                "voronoi_scale": 1.0 / length,
                "noise_detail": branching,
                "noise_distortion": branching * 0.5,
                "edge_threshold": width,
                "normal_depth": depth * 50,
            },
            "shader_setup": {
                "crack_roughness": 0.9,
                "crack_metallic": 0.0,
            }
        }

    @staticmethod
    def create_abrasion_pattern(
        intensity: float = 0.4,
        direction: Tuple[float, float, float] = (1, 0, 0),
        scale: float = 0.1,
        variation: float = 0.3,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create an abrasion/wear pattern configuration.

        Args:
            intensity: Abrasion intensity (0.0 - 1.0)
            direction: Primary abrasion direction
            scale: Pattern scale (0.01 - 1.0)
            variation: Pattern variation (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing abrasion pattern configuration
        """
        return {
            "type": "abrasion",
            "parameters": {
                "intensity": max(0.0, min(1.0, intensity)),
                "direction": direction,
                "scale": max(0.01, min(1.0, scale)),
                "variation": max(0.0, min(1.0, variation)),
                "seed": seed,
            },
            "node_config": {
                "wave_scale": 1.0 / scale,
                "noise_variation": variation,
                "anisotropy": 0.8,
                "roughness_increase": intensity * 0.3,
            },
            "shader_setup": {
                "base_roughness": 0.4,
                "abraded_roughness": 0.4 + intensity * 0.4,
            }
        }

    @staticmethod
    def create_corrosion_effect(
        coverage: float = 0.3,
        color: Tuple[float, float, float] = (0.4, 0.5, 0.2),
        pitting_depth: float = 0.01,
        spread: float = 0.5,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a corrosion/pitting effect configuration.

        Args:
            coverage: Corrosion coverage (0.0 - 1.0)
            color: Corrosion color (green patina, etc.)
            pitting_depth: Depth of pits (0.001 - 0.05)
            spread: How much corrosion spreads (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing corrosion effect configuration
        """
        return {
            "type": "corrosion",
            "parameters": {
                "coverage": max(0.0, min(1.0, coverage)),
                "color": color,
                "pitting_depth": max(0.001, min(0.05, pitting_depth)),
                "spread": max(0.0, min(1.0, spread)),
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": 20.0,
                "noise_spread": spread * 2,
                "threshold": 1.0 - coverage,
                "pitting_noise": pitting_depth * 100,
                "normal_strength": pitting_depth * 30,
            },
            "shader_setup": {
                "corrosion_roughness": 0.7,
                "corrosion_metallic": 0.2,
                "base_metallic": 0.9,
            }
        }

    @staticmethod
    def create_bullet_hole(
        size: float = 0.02,
        edge_cracks: bool = True,
        depth: float = 0.03,
        rim_elevation: float = 0.005,
        position: Tuple[float, float, float] = (0, 0, 0),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a bullet hole damage configuration.

        Args:
            size: Hole diameter (0.005 - 0.1)
            edge_cracks: Include radial cracks from edge
            depth: Hole depth (0.01 - 0.1)
            rim_elevation: Height of pushed-up rim
            position: UV position of bullet hole
            seed: Random seed for crack pattern

        Returns:
            Dictionary containing bullet hole configuration
        """
        return {
            "type": "bullet_hole",
            "parameters": {
                "size": max(0.005, min(0.1, size)),
                "edge_cracks": edge_cracks,
                "depth": max(0.01, min(0.1, depth)),
                "rim_elevation": max(0.0, min(0.02, rim_elevation)),
                "position": position,
                "seed": seed,
            },
            "node_config": {
                "inner_radius": size * 0.3,
                "outer_radius": size * 0.5,
                "rim_radius": size * 0.7,
                "crack_spread": size * 3 if edge_cracks else 0,
                "crack_count": 6 if edge_cracks else 0,
                "depth_value": depth,
                "rim_height": rim_elevation,
            },
            "shader_setup": {
                "inner_darkness": 0.9,
                "rim_brightness": 0.3,
            }
        }

    @staticmethod
    def create_impact_damage(
        size: float = 0.1,
        intensity: float = 0.7,
        debris: bool = True,
        center_crater: bool = True,
        radial_cracks: int = 5,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create an impact damage configuration.

        Args:
            size: Impact area size (0.02 - 0.5)
            intensity: Damage intensity (0.0 - 1.0)
            debris: Include debris scatter
            center_crater: Include center crater
            radial_cracks: Number of radial cracks
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing impact damage configuration
        """
        return {
            "type": "impact_damage",
            "parameters": {
                "size": max(0.02, min(0.5, size)),
                "intensity": max(0.0, min(1.0, intensity)),
                "debris": debris,
                "center_crater": center_crater,
                "radial_cracks": max(0, min(12, radial_cracks)),
                "seed": seed,
            },
            "node_config": {
                "crater_depth": intensity * 0.05,
                "crater_radius": size * 0.3,
                "crack_length": size * 2,
                "debris_count": int(intensity * 30) if debris else 0,
                "debris_size_range": (size * 0.05, size * 0.2),
            },
            "shader_setup": {
                "crater_roughness": 0.9,
                "crack_roughness": 0.8,
                "debris_roughness": 0.7,
            }
        }

    @staticmethod
    def generate_damage_texture(
        damage_type: DamageType,
        resolution: int = 1024,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a procedural damage texture.

        Args:
            damage_type: Type of damage to generate
            resolution: Texture resolution
            params: Additional parameters for specific damage type

        Returns:
            Dictionary containing texture data and metadata
        """
        params = params or {}

        if damage_type == DamageType.SCRATCHES:
            config = DamageTools.create_scratch_material(**params)
        elif damage_type == DamageType.DENTS:
            config = DamageTools.create_dent_normal_map(**params)
        elif damage_type == DamageType.PAINT_CHIPS:
            config = DamageTools.create_peeling_paint(**params)
        elif damage_type == DamageType.CRACKS:
            config = DamageTools.create_crack_network(**params)
        elif damage_type == DamageType.BURN_MARKS:
            config = DamageTools.create_burn_marks(**params)
        elif damage_type == DamageType.WATER_DAMAGE:
            config = DamageTools.create_water_damage(**params)
        elif damage_type == DamageType.BULLET_HOLES:
            config = DamageTools.create_bullet_hole(**params)
        elif damage_type == DamageType.IMPACT_DAMAGE:
            config = DamageTools.create_impact_damage(**params)
        elif damage_type == DamageType.ABRASION:
            config = DamageTools.create_abrasion_pattern(**params)
        elif damage_type == DamageType.CORROSION:
            config = DamageTools.create_corrosion_effect(**params)
        else:
            return None

        config["resolution"] = resolution
        return config

    @staticmethod
    def apply_to_material(
        material: Material,
        damage_type: DamageType,
        intensity: float = 0.5,
        blend_mode: str = "overlay",
        **kwargs,
    ) -> Material:
        """
        Apply damage to an existing Blender material.

        Args:
            material: Blender material to modify
            damage_type: Type of damage to apply
            intensity: Damage intensity (0.0 - 1.0)
            blend_mode: How to blend damage with base material
            **kwargs: Additional parameters for damage type

        Returns:
            Modified material with damage applied
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply damage to materials")

        if not material.use_nodes:
            material.use_nodes = True

        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        # Get existing principled BSDF
        bsdf = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break

        if not bsdf:
            bsdf = nodes.new('ShaderNodeBsdfPrincipled')

        # Create damage texture nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')

        # Configure based on damage type
        if damage_type == DamageType.SCRATCHES:
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 50.0 * kwargs.get('density', 50.0) / 50.0
            noise.inputs['Detail'].default_value = 8

            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

            # Mix with roughness
            mix_rgb = nodes.new('ShaderNodeMixRGB')
            mix_rgb.blend_type = 'MULTIPLY'
            mix_rgb.inputs['Fac'].default_value = intensity

            # Connect to roughness
            original_roughness = bsdf.inputs['Roughness'].default_value
            mix_rgb.inputs['Color1'].default_value = (original_roughness,) * 3 + (1,)
            mix_rgb.inputs['Color2'].default_value = (0.9,) * 3 + (1,)

            links.new(noise.outputs['Fac'], mix_rgb.inputs['Fac'])
            links.new(mix_rgb.outputs['Color'], bsdf.inputs['Roughness'])

        elif damage_type == DamageType.DENTS:
            voronoi = nodes.new('ShaderNodeTexVoronoi')
            voronoi.inputs['Scale'].default_value = 20.0 / kwargs.get('size', 0.05)
            voronoi.distance = 'MINKOWSKI'

            bump = nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value = intensity * 0.1
            bump.inputs['Distance'].default_value = kwargs.get('depth', 0.01)

            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], voronoi.inputs['Vector'])
            links.new(voronoi.outputs['Distance'], bump.inputs['Height'])
            links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

        elif damage_type == DamageType.BURN_MARKS:
            voronoi = nodes.new('ShaderNodeTexVoronoi')
            voronoi.inputs['Scale'].default_value = 10.0 / kwargs.get('size', 0.1)

            color_ramp = nodes.new('ShaderNodeValToRGB')
            color_ramp.color_ramp.elements[0].color = (0.1, 0.08, 0.05, 1.0)
            color_ramp.color_ramp.elements[1].color = (0.3, 0.15, 0.05, 1.0)

            mix_color = nodes.new('ShaderNodeMixRGB')
            mix_color.blend_type = 'MULTIPLY'
            mix_color.inputs['Fac'].default_value = intensity

            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], voronoi.inputs['Vector'])
            links.new(voronoi.outputs['Distance'], color_ramp.inputs['Fac'])
            links.new(color_ramp.outputs['Color'], mix_color.inputs['Color2'])

            # Mix with base color
            # Note: This is a simplified version
            pass

        return material

    @staticmethod
    def combine_damage_types(
        *damage_configs: Dict[str, Any],
        blend_order: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Combine multiple damage configurations into one.

        Args:
            *damage_configs: Multiple damage configuration dictionaries
            blend_order: Order to blend damage types

        Returns:
            Combined damage configuration
        """
        combined = {
            "type": "combined_damage",
            "layers": [],
            "blend_order": blend_order or [],
        }

        for config in damage_configs:
            if "type" in config:
                combined["layers"].append(config)
                if config["type"] not in combined["blend_order"]:
                    combined["blend_order"].append(config["type"])

        return combined
