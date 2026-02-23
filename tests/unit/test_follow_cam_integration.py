"""
Tests for Follow Camera Integration & Polish (Phase 8.4)

Tests:
- Dynamic framing based on velocity
- Action framing for fast-paced sequences
- Speed-based distance calculation
- Frame-by-frame analysis
- Report generation

Beads: blender_gsd-65
"""

import pytest
import math
import tempfile
import os

from lib.cinematic.follow_cam import (
    # Framing
    FramingResult,
    calculate_dynamic_framing,
    calculate_action_framing,
    calculate_speed_based_distance,
    # Frame analysis
    FrameAnalysis,
    FrameAnalyzer,
    # Supporting types
    FollowCameraConfig,
    CameraState,
    FollowMode,
)


class TestDynamicFraming:
    """Tests for dynamic framing based on target velocity."""

    def test_dynamic_framing_below_threshold(self):
        """Dynamic framing should not apply below speed threshold."""
        framing = FramingResult(
            target_offset=(0.5, 0.0, 0.2),
            horizontal_shift=0.5,
            vertical_shift=0.2,
        )

        # Slow velocity
        result = calculate_dynamic_framing(
            target_velocity=(0.5, 0.5, 0.0),  # ~0.7 m/s
            current_framing=framing,
            speed_threshold=2.0,
        )

        # Should return unchanged framing
        assert result.target_offset == framing.target_offset
        assert result.horizontal_shift == framing.horizontal_shift

    def test_dynamic_framing_above_threshold(self):
        """Dynamic framing should apply above speed threshold."""
        framing = FramingResult(
            target_offset=(0.5, 0.0, 0.2),
            horizontal_shift=0.5,
            vertical_shift=0.2,
        )

        # Fast velocity (moving forward in Y direction)
        result = calculate_dynamic_framing(
            target_velocity=(0.0, 5.0, 0.0),  # 5 m/s forward
            current_framing=framing,
            speed_threshold=2.0,
            anticipation_factor=0.3,
        )

        # Should have adjusted offset
        assert result.target_offset != framing.target_offset
        # Y offset should increase (anticipating forward movement)
        assert result.target_offset[1] > framing.target_offset[1]

    def test_dynamic_framing_direction_follows_velocity(self):
        """Dynamic framing offset should follow velocity direction."""
        framing = FramingResult()

        # Moving in +X direction
        result_x = calculate_dynamic_framing(
            target_velocity=(5.0, 0.0, 0.0),
            current_framing=framing,
            speed_threshold=2.0,
        )

        # Moving in +Y direction
        result_y = calculate_dynamic_framing(
            target_velocity=(0.0, 5.0, 0.0),
            current_framing=framing,
            speed_threshold=2.0,
        )

        # X velocity should create larger X offset
        assert abs(result_x.target_offset[0]) > abs(result_y.target_offset[0])
        # Y velocity should create larger Y offset
        assert abs(result_y.target_offset[1]) > abs(result_x.target_offset[1])

    def test_dynamic_framing_scales_with_speed(self):
        """Faster targets should get larger anticipation offset."""
        framing = FramingResult()

        result_slow = calculate_dynamic_framing(
            target_velocity=(0.0, 3.0, 0.0),  # 3 m/s
            current_framing=framing,
            speed_threshold=2.0,
        )

        result_fast = calculate_dynamic_framing(
            target_velocity=(0.0, 10.0, 0.0),  # 10 m/s
            current_framing=framing,
            speed_threshold=2.0,
        )

        # Faster should have larger offset magnitude
        slow_offset = math.sqrt(sum(v**2 for v in result_slow.target_offset))
        fast_offset = math.sqrt(sum(v**2 for v in result_fast.target_offset))
        assert fast_offset > slow_offset

    def test_dynamic_framing_preserves_dead_zone(self):
        """Dynamic framing should preserve dead zone status."""
        framing = FramingResult(is_within_dead_zone=True)

        result = calculate_dynamic_framing(
            target_velocity=(0.0, 5.0, 0.0),
            current_framing=framing,
            speed_threshold=2.0,
        )

        assert result.is_within_dead_zone == framing.is_within_dead_zone


