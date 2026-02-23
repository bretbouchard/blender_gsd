"""
Tests for lib/editorial/transitions.py

Comprehensive tests for transitions without Blender (bpy).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from lib.editorial.timeline_types import (
    Transition,
    TransitionType,
    Clip,
    Timecode,
)

from lib.editorial.transitions import (
    HAS_BLENDER,
    create_cut,
    create_dissolve,
    create_wipe,
    create_fade_to_black,
    create_fade_from_black,
    create_dip_to_color,
    apply_transition_blender,
    create_transition_from_preset,
    get_transition_presets,
    TRANSITION_PRESETS,
)


class TestHasBlender:
    """Tests for Blender availability check."""

    def test_has_blender_is_boolean(self):
        """Test that HAS_BLENDER is a boolean."""
        assert isinstance(HAS_BLENDER, bool)


class TestCreateCut:
    """Tests for create_cut function."""

    def test_create_cut_basic(self):
        """Test basic cut creation."""
        trans = create_cut()
        assert trans.type == TransitionType.CUT
        assert trans.duration == 0

    def test_create_cut_with_clips(self):
        """Test cut with clip names."""
        trans = create_cut(from_clip="Shot_001", to_clip="Shot_002")
        assert trans.from_clip == "Shot_001"
        assert trans.to_clip == "Shot_002"

    def test_cut_duration_zero(self):
        """Test that cut always has zero duration."""
        trans = create_cut()
        assert trans.duration == 0


class TestCreateDissolve:
    """Tests for create_dissolve function."""

    def test_create_dissolve_basic(self):
        """Test basic dissolve creation."""
        trans = create_dissolve()
        assert trans.type == TransitionType.DISSOLVE
        assert trans.duration == 12  # Default

    def test_create_dissolve_custom_duration(self):
        """Test dissolve with custom duration."""
        trans = create_dissolve(duration=24)
        assert trans.duration == 24

    def test_create_dissolve_with_clips(self):
        """Test dissolve with clip names."""
        trans = create_dissolve(
            duration=12,
            from_clip="A",
            to_clip="B"
        )
        assert trans.from_clip == "A"
        assert trans.to_clip == "B"


class TestCreateWipe:
    """Tests for create_wipe function."""

    def test_create_wipe_basic(self):
        """Test basic wipe creation."""
        trans = create_wipe()
        assert trans.type == TransitionType.WIPE
        assert trans.duration == 12  # Default

    def test_create_wipe_directions(self):
        """Test wipe with different directions."""
        for direction in ["left", "right", "up", "down"]:
            trans = create_wipe(direction=direction)
            assert trans.wipe_direction == direction

    def test_create_wipe_custom_duration(self):
        """Test wipe with custom duration."""
        trans = create_wipe(duration=24)
        assert trans.duration == 24

    def test_create_wipe_with_clips(self):
        """Test wipe with clip names."""
        trans = create_wipe(
            direction="right",
            duration=12,
            from_clip="A",
            to_clip="B"
        )
        assert trans.from_clip == "A"
        assert trans.to_clip == "B"


class TestCreateFadeToBlack:
    """Tests for create_fade_to_black function."""

    def test_create_fade_to_black_basic(self):
        """Test basic fade to black creation."""
        trans = create_fade_to_black()
        assert trans.type == TransitionType.FADE_TO_BLACK
        assert trans.duration == 24  # Default

    def test_create_fade_to_black_custom_duration(self):
        """Test fade to black with custom duration."""
        trans = create_fade_to_black(duration=48)
        assert trans.duration == 48

    def test_create_fade_to_black_with_from_clip(self):
        """Test fade to black with from clip."""
        trans = create_fade_to_black(duration=24, from_clip="Shot_001")
        assert trans.from_clip == "Shot_001"
        assert trans.to_clip == ""

    def test_fade_to_black_has_black_color(self):
        """Test that fade to black has black color."""
        trans = create_fade_to_black()
        assert trans.dip_color == (0.0, 0.0, 0.0, 1.0)


class TestCreateFadeFromBlack:
    """Tests for create_fade_from_black function."""

    def test_create_fade_from_black_basic(self):
        """Test basic fade from black creation."""
        trans = create_fade_from_black()
        assert trans.type == TransitionType.FADE_FROM_BLACK
        assert trans.duration == 24  # Default

    def test_create_fade_from_black_custom_duration(self):
        """Test fade from black with custom duration."""
        trans = create_fade_from_black(duration=48)
        assert trans.duration == 48

    def test_create_fade_from_black_with_to_clip(self):
        """Test fade from black with to clip."""
        trans = create_fade_from_black(duration=24, to_clip="Shot_001")
        assert trans.to_clip == "Shot_001"
        assert trans.from_clip == ""

    def test_fade_from_black_has_black_color(self):
        """Test that fade from black has black color."""
        trans = create_fade_from_black()
        assert trans.dip_color == (0.0, 0.0, 0.0, 1.0)


class TestCreateDipToColor:
    """Tests for create_dip_to_color function."""

    def test_create_dip_to_color_basic(self):
        """Test basic dip to color creation."""
        trans = create_dip_to_color()
        assert trans.type == TransitionType.DIP_TO_COLOR
        assert trans.duration == 24  # Default

    def test_create_dip_to_color_custom_color(self):
        """Test dip to color with custom color."""
        trans = create_dip_to_color(color=(1.0, 0.0, 0.0, 1.0))  # Red
        assert trans.dip_color == (1.0, 0.0, 0.0, 1.0)

    def test_create_dip_to_color_custom_duration(self):
        """Test dip to color with custom duration."""
        trans = create_dip_to_color(duration=36)
        assert trans.duration == 36

    def test_create_dip_to_color_with_clips(self):
        """Test dip to color with clip names."""
        trans = create_dip_to_color(
            color=(0.0, 0.0, 1.0, 1.0),  # Blue
            duration=24,
            from_clip="A",
            to_clip="B"
        )
        assert trans.from_clip == "A"
        assert trans.to_clip == "B"


class TestApplyTransitionBlender:
    """Tests for apply_transition_blender function."""

    def test_apply_transition_no_blender(self):
        """Test that function handles missing bpy gracefully."""
        if not HAS_BLENDER:
            trans = Transition(type=TransitionType.CUT)
            clip1 = Clip(name="A")
            clip2 = Clip(name="B")
            result = apply_transition_blender(trans, clip1, clip2)
            assert result is False

    def test_apply_cut_transition(self):
        """Test applying cut transition."""
        trans = Transition(type=TransitionType.CUT)
        clip1 = Clip(name="A")
        clip2 = Clip(name="B")
        # Cut doesn't need Blender
        if HAS_BLENDER:
            result = apply_transition_blender(trans, clip1, clip2)
            assert result is True
        else:
            # Without Blender, should return False for non-cut transitions
            pass


class TestTransitionPresets:
    """Tests for transition presets."""

    def test_transition_presets_exist(self):
        """Test that presets dictionary exists."""
        assert isinstance(TRANSITION_PRESETS, dict)
        assert len(TRANSITION_PRESETS) > 0

    def test_preset_cut(self):
        """Test cut preset."""
        assert "cut" in TRANSITION_PRESETS
        assert TRANSITION_PRESETS["cut"]["type"] == "cut"
        assert TRANSITION_PRESETS["cut"]["duration"] == 0

    def test_preset_dissolves(self):
        """Test dissolve presets."""
        assert "quick_dissolve" in TRANSITION_PRESETS
        assert "standard_dissolve" in TRANSITION_PRESETS
        assert "slow_dissolve" in TRANSITION_PRESETS

        assert TRANSITION_PRESETS["quick_dissolve"]["duration"] == 6
        assert TRANSITION_PRESETS["standard_dissolve"]["duration"] == 12
        assert TRANSITION_PRESETS["slow_dissolve"]["duration"] == 24

    def test_preset_wipes(self):
        """Test wipe presets."""
        assert "wipe_left" in TRANSITION_PRESETS
        assert "wipe_right" in TRANSITION_PRESETS

        assert TRANSITION_PRESETS["wipe_left"]["wipe_direction"] == "left"
        assert TRANSITION_PRESETS["wipe_right"]["wipe_direction"] == "right"

    def test_preset_fades(self):
        """Test fade presets."""
        assert "fade_to_black_quick" in TRANSITION_PRESETS
        assert "fade_to_black_standard" in TRANSITION_PRESETS
        assert "fade_to_black_slow" in TRANSITION_PRESETS


class TestCreateTransitionFromPreset:
    """Tests for create_transition_from_preset function."""

    def test_create_from_preset_cut(self):
        """Test creating cut from preset."""
        trans = create_transition_from_preset("cut", "A", "B")
        assert trans is not None
        assert trans.type == TransitionType.CUT
        assert trans.duration == 0

    def test_create_from_preset_dissolve(self):
        """Test creating dissolve from preset."""
        trans = create_transition_from_preset("quick_dissolve", "A", "B")
        assert trans is not None
        assert trans.type == TransitionType.DISSOLVE
        assert trans.duration == 6

    def test_create_from_preset_wipe(self):
        """Test creating wipe from preset."""
        trans = create_transition_from_preset("wipe_left", "A", "B")
        assert trans is not None
        assert trans.type == TransitionType.WIPE
        assert trans.wipe_direction == "left"

    def test_create_from_preset_fade(self):
        """Test creating fade from preset."""
        trans = create_transition_from_preset("fade_to_black_standard", "A", "B")
        assert trans is not None
        assert trans.type == TransitionType.FADE_TO_BLACK
        assert trans.duration == 24

    def test_create_from_preset_nonexistent(self):
        """Test creating from nonexistent preset."""
        trans = create_transition_from_preset("nonexistent_preset")
        assert trans is None

    def test_create_from_preset_without_clips(self):
        """Test creating from preset without clip names."""
        trans = create_transition_from_preset("standard_dissolve")
        assert trans is not None
        assert trans.from_clip == ""
        assert trans.to_clip == ""


class TestGetTransitionPresets:
    """Tests for get_transition_presets function."""

    def test_get_presets_returns_dict(self):
        """Test that function returns dictionary."""
        presets = get_transition_presets()
        assert isinstance(presets, dict)

    def test_get_presets_returns_copy(self):
        """Test that function returns a copy."""
        presets1 = get_transition_presets()
        presets2 = get_transition_presets()
        # Modifying one should not affect the other
        presets1["test"] = {"type": "test"}
        assert "test" not in presets2


class TestTransitionEdgeCases:
    """Tests for edge cases in transitions."""

    def test_zero_duration_dissolve(self):
        """Test creating dissolve with zero duration."""
        trans = create_dissolve(duration=0)
        assert trans.duration == 0
        assert trans.type == TransitionType.DISSOLVE

    def test_very_long_transition(self):
        """Test creating very long transition."""
        trans = create_dissolve(duration=1000)
        assert trans.duration == 1000

    def test_dip_with_semitransparent_color(self):
        """Test dip to color with semi-transparent color."""
        trans = create_dip_to_color(color=(1.0, 0.0, 0.0, 0.5))
        assert trans.dip_color == (1.0, 0.0, 0.0, 0.5)

    def test_wipe_with_invalid_direction(self):
        """Test wipe with non-standard direction."""
        # The function doesn't validate direction, it just stores it
        trans = create_wipe(direction="diagonal")
        assert trans.wipe_direction == "diagonal"


class TestTransitionTypeEnumConversion:
    """Tests for enum conversion in transitions."""

    def test_transition_string_to_enum(self):
        """Test that Transition converts string type to enum."""
        data = {
            "type": "dissolve",
            "duration": 12
        }
        trans = Transition.from_dict(data)
        assert trans.type == TransitionType.DISSOLVE
        assert isinstance(trans.type, TransitionType)

    def test_transition_enum_stays_enum(self):
        """Test that Transition keeps enum type."""
        trans = Transition(type=TransitionType.WIPE)
        assert trans.type == TransitionType.WIPE
        assert isinstance(trans.type, TransitionType)
