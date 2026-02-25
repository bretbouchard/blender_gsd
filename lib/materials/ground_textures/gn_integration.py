"""
Geometry Nodes Integration for Ground Textures

Provides integration between the ground_textures layered texture system
and Blender's Geometry Nodes for procedural geometry workflows.

Architecture:
- LayeredTextureConfig → GN-compatible format
- Material slot assignment for road zones
- UV/attribute-based texture sampling
- Node group generation for mask types

Usage:
    from lib.materials.ground_textures import (
        GNTextureIntegrator,
        GNOutputFormat,
        MaterialSlotConfig,
        convert_to_gn_format,
    )

    # Convert texture config to GN format
    config = create_asphalt_with_dirt()
    gn_format = convert_to_gn_format(config)

    # Create material slots for road zones
    integrator = GNTextureIntegrator()
    slots = integrator.create_material_slots(config, zones=["driving_lane", "shoulder"])
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

from .texture_layers import (
    TextureLayerType,
    BlendMode,
    MaskType,
    TextureMaps,
    TextureLayer,
    LayeredTextureConfig,
    LayeredTextureManager,
)

try:
    import bpy
    from bpy.types import Material, NodeTree, GeometryNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    NodeTree = Any
    GeometryNodeTree = Any


# =============================================================================
# GN OUTPUT FORMAT SPECIFICATION
# =============================================================================

class GNSamplingStrategy(Enum):
    """How textures are sampled within Geometry Nodes."""
    IMAGE_TEXTURE = "image_texture"      # Pre-baked textures via ShaderNodeTexImage
    PROCEDURAL = "procedural"            # Procedural nodes within GN tree
    HYBRID = "hybrid"                    # Baked base + procedural variations


class GNMaterialAssignment(Enum):
    """How materials are assigned to geometry."""
    SINGLE_MATERIAL = "single"           # One material for entire mesh
    MATERIAL_SLOT = "slot"               # Multiple slots via Set Material node
    VERTEX_COLOR = "vertex_color"        # Blend via vertex colors
    ATTRIBUTE = "attribute"              # Blend via named attribute


@dataclass
class GNMaskNodeGroup:
    """
    Specification for a mask node group within GN.

    Defines how a MaskType is converted to GN nodes.
    """
    mask_type: MaskType
    node_group_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=lambda: {"Mask": "Float"})

    # Node definitions
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mask_type": self.mask_type.value,
            "node_group_name": self.node_group_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "nodes": self.nodes,
            "links": self.links,
        }


@dataclass
class GNLayerConfig:
    """
    GN-compatible layer configuration.

    Defines a single texture layer for GN consumption.
    """
    layer_type: TextureLayerType
    layer_name: str
    blend_mode: BlendMode
    blend_factor: float

    # Texture sampling
    sampling_strategy: GNSamplingStrategy = GNSamplingStrategy.HYBRID
    texture_paths: Dict[str, Optional[str]] = field(default_factory=dict)
    procedural_params: Dict[str, Any] = field(default_factory=dict)

    # Mask configuration
    mask_config: Optional[GNMaskNodeGroup] = None

    # Transform
    uv_scale: Tuple[float, float] = (1.0, 1.0)
    uv_rotation: float = 0.0
    uv_offset: Tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "layer_type": self.layer_type.value,
            "layer_name": self.layer_name,
            "blend_mode": self.blend_mode.value,
            "blend_factor": self.blend_factor,
            "sampling_strategy": self.sampling_strategy.value,
            "texture_paths": self.texture_paths,
            "procedural_params": self.procedural_params,
            "mask_config": self.mask_config.to_dict() if self.mask_config else None,
            "uv_scale": list(self.uv_scale),
            "uv_rotation": self.uv_rotation,
            "uv_offset": list(self.uv_offset),
        }


@dataclass
class MaterialSlotConfig:
    """
    Configuration for a material slot in GN.

    Used for multi-zone materials (e.g., road with driving lane, shoulder, crosswalk).
    """
    slot_name: str
    slot_index: int
    material_name: str
    zone_type: str  # driving_lane, shoulder, crosswalk, etc.
    selection_attribute: Optional[str] = None  # Attribute to select faces for this slot

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "slot_name": self.slot_name,
            "slot_index": self.slot_index,
            "material_name": self.material_name,
            "zone_type": self.zone_type,
            "selection_attribute": self.selection_attribute,
        }


@dataclass
class GNOutputFormat:
    """
    Complete GN-compatible output format.

    This is the main output from convert_to_gn_format().
    Contains everything needed to create GN nodes.
    """
    # Identification
    config_name: str
    node_tree_name: str

    # Input configuration
    inputs: Dict[str, Any] = field(default_factory=lambda: {
        "uv_attribute": "uv_map",
        "vertex_colors": None,
        "random_seed": 0,
    })

    # Layer configuration
    layers: List[GNLayerConfig] = field(default_factory=list)

    # Material assignment
    material_assignment: GNMaterialAssignment = GNMaterialAssignment.SINGLE_MATERIAL
    material_slots: List[MaterialSlotConfig] = field(default_factory=list)

    # Output configuration
    output_material_name: str = ""

    # Node group references (created during conversion)
    mask_node_groups: Dict[str, GNMaskNodeGroup] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "config_name": self.config_name,
            "node_tree_name": self.node_tree_name,
            "inputs": self.inputs,
            "layers": [layer.to_dict() for layer in self.layers],
            "material_assignment": self.material_assignment.value,
            "material_slots": [slot.to_dict() for slot in self.material_slots],
            "output_material_name": self.output_material_name,
            "mask_node_groups": {
                k: v.to_dict() for k, v in self.mask_node_groups.items()
            },
        }

    def to_json(self, filepath: str) -> None:
        """Save to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# =============================================================================
