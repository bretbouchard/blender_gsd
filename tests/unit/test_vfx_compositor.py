"""
Unit Tests for VFX Compositor

Tests for compositor types, blend modes, color correction, and cryptomatte.
"""

import pytest
import math
from dataclasses import asdict

from lib.vfx.compositor_types import (
    BlendMode,
    LayerSource,
    OutputFormat,
    Transform2D,
    ColorCorrection,
    GradientStop,
    LayerMask,
    CompLayer,
    CryptomatteLayer,
    CompositeConfig,
)

from lib.vfx.layer_compositor import (
    LayerCompositor,
    CompositeResult,
    create_compositor,
)

from lib.vfx.blend_modes import (
    blend_normal,
    blend_multiply,
    blend_screen,
    blend_add,
    blend_overlay,
    blend_difference,
    blend_darken,
    blend_lighten,
    rgb_to_hsl,
    hsl_to_rgb,
    get_blend_function,
    apply_blend,
)

from lib.vfx.color_correction import (
    apply_exposure,
    apply_gamma,
    apply_contrast,
    apply_saturation,
    apply_lift_gamma_gain,
    apply_levels,
    rgb_to_hsv,
    hsv_to_rgb,
    apply_hsv_adjustment,
    apply_white_balance,
    apply_color_correction,
    get_color_preset,
    COLOR_PRESETS,
)

from lib.vfx.cryptomatte import (
    hash_object_name,
    hash_to_float,
    float_to_hash,
    create_cryptomatte_manifest,
    CryptomatteManifest,
    estimate_cryptomatte_ranks,
)


class TestTransform2D:
    """Tests for Transform2D dataclass."""

    def test_default_values(self):
        """Default transform should be identity."""
        t = Transform2D()
        assert t.position == (0.0, 0.0)
        assert t.rotation == 0.0
        assert t.scale == (1.0, 1.0)
        assert t.anchor == (0.5, 0.5)

    def test_custom_values(self):
        """Transform should accept custom values."""
        t = Transform2D(
            position=(100, 200),
            rotation=45.0,
            scale=(2.0, 1.5),
            anchor=(0.0, 0.0)
        )
        assert t.position == (100, 200)
        assert t.rotation == 45.0
        assert t.scale == (2.0, 1.5)

    def test_serialization(self):
        """Transform should serialize to/from dict."""
        t = Transform2D(position=(50, 100), rotation=30.0)
        d = t.to_dict()
        t2 = Transform2D.from_dict(d)
        assert t2.position == (50, 100)
        assert t2.rotation == 30.0


class TestColorCorrection:
    """Tests for ColorCorrection dataclass."""

    def test_default_values(self):
        """Default correction should be neutral."""
        cc = ColorCorrection()
        assert cc.exposure == 0.0
        assert cc.contrast == 1.0
        assert cc.saturation == 1.0
        assert cc.gamma == 1.0
        assert cc.lift == (0.0, 0.0, 0.0)
        assert cc.gain == (1.0, 1.0, 1.0)

    def test_custom_values(self):
        """Color correction should accept custom values."""
        cc = ColorCorrection(
            exposure=1.5,
            contrast=1.2,
            saturation=0.8,
            temperature=20,
        )
        assert cc.exposure == 1.5
        assert cc.contrast == 1.2
        assert cc.saturation == 0.8
        assert cc.temperature == 20

    def test_serialization(self):
        """Color correction should serialize correctly."""
        cc = ColorCorrection(exposure=2.0, contrast=1.5)
        d = cc.to_dict()
        cc2 = ColorCorrection.from_dict(d)
        assert cc2.exposure == 2.0
        assert cc2.contrast == 1.5


