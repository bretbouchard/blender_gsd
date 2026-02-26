"""
Unit tests for tentacle animation module.

Tests for shape keys, state machine, and animation components.
"""

import pytest
import numpy as np
from typing import Dict, List

from lib.tentacle.animation import (
    # Enums
    ShapeKeyPreset,
    AnimationState,
    # Config dataclasses
    ShapeKeyConfig,
    StateTransition,
    AnimationStateConfig,
    SplineIKRig,
    RigConfig,
    # Result dataclasses
    ShapeKeyResult,
    RigResult,
    # Shape key generation
    ShapeKeyGenerator,
    get_preset_config,
    SHAPE_KEY_PRESETS,
    # State machine
    TentacleStateMachine,
    MultiTentacleStateCoordinator,
    DEFAULT_STATE_CONFIGS,
    DEFAULT_TRANSITIONS,
    # Convenience functions
    create_shape_key_generator,
    create_state_machine,
    create_multi_tentacle_coordinator,
)


class TestShapeKeyPreset:
    """Tests for ShapeKeyPreset enum."""

    def test_preset_values(self):
        """Test that all preset values are defined."""
        assert ShapeKeyPreset.BASE.value == "base"
        assert ShapeKeyPreset.COMPRESS_50.value == "compress_50"
        assert ShapeKeyPreset.COMPRESS_75.value == "compress_75"
        assert ShapeKeyPreset.EXPAND_125.value == "expand_125"
        assert ShapeKeyPreset.CURL_TIP.value == "curl_tip"
        assert ShapeKeyPreset.CURL_FULL.value == "curl_full"
        assert ShapeKeyPreset.SQUEEZE_TIP.value == "squeeze_tip"
        assert ShapeKeyPreset.SQUEEZE_MID.value == "squeeze_mid"
        assert ShapeKeyPreset.SQUEEZE_BASE.value == "squeeze_base"
        assert ShapeKeyPreset.SQUEEZE_LOCAL.value == "squeeze_local"

    def test_preset_count(self):
        """Test that we have all expected presets."""
        presets = list(ShapeKeyPreset)
        assert len(presets) == 10


class TestAnimationState:
    """Tests for AnimationState enum."""

    def test_state_values(self):
        """Test that all state values are defined."""
        assert AnimationState.HIDDEN.value == "hidden"
        assert AnimationState.EMERGING.value == "emerging"
        assert AnimationState.SEARCHING.value == "searching"
        assert AnimationState.GRABBING.value == "grabbing"
        assert AnimationState.ATTACKING.value == "attacking"
        assert AnimationState.RETRACTING.value == "retracting"

    def test_is_active(self):
        """Test is_active method for states."""
        assert AnimationState.HIDDEN.is_active() is False
        assert AnimationState.EMERGING.is_active() is False
        assert AnimationState.SEARCHING.is_active() is True
        assert AnimationState.GRABBING.is_active() is True
        assert AnimationState.ATTACKING.is_active() is True
        assert AnimationState.RETRACTING.is_active() is False


class TestShapeKeyConfig:
    """Tests for ShapeKeyConfig dataclass."""

    def test_default_config(self):
        """Test default shape key configuration."""
        config = ShapeKeyConfig(
            name="Test",
            preset=ShapeKeyPreset.BASE,
        )
        assert config.name == "Test"
        assert config.preset == ShapeKeyPreset.BASE
        assert config.diameter_scale == 1.0
        assert config.length_scale == 1.0
        assert config.squeeze_position is None
        assert config.squeeze_width == 0.2
        assert config.curl_angle == 0.0
        assert config.curl_start == 0.0
        assert config.volume_preservation == 0.0
        assert config.interpolation == "linear"

    def test_get_shape_key_name(self):
        """Test shape key name generation."""
        config = ShapeKeyConfig(
            name="Compress50",
            preset=ShapeKeyPreset.COMPRESS_50,
        )
        assert config.get_shape_key_name() == "SK_Compress50"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = ShapeKeyConfig(
            name="Test",
            preset=ShapeKeyPreset.COMPRESS_50,
            diameter_scale=0.5,
            length_scale=2.0,
        )
        d = config.to_dict()
        assert d["name"] == "Test"
        assert d["preset"] == "compress_50"
        assert d["diameter_scale"] == 0.5
        assert d["length_scale"] == 2.0


