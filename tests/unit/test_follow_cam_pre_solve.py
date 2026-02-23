"""
Follow Camera Pre-Solve Workflow Unit Tests

Tests for: lib/cinematic/follow_cam/pre_solve.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-60
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.pre_solve import (
    PreSolveStage,
    PreSolveResult,
    PreSolver,
    compute_pre_solve_path,
    HAS_BLENDER,
)
from lib.cinematic.follow_cam.types import (
    FollowCameraConfig,
    FollowTarget,
    FollowMode,
)


class TestPreSolveStage:
    """Unit tests for PreSolveStage enum."""

    def test_all_stages_exist(self):
        """All expected stages should be defined."""
        expected_stages = [
            "SCENE_ANALYSIS",
            "IDEAL_PATH",
            "AVOIDANCE",
            "SMOOTHING",
            "BAKING",
            "COMPLETE",
        ]

        for stage in expected_stages:
            assert hasattr(PreSolveStage, stage), f"Missing PreSolveStage.{stage}"

    def test_stage_values(self):
        """Stage values should be lowercase strings."""
        assert PreSolveStage.SCENE_ANALYSIS.value == "scene_analysis"
        assert PreSolveStage.IDEAL_PATH.value == "ideal_path"
        assert PreSolveStage.AVOIDANCE.value == "avoidance"
        assert PreSolveStage.SMOOTHING.value == "smoothing"
        assert PreSolveStage.BAKING.value == "baking"
        assert PreSolveStage.COMPLETE.value == "complete"

    def test_stage_count(self):
        """Should have exactly 6 stages."""
        assert len(PreSolveStage) == 6


class TestPreSolveResult:
    """Unit tests for PreSolveResult dataclass."""

    def test_default_values(self):
        """Default PreSolveResult should have sensible defaults."""
        result = PreSolveResult()

        assert result.success is False
        assert result.stage == PreSolveStage.SCENE_ANALYSIS
        assert result.frames_processed == 0
        assert len(result.path_points) == 0
        assert len(result.rotation_points) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_custom_values(self):
        """PreSolveResult should store all result data."""
        result = PreSolveResult(
            success=True,
            stage=PreSolveStage.COMPLETE,
            frames_processed=250,
            path_points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
            rotation_points=[(0.0, 0.0, 0.0), (45.0, 0.0, 0.0)],
            errors=[],
            warnings=["Frame 150 had slow calculation"],
        )

        assert result.success is True
        assert result.stage == PreSolveStage.COMPLETE
        assert result.frames_processed == 250
        assert len(result.path_points) == 2
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        result = PreSolveResult(
            success=True,
            stage=PreSolveStage.SMOOTHING,
            frames_processed=100,
            path_points=[(0.0, 0.0, 0.0)],
            rotation_points=[(0.0, 0.0, 0.0)],
            errors=["Test error"],
            warnings=["Test warning"],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["stage"] == "smoothing"
        assert data["frames_processed"] == 100
        # path_points and rotation_points remain as tuples in to_dict
        assert data["path_points"] == [(0.0, 0.0, 0.0)]
        assert data["errors"] == ["Test error"]

    def test_with_errors(self):
        """Result with errors should track them."""
        result = PreSolveResult(
            errors=["Object not found", "Frame 100 failed"],
        )

        assert len(result.errors) == 2
        assert "Object not found" in result.errors


class TestPreSolver:
    """Unit tests for PreSolver class."""

    def test_initialization(self):
        """PreSolver should initialize with config and target."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)

        assert solver.config == config
        assert solver.target == target

    def test_solve_returns_result(self):
        """Solve should return a PreSolveResult."""
        config = FollowCameraConfig(
            collision_enabled=False,
            prediction_enabled=False,
        )
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)
        result = solver.solve(frame_start=1, frame_end=10)

        assert isinstance(result, PreSolveResult)
        assert result.frames_processed == 10

    @pytest.mark.skipif(HAS_BLENDER, reason="Test requires real Blender to be unavailable")
    def test_solve_progresses_through_stages(self):
        """Solve should progress through all stages."""
        config = FollowCameraConfig(
            collision_enabled=False,
            prediction_enabled=False,
        )
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)
        result = solver.solve(frame_start=1, frame_end=5)

        # Should complete successfully
        assert result.success is True
        assert result.stage == PreSolveStage.COMPLETE

    def test_solve_with_progress_callback(self):
        """Solve should call progress callback for each stage."""
        config = FollowCameraConfig(
            collision_enabled=False,
            prediction_enabled=False,
        )
        target = FollowTarget(object_name="Player")

        progress_stages = []

        def progress_callback(stage, progress):
            progress_stages.append((stage, progress))

        solver = PreSolver(config, target)
        result = solver.solve(
            frame_start=1,
            frame_end=5,
            progress_callback=progress_callback,
        )

        # Should have called callback for each stage
        assert len(progress_stages) >= 5  # At least start for each stage

    def test_solve_computes_path_points(self):
        """Solve should compute path points (even if empty without Blender)."""
        config = FollowCameraConfig(
            collision_enabled=False,
            prediction_enabled=False,
        )
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)
        result = solver.solve(frame_start=1, frame_end=10)

        # Path points should be computed (empty list without Blender objects)
        assert isinstance(result.path_points, list)

    def test_apply_to_camera_without_blender(self):
        """Apply to camera should return False without Blender."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)
        result = solver.apply_to_camera("Camera")

        # Should return False without Blender
        assert result is False

    @pytest.mark.skipif(HAS_BLENDER, reason="Test requires real Blender to be unavailable")
    def test_get_target_at_frame_without_blender(self):
        """Get target at frame should return zeros without Blender."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)
        pos, vel = solver._get_target_at_frame(1)

        compare_vectors(pos, (0.0, 0.0, 0.0))
        compare_vectors(vel, (0.0, 0.0, 0.0))


