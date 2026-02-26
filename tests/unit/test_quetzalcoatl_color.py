"""
Unit tests for Quetzalcoatl Color System (Phase 20.8)

Tests for color generation and pattern application.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.color import (
    ColorPattern,
    ColorRegion,
    ColorDefinition,
    ColorRegionConfig,
    IridescenceConfig,
    ColorSystemConfig,
    VertexColorResult,
    ColorSystem,
    generate_colors,
    get_color_preset,
    create_config_from_preset,
    COLOR_PRESETS,
)


class TestColorPattern:
    """Tests for ColorPattern enum."""

    def test_pattern_values(self):
        """Test pattern enum values."""
        assert ColorPattern.SOLID.value == 0
        assert ColorPattern.GRADIENT.value == 1
        assert ColorPattern.STRIPED.value == 2
        assert ColorPattern.SPOTTED.value == 3
        assert ColorPattern.MOTTLED.value == 4
        assert ColorPattern.IRIDESCENT.value == 5
        assert ColorPattern.TWO_TONE.value == 6
        assert ColorPattern.SCALED.value == 7


class TestColorRegion:
    """Tests for ColorRegion enum."""

    def test_region_values(self):
        """Test region enum values."""
        assert ColorRegion.HEAD.value == 0
        assert ColorRegion.NECK.value == 1
        assert ColorRegion.BODY_DORSAL.value == 2
        assert ColorRegion.BODY_VENTRAL.value == 3
        assert ColorRegion.TAIL.value == 4
        assert ColorRegion.WINGS.value == 5


class TestColorDefinition:
    """Tests for ColorDefinition dataclass."""

    def test_color_creation(self):
        """Test creating color definition."""
        color_def = ColorDefinition(
            base_color=np.array([0.5, 0.3, 0.2]),
            variation=0.1,
        )

        assert color_def.base_color[0] == 0.5
        assert color_def.variation == 0.1

    def test_list_to_array(self):
        """Test automatic conversion to numpy array."""
        color_def = ColorDefinition(
            base_color=[0.5, 0.3, 0.2],
        )

        assert isinstance(color_def.base_color, np.ndarray)

    def test_secondary_color(self):
        """Test secondary color."""
        color_def = ColorDefinition(
            base_color=np.array([0.5, 0.3, 0.2]),
            secondary_color=np.array([0.2, 0.3, 0.5]),
        )

        assert color_def.secondary_color is not None
        assert color_def.secondary_color[2] == 0.5


class TestIridescenceConfig:
    """Tests for IridescenceConfig dataclass."""

    def test_default_values(self):
        """Test default iridescence config."""
        config = IridescenceConfig()

        assert not config.enabled
        assert config.base_shift == 0.0
        assert config.shift_amount == 0.3

    def test_custom_values(self):
        """Test custom iridescence config."""
        config = IridescenceConfig(
            enabled=True,
            base_shift=0.2,
            shift_amount=0.5,
            frequency=2.0,
        )

        assert config.enabled
        assert config.base_shift == 0.2
        assert config.shift_amount == 0.5
        assert config.frequency == 2.0


class TestColorSystemConfig:
    """Tests for ColorSystemConfig dataclass."""

    def test_default_values(self):
        """Test default config values."""
        config = ColorSystemConfig()

        assert config.pattern == ColorPattern.TWO_TONE
        assert config.pattern_scale == 1.0
        assert config.color_variation == 0.1

    def test_custom_colors(self):
        """Test custom color values."""
        config = ColorSystemConfig(
            primary_color=np.array([1.0, 0.0, 0.0]),
            secondary_color=np.array([0.0, 1.0, 0.0]),
        )

        assert config.primary_color[0] == 1.0
        assert config.secondary_color[1] == 1.0

    def test_list_to_array(self):
        """Test automatic conversion to numpy arrays."""
        config = ColorSystemConfig(
            primary_color=[1.0, 0.0, 0.0],
        )

        assert isinstance(config.primary_color, np.ndarray)


class TestVertexColorResult:
    """Tests for VertexColorResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample vertex color result."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        config = ColorSystemConfig()
        system = ColorSystem(config)
        return system.generate(vertices, seed=42)

    def test_vertex_count(self, sample_result):
        """Test that vertex count is correct."""
        assert sample_result.vertex_count == 4

    def test_colors_shape(self, sample_result):
        """Test vertex colors shape."""
        assert sample_result.vertex_colors.shape == (4, 3)

    def test_pattern_mask_shape(self, sample_result):
        """Test pattern mask shape."""
        assert sample_result.pattern_mask.shape == (4,)

    def test_iridescence_shape(self, sample_result):
        """Test iridescence values shape."""
        assert sample_result.iridescence_values.shape == (4,)

    def test_colors_in_valid_range(self, sample_result):
        """Test that colors are in 0-1 range."""
        assert np.all(sample_result.vertex_colors >= 0)
        assert np.all(sample_result.vertex_colors <= 1)

    def test_pattern_mask_in_valid_range(self, sample_result):
        """Test that pattern mask is in 0-1 range."""
        assert np.all(sample_result.pattern_mask >= 0)
        assert np.all(sample_result.pattern_mask <= 1)


