"""
Tests for lib/vfx/compositor_types.py

Tests type definitions for compositor without Blender (bpy).
"""

import pytest
import json

from lib.vfx.compositor_types import (
    BlendMode,
    LayerSource,
    OutputFormat,
    GradientStop,
    Transform2D,
    ColorCorrection,
    CompLayer,
    CompositeConfig,
)


class TestBlendMode:
    """Tests for BlendMode enum."""

    def test_blend_modes_exist(self):
        """Test that expected blend modes exist."""
        assert hasattr(BlendMode, 'NORMAL')
        assert hasattr(BlendMode, 'ADD')
        assert hasattr(BlendMode, 'MULTIPLY')
        assert hasattr(BlendMode, 'SCREEN')
        assert hasattr(BlendMode, 'OVERLAY')
        assert hasattr(BlendMode, 'DARKEN')
        assert hasattr(BlendMode, 'LIGHTEN')
        assert hasattr(BlendMode, 'COLOR_DODGE')
        assert hasattr(BlendMode, 'COLOR_BURN')
        assert hasattr(BlendMode, 'HARD_LIGHT')
        assert hasattr(BlendMode, 'SOFT_LIGHT')
        assert hasattr(BlendMode, 'DIFFERENCE')

    def test_blend_mode_values(self):
        """Test blend mode enum values."""
        assert BlendMode.NORMAL.value == "normal"
        assert BlendMode.MULTIPLY.value == "multiply"


class TestLayerSource:
    """Tests for LayerSource enum."""

    def test_layer_sources_exist(self):
        """Test that expected layer sources exist."""
        assert hasattr(LayerSource, 'RENDER_PASS')
        assert hasattr(LayerSource, 'IMAGE_SEQUENCE')
        assert hasattr(LayerSource, 'SOLID')
        assert hasattr(LayerSource, 'GRADIENT')

    def test_layer_source_values(self):
        """Test layer source enum values."""
        assert LayerSource.RENDER_PASS.value == "render_pass"
        assert LayerSource.IMAGE_SEQUENCE.value == "image_sequence"


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_output_formats_exist(self):
        """Test that expected output formats exist."""
        assert hasattr(OutputFormat, 'PNG')
        assert hasattr(OutputFormat, 'JPEG')
        assert hasattr(OutputFormat, 'EXR')
        assert hasattr(OutputFormat, 'TIFF')
        assert hasattr(OutputFormat, 'WEBM')
        assert hasattr(OutputFormat, 'MP4')
        assert hasattr(OutputFormat, 'PRORES')

    def test_output_format_values(self):
        """Test output format enum values."""
        assert OutputFormat.PNG.value == "png"
        assert OutputFormat.EXR.value == "exr"


class TestGradientStop:
    """Tests for GradientStop dataclass."""

    def test_create_gradient_stop(self):
        """Test creating a gradient stop."""
        stop = GradientStop(position=0.5, color=(1.0, 0.0, 0.0, 1.0))
        assert stop.position == 0.5
        assert stop.color == (1.0, 0.0, 0.0, 1.0)

    def test_gradient_stop_to_dict(self):
        """Test gradient stop serialization."""
        stop = GradientStop(position=0.5, color=(1.0, 0.0, 0.0, 1.0))
        result = stop.to_dict()
        assert result["position"] == 0.5
        assert result["color"] == [1.0, 0.0, 0.0, 1.0]

    def test_gradient_stop_from_dict(self):
        """Test gradient stop deserialization."""
        data = {"position": 0.75, "color": [0.0, 1.0, 0.0, 0.5]}
        stop = GradientStop.from_dict(data)
        assert stop.position == 0.75
        assert stop.color == (0.0, 1.0, 0.0, 0.5)


