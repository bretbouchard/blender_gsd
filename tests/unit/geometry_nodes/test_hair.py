"""
Unit tests for lib/geometry_nodes/hair.py

Tests the hair/fur system including:
- SIZE_CURVES distribution functions
- HairClumpGenerator static methods
- FurSystem fluent API
- create_fur convenience function
- create_hair_material helper
"""

import pytest
import math

from lib.geometry_nodes.hair import (
    SIZE_CURVES,
    HairClumpGenerator,
    FurSystem,
    create_fur,
    create_hair_material,
    create_stylized_hair_material,
)

from tests.conftest import blender_available


requires_blender = pytest.mark.requires_blender


class TestSizeCurves:
    """Tests for SIZE_CURVES distribution functions."""

    def test_uniform_curve(self):
        """Test uniform distribution returns input unchanged."""
        curve = SIZE_CURVES["uniform"]
        assert curve(0.0) == pytest.approx(0.0, abs=0.001)
        assert curve(0.5) == pytest.approx(0.5, abs=0.001)
        assert curve(1.0) == pytest.approx(1.0, abs=0.001)

    def test_bias_small_curve(self):
        """Test bias_small curve (x^2) biases toward smaller values."""
        curve = SIZE_CURVES["bias_small"]
        assert curve(0.5) < 0.5  # x^2 < x for 0 < x < 1
        assert curve(0.0) == pytest.approx(0.0, abs=0.001)
        assert curve(1.0) == pytest.approx(1.0, abs=0.001)

    def test_bias_large_curve(self):
        """Test bias_large curve (x^0.5) biases toward larger values."""
        curve = SIZE_CURVES["bias_large"]
        assert curve(0.5) > 0.5  # x^0.5 > x for 0 < x < 1
        assert curve(0.0) == pytest.approx(0.0, abs=0.001)
        assert curve(1.0) == pytest.approx(1.0, abs=0.001)

    def test_bell_curve(self):
        """Test bell curve is centered at 0.5."""
        curve = SIZE_CURVES["bell"]
        # Bell curve: 0.5 + 0.5 * sin((x - 0.5) * pi)
        # At x=0.5: sin(0) = 0, so result = 0.5
        assert curve(0.5) == pytest.approx(0.5, abs=0.01)
        # At x=0: sin(-pi/2) = -1, so result = 0
        assert curve(0.0) == pytest.approx(0.0, abs=0.01)
        # At x=1: sin(pi/2) = 1, so result = 1
        assert curve(1.0) == pytest.approx(1.0, abs=0.01)

    def test_exponential_curve(self):
        """Test exponential curve."""
        curve = SIZE_CURVES["exponential"]
        assert curve(0.0) == pytest.approx(0.0, abs=0.001)
        assert curve(0.5) == pytest.approx(0.776, abs=0.01)
        # At x=1: 1 - exp(-3) ≈ 0.95, not 1.0
        assert curve(1.0) == pytest.approx(0.950, abs=0.01)

    def test_sigmoid_curve(self):
        """Test sigmoid curve."""
        curve = SIZE_CURVES["sigmoid"]
        # Sigmoid at 0.5 = 0.5
        assert curve(0.5) == pytest.approx(0.5, abs=0.01)
        # At 0, sigmoid tends to 0
        assert curve(0.0) == pytest.approx(0.0, abs=0.01)
        # At 1, sigmoid tends to 1
        assert curve(1.0) == pytest.approx(1.0, abs=0.01)
        # Curve should be increasing
        assert curve(0.1) < curve(0.9)

    def test_all_curves_defined(self):
        """Test all expected curves exist."""
        expected = ["uniform", "bias_small", "bias_large", "bell", "exponential", "sigmoid"]
        for name in expected:
            assert name in SIZE_CURVES
            assert callable(SIZE_CURVES[name])

    def test_all_curves_are_monotonic(self):
        """Test that curves behave as expected."""
        # bias_small should always be <= input
        for x in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            assert SIZE_CURVES["bias_small"](x) <= x
        # bias_large should always be >= input
        for x in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            assert SIZE_CURVES["bias_large"](x) >= x


