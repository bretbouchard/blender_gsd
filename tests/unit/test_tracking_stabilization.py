"""
Unit tests for Stabilization module.

Tests 2D video stabilization from point tracks.
"""

import pytest
import sys
import math
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.stabilization import (
    StabilizationConfig,
    Transform2D,
    StabilizationData,
    MotionAnalyzer,
    MotionSmoother,
    Stabilizer,
    stabilize_session,
    calculate_stabilization_quality,
)
from cinematic.tracking.types import (
    Track,
    TrackPoint,
    TrackStatus,
    TrackingSession,
    FootageInfo,
)
from oracle import Oracle


class TestStabilizationConfig:
    """Tests for StabilizationConfig dataclass."""

    def test_create_default(self):
        """Test creating config with defaults."""
        config = StabilizationConfig()
        Oracle.assert_equal(config.smooth_translation, 0.5)
        Oracle.assert_equal(config.smooth_rotation, 0.5)
        Oracle.assert_equal(config.smooth_scale, 0.5)
        Oracle.assert_equal(config.use_rotation, True)
        Oracle.assert_equal(config.use_scale, True)
        Oracle.assert_equal(config.anchor_frame, 0)
        Oracle.assert_equal(config.border_mode, "mirror")
        Oracle.assert_equal(config.invert, False)

    def test_create_custom(self):
        """Test creating config with custom values."""
        config = StabilizationConfig(
            smooth_translation=0.8,
            smooth_rotation=0.3,
            smooth_scale=0.6,
            use_rotation=False,
            use_scale=False,
            anchor_frame=10,
            border_mode="extend",
            invert=True,
        )
        Oracle.assert_equal(config.smooth_translation, 0.8)
        Oracle.assert_equal(config.smooth_rotation, 0.3)
        Oracle.assert_equal(config.use_rotation, False)
        Oracle.assert_equal(config.anchor_frame, 10)
        Oracle.assert_equal(config.invert, True)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = StabilizationConfig(
            smooth_translation=0.7,
            smooth_rotation=0.4,
            anchor_frame=5,
        )
        data = original.to_dict()
        restored = StabilizationConfig.from_dict(data)

        Oracle.assert_equal(restored.smooth_translation, original.smooth_translation)
        Oracle.assert_equal(restored.smooth_rotation, original.smooth_rotation)
        Oracle.assert_equal(restored.anchor_frame, original.anchor_frame)


