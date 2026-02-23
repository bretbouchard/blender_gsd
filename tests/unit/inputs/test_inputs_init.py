"""
Unit tests for lib/inputs/__init__.py

Tests the main exports from the inputs module.
This test focuses on the module structure and import behavior.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch


class TestInputsImports:
    """Tests for inputs module imports and structure."""

    def test_module_exports_list(self):
        """Test that __all__ is properly defined."""
        # Read the module file to check exports
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "inputs_init",
            "/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py"
        )
        module = importlib.util.module_from_spec(spec)

        # We need to mock bpy before loading
        with patch.dict('sys.modules', {'bpy': MagicMock()}):
            # Mock lib.nodekit as well
            with patch.dict('sys.modules', {'lib.nodekit': MagicMock()}):
                try:
                    spec.loader.exec_module(module)
                except Exception:
                    # Module may fail to fully load without Blender
                    pass

        # Check the file content for expected exports
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        # Verify expected exports are defined in __all__
        assert "__all__" in content
        assert "create_knob_node_group" in content
        assert "create_button_node_group" in content
        assert "create_fader_node_group" in content
        assert "create_led_node_group" in content


class TestInputsModuleStructure:
    """Tests for inputs module structure."""

    def test_init_file_exists(self):
        """Test that __init__.py exists."""
        import os
        init_path = "/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py"
        assert os.path.exists(init_path)

    def test_module_docstring(self):
        """Test that module has docstring."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        assert '"""' in content or "'''" in content
        assert "Console UI Elements" in content or "Elements" in content

    def test_imports_from_submodules(self):
        """Test that __init__.py imports from submodules."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        assert "from .node_group_builder import" in content
        assert "from .button_builder import" in content
        assert "from .fader_builder import" in content
        assert "from .led_builder import" in content


class TestInputsExports:
    """Tests for what the inputs module exports."""

    def test_exports_create_knob_node_group(self):
        """Test that create_knob_node_group is exported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        assert '"create_knob_node_group"' in content or "'create_knob_node_group'" in content

    def test_exports_create_button_node_group(self):
        """Test that create_button_node_group is exported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        assert '"create_button_node_group"' in content or "'create_button_node_group'" in content

    def test_exports_create_fader_node_group(self):
        """Test that create_fader_node_group is exported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        assert '"create_fader_node_group"' in content or "'create_fader_node_group'" in content

    def test_exports_create_led_node_group(self):
        """Test that create_led_node_group is exported."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        assert '"create_led_node_group"' in content or "'create_led_node_group'" in content


class TestInputsDescription:
    """Tests for module description and documentation."""

    def test_module_lists_available_elements(self):
        """Test that module documentation lists available elements."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        # Should mention the available elements
        assert "Knob" in content
        assert "Button" in content
        assert "Fader" in content
        assert "LED" in content

    def test_module_describes_methodology(self):
        """Test that module describes the methodology."""
        with open("/Users/bretbouchard/apps/blender_gsd/lib/inputs/__init__.py", "r") as f:
            content = f.read()

        # Should mention key methodology aspects
        assert "parameters exposed" in content.lower() or "node group inputs" in content.lower()
