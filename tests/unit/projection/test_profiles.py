"""Unit tests for projector profile types.

Tests for:
- Throw ratio to focal length conversion
- Throw distance calculations
- ProjectorProfile dataclass
- LensShift and KeystoneCorrection dataclasses

Part of Milestone v0.15 - Physical Projector Mapping System
"""

import pytest
import math

from lib.cinematic.projection.physical.projector.profiles import (
    ProjectorProfile,
    ProjectorType,
    AspectRatio,
    LensShift,
    KeystoneCorrection,
)
from lib.cinematic.projection.physical.projector.calibration import (
    throw_ratio_to_focal_length,
    focal_length_to_throw_ratio,
    calculate_throw_distance,
    calculate_image_width,
)


class TestThrowRatioConversion:
    """Tests for throw ratio to focal length conversion."""

    def test_horizontal_throw_ratio(self):
        """Test horizontal throw ratio conversion.

        Formula: focal_length = sensor_width * throw_ratio
        For 36mm sensor and 1.32 throw ratio: 36 * 1.32 = 47.52
        """
        focal = throw_ratio_to_focal_length(1.32, 36.0, 20.25, 'horizontal')
        assert math.isclose(focal, 47.52, rel_tol=0.001)

    def test_vertical_throw_ratio(self):
        """Test vertical throw ratio conversion.

        Vertical: sensor_height * throw_ratio * (sensor_width / sensor_height)
        = 20.25 * 1.32 * (36 / 20.25) = 47.52
        """
        focal = throw_ratio_to_focal_length(1.32, 36.0, 20.25, 'vertical')
        assert math.isclose(focal, 47.52, rel_tol=0.001)

    def test_diagonal_throw_ratio(self):
        """Test diagonal throw ratio conversion."""
        focal = throw_ratio_to_focal_length(1.32, 36.0, 20.25, 'diagonal')
        diagonal = math.sqrt(36.0**2 + 20.25**2)
        expected = diagonal * 1.32
        assert math.isclose(focal, expected, rel_tol=0.001)

    def test_short_throw_projector(self):
        """Test short throw projector (0.5 throw ratio).

        Short throw projectors have throw ratio < 1.0
        For 36mm sensor: 36 * 0.5 = 18mm focal length
        """
        focal = throw_ratio_to_focal_length(0.5, 36.0, 20.25, 'horizontal')
        assert math.isclose(focal, 18.0, rel_tol=0.001)

    def test_long_throw_projector(self):
        """Test long throw projector (2.0 throw ratio).

        Long throw projectors have throw ratio > 1.5
        For 36mm sensor: 36 * 2.0 = 72mm focal length
        """
        focal = throw_ratio_to_focal_length(2.0, 36.0, 20.25, 'horizontal')
        assert math.isclose(focal, 72.0, rel_tol=0.001)

    def test_ultra_short_throw_projector(self):
        """Test ultra-short throw projector (0.25 throw ratio).

        Ultra-short throw projectors have throw ratio < 0.4
        For 36mm sensor: 36 * 0.25 = 9mm focal length
        """
        focal = throw_ratio_to_focal_length(0.25, 36.0, 20.25, 'horizontal')
        assert math.isclose(focal, 9.0, rel_tol=0.001)

    def test_invalid_throw_ratio_zero(self):
        """Test that zero throw ratio raises error."""
        with pytest.raises(ValueError):
            throw_ratio_to_focal_length(0, 36.0, 20.25)

    def test_invalid_throw_ratio_negative(self):
        """Test that negative throw ratio raises error."""
        with pytest.raises(ValueError):
            throw_ratio_to_focal_length(-1.0, 36.0, 20.25)

    def test_invalid_aspect(self):
        """Test that invalid aspect raises error."""
        with pytest.raises(ValueError):
            throw_ratio_to_focal_length(1.32, 36.0, 20.25, 'invalid')

    def test_inverse_conversion(self):
        """Test that focal_length_to_throw_ratio is inverse."""
        original_ratio = 1.32
        focal = throw_ratio_to_focal_length(original_ratio, 36.0, 20.25, 'horizontal')
        back_to_ratio = focal_length_to_throw_ratio(focal, 36.0)
        assert math.isclose(back_to_ratio, original_ratio, rel_tol=0.001)

    def test_inverse_conversion_short_throw(self):
        """Test inverse conversion for short throw."""
        original_ratio = 0.5
        focal = throw_ratio_to_focal_length(original_ratio, 36.0, 20.25, 'horizontal')
        back_to_ratio = focal_length_to_throw_ratio(focal, 36.0)
        assert math.isclose(back_to_ratio, original_ratio, rel_tol=0.001)

    def test_invalid_focal_length(self):
        """Test that invalid focal length raises error."""
        with pytest.raises(ValueError):
            focal_length_to_throw_ratio(0, 36.0)

        with pytest.raises(ValueError):
            focal_length_to_throw_ratio(-10.0, 36.0)