class TestComputePreSolvePath:
    """Unit tests for compute_pre_solve_path convenience function."""

    def test_returns_result(self):
        """Function should return PreSolveResult."""
        config = FollowCameraConfig(
            collision_enabled=False,
            prediction_enabled=False,
        )
        target = FollowTarget(object_name="Player")

        result = compute_pre_solve_path(
            config=config,
            target=target,
            frame_start=1,
            frame_end=10,
        )

        assert isinstance(result, PreSolveResult)
        assert result.frames_processed == 10

    @pytest.mark.skipif(HAS_BLENDER, reason="Test requires real Blender to be unavailable")
    def test_propagates_to_solver(self):
        """Function should create solver and call solve."""
        config = FollowCameraConfig(
            collision_enabled=False,
            prediction_enabled=False,
        )
        target = FollowTarget(object_name="Player")

        result = compute_pre_solve_path(
            config=config,
            target=target,
            frame_start=1,
            frame_end=5,
        )

        # Should have gone through all stages
        assert result.stage == PreSolveStage.COMPLETE


class TestPathSmoothing:
    """Unit tests for path smoothing in PreSolver."""

    def test_smooth_path_basic(self):
        """Smoothing should be applied to path points."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)

        # Create some path points
        solver._result.path_points = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (5.0, 0.0, 0.0),
            (6.0, 0.0, 0.0),
            (7.0, 0.0, 0.0),
            (8.0, 0.0, 0.0),
            (9.0, 0.0, 0.0),
        ]

        solver._smooth_path()

        # Path should still have same number of points
        assert len(solver._result.path_points) == 10

    def test_smooth_path_short(self):
        """Smoothing short paths should not crash."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="Player")

        solver = PreSolver(config, target)

        # Create short path
        solver._result.path_points = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
        ]

        solver._smooth_path()

        # Should not crash
        assert len(solver._result.path_points) == 2


class TestModuleImports:
    """Tests for module-level imports."""

    def test_pre_solve_module_imports(self):
        """All pre_solve types should be importable."""
        from lib.cinematic.follow_cam.pre_solve import (
            PreSolveStage,
            PreSolveResult,
            PreSolver,
            compute_pre_solve_path,
        )

        assert PreSolveStage is not None
        assert PreSolveResult is not None
        assert PreSolver is not None

    def test_package_imports_pre_solve(self):
        """Pre-solve APIs should be importable from package."""
        from lib.cinematic.follow_cam import (
            PreSolveStage,
            PreSolveResult,
            PreSolver,
            compute_pre_solve_path,
        )

        assert PreSolveStage is not None
        assert PreSolver is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
