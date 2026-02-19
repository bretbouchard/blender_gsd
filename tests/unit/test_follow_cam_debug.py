"""
Follow Camera Debug Visualization Unit Tests

Tests for: lib/cinematic/follow_cam/debug.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-63
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.debug import (
    DebugConfig,
    DebugVisualizer,
    generate_hud_text,
    get_debug_stats,
)
from lib.cinematic.follow_cam.types import (
    FollowCameraConfig,
    CameraState,
    FollowMode,
    ObstacleInfo,
    ObstacleResponse,
)


class TestDebugConfig:
    """Unit tests for DebugConfig dataclass."""

    def test_default_values(self):
        """Default DebugConfig should have all visualizations enabled."""
        config = DebugConfig()

        assert config.show_frustum is True
        assert config.show_target is True
        assert config.show_prediction is True
        assert config.show_obstacles is True
        assert config.show_path is True
        assert config.show_hud is True

    def test_default_colors(self):
        """Default colors should be RGBA tuples."""
        config = DebugConfig()

        assert len(config.frustum_color) == 4
        assert len(config.target_color) == 4
        assert len(config.prediction_color) == 4
        assert len(config.obstacle_color) == 4
        assert len(config.path_ideal_color) == 4
        assert len(config.path_actual_color) == 4

    def test_custom_values(self):
        """DebugConfig should store all config values."""
        config = DebugConfig(
            show_frustum=False,
            show_target=True,
            show_prediction=False,
            show_obstacles=True,
            show_path=False,
            show_hud=True,
            frustum_color=(1.0, 0.0, 0.0, 0.5),
            target_color=(0.0, 1.0, 0.0, 1.0),
            line_width=3.0,
        )

        assert config.show_frustum is False
        assert config.show_target is True
        compare_numbers(config.line_width, 3.0)

    def test_color_values_in_range(self):
        """All color values should be between 0 and 1."""
        config = DebugConfig()

        for color_name in [
            "frustum_color",
            "target_color",
            "prediction_color",
            "obstacle_color",
            "path_ideal_color",
            "path_actual_color",
        ]:
            color = getattr(config, color_name)
            for value in color:
                assert 0.0 <= value <= 1.0, f"{color_name} value out of range"


class TestDebugVisualizer:
    """Unit tests for DebugVisualizer class."""

    def test_initialization(self):
        """DebugVisualizer should initialize with config."""
        config = DebugConfig()
        visualizer = DebugVisualizer(config)

        assert visualizer.config == config

    def test_default_config(self):
        """DebugVisualizer should create default config if not provided."""
        visualizer = DebugVisualizer()

        assert visualizer.config is not None

    def test_update_stores_state(self):
        """Update should store current state."""
        visualizer = DebugVisualizer()

        camera_state = CameraState(
            position=(5.0, 5.0, 2.0),
            current_mode=FollowMode.CHASE,
        )

        visualizer.update(
            camera_state=camera_state,
            target_position=(0.0, 0.0, 0.0),
        )

        assert visualizer._current_state == camera_state
        compare_vectors(visualizer._target_position, (0.0, 0.0, 0.0))

    def test_update_with_prediction(self):
        """Update should store predicted position."""
        visualizer = DebugVisualizer()

        visualizer.update(
            camera_state=CameraState(),
            target_position=(0.0, 0.0, 0.0),
            predicted_position=(1.0, 1.0, 0.5),
        )

        compare_vectors(visualizer._predicted_position, (1.0, 1.0, 0.5))

    def test_update_with_obstacles(self):
        """Update should store obstacles."""
        visualizer = DebugVisualizer()

        obstacles = [
            ObstacleInfo(object_name="Wall1", distance=2.0),
            ObstacleInfo(object_name="Wall2", distance=3.0),
        ]

        visualizer.update(
            camera_state=CameraState(),
            target_position=(0.0, 0.0, 0.0),
            obstacles=obstacles,
        )

        assert len(visualizer._obstacles) == 2

    def test_update_path_history(self):
        """Update should add to path history."""
        visualizer = DebugVisualizer()

        visualizer.update(
            camera_state=CameraState(position=(0.0, 0.0, 0.0)),
            target_position=(0.0, 0.0, 0.0),
        )

        visualizer.update(
            camera_state=CameraState(position=(1.0, 0.0, 0.0)),
            target_position=(0.0, 0.0, 0.0),
        )

        assert len(visualizer._path_history) == 2

    def test_path_history_trimming(self):
        """Path history should be trimmed to max length."""
        visualizer = DebugVisualizer()

        # Add more than max_path_length positions
        for i in range(350):
            visualizer.update(
                camera_state=CameraState(position=(float(i), 0.0, 0.0)),
                target_position=(0.0, 0.0, 0.0),
            )

        assert len(visualizer._path_history) <= 300

    def test_cleanup_clears_state(self):
        """Cleanup should clear all state."""
        visualizer = DebugVisualizer()

        visualizer.update(
            camera_state=CameraState(position=(5.0, 5.0, 2.0)),
            target_position=(0.0, 0.0, 0.0),
        )

        visualizer.cleanup()

        assert len(visualizer._path_history) == 0
        assert len(visualizer._ideal_path_history) == 0
        assert len(visualizer._debug_objects) == 0

    def test_draw_without_blender(self):
        """Draw should not crash without Blender."""
        visualizer = DebugVisualizer()

        visualizer.update(
            camera_state=CameraState(),
            target_position=(0.0, 0.0, 0.0),
        )

        # Should not crash
        visualizer.draw()

    def test_ideal_path_history(self):
        """Update should track ideal path when provided."""
        visualizer = DebugVisualizer()

        visualizer.update(
            camera_state=CameraState(position=(0.0, 0.0, 0.0)),
            target_position=(0.0, 0.0, 0.0),
            ideal_position=(0.0, 3.0, 1.5),
        )

        visualizer.update(
            camera_state=CameraState(position=(1.0, 0.0, 0.0)),
            target_position=(1.0, 0.0, 0.0),
            ideal_position=(1.0, 3.0, 1.5),
        )

        assert len(visualizer._ideal_path_history) == 2


class TestGenerateHudText:
    """Unit tests for generate_hud_text function."""

    def test_basic_hud(self):
        """HUD should show basic camera info."""
        state = CameraState(
            position=(5.0, 3.0, 2.0),
            current_mode=FollowMode.CHASE,
            distance=4.0,
            height=2.0,
        )
        config = FollowCameraConfig()

        hud = generate_hud_text(state, config)

        assert "Follow Camera Debug" in hud
        assert "chase" in hud
        assert "5.0" in hud  # Position X

    def test_hud_with_transition(self):
        """HUD should show transition progress."""
        state = CameraState(
            is_transitioning=True,
            transition_progress=0.5,
        )
        config = FollowCameraConfig()

        hud = generate_hud_text(state, config)

        assert "Transition" in hud
        assert "50%" in hud

    def test_hud_with_obstacles(self):
        """HUD should show obstacle count."""
        obstacles = [
            ObstacleInfo(object_name="Wall1"),
            ObstacleInfo(object_name="Wall2"),
        ]
        state = CameraState(obstacles=obstacles)
        config = FollowCameraConfig()

        hud = generate_hud_text(state, config)

        assert "Obstacles" in hud
        assert "2" in hud

    def test_hud_with_fps(self):
        """HUD should show FPS."""
        state = CameraState()
        config = FollowCameraConfig()

        hud = generate_hud_text(state, config, fps=60.0)

        assert "60" in hud

    def test_hud_velocity(self):
        """HUD should show target velocity."""
        state = CameraState(
            target_velocity=(1.0, 0.5, 0.0),
        )
        config = FollowCameraConfig()

        hud = generate_hud_text(state, config)

        assert "Velocity" in hud


class TestGetDebugStats:
    """Unit tests for get_debug_stats function."""

    def test_basic_stats(self):
        """Stats should include basic camera info."""
        state = CameraState(
            position=(5.0, 3.0, 2.0),
            rotation=(0.0, 45.0, 0.0),
            current_mode=FollowMode.CHASE,
        )
        config = FollowCameraConfig()

        stats = get_debug_stats(state, config)

        assert stats["mode"] == "chase"
        assert stats["position"] == (5.0, 3.0, 2.0)
        assert stats["rotation"] == (0.0, 45.0, 0.0)

    def test_stats_with_obstacles(self):
        """Stats should include obstacle count."""
        obstacles = [
            ObstacleInfo(object_name="Wall1"),
        ]
        state = CameraState(obstacles=obstacles)
        config = FollowCameraConfig()

        stats = get_debug_stats(state, config)

        assert stats["obstacle_count"] == 1

    def test_stats_with_transition(self):
        """Stats should include transition info."""
        state = CameraState(
            is_transitioning=True,
            transition_progress=0.75,
        )
        config = FollowCameraConfig()

        stats = get_debug_stats(state, config)

        assert stats["is_transitioning"] is True
        compare_numbers(stats["transition_progress"], 0.75)

    def test_stats_config_flags(self):
        """Stats should include config flags."""
        state = CameraState()
        config = FollowCameraConfig(
            collision_enabled=True,
            prediction_enabled=False,
        )

        stats = get_debug_stats(state, config)

        assert stats["collision_enabled"] is True
        assert stats["prediction_enabled"] is False

    def test_stats_yaw_pitch(self):
        """Stats should include yaw and pitch."""
        state = CameraState(
            yaw=90.0,
            pitch=-15.0,
        )
        config = FollowCameraConfig()

        stats = get_debug_stats(state, config)

        compare_numbers(stats["yaw"], 90.0)
        compare_numbers(stats["pitch"], -15.0)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_debug_module_imports(self):
        """All debug types should be importable."""
        from lib.cinematic.follow_cam.debug import (
            DebugConfig,
            DebugVisualizer,
            generate_hud_text,
            get_debug_stats,
        )

        assert DebugConfig is not None
        assert DebugVisualizer is not None

    def test_package_imports_debug(self):
        """Debug APIs should be importable from package."""
        from lib.cinematic.follow_cam import (
            DebugConfig,
            DebugVisualizer,
            generate_hud_text,
            get_debug_stats,
        )

        assert DebugConfig is not None
        assert DebugVisualizer is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
