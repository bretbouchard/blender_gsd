"""
Tests for lib/editorial/timeline_import.py

Comprehensive tests for import formats without Blender (bpy).
"""

import pytest
import tempfile
import os
import json

from lib.editorial.timeline_types import (
    Timeline,
    Clip,
    Timecode,
)

from lib.editorial.timeline_import import (
    import_edl,
    parse_edl,
    import_fcpxml,
    parse_fcpxml,
    _parse_fcpxml_time,
    import_otio,
    parse_otio,
    _parse_otio_clip,
    import_xml,
    import_timeline,
    detect_format,
)


class TestImportEDL:
    """Tests for EDL import."""

    @pytest.fixture
    def sample_edl_content(self):
        """Sample EDL content."""
        return """TITLE: Test Edit
FCM: NON-DROP FRAME

001
AX       V     C        00 00 00 00 00 00 01 00 00 00 00 00 00 00 01 00
* FROM CLIP NAME: /media/clip1.mp4

002
AX       V     C        00 00 01 00 00 00 02 00 00 00 01 00 00 00 02 00
* FROM CLIP NAME: /media/clip2.mp4

"""

    def test_parse_edl_basic(self, sample_edl_content):
        """Test parsing basic EDL content."""
        timeline = parse_edl(sample_edl_content, frame_rate=24.0)
        assert timeline is not None
        assert timeline.name == "Test Edit"

    def test_parse_edl_no_title(self):
        """Test parsing EDL without title."""
        content = """FCM: NON-DROP FRAME

001
AX       V     C        00 00 00 00 00 00 01 00 00 00 00 00 00 00 01 00
"""
        timeline = parse_edl(content, frame_rate=24.0)
        assert timeline is not None
        assert timeline.name == "Imported Timeline"  # Default

    def test_import_edl_from_file(self, sample_edl_content):
        """Test importing EDL from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as f:
            f.write(sample_edl_content)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_edl(temp_path, frame_rate=24.0)
            assert timeline is not None
            assert timeline.name == "Test Edit"
        finally:
            os.unlink(temp_path)

    def test_import_edl_missing_file(self):
        """Test importing missing EDL file."""
        timeline = import_edl("/nonexistent/file.edl", frame_rate=24.0)
        assert timeline is None

    def test_parse_edl_has_video_track(self, sample_edl_content):
        """Test that parsed EDL has video track."""
        timeline = parse_edl(sample_edl_content, frame_rate=24.0)
        assert len(timeline.video_tracks) >= 1


class TestImportFCPXML:
    """Tests for FCPXML import."""

    @pytest.fixture
    def sample_fcpxml_content(self):
        """Sample FCPXML content."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
    <resources>
        <format id="r1" name="FFVideoFormat24p" frameDuration="1/24s" width="1920" height="1080"/>
    </resources>
    <library>
        <event name="Test Event">
            <project name="Test Project">
                <sequence duration="0s" format="r1">
                    <spine>
                        <clip name="Shot_001" offset="0s" duration="4.167s">
                            <video offset="0s" name="Shot_001">
                                <asset-clip name="clip1" offset="0s" ref="r1" duration="4.167s"/>
                            </video>
                        </clip>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''

    def test_import_fcpxml_from_file(self, sample_fcpxml_content):
        """Test importing FCPXML from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fcpxml', delete=False) as f:
            f.write(sample_fcpxml_content)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_fcpxml(temp_path)
            assert timeline is not None
        finally:
            os.unlink(temp_path)

    def test_import_fcpxml_missing_file(self):
        """Test importing missing FCPXML file."""
        timeline = import_fcpxml("/nonexistent/file.fcpxml")
        assert timeline is None

    def test_parse_fcpxml_time(self):
        """Test parsing FCPXML time string."""
        # "4.167s" should convert to frames
        frames = _parse_fcpxml_time("4.167s", frame_rate=24.0)
        assert frames == 100  # 4.167 * 24 ≈ 100

    def test_parse_fcpxml_time_zero(self):
        """Test parsing zero time."""
        frames = _parse_fcpxml_time("0s", frame_rate=24.0)
        assert frames == 0


class TestImportOTIO:
    """Tests for OTIO import."""

    @pytest.fixture
    def sample_otio_data(self):
        """Sample OTIO data."""
        return {
            "OTIO_SCHEMA": "Timeline.1",
            "name": "OTIO Test",
            "global_start_time": {
                "value": 0,
                "rate": 24.0
            },
            "tracks": {
                "OTIO_SCHEMA": "Stack.1",
                "name": "tracks",
                "children": [
                    {
                        "OTIO_SCHEMA": "Track.1",
                        "name": "V1",
                        "kind": "Video",
                        "source_range": {
                            "start_time": 0,
                            "duration": 100,
                            "rate": 24.0
                        },
                        "children": [
                            {
                                "OTIO_SCHEMA": "Clip.1",
                                "name": "Shot_001",
                                "source_range": {
                                    "start_time": 0,
                                    "duration": 100,
                                    "rate": 24.0
                                },
                                "media_reference": {
                                    "OTIO_SCHEMA": "ExternalReference.1",
                                    "target_url": "/media/clip.mp4",
                                    "available_range": {
                                        "start_time": 0,
                                        "duration": 100,
                                        "rate": 24.0
                                    }
                                },
                                "metadata": {
                                    "scene": 1,
                                    "take": 1,
                                    "notes": "Test note"
                                }
                            }
                        ]
                    }
                ]
            },
            "metadata": {
                "exporter": "blender_gsd",
                "frame_rate": 24.0
            }
        }

    def test_parse_otio_basic(self, sample_otio_data):
        """Test parsing basic OTIO data."""
        timeline = parse_otio(sample_otio_data)
        assert timeline is not None
        assert timeline.name == "OTIO Test"

    def test_parse_otio_invalid_schema(self):
        """Test parsing OTIO with invalid schema."""
        data = {"OTIO_SCHEMA": "Invalid.1"}
        timeline = parse_otio(data)
        assert timeline is None

    def test_import_otio_from_file(self, sample_otio_data):
        """Test importing OTIO from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_otio_data, f)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_otio(temp_path)
            assert timeline is not None
            assert timeline.name == "OTIO Test"
        finally:
            os.unlink(temp_path)

    def test_import_otio_missing_file(self):
        """Test importing missing OTIO file."""
        timeline = import_otio("/nonexistent/file.json")
        assert timeline is None

    def test_parse_otio_clip(self):
        """Test parsing OTIO clip."""
        data = {
            "OTIO_SCHEMA": "Clip.1",
            "name": "Test Clip",
            "source_range": {
                "start_time": 0,
                "duration": 100,
                "rate": 24.0
            },
            "media_reference": {
                "OTIO_SCHEMA": "ExternalReference.1",
                "target_url": "/media/test.mp4"
            },
            "metadata": {
                "scene": 5,
                "take": 3,
                "notes": "Important"
            }
        }
        clip = _parse_otio_clip(data, track_number=1, frame_rate=24.0)
        assert clip is not None
        assert clip.name == "Test Clip"
        assert clip.source_path == "/media/test.mp4"
        assert clip.scene == 5
        assert clip.take == 3
        assert clip.notes == "Important"

    def test_parse_otio_has_tracks(self, sample_otio_data):
        """Test that parsed OTIO has tracks."""
        timeline = parse_otio(sample_otio_data)
        assert len(timeline.video_tracks) >= 1


