"""
Follow Camera Collision Unit Tests

Tests for: lib/cinematic/follow_cam/collision.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-57, 58

Note: Many tests require Blender which is not available in test environment.
Tests focus on data structures and logic that can run outside Blender.
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.types import (
    ObstacleInfo,
    ObstacleResponse,
    FollowCameraConfig,
)

from lib.cinematic.follow_cam.collision import (
    detect_obstacles,
    calculate_avoidance_position,
    check_frustum_obstruction,
    get_clearance_distance,
    _obstacle_already_detected,
    _get_primary_obstacle,
    _response_push_forward,
    _response_orbit_away,
    _response_raise_up,
    _response_back_away,
)


class TestObstacleInfo:
    """Unit tests for ObstacleInfo dataclass."""

    def test_default_values(self):
        """Default ObstacleInfo should have push_forward response."""
        info = ObstacleInfo()

        assert info.object_name == ""
        assert info.response == ObstacleResponse.PUSH_FORWARD
        assert info.is_transparent is False
        assert info.is_trigger is False

    def test_response_types(self):
        """ObstacleInfo should support all response types."""
        responses = [
            ObstacleResponse.PUSH_FORWARD,
            ObstacleResponse.ORBIT_AWAY,
            ObstacleResponse.RAISE_UP,
            ObstacleResponse.ZOOM_THROUGH,
            ObstacleResponse.BACK_AWAY,
        ]

        for response in responses:
            info = ObstacleInfo(response=response)
            assert info.response == response


class TestDetectObstacles:
    """Unit tests for detect_obstacles function."""

    def test_collision_disabled(self):
        """Should return empty list when collision is disabled."""
        config = FollowCameraConfig(collision_enabled=False)

        obstacles = detect_obstacles(
            camera_position=(0.0, 0.0, 0.0),
            target_position=(10.0, 0.0, 0.0),
            config=config,
        )

        assert obstacles == []

    def test_collision_enabled_no_blender(self):
        """Should return empty list when Blender not available."""
        config = FollowCameraConfig(collision_enabled=True)

        # This will return empty because Blender is not available
        obstacles = detect_obstacles(
            camera_position=(0.0, 0.0, 0.0),
            target_position=(10.0, 0.0, 0.0),
            config=config,
        )

        # Without Blender, raycasts can't be performed
        assert obstacles == []


class TestObstacleAlreadyDetected:
    """Unit tests for _obstacle_already_detected helper."""

    def test_no_obstacles(self):
        """Empty list should not detect."""
        new_obstacle = ObstacleInfo(object_name="Wall", position=(1.0, 0.0, 0.0))

        result = _obstacle_already_detected([], new_obstacle)

        assert result is False

    def test_different_objects(self):
        """Different object names should not match."""
        existing = [ObstacleInfo(object_name="Floor", position=(0.0, 0.0, 0.0))]
        new_obstacle = ObstacleInfo(object_name="Wall", position=(1.0, 0.0, 0.0))

        result = _obstacle_already_detected(existing, new_obstacle)

        assert result is False

    def test_same_object_same_position(self):
        """Same object at same position should match."""
        existing = [ObstacleInfo(object_name="Wall", position=(1.0, 0.0, 0.0))]
        new_obstacle = ObstacleInfo(object_name="Wall", position=(1.0, 0.0, 0.0))

        result = _obstacle_already_detected(existing, new_obstacle)

        assert result is True

    def test_same_object_nearby_position(self):
        """Same object at nearby position should match."""
        existing = [ObstacleInfo(object_name="Wall", position=(1.0, 0.0, 0.0))]
        new_obstacle = ObstacleInfo(object_name="Wall", position=(1.2, 0.0, 0.0))

        result = _obstacle_already_detected(existing, new_obstacle)

        assert result is True

    def test_same_object_distant_position(self):
        """Same object at distant position should not match."""
        existing = [ObstacleInfo(object_name="Wall", position=(0.0, 0.0, 0.0))]
        new_obstacle = ObstacleInfo(object_name="Wall", position=(10.0, 0.0, 0.0))

        result = _obstacle_already_detected(existing, new_obstacle)

        assert result is False


class TestGetPrimaryObstacle:
    """Unit tests for _get_primary_obstacle helper."""

    def test_empty_list(self):
        """Empty list should return None."""
        result = _get_primary_obstacle([])

        assert result is None

    def test_solid_obstacle(self):
        """Solid obstacle should be returned."""
        obstacles = [
            ObstacleInfo(object_name="Wall", is_transparent=False, is_trigger=False),
        ]

        result = _get_primary_obstacle(obstacles)

        assert result is not None
        assert result.object_name == "Wall"

    def test_transparent_ignored(self):
        """Transparent obstacles should be ignored."""
        obstacles = [
            ObstacleInfo(object_name="Glass", is_transparent=True, is_trigger=False),
        ]

        result = _get_primary_obstacle(obstacles)

        assert result is None

    def test_trigger_ignored(self):
        """Trigger obstacles should be ignored."""
        obstacles = [
            ObstacleInfo(object_name="Trigger", is_transparent=False, is_trigger=True),
        ]

        result = _get_primary_obstacle(obstacles)

        assert result is None

    def test_first_solid_returned(self):
        """First solid obstacle should be returned."""
        obstacles = [
            ObstacleInfo(object_name="Glass", is_transparent=True),
            ObstacleInfo(object_name="Wall", is_transparent=False),
            ObstacleInfo(object_name="Pillar", is_transparent=False),
        ]

        result = _get_primary_obstacle(obstacles)

        assert result is not None
        assert result.object_name == "Wall"


class TestResponsePushForward:
    """Unit tests for push_forward response."""

    def test_push_forward_response(self):
        """Push forward should move camera closer to target."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((0.0, 0.0, 0.0))
        target_pos = Vector((10.0, 0.0, 0.0))
        obstacle = ObstacleInfo(
            object_name="Wall",
            position=(5.0, 0.0, 0.0),
            distance=5.0,
            response=ObstacleResponse.PUSH_FORWARD,
        )
        config = FollowCameraConfig(min_distance=1.0, min_obstacle_distance=0.5)

        new_pos, description = _response_push_forward(
            cam_pos, target_pos, obstacle, config
        )

        # Camera should be moved forward (closer to target)
        assert description == "push_forward"
        assert new_pos[0] > 0  # Moved forward

    def test_push_respects_min_distance(self):
        """Push forward should not go below min_distance."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((0.0, 0.0, 0.0))
        target_pos = Vector((2.0, 0.0, 0.0))  # Close target
        obstacle = ObstacleInfo(
            object_name="Wall",
            position=(1.0, 0.0, 0.0),
            distance=1.0,
            response=ObstacleResponse.PUSH_FORWARD,
        )
        config = FollowCameraConfig(min_distance=1.0, min_obstacle_distance=0.5)

        new_pos, _ = _response_push_forward(cam_pos, target_pos, obstacle, config)

        # Should not go below min_distance
        new_distance = math.sqrt(
            (new_pos[0] - target_pos.x) ** 2 +
            (new_pos[1] - target_pos.y) ** 2 +
            (new_pos[2] - target_pos.z) ** 2
        )
        assert new_distance >= config.min_distance


class TestResponseOrbitAway:
    """Unit tests for orbit_away response."""

    def test_orbit_changes_angle(self):
        """Orbit should change camera angle around target."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((5.0, 0.0, 1.0))
        target_pos = Vector((0.0, 0.0, 0.0))
        obstacle = ObstacleInfo(
            object_name="Wall",
            position=(2.5, 0.0, 0.5),
            distance=2.5,
            normal=(1.0, 0.0, 0.0),
            response=ObstacleResponse.ORBIT_AWAY,
        )
        config = FollowCameraConfig()

        new_pos, description = _response_orbit_away(cam_pos, target_pos, obstacle, config)

        # Camera should have moved to a different angle
        assert description == "orbit_away"
        # Position should be different
        assert new_pos[0] != cam_pos.x or new_pos[1] != cam_pos.y