# UV STORAGE VALIDATION
# =============================================================================

@dataclass
class UVStorageSpec:
    """Specification for UV attribute storage."""
    uv_attribute_name: str
    domain: str = 'CORNER'  # Must be CORNER for UVs
    data_type: str = 'FLOAT_VECTOR'
    is_stored: bool = False
    store_node_name: str = ""


def validate_uv_storage(
    gn_output: GNOutputFormat,
    node_tree: Optional[GeometryNodeTree] = None,
) -> List[str]:
    """
    Validate that UV attribute is properly stored before use.

    Checks that:
    1. UV attribute name is specified
    2. If node_tree provided, verifies Store Named Attribute exists
    3. Domain is CORNER (Face Corner) for proper UV interpolation

    Args:
        gn_output: GN output format to validate
        node_tree: Optional node tree to check for actual storage

    Returns:
        List of validation warnings/errors
    """
    warnings = []
    uv_attr = gn_output.inputs.get("uv_attribute", "")

    if not uv_attr:
        warnings.append("No UV attribute name specified in inputs")
        return warnings

    if node_tree and BLENDER_AVAILABLE:
        # Check for Store Named Attribute node with UV name
        found_store = False
        for node in node_tree.nodes:
            if node.type == 'GeometryNodeStoreNamedAttribute':
                if node.inputs["Name"].default_value == uv_attr:
                    found_store = True
                    # Check domain
                    if node.domain != 'CORNER':
                        warnings.append(
                            f"UV storage node domain is {node.domain}, "
                            f"should be 'CORNER' for proper UV interpolation"
                        )

        if not found_store:
            warnings.append(
                f"No 'Store Named Attribute' node found for UV attribute '{uv_attr}'. "
                f"Use FieldOperations.store_uv_for_shader() before texture sampling."
            )

    return warnings


