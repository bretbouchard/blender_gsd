"""
Unit tests for lib/dev/templates.py

Tests the Module Template Generator including:
- ModuleConfig dataclass
- ModuleTemplate class
- create_module convenience function
- list_features function
- generate_hud_class function
- create_from_template function
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from lib.dev.templates import (
    ModuleConfig,
    ModuleTemplate,
    create_module,
    list_features,
    generate_hud_class,
    create_from_template,
    EXAMPLE_TEMPLATES,
)


class TestModuleConfig:
    """Tests for ModuleConfig dataclass."""

    def test_default_values(self):
        """Test ModuleConfig default values."""
        config = ModuleConfig(name="test", class_name="Test")
        assert config.name == "test"
        assert config.class_name == "Test"
        assert config.description == ""
        assert config.features == set()
        assert config.knowledge_refs == []
        assert config.author == ""
        assert config.version == "1.0.0"

    def test_custom_values(self):
        """Test ModuleConfig with custom values."""
        config = ModuleConfig(
            name="my_effect",
            class_name="MyEffect",
            description="A cool effect",
            features={"nodekit", "hud"},
            knowledge_refs=["Section 1"],
            author="Test Author",
            version="2.0.0"
        )
        assert config.description == "A cool effect"
        assert "nodekit" in config.features
        assert config.author == "Test Author"
        assert config.version == "2.0.0"


class TestModuleTemplate:
    """Tests for ModuleTemplate class."""

    def test_initialization_snake_case(self):
        """Test initialization with snake_case name."""
        template = ModuleTemplate("my_effect")
        assert template.config.name == "my_effect"
        assert template.config.class_name == "MyEffect"

    def test_initialization_camel_case(self):
        """Test initialization with CamelCase name."""
        template = ModuleTemplate("MyEffect")
        assert template.config.name == "my_effect"
        assert template.config.class_name == "MyEffect"

    def test_initialization_with_spaces(self):
        """Test initialization with spaced name."""
        template = ModuleTemplate("my cool effect")
        # Note: The _to_snake_case doesn't handle spaces, just camelCase
        assert template.config.name == "my cool effect"
        # Capitalizes each word, preserving spaces
        assert template.config.class_name == "My cool effect"

    def test_to_snake_case(self):
        """Test _to_snake_case conversion."""
        template = ModuleTemplate("Test")
        assert template._to_snake_case("MyEffect") == "my_effect"
        assert template._to_snake_case("my_effect") == "my_effect"
        assert template._to_snake_case("MyXMLParser") == "my_xml_parser"

    def test_to_class_name(self):
        """Test _to_class_name conversion."""
        template = ModuleTemplate("Test")
        assert template._to_class_name("my_effect") == "MyEffect"
        assert template._to_class_name("MyEffect") == "MyEffect"

    def test_set_description(self):
        """Test set_description method."""
        template = ModuleTemplate("test")
        result = template.set_description("Test description")
        assert result is template
        assert template.config.description == "Test description"

    def test_set_author(self):
        """Test set_author method."""
        template = ModuleTemplate("test")
        result = template.set_author("Test Author")
        assert result is template
        assert template.config.author == "Test Author"

    def test_set_version(self):
        """Test set_version method."""
        template = ModuleTemplate("test")
        result = template.set_version("2.0.0")
        assert result is template
        assert template.config.version == "2.0.0"

    def test_add_feature(self):
        """Test add_feature method."""
        template = ModuleTemplate("test")
        result = template.add_feature("nodekit")
        assert result is template
        assert "nodekit" in template.config.features

    def test_add_feature_unknown(self):
        """Test add_feature with unknown feature raises."""
        template = ModuleTemplate("test")
        with pytest.raises(ValueError):
            template.add_feature("unknown_feature")

    def test_add_feature_hud_adds_nodekit(self):
        """Test that adding 'hud' feature also adds 'nodekit'."""
        template = ModuleTemplate("test")
        template.add_feature("hud")
        assert "nodekit" in template.config.features
        assert "hud" in template.config.features

    def test_add_feature_closure_adds_nodekit(self):
        """Test that adding 'closure' feature also adds 'nodekit'."""
        template = ModuleTemplate("test")
        template.add_feature("closure")
        assert "nodekit" in template.config.features
        assert "closure" in template.config.features

    def test_add_features(self):
        """Test add_features method."""
        template = ModuleTemplate("test")
        result = template.add_features("nodekit", "hud", "presets")
        assert result is template
        assert "nodekit" in template.config.features
        assert "hud" in template.config.features
        assert "presets" in template.config.features

    def test_add_knowledge_ref(self):
        """Test add_knowledge_ref method."""
        template = ModuleTemplate("test")
        result = template.add_knowledge_ref("Section 1: Intro")
        assert result is template
        assert "Section 1: Intro" in template.config.knowledge_refs

    def test_available_features(self):
        """Test that AVAILABLE_FEATURES contains expected features."""
        assert "nodekit" in ModuleTemplate.AVAILABLE_FEATURES
        assert "hud" in ModuleTemplate.AVAILABLE_FEATURES
        assert "presets" in ModuleTemplate.AVAILABLE_FEATURES
        assert "bake" in ModuleTemplate.AVAILABLE_FEATURES
        assert "closure" in ModuleTemplate.AVAILABLE_FEATURES
        assert "bundle" in ModuleTemplate.AVAILABLE_FEATURES


class TestModuleTemplateGeneration:
    """Tests for code generation."""

    def test_generate_basic(self):
        """Test basic code generation."""
        template = ModuleTemplate("test_effect")
        code = template.generate()
        assert "class TestEffect:" in code
        assert "def create" in code
        assert "def build" in code

    def test_generate_with_description(self):
        """Test code generation with description."""
        template = ModuleTemplate("test")
        template.set_description("A test module")
        code = template.generate()
        assert "A test module" in code

    def test_generate_with_nodekit(self):
        """Test code generation with nodekit feature."""
        template = ModuleTemplate("test")
        template.add_feature("nodekit")
        code = template.generate()
        assert "NodeKit" in code
        assert "GeometryNodeTree" in code
        assert "group_input" in code
        assert "group_output" in code

    def test_generate_with_hud(self):
        """Test code generation with HUD feature."""
        template = ModuleTemplate("test")
        template.add_feature("hud")
        code = template.generate()
        assert "class TestHUD:" in code
        assert "display_settings" in code
        assert "display_checklist" in code

    def test_generate_with_presets(self):
        """Test code generation with presets feature."""
        template = ModuleTemplate("test")
        template.add_feature("presets")
        code = template.generate()
        assert "class TestPresets:" in code
        assert "def default" in code
        assert "def high_quality" in code

    def test_generate_with_bake(self):
        """Test code generation with bake feature."""
        template = ModuleTemplate("test")
        template.add_feature("bake")
        code = template.generate()
        assert "class TestBaker:" in code
        assert "def bake" in code
        assert "def load_cache" in code

    def test_generate_with_closure(self):
        """Test code generation with closure feature."""
        template = ModuleTemplate("test")
        template.add_feature("closure")
        code = template.generate()
        assert "class TestClosure:" in code
        assert "define_closure" in code

    def test_generate_with_bundle(self):
        """Test code generation with bundle feature."""
        template = ModuleTemplate("test")
        template.add_feature("bundle")
        code = template.generate()
        assert "TEST_BUNDLE" in code
        assert "BundleSchema" in code
        assert "TestBundleBuilder" in code

    def test_generate_with_knowledge_refs(self):
        """Test code generation with knowledge references."""
        template = ModuleTemplate("test")
        template.add_knowledge_ref("Section 1: Intro")
        template.add_knowledge_ref("Section 2: Advanced")
        code = template.generate()
        assert "Section 1: Intro" in code
        assert "Section 2: Advanced" in code
        assert "Cross-references:" in code

    def test_generate_full_featured(self):
        """Test code generation with all features."""
        template = ModuleTemplate("full_test")
        template.set_description("Full featured module")
        template.add_features("nodekit", "hud", "presets", "bake", "closure", "bundle")
        code = template.generate()

        # Check all features are present
        assert "class FullTest:" in code
        assert "class FullTestHUD:" in code
        assert "class FullTestPresets:" in code
        assert "class FullTestBaker:" in code
        assert "class FullTestClosure:" in code
        assert "FULL_TEST_BUNDLE" in code

    def test_generate_convenience_functions(self):
        """Test that convenience functions are generated."""
        template = ModuleTemplate("test")
        code = template.generate()
        assert "def create_test(" in code
        assert "def get_quick_reference" in code


class TestModuleTemplateFileWriting:
    """Tests for file writing functionality."""

    def test_write_to_file(self):
        """Test write_to_file method."""
        template = ModuleTemplate("test")
        template.set_description("Test module")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_module.py")
            template.write_to_file(output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            assert "class Test:" in content
            assert "Test module" in content

    def test_write_to_file_creates_directories(self):
        """Test write_to_file creates parent directories."""
        template = ModuleTemplate("test")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "nested", "test.py")
            template.write_to_file(output_path)

            assert os.path.exists(output_path)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_module_basic(self):
        """Test create_module with basic options."""
        code = create_module("my_effect")
        assert "class MyEffect:" in code

    def test_create_module_with_features(self):
        """Test create_module with features."""
        code = create_module("test", features=["nodekit", "hud"])
        assert "NodeKit" in code
        assert "class TestHUD:" in code

    def test_create_module_with_description(self):
        """Test create_module with description."""
        code = create_module("test", description="A test module")
        assert "A test module" in code

    def test_create_module_with_knowledge_refs(self):
        """Test create_module with knowledge references."""
        code = create_module("test", knowledge_refs=["Section 1"])
        assert "Section 1" in code

    def test_create_module_with_output_path(self):
        """Test create_module writes to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.py")
            code = create_module("test", output_path=output_path)

            assert os.path.exists(output_path)
            assert "class Test:" in code

    def test_list_features(self):
        """Test list_features function."""
        features = list_features()
        assert isinstance(features, dict)
        assert "nodekit" in features
        assert "hud" in features

    def test_generate_hud_class(self):
        """Test generate_hud_class function."""
        code = generate_hud_class("my_effect")
        assert "class MyEffectHUD:" in code
        assert "display_settings" in code

    def test_create_from_template(self):
        """Test create_from_template function."""
        code = create_from_template("basic_geometry_nodes", "my_test")
        assert "class MyTest:" in code
        assert "NodeKit" in code

    def test_create_from_template_unknown(self):
        """Test create_from_template with unknown template raises."""
        with pytest.raises(ValueError):
            create_from_template("unknown_template", "test")

    def test_create_from_template_full_featured(self):
        """Test create_from_template with full_featured template."""
        code = create_from_template("full_featured", "test")
        assert "class Test:" in code
        assert "class TestHUD:" in code
        assert "class TestPresets:" in code
        assert "class TestBaker:" in code

    def test_create_from_template_blender_50(self):
        """Test create_from_template with blender_50_bundle template."""
        code = create_from_template("blender_50_bundle", "test")
        assert "class Test:" in code
        assert "TEST_BUNDLE" in code
        assert "class TestClosure:" in code