class TestResponseRaiseUp:
    """Unit tests for raise_up response."""

    def test_raise_increases_height(self):
        """Raise up should increase camera Z position."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((5.0, 0.0, 1.0))
        target_pos = Vector((0.0, 0.0, 0.0))
        obstacle = ObstacleInfo(
            object_name="LowCeiling",
            position=(2.5, 0.0, 1.5),
            distance=2.5,
            response=ObstacleResponse.RAISE_UP,
        )
        config = FollowCameraConfig(
            min_obstacle_distance=0.5,
            max_height=10.0,
        )

        new_pos, description = _response_raise_up(cam_pos, target_pos, obstacle, config)

        # Camera should be raised
        assert description == "raise_up"
        assert new_pos[2] > cam_pos.z

    def test_raise_respects_max_height(self):
        """Raise up should not exceed max_height."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((5.0, 0.0, 9.0))  # Already near max
        target_pos = Vector((0.0, 0.0, 0.0))
        obstacle = ObstacleInfo(
            object_name="LowCeiling",
            position=(2.5, 0.0, 9.5),
            distance=2.5,
            response=ObstacleResponse.RAISE_UP,
        )
        config = FollowCameraConfig(
            min_obstacle_distance=0.5,
            max_height=10.0,
        )

        new_pos, _ = _response_raise_up(cam_pos, target_pos, obstacle, config)

        # Should not exceed max_height
        assert new_pos[2] <= target_pos.z + config.max_height


