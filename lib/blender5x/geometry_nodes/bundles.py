"""
Bundles & Closures in Geometry Nodes for Blender 5.0+.

Blender 5.0 introduced bundles and closures for Geometry Nodes, enabling
data encapsulation, reusable node groups, and functional programming patterns
in the node tree.

Example:
    >>> from lib.blender5x.geometry_nodes import Bundles, Closures
    >>> bundle = Bundles.create(mesh_obj)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, NodeTree, Node


class BundleDataType(Enum):
    """Supported bundle data types."""

    GEOMETRY = "geometry"
    """Geometry data (mesh, curve, point cloud, etc.)."""

    FLOAT = "float"
    """Single float value."""

    VECTOR = "vector"
    """3D vector value."""

    COLOR = "color"
    """RGBA color value."""

    INT = "int"
    """Integer value."""

    BOOLEAN = "boolean"
    """Boolean value."""

    STRING = "string"
    """String value."""

    MATRIX = "matrix"
    """4x4 transformation matrix."""


@dataclass
class BundleField:
    """A field in a bundle."""

    name: str
    """Field name."""

    data_type: BundleDataType
    """Data type of the field."""

    default_value: Any = None
    """Default value for the field."""

    description: str = ""
    """Field description."""


@dataclass
class BundleSchema:
    """Schema definition for a bundle."""

    name: str
    """Bundle schema name."""

    fields: list[BundleField] = field(default_factory=list)
    """List of fields in the bundle."""

    description: str = ""
    """Schema description."""

    def add_field(
        self,
        name: str,
        data_type: BundleDataType,
        default_value: Any = None,
        description: str = "",
    ) -> "BundleSchema":
        """
        Add a field to the schema.

        Args:
            name: Field name.
            data_type: Field data type.
            default_value: Default value.
            description: Field description.

        Returns:
            Self for chaining.
        """
        self.fields.append(
            BundleField(
                name=name,
                data_type=data_type,
                default_value=default_value,
                description=description,
            )
        )
        return self


@dataclass
class ClosureInfo:
    """Information about a closure."""

    name: str
    """Closure name."""

    inputs: list[BundleField]
    """Input parameters."""

    outputs: list[BundleField]
    """Output parameters."""

    node_tree_name: str
    """Associated node tree name."""

    is_pure: bool = True
    """Whether the closure is pure (no side effects)."""


class Bundles:
    """
    Bundle utilities for Geometry Nodes (Blender 5.0+).

    Bundles provide a way to package multiple named data values together,
    similar to structs or dictionaries in programming.

    Example:
        >>> schema = BundleSchema("MaterialParams")
        >>> schema.add_field("base_color", BundleDataType.COLOR)
        >>> schema.add_field("roughness", BundleDataType.FLOAT, 0.5)
    """

    @staticmethod
    def create_schema(name: str, description: str = "") -> BundleSchema:
        """
        Create a new bundle schema.

        Args:
            name: Schema name.
            description: Schema description.

        Returns:
            BundleSchema instance.

        Example:
            >>> schema = Bundles.create_schema("Transform", "Transform data")
            >>> schema.add_field("position", BundleDataType.VECTOR)
            >>> schema.add_field("rotation", BundleDataType.VECTOR)
            >>> schema.add_field("scale", BundleDataType.VECTOR, (1, 1, 1))
        """
        return BundleSchema(name=name, description=description)

    @staticmethod
    def create_bundle_node(
        tree: NodeTree,
        schema: BundleSchema,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create a bundle node in a geometry node tree.

        Args:
            tree: Geometry node tree.
            schema: Bundle schema to use.
            position: Node position in the tree.

        Returns:
            Created node.

        Example:
            >>> node = Bundles.create_bundle_node(tree, schema)
        """
        import bpy

        # Create Combine node (Blender 5.0+)
        # In Blender 5.0, bundles are created using special nodes
        combine_node = tree.nodes.new("FunctionNodeCombineBundle")
        combine_node.location = position
        combine_node.label = schema.name

        return combine_node

    @staticmethod
    def separate_bundle_node(
        tree: NodeTree,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create a separate bundle node.

        Args:
            tree: Geometry node tree.
            position: Node position.

        Returns:
            Created node.
        """
        import bpy

        separate_node = tree.nodes.new("FunctionNodeSeparateBundle")
        separate_node.location = position

        return separate_node

    @staticmethod
    def pack_geometry(
        tree: NodeTree,
        geometry_source: Node,
        attributes: dict[str, Node] | None = None,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Pack geometry with attributes into a bundle.

        Args:
            tree: Geometry node tree.
            geometry_source: Node providing geometry.
            attributes: Dictionary of attribute name -> source node.
            position: Node position.

        Returns:
            Created pack node.

        Example:
            >>> pack_node = Bundles.pack_geometry(
            ...     tree,
            ...     mesh_node,
            ...     {"UV": uv_node, "Color": color_node},
            ... )
        """
        import bpy

        # Create bundle pack node
        pack_node = tree.nodes.new("GeometryNodeBundlePack")
        pack_node.location = position

        # Link geometry
        tree.links.new(geometry_source.outputs[0], pack_node.inputs["Geometry"])

        # Link attributes if provided
        if attributes:
            for attr_name, source_node in attributes.items():
                # Add attribute input to bundle
                if hasattr(pack_node, f"add_{attr_name}"):
                    tree.links.new(
                        source_node.outputs[0],
                        pack_node.inputs[attr_name],
                    )

        return pack_node


class Closures:
    """
    Closure utilities for Geometry Nodes (Blender 5.0+).

    Closures provide reusable, encapsulated functionality in Geometry Nodes,
    similar to functions in programming. They can capture external values
    and be passed around as first-class objects.

    Example:
        >>> closure = Closures.create("TransformGeometry")
        >>> closure.add_input("offset", BundleDataType.VECTOR)
        >>> closure.add_output("geometry", BundleDataType.GEOMETRY)
    """

    @staticmethod
    def create(
        name: str,
        description: str = "",
        is_pure: bool = True,
    ) -> ClosureInfo:
        """
        Create a new closure definition.

        Args:
            name: Closure name.
            description: Closure description.
            is_pure: Whether the closure has no side effects.

        Returns:
            ClosureInfo instance.

        Example:
            >>> closure = Closures.create("ScaleByFactor", is_pure=True)
            >>> closure.inputs.append(BundleField("factor", BundleDataType.FLOAT))
            >>> closure.outputs.append(BundleField("geometry", BundleDataType.GEOMETRY))
        """
        return ClosureInfo(
            name=name,
            inputs=[],
            outputs=[],
            node_tree_name=f"Closure_{name}",
            is_pure=is_pure,
        )

    @staticmethod
    def create_node_group(
        closure: ClosureInfo,
    ) -> str:
        """
        Create a node group from a closure definition.

        Args:
            closure: Closure definition.

        Returns:
            Name of the created node group.

        Example:
            >>> node_group_name = Closures.create_node_group(closure)
        """
        import bpy

        # Create new node group
        tree = bpy.data.node_groups.new(closure.node_tree_name, "GeometryNodeTree")

        # Add interface sockets for inputs
        for inp in closure.inputs:
            socket_type = Closures._get_socket_type(inp.data_type)
            tree.interface.new_socket(
                inp.name,
                in_out="INPUT",
                socket_type=socket_type,
            )

        # Add interface sockets for outputs
        for out in closure.outputs:
            socket_type = Closures._get_socket_type(out.data_type)
            tree.interface.new_socket(
                out.name,
                in_out="OUTPUT",
                socket_type=socket_type,
            )

        # Add input and output nodes
        input_node = tree.nodes.new("NodeGroupInput")
        output_node = tree.nodes.new("NodeGroupOutput")

        # Position nodes
        input_node.location = (-400, 0)
        output_node.location = (400, 0)

        return tree.name

    @staticmethod
    def compose(
        closures: list[ClosureInfo],
        name: str = "ComposedClosure",
    ) -> ClosureInfo:
        """
        Compose multiple closures into a single closure.

        Args:
            closures: List of closures to compose.
            name: Name for composed closure.

        Returns:
            New ClosureInfo representing the composition.

        Example:
            >>> composed = Closures.compose([transform, scale, rotate])
        """
        # The first closure's inputs become the composed inputs
        # The last closure's outputs become the composed outputs
        if not closures:
            raise ValueError("Cannot compose empty list of closures")

        composed = ClosureInfo(
            name=name,
            inputs=list(closures[0].inputs),
            outputs=list(closures[-1].outputs),
            node_tree_name=f"Closure_{name}",
            is_pure=all(c.is_pure for c in closures),
        )

        return composed

    @staticmethod
    def curry(
        closure: ClosureInfo,
        bound_inputs: dict[str, Any],
    ) -> ClosureInfo:
        """
        Partially apply (curry) inputs to a closure.

        Args:
            closure: Original closure.
            bound_inputs: Dictionary of input name -> value to bind.

        Returns:
            New ClosureInfo with bound inputs removed from inputs.

        Example:
            >>> curried = Closures.curry(
            ...     scale_closure,
            ...     {"factor": 2.0},
            ... )
        """
        # Create new closure with bound inputs removed
        new_inputs = [
            inp
            for inp in closure.inputs
            if inp.name not in bound_inputs
        ]

        curried = ClosureInfo(
            name=f"{closure.name}_Curried",
            inputs=new_inputs,
            outputs=list(closure.outputs),
            node_tree_name=closure.node_tree_name,
            is_pure=closure.is_pure,
        )

        return curried

    @staticmethod
    def invoke(
        tree: NodeTree,
        closure: ClosureInfo,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create a node that invokes a closure.

        Args:
            tree: Geometry node tree.
            closure: Closure to invoke.
            position: Node position.

        Returns:
            Created invoke node.

        Example:
            >>> invoke_node = Closures.invoke(tree, transform_closure)
        """
        import bpy

        # Get the closure's node group
        node_group = bpy.data.node_groups.get(closure.node_tree_name)

        if node_group is None:
            raise ValueError(f"Node group not found: {closure.node_tree_name}")

        # Create node group instance
        invoke_node = tree.nodes.new("GeometryNodeGroup")
        invoke_node.node_tree = node_group
        invoke_node.location = position
        invoke_node.label = closure.name

        return invoke_node

    @staticmethod
    def _get_socket_type(data_type: BundleDataType) -> str:
        """Convert BundleDataType to Blender socket type string."""
        type_map = {
            BundleDataType.GEOMETRY: "NodeSocketGeometry",
            BundleDataType.FLOAT: "NodeSocketFloat",
            BundleDataType.VECTOR: "NodeSocketVector",
            BundleDataType.COLOR: "NodeSocketColor",
            BundleDataType.INT: "NodeSocketInt",
            BundleDataType.BOOLEAN: "NodeSocketBool",
            BundleDataType.STRING: "NodeSocketString",
            BundleDataType.MATRIX: "NodeSocketMatrix",
        }
        return type_map.get(data_type, "NodeSocketFloat")


class LazyEvaluation:
    """
    Lazy evaluation utilities for Geometry Nodes (Blender 5.0+).

    Provides tools for creating lazy-evaluated node trees that only
    compute values when needed.

    Example:
        >>> lazy_node = LazyEvaluation.create_delayed_input(tree, "value")
    """

    @staticmethod
    def create_delayed_input(
        tree: NodeTree,
        name: str,
        data_type: BundleDataType = BundleDataType.FLOAT,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create a delayed (lazy) input that is only evaluated when used.

        Args:
            tree: Geometry node tree.
            name: Input name.
            data_type: Data type for the input.
            position: Node position.

        Returns:
            Created node.
        """
        import bpy

        # Create an input socket that uses lazy evaluation
        # In Blender 5.0+, this uses the lazy input system
        socket_type = Closures._get_socket_type(data_type)

        # Add to tree interface with lazy flag
        socket = tree.interface.new_socket(
            name,
            in_out="INPUT",
            socket_type=socket_type,
        )

        # Mark as lazy (if supported)
        if hasattr(socket, "use_lazy_evaluation"):
            socket.use_lazy_evaluation = True

        return socket

    @staticmethod
    def create_thunk(
        tree: NodeTree,
        computation: Node,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Create a thunk (delayed computation wrapper).

        Args:
            tree: Geometry node tree.
            computation: Node whose output should be delayed.
            position: Node position.

        Returns:
            Created thunk node.
        """
        import bpy

        # Create thunk wrapper node
        thunk_node = tree.nodes.new("FunctionNodeThunk")
        thunk_node.location = position

        # Link computation output to thunk input
        if computation.outputs:
            tree.links.new(computation.outputs[0], thunk_node.inputs[0])

        return thunk_node

    @staticmethod
    def force_evaluation(
        tree: NodeTree,
        thunk_node: Node,
        position: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Force evaluation of a thunk.

        Args:
            tree: Geometry node tree.
            thunk_node: Thunk node to force.
            position: Node position.

        Returns:
            Created force node.
        """
        import bpy

        # Create force evaluation node
        force_node = tree.nodes.new("FunctionNodeForce")
        force_node.location = position

        # Link thunk to force
        tree.links.new(thunk_node.outputs[0], force_node.inputs[0])

        return force_node


# Convenience exports
__all__ = [
    "Bundles",
    "Closures",
    "LazyEvaluation",
    "BundleSchema",
    "BundleField",
    "BundleDataType",
    "ClosureInfo",
]
