"""
Tests for lib/compositing/post_process.py

Comprehensive tests for post-processing chain without Blender (bpy).
"""

import pytest
import tempfile
import os
import json

from lib.compositing.post_process import (
    EffectType,
    ColorSpace,
    ToneMapper,
    PostEffect,
    ColorGradeConfig,
    PostProcessChain,
    DEFAULT_COLOR_GRADE,
    GLARE_PRESETS,
    COLOR_CORRECTION_DEFAULTS,
    LENS_PRESETS,
    FILM_LOOK_PRESETS,
    PostProcessManager,
    create_color_grade,
    create_glare_effect,
    create_film_grain,
)


class TestEffectType:
    """Tests for EffectType enum."""

    def test_effect_types_exist(self):
        """Test that expected effect types exist."""
        assert hasattr(EffectType, 'COLOR_CORRECTION')
        assert hasattr(EffectType, 'TONE_MAP')
        assert hasattr(EffectType, 'GLARE')
        assert hasattr(EffectType, 'BLOOM')
        assert hasattr(EffectType, 'FILM_GRAIN')
        assert hasattr(EffectType, 'VIGNETTE')
        assert hasattr(EffectType, 'LENS_DISTORTION')

    def test_effect_type_values(self):
        """Test effect type enum values."""
        assert EffectType.COLOR_CORRECTION.value == "color_correction"
        assert EffectType.GLARE.value == "glare"
        assert EffectType.FILM_GRAIN.value == "film_grain"


class TestColorSpace:
    """Tests for ColorSpace enum."""

    def test_color_spaces_exist(self):
        """Test that expected color spaces exist."""
        assert hasattr(ColorSpace, 'SRGB')
        assert hasattr(ColorSpace, 'LINEAR')
        assert hasattr(ColorSpace, 'FILMIC')
        assert hasattr(ColorSpace, 'ACES')
        assert hasattr(ColorSpace, 'AGX')

    def test_color_space_values(self):
        """Test color space enum values."""
        assert ColorSpace.SRGB.value == "srgb"
        assert ColorSpace.ACES.value == "aces"


class TestToneMapper:
    """Tests for ToneMapper enum."""

    def test_tone_mappers_exist(self):
        """Test that expected tone mappers exist."""
        assert hasattr(ToneMapper, 'NONE')
        assert hasattr(ToneMapper, 'FILMIC')
        assert hasattr(ToneMapper, 'ACES')
        assert hasattr(ToneMapper, 'AGX')
        assert hasattr(ToneMapper, 'REINHARD')

    def test_tone_mapper_values(self):
        """Test tone mapper enum values."""
        assert ToneMapper.NONE.value == "none"
        assert ToneMapper.ACES.value == "aces"


class TestPostEffect:
    """Tests for PostEffect dataclass."""

    def test_create_effect(self):
        """Test creating post effect."""
        effect = PostEffect(
            effect_id="test_effect",
            effect_type="glare",
            name="Test Glare",
        )
        assert effect.effect_id == "test_effect"
        assert effect.effect_type == "glare"
        assert effect.name == "Test Glare"

    def test_effect_defaults(self):
        """Test effect defaults."""
        effect = PostEffect()
        assert effect.enabled is True
        assert effect.order == 0
        assert effect.properties == {}

    def test_effect_to_dict(self):
        """Test effect serialization."""
        effect = PostEffect(
            effect_id="test",
            effect_type="film_grain",
            properties={"intensity": 0.5},
        )
        data = effect.to_dict()
        assert data["effect_id"] == "test"
        assert data["effect_type"] == "film_grain"
        assert data["properties"]["intensity"] == 0.5

    def test_effect_from_dict(self):
        """Test effect deserialization."""
        data = {
            "effect_id": "loaded",
            "effect_type": "vignette",
            "name": "Loaded Effect",
            "enabled": False,
            "order": 5,
            "properties": {"radius": 0.8},
        }
        effect = PostEffect.from_dict(data)
        assert effect.effect_id == "loaded"
        assert effect.effect_type == "vignette"
        assert effect.enabled is False
        assert effect.order == 5


