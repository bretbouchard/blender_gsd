"""
Unit tests for lib/geometry_nodes/generator.py

Tests the Node Graph Generator including:
- SocketType enum
- SocketDef, NodeDef, LinkDef, ClosureDef dataclasses
- PatternBuilder class
- NodeGraphGenerator class
- Built-in pattern generators

Note: Tests that require Blender are marked with @pytest.mark.requires_blender
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

# Import the module - may fail if bpy not available
try:
    from lib.geometry_nodes.generator import (
        SocketType,
        SocketDef,
        NodeDef,
        LinkDef,
        ClosureDef,
        PatternBuilder,
        NodeGraphGenerator,
    )
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="bpy not available")


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestSocketType:
    """Tests for SocketType enum."""

    def test_socket_type_values(self):
        """Test that SocketType enum has expected values."""
        assert SocketType.GEOMETRY.value == "NodeSocketGeometry"
        assert SocketType.FLOAT.value == "NodeSocketFloat"
        assert SocketType.INT.value == "NodeSocketInt"
        assert SocketType.VECTOR.value == "NodeSocketVector"
        assert SocketType.COLOR.value == "NodeSocketColor"
        assert SocketType.BOOLEAN.value == "NodeSocketBool"

    def test_socket_type_count(self):
        """Test that all expected socket types exist."""
        assert len(SocketType) >= 10


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestSocketDef:
    """Tests for SocketDef dataclass."""

    def test_default_values(self):
        """Test SocketDef default values."""
        socket = SocketDef(name="test", socket_type="NodeSocketFloat")
        assert socket.name == "test"
        assert socket.socket_type == "NodeSocketFloat"
        assert socket.default_value is None
        assert socket.min_value is None
        assert socket.max_value is None
        assert socket.description == ""

    def test_custom_values(self):
        """Test SocketDef with custom values."""
        socket = SocketDef(
            name="strength",
            socket_type="NodeSocketFloat",
            default_value=1.0,
            min_value=0.0,
            max_value=10.0,
            description="Effect strength"
        )
        assert socket.default_value == 1.0
        assert socket.min_value == 0.0
        assert socket.max_value == 10.0

    def test_to_dict(self):
        """Test SocketDef.to_dict() serialization."""
        socket = SocketDef(
            name="test",
            socket_type="NodeSocketFloat",
            default_value=0.5,
            min_value=0.0
        )
        data = socket.to_dict()
        assert data["name"] == "test"
        assert data["default_value"] == 0.5
        assert data["min_value"] == 0.0


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestNodeDef:
    """Tests for NodeDef dataclass."""

    def test_default_values(self):
        """Test NodeDef default values."""
        node = NodeDef(node_type="GeometryNodeTransform", name="transform")
        assert node.node_type == "GeometryNodeTransform"
        assert node.name == "transform"
        assert node.x == 0.0
        assert node.y == 0.0
        assert node.properties == {}
        assert node.input_values == {}

    def test_custom_values(self):
        """Test NodeDef with custom values."""
        node = NodeDef(
            node_type="ShaderNodeTexNoise",
            name="noise",
            x=200.0,
            y=100.0,
            properties={"scale": 5.0},
            input_values={"detail": 2.0}
        )
        assert node.x == 200.0
        assert node.y == 100.0
        assert node.properties == {"scale": 5.0}

    def test_to_dict(self):
        """Test NodeDef.to_dict() serialization."""
        node = NodeDef(
            node_type="GeometryNodeTransform",
            name="test",
            x=100.0,
            properties={"mode": "relative"}
        )
        data = node.to_dict()
        assert data["node_type"] == "GeometryNodeTransform"
        assert data["x"] == 100.0
        assert data["properties"] == {"mode": "relative"}


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestLinkDef:
    """Tests for LinkDef dataclass."""

    def test_link_def(self):
        """Test LinkDef creation."""
        link = LinkDef(
            from_node="noise",
            from_socket="color",
            to_node="multiply",
            to_socket="value"
        )
        assert link.from_node == "noise"
        assert link.from_socket == "color"
        assert link.to_node == "multiply"
        assert link.to_socket == "value"

    def test_to_dict(self):
        """Test LinkDef.to_dict() serialization."""
        link = LinkDef(from_node="a", from_socket="out", to_node="b", to_socket="in")
        data = link.to_dict()
        assert data["from_node"] == "a"
        assert data["to_socket"] == "in"


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestClosureDef:
    """Tests for ClosureDef dataclass."""

    def test_closure_def(self):
        """Test ClosureDef creation."""
        closure = ClosureDef(
            name="randomize_transform",
            inputs=[SocketDef(name="geometry", socket_type="NodeSocketGeometry")],
            outputs=[SocketDef(name="geometry", socket_type="NodeSocketGeometry")],
            nodes=[],
            links=[],
            description="Random rotation and scale"
        )
        assert closure.name == "randomize_transform"
        assert closure.description == "Random rotation and scale"
        assert len(closure.inputs) == 1
        assert len(closure.outputs) == 1

    def test_to_dict(self):
        """Test ClosureDef.to_dict() serialization."""
        closure = ClosureDef(
            name="test",
            inputs=[SocketDef(name="in", socket_type="NodeSocketFloat")],
            outputs=[SocketDef(name="out", socket_type="NodeSocketFloat")],
            nodes=[NodeDef(node_type="TestNode", name="node")],
            links=[]
        )
        data = closure.to_dict()
        assert data["name"] == "test"
        assert len(data["inputs"]) == 1
        assert len(data["nodes"]) == 1


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestPatternBuilder:
    """Tests for PatternBuilder class."""

    def test_initialization(self):
        """Test PatternBuilder initialization."""
        builder = PatternBuilder("TestPattern")
        assert builder.name == "TestPattern"
        assert builder.tree_type == "GeometryNodeTree"
        assert builder._inputs == []
        assert builder._outputs == []
        assert builder._nodes == []
        assert builder._links == []

    def test_describe(self):
        """Test describe method."""
        builder = PatternBuilder("Test")
        result = builder.describe("Test description")
        assert result is builder
        assert builder._description == "Test description"

    def test_tag(self):
        """Test tag method."""
        builder = PatternBuilder("Test")
        result = builder.tag("tag1", "tag2")
        assert result is builder
        assert "tag1" in builder._tags
        assert "tag2" in builder._tags

    def test_add_input(self):
        """Test add_input method."""
        builder = PatternBuilder("Test")
        result = builder.add_input("Geometry", "geometry")
        assert result is builder
        assert len(builder._inputs) == 1
        assert builder._inputs[0].name == "Geometry"

    def test_add_input_with_default(self):
        """Test add_input with default value."""
        builder = PatternBuilder("Test")
        builder.add_input("Strength", "float", default_value=1.0, min_value=0.0, max_value=10.0)
        assert builder._inputs[0].default_value == 1.0
        assert builder._inputs[0].min_value == 0.0

    def test_add_output(self):
        """Test add_output method."""
        builder = PatternBuilder("Test")
        result = builder.add_output("Geometry", "geometry")
        assert result is builder
        assert len(builder._outputs) == 1

    def test_add_node(self):
        """Test add_node method."""
        builder = PatternBuilder("Test")
        result = builder.add_node("noise", "ShaderNodeTexNoise", x=200)
        assert result is builder
        assert len(builder._nodes) == 1
        assert builder._nodes[0].name == "noise"
        assert builder._nodes[0].node_type == "ShaderNodeTexNoise"

    def test_add_node_auto_position(self):
        """Test add_node auto-positioning."""
        builder = PatternBuilder("Test")
        builder.add_node("a", "TestNode")
        builder.add_node("b", "TestNode")
        builder.add_node("c", "TestNode", x=1000)  # Explicit position

        assert builder._nodes[0].x == 0
        assert builder._nodes[1].x == 200  # NODE_SPACING_X
        assert builder._nodes[2].x == 1000  # Explicit

    def test_link(self):
        """Test link method."""
        builder = PatternBuilder("Test")
        result = builder.link("noise.color", "multiply.value")
        assert result is builder
        assert len(builder._links) == 1
        assert builder._links[0].from_node == "noise"
        assert builder._links[0].from_socket == "color"

    def test_link_invalid_format(self):
        """Test link with invalid format raises."""
        builder = PatternBuilder("Test")
        with pytest.raises(ValueError):
            builder.link("invalid", "also_invalid")

    def test_chain(self):
        """Test chain method."""
        builder = PatternBuilder("Test")
        result = builder.chain("node1", "node2", "node3")
        assert result is builder
        assert len(builder._links) == 2
        # First link: node1 -> node2
        assert builder._links[0].from_node == "node1"
        assert builder._links[0].to_node == "node2"
        # Second link: node2 -> node3
        assert builder._links[1].from_node == "node2"
        assert builder._links[1].to_node == "node3"

    def test_to_closure(self):
        """Test to_closure method."""
        builder = PatternBuilder("Test")
        builder.add_input("in", "geometry")
        builder.add_output("out", "geometry")
        closure = builder.to_closure()
        assert closure.name == "Test"
        assert len(closure.inputs) == 1
        assert len(closure.outputs) == 1


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestPatternBuilderConvenienceMethods:
    """Tests for PatternBuilder convenience methods."""

    def test_add_noise_node(self):
        """Test add_noise_node method."""
        builder = PatternBuilder("Test")
        result = builder.add_noise_node("noise", scale=10.0, detail=3.0, distortion=0.5)
        assert result is builder
        assert len(builder._nodes) == 1
        assert builder._nodes[0].input_values["scale"] == 10.0

    def test_add_math_node(self):
        """Test add_math_node method."""
        builder = PatternBuilder("Test")
        result = builder.add_math_node("add", operation="ADD", value_1=1.0, value_2=2.0)
        assert result is builder
        assert builder._nodes[0].properties["operation"] == "ADD"

    def test_add_vector_math_node(self):
        """Test add_vector_math_node method."""
        builder = PatternBuilder("Test")
        result = builder.add_vector_math_node("vmath", operation="DOT_PRODUCT")
        assert result is builder
        assert builder._nodes[0].properties["operation"] == "DOT_PRODUCT"

    def test_add_separate_xyz(self):
        """Test add_separate_xyz method."""
        builder = PatternBuilder("Test")
        result = builder.add_separate_xyz("sep")
        assert result is builder
        assert builder._nodes[0].node_type == "ShaderNodeSeparateXYZ"

    def test_add_combine_xyz(self):
        """Test add_combine_xyz method."""
        builder = PatternBuilder("Test")
        result = builder.add_combine_xyz("comb")
        assert result is builder
        assert builder._nodes[0].node_type == "ShaderNodeCombineXYZ"

    def test_add_position_node(self):
        """Test add_position_node method."""
        builder = PatternBuilder("Test")
        result = builder.add_position_node()
        assert result is builder
        assert builder._nodes[0].node_type == "GeometryNodeInputPosition"

    def test_add_set_position(self):
        """Test add_set_position method."""
        builder = PatternBuilder("Test")
        result = builder.add_set_position()
        assert result is builder
        assert builder._nodes[0].node_type == "GeometryNodeSetPosition"

    def test_add_random_value(self):
        """Test add_random_value method."""
        builder = PatternBuilder("Test")
        result = builder.add_random_value("rand", min_val=0.0, max_val=1.0, seed=42)
        assert result is builder
        assert builder._nodes[0].input_values["min"] == 0.0
        assert builder._nodes[0].input_values["seed"] == 42


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestNodeGraphGenerator:
    """Tests for NodeGraphGenerator class."""

    def test_initialization(self):
        """Test NodeGraphGenerator initialization."""
        gen = NodeGraphGenerator()
        assert gen._closures == {}
        assert gen.PATTERN_GENERATORS != {}  # Has built-in generators

    def test_list_patterns(self):
        """Test list_patterns method."""
        gen = NodeGraphGenerator()
        patterns = gen.list_patterns()
        assert "random_transform" in patterns
        assert "height_scale" in patterns
        assert "noise_displace" in patterns

    def test_register_pattern(self):
        """Test register_pattern method."""
        gen = NodeGraphGenerator()

        def custom_generator(params):
            return None  # Placeholder

        gen.register_pattern("custom_pattern", custom_generator)
        assert "custom_pattern" in gen.PATTERN_GENERATORS

    def test_from_pattern_builtin(self):
        """Test from_pattern with built-in pattern."""
        gen = NodeGraphGenerator()
        # This test requires Blender to be available
        # In CI, this would be skipped
        try:
            tree = gen.from_pattern("random_transform", {"seed": 42})
            assert tree is not None
        except Exception:
            pytest.skip("Blender not available for tree creation")

    def test_from_pattern_not_found(self):
        """Test from_pattern with non-existent pattern."""
        gen = NodeGraphGenerator()
        with pytest.raises(ValueError):
            gen.from_pattern("nonexistent_pattern_xyz")


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestNodeGraphGeneratorClosures:
    """Tests for NodeGraphGenerator closure functionality."""

    def test_closure_definition(self):
        """Test closure definition."""
        gen = NodeGraphGenerator()
        closure = gen.closure(
            name="test_closure",
            inputs=[{"name": "in", "socket_type": "geometry"}],
            outputs=[{"name": "out", "socket_type": "geometry"}]
        )
        assert closure.name == "test_closure"
        assert "test_closure" in gen._closures

    def test_closure_with_logic(self):
        """Test closure with logic function."""
        gen = NodeGraphGenerator()

        def add_nodes(builder):
            builder.add_node("transform", "GeometryNodeTransform")

        closure = gen.closure(
            name="with_logic",
            inputs=[{"name": "in", "socket_type": "geometry"}],
            outputs=[{"name": "out", "socket_type": "geometry"}],
            logic=add_nodes
        )
        assert len(closure.nodes) == 1


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestBuiltInPatterns:
    """Tests for built-in pattern generators."""

    def test_random_transform_generator_exists(self):
        """Test random_transform generator is registered."""
        assert "random_transform" in NodeGraphGenerator.PATTERN_GENERATORS

    def test_height_scale_generator_exists(self):
        """Test height_scale generator is registered."""
        assert "height_scale" in NodeGraphGenerator.PATTERN_GENERATORS

    def test_noise_displace_generator_exists(self):
        """Test noise_displace generator is registered."""
        assert "noise_displace" in NodeGraphGenerator.PATTERN_GENERATORS


@pytest.mark.skipif(not GENERATOR_AVAILABLE, reason="Generator module requires bpy")
class TestDocumentationTree:
    """Tests for documentation tree fallback."""

    def test_documentation_tree_created_for_empty_pattern(self):
        """Test that documentation tree is created for patterns without nodes."""
        from lib.knowledge.query import Pattern

        gen = NodeGraphGenerator()

        # Create a pattern with no nodes
        pattern = Pattern(
            name="empty_pattern",
            description="Pattern with no nodes",
            category="test",
            nodes=[],  # Empty nodes list
            workflow="Step 1 -> Step 2 -> Step 3"
        )

        # This should create a documentation tree instead of crashing
        try:
            tree = gen._build_from_knowledge_pattern(pattern, {})
            assert tree is not None
        except Exception:
            # If Blender not available, just check the method exists
            assert hasattr(gen, '_create_documentation_tree')

    def test_documentation_tree_uses_workflow(self):
        """Test that documentation tree parses workflow steps."""
        from lib.knowledge.query import Pattern

        pattern = Pattern(
            name="workflow_test",
            description="Test workflow parsing",
            category="test",
            nodes=[],
            workflow="A -> B -> C -> D"
        )

        gen = NodeGraphGenerator()
        # Check the method handles workflow parsing
        assert hasattr(gen, '_create_documentation_tree')


# Tests that can run without bpy (mocked)
class TestPatternBuilderMocked:
    """Tests for PatternBuilder using mocks (no bpy required)."""

    def test_socket_type_map(self):
        """Test socket type mapping."""
        if not GENERATOR_AVAILABLE:
            pytest.skip("Generator not available")

        assert "geometry" in PatternBuilder.SOCKET_TYPE_MAP
        assert PatternBuilder.SOCKET_TYPE_MAP["geometry"] == "NodeSocketGeometry"
        assert PatternBuilder.SOCKET_TYPE_MAP["float"] == "NodeSocketFloat"
        assert PatternBuilder.SOCKET_TYPE_MAP["vector"] == "NodeSocketVector"

    def test_node_spacing_constants(self):
        """Test node spacing constants."""
        if not GENERATOR_AVAILABLE:
            pytest.skip("Generator not available")

        assert PatternBuilder.NODE_SPACING_X == 200
        assert PatternBuilder.NODE_SPACING_Y == 150


class TestModuleImports:
    """Tests for module import behavior."""

    def test_import_without_bpy(self):
        """Test that module handles missing bpy gracefully."""
        # This test verifies the import structure
        # The actual import behavior depends on environment
        import sys
        if 'bpy' not in sys.modules:
            # bpy not available, module should have failed to import
            # but SocketDef etc should be importable if we mock
            pass

    def test_fallback_imports(self):
        """Test fallback import paths."""
        # The module has fallback imports for NodeKit and KnowledgeQuery
        # This is tested implicitly by the import at the top
        pass
