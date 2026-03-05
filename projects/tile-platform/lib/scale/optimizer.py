"""
Performance optimization for large-scale tile platforms.

This module provides the PerformanceOptimizer class for maintaining
performance and managing resources at scale (100+ tiles).
"""

from typing import Dict, List, Any, Optional
import time
import sys
sys.path.insert(0, '/Users/bretbouchard/apps/blender_gsd/projects/tile-platform')

from .manager import ScaleManager


class PerformanceOptimizer:
    """Optimizes performance for large-scale tile platforms.

    Provides performance monitoring, bottleneck identification, and
    optimization strategies for platforms with 100+ tiles.

    Attributes:
        scale_manager: The scale manager to optimize
        performance_metrics: Dictionary of performance measurements
        optimization_settings: Configuration for optimization strategies
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        enable_lod: bool = True,
        enable_spatial_partitioning: bool = True
    ) -> None:
        """Initialize the performance optimizer.

        Args:
            scale_manager: ScaleManager instance to optimize
            enable_lod: Enable level-of-detail optimization (default True)
            enable_spatial_partitioning: Enable spatial partitioning (default True)
        """
        self.scale_manager = scale_manager
        self.performance_metrics: Dict[str, float] = {}
        self.optimization_settings = {
            'lod_enabled': enable_lod,
            'spatial_partitioning_enabled': enable_spatial_partitioning,
            'lod_distance_threshold': 50.0,  # Tiles beyond this use simplified geometry
            'instancing_threshold': 10,  # Use instancing for 10+ repeated geometries
        }

    def optimize_for_tile_count(self, count: int) -> Dict[str, Any]:
        """Adjust system parameters for optimal performance at given tile count.

        Args:
            count: Expected number of tiles

        Returns:
            Dictionary with optimization results and recommendations
        """
        results: Dict[str, Any] = {
            'tile_count': count,
            'optimizations_applied': [],
            'recommendations': []
        }

        # Adjust pool size based on tile count
        current_stats = self.scale_manager.allocator.get_stats()
        if count > current_stats['total']:
            # Need to expand pool
            expansion = count - current_stats['total']
            self.scale_manager.allocator._expand_pool(expansion)
            results['optimizations_applied'].append(
                f'Expanded pool by {expansion} tiles'
            )

        # Enable/disable optimizations based on scale
        if count > 100:
            if not self.optimization_settings['lod_enabled']:
                self.optimization_settings['lod_enabled'] = True
                results['optimizations_applied'].append('Enabled LOD optimization')

            if not self.optimization_settings['spatial_partitioning_enabled']:
                self.optimization_settings['spatial_partitioning_enabled'] = True
                results['optimizations_applied'].append('Enabled spatial partitioning')

            # Increase LOD threshold for very large platforms
            if count > 500:
                self.optimization_settings['lod_distance_threshold'] = 100.0
                results['optimizations_applied'].append('Increased LOD threshold to 100.0')

        # Memory optimization for large counts
        if count > 200:
            self.scale_manager.optimize_layout()
            results['optimizations_applied'].append('Optimized tile layout for cache performance')

        # Generate recommendations
        if count > 1000:
            results['recommendations'].append(
                'Consider chunking tiles into regions for better memory management'
            )
        if count > 500:
            results['recommendations'].append(
                'Monitor memory usage closely - consider tile streaming for distant tiles'
            )

        return results

    def benchmark_performance(self, duration: float = 1.0) -> Dict[str, float]:
        """Measure system performance over a duration.

        Args:
            duration: Duration to measure in seconds (default 1.0)

        Returns:
            Dictionary with performance metrics:
            - allocation_rate: Tiles allocated per second
            - release_rate: Tiles released per second
            - avg_operation_time_ms: Average operation time in milliseconds
        """
        # Simple benchmark: measure allocation/release operations
        operations = 0
        start_time = time.time()

        # Perform test allocations
        test_ids = []
        while (time.time() - start_time) < duration:
            # Allocate a tile
            tile_id = self.scale_manager.allocator.allocate()
            test_ids.append(tile_id)
            operations += 1

            # Release every other tile to test both paths
            if len(test_ids) > 10:
                release_id = test_ids.pop(0)
                self.scale_manager.allocator.release(release_id)
                operations += 1

        elapsed = time.time() - start_time

        # Clean up test IDs
        for tile_id in test_ids:
            self.scale_manager.allocator.release(tile_id)

        # Calculate metrics
        allocation_rate = operations / elapsed
        avg_operation_time_ms = (elapsed / operations) * 1000 if operations > 0 else 0.0

        self.performance_metrics = {
            'allocation_rate': allocation_rate,
            'release_rate': allocation_rate / 2,  # Approximately half were releases
            'avg_operation_time_ms': avg_operation_time_ms,
            'total_operations': operations,
            'elapsed_seconds': elapsed
        }

        return self.performance_metrics

    def identify_bottlenecks(self) -> List[str]:
        """Identify performance bottlenecks in the system.

        Returns:
            List of bottleneck descriptions
        """
        bottlenecks: List[str] = []

        # Check pool utilization
        stats = self.scale_manager.allocator.get_stats()
        utilization = stats['allocated'] / stats['total'] if stats['total'] > 0 else 0.0

        if utilization > 0.9:
            bottlenecks.append(
                f'High pool utilization ({utilization:.1%}) - consider expanding pool size'
            )

        # Check tile count
        tile_count = self.scale_manager.get_tile_count()
        if tile_count > 500 and not self.optimization_settings['lod_enabled']:
            bottlenecks.append(
                f'Large tile count ({tile_count}) without LOD optimization enabled'
            )

        if tile_count > 200 and not self.optimization_settings['spatial_partitioning_enabled']:
            bottlenecks.append(
                f'Large tile count ({tile_count}) without spatial partitioning'
            )

        # Check performance metrics
        if self.performance_metrics:
            avg_time = self.performance_metrics.get('avg_operation_time_ms', 0.0)
            if avg_time > 1.0:
                bottlenecks.append(
                    f'Slow average operation time ({avg_time:.2f}ms) - consider optimization'
                )

        # Check memory usage
        memory_stats = self.scale_manager.get_memory_usage()
        if memory_stats['pool_allocated'] > 1000:
            bottlenecks.append(
                f'High memory usage ({memory_stats["pool_allocated"]} tiles allocated) - '
                'consider tile streaming or chunking'
            )

        return bottlenecks

    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for improving performance.

        Returns:
            List of optimization recommendations
        """
        recommendations: List[str] = []
        tile_count = self.scale_manager.get_tile_count()

        # Scale-based recommendations
        if tile_count > 1000:
            recommendations.extend([
                'Implement tile streaming for distant tiles',
                'Use chunked spatial partitioning (e.g., quadtree)',
                'Consider GPU instancing for repeated geometries',
                'Implement background tile loading/unloading'
            ])
        elif tile_count > 500:
            recommendations.extend([
                'Enable aggressive LOD for distant tiles',
                'Use spatial partitioning for faster queries',
                'Consider tile pooling with priority-based eviction'
            ])
        elif tile_count > 100:
            recommendations.extend([
                'Enable LOD optimization',
                'Use spatial partitioning for tile queries',
                'Optimize tile layout periodically'
            ])

        # Performance-based recommendations
        if self.performance_metrics:
            if self.performance_metrics.get('avg_operation_time_ms', 0.0) > 0.5:
                recommendations.append(
                    'Profile allocation/release operations for optimization opportunities'
                )

        return recommendations

    def get_settings(self) -> Dict[str, Any]:
        """Get current optimization settings.

        Returns:
            Dictionary of optimization settings
        """
        return self.optimization_settings.copy()

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update optimization settings.

        Args:
            settings: Dictionary of settings to update
        """
        self.optimization_settings.update(settings)
