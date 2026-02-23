"""
Timeline Manager for Editorial System

Provides operations for managing timeline content:
- Add/remove/move clips
- Trim and slip operations
- Transition management
- Gap detection and filling

Part of Phase 11.1: Timeline System (REQ-EDIT-02)
Beads: blender_gsd-41
"""

from __future__ import annotations
from typing import List, Optional, Tuple
import copy

from .timeline_types import (
    Timeline,
    Track,
    Clip,
    Transition,
    Timecode,
    TransitionType,
    TrackType,
)


class TimelineManager:
    """
    Manage timeline operations.

    Provides high-level operations for editing timeline content
    while maintaining consistency.

    Attributes:
        timeline: The timeline being managed
    """

    def __init__(self, timeline: Timeline):
        """Initialize with a timeline."""
        self.timeline = timeline
        self._undo_stack: List[dict] = []
        self._redo_stack: List[dict] = []

    def save_state(self) -> None:
        """Save current state for undo."""
        self._undo_stack.append(self.timeline.to_dict())
        self._redo_stack.clear()

    def undo(self) -> bool:
        """Undo last operation."""
        if not self._undo_stack:
            return False
        self._redo_stack.append(self.timeline.to_dict())
        state = self._undo_stack.pop()
        self.timeline = Timeline.from_dict(state)
        return True

    def redo(self) -> bool:
        """Redo last undone operation."""
        if not self._redo_stack:
            return False
        self._undo_stack.append(self.timeline.to_dict())
        state = self._redo_stack.pop()
        self.timeline = Timeline.from_dict(state)
        return True

    # ==================== Track Operations ====================

    def add_video_track(self, name: str = "") -> Track:
        """Add a new video track."""
        return self.timeline.add_video_track(name)

    def add_audio_track(self, name: str = "") -> Track:
        """Add a new audio track."""
        return self.timeline.add_audio_track(name)

    def remove_track(self, track_number: int, track_type: TrackType) -> bool:
        """Remove a track by number."""
        tracks = (
            self.timeline.video_tracks
            if track_type == TrackType.VIDEO
            else self.timeline.audio_tracks
        )

        for i, track in enumerate(tracks):
            if track.track_number == track_number:
                tracks.pop(i)
                # Renumber remaining tracks
                for j, t in enumerate(tracks[i:], start=i + 1):
                    t.track_number = j
                return True
        return False

    def get_track(self, track_number: int, track_type: TrackType) -> Optional[Track]:
        """Get a track by number."""
        tracks = (
            self.timeline.video_tracks
            if track_type == TrackType.VIDEO
            else self.timeline.audio_tracks
        )
        for track in tracks:
            if track.track_number == track_number:
                return track
        return None

    # ==================== Clip Operations ====================

    def add_clip(self, clip: Clip, track_number: int = 1, track_type: TrackType = TrackType.VIDEO) -> bool:
        """
        Add a clip to the timeline.

        Args:
            clip: Clip to add
            track_number: Target track number
            track_type: Video or audio track

        Returns:
            True if clip was added successfully
        """
        track = self.get_track(track_number, track_type)
        if track is None:
            # Create track if it doesn't exist
            if track_type == TrackType.VIDEO:
                track = self.add_video_track()
            else:
                track = self.add_audio_track()

        track.add_clip(clip)
        return True

    def remove_clip(self, clip_name: str) -> bool:
        """
        Remove a clip from the timeline.

        Args:
            clip_name: Name of clip to remove

        Returns:
            True if clip was found and removed
        """
        for track in self.timeline.video_tracks + self.timeline.audio_tracks:
            if track.remove_clip(clip_name):
                # Also remove any transitions involving this clip
                self.timeline.transitions = [
                    t for t in self.timeline.transitions
                    if t.from_clip != clip_name and t.to_clip != clip_name
                ]
                return True
        return False

    def move_clip(self, clip_name: str, new_position: Timecode) -> bool:
        """
        Move a clip to a new position on the timeline.

        Args:
            clip_name: Name of clip to move
            new_position: New record-in position

        Returns:
            True if clip was moved successfully
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return False

        duration = clip.duration
        clip.record_in = new_position
        clip.record_out = new_position + duration

        return True

    def trim_clip_in(self, clip_name: str, new_in: Timecode) -> bool:
        """
        Trim clip in point.

        Args:
            clip_name: Name of clip to trim
            new_in: New source-in point

        Returns:
            True if clip was trimmed successfully
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return False

        if new_in.to_frames() >= clip.source_out.to_frames():
            return False  # Can't trim beyond out point

        # Adjust source in (keeps record in the same)
        clip.source_in = new_in
        return True

    def trim_clip_out(self, clip_name: str, new_out: Timecode) -> bool:
        """
        Trim clip out point.

        Args:
            clip_name: Name of clip to trim
            new_out: New source-out point

        Returns:
            True if clip was trimmed successfully
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return False

        if new_out.to_frames() <= clip.source_in.to_frames():
            return False  # Can't trim beyond in point

        # Adjust source out and record out
        old_duration = clip.duration
        new_duration = new_out.to_frames() - clip.source_in.to_frames()
        clip.source_out = new_out
        clip.record_out = clip.record_in + new_duration

        return True

    def slip_clip(self, clip_name: str, offset_frames: int) -> bool:
        """
        Slip clip - change source in/out while keeping record duration.

        The clip appears in the same place on the timeline but shows
        different content from the source.

        Args:
            clip_name: Name of clip to slip
            offset_frames: Frames to slip (positive = later content)

        Returns:
            True if clip was slipped successfully
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return False

        new_in = clip.source_in + offset_frames
        new_out = clip.source_out + offset_frames

        # Can't slip beyond source bounds (we don't know source length)
        if new_in.to_frames() < 0:
            return False

        clip.source_in = new_in
        clip.source_out = new_out
        return True

    def slide_clip(self, clip_name: str, offset_frames: int) -> bool:
        """
        Slide clip - move position while keeping source in/out.

        Args:
            clip_name: Name of clip to slide
            offset_frames: Frames to slide (positive = later on timeline)

        Returns:
            True if clip was slid successfully
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return False

        new_record_in = clip.record_in + offset_frames
        if new_record_in.to_frames() < 0:
            return False

        return self.move_clip(clip_name, new_record_in)

    def split_clip(self, clip_name: str, at_position: Timecode) -> Optional[Tuple[Clip, Clip]]:
        """
        Split a clip at a position.

        Args:
            clip_name: Name of clip to split
            at_position: Position to split at (record timecode)

        Returns:
            Tuple of (left_clip, right_clip) if successful, None otherwise
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return None

        # Check position is within clip
        if not (clip.record_in.to_frames() < at_position.to_frames() < clip.record_out.to_frames()):
            return None

        # Calculate source position
        offset = at_position.to_frames() - clip.record_in.to_frames()
        split_source = clip.source_in + offset

        # Create left clip
        left_clip = Clip(
            name=f"{clip_name}_L",
            source_path=clip.source_path,
            source_in=clip.source_in,
            source_out=split_source,
            record_in=clip.record_in,
            record_out=at_position,
            track=clip.track,
            scene=clip.scene,
            take=clip.take,
            notes=clip.notes,
        )

        # Create right clip
        right_clip = Clip(
            name=f"{clip_name}_R",
            source_path=clip.source_path,
            source_in=split_source,
            source_out=clip.source_out,
            record_in=at_position,
            record_out=clip.record_out,
            track=clip.track,
            scene=clip.scene,
            take=clip.take,
            notes=clip.notes,
        )

        # Remove original and add new clips
        self.remove_clip(clip_name)
        self.add_clip(left_clip, clip.track, TrackType.VIDEO)
        self.add_clip(right_clip, clip.track, TrackType.VIDEO)

        return (left_clip, right_clip)

    # ==================== Transition Operations ====================

    def add_transition(self, transition: Transition) -> bool:
        """
        Add a transition between clips.

        Args:
            transition: Transition to add

        Returns:
            True if transition was added successfully
        """
        # Validate clips exist
        if transition.from_clip and not self.timeline.get_clip_by_name(transition.from_clip):
            return False
        if transition.to_clip and not self.timeline.get_clip_by_name(transition.to_clip):
            return False

        # Remove any existing transition at this point
        self.timeline.transitions = [
            t for t in self.timeline.transitions
            if t.from_clip != transition.from_clip
        ]

        self.timeline.transitions.append(transition)
        return True

    def remove_transition(self, from_clip: str) -> bool:
        """
        Remove transition from a clip.

        Args:
            from_clip: Name of source clip

        Returns:
            True if transition was removed
        """
        original_count = len(self.timeline.transitions)
        self.timeline.transitions = [
            t for t in self.timeline.transitions
            if t.from_clip != from_clip
        ]
        return len(self.timeline.transitions) < original_count

    def get_transition_after(self, clip_name: str) -> Optional[Transition]:
        """Get transition after a clip."""
        for trans in self.timeline.transitions:
            if trans.from_clip == clip_name:
                return trans
        return None

    # ==================== Query Operations ====================

    def get_clip_at(self, position: Timecode, track_number: int = 1) -> Optional[Clip]:
        """
        Get clip at timeline position.

        Args:
            position: Timeline position
            track_number: Track to search

        Returns:
            Clip at position or None
        """
        track = self.get_track(track_number, TrackType.VIDEO)
        if track:
            return track.get_clip_at(position)
        return None

    def get_all_clips(self) -> List[Clip]:
        """Get all clips in timeline order."""
        return self.timeline.get_all_clips()

    def calculate_duration(self) -> Timecode:
        """Calculate total timeline duration."""
        return self.timeline.calculate_duration()

    def find_gaps(self) -> List[Tuple[Timecode, Timecode]]:
        """Find gaps between clips."""
        return self.timeline.find_gaps()

    def get_clips_in_range(self, start: Timecode, end: Timecode) -> List[Clip]:
        """
        Get all clips that overlap with a time range.

        Args:
            start: Range start
            end: Range end

        Returns:
            List of clips overlapping range
        """
        clips = []
        start_frames = start.to_frames()
        end_frames = end.to_frames()

        for clip in self.get_all_clips():
            clip_start = clip.record_in.to_frames()
            clip_end = clip.record_out.to_frames()

            # Check for overlap
            if clip_start < end_frames and clip_end > start_frames:
                clips.append(clip)

        return clips

    def calculate_runtime(self) -> float:
        """
        Calculate total runtime in seconds.

        Returns:
            Runtime in seconds
        """
        duration = self.calculate_duration()
        return duration.to_seconds()

    def calculate_runtime_formatted(self) -> str:
        """
        Calculate runtime as formatted string.

        Returns:
            Runtime as MM:SS or HH:MM:SS
        """
        duration = self.calculate_duration()
        seconds = duration.to_seconds()

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    # ==================== Bulk Operations ====================

    def ripple_delete(self, clip_name: str) -> bool:
        """
        Delete a clip and close the gap.

        Args:
            clip_name: Name of clip to delete

        Returns:
            True if successful
        """
        clip = self.timeline.get_clip_by_name(clip_name)
        if clip is None or clip.locked:
            return False

        duration = clip.duration
        track = clip.track

        if not self.remove_clip(clip_name):
            return False

        # Move all subsequent clips earlier
        for other_clip in self.get_all_clips():
            if other_clip.track == track and other_clip.record_in > clip.record_in:
                other_clip.record_in = other_clip.record_in - duration
                other_clip.record_out = other_clip.record_out - duration

        return True

    def insert_gap(self, position: Timecode, duration_frames: int, track_number: int = 1) -> bool:
        """
        Insert a gap at position, pushing subsequent clips later.

        Args:
            position: Position to insert gap
            duration_frames: Gap duration in frames
            track_number: Track to affect

        Returns:
            True if successful
        """
        gap_duration = Timecode.from_frames(duration_frames, self.timeline.frame_rate)

        for clip in self.get_all_clips():
            if clip.track == track_number and clip.record_in >= position:
                clip.record_in = clip.record_in + duration_frames
                clip.record_out = clip.record_out + duration_frames

        return True
