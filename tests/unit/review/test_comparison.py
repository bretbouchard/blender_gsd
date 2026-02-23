"""
Tests for comparison module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_comparison_result_creation(self):
        """Test creating a ComparisonResult."""
        from lib.review.comparison import ComparisonResult

        result = ComparisonResult(
            comparison_id="comp_001",
            source_a="image_a.png",
            source_b="image_b.png",
            difference_score=0.05,
            ssim_score=0.95,
        )

        assert result.comparison_id == "comp_001"
        assert result.source_a == "image_a.png"
        assert result.source_b == "image_b.png"
        assert result.difference_score == 0.05
        assert result.ssim_score == 0.95

    def test_comparison_result_defaults(self):
        """Test ComparisonResult default values."""
        from lib.review.comparison import ComparisonResult

        result = ComparisonResult()
        assert result.comparison_id == ""
        assert result.ssim_score == 1.0
        assert result.difference_score == 0.0
        assert result.regions == []
        assert result.metadata == {}

    def test_is_similar_high_ssim(self):
        """Test is_similar with high SSIM score."""
        from lib.review.comparison import ComparisonResult

        result = ComparisonResult(
            ssim_score=0.98,
            difference_pixels=1.0,
        )
        assert result.is_similar is True

    def test_is_similar_low_ssim(self):
        """Test is_similar with low SSIM score."""
        from lib.review.comparison import ComparisonResult

        result = ComparisonResult(
            ssim_score=0.80,
            difference_pixels=1.0,
        )
        assert result.is_similar is False

    def test_is_similar_high_difference(self):
        """Test is_similar with high difference pixels."""
        from lib.review.comparison import ComparisonResult

        result = ComparisonResult(
            ssim_score=0.98,
            difference_pixels=10.0,  # > 5%
        )
        assert result.is_similar is False

    def test_comparison_result_to_dict(self):
        """Test ComparisonResult serialization."""
        from lib.review.comparison import ComparisonResult

        result = ComparisonResult(
            comparison_id="comp_001",
            source_a="a.png",
            source_b="b.png",
            difference_score=0.1,
        )
        data = result.to_dict()

        assert data["comparison_id"] == "comp_001"
        assert data["source_a"] == "a.png"
        assert data["difference_score"] == 0.1

    def test_comparison_result_from_dict(self):
        """Test ComparisonResult deserialization."""
        from lib.review.comparison import ComparisonResult

        data = {
            "comparison_id": "comp_001",
            "source_a": "a.png",
            "source_b": "b.png",
            "difference_score": 0.1,
            "ssim_score": 0.9,
        }
        result = ComparisonResult.from_dict(data)

        assert result.comparison_id == "comp_001"
        assert result.ssim_score == 0.9


class TestComparisonTool:
    """Tests for ComparisonTool class."""

    def test_tool_creation(self):
        """Test creating a ComparisonTool."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        assert tool is not None
        assert tool.threshold == 0.01

    def test_tool_with_custom_threshold(self):
        """Test creating tool with custom threshold."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool(threshold=0.05)
        assert tool.threshold == 0.05

    def test_compare_missing_source_a(self):
        """Test comparing with missing source A."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        result = tool.compare("nonexistent_a.png", "nonexistent_b.png")

        assert "error" in result.metadata
        assert "Source A not found" in result.metadata["error"]

    def test_compare_missing_source_b(self):
        """Test comparing with missing source B."""
        from lib.review.comparison import ComparisonTool

        # Create temp file for source A
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_a = f.name
            f.write(b"fake image data")

        try:
            tool = ComparisonTool()
            result = tool.compare(temp_a, "nonexistent_b.png")

            assert "error" in result.metadata
            assert "Source B not found" in result.metadata["error"]
        finally:
            os.unlink(temp_a)

    def test_compare_existing_files(self):
        """Test comparing existing files."""
        from lib.review.comparison import ComparisonTool

        # Create temp files
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_a = f.name
            f.write(b"image a data")

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_b = f.name
            f.write(b"image b data")

        try:
            tool = ComparisonTool()
            result = tool.compare(temp_a, temp_b)

            # Should have comparison_id generated
            assert result.comparison_id.startswith("comp_")
            assert result.source_a == temp_a
            assert result.source_b == temp_b
        finally:
            os.unlink(temp_a)
            os.unlink(temp_b)

    def test_compare_directories(self):
        """Test comparing directories."""
        from lib.review.comparison import ComparisonTool

        # Create temp directories with files
        with tempfile.TemporaryDirectory() as dir_a:
            with tempfile.TemporaryDirectory() as dir_b:
                # Create matching files
                path_a = Path(dir_a) / "test.png"
                path_b = Path(dir_b) / "test.png"
                path_a.write_bytes(b"image data")
                path_b.write_bytes(b"image data")

                tool = ComparisonTool()
                results = tool.compare_directories(dir_a, dir_b)

                assert len(results) == 1
                assert results[0].source_a == str(path_a)

    def test_compare_directories_missing(self):
        """Test comparing missing directories."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        results = tool.compare_directories("/nonexistent/a", "/nonexistent/b")

        assert results == []

    def test_generate_diff_image(self):
        """Test generating difference image."""
        from lib.review.comparison import ComparisonTool

        # Create temp files
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_a = f.name
            f.write(b"image a")

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_b = f.name
            f.write(b"image b")

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_diff = f.name

        try:
            tool = ComparisonTool()
            result = tool.generate_diff_image(temp_a, temp_b, temp_diff)
            assert result is True
        finally:
            os.unlink(temp_a)
            os.unlink(temp_b)
            if os.path.exists(temp_diff):
                os.unlink(temp_diff)

    def test_generate_diff_image_missing_source(self):
        """Test generating diff with missing source."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        result = tool.generate_diff_image(
            "/nonexistent/a.png",
            "/nonexistent/b.png",
            "/tmp/diff.png"
        )
        assert result is False

    def test_compare_histograms(self):
        """Test histogram comparison."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        # Compare histograms returns placeholder values
        result = tool.compare_histograms("a.png", "b.png")

        assert "red" in result
        assert "green" in result
        assert "blue" in result
        assert "overall" in result

    def test_find_difference_regions(self):
        """Test finding difference regions."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        # Returns empty list as placeholder
        regions = tool.find_difference_regions("a.png", "b.png")

        assert isinstance(regions, list)

    def test_get_statistics(self):
        """Test getting comparison statistics."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()
        tool._comparison_counter = 5  # Simulate comparisons

        stats = tool.get_statistics()
        assert stats["total_comparisons"] == 5

    def test_comparison_counter_increments(self):
        """Test that comparison counter increments."""
        from lib.review.comparison import ComparisonTool

        tool = ComparisonTool()

        # Do a comparison (will fail but counter should increment)
        tool.compare("/nonexistent/a.png", "/nonexistent/b.png")

        stats = tool.get_statistics()
        assert stats["total_comparisons"] == 1
