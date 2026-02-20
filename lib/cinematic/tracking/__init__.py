"""
Motion Tracking Package

Provides types and utilities for motion tracking workflows:
- TrackData, SolveData, FootageMetadata, TrackingSession, SolveReport types
- Footage metadata extraction via ffprobe
- External tracking import (Nuke .chan, coordinate conversion)
- State persistence for resume capability
- Tracking context management (Phase 7.1)
- Preset loading (Phase 7.1)
- Quality analysis (Phase 7.1)
- Tracking operators (Phase 7.1)
- Compositor integration (Phase 7.4)
- Session persistence with resume (Phase 7.4)
- Shot integration (Phase 7.4)

Quick Start:
    from lib.cinematic.tracking import (
        TrackData, SolveData, FootageMetadata, TrackingSession,
        extract_metadata, analyze_footage,
        import_nuke_chan, convert_yup_to_zup_position,
        # Phase 7.1 additions
        tracking_context, get_tracking_preset,
        analyze_track_quality, detect_features, track_markers,
        # Phase 7.4 additions
        TrackingSessionManager, assemble_shot_with_tracking,
        create_stabilization_nodes, load_composite_preset,
    )

    # Extract footage metadata
    metadata = extract_metadata("footage/my_shot.mp4")

    # Import Nuke tracking
    solve = import_nuke_chan("tracking/camera.chan")

    # Session persistence with resume
    manager = create_session("footage/shot.mp4", "my_shot")
    manager.save_checkpoint(frame=50, operation="track_forward")

    # Composite preset loading
    config = load_composite_preset("over_footage")
"""

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import (
    TrackData,
    SolveData,
    SolveReport,
    FootageMetadata,
    FootageInfo,
    TrackingSession,
    # Object tracking types
    CornerPinData,
    PlanarTrack,
    RotationCurve,
    RigidBodySolve,
    # Scan import types
    FloorPlane,
    ScaleCalibration,
    ScanData,
    # Mocap import types
    JointTransform,
    BoneChannel,
    MocapData,
    FingerData,
    HandFrame,
    HandAnimation,
    # Batch processing types
    BatchJob,
    BatchConfig,
    BatchResult,
)

from .footage import (
    extract_metadata,
    analyze_footage,
    get_frame_rate,
)

from .import_export import (
    convert_yup_to_zup_position,
    convert_yup_to_zup_rotation,
    fov_to_focal_length,
    import_nuke_chan,
    import_tracking_data,
    # Phase 7.3: Import Parsers
    ColladaParser,
    C3DParser,
    # Phase 7.3: Export Helpers
    TDEExportHelper,
    SynthEyesExportHelper,
    TrackingImporter,
    TrackingExporter,
    ImportedCamera,
)

from .session_manager import TrackingSessionManager

from .object_tracker import (
    PlanarTracker,
    KnobTracker,
    RigidBodyTracker,
    FaderTracker,
    ObjectTracker,
)

from .scan_import import (
    PLYParser,
    OBJParser,
    FloorDetector,
    ScaleDetector,
    ScanImporter,
    import_polycam,
    import_reality_scan,
    SCAN_FORMATS,
)

from .mocap import (
    MocapImporter,
    MocapRetargeter,
    ButtonPressDetector,
    PressEvent,
    HAND_BONE_NAMES,
    import_move_ai,
    import_rokoko,
)

# Phase 7.1: Core Tracking additions
from .context import (
    tracking_context,
    get_clip_editor_area,
    ensure_clip_loaded,
    get_active_clip,
    get_tracking_object,
    set_active_tracking_object,
    get_track_by_name,
    get_frame_range,
    is_tracking_available,
    create_tracking_object,
    get_scene_frame_range,
    set_scene_frame,
    get_current_frame,
)

from .presets import (
    load_tracking_preset,
    get_tracking_preset,
    get_detection_params,
    get_tracking_params,
    get_clean_params,
    list_tracking_presets,
    get_preset_description,
    merge_preset_with_overrides,
    get_motion_model,
    get_correlation_threshold,
    validate_preset,
)

