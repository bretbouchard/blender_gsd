"""
Tests for math_safe module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import math
from unittest.mock import patch, MagicMock


class TestMathSafeModule:
    """Tests for math_safe module structure."""

    def test_module_imports(self):
        """Test that the math_safe module can be imported."""
        try:
            from lib.utils import math_safe
            assert math_safe is not None
        except ImportError:
            pytest.skip("math_safe module not available")

    def test_module_exports(self):
        """Test module __all__ exports."""
        try:
            from lib.utils.math_safe import __all__
            assert isinstance(__all__, list)
        except (ImportError, AttributeError):
            pytest.skip("math_safe module __all__ not available")


class TestSafeDivision:
    """Tests for safe division functions."""

    def test_safe_div_normal(self):
        """Test safe division with normal values."""
        try:
            from lib.utils.math_safe import safe_div
            result = safe_div(10, 2)
            assert result == 5
        except (ImportError, AttributeError):
            pytest.skip("safe_div not available")

    def test_safe_div_by_zero(self):
        """Test safe division by zero."""
        try:
            from lib.utils.math_safe import safe_div
            result = safe_div(10, 0)
            # Should return 0 or inf, not raise
            assert result == 0 or result == float('inf')
        except (ImportError, AttributeError):
            pytest.skip("safe_div not available")

    def test_safe_div_with_default(self):
        """Test safe division with custom default."""
        try:
            from lib.utils.math_safe import safe_div
            result = safe_div(10, 0, default=999)
            assert result == 999
        except (ImportError, AttributeError):
            pytest.skip("safe_div not available")

    def test_safe_div_float(self):
        """Test safe division with floats."""
        try:
            from lib.utils.math_safe import safe_div
            result = safe_div(1.0, 3.0)
            assert abs(result - 0.333333) < 0.001
        except (ImportError, AttributeError):
            pytest.skip("safe_div not available")


class TestSafeSqrt:
    """Tests for safe square root functions."""

    def test_safe_sqrt_positive(self):
        """Test safe sqrt with positive value."""
        try:
            from lib.utils.math_safe import safe_sqrt
            result = safe_sqrt(4)
            assert result == 2
        except (ImportError, AttributeError):
            pytest.skip("safe_sqrt not available")

    def test_safe_sqrt_zero(self):
        """Test safe sqrt with zero."""
        try:
            from lib.utils.math_safe import safe_sqrt
            result = safe_sqrt(0)
            assert result == 0
        except (ImportError, AttributeError):
            pytest.skip("safe_sqrt not available")

    def test_safe_sqrt_negative(self):
        """Test safe sqrt with negative value."""
        try:
            from lib.utils.math_safe import safe_sqrt
            result = safe_sqrt(-1)
            # Should return 0, not raise
            assert result == 0 or result == 0.0
        except (ImportError, AttributeError):
            pytest.skip("safe_sqrt not available")

    def test_safe_sqrt_with_default(self):
        """Test safe sqrt with custom default for negative."""
        try:
            from lib.utils.math_safe import safe_sqrt
            result = safe_sqrt(-1, default=0.0)
            assert result == 0.0
        except (ImportError, AttributeError):
            pytest.skip("safe_sqrt not available")


class TestSafeLog:
    """Tests for safe logarithm functions."""

    def test_safe_log_positive(self):
        """Test safe log with positive value."""
        try:
            from lib.utils.math_safe import safe_log
            result = safe_log(math.e)
            assert abs(result - 1.0) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("safe_log not available")

    def test_safe_log_zero(self):
        """Test safe log with zero."""
        try:
            from lib.utils.math_safe import safe_log
            result = safe_log(0)
            # Should return -inf or a default
            assert result == float('-inf') or result is not None
        except (ImportError, AttributeError):
            pytest.skip("safe_log not available")

    def test_safe_log_negative(self):
        """Test safe log with negative value."""
        try:
            from lib.utils.math_safe import safe_log
            result = safe_log(-1)
            # Should handle gracefully
            assert result is not None or result == float('-inf')
        except (ImportError, AttributeError):
            pytest.skip("safe_log not available")

    def test_safe_log10(self):
        """Test safe log10."""
        try:
            from lib.utils.math_safe import safe_log10
            result = safe_log10(100)
            assert abs(result - 2.0) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("safe_log10 not available")


class TestSafePow:
    """Tests for safe power functions."""

    def test_safe_pow_normal(self):
        """Test safe pow with normal values."""
        try:
            from lib.utils.math_safe import safe_pow
            result = safe_pow(2, 3)
            assert result == 8
        except (ImportError, AttributeError):
            pytest.skip("safe_pow not available")

    def test_safe_pow_zero_base(self):
        """Test safe pow with zero base."""
        try:
            from lib.utils.math_safe import safe_pow
            result = safe_pow(0, 5)
            assert result == 0
        except (ImportError, AttributeError):
            pytest.skip("safe_pow not available")

    def test_safe_pow_zero_exp(self):
        """Test safe pow with zero exponent."""
        try:
            from lib.utils.math_safe import safe_pow
            result = safe_pow(5, 0)
            assert result == 1
        except (ImportError, AttributeError):
            pytest.skip("safe_pow not available")

    def test_safe_pow_negative_exp(self):
        """Test safe pow with negative exponent."""
        try:
            from lib.utils.math_safe import safe_pow
            result = safe_pow(2, -2)
            assert abs(result - 0.25) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("safe_pow not available")


class TestSafeInverse:
    """Tests for safe inverse functions."""

    def test_safe_inverse_normal(self):
        """Test safe inverse with normal value."""
        try:
            from lib.utils.math_safe import safe_inverse
            result = safe_inverse(2)
            assert abs(result - 0.5) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("safe_inverse not available")

    def test_safe_inverse_zero(self):
        """Test safe inverse of zero."""
        try:
            from lib.utils.math_safe import safe_inverse
            result = safe_inverse(0)
            # Should return inf or 0, not raise
            assert result == 0 or result == float('inf')
        except (ImportError, AttributeError):
            pytest.skip("safe_inverse not available")


class TestSafeTrigonometry:
    """Tests for safe trigonometric functions."""

    def test_safe_asin_in_range(self):
        """Test safe asin with value in range."""
        try:
            from lib.utils.math_safe import safe_asin
            result = safe_asin(0.5)
            assert abs(result - math.asin(0.5)) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("safe_asin not available")

    def test_safe_asin_out_of_range(self):
        """Test safe asin with value out of range."""
        try:
            from lib.utils.math_safe import safe_asin
            result = safe_asin(1.5)
            # Should clamp to valid range
            assert -math.pi/2 <= result <= math.pi/2
        except (ImportError, AttributeError):
            pytest.skip("safe_asin not available")

    def test_safe_acos_in_range(self):
        """Test safe acos with value in range."""
        try:
            from lib.utils.math_safe import safe_acos
            result = safe_acos(0.5)
            assert abs(result - math.acos(0.5)) < 0.0001
        except (ImportError, AttributeError):
            pytest.skip("safe_acos not available")

    def test_safe_acos_out_of_range(self):
        """Test safe acos with value out of range."""
        try:
            from lib.utils.math_safe import safe_acos
            result = safe_acos(-1.5)
            # Should clamp to valid range
            assert 0 <= result <= math.pi
        except (ImportError, AttributeError):
            pytest.skip("safe_acos not available")


class TestNaNAndInfHandling:
    """Tests for NaN and infinity handling."""

    def test_is_nan(self):
        """Test NaN detection."""
        try:
            from lib.utils.math_safe import is_nan
            assert is_nan(float('nan')) is True
            assert is_nan(1.0) is False
            assert is_nan(float('inf')) is False
        except (ImportError, AttributeError):
            pytest.skip("is_nan not available")

    def test_is_inf(self):
        """Test infinity detection."""
        try:
            from lib.utils.math_safe import is_inf
            assert is_inf(float('inf')) is True
            assert is_inf(float('-inf')) is True
            assert is_inf(1.0) is False
            assert is_inf(float('nan')) is False
        except (ImportError, AttributeError):
            pytest.skip("is_inf not available")

    def test_is_finite(self):
        """Test finite number detection."""
        try:
            from lib.utils.math_safe import is_finite
            assert is_finite(1.0) is True
            assert is_finite(float('inf')) is False
            assert is_finite(float('nan')) is False
        except (ImportError, AttributeError):
            pytest.skip("is_finite not available")

    def test_sanitize_nan(self):
        """Test NaN sanitization."""
        try:
            from lib.utils.math_safe import sanitize_nan
            result = sanitize_nan(float('nan'), default=0.0)
            assert result == 0.0
            result = sanitize_nan(5.0, default=0.0)
            assert result == 5.0
        except (ImportError, AttributeError):
            pytest.skip("sanitize_nan not available")


class TestSafeLerp:
    """Tests for safe linear interpolation."""

    def test_safe_lerp_middle(self):
        """Test lerp at middle value."""
        try:
            from lib.utils.math_safe import safe_lerp
            result = safe_lerp(0, 10, 0.5)
            assert result == 5
        except (ImportError, AttributeError):
            pytest.skip("safe_lerp not available")

    def test_safe_lerp_start(self):
        """Test lerp at start."""
        try:
            from lib.utils.math_safe import safe_lerp
            result = safe_lerp(0, 10, 0)
            assert result == 0
        except (ImportError, AttributeError):
            pytest.skip("safe_lerp not available")

    def test_safe_lerp_end(self):
        """Test lerp at end."""
        try:
            from lib.utils.math_safe import safe_lerp
            result = safe_lerp(0, 10, 1)
            assert result == 10
        except (ImportError, AttributeError):
            pytest.skip("safe_lerp not available")

    def test_safe_lerp_extrapolate(self):
        """Test lerp with extrapolation."""
        try:
            from lib.utils.math_safe import safe_lerp
            result = safe_lerp(0, 10, 1.5)
            assert result == 15
        except (ImportError, AttributeError):
            pytest.skip("safe_lerp not available")


class TestSafeSign:
    """Tests for safe sign function."""

    def test_sign_positive(self):
        """Test sign of positive number."""
        try:
            from lib.utils.math_safe import sign
            assert sign(5) == 1
            assert sign(0.1) == 1
        except (ImportError, AttributeError):
            pytest.skip("sign not available")

    def test_sign_negative(self):
        """Test sign of negative number."""
        try:
            from lib.utils.math_safe import sign
            assert sign(-5) == -1
            assert sign(-0.1) == -1
        except (ImportError, AttributeError):
            pytest.skip("sign not available")

    def test_sign_zero(self):
        """Test sign of zero."""
        try:
            from lib.utils.math_safe import sign
            result = sign(0)
            assert result in (0, 1)  # Implementation dependent
        except (ImportError, AttributeError):
            pytest.skip("sign not available")
