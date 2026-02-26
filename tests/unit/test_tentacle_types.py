"""Unit tests for tentacle types and presets.

Tests cover:
- TentacleConfig dataclass validation
- TaperProfile calculations
- SegmentConfig validation
- ZombieMouthConfig validation and methods
- TentaclePresetLoader functionality
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from lib.tentacle import (
    TentacleConfig,
    TaperProfile,
    SegmentConfig,
    ZombieMouthConfig,
    TentaclePresetLoader,
    load_tentacle,
    load_zombie_mouth,
    list_tentacle_presets,
    list_zombie_mouth_presets,
)


# =============================================================================
# TentacleConfig Tests
# =============================================================================

class TestTentacleConfig:
    """Test TentacleConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TentacleConfig()
        assert config.length == 1.0
        assert config.base_diameter == 0.08
        assert config.tip_diameter == 0.02
        assert config.segments == 20
        assert config.curve_resolution == 64
        assert config.taper_profile == "organic"
        assert config.twist == 0.0
        assert config.subdivision_levels == 2
        assert config.seed == 42
        assert config.name == "Tentacle"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = TentacleConfig(
            length=2.0,
            base_diameter=0.10,
            tip_diameter=0.03,
            segments=30,
            curve_resolution=48,
            taper_profile="smooth",
            twist=45.0,
            subdivision_levels=3,
            seed=123,
            name="CustomTentacle",
        )
        assert config.length == 2.0
        assert config.base_diameter == 0.10
        assert config.tip_diameter == 0.03
        assert config.segments == 30
        assert config.curve_resolution == 48
        assert config.taper_profile == "smooth"
        assert config.twist == 45.0
        assert config.subdivision_levels == 3
        assert config.seed == 123
        assert config.name == "CustomTentacle"

    def test_length_validation_min(self):
        """Test minimum length validation."""
        config = TentacleConfig(length=0.1)
        assert config.length == 0.1

    def test_length_validation_max(self):
        """Test maximum length validation."""
        config = TentacleConfig(length=3.0)
        assert config.length == 3.0

    def test_length_validation_too_small(self):
        """Test that too small length raises ValueError."""
        with pytest.raises(ValueError, match="Length must be between"):
            TentacleConfig(length=0.05)

    def test_length_validation_too_large(self):
        """Test that too large length raises ValueError."""
        with pytest.raises(ValueError, match="Length must be between"):
            TentacleConfig(length=5.0)

    def test_base_diameter_validation_min(self):
        """Test minimum base diameter validation."""
        config = TentacleConfig(base_diameter=0.02, tip_diameter=0.005)
        assert config.base_diameter == 0.02

    def test_base_diameter_validation_max(self):
        """Test maximum base diameter validation."""
        config = TentacleConfig(base_diameter=0.20, tip_diameter=0.02)
        assert config.base_diameter == 0.20

    def test_base_diameter_validation_invalid(self):
        """Test that invalid base diameter raises ValueError."""
        with pytest.raises(ValueError, match="base_diameter must be between"):
            TentacleConfig(base_diameter=0.01)

    def test_tip_diameter_validation_min(self):
        """Test minimum tip diameter validation."""
        config = TentacleConfig(tip_diameter=0.005)
        assert config.tip_diameter == 0.005

    def test_tip_diameter_validation_max(self):
        """Test maximum tip diameter validation."""
        config = TentacleConfig(base_diameter=0.15, tip_diameter=0.10)
        assert config.tip_diameter == 0.10

    def test_tip_diameter_validation_invalid(self):
        """Test that invalid tip diameter raises ValueError."""
        with pytest.raises(ValueError, match="tip_diameter must be between"):
            TentacleConfig(tip_diameter=0.001)

    def test_tip_smaller_than_base_validation(self):
        """Test that tip must be smaller than base."""
        with pytest.raises(ValueError, match="tip_diameter .* must be smaller"):
            TentacleConfig(base_diameter=0.05, tip_diameter=0.06)

    def test_tip_equal_to_base_validation(self):
        """Test that tip cannot equal base."""
        with pytest.raises(ValueError, match="tip_diameter .* must be smaller"):
            TentacleConfig(base_diameter=0.05, tip_diameter=0.05)

    def test_segments_validation_min(self):
        """Test minimum segments validation."""
        config = TentacleConfig(segments=10)
        assert config.segments == 10

    def test_segments_validation_max(self):
        """Test maximum segments validation."""
        config = TentacleConfig(segments=50)
        assert config.segments == 50

    def test_segments_validation_too_small(self):
        """Test that too few segments raises ValueError."""
        with pytest.raises(ValueError, match="segments must be between"):
            TentacleConfig(segments=5)

    def test_segments_validation_too_large(self):
        """Test that too many segments raises ValueError."""
        with pytest.raises(ValueError, match="segments must be between"):
            TentacleConfig(segments=100)

    def test_curve_resolution_validation_min(self):
        """Test minimum curve resolution validation."""
        config = TentacleConfig(curve_resolution=16)
        assert config.curve_resolution == 16

    def test_curve_resolution_validation_max(self):
        """Test maximum curve resolution validation."""
        config = TentacleConfig(curve_resolution=128)
        assert config.curve_resolution == 128

    def test_curve_resolution_validation_invalid(self):
        """Test that invalid curve resolution raises ValueError."""
        with pytest.raises(ValueError, match="curve_resolution must be between"):
            TentacleConfig(curve_resolution=8)

    def test_taper_profile_validation_valid(self):
        """Test valid taper profile types."""
        for profile_type in ["linear", "smooth", "organic", "custom"]:
            config = TentacleConfig(taper_profile=profile_type)
            assert config.taper_profile == profile_type

    def test_taper_profile_validation_invalid(self):
        """Test that invalid taper profile raises ValueError."""
        with pytest.raises(ValueError, match="taper_profile must be one of"):
            TentacleConfig(taper_profile="invalid")

    def test_subdivision_levels_validation_min(self):
        """Test minimum subdivision levels validation."""
        config = TentacleConfig(subdivision_levels=0)
        assert config.subdivision_levels == 0

    def test_subdivision_levels_validation_max(self):
        """Test maximum subdivision levels validation."""
        config = TentacleConfig(subdivision_levels=4)
        assert config.subdivision_levels == 4

    def test_subdivision_levels_validation_invalid(self):
        """Test that invalid subdivision levels raises ValueError."""
        with pytest.raises(ValueError, match="subdivision_levels must be between"):
            TentacleConfig(subdivision_levels=5)

    def test_taper_ratio_property(self):
        """Test taper ratio calculation."""
        config = TentacleConfig(base_diameter=0.10, tip_diameter=0.02)
        assert config.taper_ratio == 5.0

    def test_segment_length_property(self):
        """Test segment length calculation."""
        config = TentacleConfig(length=2.0, segments=20)
        assert config.segment_length == 0.1

    def test_get_diameter_at_base(self):
        """Test diameter at base (t=0)."""
        config = TentacleConfig(base_diameter=0.10, tip_diameter=0.02)
        diameter = config.get_diameter_at(0.0)
        assert diameter == pytest.approx(0.10, rel=0.01)

    def test_get_diameter_at_tip(self):
        """Test diameter at tip (t=1)."""
        config = TentacleConfig(base_diameter=0.10, tip_diameter=0.02)
        diameter = config.get_diameter_at(1.0)
        assert diameter == pytest.approx(0.02, rel=0.01)

    def test_get_diameter_at_middle(self):
        """Test diameter at middle (t=0.5)."""
        config = TentacleConfig(base_diameter=0.10, tip_diameter=0.02)
        diameter = config.get_diameter_at(0.5)
        # Should be between base and tip
        assert 0.02 < diameter < 0.10


