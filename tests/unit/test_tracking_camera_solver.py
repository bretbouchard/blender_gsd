"""
Unit tests for Camera Solver module.

Tests solver functionality with mock/fallback implementation
when running outside Blender.
"""

import pytest
import sys
import math
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.camera_solver import (
    CameraSolver,
    SolveOptions,
    SolveReport,
)
from cinematic.tracking.types import (
    Track,
    TrackPoint,
    TrackStatus,
    Solve,
    SolveStatus,
    TrackingConfig,
    TrackingSession,
    FootageInfo,
)
from oracle import Oracle


class TestSolveOptions:
    """Tests for SolveOptions dataclass."""

    def test_create_default(self):
        """Test creating solve options with defaults."""
        options = SolveOptions()
        Oracle.assert_equal(options.refine_intrinsics, ["focal_length"])
        Oracle.assert_equal(options.motion_model, "AFFINE")
        Oracle.assert_equal(options.use_keyframe_selection, True)

    def test_create_full(self):
        """Test creating solve options with all values."""
        options = SolveOptions(
            refine_intrinsics=["focal_length", "radial_distortion_k2"],
            motion_model="HOMOGRAPHY",
            use_keyframe_selection=False,
            keyframe1=10,
            keyframe2=100,
        )
        Oracle.assert_equal(options.motion_model, "HOMOGRAPHY")
        Oracle.assert_equal(options.keyframe1, 10)
        Oracle.assert_equal(options.keyframe2, 100)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = SolveOptions(
            refine_intrinsics=["focal_length", "principal_point"],
            motion_model="SIMILARITY",
            keyframe1=25,
            keyframe2=75,
        )
        data = original.to_dict()
        restored = SolveOptions.from_dict(data)

        Oracle.assert_equal(restored.refine_intrinsics, original.refine_intrinsics)
        Oracle.assert_equal(restored.motion_model, original.motion_model)
        Oracle.assert_equal(restored.keyframe1, original.keyframe1)
        Oracle.assert_equal(restored.keyframe2, original.keyframe2)


class TestSolveReport:
    """Tests for SolveReport dataclass."""

    def test_create_default(self):
        """Test creating solve report with defaults."""
        report = SolveReport()
        Oracle.assert_equal(report.success, False)
        Oracle.assert_equal(report.average_error, 0.0)
        Oracle.assert_equal(report.frames_solved, 0)

    def test_create_success(self):
        """Test creating successful solve report."""
        report = SolveReport(
            success=True,
            average_error=0.35,
            max_error=1.2,
            min_error=0.1,
            frames_solved=120,
            tracks_used=50,
            keyframes=(10, 100),
            message="Solve completed",
        )
        Oracle.assert_equal(report.success, True)
        Oracle.assert_equal(report.average_error, 0.35)
        Oracle.assert_equal(report.frames_solved, 120)
        Oracle.assert_equal(report.keyframes, (10, 100))

    def test_serialization(self):
        """Test to_dict roundtrip."""
        original = SolveReport(
            success=True,
            average_error=0.5,
            frames_solved=60,
            keyframes=(1, 60),
            warnings=["Low track count"],
        )
        data = original.to_dict()

        Oracle.assert_equal(data["success"], True)
        Oracle.assert_equal(data["average_error"], 0.5)
        Oracle.assert_equal(data["frames_solved"], 60)
        Oracle.assert_equal(data["warnings"], ["Low track count"])


