"""
Unit tests for Footage Profiles module (Phase 7.2)

Tests for:
- FootageMetadata extended fields
- RollingShutterConfig
- FFprobeMetadataExtractor
- FootageAnalyzer
- RollingShutterDetector
- ImageSequenceAnalyzer
- FootageProfile
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from lib.cinematic.tracking.types import FootageMetadata, RollingShutterConfig
from lib.cinematic.tracking.footage_profiles import (
    FFprobeMetadataExtractor,
    FootageAnalyzer,
    RollingShutterDetector,
    FootageProfile,
    ContentAnalysis,
    ImageSequenceAnalyzer,
    extract_metadata,
    analyze_footage,
    analyze_image_sequence,
    get_tracking_recommendations,
)


class TestFootageMetadata:
    """Tests for extended FootageMetadata dataclass."""

    def test_default_values(self):
        """Test default values for FootageMetadata."""
        metadata = FootageMetadata()
        assert metadata.source_path == ""
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 24.0
        assert metadata.frame_count == 0
        assert metadata.duration_seconds == 0.0
        assert metadata.codec == ""
        assert metadata.bit_depth == 8
        assert metadata.color_space == ""
        assert metadata.color_range == "limited"
        assert metadata.pixel_aspect_ratio == 1.0

    def test_device_metadata(self):
        """Test device metadata fields."""
        metadata = FootageMetadata(
            camera_make="Apple",
            camera_model="iPhone 15 Pro",
            lens_model="Triple Camera",
            focal_length_mm=6.78,
            iso=800,
            aperture="f/1.8",
            white_balance=5600,
        )
        assert metadata.camera_make == "Apple"
        assert metadata.camera_model == "iPhone 15 Pro"
        assert metadata.focal_length_mm == 6.78

    def test_content_analysis_fields(self):
        """Test content analysis fields."""
        metadata = FootageMetadata(
            motion_blur_level="high",
            noise_level="medium",
            contrast_suitability="excellent",
            dominant_motion="pan",
        )
        assert metadata.motion_blur_level == "high"
        assert metadata.noise_level == "medium"
        assert metadata.contrast_suitability == "excellent"
        assert metadata.dominant_motion == "pan"

    def test_backward_compatibility_properties(self):
        """Test backward compatibility properties."""
        metadata = FootageMetadata(
            width=3840,
            height=2160,
            fps=29.97,
            frame_count=1000,
            focal_length_mm=50.0,
            motion_blur_level="high",
        )

        # Test resolution property
        assert metadata.resolution == (3840, 2160)

        # Test duration_frames property
        assert metadata.duration_frames == 1000

        # Test frame_rate property
        assert metadata.frame_rate == 29.97

        # Test focal_length property
        assert metadata.focal_length == 50.0

        # Test rolling_shutter_detected property
        assert metadata.rolling_shutter_detected == True

    def test_to_dict(self):
        """Test serialization to dictionary."""
        metadata = FootageMetadata(
            source_path="/path/to/video.mp4",
            width=1920,
            height=1080,
            fps=24.0,
            camera_model="iPhone 15 Pro",
            motion_blur_level="medium",
        )
        data = metadata.to_dict()

        assert data["source_path"] == "/path/to/video.mp4"
        assert data["width"] == 1920
        assert data["height"] == 1080
        assert data["fps"] == 24.0
        assert data["camera_model"] == "iPhone 15 Pro"
        # Backward compatibility fields
        assert data["resolution"] == [1920, 1080]
        assert data["frame_rate"] == 24.0

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "source_path": "/path/to/video.mp4",
            "width": 1920,
            "height": 1080,
            "fps": 24.0,
            "camera_model": "iPhone 15 Pro",
            "motion_blur_level": "medium",
        }
        metadata = FootageMetadata.from_dict(data)

        assert metadata.source_path == "/path/to/video.mp4"
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 24.0
        assert metadata.camera_model == "iPhone 15 Pro"

    def test_from_dict_backward_compatibility(self):
        """Test deserialization from old format dictionary."""
        # Old format used "resolution" and "filename"
        data = {
            "filename": "/path/to/video.mp4",
            "resolution": [3840, 2160],
            "frame_rate": 30.0,
            "duration_frames": 500,
        }
        metadata = FootageMetadata.from_dict(data)

        assert metadata.source_path == "/path/to/video.mp4"
        assert metadata.width == 3840
        assert metadata.height == 2160
        assert metadata.fps == 30.0
        assert metadata.frame_count == 500


class TestRollingShutterConfig:
    """Tests for RollingShutterConfig dataclass."""

    def test_default_values(self):
        """Test default values for RollingShutterConfig."""
        config = RollingShutterConfig()
        assert config.detected == False
        assert config.severity == "none"
        assert config.read_time == 0.0
        assert config.skew_angle == 0.0
        assert config.method == "row_rolling"
        assert config.row_count == 1080
        assert config.compensation_enabled == True

    def test_detected_config(self):
        """Test detected rolling shutter config."""
        config = RollingShutterConfig(
            detected=True,
            severity="high",
            read_time=0.025,
            skew_angle=2.5,
            row_count=2160,
            compensation_enabled=True,
        )
        assert config.detected == True
        assert config.severity == "high"
        assert config.read_time == 0.025
        assert config.skew_angle == 2.5

    def test_to_dict_from_dict(self):
        """Test serialization and deserialization."""
        config = RollingShutterConfig(
            detected=True,
            severity="medium",
            read_time=0.012,
            row_count=1080,
        )
        data = config.to_dict()
        restored = RollingShutterConfig.from_dict(data)

        assert restored.detected == True
        assert restored.severity == "medium"
        assert restored.read_time == 0.012
        assert restored.row_count == 1080


class TestContentAnalysis:
    """Tests for ContentAnalysis dataclass."""

    def test_default_values(self):
        """Test default content analysis values."""
        content = ContentAnalysis()
        assert content.motion_blur_level == "medium"
        assert content.noise_level == "medium"
        assert content.contrast_suitability == "good"
        assert content.dominant_motion == "handheld"

    def test_custom_values(self):
        """Test custom content analysis values."""
        content = ContentAnalysis(
            motion_blur_level="low",
            noise_level="low",
            contrast_suitability="excellent",
            dominant_motion="static",
            sharpness_score=0.9,
            contrast_ratio=0.8,
        )
        assert content.motion_blur_level == "low"
        assert content.sharpness_score == 0.9


class TestFFprobeMetadataExtractor:
    """Tests for FFprobeMetadataExtractor."""

    def test_parse_frame_rate_rational(self):
        """Test parsing rational frame rates like 30000/1001."""
        extractor = FFprobeMetadataExtractor()

        # Common NTSC rates
        assert extractor._parse_frame_rate("30000/1001") == pytest.approx(29.97, rel=0.001)
        assert extractor._parse_frame_rate("24000/1001") == pytest.approx(23.976, rel=0.001)
        assert extractor._parse_frame_rate("60000/1001") == pytest.approx(59.94, rel=0.001)

        # Simple rates
        assert extractor._parse_frame_rate("24/1") == 24.0
        assert extractor._parse_frame_rate("30/1") == 30.0
        assert extractor._parse_frame_rate("60/1") == 60.0

    def test_parse_frame_rate_decimal(self):
        """Test parsing decimal frame rates."""
        extractor = FFprobeMetadataExtractor()

        assert extractor._parse_frame_rate("24.0") == 24.0
        assert extractor._parse_frame_rate("29.97") == 29.97
        assert extractor._parse_frame_rate("59.94") == 59.94

    def test_parse_focal_length(self):
        """Test parsing focal length from various formats."""
        extractor = FFprobeMetadataExtractor()

        assert extractor._parse_focal_length("4.2 mm") == 4.2
        assert extractor._parse_focal_length("6.78mm") == 6.78
        assert extractor._parse_focal_length("50") == 50.0
        assert extractor._parse_focal_length("") == 0.0

    def test_parse_ratio(self):
        """Test parsing aspect ratios."""
        extractor = FFprobeMetadataExtractor()

        assert extractor._parse_ratio("1:1") == 1.0
        assert extractor._parse_ratio("4:3") == pytest.approx(4/3, rel=0.001)
        assert extractor._parse_ratio("16:9") == pytest.approx(16/9, rel=0.001)

    @patch('subprocess.run')
    def test_extract_metadata_file_not_found(self, mock_run):
        """Test handling of non-existent file."""
        extractor = FFprobeMetadataExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract("/nonexistent/video.mp4")

    @patch('subprocess.run')
    def test_extract_metadata_ffprobe_failure(self, mock_run):
        """Test handling of ffprobe failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")

        extractor = FFprobeMetadataExtractor()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError, match="ffprobe failed"):
                extractor.extract(temp_path)
        finally:
            os.unlink(temp_path)


