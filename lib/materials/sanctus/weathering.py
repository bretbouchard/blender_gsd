"""
Sanctus Weathering Tools - Extended Weathering Generation
=========================================================

Extended weathering generation tools for creating realistic
aging and environmental effects including dust, dirt, rust,
sun bleaching, moss growth, and more.
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


class WeatheringType(Enum):
    """Types of weathering effects."""
    DUST = "dust"
    DIRT = "dirt"
    EDGE_WEAR = "edge_wear"
    RUST = "rust"
    SUN_BLEACHING = "sun_bleaching"
    MOSS = "moss"
    MOLD = "mold"
    PATINA = "patina"
    WATER_STREAKS = "water_streaks"
    FADE = "fade"
    POLLUTION = "pollution"
    SALT_DEPOSITS = "salt_deposits"


@dataclass
class WeatheringParameters:
    """Parameters for weathering generation."""
    weathering_type: WeatheringType = WeatheringType.DUST
    intensity: float = 0.5
    scale: float = 1.0
    seed: int = 0

    # Gravity-dependent effects
    gravity_direction: Tuple[float, float, float] = (0, 0, -1)

    # Color adjustments
    base_color_modification: float = 0.0
    saturation_shift: float = 0.0
    brightness_shift: float = 0.0

    # Surface modifications
    roughness_increase: float = 0.0
    normal_detail: float = 0.0


class WeatheringTools:
    """
    Extended weathering generation tools.

    Provides static methods for creating various types of
    weathering and aging effects as materials and textures.
    """

    @staticmethod
    def create_dust_layer(
        amount: float = 0.3,
        color: Tuple[float, float, float] = (0.9, 0.85, 0.75),
        gravity_direction: Tuple[float, float, float] = (0, 0, -1),
        roughness: float = 0.9,
        variation: float = 0.2,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a dust layer material configuration.

        Args:
            amount: Dust amount (0.0 - 1.0)
            color: Dust color
            gravity_direction: Direction dust accumulates
            roughness: Dust surface roughness (0.0 - 1.0)
            variation: Color variation amount (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing dust layer configuration
        """
        return {
            "type": "dust_layer",
            "parameters": {
                "amount": max(0.0, min(1.0, amount)),
                "color": color,
                "gravity_direction": gravity_direction,
                "roughness": max(0.0, min(1.0, roughness)),
                "variation": max(0.0, min(1.0, variation)),
                "seed": seed,
            },
            "node_config": {
                "noise_scale": 5.0,
                "noise_detail": 3,
                "normal_factor": 0.5,  # More dust on upward-facing surfaces
                "color_variation_noise": variation * 10,
            },
            "shader_setup": {
                "dust_roughness": roughness,
                "dust_specular": 0.2,
                "dust_metallic": 0.0,
                "blend_mode": "mix",
            },
            "gravity_mask": {
                "use_normal": True,
                "direction": gravity_direction,
                "falloff": 0.3,
            }
        }

    @staticmethod
    def create_dirt_accumulation(
        crevice_intensity: float = 0.7,
        surface_dirt: float = 0.2,
        color: Tuple[float, float, float] = (0.2, 0.15, 0.1),
        wetness: float = 0.0,
        grain_size: float = 0.01,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a dirt accumulation material configuration.

        Args:
            crevice_intensity: Dirt intensity in crevices (0.0 - 1.0)
            surface_dirt: General surface dirt amount (0.0 - 1.0)
            color: Dirt color
            wetness: Wetness amount for darker dirt (0.0 - 1.0)
            grain_size: Size of dirt particles
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing dirt accumulation configuration
        """
        return {
            "type": "dirt_accumulation",
            "parameters": {
                "crevice_intensity": max(0.0, min(1.0, crevice_intensity)),
                "surface_dirt": max(0.0, min(1.0, surface_dirt)),
                "color": color,
                "wetness": max(0.0, min(1.0, wetness)),
                "grain_size": max(0.001, min(0.1, grain_size)),
                "seed": seed,
            },
            "node_config": {
                "ao_multiplier": crevice_intensity,
                "noise_scale": 1.0 / grain_size,
                "noise_detail": 4,
                "wet_darkening": wetness * 0.3,
            },
            "shader_setup": {
                "dirt_roughness": 0.85,
                "wet_roughness": 0.3 if wetness > 0 else 0.85,
                "dirt_specular": 0.15,
                "blend_mode": "multiply",
            },
            "crevice_detection": {
                "use_ao": True,
                "use_curvature": True,
                "ao_samples": 16,
            }
        }

    @staticmethod
    def create_sun_bleaching(
        intensity: float = 0.4,
        exposure_direction: Tuple[float, float, float] = (0, 1, 0),
        edge_fade: float = 0.3,
        color_shift: float = 0.2,
        saturation_loss: float = 0.3,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a sun bleaching/fading material configuration.

        Args:
            intensity: Bleaching intensity (0.0 - 1.0)
            exposure_direction: Direction of sun exposure
            edge_fade: Softness of bleaching edges (0.0 - 1.0)
            color_shift: Color shift towards yellow/white (0.0 - 1.0)
            saturation_loss: Saturation reduction (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing sun bleaching configuration
        """
        return {
            "type": "sun_bleaching",
            "parameters": {
                "intensity": max(0.0, min(1.0, intensity)),
                "exposure_direction": exposure_direction,
                "edge_fade": max(0.0, min(1.0, edge_fade)),
                "color_shift": max(0.0, min(1.0, color_shift)),
                "saturation_loss": max(0.0, min(1.0, saturation_loss)),
                "seed": seed,
            },
            "node_config": {
                "normal_factor": 0.8,  # Based on surface normal
                "falloff_exponent": 1.0 + edge_fade,
                "noise_variation": edge_fade * 0.5,
                "target_hue": 60,  # Yellow shift
                "saturation_factor": 1.0 - saturation_loss,
            },
            "shader_setup": {
                "brightness_increase": intensity * 0.3,
                "contrast_reduction": intensity * 0.2,
                "roughness_increase": intensity * 0.1,
            },
            "exposure_mask": {
                "use_normal": True,
                "direction": exposure_direction,
                "falloff_power": 2.0,
            }
        }

    @staticmethod
    def create_rust_layer(
        base_metal_color: Tuple[float, float, float] = (0.6, 0.6, 0.65),
        rust_color: Tuple[float, float, float] = (0.4, 0.2, 0.1),
        coverage: float = 0.3,
        edge_bleed: float = 0.2,
        pitting: float = 0.5,
        flaking: float = 0.3,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a rust layer material configuration.

        Args:
            base_metal_color: Color of unrusted metal
            rust_color: Color of rust
            coverage: Rust coverage amount (0.0 - 1.0)
            edge_bleed: Rust bleeding from edges (0.0 - 1.0)
            pitting: Amount of surface pitting (0.0 - 1.0)
            flaking: Amount of rust flaking (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing rust layer configuration
        """
        return {
            "type": "rust_layer",
            "parameters": {
                "base_metal_color": base_metal_color,
                "rust_color": rust_color,
                "coverage": max(0.0, min(1.0, coverage)),
                "edge_bleed": max(0.0, min(1.0, edge_bleed)),
                "pitting": max(0.0, min(1.0, pitting)),
                "flaking": max(0.0, min(1.0, flaking)),
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": 15.0,
                "voronoi_randomness": 0.8,
                "noise_bleed": edge_bleed * 2,
                "threshold": 1.0 - coverage,
                "pitting_noise_scale": 50.0 * pitting,
                "flaking_voronoi": 10.0 / (1.0 + flaking),
            },
            "shader_setup": {
                "rust_roughness": 0.8,
                "rust_metallic": 0.0,
                "metal_roughness": 0.4,
                "metal_metallic": 1.0,
            },
            "layers": {
                "base_metal": {
                    "color": base_metal_color,
                    "roughness": 0.4,
                    "metallic": 1.0,
                },
                "rust": {
                    "color": rust_color,
                    "roughness": 0.8,
                    "metallic": 0.0,
                    "normal_intensity": pitting * 0.5,
                },
            }
        }

    @staticmethod
    def create_mold_growth(
        intensity: float = 0.2,
        prefer_damp: bool = True,
        color: Tuple[float, float, float] = (0.2, 0.3, 0.15),
        spread_pattern: str = "organic",
        density: float = 0.5,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a mold/mildew growth material configuration.

        Args:
            intensity: Growth intensity (0.0 - 1.0)
            prefer_damp: Whether mold prefers damp areas
            color: Mold color
            spread_pattern: Pattern type ("organic", "spots", "patches")
            density: Mold density (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing mold growth configuration
        """
        pattern_config = {
            "organic": {"voronoi_scale": 8.0, "noise_distortion": 1.0},
            "spots": {"voronoi_scale": 20.0, "noise_distortion": 0.3},
            "patches": {"voronoi_scale": 5.0, "noise_distortion": 0.8},
        }

        return {
            "type": "mold_growth",
            "parameters": {
                "intensity": max(0.0, min(1.0, intensity)),
                "prefer_damp": prefer_damp,
                "color": color,
                "spread_pattern": spread_pattern,
                "density": max(0.0, min(1.0, density)),
                "seed": seed,
            },
            "node_config": {
                **pattern_config.get(spread_pattern, pattern_config["organic"]),
                "noise_detail": 4,
                "threshold": 1.0 - density,
                "color_variation": 0.2,
            },
            "shader_setup": {
                "mold_roughness": 0.9,
                "mold_specular": 0.1,
                "subsurface": 0.2,
                "subsurface_color": color,
            },
            "dampness_mask": {
                "enabled": prefer_damp,
                "use_ao": True,
                "ao_threshold": 0.5,
            }
        }

    @staticmethod
    def create_patina(
        coverage: float = 0.5,
        color: Tuple[float, float, float] = (0.2, 0.5, 0.5),
        variation: float = 0.3,
        base_metal_color: Tuple[float, float, float] = (0.7, 0.55, 0.3),
        streaking: bool = True,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a copper/bronze patina material configuration.

        Args:
            coverage: Patina coverage amount (0.0 - 1.0)
            color: Patina color (typically green/teal)
            variation: Color variation (0.0 - 1.0)
            base_metal_color: Base metal color
            streaking: Include vertical streaking effect
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing patina configuration
        """
        return {
            "type": "patina",
            "parameters": {
                "coverage": max(0.0, min(1.0, coverage)),
                "color": color,
                "variation": max(0.0, min(1.0, variation)),
                "base_metal_color": base_metal_color,
                "streaking": streaking,
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": 10.0,
                "voronoi_randomness": 0.7,
                "noise_variation": variation * 2,
                "streak_wave_scale": 3.0 if streaking else 0,
                "streak_direction": (0, -1, 0),
            },
            "shader_setup": {
                "patina_roughness": 0.6,
                "patina_metallic": 0.0,
                "metal_roughness": 0.3,
                "metal_metallic": 1.0,
            },
            "color_variation": {
                "hue_range": (150, 190),  # Green to teal
                "saturation_range": (0.4, 0.7),
                "value_range": (0.3, 0.6),
            }
        }

    @staticmethod
    def create_water_streaks(
        length: float = 0.5,
        width: float = 0.02,
        density: float = 10.0,
        stain_color: Tuple[float, float, float] = (0.6, 0.55, 0.5),
        deposit_amount: float = 0.2,
        direction: Tuple[float, float, float] = (0, -1, 0),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a water streak/rain stain material configuration.

        Args:
            length: Streak length (0.1 - 2.0)
            width: Streak width (0.005 - 0.1)
            density: Number of streaks per unit area
            stain_color: Color of water stains
            deposit_amount: Mineral deposit amount (0.0 - 1.0)
            direction: Streak direction
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing water streak configuration
        """
        return {
            "type": "water_streaks",
            "parameters": {
                "length": max(0.1, min(2.0, length)),
                "width": max(0.005, min(0.1, width)),
                "density": max(1.0, min(50.0, density)),
                "stain_color": stain_color,
                "deposit_amount": max(0.0, min(1.0, deposit_amount)),
                "direction": direction,
                "seed": seed,
            },
            "node_config": {
                "wave_scale_y": length * 2,
                "wave_scale_x": 1.0 / width,
                "noise_distortion": 0.5,
                "noise_scale": density,
                "gradient_direction": direction,
            },
            "shader_setup": {
                "stain_roughness": 0.4,
                "stain_specular": 0.4,
                "deposit_bump": deposit_amount * 0.01,
            }
        }

    @staticmethod
    def create_fade_effect(
        intensity: float = 0.5,
        uniformity: float = 0.3,
        saturation_loss: float = 0.4,
        brightness_change: float = 0.2,
        pattern: str = "uniform",
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a general fade/weathering material configuration.

        Args:
            intensity: Fade intensity (0.0 - 1.0)
            uniformity: How uniform the fade is (0.0 - 1.0)
            saturation_loss: Saturation reduction (0.0 - 1.0)
            brightness_change: Brightness change (-1.0 to 1.0)
            pattern: Pattern type ("uniform", "patchy", "edge")
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing fade effect configuration
        """
        pattern_config = {
            "uniform": {"noise_scale": 0.1, "noise_factor": 0.0},
            "patchy": {"noise_scale": 5.0, "noise_factor": 0.5},
            "edge": {"noise_scale": 3.0, "noise_factor": 0.3},
        }

        return {
            "type": "fade_effect",
            "parameters": {
                "intensity": max(0.0, min(1.0, intensity)),
                "uniformity": max(0.0, min(1.0, uniformity)),
                "saturation_loss": max(0.0, min(1.0, saturation_loss)),
                "brightness_change": max(-1.0, min(1.0, brightness_change)),
                "pattern": pattern,
                "seed": seed,
            },
            "node_config": {
                **pattern_config.get(pattern, pattern_config["uniform"]),
                "saturation_factor": 1.0 - (saturation_loss * intensity),
                "brightness_factor": 1.0 + (brightness_change * intensity),
                "contrast_factor": 1.0 - (intensity * 0.2),
            },
            "shader_setup": {
                "roughness_increase": intensity * 0.2,
                "specular_decrease": intensity * 0.1,
            }
        }

    @staticmethod
    def create_pollution_staining(
        amount: float = 0.3,
        color: Tuple[float, float, float] = (0.3, 0.28, 0.25),
        gravity_effect: float = 0.5,
        streaking: bool = True,
        particulate: float = 0.2,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a pollution/soot staining material configuration.

        Args:
            amount: Staining amount (0.0 - 1.0)
            color: Pollution color
            gravity_effect: How much gravity affects deposition (0.0 - 1.0)
            streaking: Include streaking effect
            particulate: Amount of visible particles (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing pollution staining configuration
        """
        return {
            "type": "pollution_staining",
            "parameters": {
                "amount": max(0.0, min(1.0, amount)),
                "color": color,
                "gravity_effect": max(0.0, min(1.0, gravity_effect)),
                "streaking": streaking,
                "particulate": max(0.0, min(1.0, particulate)),
                "seed": seed,
            },
            "node_config": {
                "noise_scale": 8.0,
                "noise_detail": 4,
                "gravity_mask_strength": gravity_effect,
                "streak_scale": 2.0 if streaking else 0,
                "particulate_scale": 50.0 * particulate if particulate > 0 else 0,
            },
            "shader_setup": {
                "stain_roughness": 0.7,
                "stain_specular": 0.2,
                "particulate_bump": particulate * 0.005,
            }
        }

    @staticmethod
    def create_salt_deposits(
        coverage: float = 0.2,
        crystal_size: float = 0.01,
        color: Tuple[float, float, float] = (0.95, 0.93, 0.9),
        prefer_edges: bool = True,
        dampness_threshold: float = 0.3,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a salt deposit/efflorescence material configuration.

        Args:
            coverage: Deposit coverage (0.0 - 1.0)
            crystal_size: Size of salt crystals
            color: Salt color
            prefer_edges: Whether deposits prefer edges/cracks
            dampness_threshold: Threshold for damp area preference
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing salt deposit configuration
        """
        return {
            "type": "salt_deposits",
            "parameters": {
                "coverage": max(0.0, min(1.0, coverage)),
                "crystal_size": max(0.001, min(0.05, crystal_size)),
                "color": color,
                "prefer_edges": prefer_edges,
                "dampness_threshold": max(0.0, min(1.0, dampness_threshold)),
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": 1.0 / crystal_size,
                "voronoi_randomness": 0.5,
                "edge_detection": prefer_edges,
                "threshold": 1.0 - coverage,
                "crystal_normal_strength": 0.3,
            },
            "shader_setup": {
                "salt_roughness": 0.4,
                "salt_specular": 0.6,
                "salt_metallic": 0.0,
                "subsurface": 0.3,
            }
        }

    @staticmethod
    def create_edge_wear(
        intensity: float = 0.5,
        sharpness: float = 0.3,
        inner_radius: float = 0.1,
        noise_amount: float = 0.1,
        color: Optional[Tuple[float, float, float]] = None,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Create an edge wear/chipping material configuration.

        Args:
            intensity: Wear intensity (0.0 - 1.0)
            sharpness: Edge sharpness (0.0 - 1.0)
            inner_radius: How far wear extends from edge
            noise_amount: Amount of noise in wear pattern
            color: Optional under-color revealed by wear
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing edge wear configuration
        """
        return {
            "type": "edge_wear",
            "parameters": {
                "intensity": max(0.0, min(1.0, intensity)),
                "sharpness": max(0.0, min(1.0, sharpness)),
                "inner_radius": max(0.0, min(1.0, inner_radius)),
                "noise_amount": max(0.0, min(1.0, noise_amount)),
                "under_color": color,
                "seed": seed,
            },
            "node_config": {
                "use_geometry_nodes": True,
                "bevel_radius": inner_radius * 2,
                "noise_scale": noise_amount * 50,
                "threshold": 1.0 - intensity,
                "edge_feather": (1.0 - sharpness) * 0.3,
            },
            "shader_setup": {
                "wear_roughness_increase": intensity * 0.3,
                "wear_specular_decrease": intensity * 0.2,
            },
            "geometry_nodes_setup": {
                "use_bevel": True,
                "use_edge_angle": True,
                "min_angle": 30,
            }
        }

    @staticmethod
    def generate_weathering_texture(
        weathering_type: WeatheringType,
        resolution: int = 1024,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a procedural weathering texture.

        Args:
            weathering_type: Type of weathering to generate
            resolution: Texture resolution
            params: Additional parameters for specific weathering type

        Returns:
            Dictionary containing texture data and metadata
        """
        params = params or {}

        generators = {
            WeatheringType.DUST: WeatheringTools.create_dust_layer,
            WeatheringType.DIRT: WeatheringTools.create_dirt_accumulation,
            WeatheringType.EDGE_WEAR: WeatheringTools.create_edge_wear,
            WeatheringType.RUST: WeatheringTools.create_rust_layer,
            WeatheringType.SUN_BLEACHING: WeatheringTools.create_sun_bleaching,
            WeatheringType.MOSS: WeatheringTools.create_mold_growth,
            WeatheringType.MOLD: WeatheringTools.create_mold_growth,
            WeatheringType.PATINA: WeatheringTools.create_patina,
            WeatheringType.WATER_STREAKS: WeatheringTools.create_water_streaks,
            WeatheringType.FADE: WeatheringTools.create_fade_effect,
            WeatheringType.POLLUTION: WeatheringTools.create_pollution_staining,
            WeatheringType.SALT_DEPOSITS: WeatheringTools.create_salt_deposits,
        }

        generator = generators.get(weathering_type)
        if not generator:
            return None

        config = generator(**params)
        config["resolution"] = resolution
        return config

    @staticmethod
    def apply_to_material(
        material: Material,
        weathering_type: WeatheringType,
        intensity: float = 0.5,
        blend_mode: str = "overlay",
        **kwargs,
    ) -> Material:
        """
        Apply weathering to an existing Blender material.

        Args:
            material: Blender material to modify
            weathering_type: Type of weathering to apply
            intensity: Weathering intensity (0.0 - 1.0)
            blend_mode: How to blend with base material
            **kwargs: Additional parameters for weathering type

        Returns:
            Modified material with weathering applied
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply weathering to materials")

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

        # Create weathering texture nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        if weathering_type == WeatheringType.DUST:
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 5.0
            noise.inputs['Detail'].default_value = 3

            color_ramp = nodes.new('ShaderNodeValToRGB')
            dust_color = kwargs.get('color', (0.9, 0.85, 0.75))
            color_ramp.color_ramp.elements[1].color = (*dust_color, 1.0)

            mix_color = nodes.new('ShaderNodeMixRGB')
            mix_color.blend_type = blend_mode.upper()
            mix_color.inputs['Fac'].default_value = intensity

            links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
            links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
            links.new(color_ramp.outputs['Color'], mix_color.inputs['Color2'])
            links.new(mix_color.outputs['Color'], bsdf.inputs['Base Color'])

            # Adjust roughness
            original_roughness = bsdf.inputs['Roughness'].default_value
            bsdf.inputs['Roughness'].default_value = min(1.0, original_roughness + intensity * 0.3)

        elif weathering_type == WeatheringType.RUST:
            voronoi = nodes.new('ShaderNodeTexVoronoi')
            voronoi.inputs['Scale'].default_value = 15.0

            color_ramp = nodes.new('ShaderNodeValToRGB')
            rust_color = kwargs.get('rust_color', (0.4, 0.2, 0.1))
            base_color = kwargs.get('base_metal_color', (0.6, 0.6, 0.65))
            color_ramp.color_ramp.elements[0].color = (*rust_color, 1.0)
            color_ramp.color_ramp.elements[1].color = (*base_color, 1.0)

            mix_color = nodes.new('ShaderNodeMixRGB')
            mix_color.blend_type = 'MIX'
            mix_color.inputs['Fac'].default_value = intensity

            links.new(mapping.outputs['Vector'], voronoi.inputs['Vector'])
            links.new(voronoi.outputs['Distance'], color_ramp.inputs['Fac'])
            links.new(color_ramp.outputs['Color'], mix_color.inputs['Color2'])

            # Adjust metallic
            bsdf.inputs['Metallic'].default_value = 1.0 - intensity * kwargs.get('coverage', 0.3)
            bsdf.inputs['Roughness'].default_value = 0.4 + intensity * 0.4

        elif weathering_type == WeatheringType.EDGE_WEAR:
            # Edge wear requires geometry nodes or vertex painting
            # Simplified version using noise
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = kwargs.get('noise_amount', 0.1) * 50

            bump = nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value = intensity * 0.1

            links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
            links.new(noise.outputs['Fac'], bump.inputs['Height'])
            links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

            # Increase roughness at edges
            original_roughness = bsdf.inputs['Roughness'].default_value
            bsdf.inputs['Roughness'].default_value = min(1.0, original_roughness + intensity * 0.2)

        elif weathering_type == WeatheringType.SUN_BLEACHING:
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 3.0
            noise.inputs['Detail'].default_value = 2

            # Desaturate and brighten
            hue_sat = nodes.new('ShaderNodeHueSaturation')
            hue_sat.inputs['Saturation'].default_value = 1.0 - intensity * kwargs.get('saturation_loss', 0.3)
            hue_sat.inputs['Value'].default_value = 1.0 + intensity * kwargs.get('brightness_change', 0.2)

            links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
            # Apply saturation modification based on noise
            pass  # Complex node setup needed

        return material

    @staticmethod
    def combine_weathering_types(
        *weathering_configs: Dict[str, Any],
        blend_order: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Combine multiple weathering configurations into one.

        Args:
            *weathering_configs: Multiple weathering configuration dictionaries
            blend_order: Order to blend weathering types

        Returns:
            Combined weathering configuration
        """
        combined = {
            "type": "combined_weathering",
            "layers": [],
            "blend_order": blend_order or [],
        }

        for config in weathering_configs:
            if "type" in config:
                combined["layers"].append(config)
                if config["type"] not in combined["blend_order"]:
                    combined["blend_order"].append(config["type"])

        return combined

    @staticmethod
    def create_aged_material(
        base_material: Material,
        age_years: float = 10.0,
        exposure_level: str = "outdoor",
        climate: str = "temperate",
        maintenance: str = "none",
    ) -> Dict[str, Any]:
        """
        Create a complete aged material configuration.

        Automatically determines appropriate weathering based on
        age, exposure, climate, and maintenance factors.

        Args:
            base_material: Base material to age
            age_years: Age in years
            exposure_level: "indoor", "outdoor", "sheltered", "harsh"
            climate: "temperate", "tropical", "arid", "arctic", "coastal"
            maintenance: "none", "minimal", "regular", "well_maintained"

        Returns:
            Dictionary containing complete aged material configuration
        """
        # Calculate weathering factors based on parameters
        maintenance_factor = {"none": 1.0, "minimal": 0.7, "regular": 0.4, "well_maintained": 0.2}
        exposure_factor = {"indoor": 0.2, "sheltered": 0.5, "outdoor": 0.8, "harsh": 1.0}
        climate_factor = {"temperate": 1.0, "tropical": 1.3, "arid": 0.8, "arctic": 0.7, "coastal": 1.5}

        age_factor = min(1.0, age_years / 50.0)  # Cap at 50 years for max effect

        total_factor = (
            age_factor *
            exposure_factor.get(exposure_level, 0.8) *
            climate_factor.get(climate, 1.0) *
            maintenance_factor.get(maintenance, 1.0)
        )

        # Generate weathering layers based on factors
        layers = []

        if total_factor > 0.1:
            layers.append(WeatheringTools.create_dust_layer(amount=total_factor * 0.3))

        if total_factor > 0.2:
            layers.append(WeatheringTools.create_dirt_accumulation(
                crevice_intensity=total_factor * 0.5,
                surface_dirt=total_factor * 0.2,
            ))

        if total_factor > 0.3:
            layers.append(WeatheringTools.create_edge_wear(intensity=total_factor * 0.5))

        if exposure_level in ["outdoor", "harsh"] and total_factor > 0.2:
            layers.append(WeatheringTools.create_sun_bleaching(intensity=total_factor * 0.4))

        if climate == "coastal" and total_factor > 0.15:
            layers.append(WeatheringTools.create_salt_deposits(coverage=total_factor * 0.3))

        if climate in ["tropical", "temperate"] and total_factor > 0.3:
            layers.append(WeatheringTools.create_mold_growth(intensity=total_factor * 0.2))

        return {
            "type": "aged_material",
            "parameters": {
                "age_years": age_years,
                "exposure_level": exposure_level,
                "climate": climate,
                "maintenance": maintenance,
                "total_weathering_factor": total_factor,
            },
            "layers": layers,
            "shader_adjustments": {
                "roughness_increase": total_factor * 0.3,
                "saturation_decrease": total_factor * 0.2,
                "brightness_change": total_factor * 0.1,
            }
        }