class TestCompLayer:
    """Tests for CompLayer dataclass."""

    def test_default_values(self):
        """Layer should have sensible defaults."""
        layer = CompLayer(name="Test", source="render_pass")
        assert layer.name == "Test"
        assert layer.blend_mode == BlendMode.NORMAL
        assert layer.opacity == 1.0
        assert layer.enabled is True

    def test_custom_values(self):
        """Layer should accept custom values."""
        layer = CompLayer(
            name="Overlay",
            source="diffuse",
            blend_mode=BlendMode.OVERLAY,
            opacity=0.5,
        )
        assert layer.blend_mode == BlendMode.OVERLAY
        assert layer.opacity == 0.5

    def test_serialization(self):
        """Layer should serialize correctly."""
        layer = CompLayer(
            name="Test",
            source="render_pass",
            blend_mode=BlendMode.SCREEN,
            opacity=0.75,
        )
        d = layer.to_dict()
        layer2 = CompLayer.from_dict(d)
        assert layer2.name == "Test"
        assert layer2.blend_mode == BlendMode.SCREEN
        assert layer2.opacity == 0.75


class TestCompositeConfig:
    """Tests for CompositeConfig."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = CompositeConfig(name="Test")
        assert config.name == "Test"
        assert config.resolution == (1920, 1080)
        assert config.frame_rate == 24.0
        assert config.frame_range == (1, 250)
        assert config.layers == []

    def test_layer_management(self):
        """Config should manage layers."""
        config = CompositeConfig(name="Test")
        layer = CompLayer(name="Layer1", source="pass1")
        config.add_layer(layer)
        assert len(config.layers) == 1
        assert config.get_layer("Layer1") == layer
        assert config.remove_layer("Layer1") is True
        assert len(config.layers) == 0

    def test_get_enabled_layers(self):
        """Should return only enabled layers."""
        config = CompositeConfig(name="Test")
        config.add_layer(CompLayer(name="L1", source="p1", enabled=True))
        config.add_layer(CompLayer(name="L2", source="p2", enabled=False))
        config.add_layer(CompLayer(name="L3", source="p3", enabled=True))
        enabled = config.get_enabled_layers()
        assert len(enabled) == 2
        assert all(l.enabled for l in enabled)


class TestLayerCompositor:
    """Tests for LayerCompositor."""

    def test_create_compositor(self):
        """Should create compositor with config."""
        comp = create_compositor("Test", (1280, 720), 30.0, (1, 100))
        assert comp.config.name == "Test"
        assert comp.config.resolution == (1280, 720)
        assert comp.config.frame_rate == 30.0

    def test_add_remove_layer(self):
        """Should add and remove layers."""
        comp = create_compositor()
        layer = CompLayer(name="Test", source="pass")
        comp.add_layer(layer)
        assert len(comp.get_all_layers()) == 1
        comp.remove_layer("Test")
        assert len(comp.get_all_layers()) == 0

    def test_create_solid_layer(self):
        """Should create solid color layer."""
        comp = create_compositor()
        layer = comp.create_solid_layer("Red", (1, 0, 0, 1))
        assert layer.name == "Red"
        assert layer.source_type == LayerSource.SOLID
        assert layer.solid_color == (1, 0, 0, 1)

    def test_set_blend_mode(self):
        """Should set blend mode."""
        comp = create_compositor()
        layer = CompLayer(name="Test", source="pass")
        comp.add_layer(layer)
        comp.set_blend_mode("Test", BlendMode.MULTIPLY)
        assert comp.get_layer("Test").blend_mode == BlendMode.MULTIPLY

    def test_set_opacity(self):
        """Should set opacity."""
        comp = create_compositor()
        layer = CompLayer(name="Test", source="pass")
        comp.add_layer(layer)
        comp.set_opacity("Test", 0.5)
        assert comp.get_layer("Test").opacity == 0.5


class TestBlendModes:
    """Tests for blend mode functions."""

    def test_blend_normal(self):
        """Normal blend should be alpha blend."""
        assert blend_normal(0.5, 0.8, 1.0) == 0.8
        assert blend_normal(0.5, 0.8, 0.5) == 0.65

    def test_blend_multiply(self):
        """Multiply should darken."""
        result = blend_multiply(0.5, 0.5, 1.0)
        assert result == 0.25

    def test_blend_screen(self):
        """Screen should lighten."""
        result = blend_screen(0.5, 0.5, 1.0)
        assert result == 0.75

    def test_blend_add(self):
        """Add should sum values."""
        assert blend_add(0.5, 0.3, 1.0) == 0.8
        assert blend_add(0.8, 0.5, 1.0) == 1.0  # Clamped

    def test_blend_difference(self):
        """Difference should return absolute difference."""
        assert blend_difference(0.8, 0.3, 1.0) == 0.5
        assert blend_difference(0.3, 0.8, 1.0) == 0.5

    def test_blend_overlay(self):
        """Overlay should combine multiply and screen."""
        # Dark values get multiplied
        result = blend_overlay(0.25, 0.5, 1.0)
        assert result == 0.25  # 2 * 0.25 * 0.5 = 0.25
        # Light values get screened
        result = blend_overlay(0.75, 0.5, 1.0)
        # 1 - 2 * (1 - 0.75) * (1 - 0.5) = 1 - 0.25 = 0.75
        assert result == 0.75

    def test_blend_darken_lighten(self):
        """Darken/lighten should use min/max."""
        assert blend_darken(0.5, 0.3, 1.0) == 0.3
        assert blend_lighten(0.5, 0.3, 1.0) == 0.5

    def test_rgb_hsl_conversion(self):
        """RGB to HSL and back should be identity."""
        r, g, b = 0.8, 0.4, 0.2
        h, s, l = rgb_to_hsl(r, g, b)
        r2, g2, b2 = hsl_to_rgb(h, s, l)
        assert r2 == pytest.approx(r, 0.01)
        assert g2 == pytest.approx(g, 0.01)
        assert b2 == pytest.approx(b, 0.01)

    def test_get_blend_function(self):
        """Should return blend function for mode."""
        func = get_blend_function(BlendMode.MULTIPLY)
        assert func == blend_multiply


class TestColorCorrection:
    """Tests for color correction functions."""

    def test_apply_exposure(self):
        """Exposure should multiply by 2^ev."""
        assert apply_exposure(0.5, 1.0) == 1.0
        assert apply_exposure(0.5, -1.0) == 0.25

    def test_apply_gamma(self):
        """Gamma should apply power curve."""
        assert apply_gamma(0.25, 2.0) == 0.5
        assert apply_gamma(0.5, 2.0) == pytest.approx(0.707, 0.01)

    def test_apply_contrast(self):
        """Contrast should expand/contract values."""
        # Higher contrast pushes away from 0.5
        result = apply_contrast(0.75, 2.0)
        assert result > 0.75
        # Lower contrast pulls toward 0.5
        result = apply_contrast(0.75, 0.5)
        assert result < 0.75

    def test_apply_saturation(self):
        """Saturation should control color intensity."""
        # Zero saturation = grayscale
        r, g, b = apply_saturation(1.0, 0.5, 0.0, 0.0)
        assert r == g == b
        # Full saturation = unchanged
        r, g, b = apply_saturation(1.0, 0.0, 1.0, 1.0)
        assert (r, g, b) == (1.0, 0.0, 1.0)

    def test_apply_levels(self):
        """Levels should remap input/output ranges."""
        result = apply_levels(0.5, 0.0, 1.0, 1.0, 0.0, 1.0)
        assert result == 0.5
        # Expand range (0.25-0.75 to 0.0-1.0)
        # 0.5 in input range = 0.5 normalized, stays 0.5
        result = apply_levels(0.5, 0.25, 0.75, 1.0, 0.0, 1.0)
        assert result == 0.5
        # Value at edge of range
        result = apply_levels(0.75, 0.25, 0.75, 1.0, 0.0, 1.0)
        assert result == 1.0

    def test_rgb_hsv_conversion(self):
        """RGB to HSV and back should be identity."""
        r, g, b = 0.8, 0.4, 0.2
        h, s, v = rgb_to_hsv(r, g, b)
        r2, g2, b2 = hsv_to_rgb(h, s, v)
        assert r2 == pytest.approx(r, 0.01)
        assert g2 == pytest.approx(g, 0.01)
        assert b2 == pytest.approx(b, 0.01)

    def test_apply_white_balance(self):
        """White balance should shift color temperature."""
        # Warm temperature adds yellow/red
        r, g, b = apply_white_balance(0.5, 0.5, 0.5, 50, 0)
        assert r > 0.5
        assert b < 0.5

    def test_get_color_preset(self):
        """Should return color preset."""
        preset = get_color_preset("cinematic_warm")
        assert "temperature" in preset
        assert preset["temperature"] > 0

    def test_color_presets_exist(self):
        """Color presets should be defined."""
        assert "neutral" in COLOR_PRESETS
        assert "cinematic_warm" in COLOR_PRESETS
        assert "vintage" in COLOR_PRESETS


class TestCryptomatte:
    """Tests for cryptomatte functions."""

    def test_hash_object_name(self):
        """Should generate consistent hash for object name."""
        hash1 = hash_object_name("Cube")
        hash2 = hash_object_name("Cube")
        assert hash1 == hash2
        assert len(hash1) == 8  # 32-bit hex

    def test_hash_different_names(self):
        """Different names should produce different hashes."""
        hash1 = hash_object_name("Cube")
        hash2 = hash_object_name("Sphere")
        assert hash1 != hash2

    def test_hash_to_float_roundtrip(self):
        """Hash to float and back should be identity."""
        original = "a1b2c3d4"
        float_val = hash_to_float(original)
        result = float_to_hash(float_val)
        assert result == original

    def test_create_manifest(self):
        """Should create manifest from object names."""
        objects = ["Cube", "Sphere", "Plane"]
        manifest = create_cryptomatte_manifest(objects)
        assert len(manifest.entries) == 3
        names = manifest.get_all_names()
        assert "Cube" in names
        assert "Sphere" in names

    def test_manifest_lookup(self):
        """Should lookup by name and hash."""
        manifest = create_cryptomatte_manifest(["Cube"])
        hash_val = manifest.get_hash("Cube")
        assert hash_val is not None
        name = manifest.get_name(hash_val)
        assert name == "Cube"

    def test_estimate_ranks(self):
        """Should estimate required cryptomatte ranks."""
        # Each rank stores ~2 objects
        assert estimate_cryptomatte_ranks(2) == 1
        assert estimate_cryptomatte_ranks(4) == 2
        assert estimate_cryptomatte_ranks(10) == 5


class TestModuleImports:
    """Test that all modules can be imported."""

    def test_import_types(self):
        """Should import all types."""
        from lib.vfx import BlendMode, CompLayer, CompositeConfig
        assert BlendMode.NORMAL.value == "normal"

    def test_import_blend_modes(self):
        """Should import blend modes."""
        from lib.vfx import blend_multiply, BLEND_MODES
        assert "multiply" in BLEND_MODES

    def test_import_color_correction(self):
        """Should import color correction."""
        from lib.vfx import apply_color_correction, COLOR_PRESETS
        assert "neutral" in COLOR_PRESETS

    def test_import_cryptomatte(self):
        """Should import cryptomatte."""
        from lib.vfx import create_cryptomatte_manifest, CryptomatteManifest
        manifest = create_cryptomatte_manifest(["Test"])
        assert isinstance(manifest, CryptomatteManifest)

    def test_import_blender(self):
        """Should import Blender integration."""
        from lib.vfx import create_composite_nodes, setup_render_passes
        assert callable(create_composite_nodes)
