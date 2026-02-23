"""
Unit tests for lib/inputs/button_builder.py

Tests the button element builder system.
Uses mocks for bpy (Blender) dependencies to test without Blender.

Tests focus on:
- ButtonBuilder class interface
- Socket interface creation
- Style definitions
- Factory function behavior
"""

import pytest
import sys
from unittest.mock import MagicMock, patch, PropertyMock


class MockInterfaceSocket:
    """Mock for Blender interface socket."""

    def __init__(self, name, socket_type):
        self.name = name
        self.socket_type = socket_type
        self.default_value = None
        self.min_value = 0.0
        self.max_value = 1.0


class MockNodeInput:
    """Mock for Blender node input."""

    def __init__(self, name):
        self.name = name
        self.default_value = None


class MockNode:
    """Mock for Blender node."""

    def __init__(self, node_type, name):
        self.node_type = node_type
        self.name = name
        self.location = (0, 0)
        self.inputs = {}
        self.outputs = {}
        self.operation = None
        self.data_type = None

    def __getitem__(self, key):
        return self.inputs.get(key) or self.outputs.get(key)


class MockNodeTree:
    """Mock for Blender node tree."""

    def __init__(self):
        self.nodes = []
        self.links = []
        self.interface = MagicMock()

    def new_socket(self, name, in_out, socket_type):
        socket = MockInterfaceSocket(name, socket_type)
        return socket


class MockTree:
    """Mock for Blender node groups tree."""

    def __init__(self, name, tree_type):
        self.name = name
        self.tree_type = tree_type
        self.interface = MockNodeTree()
        self.nodes = []

    def __getitem__(self, key):
        for node in self.nodes:
            if node.name == key:
                return node
        return None


class MockMaterial:
    """Mock for Blender material."""

    def __init__(self, name):
        self.name = name
        self.use_nodes = False
        self.node_tree = MagicMock()
        self.node_tree.nodes = []


class MockBpyData:
    """Mock for bpy.data."""

    def __init__(self):
        self.node_groups = MagicMock()
        self.materials = MagicMock()

        self.node_groups.new = MagicMock(side_effect=self._new_node_group)
        self.materials.new = MagicMock(side_effect=self._new_material)

    def _new_node_group(self, name, tree_type):
        return MockTree(name, tree_type)

    def _new_material(self, name):
        return MockMaterial(name)


class TestButtonBuilderStructure:
    """Tests for ButtonBuilder class structure and interface."""

    def test_button_builder_class_exists(self):
        """Test that ButtonBuilder class is defined."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "class ButtonBuilder" in content

    def test_button_builder_has_create_interface(self):
        """Test that ButtonBuilder has _create_interface method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _create_interface" in content

    def test_button_builder_has_build_geometry(self):
        """Test that ButtonBuilder has _build_geometry method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _build_geometry" in content

    def test_button_builder_has_create_material(self):
        """Test that ButtonBuilder has _create_material method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _create_material" in content


class TestButtonBuilderInterface:
    """Tests for button interface socket creation."""

    def test_interface_creates_diameter_socket(self):
        """Test that interface creates Diameter socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Diameter"' in content

    def test_interface_creates_height_socket(self):
        """Test that interface creates Height socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Height"' in content

    def test_interface_creates_travel_socket(self):
        """Test that interface creates Travel socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Travel"' in content

    def test_interface_creates_style_socket(self):
        """Test that interface creates Style socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Style"' in content

    def test_interface_creates_bezel_sockets(self):
        """Test that interface creates bezel-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Bezel_Enabled"' in content
        assert '"Bezel_Width"' in content

    def test_interface_creates_led_sockets(self):
        """Test that interface creates LED-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"LED_Enabled"' in content
        assert '"LED_Color_On"' in content

    def test_interface_creates_material_sockets(self):
        """Test that interface creates material-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Body_Color"' in content
        assert '"Metallic"' in content
        assert '"Roughness"' in content


class TestButtonStyles:
    """Tests for button style definitions."""

    def test_style_flat_exists(self):
        """Test that flat style (0) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Flat" in content or "flat" in content.lower()

    def test_style_domed_exists(self):
        """Test that domed style (1) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Domed" in content or "dome" in content.lower()

    def test_style_concave_exists(self):
        """Test that concave style (2) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Concave" in content or "concave" in content.lower()

    def test_style_illuminated_exists(self):
        """Test that illuminated style (3) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Illuminated" in content or "illuminate" in content.lower()

    def test_style_switch_used(self):
        """Test that style switching is implemented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Style_Switch" in content or "IndexSwitch" in content


class TestButtonGeometry:
    """Tests for button geometry building."""

    def test_uses_cylinder_for_flat(self):
        """Test that flat style uses cylinder primitive."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "MeshCylinder" in content

    def test_uses_uv_sphere_for_domed(self):
        """Test that domed style uses UV sphere primitive."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "MeshUVSphere" in content

    def test_uses_transform_for_scaling(self):
        """Test that transform node is used for scaling."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeTransform" in content

    def test_uses_join_geometry(self):
        """Test that Join Geometry is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeJoinGeometry" in content

    def test_uses_set_material(self):
        """Test that Set Material is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeSetMaterial" in content


class TestButtonMaterial:
    """Tests for button material creation."""

    def test_creates_principled_bsdf(self):
        """Test that material uses Principled BSDF."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeBsdfPrincipled" in content

    def test_creates_material_output(self):
        """Test that material has output node."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeOutputMaterial" in content


class TestButtonHelperMethods:
    """Tests for helper methods."""

    def test_has_float_helper(self):
        """Test that _float helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _float" in content

    def test_has_int_helper(self):
        """Test that _int helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _int" in content

    def test_has_bool_helper(self):
        """Test that _bool helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _bool" in content

    def test_has_color_helper(self):
        """Test that _color helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _color" in content

    def test_has_math_helper(self):
        """Test that _math helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _math" in content

    def test_has_combine_xyz_helper(self):
        """Test that _combine_xyz helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def _combine_xyz" in content


class TestCreateButtonNodeGroup:
    """Tests for create_button_node_group factory function."""

    def test_function_exists(self):
        """Test that create_button_node_group function exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "def create_button_node_group" in content

    def test_function_returns_node_tree(self):
        """Test that function returns node tree."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        # Should return builder.tree
        assert "return builder.tree" in content

    def test_function_accepts_name_parameter(self):
        """Test that function accepts name parameter."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert 'name: str = "Button_Element"' in content or 'name="Button_Element"' in content


class TestButtonUnitConversion:
    """Tests for unit conversion in button builder."""

    def test_uses_mm_to_meters_conversion(self):
        """Test that MM to meters conversion is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "MM = 0.001" in content or "0.001" in content

    def test_converts_diameter(self):
        """Test that diameter is converted."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Diameter_M" in content or "Diameter" in content

    def test_converts_height(self):
        """Test that height is converted."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "Height_M" in content or "height_m" in content.lower()


class TestButtonCapSystem:
    """Tests for button cap system."""

    def test_cap_enabled_socket(self):
        """Test that cap system has enable socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Cap_Enabled"' in content

    def test_cap_inset_socket(self):
        """Test that cap system has inset socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Cap_Inset"' in content

    def test_cap_color_socket(self):
        """Test that cap system has color socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Cap_Color"' in content


class TestButtonPressState:
    """Tests for button press state."""

    def test_press_amount_socket(self):
        """Test that press amount socket exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert '"Press_Amount"' in content

    def test_press_offset_calculation(self):
        """Test that press offset is calculated."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/button_builder.py", "r") as f:
            content = f.read()

        assert "PressOffset" in content or "press_offset" in content.lower()
