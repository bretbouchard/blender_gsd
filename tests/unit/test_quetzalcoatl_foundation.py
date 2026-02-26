"""
Unit tests for Quetzalcoatl Foundation (Phase 20.0)

Tests for types, configuration loader, and spine generator.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import yaml

# Import from project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import (
    WingType,
    ScaleShape,
    TailType,
    CrestType,
    ColorPattern,
    SpineConfig,
    BodyConfig,
    LimbConfig,
    WingConfig,
    ScaleConfig,
    FeatherConfig,
    HeadConfig,
    TeethConfig,
    WhiskerConfig,
    TailConfig,
    ColorConfig,
    AnimationConfig,
    QuetzalcoatlConfig,
)
from lib.config import ConfigLoader, load_config
from lib.spine import SpineGenerator, SpineResult, generate_spine


class TestEnums:
    """Tests for enumeration types."""

    def test_wing_type_values(self):
        """Test WingType enum values."""
        assert WingType.NONE.value == "none"
        assert WingType.FEATHERED.value == "feathered"
        assert WingType.MEMBRANE.value == "membrane"

    def test_scale_shape_values(self):
        """Test ScaleShape enum values."""
        assert ScaleShape.ROUND.value == "round"
        assert ScaleShape.OVAL.value == "oval"
        assert ScaleShape.HEXAGONAL.value == "hexagonal"
        assert ScaleShape.DIAMOND.value == "diamond"

    def test_tail_type_values(self):
        """Test TailType enum values."""
        assert TailType.POINTED.value == "pointed"
        assert TailType.FEATHER_TUFT.value == "feather_tuft"
        assert TailType.RATTLE.value == "rattle"
        assert TailType.FAN.value == "fan"

    def test_crest_type_values(self):
        """Test CrestType enum values."""
        assert CrestType.NONE.value == "none"
        assert CrestType.RIDGE.value == "ridge"
        assert CrestType.FRILL.value == "frill"
        assert CrestType.HORNS.value == "horns"


class TestSpineConfig:
    """Tests for SpineConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SpineConfig()
        assert config.length == 10.0
        assert config.segments == 64
        assert config.taper_head == 0.3
        assert config.taper_tail == 0.2
        assert config.wave_amplitude == 0.5
        assert config.wave_frequency == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SpineConfig(
            length=25.0,
            segments=128,
            taper_head=0.4,
            wave_frequency=5,
        )
        assert config.length == 25.0
        assert config.segments == 128
        assert config.wave_frequency == 5

    def test_post_init_clamping(self):
        """Test that post_init clamps invalid values."""
        config = SpineConfig(segments=2, wave_frequency=0)
        assert config.segments == 4  # Clamped to min
        assert config.wave_frequency == 1  # Clamped to min


class TestBodyConfig:
    """Tests for BodyConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = BodyConfig()
        assert config.radius == 0.5
        assert config.compression == 0.8
        assert config.dorsal_flat == 0.0

    def test_compression_clamping(self):
        """Test compression is clamped to valid range."""
        config = BodyConfig(compression=5.0)
        assert config.compression == 2.0

        config = BodyConfig(compression=-1.0)
        assert config.compression == 0.1

    def test_dorsal_flat_clamping(self):
        """Test dorsal_flat is clamped to 0-1."""
        config = BodyConfig(dorsal_flat=1.5)
        assert config.dorsal_flat == 1.0

        config = BodyConfig(dorsal_flat=-0.5)
        assert config.dorsal_flat == 0.0


class TestLimbConfig:
    """Tests for LimbConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LimbConfig()
        assert config.leg_pairs == 2
        assert config.leg_positions == [0.3, 0.6]
        assert config.leg_length == 1.0
        assert config.toe_count == 4

    def test_leg_pairs_clamping(self):
        """Test leg_pairs is clamped to 0-4."""
        config = LimbConfig(leg_pairs=10)
        assert config.leg_pairs == 4

        config = LimbConfig(leg_pairs=-2)
        assert config.leg_pairs == 0