class TestRollingShutterDetector:
    """Tests for RollingShutterDetector."""

    def test_detect_iphone_15_pro(self):
        """Test detection for iPhone 15 Pro."""
        detector = RollingShutterDetector()

        metadata = FootageMetadata(
            camera_make="Apple",
            camera_model="iPhone 15 Pro",
        )
        config = detector.detect(metadata)

        assert config.detected == True
        assert config.read_time == 0.010  # 10ms
        assert config.severity == "medium"
        assert config.compensation_enabled == True

    def test_detect_gopro(self):
        """Test detection for GoPro (high rolling shutter)."""
        detector = RollingShutterDetector()

        metadata = FootageMetadata(
            camera_make="GoPro",
            camera_model="Hero12",
        )
        config = detector.detect(metadata)

        assert config.detected == True
        assert config.read_time == 0.025  # 25ms
        assert config.severity == "high"
        assert config.compensation_enabled == True

    def test_detect_cinema_camera(self):
        """Test detection for cinema camera (low rolling shutter)."""
        detector = RollingShutterDetector()

        metadata = FootageMetadata(
            camera_make="RED",
            camera_model="KOMODO 6K",
        )
        config = detector.detect(metadata)

        assert config.detected == True
        assert config.read_time == 0.005  # 5ms
        assert config.severity == "low"
        assert config.compensation_enabled == False

    def test_detect_unknown_device(self):
        """Test handling of unknown device."""
        detector = RollingShutterDetector()

        metadata = FootageMetadata(
            camera_make="Unknown",
            camera_model="Unknown Model",
        )
        config = detector.detect(metadata)

        assert config.detected == False
        assert config.severity == "none"


