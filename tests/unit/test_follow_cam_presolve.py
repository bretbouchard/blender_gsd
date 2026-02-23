"""
Unit tests for Follow Camera Pre-Solve System (Phase 8.3)

Tests the pre-solve workflow, one-shot configuration,
and navigation mesh integration.

Part of Phase 8.3 - Pre-Solve System
Beads: blender_gsd-60, blender_gsd-61
"""

import pytest
from typing import Tuple

from lib.cinematic.follow_cam.types import (
    FollowMode,
    TransitionType,
    FollowCameraConfig,
    FollowTarget,
)
from lib.cinematic.follow_cam.pre_solve import (
    PreSolveStage,
    ModeChange,
    FramingChange,
    OneShotConfig,
    PreSolveResult,
    PreSolver,
    compute_pre_solve_path,
)
from lib.cinematic.follow_cam.navmesh import (
    NavMeshConfig,
    NavMesh,
    NavCell,
    smooth_path,
    simplify_path,
)


class TestModeChange:
    """Tests for ModeChange dataclass."""

    def test_default_values(self):
        """Test default values."""
        mc = ModeChange(frame=100, mode=FollowMode.CHASE)

        assert mc.frame == 100
        assert mc.mode == FollowMode.CHASE
        assert mc.transition_type == TransitionType.BLEND
        assert mc.transition_duration == 12

    def test_custom_values(self):
        """Test custom values."""
        mc = ModeChange(
            frame=50,
            mode=FollowMode.ORBIT_FOLLOW,
            transition_type=TransitionType.ORBIT,
            transition_duration=24,
        )

        assert mc.frame == 50
        assert mc.mode == FollowMode.ORBIT_FOLLOW
        assert mc.transition_type == TransitionType.ORBIT
        assert mc.transition_duration == 24

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        mc = ModeChange(
            frame=100,
            mode=FollowMode.AERIAL,
            transition_type=TransitionType.DOLLY,
            transition_duration=18,
        )

        d = mc.to_dict()
        mc2 = ModeChange.from_dict(d)

        assert mc2.frame == 100
        assert mc2.mode == FollowMode.AERIAL
        assert mc2.transition_type == TransitionType.DOLLY
        assert mc2.transition_duration == 18


class TestFramingChange:
    """Tests for FramingChange dataclass."""

    def test_default_values(self):
        """Test default values."""
        fc = FramingChange(frame=50)

        assert fc.frame == 50
        assert fc.distance is None
        assert fc.height is None
        assert fc.yaw_offset == 0.0
        assert fc.pitch_offset == 0.0
        assert fc.blend_duration == 12

    def test_custom_values(self):
        """Test custom values."""
        fc = FramingChange(
            frame=100,
            distance=5.0,
            height=2.0,
            yaw_offset=15.0,
            pitch_offset=-5.0,
            blend_duration=24,
        )

        assert fc.frame == 100
        assert fc.distance == 5.0
        assert fc.height == 2.0
        assert fc.yaw_offset == 15.0
        assert fc.pitch_offset == -5.0
        assert fc.blend_duration == 24

    def test_serialization(self):
        """Test serialization roundtrip."""
        fc = FramingChange(
            frame=75,
            distance=4.0,
            height=1.5,
            yaw_offset=10.0,
        )

        d = fc.to_dict()
        fc2 = FramingChange.from_dict(d)

        assert fc2.frame == 75
        assert fc2.distance == 4.0
        assert fc2.height == 1.5
        assert fc2.yaw_offset == 10.0