class TestTransform2D:
    """Tests for Transform2D dataclass."""

    def test_create_default(self):
        """Test creating transform with defaults."""
        transform = Transform2D()
        Oracle.assert_equal(transform.tx, 0.0)
        Oracle.assert_equal(transform.ty, 0.0)
        Oracle.assert_equal(transform.rotation, 0.0)
        Oracle.assert_equal(transform.scale, 1.0)
        Oracle.assert_equal(transform.cx, 0.5)
        Oracle.assert_equal(transform.cy, 0.5)

    def test_create_custom(self):
        """Test creating transform with custom values."""
        transform = Transform2D(
            tx=10.0,
            ty=-5.0,
            rotation=0.5,
            scale=1.2,
            cx=0.3,
            cy=0.7,
        )
        Oracle.assert_equal(transform.tx, 10.0)
        Oracle.assert_equal(transform.ty, -5.0)
        Oracle.assert_equal(transform.rotation, 0.5)
        Oracle.assert_equal(transform.scale, 1.2)

    def test_inverse_translation(self):
        """Test inverse of translation."""
        transform = Transform2D(tx=10.0, ty=20.0)
        inverse = transform.inverse()

        Oracle.assert_less_than(abs(inverse.tx - (-10.0)), 0.001)
        Oracle.assert_less_than(abs(inverse.ty - (-20.0)), 0.001)

    def test_inverse_scale(self):
        """Test inverse of scale."""
        transform = Transform2D(scale=2.0)
        inverse = transform.inverse()

        Oracle.assert_less_than(abs(inverse.scale - 0.5), 0.001)

    def test_inverse_rotation(self):
        """Test inverse of rotation."""
        transform = Transform2D(rotation=0.5)
        inverse = transform.inverse()

        Oracle.assert_less_than(abs(inverse.rotation - (-0.5)), 0.001)

    def test_compose_translations(self):
        """Test composing two translations."""
        t1 = Transform2D(tx=10.0, ty=5.0)
        t2 = Transform2D(tx=5.0, ty=10.0)
        result = t1.compose(t2)

        Oracle.assert_less_than(abs(result.tx - 15.0), 0.001)
        Oracle.assert_less_than(abs(result.ty - 15.0), 0.001)

    def test_compose_scales(self):
        """Test composing two scales."""
        t1 = Transform2D(scale=2.0)
        t2 = Transform2D(scale=1.5)
        result = t1.compose(t2)

        Oracle.assert_less_than(abs(result.scale - 3.0), 0.001)

    def test_apply_to_point_identity(self):
        """Test applying identity transform."""
        transform = Transform2D()
        x, y = transform.apply_to_point(0.5, 0.5)

        Oracle.assert_less_than(abs(x - 0.5), 0.001)
        Oracle.assert_less_than(abs(y - 0.5), 0.001)

    def test_apply_to_point_translation(self):
        """Test applying translation to point."""
        transform = Transform2D(tx=10.0, ty=5.0)
        x, y = transform.apply_to_point(0.5, 0.5)

        # Translation is in pixels, not normalized
        Oracle.assert_less_than(abs(x - 10.5), 0.001)
        Oracle.assert_less_than(abs(y - 5.5), 0.001)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = Transform2D(tx=15.0, ty=25.0, rotation=0.3, scale=1.5)
        data = original.to_dict()
        restored = Transform2D.from_dict(data)

        Oracle.assert_equal(restored.tx, original.tx)
        Oracle.assert_equal(restored.ty, original.ty)
        Oracle.assert_equal(restored.rotation, original.rotation)
        Oracle.assert_equal(restored.scale, original.scale)


class TestStabilizationData:
    """Tests for StabilizationData dataclass."""

    def test_create_default(self):
        """Test creating data with defaults."""
        data = StabilizationData()
        Oracle.assert_equal(len(data.transforms), 0)
        Oracle.assert_equal(len(data.smoothed_transforms), 0)
        Oracle.assert_equal(data.frame_start, 1)
        Oracle.assert_equal(data.frame_end, 1)

    def test_get_transform(self):
        """Test getting transform for frame."""
        data = StabilizationData()
        data.transforms[1] = Transform2D(tx=10.0)
        data.transforms[2] = Transform2D(tx=20.0)

        result = data.get_transform(1)
        Oracle.assert_not_none(result)
        Oracle.assert_equal(result.tx, 10.0)

        result_none = data.get_transform(99)
        Oracle.assert_none(result_none)

    def test_get_smoothed_transform(self):
        """Test getting smoothed transform for frame."""
        data = StabilizationData()
        data.smoothed_transforms[1] = Transform2D(tx=5.0)

        result = data.get_smoothed_transform(1)
        Oracle.assert_not_none(result)
        Oracle.assert_equal(result.tx, 5.0)


