"""
Unit tests for Footage module.

Tests video format import, metadata extraction, and
image sequence handling.
"""

import pytest
import sys
import os
import struct
import tempfile
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.footage import (
    FootageImporter,
    ImageSequenceInfo,
    VideoMetadata,
    SUPPORTED_VIDEO_FORMATS,
    FRAME_RATES,
    is_supported_format,
    get_format_info,
)
from cinematic.tracking.types import FootageInfo
from oracle import Oracle


class TestImageSequenceInfo:
    """Tests for ImageSequenceInfo dataclass."""

    def test_create_default(self):
        """Test creating sequence info with defaults."""
        info = ImageSequenceInfo()
        Oracle.assert_equal(info.pattern, "")
        Oracle.assert_equal(info.start_frame, 1)
        Oracle.assert_equal(info.end_frame, 1)
        Oracle.assert_equal(info.padding, 4)
        Oracle.assert_equal(len(info.missing_frames), 0)

    def test_create_full(self):
        """Test creating sequence info with all values."""
        info = ImageSequenceInfo(
            pattern="frame_####.exr",
            start_frame=1001,
            end_frame=1100,
            frame_step=2,
            padding=4,
            missing_frames=[1005, 1010],
        )
        Oracle.assert_equal(info.pattern, "frame_####.exr")
        Oracle.assert_equal(info.start_frame, 1001)
        Oracle.assert_equal(info.end_frame, 1100)
        Oracle.assert_equal(info.missing_frames, [1005, 1010])

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = ImageSequenceInfo(
            pattern="shot.###.dpx",
            start_frame=1,
            end_frame=60,
            padding=3,
        )
        data = original.to_dict()
        restored = ImageSequenceInfo.from_dict(data)

        Oracle.assert_equal(restored.pattern, original.pattern)
        Oracle.assert_equal(restored.start_frame, original.start_frame)
        Oracle.assert_equal(restored.end_frame, original.end_frame)


class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_create_default(self):
        """Test creating metadata with defaults."""
        meta = VideoMetadata()
        Oracle.assert_equal(meta.width, 1920)
        Oracle.assert_equal(meta.height, 1080)
        Oracle.assert_equal(meta.fps, 24.0)
        Oracle.assert_equal(meta.interlaced, False)

    def test_create_full(self):
        """Test creating metadata with all values."""
        meta = VideoMetadata(
            duration_seconds=120.0,
            frame_count=2880,
            fps=24.0,
            width=4096,
            height=2160,
            codec="ProRes 4444",
            colorspace="ACEScg",
            bit_depth=16,
            has_alpha=True,
        )
        Oracle.assert_equal(meta.duration_seconds, 120.0)
        Oracle.assert_equal(meta.frame_count, 2880)
        Oracle.assert_equal(meta.codec, "ProRes 4444")
        Oracle.assert_equal(meta.bit_depth, 16)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = VideoMetadata(
            width=3840,
            height=2160,
            fps=29.97,
            codec="H.264",
        )
        data = original.to_dict()
        restored = VideoMetadata.from_dict(data)

        Oracle.assert_equal(restored.width, original.width)
        Oracle.assert_equal(restored.height, original.height)
        Oracle.assert_equal(restored.fps, original.fps)
        Oracle.assert_equal(restored.codec, original.codec)


