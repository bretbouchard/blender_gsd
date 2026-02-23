"""
Tests for lib/editorial/timeline_manager.py

Comprehensive tests for TimelineManager without Blender (bpy).
"""

import pytest

from lib.editorial.timeline_types import (
    Timeline,
    Track,
    Clip,
    Transition,
    Timecode,
    TransitionType,
    TrackType,
)
from lib.editorial.timeline_manager import TimelineManager


class TestTimelineManagerInit:
    """Tests for TimelineManager initialization."""

    def test_create_manager(self):
        """Test creating a manager."""
        timeline = Timeline(name="Test")
        manager = TimelineManager(timeline)
        assert manager.timeline == timeline

    def test_manager_has_undo_stack(self):
        """Test that manager has undo stack."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        assert manager._undo_stack == []

    def test_manager_has_redo_stack(self):
        """Test that manager has redo stack."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        assert manager._redo_stack == []


class TestTimelineManagerUndo:
    """Tests for undo/redo functionality."""

    def test_save_state(self):
        """Test saving state."""
        timeline = Timeline(name="Original")
        manager = TimelineManager(timeline)
        manager.save_state()
        assert len(manager._undo_stack) == 1

    def test_undo(self):
        """Test undo operation."""
        timeline = Timeline(name="Original")
        manager = TimelineManager(timeline)

        manager.save_state()
        timeline.name = "Modified"

        result = manager.undo()
        assert result is True
        # Note: undo() creates a NEW Timeline object, so we check manager.timeline
        # not the original timeline reference
        assert manager.timeline.name == "Original"

    def test_undo_empty_stack(self):
        """Test undo with empty stack."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        result = manager.undo()
        assert result is False

    def test_redo(self):
        """Test redo operation."""
        timeline = Timeline(name="Original")
        manager = TimelineManager(timeline)

        manager.save_state()
        timeline.name = "Modified"
        manager.undo()

        result = manager.redo()
        assert result is True
        assert timeline.name == "Modified"

    def test_redo_empty_stack(self):
        """Test redo with empty stack."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        result = manager.redo()
        assert result is False

    def test_undo_redo_clears_redo(self):
        """Test that new action clears redo stack."""
        timeline = Timeline(name="Original")
        manager = TimelineManager(timeline)

        manager.save_state()
        timeline.name = "Modified1"
        manager.save_state()

        manager.undo()  # Redo stack now has 1 item

        # New save should clear redo stack
        timeline.name = "New"
        manager.save_state()

        assert len(manager._redo_stack) == 0


class TestTimelineManagerTracks:
    """Tests for track operations."""

    def test_add_video_track(self):
        """Test adding video track."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        track = manager.add_video_track("V1")
        assert len(timeline.video_tracks) == 1
        assert track.name == "V1"

    def test_add_audio_track(self):
        """Test adding audio track."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        track = manager.add_audio_track("A1")
        assert len(timeline.audio_tracks) == 1
        assert track.name == "A1"

    def test_remove_track(self):
        """Test removing track."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        manager.add_video_track("V1")
        manager.add_video_track("V2")

        result = manager.remove_track(1, TrackType.VIDEO)
        assert result is True
        assert len(timeline.video_tracks) == 1

    def test_remove_track_not_found(self):
        """Test removing non-existent track."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        result = manager.remove_track(99, TrackType.VIDEO)
        assert result is False

    def test_get_track(self):
        """Test getting track by number."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        track = manager.add_video_track("V1")

        result = manager.get_track(1, TrackType.VIDEO)
        assert result == track

    def test_get_track_not_found(self):
        """Test getting non-existent track."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        result = manager.get_track(99, TrackType.VIDEO)
        assert result is None