class TestActionFraming:
    """Tests for action sequence framing."""

    def test_action_framing_no_action(self):
        """No action should return unchanged framing."""
        framing = FramingResult(
            target_offset=(0.5, 0.0, 0.2),
            horizontal_shift=0.5,
            vertical_shift=0.2,
            framing_quality=0.9,
        )

        result = calculate_action_framing(
            is_action=False,
            action_intensity=0.5,
            base_framing=framing,
        )

        assert result.target_offset == framing.target_offset
        assert result.framing_quality == framing.framing_quality

    def test_action_framing_zero_intensity(self):
        """Zero intensity should return unchanged framing."""
        framing = FramingResult()

        result = calculate_action_framing(
            is_action=True,
            action_intensity=0.0,
            base_framing=framing,
        )

        assert result.target_offset == framing.target_offset

    def test_action_framing_centers_subject(self):
        """Action framing should center the subject more."""
        framing = FramingResult(
            target_offset=(1.0, 0.5, 0.5),
            horizontal_shift=1.0,
            vertical_shift=0.5,
        )

        result = calculate_action_framing(
            is_action=True,
            action_intensity=1.0,
            base_framing=framing,
        )

        # All offsets should be reduced (centering)
        assert abs(result.target_offset[0]) < abs(framing.target_offset[0])
        assert abs(result.target_offset[1]) < abs(framing.target_offset[1])
        assert abs(result.target_offset[2]) < abs(framing.target_offset[2])

    def test_action_framing_scales_with_intensity(self):
        """Higher intensity should create more centering."""
        framing = FramingResult(
            target_offset=(1.0, 0.0, 0.0),
        )

        result_low = calculate_action_framing(
            is_action=True,
            action_intensity=0.3,
            base_framing=framing,
        )

        result_high = calculate_action_framing(
            is_action=True,
            action_intensity=1.0,
            base_framing=framing,
        )

        # High intensity should reduce offset more
        assert abs(result_high.target_offset[0]) < abs(result_low.target_offset[0])

    def test_action_framing_reduces_quality_expectation(self):
        """Action framing should accept lower quality."""
        framing = FramingResult(framing_quality=0.9)

        result = calculate_action_framing(
            is_action=True,
            action_intensity=1.0,
            base_framing=framing,
        )

        # Quality should be reduced during action
        assert result.framing_quality < framing.framing_quality

    def test_action_framing_preserves_dead_zone(self):
        """Action framing should preserve dead zone status."""
        framing = FramingResult(is_within_dead_zone=True)

        result = calculate_action_framing(
            is_action=True,
            action_intensity=0.5,
            base_framing=framing,
        )

        assert result.is_within_dead_zone == framing.is_within_dead_zone


class TestSpeedBasedDistance:
    """Tests for speed-based distance calculation."""

    def test_base_distance_at_rest(self):
        """At rest, should return base distance."""
        result = calculate_speed_based_distance(
            base_distance=5.0,
            target_speed=0.0,
        )

        assert result == 5.0

    def test_distance_increases_with_speed(self):
        """Faster targets should have larger distance."""
        base = 5.0

        result_slow = calculate_speed_based_distance(
            base_distance=base,
            target_speed=2.0,
        )

        result_fast = calculate_speed_based_distance(
            base_distance=base,
            target_speed=8.0,
        )

        assert result_slow > base
        assert result_fast > result_slow

    def test_distance_respects_minimum(self):
        """Distance should not go below minimum."""
        result = calculate_speed_based_distance(
            base_distance=1.0,
            target_speed=-10.0,  # Negative speed shouldn't matter
            min_distance=2.0,
        )

        assert result >= 2.0

    def test_distance_respects_maximum(self):
        """Distance should not exceed maximum."""
        result = calculate_speed_based_distance(
            base_distance=5.0,
            target_speed=100.0,
            max_distance=15.0,
        )

        assert result <= 15.0

    def test_speed_scale_affects_adjustment(self):
        """Speed scale should control how much speed affects distance."""
        base = 5.0
        speed = 4.0

        result_small = calculate_speed_based_distance(
            base_distance=base,
            target_speed=speed,
            speed_scale=0.25,
        )

        result_large = calculate_speed_based_distance(
            base_distance=base,
            target_speed=speed,
            speed_scale=1.0,
        )

        # Larger scale should create larger adjustment
        assert result_large > result_small


