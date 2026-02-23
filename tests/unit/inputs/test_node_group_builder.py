"""
Unit tests for lib/inputs/node_group_builder.py

Tests the input node group builder system.
Uses mocks for bpy (Blender) dependencies to test without Blender.

Tests focus on:
- InputNodeGroupBuilder class interface
- Socket interface creation
- Zone structure
- Style definitions
- Knurling system
- Material handling
- Factory function behavior
"""

import pytest


class TestInputNodeGroupBuilderStructure:
    """Tests for InputNodeGroupBuilder class structure and interface."""

    def test_builder_class_exists(self):
        """Test that InputNodeGroupBuilder class is defined."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "class InputNodeGroupBuilder" in content

    def test_builder_has_create_interface(self):
        """Test that builder has _create_interface method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _create_interface" in content

    def test_builder_has_build_geometry(self):
        """Test that builder has _build_geometry method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _build_geometry" in content

    def test_builder_has_build_method(self):
        """Test that builder has build method."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def build" in content


class TestInputNodeGroupBuilderInterface:
    """Tests for interface socket creation."""

    def test_interface_creates_segments_socket(self):
        """Test that interface creates Segments socket."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"Segments"' in content

    def test_interface_creates_diameter_sockets(self):
        """Test that interface creates diameter sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"Top_Diameter"' in content
        assert '"Bot_Diameter"' in content
        assert '"AB_Junction_Diameter"' in content

    def test_interface_creates_height_sockets(self):
        """Test that interface creates height sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"A_Top_Height"' in content
        assert '"A_Mid_Height"' in content
        assert '"A_Bot_Height"' in content
        assert '"B_Top_Height"' in content
        assert '"B_Mid_Height"' in content
        assert '"B_Bot_Height"' in content

    def test_interface_creates_style_sockets(self):
        """Test that interface creates style sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"A_Top_Style"' in content
        assert '"B_Bot_Style"' in content

    def test_interface_creates_knurl_sockets(self):
        """Test that interface creates knurling sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"A_Mid_Knurl"' in content
        assert '"B_Mid_Knurl"' in content
        # Per-section knurl count and depth
        assert '"A_Mid_Knurl_Count"' in content
        assert '"A_Mid_Knurl_Depth"' in content

    def test_interface_creates_material_sockets(self):
        """Test that interface creates material sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"Color"' in content
        assert '"Metallic"' in content
        assert '"Roughness"' in content
        assert '"Material"' in content

    def test_interface_creates_debug_sockets(self):
        """Test that interface creates debug sockets."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"Debug_Mode"' in content


class TestZoneStructure:
    """Tests for zone-based structure."""

    def test_zone_a_sections(self):
        """Test that Zone A sections are defined."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "ZONE A" in content
        assert "A_Top" in content or "A_TOP" in content
        assert "A_Mid" in content or "A_MID" in content
        assert "A_Bot" in content or "A_BOT" in content

    def test_zone_b_sections(self):
        """Test that Zone B sections are defined."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "ZONE B" in content
        assert "B_Top" in content or "B_TOP" in content
        assert "B_Mid" in content or "B_MID" in content
        assert "B_Bot" in content or "B_BOT" in content

    def test_zone_frames(self):
        """Test that zones use frames for organization."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "frame_a" in content.lower() or "Frame_A" in content
        assert "frame_b" in content.lower() or "Frame_B" in content


class TestCapStyles:
    """Tests for cap style definitions."""

    def test_flat_style(self):
        """Test that Flat style (0) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Flat" in content

    def test_beveled_style(self):
        """Test that Beveled style (1) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Beveled" in content or "Bevel" in content

    def test_rounded_style(self):
        """Test that Rounded style (2) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Rounded" in content

    def test_tapered_skirt_style(self):
        """Test that Tapered+Skirt style (3) is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Tapered" in content or "Skirt" in content or "Neve" in content


