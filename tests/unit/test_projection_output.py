"""
Tests for projection output rendering system.
"""

import pytest
from dataclasses import asdict
from pathlib import Path

from lib.cinematic.projection.physical.output.types import (
    OutputFormat,
    ColorSpace,
    VideoCodec,
    EXRCodec,
    ProjectionOutputConfig,
    ProjectionOutputResult,
    CalibrationPatternConfig,
)
from lib.cinematic.projection.physical.output.renderer import ProjectionOutputRenderer
from lib.cinematic.projection.physical.output.multi_surface import (
    MultiSurfaceOutput,
    MultiSurfaceResult,
    MultiSurfaceRenderer,
)


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_format_values(self):
        """Test format enum values."""
        assert OutputFormat.IMAGE_SEQUENCE.value == "image_sequence"
        assert OutputFormat.VIDEO.value == "video"
        assert OutputFormat.EXR.value == "exr"
        assert OutputFormat.PNG.value == "png"

    def test_all_formats_defined(self):
        """Test all formats are defined."""
        formats = list(OutputFormat)
        assert len(formats) == 4


class TestColorSpace:
    """Tests for ColorSpace enum."""

    def test_color_space_values(self):
        """Test color space enum values."""
        assert ColorSpace.SRGB.value == "sRGB"
        assert ColorSpace.REC709.value == "Rec709"
        assert ColorSpace.REC2020.value == "Rec2020"
        assert ColorSpace.ACES.value == "ACES"
        assert ColorSpace.FILMIC.value == "Filmic"


class TestVideoCodec:
    """Tests for VideoCodec enum."""

    def test_codec_values(self):
        """Test video codec enum values."""
        assert VideoCodec.H264.value == "H264"
        assert VideoCodec.H265.value == "H265"
        assert VideoCodec.PRORES.value == "PRORES"
        assert VideoCodec.DNXHD.value == "DNXHD"


class TestEXRCodec:
    """Tests for EXRCodec enum."""

    def test_exr_codec_values(self):
        """Test EXR codec enum values."""
        assert EXRCodec.NONE.value == "NONE"
        assert EXRCodec.ZIP.value == "ZIP"
        assert EXRCodec.PIZ.value == "PIZ"
        assert EXRCodec.RLE.value == "RLE"
        assert EXRCodec.DWAA.value == "DWAA"
        assert EXRCodec.DWAB.value == "DWAB"