class TestStateTransition:
    """Tests for StateTransition dataclass."""

    def test_default_transition(self):
        """Test default state transition."""
        transition = StateTransition(
            from_state=AnimationState.HIDDEN,
            to_state=AnimationState.EMERGING,
        )
        assert transition.from_state == AnimationState.HIDDEN
        assert transition.to_state == AnimationState.EMERGING
        assert transition.duration == 0.5
        assert transition.blend_curve == "ease_out"
        assert transition.shape_key_blend == {}
        assert transition.conditions == {}

    def test_to_dict(self):
        """Test transition serialization."""
        transition = StateTransition(
            from_state=AnimationState.HIDDEN,
            to_state=AnimationState.EMERGING,
            duration=0.3,
            shape_key_blend={"Compress50": 1.0},
        )
        d = transition.to_dict()
        assert d["from_state"] == "hidden"
        assert d["to_state"] == "emerging"
        assert d["duration"] == 0.3
        assert d["shape_key_blend"] == {"Compress50": 1.0}


class TestShapeKeyGenerator:
    """Tests for ShapeKeyGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a shape key generator."""
        return ShapeKeyGenerator()

    @pytest.fixture
    def sample_vertices(self):
        """Create sample vertex data for a tentacle."""
        # Create a simple cylinder-like shape
        num_segments = 20
        vertices_per_ring = 8
        vertices = []

        for seg in range(num_segments):
            t = seg / (num_segments - 1)
            z = t * 1.0  # Length of 1 meter
            radius = 0.04 - 0.02 * t  # Taper from 0.04 to 0.02

            for v in range(vertices_per_ring):
                angle = 2 * np.pi * v / vertices_per_ring
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                vertices.append([x, y, z])

        return np.array(vertices)

    @pytest.fixture
    def sample_taper_radii(self):
        """Create sample taper radii."""
        return np.linspace(0.04, 0.01, 20)

    @pytest.fixture
    def sample_segment_positions(self):
        """Create sample segment positions."""
        return np.linspace(0.0, 1.0, 20)

    def test_generator_creation(self, generator):
        """Test that generator can be created."""
        assert generator is not None

    def test_generate_compress_50(self, generator, sample_vertices, sample_taper_radii, sample_segment_positions):
        """Test generating compress_50 shape key."""
        config = get_preset_config(ShapeKeyPreset.COMPRESS_50)

        # Get base and tip vertices
        base_verts = sample_vertices[sample_vertices[:, 2] < 0.1]
        tip_verts = sample_vertices[sample_vertices[:, 2] > 0.9]

        result = generator.generate_shape_key(
            base_verts, tip_verts, sample_vertices,
            sample_taper_radii, sample_segment_positions, config
        )

        assert result.success is True
        assert result.shape_key_name == "SK_compress_50"
        assert result.vertex_count == len(sample_vertices)
        assert result.max_displacement >= 0

    def test_generate_curl_tip(self, generator, sample_vertices, sample_taper_radii, sample_segment_positions):
        """Test generating curl_tip shape key."""
        config = get_preset_config(ShapeKeyPreset.CURL_TIP)

        base_verts = sample_vertices[sample_vertices[:, 2] < 0.1]
        tip_verts = sample_vertices[sample_vertices[:, 2] > 0.9]

        result = generator.generate_shape_key(
            base_verts, tip_verts, sample_vertices,
            sample_taper_radii, sample_segment_positions, config
        )

        assert result.success is True
        assert result.shape_key_name == "SK_curl_tip"

    def test_generate_all_presets(self, generator, sample_vertices, sample_taper_radii, sample_segment_positions):
        """Test generating all presets."""
        base_verts = sample_vertices[sample_vertices[:, 2] < 0.1]
        tip_verts = sample_vertices[sample_vertices[:, 2] > 0.9]

        results = generator.generate_all_presets(
            base_verts, tip_verts, sample_vertices,
            sample_taper_radii, sample_segment_positions
        )

        # Should have all presets except BASE
        expected_count = len(ShapeKeyPreset) - 1
        assert len(results) == expected_count

        for preset in ShapeKeyPreset:
            if preset != ShapeKeyPreset.BASE:
                assert preset.value in results
                assert results[preset.value].success is True