class TestFrameAnalysis:
    """Tests for frame analysis dataclass."""

    def test_default_values(self):
        """FrameAnalysis should have sensible defaults."""
        analysis = FrameAnalysis()

        assert analysis.frame == 0
        assert analysis.timestamp == 0.0
        assert analysis.camera_position == (0.0, 0.0, 0.0)
        assert analysis.warnings == []

    def test_to_dict(self):
        """FrameAnalysis should convert to dictionary."""
        analysis = FrameAnalysis(
            frame=100,
            timestamp=3.33,
            camera_position=(1.0, 2.0, 3.0),
            camera_rotation=(45.0, 10.0, 0.0),
            framing_quality=0.85,
            warnings=["Low framing quality"],
        )

        data = analysis.to_dict()

        assert data["frame"] == 100
        assert data["timestamp"] == 3.33
        # to_dict converts tuples to lists
        assert data["camera_position"] == [1.0, 2.0, 3.0]
        assert "Low framing quality" in data["warnings"]

    def test_add_warning(self):
        """FrameAnalysis should support adding warnings."""
        analysis = FrameAnalysis()
        analysis.warnings.append("Test warning")

        assert "Test warning" in analysis.warnings


class TestFrameAnalyzer:
    """Tests for frame analyzer class."""

    def test_initialization(self):
        """FrameAnalyzer should initialize with empty frame list."""
        analyzer = FrameAnalyzer()

        assert analyzer.get_frames() == []

    def test_analyze_frame_basic(self):
        """FrameAnalyzer should create basic frame analysis."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()
        state = CameraState()

        analysis = analyzer.analyze_frame(
            frame=0,
            camera_state=state,
            config=config,
        )

        assert analysis.frame == 0
        assert len(analyzer.get_frames()) == 1

    def test_analyze_frame_with_all_params(self):
        """FrameAnalyzer should capture all frame parameters."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()
        state = CameraState(
            position=(5.0, 10.0, 3.0),
            rotation=(45.0, -15.0, 0.0),
        )

        analysis = analyzer.analyze_frame(
            frame=100,
            camera_state=state,
            config=config,
            framing_quality=0.9,
            damping=0.5,
            oscillation_detected=False,
            is_occluded=True,
        )

        assert analysis.frame == 100
        assert analysis.camera_position == (5.0, 10.0, 3.0)
        assert analysis.camera_rotation == (45.0, -15.0, 0.0)
        assert analysis.framing_quality == 0.9
        assert analysis.damping_applied == 0.5
        assert analysis.is_occluded is True

    def test_analyze_multiple_frames(self):
        """FrameAnalyzer should accumulate analyses."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()

        for i in range(10):
            analyzer.analyze_frame(
                frame=i,
                camera_state=CameraState(position=(i * 0.5, 0.0, 0.0)),
                config=config,
            )

        assert len(analyzer.get_frames()) == 10

    def test_generate_report_empty(self):
        """Empty analyzer should generate error report."""
        analyzer = FrameAnalyzer()

        report = analyzer.generate_report()

        assert "error" in report

    def test_generate_report_with_data(self):
        """Analyzer should generate comprehensive report."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()

        # Add some frames
        for i in range(5):
            analyzer.analyze_frame(
                frame=i,
                camera_state=CameraState(position=(i, i, i)),
                config=config,
                framing_quality=0.8 + i * 0.02,
                damping=0.3 if i < 3 else 0.6,
                is_occluded=(i == 2),
            )

        report = analyzer.generate_report()

        assert report["summary"]["total_frames"] == 5
        assert "mode_distribution" in report
        assert "problem_frames" in report
        assert "average_framing_quality" in report["summary"]
        assert report["summary"]["occluded_frame_count"] == 1

    def test_save_report(self):
        """Analyzer should save report to file."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()

        analyzer.analyze_frame(
            frame=0,
            camera_state=CameraState(),
            config=config,
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = analyzer.save_report(temp_path)

            assert result is True
            assert os.path.exists(temp_path)

            # Verify content
            import json
            with open(temp_path, 'r') as f:
                saved = json.load(f)

            assert saved["summary"]["total_frames"] == 1
        finally:
            os.unlink(temp_path)

    def test_warning_generation_low_quality(self):
        """Analyzer should warn on low framing quality."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()

        analysis = analyzer.analyze_frame(
            frame=0,
            camera_state=CameraState(),
            config=config,
            framing_quality=0.4,  # Low quality
        )

        assert any("Low framing quality" in w for w in analysis.warnings)

    def test_warning_generation_occlusion(self):
        """Analyzer should warn on occlusion."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()

        analysis = analyzer.analyze_frame(
            frame=0,
            camera_state=CameraState(),
            config=config,
            is_occluded=True,
        )

        assert any("occluded" in w.lower() for w in analysis.warnings)

    def test_warning_generation_high_damping(self):
        """Analyzer should warn on high damping."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig()

        analysis = analyzer.analyze_frame(
            frame=0,
            camera_state=CameraState(),
            config=config,
            damping=0.9,  # High damping
        )

        assert any("High damping" in w for w in analysis.warnings)


