"""
Generative Modeling Utilities for Blender Geometry Nodes.

Based on Curtis Holt's "Generative Modeling Experiments" tutorial.
Creates multi-layered shell effects and faceted remesh preparation.

Components:
    MultiLayerShell: Create complex layered geometry
    FacetedRemesh: Prepare geometry for stylized low-poly look
    GenerativeShell: Quick shell creation utility

Usage:
    from lib.geometry_nodes import MultiLayerShell, FacetedRemesh

    # Create multi-layer shell
    shell = MultiLayerShell(builder)
    shell.add_layer(scale=0.95, offset=-0.02)
    shell.add_layer(scale=1.0)
    result = shell.build(input_mesh)

    # Create faceted remesh setup
    faceted = FacetedRemesh(builder)
    faceted.set_voxel_size(0.05)
    faceted.preserve_edges(angle=30.0)
    prepared = faceted.build(input_mesh)
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import math

try:
    import bpy
    from mathutils import Vector
except ImportError:
    # Type hints for testing without Blender
    pass

from .node_builder import NodeTreeBuilder
from typing import TYPE_CHECKING, Any

# Type alias for nodes (since we can't import bpy in tests)
Node = Any


__all__ = [
    "MultiLayerShell",
    "ShellLayer",
    "FacetedRemesh",
    "GenerativeShell",
    "create_generative_shell",
]


@dataclass
class ShellLayer:
    """Configuration for a single shell layer."""
    scale: float = 1.0
    offset: float = 0.0
    material: Optional[Any] = None  # Material type
    solidify: float = 0.0
    rotation: tuple = (0.0, 0.0, 0.0)
    attribute_transfer: List[str] = field(default_factory=list)


class MultiLayerShell:
    """
    Create multi-layered shell effects for generative modeling.

    Based on Curtis Holt's Generator's Lab technique. Each layer
    can have independent scale, offset, material, and solidify settings.

    Flow:
        1. Configure layers with add_layer()
        2. Build with build()
        3. Each layer transforms, optionally solidifies, and gets material
        4. All layers are joined together

    Example:
        >>> shell = MultiLayerShell(builder)
        >>> shell.add_layer(scale=0.95, offset=-0.02, material=inner_mat)
        >>> shell.add_layer(scale=1.0, material=outer_mat)
        >>> result = shell.build(input_mesh)
    """

    def __init__(self, builder: NodeTreeBuilder):
        """
        Initialize the multi-layer shell system.

        Args:
            builder: NodeTreeBuilder for node creation.
        """
        self.builder = builder
        self.layers: List[ShellLayer] = []
        self._input_mesh: Optional[Node] = None

    def add_layer(
        self,
        scale: float = 1.0,
        offset: float = 0.0,
        material: Optional[Any] = None,
        solidify: float = 0.0,
        rotation: tuple = (0.0, 0.0, 0.0),
        attribute_transfer: Optional[List[str]] = None,
    ) -> "MultiLayerShell":
        """
        Add a shell layer with the given parameters.

        Args:
            scale: Scale factor for this layer (1.0 = original size).
            offset: Distance offset from original surface.
            material: Material to apply to this layer.
            solidify: If > 0, create solidified shell with this thickness.
            rotation: Rotation in degrees (x, y, z).
            attribute_transfer: List of attribute names to transfer to this layer.

        Returns:
            Self for method chaining.
        """
        layer = ShellLayer(
            scale=max(0.001, scale),
            offset=offset,
            material=material,
            solidify=max(0.0, solidify),
            rotation=rotation if rotation != (0.0, 0.0, 0.0) else (0, 0, 0),
            attribute_transfer=attribute_transfer or [],
        )
        self.layers.append(layer)
        return self

    def set_input_mesh(self, mesh: Node) -> "MultiLayerShell":
        """Set the input mesh for the shell system."""
        self._input_mesh = mesh
        return self

    def build(self, input_mesh: Optional[Node] = None) -> Optional[Node]:
        """
        Build the multi-layered shell geometry.

        Args:
            input_mesh: Optional input mesh node/socket. If not provided,
                          uses mesh set via set_input_mesh().

        Returns:
            Join Geometry node with all layers, or single layer if only one.

        Raises:
            ValueError: If no input mesh provided and none set.
        """
        b = self.builder

        # Resolve input mesh
        if input_mesh is None:
            input_mesh = self._input_mesh
        if input_mesh is None:
            raise ValueError("No input mesh provided. Use set_input_mesh() or pass to build().")

        if not self.layers:
            # No layers configured, return input unchanged
            return input_mesh

        current_x = 0
        outputs: List[Node] = []

        for i, layer in enumerate(self.layers):
            layer_x = current_x
            layer_y = -250 * i

            # Step 1: Transform for scale, offset, rotation
            transform = b.add_node(
                "GeometryNodeTransform",
                (layer_x, layer_y),
                name=f"ShellLayer{i}_Transform",
            )

            # Configure transform
            scale_uniform = b.add_node(
                "FunctionNodeInputVector",
                (layer_x - 200, layer_y + 100),
                name=f"Layer{i}_Scale",
            )
            scale_uniform.inputs["Vector"].default_value = (layer.scale,) * 3
            b.link(scale_uniform.outputs["Vector"], transform.inputs["Scale"])

            # Offset (translation)
            offset_uniform = b.add_node(
                "FunctionNodeInputVector",
                (layer_x - 200, layer_y + 50),
                name=f"Layer{i}_Offset",
            )
            offset_uniform.inputs["Vector"].default_value = (0, 0, layer.offset)
            b.link(offset_uniform.outputs["Vector"], transform.inputs["Translation"])

            # Rotation (Euler)
            if layer.rotation != (0, 0, 0):
                rot_euler = b.add_node(
                    "FunctionNodeEulerToRotation",
                    (layer_x - 200, layer_y - 50),
                    name=f"Layer{i}_Rotation",
                )
                rot_euler.inputs["Euler"].default_value = layer.rotation
                b.link(rot_euler.outputs["Rotation"], transform.inputs["Rotation"])

            # Link input to transform
            b.link(input_mesh, transform.inputs["Geometry"])

            current_output = transform.outputs["Geometry"]
            current_x += 250

            # Step 2: Optional solidify
            if layer.solidify > 0:
                solidify_node = b.add_node(
                    "GeometryNodeSolidify",
                    (current_x, layer_y),
                    name=f"ShellLayer{i}_Solidify",
                )
                solidify_node.inputs["Thickness"].default_value = layer.solidify
                b.link(current_output, solidify_node.inputs["Geometry"])
                current_output = solidify_node.outputs["Geometry"]
                current_x += 200

            # Step 3: Optional attribute transfer
            if layer.attribute_transfer:
                for attr_name in layer.attribute_transfer:
                    transfer = b.add_node(
                        "GeometryNodeTransferAttribute",
                        (current_x, layer_y - 100 * list(layer.attribute_transfer).index(attr_name)),
                        name=f"Transfer_{attr_name}",
                    )
                    transfer.inputs["Name"].default_value = attr_name
                    # Source is original mesh, target is current layer
                    b.link(input_mesh, transfer.inputs["Source"])
                    b.link(current_output, transfer.inputs["Geometry"])
                    current_output = transfer.outputs["Geometry"]
                    current_x += 150

            # Step 4: Optional material
            if layer.material is not None:
                set_material = b.add_node(
                    "GeometryNodeSetMaterial",
                    (current_x, layer_y),
                    name=f"ShellLayer{i}_Material",
                )
                set_material.inputs["Material"].default_value = layer.material
                b.link(current_output, set_material.inputs["Geometry"])
                current_output = set_material.outputs["Geometry"]
                current_x += 150

            outputs.append(current_output)

        # Step 5: Join all layers
        if len(outputs) == 1:
            return outputs[0]

        join = b.add_node(
            "GeometryNodeJoinGeometry",
            (current_x + 200, 0),
            name="JoinShellLayers",
        )

        for output in outputs:
            b.link(output, join.inputs["Geometry"])

        return join


class FacetedRemesh:
    """
    Prepare geometry for faceted remesh look.

    Note: Actual remesh happens in the modifier stack. This class
    sets up the geometry for optimal remeshing by:
    - Storing original normals for post-process
    - Setting up edge angle thresholds for sharp edge detection
    - Preparing attribute data for faceted shading

    The faceted look is achieved by:
    1. Apply Voxel Remesh modifier (outside GN)
    2. Apply Shade Smooth with custom edge angle
    3. Use flat shading or controlled normals

    Example:
        >>> faceted = FacetedRemesh(builder)
        >>> faceted.set_voxel_size(0.05)
        >>> faceted.preserve_edges(angle=30.0)
        >>> prepared = faceted.build(input_mesh)
        >>> # Then apply Voxel Remesh modifier in Blender
    """

    def __init__(self, builder: NodeTreeBuilder):
        """Initialize the faceted remesh preparer."""
        self.builder = builder
        self._voxel_size: float = 0.05
        self._preserve_sharp_edges: bool = True
        self._edge_angle: float = 30.0
        self._store_normals: bool = True
        self._normal_attr_name: str = "faceted_normal"

    def set_voxel_size(self, size: float) -> "FacetedRemesh":
        """Set target voxel size for remeshing."""
        self._voxel_size = max(0.001, size)
        return self

    def preserve_edges(self, angle: float = 30.0) -> "FacetedRemesh":
        """Preserve sharp edges above angle threshold."""
        self._preserve_sharp_edges = True
        self._edge_angle = max(0.0, min(180.0, angle))
        return self

    def store_normals(self, store: bool = True) -> "FacetedRemesh":
        """Store original normals for post-processing."""
        self._store_normals = store
        return self

    def set_normal_attribute_name(self, name: str) -> "FacetedRemesh":
        """Set the name for stored normals."""
        self._normal_attr_name = name
        return self

    def build(self, input_mesh: Node) -> Node:
        """
        Prepare geometry for faceted remesh.

        Args:
            input_mesh: Input geometry to prepare.

        Returns:
            Output geometry ready for remesh modifier.
        """
        b = self.builder
        current_x = 0
        current_output = input_mesh

        # Step 1: Store original normals if requested
        if self._store_normals:
            store_normal = b.add_node(
                "GeometryNodeStoreNamedAttribute",
                (current_x, 100),
                name="StoreOriginalNormals",
            )
            store_normal.inputs["Name"].default_value = self._normal_attr_name
            store_normal.inputs["Domain"].default_value = "POINT"  # Per-vertex

            # Capture normal from input
            normal = b.add_node(
                "GeometryNodeInputNormal",
                (current_x - 150, 50),
                name="CaptureNormal",
            )
            b.link(current_output, normal.inputs["Geometry"])
            b.link(normal.outputs["Normal"], store_normal.inputs["Value"])
            b.link(current_output, store_normal.inputs["Geometry"])

            current_output = store_normal.outputs["Geometry"]
            current_x += 200

        # Step 2: Store edge angle threshold for post-process
        if self._preserve_sharp_edges:
            # Store edge angle as attribute
            edge_angle_node = b.add_node(
                "GeometryNodeStoreNamedAttribute",
                (current_x, -50),
                name="StoreEdgeAngle",
            )
            edge_angle_node.inputs["Name"].default_value = "edge_angle_threshold"
            edge_angle_node.inputs["Domain"].default_value = "EDGE"

            # Create float input for angle
            angle_input = b.add_node(
                "FunctionNodeInputFloat",
                (current_x - 150, -100),
                name="EdgeAngleValue",
            )
            angle_input.inputs["Value"].default_value = self._edge_angle
            b.link(angle_input.outputs["Value"], edge_angle_node.inputs["Value"])
            b.link(current_output, edge_angle_node.inputs["Geometry"])

            current_output = edge_angle_node.outputs["Geometry"]
            current_x += 200

        # Step 3: Connect to output
        # The geometry is now ready for the Voxel Remesh modifier
        return current_output


class GenerativeShell(MultiLayerShell):
    """
    Extended shell builder with additional generative features.

    Adds:
        - Noise-based displacement per layer
        - Random rotation variation
        - Scale randomization

    Example:
        >>> shell = GenerativeShell(builder)
        >>> shell.add_layer(scale=0.95).add_noise(0.02)
        >>> shell.add_layer(scale=1.0).add_noise(0.01)
        >>> result = shell.build(input_mesh)
    """

    def __init__(self, builder: NodeTreeBuilder):
        super().__init__(builder)
        self._noise_scale: Dict[int, float] = {}
        self._rotation_variation: Dict[int, float] = {}
        self._scale_variation: Dict[int, float] = {}

    def add_noise(self, scale: float = 0.02, layer_index: int = -1) -> "GenerativeShell":
        """
        Add noise displacement to a layer.

        Args:
            scale: Noise scale multiplier.
            layer_index: Index of layer to apply to (-1 = last added).

        Returns:
            Self for chaining.
        """
        if layer_index == -1:
            layer_index = len(self.layers) - 1
        self._noise_scale[layer_index] = scale
        return self

    def add_rotation_variation(self, variation: float = 10.0, layer_index: int = -1) -> "GenerativeShell":
        """
        Add random rotation variation to a layer.

        Args:
            variation: Max degrees of random rotation.
            layer_index: Index of layer to apply to (-1 = last added).

        Returns:
            Self for chaining.
        """
        if layer_index == -1:
            layer_index = len(self.layers) - 1
        self._rotation_variation[layer_index] = variation
        return self

    def add_scale_variation(self, variation: float = 0.1, layer_index: int = -1) -> "GenerativeShell":
        """
        Add random scale variation to a layer.

        Args:
            variation: Scale variation factor (0.1 = ±10%).
            layer_index: Index of layer to apply to (-1 = last added).

        Returns:
            Self for chaining.
        """
        if layer_index == -1:
            layer_index = len(self.layers) - 1
        self._scale_variation[layer_index] = variation
        return self

    def build(self, input_mesh: Optional[Node] = None) -> Optional[Node]:
        """
        Build the generative shell with all variations.

        Extends parent build() with noise and randomization.
        """
        b = self.builder

        # Resolve input mesh
        if input_mesh is None:
            input_mesh = self._input_mesh
        if input_mesh is None:
            raise ValueError("No input mesh provided.")

        if not self.layers:
            return input_mesh

        current_x = 0
        outputs: List[Node] = []

        for i, layer in enumerate(self.layers):
            layer_x = current_x
            layer_y = -300 * i

            # Apply scale variation if set
            actual_scale = layer.scale
            if i in self._scale_variation:
                variation = self._scale_variation[i]
                actual_scale = layer.scale * (1.0 + (hash(str(i)) % 100 / 100.0 * variation * 2 - variation))

            # Create transform with potentially modified scale
            transform = b.add_node(
                "GeometryNodeTransform",
                (layer_x, layer_y),
                name=f"GenShellLayer{i}_Transform",
            )

            # Scale vector
            scale_vec = b.add_node(
                "FunctionNodeInputVector",
                (layer_x - 200, layer_y + 100),
                name=f"GenLayer{i}_Scale",
            )
            scale_vec.inputs["Vector"].default_value = (actual_scale,) * 3
            b.link(scale_vec.outputs["Vector"], transform.inputs["Scale"])

            # Offset
            offset_vec = b.add_node(
                "FunctionNodeInputVector",
                (layer_x - 200, layer_y + 50),
                name=f"GenLayer{i}_Offset",
            )
            offset_vec.inputs["Vector"].default_value = (0, 0, layer.offset)
            b.link(offset_vec.outputs["Vector"], transform.inputs["Translation"])

            # Rotation with variation
            rotation = layer.rotation
            if i in self._rotation_variation:
                variation = self._rotation_variation[i]
                rotation = tuple(
                    r + (hash(f"{i}{r}") % 100 / 100.0 * variation * 2 - variation)
                    for r in layer.rotation
                )

            if rotation != (0, 0, 0):
                rot_euler = b.add_node(
                    "FunctionNodeEulerToRotation",
                    (layer_x - 200, layer_y - 50),
                    name=f"GenLayer{i}_Rotation",
                )
                rot_euler.inputs["Euler"].default_value = rotation
                b.link(rot_euler.outputs["Rotation"], transform.inputs["Rotation"])

            b.link(input_mesh, transform.inputs["Geometry"])

            current_output = transform.outputs["Geometry"]
            current_x += 250

            # Apply noise displacement if set
            if i in self._noise_scale:
                noise_scale = self._noise_scale[i]

                # Position for noise sampling
                position = b.add_node(
                    "GeometryNodeInputPosition",
                    (current_x, layer_y + 100),
                    name=f"GenLayer{i}_Position",
                )
                b.link(current_output, position.inputs["Geometry"])

                # Noise texture
                noise_tex = b.add_node(
                    "ShaderNodeTexNoise",
                    (current_x + 100, layer_y + 150),
                    name=f"GenLayer{i}_Noise",
                )
                noise_tex.inputs["Scale"].default_value = noise_scale
                b.link(position.outputs["Position"], noise_tex.inputs["Vector"])

                # Separate XYZ
                separate_xyz = b.add_node(
                    "FunctionNodeSeparateXYZ",
                    (current_x + 250, layer_y + 100),
                    name=f"GenLayer{i}_SeparateNoise",
                )
                b.link(noise_tex.outputs["Color"], separate_xyz.inputs["Vector"])

                # Displacement along normal
                normal = b.add_node(
                    "GeometryNodeInputNormal",
                    (current_x, layer_y + 50),
                    name=f"GenLayer{i}_Normal",
                )
                b.link(current_output, normal.inputs["Geometry"])

                # Multiply normal by noise
                multiply = b.add_node(
                    "FunctionNodeVectorMath",
                    (current_x + 350, layer_y),
                    name=f"GenLayer{i}_MultiplyNoise",
                )
                multiply.inputs["Operation"].default_value = "MULTIPLY"
                b.link(normal.outputs["Normal"], multiply.inputs["Vector A"])
                b.link(separate_xyz.outputs["Z"], multiply.inputs["Vector B"])

                # Set position
                set_pos = b.add_node(
                    "GeometryNodeSetPosition",
                    (current_x + 500, layer_y),
                    name=f"GenLayer{i}_Displace",
                )
                b.link(current_output, set_pos.inputs["Geometry"])
                b.link(multiply.outputs["Vector"], set_pos.inputs["Position"])

                current_output = set_pos.outputs["Geometry"]
                current_x += 550

            # Continue with solidify, material, etc. from parent
            if layer.solidify > 0:
                solidify_node = b.add_node(
                    "GeometryNodeSolidify",
                    (current_x, layer_y),
                    name=f"GenShellLayer{i}_Solidify",
                )
                solidify_node.inputs["Thickness"].default_value = layer.solidify
                b.link(current_output, solidify_node.inputs["Geometry"])
                current_output = solidify_node.outputs["Geometry"]
                current_x += 200

            if layer.material is not None:
                set_material = b.add_node(
                    "GeometryNodeSetMaterial",
                    (current_x, layer_y),
                    name=f"GenShellLayer{i}_Material",
                )
                set_material.inputs["Material"].default_value = layer.material
                b.link(current_output, set_material.inputs["Geometry"])
                current_output = set_material.outputs["Geometry"]
                current_x += 150

            outputs.append(current_output)

        # Join all layers
        if len(outputs) == 1:
            return outputs[0]

        join = b.add_node(
            "GeometryNodeJoinGeometry",
            (current_x + 200, 0),
            name="JoinGenShellLayers",
        )

        for output in outputs:
            b.link(output, join.inputs["Geometry"])

        return join


def create_generative_shell(
    builder: NodeTreeBuilder,
    input_mesh: Node,
    layers: int = 3,
    base_scale: float = 1.0,
    scale_step: float = -0.02,
    add_noise: bool = False,
    noise_scale: float = 0.02,
) -> Optional[Node]:
    """
    Quick creation of generative multi-layer shell.

    Args:
        builder: NodeTreeBuilder instance
        input_mesh: Input geometry node/socket
        layers: Number of shell layers to create
        base_scale: Scale of outermost layer
        scale_step: Scale change per layer (negative = smaller inner)
        add_noise: Whether to add noise displacement
        noise_scale: Scale of noise displacement

    Returns:
        Join Geometry node with all layers

    Example:
        >>> shell = create_generative_shell(
        ...     builder, mesh_input,
        ...     layers=5,
        ...     scale_step=-0.03,
        ...     add_noise=True
        ... )
    """
    shell = GenerativeShell(builder)

    for i in range(layers):
        scale = base_scale + (i * scale_step)
        offset = scale_step * i * 0.5

        shell.add_layer(scale=scale, offset=offset)

        if add_noise:
            shell.add_noise(noise_scale * (1 + i * 0.5), layer_index=i)

    return shell.build(input_mesh)
