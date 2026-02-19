"""
Follow Camera Modes Unit Tests

Tests for: lib/cinematic/follow_cam/follow_modes.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-52, 53, 54, 55
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.types import (
    FollowMode,
    LockedPlane,
    FollowCameraConfig,
)

from lib.cinematic.follow_cam.follow_modes import (
    calculate_ideal_position,
    smooth_position,
    smooth_angle,
    calculate_camera_rotation,
    get_target_forward_direction,
    _calc_side_scroller,
    _calc_over_shoulder,
    _calc_chase,
    _calc_chase_side,
    _calc_orbit_follow,
    _calc_lead,
    _calc_aerial,
    _calc_free_roam,
)


# Use the fallback Vector class for testing
Vector = None


def get_vector_class():
    """Get Vector class for testing."""
    global Vector
    if Vector is None:
        # Import from follow_modes which has the fallback
        from lib.cinematic.follow_cam.follow_modes import Vector as FallbackVector
        Vector = FallbackVector
    return Vector


class TestCalculateIdealPosition:
    """Unit tests for calculate_ideal_position dispatcher."""

    def test_over_shoulder_mode(self):
        """Over-shoulder mode should be dispatched correctly."""
        config = FollowCameraConfig(follow_mode=FollowMode.OVER_SHOULDER)
        pos, yaw, pitch = calculate_ideal_position(
            target_position=(0.0, 0.0, 0.0),
            target_forward=(0.0, 1.0, 0.0),
            target_velocity=(0.0, 0.0, 0.0),
            config=config,
        )

        # Camera should be behind and above target
        assert pos.z > 0  # Above target

    def test_chase_mode(self):
        """Chase mode should be dispatched correctly."""
        config = FollowCameraConfig(follow_mode=FollowMode.CHASE)
        pos, yaw, pitch = calculate_ideal_position(
            target_position=(0.0, 0.0, 0.0),
            target_forward=(0.0, 1.0, 0.0),
            target_velocity=(0.0, 5.0, 0.0),  # Moving forward
            config=config,
        )

        # Camera should be behind target
        assert pos.y < 0  # Behind target

    def test_aerial_mode(self):
        """Aerial mode should be dispatched correctly."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.AERIAL,
            ideal_height=10.0,
        )
        pos, yaw, pitch = calculate_ideal_position(
            target_position=(0.0, 0.0, 0.0),
            target_forward=(0.0, 1.0, 0.0),
            target_velocity=(0.0, 0.0, 0.0),
            config=config,
        )

        # Camera should be directly above
        compare_numbers(pos.x, 0.0, tolerance=0.1)
        compare_numbers(pos.y, 0.0, tolerance=0.1)
        compare_numbers(pos.z, 10.0, tolerance=0.1)
        # Pitch should be looking down
        assert pitch < -80


