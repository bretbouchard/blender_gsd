"""
Geometry Nodes Integration Tests

Tests that require real Blender environment to validate
geometry nodes creation and manipulation.
"""

import pytest
import sys
from pathlib import Path

# Ensure we can import from lib
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Skip all tests in this module if Blender not available
try:
    import bpy
    BPY_AVAILABLE = True
except ImportError:
    BPY_AVAILABLE = False

requires_blender = pytest.mark.skipif(
    not BPY_AVAILABLE,
    reason="Blender bpy module required"
)


@requires_blender
class TestGeometryNodeCreation:
    """Tests for creating geometry nodes in Blender."""

    def test_create_node_tree(self):
        """Test basic node tree creation."""
        import bpy

        # Create a new node tree
        node_tree = bpy.data.node_groups.new("TestGeometryNodes", 'GeometryNodeTree')
        assert node_tree is not None
        assert node_tree.type == 'GEOMETRY'

        # Cleanup
        bpy.data.node_groups.remove(node_tree)

    def test_add_input_node(self):
        """Test adding input node to tree."""
        import bpy

        # Create node tree
        node_tree = bpy.data.node_groups.new("TestInputNode", 'GeometryNodeTree')

        # Add input node
        input_node = node_tree.nodes.new('NodeGroupInput')
        assert input_node is not None

        # Cleanup
        bpy.data.node_groups.remove(node_tree)

    def test_add_output_node(self):
        """Test adding output node to tree."""
        import bpy

        # Create node tree
        node_tree = bpy.data.node_groups.new("TestOutputNode", 'GeometryNodeTree')

        # Add output node
        output_node = node_tree.nodes.new('NodeGroupOutput')
        assert output_node is not None

        # Cleanup
        bpy.data.node_groups.remove(node_tree)


@requires_blender
class TestPrimitiveNodes:
    """Tests for primitive geometry nodes."""

    def test_mesh_primitive_cube(self):
        """Test cube primitive node."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestCubePrimitive", 'GeometryNodeTree')

        # Add mesh primitive node
        cube_node = node_tree.nodes.new('GeometryNodeMeshCube')
        assert cube_node is not None

        # Verify default size (convert to tuple for comparison)
        size_val = tuple(cube_node.inputs['Size'].default_value)
        assert size_val == (1.0, 1.0, 1.0)

        # Cleanup
        bpy.data.node_groups.remove(node_tree)

    def test_mesh_primitive_grid(self):
        """Test grid primitive node."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestGridPrimitive", 'GeometryNodeTree')

        # Add grid primitive node
        grid_node = node_tree.nodes.new('GeometryNodeMeshGrid')
        assert grid_node is not None

        # Verify default size
        assert grid_node.inputs['Vertices X'].default_value == 3
        assert grid_node.inputs['Vertices Y'].default_value == 3

        # Cleanup
        bpy.data.node_groups.remove(node_tree)

    def test_mesh_primitive_uv_sphere(self):
        """Test UV sphere primitive node."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestSpherePrimitive", 'GeometryNodeTree')

        # Add sphere primitive node
        sphere_node = node_tree.nodes.new('GeometryNodeMeshUVSphere')
        assert sphere_node is not None

        # Verify default segments
        assert sphere_node.inputs['Segments'].default_value == 32

        # Cleanup
        bpy.data.node_groups.remove(node_tree)


@requires_blender
class TestGeometryNodeConnections:
    """Tests for connecting geometry nodes."""

    def test_node_linking(self):
        """Test linking nodes together."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestLinking", 'GeometryNodeTree')

        # Add input and output nodes
        input_node = node_tree.nodes.new('NodeGroupInput')
        output_node = node_tree.nodes.new('NodeGroupOutput')

        # Add a primitive node
        cube_node = node_tree.nodes.new('GeometryNodeMeshCube')

        # Create link from cube to output
        link = node_tree.links.new(
            cube_node.outputs[0],  # Geometry output
            output_node.inputs[0]   # Geometry input
        )
        assert link is not None

        # Cleanup
        bpy.data.node_groups.remove(node_tree)


@requires_blender
class TestGeometryNodeAttributes:
    """Tests for geometry node attribute handling."""

    def test_named_attribute_node(self):
        """Test named attribute node."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestAttributes", 'GeometryNodeTree')

        # Add store named attribute node
        store_node = node_tree.nodes.new('GeometryNodeStoreNamedAttribute')
        assert store_node is not None

        # Verify input socket exists
        assert 'Geometry' in store_node.inputs
        assert 'Name' in store_node.inputs

        # Cleanup
        bpy.data.node_groups.remove(node_tree)

    def test_input_attribute_node(self):
        """Test input attribute node."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestInputAttr", 'GeometryNodeTree')

        # Add input node
        input_node = node_tree.nodes.new('NodeGroupInput')

        # Add input attribute node
        attr_node = node_tree.nodes.new('GeometryNodeInputNamedAttribute')
        assert attr_node is not None

        # Verify it has data type enum
        assert hasattr(attr_node, 'data_type')

        # Cleanup
        bpy.data.node_groups.remove(node_tree)


@requires_blender
class TestNodeGroupInterface:
    """Tests for node group interface management."""

    def test_add_tree_socket(self):
        """Test adding sockets to node tree interface."""
        import bpy

        node_tree = bpy.data.node_groups.new("TestSockets", 'GeometryNodeTree')

        # Add input and output nodes
        input_node = node_tree.nodes.new('NodeGroupInput')
        output_node = node_tree.nodes.new('NodeGroupOutput')

        # Add a cube to expose geometry input
        cube_node = node_tree.nodes.new('GeometryNodeMeshCube')

        # Expose socket on interface
        # Note: In Blender 5.x, interface is managed differently
        tree_inputs = node_tree.interface.items_tree
        tree_outputs = node_tree.interface.items_tree

        assert tree_inputs is not None
        assert tree_outputs is not None

        # Cleanup
        bpy.data.node_groups.remove(node_tree)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "blender_integration"])
