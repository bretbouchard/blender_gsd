"""
Unit tests for Camera Calibration module.

Tests camera profiles, lens distortion models, and profile management.
"""

import pytest
import sys
import math
import tempfile
import os
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.calibration import (
    DistortionCoefficients,
    LensDistortion,
    CameraProfileManager,
    get_profile_manager,
    get_camera_profile,
)
from cinematic.tracking.types import CameraProfile
from oracle import Oracle


class TestDistortionCoefficients:
    """Tests for DistortionCoefficients dataclass."""

    def test_create_default(self):
        """Test creating coefficients with defaults."""
        coeffs = DistortionCoefficients()
        Oracle.assert_equal(coeffs.k1, 0.0)
        Oracle.assert_equal(coeffs.k2, 0.0)
        Oracle.assert_equal(coeffs.k3, 0.0)
        Oracle.assert_equal(coeffs.p1, 0.0)
        Oracle.assert_equal(coeffs.p2, 0.0)
        Oracle.assert_equal(coeffs.cx, 0.0)
        Oracle.assert_equal(coeffs.cy, 0.0)

    def test_create_full(self):
        """Test creating coefficients with all values."""
        coeffs = DistortionCoefficients(
            k1=-0.025,
            k2=0.012,
            k3=-0.003,
            p1=0.001,
            p2=-0.001,
            cx=0.0005,
            cy=-0.0003,
        )
        Oracle.assert_equal(coeffs.k1, -0.025)
        Oracle.assert_equal(coeffs.k2, 0.012)
        Oracle.assert_equal(coeffs.k3, -0.003)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = DistortionCoefficients(
            k1=-0.05,
            k2=0.02,
            p1=0.001,
            cx=0.0001,
        )
        data = original.to_dict()
        restored = DistortionCoefficients.from_dict(data)

        Oracle.assert_equal(restored.k1, original.k1)
        Oracle.assert_equal(restored.k2, original.k2)
        Oracle.assert_equal(restored.p1, original.p1)
        Oracle.assert_equal(restored.cx, original.cx)

    def test_from_profile(self):
        """Test creating from CameraProfile."""
        profile = CameraProfile(
            name="Test",
            k1=-0.01,
            k2=0.005,
            p1=0.0002,
            cx=0.001,
        )
        coeffs = DistortionCoefficients.from_profile(profile)

        Oracle.assert_equal(coeffs.k1, -0.01)
        Oracle.assert_equal(coeffs.k2, 0.005)
        Oracle.assert_equal(coeffs.p1, 0.0002)
        Oracle.assert_equal(coeffs.cx, 0.001)


class TestLensDistortion:
    """Tests for LensDistortion utility class."""

    def test_apply_brown_conrady_no_distortion(self):
        """Test that no distortion coefficients leaves coords unchanged."""
        coeffs = DistortionCoefficients(k1=0, k2=0, k3=0, p1=0, p2=0)
        x, y = 0.5, 0.3

        x_dist, y_dist = LensDistortion.apply_brown_conrady(x, y, coeffs)

        Oracle.assert_equal(round(x_dist, 6), x)
        Oracle.assert_equal(round(y_dist, 6), y)

    def test_apply_brown_conrady_radial_only(self):
        """Test radial distortion only."""
        coeffs = DistortionCoefficients(k1=-0.1, k2=0.05)
        x, y = 0.5, 0.5  # Diagonal point

        x_dist, y_dist = LensDistortion.apply_brown_conrady(x, y, coeffs)

        # Should apply barrel distortion (negative k1)
        # Distance from center should change
        r_orig = math.sqrt(x * x + y * y)
        r_dist = math.sqrt(x_dist * x_dist + y_dist * y_dist)

        # With negative k1, points should move inward (barrel)
        Oracle.assert_not_equal(r_dist, r_orig)

    def test_remove_brown_conrady_inverse(self):
        """Test that undistort is inverse of distort."""
        coeffs = DistortionCoefficients(k1=-0.02, k2=0.01)
        x_orig, y_orig = 0.3, 0.4

        # Apply distortion
        x_dist, y_dist = LensDistortion.apply_brown_conrady(x_orig, y_orig, coeffs)

        # Remove distortion
        x_undist, y_undist = LensDistortion.remove_brown_conrady(x_dist, y_dist, coeffs)

        # Should return to approximately original
        Oracle.assert_less_than(abs(x_undist - x_orig), 0.001)
        Oracle.assert_less_than(abs(y_undist - y_orig), 0.001)

    def test_apply_simple_radial(self):
        """Test simple radial distortion."""
        x, y = 0.5, 0.5
        k1 = -0.1

        x_dist, y_dist = LensDistortion.apply_simple_radial(x, y, k1)

        # Should apply distortion
        Oracle.assert_not_equal(x_dist, x)
        Oracle.assert_not_equal(y_dist, y)

    def test_apply_simple_radial_no_distortion(self):
        """Test simple radial with no distortion."""
        x, y = 0.3, 0.7

        x_dist, y_dist = LensDistortion.apply_simple_radial(x, y, 0.0, 0.0)

        Oracle.assert_equal(x_dist, x)
        Oracle.assert_equal(y_dist, y)