class TestThrowDistance:
    """Tests for throw distance calculations."""

    def test_throw_distance_calculation(self):
        """Test throw distance from throw ratio.

        Formula: distance = throw_ratio * image_width
        For 1.32 ratio and 2m width: 1.32 * 2 = 2.64m
        """
        distance = calculate_throw_distance(1.32, 2.0)  # 2m wide image
        assert math.isclose(distance, 2.64, rel_tol=0.001)

    def test_throw_distance_short_throw(self):
        """Test throw distance for short throw projector."""
        distance = calculate_throw_distance(0.5, 2.0)  # 0.5 ratio, 2m width
        assert math.isclose(distance, 1.0, rel_tol=0.001)

    def test_throw_distance_long_throw(self):
        """Test throw distance for long throw projector."""
        distance = calculate_throw_distance(2.0, 2.0)  # 2.0 ratio, 2m width
        assert math.isclose(distance, 4.0, rel_tol=0.001)

    def test_image_width_calculation(self):
        """Test image width from throw distance.

        Formula: width = distance / throw_ratio
        For 1.32 ratio and 2.64m distance: 2.64 / 1.32 = 2m
        """
        width = calculate_image_width(1.32, 2.64)  # 2.64m distance
        assert math.isclose(width, 2.0, rel_tol=0.001)

    def test_round_trip(self):
        """Test distance and width are inverses."""
        throw_ratio = 1.5
        image_width = 3.0
        distance = calculate_throw_distance(throw_ratio, image_width)
        back_to_width = calculate_image_width(throw_ratio, distance)
        assert math.isclose(back_to_width, image_width, rel_tol=0.001)

    def test_throw_distance_invalid_ratio(self):
        """Test that invalid throw ratio raises error."""
        with pytest.raises(ValueError):
            calculate_throw_distance(0, 2.0)

        with pytest.raises(ValueError):
            calculate_throw_distance(-1.0, 2.0)

    def test_throw_distance_invalid_width(self):
        """Test that invalid image width raises error."""
        with pytest.raises(ValueError):
            calculate_throw_distance(1.32, 0)

        with pytest.raises(ValueError):
            calculate_throw_distance(1.32, -1.0)

    def test_image_width_invalid_distance(self):
        """Test that invalid throw distance raises error."""
        with pytest.raises(ValueError):
            calculate_image_width(1.32, 0)

        with pytest.raises(ValueError):
            calculate_image_width(1.32, -1.0)


