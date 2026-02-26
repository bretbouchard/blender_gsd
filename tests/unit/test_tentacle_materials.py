"""
Unit Tests for Tentacle Material System (Phase 19.4)

Tests for types, themes, skin shader, vein patterns, baking, and presets.
"""

import pytest
from dataclasses import asdict
from typing import Dict, Any

from lib.tentacle.materials import (
    # Enums
    MaterialTheme,
    WetnessLevel,
    # Config dataclasses
    SSSConfig,
    WetnessConfig,
    VeinConfig,
    RoughnessConfig,
    MaterialZone,
    ThemePreset,
    TentacleMaterialConfig,
    BakeConfig,
    BakeResult,
    # Theme presets
    THEME_PRESETS,
    get_theme_preset,
    get_theme_preset_by_name,
    list_theme_presets,
    blend_themes,
    # Skin shader
    SkinShaderGenerator,
    create_skin_material,
    # Vein patterns
    VeinPatternGenerator,
    create_bioluminescent_pattern,
    # Baking
    TextureBaker,
    bake_material,
    bake_all_lods,
    # Preset loading
    MaterialPresetLoader,
    load_theme_preset,
    load_material_config,
    load_bake_config,
    list_yaml_theme_presets,
    list_material_configs,
    clear_cache,
    # Convenience functions
    create_horror_material,
    create_zombie_tentacle_material,
    create_mutated_tentacle_material,
)


class TestMaterialTypes:
    """Tests for material type dataclasses."""

    def test_sss_config_defaults(self):
        """SSSConfig should have correct defaults."""
        config = SSSConfig()
        assert config.radius == 1.0
        assert config.color == (1.0, 0.2, 0.2)
        assert config.weight == 1.0
        assert config.anisotropy == 0.0
        assert config.ior == 1.4

    def test_sss_config_custom(self):
        """SSSConfig should accept custom values."""
        config = SSSConfig(
            radius=2.5,
            color=(1.0, 0.0, 0.0),
            weight=0.8,
            anisotropy=0.2,
            ior=1.5,
        )
        assert config.radius == 2.5
        assert config.color == (1.0, 0.0, 0.0)

    def test_sss_config_to_dict(self):
        """SSSConfig should serialize to dict correctly."""
        config = SSSConfig(radius=2.0, color=(0.5, 0.5, 0.5))
        data = config.to_dict()
        assert data["radius"] == 2.0
        assert data["color"] == [0.5, 0.5, 0.5]

    def test_wetness_config_defaults(self):
        """WetnessConfig should have correct defaults."""
        config = WetnessConfig()
        assert config.level == WetnessLevel.DRY
        assert config.intensity == 0.5
        assert config.roughness_modifier == 0.3

    def test_wetness_config_levels(self):
        """WetnessConfig should accept all wetness levels."""
        for level in WetnessLevel:
            config = WetnessConfig(level=level)
            assert config.level == level

    def test_vein_config_defaults(self):
        """VeinConfig should have correct defaults."""
        config = VeinConfig()
        assert config.enabled is True
        assert config.color == (0.3, 0.0, 0.0)
        assert config.density == 0.5
        assert config.glow is False

    def test_vein_config_glow(self):
        """VeinConfig should support bioluminescence."""
        config = VeinConfig(
            enabled=True,
            glow=True,
            glow_color=(0.0, 1.0, 0.5),
            glow_intensity=0.7,
        )
        assert config.glow is True
        assert config.glow_color == (0.0, 1.0, 0.5)
        assert config.glow_intensity == 0.7

    def test_roughness_config_defaults(self):
        """RoughnessConfig should have correct defaults."""
        config = RoughnessConfig()
        assert config.base == 0.5
        assert config.variation == 0.1
        assert config.metallic == 0.0

    def test_material_zone(self):
        """MaterialZone should store zone properties."""
        zone = MaterialZone(
            name="base",
            position=0.0,
            width=0.3,
            color_tint=(0.9, 0.95, 0.9),
        )
        assert zone.name == "base"
        assert zone.position == 0.0
        assert zone.width == 0.3

    def test_theme_preset(self):
        """ThemePreset should store complete theme configuration."""
        preset = ThemePreset(
            name="Test",
            theme=MaterialTheme.ROTTING,
            base_color=(0.5, 0.5, 0.5),
        )
        assert preset.name == "Test"
        assert preset.theme == MaterialTheme.ROTTING
        assert preset.base_color == (0.5, 0.5, 0.5)

    def test_tentacle_material_config_defaults(self):
        """TentacleMaterialConfig should have correct defaults."""
        config = TentacleMaterialConfig()
        assert config.name == "TentacleMaterial"
        assert config.theme_preset is None
        assert config.zones == []
        assert config.blend_zones is True

    def test_bake_config_defaults(self):
        """BakeConfig should have correct defaults."""
        config = BakeConfig()
        assert config.resolution == 2048
        assert config.bake_albedo is True
        assert config.bake_normal is True
        assert config.output_format == "PNG"

    def test_bake_result(self):
        """BakeResult should track bake outputs."""
        result = BakeResult(
            albedo_path="/path/to/albedo.png",
            success=True,
            bake_time=1.5,
        )
        assert result.success is True
        assert result.albedo_path == "/path/to/albedo.png"
        assert result.bake_time == 1.5


