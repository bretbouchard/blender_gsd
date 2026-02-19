"""
Motion Tracking Types

Defines dataclasses for motion tracking, camera solving, and footage metadata.
All classes designed for YAML/JSON serialization via to_dict() and from_dict().

Follows patterns from lib/cinematic/types.py.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List, Optional


@dataclass
class TrackData:
    """
    Single track point data for feature tracking.

    Represents a tracked point/feature across multiple frames with
    pattern matching and correlation quality metrics.

    Attributes:
        name: Track identifier name
        pattern_area: Pattern search region (x, y, width, height) in pixels
        search_area: Search region for tracking (x, y, width, height) in pixels
        markers: Per-frame marker positions (frame -> (x, y) normalized 0-1)
        enabled: Whether track is active
        color: Track display color (RGB 0-1)
        correlation: Track quality score 0-1 (higher = better match)
        track_type: Track type (point, plane, object)
    """
    name: str = ""
    pattern_area: Tuple[int, int, int, int] = (0, 0, 31, 31)  # x, y, width, height
    search_area: Tuple[int, int, int, int] = (0, 0, 61, 61)
    markers: Dict[int, Tuple[float, float]] = field(default_factory=dict)  # frame -> (x, y) normalized 0-1
    enabled: bool = True
    color: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    correlation: float = 1.0  # Track quality 0-1
    track_type: str = "point"  # point, plane, object

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Convert tuple keys to strings for JSON compatibility
        markers_serialized = {str(k): list(v) for k, v in self.markers.items()}
        return {
            "name": self.name,
            "pattern_area": list(self.pattern_area),
            "search_area": list(self.search_area),
            "markers": markers_serialized,
            "enabled": self.enabled,
            "color": list(self.color),
            "correlation": self.correlation,
            "track_type": self.track_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackData:
        """Create from dictionary."""
        # Convert string keys back to integers
        markers_data = data.get("markers", {})
        markers = {int(k): tuple(v) for k, v in markers_data.items()} if markers_data else {}

        return cls(
            name=data.get("name", ""),
            pattern_area=tuple(data.get("pattern_area", (0, 0, 31, 31))),
            search_area=tuple(data.get("search_area", (0, 0, 61, 61))),
            markers=markers,
            enabled=data.get("enabled", True),
            color=tuple(data.get("color", (1.0, 0.0, 0.0))),
            correlation=data.get("correlation", 1.0),
            track_type=data.get("track_type", "point"),
        )


@dataclass
class SolveData:
    """
    Camera solve data with per-frame animation.

    Contains the result of camera tracking/solving with per-frame
    camera transforms (position and rotation).

    Attributes:
        name: Solve identifier name
        frame_range: Frame range for solve (start, end)
        focal_length: Camera focal length in mm
        sensor_width: Camera sensor width in mm
        camera_transforms: Per-frame camera data (frame -> (tx, ty, tz, rx, ry, rz))
        coordinate_system: Coordinate system convention (z_up or y_up)
        solved_at: ISO timestamp when solve was performed
    """
    name: str = ""
    frame_range: Tuple[int, int] = (1, 100)
    focal_length: float = 50.0
    sensor_width: float = 36.0
    # Per-frame data: frame -> (tx, ty, tz, rx, ry, rz)
    camera_transforms: Dict[int, Tuple[float, float, float, float, float, float]] = field(default_factory=dict)
    coordinate_system: str = "z_up"  # z_up (Blender) or y_up (FBX/Nuke)
    solved_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Convert tuple keys to strings for JSON compatibility
        transforms_serialized = {str(k): list(v) for k, v in self.camera_transforms.items()}
        return {
            "name": self.name,
            "frame_range": list(self.frame_range),
            "focal_length": self.focal_length,
            "sensor_width": self.sensor_width,
            "camera_transforms": transforms_serialized,
            "coordinate_system": self.coordinate_system,
            "solved_at": self.solved_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SolveData:
        """Create from dictionary."""
        # Convert string keys back to integers
        transforms_data = data.get("camera_transforms", {})
        transforms = {int(k): tuple(v) for k, v in transforms_data.items()} if transforms_data else {}

        return cls(
            name=data.get("name", ""),
            frame_range=tuple(data.get("frame_range", (1, 100))),
            focal_length=data.get("focal_length", 50.0),
            sensor_width=data.get("sensor_width", 36.0),
            camera_transforms=transforms,
            coordinate_system=data.get("coordinate_system", "z_up"),
            solved_at=data.get("solved_at", ""),
        )


@dataclass
class SolveReport:
    """
    Camera solve quality report.

    Provides quality metrics for camera solve results including
    reprojection error and confidence scoring.

    Attributes:
        reprojection_error_avg: Average reprojection error in pixels
        reprojection_error_max: Maximum reprojection error in pixels
        tracks_used: Number of tracks used in solve
        frames_solved: Number of frames successfully solved
        confidence_score: Overall solve confidence 0-1
        quality_level: Human-readable quality assessment
    """
    reprojection_error_avg: float = 0.0  # Pixels
    reprojection_error_max: float = 0.0
    tracks_used: int = 0
    frames_solved: int = 0
    confidence_score: float = 0.0  # 0-1
    quality_level: str = "unknown"  # excellent, good, acceptable, poor

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reprojection_error_avg": self.reprojection_error_avg,
            "reprojection_error_max": self.reprojection_error_max,
            "tracks_used": self.tracks_used,
            "frames_solved": self.frames_solved,
            "confidence_score": self.confidence_score,
            "quality_level": self.quality_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SolveReport:
        """Create from dictionary."""
        return cls(
            reprojection_error_avg=data.get("reprojection_error_avg", 0.0),
            reprojection_error_max=data.get("reprojection_error_max", 0.0),
            tracks_used=data.get("tracks_used", 0),
            frames_solved=data.get("frames_solved", 0),
            confidence_score=data.get("confidence_score", 0.0),
            quality_level=data.get("quality_level", "unknown"),
        )


@dataclass
class FootageMetadata:
    """
    Extracted video metadata from ffprobe analysis.

    Contains technical metadata extracted from video files including
    resolution, frame rate, codec, and device information.

    Attributes:
        filename: Source video filename
        resolution: Video resolution (width, height) in pixels
        frame_rate: Frame rate in frames per second
        duration_frames: Total number of frames
        duration_seconds: Duration in seconds
        codec: Video codec name
        bit_depth: Bit depth per channel
        color_space: Color space identifier
        camera_model: Camera device model (if available)
        focal_length: Focal length from metadata (if available)
        iso: ISO value from metadata (if available)
        motion_blur_level: Estimated motion blur level
        rolling_shutter_detected: Whether rolling shutter artifacts detected
    """
    filename: str = ""
    resolution: Tuple[int, int] = (1920, 1080)
    frame_rate: float = 24.0
    duration_frames: int = 0
    duration_seconds: float = 0.0
    codec: str = ""
    bit_depth: int = 8
    color_space: str = ""
    # Device metadata (if available from QuickTime tags)
    camera_model: str = ""
    focal_length: float = 0.0
    iso: int = 0
    # Content analysis results
    motion_blur_level: str = "unknown"  # low, medium, high
    rolling_shutter_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "filename": self.filename,
            "resolution": list(self.resolution),
            "frame_rate": self.frame_rate,
            "duration_frames": self.duration_frames,
            "duration_seconds": self.duration_seconds,
            "codec": self.codec,
            "bit_depth": self.bit_depth,
            "color_space": self.color_space,
            "camera_model": self.camera_model,
            "focal_length": self.focal_length,
            "iso": self.iso,
            "motion_blur_level": self.motion_blur_level,
            "rolling_shutter_detected": self.rolling_shutter_detected,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FootageMetadata:
        """Create from dictionary."""
        return cls(
            filename=data.get("filename", ""),
            resolution=tuple(data.get("resolution", (1920, 1080))),
            frame_rate=data.get("frame_rate", 24.0),
            duration_frames=data.get("duration_frames", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            codec=data.get("codec", ""),
            bit_depth=data.get("bit_depth", 8),
            color_space=data.get("color_space", ""),
            camera_model=data.get("camera_model", ""),
            focal_length=data.get("focal_length", 0.0),
            iso=data.get("iso", 0),
            motion_blur_level=data.get("motion_blur_level", "unknown"),
            rolling_shutter_detected=data.get("rolling_shutter_detected", False),
        )


@dataclass
class TrackingSession:
    """
    Tracking session state for resume capability.

    Represents a complete tracking session that can be saved and
    restored for later editing or continuation.

    Attributes:
        session_id: Unique session identifier
        footage_path: Path to source footage file
        frame_start: Start frame for tracking
        frame_end: End frame for tracking
        current_frame: Current frame position
        tracks: List of track points in session
        camera_profile: Camera profile name or preset
        preset: Tracking preset (fast, balanced, precise)
        status: Session status (in_progress, complete, error)
        created_at: ISO timestamp of session creation
        updated_at: ISO timestamp of last update
    """
    session_id: str = ""
    footage_path: str = ""
    frame_start: int = 1
    frame_end: int = 100
    current_frame: int = 1
    tracks: List[TrackData] = field(default_factory=list)
    camera_profile: str = ""
    preset: str = "balanced"
    status: str = "in_progress"  # in_progress, complete, error
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "footage_path": self.footage_path,
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "current_frame": self.current_frame,
            "tracks": [t.to_dict() for t in self.tracks],
            "camera_profile": self.camera_profile,
            "preset": self.preset,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackingSession:
        """Create from dictionary."""
        # Deserialize nested TrackData objects
        tracks_data = data.get("tracks", [])
        tracks = [TrackData.from_dict(t) for t in tracks_data] if tracks_data else []

        return cls(
            session_id=data.get("session_id", ""),
            footage_path=data.get("footage_path", ""),
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 100),
            current_frame=data.get("current_frame", 1),
            tracks=tracks,
            camera_profile=data.get("camera_profile", ""),
            preset=data.get("preset", "balanced"),
            status=data.get("status", "in_progress"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class FootageInfo:
    """
    Footage information for video files and image sequences.

    Contains basic footage metadata used by FootageImporter for
    loading and analyzing video files.

    Attributes:
        source_path: Path to video file or image sequence directory
        width: Frame width in pixels
        height: Frame height in pixels
        frame_start: First frame number
        frame_end: Last frame number
        fps: Frames per second
        duration_seconds: Duration in seconds
        colorspace: Color space name
        codec: Video codec name
        has_alpha: Whether footage has alpha channel
        is_sequence: Whether this is an image sequence
    """
    source_path: str = ""
    width: int = 1920
    height: int = 1080
    frame_start: int = 1
    frame_end: int = 100
    fps: float = 24.0
    duration_seconds: float = 0.0
    colorspace: str = "sRGB"
    codec: str = ""
    has_alpha: bool = False
    is_sequence: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_path": self.source_path,
            "width": self.width,
            "height": self.height,
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "fps": self.fps,
            "duration_seconds": self.duration_seconds,
            "colorspace": self.colorspace,
            "codec": self.codec,
            "has_alpha": self.has_alpha,
            "is_sequence": self.is_sequence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FootageInfo:
        """Create from dictionary."""
        return cls(
            source_path=data.get("source_path", ""),
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 100),
            fps=data.get("fps", 24.0),
            duration_seconds=data.get("duration_seconds", 0.0),
            colorspace=data.get("colorspace", "sRGB"),
            codec=data.get("codec", ""),
            has_alpha=data.get("has_alpha", False),
            is_sequence=data.get("is_sequence", False),
        )


@dataclass
class BatchJob:
    """
    Single batch job definition.

    Attributes:
        id: Unique job identifier
        name: Human-readable job name
        shot_config: Path to shot YAML configuration
        output_path: Output directory for job results
        status: Current job status (pending, running, completed, failed, skipped)
        error: Error message if failed
        start_time: ISO timestamp when job started
        end_time: ISO timestamp when job completed
        retry_count: Number of retry attempts
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "batch_job"
    shot_config: str = ""
    output_path: str = ""
    status: str = "pending"
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "shot_config": self.shot_config,
            "output_path": self.output_path,
            "status": self.status,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchJob":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "batch_job"),
            shot_config=data.get("shot_config", ""),
            output_path=data.get("output_path", ""),
            status=data.get("status", "pending"),
            error=data.get("error"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class BatchConfig:
    """
    Batch processing configuration.

    Attributes:
        workers: Number of parallel workers (default: CPU count - 1)
        resume_on_failure: Skip completed jobs on restart
        checkpoint_path: Path to checkpoint file
        max_retries: Maximum retry attempts per job
        timeout_seconds: Job timeout (0 = no timeout)
        continue_on_error: Continue batch if job fails
    """
    workers: int = 0  # 0 = auto-detect
    resume_on_failure: bool = True
    checkpoint_path: str = ".batch_checkpoint.json"
    max_retries: int = 3
    timeout_seconds: int = 0
    continue_on_error: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workers": self.workers,
            "resume_on_failure": self.resume_on_failure,
            "checkpoint_path": self.checkpoint_path,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "continue_on_error": self.continue_on_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchConfig":
        return cls(
            workers=data.get("workers", 0),
            resume_on_failure=data.get("resume_on_failure", True),
            checkpoint_path=data.get("checkpoint_path", ".batch_checkpoint.json"),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 0),
            continue_on_error=data.get("continue_on_error", True),
        )