class TestExampleTemplates:
    """Tests for EXAMPLE_TEMPLATES."""

    def test_templates_exist(self):
        """Test that expected templates exist."""
        assert "basic_geometry_nodes" in EXAMPLE_TEMPLATES
        assert "full_featured" in EXAMPLE_TEMPLATES
        assert "material_effect" in EXAMPLE_TEMPLATES
        assert "blender_50_bundle" in EXAMPLE_TEMPLATES

    def test_template_structure(self):
        """Test that templates have required keys."""
        for name, config in EXAMPLE_TEMPLATES.items():
            assert "features" in config
            assert "description" in config
            assert isinstance(config["features"], list)


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_name(self):
        """Test with empty name."""
        template = ModuleTemplate("")
        assert template.config.name == ""
        assert template.config.class_name == ""

    def test_single_character_name(self):
        """Test with single character name."""
        template = ModuleTemplate("a")
        assert template.config.name == "a"
        assert template.config.class_name == "A"

    def test_numbers_in_name(self):
        """Test with numbers in name."""
        template = ModuleTemplate("effect2d")
        assert template.config.name == "effect2d"
        # Note: capitalize() only capitalizes first letter
        assert template.config.class_name == "Effect2d"

    def test_special_characters(self):
        """Test with special characters in description."""
        template = ModuleTemplate("test")
        template.set_description("Test with 'quotes' and \"double quotes\" and $pecial")
        code = template.generate()
        assert "Test with 'quotes'" in code

    def test_unicode_description(self):
        """Test with unicode in description."""
        template = ModuleTemplate("test")
        template.set_description("Test with unicode: \u00e9\u00e8\u00ea")
        code = template.generate()
        assert "\u00e9\u00e8\u00ea" in code

    def test_duplicate_features(self):
        """Test adding duplicate features."""
        template = ModuleTemplate("test")
        template.add_feature("nodekit")
        template.add_feature("nodekit")
        # Should only have one instance
        assert len([f for f in template.config.features if f == "nodekit"]) == 1

    def test_feature_dependency_chain(self):
        """Test feature dependency chain (hud -> nodekit)."""
        template = ModuleTemplate("test")
        template.add_feature("hud")
        # hud should add nodekit
        assert "nodekit" in template.config.features
        assert "hud" in template.config.features

    def test_generate_without_nodekit(self):
        """Test generation without nodekit feature."""
        template = ModuleTemplate("test")
        # Don't add nodekit
        code = template.generate()
        # Should still work, just without NodeKit references
        assert "class Test:" in code
        # Should use material-based approach instead
        assert "_material" in code
