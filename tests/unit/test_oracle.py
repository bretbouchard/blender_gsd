"""
Oracle Validation Unit Tests

Tests for: lib/oracle.py
Coverage target: 90%+
"""

import pytest
import subprocess
import tempfile
from pathlib import Path

from lib.oracle import (
    compare_numbers,
    compare_numbers_relative,
    compare_within_range,
    compare_vectors,
    compare_vectors_length,
    file_exists,
    directory_exists,
    files_exist,
    exit_code_zero,
    no_stderr,
    all_pass,
)


class TestCompareNumbers:
    """Unit tests for compare_numbers function."""

    def test_exact_match(self):
        """Exact values should pass."""
        assert compare_numbers(5.0, 5.0) is True

    def test_within_tolerance(self):
        """Values within tolerance should pass."""
        assert compare_numbers(5.001, 5.0, tolerance=0.01) is True
        assert compare_numbers(5.009, 5.0, tolerance=0.01) is True

    def test_at_tolerance_boundary(self):
        """Values exactly at tolerance boundary should pass."""
        assert compare_numbers(5.01, 5.0, tolerance=0.01) is True

    def test_exceeds_tolerance(self):
        """Values exceeding tolerance should raise AssertionError."""
        with pytest.raises(AssertionError) as exc_info:
            compare_numbers(5.1, 5.0, tolerance=0.01)

        assert "Number mismatch" in str(exc_info.value)
        assert "actual=5.1" in str(exc_info.value)
        assert "expected=5.0" in str(exc_info.value)

    def test_custom_message(self):
        """Custom message should appear in error."""
        with pytest.raises(AssertionError) as exc_info:
            compare_numbers(5.1, 5.0, tolerance=0.01, message="Camera focal length")

        assert "Camera focal length" in str(exc_info.value)

    def test_negative_numbers(self):
        """Negative numbers should be handled correctly."""
        assert compare_numbers(-5.001, -5.0, tolerance=0.01) is True

    def test_zero_values(self):
        """Zero values should be handled correctly."""
        assert compare_numbers(0.0, 0.0) is True
        assert compare_numbers(0.0001, 0.0, tolerance=0.001) is True


class TestCompareNumbersRelative:
    """Unit tests for compare_numbers_relative function."""

    def test_exact_match(self):
        """Exact values should pass."""
        assert compare_numbers_relative(100.0, 100.0) is True

    def test_within_percent_tolerance(self):
        """Values within percentage tolerance should pass."""
        assert compare_numbers_relative(101.0, 100.0, tolerance_percent=2.0) is True
        assert compare_numbers_relative(99.0, 100.0, tolerance_percent=2.0) is True

    def test_exceeds_percent_tolerance(self):
        """Values exceeding percentage tolerance should raise."""
        with pytest.raises(AssertionError) as exc_info:
            compare_numbers_relative(105.0, 100.0, tolerance_percent=2.0)

        assert "diff=5.00%" in str(exc_info.value)

    def test_zero_expected(self):
        """Zero expected value should fall back to absolute tolerance."""
        assert compare_numbers_relative(0.0001, 0.0) is True

        with pytest.raises(AssertionError):
            compare_numbers_relative(0.1, 0.0)


class TestCompareWithinRange:
    """Unit tests for compare_within_range function."""

    def test_value_in_range(self):
        """Values within range should pass."""
        assert compare_within_range(5.0, 0.0, 10.0) is True
        assert compare_within_range(0.0, 0.0, 10.0) is True  # At min
        assert compare_within_range(10.0, 0.0, 10.0) is True  # At max

    def test_value_below_range(self):
        """Values below range should raise."""
        with pytest.raises(AssertionError) as exc_info:
            compare_within_range(-1.0, 0.0, 10.0)

        assert "out of range" in str(exc_info.value)

    def test_value_above_range(self):
        """Values above range should raise."""
        with pytest.raises(AssertionError) as exc_info:
            compare_within_range(15.0, 0.0, 10.0)

        assert "out of range" in str(exc_info.value)


class TestCompareVectors:
    """Unit tests for compare_vectors function."""

    def test_exact_match(self):
        """Exact vectors should pass."""
        assert compare_vectors((1.0, 2.0, 3.0), (1.0, 2.0, 3.0)) is True

    def test_within_tolerance(self):
        """Vectors within tolerance should pass."""
        assert compare_vectors((1.001, 2.0, 3.0), (1.0, 2.0, 3.0), tolerance=0.01) is True

    def test_length_mismatch(self):
        """Different length vectors should raise."""
        with pytest.raises(AssertionError) as exc_info:
            compare_vectors((1.0, 2.0), (1.0, 2.0, 3.0))

        assert "length mismatch" in str(exc_info.value)

    def test_component_mismatch(self):
        """Component mismatch should raise with index."""
        with pytest.raises(AssertionError) as exc_info:
            compare_vectors((1.0, 2.5, 3.0), (1.0, 2.0, 3.0), tolerance=0.01)

        assert "component 1" in str(exc_info.value)

    def test_2d_vectors(self):
        """2D vectors should work."""
        assert compare_vectors((1.0, 2.0), (1.0, 2.0)) is True

    def test_4d_vectors(self):
        """4D vectors should work."""
        assert compare_vectors((1.0, 2.0, 3.0, 4.0), (1.0, 2.0, 3.0, 4.0)) is True


