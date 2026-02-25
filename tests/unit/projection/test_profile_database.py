"""Unit tests for projector profile database."""
import pytest
from pathlib import Path

from lib.cinematic.projection.physical.projector.profile_database import (
    PROJECTOR_PROFILES,
    get_profile,
    list_profiles,
    get_profiles_by_throw_ratio,
    get_profiles_by_resolution,
    get_short_throw_profiles,
    get_4k_profiles,
    load_profile_from_yaml,
)
from lib.cinematic.projection.physical.projector.profiles import ProjectorType


class TestProfileDatabase:
    """Tests for the profile database."""

    def test_database_has_10_plus_profiles(self):
        """Test that database has at least 10 profiles."""
        assert len(PROJECTOR_PROFILES) >= 10

    def test_get_profile_epson_2150(self):
        """Test getting Epson Home Cinema 2150 profile."""
        profile = get_profile("Epson_Home_Cinema_2150")
        assert profile.manufacturer == "Epson"
        assert profile.throw_ratio == 1.32
        assert profile.native_resolution == (1920, 1080)

    def test_get_profile_not_found(self):
        """Test error when profile not found."""
        with pytest.raises(KeyError) as exc_info:
            get_profile("NonExistent_Projector")
        assert "not found" in str(exc_info.value)

    def test_list_all_profiles(self):
        """Test listing all profiles."""
        profiles = list_profiles()
        assert len(profiles) >= 10
        assert "Epson_Home_Cinema_2150" in profiles

    def test_list_profiles_by_manufacturer_epson(self):
        """Test filtering by manufacturer."""
        profiles = list_profiles(manufacturer="Epson")
        assert len(profiles) >= 4
        assert all("Epson" in p for p in profiles)

    def test_list_profiles_by_manufacturer_benq(self):
        """Test filtering by BenQ."""
        profiles = list_profiles(manufacturer="BenQ")
        assert len(profiles) >= 3
        assert all("BenQ" in p for p in profiles)

    def test_list_profiles_manufacturer_case_insensitive(self):
        """Test manufacturer filter is case insensitive."""
        profiles_lower = list_profiles(manufacturer="epson")
        profiles_upper = list_profiles(manufacturer="EPSON")
        assert profiles_lower == profiles_upper


class TestThrowRatioFilter:
    """Tests for throw ratio filtering."""

    def test_get_short_throw_profiles(self):
        """Test getting short-throw projectors (ratio <= 0.8)."""
        profiles = get_short_throw_profiles(0.8)
        # Should include Optoma_GT1080HDR (0.50) and BenQ_MW632ST (0.72)
        names = [p.name for p in profiles]
        assert any("GT1080HDR" in n for n in names)  # 0.50
        assert any("MW632ST" in n for n in names)    # 0.72

    def test_get_profiles_by_throw_ratio_range(self):
        """Test filtering by throw ratio range."""
        profiles = get_profiles_by_throw_ratio(min_ratio=1.3, max_ratio=1.5)
        for profile in profiles:
            assert 1.3 <= profile.throw_ratio <= 1.5

    def test_get_profiles_by_throw_ratio_min_only(self):
        """Test filtering by minimum throw ratio only."""
        profiles = get_profiles_by_throw_ratio(min_ratio=1.5)
        for profile in profiles:
            assert profile.throw_ratio >= 1.5

    def test_get_profiles_by_throw_ratio_max_only(self):
        """Test filtering by maximum throw ratio only."""
        profiles = get_profiles_by_throw_ratio(max_ratio=1.0)
        for profile in profiles:
            assert profile.throw_ratio <= 1.0


class TestResolutionFilter:
    """Tests for resolution filtering."""

    def test_get_4k_profiles(self):
        """Test getting 4K projectors."""
        profiles = get_4k_profiles()
        # Should include BenQ_W2700, Optoma_UHD38, Sony_VPL_VW295ES
        names = [p.name for p in profiles]
        assert any("W2700" in n for n in names)
        assert any("UHD38" in n for n in names)
        assert any("VW295ES" in n for n in names)

    def test_get_profiles_by_resolution_1080p(self):
        """Test filtering by 1080p minimum."""
        profiles = get_profiles_by_resolution(min_width=1920, min_height=1080)
        for profile in profiles:
            width, height = profile.native_resolution
            assert width >= 1920
            assert height >= 1080


class TestProfileFocalLength:
    """Tests for focal length calculation from profiles."""

    def test_epson_2150_focal_length(self):
        """Test Epson 2150 focal length calculation."""
        profile = get_profile("Epson_Home_Cinema_2150")
        # 36mm * 1.32 = 47.52mm
        focal = profile.get_blender_focal_length()
        assert abs(focal - 47.52) < 0.01

    def test_optoma_gt1080_focal_length(self):
        """Test Optoma GT1080HDR short-throw focal length."""
        profile = get_profile("Optoma_GT1080HDR")
        # 36mm * 0.50 = 18.0mm
        focal = profile.get_blender_focal_length()
        assert abs(focal - 18.0) < 0.01

    def test_sony_vpl_focal_length(self):
        """Test Sony VPL-HW45ES focal length."""
        profile = get_profile("Sony_VPL_HW45ES")
        # 36mm * 1.4 = 50.4mm
        focal = profile.get_blender_focal_length()
        assert abs(focal - 50.4) < 0.01


class TestYAMLLoading:
    """Tests for YAML profile loading."""

    def test_load_yaml_profile(self):
        """Test loading a profile from YAML file."""
        yaml_path = Path("configs/cinematic/projection/projector_profiles.yaml")
        if not yaml_path.exists():
            pytest.skip("YAML config not yet created")

        profile = load_profile_from_yaml(str(yaml_path), "Epson_Home_Cinema_2150")
        assert profile.manufacturer == "Epson"
        assert profile.throw_ratio == 1.32

    def test_load_yaml_not_found(self):
        """Test error when YAML file not found."""
        with pytest.raises(FileNotFoundError):
            load_profile_from_yaml("nonexistent.yaml", "Profile")

    def test_load_yaml_profile_not_found(self):
        """Test error when profile not in YAML."""
        yaml_path = Path("configs/cinematic/projection/projector_profiles.yaml")
        if not yaml_path.exists():
            pytest.skip("YAML config not yet created")

        with pytest.raises(KeyError):
            load_profile_from_yaml(str(yaml_path), "NonExistent")


class TestLensShift:
    """Tests for lens shift in profiles."""

    def test_epson_3800_has_lens_shift(self):
        """Test Epson 3800 has lens shift."""
        profile = get_profile("Epson_Home_Cinema_3800")
        assert profile.lens_shift.vertical > 0
        assert profile.lens_shift.horizontal > 0

    def test_epson_2150_no_lens_shift(self):
        """Test Epson 2150 has no lens shift."""
        profile = get_profile("Epson_Home_Cinema_2150")
        assert profile.lens_shift.vertical == 0
        assert profile.lens_shift.horizontal == 0

    def test_blender_shift_conversion(self):
        """Test shift conversion for Blender camera."""
        profile = get_profile("Epson_Home_Cinema_3800")
        # Should be the same values (already normalized 0-1)
        shift_x = profile.get_blender_shift_x()
        shift_y = profile.get_blender_shift_y()
        assert shift_x == 0.24
        assert shift_y == 0.60
