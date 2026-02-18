"""
NodeKit - Thin helper for building Blender node trees programmatically.

Works for GeometryNodeTree, ShaderNodeTree, CompositorNodeTree.

Usage:
    nk = NodeKit(tree).clear()
    pos = nk.n("GeometryNodeInputPosition", "Position", x=0, y=0)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepXYZ", x=180, y=0)
    nk.link(pos.outputs["Position"], sep.inputs["Vector"])
"""

from __future__ import annotations
import bpy


class NodeKit:
    """
    Thin helper around Blender node trees.

    All graphs are generated via Python. Manual node wiring is forbidden.
    """

    def __init__(self, node_tree: bpy.types.NodeTree):
        self.tree = node_tree
        self.nodes = node_tree.nodes
        self.links = node_tree.links

    def clear(self) -> "NodeKit":
        """Remove all existing nodes."""
        self.nodes.clear()
        return self

    def n(
        self,
        node_type: str,
        name: str | None = None,
        x: float = 0.0,
        y: float = 0.0
    ) -> bpy.types.Node:
        """
        Create a new node.

        Args:
            node_type: Blender node type identifier (e.g., "GeometryNodeTransform")
            name: Optional display name/label
            x: X position in node editor
            y: Y position in node editor

        Returns:
            The created node
        """
        node = self.nodes.new(node_type)
        if name:
            node.name = name
            node.label = name
        node.location = (x, y)
        return node

    def link(self, out_socket, in_socket) -> "NodeKit":
        """Connect two sockets."""
        self.links.new(out_socket, in_socket)
        return self

    def set(self, socket, value) -> "NodeKit":
        """Set a socket's default value."""
        socket.default_value = value
        return self

    def group_input(self, x: float = 0, y: float = 0) -> bpy.types.Node:
        """Create a group input node."""
        return self.n("NodeGroupInput", "Group In", x, y)

    def group_output(self, x: float = 800, y: float = 0) -> bpy.types.Node:
        """Create a group output node."""
        return self.n("NodeGroupOutput", "Group Out", x, y)

    def pass_through(self, geo_socket, output_socket) -> None:
        """Connect geometry directly from input to output."""
        self.link(geo_socket, output_socket)