class TestCameraProfileManager:
    """Tests for CameraProfileManager class."""

    def test_create_default(self):
        """Test creating manager with built-in profiles."""
        manager = CameraProfileManager()
        Oracle.assert_greater_than(len(manager._profiles), 0)

    def test_get_builtin_profile(self):
        """Test getting a built-in profile."""
        manager = CameraProfileManager()
        profile = manager.get_profile("iphone_15_pro_main")

        Oracle.assert_not_none(profile)
        Oracle.assert_equal(profile.manufacturer, "Apple")

    def test_get_profile_case_insensitive(self):
        """Test profile lookup is case insensitive."""
        manager = CameraProfileManager()
        profile = manager.get_profile("IPHONE_15_PRO_MAIN")

        Oracle.assert_not_none(profile)

    def test_get_profile_partial_match(self):
        """Test profile lookup with partial name."""
        manager = CameraProfileManager()
        profile = manager.get_profile("iPhone 15")

        Oracle.assert_not_none(profile)
        Oracle.assert_in("iPhone 15", profile.name)

    def test_get_nonexistent_profile(self):
        """Test getting non-existent profile."""
        manager = CameraProfileManager()
        profile = manager.get_profile("nonexistent_camera")

        Oracle.assert_none(profile)

    def test_list_all_profiles(self):
        """Test listing all profiles."""
        manager = CameraProfileManager()
        profiles = manager.list_profiles()

        Oracle.assert_greater_than(len(profiles), 0)

    def test_list_profiles_by_manufacturer(self):
        """Test filtering by manufacturer."""
        manager = CameraProfileManager()
        profiles = manager.list_profiles(manufacturer="Apple")

        Oracle.assert_greater_than(len(profiles), 0)
        for p in profiles:
            Oracle.assert_equal(p.manufacturer, "Apple")

    def test_list_manufacturers(self):
        """Test getting unique manufacturers."""
        manager = CameraProfileManager()
        manufacturers = manager.list_manufacturers()

        Oracle.assert_in("Apple", manufacturers)
        Oracle.assert_in("RED", manufacturers)
        Oracle.assert_in("Sony", manufacturers)

    def test_add_custom_profile(self):
        """Test adding custom profile."""
        manager = CameraProfileManager()

        custom = CameraProfile(
            name="Custom Camera",
            manufacturer="Test",
            model="Custom",
            sensor_width=36.0,
            sensor_height=24.0,
        )

        manager.add_profile(custom)

        # Should be able to retrieve it
        profile = manager.get_profile("Custom Camera")
        Oracle.assert_not_none(profile)

    def test_remove_profile(self):
        """Test removing a profile."""
        manager = CameraProfileManager()

        # Add then remove
        custom = CameraProfile(name="To Remove")
        manager.add_profile(custom)

        result = manager.remove_profile("To Remove")
        Oracle.assert_true(result)

        # Should not find it
        profile = manager.get_profile("To Remove")
        Oracle.assert_none(profile)

    def test_get_distortion_coefficients(self):
        """Test getting distortion coefficients."""
        manager = CameraProfileManager()
        coeffs = manager.get_distortion_coefficients("iphone_15_pro_main")

        Oracle.assert_not_none(coeffs)
        Oracle.assert_not_equal(coeffs.k1, 0.0)  # Should have distortion

    def test_apply_distortion(self):
        """Test applying distortion via profile."""
        manager = CameraProfileManager()

        x, y = 0.5, 0.5
        x_dist, y_dist = manager.apply_distortion(x, y, "gopro_hero_12")

        # GoPro has significant distortion
        Oracle.assert_not_equal(x_dist, x)

    def test_remove_distortion(self):
        """Test removing distortion via profile."""
        manager = CameraProfileManager()

        x, y = 0.3, 0.4
        # Apply then remove
        x_dist, y_dist = manager.apply_distortion(x, y, "gopro_hero_12")
        x_undist, y_undist = manager.remove_distortion(x_dist, y_dist, "gopro_hero_12")

        # Should approximately return
        Oracle.assert_less_than(abs(x_undist - x), 0.05)
        Oracle.assert_less_than(abs(y_undist - y), 0.05)

    def test_find_matching_profile(self):
        """Test finding profile by sensor dimensions."""
        manager = CameraProfileManager()

        # Full frame dimensions
        profile = manager.find_matching_profile(36.0, 24.0, tolerance=1.0)

        Oracle.assert_not_none(profile)

    def test_load_custom_profiles_file(self):
        """Test loading profiles from YAML file."""
        manager = CameraProfileManager()

        # Create temp YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
