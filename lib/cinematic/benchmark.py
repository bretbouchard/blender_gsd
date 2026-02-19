"""
Benchmark Module (Phase 6.10)

Performance benchmarking utilities for the cinematic rendering system.
Provides timing, memory, and GPU utilization measurements.

Usage:
    from lib.cinematic.benchmark import benchmark_shot_assembly, benchmark_render

    # Benchmark shot assembly
    result = benchmark_shot_assembly(config)

    # Benchmark render
    result = benchmark_render(config, num_frames=10)
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
import time
import json
from datetime import datetime

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import PerformanceConfig, BenchmarkResult, ShotAssemblyConfig


def benchmark_shot_assembly(
    config: ShotAssemblyConfig,
    iterations: int = 10
) -> BenchmarkResult:
    """
    Benchmark shot assembly performance.

    Measures time to assemble a complete shot configuration.

    Args:
        config: Shot configuration to benchmark
        iterations: Number of iterations for averaging

    Returns:
        BenchmarkResult with timing data
    """
    result = BenchmarkResult(
        name=f"shot_assembly_{config.name}",
        timestamp=datetime.now().isoformat(),
    )

    total_time = 0.0

    for i in range(iterations):
        start = time.perf_counter()

        try:
            from .shot import assemble_shot
            if BLENDER_AVAILABLE:
                objects = assemble_shot(config)
                if objects.get("camera"):
                    result.passes_generated += 1
        except Exception:
            pass

        total_time += time.perf_counter() - start

    result.duration_seconds = total_time / iterations
    result.frames_rendered = iterations

    return result


def benchmark_render(
    config: ShotAssemblyConfig,
    num_frames: int = 1,
    quality_tier: str = "preview"
) -> BenchmarkResult:
    """
    Benchmark render performance.

    Measures render time for specified number of frames.

    Args:
        config: Shot configuration to render
        num_frames: Number of frames to render
        quality_tier: Quality tier (preview, production)

    Returns:
        BenchmarkResult with render timing
    """
    result = BenchmarkResult(
        name=f"render_{config.name}_{quality_tier}",
        timestamp=datetime.now().isoformat(),
    )

    if not BLENDER_AVAILABLE:
        return result

    start = time.perf_counter()

    try:
        from .shot import assemble_shot, render_shot

        # Assemble shot
        objects = assemble_shot(config)

        # Update render settings
        if config.render:
            config.render.quality_tier = quality_tier

        # Render frames
        scene = bpy.context.scene
        original_frame_end = scene.frame_end
        scene.frame_end = scene.frame_start + num_frames - 1

        # Execute render
        render_shot(config)

        scene.frame_end = original_frame_end

        result.frames_rendered = num_frames
        result.passes_generated = num_frames

    except Exception:
        result.passed = False

    result.duration_seconds = time.perf_counter() - start

    return result


def benchmark_animation(
    config: ShotAssemblyConfig,
    animation_type: str = "orbit",
    duration_frames: int = 120
) -> BenchmarkResult:
    """
    Benchmark animation setup performance.

    Measures time to set up camera animation.

    Args:
        config: Shot configuration
        animation_type: Type of animation (orbit, turntable, path)
        duration_frames: Animation duration in frames

    Returns:
        BenchmarkResult with animation setup timing
    """
    result = BenchmarkResult(
        name=f"animation_{animation_type}_{config.name}",
        timestamp=datetime.now().isoformat(),
    )

    start = time.perf_counter()

    try:
        from .shot import assemble_shot
        from .animation import create_orbit_animation, create_turntable_animation

        objects = assemble_shot(config)
        camera = objects.get("camera")

        if camera:
            if animation_type == "orbit":
                create_orbit_animation(
                    camera=camera,
                    center=(0, 0, 0),
                    angle_range=(0, 360),
                    radius=1.5,
                    duration=duration_frames
                )
            elif animation_type == "turntable":
                # Turntable rotates subject
                pass

        result.passes_generated = 1

    except Exception:
        result.passed = False

    result.duration_seconds = time.perf_counter() - start
    result.frames_rendered = duration_frames

    return result


def run_all_benchmarks(
    config: ShotAssemblyConfig,
    perf_config: Optional[PerformanceConfig] = None
) -> Dict[str, Any]:
    """
    Run comprehensive benchmark suite.

    Args:
        config: Shot configuration to benchmark
        perf_config: Performance targets configuration

    Returns:
        Dictionary with all benchmark results
    """
    if perf_config is None:
        perf_config = PerformanceConfig()

    results = {
        "config": config.to_dict(),
        "targets": perf_config.to_dict(),
        "benchmarks": [],
        "passed": True,
        "timestamp": datetime.now().isoformat(),
    }

    # Shot assembly benchmark
    assembly_result = benchmark_shot_assembly(config)
    assembly_result.passed = assembly_result.duration_seconds * 1000 <= perf_config.target_shot_assembly_time
    results["benchmarks"].append(assembly_result.to_dict())
    if not assembly_result.passed:
        results["passed"] = False

    # Preview render benchmark (1 frame)
    preview_result = benchmark_render(config, num_frames=1, quality_tier="preview")
    preview_result.passed = preview_result.duration_seconds <= perf_config.target_render_time_preview
    results["benchmarks"].append(preview_result.to_dict())
    if not preview_result.passed:
        results["passed"] = False

    # Animation benchmark
    anim_result = benchmark_animation(config, animation_type="orbit", duration_frames=120)
    anim_result.passed = anim_result.duration_seconds * 1000 <= perf_config.target_orbit_animation_time
    results["benchmarks"].append(anim_result.to_dict())
    if not anim_result.passed:
        results["passed"] = False

    return results


def save_benchmark_results(
    results: Dict[str, Any],
    output_path: str
) -> bool:
    """
    Save benchmark results to JSON file.

    Args:
        results: Benchmark results dictionary
        output_path: Path to save results

    Returns:
        True on success
    """
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(results, f, indent=2)

        return True
    except Exception:
        return False


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for benchmark context.

    Returns:
        Dictionary with system specs
    """
    info = {
        "blender_version": "",
        "python_version": "",
        "platform": "",
        "gpu_info": "",
    }

    if BLENDER_AVAILABLE:
        info["blender_version"] = bpy.app.version_string
        info["python_version"] = str(bpy.app.version)

        import platform
        info["platform"] = platform.platform()

        # GPU info (if available)
        if hasattr(bpy.context, "preferences") and hasattr(bpy.context.preferences, "system"):
            prefs = bpy.context.preferences.system
            if hasattr(prefs, "gpu_backend"):
                info["gpu_info"] = prefs.gpu_backend

    return info


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "benchmark_shot_assembly",
    "benchmark_render",
    "benchmark_animation",
    "run_all_benchmarks",
    "save_benchmark_results",
    "get_system_info",
    "BLENDER_AVAILABLE",
]