# =============================================================================
# TaperProfile Tests
# =============================================================================

class TestTaperProfile:
    """Test TaperProfile dataclass."""

    def test_default_profile(self):
        """Test default taper profile."""
        profile = TaperProfile()
        assert profile.profile_type == "organic"
        assert profile.points == []
        assert profile.base_ratio == 2.5
        assert profile.mid_point == 0.4
        assert profile.smoothness == 0.5

    def test_custom_profile(self):
        """Test custom profile values."""
        profile = TaperProfile(
            profile_type="custom",
            base_ratio=4.0,
            mid_point=0.6,
            smoothness=0.8,
        )
        assert profile.profile_type == "custom"
        assert profile.base_ratio == 4.0
        assert profile.mid_point == 0.6
        assert profile.smoothness == 0.8

    def test_custom_points(self):
        """Test custom profile points."""
        profile = TaperProfile(
            profile_type="custom",
            points=[(0.0, 1.0), (0.5, 0.6), (1.0, 0.2)],
        )
        assert len(profile.points) == 3
        assert profile.points[0] == (0.0, 1.0)

    def test_profile_type_validation(self):
        """Test valid profile types."""
        for ptype in TaperProfile.VALID_PROFILE_TYPES:
            profile = TaperProfile(profile_type=ptype)
            assert profile.profile_type == ptype

    def test_invalid_profile_type(self):
        """Test that invalid profile type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid profile_type"):
            TaperProfile(profile_type="invalid")

    def test_base_ratio_validation_min(self):
        """Test minimum base ratio validation."""
        profile = TaperProfile(base_ratio=1.0)
        assert profile.base_ratio == 1.0

    def test_base_ratio_validation_max(self):
        """Test maximum base ratio validation."""
        profile = TaperProfile(base_ratio=10.0)
        assert profile.base_ratio == 10.0

    def test_base_ratio_validation_invalid(self):
        """Test that invalid base ratio raises ValueError."""
        with pytest.raises(ValueError, match="base_ratio must be between"):
            TaperProfile(base_ratio=0.5)

    def test_mid_point_validation(self):
        """Test mid point validation."""
        with pytest.raises(ValueError, match="mid_point must be between"):
            TaperProfile(mid_point=1.5)

    def test_smoothness_validation(self):
        """Test smoothness validation."""
        with pytest.raises(ValueError, match="smoothness must be between"):
            TaperProfile(smoothness=1.5)

    def test_custom_points_position_validation(self):
        """Test that custom point position must be 0-1."""
        with pytest.raises(ValueError, match="Point .* position must be between"):
            TaperProfile(points=[(-0.5, 1.0)])

    def test_custom_points_radius_validation(self):
        """Test that custom point radius must be 0-2."""
        with pytest.raises(ValueError, match="Point .* radius must be between"):
            TaperProfile(points=[(0.5, 3.0)])

    def test_get_radius_at_linear_base(self):
        """Test linear profile at base."""
        profile = TaperProfile(profile_type="linear", base_ratio=4.0)
        radius = profile.get_radius_at(0.0)
        assert radius == pytest.approx(1.0, rel=0.01)

    def test_get_radius_at_linear_tip(self):
        """Test linear profile at tip."""
        profile = TaperProfile(profile_type="linear", base_ratio=4.0)
        radius = profile.get_radius_at(1.0)
        assert radius == pytest.approx(0.25, rel=0.01)

    def test_get_radius_at_smooth(self):
        """Test smooth profile interpolation."""
        profile = TaperProfile(profile_type="smooth", base_ratio=4.0)
        radius_base = profile.get_radius_at(0.0)
        radius_mid = profile.get_radius_at(0.5)
        radius_tip = profile.get_radius_at(1.0)
        # Should be monotonically decreasing
        assert radius_base > radius_mid > radius_tip

    def test_get_radius_at_organic(self):
        """Test organic profile interpolation."""
        profile = TaperProfile(profile_type="organic", base_ratio=4.0)
        radius_base = profile.get_radius_at(0.0)
        radius_tip = profile.get_radius_at(1.0)
        assert radius_base == pytest.approx(1.0, rel=0.01)
        assert radius_tip == pytest.approx(0.25, rel=0.01)

    def test_get_radius_at_custom_points(self):
        """Test custom points interpolation."""
        profile = TaperProfile(
            profile_type="custom",
            points=[(0.0, 1.0), (0.5, 0.5), (1.0, 0.25)],
        )
        assert profile.get_radius_at(0.0) == 1.0
        assert profile.get_radius_at(0.5) == 0.5
        assert profile.get_radius_at(1.0) == 0.25
        # Interpolated value
        assert profile.get_radius_at(0.25) == 0.75

    def test_get_radius_at_invalid_position(self):
        """Test that invalid position raises ValueError."""
        profile = TaperProfile()
        with pytest.raises(ValueError, match="Position t must be between"):
            profile.get_radius_at(1.5)


# =============================================================================
# SegmentConfig Tests
# =============================================================================

class TestSegmentConfig:
    """Test SegmentConfig dataclass."""

    def test_default_values(self):
        """Test default segment configuration."""
        config = SegmentConfig()
        assert config.count == 20
        assert config.curve_resolution == 64
        assert config.uniform is True
        assert config.variation == 0.0

    def test_custom_values(self):
        """Test custom segment configuration."""
        config = SegmentConfig(
            count=30,
            curve_resolution=48,
            uniform=False,
            variation=0.1,
        )
        assert config.count == 30
        assert config.curve_resolution == 48
        assert config.uniform is False
        assert config.variation == 0.1

    def test_count_validation_min(self):
        """Test minimum count validation."""
        config = SegmentConfig(count=10)
        assert config.count == 10

    def test_count_validation_max(self):
        """Test maximum count validation."""
        config = SegmentConfig(count=50)
        assert config.count == 50

    def test_count_validation_invalid(self):
        """Test that invalid count raises ValueError."""
        with pytest.raises(ValueError, match="Segment count must be between"):
            SegmentConfig(count=5)

    def test_curve_resolution_validation_min(self):
        """Test minimum curve resolution validation."""
        config = SegmentConfig(curve_resolution=16)
        assert config.curve_resolution == 16

    def test_curve_resolution_validation_max(self):
        """Test maximum curve resolution validation."""
        config = SegmentConfig(curve_resolution=128)
        assert config.curve_resolution == 128

    def test_curve_resolution_validation_invalid(self):
        """Test that invalid curve resolution raises ValueError."""
        with pytest.raises(ValueError, match="Curve resolution must be between"):
            SegmentConfig(curve_resolution=8)

    def test_variation_validation_min(self):
        """Test minimum variation validation."""
        config = SegmentConfig(variation=0.0)
        assert config.variation == 0.0

    def test_variation_validation_max(self):
        """Test maximum variation validation."""
        config = SegmentConfig(variation=0.2)
        assert config.variation == 0.2

    def test_variation_validation_invalid(self):
        """Test that invalid variation raises ValueError."""
        with pytest.raises(ValueError, match="Variation must be between"):
            SegmentConfig(variation=0.5)


# =============================================================================
# ZombieMouthConfig Tests
# =============================================================================

class TestZombieMouthConfig:
    """Test ZombieMouthConfig dataclass."""

    def test_default_values(self):
        """Test default zombie mouth configuration."""
        config = ZombieMouthConfig()
        assert config.tentacle_count == 4
        assert config.distribution == "staggered"
        assert config.size_mix == 0.5
        assert config.spread_angle == 60.0
        assert isinstance(config.main_tentacle, TentacleConfig)
        assert config.feeler_tentacle is None

    def test_custom_values(self):
        """Test custom zombie mouth configuration."""
        main = TentacleConfig(length=1.5, name="Main")
        feeler = TentacleConfig(length=0.5, name="Feeler")
        config = ZombieMouthConfig(
            tentacle_count=6,
            distribution="uniform",
            size_mix=0.3,
            spread_angle=80.0,
            main_tentacle=main,
            feeler_tentacle=feeler,
        )
        assert config.tentacle_count == 6
        assert config.distribution == "uniform"
        assert config.size_mix == 0.3
        assert config.spread_angle == 80.0
        assert config.main_tentacle.length == 1.5
        assert config.feeler_tentacle.length == 0.5

    def test_tentacle_count_validation_min(self):
        """Test minimum tentacle count validation."""
        config = ZombieMouthConfig(tentacle_count=1)
        assert config.tentacle_count == 1

    def test_tentacle_count_validation_max(self):
        """Test maximum tentacle count validation."""
        config = ZombieMouthConfig(tentacle_count=6)
        assert config.tentacle_count == 6

    def test_tentacle_count_validation_invalid(self):
        """Test that invalid tentacle count raises ValueError."""
        with pytest.raises(ValueError, match="tentacle_count must be between"):
            ZombieMouthConfig(tentacle_count=10)

    def test_distribution_validation(self):
        """Test valid distribution types."""
        for dist in ZombieMouthConfig.VALID_DISTRIBUTIONS:
            config = ZombieMouthConfig(distribution=dist)
            assert config.distribution == dist

    def test_distribution_validation_invalid(self):
        """Test that invalid distribution raises ValueError."""
        with pytest.raises(ValueError, match="distribution must be one of"):
            ZombieMouthConfig(distribution="invalid")

    def test_size_mix_validation(self):
        """Test size mix validation."""
        with pytest.raises(ValueError, match="size_mix must be between"):
            ZombieMouthConfig(size_mix=1.5)

    def test_spread_angle_validation(self):
        """Test spread angle validation."""
        with pytest.raises(ValueError, match="spread_angle must be between"):
            ZombieMouthConfig(spread_angle=200.0)

    def test_get_tentacle_angles_uniform(self):
        """Test uniform angle distribution."""
        config = ZombieMouthConfig(
            tentacle_count=4,
            distribution="uniform",
            spread_angle=60.0,
        )
        angles = config.get_tentacle_angles()
        assert len(angles) == 4
        # Should span from -30 to +30
        assert angles[0] == pytest.approx(-30.0, rel=0.01)
        assert angles[-1] == pytest.approx(30.0, rel=0.01)

    def test_get_tentacle_angles_single(self):
        """Test single tentacle angle."""
        config = ZombieMouthConfig(
            tentacle_count=1,
            distribution="uniform",
        )
        angles = config.get_tentacle_angles()
        assert angles == [0.0]

    def test_get_tentacle_angles_staggered(self):
        """Test staggered angle distribution."""
        config = ZombieMouthConfig(
            tentacle_count=4,
            distribution="staggered",
            spread_angle=60.0,
        )
        angles = config.get_tentacle_angles()
        assert len(angles) == 4
        # Should be sorted
        assert angles == sorted(angles)

    def test_get_tentacle_configs_count(self):
        """Test that get_tentacle_configs returns correct count."""
        config = ZombieMouthConfig(tentacle_count=5)
        configs = config.get_tentacle_configs()
        assert len(configs) == 5

    def test_get_tentacle_configs_unique_names(self):
        """Test that each tentacle has a unique name."""
        config = ZombieMouthConfig(tentacle_count=5)
        configs = config.get_tentacle_configs()
        names = [c.name for c in configs]
        assert len(names) == len(set(names))


# =============================================================================
# TentaclePresetLoader Tests
# =============================================================================

class TestTentaclePresetLoader:
    """Test preset loading functionality."""

    def test_list_tentacle_presets(self):
        """Test listing available tentacle presets."""
        presets = list_tentacle_presets()
        assert isinstance(presets, list)
        assert "default" in presets
        assert "zombie_main" in presets

    def test_list_zombie_mouth_presets(self):
        """Test listing available zombie mouth presets."""
        presets = list_zombie_mouth_presets()
        assert isinstance(presets, list)
        assert "standard" in presets
        assert "aggressive" in presets

    def test_load_default_preset(self):
        """Test loading default preset."""
        config = load_tentacle("default")
        assert isinstance(config, TentacleConfig)
        assert config.length == 1.0
        assert config.base_diameter == 0.08
        assert config.taper_profile == "organic"

    def test_load_zombie_main_preset(self):
        """Test loading zombie_main preset."""
        config = load_tentacle("zombie_main")
        assert isinstance(config, TentacleConfig)
        assert config.length == 1.2
        assert config.base_diameter == 0.10
        assert config.twist == 15.0

    def test_load_nonexistent_preset(self):
        """Test error handling for nonexistent preset."""
        with pytest.raises(ValueError, match="Tentacle preset .* not found"):
            load_tentacle("nonexistent_preset")

    def test_load_zombie_mouth_standard(self):
        """Test loading standard zombie mouth preset."""
        config = load_zombie_mouth("standard")
        assert isinstance(config, ZombieMouthConfig)
        assert config.tentacle_count == 4
        assert config.distribution == "staggered"
        assert isinstance(config.main_tentacle, TentacleConfig)
        assert isinstance(config.feeler_tentacle, TentacleConfig)

    def test_load_zombie_mouth_aggressive(self):
        """Test loading aggressive zombie mouth preset."""
        config = load_zombie_mouth("aggressive")
        assert config.tentacle_count == 6
        assert config.distribution == "uniform"

    def test_load_zombie_mouth_nonexistent(self):
        """Test error handling for nonexistent zombie mouth preset."""
        with pytest.raises(ValueError, match="Zombie mouth preset .* not found"):
            load_zombie_mouth("nonexistent")

    def test_loader_set_presets_path(self):
        """Test setting custom presets path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a custom preset file
            preset_data = {
                "presets": {
                    "custom_test": {
                        "length": 0.5,
                        "base_diameter": 0.05,
                        "tip_diameter": 0.01,
                        "segments": 15,
                        "curve_resolution": 32,
                        "taper_profile": "linear",
                        "name": "CustomTest",
                    }
                },
                "taper_profiles": {},
                "zombie_mouths": {},
            }

            preset_file = Path(tmpdir) / "presets.yaml"
            with open(preset_file, "w") as f:
                yaml.dump(preset_data, f)

            # Set custom path
            TentaclePresetLoader.set_presets_path(Path(tmpdir))

            try:
                # Should load from custom path
                config = TentaclePresetLoader.load_tentacle("custom_test")
                assert config.length == 0.5
                assert config.name == "CustomTest"
            finally:
                # Reset to default
                TentaclePresetLoader.set_presets_path(None)

    def test_loader_clear_cache(self):
        """Test clearing the cache."""
        # Load something to populate cache
        load_tentacle("default")
        assert "presets" in TentaclePresetLoader._cache

        # Clear cache
        TentaclePresetLoader.clear_cache()
        assert "presets" not in TentaclePresetLoader._cache

    def test_loader_preset_exists(self):
        """Test checking if preset exists."""
        assert TentaclePresetLoader.preset_exists("default")
        assert not TentaclePresetLoader.preset_exists("nonexistent")

    def test_loader_zombie_mouth_exists(self):
        """Test checking if zombie mouth preset exists."""
        assert TentaclePresetLoader.zombie_mouth_exists("standard")
        assert not TentaclePresetLoader.zombie_mouth_exists("nonexistent")

    def test_load_taper_profile(self):
        """Test loading taper profile."""
        profile = TentaclePresetLoader.load_taper_profile("organic")
        assert isinstance(profile, TaperProfile)
        assert profile.profile_type == "organic"

    def test_load_nonexistent_taper_profile(self):
        """Test loading nonexistent taper profile returns default with custom type."""
        # Loading a nonexistent profile creates a profile with that type
        # but the type must still be valid
        profile = TentaclePresetLoader.load_taper_profile("custom")
        assert isinstance(profile, TaperProfile)
        assert profile.profile_type == "custom"

    def test_list_taper_profiles(self):
        """Test listing taper profiles."""
        profiles = TentaclePresetLoader.list_taper_profiles()
        assert isinstance(profiles, list)
        assert "linear" in profiles
        assert "smooth" in profiles
        assert "organic" in profiles


