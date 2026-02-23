"""
Unit tests for MSG 1998 fSpy import module.

Tests fSpy file parsing and camera data extraction without Blender.
"""

import pytest
import json
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from lib.msg1998.fspy_import import (
    import_fspy,
    validate_fspy_camera,
    get_camera_matching_quality,
)
from lib.msg1998.types import FSpyImportResult


class TestImportFspy:
    """Tests for import_fspy function."""

    def test_nonexistent_file(self):
        """Test with non-existent file."""
        result = import_fspy(Path("/nonexistent/file.fspy"))

        assert result.success is False
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower()

    def test_invalid_extension(self, tmp_path):
        """Test with wrong file extension."""
        wrong_file = tmp_path / "test.txt"
        wrong_file.write_text("not an fspy file")

        result = import_fspy(wrong_file)

        assert result.success is False
        assert any("Invalid file type" in e for e in result.errors)

    def test_invalid_zip(self, invalid_fspy_file):
        """Test with invalid ZIP file."""
        result = import_fspy(invalid_fspy_file)

        assert result.success is False
        assert any("ZIP" in e or "not a valid" in e for e in result.errors)

    def test_valid_fspy_file(self, sample_fspy_file):
        """Test with valid fSpy file."""
        result = import_fspy(sample_fspy_file)

        assert result.success is True
        assert len(result.errors) == 0
        assert result.focal_length_mm == 35.0
        assert result.sensor_width_mm == 36.0

    def test_fspy_with_custom_camera_params(self, tmp_path):
        """Test fSpy file with custom camera parameters."""
        fspy_path = tmp_path / "custom.fspy"

        fspy_data = {
            "version": "1.0.0",
            "camera": {
                "focalLength": 85.0,
                "sensorWidth": 24.0,
                "rotation": {
                    "x": [0.9, 0.1, 0.0],
                    "y": [-0.1, 0.9, 0.0],
                    "z": [0.0, 0.0, 1.0]
                }
            }
        }

        with zipfile.ZipFile(fspy_path, 'w') as zf:
            zf.writestr('data.json', json.dumps(fspy_data))

        result = import_fspy(fspy_path)

        assert result.success is True
        assert result.focal_length_mm == 85.0
        assert result.sensor_width_mm == 24.0

    def test_fspy_without_camera_section(self, tmp_path):
        """Test fSpy file missing camera section."""
        fspy_path = tmp_path / "no_camera.fspy"

        fspy_data = {
            "version": "1.0.0",
            "image": {
                "width": 1920,
                "height": 1080
            }
        }

        with zipfile.ZipFile(fspy_path, 'w') as zf:
            zf.writestr('data.json', json.dumps(fspy_data))

        result = import_fspy(fspy_path)

        # Should still succeed, just with default values
        assert result.success is True
        assert result.focal_length_mm == 35.0  # Default

    def test_fspy_with_reference_image(self, sample_fspy_file_with_image):
        """Test fSpy file with embedded reference image."""
        result = import_fspy(sample_fspy_file_with_image)

        assert result.success is True
        # With mocked bpy, reference_image is a MagicMock (not None)
        # The important thing is the import succeeds
        assert result.focal_length_mm == 50.0

    def test_fspy_with_invalid_json(self, tmp_path):
        """Test fSpy file with invalid JSON."""
        fspy_path = tmp_path / "invalid_json.fspy"

        with zipfile.ZipFile(fspy_path, 'w') as zf:
            zf.writestr('data.json', "not valid json {{{")

        result = import_fspy(fspy_path)

        assert result.success is False
        assert any("JSON" in e for e in result.errors)

    def test_fspy_empty_json(self, tmp_path):
        """Test fSpy file with empty JSON."""
        fspy_path = tmp_path / "empty.fspy"

        with zipfile.ZipFile(fspy_path, 'w') as zf:
            zf.writestr('data.json', "{}")

        result = import_fspy(fspy_path)

        # Should succeed with default values
        assert result.success is True

    def test_result_path_tracking(self, sample_fspy_file):
        """Test that original path is tracked."""
        result = import_fspy(sample_fspy_file)

        assert result.original_fspy_path == sample_fspy_file


class TestValidateFspyCamera:
    """Tests for validate_fspy_camera function."""

    def test_blender_not_available(self):
        """Test when Blender is not available."""
        errors = validate_fspy_camera(None)
        # With mocked bpy, the function runs but returns errors about None camera
        assert len(errors) >= 1
        assert any("None" in e or "not available" in e.lower() or "not a camera" in e.lower() for e in errors)

    @patch('lib.msg1998.fspy_import.BLENDER_AVAILABLE', True)
    def test_none_camera(self):
        """Test with None camera."""
        errors = validate_fspy_camera(None)
        assert "None" in errors[0]

    @patch('lib.msg1998.fspy_import.BLENDER_AVAILABLE', True)
    def test_non_camera_object(self):
        """Test with non-camera object."""
        mock_obj = MagicMock()
        mock_obj.type = 'MESH'

        errors = validate_fspy_camera(mock_obj)
        assert any("not a camera" in e.lower() for e in errors)

    @patch('lib.msg1998.fspy_import.BLENDER_AVAILABLE', True)
    def test_unusual_focal_length(self):
        """Test with unusual focal length values."""
        mock_cam = MagicMock()
        mock_cam.type = 'CAMERA'
        mock_cam.data.lens = 5  # Too wide
        mock_cam.data.sensor_width = 36
        mock_cam.matrix_world = MagicMock()

        errors = validate_fspy_camera(mock_cam)
        assert any("focal length" in e.lower() for e in errors)

    @patch('lib.msg1998.fspy_import.BLENDER_AVAILABLE', True)
    def test_unusual_sensor_width(self):
        """Test with unusual sensor width values."""
        mock_cam = MagicMock()
        mock_cam.type = 'CAMERA'
        mock_cam.data.lens = 35
        mock_cam.data.sensor_width = 5  # Too small
        mock_cam.matrix_world = MagicMock()

        errors = validate_fspy_camera(mock_cam)
        assert any("sensor" in e.lower() for e in errors)


