"""
Motion Tracking Types for Object Tracking and Follow Focus

Defines dataclasses for object tracking markers, motion data, and follow focus.
All classes designed for YAML/JSON serialization via to_dict() and from_dict().

This module provides types for:
- Object tracking markers (track objects, bones, empties)
- Motion data (positions, velocities, accelerations)
- Tracking configuration (solve method, smoothing, prediction)
- Follow focus automation

Follows patterns from lib/cinematic/types.py.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List, Optional
from enum import Enum


class SolveMethod(str, Enum):
    """Tracking solve method."""
    AUTOMATIC = "automatic"  # Auto-track using motion prediction
    MANUAL = "manual"  # Manual keyframe tracking
    PREDICTIVE = "predictive"  # Predictive interpolation for smooth following


class ExportFormat(str, Enum):
    """Tracking data export format."""
    BLENDER = "blender"  # Blender markers/empties
    AFTER_EFFECTS = "ae"  # After Effects nulls
    NUKE = "nuke"  # Nuke .chan format
    JSON = "json"  # Generic JSON export


@dataclass
class TrackingMarker:
    """
    Single tracking point on an object.

    Represents a marker that tracks a specific point on an object, bone, or empty
    through a frame range. Used for follow-focus automation and camera following.

    Attributes:
        name: Unique marker name
        object_ref: Blender object name or path
        bone_name: Bone name for armature tracking (empty for object tracking)
        offset: Local offset from object origin (x, y, z) in meters
        frame_start: First frame of tracking range
        frame_end: Last frame of tracking range
        enabled: Whether marker is active
    """
    name: str = ""
    object_ref: str = ""  # Blender object name or path
    bone_name: str = ""  # For armature tracking
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    frame_start: int = 1
    frame_end: int = 250
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "object_ref": self.object_ref,
            "bone_name": self.bone_name,
            "offset": list(self.offset),
            "frame_start": self.frame_start,
            "frame_end": self.frame_end,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackingMarker:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            object_ref=data.get("object_ref", ""),
            bone_name=data.get("bone_name", ""),
            offset=tuple(data.get("offset", (0.0, 0.0, 0.0))),
            frame_start=data.get("frame_start", 1),
            frame_end=data.get("frame_end", 250),
            enabled=data.get("enabled", True),
        )

    def validate(self) -> List[str]:
        """
        Validate marker configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        if not self.name:
            errors.append("Marker name is required")
        if not self.object_ref:
            errors.append("Object reference is required")
        if self.frame_start > self.frame_end:
            errors.append(f"frame_start ({self.frame_start}) must be <= frame_end ({self.frame_end})")
        return errors


