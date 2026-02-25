"""
Tests for vehicle stunts module.

Tests for Phase 17.0 - 17.5: Vehicle Stunt System
"""

import pytest
import math

from lib.vehicle_stunts.types import (
    RampType,
    LoopType,
    RampConfig,
    LoopConfig,
    TrajectoryPoint,
    LandingZone,
    StuntElement,
    StuntCourseConfig,
    CourseFlowAnalyzer,
)
from lib.vehicle_stunts.ramps import (
    create_ramp,
    get_ramp_preset,
    list_ramp_presets,
    estimate_launch_speed,
    RAMP_PRESETS,
)
from lib.vehicle_stunts.jumps import (
    calculate_trajectory,
    calculate_air_time,
    calculate_required_speed,
    calculate_optimal_launch_angle,
    JUMP_PRESETS,
)
from lib.vehicle_stunts.physics import (
    calculate_launch_velocity,
    calculate_g_force,
    calculate_loop_physics,
    calculate_banked_turn_physics,
    GRAVITY,
)
from lib.vehicle_stunts.loops import (
    create_loop,
    create_banked_turn,
    LOOP_PRESETS,
)
from lib.vehicle_stunts.course import (
    StuntCourseBuilder,
    create_course_from_preset,
    validate_course,
    analyze_course_flow,
    COURSE_PRESETS,
)


class TestRampTypes:
    """Test ramp type enumerations."""

    def test_ramp_types_exist(self):
        """Test that all ramp types are defined."""
        assert RampType.KICKER is not None
        assert RampType.TABLE is not None
        assert RampType.HIP is not None
        assert RampType.QUARTER_PIPE is not None
        assert RampType.SPINE is not None
        assert RampType.ROLLER is not None
        assert RampType.STEP_UP is not None
        assert RampType.STEP_DOWN is not None

    def test_loop_types_exist(self):
        """Test that all loop types are defined."""
        assert LoopType.CIRCULAR is not None
        assert LoopType.CLOTHOID is not None
        assert LoopType.EGG is not None
        assert LoopType.HELIX is not None


class TestRampConfig:
    """Test ramp configuration."""

    def test_create_ramp_defaults(self):
        """Test creating a ramp with defaults."""
        ramp = create_ramp(RampType.KICKER)
        assert ramp.ramp_type == RampType.KICKER
        assert ramp.width == 4.0
        assert ramp.height == 2.0
        assert ramp.length == 6.0
        assert ramp.angle == 30.0

    def test_create_ramp_custom(self):
        """Test creating a ramp with custom values."""
        ramp = create_ramp(
            RampType.TABLE,
            width=6.0,
            height=3.0,
            length=10.0,
            angle=35.0,
        )
        assert ramp.width == 6.0
        assert ramp.height == 3.0
        assert ramp.length == 10.0
        assert ramp.angle == 35.0

    def test_ramp_to_dict(self):
        """Test converting ramp config to dict."""
        ramp = create_ramp(RampType.KICKER)
        d = ramp.to_dict()
        assert d['ramp_type'] == 'KICKER'
        assert 'width' in d
        assert 'height' in d

    def test_get_ramp_preset(self):
        """Test getting ramp presets."""
        preset = get_ramp_preset('beginner_kicker')
        assert preset is not None
        assert preset.ramp_type == RampType.KICKER
        assert preset.height == 1.0

    def test_list_ramp_presets(self):
        """Test listing ramp presets."""
        presets = list_ramp_presets()
        assert len(presets) > 0
        assert 'beginner_kicker' in presets


class TestPhysics:
    """Test physics calculations."""

    def test_calculate_launch_velocity(self):
        """Test launch velocity calculation."""
        # 10m distance at 30 degrees should need ~11 m/s
        v = calculate_launch_velocity(10.0, 30.0)
        assert v > 0
        assert 8 < v < 15

    def test_calculate_launch_velocity_with_height(self):
        """Test launch velocity with height difference."""
        v_flat = calculate_launch_velocity(10.0, 30.0, height_diff=0.0)
        v_higher = calculate_launch_velocity(10.0, 30.0, height_diff=2.0)
        assert v_higher > v_flat

    def test_calculate_g_force(self):
        """Test G-force calculation."""
        # At 20 m/s around 10m radius
        g = calculate_g_force(20.0, 10.0)
        assert g > 0
        # Should be about 4G
        assert 3 < g < 5

    def test_calculate_air_time(self):
        """Test air time calculation."""
        # 15 m/s at 30 degrees
        t = calculate_air_time(15.0, 30.0)
        assert t > 0
        assert 1 < t < 2  # About 1.5 seconds

    def test_calculate_required_speed(self):
        """Test required speed calculation."""
        speed = calculate_required_speed(10.0, 30.0)
        assert speed > 0
        # Should be around 11 m/s for 10m at 30 degrees
        assert 8 < speed < 14

    def test_calculate_optimal_launch_angle(self):
        """Test optimal launch angle calculation."""
        angle = calculate_optimal_launch_angle(10.0)
        assert 15 < angle < 60

    def test_loop_physics(self):
        """Test loop physics calculation."""
        # 5m radius loop
        physics = calculate_loop_physics(5.0, 15.0)
        assert physics['min_entry_speed'] > 0
        assert 'can_complete' in physics
        assert 'max_g_force' in physics

    def test_banked_turn_physics(self):
        """Test banked turn physics calculation."""
        physics = calculate_banked_turn_physics(15.0, 35.0, 20.0)
        assert physics['design_speed'] > 0
        assert physics['lateral_g'] > 0
        assert 'is_safe' in physics


