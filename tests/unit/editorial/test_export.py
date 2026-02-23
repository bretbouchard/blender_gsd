"""
Tests for lib/editorial/export.py

Comprehensive tests for export formats without Blender (bpy).
"""

import pytest
import tempfile
import os
import json

from lib.editorial.timeline_types import (
    Timeline,
    Clip,
    Track,
    Transition,
    Timecode,
    TransitionType,
    TrackType,
)

from lib.editorial.export import (
    export_edl,
    generate_edl_content,
    _format_edl_timecode,
    export_fcpxml,
    generate_fcpxml_content,
    export_otio,
    generate_otio_content,
    export_aaf,
    _export_aaf_json_fallback,
    generate_cut_list,
    export_cut_list,
    export_timeline,
    export_cut_list as export_cut_list_func,
)


class TestExportEDL:
    """Tests for EDL export."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        timeline = Timeline(name="Test Sequence", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip1 = Clip(
            name="Shot_001",
            source_path="/media/clip1.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100),
            scene=1,
            take=1,
            notes="First shot"
        )
        clip2 = Clip(
            name="Shot_002",
            source_path="/media/clip2.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(150),
            record_in=Timecode.from_frames(100),
            record_out=Timecode.from_frames(250),
            scene=1,
            take=2
        )

        track.add_clip(clip1)
        track.add_clip(clip2)

        return timeline

    def test_export_edl_to_file(self, sample_timeline):
        """Test exporting EDL to file."""
        with tempfile.NamedTemporaryFile(suffix='.edl', delete=False) as f:
            temp_path = f.name

        try:
            result = export_edl(sample_timeline, temp_path)
            assert result is True
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                content = f.read()
            assert "TITLE: Test Sequence" in content
        finally:
            os.unlink(temp_path)

    def test_export_edl_invalid_path(self, sample_timeline):
        """Test exporting to invalid path."""
        result = export_edl(sample_timeline, "/nonexistent/directory/file.edl")
        assert result is False

    def test_generate_edl_content(self, sample_timeline):
        """Test generating EDL content."""
        content = generate_edl_content(sample_timeline)
        assert "TITLE: Test Sequence" in content
        assert "FCM: NON-DROP FRAME" in content

    def test_format_edl_timecode(self):
        """Test EDL timecode formatting."""
        tc = Timecode(hours=1, minutes=30, seconds=45, frames=12)
        result = _format_edl_timecode(tc)
        assert result == "01 30 45 12"

    def test_edl_includes_clip_names(self, sample_timeline):
        """Test that EDL includes clip source paths."""
        content = generate_edl_content(sample_timeline)
        assert "/media/clip1.mp4" in content
        assert "/media/clip2.mp4" in content

    def test_edl_includes_notes(self, sample_timeline):
        """Test that EDL includes clip notes."""
        content = generate_edl_content(sample_timeline)
        assert "First shot" in content


class TestExportFCPXML:
    """Tests for FCPXML export."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        timeline = Timeline(name="FCPXML Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Shot_001",
            source_path="/media/clip.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100)
        )
        track.add_clip(clip)

        return timeline

    def test_export_fcpxml_to_file(self, sample_timeline):
        """Test exporting FCPXML to file."""
        with tempfile.NamedTemporaryFile(suffix='.fcpxml', delete=False) as f:
            temp_path = f.name

        try:
            result = export_fcpxml(sample_timeline, temp_path)
            assert result is True
            assert os.path.exists(temp_path)
        finally:
            os.unlink(temp_path)

    def test_generate_fcpxml_content(self, sample_timeline):
        """Test generating FCPXML content."""
        content = generate_fcpxml_content(sample_timeline)
        assert '<?xml version="1.0"' in content
        assert '<!DOCTYPE fcpxml>' in content
        assert '<fcpxml version="1.9">' in content

    def test_fcpxml_has_resources(self, sample_timeline):
        """Test that FCPXML has resources section."""
        content = generate_fcpxml_content(sample_timeline)
        assert '<resources>' in content
        assert '<format' in content

    def test_fcpxml_has_sequence(self, sample_timeline):
        """Test that FCPXML has sequence."""
        content = generate_fcpxml_content(sample_timeline)
        assert '<sequence' in content
        assert '<spine>' in content

    def test_fcpxml_includes_clips(self, sample_timeline):
        """Test that FCPXML includes clips."""
        content = generate_fcpxml_content(sample_timeline)
        assert '<clip name="Shot_001"' in content