class TestColorGradeConfig:
    """Tests for ColorGradeConfig dataclass."""

    def test_create_config(self):
        """Test creating color grade config."""
        config = ColorGradeConfig(
            config_id="test",
            name="Test Grade",
        )
        assert config.config_id == "test"
        assert config.name == "Test Grade"

    def test_config_defaults(self):
        """Test config defaults."""
        config = ColorGradeConfig()
        assert config.exposure == 0.0
        assert config.gamma == 1.0
        assert config.saturation == 1.0
        assert config.use_hdr is True
        assert config.tone_mapper == "filmic"

    def test_config_to_dict(self):
        """Test config serialization."""
        config = ColorGradeConfig(
            config_id="test",
            name="Test",
            exposure=1.5,
            contrast=0.2,
        )
        data = config.to_dict()
        assert data["config_id"] == "test"
        assert data["exposure"] == 1.5
        assert data["contrast"] == 0.2

    def test_config_from_dict(self):
        """Test config deserialization."""
        data = {
            "config_id": "loaded",
            "name": "Loaded",
            "exposure": -0.5,
            "temperature": 25,
            "tint": 10,
            "use_hdr": False,
        }
        config = ColorGradeConfig.from_dict(data)
        assert config.config_id == "loaded"
        assert config.exposure == -0.5
        assert config.temperature == 25
        assert config.use_hdr is False

    def test_rgb_tuples(self):
        """Test RGB tuple fields."""
        config = ColorGradeConfig(
            lift=(0.1, 0.2, 0.3),
            gamma_rgb=(1.1, 1.0, 0.9),
            gain=(1.2, 1.1, 1.0),
        )
        assert config.lift == (0.1, 0.2, 0.3)
        assert config.gamma_rgb == (1.1, 1.0, 0.9)
        assert config.gain == (1.2, 1.1, 1.0)


class TestPostProcessChain:
    """Tests for PostProcessChain dataclass."""

    def test_create_chain(self):
        """Test creating chain."""
        chain = PostProcessChain(
            chain_id="test_chain",
            name="Test Chain",
        )
        assert chain.chain_id == "test_chain"
        assert chain.name == "Test Chain"

    def test_chain_defaults(self):
        """Test chain defaults."""
        chain = PostProcessChain()
        assert chain.effects == []
        assert chain.color_grade is None
        assert chain.input_format == "linear"
        assert chain.output_format == "srgb"
        assert chain.resolution_scale == 1.0

    def test_chain_to_dict(self):
        """Test chain serialization."""
        grade = ColorGradeConfig(config_id="grade1")
        chain = PostProcessChain(
            chain_id="test",
            name="Test",
            color_grade=grade,
        )
        data = chain.to_dict()
        assert data["chain_id"] == "test"
        assert data["color_grade"]["config_id"] == "grade1"

    def test_chain_with_effects(self):
        """Test chain with effects."""
        effect = PostEffect(effect_id="fx1", effect_type="glare")
        chain = PostProcessChain(
            chain_id="test",
            effects=[effect],
        )
        data = chain.to_dict()
        assert len(data["effects"]) == 1


class TestPresets:
    """Tests for preset constants."""

    def test_default_color_grade_exists(self):
        """Test default color grade exists."""
        assert isinstance(DEFAULT_COLOR_GRADE, dict)
        assert "exposure" in DEFAULT_COLOR_GRADE
        assert "gamma" in DEFAULT_COLOR_GRADE

    def test_glare_presets_exist(self):
        """Test glare presets exist."""
        assert isinstance(GLARE_PRESETS, dict)
        assert "ghost" in GLARE_PRESETS
        assert "streak" in GLARE_PRESETS
        assert "fog_glow" in GLARE_PRESETS
        assert "simple_star" in GLARE_PRESETS

    def test_lens_presets_exist(self):
        """Test lens presets exist."""
        assert isinstance(LENS_PRESETS, dict)
        assert "clean" in LENS_PRESETS
        assert "vintage" in LENS_PRESETS
        assert "anamorphic" in LENS_PRESETS

    def test_film_look_presets_exist(self):
        """Test film look presets exist."""
        assert isinstance(FILM_LOOK_PRESETS, dict)
        assert "neutral" in FILM_LOOK_PRESETS
        assert "kodak_2383" in FILM_LOOK_PRESETS
        assert "fuji_3510" in FILM_LOOK_PRESETS
        assert "bleach_bypass" in FILM_LOOK_PRESETS

    def test_color_correction_defaults_exist(self):
        """Test color correction defaults exist."""
        assert isinstance(COLOR_CORRECTION_DEFAULTS, dict)
        assert "master" in COLOR_CORRECTION_DEFAULTS
        assert "shadows" in COLOR_CORRECTION_DEFAULTS
        assert "highlights" in COLOR_CORRECTION_DEFAULTS


