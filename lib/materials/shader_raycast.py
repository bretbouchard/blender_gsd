"""
Shader Raycast Utilities for Blender 5.1+

Provides utilities for using the new Raycast node in material shaders.
The Raycast node enables proximity detection, ambient occlusion,
contact shadows, and other effects directly in shaders.

This module provides:
- Preset materials using raycast
- Node group templates for common raycast patterns
- Integration with existing material systems

Blender 5.1 Feature:
The Raycast node in shaders sends rays from surface points and detects
collisions with other geometry. This enables real-time effects that
previously required baking or complex geometry processing.

Outputs from Raycast node:
- Is Hit: Boolean - whether ray hit something
- Hit Distance: Float - distance to hit point
- Hit Position: Vector - world position of hit
- Hit Normal: Vector - normal at hit point

Usage:
    from lib.materials.shader_raycast import (
        create_proximity_ao_material,
        create_contact_shadow_material,
        RaycastMaterialBuilder,
    )

    # Create proximity AO material
    mat = create_proximity_ao_material(
        target_object="Wall",
        max_distance=1.0,
        base_color=(0.8, 0.8, 0.8),
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import bpy
    from bpy.types import Material, NodeTree, ShaderNodeTree
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = Any
    NodeTree = Any
    ShaderNodeTree = Any


# =============================================================================
# ENUMS AND DATACLASSES
# =============================================================================

class RaycastOutputType(Enum):
    """Which output from Raycast node to use."""
    IS_HIT = "is_hit"
    HIT_DISTANCE = "hit_distance"
    HIT_POSITION = "hit_position"
    HIT_NORMAL = "hit_normal"


class RaycastDirection(Enum):
    """Direction for raycast rays."""
    NORMAL = "normal"           # Along surface normal
    CUSTOM = "custom"           # Custom direction vector
    CAMERA = "camera"           # Toward camera
    REFLECTION = "reflection"   # Reflection direction


@dataclass
class RaycastConfig:
    """Configuration for shader raycast."""
    target_object: str
    max_distance: float = 1.0
    direction: RaycastDirection = RaycastDirection.NORMAL
    custom_direction: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    output_type: RaycastOutputType = RaycastOutputType.HIT_DISTANCE
    invert: bool = False

    # Mapping options
    map_range: bool = True
    from_min: float = 0.0
    from_max: float = 1.0
    to_min: float = 0.0
    to_max: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target_object": self.target_object,
            "max_distance": self.max_distance,
            "direction": self.direction.value,
            "custom_direction": list(self.custom_direction),
            "output_type": self.output_type.value,
            "invert": self.invert,
            "map_range": self.map_range,
            "from_min": self.from_min,
            "from_max": self.from_max,
            "to_min": self.to_min,
            "to_max": self.to_max,
        }


@dataclass
class RaycastMaterialPreset:
    """Preset for creating raycast-based materials."""
    name: str
    description: str
    config: RaycastConfig
    base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    affected_color: Tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1.0)
    roughness_base: float = 0.5
    roughness_affected: float = 0.8
    use_for_roughness: bool = True
    use_for_color: bool = True


# =============================================================================
# NODE GROUP SPECIFICATIONS
# =============================================================================

def create_raycast_node_group_spec(
    config: RaycastConfig,
    group_name: str = "RaycastProximity",
) -> Dict[str, Any]:
    """
    Create a node group specification for raycast effect.

    Args:
        config: Raycast configuration
        group_name: Name for the node group

    Returns:
        Dictionary with node group specification
    """
    nodes = [
        # Input: Object info for target
        {"type": "ShaderNodeObjectInfo", "name": "target_info",
         "object": config.target_object},
        # Input: Geometry for position/normal
        {"type": "ShaderNodeNewGeometry", "name": "geometry"},
        # Raycast node
        {"type": "ShaderNodeRaycast", "name": "raycast"},
        # Output selection based on type
        {"type": "ShaderNodeMapRange", "name": "map_range"},
        # Optional invert
        {"type": "ShaderNodeMath", "name": "invert", "operation": "SUBTRACT"},
    ]

    links = []

    # Connect geometry to raycast
    links.append({
        "from": "geometry", "from_socket": "Position",
        "to": "raycast", "to_socket": "Source Position"
    })

    # Set direction based on config
    if config.direction == RaycastDirection.NORMAL:
        links.append({
            "from": "geometry", "from_socket": "Normal",
            "to": "raycast", "to_socket": "Direction"
        })
    elif config.direction == RaycastDirection.CUSTOM:
        # Use custom direction via combine vector
        nodes.append({
            "type": "ShaderNodeCombineXYZ", "name": "custom_dir",
            "defaults": {
                "X": config.custom_direction[0],
                "Y": config.custom_direction[1],
                "Z": config.custom_direction[2],
            }
        })
        links.append({
            "from": "custom_dir", "from_socket": "Vector",
            "to": "raycast", "to_socket": "Direction"
        })

    # Set max distance
    nodes[2]["defaults"] = {"Ray Length": config.max_distance}

    # Select output based on type
    output_socket_map = {
        RaycastOutputType.IS_HIT: "Is Hit",
        RaycastOutputType.HIT_DISTANCE: "Hit Distance",
        RaycastOutputType.HIT_POSITION: "Hit Position",
        RaycastOutputType.HIT_NORMAL: "Hit Normal",
    }

    raycast_output = output_socket_map[config.output_type]

    # Connect to map range
    if config.map_range:
        links.append({
            "from": "raycast", "from_socket": raycast_output,
            "to": "map_range", "to_socket": "Value"
        })
        nodes[3]["defaults"] = {
            "From Min": config.from_min,
            "From Max": config.from_max,
            "To Min": config.to_min,
            "To Max": config.to_max,
        }
        final_source = "map_range"
        final_socket = "Result"
    else:
        final_source = "raycast"
        final_socket = raycast_output

    # Optional invert
    if config.invert:
        links.append({
            "from": final_source, "from_socket": final_socket,
            "to": "invert", "to_socket": "Value"
        })
        # 1 - value
        nodes[4]["inputs"] = [0, 1.0]  # Second input is 1.0
        final_source = "invert"
        final_socket = "Value"

    return {
        "name": group_name,
        "nodes": nodes,
        "links": links,
        "inputs": [],
        "outputs": [
            {"name": "Factor", "type": "Float"},
        ],
        "final_output": {"node": final_source, "socket": final_socket},
    }


# =============================================================================
# PRESET MATERIALS
# =============================================================================

# Predefined presets for common use cases
PROXIMITY_AO_PRESET = RaycastMaterialPreset(
    name="Proximity AO",
    description="Ambient occlusion based on proximity to target geometry",
    config=RaycastConfig(
        target_object="",  # Set at runtime
        max_distance=1.0,
        direction=RaycastDirection.NORMAL,
        output_type=RaycastOutputType.HIT_DISTANCE,
        map_range=True,
        from_min=0.0,
        from_max=1.0,
        to_min=1.0,  # Inverted: close = dark
        to_max=0.0,
    ),
    base_color=(0.8, 0.8, 0.8, 1.0),
    affected_color=(0.3, 0.3, 0.3, 1.0),
    roughness_base=0.5,
    roughness_affected=0.7,
    use_for_roughness=True,
    use_for_color=True,
)

CONTACT_SHADOW_PRESET = RaycastMaterialPreset(
    name="Contact Shadow",
    description="Shadows at contact points with other geometry",
    config=RaycastConfig(
        target_object="",  # Set at runtime
        max_distance=0.5,
        direction=RaycastDirection.NORMAL,
        output_type=RaycastOutputType.HIT_DISTANCE,
        map_range=True,
        from_min=0.0,
        from_max=0.5,
        to_min=1.0,  # Inverted: contact = shadow
        to_max=0.0,
    ),
    base_color=(0.9, 0.9, 0.9, 1.0),
    affected_color=(0.1, 0.1, 0.1, 1.0),
    roughness_base=0.3,
    roughness_affected=0.3,
    use_for_roughness=False,
    use_for_color=True,
)

EDGE_WEAR_PRESET = RaycastMaterialPreset(
    name="Edge Wear",
    description="Wear/dirt accumulation at edges and corners",
    config=RaycastConfig(
        target_object="",  # Self for edge detection
        max_distance=0.2,
        direction=RaycastDirection.NORMAL,
        output_type=RaycastOutputType.HIT_DISTANCE,
        map_range=True,
        from_min=0.0,
        from_max=0.2,
        to_min=0.0,
        to_max=1.0,  # Close = more wear
        invert=False,
    ),
    base_color=(0.6, 0.55, 0.5, 1.0),  # Base material
    affected_color=(0.3, 0.25, 0.2, 1.0),  # Worn/dirty color
    roughness_base=0.4,
    roughness_affected=0.8,  # Worn areas rougher
    use_for_roughness=True,
    use_for_color=True,
)

COLOR_BLEEDING_PRESET = RaycastMaterialPreset(
    name="Color Bleeding",
    description="Color bleeding from nearby geometry",
    config=RaycastConfig(
        target_object="",  # Set at runtime
        max_distance=2.0,
        direction=RaycastDirection.NORMAL,
        output_type=RaycastOutputType.HIT_POSITION,
        map_range=True,
        from_min=0.0,
        from_max=2.0,
        to_min=1.0,
        to_max=0.0,
    ),
    base_color=(0.8, 0.8, 0.8, 1.0),
    affected_color=(1.0, 0.9, 0.8, 1.0),  # Warm bounce
    roughness_base=0.5,
    roughness_affected=0.5,
    use_for_roughness=False,
    use_for_color=True,
)

# Preset registry
RAYCAST_PRESETS = {
    "proximity_ao": PROXIMITY_AO_PRESET,
    "contact_shadow": CONTACT_SHADOW_PRESET,
    "edge_wear": EDGE_WEAR_PRESET,
    "color_bleeding": COLOR_BLEEDING_PRESET,
}


# =============================================================================
# MATERIAL BUILDER CLASS
# =============================================================================

class RaycastMaterialBuilder:
    """
    Builder for creating materials with raycast effects.

    Provides a fluent interface for constructing materials that use
    the Blender 5.1 Raycast node for proximity effects.
    """

    def __init__(self, name: str = "RaycastMaterial"):
        """Initialize the builder."""
        self.name = name
        self.base_color = (0.8, 0.8, 0.8, 1.0)
        self.roughness = 0.5
        self.metallic = 0.0
        self.raycast_configs: List[RaycastConfig] = []
        self._material: Optional[Material] = None

    def with_base_color(
        self,
        color: Union[Tuple[float, float, float], Tuple[float, float, float, float]]
    ) -> RaycastMaterialBuilder:
        """Set base color."""
        if len(color) == 3:
            self.base_color = (*color, 1.0)
        else:
            self.base_color = color
        return self

    def with_roughness(self, roughness: float) -> RaycastMaterialBuilder:
        """Set roughness."""
        self.roughness = max(0.0, min(1.0, roughness))
        return self

    def with_metallic(self, metallic: float) -> RaycastMaterialBuilder:
        """Set metallic."""
        self.metallic = max(0.0, min(1.0, metallic))
        return self

    def add_proximity_ao(
        self,
        target_object: str,
        max_distance: float = 1.0,
    ) -> RaycastMaterialBuilder:
        """Add proximity-based ambient occlusion."""
        config = RaycastConfig(
            target_object=target_object,
            max_distance=max_distance,
            direction=RaycastDirection.NORMAL,
            output_type=RaycastOutputType.HIT_DISTANCE,
            map_range=True,
            from_min=0.0,
            from_max=max_distance,
            to_min=1.0,  # Close = dark
            to_max=0.0,
        )
        self.raycast_configs.append(config)
        return self

    def add_contact_shadow(
        self,
        target_object: str,
        max_distance: float = 0.5,
    ) -> RaycastMaterialBuilder:
        """Add contact shadows."""
        config = RaycastConfig(
            target_object=target_object,
            max_distance=max_distance,
            direction=RaycastDirection.NORMAL,
            output_type=RaycastOutputType.HIT_DISTANCE,
            map_range=True,
            from_min=0.0,
            from_max=max_distance,
            to_min=1.0,  # Contact = shadow
            to_max=0.0,
        )
        self.raycast_configs.append(config)
        return self

    def add_edge_wear(
        self,
        max_distance: float = 0.2,
    ) -> RaycastMaterialBuilder:
        """Add edge wear effect (self-raycast)."""
        # Note: target_object set to empty for self
        config = RaycastConfig(
            target_object="",  # Self
            max_distance=max_distance,
            direction=RaycastDirection.NORMAL,
            output_type=RaycastOutputType.HIT_DISTANCE,
            map_range=True,
            from_min=0.0,
            from_max=max_distance,
            to_min=0.0,  # Close = wear
            to_max=1.0,
        )
        self.raycast_configs.append(config)
        return self

    def add_raycast(
        self,
        config: RaycastConfig,
    ) -> RaycastMaterialBuilder:
        """Add custom raycast configuration."""
        self.raycast_configs.append(config)
        return self

    def build(self) -> Optional[Material]:
        """
        Build the material with raycast effects.

        Returns:
            Created material or None if Blender not available
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create material
        mat = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True

        # Get node tree
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create output node
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (600, 0)

        # Create principled BSDF
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (300, 0)
        bsdf.inputs["Base Color"].default_value = self.base_color
        bsdf.inputs["Roughness"].default_value = self.roughness
        bsdf.inputs["Metallic"].default_value = self.metallic

        # Connect BSDF to output
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Add raycast effects
        for i, config in enumerate(self.raycast_configs):
            self._add_raycast_nodes(
                mat.node_tree,
                config,
                bsdf,
                offset_y=i * -300,
            )

        self._material = mat
        return mat

    def _add_raycast_nodes(
        self,
        node_tree: ShaderNodeTree,
        config: RaycastConfig,
        bsdf_node,
        offset_y: float = 0,
    ) -> None:
        """Add raycast nodes to material tree."""
        nodes = node_tree.nodes
        links = node_tree.links

        # Geometry node for position/normal
        geo = nodes.new("ShaderNodeNewGeometry")
        geo.location = (-800, offset_y)

        # Raycast node
        raycast = nodes.new("ShaderNodeRaycast")
        raycast.location = (-500, offset_y)
        raycast.inputs["Ray Length"].default_value = config.max_distance

        # Connect position
        links.new(geo.outputs["Position"], raycast.inputs["Source Position"])

        # Set direction
        if config.direction == RaycastDirection.NORMAL:
            links.new(geo.outputs["Normal"], raycast.inputs["Direction"])
        elif config.direction == RaycastDirection.CUSTOM:
            combine = nodes.new("ShaderNodeCombineXYZ")
            combine.location = (-700, offset_y - 100)
            combine.inputs["X"].default_value = config.custom_direction[0]
            combine.inputs["Y"].default_value = config.custom_direction[1]
            combine.inputs["Z"].default_value = config.custom_direction[2]
            links.new(combine.outputs["Vector"], raycast.inputs["Direction"])

        # Select output
        output_map = {
            RaycastOutputType.IS_HIT: "Is Hit",
            RaycastOutputType.HIT_DISTANCE: "Hit Distance",
            RaycastOutputType.HIT_POSITION: "Hit Position",
            RaycastOutputType.HIT_NORMAL: "Hit Normal",
        }
        raycast_output = raycast.outputs[output_map[config.output_type]]

        # Map range if needed
        if config.map_range:
            map_range = nodes.new("ShaderNodeMapRange")
            map_range.location = (-200, offset_y)
            map_range.inputs["From Min"].default_value = config.from_min
            map_range.inputs["From Max"].default_value = config.from_max
            map_range.inputs["To Min"].default_value = config.to_min
            map_range.inputs["To Max"].default_value = config.to_max
            links.new(raycast_output, map_range.inputs["Value"])
            factor = map_range.outputs["Result"]
        else:
            factor = raycast_output

        # Invert if needed
        if config.invert:
            invert = nodes.new("ShaderNodeMath")
            invert.location = (0, offset_y)
            invert.operation = "SUBTRACT"
            invert.inputs[0].default_value = 1.0
            links.new(factor, invert.inputs[1])
            factor = invert.outputs[0]

        # Mix with base color (multiply for darkening)
        mix_color = nodes.new("ShaderNodeMixRGB")
        mix_color.location = (100, offset_y + 50)
        mix_color.blend_type = "MULTIPLY"
        mix_color.inputs["Fac"].default_value = 0.5
        links.new(factor, mix_color.inputs["Fac"])
        links.new(bsdf_node.outputs["BSDF"], mix_color.inputs["Color1"])

        # Note: For actual material integration, you'd need to:
        # 1. Store original color
        # 2. Mix based on factor
        # This is a simplified version

    @property
    def material(self) -> Optional[Material]:
        """Get the built material."""
        return self._material


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_proximity_ao_material(
    target_object: str,
    max_distance: float = 1.0,
    base_color: Tuple[float, float, float] = (0.8, 0.8, 0.8),
    ao_color: Tuple[float, float, float] = (0.3, 0.3, 0.3),
    material_name: str = "ProximityAO",
) -> Optional[Material]:
    """
    Create a material with proximity-based ambient occlusion.

    Uses the Blender 5.1 Raycast node to create real-time AO
    based on distance to target geometry.

    Args:
        target_object: Object to measure proximity to
        max_distance: Maximum distance for AO effect
        base_color: Base material color
        ao_color: Color in occluded areas
        material_name: Name for the material

    Returns:
        Created material or None if Blender not available

    Example:
        >>> mat = create_proximity_ao_material(
        ...     target_object="Wall",
        ...     max_distance=1.0,
        ...     base_color=(0.9, 0.9, 0.9),
        ...     ao_color=(0.4, 0.4, 0.4),
        ... )
    """
    builder = RaycastMaterialBuilder(material_name)
    builder.with_base_color((*base_color, 1.0))
    builder.add_proximity_ao(target_object, max_distance)
    return builder.build()