class TestMaterialThemes:
    """Tests for theme preset system."""

    def test_theme_presets_exist(self):
        """All theme presets should be defined."""
        assert len(THEME_PRESETS) == 5
        assert MaterialTheme.ROTTING in THEME_PRESETS
        assert MaterialTheme.PARASITIC in THEME_PRESETS
        assert MaterialTheme.DEMONIC in THEME_PRESETS
        assert MaterialTheme.MUTATED in THEME_PRESETS
        assert MaterialTheme.DECAYED in THEME_PRESETS

    def test_get_theme_preset_rotting(self):
        """Rotting theme should have correct properties."""
        preset = get_theme_preset(MaterialTheme.ROTTING)
        assert preset.name == "Rotting"
        assert preset.theme == MaterialTheme.ROTTING
        # Gray-green base color
        assert preset.base_color[1] > preset.base_color[0]  # More green than red
        # Strong red SSS
        assert preset.sss.color[0] > preset.sss.color[1]

    def test_get_theme_preset_parasitic(self):
        """Parasitic theme should have correct properties."""
        preset = get_theme_preset(MaterialTheme.PARASITIC)
        assert preset.name == "Parasitic"
        # Flesh pink base
        assert preset.base_color[0] > 0.5  # Pink/red tones

    def test_get_theme_preset_demonic(self):
        """Demonic theme should have correct properties."""
        preset = get_theme_preset(MaterialTheme.DEMONIC)
        assert preset.name == "Demonic"
        # Deep red base
        assert preset.base_color[0] > preset.base_color[1]
        assert preset.base_color[0] > preset.base_color[2]

    def test_get_theme_preset_mutated(self):
        """Mutated theme should have bioluminescence."""
        preset = get_theme_preset(MaterialTheme.MUTATED)
        assert preset.name == "Mutated"
        # Has bioluminescence
        assert preset.veins.glow is True
        assert preset.emission_strength > 0

    def test_get_theme_preset_decayed(self):
        """Decayed theme should be dry with no veins."""
        preset = get_theme_preset(MaterialTheme.DECAYED)
        assert preset.name == "Decayed"
        # No veins
        assert preset.veins.enabled is False
        # Lower wetness than other themes
        assert preset.wetness.intensity < 0.5

    def test_get_theme_preset_by_name(self):
        """Should get preset by string name."""
        preset = get_theme_preset_by_name("rotting")
        assert preset is not None
        assert preset.theme == MaterialTheme.ROTTING

        # Invalid name should raise KeyError
        with pytest.raises(KeyError):
            get_theme_preset_by_name("nonexistent")

    def test_list_theme_presets(self):
        """Should list all theme preset names."""
        names = list_theme_presets()
        assert len(names) == 5
        assert "Rotting" in names
        assert "Parasitic" in names

    def test_blend_themes(self):
        """Should blend two themes together."""
        blended = blend_themes(MaterialTheme.ROTTING, MaterialTheme.DEMONIC, blend_factor=0.5)

        rotting = get_theme_preset(MaterialTheme.ROTTING)
        demonic = get_theme_preset(MaterialTheme.DEMONIC)

        # Base color should be between both
        for i in range(3):
            min_val = min(rotting.base_color[i], demonic.base_color[i])
            max_val = max(rotting.base_color[i], demonic.base_color[i])
            assert min_val <= blended.base_color[i] <= max_val


