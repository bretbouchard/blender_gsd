"""
Tests for CalibrationManager.
"""

import pytest
from lib.cinematic.projection.physical.calibration.manager import CalibrationManager
from lib.cinematic.projection.physical.calibration.types import (
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
)
from lib.cinematic.projection.physical.projector.profiles import ProjectorProfile


class TestCalibrationManager:
    """Tests for CalibrationManager class."""

    @pytest.fixture
    def projector_profile(self):
        """Create sample projector profile."""
        return ProjectorProfile(
            name="Test_Projector",
            manufacturer="Test",
            native_resolution=(1920, 1080),
            throw_ratio=1.0,
            brightness_lumens=2000,
        )

    def test_create_calibration(self, projector_profile):
        """Test creating a calibration."""
        manager = CalibrationManager(projector_profile=projector_profile)

        calibration = manager.create_calibration(
            name="test_calibration",
            calibration_type=CalibrationType.THREE_POINT,
            points=[
                CalibrationPoint((0, 0, 0), (0, 0), "BL"),
                CalibrationPoint((1, 0, 0), (1, 0), "BR"),
                CalibrationPoint((0, 1, 0), (0, 1), "TL"),
            ]
        )

        assert "test_calibration" in manager.calibrations
        assert len(manager.calibrations) == 1

    def test_validate_calibration_success(self, projector_profile):
        """Test validation of valid calibration."""
        manager = CalibrationManager(projector_profile=projector_profile)

        is_valid, errors = manager.validate_calibration(
            CalibrationType.THREE_POINT,
            [
                CalibrationPoint((0, 0, 0), (0, 0), "BL"),
                CalibrationPoint((1, 0, 0), (1, 0), "BR"),
                CalibrationPoint((0, 1, 0), (0, 1), "TL"),
            ]
        )

        assert is_valid
        assert len(errors) == 0

    def test_validate_calibration_collinear_points(self, projector_profile):
        """Test validation fails for collinear points."""
        manager = CalibrationManager(projector_profile=projector_profile)

        # Collinear points (0,0,0), (1,0,0), (2,0,0)
        is_valid, errors = manager.validate_calibration(
            CalibrationType.THREE_POINT,
            [
                CalibrationPoint((0, 0, 0), (0, 0), "P1"),
                CalibrationPoint((1, 0, 0), (1, 0), "P2"),
                CalibrationPoint((2, 0, 0), (2, 0), "P3"),  # Collinear!
            ]
        )

        assert not is_valid
        assert any("collinear" in e for e in errors)

    def test_validate_calibration_wrong_count(self, projector_profile):
        """Test validation fails for wrong point count."""
        manager = CalibrationManager(projector_profile=projector_profile)

        is_valid, errors = manager.validate_calibration(
            CalibrationType.THREE_POINT,
            [
                CalibrationPoint((0, 0, 0), (0, 0), "P1"),
                CalibrationPoint((1, 0, 0), (1, 0), "P2"),
                # Only 2 points
            ]
        )

        assert not is_valid
        assert any("exactly 3" in e.lower() or "3 points" in e.lower() for e in errors)