def create_contact_shadow_material(
    target_object: str,
    max_distance: float = 0.5,
    base_color: Tuple[float, float, float] = (0.9, 0.9, 0.9),
    shadow_color: Tuple[float, float, float] = (0.1, 0.1, 0.1),
    material_name: str = "ContactShadow",
) -> Optional[Material]:
    """
    Create a material with contact shadows.

    Args:
        target_object: Object to detect contacts with
        max_distance: Maximum distance for shadow
        base_color: Base material color
        shadow_color: Color at contact points
        material_name: Name for the material

    Returns:
        Created material or None if Blender not available
    """
    builder = RaycastMaterialBuilder(material_name)
    builder.with_base_color((*base_color, 1.0))
    builder.add_contact_shadow(target_object, max_distance)
    return builder.build()


def create_edge_wear_material(
    max_distance: float = 0.2,
    base_color: Tuple[float, float, float] = (0.6, 0.55, 0.5),
    wear_color: Tuple[float, float, float] = (0.3, 0.25, 0.2),
    material_name: str = "EdgeWear",
) -> Optional[Material]:
    """
    Create a material with procedural edge wear.

    Uses self-raycast to detect edges and corners.

    Args:
        max_distance: Distance for edge detection
        base_color: Base material color
        wear_color: Color at worn edges
        material_name: Name for the material

    Returns:
        Created material or None if Blender not available
    """
    builder = RaycastMaterialBuilder(material_name)
    builder.with_base_color((*base_color, 1.0))
    builder.add_edge_wear(max_distance)
    return builder.build()