class TestPostProcessManager:
    """Tests for PostProcessManager class."""

    def test_create_manager(self):
        """Test creating manager."""
        manager = PostProcessManager()
        assert manager is not None
        assert isinstance(manager.color_grades, dict)
        assert isinstance(manager.chains, dict)

    def test_manager_loads_presets(self):
        """Test that manager loads presets."""
        manager = PostProcessManager()
        assert len(manager.color_grades) > 0
        assert "neutral" in manager.color_grades

    def test_create_color_grade(self):
        """Test creating color grade via manager."""
        manager = PostProcessManager()
        grade = manager.create_color_grade("my_grade", name="My Grade")
        assert grade.config_id == "my_grade"
        assert grade.name == "My Grade"
        assert "my_grade" in manager.color_grades

    def test_create_color_grade_with_preset(self):
        """Test creating color grade with preset."""
        manager = PostProcessManager()
        grade = manager.create_color_grade("custom", preset="kodak_2383")
        assert grade.config_id == "custom"
        # Should inherit from preset
        assert grade.name != ""

    def test_get_color_grade(self):
        """Test getting color grade by ID."""
        manager = PostProcessManager()
        manager.create_color_grade("test_grade")
        grade = manager.get_color_grade("test_grade")
        assert grade is not None
        assert grade.config_id == "test_grade"

    def test_get_color_grade_not_found(self):
        """Test getting non-existent color grade."""
        manager = PostProcessManager()
        grade = manager.get_color_grade("nonexistent")
        assert grade is None

    def test_list_color_grades(self):
        """Test listing color grades."""
        manager = PostProcessManager()
        manager.create_color_grade("grade1")
        manager.create_color_grade("grade2")
        grades = manager.list_color_grades()
        assert len(grades) >= 2

    def test_create_chain(self):
        """Test creating chain via manager."""
        manager = PostProcessManager()
        chain = manager.create_chain("my_chain", name="My Chain")
        assert chain.chain_id == "my_chain"
        assert chain.name == "My Chain"
        assert "my_chain" in manager.chains

    def test_create_chain_with_color_grade(self):
        """Test creating chain with color grade."""
        manager = PostProcessManager()
        grade = manager.create_color_grade("grade1")
        chain = manager.create_chain("chain1", color_grade=grade)
        assert chain.color_grade == grade

    def test_get_chain(self):
        """Test getting chain by ID."""
        manager = PostProcessManager()
        manager.create_chain("test_chain")
        chain = manager.get_chain("test_chain")
        assert chain is not None

    def test_list_chains(self):
        """Test listing chains."""
        manager = PostProcessManager()
        manager.create_chain("chain1")
        manager.create_chain("chain2")
        chains = manager.list_chains()
        assert len(chains) >= 2

    def test_create_effect(self):
        """Test creating effect."""
        manager = PostProcessManager()
        effect = manager.create_effect(
            "fx1",
            "glare",
            name="My Glare",
            properties={"threshold": 0.8},
        )
        assert effect.effect_id == "fx1"
        assert effect.effect_type == "glare"
        assert "fx1" in manager.effects

    def test_add_effect_to_chain(self):
        """Test adding effect to chain."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        effect = manager.add_effect(chain, "glare", {"threshold": 0.9})
        assert len(chain.effects) == 1
        assert effect.effect_type == "glare"

    def test_remove_effect_from_chain(self):
        """Test removing effect from chain."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        effect = manager.add_effect(chain, "glare")
        result = manager.remove_effect(chain, effect.effect_id)
        assert result is True
        assert len(chain.effects) == 0

    def test_remove_effect_not_found(self):
        """Test removing non-existent effect."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        result = manager.remove_effect(chain, "nonexistent")
        assert result is False

    def test_add_glare(self):
        """Test adding glare effect."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        effect = manager.add_glare(chain, preset="fog_glow", threshold=0.5)
        assert effect.effect_type == "glare"
        assert len(chain.effects) == 1

    def test_add_film_grain(self):
        """Test adding film grain effect."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        effect = manager.add_film_grain(chain, intensity=0.2, size=1.5)
        assert effect.effect_type == "film_grain"
        assert effect.properties["intensity"] == 0.2

    def test_add_vignette(self):
        """Test adding vignette effect."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        effect = manager.add_vignette(chain, intensity=0.7, radius=0.9)
        assert effect.effect_type == "vignette"
        assert effect.properties["intensity"] == 0.7

    def test_add_lens_distortion(self):
        """Test adding lens distortion effect."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        effect = manager.add_lens_distortion(chain, preset="vintage")
        assert effect.effect_type == "lens_distortion"

    def test_generate_compositor_setup(self):
        """Test generating compositor setup."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        setup = manager.generate_compositor_setup(chain)
        assert "nodes" in setup
        assert "links" in setup

    def test_generate_compositor_setup_with_color_grade(self):
        """Test generating setup with color grade."""
        manager = PostProcessManager()
        grade = manager.create_color_grade("grade1")
        chain = manager.create_chain("test", color_grade=grade)
        setup = manager.generate_compositor_setup(chain)
        assert "nodes" in setup
        # Should include color balance node
        node_types = [n.get("type") for n in setup["nodes"]]
        assert "CompositorNodeColorBalance" in node_types

    def test_generate_compositor_setup_with_denoise(self):
        """Test generating setup with denoise."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        chain.denoise = True  # Set denoise on the chain directly
        setup = manager.generate_compositor_setup(chain)
        node_types = [n.get("type") for n in setup["nodes"]]
        assert "CompositorNodeDenoise" in node_types

    def test_generate_compositor_setup_to_file(self):
        """Test generating compositor setup to file."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            manager.generate_compositor_setup(chain, temp_path)
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert "nodes" in data
        finally:
            os.unlink(temp_path)

    def test_get_statistics(self):
        """Test getting manager statistics."""
        manager = PostProcessManager()
        stats = manager.get_statistics()
        assert "total_color_grades" in stats
        assert "total_chains" in stats
        assert "total_effects" in stats
        assert "presets_loaded" in stats