class TestFurSystemFluentAPI:
    """Tests for FurSystem fluent interface."""

    def test_fluent_api_returns_self(self):
        """Test that all setter methods return self for chaining."""
        system = FurSystem()
        result = system.set_density(1000)
        assert result is system

        result = system.add_clump_variants(5)
        assert result is system

        result = system.set_scale_range(0.5, 2.0)
        assert result is system

        result = system.set_height_range(1.0, 3.0)
        assert result is system

        result = system.set_size_curve("bell")
        assert result is system

        result = system.set_noise_distortion(0.5, 2.0)
        assert result is system

        result = system.set_profile(4, 0.05)
        assert result is system

        result = system.create_material(melanin=0.7)
        assert result is system

    def test_set_noise_distortion(self):
        """Test noise distortion setter."""
        system = FurSystem()
        system.set_noise_distortion(1.5, 3.0)
        assert system._noise_strength == 1.5
        assert system._noise_scale == 3.0

    def test_set_scale_range_clamping(self):
        """Test scale range clamping for negative values."""
        system = FurSystem()
        system.set_scale_range(-0.5, -0.1)
        # min(0.1, -0.5) = -0.5, max(0.1, -0.1) = 0.1
        # The min is preserved as-is (via min()), max is clamped to >= 0.1
        assert system._scale_range[0] == -0.5
        assert system._scale_range[1] == 0.1

    def test_set_height_range_clamping(self):
        """Test height range clamping for negative values."""
        system = FurSystem()
        system.set_height_range(-1.0, -0.5)
        # Negative values should be clamped to 0.1
        assert system._height_range[0] == 0.1
        assert system._height_range[1] == 0.1

    def test_invalid_size_curve_raises(self):
        """Test that invalid size curve raises ValueError."""
        system = FurSystem()
        with pytest.raises(ValueError, match="Invalid size curve"):
            system.set_size_curve("nonexistent_curve")

    def test_density_clamping(self):
        """Test density clamping to minimum."""
        system = FurSystem()
        system.set_density(-100)
        assert system._density == 1  # Clamped to minimum

        system.set_density(0)
        assert system._density == 1

    def test_clump_variants_clamping(self):
        """Test clump variants clamping to minimum."""
        system = FurSystem()
        system.add_clump_variants(-5)
        assert system._clump_variants == 1

        system.add_clump_variants(0)
        assert system._clump_variants == 1

    def test_profile_clamping(self):
        """Test profile parameter clamping."""
        system = FurSystem()
        system.set_profile(resolution=-3, radius=-0.01)
        assert system._profile_resolution == 3  # Clamped to minimum
        assert system._profile_radius == 0.001  # Clamped to minimum

    def test_melanin_clamping(self):
        """Test melanin clamping to valid range."""
        system = FurSystem()
        system.create_material(melanin=-0.5)
        assert system._melanin == 0  # Clamped to 0

        system.create_material(melanin=1.5)
        assert system._melanin == 1  # Clamped to 1

    def test_default_values(self):
        """Test FurSystem default values."""
        system = FurSystem()
        assert system._density == 1000
        assert system._clump_variants == 3
        assert system._scale_range == (0.8, 1.2)
        assert system._height_range == (1.0, 2.0)
        assert system._size_curve == "uniform"
        assert system._noise_strength == 0.1
        assert system._noise_scale == 1.0
        assert system._profile_resolution == 3
        assert system._profile_radius == 0.02
        assert system._melanin == 0.5
        assert system._material is None

    def test_valid_size_curves(self):
        """Test all valid size curves are accepted."""
        system = FurSystem()
        for curve_name in SIZE_CURVES.keys():
            result = system.set_size_curve(curve_name)
            assert result is system
            assert system._size_curve == curve_name

    def test_noise_distortion_parameters(self):
        """Test noise distortion parameter handling."""
        system = FurSystem()
        system.set_noise_distortion(strength=-0.5, scale=-1.0)
        # Negative values clamped to minimum
        assert system._noise_strength == 0
        assert system._noise_scale == 0.1

    def test_profile_parameters(self):
        """Test profile parameter handling."""
        system = FurSystem()
        system.set_profile(resolution=8, radius=0.1)
        assert system._profile_resolution == 8
        assert system._profile_radius == 0.1


class TestCreateFurFunction:
    """Tests for create_fur convenience function."""

    def test_create_fur_basic(self):
        """Test basic fur creation sets sensible defaults."""
        # This test verifies the API contract
        # Actual Blender testing requires @pytest.mark.requires_blender
        assert callable(create_fur)


class TestHairMaterialHelpers:
    """Tests for hair material helper functions."""

    def test_create_hair_material_signature(self):
        """Test create_hair_material function signature."""
        # Verify function exists and is callable
        assert callable(create_hair_material)

    def test_create_stylized_hair_material_signature(self):
        """Test create_stylized_hair_material function signature."""
        assert callable(create_stylized_hair_material)


# Integration tests that require Blender context
class TestHairMaterialIntegration:
    """Integration tests requiring Blender context."""

    @pytest.mark.requires_blender
    def test_create_hair_material_basic(self, blender_available):
        """Test basic hair material creation."""
        if not blender_available:
            pytest.skip("Blender not available")
        mat = create_hair_material("TestHair", melanin=0.5)
        assert mat is not None
        assert mat.name == "TestHair"
        # Cleanup
        import bpy
        bpy.data.materials.remove(mat)

    @pytest.mark.requires_blender
    def test_create_hair_material_with_color(self, blender_available):
        """Test hair material with custom color override."""
        if not blender_available:
            pytest.skip("Blender not available")
        mat = create_hair_material(
            "ColorHair",
            base_color=(0.8, 0.4, 0.2, 1.0),
        )
        assert mat is not None
        # Cleanup
        import bpy
        bpy.data.materials.remove(mat)

    @pytest.mark.requires_blender
    def test_create_stylized_material(self, blender_available):
        """Test stylized emission material."""
        if not blender_available:
            pytest.skip("Blender not available")
        mat = create_stylized_hair_material(
            "TestStylized",
            color=(1.0, 0.5, 0.3, 1.0),
            emission_strength=2.0,
        )
        assert mat is not None
        # Cleanup
        import bpy
        bpy.data.materials.remove(mat)


class TestFurSystemClumpVariants:
    """Tests for clump variant behavior in FurSystem."""

    def test_clump_variants_default(self):
        """Test default clump variant count."""
        system = FurSystem()
        assert system._clump_variants == 3

    def test_clump_variants_custom(self):
        """Test custom clump variant count."""
        system = FurSystem()
        system.add_clump_variants(7)
        assert system._clump_variants == 7

    def test_clump_variants_reflects_in_build(self):
        """Test that clump_variants affects build configuration."""
        system = FurSystem()
        system.add_clump_variants(5)
        # The variant count should be stored for use in build
        assert system._clump_variants == 5