class TestGetPresetConfig:
    """Tests for get_preset_config function."""

    def test_get_base_preset(self):
        """Test getting base preset configuration."""
        config = get_preset_config(ShapeKeyPreset.BASE)
        assert config.preset == ShapeKeyPreset.BASE
        assert config.diameter_scale == 1.0
        assert config.length_scale == 1.0

    def test_get_compress_50_preset(self):
        """Test getting compress_50 preset configuration."""
        config = get_preset_config(ShapeKeyPreset.COMPRESS_50)
        assert config.preset == ShapeKeyPreset.COMPRESS_50
        assert config.diameter_scale == 0.5
        assert config.length_scale == 2.0
        assert config.volume_preservation == 0.3

    def test_get_curl_tip_preset(self):
        """Test getting curl_tip preset configuration."""
        config = get_preset_config(ShapeKeyPreset.CURL_TIP)
        assert config.preset == ShapeKeyPreset.CURL_TIP
        assert config.curl_angle == 180.0
        assert config.curl_start == 0.8


class TestTentacleStateMachine:
    """Tests for TentacleStateMachine class."""

    @pytest.fixture
    def state_machine(self):
        """Create a state machine."""
        return TentacleStateMachine()

    def test_initial_state(self, state_machine):
        """Test initial state is HIDDEN."""
        assert state_machine.current_state == AnimationState.HIDDEN

    def test_can_transition_to_emerging(self, state_machine):
        """Test can transition from HIDDEN to EMERGING."""
        assert state_machine.can_transition_to(AnimationState.EMERGING) is True

    def test_cannot_transition_to_searching(self, state_machine):
        """Test cannot transition directly from HIDDEN to SEARCHING."""
        assert state_machine.can_transition_to(AnimationState.SEARCHING) is False

    def test_transition_to_emerging(self, state_machine):
        """Test transitioning to EMERGING state."""
        result = state_machine.transition_to(AnimationState.EMERGING)
        assert result is True
        assert state_machine.current_state == AnimationState.EMERGING
        assert state_machine.previous_state == AnimationState.HIDDEN

    def test_state_time_increases(self, state_machine):
        """Test that state time increases with updates."""
        initial_time = state_machine.state_time
        state_machine.update(0.1)
        assert state_machine.state_time == initial_time + 0.1

    def test_get_shape_key_values(self, state_machine):
        """Test getting shape key values."""
        values = state_machine.get_shape_key_values()
        assert isinstance(values, dict)
        # HIDDEN state should have Compress50 at 1.0
        assert "Compress50" in values

    def test_transition_updates_shape_keys(self, state_machine):
        """Test that shape keys update during transition."""
        # Start in HIDDEN
        values_hidden = state_machine.get_shape_key_values()

        # Transition to EMERGING
        state_machine.transition_to(AnimationState.EMERGING)

        # Should be transitioning
        assert state_machine.is_transitioning is True

        # Update once
        state_machine.update(0.1)

        # Shape keys should be different
        values_emerging = state_machine.get_shape_key_values()

        # Shape keys should blend during transition
        assert values_emerging != values_hidden or state_machine.transition_progress < 1.0

    def test_reset(self, state_machine):
        """Test resetting state machine."""
        state_machine.transition_to(AnimationState.EMERGING)
        state_machine.update(0.5)

        state_machine.reset()

        assert state_machine.current_state == AnimationState.HIDDEN
        assert state_machine.previous_state is None
        assert state_machine.state_time == 0.0

    def test_get_idle_motion(self, state_machine):
        """Test getting idle motion for states."""
        # HIDDEN has no idle motion
        assert state_machine.get_idle_motion() is None

        # Transition to SEARCHING
        state_machine.transition_to(AnimationState.EMERGING)
        state_machine.transition_to(AnimationState.SEARCHING)

        # SEARCHING has undulate idle motion
        assert state_machine.get_idle_motion() == "undulate"


