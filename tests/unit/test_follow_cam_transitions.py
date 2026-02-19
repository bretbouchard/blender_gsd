"""
Follow Camera Transitions Unit Tests

Tests for: lib/cinematic/follow_cam/transitions.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-56
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.types import (
    TransitionType,
    FollowCameraConfig,
    CameraState,
    FollowMode,
)

from lib.cinematic.follow_cam.transitions import (
    TransitionState,
    TransitionManager,
    calculate_transition_position,
    create_instant_transition,
    create_smooth_transition,
    create_orbit_transition,
    create_dolly_transition,
    _ease_in_out_smoother,
    _ease_dolly,
    _interpolate_rotation,
    _calculate_look_rotation,
)


class TestTransitionState:
    """Unit tests for TransitionState class."""

    def test_initial_state(self):
        """Transition should start with progress 0."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(90.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
        )

        assert transition.progress == 0.0
        assert not transition.is_complete()

    def test_update_progress(self):
        """Update should advance progress."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(90.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
        )

        progress = transition.update(0.5)  # Half duration

        compare_numbers(progress, 0.5, tolerance=0.01)
        assert not transition.is_complete()

    def test_complete_transition(self):
        """Transition should complete when progress reaches 1."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(90.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
        )

        transition.update(1.0)

        compare_numbers(transition.progress, 1.0, tolerance=0.01)
        assert transition.is_complete()

    def test_over_complete(self):
        """Progress should clamp to 1.0."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(90.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
        )

        transition.update(2.0)  # Over duration

        compare_numbers(transition.progress, 1.0, tolerance=0.01)


class TestCutTransition:
    """Unit tests for cut (instant) transition."""

    def test_cut_at_start(self):
        """Cut should stay at start position before complete."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 5.0),
            target_rotation=(45.0, -10.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=0.0,
            transition_type=TransitionType.CUT,
        )

        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be at start (cut happens when progress >= 1)
        compare_vectors(pos.to_tuple(), (0.0, 0.0, 0.0), tolerance=0.01)

    def test_cut_when_complete(self):
        """Cut should jump to target when complete."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 5.0),
            target_rotation=(45.0, -10.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=0.001,  # Very short but non-zero duration
            transition_type=TransitionType.CUT,
        )

        transition.update(0.01)  # Progress to 1.0
        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be at target
        compare_vectors(pos.to_tuple(), (10.0, 0.0, 5.0), tolerance=0.01)


class TestBlendTransition:
    """Unit tests for blend transition."""

    def test_blend_midpoint(self):
        """Blend should be at midpoint at progress 0.5."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(0.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
            transition_type=TransitionType.BLEND,
        )

        transition.update(0.5)
        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be roughly at midpoint (accounting for easing)
        assert 4 < pos.x < 6  # Around 5 with easing

    def test_blend_start(self):
        """Blend should start at start position."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(0.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
            transition_type=TransitionType.BLEND,
        )

        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be at start
        compare_vectors(pos.to_tuple(), (0.0, 0.0, 0.0), tolerance=0.1)

    def test_blend_end(self):
        """Blend should end at target position."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 5.0, 3.0),
            target_rotation=(0.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
            transition_type=TransitionType.BLEND,
        )

        transition.update(1.0)
        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be at target
        compare_vectors(pos.to_tuple(), (10.0, 5.0, 3.0), tolerance=0.1)


