"""
Unit tests for Quetzalcoatl Presets & Export System (Phase 20.11)

Tests for creature presets and export functionality.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.export import (
    ExportFormat,
    PresetCategory,
    CreaturePreset,
    ExportConfig,
    ExportResult,
    ExportManager,
    CREATURE_PRESETS,
    get_preset,
    list_presets,
    get_presets_by_category,
    export_creature,
    create_custom_preset,
)
from lib.types import WingType, ScaleShape, TailType, CrestType
from lib.color import ColorSystemConfig, ColorPattern, IridescenceConfig


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_format_values(self):
        """Test export format enum values."""
        assert ExportFormat.FBX.value == 0
        assert ExportFormat.OBJ.value == 1
        assert ExportFormat.GLTF.value == 2
        assert ExportFormat.USD.value == 3


class TestPresetCategory:
    """Tests for PresetCategory enum."""

    def test_category_values(self):
        """Test preset category enum values."""
        assert PresetCategory.SERPENT.value == 0
        assert PresetCategory.DRAGON.value == 1
        assert PresetCategory.WYVERN.value == 2
        assert PresetCategory.HYDRA.value == 3


class TestCreaturePreset:
    """Tests for CreaturePreset dataclass."""

    @pytest.fixture
    def sample_preset(self):
        """Create a sample preset."""
        from lib.types import QuetzalcoatlConfig
        return CreaturePreset(
            name="Test Creature",
            category=PresetCategory.CUSTOM,
            description="A test creature",
            config=QuetzalcoatlConfig(),
            color_config=ColorSystemConfig(),
        )

    def test_preset_creation(self, sample_preset):
        """Test creating a preset."""
        assert sample_preset.name == "Test Creature"
        assert sample_preset.category == PresetCategory.CUSTOM

    def test_preset_defaults(self, sample_preset):
        """Test preset default values."""
        assert sample_preset.has_wings is True
        assert sample_preset.has_limbs is True
        assert sample_preset.shader_quality.value == 1  # STANDARD


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_values(self):
        """Test default export config."""
        config = ExportConfig()

        assert config.format == ExportFormat.FBX
        assert config.include_rig is True
        assert config.include_materials is True
        assert config.global_scale == 1.0

    def test_custom_values(self):
        """Test custom export config."""
        config = ExportConfig(
            format=ExportFormat.OBJ,
            global_scale=0.01,
            forward_axis="-Z",
            up_axis="Y",
        )

        assert config.format == ExportFormat.OBJ
        assert config.global_scale == 0.01


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_success_result(self):
        """Test successful export result."""
        result = ExportResult(
            success=True,
            format=ExportFormat.OBJ,
            vertex_count=100,
            face_count=50,
        )

        assert result.success
        assert result.vertex_count == 100
        assert len(result.errors) == 0

    def test_failure_result(self):
        """Test failed export result."""
        result = ExportResult(
            success=False,
            format=ExportFormat.FBX,
            errors=["No vertices", "No faces"],
        )

        assert not result.success
        assert len(result.errors) == 2


class TestExportManager:
    """Tests for ExportManager."""

    @pytest.fixture
    def sample_geometry(self):
        """Create sample geometry for testing."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
        ])
        return vertices, faces

    def test_export_basic(self, sample_geometry):
        """Test basic export."""
        vertices, faces = sample_geometry
        config = ExportConfig(format=ExportFormat.OBJ)
        manager = ExportManager(config)
        result = manager.export(vertices, faces)

        assert result.success
        assert result.vertex_count == 4
        assert result.face_count == 3

    def test_export_with_normals(self, sample_geometry):
        """Test export with normals."""
        vertices, faces = sample_geometry
        normals = np.array([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
        ])

        config = ExportConfig(format=ExportFormat.OBJ)
        manager = ExportManager(config)
        result = manager.export(vertices, faces, normals=normals)

        assert result.success

    def test_export_with_uvs(self, sample_geometry):
        """Test export with UVs."""
        vertices, faces = sample_geometry
        uvs = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.5, 1.0],
            [0.5, 0.5],
        ])

        config = ExportConfig(format=ExportFormat.OBJ)
        manager = ExportManager(config)
        result = manager.export(vertices, faces, uvs=uvs)

        assert result.success

    def test_export_empty_vertices(self):
        """Test export with empty vertices."""
        config = ExportConfig()
        manager = ExportManager(config)
        result = manager.export(
            np.zeros((0, 3)),
            np.zeros((0, 3), dtype=int),
        )

        assert not result.success
        assert len(result.errors) > 0

    def test_export_empty_faces(self, sample_geometry):
        """Test export with empty faces."""
        vertices, _ = sample_geometry
        config = ExportConfig()
        manager = ExportManager(config)
        result = manager.export(vertices, np.zeros((0, 3), dtype=int))

        assert not result.success

    def test_obj_output(self, sample_geometry):
        """Test OBJ output generation."""
        vertices, faces = sample_geometry
        config = ExportConfig(format=ExportFormat.OBJ)
        manager = ExportManager(config)
        result = manager.export(vertices, faces)

        assert result.success

    def test_export_with_bone_data(self, sample_geometry):
        """Test export with bone data."""
        vertices, faces = sample_geometry
        bone_data = {
            "bones": [{"name": "spine_00"}],
        }

        config = ExportConfig()
        manager = ExportManager(config)
        result = manager.export(vertices, faces, bone_data=bone_data)

        assert result.success
        assert result.bone_count == 1


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def sample_geometry(self):
        """Create sample geometry."""
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        faces = np.array([[0, 1, 2]])
        return vertices, faces

    def test_export_creature_defaults(self, sample_geometry):
        """Test export_creature with defaults."""
        vertices, faces = sample_geometry
        result = export_creature(vertices, faces)

        assert isinstance(result, ExportResult)

    def test_export_creature_obj(self, sample_geometry):
        """Test export_creature as OBJ."""
        vertices, faces = sample_geometry
        result = export_creature(vertices, faces, format=ExportFormat.OBJ)

        assert result.success


