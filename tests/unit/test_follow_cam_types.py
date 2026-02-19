"""
Follow Camera Types Unit Tests

Tests for: lib/cinematic/follow_cam/types.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-51
"""

import pytest
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.types import (
    FollowMode,
    LockedPlane,
    ObstacleResponse,
    TransitionType,
    FollowTarget,
    ObstacleInfo,
    FollowCameraConfig,
    CameraState,
)


class TestFollowMode:
    """Unit tests for FollowMode enum."""

    def test_all_modes_exist(self):
        """All 8 expected follow modes should be defined."""
        expected_modes = [
            "SIDE_SCROLLER",
            "OVER_SHOULDER",
            "CHASE",
            "CHASE_SIDE",
            "ORBIT_FOLLOW",
            "LEAD",
            "AERIAL",
            "FREE_ROAM",
        ]
        for mode in expected_modes:
            assert hasattr(FollowMode, mode), f"Missing FollowMode.{mode}"

    def test_mode_values(self):
        """Follow mode values should be lowercase strings."""
        assert FollowMode.SIDE_SCROLLER.value == "side_scroller"
        assert FollowMode.OVER_SHOULDER.value == "over_shoulder"
        assert FollowMode.CHASE.value == "chase"
        assert FollowMode.CHASE_SIDE.value == "chase_side"
        assert FollowMode.ORBIT_FOLLOW.value == "orbit_follow"
        assert FollowMode.LEAD.value == "lead"
        assert FollowMode.AERIAL.value == "aerial"
        assert FollowMode.FREE_ROAM.value == "free_roam"

    def test_mode_count(self):
        """Should have exactly 8 follow modes."""
        assert len(FollowMode) == 8


class TestLockedPlane:
    """Unit tests for LockedPlane enum."""

    def test_all_planes_exist(self):
        """All 3 locked planes should be defined."""
        expected_planes = ["XY", "XZ", "YZ"]
        for plane in expected_planes:
            assert hasattr(LockedPlane, plane), f"Missing LockedPlane.{plane}"

    def test_plane_values(self):
        """Locked plane values should be lowercase strings."""
        assert LockedPlane.XY.value == "xy"
        assert LockedPlane.XZ.value == "xz"
        assert LockedPlane.YZ.value == "yz"


class TestObstacleResponse:
    """Unit tests for ObstacleResponse enum."""

    def test_all_responses_exist(self):
        """All 5 obstacle responses should be defined."""
        expected_responses = [
            "PUSH_FORWARD",
            "ORBIT_AWAY",
            "RAISE_UP",
            "ZOOM_THROUGH",
            "BACK_AWAY",
        ]
        for response in expected_responses:
            assert hasattr(ObstacleResponse, response), f"Missing ObstacleResponse.{response}"

    def test_response_values(self):
        """Obstacle response values should be lowercase strings."""
        assert ObstacleResponse.PUSH_FORWARD.value == "push_forward"
        assert ObstacleResponse.ORBIT_AWAY.value == "orbit_away"
        assert ObstacleResponse.RAISE_UP.value == "raise_up"
        assert ObstacleResponse.ZOOM_THROUGH.value == "zoom_through"
        assert ObstacleResponse.BACK_AWAY.value == "back_away"


class TestTransitionType:
    """Unit tests for TransitionType enum."""

    def test_all_types_exist(self):
        """All 4 transition types should be defined."""
        expected_types = ["CUT", "BLEND", "ORBIT", "DOLLY"]
        for t_type in expected_types:
            assert hasattr(TransitionType, t_type), f"Missing TransitionType.{t_type}"

    def test_type_values(self):
        """Transition type values should be lowercase strings."""
        assert TransitionType.CUT.value == "cut"
        assert TransitionType.BLEND.value == "blend"
        assert TransitionType.ORBIT.value == "orbit"
        assert TransitionType.DOLLY.value == "dolly"


