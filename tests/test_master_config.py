"""
Tests for Master Production Config

Unit tests for config_schema, template_expansion, and config_validation.

Run with: pytest tests/test_master_config.py -v
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.production.config_schema import (
    ProductionMeta,
    SourceConfig,
    CharacterDef,
    LocationDef,
    ShotDef,
    RetroOutputConfig,
    OutputDef,
    MasterProductionConfig,
    MASTER_CONFIG_PRESETS,
    create_master_config_from_preset,
)

from lib.production.template_expansion import (
    CompleteShotConfig,
    SHOT_TEMPLATES,
    STYLE_PRESETS,
    expand_shot_templates,
    resolve_character_wardrobe,
    resolve_location,
    apply_style_preset,
    get_shot_template,
    list_shot_templates,
    list_style_presets,
    suggest_shot_for_context,
    expand_output_formats,
    get_production_summary,
)

from lib.production.config_validation import (
    validate_master_config,
    validate_meta,
    validate_source,
    validate_character_defs,
    validate_location_defs,
    validate_shot_defs,
    check_file_references,
    check_shot_templates,
    validate_output_defs,
    validate_for_execution_strict,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def sample_master_config():
    """Create a sample master production config."""
    return MasterProductionConfig(
        meta=ProductionMeta(
            title="Test Production",
            author="Test Author",
            description="A test production",
        ),
        source=SourceConfig(
            script="test.fountain",
            style_preset="cinematic",
        ),
        characters={
            "hero": CharacterDef(
                name="Hero",
                model="assets/hero.blend",
                wardrobe={
                    "default": "hero_casual",
                    "scenes_5_10": "hero_formal",
                },
            ),
        },
        locations={
            "warehouse": LocationDef(
                name="Warehouse",
                preset="industrial",
                hdri="warehouse_4k",
            ),
        },
        shots=[
            ShotDef(scene=1, template="establishing_wide", location="warehouse"),
            ShotDef(scene=1, template="character_cu", character="hero"),
            ShotDef(scene=5, template="two_shot", character="hero", notes="Hero scene"),
        ],
        outputs=[
            OutputDef(
                name="Master",
                format="prores_4444",
                resolution=(1920, 1080),
            ),
            OutputDef(
                name="SNES",
                format="png_sequence",
                resolution=(256, 224),
                retro=RetroOutputConfig(
                    enabled=True,
                    palette="snes",
                    dither="error_diffusion",
                ),
            ),
        ],
    )


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content for testing."""
    return """
production:
  meta:
    title: "My Test Film"
    version: "1.0"
    author: "Test Author"

  source:
    script: "scripts/test.fountain"
    style_preset: "cinematic_warm"

  characters:
    hero:
      model: "assets/hero.blend"
      wardrobe:
        default: "hero_casual"
        scenes_1_3: "hero_action"

  locations:
    warehouse:
      preset: "industrial"
      hdri: "warehouse_4k"

  shots:
    - scene: 1
      template: "establishing_wide"
      location: "warehouse"
    - scene: 1
      template: "character_cu"
      character: "hero"
      notes: "Hero close-up"

  outputs:
    - name: "Master"
      format: "prores_4444"
      resolution: [1920, 1080]
    - name: "Retro"
      format: "png_sequence"
      resolution: [256, 224]
      retro:
        enabled: true
        palette: "snes"
        dither: "error_diffusion"
"""


# =============================================================================
# Config Schema Tests
# =============================================================================

class TestProductionMeta:
    """Tests for ProductionMeta."""

    def test_create(self):
        """Test creating ProductionMeta."""
        meta = ProductionMeta(
            title="Test",
            author="Author",
        )
        assert meta.title == "Test"
        assert meta.author == "Author"

    def test_to_dict(self):
        """Test serialization."""
        meta = ProductionMeta(title="Test")
        data = meta.to_dict()
        assert data["title"] == "Test"

    def test_from_dict(self):
        """Test deserialization."""
        data = {"title": "Test", "author": "Author"}
        meta = ProductionMeta.from_dict(data)
        assert meta.title == "Test"
        assert meta.author == "Author"