class TestIntegration:
    """Integration tests combining Phase 8.4 features."""

    def test_dynamic_then_action_framing(self):
        """Dynamic framing should work before action framing."""
        base_framing = FramingResult(
            target_offset=(0.5, 0.0, 0.2),
        )

        # Apply dynamic framing for moving target
        dynamic = calculate_dynamic_framing(
            target_velocity=(0.0, 5.0, 0.0),
            current_framing=base_framing,
            speed_threshold=2.0,
        )

        # Then apply action framing during action
        action = calculate_action_framing(
            is_action=True,
            action_intensity=0.7,
            base_framing=dynamic,
        )

        # Action should reduce the dynamic offset
        assert abs(action.target_offset[0]) <= abs(dynamic.target_offset[0])

    def test_full_pipeline_with_analyzer(self):
        """Test full pipeline with frame analyzer."""
        analyzer = FrameAnalyzer()
        config = FollowCameraConfig(
            follow_mode=FollowMode.OVER_SHOULDER,
        )

        # Simulate a shot sequence
        for frame in range(60):
            # Calculate framing
            base_framing = FramingResult()
            velocity = (0.0, 3.0 + frame * 0.05, 0.0)  # Accelerating

            # Apply dynamic framing
            dynamic = calculate_dynamic_framing(
                target_velocity=velocity,
                current_framing=base_framing,
                speed_threshold=2.0,
            )

            # Analyze this frame
            analyzer.analyze_frame(
                frame=frame,
                camera_state=CameraState(
                    position=(0.0, -5.0 - frame * 0.1, 2.0),
                    target_velocity=velocity,
                ),
                config=config,
                framing_quality=dynamic.framing_quality,
            )

        report = analyzer.generate_report()

        assert report["summary"]["total_frames"] == 60
        assert "average_framing_quality" in report["summary"]

    def test_speed_based_distance_with_action(self):
        """Speed-based distance should work with action framing."""
        base_distance = 5.0
        high_speed = 8.0

        # Get speed-adjusted distance
        ideal_distance = calculate_speed_based_distance(
            base_distance=base_distance,
            target_speed=high_speed,
        )

        # During action, we might want to use this distance
        framing = FramingResult(
            target_offset=(ideal_distance, 0.0, 0.0),
        )

        action_framing = calculate_action_framing(
            is_action=True,
            action_intensity=0.5,
            base_framing=framing,
        )

        # Both should work together
        assert ideal_distance > base_distance
        assert action_framing.target_offset is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