class TestFootageImporter:
    """Tests for FootageImporter class."""

    def test_create(self):
        """Test creating importer."""
        importer = FootageImporter()
        Oracle.assert_not_none(importer)

    def test_supported_formats(self):
        """Test that common formats are supported."""
        Oracle.assert_in(".mov", SUPPORTED_VIDEO_FORMATS)
        Oracle.assert_in(".mp4", SUPPORTED_VIDEO_FORMATS)
        Oracle.assert_in(".mxf", SUPPORTED_VIDEO_FORMATS)
        Oracle.assert_in(".exr", SUPPORTED_VIDEO_FORMATS)
        Oracle.assert_in(".dpx", SUPPORTED_VIDEO_FORMATS)

    def test_is_supported_format(self):
        """Test format support check."""
        Oracle.assert_true(is_supported_format("video.mov"))
        Oracle.assert_true(is_supported_format("video.MP4"))
        Oracle.assert_true(is_supported_format("frame.exr"))
        Oracle.assert_false(is_supported_format("document.pdf"))
        Oracle.assert_false(is_supported_format("data.bin"))

    def test_get_format_info(self):
        """Test getting format info."""
        info = get_format_info("video.mov")
        Oracle.assert_not_none(info)
        Oracle.assert_equal(info["name"], "QuickTime")

        info = get_format_info("frame.exr")
        Oracle.assert_true(info.get("is_sequence"))

    def test_import_nonexistent_file(self):
        """Test importing nonexistent file raises error."""
        importer = FootageImporter()

        with pytest.raises(FileNotFoundError):
            importer.import_footage("/nonexistent/video.mp4")

    def test_import_fallback_video(self):
        """Test fallback import for video file."""
        importer = FootageImporter()

        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"mock video data")
            temp_path = f.name

        try:
            info = importer.import_footage(temp_path)

            Oracle.assert_equal(info.is_sequence, False)
            Oracle.assert_greater_than(info.width, 0)
            Oracle.assert_greater_than(info.height, 0)
            Oracle.assert_greater_than(info.fps, 0)
        finally:
            os.unlink(temp_path)

    def test_import_fallback_4k_detection(self):
        """Test 4K resolution detection from filename."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix="_4K_ProRes.mov", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            info = importer.import_footage(temp_path)
            Oracle.assert_equal(info.width, 4096)
            Oracle.assert_equal(info.height, 2160)
        finally:
            os.unlink(temp_path)

    def test_import_fallback_fps_detection(self):
        """Test FPS detection from filename."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix="_23.976_fps.mp4", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            info = importer.import_footage(temp_path)
            Oracle.assert_equal(info.fps, 23.976)
        finally:
            os.unlink(temp_path)

    def test_detect_sequence_pattern(self):
        """Test sequence pattern detection."""
        importer = FootageImporter()

        # Create temp directory with image sequence
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock sequence files
            for i in range(1001, 1011):
                frame_path = Path(temp_dir) / f"shot_{i:04d}.exr"
                frame_path.write_bytes(b"mock")

            first_frame = Path(temp_dir) / "shot_1001.exr"
            seq_info = importer._detect_sequence_pattern(first_frame)

            Oracle.assert_equal(seq_info.start_frame, 1001)
            Oracle.assert_equal(seq_info.end_frame, 1010)
            Oracle.assert_equal(seq_info.padding, 4)
            Oracle.assert_equal(len(seq_info.missing_frames), 0)

    def test_detect_sequence_with_missing_frames(self):
        """Test sequence detection with missing frames."""
        importer = FootageImporter()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sequence with gaps
            for i in [1001, 1002, 1004, 1005, 1008, 1010]:
                frame_path = Path(temp_dir) / f"frame.{i:04d}.dpx"
                frame_path.write_bytes(b"mock")

            first_frame = Path(temp_dir) / "frame.1001.dpx"
            seq_info = importer._detect_sequence_pattern(first_frame)

            Oracle.assert_equal(seq_info.start_frame, 1001)
            Oracle.assert_equal(seq_info.end_frame, 1010)
            Oracle.assert_in(1003, seq_info.missing_frames)
            Oracle.assert_in(1006, seq_info.missing_frames)
            Oracle.assert_in(1007, seq_info.missing_frames)
            Oracle.assert_in(1009, seq_info.missing_frames)

    def test_import_image_sequence(self):
        """Test importing image sequence."""
        importer = FootageImporter()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sequence
            for i in range(1, 11):
                frame_path = Path(temp_dir) / f"render_{i:04d}.png"
                frame_path.write_bytes(b"mock")

            first_frame = Path(temp_dir) / "render_0001.png"
            info = importer.import_footage(str(first_frame))

            Oracle.assert_true(info.is_sequence)
            Oracle.assert_equal(info.frame_start, 1)
            Oracle.assert_equal(info.frame_end, 10)

    def test_get_metadata_fallback(self):
        """Test metadata extraction fallback."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"mock video data")
            temp_path = f.name

        try:
            meta = importer.get_metadata(temp_path)

            Oracle.assert_greater_than(meta.width, 0)
            Oracle.assert_greater_than(meta.height, 0)
            Oracle.assert_greater_than(meta.fps, 0)
        finally:
            os.unlink(temp_path)


class TestImageHeaderParsing:
    """Tests for image header parsing."""

    def test_png_header_parsing(self):
        """Test PNG dimension extraction."""
        importer = FootageImporter()

        # Create a minimal valid PNG
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # PNG signature
            f.write(b'\x89PNG\r\n\x1a\n')
            # IHDR chunk
            width = 1920
            height = 1080
            ihdr = struct.pack('>II', width, height)
            f.write(struct.pack('>I', 13))  # Length
            f.write(b'IHDR')  # Type
            f.write(ihdr)
            f.write(b'\x00\x00\x00\x00\x00')  # Rest of IHDR + CRC placeholder
            temp_path = f.name

        try:
            w, h = importer._get_png_dimensions(Path(temp_path))
            Oracle.assert_equal(w, 1920)
            Oracle.assert_equal(h, 1080)
        finally:
            os.unlink(temp_path)

    def test_invalid_png_returns_default(self):
        """Test invalid PNG returns default dimensions."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"not a png")
            temp_path = f.name

        try:
            w, h = importer._get_png_dimensions(Path(temp_path))
            Oracle.assert_equal(w, 1920)
            Oracle.assert_equal(h, 1080)
        finally:
            os.unlink(temp_path)


class TestColorspaceDetection:
    """Tests for colorspace detection."""

    def test_exr_colorspace(self):
        """Test EXR colorspace detection."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".exr", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            colorspace = importer._detect_colorspace(Path(temp_path))
            Oracle.assert_equal(colorspace, "ACEScg")
        finally:
            os.unlink(temp_path)

    def test_dpx_colorspace(self):
        """Test DPX colorspace detection."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".dpx", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            colorspace = importer._detect_colorspace(Path(temp_path))
            Oracle.assert_equal(colorspace, "Linear")
        finally:
            os.unlink(temp_path)

    def test_png_colorspace(self):
        """Test PNG colorspace detection."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            colorspace = importer._detect_colorspace(Path(temp_path))
            Oracle.assert_equal(colorspace, "sRGB")
        finally:
            os.unlink(temp_path)


class TestAlphaDetection:
    """Tests for alpha channel detection."""

    def test_png_has_alpha(self):
        """Test PNG alpha detection."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            has_alpha = importer._check_alpha(Path(temp_path))
            Oracle.assert_true(has_alpha)
        finally:
            os.unlink(temp_path)

    def test_jpg_no_alpha(self):
        """Test JPEG has no alpha."""
        importer = FootageImporter()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            has_alpha = importer._check_alpha(Path(temp_path))
            Oracle.assert_false(has_alpha)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