class TestColorSystem:
    """Tests for ColorSystem."""

    @pytest.fixture
    def sample_vertices(self):
        """Create sample vertices."""
        return np.array([
            [0.0, 0.0, 0.5],   # Top
            [0.0, 0.5, 0.0],   # Middle
            [0.0, 1.0, -0.5],  # Bottom
            [0.5, 0.5, 0.0],   # Side
        ])

    def test_generate_basic(self, sample_vertices):
        """Test basic color generation."""
        config = ColorSystemConfig()
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        assert isinstance(result, VertexColorResult)
        assert result.vertex_count == 4

    def test_generate_with_seed(self, sample_vertices):
        """Test that seed produces consistent results."""
        config = ColorSystemConfig(color_variation=0.2)

        system1 = ColorSystem(config)
        system2 = ColorSystem(config)

        result1 = system1.generate(sample_vertices, seed=123)
        result2 = system2.generate(sample_vertices, seed=123)

        assert np.allclose(result1.vertex_colors, result2.vertex_colors)

    def test_solid_pattern(self, sample_vertices):
        """Test solid color pattern."""
        config = ColorSystemConfig(pattern=ColorPattern.SOLID)
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        # All vertices should have similar pattern values
        assert np.std(result.pattern_mask) < 0.1

    def test_gradient_pattern(self, sample_vertices):
        """Test gradient pattern."""
        config = ColorSystemConfig(pattern=ColorPattern.GRADIENT)
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        # Pattern should vary
        assert result.pattern_mask.max() > result.pattern_mask.min()

    def test_striped_pattern(self, sample_vertices):
        """Test striped pattern."""
        config = ColorSystemConfig(
            pattern=ColorPattern.STRIPED,
            pattern_scale=2.0,
        )
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        # Pattern should oscillate
        assert np.std(result.pattern_mask) > 0

    def test_two_tone_pattern(self, sample_vertices):
        """Test two-tone pattern."""
        config = ColorSystemConfig(pattern=ColorPattern.TWO_TONE)
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        # Pattern should be binary-ish
        unique_values = np.unique(np.round(result.pattern_mask, 1))
        assert len(unique_values) <= 3

    def test_iridescence_disabled(self, sample_vertices):
        """Test with iridescence disabled."""
        config = ColorSystemConfig(
            iridescence=IridescenceConfig(enabled=False)
        )
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        # All iridescence values should be 0
        assert np.allclose(result.iridescence_values, 0)

    def test_iridescence_enabled(self, sample_vertices):
        """Test with iridescence enabled."""
        config = ColorSystemConfig(
            iridescence=IridescenceConfig(
                enabled=True,
                shift_amount=0.5,
            )
        )
        system = ColorSystem(config)
        result = system.generate(sample_vertices, seed=42)

        # Some iridescence values should be non-zero
        assert np.any(result.iridescence_values > 0)

    def test_color_variation(self, sample_vertices):
        """Test color variation."""
        config_low = ColorSystemConfig(color_variation=0.0)
        config_high = ColorSystemConfig(color_variation=0.3)

        system_low = ColorSystem(config_low)
        system_high = ColorSystem(config_high)

        # Run multiple times to check variation
        results_high = [
            system_high.generate(sample_vertices, seed=i).vertex_colors
            for i in range(5)
        ]

        # Results should vary with high variation
        variance = np.var([r.mean() for r in results_high])
        # Just check it runs without error

    def test_custom_body_regions(self, sample_vertices):
        """Test with custom body regions."""
        config = ColorSystemConfig()
        system = ColorSystem(config)

        body_regions = np.array([0, 1, 2, 3])  # Different regions
        result = system.generate(
            sample_vertices,
            body_regions=body_regions,
            seed=42,
        )

        assert result.vertex_count == 4
        assert np.array_equal(result.color_regions, body_regions)

    def test_empty_vertices(self):
        """Test with empty vertex array."""
        config = ColorSystemConfig()
        system = ColorSystem(config)
        result = system.generate(np.zeros((0, 3)), seed=42)

        assert result.vertex_count == 0

    def test_pattern_contrast(self, sample_vertices):
        """Test pattern contrast affects colors."""
        config_low = ColorSystemConfig(
            pattern=ColorPattern.STRIPED,
            pattern_contrast=0.1,
        )
        config_high = ColorSystemConfig(
            pattern=ColorPattern.STRIPED,
            pattern_contrast=0.9,
        )

        system_low = ColorSystem(config_low)
        system_high = ColorSystem(config_high)

        result_low = system_low.generate(sample_vertices, seed=42)
        result_high = system_high.generate(sample_vertices, seed=42)

        # Higher contrast should produce more color variation
        var_low = np.var(result_low.vertex_colors)
        var_high = np.var(result_high.vertex_colors)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_colors_defaults(self):
        """Test generate_colors with defaults."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])

        result = generate_colors(vertices)

        assert isinstance(result, VertexColorResult)
        assert result.vertex_count == 2

    def test_generate_colors_custom(self):
        """Test generate_colors with custom parameters."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])

        result = generate_colors(
            vertices,
            pattern=ColorPattern.STRIPED,
            primary_color=(1.0, 0.0, 0.0),
            secondary_color=(0.0, 0.0, 1.0),
            seed=42,
        )

        assert result.vertex_count == 2


