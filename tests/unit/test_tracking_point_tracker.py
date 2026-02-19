"""
Unit tests for Point Tracker module.

Tests feature detection and KLT optical flow tracking
with fallback implementations.
"""

import pytest
import sys
import math
import random
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.point_tracker import (
    FeatureDetectorEngine,
    FeaturePoint,
    DetectionResult,
    KLTTracker,
    PointTracker,
    TrackingResult,
)
from cinematic.tracking.types import (
    Track,
    TrackPoint,
    TrackStatus,
    TrackingConfig,
    TrackingSession,
    FootageInfo,
    FeatureDetector,
)
from oracle import Oracle


class TestFeaturePoint:
    """Tests for FeaturePoint dataclass."""

    def test_create_default(self):
        """Test creating feature point with defaults."""
        fp = FeaturePoint(position=(0.5, 0.5))
        Oracle.assert_equal(fp.position, (0.5, 0.5))
        Oracle.assert_equal(fp.strength, 1.0)
        Oracle.assert_equal(fp.scale, 1.0)
        Oracle.assert_equal(fp.angle, 0.0)
        Oracle.assert_none(fp.descriptor)

    def test_create_full(self):
        """Test creating feature point with all values."""
        fp = FeaturePoint(
            position=(0.25, 0.75),
            strength=0.85,
            scale=1.5,
            angle=math.pi / 4,
            descriptor=[1.0, 2.0, 3.0],
        )
        Oracle.assert_equal(fp.position, (0.25, 0.75))
        Oracle.assert_equal(fp.strength, 0.85)
        Oracle.assert_equal(fp.scale, 1.5)
        Oracle.assert_equal(fp.angle, math.pi / 4)
        Oracle.assert_equal(fp.descriptor, [1.0, 2.0, 3.0])

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = FeaturePoint(
            position=(0.3, 0.7),
            strength=0.9,
            scale=2.0,
            angle=1.5,
        )
        data = original.to_dict()
        restored = FeaturePoint.from_dict(data)

        Oracle.assert_equal(restored.position, original.position)
        Oracle.assert_equal(restored.strength, original.strength)
        Oracle.assert_equal(restored.scale, original.scale)
        Oracle.assert_equal(restored.angle, original.angle)


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_create_default(self):
        """Test creating detection result with defaults."""
        result = DetectionResult()
        Oracle.assert_equal(len(result.features), 0)
        Oracle.assert_equal(result.frame, 0)
        Oracle.assert_equal(result.method, "unknown")

    def test_create_with_features(self):
        """Test creating detection result with features."""
        features = [
            FeaturePoint(position=(0.1, 0.1)),
            FeaturePoint(position=(0.5, 0.5)),
            FeaturePoint(position=(0.9, 0.9)),
        ]
        result = DetectionResult(features=features, frame=10, method="fast")

        Oracle.assert_equal(len(result.features), 3)
        Oracle.assert_equal(result.frame, 10)
        Oracle.assert_equal(result.method, "fast")

    def test_serialization(self):
        """Test to_dict roundtrip."""
        original = DetectionResult(
            features=[FeaturePoint(position=(0.5, 0.5))],
            frame=25,
            detection_time_ms=15.5,
            method="harris",
        )
        data = original.to_dict()

        Oracle.assert_equal(len(data["features"]), 1)
        Oracle.assert_equal(data["frame"], 25)
        Oracle.assert_equal(data["method"], "harris")


class TestTrackingResult:
    """Tests for TrackingResult dataclass."""

    def test_create_default(self):
        """Test creating tracking result with defaults."""
        result = TrackingResult()
        Oracle.assert_equal(len(result.tracks), 0)
        Oracle.assert_equal(result.tracked_frames, 0)
        Oracle.assert_equal(result.lost_tracks, 0)

    def test_create_with_data(self):
        """Test creating tracking result with data."""
        tracks = [Track(name="t1"), Track(name="t2")]
        result = TrackingResult(
            tracks=tracks,
            tracked_frames=100,
            lost_tracks=5,
            tracking_time_ms=250.0,
        )

        Oracle.assert_equal(len(result.tracks), 2)
        Oracle.assert_equal(result.tracked_frames, 100)
        Oracle.assert_equal(result.lost_tracks, 5)

    def test_serialization(self):
        """Test to_dict roundtrip."""
        original = TrackingResult(
            tracks=[Track(name="test")],
            tracked_frames=50,
            lost_tracks=2,
        )
        data = original.to_dict()

        Oracle.assert_equal(data["tracked_frames"], 50)
        Oracle.assert_equal(data["lost_tracks"], 2)