@dataclass
class BatchResult:
    """
    Result of batch processing operation.

    Attributes:
        total_jobs: Total number of jobs in batch
        completed: Number of completed jobs
        failed: Number of failed jobs
        skipped: Number of skipped jobs (resume)
        duration_seconds: Total processing time
        jobs: List of job results
    """
    total_jobs: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    jobs: List["BatchJob"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_jobs": self.total_jobs,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "jobs": [j.to_dict() for j in self.jobs],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchResult":
        return cls(
            total_jobs=data.get("total_jobs", 0),
            completed=data.get("completed", 0),
            failed=data.get("failed", 0),
            skipped=data.get("skipped", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            jobs=[BatchJob.from_dict(j) for j in data.get("jobs", [])],
        )


@dataclass
class CornerPinData:
    """
    Corner pin data for planar tracking.

    Represents 4 corners of a tracked plane in image coordinates.
    Used for corner pin effects and planar transformations.

    Attributes:
        frame: Frame number
        corners: Four corners as (top-left, top-right, bottom-right, bottom-left)
        perspective_matrix: Optional 3x3 homography matrix
    """
    frame: int
    corners: Tuple[
        Tuple[float, float],
        Tuple[float, float],
        Tuple[float, float],
        Tuple[float, float]
    ] = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    perspective_matrix: Optional[List[List[float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "corners": [list(c) for c in self.corners],
            "perspective_matrix": self.perspective_matrix,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CornerPinData":
        corners = tuple(tuple(c) for c in data.get("corners", []))
        if len(corners) != 4:
            corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        return cls(
            frame=data.get("frame", 0),
            corners=corners,
            perspective_matrix=data.get("perspective_matrix"),
        )


@dataclass
class PlanarTrack:
    """
    Complete planar track with corner pin data.

    Stores tracked corner positions across a frame range for
    planar tracking and corner pin effects.

    Attributes:
        id: Unique track identifier
        name: Human-readable track name
        frame_start: First frame of track
        frame_end: Last frame of track
        corners: Per-frame corner pin data
        reference_corners: Reference frame corners for alignment
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "planar_track"
    frame_start: int = 1
    frame_end: int = 1
    corners: List["CornerPinData"] = field(default_factory=list)
    reference_corners: Tuple[
        Tuple[float, float], Tuple[float, float],
        Tuple[float, float], Tuple[float, float]
    ] = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

    def get_corners_at_frame(self, frame: int) -> Optional["CornerPinData"]:
        """Get corner pin data for a specific frame."""
        for corner_data in self.corners:
            if corner_data.frame == frame:
                return corner_data
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "corners": [c.to_dict() for c in self.corners],
            "reference_corners": [list(c) for c in self.reference_corners],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanarTrack":
        corners = [CornerPinData.from_dict(c) for c in data.get("corners", [])]
        ref_corners = tuple(tuple(c) for c in data.get("reference_corners", []))
        if len(ref_corners) != 4:
            ref_corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "planar_track"),
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 1),
            corners=corners,
            reference_corners=ref_corners,
        )


@dataclass
class RotationCurve:
    """
    Rotation curve extracted from footage.

    Stores per-frame rotation data for knob tracking and
    rotation-based animation extraction.

    Attributes:
        frame: Frame number
        rotation_degrees: Rotation angle in degrees
        rotation_radians: Rotation angle in radians
        axis: Rotation axis (X, Y, or Z)
    """
    frame: int
    rotation_degrees: float = 0.0
    rotation_radians: float = 0.0
    axis: str = "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "rotation_degrees": self.rotation_degrees,
            "rotation_radians": self.rotation_radians,
            "axis": self.axis,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RotationCurve":
        import math
        deg = data.get("rotation_degrees", 0.0)
        return cls(
            frame=data.get("frame", 0),
            rotation_degrees=deg,
            rotation_radians=data.get("rotation_radians", math.radians(deg)),
            axis=data.get("axis", "Z"),
        )


@dataclass
class RigidBodySolve:
    """
    Rigid body object solve result.

    Contains 6-DOF (degrees of freedom) transform data for
    object tracking and 3D reconstruction.

    Attributes:
        frame: Frame number
        position: Object position (x, y, z)
        rotation: Object rotation as quaternion (w, x, y, z)
        scale: Object scale (x, y, z)
        error: Solve error metric
    """
    frame: int
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    error: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RigidBodySolve":
        return cls(
            frame=data.get("frame", 0),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation=tuple(data.get("rotation", (1.0, 0.0, 0.0, 0.0))),
            scale=tuple(data.get("scale", (1.0, 1.0, 1.0))),
            error=data.get("error", 0.0),
        )


@dataclass
class FloorPlane:
    """
    Detected floor plane data.

    Represents the floor plane detected from LiDAR/scan data
    using RANSAC plane fitting algorithm.

    Attributes:
        normal: Plane normal vector (nx, ny, nz)
        distance: Distance from origin to plane
        confidence: Detection confidence 0-1
        inlier_count: Number of points that fit the plane
        rotation_euler: Euler rotation to align floor to XY plane
    """
    normal: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    distance: float = 0.0
    confidence: float = 0.0
    inlier_count: int = 0
    rotation_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "normal": list(self.normal),
            "distance": self.distance,
            "confidence": self.confidence,
            "inlier_count": self.inlier_count,
            "rotation_euler": list(self.rotation_euler),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FloorPlane":
        """Create from dictionary."""
        return cls(
            normal=tuple(data.get("normal", (0.0, 0.0, 1.0))),
            distance=data.get("distance", 0.0),
            confidence=data.get("confidence", 0.0),
            inlier_count=data.get("inlier_count", 0),
            rotation_euler=tuple(data.get("rotation_euler", (0.0, 0.0, 0.0))),
        )


@dataclass
class ScaleCalibration:
    """
    Scale calibration data.

    Contains scale factor derived from known reference measurements
    in the scanned environment.

    Attributes:
        scale_factor: Multiplier to convert scan units to meters
        reference_type: Type of reference used (aruco, distance, object)
        reference_value: Known reference value in real-world units
        measured_value: Measured value in scan units
        confidence: Calibration confidence 0-1
    """
    scale_factor: float = 1.0
    reference_type: str = "unknown"  # aruco, distance, object
    reference_value: float = 0.0
    measured_value: float = 0.0
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scale_factor": self.scale_factor,
            "reference_type": self.reference_type,
            "reference_value": self.reference_value,
            "measured_value": self.measured_value,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScaleCalibration":
        """Create from dictionary."""
        return cls(
            scale_factor=data.get("scale_factor", 1.0),
            reference_type=data.get("reference_type", "unknown"),
            reference_value=data.get("reference_value", 0.0),
            measured_value=data.get("measured_value", 0.0),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class ScanData:
    """
    Imported scan data with metadata.

    Contains point cloud or mesh data from LiDAR scanners,
    photogrammetry, or other 3D scanning sources.

    Attributes:
        id: Unique scan identifier
        name: Human-readable scan name
        source_path: Path to source file
        source_format: File format (ply, obj, etc.)
        point_count: Number of points in point cloud
        vertex_count: Number of vertices in mesh
        bounds_min: Bounding box minimum corner
        bounds_max: Bounding box maximum corner
        floor: Detected floor plane data
        scale: Scale calibration data
        is_point_cloud: Whether this is point cloud data
        has_color: Whether points have color data
        has_normals: Whether points have normal data
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "scan"
    source_path: str = ""
    source_format: str = ""
    point_count: int = 0
    vertex_count: int = 0
    bounds_min: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bounds_max: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    floor: Optional["FloorPlane"] = None
    scale: Optional["ScaleCalibration"] = None
    is_point_cloud: bool = True
    has_color: bool = False
    has_normals: bool = False

    def get_dimensions(self) -> Tuple[float, float, float]:
        """Get scan dimensions (width, depth, height)."""
        return (
            self.bounds_max[0] - self.bounds_min[0],
            self.bounds_max[1] - self.bounds_min[1],
            self.bounds_max[2] - self.bounds_min[2],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "source_format": self.source_format,
            "point_count": self.point_count,
            "vertex_count": self.vertex_count,
            "bounds_min": list(self.bounds_min),
            "bounds_max": list(self.bounds_max),
            "floor": self.floor.to_dict() if self.floor else None,
            "scale": self.scale.to_dict() if self.scale else None,
            "is_point_cloud": self.is_point_cloud,
            "has_color": self.has_color,
            "has_normals": self.has_normals,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanData":
        """Create from dictionary."""
        floor_data = data.get("floor")
        floor = FloorPlane.from_dict(floor_data) if floor_data else None
        scale_data = data.get("scale")
        scale = ScaleCalibration.from_dict(scale_data) if scale_data else None
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "scan"),
            source_path=data.get("source_path", ""),
            source_format=data.get("source_format", ""),
            point_count=data.get("point_count", 0),
            vertex_count=data.get("vertex_count", 0),
            bounds_min=tuple(data.get("bounds_min", (0.0, 0.0, 0.0))),
            bounds_max=tuple(data.get("bounds_max", (1.0, 1.0, 1.0))),
            floor=floor,
            scale=scale,
            is_point_cloud=data.get("is_point_cloud", True),
            has_color=data.get("has_color", False),
            has_normals=data.get("has_normals", False),
        )


@dataclass
class JointTransform:
    """
    Single joint transform at a frame.

    Represents a single bone/joint transform at a specific frame
    in a motion capture animation.

    Attributes:
        frame: Frame number
        position: Joint position (x, y, z)
        rotation_euler: Euler rotation in degrees (x, y, z)
        rotation_quaternion: Quaternion rotation (w, x, y, z)
        scale: Joint scale (x, y, z)
    """
    frame: int
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_euler: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_quaternion: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "frame": self.frame,
            "position": list(self.position),
            "rotation_euler": list(self.rotation_euler),
            "rotation_quaternion": list(self.rotation_quaternion),
            "scale": list(self.scale),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JointTransform":
        """Create from dictionary."""
        return cls(
            frame=data.get("frame", 0),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation_euler=tuple(data.get("rotation_euler", (0.0, 0.0, 0.0))),
            rotation_quaternion=tuple(data.get("rotation_quaternion", (1.0, 0.0, 0.0, 0.0))),
            scale=tuple(data.get("scale", (1.0, 1.0, 1.0))),
        )


@dataclass
class BoneChannel:
    """
    Animation channel for a single bone/joint.

    Stores animation data for a single bone including its transform
    hierarchy and per-frame transforms.

    Attributes:
        name: Bone name
        parent: Parent bone name (empty string for root)
        transforms: Per-frame joint transforms
        offset: Bone offset from parent (x, y, z)
        channels: Animation channels (e.g., ['Xposition', 'Yposition', 'Zrotation'])
    """
    name: str = ""
    parent: str = ""
    transforms: List["JointTransform"] = field(default_factory=list)
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    channels: List[str] = field(default_factory=list)

    def get_transform_at_frame(self, frame: int) -> Optional["JointTransform"]:
        """Get transform data for a specific frame."""
        for t in self.transforms:
            if t.frame == frame:
                return t
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "parent": self.parent,
            "transforms": [t.to_dict() for t in self.transforms],
            "offset": list(self.offset),
            "channels": self.channels,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BoneChannel":
        """Create from dictionary."""
        transforms = [JointTransform.from_dict(t) for t in data.get("transforms", [])]
        return cls(
            name=data.get("name", ""),
            parent=data.get("parent", ""),
            transforms=transforms,
            offset=tuple(data.get("offset", (0.0, 0.0, 0.0))),
            channels=data.get("channels", []),
        )


@dataclass
class MocapData:
    """
    Complete motion capture data.

    Contains imported motion capture data with bone hierarchy and
    per-frame animation for all joints.

    Attributes:
        id: Unique mocap identifier
        name: Human-readable mocap name
        source_path: Path to source file
        source_format: File format (bvh, fbx, etc.)
        frame_start: First frame number
        frame_end: Last frame number
        fps: Frames per second
        duration_seconds: Animation duration in seconds
        bones: List of bone animation channels
        hierarchy: Bone hierarchy (parent -> [children])
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "mocap"
    source_path: str = ""
    source_format: str = ""
    frame_start: int = 1
    frame_end: int = 1
    fps: float = 30.0
    duration_seconds: float = 0.0
    bones: List["BoneChannel"] = field(default_factory=list)
    hierarchy: Dict[str, List[str]] = field(default_factory=dict)

    def get_bone(self, name: str) -> Optional["BoneChannel"]:
        """Get bone channel by name."""
        for bone in self.bones:
            if bone.name == name:
                return bone
        return None

    def get_bone_names(self) -> List[str]:
        """Get list of all bone names."""
        return [b.name for b in self.bones]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "source_format": self.source_format,
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "fps": self.fps,
            "duration_seconds": self.duration_seconds,
            "bones": [b.to_dict() for b in self.bones],
            "hierarchy": self.hierarchy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MocapData":
        """Create from dictionary."""
        bones = [BoneChannel.from_dict(b) for b in data.get("bones", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "mocap"),
            source_path=data.get("source_path", ""),
            source_format=data.get("source_format", ""),
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 1),
            fps=data.get("fps", 30.0),
            duration_seconds=data.get("duration_seconds", 0.0),
            bones=bones,
            hierarchy=data.get("hierarchy", {}),
        )


@dataclass
class FingerData:
    """
    Finger joint data for hand tracking.

    Represents a single finger joint's rotation and position.

    Attributes:
        finger_name: Finger name (thumb, index, middle, ring, pinky)
        joint_name: Joint name (metacarpal, proximal, intermediate, distal)
        rotation: Joint rotation in degrees (x, y, z)
        position: Joint position (x, y, z)
    """
    finger_name: str = ""
    joint_name: str = ""
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "finger_name": self.finger_name,
            "joint_name": self.joint_name,
            "rotation": list(self.rotation),
            "position": list(self.position),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FingerData":
        """Create from dictionary."""
        return cls(
            finger_name=data.get("finger_name", ""),
            joint_name=data.get("joint_name", ""),
            rotation=tuple(data.get("rotation", (0.0, 0.0, 0.0))),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
        )


@dataclass
class HandFrame:
    """
    Complete hand data for a single frame.

    Contains all finger joint data and wrist transform for
    a single frame of hand animation.

    Attributes:
        frame: Frame number
        wrist_position: Wrist position (x, y, z)
        wrist_rotation: Wrist rotation in degrees (x, y, z)
        fingers: List of finger joint data
        finger_tips: Finger tip positions by finger name
    """
    frame: int
    wrist_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    wrist_rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    fingers: List["FingerData"] = field(default_factory=list)
    finger_tips: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)

    def get_finger_tip(self, finger: str) -> Optional[Tuple[float, float, float]]:
        """Get finger tip position for a specific finger."""
        return self.finger_tips.get(finger)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "frame": self.frame,
            "wrist_position": list(self.wrist_position),
            "wrist_rotation": list(self.wrist_rotation),
            "fingers": [f.to_dict() for f in self.fingers],
            "finger_tips": {k: list(v) for k, v in self.finger_tips.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandFrame":
        """Create from dictionary."""
        fingers = [FingerData.from_dict(f) for f in data.get("fingers", [])]
        finger_tips = {k: tuple(v) for k, v in data.get("finger_tips", {}).items()}
        return cls(
            frame=data.get("frame", 0),
            wrist_position=tuple(data.get("wrist_position", (0.0, 0.0, 0.0))),
            wrist_rotation=tuple(data.get("wrist_rotation", (0.0, 0.0, 0.0))),
            fingers=fingers,
            finger_tips=finger_tips,
        )


@dataclass
class HandAnimation:
    """
    Complete hand animation extracted from mocap.

    Contains per-frame hand tracking data for animation retargeting
    and control surface interaction detection.

    Attributes:
        name: Animation name
        frames: List of hand frame data
        frame_start: First frame number
        frame_end: Last frame number
    """
    name: str = "hand"
    frames: List["HandFrame"] = field(default_factory=list)
    frame_start: int = 1
    frame_end: int = 1

    def get_frame(self, frame: int) -> Optional["HandFrame"]:
        """Get hand data for a specific frame."""
        for f in self.frames:
            if f.frame == frame:
                return f
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "frames": [f.to_dict() for f in self.frames],
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandAnimation":
        """Create from dictionary."""
        frames = [HandFrame.from_dict(f) for f in data.get("frames", [])]
        return cls(
            name=data.get("name", "hand"),
            frames=frames,
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 1),
        )
