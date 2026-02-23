"""
Tests for render/profiles module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
from pathlib import Path
import tempfile
import os
import yaml


class TestRenderEngine:
    """Tests for RenderEngine enum."""

    def test_engine_values(self):
        """Test RenderEngine enum values."""
        from lib.render.profiles import RenderEngine

        assert RenderEngine.CYCLES.value == "CYCLES"
        assert RenderEngine.EEVEE_NEXT.value == "BLENDER_EEVEE_NEXT"
        assert RenderEngine.WORKBENCH.value == "BLENDER_WORKBENCH"


class TestQualityTier:
    """Tests for QualityTier enum."""

    def test_tier_values(self):
        """Test QualityTier enum values."""
        from lib.render.profiles import QualityTier

        assert QualityTier.PREVIEW.value == "preview"
        assert QualityTier.DRAFT.value == "draft"
        assert QualityTier.PRODUCTION.value == "production"
        assert QualityTier.ARCHIVE.value == "archive"


class TestRenderProfile:
    """Tests for RenderProfile dataclass."""

    def test_profile_creation(self):
        """Test creating a RenderProfile."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(
            name="test_profile",
            engine="CYCLES",
            resolution=(1920, 1080),
            samples=256,
        )

        assert profile.name == "test_profile"
        assert profile.engine == "CYCLES"
        assert profile.resolution == (1920, 1080)
        assert profile.samples == 256

    def test_profile_defaults(self):
        """Test RenderProfile default values."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(name="default")
        assert profile.engine == "CYCLES"
        assert profile.resolution == (1920, 1080)
        assert profile.samples == 64
        assert profile.denoise is True
        assert profile.transparent_bg is False
        assert profile.motion_blur is False
        assert profile.fps == 24
        assert profile.output_format == "PNG"

    def test_profile_to_dict(self):
        """Test RenderProfile serialization."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(
            name="test",
            engine="CYCLES",
            resolution=(1920, 1080),
            samples=128,
        )
        data = profile.to_dict()

        assert data["name"] == "test"
        assert data["engine"] == "CYCLES"
        assert data["resolution"] == [1920, 1080]
        assert data["samples"] == 128

    def test_profile_from_dict(self):
        """Test RenderProfile deserialization."""
        from lib.render.profiles import RenderProfile

        data = {
            "name": "test",
            "engine": "BLENDER_EEVEE_NEXT",
            "resolution": [1280, 720],
            "samples": 32,
            "denoise": True,
            "metadata": {"custom": "value"},
        }
        profile = RenderProfile.from_dict(data)

        assert profile.name == "test"
        assert profile.engine == "BLENDER_EEVEE_NEXT"
        assert profile.resolution == (1280, 720)
        assert profile.metadata["custom"] == "value"

    def test_profile_from_dict_resolution_conversion(self):
        """Test resolution list to tuple conversion."""
        from lib.render.profiles import RenderProfile

        data = {
            "name": "test",
            "resolution": [3840, 2160],
        }
        profile = RenderProfile.from_dict(data)

        assert profile.resolution == (3840, 2160)
        assert isinstance(profile.resolution, tuple)


class TestBuiltInProfiles:
    """Tests for built-in PROFILES constant."""

    def test_profiles_dict(self):
        """Test that PROFILES is a dictionary."""
        from lib.render.profiles import PROFILES

        assert isinstance(PROFILES, dict)
        assert len(PROFILES) > 0

    def test_preview_profile(self):
        """Test preview profile exists."""
        from lib.render.profiles import PROFILES

        assert "preview" in PROFILES
        profile = PROFILES["preview"]
        assert profile.quality_tier == "preview"
        assert profile.samples <= 64  # Preview should be fast

    def test_production_profile(self):
        """Test production profile exists."""
        from lib.render.profiles import PROFILES

        assert "production" in PROFILES
        profile = PROFILES["production"]
        assert profile.quality_tier == "production"
        assert profile.denoise is True

    def test_4k_profile(self):
        """Test 4K production profile."""
        from lib.render.profiles import PROFILES

        assert "4k_production" in PROFILES
        profile = PROFILES["4k_production"]
        assert profile.resolution == (3840, 2160)

    def test_archive_profile(self):
        """Test archive profile for maximum quality."""
        from lib.render.profiles import PROFILES

        assert "archive" in PROFILES
        profile = PROFILES["archive"]
        assert profile.quality_tier == "archive"
        assert profile.samples >= 512

    def test_animation_profile(self):
        """Test animation profile."""
        from lib.render.profiles import PROFILES

        assert "animation" in PROFILES
        profile = PROFILES["animation"]
        assert profile.motion_blur is True
        assert profile.fps == 24

    def test_turntable_profile(self):
        """Test turntable profile."""
        from lib.render.profiles import PROFILES

        assert "turntable" in PROFILES
        profile = PROFILES["turntable"]
        assert profile.transparent_bg is True
        # Should be square
        assert profile.resolution[0] == profile.resolution[1]

    def test_product_hero_profile(self):
        """Test product hero profile."""
        from lib.render.profiles import PROFILES

        assert "product_hero" in PROFILES
        profile = PROFILES["product_hero"]
        assert profile.transparent_bg is True