class TestCompareVectorsLength:
    """Unit tests for compare_vectors_length function."""

    def test_unit_vector(self):
        """Unit vector length should be 1.0."""
        assert compare_vectors_length((1.0, 0.0, 0.0), 1.0) is True
        assert compare_vectors_length((0.0, 1.0, 0.0), 1.0) is True

    def test_scaled_vector(self):
        """Scaled vector length should scale accordingly."""
        assert compare_vectors_length((2.0, 0.0, 0.0), 2.0) is True
        assert compare_vectors_length((3.0, 4.0, 0.0), 5.0) is True  # 3-4-5 triangle

    def test_zero_vector(self):
        """Zero vector length should be 0."""
        assert compare_vectors_length((0.0, 0.0, 0.0), 0.0) is True


class TestFileExists:
    """Unit tests for file_exists function."""

    def test_existing_file(self, tmp_path):
        """Existing file should pass."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        assert file_exists(test_file) is True

    def test_missing_file(self, tmp_path):
        """Missing file should raise."""
        test_file = tmp_path / "missing.txt"

        with pytest.raises(AssertionError) as exc_info:
            file_exists(test_file)

        assert "does not exist" in str(exc_info.value)

    def test_empty_file_fails(self, tmp_path):
        """Empty file should fail when check_non_empty=True."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()

        with pytest.raises(AssertionError) as exc_info:
            file_exists(test_file)

        assert "is empty" in str(exc_info.value)

    def test_empty_file_allowed(self, tmp_path):
        """Empty file should pass when check_non_empty=False."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()

        assert file_exists(test_file, check_non_empty=False) is True

    def test_custom_file_type(self, tmp_path):
        """Custom file type should appear in error."""
        test_file = tmp_path / "render.png"

        with pytest.raises(AssertionError) as exc_info:
            file_exists(test_file, file_type="Render output")

        assert "Render output" in str(exc_info.value)


class TestDirectoryExists:
    """Unit tests for directory_exists function."""

    def test_existing_directory(self, tmp_path):
        """Existing directory should pass."""
        assert directory_exists(tmp_path) is True

    def test_missing_directory(self, tmp_path):
        """Missing directory should raise."""
        missing = tmp_path / "missing"

        with pytest.raises(AssertionError) as exc_info:
            directory_exists(missing)

        assert "does not exist" in str(exc_info.value)

    def test_file_not_directory(self, tmp_path):
        """File path should raise 'not a directory' error."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        with pytest.raises(AssertionError) as exc_info:
            directory_exists(test_file)

        assert "not a directory" in str(exc_info.value)


class TestFilesExist:
    """Unit tests for files_exist function."""

    def test_all_files_exist(self, tmp_path):
        """All existing files should pass."""
        files = []
        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_text("content")
            files.append(f)

        assert files_exist(files) is True

    def test_some_files_missing(self, tmp_path):
        """Missing files should be listed in error."""
        existing = tmp_path / "exists.txt"
        existing.write_text("content")

        with pytest.raises(AssertionError) as exc_info:
            files_exist([existing, tmp_path / "missing1.txt", tmp_path / "missing2.txt"])

        assert "Missing files (2)" in str(exc_info.value)
        assert "missing1.txt" in str(exc_info.value)
        assert "missing2.txt" in str(exc_info.value)

    def test_with_base_dir(self, tmp_path):
        """Base directory should be prepended to relative paths."""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file.txt").write_text("content")

        assert files_exist(["file.txt"], base_dir=tmp_path / "subdir") is True


class TestExitCodeZero:
    """Unit tests for exit_code_zero function."""

    def test_successful_process(self):
        """Process with exit code 0 should pass."""
        result = subprocess.run(["echo", "test"], capture_output=True)
        assert exit_code_zero(result) is True

    def test_failed_process(self):
        """Process with non-zero exit code should raise."""
        result = subprocess.run(["ls", "/nonexistent"], capture_output=True)

        with pytest.raises(AssertionError) as exc_info:
            exit_code_zero(result)

        assert "exit code" in str(exc_info.value)

    def test_context_in_error(self):
        """Context should appear in error message."""
        result = subprocess.run(["ls", "/nonexistent"], capture_output=True)

        with pytest.raises(AssertionError) as exc_info:
            exit_code_zero(result, context="Render process")

        assert "Render process" in str(exc_info.value)


class TestNoStderr:
    """Unit tests for no_stderr function."""

    def test_no_stderr(self):
        """Process with no stderr should pass."""
        result = subprocess.run(["echo", "test"], capture_output=True)
        assert no_stderr(result) is True

    def test_with_stderr(self):
        """Process with stderr should raise."""
        result = subprocess.run(["ls", "/nonexistent"], capture_output=True)

        with pytest.raises(AssertionError) as exc_info:
            no_stderr(result)

        assert "Unexpected stderr" in str(exc_info.value)


class TestAllPass:
    """Unit tests for all_pass function."""

    def test_all_pass(self):
        """All passing validations should pass."""
        validations = [
            lambda: compare_numbers(1.0, 1.0),
            lambda: compare_vectors((1.0, 2.0), (1.0, 2.0)),
        ]
        assert all_pass(validations) is True

    def test_collects_all_failures(self):
        """Should collect all failures, not stop at first."""
        validations = [
            lambda: compare_numbers(1.0, 2.0, tolerance=0.01),
            lambda: compare_numbers(3.0, 4.0, tolerance=0.01),
        ]

        with pytest.raises(AssertionError) as exc_info:
            all_pass(validations)

        assert "Validation failures (2)" in str(exc_info.value)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
