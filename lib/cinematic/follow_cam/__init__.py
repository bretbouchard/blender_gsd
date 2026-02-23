"""
Follow Camera System

Dynamic camera following system for subject tracking with multiple follow modes,
collision detection, and obstacle response.

Part of Phase 8.x - Follow Camera System

Modules:
    types: Core data types and configurations
    follow_modes: Follow mode implementations (side-scroller, over-shoulder, etc.)
    transitions: Smooth transitions between camera modes
    collision: Raycast-based collision detection
    prediction: Motion prediction for smoother following
    pre_solve: Pre-compute workflow for deterministic renders
    navmesh: Navigation mesh for camera pathfinding
    framing: Intelligent framing rules (rule of thirds, headroom)
    debug: Visual debug tools

Usage:
    from lib.cinematic.follow_cam import (
        FollowMode,
        FollowCameraConfig,
        FollowTarget,
        calculate_ideal_position,
    )

    # Create configuration
    config = FollowCameraConfig(
        follow_mode=FollowMode.OVER_SHOULDER,
        ideal_distance=3.0,
    )

    # Set target
    target = FollowTarget(object_name="Player")

    # Calculate ideal position
    pos, yaw, pitch = calculate_ideal_position(
        target_position=(0, 0, 0),
        target_forward=(0, 1, 0),
        target_velocity=(0, 0, 0),
        config=config,
    )
"""

from .types import (
    # Enums
    FollowMode,
    LockedPlane,
    ObstacleResponse,
    TransitionType,
    # Data classes
    FollowTarget,
    ObstacleInfo,
    OperatorBehavior,
    FollowCameraConfig,
    CameraState,
)

from .follow_modes import (
    # Mode calculations
    calculate_ideal_position,
    smooth_position,
    smooth_angle,
    calculate_camera_rotation,
    get_target_forward_direction,
)

from .transitions import (
    # Transition classes and functions
    TransitionState,
    TransitionManager,
    calculate_transition_position,
    create_instant_transition,
    create_smooth_transition,
    create_orbit_transition,
    create_dolly_transition,
)

from .collision import (
    # Collision detection
    detect_obstacles,
    calculate_avoidance_position,
    check_frustum_obstruction,
    get_clearance_distance,
)

from .prediction import (
    # Motion prediction
    MotionPredictor,
    PredictionResult,
    predict_look_ahead,
    calculate_anticipation_offset,
    # Oscillation prevention (Phase 8.2)
    OscillationPreventer,
    # Operator behavior (Phase 8.2)
    apply_breathing,
    apply_reaction_delay,
    calculate_angle_preference,
)

from .framing import (
    # Framing rules
    FramingResult,
    calculate_framing_offset,
    calculate_look_room,
    calculate_multi_subject_framing,
    apply_dead_zone,
    get_rule_of_thirds_lines,
    calculate_golden_ratio_offset,
    calculate_center_weighted_framing,
    # Dynamic framing (Phase 8.4)
    calculate_dynamic_framing,
    calculate_action_framing,
    calculate_speed_based_distance,
)

from .debug import (
    # Debug visualization
    DebugConfig,
    DebugVisualizer,
    generate_hud_text,
    get_debug_stats,
    # Frame analysis (Phase 8.4)
    FrameAnalysis,
    FrameAnalyzer,
)

from .pre_solve import (
    # Pre-solve workflow
    PreSolveStage,
    PreSolveResult,
    PreSolver,
    compute_pre_solve_path,
    # One-shot configuration (Phase 8.3)
    ModeChange,
    FramingChange,
    OneShotConfig,
    create_one_shot_from_yaml,
)

from .navmesh import (
    # Navigation mesh
    NavMeshConfig,
    NavMesh,
    NavCell,
    smooth_path,
    simplify_path,
)

__all__ = [
    # Enums
    "FollowMode",
    "LockedPlane",
    "ObstacleResponse",
    "TransitionType",
    # Data classes
    "FollowTarget",
    "ObstacleInfo",
    "OperatorBehavior",
    "FollowCameraConfig",
    "CameraState",
    # Mode calculations
    "calculate_ideal_position",
    "smooth_position",
    "smooth_angle",
    "calculate_camera_rotation",
    "get_target_forward_direction",
    # Transitions
    "TransitionState",
    "TransitionManager",
    "calculate_transition_position",
    "create_instant_transition",
    "create_smooth_transition",
    "create_orbit_transition",
    "create_dolly_transition",
    # Collision
    "detect_obstacles",
    "calculate_avoidance_position",
    "check_frustum_obstruction",
    "get_clearance_distance",
    # Prediction
    "MotionPredictor",
    "PredictionResult",
    "predict_look_ahead",
    "calculate_anticipation_offset",
    # Oscillation prevention (Phase 8.2)
    "OscillationPreventer",
    # Operator behavior (Phase 8.2)
    "apply_breathing",
    "apply_reaction_delay",
    "calculate_angle_preference",
    # Framing
    "FramingResult",
    "calculate_framing_offset",
    "calculate_look_room",
    "calculate_multi_subject_framing",
    "apply_dead_zone",
    "get_rule_of_thirds_lines",
    "calculate_golden_ratio_offset",
    "calculate_center_weighted_framing",
    # Dynamic framing (Phase 8.4)
    "calculate_dynamic_framing",
    "calculate_action_framing",
    "calculate_speed_based_distance",
    # Debug
    "DebugConfig",
    "DebugVisualizer",
    "generate_hud_text",
    "get_debug_stats",
    # Frame analysis (Phase 8.4)
    "FrameAnalysis",
    "FrameAnalyzer",
    # Pre-solve
    "PreSolveStage",
    "PreSolveResult",
    "PreSolver",
    "compute_pre_solve_path",
    # One-shot configuration (Phase 8.3)
    "ModeChange",
    "FramingChange",
    "OneShotConfig",
    "create_one_shot_from_yaml",
    # Navmesh
    "NavMeshConfig",
    "NavMesh",
    "NavCell",
    "smooth_path",
    "simplify_path",
]