class TestGetProfile:
    """Tests for get_profile function."""

    def test_get_existing_profile(self):
        """Test getting an existing profile."""
        from lib.render.profiles import get_profile

        profile = get_profile("production")
        assert profile.name == "production"

    def test_get_nonexistent_profile(self):
        """Test getting a nonexistent profile raises error."""
        from lib.render.profiles import get_profile

        with pytest.raises(KeyError) as exc_info:
            get_profile("nonexistent_profile")

        assert "not found" in str(exc_info.value)


class TestGetAllProfiles:
    """Tests for get_all_profiles function."""

    def test_get_all_profiles(self):
        """Test getting all profiles."""
        from lib.render.profiles import get_all_profiles

        profiles = get_all_profiles()

        assert isinstance(profiles, dict)
        assert len(profiles) > 0
        # Should be a copy, not the original
        from lib.render.profiles import PROFILES
        assert profiles is not PROFILES


class TestApplyProfile:
    """Tests for apply_profile function."""

    def test_apply_profile_requires_bpy(self):
        """Test that apply_profile requires Blender."""
        from lib.render.profiles import apply_profile, RenderProfile

        profile = RenderProfile(name="test")

        try:
            apply_profile(profile)
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestCreateProfileFromScene:
    """Tests for create_profile_from_scene function."""

    def test_create_from_scene_requires_bpy(self):
        """Test that create_profile_from_scene requires Blender."""
        from lib.render.profiles import create_profile_from_scene

        try:
            create_profile_from_scene("test")
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestLoadProfilesFromYaml:
    """Tests for load_profiles_from_yaml function."""

    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent file returns empty dict."""
        from lib.render.profiles import load_profiles_from_yaml

        result = load_profiles_from_yaml(Path("/nonexistent/path.yaml"))
        assert result == {}

    def test_load_from_valid_yaml(self):
        """Test loading profiles from valid YAML."""
        from lib.render.profiles import load_profiles_from_yaml

        yaml_content = """
profiles:
  custom_preview:
    engine: CYCLES
    resolution: [960, 540]
    samples: 16
    denoise: true
  custom_production:
    engine: CYCLES
    resolution: [1920, 1080]
    samples: 512
    denoise: true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            profiles = load_profiles_from_yaml(temp_path)

            assert len(profiles) == 2
            assert "custom_preview" in profiles
            assert "custom_production" in profiles
            assert profiles["custom_preview"].resolution == (960, 540)
            assert profiles["custom_production"].samples == 512
        finally:
            os.unlink(temp_path)


class TestProfileProperties:
    """Tests for profile property calculations."""

    def test_resolution_aspect_ratio(self):
        """Test resolution aspect ratio."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(name="test", resolution=(1920, 1080))
        # 16:9 aspect ratio
        assert profile.resolution[0] / profile.resolution[1] == pytest.approx(16/9, rel=0.01)

    def test_4k_resolution(self):
        """Test 4K resolution."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(name="test", resolution=(3840, 2160))
        assert profile.resolution[0] == 3840
        assert profile.resolution[1] == 2160

    def test_square_resolution(self):
        """Test square resolution."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(name="test", resolution=(2048, 2048))
        assert profile.resolution[0] == profile.resolution[1]

    def test_exr_output_format(self):
        """Test EXR output format."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(
            name="test",
            output_format="OPEN_EXR_MULTILAYER",
            exr_codec="PIZ",
        )
        assert profile.output_format == "OPEN_EXR_MULTILAYER"
        assert profile.exr_codec == "PIZ"


class TestProfileMetadata:
    """Tests for profile metadata handling."""

    def test_metadata_storage(self):
        """Test storing metadata in profile."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(
            name="test",
            metadata={
                "adaptive_sampling": True,
                "path_guiding": True,
                "custom_value": 42,
            }
        )

        assert profile.metadata["adaptive_sampling"] is True
        assert profile.metadata["path_guiding"] is True
        assert profile.metadata["custom_value"] == 42

    def test_metadata_in_serialization(self):
        """Test metadata is preserved in serialization."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(
            name="test",
            metadata={"key": "value"},
        )
        data = profile.to_dict()
        restored = RenderProfile.from_dict(data)

        assert restored.metadata["key"] == "value"

    def test_eevee_metadata(self):
        """Test EEVEE-specific metadata."""
        from lib.render.profiles import PROFILES

        profile = PROFILES["eevee_production"]
        assert "taa_samples" in profile.metadata
        assert "raytracing" in profile.metadata

    def test_cycles_metadata(self):
        """Test Cycles-specific metadata."""
        from lib.render.profiles import PROFILES

        profile = PROFILES["cycles_production"]
        assert "adaptive_sampling" in profile.metadata


class TestProfilePasses:
    """Tests for render pass configuration."""

    def test_combined_pass(self):
        """Test combined pass is included by default."""
        from lib.render.profiles import RenderProfile

        profile = RenderProfile(name="test")
        assert "combined" in profile.passes

    def test_production_passes(self):
        """Test production profile has multiple passes."""
        from lib.render.profiles import PROFILES

        profile = PROFILES["production"]
        assert "combined" in profile.passes
        assert "depth" in profile.passes
        assert "normal" in profile.passes
        assert "cryptomatte_object" in profile.passes

    def test_archive_passes(self):
        """Test archive profile has all passes."""
        from lib.render.profiles import PROFILES

        profile = PROFILES["archive"]
        # Should have many passes
        assert len(profile.passes) >= 8
        assert "emission" in profile.passes
        assert "shadow" in profile.passes
        assert "ao" in profile.passes