# =============================================================================
# Integration Tests
# =============================================================================

class TestTentacleIntegration:
    """Integration tests for tentacle system."""

    def test_create_custom_zombie_mouth(self):
        """Test creating a custom zombie mouth configuration."""
        main = TentacleConfig(
            length=1.5,
            base_diameter=0.12,
            tip_diameter=0.03,
            segments=30,
            name="CustomMain",
        )
        feeler = TentacleConfig(
            length=0.4,
            base_diameter=0.03,
            tip_diameter=0.008,
            segments=10,
            name="CustomFeeler",
        )

        mouth = ZombieMouthConfig(
            tentacle_count=5,
            distribution="staggered",
            size_mix=0.6,
            spread_angle=90.0,
            main_tentacle=main,
            feeler_tentacle=feeler,
        )

        configs = mouth.get_tentacle_configs()
        assert len(configs) == 5

        angles = mouth.get_tentacle_angles()
        assert len(angles) == 5

    def test_taper_profile_consistency(self):
        """Test that taper profile produces consistent results."""
        config = TentacleConfig(
            base_diameter=0.10,
            tip_diameter=0.02,
            taper_profile="organic",
        )

        # Get diameters at various positions
        d0 = config.get_diameter_at(0.0)
        d25 = config.get_diameter_at(0.25)
        d50 = config.get_diameter_at(0.5)
        d75 = config.get_diameter_at(0.75)
        d100 = config.get_diameter_at(1.0)

        # Should be monotonically decreasing
        assert d0 > d25 > d50 > d75 > d100

        # Base and tip should match config
        assert d0 == pytest.approx(0.10, rel=0.01)
        assert d100 == pytest.approx(0.02, rel=0.01)