class TestMotionAnalyzer:
    """Tests for MotionAnalyzer class."""

    def create_test_track(self, name: str, points: list) -> Track:
        """Create a test track with points."""
        track = Track(name=name)
        for frame, x, y in points:
            track.points[frame] = TrackPoint(
                frame=frame,
                position=(x, y),
                status=TrackStatus.OK,
            )
        return track

    def test_analyze_no_motion(self):
        """Test analyzing static points."""
        analyzer = MotionAnalyzer(100, 100)

        # Track with no movement
        track = self.create_test_track("static", [
            (1, 0.5, 0.5),
            (2, 0.5, 0.5),
        ])

        motion = analyzer.analyze_frame_motion([track], 2, 1)

        Oracle.assert_less_than(abs(motion.tx), 0.1)
        Oracle.assert_less_than(abs(motion.ty), 0.1)
        Oracle.assert_less_than(abs(motion.rotation), 0.01)
        Oracle.assert_less_than(abs(motion.scale - 1.0), 0.01)

    def test_analyze_translation(self):
        """Test analyzing translation motion."""
        analyzer = MotionAnalyzer(100, 100)

        # Track moving right
        track = self.create_test_track("moving", [
            (1, 0.4, 0.5),
            (2, 0.6, 0.5),
        ])

        motion = analyzer.analyze_frame_motion([track], 2, 1)

        # Translation should be positive in X (rightward movement)
        # 0.2 * 100 = 20 pixels
        Oracle.assert_greater_than(motion.tx, 10)

    def test_analyze_global_motion(self):
        """Test analyzing global motion across frames."""
        analyzer = MotionAnalyzer(100, 100)

        # Multiple tracks with consistent motion
        track1 = self.create_test_track("t1", [
            (1, 0.3, 0.3),
            (2, 0.4, 0.4),
            (3, 0.5, 0.5),
        ])
        track2 = self.create_test_track("t2", [
            (1, 0.7, 0.3),
            (2, 0.8, 0.4),
            (3, 0.9, 0.5),
        ])

        transforms = analyzer.analyze_global_motion(
            [track1, track2], 1, 3
        )

        Oracle.assert_equal(len(transforms), 3)
        Oracle.assert_in(1, transforms)
        Oracle.assert_in(2, transforms)
        Oracle.assert_in(3, transforms)

    def test_analyze_insufficient_tracks(self):
        """Test with insufficient track points."""
        analyzer = MotionAnalyzer(100, 100)

        # Only one track with one point
        track = Track(name="incomplete")
        track.points[1] = TrackPoint(frame=1, position=(0.5, 0.5), status=TrackStatus.OK)

        motion = analyzer.analyze_frame_motion([track], 2, 1)

        # Should return identity transform
        Oracle.assert_less_than(abs(motion.tx), 0.001)
        Oracle.assert_less_than(abs(motion.ty), 0.001)


class TestMotionSmoother:
    """Tests for MotionSmoother class."""

    def test_gaussian_smooth_identity(self):
        """Test smoothing constant values."""
        values = [5.0] * 10
        smoothed = MotionSmoother.gaussian_smooth(values, sigma=1.0)

        Oracle.assert_equal(len(smoothed), len(values))
        # All values should remain approximately 5.0
        for v in smoothed:
            Oracle.assert_less_than(abs(v - 5.0), 0.1)

    def test_gaussian_smooth_reduces_noise(self):
        """Test that smoothing reduces noise."""
        # Noisy signal
        import random
        random.seed(42)
        base = [5.0] * 50
        noisy = [v + random.uniform(-1, 1) for v in base]
        smoothed = MotionSmoother.gaussian_smooth(noisy, sigma=2.0)

        # Smoothed should have less variance
        noisy_var = sum((v - 5.0)**2 for v in noisy) / len(noisy)
        smooth_var = sum((v - 5.0)**2 for v in smoothed) / len(smoothed)

        Oracle.assert_less_than(smooth_var, noisy_var)

    def test_gaussian_smooth_short_list(self):
        """Test smoothing with very short list."""
        values = [1.0, 2.0]
        smoothed = MotionSmoother.gaussian_smooth(values, sigma=1.0)

        Oracle.assert_equal(len(smoothed), 2)

    def test_smooth_transforms(self):
        """Test smoothing transform sequence."""
        transforms = {}
        for i in range(1, 11):
            transforms[i] = Transform2D(
                tx=float(i),
                ty=float(i * 2),
                rotation=0.0,
                scale=1.0,
            )

        smoothed = MotionSmoother.smooth_transforms(
            transforms,
            smooth_translation=0.5,
            smooth_rotation=0.5,
            smooth_scale=0.5,
        )

        Oracle.assert_equal(len(smoothed), 10)
        # First transform should still exist
        Oracle.assert_in(1, smoothed)