class TestFeatureDetectorEngine:
    """Tests for FeatureDetectorEngine class."""

    def test_create_default(self):
        """Test creating detector with defaults."""
        detector = FeatureDetectorEngine()
        Oracle.assert_not_none(detector.config)

    def test_create_with_config(self):
        """Test creating detector with config."""
        config = TrackingConfig(
            detector=FeatureDetector.HARRIS,
            max_features=200,
        )
        detector = FeatureDetectorEngine(config)
        Oracle.assert_equal(detector.config.detector, FeatureDetector.HARRIS)

    def test_detect_fallback(self):
        """Test fallback detection (without OpenCV)."""
        config = TrackingConfig(
            detector=FeatureDetector.FAST,
            max_features=100,
        )
        detector = FeatureDetectorEngine(config)

        # Mock image (just needs to be non-None)
        mock_image = [[0]]  # Simplified mock

        result = detector.detect(mock_image)

        # Should detect features even without OpenCV
        Oracle.assert_greater_than(len(result.features), 0)
        Oracle.assert_less_than_or_equal(len(result.features), 100)
        Oracle.assert_equal(result.method, "fast")

    def test_detect_max_features_limit(self):
        """Test that max_features is respected."""
        config = TrackingConfig(max_features=25)
        detector = FeatureDetectorEngine(config)

        result = detector.detect([[0]])

        Oracle.assert_less_than_or_equal(len(result.features), 25)

    def test_detect_timing(self):
        """Test that detection time is recorded."""
        detector = FeatureDetectorEngine()
        result = detector.detect([[0]])

        # Should have recorded some time
        Oracle.assert_greater_than_or_equal(result.detection_time_ms, 0)


class TestKLTTracker:
    """Tests for KLTTracker class."""

    def test_create_default(self):
        """Test creating tracker with defaults."""
        tracker = KLTTracker()
        Oracle.assert_not_none(tracker.config)

    def test_track_fallback(self):
        """Test fallback tracking (without OpenCV)."""
        tracker = KLTTracker()

        prev_points = [(0.5, 0.5), (0.3, 0.7), (0.7, 0.3)]

        new_points, status, errors = tracker.track(
            prev_image=[[0]],
            curr_image=[[0]],
            prev_points=prev_points,
        )

        # Should return same number of points
        Oracle.assert_equal(len(new_points), len(prev_points))
        Oracle.assert_equal(len(status), len(prev_points))
        Oracle.assert_equal(len(errors), len(prev_points))

        # Most should succeed (90% in fallback)
        success_count = sum(1 for s in status if s)
        Oracle.assert_greater_than(success_count, 0)