camera_profiles:
  test_custom:
    name: Test Custom Profile
    manufacturer: Test
    model: Custom
    sensor_width: 24.0
    sensor_height: 18.0
    focal_length: 50.0
    crop_factor: 1.5
    distortion_model: none
""")
            temp_path = f.name

        try:
            count = manager.load_custom_profiles(temp_path)
            Oracle.assert_equal(count, 1)

            profile = manager.get_profile("test_custom")
            Oracle.assert_not_none(profile)
            Oracle.assert_equal(profile.manufacturer, "Test")

        finally:
            os.unlink(temp_path)

    def test_save_profiles(self):
        """Test saving profiles to file."""
        manager = CameraProfileManager()

        # Add a custom profile
        custom = CameraProfile(
            name="Save Test",
            manufacturer="Test",
            model="Save",
            sensor_width=36.0,
            sensor_height=24.0,
        )
        manager.add_profile(custom)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            result = manager.save_profiles(temp_path, include_builtin=False)
            Oracle.assert_true(result)

            # Verify file was created
            Oracle.assert_true(os.path.exists(temp_path))

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_profile_manager_singleton(self):
        """Test that get_profile_manager returns singleton."""
        manager1 = get_profile_manager()
        manager2 = get_profile_manager()

        Oracle.assert_equal(id(manager1), id(manager2))

    def test_get_camera_profile(self):
        """Test convenience function for getting profile."""
        profile = get_camera_profile("red_komodo")

        Oracle.assert_not_none(profile)
        Oracle.assert_equal(profile.manufacturer, "RED")


class TestBuiltInProfiles:
    """Tests for specific built-in profiles."""

    def test_iphone_profiles_exist(self):
        """Test that iPhone profiles are available."""
        manager = CameraProfileManager()

        iphone_profiles = manager.list_profiles(manufacturer="Apple")
        Oracle.assert_greater_than_or_equal(len(iphone_profiles), 4)

    def test_cinema_camera_profiles_exist(self):
        """Test that cinema camera profiles are available."""
        manager = CameraProfileManager()

        red_profiles = manager.list_profiles(manufacturer="RED")
        Oracle.assert_greater_than_or_equal(len(red_profiles), 1)

        arri_profiles = manager.list_profiles(manufacturer="ARRI")
        Oracle.assert_greater_than_or_equal(len(arri_profiles), 1)

    def test_gopro_profile_has_distortion(self):
        """Test that GoPro profile has significant distortion."""
        profile = get_camera_profile("gopro_hero_12")

        Oracle.assert_not_none(profile)
        Oracle.assert_less_than(profile.k1, -0.05)  # Significant negative distortion

    def test_generic_profile_no_distortion(self):
        """Test that generic profile has no distortion."""
        profile = get_camera_profile("generic_full_frame")

        Oracle.assert_not_none(profile)
        Oracle.assert_equal(profile.distortion_model, "none")
        Oracle.assert_equal(profile.k1, 0.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
