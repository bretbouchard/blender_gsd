"""
Unit tests for Motion Tracking types module.

Tests serialization, deserialization, and core functionality
of tracking data types.
"""

import pytest
import sys
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.types import (
    TrackStatus,
    SolveStatus,
    FeatureDetector,
    TrackPoint,
    Track,
    SolveResult,
    Solve,
    FootageInfo,
    TrackingSession,
    TrackingConfig,
    CameraProfile,
    StabilizationResult,
    ImportFormat,
    SUPPORTED_IMPORT_FORMATS,
)
from oracle import Oracle


class TestTrackPoint:
    """Tests for TrackPoint dataclass."""

    def test_create_default(self):
        """Test creating track point with defaults."""
        point = TrackPoint(frame=10)
        Oracle.assert_equal(point.frame, 10)
        Oracle.assert_equal(point.position, (0.0, 0.0))
        Oracle.assert_equal(point.status, TrackStatus.OK)
        Oracle.assert_equal(point.error, 0.0)
        Oracle.assert_equal(point.weight, 1.0)

    def test_create_full(self):
        """Test creating track point with all values."""
        point = TrackPoint(
            frame=42,
            position=(0.5, 0.3),
            status=TrackStatus.OUTLIER,
            error=2.5,
            weight=0.8,
        )
        Oracle.assert_equal(point.frame, 42)
        Oracle.assert_equal(point.position, (0.5, 0.3))
        Oracle.assert_equal(point.status, TrackStatus.OUTLIER)
        Oracle.assert_equal(point.error, 2.5)
        Oracle.assert_equal(point.weight, 0.8)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = TrackPoint(
            frame=100,
            position=(0.75, 0.25),
            status=TrackStatus.MISSING,
            error=1.5,
            weight=0.5,
        )
        data = original.to_dict()
        restored = TrackPoint.from_dict(data)

        Oracle.assert_equal(restored.frame, original.frame)
        Oracle.assert_equal(restored.position, original.position)
        Oracle.assert_equal(restored.status, original.status)
        Oracle.assert_equal(restored.error, original.error)
        Oracle.assert_equal(restored.weight, original.weight)


class TestTrack:
    """Tests for Track dataclass."""

    def test_create_default(self):
        """Test creating track with defaults."""
        track = Track(name="test_track")
        Oracle.assert_equal(track.name, "test_track")
        Oracle.assert_equal(track.pattern_size, 21)
        Oracle.assert_equal(track.search_size, 51)
        Oracle.assert_equal(len(track.points), 0)
        Oracle.assert_equal(track.marker_enabled, True)

    def test_create_with_points(self):
        """Test creating track with points."""
        points = [
            TrackPoint(frame=1, position=(0.5, 0.5)),
            TrackPoint(frame=2, position=(0.51, 0.49)),
            TrackPoint(frame=3, position=(0.52, 0.48)),
        ]
        track = Track(name="moving_track", points=points)
        Oracle.assert_equal(len(track.points), 3)
        Oracle.assert_equal(track.get_frame_range(), (1, 3))

    def test_get_point_at_frame(self):
        """Test getting point at specific frame."""
        points = [
            TrackPoint(frame=1, position=(0.5, 0.5)),
            TrackPoint(frame=3, position=(0.52, 0.48)),
        ]
        track = Track(name="sparse_track", points=points)

        point = track.get_point_at_frame(1)
        Oracle.assert_not_none(point)
        Oracle.assert_equal(point.position, (0.5, 0.5))

        point = track.get_point_at_frame(2)
        Oracle.assert_none(point)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = Track(
            name="serialize_test",
            pattern_size=31,
            search_size=71,
            points=[
                TrackPoint(frame=1, position=(0.5, 0.5)),
                TrackPoint(frame=2, position=(0.6, 0.4)),
            ],
            color=(1.0, 0.5, 0.0),
            marker_position=(0.55, 0.45),
            is_keyframe=[1, 10, 20],
        )
        data = original.to_dict()
        restored = Track.from_dict(data)

        Oracle.assert_equal(restored.name, original.name)
        Oracle.assert_equal(restored.pattern_size, original.pattern_size)
        Oracle.assert_equal(restored.search_size, original.search_size)
        Oracle.assert_equal(len(restored.points), len(original.points))
        Oracle.assert_equal(restored.color, original.color)
        Oracle.assert_equal(restored.is_keyframe, original.is_keyframe)


