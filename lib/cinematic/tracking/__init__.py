"""
Motion Tracking Package

Provides types and utilities for motion tracking workflows:
- TrackData, SolveData, FootageMetadata, TrackingSession, SolveReport types
- Footage metadata extraction via ffprobe
- External tracking import (Nuke .chan, coordinate conversion)
- State persistence for resume capability

Quick Start:
    from lib.cinematic.tracking import (
        TrackData, SolveData, FootageMetadata, TrackingSession,
        extract_metadata, analyze_footage,
        import_nuke_chan, convert_yup_to_zup_position,
    )

    # Extract footage metadata
    metadata = extract_metadata("footage/my_shot.mp4")

    # Import Nuke tracking
    solve = import_nuke_chan("tracking/camera.chan")

    # Session persistence
    manager = TrackingSessionManager()
    manager.save(session)
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
    # Constants
    "BLENDER_AVAILABLE",
]

__version__ = "0.1.0"
