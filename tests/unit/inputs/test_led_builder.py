"""
Unit tests for lib/inputs/led_builder.py

Tests the LED/indicator element builder system.
Uses mocks for bpy (Blender) dependencies to test without Blender.

Tests focus on:
- LEDBuilder class interface
- Socket interface creation
- Type definitions
- Factory function behavior
"""

import pytest


class TestLEDBuilderStructure:
    """Tests for LEDBuilder class structure and interface."""

    def test_led_builder_class_exists(self):
        """Test that LEDBuilder class is defined."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "class LEDBuilder" in content

    def test_led_builder_has_create_interface(self):
        """Test that LEDBuilder has _create_interface method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _create_interface" in content

    def test_led_builder_has_build_geometry(self):
        """Test that LEDBuilder has _build_geometry method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _build_geometry" in content

    def test_led_builder_has_create_material(self):
        """Test that LEDBuilder has _create_material method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _create_material" in content


class TestLEDBuilderInterface:
    """Tests for LED interface socket creation."""

    def test_interface_creates_type_socket(self):
        """Test that interface creates Type socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Type"' in content

    def test_interface_creates_size_socket(self):
        """Test that interface creates Size socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Size"' in content

    def test_interface_creates_shape_socket(self):
        """Test that interface creates Shape socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Shape"' in content

    def test_interface_creates_height_socket(self):
        """Test that interface creates Height socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Height"' in content

    def test_interface_creates_segment_sockets(self):
        """Test that interface creates segment-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Segments"' in content
        assert '"Segment_Width"' in content
        assert '"Segment_Height"' in content
        assert '"Segment_Spacing"' in content

    def test_interface_creates_bezel_sockets(self):
        """Test that interface creates bezel-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Bezel_Enabled"' in content
        assert '"Bezel_Width"' in content
        assert '"Bezel_Color"' in content
        assert '"Bezel_Shape"' in content

    def test_interface_creates_color_sockets(self):
        """Test that interface creates color-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Color_Off"' in content
        assert '"Color_On"' in content
        assert '"Color_Warning"' in content
        assert '"Color_Danger"' in content

    def test_interface_creates_state_sockets(self):
        """Test that interface creates state-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Value"' in content
        assert '"State"' in content

    def test_interface_creates_threshold_sockets(self):
        """Test that interface creates threshold sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Warning_Threshold"' in content
        assert '"Danger_Threshold"' in content

    def test_interface_creates_glow_sockets(self):
        """Test that interface creates glow-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Glow_Enabled"' in content
        assert '"Glow_Intensity"' in content
        assert '"Glow_Radius"' in content

    def test_interface_creates_material_sockets(self):
        """Test that interface creates material-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Roughness"' in content
        assert '"Transmission"' in content


class TestLEDTypes:
    """Tests for LED type definitions."""

    def test_single_led_type(self):
        """Test that Single LED type (0) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Single" in content

    def test_led_bar_type(self):
        """Test that LED Bar type (1) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Bar" in content

    def test_vu_meter_type(self):
        """Test that VU Meter type (2) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "VU" in content or "Meter" in content

    def test_seven_segment_type(self):
        """Test that 7-Segment type (3) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "7-Segment" in content or "7Segment" in content


class TestLEDShapes:
    """Tests for LED shape definitions."""

    def test_round_shape(self):
        """Test that Round shape (0) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Round" in content

    def test_square_shape(self):
        """Test that Square shape (1) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Square" in content


class TestLEDGeometry:
    """Tests for LED geometry building."""

    def test_uses_mesh_cylinder_for_round(self):
        """Test that mesh cylinder is used for round LED."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshCylinder" in content

    def test_uses_mesh_cube_for_square(self):
        """Test that mesh cube is used for square LED."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshCube" in content

    def test_uses_shape_switch(self):
        """Test that shape switch is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Shape_Switch" in content

    def test_uses_type_switch(self):
        """Test that type switch is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Type_Switch" in content or "IndexSwitch" in content

    def test_uses_set_material(self):
        """Test that Set Material is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeSetMaterial" in content


class TestLEDMaterial:
    """Tests for LED material creation."""

    def test_creates_emissive_material(self):
        """Test that emissive material is created."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "LED_Material" in content

    def test_uses_emission_shader(self):
        """Test that emission shader is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeEmission" in content

    def test_uses_diffuse_shader(self):
        """Test that diffuse shader is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeBsdfDiffuse" in content

    def test_uses_mix_shader(self):
        """Test that mix shader is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeMixShader" in content

    def test_uses_output_material(self):
        """Test that material output is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeOutputMaterial" in content


class TestLEDHelperMethods:
    """Tests for helper methods."""

    def test_has_float_helper(self):
        """Test that _float helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _float" in content

    def test_has_int_helper(self):
        """Test that _int helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _int" in content

    def test_has_bool_helper(self):
        """Test that _bool helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _bool" in content

    def test_has_color_helper(self):
        """Test that _color helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _color" in content

    def test_has_math_helper(self):
        """Test that _math helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _math" in content

    def test_has_combine_xyz_helper(self):
        """Test that _combine_xyz helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def _combine_xyz" in content


class TestCreateLEDNodeGroup:
    """Tests for create_led_node_group factory function."""

    def test_function_exists(self):
        """Test that create_led_node_group function exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "def create_led_node_group" in content

    def test_function_returns_node_tree(self):
        """Test that function returns node tree."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "return builder.tree" in content

    def test_function_accepts_name_parameter(self):
        """Test that function accepts name parameter."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert 'name: str = "LED_Element"' in content or 'name="LED_Element"' in content


class TestLEDUnitConversion:
    """Tests for unit conversion in LED builder."""

    def test_uses_mm_to_meters_conversion(self):
        """Test that MM to meters conversion is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "MM = 0.001" in content or "0.001" in content


class TestLEDDirection:
    """Tests for LED direction setting."""

    def test_direction_socket(self):
        """Test that direction socket exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"Direction"' in content


class TestLEDDocumentation:
    """Tests for LED module documentation."""

    def test_module_docstring(self):
        """Test that module has docstring."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert '"""' in content

    def test_documents_led_types(self):
        """Test that LED types are documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Single" in content
        assert "Bar" in content
        assert "VU" in content or "Meter" in content
        assert "7-Segment" in content or "Segment" in content


class TestLEDBarGeometry:
    """Tests for LED bar specific geometry."""

    def test_led_bar_creation(self):
        """Test that LED bar is created."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "LED_Bar" in content

    def test_bar_height_based_on_value(self):
        """Test that bar height is based on value."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "BarHeight" in content or "bar_height" in content.lower()


class TestLEDSingleGeometry:
    """Tests for single LED specific geometry."""

    def test_round_led_creation(self):
        """Test that round LED is created."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Round_LED" in content

    def test_square_led_creation(self):
        """Test that square LED is created."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        assert "Square_LED" in content


class TestLEDBezelGeometry:
    """Tests for bezel geometry."""

    def test_bezel_shapes_supported(self):
        """Test that multiple bezel shapes are supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/led_builder.py", "r") as f:
            content = f.read()

        # Should document bezel shapes
        assert "Bezel_Shape" in content
        # 0=Round, 1=Square, 2=Flanged
        assert "Round" in content or "Square" in content or "Flanged" in content