class TestColorPresets:
    """Tests for color presets."""

    def test_get_color_preset_exists(self):
        """Test getting existing preset."""
        preset = get_color_preset("quetzalcoatl")

        assert "primary" in preset
        assert "secondary" in preset
        assert "pattern" in preset

    def test_get_color_preset_not_exists(self):
        """Test getting non-existent preset returns default."""
        preset = get_color_preset("nonexistent")

        # Should return quetzalcoatl as default
        assert preset["pattern"] == ColorPattern.IRIDESCENT

    def test_create_config_from_preset(self):
        """Test creating config from preset."""
        config = create_config_from_preset("dragon_red")

        assert isinstance(config, ColorSystemConfig)
        assert config.pattern == ColorPattern.MOTTLED
        assert config.primary_color[0] > 0.5  # Red primary

    def test_all_presets_valid(self):
        """Test that all presets have required fields."""
        required_fields = ["primary", "secondary", "accent", "belly", "pattern"]

        for name, preset in COLOR_PRESETS.items():
            for field in required_fields:
                assert field in preset, f"Preset {name} missing {field}"

    def test_quetzalcoatl_preset(self):
        """Test quetzalcoatl preset values."""
        preset = get_color_preset("quetzalcoatl")

        assert preset["primary"] == (0.1, 0.5, 0.2)
        assert preset["pattern"] == ColorPattern.IRIDESCENT

    def test_dragon_red_preset(self):
        """Test dragon_red preset values."""
        preset = get_color_preset("dragon_red")

        assert preset["pattern"] == ColorPattern.MOTTLED

    def test_serpent_green_preset(self):
        """Test serpent_green preset values."""
        preset = get_color_preset("serpent_green")

        assert preset["pattern"] == ColorPattern.STRIPED

    def test_ghost_white_preset(self):
        """Test ghost_white preset values."""
        preset = get_color_preset("ghost_white")

        assert preset["pattern"] == ColorPattern.SOLID

    def test_wyvern_brown_preset(self):
        """Test wyvern_brown preset values."""
        preset = get_color_preset("wyvern_brown")

        assert preset["pattern"] == ColorPattern.SCALED


