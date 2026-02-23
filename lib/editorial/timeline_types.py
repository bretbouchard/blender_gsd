"""
Timeline Types for Editorial System

Implements core data structures for timeline management:
- Timecode: SMPTE timecode representation
- Clip: Single clip on timeline
- Track: Timeline track (video/audio)
- Timeline: Complete editorial timeline
- Marker: Timeline markers
- Transition: Clip transitions

Part of Phase 11.1: Timeline System (REQ-EDIT-01)
Beads: blender_gsd-41
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class TransitionType(Enum):
    """Types of transitions between clips."""
    CUT = "cut"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    FADE_TO_BLACK = "fade_to_black"
    FADE_FROM_BLACK = "fade_from_black"
    DIP_TO_COLOR = "dip_to_color"


class TrackType(Enum):
    """Types of timeline tracks."""
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class Timecode:
    """
    SMPTE timecode representation.

    Supports standard timecode operations and conversions.
    Format: HH:MM:SS:FF (non-drop frame) or HH:MM:SS;FF (drop frame)

    Attributes:
        hours: Hours (0-23)
        minutes: Minutes (0-59)
        seconds: Seconds (0-59)
        frames: Frames within second (0 to frame_rate-1)
        frame_rate: Frames per second (24, 25, 29.97, 30, etc.)
        drop_frame: Whether to use drop-frame notation
    """
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    frames: int = 0
    frame_rate: float = 24.0
    drop_frame: bool = False

    def __post_init__(self):
        """Validate timecode values."""
        if self.hours < 0 or self.hours > 23:
            raise ValueError(f"Hours must be 0-23, got {self.hours}")
        if self.minutes < 0 or self.minutes > 59:
            raise ValueError(f"Minutes must be 0-59, got {self.minutes}")
        if self.seconds < 0 or self.seconds > 59:
            raise ValueError(f"Seconds must be 0-59, got {self.seconds}")
        max_frames = int(self.frame_rate) - 1
        if self.frames < 0 or self.frames > max_frames:
            raise ValueError(f"Frames must be 0-{max_frames}, got {self.frames}")

    def to_frames(self) -> int:
        """
        Convert timecode to total frame count.

        Returns:
            Total frames from 00:00:00:00
        """
        total = (
            self.hours * 3600 * int(self.frame_rate) +
            self.minutes * 60 * int(self.frame_rate) +
            self.seconds * int(self.frame_rate) +
            self.frames
        )
        return total

    @classmethod
    def from_frames(cls, frames: int, frame_rate: float = 24.0) -> "Timecode":
        """
        Create timecode from total frame count.

        Args:
            frames: Total frame count
            frame_rate: Frames per second

        Returns:
            New Timecode instance
        """
        if frames < 0:
            frames = 0

        fps = int(frame_rate)
        total_seconds = frames // fps
        remaining_frames = frames % fps

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return cls(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            frames=remaining_frames,
            frame_rate=frame_rate,
        )

    @classmethod
    def from_seconds(cls, seconds: float, frame_rate: float = 24.0) -> "Timecode":
        """
        Create timecode from seconds.

        Args:
            seconds: Time in seconds
            frame_rate: Frames per second

        Returns:
            New Timecode instance
        """
        total_frames = int(seconds * frame_rate)
        return cls.from_frames(total_frames, frame_rate)

    @classmethod
    def from_string(cls, timecode_str: str, frame_rate: float = 24.0) -> "Timecode":
        """
        Parse timecode from string.

        Args:
            timecode_str: Timecode in HH:MM:SS:FF or HH:MM:SS;FF format
            frame_rate: Frames per second

        Returns:
            New Timecode instance
        """
        # Determine drop frame from separator
        drop_frame = ';' in timecode_str

        # Split by either : or ;
        parts = timecode_str.replace(';', ':').split(':')

        if len(parts) != 4:
            raise ValueError(f"Invalid timecode format: {timecode_str}")

        return cls(
            hours=int(parts[0]),
            minutes=int(parts[1]),
            seconds=int(parts[2]),
            frames=int(parts[3]),
            frame_rate=frame_rate,
            drop_frame=drop_frame,
        )

    def to_seconds(self) -> float:
        """Convert to seconds."""
        return self.to_frames() / self.frame_rate

    def __str__(self) -> str:
        """Return SMPTE format timecode."""
        separator = ';' if self.drop_frame else ':'
        return f"{self.hours:02d}{separator}{self.minutes:02d}{separator}{self.seconds:02d}{separator}{self.frames:02d}"

    def __repr__(self) -> str:
        return f"Timecode({self})"

    def __add__(self, other: "Timecode") -> "Timecode":
        """Add two timecodes."""
        if isinstance(other, Timecode):
            total = self.to_frames() + other.to_frames()
            return Timecode.from_frames(total, self.frame_rate)
        elif isinstance(other, int):
            return Timecode.from_frames(self.to_frames() + other, self.frame_rate)
        return NotImplemented

    def __sub__(self, other: "Timecode") -> "Timecode":
        """Subtract two timecodes."""
        if isinstance(other, Timecode):
            total = self.to_frames() - other.to_frames()
            return Timecode.from_frames(max(0, total), self.frame_rate)
        elif isinstance(other, int):
            return Timecode.from_frames(max(0, self.to_frames() - other), self.frame_rate)
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Timecode):
            return self.to_frames() == other.to_frames()
        return False

    def __lt__(self, other: "Timecode") -> bool:
        return self.to_frames() < other.to_frames()

    def __le__(self, other: "Timecode") -> bool:
        return self.to_frames() <= other.to_frames()

    def __gt__(self, other: "Timecode") -> bool:
        return self.to_frames() > other.to_frames()

    def __ge__(self, other: "Timecode") -> bool:
        return self.to_frames() >= other.to_frames()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hours": self.hours,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "frames": self.frames,
            "frame_rate": self.frame_rate,
            "drop_frame": self.drop_frame,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Timecode":
        """Create from dictionary."""
        return cls(
            hours=data.get("hours", 0),
            minutes=data.get("minutes", 0),
            seconds=data.get("seconds", 0),
            frames=data.get("frames", 0),
            frame_rate=data.get("frame_rate", 24.0),
            drop_frame=data.get("drop_frame", False),
        )


@dataclass
class Marker:
    """
    Timeline marker.

    Attributes:
        name: Marker name/label
        position: Position on timeline
        color: Marker color
        note: Optional note/comment
    """
    name: str
    position: Timecode
    color: str = "blue"
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "position": self.position.to_dict(),
            "color": self.color,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Marker":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            position=Timecode.from_dict(data.get("position", {})),
            color=data.get("color", "blue"),
            note=data.get("note", ""),
        )


@dataclass
class Transition:
    """
    Transition between clips.

    Attributes:
        type: Transition type
        duration: Duration in frames (0 for cut)
        from_clip: Name of source clip
        to_clip: Name of destination clip
        wipe_direction: Direction for wipe (left, right, up, down)
        dip_color: Color for dip transitions (RGBA tuple)
    """
    type: TransitionType = TransitionType.CUT
    duration: int = 0
    from_clip: str = ""
    to_clip: str = ""
    wipe_direction: str = "left"
    dip_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)

    def __post_init__(self):
        """Convert string type to enum if needed."""
        if isinstance(self.type, str):
            self.type = TransitionType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "duration": self.duration,
            "from_clip": self.from_clip,
            "to_clip": self.to_clip,
            "wipe_direction": self.wipe_direction,
            "dip_color": list(self.dip_color),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transition":
        """Create from dictionary."""
        return cls(
            type=TransitionType(data.get("type", "cut")),
            duration=data.get("duration", 0),
            from_clip=data.get("from_clip", ""),
            to_clip=data.get("to_clip", ""),
            wipe_direction=data.get("wipe_direction", "left"),
            dip_color=tuple(data.get("dip_color", [0.0, 0.0, 0.0, 1.0])),
        )


@dataclass
class Clip:
    """
    Single clip on timeline.

    Represents a portion of source media placed on the timeline.

    Attributes:
        name: Clip name/identifier
        source_path: Path to source media file
        source_in: Start point in source media
        source_out: End point in source media
        record_in: Start point on timeline
        record_out: End point on timeline
        track: Track number
        scene: Scene number (metadata)
        take: Take number (metadata)
        notes: Additional notes
        enabled: Whether clip is active
        locked: Whether clip is locked from editing
    """
    name: str
    source_path: str = ""
    source_in: Timecode = field(default_factory=Timecode)
    source_out: Timecode = field(default_factory=Timecode)
    record_in: Timecode = field(default_factory=Timecode)
    record_out: Timecode = field(default_factory=Timecode)
    track: int = 1
    scene: int = 0
    take: int = 1
    notes: str = ""
    enabled: bool = True
    locked: bool = False

    def __post_init__(self):
        """Calculate record_out if not set."""
        if self.record_out.to_frames() == 0 and self.source_out.to_frames() > 0:
            duration = self.source_out.to_frames() - self.source_in.to_frames()
            self.record_out = self.record_in + duration

    @property
    def duration(self) -> int:
        """Get clip duration in frames."""
        return self.source_out.to_frames() - self.source_in.to_frames()

    @property
    def record_duration(self) -> int:
        """Get record duration in frames."""
        return self.record_out.to_frames() - self.record_in.to_frames()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "source_path": self.source_path,
            "source_in": self.source_in.to_dict(),
            "source_out": self.source_out.to_dict(),
            "record_in": self.record_in.to_dict(),
            "record_out": self.record_out.to_dict(),
            "track": self.track,
            "scene": self.scene,
            "take": self.take,
            "notes": self.notes,
            "enabled": self.enabled,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clip":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            source_path=data.get("source_path", ""),
            source_in=Timecode.from_dict(data.get("source_in", {})),
            source_out=Timecode.from_dict(data.get("source_out", {})),
            record_in=Timecode.from_dict(data.get("record_in", {})),
            record_out=Timecode.from_dict(data.get("record_out", {})),
            track=data.get("track", 1),
            scene=data.get("scene", 0),
            take=data.get("take", 1),
            notes=data.get("notes", ""),
            enabled=data.get("enabled", True),
            locked=data.get("locked", False),
        )


@dataclass
class Track:
    """
    Timeline track.

    Contains a series of clips on a single video or audio track.

    Attributes:
        name: Track name
        track_type: Video or audio track
        track_number: Track number (1-based)
        clips: List of clips on this track
        muted: Whether track is muted
        locked: Whether track is locked
        solo: Whether track is soloed
    """
    name: str
    track_type: TrackType = TrackType.VIDEO
    track_number: int = 1
    clips: List[Clip] = field(default_factory=list)
    muted: bool = False
    locked: bool = False
    solo: bool = False

    def __post_init__(self):
        """Convert string type to enum if needed."""
        if isinstance(self.track_type, str):
            self.track_type = TrackType(self.track_type)

    def add_clip(self, clip: Clip) -> None:
        """Add a clip to this track."""
        clip.track = self.track_number
        self.clips.append(clip)
        # Sort by record_in
        self.clips.sort(key=lambda c: c.record_in.to_frames())

    def remove_clip(self, clip_name: str) -> bool:
        """Remove a clip by name."""
        for i, clip in enumerate(self.clips):
            if clip.name == clip_name:
                self.clips.pop(i)
                return True
        return False

    def get_clip_at(self, position: Timecode) -> Optional[Clip]:
        """Get clip at timeline position."""
        pos_frames = position.to_frames()
        for clip in self.clips:
            if clip.record_in.to_frames() <= pos_frames < clip.record_out.to_frames():
                return clip
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "track_type": self.track_type.value,
            "track_number": self.track_number,
            "clips": [c.to_dict() for c in self.clips],
            "muted": self.muted,
            "locked": self.locked,
            "solo": self.solo,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Track":
        """Create from dictionary."""
        track = cls(
            name=data.get("name", ""),
            track_type=TrackType(data.get("track_type", "video")),
            track_number=data.get("track_number", 1),
            muted=data.get("muted", False),
            locked=data.get("locked", False),
            solo=data.get("solo", False),
        )
        for clip_data in data.get("clips", []):
            track.clips.append(Clip.from_dict(clip_data))
        return track


@dataclass
class Timeline:
    """
    Complete editorial timeline.

    Contains all tracks, clips, transitions, and markers for a sequence.

    Attributes:
        name: Timeline name
        frame_rate: Frames per second
        duration: Total duration
        video_tracks: Video tracks
        audio_tracks: Audio tracks
        transitions: Clip transitions
        markers: Timeline markers
        starting_timecode: Starting timecode (usually 00:00:00:00 or 01:00:00:00)
    """
    name: str = "Timeline"
    frame_rate: float = 24.0
    duration: Timecode = field(default_factory=Timecode)
    video_tracks: List[Track] = field(default_factory=list)
    audio_tracks: List[Track] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    markers: List[Marker] = field(default_factory=list)
    starting_timecode: Timecode = field(default_factory=Timecode)

    def add_video_track(self, name: str = "") -> Track:
        """Add a video track."""
        track_num = len(self.video_tracks) + 1
        track = Track(
            name=name or f"V{track_num}",
            track_type=TrackType.VIDEO,
            track_number=track_num,
        )
        self.video_tracks.append(track)
        return track

    def add_audio_track(self, name: str = "") -> Track:
        """Add an audio track."""
        track_num = len(self.audio_tracks) + 1
        track = Track(
            name=name or f"A{track_num}",
            track_type=TrackType.AUDIO,
            track_number=track_num,
        )
        self.audio_tracks.append(track)
        return track

    def get_all_clips(self) -> List[Clip]:
        """Get all clips from all tracks."""
        clips = []
        for track in self.video_tracks + self.audio_tracks:
            clips.extend(track.clips)
        return sorted(clips, key=lambda c: (c.track, c.record_in.to_frames()))

    def calculate_duration(self) -> Timecode:
        """Calculate total timeline duration."""
        max_frame = 0
        for track in self.video_tracks + self.audio_tracks:
            for clip in track.clips:
                if clip.record_out.to_frames() > max_frame:
                    max_frame = clip.record_out.to_frames()
        return Timecode.from_frames(max_frame, self.frame_rate)

    def find_gaps(self) -> List[Tuple[Timecode, Timecode]]:
        """Find gaps between clips on video track 1."""
        gaps = []
        video_track_1 = None
        for track in self.video_tracks:
            if track.track_number == 1:
                video_track_1 = track
                break

        if not video_track_1 or len(video_track_1.clips) < 2:
            return gaps

        clips = sorted(video_track_1.clips, key=lambda c: c.record_in.to_frames())

        for i in range(len(clips) - 1):
            current_end = clips[i].record_out.to_frames()
            next_start = clips[i + 1].record_in.to_frames()

            if current_end < next_start:
                gaps.append((
                    Timecode.from_frames(current_end, self.frame_rate),
                    Timecode.from_frames(next_start, self.frame_rate),
                ))

        return gaps

    def get_clip_by_name(self, name: str) -> Optional[Clip]:
        """Find a clip by name."""
        for clip in self.get_all_clips():
            if clip.name == name:
                return clip
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "frame_rate": self.frame_rate,
            "duration": self.duration.to_dict(),
            "video_tracks": [t.to_dict() for t in self.video_tracks],
            "audio_tracks": [t.to_dict() for t in self.audio_tracks],
            "transitions": [t.to_dict() for t in self.transitions],
            "markers": [m.to_dict() for m in self.markers],
            "starting_timecode": self.starting_timecode.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Timeline":
        """Create from dictionary."""
        timeline = cls(
            name=data.get("name", "Timeline"),
            frame_rate=data.get("frame_rate", 24.0),
            duration=Timecode.from_dict(data.get("duration", {})),
            starting_timecode=Timecode.from_dict(data.get("starting_timecode", {})),
        )

        for track_data in data.get("video_tracks", []):
            timeline.video_tracks.append(Track.from_dict(track_data))

        for track_data in data.get("audio_tracks", []):
            timeline.audio_tracks.append(Track.from_dict(track_data))

        for trans_data in data.get("transitions", []):
            timeline.transitions.append(Transition.from_dict(trans_data))

        for marker_data in data.get("markers", []):
            timeline.markers.append(Marker.from_dict(marker_data))

        return timeline
