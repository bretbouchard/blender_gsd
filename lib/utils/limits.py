"""
Performance limits and warnings for Blender GSD pipeline.

Provides configurable limits with warnings to prevent system crashes
and maintain real-time performance.

Usage:
    from lib.utils.limits import check_limit, LIMITS, LimitWarning

    # Check and warn
    if check_limit('max_particles', count):
        create_particles(count)
"""

import warnings
import functools
import time
from typing import Dict, Any, Callable, Optional, TypeVar, ParamSpec
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


# ============================================================================
# LIMIT DEFINITIONS
# ============================================================================

@dataclass
class LimitConfig:
    """Configuration for a single limit."""
    value: int
    warn_threshold: float = 0.8  # Warn at 80% of limit
    error_threshold: float = 1.5  # Error at 150% of limit
    description: str = ""
    category: str = "general"


# Default limits - can be overridden per project
LIMITS: Dict[str, LimitConfig] = {
    # Crowd/System limits
    'max_particles': LimitConfig(
        value=5000,
        description="Maximum particle/boid count for crowd simulations",
        category="performance"
    ),
    'max_onion_skins': LimitConfig(
        value=10,
        description="Maximum onion skin ghosts to display",
        category="viewport"
    ),

    # Animation limits
    'max_shape_keys': LimitConfig(
        value=100,
        warn_threshold=0.5,  # Warn at 50 (many shape keys are heavy)
        description="Maximum shape keys for real-time playback",
        category="animation"
    ),
    'max_shape_keys_realtime': LimitConfig(
        value=20,
        description="Maximum actively animated shape keys for 24fps playback",
        category="animation"
    ),
    'max_layers': LimitConfig(
        value=50,
        description="Maximum animation layers in a stack",
        category="animation"
    ),
    'max_keyframes_per_bone': LimitConfig(
        value=1000,
        description="Maximum keyframes per bone per animation",
        category="animation"
    ),

    # Rig limits
    'max_bones': LimitConfig(
        value=500,
        description="Maximum bones for interactive performance",
        category="rigging"
    ),
    'max_bone_chains': LimitConfig(
        value=50,
        description="Maximum bone chains for IK solving",
        category="rigging"
    ),

    # Render limits
    'max_render_samples': LimitConfig(
        value=4096,
        description="Maximum render samples",
        category="render"
    ),
    'max_texture_size': LimitConfig(
        value=8192,
        description="Maximum texture dimension in pixels",
        category="render"
    ),

    # File limits
    'max_yaml_size_mb': LimitConfig(
        value=10,
        description="Maximum YAML file size to load (MB)",
        category="file"
    ),
    'max_pose_bones': LimitConfig(
        value=200,
        description="Maximum bones stored per pose file",
        category="file"
    ),

    # Memory limits
    'max_undo_steps': LimitConfig(
        value=100,
        description="Maximum undo steps in memory",
        category="memory"
    ),
}


# ============================================================================
# CUSTOM WARNING CLASS
# ============================================================================

class LimitWarning(UserWarning):
    """Warning raised when approaching or exceeding limits."""

    def __init__(self, limit_name: str, current: int, limit: int, threshold: float):
        self.limit_name = limit_name
        self.current = current
        self.limit = limit
        self.threshold = threshold

        if threshold >= 1.0:
            msg = f"LIMIT EXCEEDED: {limit_name}={current} exceeds limit of {limit}"
        else:
            msg = f"LIMIT WARNING: {limit_name}={current} is {threshold:.0%} of limit {limit}"

        super().__init__(msg)


class LimitExceededError(RuntimeError):
    """Error raised when limit is exceeded and hard limit is enforced."""
    pass


# ============================================================================
# LIMIT CHECKING
# ============================================================================

def check_limit(
    limit_name: str,
    current_value: int,
    raise_on_exceed: bool = False,
    warn_only: bool = False
) -> bool:
    """
    Check if a value is within configured limits.

    Args:
        limit_name: Name of limit from LIMITS dict
        current_value: Current value to check
        raise_on_exceed: Raise exception if limit exceeded
        warn_only: Only warn, don't return False on exceed

    Returns:
        True if within limits, False if exceeded (unless warn_only)

    Raises:
        LimitExceededError: If raise_on_exceed=True and limit exceeded
        KeyError: If limit_name not found
    """
    if limit_name not in LIMITS:
        raise KeyError(f"Unknown limit: {limit_name}. Available: {list(LIMITS.keys())}")

    config = LIMITS[limit_name]
    limit = config.value
    ratio = current_value / limit if limit > 0 else float('inf')

    # Check error threshold (severe exceed)
    if ratio >= config.error_threshold:
        msg = f"SEVERE: {limit_name}={current_value} is {ratio:.0%} of limit {limit}. {config.description}"
        logger.error(msg)

        if raise_on_exceed:
            raise LimitExceededError(msg)

        warnings.warn(LimitWarning(limit_name, current_value, limit, ratio), stacklevel=3)
        return warn_only

    # Check limit exceeded
    if ratio >= 1.0:
        msg = f"{limit_name}={current_value} exceeds limit {limit}. {config.description}"
        logger.warning(msg)

        if raise_on_exceed:
            raise LimitExceededError(msg)

        warnings.warn(LimitWarning(limit_name, current_value, limit, ratio), stacklevel=3)
        return warn_only

    # Check warning threshold
    if ratio >= config.warn_threshold:
        msg = f"{limit_name}={current_value} is {ratio:.0%} of limit {limit}. {config.description}"
        logger.info(msg)
        warnings.warn(LimitWarning(limit_name, current_value, limit, ratio), stacklevel=3)

    return True