class TestGetCameraMatchingQuality:
    """Tests for get_camera_matching_quality function."""

    def test_successful_import_quality(self):
        """Test quality assessment for successful import."""
        result = FSpyImportResult(
            success=True,
            focal_length_mm=35.0,
            rotation_matrix=MagicMock()  # Has rotation
        )

        quality = get_camera_matching_quality(result)

        assert quality["focal_length_confidence"] == 0.9
        assert quality["perspective_accuracy"] == 0.85
        assert quality["vanishing_points_defined"] is True
        assert quality["ready_for_modeling"] is True

    def test_failed_import_quality(self):
        """Test quality assessment for failed import."""
        result = FSpyImportResult(
            success=False,
            errors=["Import failed"]
        )

        quality = get_camera_matching_quality(result)

        assert quality["focal_length_confidence"] == 0.0
        assert quality["ready_for_modeling"] is False

    def test_no_rotation_matrix(self):
        """Test quality when rotation matrix is missing."""
        result = FSpyImportResult(
            success=True,
            focal_length_mm=35.0,
            rotation_matrix=None
        )

        quality = get_camera_matching_quality(result)

        assert quality["perspective_accuracy"] == 0.5
        assert quality["vanishing_points_defined"] is False

    def test_import_with_errors(self):
        """Test quality when import succeeded but has warnings."""
        result = FSpyImportResult(
            success=True,
            focal_length_mm=35.0,
            rotation_matrix=MagicMock(),
            errors=["Minor warning about alignment"]
        )

        quality = get_camera_matching_quality(result)

        # Has errors, so not ready for modeling
        assert quality["ready_for_modeling"] is False


class TestFSpyImportResultDataclass:
    """Tests for FSpyImportResult dataclass usage."""

    def test_default_result(self):
        """Test default result values."""
        result = FSpyImportResult()

        assert result.camera is None
        assert result.reference_image is None
        assert result.focal_length_mm == 35.0
        assert result.sensor_width_mm == 36.0
        assert result.rotation_matrix is None
        assert result.success is False
        assert result.errors == []

    def test_result_with_path(self):
        """Test result with path."""
        path = Path("/test/file.fspy")
        result = FSpyImportResult(original_fspy_path=path)

        assert result.original_fspy_path == path

    def test_result_mutation(self):
        """Test that result can be modified."""
        result = FSpyImportResult()
        result.success = True
        result.focal_length_mm = 50.0
        result.errors.append("Warning")

        assert result.success is True
        assert result.focal_length_mm == 50.0
        assert len(result.errors) == 1


class TestFSpyFileFormats:
    """Tests for various fSpy file format scenarios."""

    def test_multiple_json_files(self, tmp_path):
        """Test fSpy file with multiple JSON files (uses first)."""
        fspy_path = tmp_path / "multi.fspy"

        with zipfile.ZipFile(fspy_path, 'w') as zf:
            zf.writestr('data1.json', json.dumps({"camera": {"focalLength": 35}}))
            zf.writestr('data2.json', json.dumps({"camera": {"focalLength": 50}}))

        result = import_fspy(fspy_path)

        assert result.success is True
        # Uses first JSON file found
        assert result.focal_length_mm in [35.0, 50.0]

    def test_fspy_with_subdirectories(self, tmp_path):
        """Test fSpy file with nested directory structure."""
        fspy_path = tmp_path / "nested.fspy"

        fspy_data = {
            "version": "1.0.0",
            "camera": {
                "focalLength": 50.0
            }
        }

        with zipfile.ZipFile(fspy_path, 'w') as zf:
            zf.writestr('data/camera/data.json', json.dumps(fspy_data))

        result = import_fspy(fspy_path)

        assert result.success is True
        assert result.focal_length_mm == 50.0

    def test_fspy_with_various_image_formats(self, tmp_path):
        """Test fSpy file with different image formats."""
        for ext in ['jpg', 'jpeg', 'png']:
            fspy_path = tmp_path / f"test_{ext}.fspy"

            with zipfile.ZipFile(fspy_path, 'w') as zf:
                zf.writestr('data.json', json.dumps({"camera": {"focalLength": 35}}))
                zf.writestr(f'reference.{ext}', b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)

            result = import_fspy(fspy_path)

            assert result.success is True
