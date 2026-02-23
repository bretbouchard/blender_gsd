"""
Tests for lib/vfx/layer_compositor.py

Tests layer compositing without Blender (bpy).
"""

import pytest
import json
import tempfile
import os

from lib.vfx.layer_compositor import (
    CompositeResult,
    LayerCompositor,
    create_compositor,
    load_compositor,
)

from lib.vfx.compositor_types import (
    CompositeConfig,
    CompLayer,
    BlendMode,
    LayerSource,
    ColorCorrection,
    Transform2D,
)


class TestCompositeResult:
    """Tests for CompositeResult dataclass."""

    def test_composite_result_defaults(self):
        """Test CompositeResult default values."""
        result = CompositeResult(success=True, frame=1)
        assert result.success is True
        assert result.frame == 1
        assert result.output_path == ""
        assert result.error == ""
        assert result.timing_ms == 0.0

    def test_composite_result_with_values(self):
        """Test CompositeResult with custom values."""
        result = CompositeResult(
            success=False,
            frame=100,
            output_path="/tmp/output.exr",
            error="Render failed",
            timing_ms=1234.5
        )
        assert result.success is False
        assert result.frame == 100
        assert result.output_path == "/tmp/output.exr"
        assert result.error == "Render failed"
        assert result.timing_ms == 1234.5