def create_uv_storage_node_spec(
    uv_attribute_name: str = "uv_map",
    plane: str = "XZ",
    scale: tuple[float, float] = (1.0, 1.0),
    offset: tuple[float, float] = (0.0, 0.0),
) -> Dict[str, Any]:
    """
    Create node specification for UV storage from position.

    Generates a dictionary specification that can be used to create
    nodes for storing UV coordinates derived from position.

    Args:
        uv_attribute_name: Name for the UV attribute
        plane: Which position axes to use ("XZ", "XY", "YZ")
        scale: UV scale factors
        offset: UV offset values

    Returns:
        Dictionary with nodes and links for UV storage
    """
    # Determine axis indices
    axis_map = {"X": 0, "Y": 1, "Z": 2}
    u_axis = axis_map[plane[0]]
    v_axis = axis_map[plane[1]]

    return {
        "uv_attribute_name": uv_attribute_name,
        "nodes": [
            {"type": "GeometryNodeInputPosition", "name": "get_position"},
            {"type": "ShaderNodeSeparateXYZ", "name": "separate_pos"},
            {"type": "ShaderNodeMath", "name": "scale_u", "operation": "MULTIPLY"},
            {"type": "ShaderNodeMath", "name": "offset_u", "operation": "ADD"},
            {"type": "ShaderNodeMath", "name": "scale_v", "operation": "MULTIPLY"},
            {"type": "ShaderNodeMath", "name": "offset_v", "operation": "ADD"},
            {"type": "ShaderNodeCombineXYZ", "name": "combine_uv"},
            {"type": "GeometryNodeStoreNamedAttribute", "name": "store_uv",
             "domain": "CORNER", "data_type": "FLOAT_VECTOR",
             "attribute_name": uv_attribute_name},
        ],
        "links": [
            {"from": "get_position", "from_socket": "Position",
             "to": "separate_pos", "to_socket": "Vector"},
            # Scale U
            {"from": "separate_pos", "from_socket": list(axis_map.keys())[u_axis],
             "to": "scale_u", "to_socket": "Value"},
            # Offset U
            {"from": "scale_u", "from_socket": "Value",
             "to": "offset_u", "to_socket": "Value"},
            # Scale V
            {"from": "separate_pos", "from_socket": list(axis_map.keys())[v_axis],
             "to": "scale_v", "to_socket": "Value"},
            # Offset V
            {"from": "scale_v", "from_socket": "Value",
             "to": "offset_v", "to_socket": "Value"},
            # Combine UV
            {"from": "offset_u", "from_socket": "Value",
             "to": "combine_uv", "to_socket": "X"},
            {"from": "offset_v", "from_socket": "Value",
             "to": "combine_uv", "to_socket": "Y"},
            # Store UV
            {"from": "combine_uv", "from_socket": "Vector",
             "to": "store_uv", "to_socket": "Value"},
        ],
        "defaults": {
            "scale_u": {"input_index": 1, "value": scale[0]},
            "offset_u": {"input_index": 1, "value": offset[0]},
            "scale_v": {"input_index": 1, "value": scale[1]},
            "offset_v": {"input_index": 1, "value": offset[1]},
        },
    }


# =============================================================================
# MASK NODE GROUP GENERATORS
# =============================================================================

def _create_noise_mask_group(scale: float = 5.0, detail: int = 4) -> GNMaskNodeGroup:
    """Create node group specification for noise mask."""
    return GNMaskNodeGroup(
        mask_type=MaskType.NOISE,
        node_group_name="GN_Mask_Noise",
        inputs={
            "Scale": ("Float", scale),
            "Detail": ("Integer", detail),
            "Distortion": ("Float", 0.5),
            "Seed": ("Integer", 0),
        },
        nodes=[
            {"type": "GeometryNodeInputNamedAttribute", "name": "uv_input",
             "attribute_name": "uv_map", "data_type": "FLOAT_VECTOR"},
            {"type": "ShaderNodeTexNoise", "name": "noise_texture"},
            {"type": "ShaderNodeMapRange", "name": "contrast_adjust"},
        ],
        links=[
            {"from": "uv_input", "from_socket": "Attribute", "to": "noise_texture", "to_socket": "Vector"},
            {"from": "noise_texture", "from_socket": "Fac", "to": "contrast_adjust", "to_socket": "Value"},
        ],
    )


