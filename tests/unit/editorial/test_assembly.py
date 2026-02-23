"""
Tests for lib/editorial/assembly.py

Comprehensive tests for assembly functions without Blender (bpy).
"""

import pytest

from lib.editorial.timeline_types import (
    Timeline,
    Clip,
    Track,
    Timecode,
    Transition,
    TransitionType,
    TrackType,
    Marker,
)

from lib.editorial.assembly import (
    assemble_from_shot_list,
    auto_sequence_clips,
    conform_timeline,
    create_sequence_from_scenes,
    calculate_total_runtime,
    calculate_runtime_formatted,
    calculate_runtime_frames,
    calculate_runtime_timecode,
    generate_cut_list,
    fill_gaps,
    remove_gaps,
    get_timeline_statistics,
)


class TestAssembleFromShotList:
    """Tests for assemble_from_shot_list function."""

    @pytest.fixture
    def sample_shots(self):
        """Sample shot list."""
        return [
            {
                "name": "Shot_001",
                "source_path": "/media/clip1.mp4",
                "source_in": 0,
                "source_out": 100,
                "scene": 1,
                "take": 1,
                "notes": "Opening shot",
            },
            {
                "name": "Shot_002",
                "source_path": "/media/clip2.mp4",
                "source_in": 50,
                "source_out": 200,
                "scene": 1,
                "take": 2,
            },
            {
                "name": "Shot_003",
                "source_path": "/media/clip3.mp4",
                "source_in": 0,
                "source_out": 150,
                "scene": 2,
                "take": 1,
            },
        ]

    def test_assemble_basic(self, sample_shots):
        """Test basic assembly from shot list."""
        timeline = assemble_from_shot_list(sample_shots)
        assert timeline is not None
        assert timeline.name == "Sequence"
        assert len(timeline.video_tracks) == 1

    def test_assemble_custom_name(self, sample_shots):
        """Test assembly with custom timeline name."""
        timeline = assemble_from_shot_list(sample_shots, timeline_name="My Edit")
        assert timeline.name == "My Edit"

    def test_assemble_custom_frame_rate(self, sample_shots):
        """Test assembly with custom frame rate."""
        timeline = assemble_from_shot_list(sample_shots, frame_rate=30.0)
        assert timeline.frame_rate == 30.0

    def test_assemble_creates_clips(self, sample_shots):
        """Test that assembly creates correct number of clips."""
        timeline = assemble_from_shot_list(sample_shots)
        clips = timeline.get_all_clips()
        assert len(clips) == 3

    def test_assemble_clip_names(self, sample_shots):
        """Test that clips have correct names."""
        timeline = assemble_from_shot_list(sample_shots)
        clips = timeline.get_all_clips()
        assert clips[0].name == "Shot_001"
        assert clips[1].name == "Shot_002"
        assert clips[2].name == "Shot_003"

    def test_assemble_clip_timing(self, sample_shots):
        """Test that clips have correct timing."""
        timeline = assemble_from_shot_list(sample_shots)
        clips = timeline.get_all_clips()

        # First clip: 0-100
        assert clips[0].record_in.to_frames() == 0
        assert clips[0].record_out.to_frames() == 100

        # Second clip: 100-250 (150 frames)
        assert clips[1].record_in.to_frames() == 100
        assert clips[1].record_out.to_frames() == 250

        # Third clip: 250-400 (150 frames)
        assert clips[2].record_in.to_frames() == 250
        assert clips[2].record_out.to_frames() == 400

    def test_assemble_clip_metadata(self, sample_shots):
        """Test that clips have correct metadata."""
        timeline = assemble_from_shot_list(sample_shots)
        clips = timeline.get_all_clips()

        assert clips[0].source_path == "/media/clip1.mp4"
        assert clips[0].scene == 1
        assert clips[0].take == 1
        assert clips[0].notes == "Opening shot"

        assert clips[1].scene == 1
        assert clips[1].take == 2
        assert clips[1].notes == ""

    def test_assemble_with_dissolve_transition(self, sample_shots):
        """Test assembly with dissolve transitions."""
        timeline = assemble_from_shot_list(
            sample_shots, transition_type="dissolve", transition_duration=12
        )

        # Should have dissolve transitions between clips
        assert len(timeline.transitions) == 2  # Between 3 clips
        for trans in timeline.transitions:
            assert trans.type == TransitionType.DISSOLVE
            assert trans.duration == 12

    def test_assemble_with_cut_transition(self, sample_shots):
        """Test assembly with cut transitions (default)."""
        timeline = assemble_from_shot_list(sample_shots, transition_type="cut")

        # No transitions for cuts
        assert len(timeline.transitions) == 0

    def test_assemble_empty_shot_list(self):
        """Test assembly with empty shot list."""
        timeline = assemble_from_shot_list([])
        assert timeline is not None
        assert len(timeline.get_all_clips()) == 0

    def test_assemble_auto_names(self):
        """Test that clips get auto-generated names."""
        shots = [
            {"source_path": "/a.mp4", "source_in": 0, "source_out": 24},
            {"source_path": "/b.mp4", "source_in": 0, "source_out": 24},
        ]
        timeline = assemble_from_shot_list(shots)
        clips = timeline.get_all_clips()

        assert clips[0].name == "Shot_001"
        assert clips[1].name == "Shot_002"

    def test_assemble_default_values(self):
        """Test assembly with minimal shot data."""
        shots = [{"name": "Minimal"}]
        timeline = assemble_from_shot_list(shots)
        clips = timeline.get_all_clips()

        assert clips[0].source_path == ""
        assert clips[0].scene == 0
        assert clips[0].take == 1
        assert clips[0].notes == ""


