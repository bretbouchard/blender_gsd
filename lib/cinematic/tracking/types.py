"""
Motion Tracking Types

Defines dataclasses for motion tracking, camera solving, and footage metadata.
All classes designed for YAML/JSON serialization via to_dict() and from_dict().

Follows patterns from lib/cinematic/types.py.
"""

from __future__ import annotations
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