class TestOrbitTransition:
    """Unit tests for orbit transition."""

    def test_orbit_around_subject(self):
        """Orbit should arc around subject."""
        transition = TransitionState(
            start_position=(5.0, 0.0, 1.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(-5.0, 0.0, 1.0),
            target_rotation=(0.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
            transition_type=TransitionType.ORBIT,
        )

        subject_pos = (0.0, 0.0, 0.0)

        # At midpoint, should be on one side of the orbit
        transition.update(0.5)
        pos, rot = calculate_transition_position(transition, subject_pos)

        # Position should be different from linear interpolation
        # (would be at 0,0 for linear)
        assert abs(pos.x) > 0 or abs(pos.y) > 0


class TestDollyTransition:
    """Unit tests for dolly transition."""

    def test_dolly_start(self):
        """Dolly should start at start position."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(0.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
            transition_type=TransitionType.DOLLY,
        )

        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be at start
        compare_vectors(pos.to_tuple(), (0.0, 0.0, 0.0), tolerance=0.1)

    def test_dolly_end(self):
        """Dolly should end at target position."""
        transition = TransitionState(
            start_position=(0.0, 0.0, 0.0),
            start_rotation=(0.0, 0.0, 0.0),
            start_mode=FollowMode.OVER_SHOULDER,
            target_position=(10.0, 0.0, 0.0),
            target_rotation=(0.0, 0.0, 0.0),
            target_mode=FollowMode.CHASE,
            duration=1.0,
            transition_type=TransitionType.DOLLY,
        )

        transition.update(1.0)
        pos, rot = calculate_transition_position(transition, (0.0, 0.0, 0.0))

        # Should be close to target (dolly easing may not hit exactly 1.0)
        assert pos.x > 9.5  # Close to target


class TestEasingFunctions:
    """Unit tests for easing functions."""

    def test_ease_start_end(self):
        """Easing should start at 0 and end at 1."""
        assert _ease_in_out_smoother(0.0) == 0.0
        compare_numbers(_ease_in_out_smoother(1.0), 1.0, tolerance=0.001)

    def test_ease_midpoint(self):
        """Easing at midpoint should be 0.5."""
        compare_numbers(_ease_in_out_smoother(0.5), 0.5, tolerance=0.01)

    def test_ease_symmetry(self):
        """Easing should be roughly symmetric."""
        t1 = _ease_in_out_smoother(0.3)
        t2 = _ease_in_out_smoother(0.7)

        # Values should be symmetric around 0.5
        compare_numbers(t1, 1.0 - t2, tolerance=0.05)

    def test_dolly_ease_phases(self):
        """Dolly ease should have distinct phases."""
        # Start slow
        t1 = _ease_dolly(0.1)
        # Middle fast
        t2 = _ease_dolly(0.5) - _ease_dolly(0.4)
        # End slow
        t3 = 1.0 - _ease_dolly(0.9)

        # Start and end should be slower than middle
        assert t1 < t2
        assert t3 < t2


class TestRotationInterpolation:
    """Unit tests for rotation interpolation."""

    def test_interpolate_straight(self):
        """Simple rotation interpolation."""
        result = _interpolate_rotation((0.0, 0.0, 0.0), (90.0, 0.0, 0.0), 0.5)

        compare_numbers(result[0], 45.0, tolerance=0.1)

    def test_angle_wrapping_positive(self):
        """Rotation should take shortest path (positive wrap)."""
        # 350 to 10 should go through 0 (20 degree difference, not 340)
        result = _interpolate_rotation((350.0, 0.0, 0.0), (10.0, 0.0, 0.0), 0.5)

        # Should be around 0 or 360
        assert result[0] < 10 or result[0] > 350

    def test_angle_wrapping_negative(self):
        """Rotation should take shortest path (negative wrap)."""
        # 10 to 350 should go through 0 (20 degree difference)
        result = _interpolate_rotation((10.0, 0.0, 0.0), (350.0, 0.0, 0.0), 0.5)

        # Should be around 0 or 360
        assert result[0] < 10 or result[0] > 350


class TestLookRotation:
    """Unit tests for look rotation calculation."""

    def test_look_forward(self):
        """Looking forward should give zero yaw."""
        # Import Vector from the module
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((0.0, -5.0, 1.0))
        target_pos = Vector((0.0, 0.0, 0.0))

        yaw, pitch, roll = _calculate_look_rotation(cam_pos, target_pos)

        compare_numbers(yaw, 0.0, tolerance=5.0)
        compare_numbers(roll, 0.0, tolerance=0.1)

    def test_look_down(self):
        """Looking down should give negative pitch."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((0.0, 0.0, 10.0))
        target_pos = Vector((0.0, 0.0, 0.0))

        yaw, pitch, roll = _calculate_look_rotation(cam_pos, target_pos)

        assert pitch < -80


class TestTransitionManager:
    """Unit tests for TransitionManager class."""

    def test_no_active_transition(self):
        """Manager should report no transition when none active."""
        manager = TransitionManager()

        assert not manager.is_transitioning()
        compare_numbers(manager.get_progress(), 1.0, tolerance=0.01)

    def test_start_transition(self):
        """Starting transition should mark as transitioning."""
        manager = TransitionManager()
        state = CameraState(
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            current_mode=FollowMode.OVER_SHOULDER,
        )
        config = FollowCameraConfig(transition_duration=1.0)

        manager.start_transition(
            from_state=state,
            to_position=(10.0, 0.0, 0.0),
            to_rotation=(45.0, 0.0, 0.0),
            to_mode=FollowMode.CHASE,
            config=config,
        )

        assert manager.is_transitioning()
        compare_numbers(manager.get_progress(), 0.0, tolerance=0.01)

    def test_update_transition(self):
        """Update should advance transition."""
        manager = TransitionManager()
        state = CameraState(
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            current_mode=FollowMode.OVER_SHOULDER,
        )
        config = FollowCameraConfig(
            transition_duration=1.0,
            transition_type=TransitionType.BLEND,
        )

        manager.start_transition(
            from_state=state,
            to_position=(10.0, 0.0, 0.0),
            to_rotation=(45.0, 0.0, 0.0),
            to_mode=FollowMode.CHASE,
            config=config,
        )

        pos, rot, is_complete = manager.update(0.5, (0.0, 0.0, 0.0))

        assert not is_complete
        compare_numbers(manager.get_progress(), 0.5, tolerance=0.01)

    def test_complete_transition(self):
        """Transition should complete when duration elapsed."""
        manager = TransitionManager()
        state = CameraState(
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            current_mode=FollowMode.OVER_SHOULDER,
        )
        config = FollowCameraConfig(
            transition_duration=0.5,
            transition_type=TransitionType.BLEND,
        )

        manager.start_transition(
            from_state=state,
            to_position=(10.0, 0.0, 0.0),
            to_rotation=(45.0, 0.0, 0.0),
            to_mode=FollowMode.CHASE,
            config=config,
        )

        pos, rot, is_complete = manager.update(0.6, (0.0, 0.0, 0.0))

        assert is_complete
        assert not manager.is_transitioning()

    def test_cancel_transition(self):
        """Cancel should stop active transition."""
        manager = TransitionManager()
        state = CameraState(
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            current_mode=FollowMode.OVER_SHOULDER,
        )
        config = FollowCameraConfig(transition_duration=1.0)

        manager.start_transition(
            from_state=state,
            to_position=(10.0, 0.0, 0.0),
            to_rotation=(45.0, 0.0, 0.0),
            to_mode=FollowMode.CHASE,
            config=config,
        )

        manager.cancel_transition()

        assert not manager.is_transitioning()

    def test_callback_on_complete(self):
        """Callback should be called when transition completes."""
        callback_called = []

        def on_complete():
            callback_called.append(True)

        manager = TransitionManager()
        state = CameraState(
            position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            current_mode=FollowMode.OVER_SHOULDER,
        )
        config = FollowCameraConfig(transition_duration=0.1)

        manager.start_transition(
            from_state=state,
            to_position=(10.0, 0.0, 0.0),
            to_rotation=(45.0, 0.0, 0.0),
            to_mode=FollowMode.CHASE,
            config=config,
            callback=on_complete,
        )

        manager.update(0.2, (0.0, 0.0, 0.0))

        assert len(callback_called) == 1


class TestConvenienceFunctions:
    """Unit tests for convenience functions."""

    def test_instant_transition(self):
        """create_instant_transition should have cut type."""
        config = create_instant_transition()

        assert config.transition_type == TransitionType.CUT
        compare_numbers(config.transition_duration, 0.0, tolerance=0.01)

    def test_smooth_transition(self):
        """create_smooth_transition should have blend type."""
        config = create_smooth_transition(0.5)

        assert config.transition_type == TransitionType.BLEND
        compare_numbers(config.transition_duration, 0.5, tolerance=0.01)

    def test_orbit_transition(self):
        """create_orbit_transition should have orbit type."""
        config = create_orbit_transition(0.75)

        assert config.transition_type == TransitionType.ORBIT
        compare_numbers(config.transition_duration, 0.75, tolerance=0.01)

    def test_dolly_transition(self):
        """create_dolly_transition should have dolly type."""
        config = create_dolly_transition(1.0)

        assert config.transition_type == TransitionType.DOLLY
        compare_numbers(config.transition_duration, 1.0, tolerance=0.01)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_transitions_imports(self):
        """All functions should be importable from transitions module."""
        from lib.cinematic.follow_cam.transitions import (
            TransitionState,
            TransitionManager,
            calculate_transition_position,
        )

        assert TransitionState is not None
        assert TransitionManager is not None
        assert callable(calculate_transition_position)

    def test_package_imports(self):
        """Functions should be importable from package."""
        from lib.cinematic.follow_cam import (
            TransitionState,
            TransitionManager,
            calculate_transition_position,
        )

        assert TransitionState is not None
        assert TransitionManager is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