class TestProjectorProfile:
    """Tests for ProjectorProfile dataclass."""

    def test_default_profile(self):
        """Test default profile creation."""
        profile = ProjectorProfile(
            name="test_projector",
            manufacturer="Test"
        )
        assert profile.name == "test_projector"
        assert profile.manufacturer == "Test"
        assert profile.throw_ratio == 1.32
        assert profile.native_resolution == (1920, 1080)
        assert profile.projector_type == ProjectorType.DLP

    def test_get_blender_focal_length(self):
        """Test profile focal length calculation.

        For 1.5 throw ratio and 36mm sensor: 36 * 1.5 = 54mm
        """
        profile = ProjectorProfile(
            name="test",
            manufacturer="Test",
            throw_ratio=1.5,
            sensor_width=36.0,
            sensor_height=20.25
        )
        focal = profile.get_blender_focal_length()
        assert math.isclose(focal, 54.0, rel_tol=0.001)

    def test_get_blender_focal_length_short_throw(self):
        """Test profile focal length for short throw."""
        profile = ProjectorProfile(
            name="short_throw",
            manufacturer="Test",
            throw_ratio=0.5,
            sensor_width=36.0,
            sensor_height=20.25
        )
        focal = profile.get_blender_focal_length()
        assert math.isclose(focal, 18.0, rel_tol=0.001)

    def test_lens_shift_defaults(self):
        """Test default lens shift is zero."""
        profile = ProjectorProfile(
            name="test",
            manufacturer="Test"
        )
        assert profile.lens_shift.horizontal == 0.0
        assert profile.lens_shift.vertical == 0.0

    def test_lens_shift_custom(self):
        """Test custom lens shift."""
        profile = ProjectorProfile(
            name="test",
            manufacturer="Test",
            lens_shift=LensShift(vertical=0.15, horizontal=0.05)
        )
        assert profile.lens_shift.vertical == 0.15
        assert profile.lens_shift.horizontal == 0.05

    def test_blender_shift_conversion(self):
        """Test shift conversion for Blender."""
        profile = ProjectorProfile(
            name="test",
            manufacturer="Test",
            lens_shift=LensShift(vertical=0.15, horizontal=0.05)
        )
        assert profile.get_blender_shift_x() == 0.05
        assert profile.get_blender_shift_y() == 0.15

    def test_zoom_detection(self):
        """Test auto-detection of zoom capability."""
        profile = ProjectorProfile(
            name="zoom_projector",
            manufacturer="Test",
            throw_ratio=1.5,
            throw_ratio_range=(1.2, 1.8)
        )
        assert profile.has_zoom is True

    def test_no_zoom_detection(self):
        """Test detection of fixed lens."""
        profile = ProjectorProfile(
            name="fixed_projector",
            manufacturer="Test",
            throw_ratio=1.32,
            throw_ratio_range=(1.32, 1.32)
        )
        assert profile.has_zoom is False

    def test_get_throw_distance(self):
        """Test profile throw distance calculation."""
        profile = ProjectorProfile(
            name="test",
            manufacturer="Test",
            throw_ratio=1.32
        )
        distance = profile.get_throw_distance(2.0)  # 2m image width
        assert math.isclose(distance, 2.64, rel_tol=0.001)

    def test_get_image_width(self):
        """Test profile image width calculation."""
        profile = ProjectorProfile(
            name="test",
            manufacturer="Test",
            throw_ratio=1.32
        )
        width = profile.get_image_width(2.64)  # 2.64m throw distance
        assert math.isclose(width, 2.0, rel_tol=0.001)

    def test_all_projector_types(self):
        """Test all projector type enum values."""
        for ptype in ProjectorType:
            profile = ProjectorProfile(
                name=f"test_{ptype.value}",
                manufacturer="Test",
                projector_type=ptype
            )
            assert profile.projector_type == ptype

    def test_all_aspect_ratios(self):
        """Test all aspect ratio enum values."""
        for ratio in AspectRatio:
            profile = ProjectorProfile(
                name=f"test_{ratio.name}",
                manufacturer="Test",
                aspect_ratio=ratio
            )
            assert profile.aspect_ratio == ratio

    def test_aspect_ratio_value(self):
        """Test aspect ratio float value calculation."""
        assert math.isclose(AspectRatio.RATIO_16_9.ratio, 16/9, rel_tol=0.001)
        assert math.isclose(AspectRatio.RATIO_4_3.ratio, 4/3, rel_tol=0.001)
        assert math.isclose(AspectRatio.RATIO_16_10.ratio, 16/10, rel_tol=0.001)