class TestWingConfig:
    """Tests for WingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WingConfig()
        assert config.wing_type == WingType.NONE
        assert config.wing_span == 3.0
        assert config.finger_count == 4

    def test_feathered_wing(self):
        """Test feathered wing configuration."""
        config = WingConfig(wing_type=WingType.FEATHERED, feather_layers=5)
        assert config.wing_type == WingType.FEATHERED
        assert config.feather_layers == 5


class TestQuetzalcoatlConfig:
    """Tests for complete QuetzalcoatlConfig."""

    def test_default_config(self):
        """Test default configuration is valid."""
        config = QuetzalcoatlConfig()
        assert config.name == "Quetzalcoatl"
        assert config.seed == 42
        assert config.is_valid()

    def test_validate_valid_config(self):
        """Test validation passes for valid config."""
        config = QuetzalcoatlConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_spine_length(self):
        """Test validation catches invalid spine length."""
        config = QuetzalcoatlConfig()
        config.spine.length = 0.5  # Too short
        errors = config.validate()
        assert any("spine.length" in e for e in errors)

    def test_validate_invalid_leg_positions(self):
        """Test validation catches mismatched leg positions."""
        config = QuetzalcoatlConfig()
        config.limbs.leg_pairs = 4
        config.limbs.leg_positions = [0.3, 0.6]  # Only 2 positions
        errors = config.validate()
        assert any("leg_positions" in e for e in errors)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = QuetzalcoatlConfig(name="Test")
        data = config.to_dict()

        assert data["name"] == "Test"
        assert "spine" in data
        assert "body" in data
        assert data["spine"]["length"] == 10.0


class TestConfigLoader:
    """Tests for ConfigLoader."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            presets_dir = config_dir / "presets"
            presets_dir.mkdir()

            # Create base config
            base_config = {
                "name": "Base",
                "description": "Base config",
                "spine": {"length": 10.0, "segments": 64},
                "body": {"radius": 0.5},
            }
            with open(config_dir / "base_creature.yaml", "w") as f:
                yaml.dump(base_config, f)

            # Create preset
            preset_config = {
                "name": "TestPreset",
                "description": "Test preset",
                "extends": "base_creature",
                "spine": {"length": 20.0},
            }
            with open(presets_dir / "test.yaml", "w") as f:
                yaml.dump(preset_config, f)

            yield config_dir

    def test_load_yaml(self, temp_config_dir):
        """Test loading configuration from YAML."""
        loader = ConfigLoader(temp_config_dir)
        config = loader.load_yaml(temp_config_dir / "base_creature.yaml")

        assert config.name == "Base"
        assert config.spine.length == 10.0

    def test_load_preset(self, temp_config_dir):
        """Test loading preset configuration."""
        loader = ConfigLoader(temp_config_dir)
        config = loader.load_preset("test")

        assert config.name == "TestPreset"
        assert config.spine.length == 20.0  # Overridden

    def test_preset_caching(self, temp_config_dir):
        """Test that presets are cached."""
        loader = ConfigLoader(temp_config_dir)

        config1 = loader.load_preset("test")
        config2 = loader.load_preset("test")

        assert config1 is config2  # Same object from cache

    def test_list_presets(self, temp_config_dir):
        """Test listing available presets."""
        loader = ConfigLoader(temp_config_dir)
        presets = loader.list_presets()

        assert "test" in presets
        assert presets["test"] == "Test preset"

    def test_preset_not_found(self, temp_config_dir):
        """Test error when preset not found."""
        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(FileNotFoundError):
            loader.load_preset("nonexistent")

    def test_merge_configs(self):
        """Test configuration merging."""
        loader = ConfigLoader()

        base = {"spine": {"length": 10.0, "segments": 64}, "body": {"radius": 0.5}}
        override = {"spine": {"length": 20.0}}

        result = loader._merge_configs(base, override)

        assert result["spine"]["length"] == 20.0  # Overridden
        assert result["spine"]["segments"] == 64  # Preserved
        assert result["body"]["radius"] == 0.5  # Preserved


