"""
Tests for lib/compositing/__init__.py

Tests the main exports and module structure.
"""

import pytest


class TestCompositingImports:
    """Test that all expected exports are available."""

    def test_module_imports(self):
        """Test that the compositing module can be imported."""
        from lib.compositing import (
            # Cryptomatte
            CryptomatteLayer,
            MatteType,
            CryptomatteConfig,
            CryptomattePass,
            MatteData,
            CryptomatteManager,
            # Multi-Pass
            PassType,
            PassCategory,
            OutputFormat,
            RenderPass,
            PassConfig,
            MultiPassSetup,
            MultiPassManager,
            # Post-Process
            EffectType,
            ColorSpace,
            ToneMapper,
            PostEffect,
            ColorGradeConfig,
            PostProcessChain,
            PostProcessManager,
        )
        assert CryptomatteLayer is not None
        assert MatteType is not None
        assert CryptomatteConfig is not None
        assert CryptomattePass is not None
        assert MatteData is not None
        assert CryptomatteManager is not None
        assert PassType is not None
        assert PassCategory is not None
        assert OutputFormat is not None
        assert RenderPass is not None
        assert PassConfig is not None
        assert MultiPassSetup is not None
        assert MultiPassManager is not None
        assert EffectType is not None
        assert ColorSpace is not None
        assert ToneMapper is not None
        assert PostEffect is not None
        assert ColorGradeConfig is not None
        assert PostProcessChain is not None
        assert PostProcessManager is not None

    def test_cryptomatte_functions(self):
        """Test cryptomatte function exports."""
        from lib.compositing import (
            create_cryptomatte_config,
            extract_matte_from_manifest,
        )
        assert callable(create_cryptomatte_config)
        assert callable(extract_matte_from_manifest)

    def test_multi_pass_functions(self):
        """Test multi-pass function exports."""
        from lib.compositing import (
            create_pass_config,
            create_standard_setup,
        )
        assert callable(create_pass_config)
        assert callable(create_standard_setup)

    def test_post_process_functions(self):
        """Test post-process function exports."""
        from lib.compositing import (
            create_color_grade,
            create_glare_effect,
            create_film_grain,
        )
        assert callable(create_color_grade)
        assert callable(create_glare_effect)
        assert callable(create_film_grain)


class TestModuleConstants:
    """Test module-level constants."""

    def test_all_exports(self):
        """Test that __all__ is defined."""
        import lib.compositing as comp
        assert hasattr(comp, '__all__')
        assert isinstance(comp.__all__, list)
        assert len(comp.__all__) > 0

    def test_standard_passes_constant(self):
        """Test STANDARD_PASSES constant."""
        from lib.compositing import STANDARD_PASSES
        assert isinstance(STANDARD_PASSES, dict)
        assert len(STANDARD_PASSES) > 0

    def test_beauty_passes_constant(self):
        """Test BEAUTY_PASSES constant."""
        from lib.compositing import BEAUTY_PASSES
        assert isinstance(BEAUTY_PASSES, list)
        assert len(BEAUTY_PASSES) > 0

    def test_utility_passes_constant(self):
        """Test UTILITY_PASSES constant."""
        from lib.compositing import UTILITY_PASSES
        assert isinstance(UTILITY_PASSES, dict)
        assert len(UTILITY_PASSES) > 0

    def test_data_passes_constant(self):
        """Test DATA_PASSES constant."""
        from lib.compositing import DATA_PASSES
        assert isinstance(DATA_PASSES, list)
        assert len(DATA_PASSES) > 0

    def test_glare_presets_constant(self):
        """Test GLARE_PRESETS constant."""
        from lib.compositing import GLARE_PRESETS
        assert isinstance(GLARE_PRESETS, dict)
        assert len(GLARE_PRESETS) > 0

    def test_default_color_grade_constant(self):
        """Test DEFAULT_COLOR_GRADE constant."""
        from lib.compositing import DEFAULT_COLOR_GRADE
        assert isinstance(DEFAULT_COLOR_GRADE, dict)

    def test_color_correction_defaults_constant(self):
        """Test COLOR_CORRECTION_DEFAULTS constant."""
        from lib.compositing import COLOR_CORRECTION_DEFAULTS
        assert isinstance(COLOR_CORRECTION_DEFAULTS, dict)


class TestEnumValues:
    """Test that enum values are correct."""

    def test_cryptomatte_layer_values(self):
        """Test CryptomatteLayer enum values."""
        from lib.compositing import CryptomatteLayer
        assert CryptomatteLayer.OBJECT.value == "object"
        assert CryptomatteLayer.MATERIAL.value == "material"

    def test_pass_type_values(self):
        """Test PassType enum values."""
        from lib.compositing import PassType
        assert PassType.BEAUTY.value == "beauty"
        assert PassType.NORMAL.value == "normal"

    def test_output_format_values(self):
        """Test OutputFormat enum values."""
        from lib.compositing import OutputFormat
        assert OutputFormat.EXR.value == "exr"
        assert OutputFormat.PNG.value == "png"

    def test_effect_type_values(self):
        """Test EffectType enum values."""
        from lib.compositing import EffectType
        assert EffectType.GLARE.value == "glare"
        assert EffectType.FILM_GRAIN.value == "film_grain"

    def test_color_space_values(self):
        """Test ColorSpace enum values."""
        from lib.compositing import ColorSpace
        assert ColorSpace.SRGB.value == "srgb"
        assert ColorSpace.ACES.value == "aces"