class TestSourceConfig:
    """Tests for SourceConfig."""

    def test_create(self):
        """Test creating SourceConfig."""
        source = SourceConfig(
            script="test.fountain",
            style_preset="cinematic",
        )
        assert source.script == "test.fountain"
        assert source.style_preset == "cinematic"

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        source = SourceConfig(
            script="test.fountain",
            style_preset="cinematic",
            reference_images=["ref1.jpg"],
        )
        data = source.to_dict()
        restored = SourceConfig.from_dict(data)
        assert restored.script == source.script
        assert restored.style_preset == source.style_preset
        assert len(restored.reference_images) == 1


class TestCharacterDef:
    """Tests for CharacterDef."""

    def test_create(self):
        """Test creating CharacterDef."""
        char = CharacterDef(
            name="Hero",
            model="hero.blend",
        )
        assert char.name == "Hero"
        assert char.model == "hero.blend"

    def test_get_costume_for_scene(self):
        """Test costume lookup by scene."""
        char = CharacterDef(
            name="Hero",
            wardrobe={
                "default": "casual",
                "scenes_1_5": "action",
                "6-10": "formal",
            },
        )
        assert char.get_costume_for_scene(3) == "action"
        assert char.get_costume_for_scene(8) == "formal"
        assert char.get_costume_for_scene(100) == "casual"  # Falls back to default

    def test_to_character_config(self):
        """Test conversion to CharacterConfig."""
        char = CharacterDef(
            name="Hero",
            model="hero.blend",
            wardrobe={"default": "casual"},
        )
        config = char.to_character_config()
        assert config.name == "Hero"
        assert config.model == "hero.blend"


class TestLocationDef:
    """Tests for LocationDef."""

    def test_create(self):
        """Test creating LocationDef."""
        loc = LocationDef(
            name="Warehouse",
            preset="industrial",
        )
        assert loc.name == "Warehouse"
        assert loc.preset == "industrial"

    def test_to_location_config(self):
        """Test conversion to LocationConfig."""
        loc = LocationDef(
            name="Warehouse",
            preset="industrial",
            hdri="warehouse_4k",
        )
        config = loc.to_location_config()
        assert config.name == "Warehouse"
        assert config.preset == "industrial"


class TestShotDef:
    """Tests for ShotDef."""

    def test_create(self):
        """Test creating ShotDef."""
        shot = ShotDef(
            scene=1,
            template="character_cu",
            character="hero",
        )
        assert shot.scene == 1
        assert shot.template == "character_cu"
        assert shot.character == "hero"

    def test_to_shot_config(self):
        """Test conversion to ShotConfig."""
        shot = ShotDef(
            scene=1,
            template="character_cu",
            character="hero",
            duration=90,
        )
        config = shot.to_shot_config(0)
        assert config.name == "shot_001"
        assert config.scene == 1
        assert config.duration == 90


class TestRetroOutputConfig:
    """Tests for RetroOutputConfig."""

    def test_create(self):
        """Test creating RetroOutputConfig."""
        retro = RetroOutputConfig(
            enabled=True,
            palette="snes",
            dither="error_diffusion",
        )
        assert retro.enabled is True
        assert retro.palette == "snes"

    def test_to_retro_config(self):
        """Test conversion to RetroConfig."""
        retro = RetroOutputConfig(
            enabled=True,
            palette="snes",
            dither="error_diffusion",
            crt_effects=True,
        )
        config = retro.to_retro_config()
        assert config.enabled is True
        assert config.palette == "snes"
        assert config.crt_effects is True


