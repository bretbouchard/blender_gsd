"""
Tests for lib/editorial/timeline_types.py

Comprehensive tests for timeline types without Blender (bpy).
"""

import pytest

from lib.editorial.timeline_types import (
    TransitionType,
    TrackType,
    Timecode,
    Marker,
    Transition,
    Clip,
    Track,
    Timeline,
)


class TestTransitionType:
    """Tests for TransitionType enum."""

    def test_transition_types_exist(self):
        """Test that expected transition types exist."""
        assert hasattr(TransitionType, 'CUT')
        assert hasattr(TransitionType, 'DISSOLVE')
        assert hasattr(TransitionType, 'WIPE')
        assert hasattr(TransitionType, 'FADE_TO_BLACK')
        assert hasattr(TransitionType, 'FADE_FROM_BLACK')
        assert hasattr(TransitionType, 'DIP_TO_COLOR')

    def test_transition_type_values(self):
        """Test transition type enum values."""
        assert TransitionType.CUT.value == "cut"
        assert TransitionType.DISSOLVE.value == "dissolve"
        assert TransitionType.WIPE.value == "wipe"


class TestTrackType:
    """Tests for TrackType enum."""

    def test_track_types_exist(self):
        """Test that expected track types exist."""
        assert hasattr(TrackType, 'VIDEO')
        assert hasattr(TrackType, 'AUDIO')

    def test_track_type_values(self):
        """Test track type enum values."""
        assert TrackType.VIDEO.value == "video"
        assert TrackType.AUDIO.value == "audio"


class TestTimecodeExtended:
    """Extended tests for Timecode dataclass."""

    def test_from_frames_negative(self):
        """Test creating timecode from negative frames."""
        tc = Timecode.from_frames(-100, frame_rate=24.0)
        assert tc.to_frames() == 0  # Should clamp to 0

    def test_from_seconds_fractional(self):
        """Test creating timecode from fractional seconds."""
        tc = Timecode.from_seconds(1.5, frame_rate=24.0)
        assert tc.to_frames() == 36  # 1.5 * 24

    def test_from_string_drop_frame(self):
        """Test parsing drop-frame timecode."""
        tc = Timecode.from_string("01;00;00;00", frame_rate=29.97)
        assert tc.drop_frame is True

    def test_from_string_invalid_format(self):
        """Test parsing invalid timecode string."""
        with pytest.raises(ValueError):
            Timecode.from_string("invalid", frame_rate=24.0)

    def test_add_with_int(self):
        """Test adding integer frames to timecode."""
        tc = Timecode.from_frames(100, frame_rate=24.0)
        result = tc + 50
        assert result.to_frames() == 150

    def test_subtract_with_int(self):
        """Test subtracting integer frames from timecode."""
        tc = Timecode.from_frames(100, frame_rate=24.0)
        result = tc - 50
        assert result.to_frames() == 50

    def test_subtract_negative_result(self):
        """Test subtraction that would go negative."""
        tc1 = Timecode.from_frames(50, frame_rate=24.0)
        tc2 = Timecode.from_frames(100, frame_rate=24.0)
        result = tc1 - tc2
        assert result.to_frames() == 0  # Should clamp to 0

    def test_repr(self):
        """Test timecode repr."""
        tc = Timecode(hours=1, minutes=30)
        assert "Timecode" in repr(tc)

    def test_to_seconds(self):
        """Test converting to seconds."""
        tc = Timecode.from_frames(240, frame_rate=24.0)
        assert tc.to_seconds() == 10.0

    def test_validation_frames(self):
        """Test frame validation."""
        with pytest.raises(ValueError):
            Timecode(frames=100, frame_rate=24.0)  # Too many frames

    def test_validation_hours(self):
        """Test hours validation."""
        with pytest.raises(ValueError):
            Timecode(hours=-1)

        with pytest.raises(ValueError):
            Timecode(hours=24)

    def test_validation_minutes(self):
        """Test minutes validation."""
        with pytest.raises(ValueError):
            Timecode(minutes=-1)

        with pytest.raises(ValueError):
            Timecode(minutes=60)

    def test_validation_seconds(self):
        """Test seconds validation."""
        with pytest.raises(ValueError):
            Timecode(seconds=-1)

        with pytest.raises(ValueError):
            Timecode(seconds=60)