from .quality import (
    QualityMetrics,
    analyze_track_quality,
    clean_low_quality_tracks,
    filter_tracks_by_correlation,
    filter_short_tracks,
    get_track_quality_report,
    get_tracks_by_quality,
    get_solve_readiness_score,
    recommend_cleaning_action,
)

from .operators import (
    DetectionResult,
    TrackingResult,
    detect_features,
    track_markers,
    track_markers_forward,
    track_markers_backward,
    solve_camera_motion,
    set_scene_frames,
    get_clip_frame_range,
    set_clip_frame_range,
    clear_reconstruction,
    delete_track,
    delete_all_tracks,
    disable_track,
    select_track,
    get_track_count,
    get_active_track_count,
)

from .camera_solver import (
    solve_camera,
    create_camera_from_solve,
    apply_camera_from_solve,
    get_solve_report,
    export_solve_data,
    CameraSolver,
    SolveOptions,
    SolveStatus,
    TrackStatus,
    TrackingConfig,
    SolveResult,
    Solve,
)

# Phase 7.2: Footage Profiles
from .types import RollingShutterConfig

from .footage_profiles import (
    FFprobeMetadataExtractor,
    FootageAnalyzer,
    RollingShutterDetector,
    FootageProfile,
    ContentAnalysis,
    ImageSequenceAnalyzer,
    extract_metadata,
    analyze_footage,
    analyze_image_sequence,
    get_tracking_recommendations,
)

# Phase 7.4: Compositor Integration
from .compositor import (
    CompositeConfig,
    create_stabilization_nodes,
    create_corner_pin_nodes,
    create_alpha_over_composite,
    create_shadow_composite,
    create_image_node,
    create_mix_node,
    apply_stmap_distortion,
    setup_lens_distortion_workflow,
    load_composite_preset,
    clear_compositor_tree,
)

# Phase 7.4: Session Management
from .session import (
    TrackingSessionManager as SessionManager,
    SessionStatus,
    create_session,
    resume_tracking,
    load_session,
    list_sessions,
    get_session_status,
    export_session_report,
    merge_sessions,
    cleanup_old_sessions,
)

# Phase 7.4: Shot Integration
from .shot_integration import (
    FootageConfig,
    TrackingShotConfig,
    CompositeShotConfig,
    setup_tracked_shot,
    assemble_shot_with_tracking,
    apply_solved_camera,
    setup_shot_compositing,
    load_tracking_shot_yaml,
    validate_tracking_shot_config,
)

