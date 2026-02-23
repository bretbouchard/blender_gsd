"""
Tests for Outline Parser

Tests YAML/JSON parsing and validation.
"""

import pytest
import tempfile
import os
from lib.orchestrator.outline_parser import (
    OutlineParser,
    ParseResult,
    ParseError,
    ValidationError,
    parse_outline,
    outline_to_yaml,
    outline_to_json,
)


class TestParseResult:
    """Tests for ParseResult dataclass."""

    def test_create_success(self):
        """Test creating successful ParseResult."""
        from lib.orchestrator.types import SceneOutline
        outline = SceneOutline(name="Test")
        result = ParseResult(outline=outline)
        assert result.success is True
        assert result.outline is not None
        assert result.errors == []

    def test_create_failure(self):
        """Test creating failed ParseResult."""
        result = ParseResult(errors=["Error 1", "Error 2"])
        assert result.success is False
        assert result.outline is None
        assert len(result.errors) == 2

    def test_success_property_with_errors(self):
        """Test success property when errors present."""
        from lib.orchestrator.types import SceneOutline
        outline = SceneOutline(name="Test")
        result = ParseResult(outline=outline, errors=["Warning"])
        # Success is False if there are errors
        assert result.success is False


class TestOutlineParser:
    """Tests for OutlineParser class."""

    def test_init(self):
        """Test OutlineParser initialization."""
        parser = OutlineParser()
        assert parser is not None
        assert parser.strict is False

    def test_init_strict(self):
        """Test OutlineParser with strict mode."""
        parser = OutlineParser(strict=True)
        assert parser.strict is True

    def test_parse_valid_yaml(self):
        """Test parsing valid YAML."""
        yaml_content = """
name: Test Scene
scene_type: interior
style: photorealistic
description: A test scene
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)

            assert result.success is True
            assert result.outline is not None
            assert result.outline.name == "Test Scene"

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML."""
        yaml_content = """
name: [broken
scene_type: interior
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)

            assert result.success is False
            assert len(result.errors) > 0

    def test_parse_valid_json_string(self):
        """Test parsing valid JSON string."""
        json_content = '{"name": "JSON Scene", "scene_type": "interior", "style": "photorealistic"}'
        parser = OutlineParser()
        result = parser.parse_json_string(json_content)

        assert result.success is True
        assert result.outline is not None
        assert result.outline.name == "JSON Scene"

    def test_parse_invalid_json_string(self):
        """Test parsing invalid JSON string."""
        json_content = '{"name": "broken'
        parser = OutlineParser()
        result = parser.parse_json_string(json_content)

        assert result.success is False
        assert len(result.errors) > 0

    def test_parse_json_file(self):
        """Test parsing valid JSON file."""
        json_content = '{"name": "JSON Scene", "scene_type": "interior", "style": "photorealistic"}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_json(f.name)
            os.unlink(f.name)

            assert result.success is True
            assert result.outline is not None

    def test_parse_with_dimensions(self):
        """Test parsing with dimensions."""
        yaml_content = """
name: Dimension Test
scene_type: interior
style: photorealistic
dimensions:
  width: 50.0
  height: 5.0
  depth: 40.0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)

            assert result.success is True
            assert result.outline.dimensions is not None
            assert result.outline.dimensions.width == 50.0

    def test_parse_with_lighting(self):
        """Test parsing with lighting requirements."""
        yaml_content = """
name: Lighting Test
scene_type: interior
style: photorealistic
lighting:
  mood: dramatic
  time_of_day: sunset
  intensity: 1.5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)

            assert result.success is True
            assert result.outline.lighting is not None
            assert result.outline.lighting.mood == "dramatic"

    def test_parse_with_camera(self):
        """Test parsing with camera requirements."""
        yaml_content = """