class TestExportOTIO:
    """Tests for OTIO export."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        timeline = Timeline(name="OTIO Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        clip = Clip(
            name="Shot_001",
            source_path="/media/clip.mp4",
            source_in=Timecode.from_frames(0),
            source_out=Timecode.from_frames(100),
            record_in=Timecode.from_frames(0),
            record_out=Timecode.from_frames(100),
            scene=1,
            take=1,
            notes="Test note"
        )
        track.add_clip(clip)

        return timeline

    def test_export_otio_to_file(self, sample_timeline):
        """Test exporting OTIO to file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_otio(sample_timeline, temp_path)
            assert result is True
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert data["OTIO_SCHEMA"] == "Timeline.1"
        finally:
            os.unlink(temp_path)

    def test_generate_otio_content(self, sample_timeline):
        """Test generating OTIO content."""
        content = generate_otio_content(sample_timeline)
        assert content["OTIO_SCHEMA"] == "Timeline.1"
        assert content["name"] == "OTIO Test"

    def test_otio_has_tracks(self, sample_timeline):
        """Test that OTIO has tracks."""
        content = generate_otio_content(sample_timeline)
        assert "tracks" in content
        assert "children" in content["tracks"]

    def test_otio_has_clips(self, sample_timeline):
        """Test that OTIO includes clips."""
        content = generate_otio_content(sample_timeline)
        track = content["tracks"]["children"][0]
        assert len(track["children"]) == 1
        assert track["children"][0]["name"] == "Shot_001"

    def test_otio_has_metadata(self, sample_timeline):
        """Test that OTIO has metadata."""
        content = generate_otio_content(sample_timeline)
        assert "metadata" in content
        assert content["metadata"]["exporter"] == "blender_gsd"


class TestExportAAF:
    """Tests for AAF export."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        timeline = Timeline(name="AAF Test")
        track = timeline.add_video_track("V1")
        clip = Clip(name="Shot_001")
        track.add_clip(clip)
        return timeline

    def test_export_aaf_fallback(self, sample_timeline):
        """Test AAF export falls back to JSON."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_aaf(sample_timeline, temp_path)
            assert result is True

            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert data["format"] == "AAF"
        finally:
            os.unlink(temp_path)


class TestGenerateCutList:
    """Tests for cut list generation."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        timeline = Timeline(name="Cut List Test", frame_rate=24.0)
        track = timeline.add_video_track("V1")

        for i in range(3):
            clip = Clip(
                name=f"Shot_{i + 1:03d}",
                source_path=f"/media/clip{i + 1}.mp4",
                source_in=Timecode.from_frames(0),
                source_out=Timecode.from_frames(100),
                record_in=Timecode.from_frames(i * 100),
                record_out=Timecode.from_frames((i + 1) * 100),
                scene=1,
                take=i + 1
            )
            track.add_clip(clip)

        return timeline

    def test_generate_cut_list(self, sample_timeline):
        """Test generating cut list."""
        cut_list = generate_cut_list(sample_timeline)
        assert len(cut_list) == 3

    def test_cut_list_entries(self, sample_timeline):
        """Test cut list entry content."""
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

    def test_cut_list_edit_numbers(self, sample_timeline):
        """Test that cut list has sequential edit numbers."""
        cut_list = generate_cut_list(sample_timeline)
        for i, entry in enumerate(cut_list):
            assert entry["edit_number"] == i + 1

    def test_export_cut_list_to_file(self, sample_timeline):
        """Test exporting cut list to file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_cut_list(sample_timeline, temp_path)
            assert result is True
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 3
        finally:
            os.unlink(temp_path)