class TestAutoSequenceClips:
    """Tests for auto_sequence_clips function."""

    def test_auto_sequence_basic(self):
        """Test basic auto-sequencing."""
        paths = ["/media/shot1.mp4", "/media/shot2.mp4", "/media/shot3.mp4"]
        timeline = auto_sequence_clips(paths)

        assert timeline is not None
        assert timeline.name == "Auto Sequence"
        assert len(timeline.get_all_clips()) == 3

    def test_auto_sequence_custom_name(self):
        """Test auto-sequencing with custom name."""
        paths = ["/media/a.mp4"]
        timeline = auto_sequence_clips(paths, timeline_name="Custom")
        assert timeline.name == "Custom"

    def test_auto_sequence_custom_frame_rate(self):
        """Test auto-sequencing with custom frame rate."""
        paths = ["/media/a.mp4"]
        timeline = auto_sequence_clips(paths, frame_rate=30.0)
        assert timeline.frame_rate == 30.0

    def test_auto_sequence_default_duration(self):
        """Test auto-sequencing with default duration."""
        paths = ["/media/a.mp4", "/media/b.mp4"]
        timeline = auto_sequence_clips(paths, default_duration=100)

        clips = timeline.get_all_clips()
        assert clips[0].duration == 100
        assert clips[1].duration == 100

    def test_auto_sequence_timing(self):
        """Test that auto-sequenced clips are properly timed."""
        paths = ["/media/a.mp4", "/media/b.mp4", "/media/c.mp4"]
        timeline = auto_sequence_clips(paths, default_duration=72)

        clips = timeline.get_all_clips()
        assert clips[0].record_in.to_frames() == 0
        assert clips[0].record_out.to_frames() == 72
        assert clips[1].record_in.to_frames() == 72
        assert clips[1].record_out.to_frames() == 144
        assert clips[2].record_in.to_frames() == 144
        assert clips[2].record_out.to_frames() == 216

    def test_auto_sequence_clip_names_from_paths(self):
        """Test that clip names are derived from file paths."""
        paths = ["/media/MyShot001.mp4", "/media/Another_Shot.mov"]
        timeline = auto_sequence_clips(paths)

        clips = timeline.get_all_clips()
        assert clips[0].name == "MyShot001"
        assert clips[1].name == "Another_Shot"

    def test_auto_sequence_empty_paths(self):
        """Test auto-sequencing with empty path list."""
        timeline = auto_sequence_clips([])
        assert len(timeline.get_all_clips()) == 0

    def test_auto_sequence_preserves_source_paths(self):
        """Test that source paths are preserved."""
        paths = ["/path/to/clip.mp4"]
        timeline = auto_sequence_clips(paths)

        clips = timeline.get_all_clips()
        assert clips[0].source_path == "/path/to/clip.mp4"


