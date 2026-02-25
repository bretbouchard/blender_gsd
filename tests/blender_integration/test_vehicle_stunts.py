"""
Vehicle Stunts Integration Tests

Tests that require Blender's bpy module for vehicle stunt system functionality.
"""

import pytest
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from . import requires_blender, BPY_AVAILABLE

# Skip all tests in this module if Blender not available
pytestmark = pytest.mark.skipif(
    not (BLENDER_AVAILABLE and BPY_AVAILABLE),
    reason="Blender and bpy module required"
)


@requires_blender
class TestRampCreation:
    """Tests for ramp creation with Blender."""

    def test_create_kicker_ramp(self):
        """Test creating a kicker ramp mesh."""
        import bpy

        from lib.vehicle_stunts.ramps import create_ramp, from lib.vehicle_stunts.types import RampType

        config = create_ramp(
            ramp_type=RampType.KICKER,
            width=4.0,
            height=1.5,
            length=6.0,
            angle=25.0,
        )

        assert config is not None
        assert config.ramp_type == RampType.KICKER

    def test_ramp_presets(self):
        """Test loading ramp presets."""
        from lib.vehicle_stunts.ramps import get_ramp_preset, RAMP_PRESETS

        # Check preset exists
        assert "beginner_kicker" in RAMP_PRESETS

        preset = get_ramp_preset("beginner_kicker")
        assert preset is not None
        assert preset.ramp_type == RampType.KICKER

    def test_table_ramp(self):
        """Test creating a table ramp."""
        from lib.vehicle_stunts.ramps import create_ramp
        from lib.vehicle_stunts.types import RampType

        config = create_ramp(
            ramp_type=RampType.TABLE,
            width=5.0,
            height=2.0,
            length=8.0,
            table_length=4.0,
        )

        assert config is not None
        assert config.ramp_type == RampType.TABLE


@requires_blender
class TestLoopCreation:
    """Tests for loop creation with Blender."""

    def test_create_circular_loop(self):
        """Test creating a circular loop configuration."""
        from lib.vehicle_stunts.loops import create_loop
        from lib.vehicle_stunts.types import LoopType, LoopConfig

        config = LoopConfig(
            loop_type=LoopType.CIRCULAR,
            radius=5.0,
        )

        loop = create_loop(config)

        assert loop is not None
        assert loop['type'] == 'loop'
        assert loop['loop_type'] == LoopType.CIRCULAR.name

    def test_loop_physics(self):
        """Test loop physics calculations."""
        from lib.vehicle_stunts.physics import calculate_loop_physics

        physics = calculate_loop_physics(
            radius=5.0,
            entry_speed=20.0,
        )

        assert physics['min_entry_speed'] > 0
        assert physics['can_complete'] is not None
        assert 'g_entry' in physics
        assert 'g_top' in physics


@requires_blender
class TestTrajectoryCalculation:
    """Tests for trajectory calculation with Blender."""

    def test_calculate_trajectory(self):
        """Test trajectory calculation."""
        from lib.vehicle_stunts.jumps import calculate_trajectory

        points = calculate_trajectory(
            launch_velocity=15.0,
            angle=30.0,
            height=1.0,
            num_points=50,
        )

        assert len(points) == 50

        # Check first point is at launch position
        assert abs(points[0].position[2] - 1.0) < 0.1  # z height

        # Check trajectory goes up then down
        max_height = max(p.position[2] for p in points)
        assert max_height > 1.0  # Should go higher than launch height

    def test_optimal_trajectory(self):
        """Test optimal trajectory calculation."""
        from lib.vehicle_stunts.physics import calculate_optimal_trajectory

        # Test with tuple signature
        result = calculate_optimal_trajectory(
            start_pos=(0, 0, 0),
            end_pos=(10, 0, 0),
        )

        assert result['distance'] > 0
        assert result['optimal_angle'] > 0
        assert result['required_speed'] > 0

        # Test with float signature
        result2 = calculate_optimal_trajectory(
            start_pos=10.0,  # distance
            end_pos=None,
            max_height=5.0,  # height_diff
        )

        assert result2['distance'] == 10.0


@requires_blender
class TestCourseBuilder:
    """Tests for stunt course assembly."""

    def test_course_builder_basic(self):
        """Test basic course building."""
        from lib.vehicle_stunts.course import StuntCourseBuilder

        builder = StuntCourseBuilder("test_course", "Test Course")

        # Set start position
        builder.set_start((0, 0, 0), 0, 20.0)

        # Add a ramp
        builder.add_ramp(distance=15.0)

        # Build course
        course = builder.build(difficulty="beginner")

        assert course.course_id == "test_course"
        assert len(course.elements) == 1

    def test_course_validation(self):
        """Test course validation."""
        from lib.vehicle_stunts.course import (
            StuntCourseBuilder,
            validate_course,
        )

        builder = StuntCourseBuilder("validation_test")
        builder.set_start((0, 0, 0), 0, 15.0)
        builder.add_ramp(distance=10.0)
        builder.add_ramp(distance=15.0)

        course = builder.build()

        # Validate course
        is_valid, warnings = validate_course(course)

        # Course should have elements
        assert len(course.elements) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "blender_integration"])