class TestSideScrollerMode:
    """Unit tests for side-scroller mode (blender_gsd-52)."""

    def test_xz_locked_plane(self):
        """XZ locked plane (Y locked) should constrain camera."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.SIDE_SCROLLER,
            locked_plane=LockedPlane.XZ,
            locked_axis_value=10.0,
            ideal_height=2.0,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))

        pos, yaw, pitch = _calc_side_scroller(target_pos, config, 1/60)

        # Y should be locked
        compare_numbers(pos.y, 10.0, tolerance=0.01)
        # Camera should be above target
        assert pos.z >= 2.0

    def test_xy_locked_plane(self):
        """XY locked plane (Z locked) should constrain camera."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.SIDE_SCROLLER,
            locked_plane=LockedPlane.XY,
            locked_axis_value=15.0,
        )

        Vec = get_vector_class()
        target_pos = Vec((5.0, 5.0, 0.0))

        pos, yaw, pitch = _calc_side_scroller(target_pos, config, 1/60)

        # Z should be locked
        compare_numbers(pos.z, 15.0, tolerance=0.01)
        # X and Y should follow target
        compare_numbers(pos.x, 5.0, tolerance=0.01)
        compare_numbers(pos.y, 5.0, tolerance=0.01)
        # Should look straight down
        assert pitch < -80

    def test_yz_locked_plane(self):
        """YZ locked plane (X locked) should constrain camera."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.SIDE_SCROLLER,
            locked_plane=LockedPlane.YZ,
            locked_axis_value=-5.0,
            ideal_height=1.5,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 10.0, 0.0))

        pos, yaw, pitch = _calc_side_scroller(target_pos, config, 1/60)

        # X should be locked
        compare_numbers(pos.x, -5.0, tolerance=0.01)
        # Y should follow target
        compare_numbers(pos.y, 10.0, tolerance=0.01)

    def test_follows_target_horizontally(self):
        """Camera should follow target on unlocked axes."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.SIDE_SCROLLER,
            locked_plane=LockedPlane.XZ,
            locked_axis_value=5.0,
            ideal_height=1.5,
        )

        Vec = get_vector_class()
        target_pos = Vec((10.0, 0.0, 3.0))

        pos, yaw, pitch = _calc_side_scroller(target_pos, config, 1/60)

        # X should follow target
        compare_numbers(pos.x, 10.0, tolerance=0.01)
        # Z should be target.z + ideal_height (camera is above target)
        compare_numbers(pos.z, 4.5, tolerance=0.01)  # 3.0 + 1.5
        # Y should remain locked
        compare_numbers(pos.y, 5.0, tolerance=0.01)


class TestOverShoulderMode:
    """Unit tests for over-shoulder mode (blender_gsd-53)."""

    def test_behind_target(self):
        """Camera should be positioned behind target."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.OVER_SHOULDER,
            ideal_distance=3.0,
            ideal_height=1.5,
            shoulder_offset=0.0,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))  # Facing +Y

        pos, yaw, pitch = _calc_over_shoulder(target_pos, target_fwd, config, 0.0, 1/60)

        # Camera should be behind target (negative Y)
        assert pos.y < 0
        # Camera should be above target
        assert pos.z > 0

    def test_shoulder_offset_left(self):
        """Positive shoulder offset should position to left (in camera view)."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.OVER_SHOULDER,
            ideal_distance=3.0,
            ideal_height=1.5,
            shoulder_offset=0.5,  # Left shoulder (positive in our convention)
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))

        pos, yaw, pitch = _calc_over_shoulder(target_pos, target_fwd, config, 0.0, 1/60)

        # With up.cross(forward) = (-1, 0, 0), positive offset gives -X
        assert pos.x < 0

    def test_shoulder_offset_right(self):
        """Negative shoulder offset should position to right (in camera view)."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.OVER_SHOULDER,
            ideal_distance=3.0,
            ideal_height=1.5,
            shoulder_offset=-0.5,  # Right shoulder (negative in our convention)
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))

        pos, yaw, pitch = _calc_over_shoulder(target_pos, target_fwd, config, 0.0, 1/60)

        # With up.cross(forward) = (-1, 0, 0), negative offset gives +X
        assert pos.x > 0

    def test_respects_ideal_distance(self):
        """Camera should maintain ideal distance."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.OVER_SHOULDER,
            ideal_distance=5.0,
            ideal_height=0.0,
            shoulder_offset=0.0,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))

        pos, yaw, pitch = _calc_over_shoulder(target_pos, target_fwd, config, 0.0, 1/60)

        # Distance should be approximately ideal_distance
        distance = (pos - target_pos).length()
        compare_numbers(distance, 5.0, tolerance=0.5)