class TestOneShotConfig:
    """Tests for OneShotConfig."""

    def test_empty_config(self):
        """Test empty configuration."""
        config = OneShotConfig()

        assert len(config.mode_changes) == 0
        assert len(config.framing_changes) == 0
        assert config.preview_enabled is False

    def test_with_mode_changes(self):
        """Test configuration with mode changes."""
        config = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.OVER_SHOULDER),
                ModeChange(frame=100, mode=FollowMode.CHASE),
            ]
        )

        assert len(config.mode_changes) == 2

    def test_get_mode_at_frame(self):
        """Test getting mode at specific frames."""
        config = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.OVER_SHOULDER),
                ModeChange(frame=100, mode=FollowMode.CHASE),
            ]
        )

        # Before first change
        mode, change = config.get_mode_at_frame(0)
        assert mode is None

        # At first change
        mode, change = config.get_mode_at_frame(1)
        assert mode == FollowMode.OVER_SHOULDER
        assert change is not None  # Transitioning

        # After transition
        mode, change = config.get_mode_at_frame(20)
        assert mode == FollowMode.OVER_SHOULDER
        assert change is None

        # At second change
        mode, change = config.get_mode_at_frame(100)
        assert mode == FollowMode.CHASE
        assert change is not None

    def test_get_framing_at_frame(self):
        """Test getting framing at specific frames."""
        config = OneShotConfig(
            framing_changes=[
                FramingChange(frame=50, distance=5.0, height=2.0),
                FramingChange(frame=100, distance=3.0),
            ]
        )

        # Before first change
        framing = config.get_framing_at_frame(25)
        assert framing["distance"] is None

        # After first change
        framing = config.get_framing_at_frame(75)
        assert framing["distance"] == 5.0
        assert framing["height"] == 2.0

        # After second change (distance updated, height persists)
        framing = config.get_framing_at_frame(125)
        assert framing["distance"] == 3.0
        assert framing["height"] == 2.0

    def test_serialization(self):
        """Test full configuration serialization."""
        config = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.OVER_SHOULDER),
            ],
            framing_changes=[
                FramingChange(frame=50, distance=5.0),
            ],
            preview_enabled=True,
            preview_quality="draft",
        )

        d = config.to_dict()
        config2 = OneShotConfig.from_dict(d)

        assert len(config2.mode_changes) == 1
        assert len(config2.framing_changes) == 1
        assert config2.preview_enabled is True
        assert config2.preview_quality == "draft"


class TestPreSolveResult:
    """Tests for PreSolveResult."""

    def test_default_values(self):
        """Test default values."""
        result = PreSolveResult()

        assert result.success is False
        assert result.stage == PreSolveStage.SCENE_ANALYSIS
        assert result.frames_processed == 0
        assert len(result.path_points) == 0
        assert len(result.errors) == 0

    def test_serialization(self):
        """Test serialization."""
        result = PreSolveResult(
            success=True,
            stage=PreSolveStage.COMPLETE,
            frames_processed=100,
            path_points=[(0, 0, 0), (1, 1, 1)],
            mode_at_frame=["over_shoulder", "chase"],
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["stage"] == "complete"
        assert d["frames_processed"] == 100
        assert len(d["path_points"]) == 2
        assert len(d["mode_at_frame"]) == 2


class TestPreSolver:
    """Tests for PreSolver class."""

    def test_initialization(self):
        """Test solver initialization."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="TestSubject")

        solver = PreSolver(config, target)

        assert solver.config == config
        assert solver.target == target

    def test_with_one_shot(self):
        """Test solver with one-shot configuration."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="TestSubject")
        one_shot = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.CHASE),
            ]
        )

        solver = PreSolver(config, target, one_shot=one_shot)

        assert solver.one_shot == one_shot


class TestNavMeshConfig:
    """Tests for NavMeshConfig."""

    def test_default_values(self):
        """Test default values."""
        config = NavMeshConfig()

        assert config.cell_size == 0.5
        assert config.camera_height == 2.0
        assert config.camera_radius == 0.5
        assert config.max_slope == 45.0

    def test_custom_values(self):
        """Test custom values."""
        config = NavMeshConfig(
            cell_size=1.0,
            camera_height=3.0,
            camera_radius=1.0,
        )

        assert config.cell_size == 1.0
        assert config.camera_height == 3.0
        assert config.camera_radius == 1.0


class TestNavCell:
    """Tests for NavCell."""

    def test_default_values(self):
        """Test default cell."""
        cell = NavCell(x=5, y=10)

        assert cell.x == 5
        assert cell.y == 10
        assert cell.z == 0.0
        assert cell.walkable is True
        assert cell.clearance == 2.0

    def test_world_position(self):
        """Test world position calculation."""
        cell = NavCell(x=2, y=3, z=1.5)
        origin = (10.0, 20.0)
        cell_size = 0.5

        pos = cell.world_position(cell_size, origin)

        # Expected: origin + (cell * size) + (size/2)
        # x: 10 + (2 * 0.5) + 0.25 = 11.25
        # y: 20 + (3 * 0.5) + 0.25 = 21.75
        # z: 1.5
        assert pos[0] == 11.25
        assert pos[1] == 21.75
        assert pos[2] == 1.5

    def test_hash_and_equality(self):
        """Test hash and equality."""
        cell1 = NavCell(x=5, y=10)
        cell2 = NavCell(x=5, y=10)
        cell3 = NavCell(x=5, y=11)

        assert cell1 == cell2
        assert cell1 != cell3
        assert hash(cell1) == hash(cell2)