def get_limit(limit_name: str) -> int:
    """Get the current value of a limit."""
    if limit_name not in LIMITS:
        raise KeyError(f"Unknown limit: {limit_name}")
    return LIMITS[limit_name].value


def set_limit(limit_name: str, value: int, description: str = None) -> None:
    """
    Set or update a limit value.

    Args:
        limit_name: Name of limit
        value: New limit value
        description: Optional new description
    """
    if limit_name in LIMITS:
        LIMITS[limit_name].value = value
        if description:
            LIMITS[limit_name].description = description
    else:
        LIMITS[limit_name] = LimitConfig(value=value, description=description or limit_name)

    logger.debug(f"Limit {limit_name} set to {value}")


def get_all_limits() -> Dict[str, Dict[str, Any]]:
    """Get all limits as a dictionary."""
    return {
        name: {
            'value': config.value,
            'description': config.description,
            'category': config.category,
        }
        for name, config in LIMITS.items()
    }


def get_limits_by_category(category: str) -> Dict[str, LimitConfig]:
    """Get all limits in a category."""
    return {
        name: config
        for name, config in LIMITS.items()
        if config.category == category
    }


# ============================================================================
# PERFORMANCE TIMING
# ============================================================================

@dataclass
class PerformanceMetric:
    """Track performance metrics."""
    name: str
    total_time: float = 0.0
    call_count: int = 0
    max_time: float = 0.0
    min_time: float = float('inf')

    @property
    def avg_time(self) -> float:
        return self.total_time / self.call_count if self.call_count > 0 else 0.0


_metrics: Dict[str, PerformanceMetric] = {}
_target_times: Dict[str, float] = {
    'layer_evaluation': 0.01,  # 10ms
    'pose_load': 0.05,  # 50ms
    'onion_skin_update': 0.033,  # 33ms (30fps)
    'ik_solve': 0.005,  # 5ms
    'viseme_apply': 0.001,  # 1ms
}


def timed(target_name: str = None, target_ms: float = None):
    """
    Decorator to time function execution.

    Args:
        target_name: Name for metric (defaults to function name)
        target_ms: Target time in milliseconds

    Usage:
        @timed('layer_blend', target_ms=10)
        def blend_layers(...):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        name = target_name or func.__name__
        target_s = (target_ms / 1000) if target_ms else _target_times.get(name)

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start

                # Update metrics
                if name not in _metrics:
                    _metrics[name] = PerformanceMetric(name=name)

                metric = _metrics[name]
                metric.total_time += elapsed
                metric.call_count += 1
                metric.max_time = max(metric.max_time, elapsed)
                metric.min_time = min(metric.min_time, elapsed)

                # Check target time
                if target_s and elapsed > target_s:
                    logger.warning(
                        f"Performance: {name} took {elapsed*1000:.1f}ms "
                        f"(target: {target_s*1000:.1f}ms)"
                    )

        return wrapper
    return decorator


def get_performance_report() -> Dict[str, Dict[str, float]]:
    """Get performance metrics report."""
    return {
        name: {
            'total_time': m.total_time,
            'call_count': m.call_count,
            'avg_time_ms': m.avg_time * 1000,
            'max_time_ms': m.max_time * 1000,
            'min_time_ms': m.min_time * 1000 if m.min_time != float('inf') else 0,
        }
        for name, m in _metrics.items()
    }


def reset_performance_metrics() -> None:
    """Reset all performance metrics."""
    global _metrics
    _metrics.clear()


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class limit_context:
    """
    Context manager to temporarily change limits.

    Usage:
        with limit_context('max_particles', 10000):
            create_large_crowd()
    """

    def __init__(self, limit_name: str, temp_value: int):
        self.limit_name = limit_name
        self.temp_value = temp_value
        self.original_value = None

    def __enter__(self):
        if self.limit_name in LIMITS:
            self.original_value = LIMITS[self.limit_name].value
            LIMITS[self.limit_name].value = self.temp_value
        return self

    def __exit__(self, *args):
        if self.original_value is not None:
            LIMITS[self.limit_name].value = self.original_value


class performance_block:
    """
    Context manager to time a block of code.

    Usage:
        with performance_block('expensive_operation', target_ms=100) as metric:
            do_expensive_stuff()
        print(f"Took {metric.elapsed_ms:.1f}ms")
    """

    def __init__(self, name: str, target_ms: float = None, warn: bool = True):
        self.name = name
        self.target_ms = target_ms
        self.warn = warn
        self.start_time = 0
        self.elapsed = 0
        self.elapsed_ms = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start_time
        self.elapsed_ms = self.elapsed * 1000

        # Update metrics
        if self.name not in _metrics:
            _metrics[self.name] = PerformanceMetric(name=self.name)

        metric = _metrics[self.name]
        metric.total_time += self.elapsed
        metric.call_count += 1
        metric.max_time = max(metric.max_time, self.elapsed)
        metric.min_time = min(metric.min_time, self.elapsed)

        # Warn if exceeded target
        if self.warn and self.target_ms and self.elapsed_ms > self.target_ms:
            logger.warning(
                f"Performance: {self.name} took {self.elapsed_ms:.1f}ms "
                f"(target: {self.target_ms:.1f}ms)"
            )
