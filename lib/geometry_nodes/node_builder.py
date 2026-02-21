"""
NodeTreeBuilder - Programmatic geometry node tree creation.

Provides a fluent interface for building Blender geometry node trees
programmatically with support for simulation zones, repeat zones,
and group wrapping.

Usage:
    builder = NodeTreeBuilder("MyNodeGroup")
    pos = builder.add_node("GeometryNodeInputPosition", (0, 0))
    transform = builder.add_node("GeometryNodeTransform", (200, 0))
    builder.link(pos.outputs["Position"], transform.inputs["Translation"])
    tree = builder.get_tree()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

import bpy
from mathutils import Matrix, Vector

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bpy.types import (
        GeometryNode,
        GeometryNodeTree,
        Node,
        NodeLink,
        NodeSocket,
    )


class NodeTreeBuilder:
    """
    Build geometry node trees programmatically.

    Provides a high-level API for creating, connecting, and organizing
    geometry nodes with support for zones (simulation, repeat) and
    group operations.

    Attributes:
        tree: The underlying GeometryNodeTree being built.
        nodes: Direct access to the node tree's nodes collection.
        links: Direct access to the node tree's links collection.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a new NodeTreeBuilder.

        Creates a new GeometryNodeTree with the given name. If a tree
        with that name already exists, it will be replaced.

        Args:
            name: The name for the geometry node tree.

        Raises:
            ValueError: If name is empty or None.
        """
        if not name:
            raise ValueError("Node tree name cannot be empty")

        # Remove existing tree with same name if it exists
        if name in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups[name])

        self.tree: GeometryNodeTree = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.nodes = self.tree.nodes
        self.links = self.tree.links
        self._node_counter: int = 0

    def add_node(
        self,
        node_type: str,
        location: tuple[float, float],
        name: Optional[str] = None,
        **inputs: Any,
    ) -> Node:
        """
        Add a new node to the tree.

        Creates a node of the specified type at the given location and
        optionally sets input socket values.

        Args:
            node_type: The Blender node type identifier (e.g., "GeometryNodeTransform").
            location: The (x, y) position in the node editor.
            name: Optional display name/label for the node.
            **inputs: Keyword arguments to set input socket default values.
                     The key is the socket name, the value is the default value.

        Returns:
            The created node instance.

        Raises:
            TypeError: If node_type is not a valid node type.
            KeyError: If an input socket name doesn't exist on the node.

        Example:
            >>> builder.add_node(
            ...     "GeometryNodeTransform",
            ...     (200, 0),
            ...     name="MyTransform",
            ...     Translation=(1, 0, 0),
            ...     Scale=(2, 2, 2)
            ... )
        """
        node = self.nodes.new(node_type)

        # Set location
        node.location = location

        # Set name/label
        if name:
            node.name = name
            node.label = name
        else:
            self._node_counter += 1
            node.name = f"{node_type}_{self._node_counter}"
            node.label = node_type.replace("GeometryNode", "").replace("Node", "")

        # Set input values
        for socket_name, value in inputs.items():
            if socket_name in node.inputs:
                socket = node.inputs[socket_name]
                self._set_socket_value(socket, value)
            else:
                raise KeyError(
                    f"Input socket '{socket_name}' not found on {node_type}. "
                    f"Available inputs: {[s.name for s in node.inputs]}"
                )

        return node

    def _set_socket_value(self, socket: NodeSocket, value: Any) -> None:
        """
        Set a socket's default value with type handling.

        Handles various input types including vectors, colors, and scalars.

        Args:
            socket: The input socket to set.
            value: The value to assign.
        """
        try:
            if hasattr(socket, "default_value"):
                # Handle Vector/Color conversion
                if isinstance(value, (Vector, tuple, list)):
                    if len(value) == 3:
                        socket.default_value = tuple(value)
                    elif len(value) == 4:
                        socket.default_value = tuple(value)
                else:
                    socket.default_value = value
        except (AttributeError, TypeError) as e:
            # Some sockets are read-only or have incompatible types
            raise TypeError(
                f"Cannot set value {value!r} on socket {socket.name}: {e}"
            ) from e

    def link(
        self,
        from_socket: NodeSocket,
        to_socket: NodeSocket,
    ) -> NodeLink:
        """
        Connect two sockets.

        Creates a link between an output socket and an input socket.

        Args:
            from_socket: The source output socket.
            to_socket: The destination input socket.

        Returns:
            The created NodeLink.

        Raises:
            ValueError: If sockets cannot be connected (type mismatch, etc.).

        Example:
            >>> pos = builder.add_node("GeometryNodeInputPosition", (0, 0))
            >>> transform = builder.add_node("GeometryNodeTransform", (200, 0))
            >>> builder.link(pos.outputs["Position"], transform.inputs["Translation"])
        """
        try:
            return self.links.new(from_socket, to_socket)
        except RuntimeError as e:
            raise ValueError(
                f"Cannot connect {from_socket.node.name}.{from_socket.name} -> "
                f"{to_socket.node.name}.{to_socket.name}: {e}"
            ) from e

    def link_by_name(
        self,
        from_node: Node,
        from_socket_name: str,
        to_node: Node,
        to_socket_name: str,
    ) -> NodeLink:
        """
        Connect sockets by name.

        Convenience method that looks up sockets by name before linking.

        Args:
            from_node: The source node.
            from_socket_name: Name of the output socket on the source node.
            to_node: The destination node.
            to_socket_name: Name of the input socket on the destination node.

        Returns:
            The created NodeLink.

        Raises:
            KeyError: If socket names are not found.
        """
        try:
            from_socket = from_node.outputs[from_socket_name]
        except KeyError as e:
            raise KeyError(
                f"Output socket '{from_socket_name}' not found on node '{from_node.name}'. "
                f"Available outputs: {[s.name for s in from_node.outputs]}"
            ) from e

        try:
            to_socket = to_node.inputs[to_socket_name]
        except KeyError as e:
            raise KeyError(
                f"Input socket '{to_socket_name}' not found on node '{to_node.name}'. "
                f"Available inputs: {[s.name for s in to_node.inputs]}"
            ) from e

        return self.link(from_socket, to_socket)

    def add_simulation_zone(
        self,
        location: tuple[float, float] = (0, 0),
        name: Optional[str] = None,
    ) -> tuple[Node, Node]:
        """
        Add a simulation zone to the tree.

        Creates paired Simulation Input and Simulation Output nodes.
        The simulation zone allows geometry to be processed iteratively
        with persistent state between frames.

        Args:
            location: The (x, y) position for the input node.
                     Output node will be placed 400 units to the right.
            name: Optional prefix for node names.

        Returns:
            A tuple of (input_node, output_node).

        Example:
            >>> sim_in, sim_out = builder.add_simulation_zone((500, 0), "Fluid")
            >>> # Connect geometry through simulation
            >>> builder.link(geometry_node.outputs["Geometry"], sim_in.inputs["Geometry"])
        """
        prefix = f"{name}_" if name else ""

        input_node = self.add_node(
            "GeometryNodeSimulationInput",
            location,
            name=f"{prefix}SimInput",
        )
        output_node = self.add_node(
            "GeometryNodeSimulationOutput",
            (location[0] + 400, location[1]),
            name=f"{prefix}SimOutput",
        )

        # Link the paired nodes (required for simulation zone to work)
        # The simulation zone uses a paired socket system
        input_node.paired_output = output_node
        output_node.paired_input = input_node

        return input_node, output_node

    def add_repeat_zone(
        self,
        iterations: int,
        location: tuple[float, float] = (0, 0),
        name: Optional[str] = None,
    ) -> tuple[Node, Node]:
        """
        Add a repeat zone to the tree.

        Creates paired Repeat Input and Repeat Output nodes that iterate
        geometry processing a specified number of times.

        Args:
            iterations: Number of iterations to perform.
            location: The (x, y) position for the input node.
                     Output node will be placed 400 units to the right.
            name: Optional prefix for node names.

        Returns:
            A tuple of (input_node, output_node).

        Example:
            >>> repeat_in, repeat_out = builder.add_repeat_zone(5, (300, 0), "Subdivide")
            >>> # Process geometry 5 times through the repeat zone
        """
        prefix = f"{name}_" if name else ""

        input_node = self.add_node(
            "GeometryNodeRepeatInput",
            location,
            name=f"{prefix}RepeatInput",
            Iterations=iterations,
        )
        output_node = self.add_node(
            "GeometryNodeRepeatOutput",
            (location[0] + 400, location[1]),
            name=f"{prefix}RepeatOutput",
        )

        # Link the paired nodes
        input_node.paired_output = output_node
        output_node.paired_input = input_node

        return input_node, output_node

    def add_group_input(
        self,
        location: tuple[float, float] = (0, 0),
    ) -> Node:
        """
        Add a group input node.

        Args:
            location: The (x, y) position for the node.

        Returns:
            The created group input node.
        """
        return self.add_node("NodeGroupInput", location, name="Group Input")

    def add_group_output(
        self,
        location: tuple[float, float] = (800, 0),
    ) -> Node:
        """
        Add a group output node.

        Args:
            location: The (x, y) position for the node.

        Returns:
            The created group output node.
        """
        return self.add_node("NodeGroupOutput", location, name="Group Output")

    def wrap_as_group(
        self,
        inputs: Sequence[dict[str, Any]],
        outputs: Sequence[dict[str, Any]],
    ) -> None:
        """
        Configure the tree as a reusable node group.

        Defines the interface (inputs and outputs) for the node tree
        so it can be used as a group node in other node trees.

        Args:
            inputs: List of input definitions. Each dict should contain:
                - "name": Socket display name
                - "type": Socket type (e.g., "GEOMETRY", "VALUE", "VECTOR")
                - "default": Optional default value
            outputs: List of output definitions. Each dict should contain:
                - "name": Socket display name
                - "type": Socket type

        Example:
            >>> builder.wrap_as_group(
            ...     inputs=[
            ...         {"name": "Geometry", "type": "GEOMETRY"},
            ...         {"name": "Scale", "type": "VALUE", "default": 1.0},
            ...     ],
            ...     outputs=[
            ...         {"name": "Geometry", "type": "GEOMETRY"},
            ...     ]
            ... )
        """
        # Create input interface
        for input_def in inputs:
            socket = self.tree.inputs.new(input_def["type"], input_def["name"])
            if "default" in input_def:
                self._set_socket_value(socket, input_def["default"])

        # Create output interface
        for output_def in outputs:
            self.tree.outputs.new(output_def["type"], output_def["name"])

    def get_tree(self) -> GeometryNodeTree:
        """
        Get the built node tree.

        Returns:
            The underlying GeometryNodeTree instance.
        """
        return self.tree

    def clear(self) -> "NodeTreeBuilder":
        """
        Clear all nodes from the tree.

        Returns:
            Self for method chaining.
        """
        self.nodes.clear()
        self._node_counter = 0
        return self

    def remove_node(self, node: Union[Node, str]) -> None:
        """
        Remove a node from the tree.

        Args:
            node: The node instance or node name to remove.

        Raises:
            KeyError: If node name is not found.
        """
        if isinstance(node, str):
            if node not in self.nodes:
                raise KeyError(f"Node '{node}' not found in tree")
            node = self.nodes[node]

        self.nodes.remove(node)

    def organize_layout(self, spacing: float = 200) -> None:
        """
        Automatically organize node layout using a simple grid.

        Attempts to arrange nodes in a readable left-to-right flow
        based on their connection order.

        Args:
            spacing: Base spacing between nodes.
        """
        # Get all nodes sorted by their current x position
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.location.x)

        # Apply spacing
        x_offset = 0
        for node in sorted_nodes:
            node.location.x = x_offset
            x_offset += spacing

    def add_comment_frame(
        self,
        nodes: Sequence[Node],
        label: str,
    ) -> Node:
        """
        Add a frame node to group and label related nodes.

        Args:
            nodes: Nodes to include in the frame.
            label: Label text for the frame.

        Returns:
            The created frame node.
        """
        frame = self.nodes.new("NodeFrame")
        frame.label = label

        # Parent nodes to the frame
        for node in nodes:
            node.parent = frame

        return frame

    def duplicate_node(
        self,
        node: Node,
        offset: tuple[float, float] = (200, 0),
        new_name: Optional[str] = None,
    ) -> Node:
        """
        Duplicate a node with offset positioning.

        Args:
            node: The node to duplicate.
            offset: Position offset from the original.
            new_name: Optional name for the duplicate.

        Returns:
            The duplicated node.
        """
        new_node = self.nodes.new(node.bl_idname)
        new_node.location = (node.location.x + offset[0], node.location.y + offset[1])
        new_node.name = new_name or f"{node.name}_copy"
        new_node.label = new_name or f"{node.label} (copy)"

        # Copy input values
        for i, socket in enumerate(node.inputs):
            if i < len(new_node.inputs) and hasattr(socket, "default_value"):
                try:
                    new_node.inputs[i].default_value = socket.default_value
                except (AttributeError, TypeError):
                    pass

        return new_node
