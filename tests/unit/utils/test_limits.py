"""
Tests for limits module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import warnings
from unittest.mock import patch, MagicMock


class TestLimitsModule:
    """Tests for limits module structure."""

    def test_module_imports(self):
        """Test that the limits module can be imported."""
        from lib.utils import limits
        assert limits is not None

    def test_module_exports_functions(self):
        """Test module exports expected functions."""
        from lib.utils import limits
        assert hasattr(limits, 'check_limit')
        assert hasattr(limits, 'get_limit')
        assert hasattr(limits, 'set_limit')
        assert hasattr(limits, 'get_all_limits')
        assert hasattr(limits, 'LIMITS')


class TestLimitConfig:
    """Tests for LimitConfig dataclass."""

    def test_limit_config_creation(self):
        """Test creating a LimitConfig."""
        from lib.utils.limits import LimitConfig
        config = LimitConfig(
            value=100,
            warn_threshold=0.8,
            error_threshold=1.5,
            description="Test limit",
            category="test"
        )
        assert config.value == 100
        assert config.warn_threshold == 0.8
        assert config.error_threshold == 1.5
        assert config.description == "Test limit"
        assert config.category == "test"

    def test_limit_config_defaults(self):
        """Test LimitConfig default values."""
        from lib.utils.limits import LimitConfig
        config = LimitConfig(value=100)
        assert config.warn_threshold == 0.8
        assert config.error_threshold == 1.5
        assert config.description == ""
        assert config.category == "general"


class TestLimitWarning:
    """Tests for LimitWarning exception class."""

    def test_limit_warning_creation(self):
        """Test creating a LimitWarning."""
        from lib.utils.limits import LimitWarning
        warning = LimitWarning("max_particles", 5000, 5000, 1.0)
        assert warning.limit_name == "max_particles"
        assert warning.current == 5000
        assert warning.limit == 5000
        assert warning.threshold == 1.0
        assert "EXCEEDED" in str(warning)

    def test_limit_warning_below_threshold(self):
        """Test LimitWarning message below 100%."""
        from lib.utils.limits import LimitWarning
        warning = LimitWarning("max_particles", 4000, 5000, 0.8)
        assert "WARNING" in str(warning)
        assert "80%" in str(warning)


class TestLimitExceededError:
    """Tests for LimitExceededError exception class."""

    def test_limit_exceeded_error(self):
        """Test raising LimitExceededError."""
        from lib.utils.limits import LimitExceededError
        with pytest.raises(LimitExceededError):
            raise LimitExceededError("Limit exceeded")


class TestCheckLimit:
    """Tests for check_limit function."""

    def test_check_limit_within_limit(self):
        """Test check_limit when within limit."""
        from lib.utils.limits import check_limit
        result = check_limit('max_particles', 1000)
        assert result is True

    def test_check_limit_at_warning_threshold(self):
        """Test check_limit at warning threshold."""
        from lib.utils.limits import check_limit, LIMITS
        limit_value = LIMITS['max_particles'].value
        warn_value = int(limit_value * 0.8)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check_limit('max_particles', warn_value)
            assert result is True
            assert len(w) >= 1
            assert "80%" in str(w[0].message)

    def test_check_limit_exceeded(self):
        """Test check_limit when limit exceeded."""
        from lib.utils.limits import check_limit, LIMITS
        limit_value = LIMITS['max_particles'].value
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check_limit('max_particles', limit_value + 100)
            assert result is False
            assert len(w) >= 1

    def test_check_limit_exceeded_warn_only(self):
        """Test check_limit with warn_only=True."""
        from lib.utils.limits import check_limit, LIMITS
        limit_value = LIMITS['max_particles'].value
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check_limit('max_particles', limit_value + 100, warn_only=True)
            assert result is True  # warn_only returns True even when exceeded

    def test_check_limit_unknown_limit(self):
        """Test check_limit with unknown limit name."""
        from lib.utils.limits import check_limit
        with pytest.raises(KeyError):
            check_limit('unknown_limit', 100)

    def test_check_limit_raise_on_exceed(self):
        """Test check_limit with raise_on_exceed=True."""
        from lib.utils.limits import check_limit, LimitExceededError, LIMITS
        limit_value = LIMITS['max_particles'].value
        with pytest.raises(LimitExceededError):
            check_limit('max_particles', limit_value + 100, raise_on_exceed=True)


class TestGetLimit:
    """Tests for get_limit function."""

    def test_get_limit_exists(self):
        """Test get_limit for existing limit."""
        from lib.utils.limits import get_limit, LIMITS
        result = get_limit('max_particles')
        assert result == LIMITS['max_particles'].value

    def test_get_limit_unknown(self):
        """Test get_limit for unknown limit."""
        from lib.utils.limits import get_limit
        with pytest.raises(KeyError):
            get_limit('unknown_limit')


class TestSetLimit:
    """Tests for set_limit function."""

    def test_set_limit_existing(self):
        """Test set_limit for existing limit."""
        from lib.utils.limits import set_limit, get_limit, LIMITS
        original = get_limit('max_particles')
        try:
            set_limit('max_particles', 9999)
            assert get_limit('max_particles') == 9999
        finally:
            LIMITS['max_particles'].value = original

    def test_set_limit_new(self):
        """Test set_limit for new limit."""
        from lib.utils.limits import set_limit, get_limit, LIMITS
        try:
            set_limit('test_limit_new', 500, description="Test limit")
            assert get_limit('test_limit_new') == 500
        finally:
            if 'test_limit_new' in LIMITS:
                del LIMITS['test_limit_new']


class TestGetAllLimits:
    """Tests for get_all_limits function."""

    def test_get_all_limits(self):
        """Test get_all_limits returns dict."""
        from lib.utils.limits import get_all_limits
        result = get_all_limits()
        assert isinstance(result, dict)
        assert 'max_particles' in result
        assert 'value' in result['max_particles']
        assert 'description' in result['max_particles']
        assert 'category' in result['max_particles']


class TestGetLimitsByCategory:
    """Tests for get_limits_by_category function."""

    def test_get_limits_by_category(self):
        """Test getting limits by category."""
        from lib.utils.limits import get_limits_by_category
        result = get_limits_by_category('performance')
        assert isinstance(result, dict)
        # Should include max_particles which is in performance category
        assert 'max_particles' in result

    def test_get_limits_by_category_empty(self):
        """Test getting limits for non-existent category."""
        from lib.utils.limits import get_limits_by_category
        result = get_limits_by_category('nonexistent_category')
        assert result == {}


class TestPerformanceMetric:
    """Tests for PerformanceMetric dataclass."""

    def test_performance_metric_creation(self):
        """Test creating a PerformanceMetric."""
        from lib.utils.limits import PerformanceMetric
        metric = PerformanceMetric(name="test_operation")
        assert metric.name == "test_operation"
        assert metric.total_time == 0.0
        assert metric.call_count == 0
        assert metric.max_time == 0.0

    def test_performance_metric_avg_time(self):
        """Test PerformanceMetric avg_time property."""
        from lib.utils.limits import PerformanceMetric
        metric = PerformanceMetric(name="test", total_time=1.0, call_count=10)
        assert metric.avg_time == 0.1

    def test_performance_metric_avg_time_zero_calls(self):
        """Test PerformanceMetric avg_time with zero calls."""
        from lib.utils.limits import PerformanceMetric
        metric = PerformanceMetric(name="test")
        assert metric.avg_time == 0.0


class TestTimedDecorator:
    """Tests for timed decorator."""

    def test_timed_decorator(self):
        """Test timed decorator tracks metrics."""
        from lib.utils.limits import timed, get_performance_report, reset_performance_metrics
        reset_performance_metrics()

        @timed('test_timed_func', target_ms=1000)
        def test_func():
            return 42

        result = test_func()
        assert result == 42

        report = get_performance_report()
        assert 'test_timed_func' in report
        assert report['test_timed_func']['call_count'] == 1

    def test_timed_decorator_default_name(self):
        """Test timed decorator uses function name by default."""
        from lib.utils.limits import timed, get_performance_report, reset_performance_metrics
        reset_performance_metrics()

        @timed()
        def my_test_function():
            return "done"

        my_test_function()
        report = get_performance_report()
        assert 'my_test_function' in report


class TestGetPerformanceReport:
    """Tests for get_performance_report function."""

    def test_get_performance_report(self):
        """Test getting performance report."""
        from lib.utils.limits import get_performance_report
        result = get_performance_report()
        assert isinstance(result, dict)


class TestResetPerformanceMetrics:
    """Tests for reset_performance_metrics function."""

    def test_reset_performance_metrics(self):
        """Test resetting performance metrics."""
        from lib.utils.limits import (
            reset_performance_metrics, timed, get_performance_report
        )
        reset_performance_metrics()

        @timed('test_reset_func')
        def test_func():
            pass

        test_func()
        assert 'test_reset_func' in get_performance_report()

        reset_performance_metrics()
        # After reset, the metric should be gone or reset
        report = get_performance_report()
        if 'test_reset_func' in report:
            assert report['test_reset_func']['call_count'] == 0


class TestLimitContext:
    """Tests for limit_context context manager."""

    def test_limit_context(self):
        """Test limit_context temporarily changes limit."""
        from lib.utils.limits import limit_context, get_limit, LIMITS
        original = get_limit('max_particles')

        with limit_context('max_particles', 99999):
            assert get_limit('max_particles') == 99999

        assert get_limit('max_particles') == original

    def test_limit_context_unknown_limit(self):
        """Test limit_context with unknown limit (no-op)."""
        from lib.utils.limits import limit_context
        # Should not raise, just do nothing
        with limit_context('unknown_limit', 100):
            pass


class TestPerformanceBlock:
    """Tests for performance_block context manager."""

    def test_performance_block(self):
        """Test performance_block times execution."""
        from lib.utils.limits import performance_block, get_performance_report, reset_performance_metrics
        reset_performance_metrics()

        with performance_block('test_block', target_ms=1000) as metric:
            pass

        assert metric.elapsed > 0
        assert metric.elapsed_ms > 0

        report = get_performance_report()
        assert 'test_block' in report
        assert report['test_block']['call_count'] == 1

    def test_performance_block_no_warn(self):
        """Test performance_block with warn=False."""
        from lib.utils.limits import performance_block, reset_performance_metrics
        reset_performance_metrics()

        with performance_block('test_block_no_warn', target_ms=0.001, warn=False) as metric:
            pass

        # Should not raise even if target exceeded


class TestDefaultLimits:
    """Tests for default LIMITS dictionary."""

    def test_limits_dict_exists(self):
        """Test that LIMITS dict exists and has entries."""
        from lib.utils.limits import LIMITS
        assert isinstance(LIMITS, dict)
        assert len(LIMITS) > 0

    def test_common_limits_exist(self):
        """Test that common limits are defined."""
        from lib.utils.limits import LIMITS
        expected_limits = [
            'max_particles',
            'max_bones',
            'max_render_samples',
            'max_texture_size',
            'max_undo_steps',
        ]
        for limit_name in expected_limits:
            assert limit_name in LIMITS, f"Expected limit '{limit_name}' not found"