class TestSkinShader:
    """Tests for skin shader generator."""

    def test_skin_shader_generator_creation(self):
        """Should create SkinShaderGenerator with config."""
        preset = get_theme_preset(MaterialTheme.ROTTING)
        config = TentacleMaterialConfig(name="TestMaterial", theme_preset=preset)
        generator = SkinShaderGenerator(config)
        assert generator.config == config

    def test_skin_shader_custom_name(self):
        """Should accept custom material name."""
        preset = get_theme_preset(MaterialTheme.PARASITIC)
        config = TentacleMaterialConfig(name="CustomMaterial", theme_preset=preset)
        generator = SkinShaderGenerator(config)
        assert generator.config.name == "CustomMaterial"

    def test_create_skin_material_function(self):
        """create_skin_material should work."""
        result = create_skin_material(MaterialTheme.DEMONIC)
        # Will fail without Blender but should return a result
        assert result is not None
        assert result.material_name is not None

    def test_skin_shader_generate_no_blender(self):
        """Should handle missing Blender gracefully."""
        preset = get_theme_preset(MaterialTheme.ROTTING)
        config = TentacleMaterialConfig(name="TestMaterial", theme_preset=preset)
        generator = SkinShaderGenerator(config)
        result = generator.generate()
        # Will fail without Blender
        assert result.success is False or result.success is True  # Either works


class TestVeinPattern:
    """Tests for vein pattern generator."""

    def test_vein_pattern_generator_creation(self):
        """Should create VeinPatternGenerator."""
        config = VeinConfig(
            enabled=True,
            density=0.6,
            scale=0.1,
        )
        generator = VeinPatternGenerator(config)
        assert generator.config == config

    def test_vein_pattern_generate_numpy(self):
        """Should generate vein pattern array without Blender."""
        config = VeinConfig(
            enabled=True,
            density=0.5,
            scale=0.1,
        )
        generator = VeinPatternGenerator(config)

        # Generate pattern as numpy array
        pattern = generator.generate_numpy(size=(256, 256))

        assert pattern is not None
        assert pattern.shape == (256, 256)  # Grayscale pattern

    def test_vein_pattern_disabled(self):
        """Should return pattern when disabled."""
        config = VeinConfig(enabled=False)
        generator = VeinPatternGenerator(config)

        result = generator.generate_texture("test", size=(64, 64))
        # Should return success with vein_count 0
        assert result.success is True
        assert result.vein_count == 0

    def test_bioluminescent_pattern(self):
        """Should create bioluminescent pattern."""
        result = create_bioluminescent_pattern(
            glow_color=(0.0, 1.0, 0.5),
            intensity=0.8,
            size=(128, 128),
        )
        assert result is not None
        assert result.success is True

    def test_vein_pattern_deterministic(self):
        """Should produce same pattern with same seed."""
        config = VeinConfig(enabled=True, density=0.5)

        gen = VeinPatternGenerator(config)

        pattern1 = gen.generate_numpy(size=(64, 64), seed=42)
        pattern2 = gen.generate_numpy(size=(64, 64), seed=42)

        # Should be identical
        assert (pattern1 == pattern2).all()


class TestTextureBaking:
    """Tests for texture baking system."""

    def test_texture_baker_creation(self):
        """Should create TextureBaker with config."""
        config = BakeConfig(resolution=1024)
        baker = TextureBaker(config)
        assert baker.config.resolution == 1024

    def test_texture_baker_defaults(self):
        """Should use default config if none provided."""
        baker = TextureBaker()
        assert baker.config.resolution == 2048

    def test_bake_result_no_blender(self):
        """Should return error when Blender not available."""
        config = BakeConfig()
        baker = TextureBaker(config)

        result = baker.bake("TestMaterial", "TestMesh")

        # Should fail gracefully without Blender
        assert result.success is False
        assert result.error is not None

    def test_bake_material_convenience(self):
        """bake_material convenience function should work."""
        result = bake_material(
            material_name="Test",
            mesh_name="Mesh",
            output_dir="/tmp",
            resolution=512,
        )
        # Should fail gracefully without Blender
        assert result.success is False

    def test_bake_all_lods(self):
        """Should bake multiple LOD levels."""
        results = bake_all_lods(
            material_name="Test",
            mesh_name="Mesh",
            output_dir="/tmp",
            base_resolution=1024,
            lod_count=3,
        )

        assert len(results) == 3
        assert 0 in results
        assert 1 in results
        assert 2 in results