class TestResponseBackAway:
    """Unit tests for back_away response."""

    def test_back_away_moves_forward(self):
        """Back away should move camera forward (away from wall behind)."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        cam_pos = Vector((5.0, 0.0, 1.0))
        target_pos = Vector((0.0, 0.0, 0.0))
        obstacle = ObstacleInfo(
            object_name="BackWall",
            position=(6.0, 0.0, 1.0),  # Behind camera
            distance=1.0,  # Close
            response=ObstacleResponse.BACK_AWAY,
        )
        config = FollowCameraConfig(min_obstacle_distance=0.5)

        new_pos, description = _response_back_away(cam_pos, target_pos, obstacle, config)

        # Camera should move forward (closer to target)
        assert description == "back_away"
        assert new_pos[0] < cam_pos.x  # Moved toward target


class TestCalculateAvoidancePosition:
    """Unit tests for calculate_avoidance_position function."""

    def test_no_obstacles(self):
        """No obstacles should return original position."""
        pos, description = calculate_avoidance_position(
            camera_position=(5.0, 0.0, 1.0),
            target_position=(0.0, 0.0, 0.0),
            obstacles=[],
            config=FollowCameraConfig(),
        )

        compare_vectors(pos, (5.0, 0.0, 1.0), tolerance=0.01)
        assert description == "no_obstacles"

    def test_transparent_obstacle(self):
        """Transparent obstacles should be passed through."""
        obstacles = [
            ObstacleInfo(
                object_name="Glass",
                is_transparent=True,
                response=ObstacleResponse.ZOOM_THROUGH,
            ),
        ]

        pos, description = calculate_avoidance_position(
            camera_position=(5.0, 0.0, 1.0),
            target_position=(0.0, 0.0, 0.0),
            obstacles=obstacles,
            config=FollowCameraConfig(),
        )

        # When all obstacles are transparent, returns transparent_only
        assert description == "transparent_only"

    def test_solid_obstacle_response(self):
        """Solid obstacles should trigger avoidance response."""
        from lib.cinematic.follow_cam.follow_modes import Vector

        obstacles = [
            ObstacleInfo(
                object_name="Wall",
                position=(2.5, 0.0, 0.5),
                distance=2.5,
                normal=(1.0, 0.0, 0.0),
                response=ObstacleResponse.PUSH_FORWARD,
                is_transparent=False,
            ),
        ]
        config = FollowCameraConfig(
            min_distance=1.0,
            min_obstacle_distance=0.5,
        )

        pos, description = calculate_avoidance_position(
            camera_position=(5.0, 0.0, 1.0),
            target_position=(0.0, 0.0, 0.0),
            obstacles=obstacles,
            config=config,
        )

        # Should have responded
        assert description == "push_forward"


class TestCheckFrustumObstruction:
    """Unit tests for check_frustum_obstruction function."""

    def test_no_blender(self):
        """Should return empty list without Blender."""
        obstacles = check_frustum_obstruction(
            camera_position=(0.0, 0.0, 0.0),
            camera_rotation=(0.0, 0.0, 0.0),
            target_position=(10.0, 0.0, 0.0),
            fov=50.0,
        )

        # Without Blender, can't perform raycasts
        assert obstacles == []


class TestGetClearanceDistance:
    """Unit tests for get_clearance_distance function."""

    def test_no_blender(self):
        """Should return max distance without Blender."""
        config = FollowCameraConfig()

        distance = get_clearance_distance(
            position=(0.0, 0.0, 0.0),
            direction=(1.0, 0.0, 0.0),
            config=config,
        )

        # Without Blender, returns max distance
        assert distance == 1000.0


class TestModuleImports:
    """Tests for module-level imports."""

    def test_collision_imports(self):
        """All functions should be importable from collision module."""
        from lib.cinematic.follow_cam.collision import (
            detect_obstacles,
            calculate_avoidance_position,
            check_frustum_obstruction,
            get_clearance_distance,
        )

        assert callable(detect_obstacles)
        assert callable(calculate_avoidance_position)
        assert callable(check_frustum_obstruction)
        assert callable(get_clearance_distance)

    def test_package_imports(self):
        """Functions should be importable from package."""
        from lib.cinematic.follow_cam import (
            detect_obstacles,
            calculate_avoidance_position,
            check_frustum_obstruction,
            get_clearance_distance,
        )

        assert callable(detect_obstacles)
        assert callable(calculate_avoidance_position)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