@dataclass
class TrackingData:
    """
    Calculated tracking data for a marker.

    Contains per-frame world positions, velocities, and accelerations
    calculated by the tracking solver.

    Attributes:
        marker_name: Name of the marker this data belongs to
        positions: Per-frame world positions (frame -> (x, y, z))
        velocities: Per-frame velocity vectors (frame -> (vx, vy, vz))
        accelerations: Per-frame acceleration vectors (frame -> (ax, ay, az))
    """
    marker_name: str = ""
    positions: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    velocities: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    accelerations: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Convert int keys to strings for JSON compatibility
        return {
            "marker_name": self.marker_name,
            "positions": {str(k): list(v) for k, v in self.positions.items()},
            "velocities": {str(k): list(v) for k, v in self.velocities.items()},
            "accelerations": {str(k): list(v) for k, v in self.accelerations.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackingData:
        """Create from dictionary."""
        positions = {int(k): tuple(v) for k, v in data.get("positions", {}).items()}
        velocities = {int(k): tuple(v) for k, v in data.get("velocities", {}).items()}
        accelerations = {int(k): tuple(v) for k, v in data.get("accelerations", {}).items()}
        return cls(
            marker_name=data.get("marker_name", ""),
            positions=positions,
            velocities=velocities,
            accelerations=accelerations,
        )

    def get_frame_range(self) -> Tuple[int, int]:
        """Get the frame range covered by this tracking data."""
        if not self.positions:
            return (1, 1)
        frames = sorted(self.positions.keys())
        return (frames[0], frames[-1])

    def get_position_at_frame(self, frame: int) -> Optional[Tuple[float, float, float]]:
        """Get position at a specific frame."""
        return self.positions.get(frame)

    def get_velocity_at_frame(self, frame: int) -> Optional[Tuple[float, float, float]]:
        """Get velocity at a specific frame."""
        return self.velocities.get(frame)

    def get_acceleration_at_frame(self, frame: int) -> Optional[Tuple[float, float, float]]:
        """Get acceleration at a specific frame."""
        return self.accelerations.get(frame)


@dataclass
class TrackingConfig:
    """
    Complete tracking configuration.

    Defines how tracking should be solved, smoothed, and exported.

    Attributes:
        markers: List of tracking markers
        solve_method: How to solve tracking (automatic, manual, predictive)
        smoothing: Smoothing amount 0-1 (0 = none, 1 = maximum)
        prediction_frames: Look-ahead frames for predictive tracking
        export_format: Output format for tracking data
    """
    markers: List[TrackingMarker] = field(default_factory=list)
    solve_method: str = "automatic"  # automatic, manual, predictive
    smoothing: float = 0.5  # 0-1
    prediction_frames: int = 5  # Look-ahead for smooth following
    export_format: str = "blender"  # blender, ae, nuke, json

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "markers": [m.to_dict() for m in self.markers],
            "solve_method": self.solve_method,
            "smoothing": self.smoothing,
            "prediction_frames": self.prediction_frames,
            "export_format": self.export_format,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackingConfig:
        """Create from dictionary."""
        markers = [TrackingMarker.from_dict(m) for m in data.get("markers", [])]
        return cls(
            markers=markers,
            solve_method=data.get("solve_method", "automatic"),
            smoothing=data.get("smoothing", 0.5),
            prediction_frames=data.get("prediction_frames", 5),
            export_format=data.get("export_format", "blender"),
        )

    def validate(self) -> List[str]:
        """
        Validate tracking configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        if not self.markers:
            errors.append("At least one marker is required")
        if self.smoothing < 0.0 or self.smoothing > 1.0:
            errors.append(f"smoothing must be between 0 and 1, got {self.smoothing}")
        if self.prediction_frames < 0:
            errors.append(f"prediction_frames must be >= 0, got {self.prediction_frames}")

        # Validate each marker
        for i, marker in enumerate(self.markers):
            marker_errors = marker.validate()
            for err in marker_errors:
                errors.append(f"Marker {i} ({marker.name}): {err}")

        return errors


@dataclass
class FollowFocusRig:
    """
    Follow-focus rig configuration.

    Defines a camera setup that automatically tracks a target marker
    and adjusts focus distance.

    Attributes:
        name: Rig name
        camera_name: Camera object name
        target_marker: Marker to track
        follow_position: Whether to follow target position
        follow_focus: Whether to auto-adjust focus distance
        position_smoothing: Position interpolation factor (0-1)
        focus_smoothing: Focus interpolation factor (0-1)
        offset: Offset from target position (x, y, z)
    """
    name: str = ""
    camera_name: str = ""
    target_marker: str = ""
    follow_position: bool = True
    follow_focus: bool = True
    position_smoothing: float = 0.5
    focus_smoothing: float = 0.5
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "camera_name": self.camera_name,
            "target_marker": self.target_marker,
            "follow_position": self.follow_position,
            "follow_focus": self.follow_focus,
            "position_smoothing": self.position_smoothing,
            "focus_smoothing": self.focus_smoothing,
            "offset": list(self.offset),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FollowFocusRig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            camera_name=data.get("camera_name", ""),
            target_marker=data.get("target_marker", ""),
            follow_position=data.get("follow_position", True),
            follow_focus=data.get("follow_focus", True),
            position_smoothing=data.get("position_smoothing", 0.5),
            focus_smoothing=data.get("focus_smoothing", 0.5),
            offset=tuple(data.get("offset", (0.0, 0.0, 0.0))),
        )


@dataclass
class TrackingExportResult:
    """
    Result of tracking data export.

    Attributes:
        format: Export format used
        output_path: Path to exported file
        marker_count: Number of markers exported
        frame_count: Number of frames exported
        success: Whether export succeeded
        error_message: Error message if export failed
    """
    format: str = ""
    output_path: str = ""
    marker_count: int = 0
    frame_count: int = 0
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "format": self.format,
            "output_path": self.output_path,
            "marker_count": self.marker_count,
            "frame_count": self.frame_count,
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackingExportResult:
        """Create from dictionary."""
        return cls(
            format=data.get("format", ""),
            output_path=data.get("output_path", ""),
            marker_count=data.get("marker_count", 0),
            frame_count=data.get("frame_count", 0),
            success=data.get("success", True),
            error_message=data.get("error_message", ""),
        )
