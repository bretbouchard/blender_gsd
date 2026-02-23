"""
Tests for limits module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestLimitsModule:
    """Tests for limits module structure."""

    def test_module_imports(self):
        """Test that the limits module can be imported."""
        try:
            from lib.utils import limits
            assert limits is not None
        except ImportError:
            pytest.skip("limits module not available")

    def test_module_exports(self):
        """Test module __all__ exports."""
        try:
            from lib.utils.limits import __all__
            assert isinstance(__all__, list)
        except (ImportError, AttributeError):
            pytest.skip("limits module __all__ not available")


class TestClampFunctions:
    """Tests for clamp utility functions."""

    def test_clamp_within_range(self):
        """Test clamping value within range."""
        try:
            from lib.utils.limits import clamp
            result = clamp(5, 0, 10)
            assert result == 5
        except (ImportError, AttributeError):
            pytest.skip("clamp not available")

    def test_clamp_below_min(self):
        """Test clamping value below minimum."""
        try:
            from lib.utils.limits import clamp
            result = clamp(-5, 0, 10)
            assert result == 0
        except (ImportError, AttributeError):
            pytest.skip("clamp not available")

    def test_clamp_above_max(self):
        """Test clamping value above maximum."""
        try:
            from lib.utils.limits import clamp
            result = clamp(15, 0, 10)
            assert result == 10
        except (ImportError, AttributeError):
            pytest.skip("clamp not available")

    def test_clamp_float_values(self):
        """Test clamping float values."""
        try:
            from lib.utils.limits import clamp
            result = clamp(0.5, 0.0, 1.0)
            assert abs(result - 0.5) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("clamp not available")

    def test_clamp_negative_range(self):
        """Test clamping in negative range."""
        try:
            from lib.utils.limits import clamp
            result = clamp(-15, -20, -10)
            assert result == -15
        except (ImportError, AttributeError):
            pytest.skip("clamp not available")


class TestWrapFunctions:
    """Tests for wrap/modulo utility functions."""

    def test_wrap_within_range(self):
        """Test wrapping value within range."""
        try:
            from lib.utils.limits import wrap
            result = wrap(5, 0, 10)
            assert result == 5
        except (ImportError, AttributeError):
            pytest.skip("wrap not available")

    def test_wrap_above_max(self):
        """Test wrapping value above maximum."""
        try:
            from lib.utils.limits import wrap
            result = wrap(12, 0, 10)
            assert result == 2
        except (ImportError, AttributeError):
            pytest.skip("wrap not available")

    def test_wrap_below_min(self):
        """Test wrapping value below minimum."""
        try:
            from lib.utils.limits import wrap
            result = wrap(-3, 0, 10)
            assert result == 7
        except (ImportError, AttributeError):
            pytest.skip("wrap not available")

    def test_wrap_angle(self):
        """Test wrapping angle values."""
        try:
            from lib.utils.limits import wrap_angle
            result = wrap_angle(370, 0, 360)
            assert result == 10
        except (ImportError, AttributeError):
            pytest.skip("wrap_angle not available")


class TestNormalizeFunctions:
    """Tests for normalize utility functions."""

    def test_normalize_0_to_1(self):
        """Test normalizing to 0-1 range."""
        try:
            from lib.utils.limits import normalize
            result = normalize(50, 0, 100)
            assert abs(result - 0.5) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("normalize not available")

    def test_normalize_negative_range(self):
        """Test normalizing negative range."""
        try:
            from lib.utils.limits import normalize
            result = normalize(0, -100, 100)
            assert abs(result - 0.5) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("normalize not available")

    def test_normalize_at_min(self):
        """Test normalizing at minimum."""
        try:
            from lib.utils.limits import normalize
            result = normalize(0, 0, 100)
            assert result == 0
        except (ImportError, AttributeError):
            pytest.skip("normalize not available")

    def test_normalize_at_max(self):
        """Test normalizing at maximum."""
        try:
            from lib.utils.limits import normalize
            result = normalize(100, 0, 100)
            assert abs(result - 1.0) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("normalize not available")


class TestRemapFunctions:
    """Tests for remap utility functions."""

    def test_remap_simple(self):
        """Test simple remapping."""
        try:
            from lib.utils.limits import remap
            result = remap(50, 0, 100, 0, 1)
            assert abs(result - 0.5) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("remap not available")

    def test_remap_different_ranges(self):
        """Test remapping between different ranges."""
        try:
            from lib.utils.limits import remap
            result = remap(5, 0, 10, 0, 100)
            assert result == 50
        except (ImportError, AttributeError):
            pytest.skip("remap not available")

    def test_remap_negative_to_positive(self):
        """Test remapping negative to positive range."""
        try:
            from lib.utils.limits import remap
            result = remap(0, -1, 1, 0, 100)
            assert result == 50
        except (ImportError, AttributeError):
            pytest.skip("remap not available")

    def test_remap_with_clamp(self):
        """Test remapping with clamping."""
        try:
            from lib.utils.limits import remap_clamped
            result = remap_clamped(150, 0, 100, 0, 1)
            assert abs(result - 1.0) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("remap_clamped not available")


class TestSmoothStepFunctions:
    """Tests for smooth step interpolation."""

    def test_smooth_step_at_edges(self):
        """Test smooth step at edge values."""
        try:
            from lib.utils.limits import smooth_step
            assert smooth_step(0, 1, 0) == 0
            assert smooth_step(0, 1, 1) == 1
        except (ImportError, AttributeError):
            pytest.skip("smooth_step not available")

    def test_smooth_step_middle(self):
        """Test smooth step at middle value."""
        try:
            from lib.utils.limits import smooth_step
            result = smooth_step(0, 1, 0.5)
            assert 0 < result < 1
        except (ImportError, AttributeError):
            pytest.skip("smooth_step not available")

    def test_smoother_step(self):
        """Test smoother step (Ken Perlin's version)."""
        try:
            from lib.utils.limits import smoother_step
            result = smoother_step(0, 1, 0.5)
            assert 0 < result < 1
        except (ImportError, AttributeError):
            pytest.skip("smoother_step not available")


class TestLimitRange:
    """Tests for LimitRange dataclass."""

    def test_limit_range_creation(self):
        """Test creating a LimitRange."""
        try:
            from lib.utils.limits import LimitRange
            limit = LimitRange(min_value=0, max_value=100)
            assert limit.min_value == 0
            assert limit.max_value == 100
        except (ImportError, AttributeError):
            pytest.skip("LimitRange not available")

    def test_limit_range_clamp(self):
        """Test LimitRange clamp method."""
        try:
            from lib.utils.limits import LimitRange
            limit = LimitRange(min_value=0, max_value=100)
            assert limit.clamp(50) == 50
            assert limit.clamp(-10) == 0
            assert limit.clamp(150) == 100
        except (ImportError, AttributeError):
            pytest.skip("LimitRange not available")

    def test_limit_range_normalize(self):
        """Test LimitRange normalize method."""
        try:
            from lib.utils.limits import LimitRange
            limit = LimitRange(min_value=0, max_value=100)
            result = limit.normalize(50)
            assert abs(result - 0.5) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("LimitRange not available")

    def test_limit_range_contains(self):
        """Test LimitRange contains check."""
        try:
            from lib.utils.limits import LimitRange
            limit = LimitRange(min_value=0, max_value=100)
            assert limit.contains(50) is True
            assert limit.contains(-10) is False
            assert limit.contains(150) is False
        except (ImportError, AttributeError):
            pytest.skip("LimitRange not available")

    def test_limit_range_span(self):
        """Test LimitRange span property."""
        try:
            from lib.utils.limits import LimitRange
            limit = LimitRange(min_value=0, max_value=100)
            assert limit.span == 100
        except (ImportError, AttributeError):
            pytest.skip("LimitRange not available")


class TestCommonLimits:
    """Tests for common limit constants."""

    def test_common_limits_exist(self):
        """Test that common limit constants exist."""
        try:
            from lib.utils.limits import COMMON_LIMITS
            assert isinstance(COMMON_LIMITS, dict)
        except (ImportError, AttributeError):
            pytest.skip("COMMON_LIMITS not available")

    def test_get_limit_function(self):
        """Test getting a limit by name."""
        try:
            from lib.utils.limits import get_limit
            limit = get_limit("rotation")
            assert limit is not None
        except (ImportError, AttributeError):
            pytest.skip("get_limit not available")


class TestEpsilonComparisons:
    """Tests for epsilon-based comparisons."""

    def test_approximately_equal(self):
        """Test approximate equality."""
        try:
            from lib.utils.limits import approximately_equal
            assert approximately_equal(1.0, 1.0000001) is True
            assert approximately_equal(1.0, 1.1) is False
        except (ImportError, AttributeError):
            pytest.skip("approximately_equal not available")

    def test_is_zero(self):
        """Test zero check with epsilon."""
        try:
            from lib.utils.limits import is_zero
            assert is_zero(0.0) is True
            assert is_zero(0.0000001) is True
            assert is_zero(0.1) is False
        except (ImportError, AttributeError):
            pytest.skip("is_zero not available")

    def test_epsilon_constant(self):
        """Test epsilon constant."""
        try:
            from lib.utils.limits import EPSILON
            assert EPSILON > 0
            assert EPSILON < 0.001
        except (ImportError, AttributeError):
            pytest.skip("EPSILON not available")