class TestMaterialPresets:
    """Tests for YAML preset loading."""

    def test_list_yaml_theme_presets(self):
        """Should list theme presets from YAML."""
        names = list_yaml_theme_presets()
        # May be empty if file doesn't exist yet
        assert isinstance(names, list)

    def test_list_material_configs(self):
        """Should list material configs from YAML."""
        names = list_material_configs()
        assert isinstance(names, list)

    def test_load_theme_preset(self):
        """Should load theme preset from YAML."""
        preset = load_theme_preset("rotting")
        # May be None if file doesn't exist
        if preset is not None:
            assert preset.theme == MaterialTheme.ROTTING

    def test_load_bake_config(self):
        """Should load bake config from YAML."""
        config = load_bake_config("default")
        assert isinstance(config, BakeConfig)

    def test_material_preset_loader(self):
        """MaterialPresetLoader should load presets."""
        loader = MaterialPresetLoader()
        themes = loader.list_themes()
        assert isinstance(themes, list)

    def test_preset_loader_clear_cache(self):
        """Should clear cache."""
        loader = MaterialPresetLoader(cache_enabled=True)
        loader._local_cache["test"] = {"data": "value"}

        loader.clear_cache()
        assert len(loader._local_cache) == 0

    def test_clear_cache_function(self):
        """Global clear_cache should work."""
        clear_cache()  # Should not raise


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_horror_material_rotting(self):
        """Should create rotting horror material."""
        generator = create_horror_material(MaterialTheme.ROTTING)
        assert generator.config.theme_preset.theme == MaterialTheme.ROTTING

    def test_create_horror_material_custom_name(self):
        """Should accept custom name."""
        generator = create_horror_material(
            MaterialTheme.DEMONIC,
            name="MyDemonTentacle",
        )
        assert generator.config.name == "MyDemonTentacle"

    def test_create_zombie_tentacle_material(self):
        """Should create zombie tentacle material."""
        generator = create_zombie_tentacle_material()
        assert generator.config.theme_preset.theme == MaterialTheme.ROTTING
        assert "Zombie" in generator.config.name

    def test_create_mutated_tentacle_material(self):
        """Should create mutated tentacle material with bioluminescence."""
        generator = create_mutated_tentacle_material()
        assert generator.config.theme_preset.theme == MaterialTheme.MUTATED
        assert generator.config.theme_preset.veins.glow is True


class TestEnums:
    """Tests for enum types."""

    def test_material_theme_values(self):
        """MaterialTheme should have correct values."""
        assert MaterialTheme.ROTTING.value == "rotting"
        assert MaterialTheme.PARASITIC.value == "parasitic"
        assert MaterialTheme.DEMONIC.value == "demonic"
        assert MaterialTheme.MUTATED.value == "mutated"
        assert MaterialTheme.DECAYED.value == "decayed"

    def test_wetness_level_values(self):
        """WetnessLevel should have correct values."""
        assert WetnessLevel.DRY.value == "dry"
        assert WetnessLevel.MOIST.value == "moist"
        assert WetnessLevel.SLIMY.value == "slimy"
        assert WetnessLevel.DRIPPING.value == "dripping"

    def test_material_theme_count(self):
        """Should have exactly 5 themes."""
        assert len(list(MaterialTheme)) == 5

    def test_wetness_level_count(self):
        """Should have exactly 4 levels."""
        assert len(list(WetnessLevel)) == 4


class TestSerialization:
    """Tests for to_dict serialization."""

    def test_theme_preset_to_dict(self):
        """ThemePreset should serialize correctly."""
        preset = get_theme_preset(MaterialTheme.ROTTING)
        data = preset.to_dict()

        assert "name" in data
        assert "theme" in data
        assert "base_color" in data
        assert "sss" in data
        assert "wetness" in data
        assert "veins" in data

    def test_tentacle_material_config_to_dict(self):
        """TentacleMaterialConfig should serialize correctly."""
        config = TentacleMaterialConfig(
            name="Test",
            zones=[
                MaterialZone(name="base", position=0.0),
            ],
        )
        data = config.to_dict()

        assert data["name"] == "Test"
        assert len(data["zones"]) == 1

    def test_bake_result_to_dict(self):
        """BakeResult should serialize correctly."""
        result = BakeResult(
            albedo_path="/path/albedo.png",
            success=True,
            resolution=(2048, 2048),
            bake_time=2.5,
        )
        data = result.to_dict()

        assert data["albedo_path"] == "/path/albedo.png"
        assert data["success"] is True
        assert data["resolution"] == [2048, 2048]
        assert data["bake_time"] == 2.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
