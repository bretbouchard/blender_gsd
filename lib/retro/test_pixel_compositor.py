"""
Tests for pixel_compositor module.

Note: Most functions require Blender, so these tests focus on
the functions that can be tested without Blender.

Run with: pytest lib/retro/test_pixel_compositor.py -v
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Check for optional dependencies
try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from lib.retro.pixel_types import PixelationConfig, PixelStyle
from lib.retro.pixel_compositor import (
    bake_pixelation,
)


class TestBakePixelation:
    """Tests for bake_pixelation function."""

    @pytest.mark.skipif(not HAS_PIL, reason="PIL required")
    def test_bake_basic(self):
        """Test basic pixelation baking."""
        # Create a test image
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.png")
            output_path = os.path.join(tmpdir, "output.png")

            # Create test image
            img = Image.new("RGB", (100, 100), color=(128, 128, 128))
            img.save(input_path)

            # Run pixelation
            config = PixelationConfig(style=PixelStyle(pixel_size=4))
            result = bake_pixelation(input_path, config, output_path)

            # Check output exists
            assert os.path.exists(output_path)

            # Load and verify
            output_img = Image.open(output_path)
            assert output_img is not None

    @pytest.mark.skipif(not HAS_PIL, reason="PIL required")
    def test_bake_with_alpha(self):
        """Test pixelation with alpha channel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.png")
            output_path = os.path.join(tmpdir, "output.png")

            # Create RGBA image with alpha
            img = Image.new("RGBA", (100, 100), color=(128, 128, 128, 200))
            img.save(input_path)

            config = PixelationConfig(style=PixelStyle(pixel_size=2))
            result = bake_pixelation(input_path, config, output_path, use_alpha=True)

            # Check output
            output_img = Image.open(output_path)
            assert output_img.mode == "RGBA"

    @pytest.mark.skipif(not HAS_PIL, reason="PIL required")
    def test_bake_gameboy_style(self):
        """Test Game Boy style pixelation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.png")
            output_path = os.path.join(tmpdir, "output.png")

            # Create gradient test image
            img = Image.new("RGB", (160, 144))
            pixels = img.load()
            for y in range(144):
                for x in range(160):
                    pixels[x, y] = (x, y, 128)
            img.save(input_path)

            config = PixelationConfig.for_console("gameboy")
            result = bake_pixelation(input_path, config, output_path)

            assert os.path.exists(output_path)


class TestCompositorFunctions:
    """Tests that require mocking Blender."""

    def test_create_pixelator_nodes_requires_blender(self):
        """Test that create_pixelator_nodes raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        config = PixelationConfig()
        with pytest.raises(ImportError):
            pixel_compositor.create_pixelator_nodes(None, config)

    def test_setup_pixelator_pass_requires_blender(self):
        """Test that setup_pixelator_pass raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        config = PixelationConfig()
        with pytest.raises(ImportError):
            pixel_compositor.setup_pixelator_pass(None, config)

    def test_create_scale_node_requires_blender(self):
        """Test that create_scale_node raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        with pytest.raises(ImportError):
            pixel_compositor.create_scale_node(None, 0.5)

    def test_create_posterize_node_requires_blender(self):
        """Test that create_posterize_node raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        with pytest.raises(ImportError):
            pixel_compositor.create_posterize_node(None, 4)

    def test_create_color_ramp_quantize_requires_blender(self):
        """Test that create_color_ramp_quantize raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        colors = [(1.0, 0.0, 0.0, 1.0), (0.0, 1.0, 0.0, 1.0)]
        with pytest.raises(ImportError):
            pixel_compositor.create_color_ramp_quantize(None, colors)

    def test_setup_pixel_preview_requires_blender(self):
        """Test that setup_pixel_preview raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        config = PixelationConfig()
        with pytest.raises(ImportError):
            pixel_compositor.setup_pixel_preview(None, config)

    def test_apply_pixel_style_to_scene_requires_blender(self):
        """Test that apply_pixel_style_to_scene raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        config = PixelationConfig()
        with pytest.raises(ImportError):
            pixel_compositor.apply_pixel_style_to_scene(None, config)

    def test_get_pixel_node_group_requires_blender(self):
        """Test that get_pixel_node_group raises without Blender."""
        from lib.retro import pixel_compositor

        if pixel_compositor.HAS_BLENDER:
            pytest.skip("Blender is available, skipping negative test")

        config = PixelationConfig()
        with pytest.raises(ImportError):
            pixel_compositor.get_pixel_node_group(config)


class TestMockedBlenderFunctions:
    """Tests with mocked Blender."""

    @patch("lib.retro.pixel_compositor.HAS_BLENDER", True)
    @patch("lib.retro.pixel_compositor.bpy")
    def test_create_pixelator_nodes_mocked(self, mock_bpy):
        """Test create_pixelator_nodes with mocked Blender."""
        from lib.retro.pixel_compositor import create_pixelator_nodes

        # Create mock node tree
        mock_node_tree = Mock()
        mock_nodes = {}
        mock_node_tree.nodes = Mock()
        mock_node_tree.links = Mock()

        def mock_new(node_type):
            node = Mock()
            node.name = node_type
            node.inputs = [Mock() for _ in range(10)]  # Many inputs
            node.outputs = [Mock() for _ in range(5)]  # Many outputs
            node.color_ramp = Mock()
            node.color_ramp.elements = Mock()
            node.color_ramp.elements.new = lambda pos: Mock(color=(1,1,1,1))
            node.color_ramp.elements.clear = lambda: None
            mock_nodes[node_type] = node
            return node

        mock_node_tree.nodes.new = mock_new
        mock_node_tree.nodes.get = lambda n: None

        config = PixelationConfig(style=PixelStyle(pixel_size=2, posterize_levels=4))
        result = create_pixelator_nodes(mock_node_tree, config)

        assert "input" in result
        assert "scale" in result
        assert "output" in result

    @patch("lib.retro.pixel_compositor.HAS_BLENDER", True)
    @patch("lib.retro.pixel_compositor.bpy")
    def test_create_scale_node_mocked(self, mock_bpy):
        """Test create_scale_node with mocked Blender."""
        from lib.retro.pixel_compositor import create_scale_node

        mock_node_tree = Mock()
        created_node = Mock()
        created_node.inputs = [Mock() for _ in range(10)]  # Many inputs
        mock_node_tree.nodes.new = lambda t: created_node

        result = create_scale_node(mock_node_tree, 0.5, "nearest")
        assert result is not None