class TestOutputDef:
    """Tests for OutputDef."""

    def test_create(self):
        """Test creating OutputDef."""
        output = OutputDef(
            name="Master",
            format="prores_4444",
            resolution=(1920, 1080),
        )
        assert output.name == "Master"
        assert output.resolution == (1920, 1080)

    def test_with_retro(self):
        """Test output with retro config."""
        output = OutputDef(
            name="SNES",
            format="png_sequence",
            retro=RetroOutputConfig(enabled=True, palette="snes"),
        )
        data = output.to_dict()
        assert data["retro"]["enabled"] is True
        assert data["retro"]["palette"] == "snes"

    def test_to_output_format(self):
        """Test conversion to OutputFormat."""
        output = OutputDef(
            name="Master",
            format="prores_4444",
            resolution=(1920, 1080),
            frame_rate=24,
        )
        fmt = output.to_output_format()
        assert fmt.name == "Master"
        assert fmt.resolution == (1920, 1080)


class TestMasterProductionConfig:
    """Tests for MasterProductionConfig."""

    def test_create(self, sample_master_config):
        """Test creating MasterProductionConfig."""
        assert sample_master_config.meta.title == "Test Production"
        assert len(sample_master_config.characters) == 1
        assert len(sample_master_config.shots) == 3
        assert len(sample_master_config.outputs) == 2

    def test_to_dict(self, sample_master_config):
        """Test serialization."""
        data = sample_master_config.to_dict()
        assert data["meta"]["title"] == "Test Production"
        assert "characters" in data
        assert "shots" in data

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "meta": {"title": "Test"},
            "characters": {
                "hero": {"model": "hero.blend"}
            },
            "shots": [{"scene": 1, "template": "establishing_wide"}],
            "outputs": [{"name": "Master", "format": "prores_4444"}],
        }
        config = MasterProductionConfig.from_dict(data)
        assert config.meta.title == "Test"
        assert len(config.characters) == 1
        assert len(config.shots) == 1

    def test_from_yaml(self, temp_dir, sample_yaml_content):
        """Test loading from YAML."""
        yaml_path = os.path.join(temp_dir, "production.yaml")
        with open(yaml_path, "w") as f:
            f.write(sample_yaml_content)

        config = MasterProductionConfig.from_yaml(yaml_path)
        assert config.meta.title == "My Test Film"
        assert config.base_path == temp_dir
        assert len(config.characters) == 1
        assert len(config.shots) == 2

    def test_to_yaml(self, sample_master_config, temp_dir):
        """Test saving to YAML."""
        yaml_path = os.path.join(temp_dir, "output.yaml")
        sample_master_config.to_yaml(yaml_path)

        assert os.path.exists(yaml_path)

        # Load and verify
        loaded = MasterProductionConfig.from_yaml(yaml_path)
        assert loaded.meta.title == "Test Production"

    def test_validate(self, sample_master_config):
        """Test validation."""
        result = sample_master_config.validate()
        # Should have warnings but may be valid
        assert isinstance(result.valid, bool)

    def test_get_shot_count(self, sample_master_config):
        """Test shot count."""
        count = sample_master_config.get_shot_count()
        assert count == 3  # 3 shots, no variations

        # Add variations
        sample_master_config.shots[0].variations = 2
        count = sample_master_config.get_shot_count()
        assert count == 5  # 3 shots + 2 variations

    def test_get_scenes(self, sample_master_config):
        """Test getting scene numbers."""
        scenes = sample_master_config.get_scenes()
        assert scenes == [1, 5]

    def test_get_retro_outputs(self, sample_master_config):
        """Test getting retro outputs."""
        retro = sample_master_config.get_retro_outputs()
        assert len(retro) == 1
        assert retro[0].name == "SNES"

    def test_get_cinematic_outputs(self, sample_master_config):
        """Test getting cinematic outputs."""
        cinematic = sample_master_config.get_cinematic_outputs()
        assert len(cinematic) == 1
        assert cinematic[0].name == "Master"

    def test_to_production_config(self, sample_master_config):
        """Test conversion to ProductionConfig."""
        prod_config = sample_master_config.to_production_config()
        assert prod_config.meta.title == "Test Production"
        assert len(prod_config.characters) == 1
        assert len(prod_config.shots) == 3