class TestImageSequenceAnalyzer:
    """Tests for ImageSequenceAnalyzer."""

    def test_supported_formats(self):
        """Test supported image formats."""
        analyzer = ImageSequenceAnalyzer()

        assert ".exr" in analyzer.SUPPORTED_FORMATS
        assert ".dpx" in analyzer.SUPPORTED_FORMATS
        assert ".png" in analyzer.SUPPORTED_FORMATS
        assert ".jpg" in analyzer.SUPPORTED_FORMATS
        assert ".tiff" in analyzer.SUPPORTED_FORMATS

    def test_parse_sequence_pattern_hash(self):
        """Test parsing #### style pattern."""
        analyzer = ImageSequenceAnalyzer()

        # Test with non-existent pattern
        info = analyzer._parse_hash_pattern(Path("/path/to/frames/frame_####.exr"))

        assert info["padding"] == 4
        assert "####.exr" in info["pattern"]

    def test_analyze_basic(self):
        """Test basic sequence analysis."""
        analyzer = ImageSequenceAnalyzer()

        # Create a temp PNG file for testing
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="frame_0001_") as f:
            # Write minimal PNG header
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(b'\x00\x00\x00\rIHDR')
            f.write(b'\x00\x00\x07\x80')  # width = 1920
            f.write(b'\x00\x00\x04\x38')  # height = 1080
            temp_path = f.name

        try:
            metadata, content = analyzer.analyze(temp_path, fps=24.0)

            assert metadata.fps == 24.0
            assert metadata.codec == "PNG"
            assert content.motion_blur_level == "low"  # Still images have low blur
        finally:
            os.unlink(temp_path)


