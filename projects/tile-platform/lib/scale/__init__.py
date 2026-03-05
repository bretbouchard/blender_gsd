"""
Scale management package for unlimited tile platforms.

This package provides components for managing large-scale tile platforms
with efficient memory allocation and performance optimization.

Components:
    - ScaleManager: Unlimited tile allocation and platform scaling
    - TileAllocator: Efficient tile ID allocation with object pooling
    - PerformanceOptimizer: Performance optimization for large platforms
"""

from .manager import ScaleManager
from .allocator import TileAllocator
from .optimizer import PerformanceOptimizer

__all__ = [
    'ScaleManager',
    'TileAllocator',
    'PerformanceOptimizer',
]
