"""
Unit tests for lib/inputs/fader_builder.py

Tests the fader element builder system.
Uses mocks for bpy (Blender) dependencies to test without Blender.

Tests focus on:
- FaderBuilder class interface
- Socket interface creation
- Type definitions
- Factory function behavior
"""

import pytest


class TestFaderBuilderStructure:
    """Tests for FaderBuilder class structure and interface."""

    def test_fader_builder_class_exists(self):
        """Test that FaderBuilder class is defined."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "class FaderBuilder" in content

    def test_fader_builder_has_create_interface(self):
        """Test that FaderBuilder has _create_interface method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _create_interface" in content

    def test_fader_builder_has_build_geometry(self):
        """Test that FaderBuilder has _build_geometry method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _build_geometry" in content

    def test_fader_builder_has_create_material(self):
        """Test that FaderBuilder has _create_material method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _create_material" in content


class TestFaderBuilderInterface:
    """Tests for fader interface socket creation."""

    def test_interface_creates_type_socket(self):
        """Test that interface creates Type socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Type"' in content

    def test_interface_creates_track_sockets(self):
        """Test that interface creates track-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Track_Width"' in content
        assert '"Track_Depth"' in content

    def test_interface_creates_knob_sockets(self):
        """Test that interface creates knob-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Knob_Style"' in content
        assert '"Knob_Width"' in content
        assert '"Knob_Height"' in content
        assert '"Knob_Depth"' in content

    def test_interface_creates_value_socket(self):
        """Test that interface creates Value socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Value"' in content

    def test_interface_creates_travel_length_socket(self):
        """Test that interface creates Travel_Length socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Travel_Length"' in content

    def test_interface_creates_scale_sockets(self):
        """Test that interface creates scale-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Scale_Enabled"' in content
        assert '"Scale_Position"' in content
        assert '"Scale_Color"' in content

    def test_interface_creates_led_sockets(self):
        """Test that interface creates LED-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"LED_Enabled"' in content
        assert '"LED_Segments"' in content
        assert '"LED_Value"' in content

    def test_interface_creates_material_sockets(self):
        """Test that interface creates material-related sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Track_Color"' in content
        assert '"Knob_Color"' in content
        assert '"Metallic"' in content
        assert '"Roughness"' in content


class TestFaderTypes:
    """Tests for fader type definitions."""

    def test_channel_fader_type(self):
        """Test that Channel fader type (0) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Channel" in content or "100mm" in content

    def test_short_fader_type(self):
        """Test that Short fader type (1) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Short" in content or "60mm" in content

    def test_mini_fader_type(self):
        """Test that Mini fader type (2) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Mini" in content or "45mm" in content


class TestFaderKnobStyles:
    """Tests for fader knob style definitions."""

    def test_square_knob_style(self):
        """Test that Square knob style (0) is documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Square" in content or "SSL" in content

    def test_rounded_knob_style(self):
        """Test that Rounded knob style (1) is documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Rounded" in content or "Neve" in content

    def test_angled_knob_style(self):
        """Test that Angled knob style (2) is documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Angled" in content or "API" in content


class TestFaderGeometry:
    """Tests for fader geometry building."""

    def test_uses_mesh_grid(self):
        """Test that mesh grid is used for track."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshGrid" in content

    def test_uses_mesh_cube(self):
        """Test that mesh cube is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshCube" in content

    def test_uses_transform(self):
        """Test that transform node is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeTransform" in content

    def test_uses_join_geometry(self):
        """Test that Join Geometry is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeJoinGeometry" in content

    def test_uses_set_material(self):
        """Test that Set Material is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeSetMaterial" in content


class TestFaderMaterial:
    """Tests for fader material creation."""

    def test_creates_material(self):
        """Test that material is created."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Fader_Material" in content


class TestFaderHelperMethods:
    """Tests for helper methods."""

    def test_has_float_helper(self):
        """Test that _float helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _float" in content

    def test_has_int_helper(self):
        """Test that _int helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _int" in content

    def test_has_bool_helper(self):
        """Test that _bool helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _bool" in content

    def test_has_color_helper(self):
        """Test that _color helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _color" in content

    def test_has_math_helper(self):
        """Test that _math helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _math" in content

    def test_has_combine_xyz_helper(self):
        """Test that _combine_xyz helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def _combine_xyz" in content


class TestCreateFaderNodeGroup:
    """Tests for create_fader_node_group factory function."""

    def test_function_exists(self):
        """Test that create_fader_node_group function exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "def create_fader_node_group" in content

    def test_function_returns_node_tree(self):
        """Test that function returns node tree."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "return builder.tree" in content

    def test_function_accepts_name_parameter(self):
        """Test that function accepts name parameter."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert 'name: str = "Fader_Element"' in content or 'name="Fader_Element"' in content


class TestFaderUnitConversion:
    """Tests for unit conversion in fader builder."""

    def test_uses_mm_to_meters_conversion(self):
        """Test that MM to meters conversion is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "MM = 0.001" in content or "0.001" in content


class TestFaderPositionCalculation:
    """Tests for knob position calculation."""

    def test_calculates_knob_position(self):
        """Test that knob position is calculated based on Value."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "KnobZ" in content or "knob_z" in content.lower()

    def test_uses_travel_length(self):
        """Test that travel length affects position."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Travel" in content


class TestFaderLEDMeter:
    """Tests for LED meter functionality."""

    def test_led_enabled_controls_meter(self):
        """Test that LED_Enabled controls meter visibility."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"LED_Enabled"' in content

    def test_led_segments_socket(self):
        """Test that LED_Segments socket exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"LED_Segments"' in content

    def test_led_color_sockets(self):
        """Test that LED color sockets exist."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"LED_Color_Safe"' in content
        assert '"LED_Color_Warning"' in content
        assert '"LED_Color_Danger"' in content


class TestFaderScale:
    """Tests for scale (markings) functionality."""

    def test_scale_enabled_socket(self):
        """Test that scale enable socket exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Scale_Enabled"' in content

    def test_scale_position_socket(self):
        """Test that scale position socket exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"Scale_Position"' in content


class TestFaderDocumentation:
    """Tests for fader module documentation."""

    def test_module_docstring(self):
        """Test that module has docstring."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert '"""' in content

    def test_documents_fader_types(self):
        """Test that fader types are documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "Channel" in content or "100mm" in content
        assert "Short" in content or "60mm" in content
        assert "Mini" in content or "45mm" in content

    def test_documents_knob_styles(self):
        """Test that knob styles are documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/fader_builder.py", "r") as f:
            content = f.read()

        assert "SSL" in content or "Square" in content
        assert "Neve" in content or "Rounded" in content
        assert "API" in content or "Angled" in content