def _create_voronoi_mask_group(scale: float = 10.0, randomness: float = 0.8) -> GNMaskNodeGroup:
    """Create node group specification for voronoi mask."""
    return GNMaskNodeGroup(
        mask_type=MaskType.VORONOI,
        node_group_name="GN_Mask_Voronoi",
        inputs={
            "Scale": ("Float", scale),
            "Randomness": ("Float", randomness),
            "Seed": ("Integer", 0),
        },
        nodes=[
            {"type": "GeometryNodeInputNamedAttribute", "name": "uv_input"},
            {"type": "ShaderNodeTexVoronoi", "name": "voronoi_texture"},
        ],
        links=[
            {"from": "uv_input", "from_socket": "Attribute", "to": "voronoi_texture", "to_socket": "Vector"},
        ],
    )


def _create_grunge_mask_group(
    scale: float = 5.0,
    intensity: float = 0.3,
    power: float = 1.5,
) -> GNMaskNodeGroup:
    """Create node group specification for grunge mask."""
    return GNMaskNodeGroup(
        mask_type=MaskType.GRUNGE,
        node_group_name="GN_Mask_Grunge",
        inputs={
            "Scale_1": ("Float", scale),
            "Scale_2": ("Float", scale * 3),
            "Intensity": ("Float", intensity),
            "Power": ("Float", power),
            "Seed": ("Integer", 0),
        },
        nodes=[
            {"type": "GeometryNodeInputNamedAttribute", "name": "uv_input"},
            {"type": "ShaderNodeTexNoise", "name": "grunge_noise1"},
            {"type": "ShaderNodeTexNoise", "name": "grunge_noise2"},
            {"type": "ShaderNodeMixRGB", "name": "grunge_mix", "blend_type": "MULTIPLY"},
            {"type": "ShaderNodeMath", "name": "grunge_power", "operation": "POWER"},
        ],
        links=[
            {"from": "uv_input", "from_socket": "Attribute", "to": "grunge_noise1", "to_socket": "Vector"},
            {"from": "uv_input", "from_socket": "Attribute", "to": "grunge_noise2", "to_socket": "Vector"},
            {"from": "grunge_noise1", "from_socket": "Fac", "to": "grunge_mix", "to_socket": "Color1"},
            {"from": "grunge_noise2", "from_socket": "Fac", "to": "grunge_mix", "to_socket": "Color2"},
            {"from": "grunge_mix", "from_socket": "Color", "to": "grunge_power", "to_socket": "Value"},
        ],
    )


def _create_edge_wear_mask_group(edge_width: float = 0.1, chaos: float = 0.3) -> GNMaskNodeGroup:
    """Create node group specification for edge wear mask."""
    return GNMaskNodeGroup(
        mask_type=MaskType.EDGE,
        node_group_name="GN_Mask_EdgeWear",
        inputs={
            "EdgeWidth": ("Float", edge_width),
            "Chaos": ("Float", chaos),
            "Seed": ("Integer", 0),
        },
        nodes=[
            {"type": "GeometryNodeInputNamedAttribute", "name": "uv_input"},
            {"type": "GeometryNodeInputMeshEdgeAngle", "name": "edge_angle"},
            {"type": "ShaderNodeMath", "name": "edge_strength", "operation": "ABSOLUTE"},
            {"type": "ShaderNodeMapRange", "name": "edge_falloff"},
        ],
        links=[
            {"from": "edge_angle", "from_socket": "Unsigned Angle", "to": "edge_strength", "to_socket": "Value"},
        ],
    )


# Mask type to generator mapping
_MASK_GENERATORS = {
    MaskType.NOISE: _create_noise_mask_group,
    MaskType.VORONOI: _create_voronoi_mask_group,
    MaskType.GRUNGE: _create_grunge_mask_group,
    MaskType.EDGE: _create_edge_wear_mask_group,
}