class TestLayerCompositor:
    """Tests for LayerCompositor class."""

    def test_create_compositor(self):
        """Test creating a compositor."""
        comp = LayerCompositor()
        assert comp.config is not None
        assert comp.config.name == "Composite"

    def test_create_compositor_with_config(self):
        """Test creating compositor with config."""
        config = CompositeConfig(
            name="Custom",
            resolution=(3840, 2160),
            frame_rate=30.0
        )
        comp = LayerCompositor(config)
        assert comp.config.name == "Custom"
        assert comp.config.resolution == (3840, 2160)

    def test_add_layer(self):
        """Test adding a layer."""
        comp = LayerCompositor()
        layer = CompLayer(
            name="Background",
            source="bg.exr",
            source_type=LayerSource.IMAGE_SEQUENCE
        )
        comp.add_layer(layer)
        assert len(comp.config.layers) == 1

    def test_remove_layer(self):
        """Test removing a layer."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        result = comp.remove_layer("Test")
        assert result is True
        assert len(comp.config.layers) == 0

    def test_remove_layer_not_found(self):
        """Test removing non-existent layer."""
        comp = LayerCompositor()
        result = comp.remove_layer("NonExistent")
        assert result is False

    def test_get_layer(self):
        """Test getting a layer."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        result = comp.get_layer("Test")
        assert result == layer

    def test_get_layer_not_found(self):
        """Test getting non-existent layer."""
        comp = LayerCompositor()
        result = comp.get_layer("NonExistent")
        assert result is None

    def test_get_all_layers(self):
        """Test getting all layers."""
        comp = LayerCompositor()
        layer1 = CompLayer(name="L1", source="1.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer2 = CompLayer(name="L2", source="2.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer1)
        comp.add_layer(layer2)
        layers = comp.get_all_layers()
        assert len(layers) == 2

    def test_get_enabled_layers(self):
        """Test getting enabled layers."""
        comp = LayerCompositor()
        layer1 = CompLayer(name="Enabled", source="1.exr", source_type=LayerSource.IMAGE_SEQUENCE, enabled=True)
        layer2 = CompLayer(name="Disabled", source="2.exr", source_type=LayerSource.IMAGE_SEQUENCE, enabled=False)
        comp.add_layer(layer1)
        comp.add_layer(layer2)
        enabled = comp.get_enabled_layers()
        assert len(enabled) == 1
        assert enabled[0].name == "Enabled"

    def test_reorder_layer(self):
        """Test reordering layers."""
        comp = LayerCompositor()
        layer1 = CompLayer(name="L1", source="1.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer2 = CompLayer(name="L2", source="2.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer3 = CompLayer(name="L3", source="3.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer1)
        comp.add_layer(layer2)
        comp.add_layer(layer3)

        # Move L1 to position 2 (end)
        comp.reorder_layer("L1", 2)
        names = [l.name for l in comp.config.layers]
        assert names == ["L2", "L3", "L1"]

    def test_reorder_layer_not_found(self):
        """Test reordering non-existent layer."""
        comp = LayerCompositor()
        result = comp.reorder_layer("NonExistent", 0)
        assert result is False

    def test_move_layer_up(self):
        """Test moving layer up (toward higher index)."""
        comp = LayerCompositor()
        layer1 = CompLayer(name="L1", source="1.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer2 = CompLayer(name="L2", source="2.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer3 = CompLayer(name="L3", source="3.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer1)
        comp.add_layer(layer2)
        comp.add_layer(layer3)

        # Move L2 up (from index 1 to index 2)
        comp.move_layer_up("L2")
        names = [l.name for l in comp.config.layers]
        assert names == ["L1", "L3", "L2"]

    def test_move_layer_down(self):
        """Test moving layer down (toward lower index)."""
        comp = LayerCompositor()
        layer1 = CompLayer(name="L1", source="1.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer2 = CompLayer(name="L2", source="2.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer3 = CompLayer(name="L3", source="3.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer1)
        comp.add_layer(layer2)
        comp.add_layer(layer3)

        # Move L2 down (from index 1 to index 0)
        comp.move_layer_down("L2")
        names = [l.name for l in comp.config.layers]
        assert names == ["L2", "L1", "L3"]

    def test_duplicate_layer(self):
        """Test duplicating a layer."""
        comp = LayerCompositor()
        layer = CompLayer(
            name="Original",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            opacity=0.8
        )
        comp.add_layer(layer)
        duplicate = comp.duplicate_layer("Original")
        assert duplicate is not None
        assert duplicate.name == "Original_copy"
        assert duplicate.opacity == 0.8
        assert len(comp.config.layers) == 2

    def test_duplicate_layer_with_custom_name(self):
        """Test duplicating a layer with custom name."""
        comp = LayerCompositor()
        layer = CompLayer(name="Original", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        duplicate = comp.duplicate_layer("Original", new_name="CustomName")
        assert duplicate.name == "CustomName"

    def test_duplicate_layer_not_found(self):
        """Test duplicating non-existent layer."""
        comp = LayerCompositor()
        result = comp.duplicate_layer("NonExistent")
        assert result is None

    def test_merge_down(self):
        """Test merging layer down."""
        comp = LayerCompositor()
        layer1 = CompLayer(name="L1", source="1.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        layer2 = CompLayer(name="L2", source="2.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer1)
        comp.add_layer(layer2)

        result = comp.merge_down("L2")
        assert result is True
        assert len(comp.config.layers) == 1

    def test_merge_down_bottom_layer(self):
        """Test merging bottom layer fails."""
        comp = LayerCompositor()
        layer = CompLayer(name="Only", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        result = comp.merge_down("Only")
        assert result is False


class TestLayerCompositorProperties:
    """Tests for layer property setters."""

    def test_set_blend_mode(self):
        """Test setting blend mode."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp.set_blend_mode("Test", BlendMode.MULTIPLY)
        assert comp.get_layer("Test").blend_mode == BlendMode.MULTIPLY

    def test_set_blend_mode_not_found(self):
        """Test setting blend mode on non-existent layer."""
        comp = LayerCompositor()
        result = comp.set_blend_mode("NonExistent", BlendMode.MULTIPLY)
        assert result is False

    def test_set_opacity(self):
        """Test setting opacity."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp.set_opacity("Test", 0.5)
        assert comp.get_layer("Test").opacity == 0.5

    def test_set_opacity_clamped(self):
        """Test opacity is clamped to valid range."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp.set_opacity("Test", 2.0)
        assert comp.get_layer("Test").opacity == 1.0
        comp.set_opacity("Test", -0.5)
        assert comp.get_layer("Test").opacity == 0.0

    def test_set_enabled(self):
        """Test setting enabled state."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp.set_enabled("Test", False)
        assert comp.get_layer("Test").enabled is False

    def test_set_solo(self):
        """Test setting solo state."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp.set_solo("Test", True)
        assert comp.get_layer("Test").solo is True

    def test_set_locked(self):
        """Test setting locked state."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp.set_locked("Test", True)
        assert comp.get_layer("Test").locked is True

    def test_set_transform(self):
        """Test setting transform."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        transform = Transform2D(position=(100, 50), rotation=45)
        comp.set_transform("Test", transform)
        result = comp.get_layer("Test").transform
        assert result.position == (100, 50)
        assert result.rotation == 45

    def test_set_color_correction(self):
        """Test setting color correction."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        cc = ColorCorrection(exposure=0.5)
        comp.set_color_correction("Test", cc)
        assert comp.get_layer("Test").color_correction.exposure == 0.5


class TestLayerCompositorFactoryMethods:
    """Tests for factory methods."""

    def test_create_solid_layer(self):
        """Test creating solid color layer."""
        comp = LayerCompositor()
        layer = comp.create_solid_layer(
            name="Solid Red",
            color=(1.0, 0.0, 0.0, 1.0)
        )
        assert layer.name == "Solid Red"
        assert layer.source_type == LayerSource.SOLID
        assert layer.solid_color == (1.0, 0.0, 0.0, 1.0)

    def test_create_gradient_layer(self):
        """Test creating gradient layer."""
        comp = LayerCompositor()
        stops = [
            (0.0, (0.0, 0.0, 0.0, 1.0)),
            (1.0, (1.0, 1.0, 1.0, 1.0))
        ]
        layer = comp.create_gradient_layer(
            name="Gradient",
            stops=stops,
            angle=45
        )
        assert layer.name == "Gradient"
        assert layer.source_type == LayerSource.GRADIENT
        assert layer.gradient_angle == 45

    def test_create_image_layer(self):
        """Test creating image layer."""
        comp = LayerCompositor()
        layer = comp.create_image_layer(
            name="Image",
            path="/path/to/image.exr",
            opacity=0.8
        )
        assert layer.name == "Image"
        assert layer.source_type == LayerSource.IMAGE_SEQUENCE
        assert layer.source == "/path/to/image.exr"
        assert layer.opacity == 0.8

    def test_create_render_pass_layer(self):
        """Test creating render pass layer."""
        comp = LayerCompositor()
        layer = comp.create_render_pass_layer(
            name="Diffuse",
            pass_name="diffuse_direct"
        )
        assert layer.name == "Diffuse"
        assert layer.source_type == LayerSource.RENDER_PASS
        assert layer.source == "diffuse_direct"


class TestLayerCompositorRendering:
    """Tests for rendering methods."""

    def test_render_frame(self):
        """Test rendering a frame."""
        config = CompositeConfig(name="Test", frame_range=(1, 10))
        comp = LayerCompositor(config)
        result = comp.render_frame(1)
        assert result.success is True
        assert result.frame == 1

    def test_render_all(self):
        """Test rendering all frames."""
        config = CompositeConfig(name="Test", frame_range=(1, 5))
        comp = LayerCompositor(config)
        results = comp.render_all()
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.frame == i + 1


class TestLayerCompositorSerialization:
    """Tests for serialization methods."""

    def test_save_config(self):
        """Test saving config."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            result = comp.save_config(path)
            assert result is True
            assert os.path.exists(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_load_config(self):
        """Test loading config."""
        # Create a config file
        config = CompositeConfig(name="Loaded")
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        config.add_layer(layer)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config.to_dict(), f)
            f.flush()
            path = f.name

        try:
            comp = LayerCompositor()
            result = comp.load_config(path)
            assert result is True
            assert comp.config.name == "Loaded"
            assert len(comp.config.layers) == 1
        finally:
            os.unlink(path)

    def test_load_config_invalid(self):
        """Test loading invalid config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            f.flush()
            path = f.name

        try:
            comp = LayerCompositor()
            result = comp.load_config(path)
            assert result is False
        finally:
            os.unlink(path)


class TestLayerCompositorCallbacks:
    """Tests for callback functionality."""

    def test_set_change_callback(self):
        """Test setting change callback."""
        comp = LayerCompositor()
        changes = []

        def on_change(name):
            changes.append(name)

        comp.set_change_callback(on_change)
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)

        assert "Test" in changes

    def test_callback_on_remove(self):
        """Test callback is called on remove."""
        comp = LayerCompositor()
        changes = []

        def on_change(name):
            changes.append(name)

        comp.set_change_callback(on_change)
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        changes.clear()
        comp.remove_layer("Test")

        assert "Test" in changes


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_compositor(self):
        """Test create_compositor function."""
        comp = create_compositor(
            name="Custom",
            resolution=(3840, 2160),
            frame_rate=30.0,
            frame_range=(1, 100)
        )
        assert comp.config.name == "Custom"
        assert comp.config.resolution == (3840, 2160)
        assert comp.config.frame_rate == 30.0
        assert comp.config.frame_range == (1, 100)

    def test_load_compositor(self):
        """Test load_compositor function."""
        # Create a config file
        config = CompositeConfig(name="Loaded Test")
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        config.add_layer(layer)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config.to_dict(), f)
            f.flush()
            path = f.name

        try:
            comp = load_compositor(path)
            assert comp is not None
            assert comp.config.name == "Loaded Test"
        finally:
            os.unlink(path)

    def test_load_compositor_invalid(self):
        """Test load_compositor with invalid file."""
        comp = load_compositor("/nonexistent/file.json")
        assert comp is None


class TestLayerCompositorCache:
    """Tests for cache invalidation."""

    def test_cache_invalidation_on_property_change(self):
        """Test that cache is invalidated on property change."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)

        # Add something to cache
        comp._layer_cache["Test"] = "cached_data"

        # Change property should invalidate
        comp.set_opacity("Test", 0.5)
        assert "Test" not in comp._layer_cache

    def test_cache_invalidation_on_remove(self):
        """Test that cache is cleared on layer remove."""
        comp = LayerCompositor()
        layer = CompLayer(name="Test", source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        comp._layer_cache["Test"] = "cached_data"

        comp.remove_layer("Test")
        assert "Test" not in comp._layer_cache


class TestLayerCompositorEdgeCases:
    """Tests for edge cases."""

    def test_operations_on_locked_layer(self):
        """Test operations on locked layer."""
        comp = LayerCompositor()
        layer = CompLayer(
            name="Locked",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            locked=True
        )
        comp.add_layer(layer)

        # Should still be able to modify (locking is UI hint)
        comp.set_opacity("Locked", 0.5)
        assert comp.get_layer("Locked").opacity == 0.5

    def test_empty_compositor_render(self):
        """Test rendering empty compositor."""
        comp = LayerCompositor()
        result = comp.render_frame(1)
        assert result.success is True

    def test_layer_with_special_characters(self):
        """Test layer names with special characters."""
        comp = LayerCompositor()
        layer = CompLayer(
            name="Layer With Spaces & Special!",
            source="test.exr",
            source_type=LayerSource.IMAGE_SEQUENCE
        )
        comp.add_layer(layer)
        assert comp.get_layer("Layer With Spaces & Special!") is not None

    def test_very_long_layer_name(self):
        """Test very long layer names."""
        comp = LayerCompositor()
        long_name = "A" * 500
        layer = CompLayer(name=long_name, source="test.exr", source_type=LayerSource.IMAGE_SEQUENCE)
        comp.add_layer(layer)
        assert comp.get_layer(long_name) is not None

    def test_many_layers(self):
        """Test compositor with many layers."""
        comp = LayerCompositor()
        for i in range(100):
            layer = CompLayer(
                name=f"Layer_{i:03d}",
                source=f"file_{i}.exr",
                source_type=LayerSource.IMAGE_SEQUENCE
            )
            comp.add_layer(layer)
        assert len(comp.config.layers) == 100