class TestProjectionOutputConfig:
    """Tests for ProjectionOutputConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ProjectionOutputConfig()

        assert config.resolution == (1920, 1080)
        assert config.frame_start == 1
        assert config.frame_end == 250
        assert config.format == OutputFormat.IMAGE_SEQUENCE
        assert config.color_space == ColorSpace.SRGB
        assert config.output_path == "//projector_output/"
        assert config.file_prefix == "frame_"
        assert config.video_codec == VideoCodec.H264
        assert config.video_quality == 90
        assert config.frame_rate == 24
        assert config.exr_codec == EXRCodec.ZIP
        assert config.exr_depth == 16
        assert config.use_motion_blur is False
        assert config.motion_blur_shutter == 0.5
        assert config.use_transparent_bg is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ProjectionOutputConfig(
            resolution=(3840, 2160),
            frame_start=10,
            frame_end=100,
            format=OutputFormat.VIDEO,
            color_space=ColorSpace.ACES,
            output_path="//renders/",
            file_prefix="shot01_",
            video_codec=VideoCodec.H265,
            video_quality=95,
            frame_rate=30,
            use_motion_blur=True,
            motion_blur_shutter=0.25,
        )

        assert config.resolution == (3840, 2160)
        assert config.frame_start == 10
        assert config.frame_end == 100
        assert config.format == OutputFormat.VIDEO
        assert config.color_space == ColorSpace.ACES
        assert config.output_path == "//renders/"
        assert config.file_prefix == "shot01_"
        assert config.video_codec == VideoCodec.H265
        assert config.video_quality == 95
        assert config.frame_rate == 30
        assert config.use_motion_blur is True
        assert config.motion_blur_shutter == 0.25

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = ProjectionOutputConfig(
            resolution=(1920, 1080),
            format=OutputFormat.EXR,
            exr_codec=EXRCodec.PIZ,
        )
        data = config.to_dict()

        assert data["resolution"] == [1920, 1080]
        assert data["format"] == "exr"
        assert data["exr_codec"] == "PIZ"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "resolution": [3840, 2160],
            "frame_start": 1,
            "frame_end": 100,
            "format": "video",
            "color_space": "ACES",
            "video_codec": "PRORES",
        }
        config = ProjectionOutputConfig.from_dict(data)

        assert config.resolution == (3840, 2160)
        assert config.format == OutputFormat.VIDEO
        assert config.color_space == ColorSpace.ACES
        assert config.video_codec == VideoCodec.PRORES

    def test_round_trip(self):
        """Test serialization round trip."""
        original = ProjectionOutputConfig(
            resolution=(2560, 1440),
            format=OutputFormat.EXR,
            exr_codec=EXRCodec.DWAA,
            exr_depth=32,
            color_space=ColorSpace.REC2020,
        )
        data = original.to_dict()
        restored = ProjectionOutputConfig.from_dict(data)

        assert restored.resolution == original.resolution
        assert restored.format == original.format
        assert restored.exr_codec == original.exr_codec
        assert restored.exr_depth == original.exr_depth
        assert restored.color_space == original.color_space


class TestProjectionOutputResult:
    """Tests for ProjectionOutputResult."""

    def test_default_result(self):
        """Test default result values."""
        result = ProjectionOutputResult()

        assert result.output_files == []
        assert result.total_frames == 0
        assert result.render_time_seconds == 0.0
        assert result.output_size_bytes == 0
        assert result.success is True
        assert result.errors == []

    def test_custom_result(self):
        """Test custom result values."""
        result = ProjectionOutputResult(
            output_files=[Path("/tmp/frame_001.png"), Path("/tmp/frame_002.png")],
            total_frames=2,
            render_time_seconds=12.5,
            output_size_bytes=2048576,
            success=True,
        )

        assert len(result.output_files) == 2
        assert result.total_frames == 2
        assert result.render_time_seconds == 12.5
        assert result.output_size_bytes == 2048576

    def test_result_serialization(self):
        """Test result serialization."""
        result = ProjectionOutputResult(
            output_files=[Path("/tmp/frame_001.png")],
            total_frames=1,
            render_time_seconds=5.0,
            output_size_bytes=1024000,
            errors=["warning: low memory"],
        )
        data = result.to_dict()

        assert data["output_files"] == ["/tmp/frame_001.png"]
        assert data["total_frames"] == 1
        assert data["render_time_seconds"] == 5.0
        assert data["output_size_bytes"] == 1024000
        assert "warning: low memory" in data["errors"]


class TestCalibrationPatternConfig:
    """Tests for CalibrationPatternConfig."""

    def test_default_config(self):
        """Test default calibration pattern config."""
        config = CalibrationPatternConfig()

        assert config.resolution == (1920, 1080)
        assert config.pattern_type == "checkerboard"
        assert config.grid_size == (8, 6)
        assert config.line_width == 2
        assert config.background_color == (0, 0, 0)
        assert config.foreground_color == (255, 255, 255)

    def test_custom_config(self):
        """Test custom calibration pattern config."""
        config = CalibrationPatternConfig(
            resolution=(3840, 2160),
            pattern_type="grid",
            grid_size=(16, 9),
            line_width=4,
            background_color=(50, 50, 50),
            foreground_color=(255, 0, 0),
        )

        assert config.resolution == (3840, 2160)
        assert config.pattern_type == "grid"
        assert config.grid_size == (16, 9)
        assert config.line_width == 4
        assert config.background_color == (50, 50, 50)
        assert config.foreground_color == (255, 0, 0)

    def test_serialization(self):
        """Test calibration pattern config serialization."""
        config = CalibrationPatternConfig(
            pattern_type="color_bars",
            resolution=(1920, 1080),
        )
        data = config.to_dict()

        assert data["pattern_type"] == "color_bars"
        assert data["resolution"] == [1920, 1080]


class TestProjectionOutputRenderer:
    """Tests for ProjectionOutputRenderer."""

    @pytest.fixture
    def mock_projector_profile(self):
        """Create mock projector profile."""
        class MockProfile:
            native_resolution = (1920, 1080)
            throw_ratio = 1.5
            lens_shift_horizontal = 0.0
            lens_shift_vertical = 0.0
        return MockProfile()

    def test_renderer_initialization(self, mock_projector_profile):
        """Test renderer initialization."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        assert renderer.profile == mock_projector_profile
        assert renderer.config.resolution == (1920, 1080)

    def test_render_without_blender(self, mock_projector_profile):
        """Test rendering fails gracefully without Blender or with None scene."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)
        config = ProjectionOutputConfig()

        # render_animation should return error result without bpy or with None scene
        result = renderer.render_animation(None, config)

        assert result.success is False
        assert len(result.errors) > 0
        # Error will be about scene/blender/config issues
        assert len(result.errors[0]) > 0  # Just check we have an error message

    def test_render_single_frame_without_blender(self, mock_projector_profile):
        """Test single frame rendering fails gracefully without Blender."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        result = renderer.render_single_frame(None, 1)

        assert result.success is False
        assert len(result.errors) > 0

    def test_configure_scene_without_blender(self, mock_projector_profile):
        """Test scene configuration returns warning without Blender or None scene."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)
        config = ProjectionOutputConfig()

        warnings = renderer.configure_scene_for_output(None, config)

        # May have Blender warning or error about NoneType
        assert len(warnings) > 0

    def test_get_output_statistics(self, mock_projector_profile):
        """Test output statistics calculation."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        result = ProjectionOutputResult(
            output_files=[Path("/tmp/f1.png"), Path("/tmp/f2.png")],
            total_frames=2,
            render_time_seconds=10.0,
            output_size_bytes=2048000,
        )

        stats = renderer.get_output_statistics(result)

        assert stats["total_files"] == 2
        assert stats["total_frames"] == 2
        assert stats["render_time_seconds"] == 10.0
        assert stats["output_size_mb"] == pytest.approx(2048000 / (1024 * 1024))
        assert stats["avg_frame_time"] == 5.0
        assert stats["avg_frame_size_kb"] == pytest.approx(2048000 / 2 / 1024)

    def test_get_output_statistics_zero_frames(self, mock_projector_profile):
        """Test output statistics with zero frames."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        result = ProjectionOutputResult(total_frames=0)
        stats = renderer.get_output_statistics(result)

        assert stats["avg_frame_time"] == 0
        assert stats["avg_frame_size_kb"] == 0


class TestCalibrationPatternGeneration:
    """Tests for calibration pattern generation."""

    @pytest.fixture
    def mock_projector_profile(self):
        """Create mock projector profile."""
        class MockProfile:
            native_resolution = (1920, 1080)
            throw_ratio = 1.5
            lens_shift_horizontal = 0.0
            lens_shift_vertical = 0.0
        return MockProfile()

    def test_checkerboard_pattern_generation(self, mock_projector_profile):
        """Test checkerboard pattern pixel generation."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        config = CalibrationPatternConfig(
            resolution=(16, 16),
            pattern_type="checkerboard",
            grid_size=(4, 4),
        )

        pixels = renderer._generate_checkerboard_pattern(config)

        # Should have 16 * 16 * 3 = 768 pixel values
        assert len(pixels) == 16 * 16 * 3

        # Check that we have both black (0.0) and white (1.0) pixels
        assert 0.0 in pixels
        assert 1.0 in pixels

    def test_color_bars_pattern_generation(self, mock_projector_profile):
        """Test color bars pattern pixel generation."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        config = CalibrationPatternConfig(
            resolution=(700, 100),
            pattern_type="color_bars",
        )

        pixels = renderer._generate_color_bars_pattern(config)

        # Should have 700 * 100 * 3 pixel values
        assert len(pixels) == 700 * 100 * 3

    def test_grid_pattern_generation(self, mock_projector_profile):
        """Test grid pattern pixel generation."""
        renderer = ProjectionOutputRenderer(mock_projector_profile)

        config = CalibrationPatternConfig(
            resolution=(100, 100),
            pattern_type="grid",
            grid_size=(5, 5),
            line_width=2,
        )

        pixels = renderer._generate_grid_pattern(config)

        # Should have 100 * 100 * 3 pixel values
        assert len(pixels) == 100 * 100 * 3

        # Check that we have both black and white pixels
        assert 0.0 in pixels
        assert 1.0 in pixels


class TestMultiSurfaceOutput:
    """Tests for MultiSurfaceOutput."""

    def test_default_config(self):
        """Test default multi-surface output config."""
        config = MultiSurfaceOutput()

        assert config.surfaces == {}
        assert config.content == {}
        assert config.output_prefix == "surface_"
        assert config.render_separate is True
        assert config.render_combined is True

    def test_custom_config(self):
        """Test custom multi-surface output config."""
        config = MultiSurfaceOutput(
            surfaces={"left": None, "right": None},
            content={"left": "left.png", "right": "right.png"},
            output_prefix="cabinet_",
            render_separate=True,
            render_combined=False,
        )

        assert len(config.surfaces) == 2
        assert config.content["left"] == "left.png"
        assert config.output_prefix == "cabinet_"
        assert config.render_combined is False

    def test_serialization(self):
        """Test multi-surface output serialization."""
        config = MultiSurfaceOutput(
            surfaces={"a": None, "b": None},
            content={"a": "a.png"},
        )
        data = config.to_dict()

        assert "a" in data["surfaces"]
        assert "b" in data["surfaces"]
        assert data["content"]["a"] == "a.png"


class TestMultiSurfaceResult:
    """Tests for MultiSurfaceResult."""

    def test_default_result(self):
        """Test default multi-surface result."""
        result = MultiSurfaceResult()

        assert result.surface_results == {}
        assert result.combined_result is None
        assert result.success is True
        assert result.errors == []

    def test_custom_result(self):
        """Test custom multi-surface result."""
        surface_result = ProjectionOutputResult(
            total_frames=10,
            success=True,
        )

        result = MultiSurfaceResult(
            surface_results={"left": surface_result},
            success=True,
        )

        assert "left" in result.surface_results
        assert result.surface_results["left"].total_frames == 10

    def test_serialization(self):
        """Test multi-surface result serialization."""
        surface_result = ProjectionOutputResult(
            output_files=[Path("/tmp/left_001.png")],
            total_frames=1,
        )

        result = MultiSurfaceResult(
            surface_results={"left": surface_result},
            combined_result=ProjectionOutputResult(total_frames=2),
            success=True,
        )

        data = result.to_dict()

        assert "left" in data["surface_results"]
        assert data["combined_result"]["total_frames"] == 2


class TestMultiSurfaceRenderer:
    """Tests for MultiSurfaceRenderer."""

    @pytest.fixture
    def mock_renderer(self):
        """Create mock base renderer."""
        class MockProfile:
            native_resolution = (1920, 1080)
            throw_ratio = 1.5

        class MockRenderer:
            config = ProjectionOutputConfig(resolution=(1920, 1080))

            def render_animation(self, scene, config):
                return ProjectionOutputResult(
                    output_files=[Path("/tmp/test.png")],
                    total_frames=1,
                    success=True,
                )

            def get_output_statistics(self, result):
                return {
                    "total_files": len(result.output_files),
                    "total_frames": result.total_frames,
                    "render_time_seconds": result.render_time_seconds,
                    "output_size_mb": result.output_size_bytes / (1024 * 1024),
                    "avg_frame_time": result.render_time_seconds / result.total_frames if result.total_frames > 0 else 0,
                    "avg_frame_size_kb": result.output_size_bytes / result.total_frames / 1024 if result.total_frames > 0 else 0,
                    "success": result.success,
                    "error_count": len(result.errors),
                }

        return MockRenderer()

    def test_renderer_initialization(self, mock_renderer):
        """Test multi-surface renderer initialization."""
        multi_renderer = MultiSurfaceRenderer(mock_renderer)

        assert multi_renderer.renderer == mock_renderer

    def test_render_multi_surface_separate_disabled(self, mock_renderer):
        """Test multi-surface render with separate disabled."""
        multi_renderer = MultiSurfaceRenderer(mock_renderer)

        config = MultiSurfaceOutput(
            surfaces={"left": None},
            render_separate=False,
        )

        result = multi_renderer.render_multi_surface(config, "/tmp/")

        assert result.success is False
        assert "render_separate is False" in result.errors[0]

    def test_get_surface_statistics(self, mock_renderer):
        """Test surface statistics calculation."""
        multi_renderer = MultiSurfaceRenderer(mock_renderer)

        result = MultiSurfaceResult(
            surface_results={
                "left": ProjectionOutputResult(total_frames=1),
                "right": ProjectionOutputResult(total_frames=1),
            },
            combined_result=ProjectionOutputResult(total_frames=2),
        )

        stats = multi_renderer.get_surface_statistics(result)

        assert stats["surface_count"] == 2
        assert "left" in stats["surfaces"]
        assert "right" in stats["surfaces"]
        assert stats["combined"] is not None


class TestEnumCoverage:
    """Tests to ensure enum coverage."""

    def test_all_output_formats_covered(self):
        """Test all output formats are accessible."""
        formats = [OutputFormat.IMAGE_SEQUENCE, OutputFormat.VIDEO, OutputFormat.EXR, OutputFormat.PNG]
        assert len(formats) == 4

    def test_all_color_spaces_covered(self):
        """Test all color spaces are accessible."""
        spaces = [ColorSpace.SRGB, ColorSpace.REC709, ColorSpace.REC2020, ColorSpace.ACES, ColorSpace.FILMIC]
        assert len(spaces) == 5

    def test_all_video_codecs_covered(self):
        """Test all video codecs are accessible."""
        codecs = [VideoCodec.H264, VideoCodec.H265, VideoCodec.PRORES, VideoCodec.DNXHD]
        assert len(codecs) == 4

    def test_all_exr_codecs_covered(self):
        """Test all EXR codecs are accessible."""
        codecs = [EXRCodec.NONE, EXRCodec.ZIP, EXRCodec.PIZ, EXRCodec.RLE,
                  EXRCodec.ZIPS, EXRCodec.B44, EXRCodec.B44A, EXRCodec.DWAA, EXRCodec.DWAB]
        assert len(codecs) == 9