class TestTransform2D:
    """Tests for Transform2D dataclass."""

    def test_create_transform(self):
        """Test creating a transform."""
        transform = Transform2D(
            position=(100, 50),
            rotation=45,
            scale=(1.5, 1.5)
        )
        assert transform.position == (100, 50)
        assert transform.rotation == 45
        assert transform.scale == (1.5, 1.5)

    def test_transform_defaults(self):
        """Test transform default values."""
        transform = Transform2D()
        assert transform.position == (0.0, 0.0)
        assert transform.rotation == 0.0
        assert transform.scale == (1.0, 1.0)

    def test_transform_to_dict(self):
        """Test transform serialization."""
        transform = Transform2D(position=(100, 50), rotation=45)
        result = transform.to_dict()
        assert result["position"] == [100, 50]
        assert result["rotation"] == 45

    def test_transform_from_dict(self):
        """Test transform deserialization."""
        data = {
            "position": [200, 100],
            "rotation": 90,
            "scale": [2.0, 2.0]
        }
        transform = Transform2D.from_dict(data)
        assert transform.position == (200, 100)
        assert transform.rotation == 90
        assert transform.scale == (2.0, 2.0)


class TestColorCorrection:
    """Tests for ColorCorrection dataclass."""

    def test_create_color_correction(self):
        """Test creating color correction."""
        cc = ColorCorrection(
            exposure=1.0,
            contrast=1.2,
            saturation=0.8,
            gamma=2.2
        )
        assert cc.exposure == 1.0
        assert cc.contrast == 1.2
        assert cc.saturation == 0.8
        assert cc.gamma == 2.2

    def test_color_correction_defaults(self):
        """Test color correction default values."""
        cc = ColorCorrection()
        assert cc.exposure == 0.0
        assert cc.contrast == 1.0
        assert cc.saturation == 1.0
        assert cc.gamma == 1.0
        assert cc.lift == (0.0, 0.0, 0.0)
        assert cc.gain == (1.0, 1.0, 1.0)

    def test_color_correction_to_dict(self):
        """Test color correction serialization."""
        cc = ColorCorrection(exposure=0.5)
        result = cc.to_dict()
        assert result["exposure"] == 0.5

    def test_color_correction_from_dict(self):
        """Test color correction deserialization."""
        data = {"exposure": 1.5, "gamma": 1.8}
        cc = ColorCorrection.from_dict(data)
        assert cc.exposure == 1.5
        assert cc.gamma == 1.8


class TestCompLayer:
    """Tests for CompLayer dataclass."""

    def test_create_layer(self):
        """Test creating a layer."""
        layer = CompLayer(
            name="Background",
            source="/path/to/bg.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            blend_mode=BlendMode.NORMAL,
            opacity=1.0
        )
        assert layer.name == "Background"
        assert layer.source == "/path/to/bg.exr"
        assert layer.source_type == LayerSource.IMAGE_SEQUENCE
        assert layer.blend_mode == BlendMode.NORMAL
        assert layer.opacity == 1.0

    def test_layer_defaults(self):
        """Test layer default values."""
        layer = CompLayer(name="Test", source="test.exr")
        assert layer.enabled is True
        assert layer.locked is False
        assert layer.solo is False
        assert layer.blend_mode == BlendMode.NORMAL
        assert layer.opacity == 1.0

    def test_layer_with_transform(self):
        """Test layer with transform."""
        transform = Transform2D(position=(100, 50))
        layer = CompLayer(
            name="Transformed",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            transform=transform
        )
        assert layer.transform.position == (100, 50)

    def test_layer_with_color_correction(self):
        """Test layer with color correction."""
        cc = ColorCorrection(exposure=0.5)
        layer = CompLayer(
            name="Color Corrected",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            color_correction=cc
        )
        assert layer.color_correction.exposure == 0.5

    def test_layer_to_dict(self):
        """Test layer serialization."""
        layer = CompLayer(
            name="Test Layer",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE
        )
        result = layer.to_dict()
        assert result["name"] == "Test Layer"
        assert result["source"] == "test.exr"

    def test_layer_from_dict(self):
        """Test layer deserialization."""
        data = {
            "name": "Loaded Layer",
            "source": "/path/to/file.exr",
            "source_type": "image_sequence",
            "blend_mode": "multiply",
            "opacity": 0.8,
            "enabled": False
        }
        layer = CompLayer.from_dict(data)
        assert layer.name == "Loaded Layer"
        assert layer.source == "/path/to/file.exr"
        assert layer.source_type == LayerSource.IMAGE_SEQUENCE
        assert layer.blend_mode == BlendMode.MULTIPLY
        assert layer.opacity == 0.8
        assert layer.enabled is False

    def test_layer_solid_color(self):
        """Test layer with solid color."""
        layer = CompLayer(
            name="Solid",
            source="solid",
            source_type=LayerSource.SOLID,
            solid_color=(0.5, 0.5, 0.5, 1.0)
        )
        assert layer.solid_color == (0.5, 0.5, 0.5, 1.0)