class TestPresetFunctions:
    """Tests for preset functions."""

    def test_get_preset_exists(self):
        """Test getting existing preset."""
        preset = get_preset("quetzalcoatl")

        assert preset is not None
        assert preset.name == "Quetzalcoatl"

    def test_get_preset_not_exists(self):
        """Test getting non-existent preset."""
        preset = get_preset("nonexistent")

        assert preset is None

    def test_get_preset_case_insensitive(self):
        """Test preset lookup is case insensitive."""
        preset1 = get_preset("QUETZALCOATL")
        preset2 = get_preset("Quetzalcoatl")
        preset3 = get_preset("quetzalcoatl")

        assert preset1 == preset2 == preset3

    def test_list_presets_all(self):
        """Test listing all presets."""
        presets = list_presets()

        assert len(presets) > 0
        assert "quetzalcoatl" in presets

    def test_list_presets_by_category(self):
        """Test listing presets by category."""
        serpent_presets = list_presets(PresetCategory.SERPENT)

        assert len(serpent_presets) > 0
        assert "sea_serpent" in serpent_presets

    def test_get_presets_by_category(self):
        """Test getting all presets organized by category."""
        organized = get_presets_by_category()

        assert PresetCategory.SERPENT in organized
        assert PresetCategory.DRAGON in organized
        assert len(organized[PresetCategory.SERPENT]) > 0


