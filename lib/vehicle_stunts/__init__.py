"""
Vehicle Stunts Package

Physics-based vehicle stunt system for Blender.

Milestone v0.14 - Vehicle Stunt System
Requirements: REQ-STUNT-01 through REQ-STUNT-06

Phases:
- Phase 17.0: Stunt Foundation (REQ-STUNT-01)
- Phase 17.1: Ramp & Jump Generation (REQ-STUNT-02)
- Phase 17.2: Building Interaction (REQ-STUNT-03)
- Phase 17.3: Loop & Curve Generation (REQ-STUNT-04)
- Phase 17.4: Launch Control & Physics (REQ-STUNT-05)
- Phase 17.5: Stunt Course Assembly (REQ-STUNT-06)

"""

from .types import (
    # Phase 17.0
    RampType,
    RampConfig,
    TrajectoryPoint,
    LandingZone,
    # Phase 17.2
    KickerConfig,
    TableConfig,
    HipConfig,
    QuarterPipeConfig,
    SpineConfig,
    RollerConfig,
    StepUpConfig,
    StepDownConfig,
    # Phase 17.3
    LoopType,
    LoopConfig,
    BankedTurnConfig,
    HalfPipeConfig,
    WaveConfig,
    BarrelRollConfig,
    # Phase 17.4
    LaunchParams,
    TrajectoryResult,
    SpeedCalculator,
    # Phase 17.5
    StuntElement,
    StuntCourseConfig,
    CourseFlowAnalyzer,
)

from .ramps import (
    # Phase 17.1
    create_ramp,
    get_ramp_preset,
    list_ramp_presets,
    RAMP_PRESETS,
)
from .jumps import (
    # Phase 17.1
    calculate_trajectory,
    generate_landing_zone,
    visualize_trajectory,
    JUMP_PRESETS,
)
from .building_interaction import (
    # Phase 17.2
    detect_rideable_surface,
    create_wall_ride,
    create_corner_bank,
    detect_landing_zones,
    BUILDING_PRESETS,
)
from .loops import (
    # Phase 17.3
    create_loop,
    create_banked_turn,
    create_half_pipe,
    create_wave,
    create_barrel_roll,
    LOOP_PRESETS,
)
from .physics import (
    # Phase 17.4
    calculate_launch_velocity,
    calculate_air_time,
    calculate_landing_velocity,
    calculate_g_force,
    PHYSICS_CONSTANTS,
)
from .launch_control import (
    # Phase 17.4
    LaunchController,
    SpeedRequirement,
    calculate_speed_requirement,
    optimize_launch_angle,
)
from .course import (
    # Phase 17.5
    StuntCourseBuilder,
    add_element_to_course,
    analyze_course_flow,
    validate_course,
    COURSE_PRESETS,
)


__all__ = [
    # Types
    "RampType",
    "RampConfig",
    "TrajectoryPoint",
    "LandingZone",
    "LoopType",
    "LoopConfig",
    "BankedTurnConfig",
    "HalfPipeConfig",
    "WaveConfig",
    "BarrelRollConfig",
    "LaunchParams",
    "TrajectoryResult",
    "StuntElement",
    "StuntCourseConfig",
    # Ramps
    "create_ramp",
    "get_ramp_preset",
    "list_ramp_presets",
    "RAMP_PRESETS",
    # Jumps
    "calculate_trajectory",
    "generate_landing_zone",
    "visualize_trajectory",
    "JUMP_PRESETS",
    # Building
    "detect_rideable_surface",
    "create_wall_ride",
    "create_corner_bank",
    "detect_landing_zones",
    "BUILDING_PRESETS",
    # Loops
    "create_loop",
    "create_banked_turn",
    "create_half_pipe",
    "create_wave",
    "create_barrel_roll",
    "LOOP_PRESETS",
    # Physics
    "calculate_launch_velocity",
    "calculate_air_time",
    "calculate_landing_velocity",
    "calculate_g_force",
    "PHYSICS_CONSTANTS",
    # Launch Control
    "LaunchController",
    "SpeedRequirement",
    "calculate_speed_requirement",
    "optimize_launch_angle",
    # Course
    "StuntCourseBuilder",
    "add_element_to_course",
    "analyze_course_flow",
    "validate_course",
    "COURSE_PRESETS",
]

__version__ = "0.1.0"
