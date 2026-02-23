"""
Sanctus Material System Integration

Integration between ground texture system and Sanctus weathering/material system.
Provides weathered ground materials with dirt accumulation, edge wear, and more.

Usage:
    from lib.materials.ground_textures import (
        SanctusGroundIntegration,
        WeatheredGroundConfig,
        create_weathered_road_material,
        apply_road_weathering,
    )

    # Create weathered road material
    integration = SanctusGroundIntegration()
    config = create_weathered_road_material(
        base_type="asphalt",
        wear_level="heavy",
        wetness=0.2
    )
    material = integration.create_material(config)
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

from .texture_layers import (
    TextureLayerType,
    BlendMode,
    MaskType,
    TextureMaps,
    TextureLayer,
    LayeredTextureConfig,
    LayeredTextureManager,
    create_asphalt_with_dirt,
    create_road_material,
)

from .painted_masks import (
    BrushType,
    MaskEdgeMode,
    GrungeBrush,
    MaskTexture,
    PaintedMaskWorkflow,
    create_grunge_brush,
    generate_road_dirt_mask,
)

try:
    import bpy
    from bpy.types import Material, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    ShaderNodeTree = Any


class RoadWeatheringLevel(Enum):
    """Levels of road weathering."""
    CLEAN = "clean"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    ABANDONED = "abandoned"


class RoadEnvironment(Enum):
    """Environmental conditions affecting road wear."""
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    INDUSTRIAL = "industrial"
    COASTAL = "coastal"
    DESERT = "desert"


@dataclass
class WeatheredGroundConfig:
    """
    Configuration for weathered ground materials.

    Combines layered textures with Sanctus-style weathering.
    """
    name: str
    base_type: TextureLayerType = TextureLayerType.ASPHALT
    weathering_level: RoadWeatheringLevel = RoadWeatheringLevel.MEDIUM
    environment: RoadEnvironment = RoadEnvironment.URBAN

    # Weathering parameters
    dirt_amount: float = 0.4
    edge_wear: float = 0.3
    crack_intensity: float = 0.0
    wetness: float = 0.0
    pollution: float = 0.2
    sun_bleaching: float = 0.0

    # Mask settings
    use_painted_mask: bool = True
    mask_resolution: int = 2048
    grunge_intensity: float = 0.3

    # Layer overrides
    layers: List[TextureLayer] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "base_type": self.base_type.value,
            "weathering_level": self.weathering_level.value,
            "environment": self.environment.value,
            "dirt_amount": self.dirt_amount,
            "edge_wear": self.edge_wear,
            "crack_intensity": self.crack_intensity,
            "wetness": self.wetness,
            "pollution": self.pollution,
            "sun_bleaching": self.sun_bleaching,
            "use_painted_mask": self.use_painted_mask,
            "mask_resolution": self.mask_resolution,
        }


# =============================================================================
# WEATHERING PRESETS BY ENVIRONMENT
# =============================================================================

ENVIRONMENT_PRESETS: Dict[RoadEnvironment, Dict[str, Any]] = {
    RoadEnvironment.URBAN: {
        "dirt_amount": 0.3,
        "edge_wear": 0.2,
        "pollution": 0.4,
        "grunge_intensity": 0.3,
    },
    RoadEnvironment.SUBURBAN: {
        "dirt_amount": 0.2,
        "edge_wear": 0.15,
        "pollution": 0.1,
        "grunge_intensity": 0.2,
    },
    RoadEnvironment.RURAL: {
        "dirt_amount": 0.5,
        "edge_wear": 0.4,
        "pollution": 0.0,
        "sun_bleaching": 0.2,
        "grunge_intensity": 0.4,
    },
    RoadEnvironment.INDUSTRIAL: {
        "dirt_amount": 0.6,
        "edge_wear": 0.5,
        "pollution": 0.7,
        "grunge_intensity": 0.5,
    },
    RoadEnvironment.COASTAL: {
        "dirt_amount": 0.3,
        "edge_wear": 0.3,
        "wetness": 0.3,
        "sun_bleaching": 0.3,
        "grunge_intensity": 0.35,
    },
    RoadEnvironment.DESERT: {
        "dirt_amount": 0.4,
        "edge_wear": 0.2,
        "sun_bleaching": 0.5,
        "grunge_intensity": 0.25,
    },
}

WEATHERING_LEVEL_MULTIPLIERS: Dict[RoadWeatheringLevel, float] = {
    RoadWeatheringLevel.CLEAN: 0.0,
    RoadWeatheringLevel.LIGHT: 0.3,
    RoadWeatheringLevel.MEDIUM: 0.6,
    RoadWeatheringLevel.HEAVY: 0.85,
    RoadWeatheringLevel.ABANDONED: 1.0,
}


# =============================================================================
# SANCTUS GROUND INTEGRATION
# =============================================================================

class SanctusGroundIntegration:
    """
    Integration between ground textures and Sanctus weathering.

    Provides:
    - Weathered ground material creation
    - Sanctus-compatible shader node setup
    - Environment-based weathering presets
    - Urban road system compatibility
    """

    def __init__(self):
        """Initialize the integration."""
        self.texture_manager = LayeredTextureManager()
        self.mask_workflow = PaintedMaskWorkflow()
        self.configs: Dict[str, WeatheredGroundConfig] = {}

    def create_config(
        self,
        name: str,
        base_type: TextureLayerType = TextureLayerType.ASPHALT,
        weathering_level: RoadWeatheringLevel = RoadWeatheringLevel.MEDIUM,
        environment: RoadEnvironment = RoadEnvironment.URBAN,
        **overrides
    ) -> WeatheredGroundConfig:
        """
        Create a weathered ground configuration.

        Args:
            name: Configuration name
            base_type: Base surface type
            weathering_level: Overall weathering level
            environment: Environmental conditions
            **overrides: Parameter overrides

        Returns:
            Created WeatheredGroundConfig
        """
        # Get environment preset
        env_preset = ENVIRONMENT_PRESETS.get(environment, {})
        level_mult = WEATHERING_LEVEL_MULTIPLIERS.get(weathering_level, 0.5)

        # Calculate parameters
        params = {
            "dirt_amount": env_preset.get("dirt_amount", 0.3) * level_mult,
            "edge_wear": env_preset.get("edge_wear", 0.2) * level_mult,
            "pollution": env_preset.get("pollution", 0.2) * level_mult,
            "sun_bleaching": env_preset.get("sun_bleaching", 0.0) * level_mult,
            "wetness": env_preset.get("wetness", 0.0),
            "grunge_intensity": env_preset.get("grunge_intensity", 0.3),
        }

        # Apply overrides
        params.update(overrides)

        config = WeatheredGroundConfig(
            name=name,
            base_type=base_type,
            weathering_level=weathering_level,
            environment=environment,
            **params
        )

        self.configs[name] = config
        return config

    def create_layered_config(
        self,
        weathered_config: WeatheredGroundConfig,
    ) -> LayeredTextureConfig:
        """
        Convert WeatheredGroundConfig to LayeredTextureConfig.

        Creates the layered texture structure with weathering.

        Args:
            weathered_config: Source weathered configuration

        Returns:
            LayeredTextureConfig with weathering layers
        """
        # Create base layered config
        layered = self.texture_manager.create_config(
            weathered_config.name,
            weathered_config.base_type,
        )

        # Adjust base layer based on weathering
        if layered.layers:
            base = layered.layers[0]
            base.maps.procedural_roughness = 0.7 - weathered_config.wetness * 0.4

            # Apply sun bleaching to base
            if weathered_config.sun_bleaching > 0:
                r, g, b = base.maps.procedural_color
                bleach = weathered_config.sun_bleaching
                base.maps.procedural_color = (
                    min(1.0, r + bleach * 0.2),
                    min(1.0, g + bleach * 0.15),
                    min(1.0, b + bleach * 0.1),
                )

        # Add dirt layer
        if weathered_config.dirt_amount > 0.1:
            dirt_layer = self.texture_manager.add_overlay(
                layered,
                layer_type=TextureLayerType.DIRT,
                blend_factor=weathered_config.dirt_amount,
                mask_type=MaskType.GRUNGE if weathered_config.grunge_intensity > 0.2 else MaskType.NOISE,
                mask_scale=5.0 + weathered_config.grunge_intensity * 5,
                color=(0.35 - weathered_config.pollution * 0.1,
                       0.3 - weathered_config.pollution * 0.05,
                       0.25),
            )

            # Adjust dirt for wetness
            if weathered_config.wetness > 0:
                dirt_layer.roughness_mult = 1.0 - weathered_config.wetness * 0.5

        # Add edge wear layer
        if weathered_config.edge_wear > 0.2:
            self.texture_manager.add_overlay(
                layered,
                layer_type=TextureLayerType.GRAVEL,
                blend_factor=weathered_config.edge_wear * 0.5,
                mask_type=MaskType.EDGE,
                mask_scale=3.0,
                color=(0.4, 0.38, 0.35),
            )

        # Add pollution staining for industrial
        if weathered_config.pollution > 0.3:
            self.texture_manager.add_overlay(
                layered,
                layer_type=TextureLayerType.DIRT,
                blend_factor=weathered_config.pollution * 0.3,
                mask_type=MaskType.NOISE,
                mask_scale=8.0,
                color=(0.25, 0.23, 0.2),  # Darker pollution color
            )

        return layered

    def generate_weathering_mask(
        self,
        config: WeatheredGroundConfig,
    ) -> MaskTexture:
        """
        Generate a weathering mask based on configuration.

        Args:
            config: Weathered ground configuration

        Returns:
            Generated MaskTexture
        """
        mask = self.mask_workflow.create_mask_texture(
            f"{config.name}_weather_mask",
            resolution=config.mask_resolution,
        )

        # Add edge wear
        if config.edge_wear > 0:
            self.mask_workflow.add_edge_wear_to_mask(
                mask,
                edge_width=0.1 + config.edge_wear * 0.1,
                chaos=config.grunge_intensity,
                intensity=config.edge_wear,
            )

        # Add dirt noise
        if config.dirt_amount > 0:
            self.mask_workflow.add_noise_to_mask(
                mask,
                scale=5.0,
                detail=4,
                intensity=config.dirt_amount,
                blend_mode="overlay",
            )

        # Add grunge detail
        if config.grunge_intensity > 0:
            brush = create_grunge_brush(
                "weather_grunge",
                intensity=config.grunge_intensity,
                scale=8.0,
            )
            self.mask_workflow.apply_grunge_to_mask(mask, brush)

        return mask

    def create_material(
        self,
        config: WeatheredGroundConfig,
        material_name: Optional[str] = None,
    ) -> Optional[Material]:
        """
        Create a Blender material from weathered configuration.

        Args:
            config: Weathered ground configuration
            material_name: Optional material name

        Returns:
            Created Blender material
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create layered config
        layered = self.create_layered_config(config)

        # Create material
        name = material_name or config.name
        material = self.texture_manager.apply_to_material(layered, material_name=name)

        # Apply Sanctus-style weathering adjustments
        if material:
            self._apply_sanctus_weathering(material, config)

        return material

    def _apply_sanctus_weathering(
        self,
        material: Material,
        config: WeatheredGroundConfig,
    ) -> None:
        """Apply Sanctus-compatible weathering to material."""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find principled BSDF
        bsdf = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break

        if not bsdf:
            return

        # Apply wetness (reduced roughness)
        if config.wetness > 0:
            current_roughness = bsdf.inputs['Roughness'].default_value
            bsdf.inputs['Roughness'].default_value = max(
                0.1, current_roughness - config.wetness * 0.5
            )

            # Slight specular increase for wet look
            bsdf.inputs['Specular IOR Level'].default_value = min(
                1.0, bsdf.inputs['Specular IOR Level'].default_value + config.wetness * 0.3
            )

        # Apply sun bleaching
        if config.sun_bleaching > 0:
            current_color = list(bsdf.inputs['Base Color'].default_value[:3])
            bleach = config.sun_bleaching
            new_color = (
                min(1.0, current_color[0] + bleach * 0.1),
                min(1.0, current_color[1] + bleach * 0.08),
                min(1.0, current_color[2] + bleach * 0.05),
            )
            bsdf.inputs['Base Color'].default_value = (*new_color, 1.0)

    def create_urban_road_material(
        self,
        road_type: str = "main",
        wear: str = "medium",
        district: str = "commercial",
    ) -> WeatheredGroundConfig:
        """
        Create a road material for urban scenes.

        Args:
            road_type: "main", "secondary", "alley", "highway"
            wear: "clean", "light", "medium", "heavy"
            district: "commercial", "residential", "industrial", "historic"

        Returns:
            WeatheredGroundConfig for urban road
        """
        # Map parameters
        wear_mapping = {
            "clean": RoadWeatheringLevel.CLEAN,
            "light": RoadWeatheringLevel.LIGHT,
            "medium": RoadWeatheringLevel.MEDIUM,
            "heavy": RoadWeatheringLevel.HEAVY,
        }

        district_env = {
            "commercial": RoadEnvironment.URBAN,
            "residential": RoadEnvironment.SUBURBAN,
            "industrial": RoadEnvironment.INDUSTRIAL,
            "historic": RoadEnvironment.URBAN,
        }

        weathering_level = wear_mapping.get(wear, RoadWeatheringLevel.MEDIUM)
        environment = district_env.get(district, RoadEnvironment.URBAN)

        # Adjust based on road type
        dirt_mult = {"main": 0.7, "secondary": 1.0, "alley": 1.5, "highway": 0.5}
        edge_mult = {"main": 0.5, "secondary": 0.8, "alley": 1.2, "highway": 0.3}

        dm = dirt_mult.get(road_type, 1.0)
        em = edge_mult.get(road_type, 1.0)

        config = self.create_config(
            name=f"urban_{road_type}_{wear}_{district}",
            base_type=TextureLayerType.ASPHALT,
            weathering_level=weathering_level,
            environment=environment,
        )

        # Apply multipliers
        config.dirt_amount *= dm
        config.edge_wear *= em

        return config


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_weathered_road_material(
    base_type: str = "asphalt",
    wear_level: str = "medium",
    wetness: float = 0.0,
    environment: str = "urban",
) -> WeatheredGroundConfig:
    """
    Create a weathered road material configuration.

    Args:
        base_type: "asphalt", "concrete", or "cobblestone"
        wear_level: "clean", "light", "medium", "heavy", "abandoned"
        wetness: Wetness amount 0-1
        environment: "urban", "suburban", "rural", "industrial", "coastal", "desert"

    Returns:
        WeatheredGroundConfig
    """
    integration = SanctusGroundIntegration()

    type_map = {
        "asphalt": TextureLayerType.ASPHALT,
        "concrete": TextureLayerType.CONCRETE,
        "cobblestone": TextureLayerType.COBBLESTONE,
    }

    wear_map = {
        "clean": RoadWeatheringLevel.CLEAN,
        "light": RoadWeatheringLevel.LIGHT,
        "medium": RoadWeatheringLevel.MEDIUM,
        "heavy": RoadWeatheringLevel.HEAVY,
        "abandoned": RoadWeatheringLevel.ABANDONED,
    }

    env_map = {
        "urban": RoadEnvironment.URBAN,
        "suburban": RoadEnvironment.SUBURBAN,
        "rural": RoadEnvironment.RURAL,
        "industrial": RoadEnvironment.INDUSTRIAL,
        "coastal": RoadEnvironment.COASTAL,
        "desert": RoadEnvironment.DESERT,
    }

    return integration.create_config(
        name=f"road_{base_type}_{wear_level}",
        base_type=type_map.get(base_type, TextureLayerType.ASPHALT),
        weathering_level=wear_map.get(wear_level, RoadWeatheringLevel.MEDIUM),
        environment=env_map.get(environment, RoadEnvironment.URBAN),
        wetness=wetness,
    )