class TestFootageProfile:
    """Tests for FootageProfile."""

    def test_from_image_sequence(self):
        """Test creating profile from image sequence."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="frame_0001_") as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            temp_path = f.name

        try:
            profile = FootageProfile.from_image_sequence(temp_path, fps=30.0)

            assert profile.metadata.fps == 30.0
            assert profile.content.motion_blur_level == "low"
            assert profile.rolling_shutter.detected == False
        finally:
            os.unlink(temp_path)

    def test_get_tracking_recommendations_default(self):
        """Test default tracking recommendations."""
        metadata = FootageMetadata()
        content = ContentAnalysis()
        rolling_shutter = RollingShutterConfig(detected=False, compensation_enabled=False)
        profile = FootageProfile(metadata, content, rolling_shutter)

        rec = profile.get_tracking_recommendations()

        assert rec["preset"] == "balanced"
        assert rec["min_correlation"] == 0.6
        assert rec["rolling_shutter_compensation"] == False
        assert rec["frame_limit"] == 0

    def test_get_tracking_recommendations_high_motion_blur(self):
        """Test recommendations for high motion blur footage."""
        metadata = FootageMetadata(motion_blur_level="high")
        content = ContentAnalysis()
        profile = FootageProfile(metadata, content)

        rec = profile.get_tracking_recommendations()

        assert rec["preset"] == "precise"
        assert rec["pattern_size"] == 31
        assert any("motion blur" in note.lower() for note in rec["notes"])

    def test_get_tracking_recommendations_rolling_shutter(self):
        """Test recommendations for footage with rolling shutter."""
        metadata = FootageMetadata()
        content = ContentAnalysis()
        rolling_shutter = RollingShutterConfig(
            detected=True,
            severity="high",
            compensation_enabled=True,
        )
        profile = FootageProfile(metadata, content, rolling_shutter)

        rec = profile.get_tracking_recommendations()

        assert rec["rolling_shutter_compensation"] == True
        assert any("rolling shutter" in note.lower() for note in rec["notes"])

    def test_to_dict(self):
        """Test profile serialization."""
        metadata = FootageMetadata(width=1920, height=1080)
        content = ContentAnalysis(motion_blur_level="low")
        profile = FootageProfile(metadata, content)

        data = profile.to_dict()

        assert "metadata" in data
        assert "content" in data
        assert "rolling_shutter" in data
        assert data["content"]["motion_blur_level"] == "low"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_extract_metadata_function(self):
        """Test extract_metadata convenience function."""
        # This would normally call ffprobe, so we'll just verify it exists
        assert callable(extract_metadata)

    def test_analyze_footage_function(self):
        """Test analyze_footage convenience function."""
        assert callable(analyze_footage)

    def test_analyze_image_sequence_function(self):
        """Test analyze_image_sequence convenience function."""
        assert callable(analyze_image_sequence)

    def test_get_tracking_recommendations_function(self):
        """Test get_tracking_recommendations convenience function."""
        assert callable(get_tracking_recommendations)


class TestFootageAnalyzer:
    """Tests for FootageAnalyzer."""

    def test_infer_motion_blur_from_fps(self):
        """Test motion blur inference from frame rate."""
        analyzer = FootageAnalyzer()

        # High frame rate should result in low motion blur
        metadata_high_fps = FootageMetadata(fps=120.0)
        content = analyzer._analyze_content("/dummy/path", metadata_high_fps)
        assert content.motion_blur_level == "low"

    def test_infer_noise_from_iso(self):
        """Test noise level inference from ISO."""
        analyzer = FootageAnalyzer()

        # High ISO should result in high noise
        metadata_high_iso = FootageMetadata(iso=6400)
        content = analyzer._analyze_content("/dummy/path", metadata_high_iso)
        assert content.noise_level == "high"

        # Low ISO should result in low noise
        metadata_low_iso = FootageMetadata(iso=100)
        content = analyzer._analyze_content("/dummy/path", metadata_low_iso)
        assert content.noise_level == "low"

    def test_infer_contrast_from_resolution(self):
        """Test contrast inference from resolution."""
        analyzer = FootageAnalyzer()

        # 4K+ should be excellent
        metadata_4k = FootageMetadata(width=4096, height=2160)
        content = analyzer._analyze_content("/dummy/path", metadata_4k)
        assert content.contrast_suitability == "excellent"

        # HD should be good
        metadata_hd = FootageMetadata(width=1920, height=1080)
        content = analyzer._analyze_content("/dummy/path", metadata_hd)
        assert content.contrast_suitability == "good"

        # SD should be fair
        metadata_sd = FootageMetadata(width=640, height=480)
        content = analyzer._analyze_content("/dummy/path", metadata_sd)
        assert content.contrast_suitability == "fair"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