class TestFollowTarget:
    """Unit tests for FollowTarget dataclass."""

    def test_default_values(self):
        """Default FollowTarget should have empty object name."""
        target = FollowTarget()

        assert target.object_name == ""
        assert target.bone_name == ""
        compare_vectors(target.offset, (0.0, 0.0, 0.0))
        compare_numbers(target.look_ahead_distance, 1.0)
        compare_numbers(target.velocity_smoothing, 0.5)
        assert target.prediction_frames == 10
        assert target.use_animation_prediction is False

    def test_custom_values(self):
        """FollowTarget should store all custom values."""
        target = FollowTarget(
            object_name="Player",
            bone_name="Head",
            offset=(0.0, 0.0, 1.5),
            look_ahead_distance=2.0,
            velocity_smoothing=0.8,
            prediction_frames=20,
            use_animation_prediction=True,
        )

        assert target.object_name == "Player"
        assert target.bone_name == "Head"
        compare_vectors(target.offset, (0.0, 0.0, 1.5))
        compare_numbers(target.look_ahead_distance, 2.0)
        compare_numbers(target.velocity_smoothing, 0.8)
        assert target.prediction_frames == 20
        assert target.use_animation_prediction is True

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        target = FollowTarget(
            object_name="Character",
            offset=(1.0, 2.0, 3.0),
            prediction_frames=15,
        )

        data = target.to_dict()

        assert data["object_name"] == "Character"
        assert data["offset"] == [1.0, 2.0, 3.0]
        assert data["prediction_frames"] == 15

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "object_name": "Enemy",
            "bone_name": "Spine",
            "offset": [0.5, 0.0, 1.0],
            "look_ahead_distance": 1.5,
            "velocity_smoothing": 0.7,
            "prediction_frames": 25,
            "use_animation_prediction": True,
        }

        target = FollowTarget.from_dict(data)

        assert target.object_name == "Enemy"
        assert target.bone_name == "Spine"
        compare_vectors(target.offset, (0.5, 0.0, 1.0))
        compare_numbers(target.look_ahead_distance, 1.5)

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = FollowTarget(
            object_name="TestObject",
            bone_name="TestBone",
            offset=(2.5, -1.0, 0.5),
            look_ahead_distance=3.0,
            velocity_smoothing=0.9,
            prediction_frames=30,
            use_animation_prediction=True,
        )

        restored = FollowTarget.from_dict(original.to_dict())

        assert restored.object_name == original.object_name
        assert restored.bone_name == original.bone_name
        compare_vectors(restored.offset, original.offset)
        compare_numbers(restored.look_ahead_distance, original.look_ahead_distance)


class TestObstacleInfo:
    """Unit tests for ObstacleInfo dataclass."""

    def test_default_values(self):
        """Default ObstacleInfo should have empty object name."""
        info = ObstacleInfo()

        assert info.object_name == ""
        compare_vectors(info.position, (0.0, 0.0, 0.0))
        compare_vectors(info.normal, (0.0, 0.0, 1.0))
        compare_numbers(info.distance, 0.0)
        assert info.is_transparent is False
        assert info.is_trigger is False
        assert info.response == ObstacleResponse.PUSH_FORWARD

    def test_custom_values(self):
        """ObstacleInfo should store all obstacle data."""
        info = ObstacleInfo(
            object_name="Wall",
            position=(5.0, 0.0, 1.0),
            normal=(1.0, 0.0, 0.0),
            distance=2.5,
            is_transparent=False,
            is_trigger=False,
            response=ObstacleResponse.ORBIT_AWAY,
        )

        assert info.object_name == "Wall"
        compare_vectors(info.position, (5.0, 0.0, 1.0))
        compare_vectors(info.normal, (1.0, 0.0, 0.0))
        compare_numbers(info.distance, 2.5)
        assert info.response == ObstacleResponse.ORBIT_AWAY

    def test_transparent_obstacle(self):
        """Transparent obstacles should be marked."""
        info = ObstacleInfo(
            object_name="Glass",
            is_transparent=True,
            response=ObstacleResponse.ZOOM_THROUGH,
        )

        assert info.is_transparent is True
        assert info.response == ObstacleResponse.ZOOM_THROUGH

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        info = ObstacleInfo(
            object_name="Pillar",
            position=(1.0, 2.0, 0.0),
            normal=(0.0, 1.0, 0.0),
            distance=3.0,
            response=ObstacleResponse.RAISE_UP,
        )

        data = info.to_dict()

        assert data["object_name"] == "Pillar"
        assert data["position"] == [1.0, 2.0, 0.0]
        assert data["normal"] == [0.0, 1.0, 0.0]
        assert data["response"] == "raise_up"

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "object_name": "Door",
            "position": [2.0, 3.0, 0.5],
            "normal": [0.0, 0.0, 1.0],
            "distance": 1.5,
            "is_transparent": True,
            "is_trigger": False,
            "response": "back_away",
        }

        info = ObstacleInfo.from_dict(data)

        assert info.object_name == "Door"
        compare_vectors(info.position, (2.0, 3.0, 0.5))
        assert info.is_transparent is True
        assert info.response == ObstacleResponse.BACK_AWAY