class TestSolveResult:
    """Tests for SolveResult dataclass."""

    def test_create_default(self):
        """Test creating solve result with defaults."""
        result = SolveResult(frame=10)
        Oracle.assert_equal(result.frame, 10)
        Oracle.assert_equal(result.position, (0.0, 0.0, 0.0))
        Oracle.assert_equal(result.rotation, (1.0, 0.0, 0.0, 0.0))
        Oracle.assert_equal(result.focal_length, 50.0)
        Oracle.assert_equal(result.error, 0.0)

    def test_create_full(self):
        """Test creating solve result with all values."""
        result = SolveResult(
            frame=50,
            position=(1.0, 2.0, 3.0),
            rotation=(0.707, 0.0, 0.707, 0.0),
            focal_length=35.0,
            error=0.5,
            intrinsics=[1.2, 1.2, 0.5, 0.5, -0.01, 0.002],
        )
        Oracle.assert_equal(result.frame, 50)
        Oracle.assert_equal(result.position, (1.0, 2.0, 3.0))
        Oracle.assert_equal(result.focal_length, 35.0)
        Oracle.assert_equal(result.error, 0.5)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = SolveResult(
            frame=25,
            position=(5.0, -3.0, 2.0),
            rotation=(0.924, 0.383, 0.0, 0.0),
            focal_length=85.0,
            error=1.2,
        )
        data = original.to_dict()
        restored = SolveResult.from_dict(data)

        Oracle.assert_equal(restored.frame, original.frame)
        Oracle.assert_equal(restored.position, original.position)
        Oracle.assert_equal(restored.rotation, original.rotation)
        Oracle.assert_equal(restored.focal_length, original.focal_length)
        Oracle.assert_equal(restored.error, original.error)


class TestSolve:
    """Tests for Solve dataclass."""

    def test_create_default(self):
        """Test creating solve with defaults."""
        solve = Solve()
        Oracle.assert_equal(solve.status, SolveStatus.PENDING)
        Oracle.assert_equal(len(solve.results), 0)
        Oracle.assert_equal(solve.average_error, 0.0)

    def test_get_result_at_frame(self):
        """Test getting result at specific frame."""
        results = [
            SolveResult(frame=1, position=(0.0, 0.0, 0.0)),
            SolveResult(frame=2, position=(1.0, 0.0, 0.0)),
            SolveResult(frame=3, position=(2.0, 0.0, 0.0)),
        ]
        solve = Solve(results=results)

        result = solve.get_result_at_frame(2)
        Oracle.assert_not_none(result)
        Oracle.assert_equal(result.position, (1.0, 0.0, 0.0))

        result = solve.get_result_at_frame(10)
        Oracle.assert_none(result)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = Solve(
            status=SolveStatus.SUCCESS,
            results=[
                SolveResult(frame=1, position=(0.0, 0.0, 0.0)),
                SolveResult(frame=2, position=(1.0, 0.0, 0.0)),
            ],
            average_error=0.35,
            keyframes=[1, 5, 10],
            solve_time_seconds=12.5,
        )
        data = original.to_dict()
        restored = Solve.from_dict(data)

        Oracle.assert_equal(restored.status, original.status)
        Oracle.assert_equal(len(restored.results), len(original.results))
        Oracle.assert_equal(restored.average_error, original.average_error)
        Oracle.assert_equal(restored.keyframes, original.keyframes)
        Oracle.assert_equal(restored.solve_time_seconds, original.solve_time_seconds)