class TestBuiltInPresets:
    """Tests for built-in presets."""

    def test_quetzalcoatl_preset(self):
        """Test Quetzalcoatl preset values."""
        preset = get_preset("quetzalcoatl")

        assert preset.category == PresetCategory.COATL
        assert preset.has_feathers is True
        assert preset.has_limbs is False
        assert preset.config.wings.wing_type == WingType.FEATHERED

    def test_european_dragon_preset(self):
        """Test European Dragon preset values."""
        preset = get_preset("european_dragon")

        assert preset.category == PresetCategory.DRAGON
        assert preset.has_wings is True
        assert preset.has_limbs is True
        assert preset.config.wings.wing_type == WingType.MEMBRANE

    def test_wyvern_preset(self):
        """Test Wyvern preset values."""
        preset = get_preset("wyvern")

        assert preset.category == PresetCategory.WYVERN
        assert preset.has_wings is True

    def test_sea_serpent_preset(self):
        """Test Sea Serpent preset values."""
        preset = get_preset("sea_serpent")

        assert preset.category == PresetCategory.SERPENT
        assert preset.has_wings is False
        assert preset.has_limbs is False

    def test_hydra_preset(self):
        """Test Hydra preset values."""
        preset = get_preset("hydra")

        assert preset.category == PresetCategory.HYDRA
        assert preset.has_wings is False

    def test_amphiptere_preset(self):
        """Test Amphiptere preset values."""
        preset = get_preset("amphiptere")

        assert preset.category == PresetCategory.AMPHIPTERE
        assert preset.has_feathers is True

    def test_ghost_serpent_preset(self):
        """Test Ghost Serpent preset values."""
        preset = get_preset("ghost_serpent")

        assert preset.category == PresetCategory.SERPENT
        assert preset.color_config.primary_color[0] > 0.8  # White-ish

    def test_all_presets_have_required_fields(self):
        """Test all presets have required fields."""
        for name, preset in CREATURE_PRESETS.items():
            assert preset.name is not None
            assert preset.category is not None
            assert preset.description is not None
            assert preset.config is not None
            assert preset.color_config is not None


class TestCreateCustomPreset:
    """Tests for creating custom presets."""

    def test_create_custom_preset_basic(self):
        """Test creating basic custom preset."""
        from lib.types import QuetzalcoatlConfig

        preset = create_custom_preset(
            name="My Creature",
            category=PresetCategory.CUSTOM,
            config=QuetzalcoatlConfig(),
            color_config=ColorSystemConfig(),
        )

        assert preset.name == "My Creature"
        assert preset.category == PresetCategory.CUSTOM

    def test_create_custom_preset_with_features(self):
        """Test creating custom preset with feature flags."""
        from lib.types import QuetzalcoatlConfig

        preset = create_custom_preset(
            name="Feature Test",
            category=PresetCategory.CUSTOM,
            config=QuetzalcoatlConfig(),
            color_config=ColorSystemConfig(),
            has_wings=False,
            has_limbs=True,
            has_feathers=True,
        )

        assert preset.has_wings is False
        assert preset.has_limbs is True
        assert preset.has_feathers is True


class TestIntegration:
    """Integration tests for presets and export."""

    def test_preset_to_export_pipeline(self):
        """Test pipeline from preset to export."""
        # Get preset
        preset = get_preset("quetzalcoatl")
        assert preset is not None

        # Create geometry
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        faces = np.array([[0, 1, 2]])

        # Export
        result = export_creature(vertices, faces, format=ExportFormat.OBJ)

        assert result.success

    def test_multiple_presets_different_configs(self):
        """Test that different presets have different configurations."""
        presets = ["quetzalcoatl", "european_dragon", "sea_serpent"]
        configs = [get_preset(p).config for p in presets]

        # Check wing types differ
        wing_types = [c.wings.wing_type for c in configs]
        assert len(set(wing_types)) > 1

    def test_category_organization(self):
        """Test that presets are properly organized by category."""
        organized = get_presets_by_category()

        # Each category should have at least one preset or be empty
        for category, presets in organized.items():
            assert isinstance(presets, list)

        # Some categories should have presets
        non_empty = [c for c, p in organized.items() if len(p) > 0]
        assert len(non_empty) > 0

    def test_export_all_formats(self):
        """Test exporting in all formats."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])

        for format_type in [ExportFormat.OBJ, ExportFormat.FBX, ExportFormat.GLTF]:
            result = export_creature(vertices, faces, format=format_type)
            # OBJ should succeed, others may just return placeholders
            assert isinstance(result, ExportResult)