class TestImportXML:
    """Tests for generic XML import."""

    def test_import_xml_fcpxml(self):
        """Test importing FCPXML via XML import."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.9">
    <library>
        <event name="Test">
            <project name="Project">
                <sequence format="r1">
                    <spine></spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_xml(temp_path)
            assert timeline is not None
        finally:
            os.unlink(temp_path)

    def test_import_xml_unknown_format(self):
        """Test importing unknown XML format."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<unknown root="true">
</unknown>'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_xml(temp_path)
            assert timeline is None
        finally:
            os.unlink(temp_path)

    def test_import_xml_missing_file(self):
        """Test importing missing XML file."""
        timeline = import_xml("/nonexistent/file.xml")
        assert timeline is None


class TestImportTimeline:
    """Tests for generic import_timeline function."""

    def test_import_timeline_edl(self):
        """Test importing timeline as EDL."""
        content = """TITLE: Test
FCM: NON-DROP FRAME
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_timeline(temp_path, format="edl")
            assert timeline is not None
        finally:
            os.unlink(temp_path)

    def test_import_timeline_fcpxml(self):
        """Test importing timeline as FCPXML."""
        content = '''<?xml version="1.0"?>
<fcpxml version="1.9">
    <library>
        <event name="Test">
            <project name="Test">
                <sequence format="r1">
                    <spine></spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fcpxml', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            timeline = import_timeline(temp_path, format="fcpxml")
            assert timeline is not None
        finally:
            os.unlink(temp_path)

    def test_import_timeline_auto_detect(self):
        """Test importing timeline with auto-detection."""
        # EDL detection
        content = "TITLE: Test\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            timeline = import_timeline(temp_path)
            # Should detect EDL format
            assert timeline is not None
        finally:
            os.unlink(temp_path)

    def test_import_timeline_unknown_format(self):
        """Test importing with unknown format."""
        result = import_timeline("/tmp/file.xyz", format="unknown")
        assert result is None


class TestDetectFormat:
    """Tests for format detection."""

    def test_detect_edl(self):
        """Test detecting EDL format."""
        content = "TITLE: Test Edit\n001\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edl', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            fmt = detect_format(temp_path)
            assert fmt == "edl"
        finally:
            os.unlink(temp_path)

    def test_detect_fcpxml(self):
        """Test detecting FCPXML format."""
        content = '<?xml version="1.0"?>\n<fcpxml version="1.9">'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            fmt = detect_format(temp_path)
            assert fmt == "fcpxml"
        finally:
            os.unlink(temp_path)

    def test_detect_otio(self):
        """Test detecting OTIO format."""
        content = '{"OTIO_SCHEMA": "Timeline.1"}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            fmt = detect_format(temp_path)
            assert fmt == "otio"
        finally:
            os.unlink(temp_path)

    def test_detect_missing_file(self):
        """Test detecting format of missing file."""
        fmt = detect_format("/nonexistent/file.xyz")
        assert fmt is None


class TestImportEdgeCases:
    """Tests for edge cases in import."""

    def test_import_empty_edl(self):
        """Test importing empty EDL."""
        content = ""
        timeline = parse_edl(content, frame_rate=24.0)
        assert timeline is not None
        assert len(timeline.video_tracks[0].clips) == 0

    def test_import_empty_otio(self):
        """Test importing empty OTIO."""
        data = {
            "OTIO_SCHEMA": "Timeline.1",
            "name": "Empty",
            "tracks": {
                "OTIO_SCHEMA": "Stack.1",
                "children": []
            },
            "metadata": {}
        }
        timeline = parse_otio(data)
        assert timeline is not None
        assert len(timeline.video_tracks) == 0

    def test_import_invalid_json(self):
        """Test importing invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {")
            f.flush()
            temp_path = f.name

        try:
            timeline = import_otio(temp_path)
            assert timeline is None
        finally:
            os.unlink(temp_path)

    def test_import_malformed_xml(self):
        """Test importing malformed XML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write('<?xml version="1.0"?><unclosed>')
            f.flush()
            temp_path = f.name

        try:
            timeline = import_xml(temp_path)
            assert timeline is None
        finally:
            os.unlink(temp_path)