class TestMasterConfigPresets:
    """Tests for master config presets."""

    def test_preset_exists(self):
        """Test presets exist."""
        assert "short_film" in MASTER_CONFIG_PRESETS
        assert "commercial" in MASTER_CONFIG_PRESETS
        assert "game_assets" in MASTER_CONFIG_PRESETS

    def test_create_from_preset(self, temp_dir):
        """Test creating from preset."""
        config = create_master_config_from_preset(
            "Test Film",
            preset="short_film",
            output_dir=temp_dir
        )
        assert config.meta.title == "Test Film"
        assert os.path.exists(os.path.join(temp_dir, "production.yaml"))


# =============================================================================
# Template Expansion Tests
# =============================================================================

class TestShotTemplates:
    """Tests for shot templates."""

    def test_template_exists(self):
        """Test templates exist."""
        assert "establishing_wide" in SHOT_TEMPLATES
        assert "character_cu" in SHOT_TEMPLATES
        assert "two_shot" in SHOT_TEMPLATES

    def test_get_shot_template(self):
        """Test getting shot template."""
        template = get_shot_template("establishing_wide")
        assert template is not None
        assert "description" in template

    def test_list_shot_templates(self):
        """Test listing templates."""
        templates = list_shot_templates()
        assert len(templates) > 0
        assert "establishing_wide" in templates


class TestStylePresets:
    """Tests for style presets."""

    def test_preset_exists(self):
        """Test presets exist."""
        assert "cinematic" in STYLE_PRESETS
        assert "product_hero" in STYLE_PRESETS

    def test_list_style_presets(self):
        """Test listing presets."""
        presets = list_style_presets()
        assert len(presets) > 0
        assert "cinematic" in presets


class TestExpandShotTemplates:
    """Tests for template expansion."""

    def test_expand_shots(self, sample_master_config):
        """Test expanding shots."""
        expanded = expand_shot_templates(sample_master_config)

        assert len(expanded) == 3

        # Check first shot
        shot1 = expanded[0]
        assert shot1.template == "establishing_wide"
        assert shot1.location is not None
        assert shot1.location.name == "Warehouse"

        # Check second shot
        shot2 = expanded[1]
        assert shot2.template == "character_cu"
        assert shot2.character is not None
        assert shot2.character.name == "Hero"

    def test_resolve_wardrobe(self, sample_master_config):
        """Test wardrobe resolution."""
        costume = resolve_character_wardrobe("hero", 7, sample_master_config)
        assert costume == "hero_formal"

    def test_resolve_location(self, sample_master_config):
        """Test location resolution."""
        loc = resolve_location("warehouse", sample_master_config)
        assert loc is not None
        assert loc.name == "Warehouse"

    def test_suggest_shot_for_context(self):
        """Test shot suggestion."""
        # Character context
        suggestions = suggest_shot_for_context(has_character=True)
        assert len(suggestions) > 0
        assert "character_cu" in suggestions or "character_ms" in suggestions

        # Two character context
        suggestions = suggest_shot_for_context(has_two_characters=True)
        assert "two_shot" in suggestions

        # Location context
        suggestions = suggest_shot_for_context(has_location=True)
        assert "establishing_wide" in suggestions


class TestGetProductionSummary:
    """Tests for production summary."""

    def test_get_summary(self, sample_master_config):
        """Test getting summary."""
        summary = get_production_summary(sample_master_config)

        assert summary["title"] == "Test Production"
        assert summary["character_count"] == 1
        assert summary["location_count"] == 1
        assert summary["shot_count"] == 3
        assert summary["cinematic_outputs"] == 1
        assert summary["retro_outputs"] == 1
        assert summary["total_frames"] > 0


# =============================================================================
# Config Validation Tests
# =============================================================================