name: Camera Test
scene_type: interior
style: photorealistic
camera:
  focal_length: 85.0
  framing: close-up
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)

            assert result.success is True
            assert result.outline.camera is not None
            assert result.outline.camera.focal_length == 85.0

    def test_parse_with_asset_requirements(self):
        """Test parsing with asset requirements."""
        yaml_content = """
name: Asset Test
scene_type: interior
style: photorealistic
asset_requirements:
  - requirement_id: req_01
    category: furniture
    quantity: 2
  - requirement_id: req_02
    category: props
    quantity: 5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            parser = OutlineParser()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)

            assert result.success is True
            assert len(result.outline.asset_requirements) == 2

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        parser = OutlineParser()
        result = parser.parse_yaml("/nonexistent/path/to/file.yaml")
        assert result.success is False
        assert "not found" in result.errors[0].lower()


class TestValidation:
    """Tests for validation functionality."""

    def test_validate_required_fields(self):
        """Test validation of required fields."""
        parser = OutlineParser()
        # Missing required fields should generate warnings, not errors
        yaml_content = "{}"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)
            # Should still succeed with defaults
            assert result.success is True

    def test_validate_invalid_scene_type(self):
        """Test validation catches invalid scene type."""
        parser = OutlineParser()
        yaml_content = """
name: Test
scene_type: invalid_type
style: photorealistic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)
            # Should fail due to invalid scene type
            assert result.success is False

    def test_validate_invalid_style(self):
        """Test validation catches invalid style."""
        parser = OutlineParser()
        yaml_content = """
name: Test
scene_type: interior
style: invalid_style
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)
            # Should fail due to invalid style
            assert result.success is False


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_parse_outline_yaml(self):
        """Test parse_outline function with YAML."""
        yaml_content = "name: Test\nscene_type: interior\nstyle: photorealistic"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            result = parse_outline(f.name)
            os.unlink(f.name)
            assert result.success is True

    def test_parse_outline_json(self):
        """Test parse_outline function with JSON."""
        json_content = '{"name": "Test", "scene_type": "interior", "style": "photorealistic"}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            f.flush()
            result = parse_outline(f.name)
            os.unlink(f.name)
            assert result.success is True

    def test_parse_outline_dict(self):
        """Test parse_outline function with dict."""
        data = {"name": "Test", "scene_type": "interior", "style": "photorealistic"}
        result = parse_outline(data)
        assert result.success is True

    def test_outline_to_yaml(self):
        """Test outline_to_yaml function."""
        from lib.orchestrator.types import SceneOutline
        outline = SceneOutline(name="Test", scene_type="interior")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.flush()
            success = outline_to_yaml(outline, f.name)
            os.unlink(f.name)
            assert success is True

    def test_outline_to_json(self):
        """Test outline_to_json function."""
        from lib.orchestrator.types import SceneOutline
        outline = SceneOutline(name="Test", scene_type="interior")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.flush()
            success = outline_to_json(outline, f.name)
            os.unlink(f.name)
            assert success is True


class TestOutlineParserEdgeCases:
    """Edge case tests for OutlineParser."""

    def test_empty_file(self):
        """Test parsing empty file."""
        parser = OutlineParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)
            # Empty file gets defaults applied
            assert result.success is True
            assert result.outline.name == "Untitled Scene"

    def test_extra_fields(self):
        """Test parsing with extra unknown fields."""
        parser = OutlineParser()
        yaml_content = """
name: Test
scene_type: interior
style: photorealistic
unknown_field: some_value
another_unknown:
  nested: value
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)
            # Should succeed, ignoring unknown fields
            assert result.success is True

    def test_unicode_content(self):
        """Test parsing with unicode content."""
        parser = OutlineParser()
        yaml_content = """
name: "Test Scene"
scene_type: interior
style: photorealistic
description: "A test scene"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            f.flush()
            result = parser.parse_yaml(f.name)
            os.unlink(f.name)
            assert result.success is True

    def test_unsupported_format(self):
        """Test parsing unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            f.flush()
            result = parse_outline(f.name)
            os.unlink(f.name)
            assert result.success is False
            assert "unsupported" in result.errors[0].lower()
