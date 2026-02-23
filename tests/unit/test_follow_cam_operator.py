"""
Unit tests for Follow Camera Operator Behavior (Phase 8.2)

Tests the operator behavior simulation, oscillation prevention,
and human-like camera movement features.

Part of Phase 8.2 - Obstacle Avoidance
Beads: blender_gsd-57, blender_gsd-58
"""

import pytest
import math
from typing import Tuple

from lib.cinematic.follow_cam.types import (
    OperatorBehavior,
    FollowCameraConfig,
)
from lib.cinematic.follow_cam.prediction import (
    OscillationPreventer,
    apply_breathing,
    apply_reaction_delay,
    calculate_angle_preference,
)


class TestOperatorBehavior:
    """Tests for OperatorBehavior dataclass."""

    def test_default_values(self):
        """Test default values are sensible."""
        ob = OperatorBehavior()

        assert ob.reaction_delay == 0.1
        assert ob.avoid_jerky_motion is True
        assert ob.min_movement_time == 0.3
        assert ob.horizontal_angle_range == (-45.0, 45.0)
        assert ob.vertical_angle_range == (10.0, 30.0)
        assert ob.breathing_enabled is True
        assert ob.breathing_amplitude == 0.01
        assert ob.breathing_frequency == 0.25
        assert ob.oscillation_threshold == 0.1
        assert ob.position_history_size == 10
        assert ob.max_direction_changes == 3

    def test_custom_values(self):
        """Test custom values can be set."""
        ob = OperatorBehavior(
            reaction_delay=0.2,
            breathing_enabled=False,
            oscillation_threshold=0.05,
        )

        assert ob.reaction_delay == 0.2
        assert ob.breathing_enabled is False
        assert ob.oscillation_threshold == 0.05

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        ob = OperatorBehavior(
            reaction_delay=0.15,
            breathing_amplitude=0.02,
            weight_visibility=0.8,
        )

        d = ob.to_dict()
        ob2 = OperatorBehavior.from_dict(d)

        assert ob2.reaction_delay == 0.15
        assert ob2.breathing_amplitude == 0.02
        assert ob2.weight_visibility == 0.8

    def test_in_follow_camera_config(self):
        """Test OperatorBehavior is part of FollowCameraConfig."""
        cfg = FollowCameraConfig()

        assert hasattr(cfg, 'operator_behavior')
        assert isinstance(cfg.operator_behavior, OperatorBehavior)

    def test_config_serialization_with_operator(self):
        """Test FollowCameraConfig serialization includes operator_behavior."""
        cfg = FollowCameraConfig(
            operator_behavior=OperatorBehavior(
                reaction_delay=0.2,
                breathing_enabled=False,
            )
        )

        d = cfg.to_dict()
        assert 'operator_behavior' in d
        assert d['operator_behavior']['reaction_delay'] == 0.2

        cfg2 = FollowCameraConfig.from_dict(d)
        assert cfg2.operator_behavior.reaction_delay == 0.2
        assert cfg2.operator_behavior.breathing_enabled is False


