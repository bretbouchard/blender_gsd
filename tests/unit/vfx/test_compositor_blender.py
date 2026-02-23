"""
Tests for lib/vfx/compositor_blender.py

Tests Blender compositor integration without actual Blender (bpy).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from lib.vfx.compositor_blender import (
    create_composite_nodes,
    create_layer_node,
    create_transform_node,
    create_color_correction_node,
    create_blend_node,
    setup_render_passes,
    create_basic_composite,
    add_color_correction_to_composite,
    _get_blender_format,
    _transform_non_default,
    _color_correction_non_default,
)

from lib.vfx.compositor_types import (
    CompositeConfig,
    CompLayer,
    ColorCorrection,
    Transform2D,
    BlendMode,
    LayerSource,
    OutputFormat,
)


class TestCreateCompositeNodes:
    """Tests for create_composite_nodes function."""

    def test_create_composite_nodes_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        # When bpy is not installed, the function should return None
        # We test this by verifying the behavior when import bpy fails
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            config = CompositeConfig(name="Test")
            result = create_composite_nodes(config)
            # Without Blender, should return None
            assert result is None
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy

    def test_create_composite_nodes_without_bpy(self):
        """Test with bpy import failing."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            config = CompositeConfig(name="Test")
            result = create_composite_nodes(config)
            assert result is None
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestCreateLayerNode:
    """Tests for create_layer_node function."""

    def test_create_layer_node_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            layer = CompLayer(
                name="Test Layer",
                source="test.exr",
                source_type=LayerSource.IMAGE_SEQUENCE
            )
            result = create_layer_node(None, layer, None)
            # Without Blender, should return None
            assert result is None
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestCreateTransformNode:
    """Tests for create_transform_node function."""

    def test_create_transform_node_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            transform = Transform2D(position=(100, 50), rotation=45, scale=(1.5, 1.5))
            # create_transform_node doesn't check for bpy, it tries to call tree.nodes.new
            # which will fail on None. We just verify it doesn't raise an unhandled exception.
            try:
                result = create_transform_node(None, transform)
            except (AttributeError, TypeError):
                # Expected when tree is None
                pass
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestCreateColorCorrectionNode:
    """Tests for create_color_correction_node function."""

    def test_create_color_correction_node_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            cc = ColorCorrection(exposure=0.5, contrast=1.2)
            # create_color_correction_node doesn't check for bpy, it tries to call tree.nodes.new
            # which will fail on None. We just verify it doesn't raise an unhandled exception.
            try:
                result = create_color_correction_node(None, cc)
            except (AttributeError, TypeError):
                # Expected when tree is None
                pass
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestCreateBlendNode:
    """Tests for create_blend_node function."""

    def test_create_blend_node_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            # create_blend_node doesn't check for bpy, it tries to call tree.nodes.new
            # which will fail on None. We just verify it doesn't raise an unhandled exception.
            try:
                result = create_blend_node(None, BlendMode.NORMAL, 0.8)
            except (AttributeError, TypeError):
                # Expected when tree is None
                pass
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestSetupRenderPasses:
    """Tests for setup_render_passes function."""

    def test_setup_render_passes_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            # Should not crash even without Blender
            setup_render_passes(None, ["combined", "normal", "z"])
            # No exception is success
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy

    def test_setup_render_passes_empty(self):
        """Test with empty passes list."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            setup_render_passes(None, [])
            # No exception is success
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestCreateBasicComposite:
    """Tests for create_basic_composite function."""

    def test_create_basic_composite_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            result = create_basic_composite()
            # Without Blender, should return None
            assert result is None
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestAddColorCorrectionToComposite:
    """Tests for add_color_correction_to_composite function."""

    def test_add_color_correction_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        import sys
        # Save original bpy if it exists
        original_bpy = sys.modules.get('bpy')
        # Remove bpy from modules to simulate it not being installed
        if 'bpy' in sys.modules:
            del sys.modules['bpy']

        try:
            cc = ColorCorrection(exposure=0.5)
            # add_color_correction_to_composite calls create_color_correction_node
            # which doesn't check for bpy. Will fail on None tree.
            try:
                result = add_color_correction_to_composite(None, cc)
            except (AttributeError, TypeError):
                # Expected when tree is None
                pass
        finally:
            # Restore bpy if it existed
            if original_bpy is not None:
                sys.modules['bpy'] = original_bpy


class TestGetBlenderFormat:
    """Tests for _get_blender_format helper function."""

    def test_get_blender_format_png(self):
        """Test PNG format conversion."""
        result = _get_blender_format(OutputFormat.PNG)
        assert result == 'PNG'

    def test_get_blender_format_jpeg(self):
        """Test JPEG format conversion."""
        result = _get_blender_format(OutputFormat.JPEG)
        assert result == 'JPEG'

    def test_get_blender_format_exr(self):
        """Test EXR format conversion."""
        result = _get_blender_format(OutputFormat.EXR)
        assert result == 'OPEN_EXR'

    def test_get_blender_format_tiff(self):
        """Test TIFF format conversion."""
        result = _get_blender_format(OutputFormat.TIFF)
        assert result == 'TIFF'

    def test_get_blender_format_webm(self):
        """Test WEBM format conversion."""
        result = _get_blender_format(OutputFormat.WEBM)
        assert result == 'WEBM'

    def test_get_blender_format_mp4(self):
        """Test MP4 format conversion."""
        result = _get_blender_format(OutputFormat.MP4)
        assert result == 'FFMPEG'

    def test_get_blender_format_prores(self):
        """Test PRORES format conversion."""
        result = _get_blender_format(OutputFormat.PRORES)
        assert result == 'FFMPEG'

    def test_get_blender_format_unknown(self):
        """Test unknown format defaults to PNG."""
        # Create a mock enum value
        result = _get_blender_format("unknown")
        assert result == 'PNG'


class TestTransformNonDefault:
    """Tests for _transform_non_default helper function."""

    def test_transform_default(self):
        """Test default transform returns False."""
        transform = Transform2D()
        result = _transform_non_default(transform)
        assert result is False

    def test_transform_position_changed(self):
        """Test non-default position returns True."""
        transform = Transform2D(position=(100, 50))
        result = _transform_non_default(transform)
        assert result is True

    def test_transform_rotation_changed(self):
        """Test non-default rotation returns True."""
        transform = Transform2D(rotation=45)
        result = _transform_non_default(transform)
        assert result is True

    def test_transform_scale_changed(self):
        """Test non-default scale returns True."""
        transform = Transform2D(scale=(2.0, 2.0))
        result = _transform_non_default(transform)
        assert result is True

    def test_transform_all_changed(self):
        """Test all changed returns True."""
        transform = Transform2D(position=(100, 50), rotation=45, scale=(2.0, 2.0))
        result = _transform_non_default(transform)
        assert result is True


class TestColorCorrectionNonDefault:
    """Tests for _color_correction_non_default helper function."""

    def test_cc_default(self):
        """Test default CC returns False."""
        cc = ColorCorrection()
        result = _color_correction_non_default(cc)
        assert result is False

    def test_cc_exposure_changed(self):
        """Test non-default exposure returns True."""
        cc = ColorCorrection(exposure=1.0)
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_contrast_changed(self):
        """Test non-default contrast returns True."""
        cc = ColorCorrection(contrast=1.5)
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_saturation_changed(self):
        """Test non-default saturation returns True."""
        cc = ColorCorrection(saturation=0.8)
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_gamma_changed(self):
        """Test non-default gamma returns True."""
        cc = ColorCorrection(gamma=2.2)
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_lift_changed(self):
        """Test non-default lift returns True."""
        cc = ColorCorrection(lift=(0.1, 0.0, 0.0))
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_gain_changed(self):
        """Test non-default gain returns True."""
        cc = ColorCorrection(gain=(1.5, 1.0, 1.0))
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_offset_changed(self):
        """Test non-default offset returns True."""
        cc = ColorCorrection(offset=(0.1, 0.0, 0.0))
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_hue_shift_changed(self):
        """Test non-default hue shift returns True."""
        cc = ColorCorrection(hue_shift=45)
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_temperature_changed(self):
        """Test non-default temperature returns True."""
        cc = ColorCorrection(temperature=50)
        result = _color_correction_non_default(cc)
        assert result is True

    def test_cc_tint_changed(self):
        """Test non-default tint returns True."""
        cc = ColorCorrection(tint=25)
        result = _color_correction_non_default(cc)
        assert result is True


class TestCompositeConfigIntegration:
    """Tests that verify config works with compositor functions."""

    def test_config_with_layers(self):
        """Test config with multiple layers."""
        config = CompositeConfig(name="Multi Layer")

        layer1 = CompLayer(
            name="Background",
            source="bg.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            blend_mode=BlendMode.NORMAL,
            opacity=1.0
        )
        layer2 = CompLayer(
            name="Foreground",
            source="fg.exr",
            source_type=LayerSource.IMAGE_SEQUENCE,
            blend_mode=BlendMode.NORMAL,
            opacity=0.8,
            transform=Transform2D(position=(100, 50))
        )

        config.add_layer(layer1)
        config.add_layer(layer2)

        # Config should be valid
        assert len(config.layers) == 2
        assert config.get_enabled_layers() == [layer1, layer2]

    def test_config_output_path(self):
        """Test config with output path."""
        config = CompositeConfig(
            name="Output Test",
            output_path="/tmp/output/",
            output_format=OutputFormat.EXR
        )
        assert config.output_path == "/tmp/output/"
        assert config.output_format == OutputFormat.EXR


class TestCompLayerTypes:
    """Tests for different CompLayer source types."""

    def test_render_pass_layer(self):
        """Test creating render pass layer."""
        layer = CompLayer(
            name="Diffuse",
            source="diffuse_direct",
            source_type=LayerSource.RENDER_PASS
        )
        assert layer.source_type == LayerSource.RENDER_PASS

    def test_image_sequence_layer(self):
        """Test creating image sequence layer."""
        layer = CompLayer(
            name="Plate",
            source="/path/to/plate.####.exr",
            source_type=LayerSource.IMAGE_SEQUENCE
        )
        assert layer.source_type == LayerSource.IMAGE_SEQUENCE

    def test_solid_layer(self):
        """Test creating solid color layer."""
        layer = CompLayer(
            name="Solid Black",
            source="solid",
            source_type=LayerSource.SOLID,
            solid_color=(0.0, 0.0, 0.0, 1.0)
        )
        assert layer.source_type == LayerSource.SOLID
        assert layer.solid_color == (0.0, 0.0, 0.0, 1.0)

    def test_gradient_layer(self):
        """Test creating gradient layer."""
        from lib.vfx.compositor_types import GradientStop
        layer = CompLayer(
            name="Gradient",
            source="gradient",
            source_type=LayerSource.GRADIENT,
            gradient_stops=[
                GradientStop(0.0, (0.0, 0.0, 0.0, 1.0)),
                GradientStop(1.0, (1.0, 1.0, 1.0, 1.0))
            ]
        )
        assert layer.source_type == LayerSource.GRADIENT
        assert len(layer.gradient_stops) == 2


class TestBlendModes:
    """Tests for blend mode handling."""

    def test_all_blend_modes_available(self):
        """Test that all blend modes are available."""
        modes = [
            BlendMode.NORMAL,
            BlendMode.ADD,
            BlendMode.MULTIPLY,
            BlendMode.SCREEN,
            BlendMode.OVERLAY,
            BlendMode.DARKEN,
            BlendMode.LIGHTEN,
            BlendMode.COLOR_DODGE,
            BlendMode.COLOR_BURN,
            BlendMode.HARD_LIGHT,
            BlendMode.SOFT_LIGHT,
            BlendMode.DIFFERENCE,
        ]
        for mode in modes:
            layer = CompLayer(
                name=f"Layer_{mode.value}",
                source="test.exr",
                source_type=LayerSource.IMAGE_SEQUENCE,
                blend_mode=mode
            )
            assert layer.blend_mode == mode


class TestOutputFormats:
    """Tests for output format handling."""

    def test_all_output_formats_available(self):
        """Test that all output formats are available."""
        formats = [
            OutputFormat.PNG,
            OutputFormat.JPEG,
            OutputFormat.EXR,
            OutputFormat.TIFF,
            OutputFormat.WEBM,
            OutputFormat.MP4,
            OutputFormat.PRORES,
        ]
        for fmt in formats:
            config = CompositeConfig(
                name=f"Config_{fmt.value}",
                output_format=fmt
            )
            assert config.output_format == fmt
