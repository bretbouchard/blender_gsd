"""
Sanctus Pattern Generators - Procedural Pattern Generation
==========================================================

Procedural pattern generation utilities for creating various
surface patterns including tiles, bricks, wood planks, fabric
weaves, noise patterns, and more.
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


class PatternType(Enum):
    """Types of procedural patterns."""
    TILES = "tiles"
    BRICKS = "bricks"
    WOOD_PLANKS = "wood_planks"
    FABRIC_WEAVE = "fabric_weave"
    NOISE = "noise"
    VORONOI = "voronoi"
    WAVE = "wave"
    CHECKERBOARD = "checkerboard"
    HEXAGON = "hexagon"
    DIAMOND = "diamond"
    HERRINGBONE = "herringbone"
    CHEVRON = "chevron"
    SCALE = "scale"
    CIRCLES = "circles"


@dataclass
class PatternParameters:
    """Parameters for pattern generation."""
    pattern_type: PatternType = PatternType.TILES
    scale: float = 1.0
    rotation: float = 0.0
    offset: Tuple[float, float] = (0.0, 0.0)
    seed: int = 0

    # Pattern-specific
    primary_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    secondary_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    variation: float = 0.0

    # Surface properties
    roughness: float = 0.5
    normal_intensity: float = 1.0


class PatternGenerator:
    """
    Procedural pattern generation utilities.

    Provides static methods for creating various types of
    surface patterns as materials and textures.
    """

    @staticmethod
    def tiles(
        scale: float = 1.0,
        mortar_width: float = 0.05,
        variation: float = 0.1,
        tile_color: Tuple[float, float, float] = (0.7, 0.7, 0.7),
        mortar_color: Tuple[float, float, float] = (0.4, 0.4, 0.4),
        offset_pattern: str = "grid",
        bevel_radius: float = 0.01,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a tile pattern configuration.

        Args:
            scale: Overall tile scale (0.1 - 10.0)
            mortar_width: Width of mortar gaps (0.0 - 0.2)
            variation: Color variation between tiles (0.0 - 0.5)
            tile_color: Base tile color
            mortar_color: Mortar color
            offset_pattern: Pattern type ("grid", "running", "herringbone")
            bevel_radius: Tile edge bevel radius
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing tile pattern configuration
        """
        offset_configs = {
            "grid": {"offset_x": 0.0, "offset_y": 0.0},
            "running": {"offset_x": 0.5, "offset_y": 0.0},
            "herringbone": {"offset_x": 0.5, "offset_y": 0.5},
        }

        return {
            "type": "tiles",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "mortar_width": max(0.0, min(0.2, mortar_width)),
                "variation": max(0.0, min(0.5, variation)),
                "tile_color": tile_color,
                "mortar_color": mortar_color,
                "offset_pattern": offset_pattern,
                "bevel_radius": max(0.0, min(0.1, bevel_radius)),
                "seed": seed,
            },
            "node_config": {
                "brick_scale": scale,
                "mortar_size": mortar_width,
                "color_variation": variation,
                **offset_configs.get(offset_pattern, offset_configs["grid"]),
                "bevel_normal": bevel_radius * 10,
            },
            "shader_setup": {
                "tile_roughness": 0.5,
                "mortar_roughness": 0.9,
                "tile_bump": bevel_radius * 0.01,
                "mortar_depth": -mortar_width * 0.5,
            }
        }

    @staticmethod
    def bricks(
        scale: float = 1.0,
        mortar_width: float = 0.03,
        offset: bool = True,
        variation: float = 0.05,
        brick_color: Tuple[float, float, float] = (0.6, 0.35, 0.25),
        mortar_color: Tuple[float, float, float] = (0.5, 0.5, 0.45),
        brick_size: Tuple[float, float] = (2.0, 1.0),
        surface_roughness: float = 0.8,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a brick pattern configuration.

        Args:
            scale: Overall brick scale (0.1 - 10.0)
            mortar_width: Width of mortar gaps (0.0 - 0.1)
            offset: Whether rows are offset (running bond)
            variation: Color and size variation (0.0 - 0.3)
            brick_color: Base brick color
            mortar_color: Mortar color
            brick_size: Brick dimensions (width, height)
            surface_roughness: Brick surface roughness
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing brick pattern configuration
        """
        return {
            "type": "bricks",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "mortar_width": max(0.0, min(0.1, mortar_width)),
                "offset": offset,
                "variation": max(0.0, min(0.3, variation)),
                "brick_color": brick_color,
                "mortar_color": mortar_color,
                "brick_size": brick_size,
                "surface_roughness": max(0.0, min(1.0, surface_roughness)),
                "seed": seed,
            },
            "node_config": {
                "brick_texture_scale": scale,
                "mortar_size": mortar_width,
                "offset_amount": 0.5 if offset else 0.0,
                "color_variation": variation,
                "aspect_ratio": brick_size[0] / brick_size[1],
            },
            "shader_setup": {
                "brick_roughness": surface_roughness,
                "mortar_roughness": 0.95,
                "brick_bump": 0.002,
                "mortar_depth": -mortar_width * 0.3,
            }
        }

    @staticmethod
    def wood_planks(
        length: float = 2.0,
        width: float = 0.2,
        grain_scale: float = 1.0,
        plank_variation: float = 0.1,
        base_color: Tuple[float, float, float] = (0.55, 0.35, 0.15),
        grain_contrast: float = 0.3,
        knots: bool = True,
        plank_gaps: float = 0.005,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a wood plank pattern configuration.

        Args:
            length: Average plank length (0.5 - 10.0)
            width: Plank width (0.05 - 1.0)
            grain_scale: Wood grain scale factor
            plank_variation: Color variation between planks (0.0 - 0.3)
            base_color: Base wood color
            grain_contrast: Contrast of wood grain (0.0 - 1.0)
            knots: Include wood knots
            plank_gaps: Gap between planks
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing wood plank pattern configuration
        """
        return {
            "type": "wood_planks",
            "parameters": {
                "length": max(0.5, min(10.0, length)),
                "width": max(0.05, min(1.0, width)),
                "grain_scale": max(0.1, min(5.0, grain_scale)),
                "plank_variation": max(0.0, min(0.3, plank_variation)),
                "base_color": base_color,
                "grain_contrast": max(0.0, min(1.0, grain_contrast)),
                "knots": knots,
                "plank_gaps": max(0.0, min(0.02, plank_gaps)),
                "seed": seed,
            },
            "node_config": {
                "plank_scale_x": length,
                "plank_scale_y": width,
                "grain_noise_scale": 100.0 * grain_scale,
                "grain_detail": 8,
                "wave_scale_y": 50.0,  # Grain direction
                "color_ramp_grain": [0.0, grain_contrast],
                "knot_scale": 20.0 if knots else 0,
                "knot_randomness": 0.8 if knots else 0,
            },
            "shader_setup": {
                "roughness": 0.4,
                "anisotropic": 0.3,
                "grain_normal_intensity": 0.2,
                "plank_bump": plank_gaps * 0.5,
            }
        }

    @staticmethod
    def fabric_weave(
        weft_scale: float = 0.1,
        warp_scale: float = 0.1,
        thread_thickness: float = 0.02,
        weft_color: Tuple[float, float, float] = (0.8, 0.2, 0.2),
        warp_color: Tuple[float, float, float] = (0.2, 0.2, 0.8),
        thread_roughness: float = 0.8,
        pattern_type: str = "plain",
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a fabric weave pattern configuration.

        Args:
            weft_scale: Scale of weft threads (0.01 - 0.5)
            warp_scale: Scale of warp threads (0.01 - 0.5)
            thread_thickness: Thread thickness (0.005 - 0.1)
            weft_color: Weft thread color
            warp_color: Warp thread color
            thread_roughness: Thread surface roughness
            pattern_type: Weave pattern ("plain", "twill", "satin")
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing fabric weave configuration
        """
        pattern_configs = {
            "plain": {"repeat": 2, "pattern": [1, 0, 0, 1]},
            "twill": {"repeat": 3, "pattern": [1, 1, 0, 1, 0, 0, 0, 1, 1]},
            "satin": {"repeat": 5, "pattern": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1]},
        }

        return {
            "type": "fabric_weave",
            "parameters": {
                "weft_scale": max(0.01, min(0.5, weft_scale)),
                "warp_scale": max(0.01, min(0.5, warp_scale)),
                "thread_thickness": max(0.005, min(0.1, thread_thickness)),
                "weft_color": weft_color,
                "warp_color": warp_color,
                "thread_roughness": max(0.0, min(1.0, thread_roughness)),
                "pattern_type": pattern_type,
                "seed": seed,
            },
            "node_config": {
                "weft_frequency": 1.0 / weft_scale,
                "warp_frequency": 1.0 / warp_scale,
                "thread_width": thread_thickness,
                **pattern_configs.get(pattern_type, pattern_configs["plain"]),
            },
            "shader_setup": {
                "roughness": thread_roughness,
                "sheen": 0.3,
                "sheen_tint": 0.2,
                "subsurface": 0.1,
                "normal_intensity": thread_thickness * 5,
            }
        }

    @staticmethod
    def noise_pattern(
        scale: float = 1.0,
        detail: int = 3,
        distortion: float = 0.0,
        noise_type: str = "perlin",
        color_ramp: Optional[List[Tuple[float, Tuple[float, float, float]]]] = None,
        roughness_modulation: float = 0.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a noise pattern configuration.

        Args:
            scale: Noise scale (0.1 - 50.0)
            detail: Level of detail (0 - 16)
            distortion: Amount of distortion (0.0 - 10.0)
            noise_type: Type of noise ("perlin", "voronoi", "musgrave")
            color_ramp: Custom color ramp stops
            roughness_modulation: Roughness modulation amount
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing noise pattern configuration
        """
        if color_ramp is None:
            color_ramp = [
                (0.0, (0.0, 0.0, 0.0)),
                (1.0, (1.0, 1.0, 1.0)),
            ]

        return {
            "type": "noise_pattern",
            "parameters": {
                "scale": max(0.1, min(50.0, scale)),
                "detail": max(0, min(16, detail)),
                "distortion": max(0.0, min(10.0, distortion)),
                "noise_type": noise_type,
                "color_ramp": color_ramp,
                "roughness_modulation": max(0.0, min(1.0, roughness_modulation)),
                "seed": seed,
            },
            "node_config": {
                "noise_scale": scale,
                "noise_detail": detail,
                "noise_distortion": distortion,
                "noise_type_blender": {
                    "perlin": "BLENDER",
                    "voronoi": "VORONOI",
                    "musgrave": "MULTIFRACTAL",
                }.get(noise_type, "BLENDER"),
            },
            "shader_setup": {
                "base_roughness": 0.5,
                "roughness_modulation": roughness_modulation,
                "normal_intensity": 0.3,
            }
        }

    @staticmethod
    def voronoi_cells(
        scale: float = 1.0,
        randomness: float = 0.5,
        edge_width: float = 0.05,
        cell_color: Tuple[float, float, float] = (0.8, 0.8, 0.8),
        edge_color: Tuple[float, float, float] = (0.2, 0.2, 0.2),
        distance_metric: str = "euclidean",
        color_variation: float = 0.2,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a Voronoi cell pattern configuration.

        Args:
            scale: Cell scale (0.1 - 20.0)
            randomness: Cell position randomness (0.0 - 1.0)
            edge_width: Width of cell edges (0.0 - 0.5)
            cell_color: Cell interior color
            edge_color: Edge color
            distance_metric: Distance metric ("euclidean", "manhattan", "chebyshev")
            color_variation: Color variation between cells (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing Voronoi cell configuration
        """
        return {
            "type": "voronoi_cells",
            "parameters": {
                "scale": max(0.1, min(20.0, scale)),
                "randomness": max(0.0, min(1.0, randomness)),
                "edge_width": max(0.0, min(0.5, edge_width)),
                "cell_color": cell_color,
                "edge_color": edge_color,
                "distance_metric": distance_metric,
                "color_variation": max(0.0, min(1.0, color_variation)),
                "seed": seed,
            },
            "node_config": {
                "voronoi_scale": scale,
                "voronoi_randomness": randomness,
                "edge_threshold": edge_width,
                "distance_metric_blender": {
                    "euclidean": "EUCLIDEAN",
                    "manhattan": "MANHATTAN",
                    "chebyshev": "MINKOWSKI",
                }.get(distance_metric, "EUCLIDEAN"),
            },
            "shader_setup": {
                "cell_roughness": 0.5,
                "edge_roughness": 0.7,
                "edge_depth": -edge_width * 0.1,
                "cell_bump": 0.001,
            }
        }

    @staticmethod
    def wave_pattern(
        scale: float = 1.0,
        direction: Tuple[float, float] = (1.0, 0.0),
        wave_type: str = "sine",
        rings: bool = False,
        distortion: float = 0.0,
        detail: int = 2,
        color1: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        color2: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a wave pattern configuration.

        Args:
            scale: Wave scale (0.1 - 20.0)
            direction: Wave direction vector
            wave_type: Type of wave ("sine", "saw", "triangle")
            rings: Use concentric rings instead of linear
            distortion: Amount of distortion
            detail: Level of detail
            color1: First color
            color2: Second color
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing wave pattern configuration
        """
        return {
            "type": "wave_pattern",
            "parameters": {
                "scale": max(0.1, min(20.0, scale)),
                "direction": direction,
                "wave_type": wave_type,
                "rings": rings,
                "distortion": max(0.0, min(10.0, distortion)),
                "detail": max(0, min(16, detail)),
                "color1": color1,
                "color2": color2,
                "seed": seed,
            },
            "node_config": {
                "wave_scale": scale,
                "wave_direction": direction,
                "wave_type_blender": {
                    "sine": "SIN",
                    "saw": "SAW",
                    "triangle": "TRI",
                }.get(wave_type, "SIN"),
                "rings_mode": rings,
                "distortion": distortion,
                "detail": detail,
            },
            "shader_setup": {
                "roughness": 0.3,
                "normal_intensity": 0.2,
            }
        }

    @staticmethod
    def checkerboard(
        scale: float = 1.0,
        color1: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        color2: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: float = 0.0,
        bevel: float = 0.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a checkerboard pattern configuration.

        Args:
            scale: Square scale (0.1 - 20.0)
            color1: First color
            color2: Second color
            rotation: Pattern rotation in degrees
            bevel: Edge bevel amount
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing checkerboard configuration
        """
        return {
            "type": "checkerboard",
            "parameters": {
                "scale": max(0.1, min(20.0, scale)),
                "color1": color1,
                "color2": color2,
                "rotation": rotation,
                "bevel": max(0.0, min(0.1, bevel)),
                "seed": seed,
            },
            "node_config": {
                "checker_scale": scale * 5,
                "rotation_radians": math.radians(rotation),
                "bevel_normal": bevel * 10,
            },
            "shader_setup": {
                "roughness": 0.4,
                "normal_intensity": bevel * 5,
            }
        }

    @staticmethod
    def hexagon_grid(
        scale: float = 1.0,
        edge_width: float = 0.02,
        rotation: float = 0.0,
        cell_color: Tuple[float, float, float] = (0.7, 0.7, 0.7),
        edge_color: Tuple[float, float, float] = (0.3, 0.3, 0.3),
        color_variation: float = 0.1,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a hexagon grid pattern configuration.

        Args:
            scale: Hexagon scale (0.1 - 10.0)
            edge_width: Edge line width (0.0 - 0.2)
            rotation: Pattern rotation in degrees
            cell_color: Cell interior color
            edge_color: Edge color
            color_variation: Color variation between cells
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing hexagon grid configuration
        """
        return {
            "type": "hexagon_grid",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "edge_width": max(0.0, min(0.2, edge_width)),
                "rotation": rotation,
                "cell_color": cell_color,
                "edge_color": edge_color,
                "color_variation": max(0.0, min(0.3, color_variation)),
                "seed": seed,
            },
            "node_config": {
                "hexagon_scale": scale,
                "edge_threshold": edge_width,
                "rotation_radians": math.radians(rotation),
                "sqrt3": math.sqrt(3),
            },
            "shader_setup": {
                "cell_roughness": 0.5,
                "edge_roughness": 0.6,
                "edge_depth": -edge_width * 0.2,
            },
            "math_setup": {
                "description": "Uses mathematical hexagon distance function",
                "formula": "hex_dist = max(abs(x), abs(y), abs(x+y))",
            }
        }

    @staticmethod
    def diamond_pattern(
        scale: float = 1.0,
        edge_width: float = 0.02,
        rotation: float = 45.0,
        color1: Tuple[float, float, float] = (0.8, 0.8, 0.8),
        color2: Tuple[float, float, float] = (0.4, 0.4, 0.4),
        edge_color: Tuple[float, float, float] = (0.2, 0.2, 0.2),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a diamond pattern configuration.

        Args:
            scale: Diamond scale (0.1 - 10.0)
            edge_width: Edge line width (0.0 - 0.2)
            rotation: Pattern rotation in degrees
            color1: First diamond color
            color2: Second diamond color
            edge_color: Edge color
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing diamond pattern configuration
        """
        return {
            "type": "diamond_pattern",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "edge_width": max(0.0, min(0.2, edge_width)),
                "rotation": rotation,
                "color1": color1,
                "color2": color2,
                "edge_color": edge_color,
                "seed": seed,
            },
            "node_config": {
                "diamond_scale": scale,
                "edge_threshold": edge_width,
                "rotation_radians": math.radians(rotation),
            },
            "shader_setup": {
                "diamond_roughness": 0.4,
                "edge_roughness": 0.7,
                "edge_depth": -edge_width * 0.15,
            }
        }

    @staticmethod
    def herringbone(
        scale: float = 1.0,
        plank_width: float = 0.1,
        plank_length: float = 0.5,
        gap_width: float = 0.005,
        color: Tuple[float, float, float] = (0.55, 0.35, 0.15),
        color_variation: float = 0.1,
        rotation: float = 0.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a herringbone pattern configuration.

        Args:
            scale: Overall pattern scale (0.1 - 10.0)
            plank_width: Width of individual planks (0.02 - 0.5)
            plank_length: Length of individual planks (0.1 - 2.0)
            gap_width: Gap between planks
            color: Base plank color
            color_variation: Color variation between planks
            rotation: Pattern rotation in degrees
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing herringbone pattern configuration
        """
        return {
            "type": "herringbone",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "plank_width": max(0.02, min(0.5, plank_width)),
                "plank_length": max(0.1, min(2.0, plank_length)),
                "gap_width": max(0.0, min(0.02, gap_width)),
                "color": color,
                "color_variation": max(0.0, min(0.3, color_variation)),
                "rotation": rotation,
                "seed": seed,
            },
            "node_config": {
                "pattern_scale": scale,
                "plank_dimensions": (plank_length, plank_width),
                "gap_size": gap_width,
                "rotation_radians": math.radians(rotation),
                "tile_size": (plank_length * 2, plank_length * 2),
            },
            "shader_setup": {
                "plank_roughness": 0.4,
                "gap_depth": -gap_width * 0.3,
                "grain_normal": 0.2,
            }
        }

    @staticmethod
    def chevron(
        scale: float = 1.0,
        stripe_width: float = 0.1,
        angle: float = 45.0,
        color1: Tuple[float, float, float] = (0.8, 0.2, 0.2),
        color2: Tuple[float, float, float] = (0.2, 0.2, 0.8),
        edge_softness: float = 0.02,
        rotation: float = 0.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a chevron (V-shaped) pattern configuration.

        Args:
            scale: Overall pattern scale (0.1 - 10.0)
            stripe_width: Width of each stripe (0.02 - 0.5)
            angle: Chevron angle in degrees (15 - 75)
            color1: First stripe color
            color2: Second stripe color
            edge_softness: Edge softness/blur
            rotation: Pattern rotation in degrees
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing chevron pattern configuration
        """
        return {
            "type": "chevron",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "stripe_width": max(0.02, min(0.5, stripe_width)),
                "angle": max(15, min(75, angle)),
                "color1": color1,
                "color2": color2,
                "edge_softness": max(0.0, min(0.1, edge_softness)),
                "rotation": rotation,
                "seed": seed,
            },
            "node_config": {
                "pattern_scale": scale,
                "stripe_frequency": 1.0 / stripe_width,
                "angle_radians": math.radians(angle),
                "rotation_radians": math.radians(rotation),
                "edge_feather": edge_softness,
            },
            "shader_setup": {
                "roughness": 0.5,
                "normal_intensity": 0.1,
            }
        }

    @staticmethod
    def scale_pattern(
        scale: float = 1.0,
        overlap: float = 0.3,
        color: Tuple[float, float, float] = (0.6, 0.5, 0.3),
        edge_color: Tuple[float, float, float] = (0.3, 0.25, 0.15),
        color_variation: float = 0.1,
        rotation: float = 0.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a scale (fish scale / dragon scale) pattern configuration.

        Args:
            scale: Scale size (0.1 - 10.0)
            overlap: How much scales overlap (0.0 - 0.5)
            color: Base scale color
            edge_color: Scale edge/shadow color
            color_variation: Color variation between scales
            rotation: Pattern rotation in degrees
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing scale pattern configuration
        """
        return {
            "type": "scale_pattern",
            "parameters": {
                "scale_size": max(0.1, min(10.0, scale)),
                "overlap": max(0.0, min(0.5, overlap)),
                "color": color,
                "edge_color": edge_color,
                "color_variation": max(0.0, min(0.3, color_variation)),
                "rotation": rotation,
                "seed": seed,
            },
            "node_config": {
                "scale_radius": scale * 0.5,
                "offset_y": scale * overlap,
                "offset_x": scale * 0.5,  # Staggered rows
                "rotation_radians": math.radians(rotation),
            },
            "shader_setup": {
                "scale_roughness": 0.4,
                "edge_roughness": 0.6,
                "scale_height": 0.01,
                "overlap_shadow": overlap * 0.3,
            }
        }

    @staticmethod
    def circles(
        scale: float = 1.0,
        ring_width: float = 0.1,
        spacing: float = 0.5,
        color: Tuple[float, float, float] = (0.8, 0.8, 0.8),
        background_color: Tuple[float, float, float] = (0.2, 0.2, 0.2),
        variation: float = 0.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a circles/dots pattern configuration.

        Args:
            scale: Circle scale (0.1 - 10.0)
            ring_width: Circle ring width (0.02 - 0.5)
            spacing: Spacing between circles (0.1 - 2.0)
            color: Circle color
            background_color: Background color
            variation: Size/position variation (0.0 - 0.5)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing circles pattern configuration
        """
        return {
            "type": "circles",
            "parameters": {
                "scale": max(0.1, min(10.0, scale)),
                "ring_width": max(0.02, min(0.5, ring_width)),
                "spacing": max(0.1, min(2.0, spacing)),
                "color": color,
                "background_color": background_color,
                "variation": max(0.0, min(0.5, variation)),
                "seed": seed,
            },
            "node_config": {
                "circle_scale": scale,
                "grid_spacing": scale + spacing,
                "ring_threshold": ring_width,
                "variation_noise": variation * 10,
            },
            "shader_setup": {
                "circle_roughness": 0.5,
                "background_roughness": 0.6,
                "circle_height": 0.005,
            }
        }

    @staticmethod
    def generate_pattern_texture(
        pattern_type: PatternType,
        resolution: int = 1024,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a procedural pattern texture.

        Args:
            pattern_type: Type of pattern to generate
            resolution: Texture resolution
            params: Additional parameters for specific pattern type

        Returns:
            Dictionary containing texture data and metadata
        """
        params = params or {}

        generators = {
            PatternType.TILES: PatternGenerator.tiles,
            PatternType.BRICKS: PatternGenerator.bricks,
            PatternType.WOOD_PLANKS: PatternGenerator.wood_planks,
            PatternType.FABRIC_WEAVE: PatternGenerator.fabric_weave,
            PatternType.NOISE: PatternGenerator.noise_pattern,
            PatternType.VORONOI: PatternGenerator.voronoi_cells,
            PatternType.WAVE: PatternGenerator.wave_pattern,
            PatternType.CHECKERBOARD: PatternGenerator.checkerboard,
            PatternType.HEXAGON: PatternGenerator.hexagon_grid,
            PatternType.DIAMOND: PatternGenerator.diamond_pattern,
            PatternType.HERRINGBONE: PatternGenerator.herringbone,
            PatternType.CHEVRON: PatternGenerator.chevron,
            PatternType.SCALE: PatternGenerator.scale_pattern,
            PatternType.CIRCLES: PatternGenerator.circles,
        }

        generator = generators.get(pattern_type)
        if not generator:
            return None

        config = generator(**params)
        config["resolution"] = resolution
        return config

    @staticmethod
    def apply_to_material(
        material: Material,
        pattern_type: PatternType,
        scale: float = 1.0,
        **kwargs,
    ) -> Material:
        """
        Apply a pattern to an existing Blender material.

        Args:
            material: Blender material to modify
            pattern_type: Type of pattern to apply
            scale: Pattern scale
            **kwargs: Additional parameters for pattern type

        Returns:
            Modified material with pattern applied
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply patterns to materials")

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

        # Create coordinate and mapping nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (scale, scale, 1)

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        # Create pattern-specific nodes
        if pattern_type == PatternType.TILES or pattern_type == PatternType.BRICKS:
            brick_tex = nodes.new('ShaderNodeTexBrick')
            brick_tex.inputs['Scale'].default_value = 1.0
            brick_tex.inputs['Mortar Size'].default_value = kwargs.get('mortar_width', 0.05)
            links.new(mapping.outputs['Vector'], brick_tex.inputs['Vector'])

            color_ramp = nodes.new('ShaderNodeValToRGB')
            tile_color = kwargs.get('tile_color', kwargs.get('brick_color', (0.7, 0.7, 0.7)))
            mortar_color = kwargs.get('mortar_color', (0.4, 0.4, 0.4))
            color_ramp.color_ramp.elements[0].color = (*mortar_color, 1.0)
            color_ramp.color_ramp.elements[1].color = (*tile_color, 1.0)
            links.new(brick_tex.outputs['Fac'], color_ramp.inputs['Fac'])
            links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])

        elif pattern_type == PatternType.CHECKERBOARD:
            checker_tex = nodes.new('ShaderNodeTexChecker')
            checker_tex.inputs['Scale'].default_value = scale * 5
            color1 = kwargs.get('color1', (1.0, 1.0, 1.0))
            color2 = kwargs.get('color2', (0.0, 0.0, 0.0))
            checker_tex.inputs['Color1'].default_value = (*color1, 1.0)
            checker_tex.inputs['Color2'].default_value = (*color2, 1.0)
            links.new(mapping.outputs['Vector'], checker_tex.inputs['Vector'])
            links.new(checker_tex.outputs['Color'], bsdf.inputs['Base Color'])

        elif pattern_type == PatternType.VORONOI:
            voronoi_tex = nodes.new('ShaderNodeTexVoronoi')
            voronoi_tex.inputs['Scale'].default_value = scale * 5
            voronoi_tex.inputs['Randomness'].default_value = kwargs.get('randomness', 0.5)
            links.new(mapping.outputs['Vector'], voronoi_tex.inputs['Vector'])
            links.new(voronoi_tex.outputs['Distance'], bsdf.inputs['Roughness'])

        elif pattern_type == PatternType.NOISE:
            noise_tex = nodes.new('ShaderNodeTexNoise')
            noise_tex.inputs['Scale'].default_value = scale * 5
            noise_tex.inputs['Detail'].default_value = kwargs.get('detail', 3)
            noise_tex.inputs['Distortion'].default_value = kwargs.get('distortion', 0.0)
            links.new(mapping.outputs['Vector'], noise_tex.inputs['Vector'])
            links.new(noise_tex.outputs['Fac'], bsdf.inputs['Roughness'])

        elif pattern_type == PatternType.WAVE:
            wave_tex = nodes.new('ShaderNodeTexWave')
            wave_tex.inputs['Scale'].default_value = scale * 5
            links.new(mapping.outputs['Vector'], wave_tex.inputs['Vector'])
            links.new(wave_tex.outputs['Fac'], bsdf.inputs['Roughness'])

        return material