class TestFootageInfo:
    """Tests for FootageInfo dataclass."""

    def test_create_default(self):
        """Test creating footage info with defaults."""
        info = FootageInfo()
        Oracle.assert_equal(info.width, 1920)
        Oracle.assert_equal(info.height, 1080)
        Oracle.assert_equal(info.fps, 24.0)
        Oracle.assert_equal(info.colorspace, "sRGB")

    def test_create_full(self):
        """Test creating footage info with all values."""
        info = FootageInfo(
            source_path="/path/to/video.mov",
            width=4096,
            height=2160,
            frame_start=1001,
            frame_end=1100,
            fps=23.976,
            duration_seconds=4.17,
            colorspace="ACEScg",
            codec="ProRes 4444",
            has_alpha=True,
        )
        Oracle.assert_equal(info.width, 4096)
        Oracle.assert_equal(info.height, 2160)
        Oracle.assert_equal(info.fps, 23.976)
        Oracle.assert_equal(info.has_alpha, True)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = FootageInfo(
            source_path="/test/video.mp4",
            width=3840,
            height=2160,
            fps=30.0,
            codec="H.264",
        )
        data = original.to_dict()
        restored = FootageInfo.from_dict(data)

        Oracle.assert_equal(restored.source_path, original.source_path)
        Oracle.assert_equal(restored.width, original.width)
        Oracle.assert_equal(restored.height, original.height)
        Oracle.assert_equal(restored.fps, original.fps)
        Oracle.assert_equal(restored.codec, original.codec)


class TestTrackingSession:
    """Tests for TrackingSession dataclass."""

    def test_create_default(self):
        """Test creating session with defaults."""
        session = TrackingSession(name="test_session")
        Oracle.assert_equal(session.name, "test_session")
        Oracle.assert_equal(len(session.tracks), 0)
        Oracle.assert_equal(len(session.solves), 0)

    def test_get_track_by_id(self):
        """Test getting track by ID."""
        track1 = Track(id="track_01", name="first")
        track2 = Track(id="track_02", name="second")
        session = TrackingSession(tracks=[track1, track2])

        found = session.get_track_by_id("track_02")
        Oracle.assert_not_none(found)
        Oracle.assert_equal(found.name, "second")

        not_found = session.get_track_by_id("track_99")
        Oracle.assert_none(not_found)

    def test_get_solve_by_id(self):
        """Test getting solve by ID."""
        solve1 = Solve(id="solve_01")
        solve2 = Solve(id="solve_02")
        session = TrackingSession(solves=[solve1, solve2])

        found = session.get_solve_by_id("solve_01")
        Oracle.assert_not_none(found)
        Oracle.assert_equal(found.id, "solve_01")

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = TrackingSession(
            name="serialize_test",
            footage=FootageInfo(width=1920, height=1080),
            tracks=[Track(name="track1"), Track(name="track2")],
            solves=[Solve(id="solve1")],
            frame_current=50,
            metadata={"project": "test"},
        )
        data = original.to_dict()
        restored = TrackingSession.from_dict(data)

        Oracle.assert_equal(restored.name, original.name)
        Oracle.assert_equal(restored.footage.width, original.footage.width)
        Oracle.assert_equal(len(restored.tracks), len(original.tracks))
        Oracle.assert_equal(len(restored.solves), len(original.solves))
        Oracle.assert_equal(restored.frame_current, original.frame_current)
        Oracle.assert_equal(restored.metadata["project"], "test")


class TestTrackingConfig:
    """Tests for TrackingConfig dataclass."""

    def test_create_default(self):
        """Test creating config with defaults."""
        config = TrackingConfig()
        Oracle.assert_equal(config.detector, FeatureDetector.FAST)
        Oracle.assert_equal(config.min_features, 50)
        Oracle.assert_equal(config.max_features, 500)
        Oracle.assert_equal(config.use_optical_flow, True)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = TrackingConfig(
            detector=FeatureDetector.HARRIS,
            min_features=100,
            max_features=1000,
            pattern_size=31,
            refine_radial_distortion=True,
        )
        data = original.to_dict()
        restored = TrackingConfig.from_dict(data)

        Oracle.assert_equal(restored.detector, original.detector)
        Oracle.assert_equal(restored.min_features, original.min_features)
        Oracle.assert_equal(restored.max_features, original.max_features)
        Oracle.assert_equal(restored.pattern_size, original.pattern_size)
        Oracle.assert_equal(restored.refine_radial_distortion, original.refine_radial_distortion)