class TestMarker:
    """Tests for Marker dataclass."""

    def test_create_marker(self):
        """Test creating a marker."""
        tc = Timecode.from_frames(100)
        marker = Marker(name="Scene 1", position=tc)
        assert marker.name == "Scene 1"
        assert marker.position == tc
        assert marker.color == "blue"
        assert marker.note == ""

    def test_marker_with_note(self):
        """Test marker with note."""
        tc = Timecode.from_frames(100)
        marker = Marker(name="Important", position=tc, color="red", note="Check this")
        assert marker.color == "red"
        assert marker.note == "Check this"

    def test_marker_to_dict(self):
        """Test marker serialization."""
        tc = Timecode.from_frames(100)
        marker = Marker(name="Test", position=tc)
        data = marker.to_dict()
        assert data["name"] == "Test"
        assert "position" in data

    def test_marker_from_dict(self):
        """Test marker deserialization."""
        data = {
            "name": "Loaded",
            "position": {"hours": 0, "minutes": 0, "seconds": 4, "frames": 4, "frame_rate": 24.0},
            "color": "green",
            "note": "A note"
        }
        marker = Marker.from_dict(data)
        assert marker.name == "Loaded"
        assert marker.color == "green"
        assert marker.note == "A note"


class TestTransitionExtended:
    """Extended tests for Transition dataclass."""

    def test_create_transition(self):
        """Test creating a transition."""
        trans = Transition(
            type=TransitionType.DISSOLVE,
            duration=12,
            from_clip="Shot_001",
            to_clip="Shot_002"
        )
        assert trans.type == TransitionType.DISSOLVE
        assert trans.duration == 12
        assert trans.from_clip == "Shot_001"
        assert trans.to_clip == "Shot_002"

    def test_transition_from_string_type(self):
        """Test creating transition with string type."""
        trans = Transition(type="dissolve", duration=12)
        assert trans.type == TransitionType.DISSOLVE

    def test_transition_wipe(self):
        """Test wipe transition with direction."""
        trans = Transition(
            type=TransitionType.WIPE,
            duration=12,
            wipe_direction="right"
        )
        assert trans.wipe_direction == "right"

    def test_transition_dip_to_color(self):
        """Test dip to color transition."""
        trans = Transition(
            type=TransitionType.DIP_TO_COLOR,
            duration=24,
            dip_color=(1.0, 0.0, 0.0, 1.0)  # Red
        )
        assert trans.dip_color == (1.0, 0.0, 0.0, 1.0)

    def test_transition_to_dict(self):
        """Test transition serialization."""
        trans = Transition(
            type=TransitionType.DISSOLVE,
            duration=12,
            from_clip="A",
            to_clip="B"
        )
        data = trans.to_dict()
        assert data["type"] == "dissolve"
        assert data["duration"] == 12
        assert data["from_clip"] == "A"
        assert data["to_clip"] == "B"

    def test_transition_from_dict(self):
        """Test transition deserialization."""
        data = {
            "type": "wipe",
            "duration": 24,
            "from_clip": "X",
            "to_clip": "Y",
            "wipe_direction": "up",
            "dip_color": [0.5, 0.5, 0.5, 1.0]
        }
        trans = Transition.from_dict(data)
        assert trans.type == TransitionType.WIPE
        assert trans.wipe_direction == "up"
        assert trans.dip_color == (0.5, 0.5, 0.5, 1.0)


class TestClipExtended:
    """Extended tests for Clip dataclass."""

    def test_clip_duration_property(self):
        """Test clip duration calculation."""
        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(50),
            source_out=Timecode.from_frames(150)
        )
        assert clip.duration == 100

    def test_clip_record_duration_property(self):
        """Test clip record duration calculation."""
        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(200)
        )
        assert clip.record_duration == 200

    def test_clip_auto_record_out(self):
        """Test auto-calculation of record_out."""
        clip = Clip(
            name="Test",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(50)
        )
        # record_out should be auto-calculated in __post_init__
        assert clip.record_out.to_frames() == 150

    def test_clip_metadata(self):
        """Test clip with metadata."""
        clip = Clip(
            name="Shot_001",
            source_path="/media/clip.mp4",
            scene=5,
            take=3,
            notes="Best take",
            enabled=True,
            locked=False
        )
        assert clip.scene == 5
        assert clip.take == 3
        assert clip.notes == "Best take"
        assert clip.enabled is True
        assert clip.locked is False

    def test_clip_to_dict(self):
        """Test clip serialization."""
        clip = Clip(
            name="Test",
            source_path="/path/to/file.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            scene=1,
            take=1
        )
        data = clip.to_dict()
        assert data["name"] == "Test"
        assert data["source_path"] == "/path/to/file.mp4"
        assert data["scene"] == 1

    def test_clip_from_dict(self):
        """Test clip deserialization."""
        data = {
            "name": "Loaded",
            "source_path": "/loaded/file.mp4",
            "source_in": {"hours": 0, "minutes": 0, "seconds": 0, "frames": 0, "frame_rate": 24.0},
            "source_out": {"hours": 0, "minutes": 0, "seconds": 4, "frames": 4, "frame_rate": 24.0},
            "record_in": {"hours": 0, "minutes": 0, "seconds": 0, "frames": 0, "frame_rate": 24.0},
            "record_out": {"hours": 0, "minutes": 0, "seconds": 4, "frames": 4, "frame_rate": 24.0},
            "track": 2,
            "scene": 3,
            "take": 5,
            "notes": "Loaded clip",
            "enabled": False,
            "locked": True
        }
        clip = Clip.from_dict(data)
        assert clip.name == "Loaded"
        assert clip.track == 2
        assert clip.scene == 3
        assert clip.enabled is False
        assert clip.locked is True