# =============================================================================
# MAIN CONVERSION FUNCTION
# =============================================================================

def convert_to_gn_format(
    config: LayeredTextureConfig,
    sampling_strategy: GNSamplingStrategy = GNSamplingStrategy.HYBRID,
    material_assignment: GNMaterialAssignment = GNMaterialAssignment.SINGLE_MATERIAL,
    uv_attribute: str = "uv_map",
) -> GNOutputFormat:
    """
    Convert a LayeredTextureConfig to GN-compatible format.

    This is the main conversion function that produces a complete
    specification for creating Geometry Nodes.

    Args:
        config: Source LayeredTextureConfig
        sampling_strategy: How textures should be sampled
        material_assignment: How materials are assigned to geometry
        uv_attribute: Name of UV attribute to use

    Returns:
        GNOutputFormat ready for GN node creation

    Example:
        config = create_asphalt_with_dirt()
        gn_format = convert_to_gn_format(config)

        # gn_format contains everything needed to create GN nodes
        print(gn_format.to_dict())
    """
    # Create output format
    output = GNOutputFormat(
        config_name=config.name,
        node_tree_name=f"GN_{config.name}",
        inputs={
            "uv_attribute": uv_attribute,
            "vertex_colors": None,
            "random_seed": 0,
        },
        material_assignment=material_assignment,
        output_material_name=f"Mat_{config.name}",
    )

    # Convert each layer
    for i, layer in enumerate(config.layers):
        # Create mask config if present
        mask_config = None
        if layer.mask_type != MaskType.PAINTED:  # Painted requires external texture
            generator = _MASK_GENERATORS.get(layer.mask_type)
            if generator:
                mask_config = generator(
                    scale=layer.mask_scale,
                )
                # Store in mask groups
                group_key = f"{layer.mask_type.value}_{i}"
                output.mask_node_groups[group_key] = mask_config

        # Create layer config
        gn_layer = GNLayerConfig(
            layer_type=layer.layer_type,
            layer_name=layer.name,
            blend_mode=layer.blend_mode,
            blend_factor=layer.blend_factor,
            sampling_strategy=sampling_strategy,
            texture_paths={
                "base_color": layer.maps.base_color,
                "roughness": layer.maps.roughness,
                "normal": layer.maps.normal,
            },
            procedural_params={
                "color": layer.maps.procedural_color,
                "roughness": layer.maps.procedural_roughness,
                "scale": layer.maps.procedural_scale,
            },
            mask_config=mask_config,
            uv_scale=(layer.uv_scale, layer.uv_scale),
            uv_rotation=layer.uv_rotation,
            uv_offset=layer.uv_offset,
        )

        output.layers.append(gn_layer)

    return output


# =============================================================================
# GN INTEGRATOR CLASS
# =============================================================================