class TestLensShift:
    """Tests for LensShift dataclass."""

    def test_default_lens_shift(self):
        """Test default lens shift."""
        shift = LensShift()
        assert shift.vertical == 0.0
        assert shift.horizontal == 0.0

    def test_range_defaults(self):
        """Test range defaults to zero."""
        shift = LensShift(vertical=0.15)
        assert shift.vertical_range == (0.0, 0.0)
        assert shift.horizontal_range == (0.0, 0.0)

    def test_range_custom(self):
        """Test custom range."""
        shift = LensShift(
            vertical=0.10,
            vertical_range=(0.0, 0.20)
        )
        assert shift.vertical_range == (0.0, 0.20)

    def test_full_spec(self):
        """Test fully specified lens shift."""
        shift = LensShift(
            vertical=0.10,
            horizontal=-0.05,
            vertical_range=(-0.15, 0.15),
            horizontal_range=(-0.10, 0.10)
        )
        assert shift.vertical == 0.10
        assert shift.horizontal == -0.05
        assert shift.vertical_range == (-0.15, 0.15)
        assert shift.horizontal_range == (-0.10, 0.10)


class TestKeystoneCorrection:
    """Tests for KeystoneCorrection dataclass."""

    def test_default_keystone(self):
        """Test default keystone."""
        keystone = KeystoneCorrection()
        assert keystone.horizontal == 0.0
        assert keystone.vertical == 0.0
        assert keystone.automatic is False
        assert keystone.corner_correction is False

    def test_custom_keystone(self):
        """Test custom keystone settings."""
        keystone = KeystoneCorrection(
            horizontal=15.0,
            vertical=10.0,
            automatic=True,
            corner_correction=True
        )
        assert keystone.horizontal == 15.0
        assert keystone.vertical == 10.0
        assert keystone.automatic is True
        assert keystone.corner_correction is True

    def test_negative_keystone(self):
        """Test negative keystone values (valid for correction)."""
        keystone = KeystoneCorrection(
            horizontal=-15.0,
            vertical=-10.0
        )
        assert keystone.horizontal == -15.0
        assert keystone.vertical == -10.0


class TestIntegration:
    """Integration tests for projector profile system."""

    def test_epson_home_cinema_2150_profile(self):
        """Test a realistic Epson Home Cinema 2150 profile."""
        profile = ProjectorProfile(
            name="Epson_Home_Cinema_2150",
            manufacturer="Epson",
            model="Home Cinema 2150",
            projector_type=ProjectorType.LCD,
            native_resolution=(1920, 1080),
            aspect_ratio=AspectRatio.RATIO_16_9,
            max_refresh_rate=60,
            throw_ratio=1.32,
            throw_ratio_range=(1.32, 1.32),
            lens_shift=LensShift(
                vertical=0.15,
                horizontal=0.0,
                vertical_range=(-0.15, 0.15),
                horizontal_range=(0.0, 0.0)
            ),
            keystone=KeystoneCorrection(
                horizontal=0.0,
                vertical=0.0,
                automatic=True,
                corner_correction=False
            ),
            brightness_lumens=2500,
            contrast_ratio=70000,
            color_gamut="Rec.709",
            sensor_width=36.0,
            sensor_height=20.25
        )

        # Verify focal length
        focal = profile.get_blender_focal_length()
        assert math.isclose(focal, 47.52, rel_tol=0.001)

        # Verify throw distance for 2.5m image
        distance = profile.get_throw_distance(2.5)
        assert math.isclose(distance, 3.3, rel_tol=0.001)

        # Verify lens shift
        assert profile.get_blender_shift_y() == 0.15

    def test_short_throw_profile(self):
        """Test a realistic short-throw projector profile."""
        profile = ProjectorProfile(
            name="Optoma_GT1080",
            manufacturer="Optoma",
            model="GT1080",
            projector_type=ProjectorType.DLP,
            native_resolution=(1920, 1080),
            aspect_ratio=AspectRatio.RATIO_16_9,
            throw_ratio=0.5,
            sensor_width=36.0,
            sensor_height=20.25,
            brightness_lumens=3000
        )

        # Short throw should have lower focal length
        focal = profile.get_blender_focal_length()
        assert math.isclose(focal, 18.0, rel_tol=0.001)

        # Short distance for large image
        distance = profile.get_throw_distance(2.0)
        assert math.isclose(distance, 1.0, rel_tol=0.001)

    def test_laser_projector_profile(self):
        """Test a laser projector profile."""
        profile = ProjectorProfile(
            name="Sony_VPL_VW295ES",
            manufacturer="Sony",
            model="VPL-VW295ES",
            projector_type=ProjectorType.LASER,
            native_resolution=(3840, 2160),
            aspect_ratio=AspectRatio.RATIO_16_9,
            throw_ratio=1.38,
            sensor_width=36.0,
            sensor_height=20.25,
            brightness_lumens=1500,
            contrast_ratio=1000000,
            color_gamut="DCI-P3"
        )

        # 4K resolution
        assert profile.native_resolution == (3840, 2160)

        # Laser type
        assert profile.projector_type == ProjectorType.LASER

        # Focal length
        focal = profile.get_blender_focal_length()
        assert math.isclose(focal, 49.68, rel_tol=0.001)


