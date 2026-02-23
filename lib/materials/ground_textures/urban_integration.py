"""
Urban Road System Integration

Integration between ground texture system and urban road network generation.
Provides materials for procedural road geometry with proper texturing.

Usage:
    from lib.materials.ground_textures import (
        UrbanRoadMaterialManager,
        RoadMaterialConfig,
        create_road_surface_material,
        apply_materials_to_road_network,
    )

    # Create road materials
    manager = UrbanRoadMaterialManager()
    config = manager.create_road_material("main_road", surface="asphalt")
    material = manager.generate_material(config)

    # Apply to road network
    apply_materials_to_road_network(network, manager)
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
)

from .painted_masks import (
    MaskTexture,
    PaintedMaskWorkflow,
    generate_road_dirt_mask,
)

from .sanctus_integration import (
    RoadWeatheringLevel,
    RoadEnvironment,
    WeatheredGroundConfig,
    SanctusGroundIntegration,
    create_weathered_road_material,
)

try:
    import bpy
    from bpy.types import Material, Object, Collection
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    Object = Any
    Collection = Any


class RoadSurfaceType(Enum):
    """Types of road surfaces."""
    ASPHALT_FRESH = "asphalt_fresh"
    ASPHALT_WORN = "asphalt_worn"
    ASPHALT_DAMAGED = "asphalt_damaged"
    CONCRETE_FRESH = "concrete_fresh"
    CONCRETE_AGED = "concrete_aged"
    COBBLESTONE = "cobblestone"
    COBBLESTONE_WORN = "cobblestone_worn"
    BRICK = "brick"
    GRAVEL = "gravel"
    DIRT = "dirt"


class RoadZoneType(Enum):
    """Different zones on a road."""
    DRIVING_LANE = "driving_lane"
    BIKE_LANE = "bike_lane"
    PARKING = "parking"
    SIDEWALK = "sidewalk"
    CROSSWALK = "crosswalk"
    INTERSECTION = "intersection"
    SHOULDER = "shoulder"
    MEDIAN = "median"


@dataclass
class RoadMaterialConfig:
    """
    Configuration for a road material.

    Combines surface type, zone, and weathering.
    """
    name: str
    surface_type: RoadSurfaceType = RoadSurfaceType.ASPHALT_WORN
    zone_type: RoadZoneType = RoadZoneType.DRIVING_LANE

    # Weathering
    weathering_level: RoadWeatheringLevel = RoadWeatheringLevel.MEDIUM
    environment: RoadEnvironment = RoadEnvironment.URBAN

    # Zone-specific parameters
    tire_marks: float = 0.0  # Amount of tire marking
    oil_stains: float = 0.0
    wear_pattern: str = "uniform"  # uniform, center, edges, corners

    # Markings
    has_markings: bool = False
    marking_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    marking_wear: float = 0.3

    # Material properties
    roughness_base: float = 0.7
    wetness: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "surface_type": self.surface_type.value,
            "zone_type": self.zone_type.value,
            "weathering_level": self.weathering_level.value,
            "tire_marks": self.tire_marks,
            "oil_stains": self.oil_stains,
            "has_markings": self.has_markings,
            "roughness_base": self.roughness_base,
            "wetness": self.wetness,
        }


# =============================================================================
# ROAD MATERIAL PRESETS
# =============================================================================

ROAD_SURFACE_PRESETS: Dict[RoadSurfaceType, Dict[str, Any]] = {
    RoadSurfaceType.ASPHALT_FRESH: {
        "base_color": (0.12, 0.12, 0.12),
        "roughness": 0.7,
        "texture_scale": 2.0,
        "layers": [],
    },
    RoadSurfaceType.ASPHALT_WORN: {
        "base_color": (0.15, 0.14, 0.13),
        "roughness": 0.8,
        "texture_scale": 2.0,
        "layers": ["dirt_light", "edge_wear"],
    },
    RoadSurfaceType.ASPHALT_DAMAGED: {
        "base_color": (0.18, 0.16, 0.14),
        "roughness": 0.85,
        "texture_scale": 1.5,
        "layers": ["dirt_heavy", "cracks", "patches"],
    },
    RoadSurfaceType.CONCRETE_FRESH: {
        "base_color": (0.6, 0.58, 0.55),
        "roughness": 0.5,
        "texture_scale": 1.5,
        "layers": [],
    },
    RoadSurfaceType.CONCRETE_AGED: {
        "base_color": (0.55, 0.52, 0.48),
        "roughness": 0.55,
        "texture_scale": 1.5,
        "layers": ["dirt_light", "stains"],
    },
    RoadSurfaceType.COBBLESTONE: {
        "base_color": (0.35, 0.32, 0.3),
        "roughness": 0.6,
        "texture_scale": 0.5,
        "layers": [],
    },
    RoadSurfaceType.COBBLESTONE_WORN: {
        "base_color": (0.32, 0.29, 0.27),
        "roughness": 0.65,
        "texture_scale": 0.5,
        "layers": ["dirt_between", "moss_edges"],
    },
}

ZONE_CONFIGS: Dict[RoadZoneType, Dict[str, Any]] = {
    RoadZoneType.DRIVING_LANE: {
        "tire_marks": 0.3,
        "oil_stains": 0.1,
        "wear_pattern": "center",
    },
    RoadZoneType.BIKE_LANE: {
        "tire_marks": 0.1,
        "oil_stains": 0.0,
        "wear_pattern": "uniform",
    },
    RoadZoneType.PARKING: {
        "tire_marks": 0.4,
        "oil_stains": 0.3,
        "wear_pattern": "spots",
    },
    RoadZoneType.SIDEWALK: {
        "tire_marks": 0.0,
        "oil_stains": 0.0,
        "wear_pattern": "edges",
    },
    RoadZoneType.CROSSWALK: {
        "has_markings": True,
        "marking_wear": 0.3,
        "tire_marks": 0.2,
    },
    RoadZoneType.INTERSECTION: {
        "tire_marks": 0.4,
        "oil_stains": 0.2,
        "wear_pattern": "corners",
    },
    RoadZoneType.SHOULDER: {
        "tire_marks": 0.1,
        "dirt_amount": 0.5,
        "wear_pattern": "edges",
    },
    RoadZoneType.MEDIAN: {
        "tire_marks": 0.0,
        "dirt_amount": 0.3,
        "grass_patches": True,
    },
}


# =============================================================================
# URBAN ROAD MATERIAL MANAGER
# =============================================================================

class UrbanRoadMaterialManager:
    """
    Manager for creating and applying road materials.

    Handles:
    - Road surface material creation
    - Zone-specific variations
    - Road marking materials
    - Weathering and wear patterns
    """

    def __init__(self):
        """Initialize the road material manager."""
        self.texture_manager = LayeredTextureManager()
        self.sanctus_integration = SanctusGroundIntegration()
        self.mask_workflow = PaintedMaskWorkflow()
        self.configs: Dict[str, RoadMaterialConfig] = {}
        self.materials: Dict[str, Material] = {}

    def create_road_material(
        self,
        name: str,
        surface: str = "asphalt_worn",
        zone: str = "driving_lane",
        weathering: str = "medium",
        **overrides
    ) -> RoadMaterialConfig:
        """
        Create a road material configuration.

        Args:
            name: Configuration name
            surface: Surface type string
            zone: Zone type string
            weathering: Weathering level string
            **overrides: Parameter overrides

        Returns:
            Created RoadMaterialConfig
        """
        # Map strings to enums
        surface_map = {
            "asphalt_fresh": RoadSurfaceType.ASPHALT_FRESH,
            "asphalt_worn": RoadSurfaceType.ASPHALT_WORN,
            "asphalt_damaged": RoadSurfaceType.ASPHALT_DAMAGED,
            "concrete_fresh": RoadSurfaceType.CONCRETE_FRESH,
            "concrete_aged": RoadSurfaceType.CONCRETE_AGED,
            "cobblestone": RoadSurfaceType.COBBLESTONE,
            "cobblestone_worn": RoadSurfaceType.COBBLESTONE_WORN,
            "brick": RoadSurfaceType.BRICK,
            "gravel": RoadSurfaceType.GRAVEL,
            "dirt": RoadSurfaceType.DIRT,
        }

        zone_map = {
            "driving_lane": RoadZoneType.DRIVING_LANE,
            "bike_lane": RoadZoneType.BIKE_LANE,
            "parking": RoadZoneType.PARKING,
            "sidewalk": RoadZoneType.SIDEWALK,
            "crosswalk": RoadZoneType.CROSSWALK,
            "intersection": RoadZoneType.INTERSECTION,
            "shoulder": RoadZoneType.SHOULDER,
            "median": RoadZoneType.MEDIAN,
        }

        wear_map = {
            "clean": RoadWeatheringLevel.CLEAN,
            "light": RoadWeatheringLevel.LIGHT,
            "medium": RoadWeatheringLevel.MEDIUM,
            "heavy": RoadWeatheringLevel.HEAVY,
        }

        surface_type = surface_map.get(surface, RoadSurfaceType.ASPHALT_WORN)
        zone_type = zone_map.get(zone, RoadZoneType.DRIVING_LANE)
        weathering_level = wear_map.get(weathering, RoadWeatheringLevel.MEDIUM)

        # Get presets
        surface_preset = ROAD_SURFACE_PRESETS.get(surface_type, {})
        zone_config = ZONE_CONFIGS.get(zone_type, {})

        # Create config
        params = {
            **zone_config,
            "roughness_base": surface_preset.get("roughness", 0.7),
        }
        params.update(overrides)

        config = RoadMaterialConfig(
            name=name,
            surface_type=surface_type,
            zone_type=zone_type,
            weathering_level=weathering_level,
            **params
        )

        self.configs[name] = config
        return config

    def generate_material(
        self,
        config: RoadMaterialConfig,
    ) -> Optional[Material]:
        """
        Generate a Blender material from configuration.

        Args:
            config: Road material configuration

        Returns:
            Created Blender material
        """
        if not BLENDER_AVAILABLE:
            return None

        # Check cache
        if config.name in self.materials:
            return self.materials[config.name]

        # Get surface preset
        surface_preset = ROAD_SURFACE_PRESETS.get(config.surface_type, {})

        # Create layered texture config
        texture_config = self._create_texture_config(config, surface_preset)

        # Generate material
        material = self.texture_manager.apply_to_material(
            texture_config,
            material_name=config.name
        )

        # Apply zone-specific effects
        if material:
            self._apply_zone_effects(material, config)

        # Apply weathering
        if material:
            weathered = self._create_weathered_config(config)
            self.sanctus_integration._apply_sanctus_weathering(material, weathered)

        self.materials[config.name] = material
        return material

    def _create_texture_config(
        self,
        config: RoadMaterialConfig,
        surface_preset: Dict[str, Any],
    ) -> LayeredTextureConfig:
        """Create layered texture configuration."""
        # Map surface type to texture layer type
        type_map = {
            RoadSurfaceType.ASPHALT_FRESH: TextureLayerType.ASPHALT,
            RoadSurfaceType.ASPHALT_WORN: TextureLayerType.ASPHALT,
            RoadSurfaceType.ASPHALT_DAMAGED: TextureLayerType.ASPHALT,
            RoadSurfaceType.CONCRETE_FRESH: TextureLayerType.CONCRETE,
            RoadSurfaceType.CONCRETE_AGED: TextureLayerType.CONCRETE,
            RoadSurfaceType.COBBLESTONE: TextureLayerType.COBBLESTONE,
            RoadSurfaceType.COBBLESTONE_WORN: TextureLayerType.COBBLESTONE,
            RoadSurfaceType.BRICK: TextureLayerType.BRICK,
            RoadSurfaceType.GRAVEL: TextureLayerType.GRAVEL,
            RoadSurfaceType.DIRT: TextureLayerType.DIRT,
        }

        base_type = type_map.get(config.surface_type, TextureLayerType.ASPHALT)

        # Create base config
        texture_config = self.texture_manager.create_config(config.name, base_type)

        # Apply surface preset
        if texture_config.layers:
            base = texture_config.layers[0]
            base.maps.procedural_color = surface_preset.get("base_color", (0.15, 0.15, 0.15))
            base.maps.procedural_roughness = surface_preset.get("roughness", 0.7)
            base.maps.procedural_scale = surface_preset.get("texture_scale", 2.0)

        # Add layers from preset
        for layer_name in surface_preset.get("layers", []):
            if layer_name == "dirt_light":
                self.texture_manager.add_overlay(
                    texture_config,
                    layer_type=TextureLayerType.DIRT,
                    blend_factor=0.25,
                    mask_type=MaskType.NOISE,
                    color=(0.35, 0.3, 0.25),
                )
            elif layer_name == "dirt_heavy":
                self.texture_manager.add_overlay(
                    texture_config,
                    layer_type=TextureLayerType.DIRT,
                    blend_factor=0.5,
                    mask_type=MaskType.GRUNGE,
                    color=(0.3, 0.25, 0.2),
                )
            elif layer_name == "edge_wear":
                self.texture_manager.add_overlay(
                    texture_config,
                    layer_type=TextureLayerType.GRAVEL,
                    blend_factor=0.2,
                    mask_type=MaskType.EDGE,
                    color=(0.4, 0.38, 0.35),
                )
            elif layer_name == "cracks":
                # Cracks would be a separate system
                pass
            elif layer_name == "patches":
                self.texture_manager.add_overlay(
                    texture_config,
                    layer_type=TextureLayerType.ASPHALT,
                    blend_factor=0.3,
                    mask_type=MaskType.VORONOI,
                    color=(0.1, 0.1, 0.1),
                )

        return texture_config

    def _create_weathered_config(self, config: RoadMaterialConfig) -> WeatheredGroundConfig:
        """Create weathered config from road config."""
        # Map enums
        type_map = {
            RoadSurfaceType.ASPHALT_FRESH: TextureLayerType.ASPHALT,
            RoadSurfaceType.ASPHALT_WORN: TextureLayerType.ASPHALT,
            RoadSurfaceType.ASPHALT_DAMAGED: TextureLayerType.ASPHALT,
            RoadSurfaceType.CONCRETE_FRESH: TextureLayerType.CONCRETE,
            RoadSurfaceType.CONCRETE_AGED: TextureLayerType.CONCRETE,
            RoadSurfaceType.COBBLESTONE: TextureLayerType.COBBLESTONE,
            RoadSurfaceType.COBBLESTONE_WORN: TextureLayerType.COBBLESTONE,
        }

        return WeatheredGroundConfig(
            name=config.name,
            base_type=type_map.get(config.surface_type, TextureLayerType.ASPHALT),
            weathering_level=config.weathering_level,
            environment=config.environment,
            wetness=config.wetness,
            dirt_amount=config.tire_marks * 0.5,
        )

    def _apply_zone_effects(self, material: Material, config: RoadMaterialConfig) -> None:
        """Apply zone-specific effects to material."""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find BSDF
        bsdf = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break

        if not bsdf:
            return

        # Apply tire marks
        if config.tire_marks > 0:
            # Darken slightly
            color = list(bsdf.inputs['Base Color'].default_value[:3])
            darken = config.tire_marks * 0.1
            new_color = (
                max(0, color[0] - darken),
                max(0, color[1] - darken),
                max(0, color[2] - darken),
            )
            bsdf.inputs['Base Color'].default_value = (*new_color, 1.0)

        # Apply oil stains
        if config.oil_stains > 0:
            # Increase roughness variation would need more complex setup
            pass

    def create_marking_material(
        self,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        wear: float = 0.3,
        name: str = "road_marking",
    ) -> Optional[Material]:
        """
        Create a road marking paint material.

        Args:
            color: Marking color (white/yellow/red)
            wear: Paint wear level (0-1)
            name: Material name

        Returns:
            Created marking material
        """
        if not BLENDER_AVAILABLE:
            return None

        if name in self.materials:
            return self.materials[name]

        material = bpy.data.materials.new(name=name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create node setup
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (400, 0)

        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.4 - wear * 0.2
        bsdf.inputs['Specular IOR Level'].default_value = 0.3

        # Add wear noise
        if wear > 0:
            tex_coord = nodes.new('ShaderNodeTexCoord')
            tex_coord.location = (-600, 0)

            mapping = nodes.new('ShaderNodeMapping')
            mapping.location = (-400, 0)
            mapping.inputs['Scale'].default_value = (20, 20, 1)

            noise = nodes.new('ShaderNodeTexNoise')
            noise.location = (-200, 0)
            noise.inputs['Scale'].default_value = 10
            noise.inputs['Detail'].default_value = 4

            math = nodes.new('ShaderNodeMath')
            math.location = (0, 200)
            math.operation = 'MULTIPLY'
            math.inputs[1].default_value = wear

            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
            links.new(noise.outputs['Fac'], math.inputs[0])
            links.new(math.outputs[0], bsdf.inputs['Roughness'])

        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        self.materials[name] = material
        return material

    def get_or_create_material(
        self,
        config: RoadMaterialConfig,
    ) -> Optional[Material]:
        """Get cached material or create new one."""
        if config.name in self.materials:
            return self.materials[config.name]
        return self.generate_material(config)


# =============================================================================
# ROAD NETWORK MATERIAL APPLICATION
# =============================================================================

def apply_materials_to_road_network(
    network: Any,
    manager: Optional[UrbanRoadMaterialManager] = None,
    base_surface: str = "asphalt_worn",
    weathering: str = "medium",
) -> Dict[str, Material]:
    """
    Apply materials to a road network.

    Args:
        network: Road network from lib.urban
        manager: Optional UrbanRoadMaterialManager
        base_surface: Base surface type
        weathering: Weathering level

    Returns:
        Dictionary of material names to materials
    """
    if not BLENDER_AVAILABLE:
        return {}

    if manager is None:
        manager = UrbanRoadMaterialManager()

    materials = {}

    # Create main road material
    main_config = manager.create_road_material(
        name=f"road_main_{base_surface}",
        surface=base_surface,
        zone="driving_lane",
        weathering=weathering,
    )
    materials["main"] = manager.get_or_create_material(main_config)

    # Create intersection material
    intersection_config = manager.create_road_material(
        name=f"road_intersection_{base_surface}",
        surface=base_surface,
        zone="intersection",
        weathering=weathering,
    )
    materials["intersection"] = manager.get_or_create_material(intersection_config)

    # Create shoulder material
    shoulder_config = manager.create_road_material(
        name=f"road_shoulder_{base_surface}",
        surface=base_surface,
        zone="shoulder",
        weathering=weathering,
    )
    materials["shoulder"] = manager.get_or_create_material(shoulder_config)

    # Create marking material
    materials["marking"] = manager.create_marking_material(
        color=(1.0, 1.0, 1.0),
        wear=0.3,
        name="road_marking_white",
    )

    return materials


def create_road_surface_material(
    surface_type: str = "asphalt_worn",
    zone: str = "driving_lane",
    weathering: str = "medium",
    name: Optional[str] = None,
) -> Optional[Material]:
    """
    Convenience function to create a road surface material.

    Args:
        surface_type: Surface type string
        zone: Zone type string
        weathering: Weathering level string
        name: Optional material name

    Returns:
        Created Blender material
    """
    manager = UrbanRoadMaterialManager()
    config_name = name or f"road_{surface_type}_{zone}"
    config = manager.create_road_material(
        name=config_name,
        surface=surface_type,
        zone=zone,
        weathering=weathering,
    )
    return manager.generate_material(config)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RoadSurfaceType",
    "RoadZoneType",
    # Dataclasses
    "RoadMaterialConfig",
    # Manager
    "UrbanRoadMaterialManager",
    # Presets
    "ROAD_SURFACE_PRESETS",
    "ZONE_CONFIGS",
    # Functions
    "create_road_surface_material",
    "apply_materials_to_road_network",
]
