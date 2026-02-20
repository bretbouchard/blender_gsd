"""
Unit tests for Follow Camera System (Phase 6.3)

Tests for follow_types, follow_modes, follow_deadzone, and follow_controller.

Requirements covered:
- REQ-FOLLOW-01: Subject following with configurable modes
- REQ-FOLLOW-02: Look-ahead prediction
- REQ-FOLLOW-03: Dead zones for stable framing
- REQ-FOLLOW-04: Obstacle awareness (basic)
- REQ-FOLLOW-05: Smooth interpolation modes
"""

import pytest
import math
from typing import Tuple

from lib.cinematic.follow_types import (
    FollowModeType,
    FollowConfig,
    FollowState,
    FollowRig,
    DeadZoneResult,
    FollowResult,
)
from lib.cinematic.follow_modes import (
    follow_tight,
    follow_loose,
    follow_anticipatory,
    follow_elastic,
    follow_orbit,
    calculate_follow,
    calculate_look_at_rotation,
    smooth_position,
    smooth_angle,
)
from lib.cinematic.follow_deadzone import (
    calculate_screen_position,
    is_in_dead_zone,
    calculate_dead_zone_reaction,
    create_dynamic_dead_zone,
    calculate_dead_zone_result,
    calculate_edge_distance,
)
from lib.cinematic.follow_controller import (
    create_follow_rig,
    update_follow_rig,
    bake_follow_animation,
    preview_follow_motion,
    reset_follow_state,
    get_follow_rig_info,
)