class TestCompositeConfig:
    """Tests for CompositeConfig dataclass."""

    def test_create_config(self):
        """Test creating a config."""
        config = CompositeConfig(name="Test Composite")
        assert config.name == "Test Composite"
        assert config.layers == []

    def test_config_defaults(self):
        """Test config default values."""
        config = CompositeConfig(name="Test")
        assert config.resolution == (1920, 1080)
        assert config.frame_rate == 24.0
        assert config.frame_range == (1, 250)
        assert config.output_format == OutputFormat.PNG  # Default is PNG

    def test_add_layer(self):
        """Test adding layers to config."""
        config = CompositeConfig(name="Test")
        layer = CompLayer(name="Layer1", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        config.add_layer(layer)
        assert len(config.layers) == 1
        assert config.layers[0].name == "Layer1"

    def test_remove_layer(self):
        """Test removing layers from config."""
        config = CompositeConfig(name="Test")
        layer = CompLayer(name="Layer1", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        config.add_layer(layer)
        result = config.remove_layer("Layer1")
        assert result is True
        assert len(config.layers) == 0

    def test_remove_layer_not_found(self):
        """Test removing non-existent layer."""
        config = CompositeConfig(name="Test")
        result = config.remove_layer("NonExistent")
        assert result is False

    def test_get_layer(self):
        """Test getting layer by name."""
        config = CompositeConfig(name="Test")
        layer = CompLayer(name="Layer1", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        config.add_layer(layer)
        result = config.get_layer("Layer1")
        assert result == layer

    def test_get_layer_not_found(self):
        """Test getting non-existent layer."""
        config = CompositeConfig(name="Test")
        result = config.get_layer("NonExistent")
        assert result is None

    def test_get_enabled_layers(self):
        """Test getting enabled layers."""
        config = CompositeConfig(name="Test")
        layer1 = CompLayer(name="Enabled", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE, enabled=True)
        layer2 = CompLayer(name="Disabled", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE, enabled=False)
        config.add_layer(layer1)
        config.add_layer(layer2)
        enabled = config.get_enabled_layers()
        assert len(enabled) == 1
        assert enabled[0].name == "Enabled"

    def test_get_enabled_layers_with_solo(self):
        """Test solo layer takes precedence."""
        config = CompositeConfig(name="Test")
        layer1 = CompLayer(name="Normal", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE, enabled=True)
        layer2 = CompLayer(name="Solo", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE, enabled=True, solo=True)
        config.add_layer(layer1)
        config.add_layer(layer2)
        enabled = config.get_enabled_layers()
        assert len(enabled) == 1
        assert enabled[0].name == "Solo"

    def test_config_to_dict(self):
        """Test config serialization."""
        config = CompositeConfig(name="My Config")
        layer = CompLayer(name="Layer1", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        config.add_layer(layer)
        result = config.to_dict()
        assert result["name"] == "My Config"
        assert len(result["layers"]) == 1

    def test_config_from_dict(self):
        """Test config deserialization."""
        data = {
            "name": "Loaded Config",
            "resolution": [3840, 2160],
            "frame_rate": 30.0,
            "frame_range": [1, 100],
            "output_path": "/tmp/output/",
            "output_format": "png",
            "layers": [
                {
                    "name": "Layer1",
                    "source": "test.exr",
                    "source_type": "image_sequence",
                    "blend_mode": "normal",
                    "opacity": 1.0
                }
            ]
        }
        config = CompositeConfig.from_dict(data)
        assert config.name == "Loaded Config"
        assert config.resolution == (3840, 2160)
        assert config.frame_rate == 30.0
        assert config.frame_range == (1, 100)
        assert config.output_format == OutputFormat.PNG
        assert len(config.layers) == 1


class TestCompositeConfigEdgeCases:
    """Tests for edge cases in CompositeConfig."""

    def test_empty_config_serialization(self):
        """Test serializing empty config."""
        config = CompositeConfig(name="Empty")
        result = config.to_dict()
        assert result["name"] == "Empty"
        assert result["layers"] == []

    def test_config_with_multiple_layers(self):
        """Test config with many layers."""
        config = CompositeConfig(name="Many Layers")
        for i in range(10):
            layer = CompLayer(
                name=f"Layer_{i}",
                source=f"file_{i}.exr",
                source_type=LayerSource.IMAGE_SEQUENCE
            )
            config.add_layer(layer)
        assert len(config.layers) == 10

    def test_config_layer_order(self):
        """Test that layer order is preserved."""
        config = CompositeConfig(name="Order Test")
        for name in ["A", "B", "C", "D"]:
            config.add_layer(CompLayer(name=name, source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE))
        names = [l.name for l in config.layers]
        assert names == ["A", "B", "C", "D"]


class TestEnumSerialization:
    """Tests for enum serialization in contexts."""

    def test_blend_mode_from_string(self):
        """Test creating blend mode from string."""
        data = {
            "name": "Test",
            "source": "test.exr",
            "source_type": "image_sequence",
            "blend_mode": "multiply"
        }
        layer = CompLayer.from_dict(data)
        assert layer.blend_mode == BlendMode.MULTIPLY

    def test_layer_source_from_string(self):
        """Test creating layer source from string."""
        data = {
            "name": "Test",
            "source": "test.exr",
            "source_type": "render_pass"
        }
        layer = CompLayer.from_dict(data)
        assert layer.source_type == LayerSource.RENDER_PASS

    def test_output_format_from_string(self):
        """Test creating output format from string."""
        data = {
            "name": "Test",
            "output_format": "jpeg"
        }
        config = CompositeConfig.from_dict(data)
        assert config.output_format == OutputFormat.JPEG


class TestNestedSerialization:
    """Tests for nested object serialization."""

    def test_layer_with_nested_transform(self):
        """Test layer with nested transform serialization."""
        layer = CompLayer(
            name="Transformed",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            transform=Transform2D(position=(100, 50), rotation=45)
        )
        data = layer.to_dict()
        loaded = CompLayer.from_dict(data)
        assert loaded.transform.position == (100, 50)
        assert loaded.transform.rotation == 45

    def test_layer_with_nested_color_correction(self):
        """Test layer with nested color correction serialization."""
        layer = CompLayer(
            name="CC",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            color_correction=ColorCorrection(exposure=0.5, contrast=1.2)
        )
        data = layer.to_dict()
        loaded = CompLayer.from_dict(data)
        assert loaded.color_correction.exposure == 0.5
        assert loaded.color_correction.contrast == 1.2

    def test_full_config_roundtrip(self):
        """Test full config serialization roundtrip."""
        config = CompositeConfig(
            name="Full Test",
            resolution=(3840, 2160),
            frame_rate=30.0,
            output_path="/tmp/output/",
            output_format=OutputFormat.PNG
        )

        layer1 = CompLayer(
            name="Background",
            source="bg.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            transform=Transform2D(position=(0, 0)),
            color_correction=ColorCorrection(exposure=0.3)
        )

        layer2 = CompLayer(
            name="Foreground",
            source="fg.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            blend_mode=BlendMode.SCREEN,
            opacity=0.8
        )

        config.add_layer(layer1)
        config.add_layer(layer2)

        # Roundtrip
        data = config.to_dict()
        loaded = CompositeConfig.from_dict(data)

        assert loaded.name == "Full Test"
        assert loaded.resolution == (3840, 2160)
        assert len(loaded.layers) == 2
        assert loaded.layers[0].color_correction.exposure == 0.3
        assert loaded.layers[1].blend_mode == BlendMode.SCREEN