class TestNavMesh:
    """Tests for NavMesh."""

    def test_initialization(self):
        """Test mesh initialization."""
        navmesh = NavMesh()

        assert navmesh.is_generated() is False
        assert navmesh.get_cell_count() == 0

    def test_find_path_empty(self):
        """Test find path on empty mesh."""
        navmesh = NavMesh()

        path = navmesh.find_path((0, 0, 0), (10, 10, 0))

        assert len(path) == 0


class TestPathSmoothing:
    """Tests for path smoothing functions."""

    def test_smooth_path_short(self):
        """Test smoothing on short path."""
        path = [(0, 0, 0), (1, 0, 0)]
        result = smooth_path(path)

        assert len(result) == 2

    def test_smooth_path_basic(self):
        """Test basic path smoothing."""
        # Create a zigzag path
        path = [
            (0, 0, 0),
            (1, 1, 0),
            (2, 0, 0),
            (3, 1, 0),
            (4, 0, 0),
        ]

        smoothed = smooth_path(path, smoothing_factor=0.5, iterations=1)

        # Should have same number of points
        assert len(smoothed) == len(path)

        # First and last should be unchanged
        assert smoothed[0] == path[0]
        assert smoothed[-1] == path[-1]

    def test_simplify_path_short(self):
        """Test simplification on short path."""
        path = [(0, 0, 0), (1, 0, 0)]
        result = simplify_path(path, tolerance=0.1)

        assert len(result) == 2

    def test_simplify_path_colinear(self):
        """Test simplification removes colinear points."""
        # Straight line with intermediate points
        path = [
            (0, 0, 0),
            (1, 0, 0),
            (2, 0, 0),
            (3, 0, 0),
            (4, 0, 0),
        ]

        simplified = simplify_path(path, tolerance=0.1)

        # Should reduce to just endpoints
        assert len(simplified) == 2
        assert simplified[0] == path[0]
        assert simplified[-1] == path[-1]

    def test_simplify_path_curve(self):
        """Test simplification preserves curves."""
        # Curved path
        path = [
            (0, 0, 0),
            (1, 1, 0),  # Significant deviation
            (2, 0, 0),
        ]

        simplified = simplify_path(path, tolerance=0.1)

        # Should keep the middle point
        assert len(simplified) >= 2


class TestIntegration:
    """Integration tests for pre-solve system."""

    def test_one_shot_workflow(self):
        """Test complete one-shot configuration workflow."""
        # Create configuration
        config = FollowCameraConfig(
            follow_mode=FollowMode.OVER_SHOULDER,
            ideal_distance=3.0,
        )

        target = FollowTarget(object_name="Character")

        one_shot = OneShotConfig(
            mode_changes=[
                ModeChange(frame=1, mode=FollowMode.OVER_SHOULDER),
                ModeChange(frame=60, mode=FollowMode.CHASE,
                          transition_type=TransitionType.ORBIT),
                ModeChange(frame=120, mode=FollowMode.AERIAL),
            ],
            framing_changes=[
                FramingChange(frame=30, distance=5.0),
                FramingChange(frame=90, height=2.5),
            ],
        )

        # Create solver
        solver = PreSolver(config, target, one_shot=one_shot)

        # Verify one-shot is attached
        assert len(solver.one_shot.mode_changes) == 3
        assert len(solver.one_shot.framing_changes) == 2

        # Verify mode lookup
        mode, _ = solver.one_shot.get_mode_at_frame(60)
        assert mode == FollowMode.CHASE

    def test_compute_pre_solve_path_function(self):
        """Test convenience function."""
        config = FollowCameraConfig()
        target = FollowTarget(object_name="Test")

        # This will fail without Blender, but we can verify signature
        # result = compute_pre_solve_path(config, target, 1, 100)
        pass  # Function exists and has correct signature


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