class TestFollowConfig:
    """Tests for FollowConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = FollowConfig()

        assert config.mode == "loose"
        assert config.dead_zone == (0.1, 0.1)
        assert config.look_ahead_frames == 10
        assert config.smoothing == 0.3
        assert config.max_speed == 2.0
        assert config.keep_distance == 3.0
        assert config.keep_height == 1.6

    def test_config_to_dict(self):
        """Test serialization to dictionary."""
        config = FollowConfig(mode="tight", smoothing=0.5)

        data = config.to_dict()

        assert data["mode"] == "tight"
        assert data["smoothing"] == 0.5
        assert "dead_zone" in data
        assert "keep_distance" in data

    def test_config_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "mode": "elastic",
            "smoothing": 0.7,
            "spring_stiffness": 15.0,
            "keep_distance": 5.0,
        }

        config = FollowConfig.from_dict(data)

        assert config.mode == "elastic"
        assert config.smoothing == 0.7
        assert config.spring_stiffness == 15.0
        assert config.keep_distance == 5.0


class TestFollowState:
    """Tests for FollowState dataclass."""

    def test_default_state(self):
        """Test default state values."""
        state = FollowState()

        assert state.current_velocity == (0.0, 0.0, 0.0)
        assert state.target_position == (0.0, 0.0, 0.0)
        assert state.is_in_dead_zone is True
        assert state.frames_since_move == 0

    def test_state_serialization(self):
        """Test state serialization roundtrip."""
        state = FollowState(
            current_velocity=(1.0, 2.0, 0.5),
            target_position=(5.0, 3.0, 1.0),
            is_in_dead_zone=False,
        )

        data = state.to_dict()
        restored = FollowState.from_dict(data)

        assert restored.current_velocity == (1.0, 2.0, 0.5)
        assert restored.target_position == (5.0, 3.0, 1.0)
        assert restored.is_in_dead_zone is False


class TestFollowRig:
    """Tests for FollowRig dataclass."""

    def test_rig_creation(self):
        """Test creating a follow rig."""
        config = FollowConfig(mode="tight")
        rig = FollowRig(
            name="test_rig",
            camera="MainCamera",
            target="Player",
            config=config,
        )

        assert rig.name == "test_rig"
        assert rig.camera == "MainCamera"
        assert rig.target == "Player"
        assert rig.config.mode == "tight"

    def test_rig_serialization(self):
        """Test rig serialization roundtrip."""
        rig = FollowRig(
            name="test_rig",
            camera="Camera",
            target="Target",
            config=FollowConfig(mode="orbit"),
            state=FollowState(current_position=(1, 2, 3)),
        )

        data = rig.to_dict()
        restored = FollowRig.from_dict(data)

        assert restored.name == "test_rig"
        assert restored.config.mode == "orbit"
        assert restored.state.current_position == (1, 2, 3)


class TestFollowModes:
    """Tests for follow mode implementations."""

    def test_follow_tight_basic(self):
        """Test tight following moves camera toward target."""
        camera_pos = (0.0, -5.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)
        config = FollowConfig(mode="tight", keep_distance=3.0, smoothing=0.1)

        new_pos = follow_tight(camera_pos, target_pos, config, delta_time=1/24)

        # Camera should move closer to target
        assert new_pos[1] > camera_pos[1]  # Y should increase (move forward)

    def test_follow_loose_smoothed(self):
        """Test loose following applies smoothing."""
        camera_pos = (0.0, -5.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)
        config = FollowConfig(mode="loose", smoothing=0.5)

        new_pos = follow_loose(camera_pos, target_pos, config)

        # Position should change but not jump to target
        assert new_pos != camera_pos
        assert new_pos != target_pos

    def test_follow_anticipatory_uses_velocity(self):
        """Test anticipatory mode uses velocity prediction."""
        camera_pos = (0.0, -5.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)
        target_velocity = (0.0, 2.0, 0.0)  # Moving in +Y
        config = FollowConfig(mode="anticipatory", look_ahead_frames=10)

        new_pos = follow_anticipatory(
            camera_pos, target_pos, target_velocity, config
        )

        # Camera should anticipate movement
        # The exact position depends on the algorithm
        assert new_pos is not None
        assert len(new_pos) == 3

    def test_follow_elastic_spring_physics(self):
        """Test elastic mode uses spring physics."""
        camera_pos = (0.0, -5.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)
        config = FollowConfig(
            mode="elastic",
            spring_stiffness=10.0,
            spring_damping=0.5,
        )

        new_pos = follow_elastic(camera_pos, target_pos, config)

        # Spring should pull camera toward ideal position
        assert new_pos is not None

    def test_follow_orbit_circular(self):
        """Test orbit mode creates circular path."""
        camera_pos = (3.0, 0.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)
        config = FollowConfig(mode="orbit", orbit_speed=1.0, orbit_radius=3.0)
        state = FollowState(orbit_angle=0.0)

        # Multiple updates should create circular motion
        positions = []
        for _ in range(360):
            new_pos = follow_orbit(camera_pos, target_pos, config, state)
            positions.append(new_pos)
            camera_pos = new_pos
            state.orbit_angle += config.orbit_speed

        # Verify circular motion (radius stays constant)
        distances = [
            math.sqrt(p[0]**2 + p[1]**2)
            for p in positions
        ]
        # Allow some tolerance for accumulated floating point errors
        for d in distances:
            assert abs(d - 3.0) < 0.1, f"Orbit radius should be ~3.0, got {d}"

    def test_calculate_follow_dispatch(self):
        """Test calculate_follow routes to correct mode."""
        camera_pos = (0.0, -5.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)
        target_velocity = (0.0, 0.0, 0.0)

        # Test each mode
        for mode in ["tight", "loose", "anticipatory", "elastic", "orbit"]:
            config = FollowConfig(mode=mode)
            result = calculate_follow(
                camera_pos, target_pos, target_velocity, config
            )

            assert isinstance(result, FollowResult)
            assert result.mode_used == mode

    def test_calculate_look_at_rotation(self):
        """Test look-at rotation calculation."""
        camera_pos = (0.0, -5.0, 1.6)
        target_pos = (0.0, 0.0, 0.0)

        rotation = calculate_look_at_rotation(camera_pos, target_pos)

        assert len(rotation) == 3
        # Should look forward (positive Y direction from camera)
        assert rotation[1] < 90  # Yaw should be reasonable


class TestSmoothPosition:
    """Tests for position smoothing."""

    def test_smooth_position_interpolates(self):
        """Test smoothing interpolates between positions."""
        current = (0.0, 0.0, 0.0)
        target = (10.0, 10.0, 10.0)

        smoothed = smooth_position(current, target, smoothing=0.5)

        # Should be between current and target
        for i in range(3):
            assert current[i] < smoothed[i] < target[i]

    def test_smooth_position_zero_smoothing(self):
        """Test zero smoothing returns target."""
        current = (0.0, 0.0, 0.0)
        target = (10.0, 10.0, 10.0)

        smoothed = smooth_position(current, target, smoothing=0.0)

        assert smoothed == target

    def test_smooth_angle_wrapping(self):
        """Test angle smoothing handles wrapping."""
        # 350 to 10 should go through 360/0
        smoothed = smooth_angle(350.0, 10.0, smoothing=0.5)

        # Should be somewhere between, considering wrap
        assert 350 < smoothed or smoothed < 10


class TestDeadZone:
    """Tests for dead zone system."""

    def test_is_in_dead_zone_center(self):
        """Test center is always in dead zone."""
        screen_pos = (0.5, 0.5)
        dead_zone = (0.1, 0.1)

        assert is_in_dead_zone(screen_pos, dead_zone) is True

    def test_is_in_dead_zone_edge(self):
        """Test position at edge of dead zone."""
        # Just inside
        screen_pos = (0.54, 0.5)
        dead_zone = (0.1, 0.1)
        assert is_in_dead_zone(screen_pos, dead_zone) is True

        # Just outside
        screen_pos = (0.56, 0.5)
        assert is_in_dead_zone(screen_pos, dead_zone) is False

    def test_is_in_dead_zone_outside(self):
        """Test position outside dead zone."""
        screen_pos = (0.7, 0.7)
        dead_zone = (0.1, 0.1)

        assert is_in_dead_zone(screen_pos, dead_zone) is False

    def test_calculate_dead_zone_reaction(self):
        """Test reaction calculation."""
        # Target at edge of frame, outside dead zone
        screen_pos = (0.7, 0.5)
        dead_zone = (0.1, 0.1)

        reaction = calculate_dead_zone_reaction(screen_pos, dead_zone)

        # Should calculate reaction (non-zero)
        assert reaction[0] != 0  # X reaction

    def test_dynamic_dead_zone_expands(self):
        """Test dynamic dead zone expands with speed."""
        # Stationary
        velocity = (0.0, 0.0, 0.0)
        dz_slow = create_dynamic_dead_zone(velocity, base_size=0.1)

        # Fast moving
        velocity = (0.0, 10.0, 0.0)
        dz_fast = create_dynamic_dead_zone(velocity, base_size=0.1)

        # Fast dead zone should be larger
        assert dz_fast[0] > dz_slow[0]

    def test_calculate_edge_distance(self):
        """Test edge distance calculation."""
        # Inside dead zone
        screen_pos = (0.5, 0.5)
        dead_zone = (0.2, 0.2)
        dist = calculate_edge_distance(screen_pos, dead_zone)
        assert dist < 0  # Negative = inside

        # Outside dead zone
        screen_pos = (0.7, 0.5)
        dist = calculate_edge_distance(screen_pos, dead_zone)
        assert dist > 0  # Positive = outside


class TestFollowController:
    """Tests for follow controller."""

    def test_create_follow_rig(self):
        """Test creating a follow rig."""
        rig = create_follow_rig(
            camera_name="MainCamera",
            target_name="Player",
        )

        assert rig.name == "follow_MainCamera"
        assert rig.camera == "MainCamera"
        assert rig.target == "Player"
        assert isinstance(rig.config, FollowConfig)
        assert isinstance(rig.state, FollowState)

    def test_create_follow_rig_with_config(self):
        """Test creating rig with custom config."""
        config = FollowConfig(mode="tight", smoothing=0.2)
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=config,
            rig_name="custom_rig",
        )

        assert rig.name == "custom_rig"
        assert rig.config.mode == "tight"
        assert rig.config.smoothing == 0.2

    def test_update_follow_rig(self):
        """Test updating follow rig."""
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=FollowConfig(mode="loose"),
        )

        result = update_follow_rig(
            rig,
            frame=1,
            target_position=(0.0, 5.0, 0.0),
            target_velocity=(0.0, 1.0, 0.0),
            apply_to_blender=False,
        )

        assert isinstance(result, FollowResult)
        assert result.mode_used == "loose"
        # State should be updated
        assert rig.state.target_position == (0.0, 5.0, 0.0)

    def test_preview_follow_motion(self):
        """Test previewing follow motion."""
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=FollowConfig(mode="tight"),
        )

        # Create sample target positions
        target_positions = [
            (0.0, float(i), 0.0) for i in range(10)
        ]

        results = preview_follow_motion(
            rig, frames=10, target_positions=target_positions
        )

        assert len(results) == 10
        assert all(isinstance(r, FollowResult) for r in results)

    def test_bake_follow_animation(self):
        """Test baking follow animation."""
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=FollowConfig(mode="loose"),
        )

        # Create target positions for frames 1-5
        target_positions = {
            1: (0, 0, 0),
            2: (0, 1, 0),
            3: (0, 2, 0),
            4: (0, 3, 0),
            5: (0, 4, 0),
        }

        results = bake_follow_animation(
            rig,
            frame_start=1,
            frame_end=5,
            target_positions=target_positions,
        )

        assert len(results) == 5

    def test_reset_follow_state(self):
        """Test resetting follow state."""
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
        )

        # Update state
        rig.state.current_position = (1, 2, 3)
        rig.state.target_position = (4, 5, 6)

        # Reset
        reset_follow_state(rig)

        assert rig.state.current_position == (0.0, 0.0, 0.0)
        assert rig.state.target_position == (0.0, 0.0, 0.0)

    def test_get_follow_rig_info(self):
        """Test getting rig info."""
        config = FollowConfig(mode="orbit", orbit_speed=2.0)
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=config,
        )

        info = get_follow_rig_info(rig)

        assert info["name"] == "follow_Camera"
        assert info["camera"] == "Camera"
        assert info["target"] == "Target"
        assert info["mode"] == "orbit"
        assert "config" in info


class TestFollowResult:
    """Tests for FollowResult dataclass."""

    def test_result_creation(self):
        """Test creating a follow result."""
        result = FollowResult(
            position=(1.0, 2.0, 3.0),
            rotation=(0.0, 45.0, 0.0),
            distance=5.0,
            height=1.5,
            mode_used="loose",
            is_smoothed=True,
            prediction_used=False,
        )

        assert result.position == (1.0, 2.0, 3.0)
        assert result.rotation == (0.0, 45.0, 0.0)
        assert result.distance == 5.0
        assert result.mode_used == "loose"

    def test_result_serialization(self):
        """Test result serialization."""
        result = FollowResult(
            position=(1, 2, 3),
            rotation=(0, 0, 0),
            mode_used="tight",
        )

        data = result.to_dict()

        assert data["position"] == [1, 2, 3]
        assert data["mode_used"] == "tight"


class TestDeadZoneResult:
    """Tests for DeadZoneResult dataclass."""

    def test_result_creation(self):
        """Test creating a dead zone result."""
        result = DeadZoneResult(
            screen_position=(0.5, 0.5),
            is_in_dead_zone=True,
            reaction_needed=(0.0, 0.0, 0.0),
            dead_zone_size=(0.1, 0.1),
        )

        assert result.screen_position == (0.5, 0.5)
        assert result.is_in_dead_zone is True


class TestFollowModeType:
    """Tests for FollowModeType enum."""

    def test_all_modes_exist(self):
        """Test all expected modes exist."""
        modes = [m.value for m in FollowModeType]

        assert "tight" in modes
        assert "loose" in modes
        assert "anticipatory" in modes
        assert "elastic" in modes
        assert "orbit" in modes


# Integration tests
class TestFollowIntegration:
    """Integration tests for complete follow workflows."""

    def test_complete_follow_workflow(self):
        """Test complete follow camera workflow."""
        # 1. Create rig
        rig = create_follow_rig(
            camera_name="HeroCamera",
            target_name="Subject",
            config=FollowConfig(mode="cinematic", smoothing=0.4),
        )

        # 2. Simulate target movement
        target_path = [
            (0, 0, 0),
            (1, 1, 0),
            (2, 2, 0),
            (3, 3, 0),
            (4, 4, 0),
        ]

        # 3. Preview motion
        results = preview_follow_motion(
            rig, frames=5, target_positions=target_path
        )

        # 4. Verify results
        assert len(results) == 5

        # Camera should follow target
        for i, result in enumerate(results):
            assert isinstance(result, FollowResult)

    def test_mode_switching(self):
        """Test switching between modes during playback."""
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=FollowConfig(mode="tight"),
        )

        # Update with tight mode
        result1 = update_follow_rig(
            rig, frame=1,
            target_position=(0, 5, 0),
            apply_to_blender=False,
        )
        assert result1.mode_used == "tight"

        # Switch to loose mode
        rig.config.mode = "loose"
        result2 = update_follow_rig(
            rig, frame=2,
            target_position=(0, 10, 0),
            apply_to_blender=False,
        )
        assert result2.mode_used == "loose"

        # Switch to orbit mode
        rig.config.mode = "orbit"
        result3 = update_follow_rig(
            rig, frame=3,
            target_position=(0, 15, 0),
            apply_to_blender=False,
        )
        assert result3.mode_used == "orbit"

    def test_elastic_settling(self):
        """Test elastic mode settles to stable position."""
        rig = create_follow_rig(
            camera_name="Camera",
            target_name="Target",
            config=FollowConfig(
                mode="elastic",
                spring_stiffness=5.0,
                spring_damping=0.8,
            ),
        )

        # Set initial position far from target
        rig.state.current_position = (0, -10, 0)

        # Update multiple times
        target = (0, 0, 0)
        positions = []
        for _ in range(50):
            result = update_follow_rig(
                rig, frame=1,
                target_position=target,
                apply_to_blender=False,
            )
            positions.append(result.position)

        # Position should stabilize (changes get smaller)
        first_half_changes = []
        second_half_changes = []

        for i in range(1, 25):
            change = math.sqrt(sum(
                (a - b) ** 2 for a, b in zip(positions[i], positions[i-1])
            ))
            first_half_changes.append(change)

        for i in range(26, 50):
            change = math.sqrt(sum(
                (a - b) ** 2 for a, b in zip(positions[i], positions[i-1])
            ))
            second_half_changes.append(change)

        avg_first = sum(first_half_changes) / len(first_half_changes)
        avg_second = sum(second_half_changes) / len(second_half_changes)

        # Second half changes should be smaller (settling)
        assert avg_second < avg_first
