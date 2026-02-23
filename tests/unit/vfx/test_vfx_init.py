"""
Tests for lib/vfx/__init__.py

Tests the main exports and module structure.
"""

import pytest


class TestVfxImports:
    """Test that all expected exports are available."""

    def test_type_imports(self):
        """Test that types are importable."""
        from lib.vfx import (
            BlendMode,
            LayerSource,
            OutputFormat,
            CompositeConfig,
            CompLayer,
            ColorCorrection,
            Transform2D,
        )
        assert BlendMode is not None
        assert LayerSource is not None
        assert OutputFormat is not None
        assert CompositeConfig is not None
        assert CompLayer is not None
        assert ColorCorrection is not None
        assert Transform2D is not None

    def test_blend_mode_functions(self):
        """Test blend mode function exports."""
        from lib.vfx import (
            blend_normal,
            blend_multiply,
            blend_screen,
            blend_overlay,
            blend_add,
        )
        assert callable(blend_normal)
        assert callable(blend_multiply)
        assert callable(blend_screen)
        assert callable(blend_overlay)
        assert callable(blend_add)

    def test_color_correction_functions(self):
        """Test color correction function exports."""
        from lib.vfx import (
            apply_exposure,
            apply_contrast,
            apply_saturation,
            apply_gamma,
            apply_lift_gamma_gain,
        )
        assert callable(apply_exposure)
        assert callable(apply_contrast)
        assert callable(apply_saturation)
        assert callable(apply_gamma)
        assert callable(apply_lift_gamma_gain)

    def test_compositor_functions(self):
        """Test compositor function exports."""
        from lib.vfx import (
            create_composite_nodes,
            create_layer_node,
            create_transform_node,
            create_color_correction_node,
            create_blend_node,
        )
        assert callable(create_composite_nodes)
        assert callable(create_layer_node)
        assert callable(create_transform_node)
        assert callable(create_color_correction_node)
        assert callable(create_blend_node)

    def test_layer_compositor_classes(self):
        """Test layer compositor class exports."""
        from lib.vfx import (
            LayerCompositor,
            CompositeResult,
            create_compositor,
            load_compositor,
        )
        assert LayerCompositor is not None
        assert CompositeResult is not None
        assert callable(create_compositor)
        assert callable(load_compositor)


class TestModuleConstants:
    """Test module-level constants."""

    def test_version_exists(self):
        """Test that __version__ exists."""
        import lib.vfx as vfx
        assert hasattr(vfx, '__version__')
        assert isinstance(vfx.__version__, str)

    def test_all_exports(self):
        """Test that __all__ is defined."""
        import lib.vfx as vfx
        assert hasattr(vfx, '__all__')
        assert isinstance(vfx.__all__, list)
        assert len(vfx.__all__) > 0