class TestExportTimeline:
    """Tests for generic export_timeline function."""

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample timeline for testing."""
        timeline = Timeline(name="Generic Export Test")
        track = timeline.add_video_track("V1")
        clip = Clip(name="Shot_001")
        track.add_clip(clip)
        return timeline

    def test_export_timeline_edl(self, sample_timeline):
        """Test exporting as EDL."""
        with tempfile.NamedTemporaryFile(suffix='.edl', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="edl")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_fcpxml(self, sample_timeline):
        """Test exporting as FCPXML."""
        with tempfile.NamedTemporaryFile(suffix='.fcpxml', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="fcpxml")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_xml_alias(self, sample_timeline):
        """Test exporting with xml alias."""
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="xml")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_otio(self, sample_timeline):
        """Test exporting as OTIO."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="otio")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_json_alias(self, sample_timeline):
        """Test exporting with json alias."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="json")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_aaf(self, sample_timeline):
        """Test exporting as AAF."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="aaf")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_cutlist(self, sample_timeline):
        """Test exporting as cut list."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = export_timeline(sample_timeline, temp_path, format="cutlist")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_timeline_unknown_format(self, sample_timeline):
        """Test exporting with unknown format."""
        result = export_timeline(sample_timeline, "/tmp/test.xyz", format="unknown")
        assert result is False


class TestExportEdgeCases:
    """Tests for edge cases in export."""

    def test_export_empty_timeline(self):
        """Test exporting empty timeline."""
        timeline = Timeline(name="Empty")

        with tempfile.NamedTemporaryFile(suffix='.edl', delete=False) as f:
            temp_path = f.name

        try:
            result = export_edl(timeline, temp_path)
            assert result is True

            with open(temp_path, 'r') as f:
                content = f.read()
            assert "TITLE: Empty" in content
        finally:
            os.unlink(temp_path)

    def test_export_timeline_with_special_characters(self):
        """Test exporting timeline with special characters in name."""
        timeline = Timeline(name="Test & Special <Characters>")
        track = timeline.add_video_track("V1")

        content = generate_edl_content(timeline)
        assert "Test & Special <Characters>" in content

    def test_export_timeline_with_multiple_tracks(self):
        """Test exporting timeline with multiple tracks."""
        timeline = Timeline(name="Multi Track")
        v1 = timeline.add_video_track("V1")
        v2 = timeline.add_video_track("V2")
        a1 = timeline.add_audio_track("A1")

        v1.add_clip(Clip(name="V1_Clip"))
        v2.add_clip(Clip(name="V2_Clip"))
        a1.add_clip(Clip(name="A1_Clip"))

        cut_list = generate_cut_list(timeline)
        assert len(cut_list) == 3

    def test_export_timeline_with_transitions(self):
        """Test exporting timeline with transitions."""
        timeline = Timeline(name="With Transitions")
        track = timeline.add_video_track("V1")

        clip1 = Clip(name="A")
        clip2 = Clip(name="B")
        track.add_clip(clip1)
        track.add_clip(clip2)

        trans = Transition(type=TransitionType.DISSOLVE, from_clip="A", to_clip="B")
        timeline.transitions.append(trans)

        # Export should succeed
        with tempfile.NamedTemporaryFile(suffix='.edl', delete=False) as f:
            temp_path = f.name

        try:
            result = export_edl(timeline, temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_export_with_long_clip_names(self):
        """Test exporting with very long clip names."""
        timeline = Timeline(name="Long Names")
        track = timeline.add_video_track("V1")

        long_name = "A" * 100
        clip = Clip(name=long_name)
        track.add_clip(clip)

        # Should not crash
        content = generate_edl_content(timeline)
        assert content is not None