class TestMultiTentacleStateCoordinator:
    """Tests for MultiTentacleStateCoordinator class."""

    @pytest.fixture
    def coordinator(self):
        """Create a coordinator with 4 tentacles."""
        return MultiTentacleStateCoordinator(
            tentacle_count=4,
            base_delay=0.0,
            stagger_delay=0.1
        )

    def test_initial_state(self, coordinator):
        """Test initial state of coordinator."""
        assert coordinator.tentacle_count == 4
        assert len(coordinator.state_machines) == 4

    def test_all_start_hidden(self, coordinator):
        """Test all tentacles start in HIDDEN state."""
        states = coordinator.get_states()
        assert all(s == AnimationState.HIDDEN for s in states)

    def test_trigger_emergence(self, coordinator):
        """Test triggering emergence."""
        coordinator.trigger_emergence()

        # Update enough time for all to emerge
        for _ in range(10):
            coordinator.update(0.1)

        # At least first tentacle should be emerging
        states = coordinator.get_states()
        assert states[0] != AnimationState.HIDDEN

    def test_staggered_emergence(self, coordinator):
        """Test staggered emergence timing."""
        coordinator.trigger_emergence()

        # After 0.05s, first tentacle should start
        coordinator.update(0.05)
        states = coordinator.get_states()
        # First tentacle should be emerging
        assert states[0] == AnimationState.EMERGING

        # After 0.15s total, second tentacle should start
        coordinator.update(0.1)
        states = coordinator.get_states()
        assert states[1] == AnimationState.EMERGING

    def test_trigger_retraction(self, coordinator):
        """Test triggering retraction."""
        # First get tentacles to a state that can transition to RETRACTING
        # (GRABBING and ATTACKING can transition to RETRACTING)
        for sm in coordinator.state_machines:
            # Go through valid transition path
            sm.transition_to(AnimationState.EMERGING)
            sm.transition_to(AnimationState.SEARCHING)
            sm.transition_to(AnimationState.GRABBING)

        coordinator.trigger_retraction()

        states = coordinator.get_states()
        assert all(s == AnimationState.RETRACTING for s in states)

    def test_all_hidden(self, coordinator):
        """Test all_hidden check."""
        assert coordinator.all_hidden() is True

        coordinator.state_machines[0].transition_to(AnimationState.EMERGING)
        assert coordinator.all_hidden() is False

    def test_reset(self, coordinator):
        """Test resetting coordinator."""
        coordinator.trigger_emergence()
        coordinator.update(0.5)

        coordinator.reset()

        assert coordinator.all_hidden() is True
        assert coordinator._time == 0.0


