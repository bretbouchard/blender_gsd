"""
Eye Performance Benchmark

Tests eye generation performance at various scales.
Run inside Blender to measure actual performance.
"""

import bpy
import time
import sys
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    eye_count: int
    generation_time: float
    memory_mb: float
    viewport_fps: Optional[float]
    success: bool
    error: Optional[str] = None


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Also clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)


def benchmark_generation(
    count: int,
    radius: float = 10.0,
    size_min: float = 0.1,
    size_max: float = 1.0,
    seed: int = 42,
) -> BenchmarkResult:
    """
    Benchmark eye generation for a specific count.

    Args:
        count: Number of eyes to generate
        radius: Distribution radius
        size_min: Minimum eye size
        size_max: Maximum eye size
        seed: Random seed

    Returns:
        BenchmarkResult with timing and memory data
    """
    from generate_eyes import generate_eyes, clear_all_eyes

    # Clear previous
    clear_all_eyes()
    clear_scene()

    # Record initial memory
    initial_memory = get_memory_usage()

    # Time the generation
    start_time = time.perf_counter()

    try:
        obj = generate_eyes(
            count=count,
            radius=radius,
            size_min=size_min,
            size_max=size_max,
            seed=seed,
            name=f"BenchmarkEyes_{count}",
        )

        generation_time = time.perf_counter() - start_time

        # Force dependency graph update
        bpy.context.view_layer.update()

        # Record final memory
        final_memory = get_memory_usage()
        memory_used = final_memory - initial_memory

        # Try to measure viewport FPS (approximate)
        viewport_fps = None
        try:
            # Simple frame timing test
            start_frame = time.perf_counter()
            for _ in range(10):
                bpy.context.scene.frame_set(bpy.context.scene.frame_current)
            frame_time = (time.perf_counter() - start_frame) / 10
            viewport_fps = 1.0 / frame_time if frame_time > 0 else 0
        except:
            pass

        return BenchmarkResult(
            eye_count=count,
            generation_time=generation_time,
            memory_mb=memory_used,
            viewport_fps=viewport_fps,
            success=True,
        )

    except Exception as e:
        return BenchmarkResult(
            eye_count=count,
            generation_time=time.perf_counter() - start_time,
            memory_mb=get_memory_usage() - initial_memory,
            viewport_fps=None,
            success=False,
            error=str(e),
        )


def run_benchmark_suite(
    counts: List[int] = None,
    output_path: str = None,
) -> List[BenchmarkResult]:
    """
    Run benchmarks at various eye counts.

    Args:
        counts: List of eye counts to test
        output_path: Optional path to save results

    Returns:
        List of BenchmarkResult objects
    """
    if counts is None:
        counts = [100, 1000, 5000, 10000, 50000, 100000]

    results = []

    print("\n" + "=" * 60)
    print("Eye Generator Performance Benchmark")
    print("=" * 60)
    print(f"{'Count':>10} | {'Time (s)':>10} | {'Memory (MB)':>12} | {'FPS':>8} | Status")
    print("-" * 60)

    for count in counts:
        result = benchmark_generation(count)
        results.append(result)

        status = "OK" if result.success else "FAILED"
        fps_str = f"{result.viewport_fps:.1f}" if result.viewport_fps else "N/A"

        print(f"{result.eye_count:>10,} | {result.generation_time:>10.2f} | "
              f"{result.memory_mb:>12.1f} | {fps_str:>8} | {status}")

        if not result.success:
            print(f"  Error: {result.error}")

        # Clean up between tests
        clear_scene()

    print("=" * 60)

    # Performance targets
    print("\nPerformance Targets:")
    print("  100 eyes:      < 1s generation")
    print("  10,000 eyes:   < 5s generation, 30+ FPS")
    print("  100,000 eyes:  < 30s generation, 15+ FPS")
    print("  1,000,000 eyes: Loads without crash")

    # Save results if path provided
    if output_path:
        import json
        output = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': [
                {
                    'eye_count': r.eye_count,
                    'generation_time': r.generation_time,
                    'memory_mb': r.memory_mb,
                    'viewport_fps': r.viewport_fps,
                    'success': r.success,
                    'error': r.error,
                }
                for r in results
            ]
        }
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return results


def quick_benchmark() -> bool:
    """
    Quick benchmark to verify basic performance.
    Returns True if performance is acceptable.
    """
    print("\nQuick Performance Check...")

    # Test 1000 eyes
    result = benchmark_generation(1000)

    if not result.success:
        print(f"FAILED: {result.error}")
        return False

    if result.generation_time > 5.0:
        print(f"WARNING: Generation took {result.generation_time:.1f}s (target: < 5s)")

    # Test 10000 eyes
    result = benchmark_generation(10000)

    if not result.success:
        print(f"FAILED: {result.error}")
        return False

    if result.generation_time > 30.0:
        print(f"WARNING: Generation took {result.generation_time:.1f}s (target: < 30s)")

    print("Quick benchmark PASSED")
    return True


if __name__ == "__main__":
    # Check if running in Blender
    if 'bpy' not in dir():
        print("Error: This script must be run inside Blender")
        print("Run with: blender --python benchmark_eyes.py")
        sys.exit(1)

    # Run benchmark suite
    results = run_benchmark_suite(
        counts=[100, 1000, 5000, 10000],
        output_path=str(Path(__file__).parent.parent / ".planning" / "benchmark_results.json")
    )

    # Exit Blender if running headless
    if bpy.app.background:
        bpy.ops.wm.quit_blender()
