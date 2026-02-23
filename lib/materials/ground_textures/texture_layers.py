"""
Ground Texture Layering System

Layered texture system for combining multiple ground materials
(asphalt, dirt, gravel, etc.) with procedural blending.

Based on Polygon Runway texture painting workflow:
- Multiple texture layers (base + overlays)
- Mix shader blending with painted masks
- Node Wrangler-compatible texture import (Ctrl+Shift+T)
- Procedural mask generation for natural blending

Usage:
    from lib.materials.ground_textures import (
        TextureLayer,
        LayeredTextureConfig,
        LayeredTextureManager,
        create_asphalt_with_dirt,
        create_road_material,
    )

    # Create a layered road material
    manager = LayeredTextureManager()
    config = create_asphalt_with_dirt()
    node_setup = manager.generate_shader_nodes(config)
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
    from bpy.types import Material, ShaderNodeTree, Image
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    ShaderNodeTree = Any
    Image = Any


class TextureLayerType(Enum):
    """Types of ground texture layers."""
    ASPHALT = "asphalt"
    CONCRETE = "concrete"
    DIRT = "dirt"
    GRAVEL = "gravel"
    SAND = "sand"
    MUD = "mud"
    GRASS = "grass"
    COBBLESTONE = "cobblestone"
    BRICK = "brick"
    PAINT = "paint"  # Road markings
    RUST = "rust"
    MOSS = "moss"


class BlendMode(Enum):
    """How texture layers blend together."""
    MIX = "mix"
    ADD = "add"
    MULTIPLY = "multiply"
    OVERLAY = "overlay"
    SCREEN = "screen"
    SUBTRACT = "subtract"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"


class MaskType(Enum):
    """Types of procedural masks for layer blending."""
    PAINTED = "painted"  # Hand-painted vertex/texture mask
    NOISE = "noise"  # Procedural noise mask
    EDGE = "edge"  # Edge-based wear
    DISTANCE = "distance"  # Distance from center/edges
    VORONOI = "voronoi"  # Voronoi cell-based
    GRUNGE = "grunge"  # Custom grunge brush pattern
    GRADIENT = "gradient"  # Directional gradient


@dataclass
class TextureMaps:
    """
    PBR texture maps for a single layer.

    Supports Node Wrangler-style import (Ctrl+Shift+T)
    with automatic map detection from naming conventions.
    """
    base_color: Optional[str] = None  # albedo/diffuse path
    roughness: Optional[str] = None
    normal: Optional[str] = None
    normal_strength: float = 1.0
    displacement: Optional[str] = None
    displacement_strength: float = 0.1
    ao: Optional[str] = None  # ambient occlusion
    metallic: Optional[str] = None
    specular: Optional[str] = None

    # Procedural fallbacks if no textures provided
    procedural_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
    procedural_roughness: float = 0.5
    procedural_scale: float = 1.0

    @classmethod
    def from_directory(cls, directory: str, prefix: str = "") -> "TextureMaps":
        """
        Auto-detect texture maps from a directory.

        Follows common naming conventions:
        - *_color*, *_albedo*, *_diffuse* → Base Color
        - *_roughness*, *_rough* → Roughness
        - *_normal*, *_nrm*, *_gl* → Normal
        - *_displacement*, *_height*, *_disp* → Displacement
        - *_ao*, *_ambient* → AO
        - *_metallic*, *_metal* → Metallic

        Args:
            directory: Directory containing texture files
            prefix: Optional prefix to filter files

        Returns:
            TextureMaps with detected paths
        """
        import os
        import glob

        maps = cls()
        patterns = {
            "base_color": ["*color*", "*albedo*", "*diffuse*"],
            "roughness": ["*roughness*", "*rough*"],
            "normal": ["*normal*", "*nrm*", "*gl*"],
            "displacement": ["*displacement*", "*height*", "*disp*"],
            "ao": ["*ao*", "*ambient*"],
            "metallic": ["*metallic*", "*metal*"],
        }

        for map_type, pats in patterns.items():
            for pat in pats:
                if prefix:
                    full_pat = os.path.join(directory, f"{prefix}{pat}*")
                else:
                    full_pat = os.path.join(directory, pat)

                files = glob.glob(full_pat + ".png") + glob.glob(full_pat + ".jpg")
                if files:
                    setattr(maps, map_type, files[0])
                    break

        return maps


@dataclass
class TextureLayer:
    """
    A single texture layer in a layered material.

    Each layer has its own PBR textures and a mask
    that controls how it blends with layers below.
    """
    name: str
    layer_type: TextureLayerType
    maps: TextureMaps
    blend_mode: BlendMode = BlendMode.MIX
    blend_factor: float = 1.0  # Overall layer opacity

    # Mask configuration
    mask_type: MaskType = MaskType.NOISE
    mask_texture: Optional[str] = None  # Custom mask texture path
    mask_scale: float = 1.0
    mask_contrast: float = 1.0
    mask_invert: bool = False

    # Transform
    uv_scale: float = 1.0
    uv_rotation: float = 0.0
    uv_offset: Tuple[float, float] = (0.0, 0.0)

    # Layer-specific adjustments
    color_adjust: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    # (hue, saturation, value, brightness)
    roughness_mult: float = 1.0
    normal_mult: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "layer_type": self.layer_type.value,
            "blend_mode": self.blend_mode.value,
            "blend_factor": self.blend_factor,
            "mask_type": self.mask_type.value,
            "mask_scale": self.mask_scale,
            "mask_contrast": self.mask_contrast,
            "mask_invert": self.mask_invert,
            "uv_scale": self.uv_scale,
            "uv_rotation": self.uv_rotation,
            "uv_offset": list(self.uv_offset),
            "roughness_mult": self.roughness_mult,
            "normal_mult": self.normal_mult,
        }


@dataclass
class PaintedMask:
    """
    Hand-painted mask for layer blending.

    Supports Blender's texture painting workflow
    with custom brushes and grunge patterns.
    """
    name: str
    resolution: Tuple[int, int] = (2048, 2048)
    paint_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)

    # Brush settings
    brush_strength: float = 1.0
    brush_size: float = 50.0
    brush_falloff: float = 0.5  # Softness

    # Grunge brush overlay
    grunge_intensity: float = 0.3
    grunge_scale: float = 5.0
    grunge_seed: int = 0

    # Edge effects
    edge_chaos: float = 0.2  # How ragged/chaotic the edges are
    edge_softness: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "resolution": list(self.resolution),
            "brush_strength": self.brush_strength,
            "brush_size": self.brush_size,
            "grunge_intensity": self.grunge_intensity,
            "edge_chaos": self.edge_chaos,
        }


@dataclass
class LayeredTextureConfig:
    """
    Configuration for a complete layered texture setup.

    Defines multiple texture layers with blending and masking.
    """
    name: str
    layers: List[TextureLayer] = field(default_factory=list)
    painted_masks: List[PaintedMask] = field(default_factory=list)

    # Global settings
    uv_channel: str = "UV"
    triplanar: bool = False  # Use triplanar mapping
    triplanar_blend: float = 0.5

    # Output settings
    output_ao: bool = True
    output_curvature: bool = False

    def add_layer(
        self,
        name: str,
        layer_type: TextureLayerType,
        maps: TextureMaps,
        mask_type: MaskType = MaskType.NOISE,
        **kwargs
    ) -> TextureLayer:
        """Add a new layer to the configuration."""
        layer = TextureLayer(
            name=name,
            layer_type=layer_type,
            maps=maps,
            mask_type=mask_type,
            **kwargs
        )
        self.layers.append(layer)
        return layer

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "layers": [l.to_dict() for l in self.layers],
            "painted_masks": [m.to_dict() for m in self.painted_masks],
            "uv_channel": self.uv_channel,
            "triplanar": self.triplanar,
        }


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

GROUND_TEXTURE_PRESETS = {
    "asphalt_clean": {
        "description": "Clean asphalt road surface",
        "base_layer": {
            "type": TextureLayerType.ASPHALT,
            "color": (0.15, 0.15, 0.15),
            "roughness": 0.7,
            "scale": 2.0,
        },
    },
    "asphalt_dirty": {
        "description": "Dirty asphalt with dust and grime",
        "base_layer": {
            "type": TextureLayerType.ASPHALT,
            "color": (0.12, 0.12, 0.12),
            "roughness": 0.75,
            "scale": 2.0,
        },
        "overlays": [
            {
                "type": TextureLayerType.DIRT,
                "blend": 0.4,
                "mask": MaskType.NOISE,
                "color": (0.35, 0.3, 0.25),
            },
        ],
    },
    "asphalt_worn": {
        "description": "Worn asphalt with cracks and patches",
        "base_layer": {
            "type": TextureLayerType.ASPHALT,
            "color": (0.18, 0.17, 0.16),
            "roughness": 0.8,
        },
        "overlays": [
            {
                "type": TextureLayerType.DIRT,
                "blend": 0.5,
                "mask": MaskType.GRUNGE,
                "color": (0.3, 0.25, 0.2),
            },
            {
                "type": TextureLayerType.GRAVEL,
                "blend": 0.2,
                "mask": MaskType.EDGE,
                "color": (0.4, 0.38, 0.35),
            },
        ],
    },
    "concrete_clean": {
        "description": "Clean concrete surface",
        "base_layer": {
            "type": TextureLayerType.CONCRETE,
            "color": (0.6, 0.58, 0.55),
            "roughness": 0.5,
            "scale": 1.5,
        },
    },
    "concrete_stained": {
        "description": "Concrete with stains and wear",
        "base_layer": {
            "type": TextureLayerType.CONCRETE,
            "color": (0.55, 0.52, 0.48),
            "roughness": 0.55,
        },
        "overlays": [
            {
                "type": TextureLayerType.DIRT,
                "blend": 0.3,
                "mask": MaskType.VORONOI,
                "color": (0.35, 0.3, 0.25),
            },
        ],
    },
    "dirt_road": {
        "description": "Dirt road with tire tracks",
        "base_layer": {
            "type": TextureLayerType.DIRT,
            "color": (0.4, 0.35, 0.25),
            "roughness": 0.9,
            "scale": 3.0,
        },
        "overlays": [
            {
                "type": TextureLayerType.GRAVEL,
                "blend": 0.3,
                "mask": MaskType.NOISE,
                "color": (0.45, 0.42, 0.38),
            },
        ],
    },
    "cobblestone_wet": {
        "description": "Wet cobblestone street",
        "base_layer": {
            "type": TextureLayerType.COBBLESTONE,
            "color": (0.35, 0.32, 0.3),
            "roughness": 0.3,  # Wet = low roughness
            "scale": 0.5,
        },
        "overlays": [
            {
                "type": TextureLayerType.DIRT,
                "blend": 0.2,
                "mask": MaskType.GRUNGE,
                "color": (0.2, 0.18, 0.15),
            },
        ],
    },
}


# =============================================================================
# LAYERED TEXTURE MANAGER
# =============================================================================

class LayeredTextureManager:
    """
    Manager for creating layered ground textures.

    Handles layer stacking, mask generation, and Blender
    shader node setup for multi-layer ground materials.
    """

    def __init__(self):
        """Initialize the layered texture manager."""
        self.configs: Dict[str, LayeredTextureConfig] = {}

    def create_config(
        self,
        name: str,
        base_type: TextureLayerType = TextureLayerType.ASPHALT,
    ) -> LayeredTextureConfig:
        """
        Create a new layered texture configuration.

        Args:
            name: Configuration name
            base_type: Base layer type

        Returns:
            New LayeredTextureConfig
        """
        config = LayeredTextureConfig(name=name)

        # Add base layer
        base_maps = TextureMaps(
            procedural_color=(0.15, 0.15, 0.15),
            procedural_roughness=0.7,
            procedural_scale=2.0,
        )
        config.add_layer(
            name="base",
            layer_type=base_type,
            maps=base_maps,
            blend_factor=1.0,
            mask_type=MaskType.NOISE,
        )

        self.configs[name] = config
        return config

    def add_overlay(
        self,
        config: LayeredTextureConfig,
        layer_type: TextureLayerType,
        blend_factor: float = 0.5,
        mask_type: MaskType = MaskType.NOISE,
        mask_scale: float = 5.0,
        color: Tuple[float, float, float] = (0.35, 0.3, 0.25),
    ) -> TextureLayer:
        """
        Add an overlay layer to a configuration.

        Args:
            config: Configuration to modify
            layer_type: Type of overlay layer
            blend_factor: How much the overlay shows (0-1)
            mask_type: Type of blending mask
            mask_scale: Scale of the mask pattern
            color: Procedural color if no texture

        Returns:
            The created overlay layer
        """
        maps = TextureMaps(
            procedural_color=color,
            procedural_roughness=0.8,
            procedural_scale=mask_scale,
        )

        layer = config.add_layer(
            name=f"overlay_{len(config.layers)}",
            layer_type=layer_type,
            maps=maps,
            blend_factor=blend_factor,
            mask_type=mask_type,
            mask_scale=mask_scale,
        )

        return layer

    def create_painted_mask(
        self,
        config: LayeredTextureConfig,
        name: str,
        resolution: Tuple[int, int] = (2048, 2048),
        grunge_intensity: float = 0.3,
    ) -> PaintedMask:
        """
        Create a painted mask for texture painting workflow.

        Args:
            config: Configuration to add mask to
            name: Mask name
            resolution: Mask texture resolution
            grunge_intensity: Amount of grunge overlay

        Returns:
            Created PaintedMask
        """
        mask = PaintedMask(
            name=name,
            resolution=resolution,
            grunge_intensity=grunge_intensity,
        )
        config.painted_masks.append(mask)
        return mask

    def generate_mask_node_setup(
        self,
        mask_type: MaskType,
        scale: float = 5.0,
        contrast: float = 1.0,
        seed: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate node configuration for a procedural mask.

        Args:
            mask_type: Type of mask to generate
            scale: Pattern scale
            contrast: Mask contrast
            seed: Random seed

        Returns:
            Dictionary with node setup configuration
        """
        base_setup = {
            "type": mask_type.value,
            "scale": scale,
            "contrast": contrast,
            "seed": seed,
        }

        if mask_type == MaskType.NOISE:
            base_setup["nodes"] = [
                {"type": "ShaderNodeTexNoise", "name": "mask_noise"},
                {"type": "ShaderNodeMapRange", "name": "mask_contrast"},
            ]
            base_setup["noise_config"] = {
                "scale": scale,
                "detail": 4,
                "distortion": 0.5,
            }

        elif mask_type == MaskType.VORONOI:
            base_setup["nodes"] = [
                {"type": "ShaderNodeTexVoronoi", "name": "mask_voronoi"},
                {"type": "ShaderNodeMapRange", "name": "mask_contrast"},
            ]
            base_setup["voronoi_config"] = {
                "scale": scale,
                "randomness": 0.8,
            }

        elif mask_type == MaskType.GRUNGE:
            base_setup["nodes"] = [
                {"type": "ShaderNodeTexNoise", "name": "grunge_noise1"},
                {"type": "ShaderNodeTexNoise", "name": "grunge_noise2"},
                {"type": "ShaderNodeMixRGB", "name": "grunge_mix", "blend_type": "MULTIPLY"},
                {"type": "ShaderNodeMath", "name": "grunge_power", "operation": "POWER"},
            ]
            base_setup["grunge_config"] = {
                "noise1_scale": scale,
                "noise2_scale": scale * 3,
                "power": 1.5,
            }

        elif mask_type == MaskType.EDGE:
            base_setup["nodes"] = [
                {"type": "ShaderNodeNewGeometry", "name": "geo_input"},
                {"type": "ShaderNodeVectorMath", "name": "edge_detect", "operation": "LENGTH"},
            ]
            base_setup["edge_config"] = {
                "use_pointiness": True,
                "invert": False,
            }

        elif mask_type == MaskType.GRADIENT:
            base_setup["nodes"] = [
                {"type": "ShaderNodeTexCoord", "name": "tex_coord"},
                {"type": "ShaderNodeSeparateXYZ", "name": "separate"},
                {"type": "ShaderNodeMath", "name": "gradient_math"},
            ]
            base_setup["gradient_config"] = {
                "axis": "Y",  # X, Y, or Z
                "direction": "bottom_to_top",
            }

        elif mask_type == MaskType.PAINTED:
            base_setup["nodes"] = [
                {"type": "ShaderNodeTexImage", "name": "painted_mask"},
            ]
            base_setup["painted_config"] = {
                "use_vertex_colors": False,
                "texture_slot": 0,
            }

        return base_setup

    def generate_shader_nodes(
        self,
        config: LayeredTextureConfig,
        output_path: str = ""
    ) -> Dict[str, Any]:
        """
        Generate complete shader node setup for layered texture.

        Creates a node graph with:
        - Texture coordinate and mapping for each layer
        - PBR texture nodes (or procedural fallbacks)
        - Mask generation for blending
        - Mix shader/mix color nodes for layering
        - Final BSDF output

        Args:
            config: Layered texture configuration
            output_path: Optional path to save node setup JSON

        Returns:
            Dictionary with complete node setup configuration
        """
        setup = {
            "config_name": config.name,
            "layers": [],
            "nodes": [],
            "links": [],
            "groups": {},
        }

        # Common nodes
        setup["nodes"].extend([
            {"type": "ShaderNodeTexCoord", "name": "tex_coord", "location": (-800, 0)},
            {"type": "ShaderNodeOutputMaterial", "name": "output", "location": (800, 0)},
        ])

        current_y = 400
        layer_output = None

        for i, layer in enumerate(config.layers):
            layer_setup = {
                "name": layer.name,
                "type": layer.layer_type.value,
                "blend_mode": layer.blend_mode.value,
                "blend_factor": layer.blend_factor,
            }

            # Mapping node for this layer
            mapping_name = f"mapping_{layer.name}"
            setup["nodes"].append({
                "type": "ShaderNodeMapping",
                "name": mapping_name,
                "location": (-600, current_y),
                "properties": {
                    "scale": (layer.uv_scale, layer.uv_scale, 1.0),
                    "rotation": (0, 0, layer.uv_rotation),
                    "translation": (*layer.uv_offset, 0),
                }
            })

            # Link tex coord to mapping
            setup["links"].append({
                "from_node": "tex_coord",
                "from_socket": "UV",
                "to_node": mapping_name,
                "to_socket": "Vector",
            })

            # PBR texture nodes (simplified for procedural)
            if layer.maps.base_color is None:
                # Procedural generation
                noise_name = f"noise_{layer.name}"
                setup["nodes"].append({
                    "type": "ShaderNodeTexNoise",
                    "name": noise_name,
                    "location": (-400, current_y),
                    "properties": {
                        "scale": layer.maps.procedural_scale * 10,
                        "detail": 4,
                    }
                })
                setup["links"].append({
                    "from_node": mapping_name,
                    "from_socket": "Vector",
                    "to_node": noise_name,
                    "to_socket": "Vector",
                })

                color_ramp_name = f"color_ramp_{layer.name}"
                setup["nodes"].append({
                    "type": "ShaderNodeValToRGB",
                    "name": color_ramp_name,
                    "location": (-200, current_y),
                })
                setup["links"].append({
                    "from_node": noise_name,
                    "from_socket": "Fac",
                    "to_node": color_ramp_name,
                    "to_socket": "Fac",
                })

                layer_setup["color_source"] = color_ramp_name

            # Mask setup
            mask_setup = self.generate_mask_node_setup(
                layer.mask_type,
                scale=layer.mask_scale,
                contrast=layer.mask_contrast,
            )
            layer_setup["mask"] = mask_setup

            # Mix node for blending
            mix_name = f"mix_{layer.name}"
            if layer.blend_mode == BlendMode.MIX:
                mix_type = "ShaderNodeMixShader"
            else:
                mix_type = "ShaderNodeMixRGB"

            setup["nodes"].append({
                "type": mix_type,
                "name": mix_name,
                "location": (200 + i * 100, current_y),
                "blend_type": layer.blend_mode.value if mix_type == "ShaderNodeMixRGB" else None,
            })

            layer_setup["mix_node"] = mix_name
            setup["layers"].append(layer_setup)

            current_y -= 300

        # Save if path provided
        if output_path:
            import json
            with open(output_path, 'w') as f:
                json.dump(setup, f, indent=2)

        return setup

    def apply_to_material(
        self,
        config: LayeredTextureConfig,
        material: Optional[Material] = None,
        material_name: str = "GroundMaterial"
    ) -> Optional[Material]:
        """
        Apply layered texture configuration to a Blender material.

        Creates actual shader nodes in Blender based on the configuration.

        Args:
            config: Layered texture configuration
            material: Existing material to modify (optional)
            material_name: Name for new material if creating

        Returns:
            Modified or created material
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender is required to apply materials")

        # Create or use existing material
        if material is None:
            material = bpy.data.materials.new(name=material_name)

        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear existing nodes
        nodes.clear()

        # Generate node setup
        setup = self.generate_shader_nodes(config)

        # Create nodes
        created_nodes = {}
        for node_def in setup["nodes"]:
            node = nodes.new(node_def["type"])
            node.name = node_def["name"]
            node.label = node_def.get("name", node_def["type"])

            if "location" in node_def:
                node.location = node_def["location"]

            if "properties" in node_def:
                for prop, value in node_def["properties"].items():
                    try:
                        setattr(node.inputs[prop], "default_value", value)
                    except (KeyError, AttributeError):
                        pass

            if "blend_type" in node_def and node_def["blend_type"]:
                try:
                    node.blend_type = node_def["blend_type"].upper()
                except AttributeError:
                    pass

            created_nodes[node_def["name"]] = node

        # Create links
        for link_def in setup["links"]:
            try:
                from_node = created_nodes[link_def["from_node"]]
                to_node = created_nodes[link_def["to_node"]]
                links.new(
                    from_node.outputs[link_def["from_socket"]],
                    to_node.inputs[link_def["to_socket"]]
                )
            except (KeyError, AttributeError):
                pass

        return material


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_asphalt_with_dirt(
    dirt_amount: float = 0.4,
    grunge_edges: bool = True,
) -> LayeredTextureConfig:
    """
    Create a standard asphalt with dirt overlay configuration.

    Based on Polygon Runway tutorial workflow:
    - Base asphalt layer
    - Dirt overlay with noise/grunge mask
    - Optional edge grunge for natural blending

    Args:
        dirt_amount: Amount of dirt overlay (0-1)
        grunge_edges: Add grunge to dirt edges

    Returns:
        LayeredTextureConfig ready for use
    """
    manager = LayeredTextureManager()
    config = manager.create_config("asphalt_dirt", TextureLayerType.ASPHALT)

    # Configure base layer
    config.layers[0].maps.procedural_color = (0.15, 0.15, 0.15)
    config.layers[0].maps.procedural_roughness = 0.7
    config.layers[0].uv_scale = 2.0

    # Add dirt overlay
    dirt_layer = manager.add_overlay(
        config,
        layer_type=TextureLayerType.DIRT,
        blend_factor=dirt_amount,
        mask_type=MaskType.GRUNGE if grunge_edges else MaskType.NOISE,
        mask_scale=5.0,
        color=(0.35, 0.3, 0.25),
    )

    return config


def create_road_material(
    surface_type: str = "asphalt",
    wear_level: str = "medium",
    wetness: float = 0.0,
) -> LayeredTextureConfig:
    """
    Create a road surface material configuration.

    Args:
        surface_type: "asphalt", "concrete", or "cobblestone"
        wear_level: "clean", "medium", "worn"
        wetness: Wetness amount 0-1 (affects roughness)

    Returns:
        LayeredTextureConfig for the road material
    """
    manager = LayeredTextureManager()

    type_mapping = {
        "asphalt": TextureLayerType.ASPHALT,
        "concrete": TextureLayerType.CONCRETE,
        "cobblestone": TextureLayerType.COBBLESTONE,
    }

    base_type = type_mapping.get(surface_type, TextureLayerType.ASPHALT)
    config = manager.create_config(f"road_{surface_type}_{wear_level}", base_type)

    # Adjust based on wear level
    if wear_level == "clean":
        config.layers[0].maps.procedural_roughness = 0.5 - wetness * 0.3
    elif wear_level == "medium":
        config.layers[0].maps.procedural_roughness = 0.7 - wetness * 0.3
        manager.add_overlay(
            config,
            layer_type=TextureLayerType.DIRT,
            blend_factor=0.3,
            mask_type=MaskType.NOISE,
            color=(0.35, 0.3, 0.25),
        )
    elif wear_level == "worn":
        config.layers[0].maps.procedural_roughness = 0.8 - wetness * 0.3
        manager.add_overlay(
            config,
            layer_type=TextureLayerType.DIRT,
            blend_factor=0.5,
            mask_type=MaskType.GRUNGE,
            color=(0.3, 0.25, 0.2),
        )
        manager.add_overlay(
            config,
            layer_type=TextureLayerType.GRAVEL,
            blend_factor=0.2,
            mask_type=MaskType.EDGE,
            color=(0.4, 0.38, 0.35),
        )

    # Apply wetness to roughness
    for layer in config.layers:
        layer.roughness_mult = 1.0 - wetness * 0.5

    return config


def create_painted_marking_material(
    base_material: LayeredTextureConfig,
    marking_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    paint_quality: str = "fresh",
) -> LayeredTextureConfig:
    """
    Add road marking paint layer to a ground material.

    Args:
        base_material: Base ground material config
        marking_color: Paint color (white/yellow/red)
        paint_quality: "fresh", "faded", or "worn"

    Returns:
        Modified LayeredTextureConfig with paint layer
    """
    manager = LayeredTextureManager()

    # Add paint layer
    paint_maps = TextureMaps(
        procedural_color=marking_color,
        procedural_roughness=0.4,
        procedural_scale=1.0,
    )

    blend_factor = {"fresh": 1.0, "faded": 0.7, "worn": 0.4}.get(paint_quality, 0.8)

    base_material.add_layer(
        name="road_marking",
        layer_type=TextureLayerType.PAINT,
        maps=paint_maps,
        blend_factor=blend_factor,
        mask_type=MaskType.PAINTED,  # Requires painted mask
        roughness_mult=0.5,
    )

    return base_material


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "TextureLayerType",
    "BlendMode",
    "MaskType",
    # Dataclasses
    "TextureMaps",
    "TextureLayer",
    "PaintedMask",
    "LayeredTextureConfig",
    # Manager
    "LayeredTextureManager",
    # Presets
    "GROUND_TEXTURE_PRESETS",
    # Functions
    "create_asphalt_with_dirt",
    "create_road_material",
    "create_painted_marking_material",
]