class TestTimelineManagerClips:
    """Tests for clip operations."""

    def test_add_clip(self):
        """Test adding clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(name="Test")
        result = manager.add_clip(clip, track_number=1)
        assert result is True
        assert len(timeline.get_all_clips()) == 1

    def test_add_clip_creates_track(self):
        """Test adding clip creates track if needed."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(name="Test")
        manager.add_clip(clip, track_number=1)

        assert len(timeline.video_tracks) == 1

    def test_remove_clip(self):
        """Test removing clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(name="Test")
        manager.add_clip(clip)

        result = manager.remove_clip("Test")
        assert result is True
        assert len(timeline.get_all_clips()) == 0

    def test_remove_clip_not_found(self):
        """Test removing non-existent clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)
        result = manager.remove_clip("NonExistent")
        assert result is False

    def test_move_clip(self):
        """Test moving clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        manager.move_clip("Test", Timecode.from_frames(50))
        assert clip.record_in.to_frames() == 50
        assert clip.record_out.to_frames() == 150

    def test_move_clip_locked(self):
        """Test moving locked clip fails."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(name="Test", locked=True)
        manager.add_clip(clip)

        result = manager.move_clip("Test", Timecode.from_frames(50))
        assert result is False

    def test_trim_clip_in(self):
        """Test trimming clip in point."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.trim_clip_in("Test", Timecode.from_frames(10))
        assert result is True
        assert clip.source_in.to_frames() == 10

    def test_trim_clip_in_beyond_out(self):
        """Test trimming in point beyond out point fails."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.trim_clip_in("Test", Timecode.from_frames(200))
        assert result is False

    def test_trim_clip_out(self):
        """Test trimming clip out point."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.trim_clip_out("Test", Timecode.from_frames(50))
        assert result is True
        assert clip.source_out.to_frames() == 50
        assert clip.record_out.to_frames() == 50

    def test_slip_clip(self):
        """Test slipping clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(100),
            source_out=Timecode.from_frames(200)
        )
        manager.add_clip(clip)

        result = manager.slip_clip("Test", 50)
        assert result is True
        assert clip.source_in.to_frames() == 150
        assert clip.source_out.to_frames() == 250

    def test_slip_clip_negative(self):
        """Test slipping clip negative."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(100),
            source_out=Timecode.from_frames(200)
        )
        manager.add_clip(clip)

        result = manager.slip_clip("Test", -50)
        assert result is True
        assert clip.source_in.to_frames() == 50
        assert clip.source_out.to_frames() == 150

    def test_slide_clip(self):
        """Test sliding clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.slide_clip("Test", 50)
        assert result is True
        assert clip.record_in.to_frames() == 50

    def test_split_clip(self):
        """Test splitting clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.split_clip("Test", Timecode.from_frames(50))
        assert result is not None
        left, right = result
        assert left.name == "Test_L"
        assert right.name == "Test_R"
        assert left.record_out.to_frames() == 50
        assert right.record_in.to_frames() == 50

    def test_split_clip_at_boundary(self):
        """Test splitting clip at boundary fails."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        # At start
        result = manager.split_clip("Test", Timecode.from_frames(0))
        assert result is None

        # At end
        result = manager.split_clip("Test", Timecode.from_frames(100))
        assert result is None


class TestTimelineManagerTransitions:
    """Tests for transition operations."""

    def test_add_transition(self):
        """Test adding transition."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip1 = Clip(name="A")
        clip2 = Clip(name="B")
        manager.add_clip(clip1)
        manager.add_clip(clip2)

        trans = Transition(type=TransitionType.DISSOLVE, from_clip="A", to_clip="B")
        result = manager.add_transition(trans)
        assert result is True
        assert len(timeline.transitions) == 1

    def test_add_transition_invalid_clip(self):
        """Test adding transition with invalid clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        trans = Transition(type=TransitionType.DISSOLVE, from_clip="NonExistent")
        result = manager.add_transition(trans)
        assert result is False

    def test_remove_transition(self):
        """Test removing transition."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip1 = Clip(name="A")
        clip2 = Clip(name="B")
        manager.add_clip(clip1)
        manager.add_clip(clip2)

        trans = Transition(type=TransitionType.DISSOLVE, from_clip="A", to_clip="B")
        manager.add_transition(trans)

        result = manager.remove_transition("A")
        assert result is True
        assert len(timeline.transitions) == 0

    def test_get_transition_after(self):
        """Test getting transition after clip."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip1 = Clip(name="A")
        clip2 = Clip(name="B")
        manager.add_clip(clip1)
        manager.add_clip(clip2)

        trans = Transition(type=TransitionType.DISSOLVE, from_clip="A", to_clip="B")
        manager.add_transition(trans)

        result = manager.get_transition_after("A")
        assert result == trans