class TestCameraProfile:
    """Tests for CameraProfile dataclass."""

    def test_create_default(self):
        """Test creating profile with defaults."""
        profile = CameraProfile(name="test")
        Oracle.assert_equal(profile.name, "test")
        Oracle.assert_equal(profile.sensor_width, 36.0)
        Oracle.assert_equal(profile.sensor_height, 24.0)
        Oracle.assert_equal(profile.distortion_model, "brown_conrady")

    def test_iphone_profile(self):
        """Test creating iPhone profile."""
        profile = CameraProfile(
            name="iPhone 15 Pro",
            manufacturer="Apple",
            model="iPhone 15 Pro",
            sensor_width=8.28,
            sensor_height=6.22,
            focal_length=6.78,
            crop_factor=4.35,
            k1=-0.0220,
            k2=0.0108,
        )
        Oracle.assert_equal(profile.manufacturer, "Apple")
        Oracle.assert_equal(profile.crop_factor, 4.35)
        Oracle.assert_equal(profile.k1, -0.0220)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = CameraProfile(
            name="RED Komodo",
            manufacturer="RED",
            model="Komodo 6K",
            sensor_width=27.03,
            sensor_height=14.26,
            k1=-0.0080,
            k2=0.0035,
        )
        data = original.to_dict()
        restored = CameraProfile.from_dict(data)

        Oracle.assert_equal(restored.name, original.name)
        Oracle.assert_equal(restored.manufacturer, original.manufacturer)
        Oracle.assert_equal(restored.sensor_width, original.sensor_width)
        Oracle.assert_equal(restored.k1, original.k1)


class TestStabilizationResult:
    """Tests for StabilizationResult dataclass."""

    def test_create_default(self):
        """Test creating stabilization result with defaults."""
        result = StabilizationResult(frame=10)
        Oracle.assert_equal(result.frame, 10)
        Oracle.assert_equal(result.translation, (0.0, 0.0))
        Oracle.assert_equal(result.rotation, 0.0)
        Oracle.assert_equal(result.scale, 1.0)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = StabilizationResult(
            frame=25,
            translation=(10.5, -5.2),
            rotation=0.02,
            scale=1.01,
            shear_x=0.001,
            shear_y=-0.001,
        )
        data = original.to_dict()
        restored = StabilizationResult.from_dict(data)

        Oracle.assert_equal(restored.frame, original.frame)
        Oracle.assert_equal(restored.translation, original.translation)
        Oracle.assert_equal(restored.rotation, original.rotation)
        Oracle.assert_equal(restored.scale, original.scale)


class TestImportFormat:
    """Tests for ImportFormat dataclass."""

    def test_create(self):
        """Test creating import format."""
        fmt = ImportFormat(
            name="FBX",
            extensions=[".fbx"],
            description="Autodesk FBX camera animation",
        )
        Oracle.assert_equal(fmt.name, "FBX")
        Oracle.assert_equal(fmt.extensions, [".fbx"])
        Oracle.assert_equal(fmt.description, "Autodesk FBX camera animation")

    def test_supported_formats(self):
        """Test that supported formats are defined."""
        Oracle.assert_equal(len(SUPPORTED_IMPORT_FORMATS), 6)

        format_names = [f.name for f in SUPPORTED_IMPORT_FORMATS]
        Oracle.assert_in("fbx", format_names)
        Oracle.assert_in("alembic", format_names)
        Oracle.assert_in("bvh", format_names)
        Oracle.assert_in("nuke_chan", format_names)


class TestEnums:
    """Tests for enum types."""

    def test_track_status(self):
        """Test TrackStatus enum values."""
        Oracle.assert_equal(TrackStatus.OK.value, "ok")
        Oracle.assert_equal(TrackStatus.MISSING.value, "missing")
        Oracle.assert_equal(TrackStatus.DISABLED.value, "disabled")
        Oracle.assert_equal(TrackStatus.OUTLIER.value, "outlier")

    def test_solve_status(self):
        """Test SolveStatus enum values."""
        Oracle.assert_equal(SolveStatus.PENDING.value, "pending")
        Oracle.assert_equal(SolveStatus.RUNNING.value, "running")
        Oracle.assert_equal(SolveStatus.SUCCESS.value, "success")
        Oracle.assert_equal(SolveStatus.FAILED.value, "failed")

    def test_feature_detector(self):
        """Test FeatureDetector enum values."""
        Oracle.assert_equal(FeatureDetector.FAST.value, "fast")
        Oracle.assert_equal(FeatureDetector.HARRIS.value, "harris")
        Oracle.assert_equal(FeatureDetector.SIFT.value, "sift")
        Oracle.assert_equal(FeatureDetector.ORB.value, "orb")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
