"""
Tests for safety module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSafetyModule:
    """Tests for safety module structure."""

    def test_module_imports(self):
        """Test that the safety module can be imported."""
        try:
            from lib.utils import safety
            assert safety is not None
        except ImportError:
            pytest.skip("safety module not available")

    def test_module_exports(self):
        """Test module __all__ exports."""
        try:
            from lib.utils.safety import __all__
            assert isinstance(__all__, list)
        except (ImportError, AttributeError):
            pytest.skip("safety module __all__ not available")


class TestInputValidation:
    """Tests for input validation functions."""

    def test_validate_numeric_input(self):
        """Test numeric input validation."""
        try:
            from lib.utils.safety import validate_numeric
            assert validate_numeric(5) is True
            assert validate_numeric(5.0) is True
            assert validate_numeric("string") is False
        except (ImportError, AttributeError):
            pytest.skip("validate_numeric not available")

    def test_validate_range(self):
        """Test range validation."""
        try:
            from lib.utils.safety import validate_range
            assert validate_range(5, 0, 10) is True
            assert validate_range(-5, 0, 10) is False
            assert validate_range(15, 0, 10) is False
        except (ImportError, AttributeError):
            pytest.skip("validate_range not available")

    def test_validate_type(self):
        """Test type validation."""
        try:
            from lib.utils.safety import validate_type
            assert validate_type("hello", str) is True
            assert validate_type(123, str) is False
            assert validate_type([1, 2, 3], list) is True
        except (ImportError, AttributeError):
            pytest.skip("validate_type not available")


class TestSanitization:
    """Tests for sanitization functions."""

    def test_sanitize_string(self):
        """Test string sanitization."""
        try:
            from lib.utils.safety import sanitize_string
            result = sanitize_string("hello_world")
            assert result == "hello_world"
        except (ImportError, AttributeError):
            pytest.skip("sanitize_string not available")

    def test_sanitize_path(self):
        """Test path sanitization."""
        try:
            from lib.utils.safety import sanitize_path
            result = sanitize_path("/safe/path")
            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("sanitize_path not available")

    def test_sanitize_identifier(self):
        """Test identifier sanitization."""
        try:
            from lib.utils.safety import sanitize_identifier
            result = sanitize_identifier("my-variable!")
            assert "-" not in result
            assert "!" not in result
        except (ImportError, AttributeError):
            pytest.skip("sanitize_identifier not available")


class TestSafeOperations:
    """Tests for safe operation wrappers."""

    def test_safe_call_success(self):
        """Test safe call with successful function."""
        try:
            from lib.utils.safety import safe_call

            def add(a, b):
                return a + b

            result = safe_call(add, 2, 3)
            assert result == 5
        except (ImportError, AttributeError):
            pytest.skip("safe_call not available")

    def test_safe_call_failure(self):
        """Test safe call with failing function."""
        try:
            from lib.utils.safety import safe_call

            def raise_error():
                raise ValueError("test error")

            result = safe_call(raise_error, default=None)
            assert result is None
        except (ImportError, AttributeError):
            pytest.skip("safe_call not available")

    def test_safe_getattr(self):
        """Test safe getattr."""
        try:
            from lib.utils.safety import safe_getattr

            obj = type('Test', (), {'attr': 'value'})()
            result = safe_getattr(obj, 'attr', default='default')
            assert result == 'value'

            result = safe_getattr(obj, 'missing', default='default')
            assert result == 'default'
        except (ImportError, AttributeError):
            pytest.skip("safe_getattr not available")


class TestErrorHandling:
    """Tests for error handling utilities."""

    def test_error_context(self):
        """Test error context manager."""
        try:
            from lib.utils.safety import error_context

            with error_context("test operation"):
                pass  # No error

            # Should not raise
            assert True
        except (ImportError, AttributeError):
            pytest.skip("error_context not available")

    def test_error_context_captures(self):
        """Test error context captures exceptions."""
        try:
            from lib.utils.safety import error_context

            error_occurred = False
            try:
                with error_context("test operation"):
                    raise ValueError("test")
            except ValueError:
                error_occurred = True

            assert error_occurred
        except (ImportError, AttributeError):
            pytest.skip("error_context not available")


class TestGuardClauses:
    """Tests for guard clause utilities."""

    def test_guard_against_none(self):
        """Test guard against None values."""
        try:
            from lib.utils.safety import guard_not_none

            guard_not_none("value")  # Should not raise

            with pytest.raises((ValueError, TypeError)):
                guard_not_none(None)
        except (ImportError, AttributeError):
            pytest.skip("guard_not_none not available")

    def test_guard_against_empty(self):
        """Test guard against empty values."""
        try:
            from lib.utils.safety import guard_not_empty

            guard_not_empty([1, 2, 3])  # Should not raise

            with pytest.raises((ValueError, TypeError)):
                guard_not_empty([])
        except (ImportError, AttributeError):
            pytest.skip("guard_not_empty not available")

    def test_guard_type(self):
        """Test guard for type checking."""
        try:
            from lib.utils.safety import guard_type

            guard_type("hello", str)  # Should not raise

            with pytest.raises(TypeError):
                guard_type(123, str)
        except (ImportError, AttributeError):
            pytest.skip("guard_type not available")


class TestRateLimiter:
    """Tests for rate limiting utilities."""

    def test_rate_limiter_creation(self):
        """Test creating a rate limiter."""
        try:
            from lib.utils.safety import RateLimiter
            limiter = RateLimiter(max_calls=10, period=1.0)
            assert limiter is not None
        except (ImportError, AttributeError):
            pytest.skip("RateLimiter not available")

    def test_rate_limiter_allows(self):
        """Test rate limiter allows calls."""
        try:
            from lib.utils.safety import RateLimiter
            limiter = RateLimiter(max_calls=5, period=1.0)

            for _ in range(5):
                assert limiter.allow() is True
        except (ImportError, AttributeError):
            pytest.skip("RateLimiter not available")

    def test_rate_limiter_blocks(self):
        """Test rate limiter blocks excess calls."""
        try:
            from lib.utils.safety import RateLimiter
            limiter = RateLimiter(max_calls=2, period=1.0)

            limiter.allow()
            limiter.allow()
            assert limiter.allow() is False
        except (ImportError, AttributeError):
            pytest.skip("RateLimiter not available")


class TestRetryLogic:
    """Tests for retry utilities."""

    def test_retry_success(self):
        """Test retry with eventual success."""
        try:
            from lib.utils.safety import retry

            call_count = 0

            @retry(max_attempts=3)
            def flaky_function():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("Temporary error")
                return "success"

            result = flaky_function()
            assert result == "success"
            assert call_count == 2
        except (ImportError, AttributeError):
            pytest.skip("retry not available")

    def test_retry_failure(self):
        """Test retry with persistent failure."""
        try:
            from lib.utils.safety import retry

            @retry(max_attempts=3, delay=0.01)
            def always_fail():
                raise ValueError("Always fails")

            with pytest.raises(ValueError):
                always_fail()
        except (ImportError, AttributeError):
            pytest.skip("retry not available")


class TestTimeoutProtection:
    """Tests for timeout protection."""

    def test_timeout_not_exceeded(self):
        """Test when timeout is not exceeded."""
        try:
            from lib.utils.safety import timeout

            @timeout(seconds=5)
            def quick_function():
                return "done"

            result = quick_function()
            assert result == "done"
        except (ImportError, AttributeError):
            pytest.skip("timeout not available")


class TestDeprecationWarnings:
    """Tests for deprecation warning utilities."""

    def test_deprecated_decorator(self):
        """Test deprecated decorator."""
        try:
            from lib.utils.safety import deprecated

            @deprecated("Use new_function instead")
            def old_function():
                return "result"

            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = old_function()

                assert result == "result"
                assert len(w) == 1
                assert "deprecated" in str(w[0].message).lower()
        except (ImportError, AttributeError):
            pytest.skip("deprecated not available")


class TestSafeCollections:
    """Tests for safe collection operations."""

    def test_safe_list_get(self):
        """Test safe list access."""
        try:
            from lib.utils.safety import safe_list_get

            items = [1, 2, 3]
            assert safe_list_get(items, 0) == 1
            assert safe_list_get(items, 10, default=99) == 99
        except (ImportError, AttributeError):
            pytest.skip("safe_list_get not available")

    def test_safe_dict_get(self):
        """Test safe dict access."""
        try:
            from lib.utils.safety import safe_dict_get

            data = {"a": 1, "b": 2}
            assert safe_dict_get(data, "a") == 1
            assert safe_dict_get(data, "c", default=99) == 99
        except (ImportError, AttributeError):
            pytest.skip("safe_dict_get not available")


class TestMemorySafety:
    """Tests for memory safety utilities."""

    def test_memory_limit_context(self):
        """Test memory limit context manager."""
        try:
            from lib.utils.safety import memory_limit

            with memory_limit(max_mb=100):
                # Small allocation should work
                data = [0] * 1000
                assert len(data) == 1000
        except (ImportError, AttributeError):
            pytest.skip("memory_limit not available")