__all__ = [
    # Types
    "TrackData",
    "SolveData",
    "SolveReport",
    "FootageMetadata",
    "FootageInfo",
    "TrackingSession",
    # Object tracking types
    "CornerPinData",
    "PlanarTrack",
    "RotationCurve",
    "RigidBodySolve",
    # Scan import types
    "FloorPlane",
    "ScaleCalibration",
    "ScanData",
    # Mocap import types
    "JointTransform",
    "BoneChannel",
    "MocapData",
    "FingerData",
    "HandFrame",
    "HandAnimation",
    # Batch processing types
    "BatchJob",
    "BatchConfig",
    "BatchResult",
    # Footage
    "extract_metadata",
    "analyze_footage",
    "get_frame_rate",
    # Import/Export
    "convert_yup_to_zup_position",
    "convert_yup_to_zup_rotation",
    "fov_to_focal_length",
    "import_nuke_chan",
    "import_tracking_data",
    # Phase 7.3: Import/Export
    "ColladaParser",
    "C3DParser",
    "TDEExportHelper",
    "SynthEyesExportHelper",
    "TrackingImporter",
    "TrackingExporter",
    "ImportedCamera",
    # Session Management
    "TrackingSessionManager",
    # Object Trackers
    "PlanarTracker",
    "KnobTracker",
    "RigidBodyTracker",
    "FaderTracker",
    "ObjectTracker",
    # Scan Import
    "PLYParser",
    "OBJParser",
    "FloorDetector",
    "ScaleDetector",
    "ScanImporter",
    "import_polycam",
    "import_reality_scan",
    "SCAN_FORMATS",
    # Mocap Import
    "MocapImporter",
    "MocapRetargeter",
    "ButtonPressDetector",
    "PressEvent",
    "HAND_BONE_NAMES",
    "import_move_ai",
    "import_rokoko",
    # Phase 7.1: Context
    "tracking_context",
    "get_clip_editor_area",
    "ensure_clip_loaded",
    "get_active_clip",
    "get_tracking_object",
    "set_active_tracking_object",
    "get_track_by_name",
    "get_frame_range",
    "is_tracking_available",
    "create_tracking_object",
    "get_scene_frame_range",
    "set_scene_frame",
    "get_current_frame",
    # Phase 7.1: Presets
    "load_tracking_preset",
    "get_tracking_preset",
    "get_detection_params",
    "get_tracking_params",
    "get_clean_params",
    "list_tracking_presets",
    "get_preset_description",
    "merge_preset_with_overrides",
    "get_motion_model",
    "get_correlation_threshold",
    "validate_preset",
    # Phase 7.1: Quality
    "QualityMetrics",
    "analyze_track_quality",
    "clean_low_quality_tracks",
    "filter_tracks_by_correlation",
    "filter_short_tracks",
    "get_track_quality_report",
    "get_tracks_by_quality",
    "get_solve_readiness_score",
    "recommend_cleaning_action",
    # Phase 7.1: Operators
    "DetectionResult",
    "TrackingResult",
    "detect_features",
    "track_markers",
    "track_markers_forward",
    "track_markers_backward",
    "solve_camera_motion",
    "set_scene_frames",
    "get_clip_frame_range",
    "set_clip_frame_range",
    "clear_reconstruction",
    "delete_track",
    "delete_all_tracks",
    "disable_track",
    "select_track",
    "get_track_count",
    "get_active_track_count",
    # Phase 7.1: Camera Solver
    "solve_camera",
    "create_camera_from_solve",
    "apply_camera_from_solve",
    "get_solve_report",
    "export_solve_data",
    "CameraSolver",
    "SolveOptions",
    "SolveStatus",
    "TrackStatus",
    "TrackingConfig",
    "SolveResult",
    "Solve",
    # Phase 7.2: Footage Profiles
    "RollingShutterConfig",
    "FFprobeMetadataExtractor",
    "FootageAnalyzer",
    "RollingShutterDetector",
    "FootageProfile",
    "ContentAnalysis",
    "ImageSequenceAnalyzer",
    "analyze_image_sequence",
    "get_tracking_recommendations",

    # Phase 7.4: Compositor Integration
    "CompositeConfig",
    "create_stabilization_nodes",
    "create_corner_pin_nodes",
    "create_alpha_over_composite",
    "create_shadow_composite",
    "create_image_node",
    "create_mix_node",
    "apply_stmap_distortion",
    "setup_lens_distortion_workflow",
    "load_composite_preset",
    "clear_compositor_tree",

    # Phase 7.4: Session Management
    "SessionManager",
    "SessionStatus",
    "create_session",
    "resume_tracking",
    "load_session",
    "list_sessions",
    "get_session_status",
    "export_session_report",
    "merge_sessions",
    "cleanup_old_sessions",

    # Phase 7.4: Shot Integration
    "FootageConfig",
    "TrackingShotConfig",
    "CompositeShotConfig",
    "setup_tracked_shot",
    "assemble_shot_with_tracking",
    "apply_solved_camera",
    "setup_shot_compositing",
    "load_tracking_shot_yaml",
    "validate_tracking_shot_config",

    # Constants
    "BLENDER_AVAILABLE",
]

__version__ = "1.2.0"