def apply_road_weathering(
    material: Material,
    dirt_amount: float = 0.3,
    edge_wear: float = 0.2,
    wetness: float = 0.0,
) -> Material:
    """
    Apply weathering to an existing road material.

    Args:
        material: Blender material to modify
        dirt_amount: Amount of dirt (0-1)
        edge_wear: Amount of edge wear (0-1)
        wetness: Wetness amount (0-1)

    Returns:
        Modified material
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("Blender required")

    integration = SanctusGroundIntegration()
    config = integration.create_config(
        name="temp_weathering",
        dirt_amount=dirt_amount,
        edge_wear=edge_wear,
        wetness=wetness,
    )

    integration._apply_sanctus_weathering(material, config)
    return material


def get_environment_preset(environment: str) -> Dict[str, Any]:
    """
    Get weathering preset for an environment type.

    Args:
        environment: Environment type string

    Returns:
        Dictionary with weathering parameters
    """
    env_map = {
        "urban": RoadEnvironment.URBAN,
        "suburban": RoadEnvironment.SUBURBAN,
        "rural": RoadEnvironment.RURAL,
        "industrial": RoadEnvironment.INDUSTRIAL,
        "coastal": RoadEnvironment.COASTAL,
        "desert": RoadEnvironment.DESERT,
    }

    env = env_map.get(environment, RoadEnvironment.URBAN)
    return ENVIRONMENT_PRESETS.get(env, {})


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RoadWeatheringLevel",
    "RoadEnvironment",
    # Dataclasses
    "WeatheredGroundConfig",
    # Manager
    "SanctusGroundIntegration",
    # Presets
    "ENVIRONMENT_PRESETS",
    "WEATHERING_LEVEL_MULTIPLIERS",
    # Functions
    "create_weathered_road_material",
    "apply_road_weathering",
    "get_environment_preset",
]
