"""
Tests for calibration types and configuration.
"""

import pytest
from datetime import datetime

from lib.cinematic.projection.physical.calibration.types import (
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
    CalibrationPattern,
    PatternType,
    CHECKERBOARD_STANDARD,
    CHECKERBOARD_FINE,
    COLOR_BARS_SMpte,
    GRID_100PX,
    GRADIENT_HORIZONTAL,
)


class TestCalibrationPoint:
    """Tests for CalibrationPoint dataclass."""

    def test_create_calibration_point(self):
        """Test creating a calibration point."""
        point = CalibrationPoint(
            world_position=(1.0, 2.0, 3.0),
            projector_uv=(0.5, 0.5),
            label="Center"
        )

        assert point.world_position == (1.0, 2.0, 3.0)
        assert point.projector_uv == (0.5, 0.5)
        assert point.label == "Center"

    def test_calibration_point_to_dict(self):
        """Test serialization to dictionary."""
        point = CalibrationPoint(
            world_position=(1.0, 2.0, 3.0),
            projector_uv=(0.5, 0.5),
            label="Center"
        )

        data = point.to_dict()

        assert data['world_position'] == [1.0, 2.0, 3.0]
        assert data['projector_uv'] == [0.5, 0.5]
        assert data['label'] == "Center"

    def test_calibration_point_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'world_position': [1.0, 2.0, 3.0],
            'projector_uv': [0.5, 0.5],
            'label': "Center"
        }

        point = CalibrationPoint.from_dict(data)

        assert point.world_position == (1.0, 2.0, 3.0)
        assert point.projector_uv == (0.5, 0.5)
        assert point.label == "Center"

    def test_calibration_point_round_trip(self):
        """Test serialization round trip."""
        original = CalibrationPoint(
            world_position=(1.5, 2.5, 3.5),
            projector_uv=(0.25, 0.75),
            label="Test Point"
        )

        data = original.to_dict()
        restored = CalibrationPoint.from_dict(data)

        assert restored.world_position == original.world_position
        assert restored.projector_uv == original.projector_uv
        assert restored.label == original.label


class TestSurfaceCalibration:
    """Tests for SurfaceCalibration dataclass."""

    def test_create_surface_calibration(self):
        """Test creating a surface calibration."""
        calibration = SurfaceCalibration(
            name="test_calibration",
            calibration_type=CalibrationType.THREE_POINT,
        )

        assert calibration.name == "test_calibration"
        assert calibration.calibration_type == CalibrationType.THREE_POINT
        assert len(calibration.points) == 0
        assert not calibration.is_calibrated

    def test_add_point(self):
        """Test adding calibration points."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
        )

        point = calibration.add_point(
            world_position=(0, 0, 0),
            projector_uv=(0, 0),
            label="Origin"
        )

        assert len(calibration.points) == 1
        assert calibration.points[0] == point
        assert point.world_position == (0, 0, 0)

    def test_clear_calibration(self):
        """Test clearing calibration data."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
            transform_matrix=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            calibration_error=0.5,
            is_calibrated=True,
        )

        calibration.clear_calibration()

        assert calibration.transform_matrix is None
        assert calibration.calibration_error == 0.0
        assert not calibration.is_calibrated

    def test_validate_three_point_success(self):
        """Test validation of valid 3-point calibration."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
        )

        calibration.add_point((0, 0, 0), (0, 0), "BL")
        calibration.add_point((1, 0, 0), (1, 0), "BR")
        calibration.add_point((0, 1, 0), (0, 1), "TL")

        is_valid, errors = calibration.validate()

        assert is_valid
        assert len(errors) == 0

    def test_validate_three_point_wrong_count(self):
        """Test validation fails with wrong point count."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
        )

        calibration.add_point((0, 0, 0), (0, 0), "P1")
        calibration.add_point((1, 0, 0), (1, 0), "P2")
        # Only 2 points

        is_valid, errors = calibration.validate()

        assert not is_valid
        assert any("exactly 3 points" in e for e in errors)

    def test_validate_four_point_dlt_success(self):
        """Test validation of valid 4-point DLT calibration."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.FOUR_POINT_DLT,
        )

        calibration.add_point((0, 0, 0), (0, 0), "BL")
        calibration.add_point((1, 0, 0), (1, 0), "BR")
        calibration.add_point((0, 1, 0), (0, 1), "TL")
        calibration.add_point((1, 1, 0), (1, 1), "TR")

        is_valid, errors = calibration.validate()

        assert is_valid
        assert len(errors) == 0

    def test_validate_four_point_dlt_too_few(self):
        """Test validation fails with too few points for DLT."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.FOUR_POINT_DLT,
        )

        calibration.add_point((0, 0, 0), (0, 0), "P1")
        calibration.add_point((1, 0, 0), (1, 0), "P2")
        calibration.add_point((0, 1, 0), (0, 1), "P3")
        # Only 3 points

        is_valid, errors = calibration.validate()

        assert not is_valid
        assert any("at least 4 points" in e for e in errors)

    def test_validate_uv_out_of_bounds(self):
        """Test validation fails with UV out of bounds."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
        )

        calibration.add_point((0, 0, 0), (0, 0), "P1")
        calibration.add_point((1, 0, 0), (1.5, 0), "P2")  # UV out of bounds
        calibration.add_point((0, 1, 0), (0, 1), "P3")

        is_valid, errors = calibration.validate()

        assert not is_valid
        assert any("out of bounds" in e for e in errors)

    def test_validate_duplicate_world_positions(self):
        """Test validation fails with duplicate world positions."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
        )

        calibration.add_point((0, 0, 0), (0, 0), "P1")
        calibration.add_point((0, 0, 0), (1, 0), "P2")  # Same world position
        calibration.add_point((0, 1, 0), (0, 1), "P3")

        is_valid, errors = calibration.validate()

        assert not is_valid
        assert any("Duplicate world positions" in e for e in errors)

    def test_surface_calibration_to_dict(self):
        """Test serialization to dictionary."""
        calibration = SurfaceCalibration(
            name="test",
            calibration_type=CalibrationType.THREE_POINT,
        )
        calibration.add_point((0, 0, 0), (0, 0), "P1")
        calibration.add_point((1, 0, 0), (1, 0), "P2")
        calibration.add_point((0, 1, 0), (0, 1), "P3")

        data = calibration.to_dict()

        assert data['name'] == "test"
        assert data['calibration_type'] == "three_point"
        assert len(data['points']) == 3

    def test_surface_calibration_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'name': 'restored_calibration',
            'calibration_type': 'four_point_dlt',
            'points': [
                {'world_position': [0, 0, 0], 'projector_uv': [0, 0], 'label': 'P1'},
                {'world_position': [1, 0, 0], 'projector_uv': [1, 0], 'label': 'P2'},
                {'world_position': [0, 1, 0], 'projector_uv': [0, 1], 'label': 'P3'},
                {'world_position': [1, 1, 0], 'projector_uv': [1, 1], 'label': 'P4'},
            ],
            'is_calibrated': True,
            'calibration_error': 0.5,
        }

        calibration = SurfaceCalibration.from_dict(data)

        assert calibration.name == 'restored_calibration'
        assert calibration.calibration_type == CalibrationType.FOUR_POINT_DLT
        assert len(calibration.points) == 4
        assert calibration.is_calibrated