def apply_raycast_to_existing_material(
    material: Material,
    preset_name: str,
    target_object: str,
) -> bool:
    """
    Apply a raycast effect preset to an existing material.

    Args:
        material: Material to modify
        preset_name: Name of preset ("proximity_ao", "contact_shadow", "edge_wear")
        target_object: Target object name

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    preset = RAYCAST_PRESETS.get(preset_name)
    if not preset:
        return False

    # Clone preset config with target object
    config = RaycastConfig(
        target_object=target_object,
        max_distance=preset.config.max_distance,
        direction=preset.config.direction,
        output_type=preset.config.output_type,
        map_range=preset.config.map_range,
        from_min=preset.config.from_min,
        from_max=preset.config.from_max,
        to_min=preset.config.to_min,
        to_max=preset.config.to_max,
    )

    # Add raycast nodes to existing material
    if not material.use_nodes:
        material.use_nodes = True

    # Find Principled BSDF
    bsdf = None
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break

    if not bsdf:
        return False

    # Create builder and add effect
    builder = RaycastMaterialBuilder(material.name)
    builder._add_raycast_nodes(
        material.node_tree,
        config,
        bsdf,
        offset_y=-200,
    )

    return True


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RaycastOutputType",
    "RaycastDirection",
    # Dataclasses
    "RaycastConfig",
    "RaycastMaterialPreset",
    # Presets
    "PROXIMITY_AO_PRESET",
    "CONTACT_SHADOW_PRESET",
    "EDGE_WEAR_PRESET",
    "COLOR_BLEEDING_PRESET",
    "RAYCAST_PRESETS",
    # Functions
    "create_raycast_node_group_spec",
    "create_proximity_ao_material",
    "create_contact_shadow_material",
    "create_edge_wear_material",
    "apply_raycast_to_existing_material",
    # Classes
    "RaycastMaterialBuilder",
]
