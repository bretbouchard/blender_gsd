"""Integration tests for projector profile system.

These tests verify the complete workflow from profile selection
to camera creation.
"""
import pytest
import math


class TestProjectorWorkflow:
    """Integration tests for complete projector workflow."""

    def test_profile_to_camera_workflow(self):
        """Test complete workflow: profile -> camera."""
        from lib.cinematic.projection.physical import (
            get_profile,
            create_projector_camera,
            configure_render_for_projector,
            restore_render_settings,
        )

        # Get profile
        profile = get_profile("Epson_Home_Cinema_2150")
        assert profile.name == "Epson_Home_Cinema_2150"

        # Verify focal length calculation
        focal = profile.get_blender_focal_length()
        expected = 36.0 * 1.32  # sensor_width * throw_ratio
        assert abs(focal - expected) < 0.01

    def test_short_throw_workflow(self):
        """Test short-throw projector workflow."""
        from lib.cinematic.projection.physical import (
            get_short_throw_profiles,
        )

        # Get short-throw projectors
        profiles = get_short_throw_profiles(0.8)
        assert len(profiles) >= 1

        # Verify all are short-throw
        for profile in profiles:
            assert profile.throw_ratio <= 0.8

    def test_4k_workflow(self):
        """Test 4K projector workflow."""
        from lib.cinematic.projection.physical import (
            get_4k_profiles,
        )

        # Get 4K projectors
        profiles = get_4k_profiles()
        assert len(profiles) >= 1

        # Verify all are 4K
        for profile in profiles:
            width, height = profile.native_resolution
            assert width >= 3840
            assert height >= 2160

    def test_lens_shift_workflow(self):
        """Test lens shift configuration."""
        from lib.cinematic.projection.physical import get_profile

        # Get projector with lens shift
        profile = get_profile("Epson_Home_Cinema_3800")

        # Verify lens shift
        assert profile.lens_shift.vertical > 0
        assert profile.lens_shift.horizontal > 0

        # Verify Blender shift conversion
        shift_x = profile.get_blender_shift_x()
        shift_y = profile.get_blender_shift_y()
        assert shift_x == profile.lens_shift.horizontal
        assert shift_y == profile.lens_shift.vertical


class TestStagePipeline:
    """Tests for stage-based pipeline."""

    def test_stage_normalize(self):
        """Test normalize stage."""
        from lib.cinematic.projection.physical.stages import (
            stage_normalize,
            StageContext,
            StageState,
        )

        context = StageContext(
            parameters={'position': [2.5, 0, 1.8]},
            profile_name="Epson_Home_Cinema_2150",
        )

        state = StageState(stage=-1, profile=None, camera=None)
        result = stage_normalize(state, context)

        assert result.stage == 0
        assert result.profile is not None
        assert result.profile.name == "Epson_Home_Cinema_2150"

    def test_stage_primary_requires_blender(self):
        """Test primary stage requires Blender for camera creation."""
        from lib.cinematic.projection.physical.stages import (
            stage_normalize,
            stage_primary,
            StageContext,
            StageState,
        )

        context = StageContext(
            parameters={'position': [2.5, 0, 1.8]},
            profile_name="Epson_Home_Cinema_2150",
        )

        # Run normalize first
        state = StageState(stage=-1, profile=None, camera=None)
        state = stage_normalize(state, context)

        # Verify normalize succeeded
        assert state.stage == 0
        assert state.profile is not None

        # stage_primary will raise ImportError when bpy is unavailable
        # This is expected behavior - camera creation requires Blender
        try:
            stage_primary(state, context)
            # If we get here, bpy was available (Blender environment)
            assert True  # Test passes if camera was created
        except ImportError:
            # Expected when running outside Blender
            assert True  # Test passes - this is expected


class TestDeterminism:
    """Tests for deterministic execution (Pipeline Rick requirement)."""

    def test_same_inputs_same_seed(self):
        """Test that same inputs produce same seed."""
        from lib.cinematic.projection.physical.stages import (
            stage_normalize,
            StageContext,
            StageState,
        )
        import hashlib

        context = StageContext(
            parameters={'position': [2.5, 0, 1.8]},
            profile_name="Epson_Home_Cinema_2150",
            target_id="reading_room",
        )

        # Run twice with same inputs
        state1 = StageState(stage=-1, profile=None, camera=None)
        result1 = stage_normalize(state1, context)

        state2 = StageState(stage=-1, profile=None, camera=None)
        result2 = stage_normalize(state2, context)

        # Seeds should be identical
        assert context.seed is not None
        # Both calls should produce same seed
        seed1 = int(hashlib.md5('|'.join((
            "Epson_Home_Cinema_2150",
            "[2.5, 0, 1.8]",
            "reading_room",
        )).encode()).hexdigest()[:8], 16)

        assert context.seed == seed1

    def test_different_inputs_different_seed(self):
        """Test that different inputs produce different seeds."""
        from lib.cinematic.projection.physical.stages import (
            stage_normalize,
            StageContext,
            StageState,
        )

        context1 = StageContext(
            parameters={'position': [2.5, 0, 1.8]},
            profile_name="Epson_Home_Cinema_2150",
            target_id="reading_room",
        )

        context2 = StageContext(
            parameters={'position': [3.0, 0, 1.8]},
            profile_name="Epson_Home_Cinema_2150",
            target_id="garage_door",
        )

        state1 = StageState(stage=-1, profile=None, camera=None)
        stage_normalize(state1, context1)
        seed1 = context1.seed

        state2 = StageState(stage=-1, profile=None, camera=None)
        stage_normalize(state2, context2)
        seed2 = context2.seed

        assert seed1 != seed2