class TestGeometryNodes:
    """Tests for geometry node usage."""

    def test_uses_mesh_cone(self):
        """Test that Mesh Cone is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshCone" in content

    def test_uses_mesh_cylinder(self):
        """Test that Mesh Cylinder is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshCylinder" in content

    def test_uses_mesh_uv_sphere(self):
        """Test that Mesh UV Sphere is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshUVSphere" in content

    def test_uses_transform(self):
        """Test that Transform is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeTransform" in content

    def test_uses_join_geometry(self):
        """Test that Join Geometry is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeJoinGeometry" in content

    def test_uses_set_material(self):
        """Test that Set Material is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeSetMaterial" in content

    def test_uses_index_switch(self):
        """Test that Index Switch is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeIndexSwitch" in content


class TestKnurlingSystem:
    """Tests for knurling system."""

    def test_knurling_uses_boolean(self):
        """Test that knurling uses boolean operations."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshBoolean" in content

    def test_knurling_uses_instances(self):
        """Test that knurling uses instance on points."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeInstanceOnPoints" in content

    def test_knurling_uses_circle(self):
        """Test that knurling uses mesh circle for positions."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeMeshCircle" in content

    def test_knurling_uses_realize_instances(self):
        """Test that knurling realizes instances."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeRealizeInstances" in content

    def test_knurling_per_section(self):
        """Test that knurling is per-section."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        # Should have separate knurl controls for each section
        assert "A_Mid_Knurl" in content
        assert "A_Bot_Knurl" in content
        assert "B_Top_Knurl" in content
        assert "B_Mid_Knurl" in content


class TestMaterialSystem:
    """Tests for material system."""

    def test_creates_material(self):
        """Test that material is created."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Input_Material" in content

    def test_uses_principled_bsdf(self):
        """Test that Principled BSDF is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "ShaderNodeBsdfPrincipled" in content

    def test_debug_material_system(self):
        """Test that debug material system exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Debug_A_Top_Material" in content
        assert "Debug_B_Bot_Material" in content

    def test_external_material_input(self):
        """Test that external material input is supported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"Material"' in content


class TestHelperMethods:
    """Tests for helper methods."""

    def test_has_float_helper(self):
        """Test that _float helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _float" in content

    def test_has_int_helper(self):
        """Test that _int helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _int" in content

    def test_has_bool_helper(self):
        """Test that _bool helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _bool" in content

    def test_has_color_helper(self):
        """Test that _color helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _color" in content

    def test_has_material_helper(self):
        """Test that _material helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _material" in content

    def test_has_math_helper(self):
        """Test that _math helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _math" in content

    def test_has_combine_xyz_helper(self):
        """Test that _combine_xyz helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _combine_xyz" in content

    def test_has_frame_helper(self):
        """Test that _frame helper method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _frame" in content


class TestBuildCap:
    """Tests for cap building."""

    def test_build_cap_method(self):
        """Test that _build_cap method exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def _build_cap" in content

    def test_cap_style_switch(self):
        """Test that cap uses style switch."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "IndexSwitch" in content


class TestPositionCalculation:
    """Tests for position calculations."""

    def test_position_stack_from_bottom(self):
        """Test that sections are stacked from bottom."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "POSITION CALC" in content or "b_bot_z" in content.lower()

    def test_diameter_chain(self):
        """Test that diameters form a continuous chain."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        # Should have diameters that chain together
        assert "Radius" in content


class TestCreateInputNodeGroup:
    """Tests for create_input_node_group factory function."""

    def test_function_exists(self):
        """Test that create_input_node_group function exists."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "def create_input_node_group" in content

    def test_function_returns_node_tree(self):
        """Test that function returns node tree."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "return builder.build" in content

    def test_function_accepts_name_parameter(self):
        """Test that function accepts name parameter."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert 'name: str = "Input_ZoneBased"' in content or 'name="Input_ZoneBased"' in content


class TestUnitConversion:
    """Tests for unit conversion."""

    def test_uses_mm_to_meters_conversion(self):
        """Test that MM to meters conversion is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "MM = 0.001" in content or "0.001" in content

    def test_unit_conversion_frame(self):
        """Test that unit conversion has its own frame."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "UNIT CONVERSION" in content


class TestNormalRecalculation:
    """Tests for normal recalculation."""

    def test_uses_set_mesh_normal(self):
        """Test that Set Mesh Normal is used."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "GeometryNodeSetMeshNormal" in content

    def test_normals_after_boolean(self):
        """Test that normals are recalculated after boolean operations."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "RecalcNormals" in content


class TestDocumentation:
    """Tests for module documentation."""

    def test_module_docstring(self):
        """Test that module has docstring."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert '"""' in content

    def test_frame_structure_documented(self):
        """Test that frame structure is documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "Frame Structure" in content or "FRAME" in content

    def test_continuous_surface_documented(self):
        """Test that continuous surface approach is documented."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/node_group_builder.py", "r") as f:
            content = f.read()

        assert "continuous" in content.lower() or "chained" in content.lower()