class TestConformTimeline:
    """Tests for conform_timeline function."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline."""
        timeline = Timeline(name="Offline Edit")
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="Shot_A",
            source_path="/offline/shot_a_low.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
        )
        clip2 = Clip(
            name="Shot_B",
            source_path="/offline/shot_b_low.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        return timeline

    def test_conform_basic(self, sample_timeline):
        """Test basic conforming."""
        new_sources = {
            "Shot_A": "/online/shot_a_high.mp4",
            "Shot_B": "/online/shot_b_high.mp4",
        }

        conformed = conform_timeline(sample_timeline, new_sources)

        assert conformed is not None
        clips = conformed.get_all_clips()
        assert clips[0].source_path == "/online/shot_a_high.mp4"
        assert clips[1].source_path == "/online/shot_b_high.mp4"

    def test_conform_returns_new_instance(self, sample_timeline):
        """Test that conforming returns a new timeline instance."""
        new_sources = {"Shot_A": "/online/shot_a.mp4"}
        conformed = conform_timeline(sample_timeline, new_sources)

        assert conformed is not sample_timeline

    def test_conform_preserves_original(self, sample_timeline):
        """Test that original timeline is not modified."""
        original_path = sample_timeline.get_all_clips()[0].source_path
        new_sources = {"Shot_A": "/online/shot_a.mp4"}

        conform_timeline(sample_timeline, new_sources)

        # Original should be unchanged
        assert sample_timeline.get_all_clips()[0].source_path == original_path

    def test_conform_partial_update(self, sample_timeline):
        """Test conforming with partial source mapping."""
        new_sources = {"Shot_A": "/online/shot_a.mp4"}  # Shot_B not mapped

        conformed = conform_timeline(sample_timeline, new_sources)
        clips = conformed.get_all_clips()

        assert clips[0].source_path == "/online/shot_a.mp4"
        assert clips[1].source_path == "/offline/shot_b_low.mp4"  # Unchanged

    def test_conform_empty_mapping(self, sample_timeline):
        """Test conforming with empty mapping."""
        conformed = conform_timeline(sample_timeline, {})

        # All clips should be unchanged
        clips = conformed.get_all_clips()
        assert clips[0].source_path == "/offline/shot_a_low.mp4"
        assert clips[1].source_path == "/offline/shot_b_low.mp4"

    def test_conform_nonexistent_clip(self, sample_timeline):
        """Test conforming with non-existent clip names in mapping."""
        new_sources = {
            "NonExistent": "/online/clip.mp4",
            "Shot_A": "/online/shot_a.mp4",
        }

        conformed = conform_timeline(sample_timeline, new_sources)
        # Should not crash, just ignore non-existent clips
        assert conformed is not None


class TestCreateSequenceFromScenes:
    """Tests for create_sequence_from_scenes function."""

    @pytest.fixture
    def sample_scenes(self):
        """Sample scene data."""
        return [
            {
                "name": "Scene 1",
                "location": "Interior - Office",
                "shots": [
                    {
                        "name": "Wide",
                        "source_path": "/scene1/wide.mp4",
                        "source_in": 0,
                        "source_out": 100,
                        "take": 1,
                    },
                    {
                        "name": "Close-up",
                        "source_path": "/scene1/cu.mp4",
                        "source_in": 0,
                        "source_out": 80,
                        "take": 2,
                    },
                ],
            },
            {
                "name": "Scene 2",
                "location": "Exterior - Street",
                "shots": [
                    {
                        "name": "Establishing",
                        "source_path": "/scene2/est.mp4",
                        "source_in": 0,
                        "source_out": 150,
                        "take": 1,
                    }
                ],
            },
        ]

    def test_create_from_scenes_basic(self, sample_scenes):
        """Test basic creation from scenes."""
        timeline = create_sequence_from_scenes(sample_scenes)

        assert timeline is not None
        assert timeline.name == "Scene Sequence"

    def test_create_from_scenes_creates_clips(self, sample_scenes):
        """Test that all shots become clips."""
        timeline = create_sequence_from_scenes(sample_scenes)
        clips = timeline.get_all_clips()

        # 2 shots in scene 1 + 1 shot in scene 2 = 3 clips
        assert len(clips) == 3

    def test_create_from_scenes_custom_frame_rate(self, sample_scenes):
        """Test with custom frame rate."""
        timeline = create_sequence_from_scenes(sample_scenes, frame_rate=25.0)
        assert timeline.frame_rate == 25.0

    def test_create_from_scenes_timing(self, sample_scenes):
        """Test that clips are properly sequenced."""
        timeline = create_sequence_from_scenes(sample_scenes)
        clips = timeline.get_all_clips()

        # Scene 1: 100 + 80 = 180 frames
        assert clips[0].record_in.to_frames() == 0
        assert clips[0].record_out.to_frames() == 100
        assert clips[1].record_in.to_frames() == 100
        assert clips[1].record_out.to_frames() == 180

        # Scene 2 starts at 180
        assert clips[2].record_in.to_frames() == 180
        assert clips[2].record_out.to_frames() == 330

    def test_create_from_scenes_empty(self):
        """Test with empty scenes list."""
        timeline = create_sequence_from_scenes([])
        assert len(timeline.get_all_clips()) == 0

    def test_create_from_scenes_scene_numbers(self, sample_scenes):
        """Test that scene numbers are assigned."""
        timeline = create_sequence_from_scenes(sample_scenes)
        clips = timeline.get_all_clips()

        # First two clips are scene 1
        assert clips[0].scene == 1
        assert clips[1].scene == 1

        # Third clip is scene 2
        assert clips[2].scene == 2

    def test_create_from_scenes_default_duration(self):
        """Test shots with missing source_out get default duration."""
        scenes = [
            {
                "name": "Scene 1",
                "shots": [
                    {
                        "name": "Shot",
                        "source_in": 0,
                        # No source_out - should get default 72 frames
                    }
                ],
            }
        ]

        timeline = create_sequence_from_scenes(scenes)
        clips = timeline.get_all_clips()

        assert clips[0].duration == 72


class TestCalculateTotalRuntime:
    """Tests for calculate_total_runtime function."""

    def test_calculate_runtime_empty(self):
        """Test runtime of empty timeline."""
        timeline = Timeline(name="Empty")
        runtime = calculate_total_runtime(timeline)
        assert runtime == 0.0

    def test_calculate_runtime_single_clip(self):
        """Test runtime with single clip."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(240, 24.0),  # 10 seconds
        )
        track.add_clip(clip)

        runtime = calculate_total_runtime(timeline)
        assert runtime == 10.0

    def test_calculate_runtime_multiple_clips(self):
        """Test runtime with multiple clips."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        # Total: 500 frames = ~20.83 seconds
        for i in range(5):
            clip = Clip(
                name=f"Clip_{i}",
                record_in=Timecode.from_frames(i * 100, 24.0),
                record_out=Timecode.from_frames((i + 1) * 100, 24.0),
            )
            track.add_clip(clip)

        runtime = calculate_total_runtime(timeline)
        assert runtime == pytest.approx(500 / 24.0, rel=0.01)

    def test_calculate_runtime_with_gap(self):
        """Test runtime with gap between clips."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(100, 24.0),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(200, 24.0),  # Gap from 100-200
            record_out=Timecode.from_frames(300, 24.0),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        # Runtime should be 300 frames = 12.5 seconds
        runtime = calculate_total_runtime(timeline)
        assert runtime == pytest.approx(300 / 24.0, rel=0.01)


class TestCalculateRuntimeFormatted:
    """Tests for calculate_runtime_formatted function."""

    def test_formatted_under_minute(self):
        """Test formatted runtime under a minute."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(720, 24.0),  # 30 seconds
        )
        track.add_clip(clip)

        formatted = calculate_runtime_formatted(timeline)
        assert formatted == "0:30"

    def test_formatted_over_minute(self):
        """Test formatted runtime over a minute."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(2880, 24.0),  # 2 minutes
        )
        track.add_clip(clip)

        formatted = calculate_runtime_formatted(timeline)
        assert formatted == "2:00"

    def test_formatted_over_hour(self):
        """Test formatted runtime over an hour."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(108000, 24.0),  # 1:15:00
        )
        track.add_clip(clip)

        formatted = calculate_runtime_formatted(timeline)
        assert formatted == "1:15:00"

    def test_formatted_complex_time(self):
        """Test formatted runtime with complex time."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        # 1 hour, 23 minutes, 45 seconds
        frames = 3600 * 24 + 23 * 60 * 24 + 45 * 24
        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(frames, 24.0),
        )
        track.add_clip(clip)

        formatted = calculate_runtime_formatted(timeline)
        assert formatted == "1:23:45"

    def test_formatted_empty(self):
        """Test formatted runtime of empty timeline."""
        timeline = Timeline(name="Empty")
        formatted = calculate_runtime_formatted(timeline)
        assert formatted == "0:00"


class TestCalculateRuntimeFrames:
    """Tests for calculate_runtime_frames function."""

    def test_frames_empty(self):
        """Test frame count of empty timeline."""
        timeline = Timeline(name="Empty")
        frames = calculate_runtime_frames(timeline)
        assert frames == 0

    def test_frames_single_clip(self):
        """Test frame count with single clip."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(150),
        )
        track.add_clip(clip)

        frames = calculate_runtime_frames(timeline)
        assert frames == 150

    def test_frames_multiple_clips(self):
        """Test frame count with multiple clips."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")

        for i in range(3):
            clip = Clip(
                name=f"Clip_{i}",
                record_in=Timecode.from_frames(i * 50),
                record_out=Timecode.from_frames((i + 1) * 50),
            )
            track.add_clip(clip)

        frames = calculate_runtime_frames(timeline)
        assert frames == 150


class TestCalculateRuntimeTimecode:
    """Tests for calculate_runtime_timecode function."""

    def test_timecode_empty(self):
        """Test timecode of empty timeline."""
        timeline = Timeline(name="Empty")
        tc = calculate_runtime_timecode(timeline)
        assert tc.to_frames() == 0

    def test_timecode_with_content(self):
        """Test timecode with content."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(2400, 24.0),  # 100 seconds
        )
        track.add_clip(clip)

        tc = calculate_runtime_timecode(timeline)
        assert tc.to_frames() == 2400
        assert tc.to_seconds() == 100.0