class TestConfigValidation:
    """Tests for config validation."""

    def test_validate_valid_config(self, temp_dir):
        """Test validating valid config."""
        config = MasterProductionConfig(
            meta=ProductionMeta(title="Test"),
            characters={
                "hero": CharacterDef(name="hero"),
            },
            locations={
                "warehouse": LocationDef(name="warehouse", preset="industrial"),
            },
            shots=[
                ShotDef(scene=1, template="establishing_wide"),
            ],
            outputs=[
                OutputDef(name="Master", format="prores_4444", resolution=(1920, 1080)),
            ],
            base_path=temp_dir,
        )
        result = validate_master_config(config)
        # Should be valid or have only warnings
        assert len(result.errors) == 0

    def test_validate_missing_shots(self):
        """Test validation with no shots."""
        config = MasterProductionConfig(
            meta=ProductionMeta(title="Test"),
        )
        result = validate_master_config(config)
        assert not result.valid
        assert any("No shots" in e.message for e in result.errors)

    def test_validate_missing_character_reference(self):
        """Test validation with missing character."""
        config = MasterProductionConfig(
            meta=ProductionMeta(title="Test"),
            shots=[
                ShotDef(scene=1, template="character_cu", character="missing"),
            ],
        )
        result = validate_master_config(config)
        assert any("missing" in e.message.lower() for e in result.errors)

    def test_validate_unknown_template(self):
        """Test validation with unknown template."""
        config = MasterProductionConfig(
            meta=ProductionMeta(title="Test"),
            shots=[
                ShotDef(scene=1, template="unknown_template"),
            ],
            outputs=[
                OutputDef(name="Master", format="prores_4444"),
            ],
        )
        issues = check_shot_templates(config)
        assert len(issues) > 0

    def test_validate_output_resolution(self):
        """Test output resolution validation."""
        output = OutputDef(
            name="Bad",
            format="test",
            resolution=(0, 0),  # Invalid
        )
        issues = validate_output_defs(MasterProductionConfig(outputs=[output]))
        assert any("resolution" in issue.message.lower() for issue in issues)

    def test_strict_validation(self):
        """Test strict validation for execution."""
        # Config without model files
        config = MasterProductionConfig(
            meta=ProductionMeta(title="Test"),
            characters={
                "hero": CharacterDef(name="hero", model="nonexistent.blend"),
            },
            shots=[
                ShotDef(scene=1, template="character_cu", character="hero"),
            ],
            outputs=[
                OutputDef(name="Master", format="prores_4444"),
            ],
        )
        result = validate_for_execution_strict(config)
        # Should have errors for missing model
        assert not result.valid


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self, temp_dir, sample_yaml_content):
        """Test full workflow from YAML to expanded shots."""
        # 1. Create YAML file
        yaml_path = os.path.join(temp_dir, "production.yaml")
        with open(yaml_path, "w") as f:
            f.write(sample_yaml_content)

        # 2. Load master config
        config = MasterProductionConfig.from_yaml(yaml_path)
        assert config.meta.title == "My Test Film"

        # 3. Validate
        result = validate_master_config(config)
        # May have warnings (files don't exist)

        # 4. Expand shots
        expanded = expand_shot_templates(config)
        assert len(expanded) == 2

        # 5. Get summary
        summary = get_production_summary(config)
        assert summary["shot_count"] == 2
        assert summary["retro_outputs"] == 1

    def test_cli_commands(self, temp_dir, sample_yaml_content):
        """Test that CLI can load and process config."""
        yaml_path = os.path.join(temp_dir, "production.yaml")
        with open(yaml_path, "w") as f:
            f.write(sample_yaml_content)

        # Load as master config
        config = MasterProductionConfig.from_yaml(yaml_path)

        # Verify it loaded correctly
        assert config.meta.title == "My Test Film"
        assert len(config.shots) == 2
        assert len(config.outputs) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