class TestLoops:
    """Test loop and curve generation."""

    def test_create_loop(self):
        """Test creating a loop."""
        config = LoopConfig(radius=5.0)
        loop = create_loop(config)
        assert loop['type'] == 'loop'
        assert 'geometry' in loop
        assert 'physics' in loop
        assert loop['physics']['min_entry_speed'] > 0

    def test_loop_min_speed(self):
        """Test loop minimum speed calculation."""
        config = LoopConfig(radius=5.0)
        min_speed = config.get_min_speed()
        assert min_speed > 0
        # For 5m radius, should be around 11-12 m/s
        assert 10 < min_speed < 15

    def test_create_banked_turn(self):
        """Test creating a banked turn."""
        from lib.vehicle_stunts.types import BankedTurnConfig
        config = BankedTurnConfig(radius=15.0, angle=35.0)
        turn = create_banked_turn(config)
        assert turn['type'] == 'banked_turn'
        assert 'geometry' in turn
        assert turn['physics']['design_speed'] > 0


class TestCourse:
    """Test stunt course assembly."""

    def test_course_builder(self):
        """Test building a stunt course."""
        builder = StuntCourseBuilder("test_course", "Test Course")
        builder.set_start((0, 0, 0), 0, 20)
        builder.add_ramp(distance=10.0)
        builder.add_turn(angle=90.0, radius=15.0)

        course = builder.build()
        assert course.course_id == "test_course"
        assert len(course.elements) == 2
        assert course.total_length > 0

    def test_course_flow_analyzer(self):
        """Test course flow analysis."""
        builder = StuntCourseBuilder("test_course")
        builder.set_start((0, 0, 0), 0, 20)
        builder.add_ramp(distance=10.0)
        builder.add_ramp(distance=15.0)

        course = builder.build()
        analyzer = CourseFlowAnalyzer(course)
        is_safe = analyzer.analyze()

        assert len(analyzer.speed_profile) == 2

    def test_validate_course(self):
        """Test course validation."""
        builder = StuntCourseBuilder("test_course")
        builder.set_start((0, 0, 0), 0, 20)
        builder.add_ramp(distance=10.0)

        course = builder.build()
        is_valid, issues = validate_course(course)

        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)

    def test_course_from_preset(self):
        """Test creating course from preset."""
        course = create_course_from_preset('beginner_course')
        assert course is not None
        assert len(course.elements) > 0

    def test_list_course_presets(self):
        """Test listing course presets."""
        from lib.vehicle_stunts.course import list_course_presets
        presets = list_course_presets()
        assert len(presets) > 0
        assert 'beginner_course' in presets


class TestTrajectory:
    """Test trajectory calculations."""

    def test_calculate_trajectory(self):
        """Test trajectory calculation."""
        from lib.vehicle_stunts.types import LaunchParams

        params = LaunchParams(speed=15.0, angle=30.0)
        result = calculate_trajectory(params)

        assert len(result.points) > 0
        assert result.peak_height > 0
        assert result.horizontal_distance > 0
        assert result.air_time > 0

    def test_trajectory_phases(self):
        """Test that trajectory has correct phases."""
        from lib.vehicle_stunts.types import LaunchParams

        params = LaunchParams(speed=20.0, angle=35.0)
        result = calculate_trajectory(params)

        phases = {p.phase for p in result.points}
        assert 'launch' in phases or 'flight' in phases


class TestLandingZone:
    """Test landing zone functionality."""

    def test_landing_zone_contains_point(self):
        """Test landing zone point checking."""
        zone = LandingZone(
            center=(10, 0, 0),
            width=5.0,
            length=10.0,
        )

        # Center point should be in zone
        assert zone.contains_point((10, 0, 0))

        # Point outside width
        assert not zone.contains_point((20, 0, 0))