class TestFollowCameraConfig:
    """Unit tests for FollowCameraConfig dataclass."""

    def test_default_values(self):
        """Default config should have over_shoulder mode."""
        config = FollowCameraConfig()

        assert config.name == "default_follow"
        assert config.follow_mode == FollowMode.OVER_SHOULDER
        compare_numbers(config.ideal_distance, 3.0)
        compare_numbers(config.ideal_height, 1.5)
        assert config.collision_enabled is True
        assert config.prediction_enabled is True

    def test_distance_clamp_values(self):
        """Distance min/max should define valid range."""
        config = FollowCameraConfig(
            min_distance=1.0,
            max_distance=10.0,
            ideal_distance=3.0,
        )

        assert config.min_distance <= config.ideal_distance
        assert config.ideal_distance <= config.max_distance

    def test_mode_specific_settings(self):
        """Side-scroller mode should have locked plane."""
        config = FollowCameraConfig(
            follow_mode=FollowMode.SIDE_SCROLLER,
            locked_plane=LockedPlane.XZ,
            locked_axis_value=5.0,
        )

        assert config.follow_mode == FollowMode.SIDE_SCROLLER
        assert config.locked_plane == LockedPlane.XZ
        compare_numbers(config.locked_axis_value, 5.0)

    def test_collision_settings(self):
        """Collision settings should be configurable."""
        config = FollowCameraConfig(
            collision_enabled=True,
            collision_radius=0.5,
            collision_layers=["Default", "Walls"],
            ignore_objects=["Trigger"],
        )

        assert config.collision_enabled is True
        compare_numbers(config.collision_radius, 0.5)
        assert "Default" in config.collision_layers
        assert "Trigger" in config.ignore_objects

    def test_transition_settings(self):
        """Transition settings should be configurable."""
        config = FollowCameraConfig(
            transition_type=TransitionType.DOLLY,
            transition_duration=1.0,
        )

        assert config.transition_type == TransitionType.DOLLY
        compare_numbers(config.transition_duration, 1.0)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        config = FollowCameraConfig(
            name="test_config",
            follow_mode=FollowMode.CHASE,
            ideal_distance=5.0,
            speed_distance_factor=0.4,
        )

        data = config.to_dict()

        assert data["name"] == "test_config"
        assert data["follow_mode"] == "chase"
        assert data["ideal_distance"] == 5.0
        assert data["speed_distance_factor"] == 0.4

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "name": "custom_config",
            "follow_mode": "aerial",
            "ideal_distance": 8.0,
            "ideal_height": 6.0,
            "min_height": 3.0,
            "max_height": 10.0,
            "collision_enabled": False,
            "prediction_enabled": True,
        }

        config = FollowCameraConfig.from_dict(data)

        assert config.name == "custom_config"
        assert config.follow_mode == FollowMode.AERIAL
        compare_numbers(config.ideal_distance, 8.0)
        compare_numbers(config.ideal_height, 6.0)
        assert config.collision_enabled is False

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = FollowCameraConfig(
            name="round_trip_test",
            follow_mode=FollowMode.ORBIT_FOLLOW,
            ideal_distance=4.0,
            ideal_height=2.0,
            orbit_speed=25.0,
            collision_radius=0.25,
            shoulder_offset=-0.5,
            dead_zone_radius=0.15,
        )

        restored = FollowCameraConfig.from_dict(original.to_dict())

        assert restored.name == original.name
        assert restored.follow_mode == original.follow_mode
        compare_numbers(restored.ideal_distance, original.ideal_distance)
        compare_numbers(restored.orbit_speed, original.orbit_speed)
        compare_numbers(restored.shoulder_offset, original.shoulder_offset)

    def test_nested_target_serialization(self):
        """Config should properly serialize nested FollowTarget."""
        config = FollowCameraConfig(
            target=FollowTarget(
                object_name="Player",
                offset=(0.0, 0.0, 1.5),
            )
        )

        data = config.to_dict()
        assert data["target"]["object_name"] == "Player"
        assert data["target"]["offset"] == [0.0, 0.0, 1.5]

        restored = FollowCameraConfig.from_dict(data)
        assert restored.target.object_name == "Player"
        compare_vectors(restored.target.offset, (0.0, 0.0, 1.5))