class TestCameraSolver:
    """Tests for CameraSolver class."""

    def _create_test_session(self, num_tracks=10, frame_range=(1, 120)):
        """Create a test tracking session with tracks."""
        tracks = []
        for i in range(num_tracks):
            points = []
            for frame in range(frame_range[0], frame_range[1] + 1):
                # Create moving points
                t = (frame - frame_range[0]) / max(1, frame_range[1] - frame_range[0])
                x = 0.3 + 0.1 * i + 0.05 * math.sin(t * math.pi * 2)
                y = 0.3 + 0.1 * (i % 3) + 0.05 * math.cos(t * math.pi * 2)
                points.append(TrackPoint(frame=frame, position=(x, y)))

            track = Track(
                id=f"track_{i:03d}",
                name=f"Track {i}",
                points=points,
                is_keyframe=[frame_range[0], frame_range[1] // 2, frame_range[1]],
            )
            tracks.append(track)

        footage = FootageInfo(
            frame_start=frame_range[0],
            frame_end=frame_range[1],
            fps=24.0,
        )

        return TrackingSession(
            name="test_session",
            tracks=tracks,
            footage=footage,
        )

    def test_create_solver_default(self):
        """Test creating solver with no session."""
        solver = CameraSolver()
        Oracle.assert_none(solver.session)
        Oracle.assert_none(solver.get_solve())

    def test_create_solver_with_session(self):
        """Test creating solver with session."""
        session = self._create_test_session(num_tracks=5)
        solver = CameraSolver(session)
        Oracle.assert_not_none(solver.session)

    def test_set_session(self):
        """Test setting session after creation."""
        solver = CameraSolver()
        session = self._create_test_session(num_tracks=3)
        solver.set_session(session)
        Oracle.assert_equal(solver.session, session)

    def test_solve_no_session(self):
        """Test solving without session returns failure."""
        solver = CameraSolver()
        report = solver.solve()

        Oracle.assert_equal(report.success, False)
        Oracle.assert_in("No session set", report.warnings)

    def test_solve_with_session(self):
        """Test solving with session (fallback/mock)."""
        session = self._create_test_session(num_tracks=15)
        solver = CameraSolver(session)

        config = TrackingConfig(
            auto_keyframe=True,
            refine_focal_length=True,
        )

        report = solver.solve(config)

        # Fallback solver should succeed
        Oracle.assert_equal(report.success, True)
        Oracle.assert_greater_than(report.frames_solved, 0)
        Oracle.assert_greater_than(report.tracks_used, 0)

    def test_solve_produces_results(self):
        """Test that solve produces SolveResult data."""
        session = self._create_test_session(num_tracks=10, frame_range=(1, 60))
        solver = CameraSolver(session)
        solver.solve()

        solve = solver.get_solve()
        Oracle.assert_not_none(solve)
        Oracle.assert_equal(solve.status, SolveStatus.SUCCESS)
        Oracle.assert_greater_than(len(solve.results), 0)

    def test_solve_keyframe_selection(self):
        """Test automatic keyframe selection."""
        session = self._create_test_session(num_tracks=10, frame_range=(1, 100))
        solver = CameraSolver(session)

        config = TrackingConfig(auto_keyframe=True)
        report = solver.solve(config)

        # Should have selected keyframes
        Oracle.assert_not_equal(report.keyframes, (0, 0))
        Oracle.assert_less_than(report.keyframes[0], report.keyframes[1])

    def test_solve_error_statistics(self):
        """Test that solve reports error statistics."""
        session = self._create_test_session(num_tracks=20)
        solver = CameraSolver(session)
        report = solver.solve()

        Oracle.assert_greater_than(report.average_error, 0)
        Oracle.assert_greater_than(report.max_error, 0)
        Oracle.assert_greater_than(report.min_error, 0)
        Oracle.assert_greater_than_or_equal(report.max_error, report.average_error)
        Oracle.assert_less_than_or_equal(report.min_error, report.average_error)

    def test_solve_progress_callback(self):
        """Test that progress callback is called."""
        session = self._create_test_session(num_tracks=5)
        solver = CameraSolver(session)

        progress_values = []

        def callback(value):
            progress_values.append(value)

        config = TrackingConfig()
        solver.solve(config, progress_callback=callback)

        # Should have received progress updates
        Oracle.assert_greater_than(len(progress_values), 0)
        # Final value should be close to 1.0
        Oracle.assert_less_than(abs(progress_values[-1] - 0.9), 0.2)

    def test_get_report(self):
        """Test getting solve report."""
        session = self._create_test_session()
        solver = CameraSolver(session)
        solver.solve()

        report = solver.get_report()
        Oracle.assert_not_none(report)
        Oracle.assert_equal(report.success, True)

    def test_refine_focal_length(self):
        """Test focal length refinement."""
        session = self._create_test_session()
        solver = CameraSolver(session)
        solver.solve()

        refined = solver.refine_focal_length(initial_focal=50.0)
        Oracle.assert_greater_than(refined, 0)

    def test_refine_focal_length_with_range(self):
        """Test focal length refinement with frame range."""
        session = self._create_test_session(frame_range=(1, 120))
        solver = CameraSolver(session)
        solver.solve()

        refined = solver.refine_focal_length(
            initial_focal=50.0,
            frame_range=(30, 90),
        )
        Oracle.assert_greater_than(refined, 0)

    def test_validate_session_warnings(self):
        """Test session validation produces warnings."""
        # Session with few tracks
        session = self._create_test_session(num_tracks=3)
        solver = CameraSolver(session)

        # Solve should include warnings about low track count
        report = solver.solve()
        has_track_warning = any("3 tracks" in w for w in report.warnings)
        Oracle.assert_true(has_track_warning)

    def test_solve_config_motion_model(self):
        """Test that motion model config is used."""
        session = self._create_test_session()
        solver = CameraSolver(session)

        config = TrackingConfig(solver_motion_model="perspective")
        report = solver.solve(config)

        # Should complete successfully regardless of motion model
        Oracle.assert_equal(report.success, True)


class TestCameraSolverEdgeCases:
    """Edge case tests for CameraSolver."""

    def test_solve_empty_tracks(self):
        """Test solving with empty tracks list."""
        session = TrackingSession(name="empty", tracks=[])
        solver = CameraSolver(session)
        report = solver.solve()

        # Should fail or warn
        Oracle.assert_equal(report.success, False)

    def test_solve_single_frame(self):
        """Test solving with single frame."""
        session = TrackingSession(
            name="single_frame",
            tracks=[Track(name="t1", points=[TrackPoint(frame=1, position=(0.5, 0.5))])],
            footage=FootageInfo(frame_start=1, frame_end=1),
        )
        solver = CameraSolver(session)
        report = solver.solve()

        # Single frame can't really solve camera motion
        # But fallback should still produce something
        Oracle.assert_not_none(report)

    def test_solve_missing_frames(self):
        """Test solving with sparse tracks (missing frames)."""
        # Create tracks with gaps
        tracks = []
        for i in range(10):
            points = [
                TrackPoint(frame=1, position=(0.3 + i * 0.05, 0.5)),
                TrackPoint(frame=50, position=(0.35 + i * 0.05, 0.5)),
                TrackPoint(frame=100, position=(0.4 + i * 0.05, 0.5)),
            ]
            tracks.append(Track(name=f"sparse_{i}", points=points))

        session = TrackingSession(
            name="sparse",
            tracks=tracks,
            footage=FootageInfo(frame_start=1, frame_end=100),
        )
        solver = CameraSolver(session)
        report = solver.solve()

        # Should still produce results
        Oracle.assert_equal(report.success, True)

    def test_multiple_solves(self):
        """Test running multiple solves in sequence."""
        session = self._create_test_session(num_tracks=15)
        solver = CameraSolver(session)

        # First solve
        report1 = solver.solve()
        solve1 = solver.get_solve()

        # Second solve (should replace first)
        report2 = solver.solve()
        solve2 = solver.get_solve()

        Oracle.assert_equal(report2.success, True)
        Oracle.assert_not_equal(solve1.id, solve2.id)  # Different solve IDs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