class TestPointTracker:
    """Tests for PointTracker class."""

    def _create_mock_get_frame(self, frame_range=(1, 120)):
        """Create mock get_frame function."""
        def get_frame(frame):
            # Return mock image data
            return [[0]]  # Simplified mock
        return get_frame

    def test_create_default(self):
        """Test creating point tracker with defaults."""
        tracker = PointTracker()
        Oracle.assert_not_none(tracker.config)
        Oracle.assert_not_none(tracker.detector)
        Oracle.assert_not_none(tracker.klt)

    def test_detect_features(self):
        """Test feature detection creates tracks."""
        config = TrackingConfig(max_features=50)
        tracker = PointTracker(config)

        tracks = tracker.detect_features(
            frame=1,
            image=[[0]],
        )

        # Should create tracks from features
        Oracle.assert_greater_than(len(tracks), 0)

        # Each track should have a point at frame 1
        for track in tracks:
            point = track.get_point_at_frame(1)
            Oracle.assert_not_none(point)
            Oracle.assert_equal(point.status, TrackStatus.OK)

    def test_detect_features_excludes_existing(self):
        """Test that detection excludes existing track positions."""
        tracker = PointTracker()

        # Create existing track
        existing = Track(
            name="existing",
            points=[TrackPoint(frame=1, position=(0.5, 0.5))],
        )

        new_tracks = tracker.detect_features(
            frame=1,
            image=[[0]],
            exclude_existing=[existing],
        )

        # New tracks should not be at same position
        for track in new_tracks:
            point = track.get_point_at_frame(1)
            # Allow some tolerance
            dist = math.sqrt(
                (point.position[0] - 0.5) ** 2 +
                (point.position[1] - 0.5) ** 2
            )
            # Should be at least 0.01 away (due to quantization to 2 decimals)
            Oracle.assert_greater_than(dist, 0.005)

    def test_track_forward(self):
        """Test forward tracking."""
        config = TrackingConfig(min_features=10)
        tracker = PointTracker(config)

        # Create initial tracks
        tracks = tracker.detect_features(frame=1, image=[[0]])

        get_frame = self._create_mock_get_frame()

        result = tracker.track_forward(
            tracks=tracks,
            start_frame=1,
            end_frame=10,
            get_frame_func=get_frame,
        )

        # Should have tracked forward
        Oracle.assert_greater_than(result.tracked_frames, 0)
        Oracle.assert_equal(len(result.tracks), len(tracks))

        # Each track should have points for multiple frames
        for track in result.tracks:
            Oracle.assert_greater_than(len(track.points), 1)

    def test_track_backward(self):
        """Test backward tracking."""
        tracker = PointTracker()

        # Create tracks at end frame
        tracks = tracker.detect_features(frame=10, image=[[0]])

        get_frame = self._create_mock_get_frame()

        result = tracker.track_backward(
            tracks=tracks,
            start_frame=10,
            end_frame=1,
            get_frame_func=get_frame,
        )

        # Should have tracked backward
        Oracle.assert_greater_than(result.tracked_frames, 0)

    def test_auto_track(self):
        """Test automatic tracking with replenishment."""
        config = TrackingConfig(
            min_features=20,
            max_features=100,
        )
        tracker = PointTracker(config)

        session = TrackingSession(
            name="auto_test",
            footage=FootageInfo(frame_start=1, frame_end=30),
        )

        get_frame = self._create_mock_get_frame((1, 30))

        progress_values = []

        def progress_cb(progress, stage):
            progress_values.append((progress, stage))

        result = tracker.auto_track(
            session=session,
            get_frame_func=get_frame,
            progress_callback=progress_cb,
        )

        # Should have tracked all frames
        Oracle.assert_greater_than(result.tracked_frames, 0)

        # Should have created multiple tracks
        Oracle.assert_greater_than(len(result.tracks), 0)

        # Progress should have been reported
        Oracle.assert_greater_than(len(progress_values), 0)

    def test_auto_track_maintains_min_tracks(self):
        """Test that auto_track maintains minimum track count."""
        config = TrackingConfig(min_features=30)
        tracker = PointTracker(config)

        session = TrackingSession(
            footage=FootageInfo(frame_start=1, frame_end=20),
        )

        get_frame = self._create_mock_get_frame()

        result = tracker.auto_track(
            session=session,
            get_frame_func=get_frame,
        )

        # Should have at least min_features tracks
        Oracle.assert_greater_than_or_equal(len(result.tracks), 30)

    def test_generate_track_color(self):
        """Test track color generation."""
        tracker = PointTracker()

        colors = [tracker._generate_track_color(i) for i in range(10)]

        # All colors should be unique (mostly)
        unique_colors = set(colors)
        Oracle.assert_greater_than(len(unique_colors), 8)  # Allow some collision

        # All colors should be in valid range
        for r, g, b in colors:
            Oracle.assert_greater_than_or_equal(r, 0)
            Oracle.assert_less_than_or_equal(r, 1)
            Oracle.assert_greater_than_or_equal(g, 0)
            Oracle.assert_less_than_or_equal(g, 1)
            Oracle.assert_greater_than_or_equal(b, 0)
            Oracle.assert_less_than_or_equal(b, 1)


class TestPointTrackerIntegration:
    """Integration tests for PointTracker."""

    def test_full_tracking_workflow(self):
        """Test complete tracking workflow."""
        config = TrackingConfig(
            detector=FeatureDetector.FAST,
            min_features=50,
            max_features=200,
            auto_keyframe=True,
            keyframe_interval=10,
        )
        tracker = PointTracker(config)

        # Create session
        session = TrackingSession(
            name="workflow_test",
            footage=FootageInfo(frame_start=1, frame_end=60),
        )

        # Mock frame provider
        get_frame = lambda f: [[0]]

        # Run auto tracking
        result = tracker.auto_track(
            session=session,
            get_frame_func=get_frame,
        )

        # Update session with results
        session.tracks = result.tracks

        # Verify results
        Oracle.assert_greater_than(len(session.tracks), 0)

        # Check that tracks have keyframes
        tracks_with_keyframes = sum(1 for t in session.tracks if t.is_keyframe)
        Oracle.assert_greater_than(tracks_with_keyframes, 0)

        # Check that tracks span the frame range
        for track in session.tracks[:10]:  # Check first 10
            frame_range = track.get_frame_range()
            Oracle.assert_greater_than(frame_range[1] - frame_range[0], 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