class TestTimelineManagerQueries:
    """Tests for query operations."""

    def test_get_clip_at(self):
        """Test getting clip at position."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.get_clip_at(Timecode.from_frames(50))
        assert result == clip

    def test_get_all_clips(self):
        """Test getting all clips."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        manager.add_clip(Clip(name="A"))
        manager.add_clip(Clip(name="B"))

        clips = manager.get_all_clips()
        assert len(clips) == 2

    def test_calculate_duration(self):
        """Test calculating duration."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        duration = manager.calculate_duration()
        assert duration.to_frames() == 100

    def test_find_gaps(self):
        """Test finding gaps."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(150),
            record_out=Timecode.from_frames(250)
        )
        manager.add_clip(clip1)
        manager.add_clip(clip2)

        gaps = manager.find_gaps()
        assert len(gaps) == 1
        assert gaps[0][0].to_frames() == 100
        assert gaps[0][1].to_frames() == 150

    def test_get_clips_in_range(self):
        """Test getting clips in range."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip1 = Clip(name="A", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        clip2 = Clip(name="B", record_in=Timecode.from_frames(100), record_out=Timecode.from_frames(200))
        clip3 = Clip(name="C", record_in=Timecode.from_frames(200), record_out=Timecode.from_frames(300))

        manager.add_clip(clip1)
        manager.add_clip(clip2)
        manager.add_clip(clip3)

        # Range 50-150 should include clips A and B
        clips = manager.get_clips_in_range(
            Timecode.from_frames(50),
            Timecode.from_frames(150)
        )
        assert len(clips) == 2

    def test_calculate_runtime(self):
        """Test calculating runtime."""
        timeline = Timeline(frame_rate=24.0)
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(240)  # 10 seconds
        )
        manager.add_clip(clip)

        runtime = manager.calculate_runtime()
        assert runtime == 10.0

    def test_calculate_runtime_formatted(self):
        """Test calculating formatted runtime."""
        timeline = Timeline(frame_rate=24.0)
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(2400)  # 100 seconds
        )
        manager.add_clip(clip)

        formatted = manager.calculate_runtime_formatted()
        assert formatted == "1:40"  # 1 minute 40 seconds


class TestTimelineManagerBulkOperations:
    """Tests for bulk operations."""

    def test_ripple_delete(self):
        """Test ripple delete."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip1 = Clip(
            name="A",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        clip2 = Clip(
            name="B",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(100),
            record_out=Timecode.from_frames(200)
        )
        manager.add_clip(clip1)
        manager.add_clip(clip2)

        result = manager.ripple_delete("A")
        assert result is True
        assert len(timeline.get_all_clips()) == 1
        assert clip2.record_in.to_frames() == 0

    def test_ripple_delete_locked(self):
        """Test ripple delete of locked clip fails."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(name="Test", locked=True)
        manager.add_clip(clip)

        result = manager.ripple_delete("Test")
        assert result is False

    def test_insert_gap(self):
        """Test inserting gap."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        manager.add_clip(clip)

        result = manager.insert_gap(Timecode.from_frames(0), 50)
        assert result is True
        assert clip.record_in.to_frames() == 50
        assert clip.record_out.to_frames() == 150

    def test_insert_negative_gap(self):
        """Test inserting negative gap (removing space)."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(100),
            record_out=Timecode.from_frames(200)
        )
        manager.add_clip(clip)

        result = manager.insert_gap(Timecode.from_frames(0), -50)
        assert result is True
        assert clip.record_in.to_frames() == 50


class TestTimelineManagerEdgeCases:
    """Tests for edge cases."""

    def test_operations_on_empty_timeline(self):
        """Test operations on empty timeline."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        assert manager.get_clip_at(Timecode.from_frames(0)) is None
        assert manager.get_all_clips() == []
        assert manager.find_gaps() == []

    def test_clip_not_found_operations(self):
        """Test operations on non-existent clips."""
        timeline = Timeline()
        manager = TimelineManager(timeline)

        assert manager.move_clip("X", Timecode.from_frames(0)) is False
        assert manager.trim_clip_in("X", Timecode.from_frames(0)) is False
        assert manager.trim_clip_out("X", Timecode.from_frames(0)) is False
        assert manager.slip_clip("X", 10) is False
        assert manager.slide_clip("X", 10) is False
        assert manager.split_clip("X", Timecode.from_frames(0)) is None