class TestCreateColorGrade:
    """Tests for create_color_grade helper."""

    def test_create_grade_basic(self):
        """Test basic grade creation."""
        grade = create_color_grade("Test Grade")
        assert grade is not None
        assert "test_grade" in grade.config_id

    def test_create_grade_with_preset(self):
        """Test grade creation with preset."""
        grade = create_color_grade("Test", preset="kodak_2383")
        assert grade is not None

    def test_create_grade_with_kwargs(self):
        """Test grade creation with kwargs."""
        grade = create_color_grade("Test", exposure=1.5, contrast=0.3)
        assert grade.exposure == 1.5
        assert grade.contrast == 0.3


class TestCreateGlareEffect:
    """Tests for create_glare_effect helper."""

    def test_create_glare_default(self):
        """Test creating glare with defaults."""
        effect = create_glare_effect()
        assert effect is not None
        assert effect.effect_type == "glare"

    def test_create_glare_with_preset(self):
        """Test creating glare with preset."""
        effect = create_glare_effect(preset="streak", threshold=0.7)
        assert effect.properties["preset"] == "streak"
        assert effect.properties["threshold"] == 0.7


class TestCreateFilmGrain:
    """Tests for create_film_grain helper."""

    def test_create_grain_default(self):
        """Test creating grain with defaults."""
        effect = create_film_grain()
        assert effect is not None
        assert effect.effect_type == "film_grain"

    def test_create_grain_with_params(self):
        """Test creating grain with params."""
        effect = create_film_grain(intensity=0.3, size=2.0)
        assert effect.properties["intensity"] == 0.3
        assert effect.properties["size"] == 2.0


class TestPostProcessEdgeCases:
    """Tests for edge cases."""

    def test_chain_with_multiple_effects(self):
        """Test chain with multiple effects."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        manager.add_glare(chain)
        manager.add_film_grain(chain)
        manager.add_vignette(chain)
        assert len(chain.effects) == 3

    def test_effect_ordering(self):
        """Test effect ordering."""
        manager = PostProcessManager()
        chain = manager.create_chain("test")
        manager.add_effect(chain, "glare", order=2)
        manager.add_effect(chain, "film_grain", order=0)
        manager.add_effect(chain, "vignette", order=1)
        # Effects should be sorted by order
        assert chain.effects[0].order == 0
        assert chain.effects[1].order == 1
        assert chain.effects[2].order == 2

    def test_disabled_effect(self):
        """Test disabled effect."""
        effect = PostEffect(effect_id="test", enabled=False)
        assert effect.enabled is False

    def test_chain_with_curves(self):
        """Test color grade with curves."""
        grade = ColorGradeConfig(
            curves={"master": [(0, 0), (0.5, 0.55), (1, 1)]}
        )
        assert "master" in grade.curves

    def test_chain_resolution_scale(self):
        """Test chain resolution scale."""
        chain = PostProcessChain(resolution_scale=0.5)
        assert chain.resolution_scale == 0.5
