"""
Follow Camera Intelligent Framing Unit Tests

Tests for: lib/cinematic/follow_cam/framing.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-62
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.framing import (
    FramingResult,
    calculate_framing_offset,
    calculate_look_room,
    calculate_multi_subject_framing,
    apply_dead_zone,
    get_rule_of_thirds_lines,
    calculate_golden_ratio_offset,
    calculate_center_weighted_framing,
    RULE_OF_THIRDS_POINTS,
)
from lib.cinematic.follow_cam.types import (
    FollowCameraConfig,
    FollowTarget,
)


class TestFramingResult:
    """Unit tests for FramingResult dataclass."""

    def test_default_values(self):
        """Default FramingResult should have zero offsets."""
        result = FramingResult()

        compare_vectors(result.target_offset, (0.0, 0.0, 0.0))
        compare_numbers(result.horizontal_shift, 0.0)
        compare_numbers(result.vertical_shift, 0.0)
        assert result.is_within_dead_zone is False
        compare_numbers(result.framing_quality, 1.0)

    def test_custom_values(self):
        """FramingResult should store all framing data."""
        result = FramingResult(
            target_offset=(1.0, 0.0, 0.5),
            horizontal_shift=0.5,
            vertical_shift=-0.25,
            is_within_dead_zone=True,
            framing_quality=0.85,
        )

        compare_vectors(result.target_offset, (1.0, 0.0, 0.5))
        compare_numbers(result.horizontal_shift, 0.5)
        compare_numbers(result.vertical_shift, -0.25)
        assert result.is_within_dead_zone is True
        compare_numbers(result.framing_quality, 0.85)

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        result = FramingResult(
            target_offset=(0.5, 0.0, 0.3),
            horizontal_shift=0.33,
            vertical_shift=-0.1,
            is_within_dead_zone=False,
            framing_quality=0.9,
        )

        data = result.to_dict()

        assert data["target_offset"] == [0.5, 0.0, 0.3]
        assert data["horizontal_shift"] == 0.33
        assert data["vertical_shift"] == -0.1
        assert data["is_within_dead_zone"] is False
        assert data["framing_quality"] == 0.9


class TestCalculateFramingOffset:
    """Unit tests for calculate_framing_offset function."""

    def test_same_position(self):
        """Camera at target position should return default result."""
        result = calculate_framing_offset(
            target_position=(0.0, 0.0, 0.0),
            camera_position=(0.0, 0.0, 0.0),
            camera_rotation=(0.0, 0.0, 0.0),
            config=FollowCameraConfig(),
        )

        compare_vectors(result.target_offset, (0.0, 0.0, 0.0))

    def test_basic_framing(self):
        """Basic framing should calculate offsets."""
        config = FollowCameraConfig(
            rule_of_thirds_offset=(0.33, 0.0),
            headroom=1.1,
        )

        result = calculate_framing_offset(
            target_position=(0.0, 5.0, 0.0),
            camera_position=(0.0, 0.0, 2.0),
            camera_rotation=(0.0, 0.0, 0.0),
            config=config,
        )

        # Should have some horizontal/vertical shift
        assert result.horizontal_shift != 0 or result.vertical_shift != 0

    def test_dead_zone_velocity_low(self):
        """Low velocity should be within dead zone."""
        config = FollowCameraConfig(dead_zone_radius=0.5)

        result = calculate_framing_offset(
            target_position=(0.0, 5.0, 0.0),
            camera_position=(0.0, 0.0, 2.0),
            camera_rotation=(0.0, 0.0, 0.0),
            config=config,
            screen_velocity=(0.1, 0.1),  # Low velocity
        )

        assert result.is_within_dead_zone is True

    def test_dead_zone_velocity_high(self):
        """High velocity should be outside dead zone."""
        config = FollowCameraConfig(dead_zone_radius=0.5)

        result = calculate_framing_offset(
            target_position=(0.0, 5.0, 0.0),
            camera_position=(0.0, 0.0, 2.0),
            camera_rotation=(0.0, 0.0, 0.0),
            config=config,
            screen_velocity=(1.0, 1.0),  # High velocity
        )

        assert result.is_within_dead_zone is False

    def test_framing_quality_calculation(self):
        """Framing quality should be calculated."""
        config = FollowCameraConfig()

        result = calculate_framing_offset(
            target_position=(0.0, 5.0, 0.0),
            camera_position=(0.0, 0.0, 2.0),
            camera_rotation=(0.0, 0.0, 0.0),
            config=config,
        )

        # Quality should be between 0 and 1
        assert 0.0 <= result.framing_quality <= 1.0


class TestCalculateLookRoom:
    """Unit tests for calculate_look_room function."""

    def test_facing_away(self):
        """Subject facing away should have positive look room."""
        offset = calculate_look_room(
            facing_direction=(0.0, 1.0, 0.0),  # Facing +Y
            camera_direction=(0.0, 1.0, 0.0),  # Looking +Y
        )

        # Dot product is 1.0, so offset should be positive
        assert offset > 0

    def test_facing_camera(self):
        """Subject facing camera should have negative look room."""
        offset = calculate_look_room(
            facing_direction=(0.0, -1.0, 0.0),  # Facing -Y
            camera_direction=(0.0, 1.0, 0.0),  # Looking +Y
        )

        # Dot product is -1.0, so offset should be negative
        assert offset < 0

    def test_perpendicular(self):
        """Subject perpendicular to camera should have neutral look room."""
        offset = calculate_look_room(
            facing_direction=(1.0, 0.0, 0.0),  # Facing +X
            camera_direction=(0.0, 1.0, 0.0),  # Looking +Y
        )

        # Dot product is 0, so offset should be near zero
        compare_numbers(offset, 0.0, tolerance=0.01)


class TestCalculateMultiSubjectFraming:
    """Unit tests for calculate_multi_subject_framing function."""

    def test_empty_subjects(self):
        """Empty subjects should return default center."""
        center, distance = calculate_multi_subject_framing([])

        compare_vectors(center, (0.0, 0.0, 0.0))
        compare_numbers(distance, 5.0)  # Default distance

    def test_single_subject(self):
        """Single subject should return its position."""
        center, distance = calculate_multi_subject_framing(
            [(10.0, 5.0, 2.0)]
        )

        compare_vectors(center, (10.0, 5.0, 2.0))
        # Single subject has no spread, so distance is 0.0
        compare_numbers(distance, 0.0)

    def test_two_subjects_equal(self):
        """Two subjects should average their positions."""
        center, distance = calculate_multi_subject_framing(
            [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
        )

        # Center should be at midpoint
        compare_vectors(center, (5.0, 0.0, 0.0))
        # Distance should be enough to frame both (spread is 5, so distance ~12.5)
        assert distance > 5.0

    def test_multiple_subjects(self):
        """Multiple subjects should find center and required distance."""
        center, distance = calculate_multi_subject_framing(
            [
                (0.0, 0.0, 0.0),
                (10.0, 0.0, 0.0),
                (5.0, 10.0, 0.0),
            ]
        )

        # Center should be somewhere between the subjects
        assert 0.0 <= center[0] <= 10.0
        assert 0.0 <= center[1] <= 10.0

    def test_weighted_subjects(self):
        """Weighted subjects should be averaged with weights."""
        center, distance = calculate_multi_subject_framing(
            [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)],
            weights=[0.8, 0.2],  # Favor first subject
        )

        # Center should be closer to first subject
        assert center[0] < 5.0  # Less than midpoint


class TestApplyDeadZone:
    """Unit tests for apply_dead_zone function."""

    def test_within_dead_zone(self):
        """Small changes within dead zone should be ignored."""
        result = apply_dead_zone(
            current_offset=(0.0, 0.0),
            target_offset=(0.1, 0.1),
            dead_zone_radius=0.5,
        )

        # Should return current offset (unchanged)
        compare_vectors(result, (0.0, 0.0))

    def test_outside_dead_zone(self):
        """Changes outside dead zone should be applied."""
        result = apply_dead_zone(
            current_offset=(0.0, 0.0),
            target_offset=(1.0, 1.0),
            dead_zone_radius=0.5,
        )

        # Should return target offset
        compare_vectors(result, (1.0, 1.0))

    def test_exactly_at_dead_zone_radius(self):
        """Exactly at dead zone radius should return current."""
        result = apply_dead_zone(
            current_offset=(0.0, 0.0),
            target_offset=(0.5, 0.0),
            dead_zone_radius=0.5,
        )

        # At boundary, distance equals radius
        compare_vectors(result, (0.5, 0.0))


class TestRuleOfThirdsLines:
    """Unit tests for get_rule_of_thirds_lines function."""

    def test_returns_dictionary(self):
        """Should return a dictionary of line positions."""
        lines = get_rule_of_thirds_lines()

        assert isinstance(lines, dict)

    def test_contains_expected_keys(self):
        """Should contain all expected line positions."""
        lines = get_rule_of_thirds_lines()

        expected_keys = [
            "left_third",
            "right_third",
            "top_third",
            "bottom_third",
            "center",
        ]

        for key in expected_keys:
            assert key in lines, f"Missing key: {key}"

    def test_values_in_range(self):
        """All values should be between 0 and 1."""
        lines = get_rule_of_thirds_lines()

        for key, value in lines.items():
            assert 0.0 <= value <= 1.0, f"{key} value out of range: {value}"

    def test_thirds_values(self):
        """Thirds should be at expected positions."""
        lines = get_rule_of_thirds_lines()

        compare_numbers(lines["left_third"], 0.33, tolerance=0.01)
        compare_numbers(lines["right_third"], 0.67, tolerance=0.01)
        compare_numbers(lines["center"], 0.5, tolerance=0.01)

    def test_rule_of_thirds_constant(self):
        """RULE_OF_THIRDS_POINTS should match function result."""
        lines = get_rule_of_thirds_lines()

        assert lines == RULE_OF_THIRDS_POINTS


class TestCalculateGoldenRatioOffset:
    """Unit tests for calculate_golden_ratio_offset function."""

    def test_returns_tuple(self):
        """Should return a tuple of two floats."""
        result = calculate_golden_ratio_offset()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_golden_ratio_values(self):
        """Should use golden ratio for offset calculation."""
        horizontal, vertical = calculate_golden_ratio_offset()

        # Golden ratio is approximately 1.618
        # Golden point is approximately 0.618
        # Offset from center (0.5) should be ~0.118
        expected_offset = (1.0 / ((1.0 + math.sqrt(5.0)) / 2.0)) - 0.5

        compare_numbers(horizontal, expected_offset, tolerance=0.01)
        compare_numbers(vertical, expected_offset, tolerance=0.01)


class TestCalculateCenterWeightedFraming:
    """Unit tests for calculate_center_weighted_framing function."""

    def test_primary_only(self):
        """Primary with no secondaries should return scaled primary position."""
        result = calculate_center_weighted_framing(
            primary_position=(10.0, 5.0, 2.0),
            secondary_positions=[],
            primary_weight=0.7,
        )

        # With no secondaries, secondary_weight = (1 - 0.7) / 1 = 0.3
        # center = primary * 0.7 = (7.0, 3.5, 1.4)
        compare_vectors(result, (7.0, 3.5, 1.4))

    def test_equal_weight(self):
        """Primary weight of 1.0 should ignore secondaries."""
        result = calculate_center_weighted_framing(
            primary_position=(0.0, 0.0, 0.0),
            secondary_positions=[(10.0, 0.0, 0.0)],
            primary_weight=1.0,
        )

        compare_vectors(result, (0.0, 0.0, 0.0))

    def test_weighted_average(self):
        """Should calculate weighted average of positions."""
        result = calculate_center_weighted_framing(
            primary_position=(0.0, 0.0, 0.0),
            secondary_positions=[(10.0, 0.0, 0.0)],
            primary_weight=0.5,
        )

        # 50% primary + 50% secondary
        compare_vectors(result, (5.0, 0.0, 0.0))

    def test_multiple_secondaries(self):
        """Multiple secondaries should be averaged correctly."""
        result = calculate_center_weighted_framing(
            primary_position=(0.0, 0.0, 0.0),
            secondary_positions=[
                (10.0, 0.0, 0.0),
                (0.0, 10.0, 0.0),
            ],
            primary_weight=0.6,
        )

        # 60% primary at (0, 0, 0)
        # 20% each secondary
        # X: 0.6*0 + 0.2*10 + 0.2*0 = 2.0
        # Y: 0.6*0 + 0.2*0 + 0.2*10 = 2.0
        compare_numbers(result[0], 2.0, tolerance=0.1)
        compare_numbers(result[1], 2.0, tolerance=0.1)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_framing_module_imports(self):
        """All framing types should be importable."""
        from lib.cinematic.follow_cam.framing import (
            FramingResult,
            calculate_framing_offset,
            calculate_look_room,
            calculate_multi_subject_framing,
            apply_dead_zone,
            get_rule_of_thirds_lines,
            calculate_golden_ratio_offset,
            calculate_center_weighted_framing,
        )

        assert FramingResult is not None
        assert calculate_framing_offset is not None

    def test_package_imports_framing(self):
        """Framing APIs should be importable from package."""
        from lib.cinematic.follow_cam import (
            FramingResult,
            calculate_framing_offset,
            calculate_look_room,
            calculate_multi_subject_framing,
            apply_dead_zone,
            get_rule_of_thirds_lines,
            calculate_golden_ratio_offset,
            calculate_center_weighted_framing,
        )

        assert FramingResult is not None
        assert calculate_framing_offset is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