class TestCameraState:
    """Unit tests for CameraState dataclass."""

    def test_default_values(self):
        """Default state should have zero position and rotation."""
        state = CameraState()

        compare_vectors(state.position, (0.0, 0.0, 0.0))
        compare_vectors(state.rotation, (0.0, 0.0, 0.0))
        compare_numbers(state.distance, 3.0)
        compare_numbers(state.height, 1.5)
        assert state.current_mode == FollowMode.OVER_SHOULDER
        assert state.is_transitioning is False

    def test_position_and_rotation(self):
        """State should store camera position and rotation."""
        state = CameraState(
            position=(10.0, 5.0, 2.0),
            rotation=(0.0, 45.0, 0.0),
        )

        compare_vectors(state.position, (10.0, 5.0, 2.0))
        compare_vectors(state.rotation, (0.0, 45.0, 0.0))

    def test_velocity_tracking(self):
        """State should track camera velocity."""
        state = CameraState(
            velocity=(1.0, 0.5, 0.0),
            target_velocity=(0.5, 0.25, 0.0),
        )

        compare_vectors(state.velocity, (1.0, 0.5, 0.0))
        compare_vectors(state.target_velocity, (0.5, 0.25, 0.0))

    def test_obstacle_list(self):
        """State should store detected obstacles."""
        obstacles = [
            ObstacleInfo(object_name="Wall1", distance=2.0),
            ObstacleInfo(object_name="Wall2", distance=3.0),
        ]
        state = CameraState(obstacles=obstacles)

        assert len(state.obstacles) == 2
        assert state.obstacles[0].object_name == "Wall1"
        assert state.obstacles[1].object_name == "Wall2"

    def test_transition_state(self):
        """State should track transition progress."""
        state = CameraState(
            is_transitioning=True,
            transition_progress=0.5,
        )

        assert state.is_transitioning is True
        compare_numbers(state.transition_progress, 0.5)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        state = CameraState(
            position=(5.0, 5.0, 2.0),
            distance=4.0,
            current_mode=FollowMode.CHASE,
            is_transitioning=True,
        )

        data = state.to_dict()

        assert data["position"] == [5.0, 5.0, 2.0]
        assert data["distance"] == 4.0
        assert data["current_mode"] == "chase"
        assert data["is_transitioning"] is True

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "position": [8.0, 3.0, 1.5],
            "rotation": [0.0, 30.0, 0.0],
            "distance": 5.0,
            "height": 2.0,
            "yaw": 45.0,
            "pitch": -15.0,
            "velocity": [0.5, 0.0, 0.0],
            "target_position": [7.0, 3.0, 0.0],
            "current_mode": "aerial",
            "obstacles": [],
            "is_transitioning": False,
        }

        state = CameraState.from_dict(data)

        compare_vectors(state.position, (8.0, 3.0, 1.5))
        compare_vectors(state.rotation, (0.0, 30.0, 0.0))
        compare_numbers(state.distance, 5.0)
        assert state.current_mode == FollowMode.AERIAL

    def test_serialization_round_trip(self):
        """Round-trip serialization should preserve values."""
        original = CameraState(
            position=(12.0, -5.0, 3.0),
            rotation=(0.0, 60.0, 0.0),
            distance=6.0,
            height=2.5,
            yaw=90.0,
            pitch=-20.0,
            current_mode=FollowMode.ORBIT_FOLLOW,
            is_transitioning=True,
            transition_progress=0.75,
        )

        restored = CameraState.from_dict(original.to_dict())

        compare_vectors(restored.position, original.position)
        compare_vectors(restored.rotation, original.rotation)
        compare_numbers(restored.distance, original.distance)
        compare_numbers(restored.yaw, original.yaw)
        assert restored.current_mode == original.current_mode
        assert restored.is_transitioning == original.is_transitioning


class TestModuleImports:
    """Tests for module-level imports."""

    def test_types_module_imports(self):
        """All types should be importable from types module."""
        from lib.cinematic.follow_cam.types import (
            FollowMode,
            LockedPlane,
            ObstacleResponse,
            TransitionType,
            FollowTarget,
            ObstacleInfo,
            FollowCameraConfig,
            CameraState,
        )

        assert FollowMode is not None
        assert LockedPlane is not None
        assert ObstacleResponse is not None
        assert TransitionType is not None

    def test_package_imports(self):
        """All public APIs should be importable from package."""
        from lib.cinematic.follow_cam import (
            FollowMode,
            LockedPlane,
            ObstacleResponse,
            TransitionType,
            FollowTarget,
            ObstacleInfo,
            FollowCameraConfig,
            CameraState,
        )

        assert FollowMode is not None
        assert FollowTarget is not None
        assert FollowCameraConfig is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
