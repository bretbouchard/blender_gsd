"""
Sanctus Shader Tools - 32+ Shader Tools API
===========================================

Comprehensive shader tool collection for damage, weathering,
and pattern generation. Performance-rated for Eevee and Cycles.

Performance Color Coding:
- Green: Fast (real-time in Eevee)
- Yellow: Medium (good performance)
- Red: Slow (Cycles recommended)

Compatibility:
- E: Eevee compatible
- C: Cycles compatible
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)
import math
import random

try:
    import bpy
    from bpy.types import Material, Node, NodeTree, ShaderNodeTree
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    # Type stubs for non-Blender environments
    Material = Any
    Node = Any
    NodeTree = Any
    ShaderNodeTree = Any
    Vector = Any


class ToolCategory(Enum):
    """Categories for shader tools."""
    DAMAGE = auto()
    WEATHERING = auto()
    PATTERN = auto()
    MASK = auto()
    BLEND = auto()
    UTILITY = auto()


class PerformanceRating(Enum):
    """
    Performance rating for shader tools.

    GREEN: Fast - Real-time in Eevee
    YELLOW: Medium - Good performance, may be slower in Eevee
    RED: Slow - Cycles recommended for best results
    """
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class ShaderTool:
    """Represents a shader tool with metadata."""
    name: str
    display_name: str
    category: ToolCategory
    performance: PerformanceRating
    eevee_compatible: bool = True
    cycles_compatible: bool = True
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    node_group_name: Optional[str] = None


class ShaderToolRegistry:
    """
    Registry for all available shader tools.

    Contains 32+ shader tools organized by category.
    """

    _tools: Dict[str, ShaderTool] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the tool registry with all available tools."""
        if cls._initialized:
            return

        # DAMAGE TOOLS (8 tools)
        damage_tools = [
            ShaderTool(
                name="scratches",
                display_name="Scratches",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.GREEN,
                description="Generate procedural scratch marks",
                parameters={
                    "length": {"default": 0.1, "min": 0.001, "max": 1.0, "type": "float"},
                    "width": {"default": 0.002, "min": 0.0001, "max": 0.1, "type": "float"},
                    "density": {"default": 50.0, "min": 1.0, "max": 500.0, "type": "float"},
                    "direction": {"default": (1, 0, 0), "type": "vector"},
                    "seed": {"default": 0, "min": 0, "max": 9999, "type": "int"},
                }
            ),
            ShaderTool(
                name="dents",
                display_name="Dents",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.YELLOW,
                description="Create procedural dent marks",
                parameters={
                    "depth": {"default": 0.01, "min": 0.001, "max": 0.1, "type": "float"},
                    "size": {"default": 0.05, "min": 0.01, "max": 0.5, "type": "float"},
                    "density": {"default": 20.0, "min": 1.0, "max": 200.0, "type": "float"},
                    "seed": {"default": 0, "min": 0, "max": 9999, "type": "int"},
                }
            ),
            ShaderTool(
                name="paint_chips",
                display_name="Paint Chips",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.GREEN,
                description="Generate peeling paint chips",
                parameters={
                    "size_min": {"default": 0.01, "min": 0.001, "max": 0.1, "type": "float"},
                    "size_max": {"default": 0.05, "min": 0.01, "max": 0.2, "type": "float"},
                    "edge_sharpness": {"default": 0.8, "min": 0.0, "max": 1.0, "type": "float"},
                    "coverage": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="cracks",
                display_name="Cracks",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.RED,
                description="Generate procedural crack patterns",
                parameters={
                    "width": {"default": 0.005, "min": 0.001, "max": 0.05, "type": "float"},
                    "branching": {"default": 3, "min": 1, "max": 10, "type": "int"},
                    "depth": {"default": 0.02, "min": 0.001, "max": 0.1, "type": "float"},
                    "seed": {"default": 0, "min": 0, "max": 9999, "type": "int"},
                }
            ),
            ShaderTool(
                name="burn_marks",
                display_name="Burn Marks",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.GREEN,
                description="Create burn and scorch marks",
                parameters={
                    "intensity": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "size": {"default": 0.1, "min": 0.01, "max": 0.5, "type": "float"},
                    "edge_softness": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="water_damage",
                display_name="Water Damage",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.GREEN,
                description="Generate water stain patterns",
                parameters={
                    "stain_color": {"default": (0.8, 0.75, 0.7), "type": "color"},
                    "intensity": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                    "spread": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="bullet_holes",
                display_name="Bullet Holes",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.YELLOW,
                description="Create bullet hole damage",
                parameters={
                    "size": {"default": 0.02, "min": 0.005, "max": 0.1, "type": "float"},
                    "edge_cracks": {"default": True, "type": "bool"},
                    "depth": {"default": 0.03, "min": 0.01, "max": 0.1, "type": "float"},
                }
            ),
            ShaderTool(
                name="impact_damage",
                display_name="Impact Damage",
                category=ToolCategory.DAMAGE,
                performance=PerformanceRating.YELLOW,
                description="Generate impact damage patterns",
                parameters={
                    "size": {"default": 0.1, "min": 0.02, "max": 0.5, "type": "float"},
                    "debris": {"default": True, "type": "bool"},
                    "intensity": {"default": 0.7, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
        ]

        # WEATHERING TOOLS (10 tools)
        weathering_tools = [
            ShaderTool(
                name="edge_wear",
                display_name="Edge Wear",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Generate edge wear patterns",
                parameters={
                    "intensity": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "sharpness": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                    "inner_radius": {"default": 0.1, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="dust_accumulation",
                display_name="Dust Accumulation",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Create dust layer effects",
                parameters={
                    "amount": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                    "gravity_dir": {"default": (0, 0, -1), "type": "vector"},
                    "color": {"default": (0.9, 0.85, 0.75), "type": "color"},
                }
            ),
            ShaderTool(
                name="water_streaks",
                display_name="Water Streaks",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Generate water streak patterns",
                parameters={
                    "length": {"default": 0.5, "min": 0.1, "max": 2.0, "type": "float"},
                    "width": {"default": 0.02, "min": 0.005, "max": 0.1, "type": "float"},
                    "density": {"default": 10.0, "min": 1.0, "max": 50.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="moss_growth",
                display_name="Moss Growth",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.YELLOW,
                description="Create moss and vegetation growth",
                parameters={
                    "amount": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                    "prefer_shade": {"default": True, "type": "bool"},
                    "color_variation": {"default": 0.2, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="rust_spots",
                display_name="Rust Spots",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Generate rust spot patterns",
                parameters={
                    "size": {"default": 0.1, "min": 0.01, "max": 0.5, "type": "float"},
                    "spread": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "color": {"default": (0.4, 0.2, 0.1), "type": "color"},
                }
            ),
            ShaderTool(
                name="dirt_accumulation",
                display_name="Dirt Accumulation",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Create dirt in crevices",
                parameters={
                    "crevice_intensity": {"default": 0.7, "min": 0.0, "max": 1.0, "type": "float"},
                    "surface_dirt": {"default": 0.2, "min": 0.0, "max": 1.0, "type": "float"},
                    "color": {"default": (0.2, 0.15, 0.1), "type": "color"},
                }
            ),
            ShaderTool(
                name="sun_bleaching",
                display_name="Sun Bleaching",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Create sun-faded areas",
                parameters={
                    "intensity": {"default": 0.4, "min": 0.0, "max": 1.0, "type": "float"},
                    "exposure_dir": {"default": (0, 1, 0), "type": "vector"},
                    "edge_fade": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="rust_layer",
                display_name="Rust Layer",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.YELLOW,
                description="Create full rust layer effect",
                parameters={
                    "base_color": {"default": (0.6, 0.6, 0.65), "type": "color"},
                    "rust_color": {"default": (0.4, 0.2, 0.1), "type": "color"},
                    "coverage": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="mold_growth",
                display_name="Mold Growth",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.YELLOW,
                description="Generate mold and mildew patterns",
                parameters={
                    "intensity": {"default": 0.2, "min": 0.0, "max": 1.0, "type": "float"},
                    "prefer_damp": {"default": True, "type": "bool"},
                    "color": {"default": (0.3, 0.4, 0.2), "type": "color"},
                }
            ),
            ShaderTool(
                name="patina",
                display_name="Patina",
                category=ToolCategory.WEATHERING,
                performance=PerformanceRating.GREEN,
                description="Create aged metal patina",
                parameters={
                    "coverage": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "color": {"default": (0.2, 0.5, 0.5), "type": "color"},
                    "variation": {"default": 0.3, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
        ]

        # PATTERN TOOLS (8 tools)
        pattern_tools = [
            ShaderTool(
                name="tiles",
                display_name="Tiles",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate tile patterns",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 10.0, "type": "float"},
                    "mortar_width": {"default": 0.05, "min": 0.0, "max": 0.2, "type": "float"},
                    "variation": {"default": 0.1, "min": 0.0, "max": 0.5, "type": "float"},
                }
            ),
            ShaderTool(
                name="bricks",
                display_name="Bricks",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate brick patterns",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 10.0, "type": "float"},
                    "mortar_width": {"default": 0.03, "min": 0.0, "max": 0.1, "type": "float"},
                    "offset": {"default": True, "type": "bool"},
                    "variation": {"default": 0.05, "min": 0.0, "max": 0.3, "type": "float"},
                }
            ),
            ShaderTool(
                name="wood_planks",
                display_name="Wood Planks",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate wood plank patterns",
                parameters={
                    "length": {"default": 2.0, "min": 0.5, "max": 10.0, "type": "float"},
                    "width": {"default": 0.2, "min": 0.05, "max": 1.0, "type": "float"},
                    "grain_scale": {"default": 1.0, "min": 0.1, "max": 5.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="fabric_weave",
                display_name="Fabric Weave",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.YELLOW,
                description="Generate fabric weave patterns",
                parameters={
                    "weft_scale": {"default": 0.1, "min": 0.01, "max": 0.5, "type": "float"},
                    "warp_scale": {"default": 0.1, "min": 0.01, "max": 0.5, "type": "float"},
                    "thread_thickness": {"default": 0.02, "min": 0.005, "max": 0.1, "type": "float"},
                }
            ),
            ShaderTool(
                name="noise_pattern",
                display_name="Noise Pattern",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate noise-based patterns",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 50.0, "type": "float"},
                    "detail": {"default": 3, "min": 0, "max": 16, "type": "int"},
                    "distortion": {"default": 0.0, "min": 0.0, "max": 10.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="voronoi_cells",
                display_name="Voronoi Cells",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate Voronoi cell patterns",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 20.0, "type": "float"},
                    "randomness": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "edge_width": {"default": 0.05, "min": 0.0, "max": 0.5, "type": "float"},
                }
            ),
            ShaderTool(
                name="hexagon_grid",
                display_name="Hexagon Grid",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate hexagonal grid patterns",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 10.0, "type": "float"},
                    "edge_width": {"default": 0.02, "min": 0.0, "max": 0.2, "type": "float"},
                    "rotation": {"default": 0.0, "min": 0.0, "max": 360.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="checkerboard",
                display_name="Checkerboard",
                category=ToolCategory.PATTERN,
                performance=PerformanceRating.GREEN,
                description="Generate checkerboard patterns",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 20.0, "type": "float"},
                    "color1": {"default": (1.0, 1.0, 1.0), "type": "color"},
                    "color2": {"default": (0.0, 0.0, 0.0), "type": "color"},
                }
            ),
        ]

        # MASK TOOLS (4 tools)
        mask_tools = [
            ShaderTool(
                name="curvature_mask",
                display_name="Curvature Mask",
                category=ToolCategory.MASK,
                performance=PerformanceRating.GREEN,
                description="Create mask based on surface curvature",
                parameters={
                    "convex": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "concave": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "edge_only": {"default": False, "type": "bool"},
                }
            ),
            ShaderTool(
                name="ao_mask",
                display_name="AO Mask",
                category=ToolCategory.MASK,
                performance=PerformanceRating.YELLOW,
                description="Create ambient occlusion based mask",
                parameters={
                    "distance": {"default": 1.0, "min": 0.1, "max": 10.0, "type": "float"},
                    "samples": {"default": 16, "min": 1, "max": 64, "type": "int"},
                    "invert": {"default": False, "type": "bool"},
                }
            ),
            ShaderTool(
                name="height_mask",
                display_name="Height Mask",
                category=ToolCategory.MASK,
                performance=PerformanceRating.GREEN,
                description="Create mask based on height/position",
                parameters={
                    "min_height": {"default": -1.0, "min": -10.0, "max": 10.0, "type": "float"},
                    "max_height": {"default": 1.0, "min": -10.0, "max": 10.0, "type": "float"},
                    "falloff": {"default": 0.1, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="procedural_mask",
                display_name="Procedural Mask",
                category=ToolCategory.MASK,
                performance=PerformanceRating.GREEN,
                description="Create procedural noise-based mask",
                parameters={
                    "scale": {"default": 1.0, "min": 0.1, "max": 50.0, "type": "float"},
                    "threshold": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                    "contrast": {"default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
        ]

        # BLEND TOOLS (2 tools)
        blend_tools = [
            ShaderTool(
                name="layer_blend",
                display_name="Layer Blend",
                category=ToolCategory.BLEND,
                performance=PerformanceRating.GREEN,
                description="Blend material layers with various modes",
                parameters={
                    "blend_mode": {"default": "mix", "options": ["mix", "multiply", "add", "overlay"]},
                    "opacity": {"default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
            ShaderTool(
                name="masked_blend",
                display_name="Masked Blend",
                category=ToolCategory.BLEND,
                performance=PerformanceRating.GREEN,
                description="Blend materials using a mask",
                parameters={
                    "mask_type": {"default": "edge_wear", "options": ["edge_wear", "noise", "curvature"]},
                    "blend_softness": {"default": 0.1, "min": 0.0, "max": 1.0, "type": "float"},
                }
            ),
        ]

        # Register all tools
        all_tools = damage_tools + weathering_tools + pattern_tools + mask_tools + blend_tools
        for tool in all_tools:
            cls._tools[tool.name] = tool

        cls._initialized = True

    @classmethod
    def list_tools(cls) -> List[str]:
        """List all available tool names."""
        cls._initialize()
        return list(cls._tools.keys())

    @classmethod
    def list_tools_by_category(cls, category: ToolCategory) -> List[ShaderTool]:
        """List all tools in a specific category."""
        cls._initialize()
        return [t for t in cls._tools.values() if t.category == category]

    @classmethod
    def get_tool(cls, name: str) -> Optional[ShaderTool]:
        """Get a tool by name."""
        cls._initialize()
        return cls._tools.get(name)

    @classmethod
    def get_tool_count(cls) -> int:
        """Get total number of tools."""
        cls._initialize()
        return len(cls._tools)


class DamageGenerator:
    """
    Procedural damage generation utilities.

    Provides static methods for creating various types of damage
    patterns on materials.
    """

    @staticmethod
    def scratches(
        length: float = 0.1,
        width: float = 0.002,
        density: float = 50.0,
        direction: Tuple[float, float, float] = (1, 0, 0),
        seed: int = 0,
        depth: float = 0.001,
    ) -> Dict[str, Any]:
        """
        Generate procedural scratch marks.

        Args:
            length: Average scratch length (0.001 - 1.0)
            width: Scratch width (0.0001 - 0.1)
            density: Number of scratches per unit area (1.0 - 500.0)
            direction: Primary scratch direction vector
            seed: Random seed for reproducibility
            depth: Scratch depth for normal displacement

        Returns:
            Dictionary containing scratch pattern node configuration
        """
        return {
            "type": "scratches",
            "length": max(0.001, min(1.0, length)),
            "width": max(0.0001, min(0.1, width)),
            "density": max(1.0, min(500.0, density)),
            "direction": direction,
            "seed": seed,
            "depth": depth,
            "node_config": {
                "noise_scale": length * 10,
                "voronoi_randomness": 0.8,
                "color_ramp_positions": [0.0, width, width * 2, 1.0],
            }
        }

    @staticmethod
    def dents(
        depth: float = 0.01,
        size: float = 0.05,
        density: float = 20.0,
        seed: int = 0,
        sharpness: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Generate procedural dent marks.

        Args:
            depth: Dent depth for displacement (0.001 - 0.1)
            size: Average dent size (0.01 - 0.5)
            density: Number of dents per unit area (1.0 - 200.0)
            seed: Random seed for reproducibility
            sharpness: Edge sharpness of dents (0.0 - 1.0)

        Returns:
            Dictionary containing dent pattern node configuration
        """
        return {
            "type": "dents",
            "depth": max(0.001, min(0.1, depth)),
            "size": max(0.01, min(0.5, size)),
            "density": max(1.0, min(200.0, density)),
            "seed": seed,
            "sharpness": max(0.0, min(1.0, sharpness)),
            "node_config": {
                "voronoi_scale": 1.0 / size,
                "smooth_radius": size * (1.0 - sharpness),
                "height_invert": True,
            }
        }

    @staticmethod
    def paint_chips(
        size_range: Tuple[float, float] = (0.01, 0.05),
        edge_sharpness: float = 0.8,
        coverage: float = 0.3,
        seed: int = 0,
        layer_count: int = 2,
    ) -> Dict[str, Any]:
        """
        Generate peeling paint chip patterns.

        Args:
            size_range: Min and max chip size
            edge_sharpness: Sharpness of chip edges (0.0 - 1.0)
            coverage: Overall coverage percentage (0.0 - 1.0)
            seed: Random seed for reproducibility
            layer_count: Number of paint layers to reveal

        Returns:
            Dictionary containing paint chip pattern configuration
        """
        size_min, size_max = size_range
        return {
            "type": "paint_chips",
            "size_min": max(0.001, min(0.1, size_min)),
            "size_max": max(size_min, min(0.2, size_max)),
            "edge_sharpness": max(0.0, min(1.0, edge_sharpness)),
            "coverage": max(0.0, min(1.0, coverage)),
            "seed": seed,
            "layer_count": layer_count,
            "node_config": {
                "voronoi_scale": 2.0 / size_max,
                "threshold": coverage,
                "color_ramp_interpolation": "constant" if edge_sharpness > 0.5 else "linear",
            }
        }

    @staticmethod
    def cracks(
        width: float = 0.005,
        branching: int = 3,
        seed: int = 0,
        depth: float = 0.02,
        length: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Generate procedural crack patterns.

        Args:
            width: Crack width (0.001 - 0.05)
            branching: Number of branch points (1 - 10)
            seed: Random seed for reproducibility
            depth: Crack depth for displacement
            length: Average crack length

        Returns:
            Dictionary containing crack pattern configuration
        """
        return {
            "type": "cracks",
            "width": max(0.001, min(0.05, width)),
            "branching": max(1, min(10, branching)),
            "seed": seed,
            "depth": max(0.001, min(0.1, depth)),
            "length": max(0.1, min(2.0, length)),
            "node_config": {
                "voronoi_edge": True,
                "noise_distortion": branching * 0.5,
                "musgrave_octaves": branching,
            }
        }

    @staticmethod
    def bullet_holes(
        size: float = 0.02,
        edge_cracks: bool = True,
        depth: float = 0.03,
        count: int = 1,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate bullet hole damage patterns.

        Args:
            size: Hole diameter (0.005 - 0.1)
            edge_cracks: Whether to include edge cracking
            depth: Hole depth
            count: Number of holes to generate
            seed: Random seed for positioning

        Returns:
            Dictionary containing bullet hole pattern configuration
        """
        return {
            "type": "bullet_holes",
            "size": max(0.005, min(0.1, size)),
            "edge_cracks": edge_cracks,
            "depth": max(0.01, min(0.1, depth)),
            "count": max(1, min(20, count)),
            "seed": seed,
            "node_config": {
                "inner_ring_scale": size * 0.5,
                "crack_spread": size * 3 if edge_cracks else 0,
                "crack_branches": 4 if edge_cracks else 0,
            }
        }

    @staticmethod
    def impact_damage(
        size: float = 0.1,
        debris: bool = True,
        intensity: float = 0.7,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate impact damage patterns.

        Args:
            size: Impact area size (0.02 - 0.5)
            debris: Whether to include debris scatter
            intensity: Damage intensity (0.0 - 1.0)
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing impact damage configuration
        """
        return {
            "type": "impact_damage",
            "size": max(0.02, min(0.5, size)),
            "debris": debris,
            "intensity": max(0.0, min(1.0, intensity)),
            "seed": seed,
            "node_config": {
                "center_crater": True,
                "radial_cracks": int(intensity * 8),
                "debris_count": int(intensity * 20) if debris else 0,
            }
        }


class WeatheringGenerator:
    """
    Procedural weathering effect utilities.

    Provides static methods for creating various weathering
    and aging effects on materials.
    """

    @staticmethod
    def edge_wear(
        intensity: float = 0.5,
        sharpness: float = 0.3,
        inner_radius: float = 0.1,
        noise_amount: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Generate edge wear patterns.

        Args:
            intensity: Wear intensity (0.0 - 1.0)
            sharpness: Edge sharpness of wear (0.0 - 1.0)
            inner_radius: How far wear extends from edge
            noise_amount: Amount of noise in wear pattern

        Returns:
            Dictionary containing edge wear configuration
        """
        return {
            "type": "edge_wear",
            "intensity": max(0.0, min(1.0, intensity)),
            "sharpness": max(0.0, min(1.0, sharpness)),
            "inner_radius": max(0.0, min(1.0, inner_radius)),
            "noise_amount": max(0.0, min(1.0, noise_amount)),
            "node_config": {
                "use_geometry_nodes": True,
                "bevel_radius": inner_radius * 2,
                "noise_scale": noise_amount * 50,
            }
        }

    @staticmethod
    def dust_accumulation(
        amount: float = 0.3,
        gravity_direction: Tuple[float, float, float] = (0, 0, -1),
        color: Tuple[float, float, float] = (0.9, 0.85, 0.75),
        roughness: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Generate dust accumulation effects.

        Args:
            amount: Dust amount (0.0 - 1.0)
            gravity_direction: Direction dust accumulates
            color: Dust color
            roughness: Dust roughness

        Returns:
            Dictionary containing dust accumulation configuration
        """
        return {
            "type": "dust_accumulation",
            "amount": max(0.0, min(1.0, amount)),
            "gravity_direction": gravity_direction,
            "color": color,
            "roughness": max(0.0, min(1.0, roughness)),
            "node_config": {
                "noise_scale": 5.0,
                "detail": 2,
                "use_normal_for_gravity": True,
            }
        }

    @staticmethod
    def water_streaks(
        length: float = 0.5,
        width: float = 0.02,
        density: float = 10.0,
        stain_color: Tuple[float, float, float] = (0.6, 0.55, 0.5),
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate water streak patterns.

        Args:
            length: Average streak length (0.1 - 2.0)
            width: Streak width (0.005 - 0.1)
            density: Number of streaks per unit area
            stain_color: Color of water stains
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing water streak configuration
        """
        return {
            "type": "water_streaks",
            "length": max(0.1, min(2.0, length)),
            "width": max(0.005, min(0.1, width)),
            "density": max(1.0, min(50.0, density)),
            "stain_color": stain_color,
            "seed": seed,
            "node_config": {
                "wave_scale_y": length * 2,
                "noise_distortion": 0.5,
                "gradient_direction": (0, -1, 0),
            }
        }

    @staticmethod
    def moss_growth(
        amount: float = 0.3,
        prefer_shade: bool = True,
        color_variation: float = 0.2,
        base_color: Tuple[float, float, float] = (0.2, 0.4, 0.1),
        thickness: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Generate moss and vegetation growth patterns.

        Args:
            amount: Growth amount (0.0 - 1.0)
            prefer_shade: Whether moss prefers shaded areas
            color_variation: Color variation amount (0.0 - 1.0)
            base_color: Base moss color
            thickness: Moss thickness for displacement

        Returns:
            Dictionary containing moss growth configuration
        """
        return {
            "type": "moss_growth",
            "amount": max(0.0, min(1.0, amount)),
            "prefer_shade": prefer_shade,
            "color_variation": max(0.0, min(1.0, color_variation)),
            "base_color": base_color,
            "thickness": max(0.0, min(0.1, thickness)),
            "node_config": {
                "voronoi_scale": 5.0,
                "noise_detail": 4,
                "use_ao_for_shade": prefer_shade,
            }
        }

    @staticmethod
    def rust_spots(
        size: float = 0.1,
        spread: float = 0.5,
        color: Tuple[float, float, float] = (0.4, 0.2, 0.1),
        intensity: float = 0.5,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate rust spot patterns.

        Args:
            size: Average spot size (0.01 - 0.5)
            spread: How much rust spreads (0.0 - 1.0)
            color: Rust color
            intensity: Rust intensity/depth
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing rust spot configuration
        """
        return {
            "type": "rust_spots",
            "size": max(0.01, min(0.5, size)),
            "spread": max(0.0, min(1.0, spread)),
            "color": color,
            "intensity": max(0.0, min(1.0, intensity)),
            "seed": seed,
            "node_config": {
                "voronoi_scale": 1.0 / size,
                "noise_spread": spread * 2,
                "color_ramp_feather": 0.3,
            }
        }

    @staticmethod
    def dirt_accumulation(
        crevice_intensity: float = 0.7,
        surface_dirt: float = 0.2,
        color: Tuple[float, float, float] = (0.2, 0.15, 0.1),
        wetness: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate dirt accumulation in crevices.

        Args:
            crevice_intensity: Dirt intensity in crevices (0.0 - 1.0)
            surface_dirt: General surface dirt amount (0.0 - 1.0)
            color: Dirt color
            wetness: Wetness amount for darker dirt

        Returns:
            Dictionary containing dirt accumulation configuration
        """
        return {
            "type": "dirt_accumulation",
            "crevice_intensity": max(0.0, min(1.0, crevice_intensity)),
            "surface_dirt": max(0.0, min(1.0, surface_dirt)),
            "color": color,
            "wetness": max(0.0, min(1.0, wetness)),
            "node_config": {
                "use_ao": True,
                "noise_scale": 10.0,
                "ao_multiplier": crevice_intensity,
            }
        }

    @staticmethod
    def sun_bleaching(
        intensity: float = 0.4,
        exposure_direction: Tuple[float, float, float] = (0, 1, 0),
        edge_fade: float = 0.3,
        color_shift: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Generate sun bleaching/fading effects.

        Args:
            intensity: Bleaching intensity (0.0 - 1.0)
            exposure_direction: Direction of sun exposure
            edge_fade: Softness of bleaching edges
            color_shift: Color shift towards white/yellow

        Returns:
            Dictionary containing sun bleaching configuration
        """
        return {
            "type": "sun_bleaching",
            "intensity": max(0.0, min(1.0, intensity)),
            "exposure_direction": exposure_direction,
            "edge_fade": max(0.0, min(1.0, edge_fade)),
            "color_shift": max(0.0, min(1.0, color_shift)),
            "node_config": {
                "use_normal": True,
                "falloff_exponent": 1.0 + edge_fade,
                "target_hue": 60,  # Yellow shift
            }
        }


class SanctusShaderTools:
    """
    Main API for Sanctus Library shader tools.

    Provides access to 32+ shader tools for damage, weathering,
    and pattern generation with performance ratings.

    Performance Color Coding:
        Green = Fast (real-time in Eevee)
        Yellow = Medium (good performance)
        Red = Slow (Cycles recommended)

    Compatibility:
        E = Eevee compatible
        C = Cycles compatible
    """

    def __init__(self):
        """Initialize shader tools system."""
        # Ensure registry is initialized
        ShaderToolRegistry._initialize()

        self._damage_gen = DamageGenerator()
        self._weathering_gen = WeatheringGenerator()

        # Blender-specific initialization
        self._node_groups: Dict[str, Any] = {}
        if BLENDER_AVAILABLE:
            self._ensure_node_groups()

    def _ensure_node_groups(self) -> None:
        """Ensure all required node groups exist in Blender."""
        if not BLENDER_AVAILABLE:
            return

        for tool_name in ShaderToolRegistry.list_tools():
            tool = ShaderToolRegistry.get_tool(tool_name)
            if tool and tool.node_group_name:
                if tool.node_group_name not in bpy.data.node_groups:
                    self._create_node_group(tool)

    def _create_node_group(self, tool: ShaderTool) -> Optional[ShaderNodeTree]:
        """Create a node group for a shader tool."""
        if not BLENDER_AVAILABLE:
            return None

        # Create basic node group structure
        node_group = bpy.data.node_groups.new(
            name=f"Sanctus_{tool.name}",
            type='ShaderNodeTree'
        )

        # Add input/output nodes
        input_node = node_group.nodes.new('NodeGroupInput')
        output_node = node_group.nodes.new('NodeGroupOutput')

        # Create interface sockets based on parameters
        for param_name, param_config in tool.parameters.items():
            param_type = param_config.get("type", "float")
            if param_type == "float":
                node_group.interface.new_socket(
                    name=param_name,
                    in_out='INPUT',
                    socket_type='NodeSocketFloat'
                )
            elif param_type == "color":
                node_group.interface.new_socket(
                    name=param_name,
                    in_out='INPUT',
                    socket_type='NodeSocketColor'
                )
            elif param_type == "vector":
                node_group.interface.new_socket(
                    name=param_name,
                    in_out='INPUT',
                    socket_type='NodeSocketVector'
                )
            elif param_type == "int":
                node_group.interface.new_socket(
                    name=param_name,
                    in_out='INPUT',
                    socket_type='NodeSocketInt'
                )
            elif param_type == "bool":
                node_group.interface.new_socket(
                    name=param_name,
                    in_out='INPUT',
                    socket_type='NodeSocketBool'
                )

        # Add output sockets
        node_group.interface.new_socket(
            name="Color",
            in_out='OUTPUT',
            socket_type='NodeSocketColor'
        )
        node_group.interface.new_socket(
            name="Normal",
            in_out='OUTPUT',
            socket_type='NodeSocketVector'
        )
        node_group.interface.new_socket(
            name="Mask",
            in_out='OUTPUT',
            socket_type='NodeSocketFloat'
        )

        self._node_groups[tool.name] = node_group
        return node_group

    def get_tool(self, tool_name: str) -> Optional[ShaderTool]:
        """
        Get a shader tool by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            ShaderTool if found, None otherwise
        """
        return ShaderToolRegistry.get_tool(tool_name)

    def list_tools(self) -> List[str]:
        """
        List all available shader tools.

        Returns:
            List of tool names
        """
        return ShaderToolRegistry.list_tools()

    def list_tools_by_category(self, category: ToolCategory) -> List[ShaderTool]:
        """
        List tools by category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tools in the category
        """
        return ShaderToolRegistry.list_tools_by_category(category)

    def apply_damage(
        self,
        material: Material,
        damage_type: str = "scratches",
        intensity: float = 0.5,
        seed: int = 0,
        **kwargs,
    ) -> Material:
        """
        Apply damage effect to a material.

        Args:
            material: Blender material to modify
            damage_type: Type of damage (scratches, dents, paint_chips, cracks, etc.)
            intensity: Damage intensity (0.0 - 1.0)
            seed: Random seed for reproducibility
            **kwargs: Additional parameters for specific damage types

        Returns:
            Modified material with damage applied
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply damage")

        # Get the damage configuration
        damage_config = None
        if damage_type == "scratches":
            damage_config = self._damage_gen.scratches(
                seed=seed,
                depth=intensity * 0.01,
                **kwargs
            )
        elif damage_type == "dents":
            damage_config = self._damage_gen.dents(
                seed=seed,
                depth=intensity * 0.02,
                **kwargs
            )
        elif damage_type == "paint_chips":
            damage_config = self._damage_gen.paint_chips(
                seed=seed,
                coverage=intensity,
                **kwargs
            )
        elif damage_type == "cracks":
            damage_config = self._damage_gen.cracks(
                seed=seed,
                depth=intensity * 0.02,
                **kwargs
            )
        elif damage_type == "bullet_holes":
            damage_config = self._damage_gen.bullet_holes(
                seed=seed,
                depth=intensity * 0.03,
                **kwargs
            )
        elif damage_type == "impact_damage":
            damage_config = self._damage_gen.impact_damage(
                seed=seed,
                intensity=intensity,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown damage type: {damage_type}")

        # Apply to material node tree
        if material.use_nodes:
            self._apply_damage_to_nodetree(material.node_tree, damage_config)

        return material

    def _apply_damage_to_nodetree(
        self,
        node_tree: ShaderNodeTree,
        damage_config: Dict[str, Any],
    ) -> None:
        """Apply damage configuration to a node tree."""
        if not BLENDER_AVAILABLE:
            return

        damage_type = damage_config.get("type", "scratches")

        # Create node group instance
        group_name = f"Sanctus_{damage_type}"
        if group_name in bpy.data.node_groups:
            node_group = node_tree.nodes.new('ShaderNodeGroup')
            node_group.node_tree = bpy.data.node_groups[group_name]

            # Set default values from config
            for param_name, value in damage_config.items():
                if param_name != "node_config" and param_name in node_group.inputs:
                    node_group.inputs[param_name].default_value = value

    def apply_weathering(
        self,
        material: Material,
        weather_type: str = "dust",
        amount: float = 0.5,
        **kwargs,
    ) -> Material:
        """
        Apply weathering effect to a material.

        Args:
            material: Blender material to modify
            weather_type: Type of weathering (dust, edge_wear, rust, moss, etc.)
            amount: Weathering amount (0.0 - 1.0)
            **kwargs: Additional parameters for specific weathering types

        Returns:
            Modified material with weathering applied
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply weathering")

        # Get the weathering configuration
        weather_config = None
        if weather_type == "edge_wear":
            weather_config = self._weathering_gen.edge_wear(
                intensity=amount,
                **kwargs
            )
        elif weather_type == "dust" or weather_type == "dust_accumulation":
            weather_config = self._weathering_gen.dust_accumulation(
                amount=amount,
                **kwargs
            )
        elif weather_type == "water_streaks":
            weather_config = self._weathering_gen.water_streaks(
                **kwargs
            )
        elif weather_type == "moss" or weather_type == "moss_growth":
            weather_config = self._weathering_gen.moss_growth(
                amount=amount,
                **kwargs
            )
        elif weather_type == "rust" or weather_type == "rust_spots":
            weather_config = self._weathering_gen.rust_spots(
                intensity=amount,
                **kwargs
            )
        elif weather_type == "dirt" or weather_type == "dirt_accumulation":
            weather_config = self._weathering_gen.dirt_accumulation(
                surface_dirt=amount,
                **kwargs
            )
        elif weather_type == "sun_bleaching":
            weather_config = self._weathering_gen.sun_bleaching(
                intensity=amount,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown weathering type: {weather_type}")

        # Apply to material node tree
        if material.use_nodes:
            self._apply_weathering_to_nodetree(material.node_tree, weather_config)

        return material

    def _apply_weathering_to_nodetree(
        self,
        node_tree: ShaderNodeTree,
        weather_config: Dict[str, Any],
    ) -> None:
        """Apply weathering configuration to a node tree."""
        if not BLENDER_AVAILABLE:
            return

        weather_type = weather_config.get("type", "dust_accumulation")

        # Create node group instance
        group_name = f"Sanctus_{weather_type}"
        if group_name in bpy.data.node_groups:
            node_group = node_tree.nodes.new('ShaderNodeGroup')
            node_group.node_tree = bpy.data.node_groups[group_name]

            # Set default values from config
            for param_name, value in weather_config.items():
                if param_name != "node_config" and param_name in node_group.inputs:
                    node_group.inputs[param_name].default_value = value

    def apply_pattern(
        self,
        material: Material,
        pattern_type: str = "tiles",
        scale: float = 1.0,
        **kwargs,
    ) -> Material:
        """
        Apply pattern effect to a material.

        Args:
            material: Blender material to modify
            pattern_type: Type of pattern (tiles, bricks, wood_planks, etc.)
            scale: Pattern scale factor
            **kwargs: Additional parameters for specific pattern types

        Returns:
            Modified material with pattern applied
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply patterns")

        pattern_config = {
            "type": pattern_type,
            "scale": scale,
            **kwargs
        }

        # Apply to material node tree
        if material.use_nodes:
            self._apply_pattern_to_nodetree(material.node_tree, pattern_config)

        return material

    def _apply_pattern_to_nodetree(
        self,
        node_tree: ShaderNodeTree,
        pattern_config: Dict[str, Any],
    ) -> None:
        """Apply pattern configuration to a node tree."""
        if not BLENDER_AVAILABLE:
            return

        pattern_type = pattern_config.get("type", "tiles")

        # Create appropriate procedural pattern
        nodes = node_tree.nodes
        links = node_tree.links

        # Create coordinate and mapping nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (pattern_config.get("scale", 1.0),) * 3

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        # Create pattern-specific nodes
        if pattern_type == "tiles" or pattern_type == "bricks":
            brick_tex = nodes.new('ShaderNodeTexBrick')
            brick_tex.inputs['Scale'].default_value = 1.0
            brick_tex.inputs['Mortar Size'].default_value = pattern_config.get("mortar_width", 0.05)
            links.new(mapping.outputs['Vector'], brick_tex.inputs['Vector'])

        elif pattern_type == "checkerboard":
            checker_tex = nodes.new('ShaderNodeTexChecker')
            checker_tex.inputs['Scale'].default_value = pattern_config.get("scale", 1.0) * 5
            links.new(mapping.outputs['Vector'], checker_tex.inputs['Vector'])

        elif pattern_type == "voronoi" or pattern_type == "voronoi_cells":
            voronoi_tex = nodes.new('ShaderNodeTexVoronoi')
            voronoi_tex.inputs['Scale'].default_value = pattern_config.get("scale", 1.0) * 5
            voronoi_tex.inputs['Randomness'].default_value = pattern_config.get("randomness", 0.5)
            links.new(mapping.outputs['Vector'], voronoi_tex.inputs['Vector'])

        elif pattern_type == "noise" or pattern_type == "noise_pattern":
            noise_tex = nodes.new('ShaderNodeTexNoise')
            noise_tex.inputs['Scale'].default_value = pattern_config.get("scale", 1.0) * 5
            noise_tex.inputs['Detail'].default_value = pattern_config.get("detail", 3)
            links.new(mapping.outputs['Vector'], noise_tex.inputs['Vector'])

        elif pattern_type == "wave":
            wave_tex = nodes.new('ShaderNodeTexWave')
            wave_tex.inputs['Scale'].default_value = pattern_config.get("scale", 1.0) * 5
            links.new(mapping.outputs['Vector'], wave_tex.inputs['Vector'])

    def layer_materials(
        self,
        base: Material,
        overlay: Material,
        mask_type: str = "edge_wear",
        blend_mode: str = "mix",
        opacity: float = 1.0,
    ) -> Material:
        """
        Layer two materials together with a mask.

        Args:
            base: Base material
            overlay: Overlay material to blend on top
            mask_type: Type of mask (edge_wear, noise, curvature, etc.)
            blend_mode: Blend mode (mix, multiply, add, overlay)
            opacity: Overlay opacity (0.0 - 1.0)

        Returns:
            New material with layers combined
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to layer materials")

        # Create new layered material
        layered_mat = bpy.data.materials.new(name=f"{base.name}_layered")
        layered_mat.use_nodes = True

        node_tree = layered_mat.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        # Clear default nodes
        for node in nodes:
            nodes.remove(node)

        # Create mix shader
        mix_shader = nodes.new('ShaderNodeMixShader')
        mix_shader.inputs['Fac'].default_value = opacity

        # Add material outputs
        output = nodes.new('ShaderNodeOutputMaterial')

        # Link nodes
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

        return layered_mat

    def create_mask(
        self,
        mask_type: str = "edge_wear",
        resolution: int = 1024,
        **kwargs,
    ) -> "bpy.types.Image":
        """
        Create a procedural mask texture.

        Args:
            mask_type: Type of mask to generate
            resolution: Texture resolution
            **kwargs: Additional parameters for mask generation

        Returns:
            Generated mask image
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to create masks")

        # Create new image
        image = bpy.data.images.new(
            name=f"Sanctus_Mask_{mask_type}",
            width=resolution,
            height=resolution,
            alpha=True,
        )

        # Generate mask data based on type
        pixels = [0.0] * (resolution * resolution * 4)

        if mask_type == "edge_wear":
            intensity = kwargs.get("intensity", 0.5)
            for i in range(0, len(pixels), 4):
                x = (i // 4) % resolution
                y = (i // 4) // resolution
                # Simple edge detection based on distance from edge
                edge_dist = min(
                    x, y,
                    resolution - x - 1,
                    resolution - y - 1
                ) / (resolution * 0.1)
                value = max(0.0, min(1.0, edge_dist * intensity))
                pixels[i] = value
                pixels[i + 1] = value
                pixels[i + 2] = value
                pixels[i + 3] = 1.0

        elif mask_type == "noise":
            scale = kwargs.get("scale", 1.0)
            threshold = kwargs.get("threshold", 0.5)
            random.seed(kwargs.get("seed", 0))
            for i in range(0, len(pixels), 4):
                x = (i // 4) % resolution
                y = (i // 4) // resolution
                # Simple Perlin-like noise approximation
                noise_val = random.random()
                value = 1.0 if noise_val > threshold else 0.0
                pixels[i] = value
                pixels[i + 1] = value
                pixels[i + 2] = value
                pixels[i + 3] = 1.0

        image.pixels = pixels
        return image

    def get_performance_rating(self, tool_name: str) -> PerformanceRating:
        """
        Get the performance rating for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Performance rating (GREEN, YELLOW, or RED)
        """
        tool = self.get_tool(tool_name)
        if tool:
            return tool.performance
        return PerformanceRating.YELLOW

    def is_eevee_compatible(self, tool_name: str) -> bool:
        """
        Check if a tool is Eevee compatible.

        Args:
            tool_name: Name of the tool

        Returns:
            True if Eevee compatible
        """
        tool = self.get_tool(tool_name)
        if tool:
            return tool.eevee_compatible
        return True

    def is_cycles_compatible(self, tool_name: str) -> bool:
        """
        Check if a tool is Cycles compatible.

        Args:
            tool_name: Name of the tool

        Returns:
            True if Cycles compatible
        """
        tool = self.get_tool(tool_name)
        if tool:
            return tool.cycles_compatible
        return True

    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get complete information about a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dictionary with tool information
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {}

        return {
            "name": tool.name,
            "display_name": tool.display_name,
            "category": tool.category.name,
            "performance": tool.performance.value,
            "eevee_compatible": tool.eevee_compatible,
            "cycles_compatible": tool.cycles_compatible,
            "description": tool.description,
            "parameters": tool.parameters,
        }