class TestGenerateCutList:
    """Tests for generate_cut_list function."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="Shot_001",
            source_path="/media/clip1.mp4",
            source_in=Timecode.from_frames(0, 24.0),
            source_out=Timecode.from_frames(100, 24.0),
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(100, 24.0),
            track=1,
            scene=1,
            take=1,
            notes="First",
        )
        clip2 = Clip(
            name="Shot_002",
            source_path="/media/clip2.mp4",
            source_in=Timecode.from_frames(50, 24.0),
            source_out=Timecode.from_frames(200, 24.0),
            record_in=Timecode.from_frames(100, 24.0),
            record_out=Timecode.from_frames(250, 24.0),
            track=1,
            scene=1,
            take=2,
            notes="Second",
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        return timeline

    def test_generate_cut_list_basic(self, sample_timeline):
        """Test basic cut list generation."""
        cut_list = generate_cut_list(sample_timeline)

        assert len(cut_list) == 2

    def test_generate_cut_list_entries(self, sample_timeline):
        """Test cut list entry structure."""
        cut_list = generate_cut_list(sample_timeline)
        entry = cut_list[0]

        assert "edit_number" in entry
        assert "clip_name" in entry
        assert "source_file" in entry
        assert "source_in" in entry
        assert "source_out" in entry
        assert "record_in" in entry
        assert "record_out" in entry
        assert "duration_frames" in entry
        assert "track" in entry
        assert "scene" in entry
        assert "take" in entry
        assert "notes" in entry

    def test_generate_cut_list_values(self, sample_timeline):
        """Test cut list entry values."""
        cut_list = generate_cut_list(sample_timeline)

        assert cut_list[0]["edit_number"] == 1
        assert cut_list[0]["clip_name"] == "Shot_001"
        assert cut_list[0]["source_file"] == "/media/clip1.mp4"
        assert cut_list[0]["source_in_frames"] == 0
        assert cut_list[0]["source_out_frames"] == 100
        assert cut_list[0]["record_in_frames"] == 0
        assert cut_list[0]["record_out_frames"] == 100
        assert cut_list[0]["duration_frames"] == 100
        assert cut_list[0]["scene"] == 1
        assert cut_list[0]["take"] == 1
        assert cut_list[0]["notes"] == "First"

        assert cut_list[1]["edit_number"] == 2
        assert cut_list[1]["clip_name"] == "Shot_002"

    def test_generate_cut_list_empty(self):
        """Test cut list for empty timeline."""
        timeline = Timeline(name="Empty")
        cut_list = generate_cut_list(timeline)

        assert cut_list == []

    def test_generate_cut_list_sequential_numbers(self, sample_timeline):
        """Test that edit numbers are sequential."""
        cut_list = generate_cut_list(sample_timeline)

        for i, entry in enumerate(cut_list):
            assert entry["edit_number"] == i + 1


class TestFillGaps:
    """Tests for fill_gaps function."""

    def test_fill_gaps_no_gaps(self):
        """Test filling timeline without gaps."""
        timeline = Timeline(name="No Gaps")
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(100),
            record_out=Timecode.from_frames(200),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        result = fill_gaps(timeline)
        clips = result.get_all_clips()

        # Should still have 2 clips (no slugs added)
        assert len(clips) == 2

    def test_fill_gaps_with_gap(self):
        """Test filling timeline with gap."""
        timeline = Timeline(name="With Gap", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(100, 24.0),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(150, 24.0),  # Gap from 100-150
            record_out=Timecode.from_frames(250, 24.0),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        result = fill_gaps(timeline)
        clips = result.get_all_clips()

        # Should have 3 clips: A, Slug_001, B
        assert len(clips) == 3
        assert clips[1].name == "Slug_001"
        assert clips[1].duration == 50

    def test_fill_gaps_multiple_gaps(self):
        """Test filling timeline with multiple gaps."""
        timeline = Timeline(name="Multi Gap", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(50, 24.0),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(100, 24.0),  # Gap 50-100
            record_out=Timecode.from_frames(150, 24.0),
        )
        clip3 = Clip(
            name="C",
            record_in=Timecode.from_frames(200, 24.0),  # Gap 150-200
            record_out=Timecode.from_frames(250, 24.0),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)
        track.add_clip(clip3)

        result = fill_gaps(timeline)
        clips = result.get_all_clips()

        # Should have 5 clips: A, Slug_001, B, Slug_002, C
        assert len(clips) == 5
        assert clips[1].name == "Slug_001"
        assert clips[3].name == "Slug_002"

    def test_fill_gaps_returns_same_instance(self):
        """Test that fill_gaps returns modified same timeline."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")

        clip = Clip(name="A", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        track.add_clip(clip)

        result = fill_gaps(timeline)
        assert result is timeline


class TestRemoveGaps:
    """Tests for remove_gaps function."""

    def test_remove_gaps_no_gaps(self):
        """Test removing gaps from timeline without gaps."""
        timeline = Timeline(name="No Gaps")
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(100),
            record_out=Timecode.from_frames(200),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        result = remove_gaps(timeline)
        clips = result.get_all_clips()

        assert len(clips) == 2
        assert clips[0].record_in.to_frames() == 0
        assert clips[1].record_in.to_frames() == 100

    def test_remove_gaps_with_gap(self):
        """Test removing gap from timeline."""
        timeline = Timeline(name="With Gap")
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(150),  # 50 frame gap
            record_out=Timecode.from_frames(250),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        result = remove_gaps(timeline)
        clips = result.get_all_clips()

        # B should now start at 100 (gap closed)
        assert clips[1].record_in.to_frames() == 100
        assert clips[1].record_out.to_frames() == 200

    def test_remove_gaps_multiple_gaps(self):
        """Test removing multiple gaps."""
        timeline = Timeline(name="Multi Gap")
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(50),
        )
        clip2 = Clip(
            name="B",
            record_in=Timecode.from_frames(100),  # 50 frame gap
            record_out=Timecode.from_frames(150),
        )
        clip3 = Clip(
            name="C",
            record_in=Timecode.from_frames(200),  # 50 frame gap
            record_out=Timecode.from_frames(250),
        )

        track.add_clip(clip1)
        track.add_clip(clip2)
        track.add_clip(clip3)

        result = remove_gaps(timeline)
        clips = result.get_all_clips()

        # All clips should be contiguous
        assert clips[0].record_out.to_frames() == clips[1].record_in.to_frames()
        assert clips[1].record_out.to_frames() == clips[2].record_in.to_frames()

    def test_remove_gaps_returns_same_instance(self):
        """Test that remove_gaps returns modified same timeline."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")

        clip = Clip(name="A", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        track.add_clip(clip)

        result = remove_gaps(timeline)
        assert result is timeline


class TestGetTimelineStatistics:
    """Tests for get_timeline_statistics function."""

    def test_statistics_empty(self):
        """Test statistics for empty timeline."""
        timeline = Timeline(name="Empty")
        stats = get_timeline_statistics(timeline)

        assert stats["name"] == "Empty"
        assert stats["clip_count"] == 0
        assert stats["total_frames"] == 0
        assert stats["total_seconds"] == 0.0

    def test_statistics_basic(self):
        """Test basic statistics."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Shot",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(240, 24.0),  # 10 seconds
        )
        track.add_clip(clip)

        stats = get_timeline_statistics(timeline)

        assert stats["name"] == "Test"
        assert stats["frame_rate"] == 24.0
        assert stats["clip_count"] == 1
        assert stats["total_frames"] == 240
        assert stats["total_seconds"] == 10.0

    def test_statistics_fields(self):
        """Test that statistics has all expected fields."""
        timeline = Timeline(name="Test")
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Shot",
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100),
        )
        track.add_clip(clip)

        stats = get_timeline_statistics(timeline)

        required_fields = [
            "name",
            "frame_rate",
            "total_frames",
            "total_seconds",
            "runtime_formatted",
            "clip_count",
            "video_track_count",
            "audio_track_count",
            "transition_count",
            "marker_count",
            "gap_count",
            "clip_frames",
            "gap_frames",
            "fill_percentage",
        ]

        for field in required_fields:
            assert field in stats, f"Missing field: {field}"

    def test_statistics_multiple_tracks(self):
        """Test statistics with multiple tracks."""
        timeline = Timeline(name="Multi")
        v1 = timeline.add_video_track("V1")
        v2 = timeline.add_video_track("V2")
        a1 = timeline.add_audio_track("A1")

        clip = Clip(name="V1_Clip", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        v1.add_clip(clip)

        stats = get_timeline_statistics(timeline)

        assert stats["video_track_count"] == 2
        assert stats["audio_track_count"] == 1
        assert stats["clip_count"] == 1

    def test_statistics_with_transitions(self):
        """Test statistics with transitions."""
        timeline = Timeline(name="With Trans")
        track = timeline.add_video_track("V1")

        clip1 = Clip(name="A", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(100))
        clip2 = Clip(name="B", record_in=Timecode.from_frames(100), record_out=Timecode.from_frames(200))
        track.add_clip(clip1)
        track.add_clip(clip2)

        trans = Transition(type=TransitionType.DISSOLVE)
        timeline.transitions.append(trans)

        stats = get_timeline_statistics(timeline)

        assert stats["transition_count"] == 1

    def test_statistics_with_gaps(self):
        """Test statistics with gaps."""
        timeline = Timeline(name="With Gaps")
        track = timeline.add_video_track("V1")

        clip1 = Clip(name="A", record_in=Timecode.from_frames(0), record_out=Timecode.from_frames(50))
        clip2 = Clip(name="B", record_in=Timecode.from_frames(100), record_out=Timecode.from_frames(150))
        track.add_clip(clip1)
        track.add_clip(clip2)

        stats = get_timeline_statistics(timeline)

        assert stats["gap_count"] == 1
        assert stats["gap_frames"] == 50

    def test_statistics_fill_percentage(self):
        """Test fill percentage calculation."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        # 50 frames of content, 50 frame gap = 50% fill
        # Need to set both source timing (for duration) and record timing
        clip1 = Clip(
            name="A",
            source_in=Timecode.from_frames(0, 24.0),
            source_out=Timecode.from_frames(50, 24.0),
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(50, 24.0),
        )
        clip2 = Clip(
            name="B",
            source_in=Timecode.from_frames(0, 24.0),
            source_out=Timecode.from_frames(50, 24.0),
            record_in=Timecode.from_frames(100, 24.0),
            record_out=Timecode.from_frames(150, 24.0),
        )
        track.add_clip(clip1)
        track.add_clip(clip2)

        stats = get_timeline_statistics(timeline)

        # 100 clip frames / 150 total frames
        assert stats["fill_percentage"] == pytest.approx(100 / 150 * 100, rel=0.01)

    def test_statistics_fill_percentage_no_gaps(self):
        """Test fill percentage with no gaps (100%)."""
        timeline = Timeline(name="No Gaps", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="A",
            source_in=Timecode.from_frames(0, 24.0),
            source_out=Timecode.from_frames(100, 24.0),
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(100, 24.0),
        )
        clip2 = Clip(
            name="B",
            source_in=Timecode.from_frames(0, 24.0),
            source_out=Timecode.from_frames(100, 24.0),
            record_in=Timecode.from_frames(100, 24.0),
            record_out=Timecode.from_frames(200, 24.0),
        )
        track.add_clip(clip1)
        track.add_clip(clip2)

        stats = get_timeline_statistics(timeline)

        assert stats["fill_percentage"] == 100.0

    def test_statistics_fill_percentage_empty(self):
        """Test fill percentage for empty timeline."""
        timeline = Timeline(name="Empty")
        stats = get_timeline_statistics(timeline)

        # Empty timeline should be 100% (no gaps)
        assert stats["fill_percentage"] == 100.0


class TestAssemblyEdgeCases:
    """Tests for edge cases in assembly functions."""

    def test_assemble_single_shot(self):
        """Test assembly with single shot."""
        shots = [{"name": "Only", "source_in": 0, "source_out": 100}]
        timeline = assemble_from_shot_list(shots)

        clips = timeline.get_all_clips()
        assert len(clips) == 1
        assert clips[0].record_in.to_frames() == 0
        assert clips[0].record_out.to_frames() == 100

    def test_assemble_zero_duration_shot(self):
        """Test assembly with zero duration shot."""
        shots = [{"name": "Zero", "source_in": 50, "source_out": 50}]
        timeline = assemble_from_shot_list(shots)

        clips = timeline.get_all_clips()
        assert clips[0].duration == 0

    def test_auto_sequence_special_path(self):
        """Test auto-sequencing with special path characters."""
        paths = ["/path/with spaces/clip name.mp4"]
        timeline = auto_sequence_clips(paths)

        clips = timeline.get_all_clips()
        assert clips[0].name == "clip name"

    def test_runtime_with_fractional_seconds(self):
        """Test runtime calculation with fractional seconds."""
        timeline = Timeline(name="Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        # 125 frames at 24fps = 5.2083... seconds
        clip = Clip(
            name="Test",
            record_in=Timecode.from_frames(0, 24.0),
            record_out=Timecode.from_frames(125, 24.0),
        )
        track.add_clip(clip)

        runtime = calculate_total_runtime(timeline)
        assert runtime == pytest.approx(125 / 24.0, rel=0.001)