class TestOscillationPreventer:
    """Tests for OscillationPreventer class."""

    def test_default_values(self):
        """Test default initialization."""
        op = OscillationPreventer()

        assert op.threshold == 0.1
        assert op.history_size == 10
        assert op.max_direction_changes == 3
        assert op.damping_strength == 0.5

    def test_filter_position_no_movement(self):
        """Test filtering when target equals current (no movement)."""
        op = OscillationPreventer()
        pos = (0.0, 0.0, 0.0)

        result, damping = op.filter_position(pos, pos, 0.0)

        assert result == pos
        assert damping == 0.0

    def test_filter_position_below_threshold(self):
        """Test filtering when movement is below threshold."""
        op = OscillationPreventer(threshold=0.1)
        current = (0.0, 0.0, 0.0)
        target = (0.05, 0.0, 0.0)  # Below threshold

        result, damping = op.filter_position(target, current, 0.0, 1/60)

        # Should stay at current when below threshold
        assert result == current

    def test_filter_position_normal_movement(self):
        """Test filtering with normal movement."""
        op = OscillationPreventer()
        current = (0.0, 0.0, 0.0)
        target = (1.0, 0.0, 0.0)

        result, damping = op.filter_position(target, current, 0.0, 1/60)

        # First movement should not be damped
        assert result == target
        assert damping == 0.0

    def test_oscillation_detection(self):
        """Test oscillation is detected with rapid direction changes."""
        op = OscillationPreventer(
            threshold=0.01,
            max_direction_changes=2,
        )

        current = (0.0, 0.0, 0.0)
        time = 0.0
        dt = 0.1  # 100ms steps, so all changes happen within 1 second

        # Move right
        target1 = (1.0, 0.0, 0.0)
        result, damping = op.filter_position(target1, current, time, dt)
        time += dt

        # Move left (direction change 1)
        target2 = (-1.0, 0.0, 0.0)
        result, damping = op.filter_position(target2, result, time, dt)
        time += dt

        # Move right again (direction change 2)
        target3 = (1.0, 0.0, 0.0)
        result, damping = op.filter_position(target3, result, time, dt)
        time += dt

        # Move left again (direction change 3 - should trigger damping)
        target4 = (-1.0, 0.0, 0.0)
        result, damping = op.filter_position(target4, result, time, dt)

        # Should be damping now
        assert op.is_oscillating() is True
        assert damping > 0.0

    def test_stability_score(self):
        """Test stability score calculation."""
        op = OscillationPreventer()

        # Initially stable
        assert op.get_stability_score() == 1.0

    def test_reset(self):
        """Test reset clears all state."""
        op = OscillationPreventer()

        # Record some positions
        op.record_position((0, 0, 0), 0.0)
        op.record_position((1, 0, 0), 1/60)
        op._current_damping = 0.5

        op.reset()

        assert len(op._position_history) == 0
        assert len(op._time_history) == 0
        assert op._current_damping == 0.0

    def test_from_operator_behavior(self):
        """Test factory method from OperatorBehavior."""
        ob = OperatorBehavior(
            oscillation_threshold=0.05,
            position_history_size=15,
            max_direction_changes=5,
        )

        op = OscillationPreventer.from_operator_behavior(ob)

        assert op.threshold == 0.05
        assert op.history_size == 15
        assert op.max_direction_changes == 5


class TestApplyBreathing:
    """Tests for apply_breathing function."""

    def test_breathing_disabled(self):
        """Test breathing when disabled."""
        pos = (0.0, 0.0, 1.0)
        result = apply_breathing(pos, 0.0, enabled=False)

        assert result == pos

    def test_breathing_zero_amplitude(self):
        """Test breathing with zero amplitude."""
        pos = (0.0, 0.0, 1.0)
        result = apply_breathing(pos, 0.0, amplitude=0.0)

        assert result == pos

    def test_breathing_applies_vertical_offset(self):
        """Test breathing applies vertical offset."""
        pos = (0.0, 0.0, 1.0)

        # At t=0, sin(0) = 0, so no offset
        result = apply_breathing(pos, 0.0, amplitude=0.01)
        assert result[2] == 1.0

        # At t=0.5s with frequency 0.25Hz, sin(pi/4) = sqrt(2)/2
        result = apply_breathing(pos, 0.5, amplitude=0.01, frequency=0.25)
        expected_z = 1.0 + math.sin(0.5 * 0.25 * 2 * math.pi) * 0.01
        assert abs(result[2] - expected_z) < 0.0001

    def test_breathing_cycle(self):
        """Test breathing completes a full cycle."""
        pos = (0.0, 0.0, 1.0)
        frequency = 1.0  # 1 Hz

        # At t=0 (start of cycle)
        result0 = apply_breathing(pos, 0.0, amplitude=0.01, frequency=frequency)

        # At t=0.25 (peak)
        result25 = apply_breathing(pos, 0.25, amplitude=0.01, frequency=frequency)

        # At t=0.5 (back to zero)
        result50 = apply_breathing(pos, 0.5, amplitude=0.01, frequency=frequency)

        # At t=1.0 (same as t=0)
        result100 = apply_breathing(pos, 1.0, amplitude=0.01, frequency=frequency)

        assert abs(result0[2] - result100[2]) < 0.0001
        assert result25[2] > result0[2]  # Peak should be higher