class TestSpineGenerator:
    """Tests for SpineGenerator."""

    def test_generate_basic(self):
        """Test basic spine generation."""
        config = SpineConfig()
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        assert isinstance(result, SpineResult)
        assert result.point_count == 64
        assert result.points.shape == (64, 3)

    def test_generate_custom_segments(self):
        """Test generation with custom segment count."""
        config = SpineConfig(segments=128)
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        assert result.point_count == 128

    def test_points_start_at_origin(self):
        """Test that spine starts at origin."""
        config = SpineConfig()
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        assert result.points[0][0] == 0.0  # X starts at 0

    def test_points_end_at_length(self):
        """Test that spine ends at configured length."""
        config = SpineConfig(length=25.0)
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        assert abs(result.points[-1][0] - 25.0) < 0.1  # X ends at length

    def test_tangents_normalized(self):
        """Test that tangent vectors are normalized."""
        config = SpineConfig()
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        lengths = np.linalg.norm(result.tangents, axis=1)
        assert np.allclose(lengths, 1.0, atol=0.01)

    def test_normals_normalized(self):
        """Test that normal vectors are normalized."""
        config = SpineConfig()
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        lengths = np.linalg.norm(result.normals, axis=1)
        assert np.allclose(lengths, 1.0, atol=0.01)

    def test_radii_range(self):
        """Test that radii are in valid range."""
        config = SpineConfig()
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        assert np.all(result.radii > 0)
        assert np.all(result.radii <= 1.5)  # Allow for body bulge

    def test_spine_positions_range(self):
        """Test that spine positions are 0-1."""
        config = SpineConfig()
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        assert result.spine_positions[0] == 0.0
        assert result.spine_positions[-1] == 1.0

    def test_deterministic_generation(self):
        """Test that same seed produces same output."""
        config = SpineConfig()

        gen1 = SpineGenerator(config, seed=12345)
        result1 = gen1.generate()

        gen2 = SpineGenerator(config, seed=12345)
        result2 = gen2.generate()

        assert np.array_equal(result1.points, result2.points)

    def test_different_seeds_different_output(self):
        """Test that different seeds produce different output."""
        config = SpineConfig()

        gen1 = SpineGenerator(config, seed=111)
        result1 = gen1.generate()

        gen2 = SpineGenerator(config, seed=222)
        result2 = gen2.generate()

        assert not np.array_equal(result1.points, result2.points)

    def test_wave_deformation(self):
        """Test that wave is applied to Y axis."""
        config = SpineConfig(wave_amplitude=1.0, wave_frequency=2)
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        # Y should have non-zero values (wave deformation)
        assert np.any(result.points[:, 1] != 0)

    def test_taper_at_head(self):
        """Test that radius is smaller at head."""
        config = SpineConfig(taper_head=0.3)
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        # Head radius should be smaller than mid-body
        head_radius = result.radii[0]
        mid_radius = result.radii[len(result.radii) // 2]
        assert head_radius < mid_radius

    def test_taper_at_tail(self):
        """Test that radius is smaller at tail."""
        config = SpineConfig(taper_tail=0.2)
        generator = SpineGenerator(config, seed=42)
        result = generator.generate()

        # Tail radius should be smaller than mid-body
        tail_radius = result.radii[-1]
        mid_radius = result.radii[len(result.radii) // 2]
        assert tail_radius < mid_radius


class TestSpineResult:
    """Tests for SpineResult dataclass."""

    def test_point_count_property(self):
        """Test point_count property."""
        result = generate_spine(segments=50)
        assert result.point_count == 50

    def test_length_property(self):
        """Test approximate length calculation."""
        result = generate_spine(length=20.0)
        # Length should be close to configured length
        assert 18.0 < result.length < 22.0


class TestGenerateSpine:
    """Tests for convenience function."""

    def test_generate_spine_defaults(self):
        """Test generate_spine with default parameters."""
        result = generate_spine()

        assert result.point_count == 64
        assert isinstance(result, SpineResult)

    def test_generate_spine_custom(self):
        """Test generate_spine with custom parameters."""
        result = generate_spine(
            length=30.0,
            segments=100,
            taper_head=0.4,
            taper_tail=0.3,
            wave_amplitude=1.0,
            wave_frequency=5,
            seed=999,
        )

        assert result.point_count == 100


class TestIntegration:
    """Integration tests for foundation modules."""

    @pytest.fixture
    def config_path(self):
        """Get path to actual config files."""
        return Path(__file__).parent.parent.parent / "projects" / "quetzalcoatl" / "configs"

    def test_load_real_base_config(self, config_path):
        """Test loading the actual base_creature.yaml."""
        if not config_path.exists():
            pytest.skip("Config directory not found")

        loader = ConfigLoader(config_path)
        config = loader.load_yaml(config_path / "base_creature.yaml")

        assert config.name == "Quetzalcoatl"
        assert config.is_valid()

    def test_load_real_preset(self, config_path):
        """Test loading actual preset configurations."""
        if not config_path.exists():
            pytest.skip("Config directory not found")

        loader = ConfigLoader(config_path)

        # Try to load serpent preset
        try:
            config = loader.load_preset("serpent")
            assert config.limbs.leg_pairs == 0
            assert config.wings.wing_type == WingType.NONE
        except FileNotFoundError:
            pytest.skip("serpent.yaml not found")

    def test_full_workflow(self, config_path):
        """Test full workflow: load config, generate spine."""
        if not config_path.exists():
            pytest.skip("Config directory not found")

        loader = ConfigLoader(config_path)

        try:
            config = loader.load_preset("dragon")
        except FileNotFoundError:
            config = QuetzalcoatlConfig()

        # Generate spine from config
        generator = SpineGenerator(config.spine, seed=config.seed)
        result = generator.generate()

        assert result.point_count == config.spine.segments
        assert result.point_count > 0
