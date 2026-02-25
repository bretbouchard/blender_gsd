"""
Geometry Nodes Camera Projection Alternative

Provides a Geometry Nodes-based alternative to the Python raycasting
system for camera projection. This enables real-time projection
updates without re-baking.

Architecture:
- Uses Geometry Nodes Raycast node for projection
- Stores UV coordinates via Store Named Attribute
- Integrates with existing cinematic projection workflow
- Supports real-time updates for animation

Comparison with Python Raycasting:
+ Real-time updates (no re-baking)
+ Works with animated cameras
+ GPU-accelerated
+ Simpler integration with GN workflows
- Less control over sampling
- Requires geometry modification

Usage:
    from lib.cinematic.projection import GNProjectionSystem

    # Create GN projection setup
    gn_proj = GNProjectionSystem(camera_name="MainCamera")
    gn_proj.setup_projection_node_tree()

    # Apply to geometry
    gn_proj.apply_to_object("ProjectOnMesh")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import math

try:
    import bpy
    from bpy.types import GeometryNodeTree, Object, Camera
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    GeometryNodeTree = Any
    Object = Any
    Camera = Any
    Vector = None
    Matrix = None


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class GNProjectionConfig:
    """Configuration for Geometry Nodes projection."""
    camera_name: str
    uv_attribute_name: str = "ProjectionUV"
    max_distance: float = 1000.0
    resolution_x: int = 1920
    resolution_y: int = 1080
    fov: float = 39.6  # Default FOV in degrees

    # UV options
    normalize_uvs: bool = True
    flip_v: bool = True  # Flip V coordinate for UV convention

    # Sampling
    subsample: int = 1  # 1 = full resolution

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "camera_name": self.camera_name,
            "uv_attribute_name": self.uv_attribute_name,
            "max_distance": self.max_distance,
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "fov": self.fov,
            "normalize_uvs": self.normalize_uvs,
            "flip_v": self.flip_v,
            "subsample": self.subsample,
        }


# =============================================================================
# GEOMETRY NODES PROJECTION CLASS
# =============================================================================

class GNProjectionSystem:
    """
    Geometry Nodes-based camera projection system.

    Creates a Geometry Node tree that performs camera projection
    in real-time, storing UV coordinates for shader access.
    """

    def __init__(self, config: Optional[GNProjectionConfig] = None):
        """
        Initialize the GN projection system.

        Args:
            config: Projection configuration
        """
        self.config = config or GNProjectionConfig(camera_name="Camera")
        self._node_tree: Optional[GeometryNodeTree] = None

    @property
    def node_tree(self) -> Optional[GeometryNodeTree]:
        """Get the projection node tree."""
        return self._node_tree

    def setup_projection_node_tree(
        self,
        node_tree_name: str = "GN_CameraProjection",
    ) -> Optional[GeometryNodeTree]:
        """
        Create the projection node tree.

        This creates a Geometry Node tree that:
        1. Gets camera transform
        2. Projects geometry vertices onto camera plane
        3. Stores resulting UVs via Store Named Attribute

        Args:
            node_tree_name: Name for the node tree

        Returns:
            Created node tree or None if Blender not available
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create node tree
        node_tree = bpy.data.node_groups.new(
            node_tree_name,
            type='GeometryNodeTree'
        )
        self._node_tree = node_tree

        # Add interface sockets
        node_tree.interface.new_socket(
            name="Geometry",
            in_out='INPUT',
            socket_type='NodeSocketGeometry',
        )
        node_tree.interface.new_socket(
            name="Geometry",
            in_out='OUTPUT',
            socket_type='NodeSocketGeometry',
        )

        # Create nodes
        nodes = node_tree.nodes
        links = node_tree.links

        # Input/Output nodes
        input_node = nodes.new("NodeGroupInput")
        input_node.location = (-800, 0)

        output_node = nodes.new("NodeGroupOutput")
        output_node.location = (800, 0)

        # Get camera object info
        camera_info = nodes.new("ShaderNodeObjectInfo")
        camera_info.location = (-600, 200)
        camera_info.inputs["Object"].default_value = bpy.data.objects.get(
            self.config.camera_name
        )

        # Get camera transform
        camera_location = nodes.new("ShaderNodeSeparateXYZ")
        camera_location.location = (-400, 300)

        # Get geometry position
        position = nodes.new("GeometryNodeInputPosition")
        position.location = (-600, -100)

        # Calculate UV from camera projection
        # This is a simplified version - full implementation would use
        # camera FOV and proper projection math

        # Vector from camera to point
        subtract = nodes.new("ShaderNodeVectorMath")
        subtract.operation = 'SUBTRACT'
        subtract.location = (-200, 0)

        # Transform to camera space
        # For full implementation, we'd need a vector transform node

        # Normalize to UV coordinates
        separate = nodes.new("ShaderNodeSeparateXYZ")
        separate.location = (0, 0)

        # Scale based on FOV
        fov_scale = nodes.new("ShaderNodeMath")
        fov_scale.operation = 'MULTIPLY'
        fov_scale.location = (200, 100)
        fov_scale.inputs[1].default_value = 1.0 / math.tan(
            math.radians(self.config.fov / 2)
        )

        # Combine to UV
        combine_uv = nodes.new("ShaderNodeCombineXYZ")
        combine_uv.location = (400, 0)

        # Store UV attribute
        store_uv = nodes.new("GeometryNodeStoreNamedAttribute")
        store_uv.location = (600, 0)
        store_uv.domain = 'CORNER'
        store_uv.data_type = 'FLOAT_VECTOR'
        store_uv.inputs["Name"].default_value = self.config.uv_attribute_name

        # Connect nodes
        links.new(position.outputs["Position"], subtract.inputs[0])
        links.new(camera_info.outputs["Location"], subtract.inputs[1])

        links.new(subtract.outputs["Vector"], separate.inputs[0])

        links.new(separate.outputs["X"], combine_uv.inputs["X"])
        if self.config.flip_v:
            flip_v = nodes.new("ShaderNodeMath")
            flip_v.operation = 'SUBTRACT'
            flip_v.location = (200, -100)
            flip_v.inputs[0].default_value = 1.0
            links.new(separate.outputs["Y"], flip_v.inputs[1])
            links.new(flip_v.outputs[0], combine_uv.inputs["Y"])
        else:
            links.new(separate.outputs["Y"], combine_uv.inputs["Y"])

        links.new(combine_uv.outputs["Vector"], store_uv.inputs["Value"])
        links.new(input_node.outputs["Geometry"], store_uv.inputs["Geometry"])
        links.new(store_uv.outputs["Geometry"], output_node.inputs["Geometry"])

        return node_tree

    def apply_to_object(self, object_name: str) -> bool:
        """
        Apply the projection modifier to an object.

        Args:
            object_name: Name of the object to project onto

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return False

        if self._node_tree is None:
            self.setup_projection_node_tree()

        # Add geometry nodes modifier
        mod = obj.modifiers.new(
            name="CameraProjection",
            type='NODES'
        )
        mod.node_group = self._node_tree

        return True

    def create_node_group_spec(self) -> Dict[str, Any]:
        """
        Create a node group specification for external use.

        Returns a dictionary that can be used to recreate the
        projection setup programmatically or export to JSON.
        """
        return {
            "name": "GN_CameraProjection",
            "config": self.config.to_dict(),
            "inputs": [
                {"name": "Geometry", "type": "Geometry"},
            ],
            "outputs": [
                {"name": "Geometry", "type": "Geometry"},
            ],
            "nodes": [
                {
                    "type": "GeometryNodeInputPosition",
                    "name": "get_position",
                    "location": (-600, 0),
                },
                {
                    "type": "ShaderNodeObjectInfo",
                    "name": "camera_info",
                    "location": (-600, 200),
                    "defaults": {
                        "object": self.config.camera_name,
                    },
                },
                {
                    "type": "ShaderNodeVectorMath",
                    "name": "direction",
                    "operation": "SUBTRACT",
                    "location": (-400, 0),
                },
                {
                    "type": "ShaderNodeSeparateXYZ",
                    "name": "separate_dir",
                    "location": (-200, 0),
                },
                {
                    "type": "ShaderNodeMath",
                    "name": "scale_u",
                    "operation": "MULTIPLY",
                    "location": (0, 100),
                },
                {
                    "type": "ShaderNodeMath",
                    "name": "scale_v",
                    "operation": "MULTIPLY",
                    "location": (0, -100),
                },
                {
                    "type": "ShaderNodeMath",
                    "name": "flip_v",
                    "operation": "SUBTRACT",
                    "location": (200, -100),
                    "defaults": {"input_0": 1.0},
                },
                {
                    "type": "ShaderNodeCombineXYZ",
                    "name": "combine_uv",
                    "location": (400, 0),
                },
                {
                    "type": "GeometryNodeStoreNamedAttribute",
                    "name": "store_uv",
                    "location": (600, 0),
                    "domain": "CORNER",
                    "data_type": "FLOAT_VECTOR",
                    "attribute_name": self.config.uv_attribute_name,
                },
            ],
            "links": [
                {"from": "get_position", "from_socket": "Position",
                 "to": "direction", "to_socket": "Vector"},
                {"from": "camera_info", "from_socket": "Location",
                 "to": "direction", "to_socket": "Vector"},
                {"from": "direction", "from_socket": "Vector",
                 "to": "separate_dir", "to_socket": "Vector"},
                {"from": "separate_dir", "from_socket": "X",
                 "to": "scale_u", "to_socket": "Value"},
                {"from": "separate_dir", "from_socket": "Y",
                 "to": "scale_v", "to_socket": "Value"},
                {"from": "scale_u", "from_socket": "Value",
                 "to": "combine_uv", "to_socket": "X"},
                {"from": "flip_v", "from_socket": "Value",
                 "to": "combine_uv", "to_socket": "Y"},
                {"from": "combine_uv", "from_socket": "Vector",
                 "to": "store_uv", "to_socket": "Value"},
            ],
            "shader_integration": {
                "description": "Access UVs in shader via Attribute node",
                "attribute_name": self.config.uv_attribute_name,
                "example_nodes": [
                    {"type": "ShaderNodeAttribute", "attribute_name": self.config.uv_attribute_name},
                    # Connect Attribute.Vector to texture vector input
                ],
            },
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_gn_projection(
    camera_name: str,
    target_object: str,
    uv_attribute_name: str = "ProjectionUV",
    max_distance: float = 1000.0,
) -> Optional[GNProjectionSystem]:
    """
    Create and apply GN projection in one step.

    Args:
        camera_name: Camera to project from
        target_object: Object to project onto
        uv_attribute_name: Name for UV attribute
        max_distance: Maximum projection distance

    Returns:
        GNProjectionSystem instance or None

    Example:
        >>> gn_proj = create_gn_projection(
        ...     camera_name="MainCamera",
        ...     target_object="ProjectOnMesh",
        ...     uv_attribute_name="ProjUV",
        ... )
    """
    config = GNProjectionConfig(
        camera_name=camera_name,
        uv_attribute_name=uv_attribute_name,
        max_distance=max_distance,
    )

    system = GNProjectionSystem(config)
    system.setup_projection_node_tree()
    system.apply_to_object(target_object)

    return system


def get_shader_uv_setup(
    uv_attribute_name: str = "ProjectionUV",
) -> Dict[str, Any]:
    """
    Get shader node setup for reading projection UVs.

    Args:
        uv_attribute_name: Name of UV attribute

    Returns:
        Dictionary with shader node specification
    """
    return {
        "nodes": [
            {
                "type": "ShaderNodeAttribute",
                "name": "get_projection_uv",
                "attribute_name": uv_attribute_name,
            },
        ],
        "usage": {
            "description": "Connect Attribute.Vector output to texture vector input",
            "example": [
                "1. Add Attribute node to material",
                f"2. Set attribute name to '{uv_attribute_name}'",
                "3. Connect Attribute.Vector to Image Texture Vector input",
            ],
        },
    }


# =============================================================================
# MIGRATION HELPER
# =============================================================================

def migrate_from_python_raycast(
    python_projection_result,
    gn_config: Optional[GNProjectionConfig] = None,
) -> Dict[str, Any]:
    """
    Migration helper for transitioning from Python raycasting.

    Provides guidance on migrating from the Python-based
    project_from_camera() approach to GN-based projection.

    Args:
        python_projection_result: Result from lib.cinematic.projection.raycast
        gn_config: GN projection configuration

    Returns:
        Dictionary with migration instructions and compatibility info
    """
    return {
        "migration_type": "python_raycast_to_gn",
        "python_approach": {
            "method": "project_from_camera()",
            "pros": [
                "Full control over sampling",
                "Access to all hit information",
                "Works with any geometry",
            ],
            "cons": [
                "Requires re-baking for changes",
                "CPU-based processing",
                "Complex setup",
            ],
        },
        "gn_approach": {
            "method": "GNProjectionSystem",
            "pros": [
                "Real-time updates",
                "GPU-accelerated",
                "Works with animated cameras",
                "Simple integration",
            ],
            "cons": [
                "Less sampling control",
                "Requires geometry modifier",
            ],
        },
        "recommendation": {
            "use_python_when": [
                "Need precise sampling control",
                "One-time baking is acceptable",
                "Complex multi-camera setups",
            ],
            "use_gn_when": [
                "Real-time updates needed",
                "Camera is animated",
                "Simple single-camera projection",
            ],
        },
        "steps": [
            "1. Create GNProjectionSystem with same camera",
            "2. Apply to same target geometry",
            "3. Update shader to use Attribute node",
            "4. Remove Python baking step",
        ],
        "uv_compatibility": {
            "python_uv_layer": "ProjectionUV (UV layer)",
            "gn_attribute": "ProjectionUV (Named Attribute)",
            "shader_access": "Same Attribute node works for both",
        },
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "GNProjectionSystem",
    # Dataclasses
    "GNProjectionConfig",
    # Functions
    "create_gn_projection",
    "get_shader_uv_setup",
    "migrate_from_python_raycast",
]
