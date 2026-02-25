"""
Unit tests for lib/sd_projection/style_blender.py

Tests style blending and drift animation functionality including:
- DriftConfig configuration
- StyleBlendConfig and StyleLayer
- DriftPattern enum and patterns
- StyleBlender material application
- StyleAnimator keyframe generation

Note: bpy and mathutils are mocked globally in tests/unit/conftest.py
"""

import pytest
from pathlib import Path
from dataclasses import asdict
from unittest.mock import Mock, patch, MagicMock
import math


class TestDriftConfig:
    """Tests for DriftConfig dataclass."""

    def test_default_drift_config(self):
        """Test default DriftConfig values."""
        from lib.sd_projection.style_blender import DriftConfig

        config = DriftConfig()

        assert config.enabled is True
        assert config.speed == 0.1
        assert config.direction == (1.0, 0.0)
        assert config.noise_enabled is True
        assert config.noise_scale == 5.0
        assert config.noise_strength == 0.2
        assert config.wave_enabled is True
        assert config.wave_amplitude == 0.05
        assert config.wave_frequency == 2.0

    def test_drift_config_with_values(self):
        """Test DriftConfig with custom values."""
        from lib.sd_projection.style_blender import DriftConfig, DriftPattern

        config = DriftConfig(
            enabled=True,
            speed=0.15,
            direction=(0.5, 0.5),
            noise_enabled=True,
            noise_strength=0.4,
            wave_amplitude=0.1,
            pattern=DriftPattern.CHAOS,
        )

        assert config.speed == 0.15
        assert config.direction == (0.5, 0.5)
        assert config.noise_strength == 0.4
        assert config.pattern == DriftPattern.CHAOS


class TestDriftPattern:
    """Tests for DriftPattern enum."""

    def test_pattern_types(self):
        """Test all DriftPattern enum values."""
        from lib.sd_projection.style_blender import DriftPattern

        assert DriftPattern.LINEAR.value == "linear"
        assert DriftPattern.RADIAL.value == "radial"
        assert DriftPattern.SPIRAL.value == "spiral"
        assert DriftPattern.CHAOS.value == "chaos"
        assert DriftPattern.WAVE.value == "wave"
        assert DriftPattern.PULSE.value == "pulse"


class TestStyleLayer:
    """Tests for StyleLayer dataclass."""

    def test_default_style_layer(self):
        """Test StyleLayer default values."""
        from lib.sd_projection.style_blender import StyleLayer

        layer = StyleLayer(name="cyberpunk")

        assert layer.name == "cyberpunk"
        assert layer.weight == 1.0
        assert layer.lora_path == ""
        assert layer.checkpoint == ""
        assert layer.prompt_suffix == ""
        assert layer.animate_weight is False
        assert layer.weight_keyframes == {}

    def test_style_layer_with_values(self):
        """Test StyleLayer with custom values."""
        from lib.sd_projection.style_blender import StyleLayer

        layer = StyleLayer(
            name="noir",
            weight=0.8,
            lora_path="/models/noir.safetensors",
            checkpoint="sd15_noir.ckpt",
            prompt_suffix="noir style",
        )

        assert layer.name == "noir"
        assert layer.weight == 0.8
        assert layer.lora_path == "/models/noir.safetensors"
        assert layer.checkpoint == "sd15_noir.ckpt"
        assert layer.prompt_suffix == "noir style"


class TestBlendMode:
    """Tests for BlendMode enum."""

    def test_blend_modes(self):
        """Test all BlendMode enum values."""
        from lib.sd_projection.style_blender import BlendMode

        assert BlendMode.LINEAR.value == "linear"
        assert BlendMode.SMOOTH.value == "smooth"
        assert BlendMode.EASE_IN.value == "ease_in"
        assert BlendMode.EASE_OUT.value == "ease_out"
        assert BlendMode.EASE_IN_OUT.value == "ease_in_out"
        assert BlendMode.BOUNCE.value == "bounce"
        assert BlendMode.RANDOM.value == "random"


class TestStyleBlendConfig:
    """Tests for StyleBlendConfig dataclass."""

    def test_default_config(self):
        """Test default StyleBlendConfig."""
        from lib.sd_projection.style_blender import StyleBlendConfig

        config = StyleBlendConfig()

        assert config.styles == []
        assert config.blend_mode.value == "smooth"
        assert config.blend_value == 0.5
        assert config.crossfade_duration == 30.0

    def test_config_with_styles(self):
        """Test StyleBlendConfig with styles."""
        from lib.sd_projection.style_blender import (
            StyleBlendConfig,
            StyleLayer,
        )

        config = StyleBlendConfig(
            styles=[
                StyleLayer(name="base", weight=0.6),
                StyleLayer(name="detail", weight=0.4),
            ],
            crossfade_duration=60.0,
        )

        assert len(config.styles) == 2
        assert config.crossfade_duration == 60.0