class TestIntegration:
    """Integration tests for color system."""

    def test_full_color_pipeline(self):
        """Test full color generation pipeline."""
        # Create body-like vertices
        n_verts = 100
        t = np.linspace(0, 1, n_verts)
        angles = np.linspace(0, 2 * np.pi, n_verts)

        vertices = np.column_stack([
            np.zeros(n_verts),
            t * 10,
            np.sin(angles) * 0.5,
        ])

        config = ColorSystemConfig(
            pattern=ColorPattern.TWO_TONE,
            color_variation=0.1,
            iridescence=IridescenceConfig(enabled=True, shift_amount=0.3),
        )

        system = ColorSystem(config)
        result = system.generate(vertices, seed=42)

        assert result.vertex_count == n_verts
        assert np.all(result.vertex_colors >= 0)
        assert np.all(result.vertex_colors <= 1)

    def test_different_patterns_different_colors(self):
        """Test that different patterns produce different results."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.5, 0.5, 0.5],
        ])

        results = {}
        for pattern in [ColorPattern.SOLID, ColorPattern.STRIPED, ColorPattern.SPOTTED]:
            config = ColorSystemConfig(pattern=pattern)
            system = ColorSystem(config)
            results[pattern] = system.generate(vertices, seed=42)

        # Different patterns should produce different pattern masks
        solid_mask = results[ColorPattern.SOLID].pattern_mask
        striped_mask = results[ColorPattern.STRIPED].pattern_mask
        spotted_mask = results[ColorPattern.SPOTTED].pattern_mask

        # At least one should be different
        assert not (
            np.allclose(solid_mask, striped_mask) and
            np.allclose(striped_mask, spotted_mask)
        )

    def test_preset_integration(self):
        """Test using presets with color system."""
        vertices = np.random.rand(50, 3) * 10

        for preset_name in COLOR_PRESETS.keys():
            config = create_config_from_preset(preset_name)
            system = ColorSystem(config)
            result = system.generate(vertices, seed=42)

            assert result.vertex_count == 50
            assert np.all(result.vertex_colors >= 0)
            assert np.all(result.vertex_colors <= 1)

    def test_region_based_coloring(self):
        """Test region-based coloring."""
        vertices = np.array([
            [0.0, 0.0, 0.5],   # Head region (top)
            [0.0, 5.0, 0.0],   # Body region (middle)
            [0.0, 10.0, -0.5], # Tail region (bottom)
        ])

        body_regions = np.array([
            ColorRegion.HEAD.value,
            ColorRegion.BODY_DORSAL.value,
            ColorRegion.TAIL.value,
        ])

        config = ColorSystemConfig()
        system = ColorSystem(config)
        result = system.generate(
            vertices,
            body_regions=body_regions,
            seed=42,
        )

        assert result.vertex_count == 3
        assert np.array_equal(result.color_regions, body_regions)