class TestCalibrationPattern:
    """Tests for CalibrationPattern dataclass."""

    def test_create_calibration_pattern(self):
        """Test creating a calibration pattern."""
        pattern = CalibrationPattern(
            name="test_checkerboard",
            pattern_type=PatternType.CHECKERBOARD,
            resolution=(1920, 1080),
            grid_size=8,
        )

        assert pattern.name == "test_checkerboard"
        assert pattern.pattern_type == PatternType.CHECKERBOARD
        assert pattern.resolution == (1920, 1080)
        assert pattern.grid_size == 8

    def test_preset_patterns(self):
        """Test preset patterns are defined correctly."""
        assert CHECKERBOARD_STANDARD.grid_size == 8
        assert CHECKERBOARD_FINE.grid_size == 16
        assert COLOR_BARS_SMpte.smpte_standard == True
        assert GRID_100PX.spacing == 100
        assert GRADIENT_HORIZONTAL.pattern_type == PatternType.GRADIENT

    def test_calibration_pattern_to_dict(self):
        """Test pattern serialization."""
        pattern = CalibrationPattern(
            name="test",
            pattern_type=PatternType.GRID,
            resolution=(1920, 1080),
            spacing=50,
        )

        data = pattern.to_dict()

        assert data['name'] == "test"
        assert data['pattern_type'] == "grid"
        assert data['spacing'] == 50

    def test_calibration_pattern_from_dict(self):
        """Test pattern deserialization."""
        data = {
            'name': 'restored_pattern',
            'pattern_type': 'checkerboard',
            'resolution': [3840, 2160],
            'grid_size': 12,
        }

        pattern = CalibrationPattern.from_dict(data)

        assert pattern.name == 'restored_pattern'
        assert pattern.pattern_type == PatternType.CHECKERBOARD
        assert pattern.resolution == (3840, 2160)
        assert pattern.grid_size == 12


class TestCalibrationTypeEnum:
    """Tests for calibration type enum."""

    def test_calibration_type_values(self):
        """Test enum values."""
        assert CalibrationType.THREE_POINT.value == "three_point"
        assert CalibrationType.FOUR_POINT_DLT.value == "four_point_dlt"

    def test_pattern_type_values(self):
        """Test pattern type enum values."""
        assert PatternType.CHECKERBOARD.value == "checkerboard"
        assert PatternType.COLOR_BARS.value == "color_bars"
        assert PatternType.GRID.value == "grid"
        assert PatternType.CROSSHAIR.value == "crosshair"
        assert PatternType.GRADIENT.value == "gradient"