class GNTextureIntegrator:
    """
    Integrates ground textures with Geometry Nodes.

    Provides:
    - Conversion from LayeredTextureConfig to GN format
    - Material slot creation for multi-zone geometry
    - Node tree generation
    """

    def __init__(self):
        """Initialize the integrator."""
        self.output_formats: Dict[str, GNOutputFormat] = {}
        self.material_slots: Dict[str, List[MaterialSlotConfig]] = {}

    def convert_config(
        self,
        config: LayeredTextureConfig,
        sampling_strategy: GNSamplingStrategy = GNSamplingStrategy.HYBRID,
    ) -> GNOutputFormat:
        """
        Convert a texture config to GN format.

        Args:
            config: Source configuration
            sampling_strategy: Texture sampling approach

        Returns:
            GNOutputFormat specification
        """
        output = convert_to_gn_format(config, sampling_strategy)
        self.output_formats[config.name] = output
        return output

    def create_material_slots(
        self,
        config: LayeredTextureConfig,
        zones: List[str],
        base_material_name: Optional[str] = None,
    ) -> List[MaterialSlotConfig]:
        """
        Create material slot configurations for road zones.

        Args:
            config: Texture configuration
            zones: List of zone types (driving_lane, shoulder, etc.)
            base_material_name: Base name for materials

        Returns:
            List of MaterialSlotConfig
        """
        base_name = base_material_name or f"Mat_{config.name}"
        slots = []

        for i, zone in enumerate(zones):
            slot = MaterialSlotConfig(
                slot_name=f"{zone}_slot",
                slot_index=i,
                material_name=f"{base_name}_{zone}",
                zone_type=zone,
                selection_attribute=f"zone_{zone}",
            )
            slots.append(slot)

        self.material_slots[config.name] = slots
        return slots

    def create_gn_node_tree(
        self,
        output_format: GNOutputFormat,
    ) -> Optional[GeometryNodeTree]:
        """
        Create a Blender Geometry Node tree from the output format.

        Args:
            output_format: GN output specification

        Returns:
            Created GeometryNodeTree or None if Blender not available
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create new node tree
        node_tree = bpy.data.node_groups.new(
            output_format.node_tree_name,
            type='GeometryNodeTree'
        )

        # Add inputs
        for input_name, input_spec in output_format.inputs.items():
            if isinstance(input_spec, tuple):
                socket_type, default = input_spec
                node_tree.interface.new_socket(
                    name=input_name,
                    in_out='INPUT',
                    socket_type=socket_type,
                )
            else:
                node_tree.interface.new_socket(
                    name=input_name,
                    in_out='INPUT',
                )

        # Add output
        node_tree.interface.new_socket(
            name="Material",
            in_out='OUTPUT',
        )

        return node_tree

    def export_to_json(
        self,
        output_format: GNOutputFormat,
        filepath: str,
    ) -> None:
        """
        Export GN format to JSON file.

        Args:
            output_format: Format to export
            filepath: Output file path
        """
        output_format.to_json(filepath)


# =============================================================================
# ROAD ZONE MATERIAL PRESETS
# =============================================================================

ROAD_ZONE_PRESETS = {
    "driving_lane": {
        "tire_marks": 0.3,
        "oil_stains": 0.1,
        "wear_pattern": "center",
    },
    "shoulder": {
        "tire_marks": 0.1,
        "dirt_amount": 0.5,
        "wear_pattern": "edges",
    },
    "crosswalk": {
        "has_markings": True,
        "marking_wear": 0.3,
        "tire_marks": 0.2,
    },
    "intersection": {
        "tire_marks": 0.4,
        "oil_stains": 0.2,
        "wear_pattern": "corners",
    },
}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_road_gn_config(
    base_type: str = "asphalt",
    zones: List[str] = None,
    wear_level: str = "medium",
) -> GNOutputFormat:
    """
    Create a complete GN configuration for a road.

    Args:
        base_type: Surface type (asphalt, concrete, cobblestone)
        zones: Road zones to create materials for
        wear_level: Overall wear level

    Returns:
        GNOutputFormat ready for node creation
    """
    from .texture_layers import create_road_material

    zones = zones or ["driving_lane", "shoulder"]

    # Create base texture config
    texture_config = create_road_material(
        surface_type=base_type,
        wear_level=wear_level,
    )

    # Convert to GN format
    integrator = GNTextureIntegrator()
    gn_format = integrator.convert_config(texture_config)

    # Add material slots
    integrator.create_material_slots(texture_config, zones)

    return gn_format


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "GNSamplingStrategy",
    "GNMaterialAssignment",
    # Dataclasses
    "GNMaskNodeGroup",
    "GNLayerConfig",
    "MaterialSlotConfig",
    "GNOutputFormat",
    "UVStorageSpec",
    # Functions
    "convert_to_gn_format",
    "create_road_gn_config",
    "validate_uv_storage",
    "create_uv_storage_node_spec",
    # Classes
    "GNTextureIntegrator",
    # Presets
    "ROAD_ZONE_PRESETS",
]