class TestDriftPatternGenerator:
    """Tests for DriftPatternGenerator."""

    def test_linear_pattern(self):
        """Test LINEAR drift pattern calculation."""
        from lib.sd_projection.style_blender import (
            DriftPatternGenerator,
            DriftPattern,
            DriftConfig,
        )

        config = DriftConfig(
            pattern=DriftPattern.LINEAR,
            direction=(1.0, 0.0),
            speed=0.1,
        )

        # Test static method with uv and time
        uv = (0.5, 0.5)
        result = DriftPatternGenerator.linear(uv, time=10.0, config=config)
        assert len(result) == 2
        # Linear should move in consistent direction
        assert result[0] != uv[0] or result[1] != uv[1]

    def test_radial_pattern(self):
        """Test RADIAL drift pattern calculation."""
        from lib.sd_projection.style_blender import (
            DriftPatternGenerator,
            DriftPattern,
            DriftConfig,
        )

        config = DriftConfig(
            pattern=DriftPattern.RADIAL,
            speed=0.1,
        )

        uv = (0.5, 0.5)
        result = DriftPatternGenerator.radial(uv, time=10.0, config=config)
        assert len(result) == 2

    def test_spiral_pattern(self):
        """Test SPIRAL drift pattern calculation."""
        from lib.sd_projection.style_blender import (
            DriftPatternGenerator,
            DriftPattern,
            DriftConfig,
        )

        config = DriftConfig(
            pattern=DriftPattern.SPIRAL,
            speed=0.1,
        )

        uv = (0.5, 0.5)
        result = DriftPatternGenerator.spiral(uv, time=10.0, config=config)
        assert len(result) == 2

    def test_chaos_pattern(self):
        """Test CHAOS drift pattern calculation."""
        from lib.sd_projection.style_blender import (
            DriftPatternGenerator,
            DriftPattern,
            DriftConfig,
        )

        config = DriftConfig(
            pattern=DriftPattern.CHAOS,
            noise_enabled=True,
            noise_strength=0.3,
        )

        # Chaos should produce different offsets
        uv = (0.5, 0.5)
        result1 = DriftPatternGenerator.chaos(uv, time=10.0, config=config)
        result2 = DriftPatternGenerator.chaos(uv, time=20.0, config=config)

        # Both should be 2D offsets
        assert len(result1) == 2
        assert len(result2) == 2


class TestStyleBlender:
    """Tests for StyleBlender class."""

    def test_blender_initialization(self):
        """Test StyleBlender initialization."""
        from lib.sd_projection.style_blender import StyleBlender, DriftConfig

        config = DriftConfig(speed=0.2)
        blender = StyleBlender(drift_config=config)

        assert blender.drift_config.speed == 0.2

    def test_blender_default_config(self):
        """Test StyleBlender with default config."""
        from lib.sd_projection.style_blender import StyleBlender

        blender = StyleBlender()

        assert blender.drift_config.enabled is True


class TestStyleAnimator:
    """Tests for StyleAnimator class."""

    def test_animator_initialization(self):
        """Test StyleAnimator initialization."""
        from lib.sd_projection.style_blender import StyleAnimator, StyleBlendConfig

        config = StyleBlendConfig()
        animator = StyleAnimator(config)

        assert animator is not None
        assert animator.config == config

    def test_get_blend_at_frame(self):
        """Test blend calculation at different frames."""
        from lib.sd_projection.style_blender import StyleAnimator, StyleBlendConfig

        config = StyleBlendConfig()
        animator = StyleAnimator(config)

        # Add keyframes
        animator.add_keyframe(0, 0.0)
        animator.add_keyframe(30, 1.0)

        # Test blend at different points
        blend_0 = animator.get_blend_at_frame(0)
        blend_15 = animator.get_blend_at_frame(15)
        blend_30 = animator.get_blend_at_frame(30)

        # Blend should be between 0 and 1
        assert 0.0 <= blend_0 <= 1.0
        assert 0.0 <= blend_15 <= 1.0
        assert 0.0 <= blend_30 <= 1.0

    def test_create_blend_animation(self):
        """Test creating blend animation."""
        from lib.sd_projection.style_blender import StyleAnimator, StyleBlendConfig

        config = StyleBlendConfig()
        animator = StyleAnimator(config)

        animator.create_blend_animation(
            start_frame=0,
            end_frame=60,
            start_blend=0.0,
            end_blend=1.0,
        )

        # Should have two keyframes
        assert len(animator._keyframes) == 2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_drift_material(self):
        """Test create_drift_material convenience function."""
        from lib.sd_projection.style_blender import (
            create_drift_material,
            DriftConfig,
        )

        config = DriftConfig(speed=0.15)
        # Function exists and accepts config
        assert create_drift_material is not None

    def test_create_style_crossfade(self):
        """Test create_style_crossfade convenience function."""
        from lib.sd_projection.style_blender import (
            create_style_crossfade,
            StyleBlendConfig,
            StyleLayer,
        )

        # Function exists
        assert create_style_crossfade is not None

        # Create crossfade
        animator = create_style_crossfade(
            styles=["style1", "style2"],
            duration_frames=60,
        )

        assert animator is not None
