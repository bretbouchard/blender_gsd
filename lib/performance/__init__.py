"""
Performance Utilities for Blender GSD Framework

Provides caching, memoization, profiling, and optimization utilities
for high-performance geometry generation and configuration loading.

Key Features:
- LRU cache for YAML/config loading
- Geometry cache with TTL support
- Profiling decorators and context managers
- Lazy loading utilities
- Memory-efficient iterators

Usage:
    from lib.performance import cached, memoize, profiled, CacheManager

    @cached(ttl_seconds=300)
    def load_heavy_config(name: str) -> dict:
        # This will be cached for 5 minutes
        return yaml.safe_load(open(f"configs/{name}.yaml"))

    @memoize(maxsize=128)
    def expensive_calculation(x: float, y: float) -> float:
        return complex_math(x, y)

    @profiled
    def generate_geometry(config: GeometryConfig) -> Mesh:
        # Execution time logged automatically
        return build_mesh(config)
"""

from __future__ import annotations

from .cache import (
    CacheManager,
    cached,
    cached_property,
    clear_all_caches,
    get_cache_stats,
    invalidate_cache,
    set_cache_config,
)
from .memoize import (
    memoize,
    memoize_method,
    clear_memoization_cache,
    get_memoization_stats,
)
from .profiling import (
    Profiler,
    ProfileResult,
    profiled,
    profile_context,
    get_profile_results,
    reset_profiler,
    print_profile_summary,
)
from .lazy import (
    lazy,
    lazy_property,
    LazyLoader,
    LazyDict,
)
from .geometry_cache import (
    GeometryCache,
    cached_geometry,
    get_geometry_cache,
    clear_geometry_cache,
)
from .iterators import (
    chunked,
    batched,
    ProgressIterator,
    memory_efficient_map,
)

__all__ = [
    # Cache
    "CacheManager",
    "cached",
    "cached_property",
    "clear_all_caches",
    "get_cache_stats",
    "invalidate_cache",
    "set_cache_config",
    # Memoize
    "memoize",
    "memoize_method",
    "clear_memoization_cache",
    "get_memoization_stats",
    # Profiling
    "Profiler",
    "ProfileResult",
    "profiled",
    "profile_context",
    "get_profile_results",
    "reset_profiler",
    "print_profile_summary",
    # Lazy
    "lazy",
    "lazy_property",
    "LazyLoader",
    "LazyDict",
    # Geometry Cache
    "GeometryCache",
    "cached_geometry",
    "get_geometry_cache",
    "clear_geometry_cache",
    # Iterators
    "chunked",
    "batched",
    "ProgressIterator",
    "memory_efficient_map",
]

__version__ = "1.0.0"