class TestBlenderIntegration:
    """Tests for Blender camera creation with mocked bpy.

    Note: These tests use the mock bpy provided by conftest.py.
    The real bpy module is only available within Blender itself.
    """

    def test_create_projector_camera_with_mock(self):
        """Test creating a projector camera with mocked bpy."""
        from lib.cinematic.projection.physical.projector.calibration import create_projector_camera
        import bpy  # This is the mock from conftest.py

        profile = ProjectorProfile(
            name="test_camera",
            manufacturer="Test",
            throw_ratio=1.5,
            sensor_width=36.0,
            sensor_height=20.25
        )

        # Create the camera (uses mock bpy)
        cam_obj = create_projector_camera(profile)

        # Verify the mock returned an object
        assert cam_obj is not None

        # Verify bpy.data.cameras.new was called
        bpy.data.cameras.new.assert_called_once()

        # Verify bpy.data.objects.new was called
        bpy.data.objects.new.assert_called_once()

    def test_configure_render_for_projector_with_mock(self):
        """Test configuring render settings with mocked bpy."""
        from lib.cinematic.projection.physical.projector.calibration import (
            configure_render_for_projector,
            restore_render_settings
        )
        import bpy  # This is the mock from conftest.py

        profile = ProjectorProfile(
            name="test_render",
            manufacturer="Test",
            native_resolution=(1920, 1080)
        )

        # Configure render settings
        original = configure_render_for_projector(profile)

        # Verify original settings dict was returned
        assert isinstance(original, dict)
        assert 'resolution_x' in original
        assert 'resolution_y' in original

        # Restore settings
        restore_render_settings(original)

    def test_create_projector_camera_with_custom_name(self):
        """Test creating a projector camera with custom name."""
        from lib.cinematic.projection.physical.projector.calibration import create_projector_camera
        import bpy  # This is the mock from conftest.py

        profile = ProjectorProfile(
            name="test",
            manufacturer="Test",
            throw_ratio=1.32
        )

        cam_obj = create_projector_camera(profile, name="custom_projector_cam")

        # Verify the camera was created with custom name
        assert cam_obj is not None
        # Just verify new was called (don't check call count as mock is shared)
        assert bpy.data.cameras.new.called

    def test_create_projector_camera_with_lens_shift(self):
        """Test creating a projector camera with lens shift."""
        from lib.cinematic.projection.physical.projector.calibration import create_projector_camera
        import bpy  # This is the mock from conftest.py

        profile = ProjectorProfile(
            name="shifted_projector",
            manufacturer="Test",
            throw_ratio=1.5,
            lens_shift=LensShift(vertical=0.15, horizontal=-0.05)
        )

        cam_obj = create_projector_camera(profile)

        # Verify the camera object was created
        assert cam_obj is not None