class TestDefaultConfigs:
    """Tests for default configurations."""

    def test_default_state_configs_exist(self):
        """Test that all states have default configs."""
        assert AnimationState.HIDDEN in DEFAULT_STATE_CONFIGS
        assert AnimationState.EMERGING in DEFAULT_STATE_CONFIGS
        assert AnimationState.SEARCHING in DEFAULT_STATE_CONFIGS
        assert AnimationState.GRABBING in DEFAULT_STATE_CONFIGS
        assert AnimationState.ATTACKING in DEFAULT_STATE_CONFIGS
        assert AnimationState.RETRACTING in DEFAULT_STATE_CONFIGS

    def test_default_transitions_exist(self):
        """Test that default transitions are defined."""
        assert len(DEFAULT_TRANSITIONS) > 0

        # Check key transitions exist
        transition_pairs = [
            (AnimationState.HIDDEN, AnimationState.EMERGING),
            (AnimationState.EMERGING, AnimationState.SEARCHING),
            (AnimationState.SEARCHING, AnimationState.GRABBING),
            (AnimationState.SEARCHING, AnimationState.ATTACKING),
        ]

        for from_state, to_state in transition_pairs:
            found = any(
                t.from_state == from_state and t.to_state == to_state
                for t in DEFAULT_TRANSITIONS
            )
            assert found, f"Missing transition: {from_state} -> {to_state}"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_shape_key_generator(self):
        """Test creating shape key generator."""
        generator = create_shape_key_generator()
        assert isinstance(generator, ShapeKeyGenerator)

    def test_create_state_machine(self):
        """Test creating state machine."""
        sm = create_state_machine()
        assert isinstance(sm, TentacleStateMachine)
        assert sm.current_state == AnimationState.HIDDEN

    def test_create_state_machine_with_initial_state(self):
        """Test creating state machine with custom initial state."""
        sm = create_state_machine(initial_state=AnimationState.SEARCHING)
        assert sm.current_state == AnimationState.SEARCHING

    def test_create_multi_tentacle_coordinator(self):
        """Test creating multi-tentacle coordinator."""
        coordinator = create_multi_tentacle_coordinator(
            tentacle_count=3,
            base_delay=0.5,
            stagger_delay=0.2
        )
        assert isinstance(coordinator, MultiTentacleStateCoordinator)
        assert coordinator.tentacle_count == 3
        assert coordinator.base_delay == 0.5
        assert coordinator.stagger_delay == 0.2


class TestRigTypes:
    """Tests for rig-related types."""

    def test_spline_ik_rig_defaults(self):
        """Test SplineIKRig default values."""
        rig = SplineIKRig()
        assert rig.bone_count == 15
        assert rig.bone_prefix == "Tentacle"
        assert rig.curve_name == "Tentacle_Curve"
        assert rig.chain_length == 1.0
        assert rig.root_bone is None
        assert rig.control_empty is True

    def test_rig_config_defaults(self):
        """Test RigConfig default values."""
        ik_rig = SplineIKRig()
        config = RigConfig(ik_rig=ik_rig)
        assert config.ik_rig == ik_rig
        assert config.shape_keys == []
        assert config.control_curve_points == 6
        assert config.skin_weights == "automatic"

    def test_rig_result_defaults(self):
        """Test RigResult default values."""
        result = RigResult(
            armature_name="Test_Armature",
            curve_name="Test_Curve"
        )
        assert result.armature_name == "Test_Armature"
        assert result.curve_name == "Test_Curve"
        assert result.bone_names == []
        assert result.shape_keys == []
        assert result.success is True
        assert result.error is None


class TestShapeKeyPresets:
    """Tests for SHAPE_KEY_PRESETS dictionary."""

    def test_all_presets_have_required_keys(self):
        """Test that all presets have required configuration keys."""
        required_keys = [
            "diameter_scale",
            "length_scale",
            "squeeze_position",
            "squeeze_width",
            "curl_angle",
            "curl_start",
            "volume_preservation",
        ]

        for preset, config in SHAPE_KEY_PRESETS.items():
            for key in required_keys:
                assert key in config, f"Missing key {key} in preset {preset}"

    def test_compress_50_preset_values(self):
        """Test compress_50 preset has correct values."""
        config = SHAPE_KEY_PRESETS[ShapeKeyPreset.COMPRESS_50]
        assert config["diameter_scale"] == 0.5
        assert config["length_scale"] == 2.0
        assert config["volume_preservation"] == 0.3

    def test_curl_full_preset_values(self):
        """Test curl_full preset has correct values."""
        config = SHAPE_KEY_PRESETS[ShapeKeyPreset.CURL_FULL]
        assert config["curl_angle"] == 540.0
        assert config["curl_start"] == 0.3