class TestApplyReactionDelay:
    """Tests for apply_reaction_delay function."""

    def test_no_delay(self):
        """Test with no delay (instant response)."""
        current = (0.0, 0.0, 0.0)
        target = (1.0, 0.0, 0.0)

        result = apply_reaction_delay(current, target, 0.0, 1/60)

        assert result == target

    def test_with_delay(self):
        """Test with reaction delay."""
        current = (0.0, 0.0, 0.0)
        target = (1.0, 0.0, 0.0)
        delay = 0.5  # 500ms reaction time

        result = apply_reaction_delay(current, target, delay, 1/60)

        # Should move towards target but not reach it
        assert result[0] > current[0]
        assert result[0] < target[0]

    def test_delay_blend_calculation(self):
        """Test delay creates proper blend factor."""
        current = (0.0, 0.0, 0.0)
        target = (1.0, 0.0, 0.0)

        # With delay of 0.1s and dt of 1/60, blend should be ~0.167
        # blend = (dt / delay) * (1 - smoothing)
        # blend = (1/60 / 0.1) * 0.9 = 0.167 * 0.9 = 0.15
        result = apply_reaction_delay(current, target, 0.1, 1/60, smoothing=0.1)

        expected_x = 0.0 + (1.0 - 0.0) * ((1/60 / 0.1) * 0.9)
        assert abs(result[0] - expected_x) < 0.001


class TestCalculateAnglePreference:
    """Tests for calculate_angle_preference function."""

    def test_within_range(self):
        """Test when angles are within preferred range."""
        result = calculate_angle_preference(
            (0.0, 20.0),  # yaw=0, pitch=20
            (-45.0, 45.0),  # horizontal range
            (10.0, 30.0),  # vertical range
            weight=0.5,
        )

        # Within range, no adjustment needed
        assert result == (0.0, 20.0)

    def test_outside_horizontal_range(self):
        """Test when yaw is outside preferred range."""
        result = calculate_angle_preference(
            (60.0, 20.0),  # yaw=60 (outside -45 to 45)
            (-45.0, 45.0),
            (10.0, 30.0),
            weight=1.0,  # Full weight
        )

        # Should be pulled back to max (45.0)
        assert result[0] == 45.0

    def test_outside_vertical_range(self):
        """Test when pitch is outside preferred range."""
        result = calculate_angle_preference(
            (0.0, 40.0),  # pitch=40 (outside 10-30)
            (-45.0, 45.0),
            (10.0, 30.0),
            weight=1.0,
        )

        # Should be pulled back to max (30.0)
        assert result[1] == 30.0

    def test_weight_applied(self):
        """Test weight moderates adjustment."""
        result = calculate_angle_preference(
            (60.0, 20.0),
            (-45.0, 45.0),
            (10.0, 30.0),
            weight=0.5,  # 50% weight
        )

        # Offset is 15 (60-45), with 50% weight = 7.5
        # Result should be 60 - 7.5 = 52.5
        assert result[0] == 52.5


class TestIntegration:
    """Integration tests for operator behavior system."""

    def test_full_operator_workflow(self):
        """Test complete workflow with all components."""
        # Create config with operator behavior
        config = FollowCameraConfig(
            operator_behavior=OperatorBehavior(
                breathing_enabled=True,
                breathing_amplitude=0.02,
                reaction_delay=0.15,
            )
        )

        # Create oscillation preventer from config
        preventer = OscillationPreventer.from_operator_behavior(
            config.operator_behavior
        )

        # Simulate camera movement
        current_pos = (0.0, 0.0, 1.5)
        target_pos = (0.0, -3.0, 1.5)
        time = 0.0

        # Apply operator behavior effects
        for _ in range(10):
            # Filter for oscillation
            filtered_pos, damping = preventer.filter_position(
                target_pos, current_pos, time, 1/60
            )

            # Apply reaction delay
            delayed_pos = apply_reaction_delay(
                current_pos,
                filtered_pos,
                config.operator_behavior.reaction_delay,
                1/60,
            )

            # Apply breathing
            final_pos = apply_breathing(
                delayed_pos,
                time,
                config.operator_behavior.breathing_amplitude,
                config.operator_behavior.breathing_frequency,
                config.operator_behavior.breathing_enabled,
            )

            current_pos = final_pos
            time += 1/60

        # Camera should have moved towards target
        assert current_pos[1] < 0.0  # Moved towards target y=-3

    def test_oscillation_prevented_in_config(self):
        """Test oscillation prevention integrates with FollowCameraConfig."""
        config = FollowCameraConfig(
            operator_behavior=OperatorBehavior(
                oscillation_threshold=0.05,
                max_direction_changes=2,
            )
        )

        preventer = OscillationPreventer.from_operator_behavior(
            config.operator_behavior
        )

        # Verify settings propagated
        assert preventer.threshold == 0.05
        assert preventer.max_direction_changes == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