class TestStabilizer:
    """Tests for Stabilizer class."""

    def create_test_tracks(self) -> list:
        """Create test tracks for stabilization."""
        tracks = []

        # Create multiple tracks with consistent motion
        track1 = Track(name="track_1")
        track2 = Track(name="track_2")
        track3 = Track(name="track_3")

        for frame in range(1, 11):
            # Tracks move slightly with some noise
            noise1 = 0.001 * ((frame % 3) - 1)
            noise2 = 0.001 * ((frame % 2) - 0.5)

            track1.points[frame] = TrackPoint(
                frame=frame,
                position=(0.3 + noise1, 0.3 + noise2),
                status=TrackStatus.OK,
            )
            track2.points[frame] = TrackPoint(
                frame=frame,
                position=(0.7 + noise1, 0.3 + noise2),
                status=TrackStatus.OK,
            )
            track3.points[frame] = TrackPoint(
                frame=frame,
                position=(0.5 + noise1, 0.7 + noise2),
                status=TrackStatus.OK,
            )

        tracks.extend([track1, track2, track3])
        return tracks

    def test_create_default(self):
        """Test creating stabilizer with defaults."""
        stabilizer = Stabilizer()
        Oracle.assert_not_none(stabilizer.config)

    def test_create_with_config(self):
        """Test creating stabilizer with config."""
        config = StabilizationConfig(smooth_translation=0.8)
        stabilizer = Stabilizer(config)
        Oracle.assert_equal(stabilizer.config.smooth_translation, 0.8)

    def test_stabilize(self):
        """Test stabilization calculation."""
        config = StabilizationConfig(
            smooth_translation=0.5,
            use_rotation=True,
            use_scale=True,
        )
        stabilizer = Stabilizer(config)

        tracks = self.create_test_tracks()
        data = stabilizer.stabilize(
            tracks=tracks,
            frame_start=1,
            frame_end=10,
            width=1920,
            height=1080,
        )

        Oracle.assert_not_none(data)
        Oracle.assert_equal(data.frame_start, 1)
        Oracle.assert_equal(data.frame_end, 10)
        Oracle.assert_equal(data.width, 1920)
        Oracle.assert_equal(data.height, 1080)
        Oracle.assert_greater_than(len(data.transforms), 0)
        Oracle.assert_greater_than(len(data.smoothed_transforms), 0)

    def test_stabilize_with_progress(self):
        """Test stabilization with progress callback."""
        stabilizer = Stabilizer()
        tracks = self.create_test_tracks()

        progress_values = []
        def callback(p):
            progress_values.append(p)

        stabilizer.stabilize(
            tracks=tracks,
            frame_start=1,
            frame_end=10,
            progress_callback=callback,
        )

        Oracle.assert_greater_than(len(progress_values), 0)
        Oracle.assert_less_than_or_equal(progress_values[-1], 1.0)

    def test_get_stabilization_transform(self):
        """Test getting stabilization transform."""
        stabilizer = Stabilizer()
        tracks = self.create_test_tracks()

        stabilizer.stabilize(tracks=tracks, frame_start=1, frame_end=10)

        transform = stabilizer.get_stabilization_transform(5)
        Oracle.assert_not_none(transform)

    def test_get_stabilization_transform_no_data(self):
        """Test getting transform without stabilization data."""
        stabilizer = Stabilizer()
        transform = stabilizer.get_stabilization_transform(1)
        Oracle.assert_none(transform)

    def test_get_results(self):
        """Test getting all stabilization results."""
        stabilizer = Stabilizer()
        tracks = self.create_test_tracks()

        stabilizer.stabilize(tracks=tracks, frame_start=1, frame_end=10)

        results = stabilizer.get_results()
        Oracle.assert_greater_than(len(results), 0)

    def test_disable_rotation(self):
        """Test with rotation disabled."""
        config = StabilizationConfig(use_rotation=False)
        stabilizer = Stabilizer(config)

        tracks = self.create_test_tracks()
        stabilizer.stabilize(tracks=tracks, frame_start=1, frame_end=10)

        # All smoothed transforms should have rotation = 0
        for frame, t in stabilizer._data.smoothed_transforms.items():
            Oracle.assert_less_than(abs(t.rotation), 0.001)

    def test_disable_scale(self):
        """Test with scale disabled."""
        config = StabilizationConfig(use_scale=False)
        stabilizer = Stabilizer(config)

        tracks = self.create_test_tracks()
        stabilizer.stabilize(tracks=tracks, frame_start=1, frame_end=10)

        # All smoothed transforms should have scale = 1.0
        for frame, t in stabilizer._data.smoothed_transforms.items():
            Oracle.assert_less_than(abs(t.scale - 1.0), 0.001)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def create_test_session(self) -> TrackingSession:
        """Create a test tracking session."""
        session = TrackingSession(
            name="test_session",
            footage=FootageInfo(
                width=1920,
                height=1080,
                frame_start=1,
                frame_end=10,
                frame_rate=24.0,
            ),
        )

        # Add test tracks
        for i in range(3):
            track = Track(name=f"track_{i}")
            for frame in range(1, 11):
                track.points[frame] = TrackPoint(
                    frame=frame,
                    position=(0.3 + i * 0.2, 0.5),
                    status=TrackStatus.OK,
                )
            session.tracks.append(track)

        return session

    def test_stabilize_session(self):
        """Test stabilize_session convenience function."""
        session = self.create_test_session()
        results = stabilize_session(session)

        Oracle.assert_not_none(results)
        Oracle.assert_greater_than(len(results), 0)

    def test_stabilize_session_with_config(self):
        """Test stabilize_session with custom config."""
        session = self.create_test_session()
        config = StabilizationConfig(smooth_translation=0.8)

        results = stabilize_session(session, config)
        Oracle.assert_greater_than(len(results), 0)

    def test_calculate_stabilization_quality(self):
        """Test quality calculation."""
        original = {
            1: Transform2D(tx=0.0),
            2: Transform2D(tx=10.0),
            3: Transform2D(tx=20.0),
        }
        smoothed = {
            1: Transform2D(tx=5.0),
            2: Transform2D(tx=15.0),
            3: Transform2D(tx=25.0),
        }

        quality = calculate_stabilization_quality(original, smoothed)

        Oracle.assert_in("quality", quality)
        Oracle.assert_in("avg_tx_jitter_removed", quality)
        Oracle.assert_in("frames_processed", quality)

    def test_calculate_stabilization_quality_empty(self):
        """Test quality calculation with empty data."""
        quality = calculate_stabilization_quality({}, {})
        Oracle.assert_equal(quality["quality"], 0.0)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_tracks(self):
        """Test with empty track list."""
        stabilizer = Stabilizer()
        data = stabilizer.stabilize(
            tracks=[],
            frame_start=1,
            frame_end=10,
        )

        # Should still return data structure
        Oracle.assert_not_none(data)

    def test_single_frame(self):
        """Test with single frame range."""
        track = Track(name="single")
        track.points[1] = TrackPoint(
            frame=1,
            position=(0.5, 0.5),
            status=TrackStatus.OK,
        )

        stabilizer = Stabilizer()
        data = stabilizer.stabilize(
            tracks=[track],
            frame_start=1,
            frame_end=1,
        )

        Oracle.assert_not_none(data)

    def test_tracks_with_missing_frames(self):
        """Test with tracks that have missing frames."""
        track = Track(name="incomplete")
        track.points[1] = TrackPoint(frame=1, position=(0.5, 0.5), status=TrackStatus.OK)
        track.points[3] = TrackPoint(frame=3, position=(0.6, 0.5), status=TrackStatus.OK)
        # Frame 2 is missing

        stabilizer = Stabilizer()
        data = stabilizer.stabilize(
            tracks=[track],
            frame_start=1,
            frame_end=3,
        )

        Oracle.assert_not_none(data)

    def test_tracks_with_bad_status(self):
        """Test with tracks that have bad status."""
        track = Track(name="bad_track")
        track.points[1] = TrackPoint(frame=1, position=(0.5, 0.5), status=TrackStatus.OK)
        track.points[2] = TrackPoint(frame=2, position=(0.6, 0.5), status=TrackStatus.LOST)

        analyzer = MotionAnalyzer(100, 100)
        motion = analyzer.analyze_frame_motion([track], 2, 1)

        # Should return identity since one point is lost
        Oracle.assert_less_than(abs(motion.tx), 0.001)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