class TestChaseModes:
    """Unit tests for chase modes (blender_gsd-54)."""

    def test_chase_behind_target(self):
        """Chase camera should be behind target."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.CHASE,
            ideal_distance=4.0,
            ideal_height=1.5,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))
        target_vel = Vec((0.0, 0.0, 0.0))  # Stationary

        pos, yaw, pitch = _calc_chase(target_pos, target_fwd, target_vel, config, 0.0, 1/60)

        # Camera should be behind target
        assert pos.y < 0
        assert pos.z > 0

    def test_chase_speed_distance(self):
        """Chase camera should increase distance with speed."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.CHASE,
            ideal_distance=4.0,
            speed_distance_factor=0.5,
            max_speed_distance=3.0,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))

        # Stationary
        pos_slow, _, _ = _calc_chase(
            target_pos, target_fwd, Vec((0.0, 0.0, 0.0)), config, 0.0, 1/60
        )

        # Fast moving
        pos_fast, _, _ = _calc_chase(
            target_pos, target_fwd, Vec((0.0, 10.0, 0.0)), config, 0.0, 1/60
        )

        # Fast camera should be further back
        assert pos_fast.y < pos_slow.y

    def test_chase_side_position(self):
        """Chase-side camera should be to the side."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.CHASE_SIDE,
            ideal_distance=4.0,
            shoulder_offset=3.0,  # Side distance
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))
        target_vel = Vec((0.0, 5.0, 0.0))

        pos, yaw, pitch = _calc_chase_side(target_pos, target_fwd, target_vel, config, 0.0, 1/60)

        # Camera should be to the side
        assert abs(pos.x) > 1.0
        # Camera should be above target
        assert pos.z > 0


class TestAdvancedModes:
    """Unit tests for advanced modes (blender_gsd-55)."""

    def test_orbit_follow_rotates(self):
        """Orbit-follow should rotate around target."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.ORBIT_FOLLOW,
            ideal_distance=3.0,
            ideal_height=1.5,
            orbit_speed=30.0,  # Degrees per second
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))

        # Starting position (yaw = 0)
        pos1, yaw1, _ = _calc_orbit_follow(target_pos, config, 0.0, 1/60)

        # After 1 second (yaw should have increased)
        pos2, yaw2, _ = _calc_orbit_follow(target_pos, config, 0.0, 1.0)

        # Yaw should have changed
        assert abs(yaw2 - yaw1) > 20  # At least 20 degrees difference

    def test_lead_ahead_of_target(self):
        """Lead camera should be ahead of target."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.LEAD,
            ideal_distance=3.0,
            lead_distance=2.0,
            ideal_height=1.5,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))
        target_fwd = Vec((0.0, 1.0, 0.0))  # Facing +Y

        pos, yaw, pitch = _calc_lead(target_pos, target_fwd, config, 0.0, 1/60)

        # Camera should be ahead (in front) of target
        assert pos.y > 0
        # Camera should be above
        assert pos.z > 0

    def test_aerial_above_target(self):
        """Aerial camera should be directly above target."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.AERIAL,
            ideal_distance=10.0,
            ideal_height=8.0,
        )

        Vec = get_vector_class()
        target_pos = Vec((5.0, 3.0, 0.0))

        pos, yaw, pitch = _calc_aerial(target_pos, config, 1/60)

        # Camera should be directly above
        compare_numbers(pos.x, 5.0, tolerance=0.1)
        compare_numbers(pos.y, 3.0, tolerance=0.1)
        compare_numbers(pos.z, 8.0, tolerance=0.1)
        # Should look nearly straight down
        assert pitch < -80

    def test_free_roam_uses_yaw(self):
        """Free roam should use current yaw for position."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.FREE_ROAM,
            ideal_distance=3.0,
            ideal_height=1.5,
        )

        Vec = get_vector_class()
        target_pos = Vec((0.0, 0.0, 0.0))

        # Different yaw values should give different positions
        pos1, _, _ = _calc_free_roam(target_pos, config, 0.0, 1/60)
        pos2, _, _ = _calc_free_roam(target_pos, config, 90.0, 1/60)

        # Positions should be different
        assert abs(pos1.x - pos2.x) > 0.1 or abs(pos1.y - pos2.y) > 0.1


class TestSmoothingUtilities:
    """Unit tests for smoothing utility functions."""

    def test_smooth_position_instant(self):
        """Zero smoothing should give instant transition."""
        Vec = get_vector_class()
        current = Vec((0.0, 0.0, 0.0))
        target = Vec((10.0, 0.0, 0.0))

        result = smooth_position(current, target, smoothing=0.0, delta_time=1/60)

        # Should be at target
        compare_numbers(result.x, 10.0, tolerance=0.01)

    def test_smooth_position_gradual(self):
        """Non-zero smoothing should be gradual."""
        Vec = get_vector_class()
        current = Vec((0.0, 0.0, 0.0))
        target = Vec((10.0, 0.0, 0.0))

        result = smooth_position(current, target, smoothing=0.5, delta_time=1/60)

        # Should be between current and target
        assert 0 < result.x < 10

    def test_smooth_angle_instant(self):
        """Zero smoothing should give instant angle change."""
        result = smooth_angle(current=0.0, target=90.0, smoothing=0.0, delta_time=1/60)

        compare_numbers(result, 90.0, tolerance=0.01)

    def test_smooth_angle_wrapping(self):
        """Angle smoothing should handle wrapping."""
        # Going from 350 to 10 degrees (20 degree difference, not 340)
        result = smooth_angle(current=350.0, target=10.0, smoothing=0.1, delta_time=1/60)

        # Should move towards 10 (which is 370 in wrapped terms)
        assert 350 < result or result < 30

    def test_smooth_angle_gradual(self):
        """Non-zero smoothing should be gradual."""
        result = smooth_angle(current=0.0, target=90.0, smoothing=0.5, delta_time=1/60)

        # Should be between current and target
        assert 0 < result < 90


class TestCameraRotation:
    """Unit tests for camera rotation calculation."""

    def test_look_forward(self):
        """Camera behind target should look forward."""
        Vec = get_vector_class()
        cam_pos = Vec((0.0, -5.0, 1.0))
        target_pos = Vec((0.0, 0.0, 0.0))

        yaw, pitch, roll = calculate_camera_rotation(cam_pos, target_pos)

        # Yaw should be roughly facing +Y direction
        compare_numbers(yaw, 0.0, tolerance=5.0)
        # Roll should be zero
        compare_numbers(roll, 0.0, tolerance=0.01)

    def test_look_down(self):
        """Camera above target should look down."""
        Vec = get_vector_class()
        cam_pos = Vec((0.0, 0.0, 10.0))
        target_pos = Vec((0.0, 0.0, 0.0))

        yaw, pitch, roll = calculate_camera_rotation(cam_pos, target_pos)

        # Pitch should be negative (looking down)
        assert pitch < -80


class TestTargetForwardDirection:
    """Unit tests for target forward direction calculation."""

    def test_stationary_uses_default(self):
        """Stationary target should use default forward."""
        Vec = get_vector_class()
        velocity = Vec((0.0, 0.0, 0.0))

        forward = get_target_forward_direction(velocity, default_forward=(0.0, 1.0, 0.0))

        compare_numbers(forward.x, 0.0, tolerance=0.01)
        compare_numbers(forward.y, 1.0, tolerance=0.01)

    def test_moving_uses_velocity(self):
        """Moving target should use velocity direction."""
        Vec = get_vector_class()
        velocity = Vec((5.0, 0.0, 0.0))  # Moving along X

        forward = get_target_forward_direction(velocity, default_forward=(0.0, 1.0, 0.0))

        compare_numbers(forward.x, 1.0, tolerance=0.01)
        compare_numbers(forward.y, 0.0, tolerance=0.01)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_follow_modes_imports(self):
        """All functions should be importable from follow_modes module."""
        from lib.cinematic.follow_cam.follow_modes import (
            calculate_ideal_position,
            smooth_position,
            smooth_angle,
            calculate_camera_rotation,
            get_target_forward_direction,
        )

        assert callable(calculate_ideal_position)
        assert callable(smooth_position)
        assert callable(smooth_angle)
        assert callable(calculate_camera_rotation)
        assert callable(get_target_forward_direction)

    def test_package_imports(self):
        """Functions should be importable from package."""
        from lib.cinematic.follow_cam import (
            calculate_ideal_position,
            smooth_position,
            smooth_angle,
            calculate_camera_rotation,
            get_target_forward_direction,
        )

        assert callable(calculate_ideal_position)
        assert callable(smooth_position)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