class TestTrackExtended:
    """Extended tests for Track dataclass."""

    def test_track_from_string_type(self):
        """Test creating track with string type."""
        track = Track(name="A1", track_type="audio")
        assert track.track_type == TrackType.AUDIO

    def test_track_state(self):
        """Test track state properties."""
        track = Track(
            name="V1",
            track_type=TrackType.VIDEO,
            muted=True,
            locked=True,
            solo=True
        )
        assert track.muted is True
        assert track.locked is True
        assert track.solo is True

    def test_track_add_multiple_clips(self):
        """Test adding multiple clips to track."""
        track = Track(name="V1", track_number=1)
        for i in range(5):
            clip = Clip(
                name=f"Shot_{i:03d}",
                record_in=Timecode.from_frames(i * 100),
                record_out=Timecode.from_frames((i + 1) * 100)
            )
            track.add_clip(clip)
        assert len(track.clips) == 5

    def test_track_clips_sorted_by_record_in(self):
        """Test that clips are sorted by record_in."""
        track = Track(name="V1", track_number=1)
        # Add in non-sequential order
        clip3 = Clip(name="C3", record_in=Timecode.from_frames(200), record_out=Timecode.from_frames(300))
        clip1 = Clip(name="C1", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        clip2 = Clip(name="C2", record_in=Timecode.from_frames(100), record_out=Timecode.from_frames(200))

        track.add_clip(clip3)
        track.add_clip(clip1)
        track.add_clip(clip2)

        # Should be sorted
        assert track.clips[0].name == "C1"
        assert track.clips[1].name == "C2"
        assert track.clips[2].name == "C3"

    def test_track_to_dict(self):
        """Test track serialization."""
        track = Track(name="V1", track_number=1, muted=True)
        track.add_clip(Clip(name="Shot"))
        data = track.to_dict()
        assert data["name"] == "V1"
        assert data["track_type"] == "video"
        assert data["muted"] is True
        assert len(data["clips"]) == 1

    def test_track_from_dict(self):
        """Test track deserialization."""
        data = {
            "name": "A1",
            "track_type": "audio",
            "track_number": 2,
            "clips": [
                {
                    "name": "Audio_001",
                    "source_path": "/audio.wav",
                    "source_in": {"hours": 0, "minutes": 0, "seconds": 0, "frames": 0, "frame_rate": 24.0},
                    "source_out": {"hours": 0, "minutes": 0, "seconds": 4, "frames": 4, "frame_rate": 24.0},
                    "record_in": {"hours": 0, "minutes": 0, "seconds": 0, "frames": 0, "frame_rate": 24.0},
                    "record_out": {"hours": 0, "minutes": 0, "seconds": 4, "frames": 4, "frame_rate": 24.0}
                }
            ],
            "muted": False,
            "locked": True,
            "solo": False
        }
        track = Track.from_dict(data)
        assert track.name == "A1"
        assert track.track_type == TrackType.AUDIO
        assert track.track_number == 2
        assert track.locked is True
        assert len(track.clips) == 1


class TestTimelineExtended:
    """Extended tests for Timeline dataclass."""

    def test_timeline_with_transitions(self):
        """Test timeline with transitions."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")

        clip1 = Clip(name="A", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        clip2 = Clip(name="B", record_in=Timecode.from_frames(100), record_out=Timecode.from_frames(200))

        track.add_clip(clip1)
        track.add_clip(clip2)

        trans = Transition(type=TransitionType.DISSOLVE, duration=12, from_clip="A", to_clip="B")
        timeline.transitions.append(trans)

        assert len(timeline.transitions) == 1

    def test_timeline_with_markers(self):
        """Test timeline with markers."""
        timeline = Timeline(name="Test")
        timeline.add_video_track("V1")

        marker = Marker(name="Chapter 1", position=Timecode.from_frames(100))
        timeline.markers.append(marker)

        assert len(timeline.markers) == 1

    def test_timeline_starting_timecode(self):
        """Test timeline starting timecode."""
        tc = Timecode(hours=1)  # 01:00:00:00
        timeline = Timeline(name="Test", starting_timecode=tc)
        assert timeline.starting_timecode.hours == 1

    def test_timeline_find_gaps_no_track(self):
        """Test finding gaps with no video track 1."""
        timeline = Timeline(name="Test")
        # No tracks added
        gaps = timeline.find_gaps()
        assert gaps == []

    def test_timeline_find_gaps_single_clip(self):
        """Test finding gaps with single clip."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")
        track.add_clip(Clip(
            name="Only",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        ))
        gaps = timeline.find_gaps()
        assert gaps == []

    def test_timeline_get_clip_by_name(self):
        """Test finding clip by name."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")
        clip = Clip(name="Target")
        track.add_clip(clip)

        result = timeline.get_clip_by_name("Target")
        assert result == clip

        result2 = timeline.get_clip_by_name("NonExistent")
        assert result2 is None

    def test_timeline_to_dict_full(self):
        """Test full timeline serialization."""
        timeline = Timeline(name="Full Test", frame_rate=30.0)
        track = timeline.add_video_track("V1")
        track.add_clip(Clip(name="Shot"))

        marker = Marker(name="Mark", position=Timecode.from_frames(50))
        timeline.markers.append(marker)

        trans = Transition(type=TransitionType.CUT)
        timeline.transitions.append(trans)

        data = timeline.to_dict()
        assert data["name"] == "Full Test"
        assert data["frame_rate"] == 30.0
        assert len(data["video_tracks"]) == 1
        assert len(data["markers"]) == 1
        assert len(data["transitions"]) == 1

    def test_timeline_from_dict_full(self):
        """Test full timeline deserialization."""
        data = {
            "name": "Loaded Timeline",
            "frame_rate": 25.0,
            "duration": {"hours": 0, "minutes": 0, "seconds": 4, "frames": 4, "frame_rate": 25.0},
            "video_tracks": [
                {
                    "name": "V1",
                    "track_type": "video",
                    "track_number": 1,
                    "clips": [],
                    "muted": False,
                    "locked": False,
                    "solo": False
                }
            ],
            "audio_tracks": [
                {
                    "name": "A1",
                    "track_type": "audio",
                    "track_number": 1,
                    "clips": [],
                    "muted": False,
                    "locked": False,
                    "solo": False
                }
            ],
            "transitions": [],
            "markers": [],
            "starting_timecode": {"hours": 1, "minutes": 0, "seconds": 0, "frames": 0, "frame_rate": 25.0}
        }
        timeline = Timeline.from_dict(data)
        assert timeline.name == "Loaded Timeline"
        assert timeline.frame_rate == 25.0
        assert len(timeline.video_tracks) == 1
        assert len(timeline.audio_tracks) == 1
        assert timeline.starting_timecode.hours == 1


class TestEdgeCases:
    """Tests for edge cases."""

    def test_timecode_max_values(self):
        """Test timecode with maximum valid values."""
        tc = Timecode(hours=23, minutes=59, seconds=59, frames=23, frame_rate=24.0)
        assert tc.hours == 23
        assert tc.minutes == 59
        assert tc.seconds == 59
        assert tc.frames == 23

    def test_clip_zero_duration(self):
        """Test clip with zero duration."""
        clip = Clip(
            name="Zero",
            source_in=Timecode.from_frames(100),
            source_out=Timecode.from_frames(100)
        )
        assert clip.duration == 0

    def test_track_get_clip_at_boundary(self):
        """Test getting clip at exact boundaries."""
        track = Track(name="V1", track_number=1)
        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        track.add_clip(clip)

        # At start - should be found
        assert track.get_clip_at(Timecode.from_frames(0)) == clip
        # At end - should NOT be found (exclusive)
        assert track.get_clip_at(Timecode.from_frames(100)) is None
        # Middle - should be found
        assert track.get_clip_at(Timecode.from_frames(50)) == clip

    def test_timeline_multiple_tracks_same_number(self):
        """Test adding tracks with explicit numbers."""
        timeline = Timeline()
        track1 = timeline.add_video_track("V1")
        track2 = timeline.add_video_track("V2")

        # Track numbers should auto-increment
        assert track1.track_number == 1
        assert track2.track_number == 2
